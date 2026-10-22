# SPDX-License-Identifier: Apache-2.0
"""Bounded ruleset visibility experiment; no publication imports or operations."""
import base64
from contextlib import contextmanager
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

REPOSITORY = "benchristian88/atlas-connectors"
APP_ID = "5424851"
INSTALLATION_ID = "174088125"
API = "https://api.github.com"
VERSION = "2022-11-28"
PERMISSIONS = {"administration": "write", "metadata": "read"}
EXPECTED = {
    "atlas-main": [],
    "atlas-history-lock": [],
    "atlas-bootstrap-lock": [],
    "atlas-catalogue-current": [
        {"actor_id": 5422372, "actor_type": "Integration", "bypass_mode": "always"}
    ],
    "atlas-publication-tags": [
        {"actor_id": 5422372, "actor_type": "Integration", "bypass_mode": "always"}
    ],
}
BASE = f"/repos/{REPOSITORY}"
# One extra slot detects overflow even if the server omits pagination headers.
LIST_PATH = BASE + "/rulesets?includes_parents=true&per_page=6&page=1"
INSTALLATION_PATH = BASE + "/installation"
TOKEN_PATH = f"/app/installations/{INSTALLATION_ID}/access_tokens"
MAX_BYTES = 262144
FAILURE_CODES = frozenset({
    "verifier_context_failed", "verifier_configuration_failed",
    "verifier_jwt_failed", "verifier_installation_failed", "verifier_token_failed",
    "ruleset_list_failed", "ruleset_detail_failed",
    "ruleset_bypass_missing", "ruleset_bypass_mismatch", "verifier_unexpected_failed",
})


class EvidenceError(ValueError):
    """Never include remote content, headers, credentials or exception text."""


class StageFailure(EvidenceError):
    def __init__(self, code):
        super().__init__()
        self.code = code


@contextmanager
def failure_stage(code):
    """Map any stage failure to a local constant, never to exception content."""
    try:
        yield
    except Exception:
        raise StageFailure(code) from None


def require(condition):
    if not condition:
        raise EvidenceError()


def positive_id(value):
    return type(value) is int and 0 < value < 2**63


def parse_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result)
            result[key] = value
        return result

    def invalid_constant(_):
        raise EvidenceError()

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=unique,
                          parse_constant=invalid_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise EvidenceError() from None


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise EvidenceError()


class Transport:
    """Fixed host and endpoints. Only authentication may use a POST."""

    def __init__(self):
        self.opener = urllib.request.build_opener(NoRedirect())

    def _json(self, path, credential, *, mint=False):
        is_detail = re.fullmatch(
            re.escape(BASE) + r"/rulesets/[1-9][0-9]{0,18}\?includes_parents=true", path
        )
        require(path == TOKEN_PATH if mint else
                path in {LIST_PATH, INSTALLATION_PATH} or is_detail is not None)
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": VERSION,
            "User-Agent": "atlas-ruleset-visibility-experiment",
            "Accept-Encoding": "identity",
            "Authorization": "Bearer " + credential,
        }
        data = None
        if mint:
            headers["Content-Type"] = "application/json"
            data = json.dumps({"repositories": ["atlas-connectors"],
                               "permissions": PERMISSIONS}).encode()
        request = urllib.request.Request(API + path, headers=headers, data=data,
                                         method="POST" if mint else "GET")
        try:
            with self.opener.open(request, timeout=20) as response:
                require(response.status == (201 if mint else 200))
                require(response.headers.get_content_type() == "application/json")
                require(response.headers.get("Content-Encoding", "identity") == "identity")
                # This experiment accepts one complete page only. Never follow Link.
                require(response.headers.get_all("Link") is None)
                lengths = response.headers.get_all("Content-Length")
                require(lengths is None or len(lengths) == 1 and
                        lengths[0].isascii() and lengths[0].isdigit() and
                        int(lengths[0]) <= MAX_BYTES)
                raw = response.read(MAX_BYTES + 1)
                require(len(raw) <= MAX_BYTES)
                require(lengths is None or len(raw) == int(lengths[0]))
                return parse_json(raw)
        except Exception:
            # HTTP errors can carry credential-bearing requests and remote bodies.
            raise EvidenceError() from None

    def get(self, path, token):
        require(path == LIST_PATH or re.fullmatch(
            re.escape(BASE) + r"/rulesets/[1-9][0-9]{0,18}\?includes_parents=true", path
        ) is not None)
        return self._json(path, token)

    def installation(self, jwt):
        return self._json(INSTALLATION_PATH, jwt)

    def mint(self, jwt):
        return self._json(TOKEN_PATH, jwt, mint=True)


def app_jwt(private_key):
    def encode(raw):
        return base64.urlsafe_b64encode(raw).rstrip(b"=")

    now = int(time.time())
    header = encode(b'{"alg":"RS256","typ":"JWT"}')
    claims = encode(json.dumps({"iss": APP_ID, "iat": now - 60,
                                "exp": now + 300}).encode())
    message = header + b"." + claims
    # NamedTemporaryFile is mode 0600; no key material in argv or output.
    with tempfile.NamedTemporaryFile() as key:
        key.write(private_key.encode())
        key.flush()
        signature = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", key.name],
            input=message, capture_output=True, check=True, timeout=10,
        ).stdout
    return (message + b"." + encode(signature)).decode("ascii")


