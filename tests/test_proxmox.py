# SPDX-License-Identifier: Apache-2.0
import importlib.util
import json
from pathlib import Path
import secrets
import ssl
import sys

import pytest
from atlas_connector_sdk.contracts import validate_manifest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_bundle import build
spec = importlib.util.spec_from_file_location("probe", ROOT / "connectors/proxmox/library/atlas_probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def credential():
    return {"token_id": "fixture_" + secrets.token_hex(8) + "@pve!probe", "token_secret": secrets.token_urlsafe(32)}


def resolver(*args, **kwargs):
    return [(2, 1, 6, "", ("192.168.1.2", 8006))]


class Response:
    def __init__(self, value, status=200): self.value, self.status = value, status
    def getheader(self, name, default=None): return default
    def read(self, maximum): return self.value[:maximum]


def factory(status=200, oversized=False):
    class Connection:
        def __init__(self, host, port, address, context, fingerprint):
            assert address == "192.168.1.2"
            assert context.verify_mode == ssl.CERT_REQUIRED
        def request(self, method, path, headers):
            assert method == "GET"
            assert path in {"/api2/json/version", "/api2/json/access/permissions"}
            self.path = path
        def getresponse(self):
            value = {"version": "8.4"} if self.path.endswith("version") else {"/": {"Sys.Audit": 1}}
            return Response(b"x" * (probe.MAX_RESPONSE + 1) if oversized else json.dumps({"data": value}).encode(), status)
        def close(self): pass
    return Connection


def test_manifest_and_reproducible_bundle_has_no_discovery_entry_point():
    first, manifest = build()
    second, _ = build()
    assert first == second
    validate_manifest(manifest)
    assert manifest["capabilities"]["discover"] is False
    assert set(manifest["implementation"]["entry_points"]) == {"test_connection"}
    assert manifest["source_versions"]["qualified_versions"] == []
    assert manifest["source_versions"]["qualification"] == "unqualified"
    assert not manifest.get("object_classes")


@pytest.mark.parametrize("url", ["http://192.168.1.2", "file:///tmp/x", "https://u:p@example.test", "https://localhost", "https://example.test:0", "https://example.test:99999", "https://example.test/a", "https://example.test?token=x"])
def test_unsafe_endpoints_never_transmit_credentials(url):
    result = probe.probe({"endpoint": url}, credential(), resolver=lambda *a, **kw: pytest.fail("unsafe URL resolved"))
    assert not result["success"] and result["category"] == "unsafe_endpoint"


@pytest.mark.parametrize("address", ["127.0.0.1", "169.254.169.254", "::1", "fe80::1", "::ffff:127.0.0.1", "100.100.100.200", "0.0.0.0"])
def test_dns_rebinding_to_unsafe_target_is_blocked(address):
    def resolve(*args, **kwargs): return [(2, 1, 6, "", (address, 8006))]
    assert probe.probe({"endpoint": "https://source.example.test:8006"}, credential(), resolver=resolve)["category"] == "unsafe_endpoint"


@pytest.mark.parametrize("status,category", [(200, "connected"), (401, "authentication_failed"), (403, "permission_limited"), (302, "redirect_rejected"), (500, "source_unavailable")])
def test_bounded_probe_and_secret_redaction(status, category):
    values = credential()
    result = probe.probe({"endpoint": "https://192.168.1.2:8006"}, values, resolver=resolver, connection_factory=factory(status))
    assert result["category"] == category
    assert all(value not in json.dumps(result) for value in values.values())
    if status == 200:
        assert result["source_version"] == "8.4"
    assert "assets" not in result and "observations" not in result


def test_response_limit_and_tls_default():
    assert probe.probe({"endpoint": "https://192.168.1.2:8006"}, credential(), resolver=resolver, connection_factory=factory(oversized=True))["category"] == "response_too_large"
    for address in ["192.168.1.2", "10.0.0.2", "fd00::2"]:
        assert probe.allowed_address(address)


def test_fingerprint_is_enforced_before_http_credentials_can_be_sent(monkeypatch):
    from types import SimpleNamespace
    import hashlib
    certificate = secrets.token_bytes(96)
    class Socket:
        closed = False
        def close(self): self.closed = True
        def getpeercert(self, binary_form): return certificate
        def send(self, _data): pytest.fail("credential transmitted before pin validation")
    raw = Socket()
    monkeypatch.setattr(probe.socket, "create_connection", lambda *a: raw)
    context = SimpleNamespace(wrap_socket=lambda socket, **kw: raw)
    connection = probe.PinnedConnection.__new__(probe.PinnedConnection)
    connection.address, connection.host, connection.port = "192.168.1.2", "source.example.test", 8006
    connection._context, connection.sock = context, None
    connection.fingerprint = "0" * 64
    with pytest.raises(probe.ProbeError, match="tls_trust_required"):
        connection.connect()
    assert raw.closed
    connection.fingerprint = hashlib.sha256(certificate).hexdigest()
    connection.connect()


def test_tls_error_does_not_fall_back_to_insecure_mode():
    attempts = []
    def failure(host, port, address, context, pin):
        attempts.append(context.verify_mode)
        raise ssl.SSLCertVerificationError()
    result = probe.probe({"endpoint": "https://192.168.1.2:8006"}, credential(), resolver=resolver, connection_factory=failure)
    assert result["category"] == "tls_trust_required"
    assert attempts == [ssl.CERT_REQUIRED]
