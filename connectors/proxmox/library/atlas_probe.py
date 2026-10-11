# SPDX-License-Identifier: Apache-2.0
"""Read-only, bounded token authentication and version probe. No inventory calls."""
import hashlib
import http.client
import ipaddress
import json
import os
import re
import socket
import ssl
from urllib.parse import urlsplit

MAX_RESPONSE = 128 * 1024
TIMEOUT = 6


class ProbeError(ValueError):
    pass


def endpoint_policy(value):
    try:
        url = urlsplit(value)
        if (url.scheme != "https" or not url.hostname or url.username is not None or url.password is not None
                or url.path not in {"", "/"} or url.query or url.fragment or url.port == 0
                or "\\" in value or any(char.isspace() for char in value)):
            raise ValueError
        hostname = url.hostname
        if hostname.lower() == "localhost" or hostname.lower().endswith(".localhost"):
            raise ValueError
        return hostname, url.port or 443
    except (ValueError, TypeError):
        raise ProbeError("unsafe_endpoint") from None


def allowed_address(value):
    address = ipaddress.ip_address(value.split("%", 1)[0])
    address = address.ipv4_mapped if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped else address
    return not (address.is_loopback or address.is_link_local or address.is_multicast
                or address.is_unspecified or address.is_reserved or str(address) == "100.100.100.200")


class PinnedConnection(http.client.HTTPSConnection):
    def __init__(self, hostname, port, address, context, fingerprint=None):
        super().__init__(hostname, port, timeout=TIMEOUT, context=context)
        self.address = address
        self.fingerprint = fingerprint

    def connect(self):
        # The vetted DNS result is the actual peer; TLS SNI/hostname remains the
        # operator's hostname. No second resolver call or redirect is permitted.
        raw = socket.create_connection((self.address, self.port), TIMEOUT)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
            if self.fingerprint and hashlib.sha256(self.sock.getpeercert(binary_form=True)).hexdigest() != self.fingerprint:
                raise ProbeError("tls_trust_required")
        except BaseException:
            raw.close()
            if self.sock:
                self.sock.close()
            raise


def bounded_get(connection, path, authorization):
    try:
        connection.request("GET", path, headers={"Authorization": authorization, "Accept": "application/json", "Accept-Encoding": "identity"})
        response = connection.getresponse()
        if response.status in {401, 403}:
            raise ProbeError("authentication_failed" if response.status == 401 else "permission_limited")
        if 300 <= response.status < 400:
            raise ProbeError("redirect_rejected")
        if response.status != 200 or response.getheader("Content-Encoding", "identity") != "identity":
            raise ProbeError("source_unavailable")
        raw = response.read(MAX_RESPONSE + 1)
        if len(raw) > MAX_RESPONSE:
            raise ProbeError("response_too_large")
        parsed = json.loads(raw)
        if not isinstance(parsed, dict) or not isinstance(parsed.get("data"), dict):
            raise ProbeError("invalid_source_response")
        return parsed["data"]
    finally:
        connection.close()


def probe(config, credentials, *, resolver=socket.getaddrinfo, connection_factory=PinnedConnection):
    try:
        host, port = endpoint_policy(config["endpoint"])
        token_id, token_secret = credentials["token_id"], credentials["token_secret"]
        if (not re.fullmatch(r"[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+![A-Za-z0-9_.-]+", token_id)
                or not isinstance(token_secret, str) or not 1 <= len(token_secret) <= 2048
                or any(ord(char) <= 32 or ord(char) > 126 for char in token_secret)):
            raise ProbeError("invalid_credentials")
        mode = config.get("tls_policy", "verify")
        fingerprint = None
        if mode == "verify":
            context = ssl.create_default_context()
        elif mode in {"fingerprint", "insecure"}:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            if mode == "fingerprint":
                fingerprint = config.get("fingerprint", "").lower().replace(":", "")
                if not re.fullmatch(r"[a-f0-9]{64}", fingerprint):
                    raise ProbeError("tls_trust_required")
        else:
            raise ProbeError("invalid_configuration")
        addresses = resolver(host, port, type=socket.SOCK_STREAM)
        if not addresses or len(addresses) > 32 or any(not allowed_address(row[4][0]) for row in addresses):
            raise ProbeError("unsafe_endpoint")
        address = addresses[0][4][0]
        authorization = "PVEAPIToken=" + token_id + "=" + token_secret
        def get(path):
            return bounded_get(connection_factory(host, port, address, context, fingerprint), path, authorization)
        # /version may be readable without auth; /access/permissions proves the
        # token can authenticate. No nodes/guests/storage/network enumeration.
        permissions = get("/api2/json/access/permissions")
        version = get("/api2/json/version").get("version")
        if not isinstance(version, str) or not re.fullmatch(r"[0-9]{1,3}(?:\.[0-9]{1,3}){1,3}(?:-[0-9]{1,4})?", version):
            version = None
        return {"success": True, "category": "connected", "source_version": version,
                "tls": mode, "permission_limited": not any(isinstance(grants, dict) and grants for grants in permissions.values())}
    except ProbeError as error:
        return {"success": False, "category": str(error), "source_version": None}
    except ssl.SSLError:
        return {"success": False, "category": "tls_trust_required", "source_version": None}
    except TimeoutError:
        return {"success": False, "category": "timeout", "source_version": None}
    except (OSError, ValueError, TypeError, KeyError, http.client.HTTPException):
        return {"success": False, "category": "source_unavailable", "source_version": None}


def main():
    from ansible.module_utils.basic import AnsibleModule
    module = AnsibleModule(argument_spec={"input_file": {"type": "path", "required": True},
        "result_file": {"type": "path", "required": True}}, supports_check_mode=False)
    descriptor = os.open(module.params["input_file"], os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as source:
        payload = json.loads(source.read(128 * 1024 + 1))
    result = probe(payload["config"], payload["credentials"])
    payload.clear()
    # Runtime supplies this private output destination, never browser input.
    descriptor = os.open(module.params["result_file"], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "w") as output:
        json.dump(result, output)
    module.exit_json(changed=False)


if __name__ == "__main__":
    main()
