# SPDX-License-Identifier: Apache-2.0
"""Privileged verifier transport: fixed endpoints, GET evidence, one mint POST.

No repository mutation API, generic request method, proxy, redirects or retries.
Pagination fails closed rather than yielding partial security evidence.
"""
import time
import re
import urllib.error
import urllib.request

from atlas_connector_sdk.contracts import strict_json
from publication_contract import REPOSITORY, canonical_json, require
from ruleset_visibility import NoRedirect, MAX_INSTALLATION_TOKEN_LENGTH

BASE = "/repos/" + REPOSITORY
INSTALLATION = BASE + "/installation"
MINT = "/app/installations/174088125/access_tokens"
LIST = BASE + "/rulesets?includes_parents=true&per_page=6&page=1"
PERMISSIONS = {"administration": "write", "contents": "read", "actions": "read",
               "checks": "read", "metadata": "read"}
MAX_RESPONSE = 256 * 1024


def credential(value):
    require(isinstance(value, str) and 0 < len(value) <= MAX_INSTALLATION_TOKEN_LENGTH
            and all("!" <= c <= "~" for c in value), "verification_credential")
    return value


def allowed(path):
    if path in {"/app", INSTALLATION, LIST, "/installation/repositories?per_page=2&page=1",
                "/apps/atlas-catalogue-publisher", "/users/benchristian88", BASE,
                BASE + "/branches/main", BASE + "/immutable-releases",
                BASE + "/environments/catalogue-publication", BASE + "/environments/catalogue-verification"}:
        return True
    patterns = (
        r"/rulesets/[1-9][0-9]{0,15}\?includes_parents=true",
        r"/actions/runs/[1-9][0-9]{0,15}(?:/attempts/1)?",
        r"/actions/workflows/[1-9][0-9]{0,15}",
        r"/commits/[a-f0-9]{40}/check-runs\?check_name=validate&filter=latest&per_page=2&page=1",
        r"/contents/catalogue/publication/policy\.json\?ref=[a-f0-9]{40}",
    )
    return any(re.fullmatch(re.escape(BASE) + suffix, path) for suffix in patterns)


class VerificationGithub:
    def __init__(self):
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        self.deadline = time.monotonic() + 50

    def _json(self, path, token, *, mint=False, missing=False):
        require(type(path) is str and (path == MINT if mint else allowed(path)), "verification_endpoint")
        headers = {"Authorization": "Bearer " + credential(token), "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "atlas-publication-verifier-v2",
            "Accept-Encoding": "identity"}
        data = None
        if mint:
            headers["Content-Type"] = "application/json"
            data = canonical_json({"repository_ids": [1414494920], "permissions": PERMISSIONS})
        request = urllib.request.Request("https://api.github.com" + path, data=data,
                                        headers=headers, method="POST" if mint else "GET")
        try:
            require(time.monotonic() < self.deadline, "verification_deadline")
            with self.opener.open(request, timeout=min(20, max(0.1, self.deadline - time.monotonic()))) as response:
                require(response.status == (201 if mint else 200), "verification_status")
                require(response.headers.get_content_type() == "application/json"
                        and response.headers.get("Content-Encoding", "identity") == "identity"
                        and response.headers.get_all("Link") is None, "verification_headers")
                lengths = response.headers.get_all("Content-Length")
                require(lengths is None or len(lengths) == 1 and lengths[0].isascii()
                        and lengths[0].isdigit() and int(lengths[0]) <= MAX_RESPONSE, "verification_response_size")
                raw = bytearray()
                while True:
                    require(time.monotonic() < self.deadline, "verification_deadline")
                    chunk = response.read(min(65536, MAX_RESPONSE + 1 - len(raw)))
                    if not chunk:
                        break
                    raw.extend(chunk)
                    require(len(raw) <= MAX_RESPONSE, "verification_response_size")
                require(lengths is None or len(raw) == int(lengths[0]), "verification_response_size")
                return strict_json(bytes(raw).decode("utf-8"), maximum=MAX_RESPONSE)
        except urllib.error.HTTPError as error:
            if missing and not mint and error.code == 404:
                return None
            require(False, "verification_request_failed")
        except Exception:
            # Never include provider errors, headers, URLs or credentials.
            require(False, "verification_request_failed")

    def get(self, path, token, *, missing=False):
        return self._json(path, token, missing=missing)

    def mint(self, jwt):
        return self._json(MINT, jwt, mint=True)