def authenticate(api, environ):
    with failure_stage("verifier_configuration_failed"):
        require(environ.get("VERIFICATION_APP_ID") == APP_ID)
        require(environ.get("VERIFICATION_APP_INSTALLATION_ID") == INSTALLATION_ID)
        key = environ.get("VERIFICATION_APP_PRIVATE_KEY")
        require(isinstance(key, str) and bool(key))
    with failure_stage("verifier_jwt_failed"):
        jwt = app_jwt(key)
    with failure_stage("verifier_installation_failed"):
        installation = api.installation(jwt)
        require(isinstance(installation, dict))
        require(type(installation.get("id")) is int and installation["id"] == int(INSTALLATION_ID))
        require(type(installation.get("app_id")) is int and installation["app_id"] == int(APP_ID))
        require(isinstance(installation.get("account"), dict) and
                installation["account"].get("login") == "benchristian88")
        require(installation.get("repository_selection") == "selected")
        require("suspended_at" in installation and installation["suspended_at"] is None)
    with failure_stage("verifier_token_failed"):
        result = api.mint(jwt)
        require(isinstance(result, dict) and result.get("permissions") == PERMISSIONS)
        repositories = result.get("repositories")
        require(isinstance(repositories, list) and len(repositories) == 1 and
                isinstance(repositories[0], dict) and
                repositories[0].get("full_name") == REPOSITORY)
        token = result.get("token")
        require(isinstance(token, str) and re.fullmatch(r"[A-Za-z0-9_]+", token) is not None)
    # Keep token in process memory: no outputs, artifacts, logs or revocation DELETE.
    return token


def validate_list(value):
    require(isinstance(value, list) and len(value) == len(EXPECTED))
    by_name = {}
    ids = set()
    for item in value:
        require(isinstance(item, dict))
        name, identity = item.get("name"), item.get("id")
        require(isinstance(name, str) and name in EXPECTED and name not in by_name)
        require(positive_id(identity) and identity not in ids)
        require(item.get("source_type") == "Repository" and item.get("source") == REPOSITORY)
        by_name[name] = identity
        ids.add(identity)
    return by_name


def detail_diagnostic(value, name, identity):
    with failure_stage("ruleset_detail_failed"):
        require(isinstance(value, dict))
        require(positive_id(value.get("id")) and value["id"] == identity and value.get("name") == name)
        require(value.get("source_type") == "Repository" and value.get("source") == REPOSITORY)
        require(isinstance(value.get("target"), str) and value["target"] in {"branch", "tag"})
        require(isinstance(value.get("enforcement"), str) and
                value["enforcement"] in {"active", "disabled", "evaluate"})
        require(isinstance(value.get("conditions"), dict))
        require(isinstance(value.get("rules"), list) and all(
            isinstance(rule, dict) and isinstance(rule.get("type"), str) and bool(rule["type"])
            for rule in value["rules"]))
    if "bypass_actors" not in value:
        return {"name": name, "id": identity, "bypass_actors_present": False,
                "bypass_actor_count": None, "bypass_actors": None}
    with failure_stage("ruleset_bypass_mismatch"):
        actors = value["bypass_actors"]
        require(isinstance(actors, list))
        safe_actors = []
        for actor in actors:
            require(isinstance(actor, dict))
            require(actor.get("actor_id") is None or positive_id(actor["actor_id"]))
            require(isinstance(actor.get("actor_type"), str) and actor["actor_type"] in {
                "Integration", "OrganizationAdmin", "RepositoryRole", "Team", "DeployKey", "User"})
            require(isinstance(actor.get("bypass_mode"), str) and
                    actor["bypass_mode"] in {"always", "pull_request", "exempt"})
            safe_actors.append({key: actor.get(key) for key in ("actor_id", "actor_type", "bypass_mode")})
    return {"name": name, "id": identity, "bypass_actors_present": True,
            "bypass_actor_count": len(actors), "bypass_actors": safe_actors}


def validate_detail(value, name, identity):
    diagnostic = detail_diagnostic(value, name, identity)
    # Absence must never be treated as an empty bypass list.
    with failure_stage("ruleset_bypass_missing"):
        require("bypass_actors" in value)
    with failure_stage("ruleset_bypass_mismatch"):
        require(value["bypass_actors"] == EXPECTED[name])
    return diagnostic


def experiment(api, token, emit=None):
    with failure_stage("ruleset_list_failed"):
        listed = validate_list(api.get(LIST_PATH, token))
    # Fetch and validate all five details before emitting any success output.
    details = {}
    for name in EXPECTED:
        with failure_stage("ruleset_detail_failed"):
            details[name] = api.get(BASE + f"/rulesets/{listed[name]}?includes_parents=true", token)
    diagnostics = [validate_detail(details[name], name, listed[name]) for name in EXPECTED]
    if emit is not None:
        for diagnostic in diagnostics:
            emit(diagnostic)
    return diagnostics


def main():
    try:
        with failure_stage("verifier_context_failed"):
            require(os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch")
            require(os.environ.get("GITHUB_REF") == "refs/heads/main")
            require(os.environ.get("GITHUB_REPOSITORY") == REPOSITORY)
        api = Transport()
        token = authenticate(api, os.environ)
        experiment(api, token, emit=lambda diagnostic: print(
            json.dumps(diagnostic, separators=(",", ":"))))
    except Exception as error:
        # Only local allowlisted codes reach stderr, never exception text/args.
        code = error.code if isinstance(error, StageFailure) else None
        if type(code) is not str or code not in FAILURE_CODES:
            code = "verifier_unexpected_failed"
        print(code, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
