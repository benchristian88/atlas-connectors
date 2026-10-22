# SPDX-License-Identifier: Apache-2.0
"""Privileged transport protections. All HTTP responses are synthetic and local."""
from email.message import Message
import io
from pathlib import Path
import sys
import urllib.error

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import verification_github as transport
from publication_contract import canonical_json


class Response(io.BytesIO):
    def __init__(self, raw=b"[]", status=200, headers=()):
        super().__init__(raw)
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = "application/json"
        for key, value in headers:
            self.headers[key] = value


class Opener:
    def __init__(self, response):
        self.response, self.calls = response, []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def client(response):
    api = transport.VerificationGithub()
    api.opener = Opener(response)
    return api


def test_only_mint_can_post_and_is_exactly_repository_scoped():
    api = client(Response(b"{}", status=201))
    assert api.mint("synthetic-jwt") == {}
    request, timeout = api.opener.calls[0]
    assert request.get_method() == "POST"
    assert request.full_url == "https://api.github.com" + transport.MINT
    assert request.data == canonical_json({"repository_ids": [1414494920], "permissions": transport.PERMISSIONS})
    assert 0 < timeout <= 20
    assert not hasattr(api, "request") and not hasattr(api, "patch")
    with pytest.raises(ValueError):
        api.get(transport.MINT, "synthetic-token")


def test_get_has_no_body_and_preserves_opaque_token_bytes():
    api = client(Response())
    token = "ghs." + "a-_." * 130
    assert api.get(transport.LIST, token) == []
    request, _ = api.opener.calls[0]
    assert request.get_method() == "GET" and request.data is None
    assert request.get_header("Authorization") == "Bearer " + token


@pytest.mark.parametrize("path", ["https://evil.example", "//evil.example", "/repos/other/repo/rulesets",
    transport.BASE + "/rulesets/../1?includes_parents=true", transport.BASE + "/rulesets/%2e%2e",
    transport.LIST + "&page=2", transport.BASE + "/git/refs", "/app/installations/1/access_tokens",
    transport.BASE + "/contents/tools/evil.py?ref=" + "a" * 40, transport.BASE + "/releases/1/assets"])
def test_restricted_token_never_reaches_unapproved_paths(path):
    api = client(Response())
    with pytest.raises(ValueError):
        api.get(path, "synthetic-token")
    assert api.opener.calls == []


@pytest.mark.parametrize("token", [None, "", "bad\r\n", "bad token", "é", "a" * 4097])
def test_bad_tokens_never_reach_network(token):
    api = client(Response())
    with pytest.raises(ValueError):
        api.get(transport.LIST, token)
    assert api.opener.calls == []


@pytest.mark.parametrize("raw,headers,status", [
    (b"[]", [("Link", "")], 200), (b"[]", [("Link", '<https://evil.example>; rel="next"')], 200),
    (b"[]", [("Content-Encoding", "gzip")], 200), (b"[]", [("Content-Length", "1")], 200),
    (b"[]", [("Content-Length", "999999999")], 200), (b"[]", [("Content-Length", "-1")], 200),
    (b"[]", [("Content-Length", "2"), ("Content-Length", "2")], 200),
    (b"[]", [("Content-Length", "２")], 200), (b"[]", [], 302),
    (b"x" * (transport.MAX_RESPONSE + 1), [], 200), (b'{"a":1,"a":2}', [], 200),
    (b"NaN", [], 200), (b"\xff", [], 200), (b"[]", [], 201),
])
def test_response_limits_ambiguity_pagination_and_redirect_status(raw, headers, status):
    api = client(Response(raw, status=status, headers=headers))
    with pytest.raises(ValueError, match="verification_request_failed"):
        api.get(transport.LIST, "synthetic-token")
    assert len(api.opener.calls) == 1


def test_redirect_handler_cannot_forward_any_credentials():
    with pytest.raises(ValueError):
        transport.NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.example")


@pytest.mark.parametrize("error", [TimeoutError("sensitive-token"),
    urllib.error.URLError("sensitive-token"),
    urllib.error.HTTPError("https://api.github.com", 302, "sensitive-token", Message(), io.BytesIO(b"sensitive-token"))])
def test_failure_sanitization_and_no_retry(error):
    api = client(error)
    with pytest.raises(ValueError, match="^verification_request_failed$"):
        api.get(transport.LIST, "synthetic-token")
    assert len(api.opener.calls) == 1


def test_deadline_stops_before_request(monkeypatch):
    api = client(Response())
    monkeypatch.setattr(transport.time, "monotonic", lambda: api.deadline + 1)
    with pytest.raises(ValueError):
        api.get(transport.LIST, "synthetic-token")
    assert api.opener.calls == []


def test_draft_and_ref_absence_endpoints_are_not_available_to_verifier():
    error = urllib.error.HTTPError("https://api.github.com", 404, "sensitive", Message(), io.BytesIO())
    with pytest.raises(ValueError, match="verification_endpoint"):
        client(error).get(transport.BASE + "/git/ref/heads/catalogue-current", "synthetic-token", missing=True)
    with pytest.raises(ValueError):
        client(error).get(transport.LIST, "synthetic-token")
