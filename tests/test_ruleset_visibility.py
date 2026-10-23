# SPDX-License-Identifier: Apache-2.0
"""Offline experiment tests: no Git operations, live credentials or network."""
import base64
from copy import deepcopy
from email.message import Message
import io
import json
from pathlib import Path
import subprocess
import sys
import urllib.error

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "tests/fixtures/historical_workflows/ruleset-visibility-experiment.yml"
sys.path.insert(0, str(ROOT / "tools"))
import ruleset_visibility as visibility

# Synthetic opaque examples only; no real credentials or embedded JWT claims.
STATELESS_TOKEN = "ghs_5424851_" + "a_-" * 40 + "." + "b_-" * 100 + "." + "c_-" * 28 + "c_"
ACCEPTED_TOKENS = [
    pytest.param("ghs_" + "a" * 36, id="legacy"),
    pytest.param(STATELESS_TOKEN, id="stateless-520-characters"),
    pytest.param("opaque.with_more-than.two.periods/+==", id="no-jwt-structure"),
    pytest.param("opaque!punctuation:allowed", id="visible-ascii"),
    pytest.param("x", id="no-fixed-minimum"),
    pytest.param("x" * visibility.MAX_INSTALLATION_TOKEN_LENGTH, id="upper-bound"),
]


def records():
    return [dict(id=index, name=name, source_type="Repository", source=visibility.REPOSITORY,
                 target="tag" if name in {"atlas-bootstrap-lock", "atlas-publication-tags"} else "branch",
                 enforcement="active", conditions={}, rules=[], bypass_actors=deepcopy(actors))
            for index, (name, actors) in enumerate(visibility.EXPECTED.items(), 1)]


class FakeAPI:
    def __init__(self):
        self.rules = records()
        self.calls = []

    def get(self, path, token):
        self.calls.append(path)
        if path == visibility.LIST_PATH:
            return [{key: item[key] for key in ("id", "name", "source", "source_type")}
                    for item in reversed(self.rules)]
        return deepcopy(next(item for item in self.rules
                             if path == visibility.BASE + f'/rulesets/{item["id"]}?includes_parents=true'))


def test_exact_success_fetches_every_detail_in_deterministic_order():
    api = FakeAPI()
    result = visibility.experiment(api, "synthetic-token")
    assert len(api.calls) == 6
    assert [row["name"] for row in result] == list(visibility.EXPECTED)
    assert [row["bypass_actor_count"] for row in result] == [0, 0, 0, 1, 1]
    assert all(row["bypass_actors_present"] is True for row in result)
    assert [row["bypass_actors"] for row in result] == list(visibility.EXPECTED.values())


@pytest.mark.parametrize("change", [
    lambda rows: rows.pop(),
    lambda rows: rows.append(deepcopy(rows[0])),
    lambda rows: rows.__setitem__(1, deepcopy(rows[0])),
    lambda rows: rows[1].update(id=rows[0]["id"]),
    lambda rows: rows[1].update(name=rows[0]["name"]),
    lambda rows: rows[0].update(name="unexpected"),
    lambda rows: rows[0].update(name=[]),
    lambda rows: rows[0].update(id=True),
    lambda rows: rows[0].update(id=1.0),
    lambda rows: rows[0].update(id="1"),
    lambda rows: rows[0].update(id=0),
    lambda rows: rows[0].update(id=2**63),
    lambda rows: rows[0].update(source="another/repository"),
    lambda rows: rows[0].update(source_type="Organization"),
    lambda rows: rows.__setitem__(0, None),
])
def test_list_fails_closed(change):
    rows = records()
    change(rows)
    with pytest.raises(visibility.EvidenceError):
        visibility.validate_list(rows)


@pytest.mark.parametrize("value", [None, {}, "", True, [], [1] * 6])
def test_invalid_list_shapes(value):
    with pytest.raises(visibility.EvidenceError):
        visibility.validate_list(value)


@pytest.mark.parametrize("index", range(5))
def test_every_detail_requires_explicit_bypass_actors(index):
    api = FakeAPI()
    del api.rules[index]["bypass_actors"]
    with pytest.raises(visibility.EvidenceError):
        visibility.experiment(api, "synthetic-token")
    assert len(api.calls) == 6


@pytest.mark.parametrize("change", [
    lambda row: row.update(id=99),
    lambda row: row.update(id=True),
    lambda row: row.update(name="atlas-main"),
    lambda row: row.update(source="other/repo"),
    lambda row: row.update(source_type="Organization"),
    lambda row: row.update(target=[]),
    lambda row: row.update(enforcement={}),
    lambda row: row.update(conditions=None),
    lambda row: row.update(rules=None),
    lambda row: row.update(rules=[{}]),
    lambda row: row.update(bypass_actors=None),
    lambda row: row.update(bypass_actors={}),
    lambda row: row.update(bypass_actors=[]),
    lambda row: row["bypass_actors"].append(deepcopy(row["bypass_actors"][0])),
    lambda row: row["bypass_actors"][0].update(actor_id=5424851),
    lambda row: row["bypass_actors"][0].update(actor_id=5422372.0),
    lambda row: row["bypass_actors"][0].update(actor_type="Team"),
    lambda row: row["bypass_actors"][0].update(bypass_mode="pull_request"),
    lambda row: row["bypass_actors"][0].update(extra="unknown"),
    lambda row: row["bypass_actors"][0].pop("bypass_mode"),
    lambda row: row["bypass_actors"].__setitem__(0, None),
])
def test_detail_fails_closed(change):
    row = records()[3]
    change(row)
    with pytest.raises(visibility.EvidenceError):
        visibility.validate_detail(row, "atlas-catalogue-current", 4)


@pytest.mark.parametrize("index", range(3))
def test_empty_bypass_rules_reject_any_actor(index):
    row = records()[index]
    row["bypass_actors"] = records()[3]["bypass_actors"]
    with pytest.raises(visibility.EvidenceError):
        visibility.validate_detail(row, row["name"], row["id"])


class Response(io.BytesIO):
    def __init__(self, raw=b"[]", *, status=200, headers=()):
        super().__init__(raw)
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = "application/json; charset=utf-8"
        for key, value in headers:
            self.headers[key] = value


class Opener:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def open(self, request, timeout):
        self.requests.append(request)
        assert timeout == 20
        return self.response


def client(response):
    api = visibility.Transport()
    api.opener = Opener(response)
    return api


def test_transport_get_headers_and_no_body():
    api = client(Response())
    assert api.get(visibility.LIST_PATH, "synthetic-token") == []
    request = api.opener.requests[0]
    assert request.get_method() == "GET" and request.data is None
    assert request.full_url == visibility.API + visibility.LIST_PATH
    assert request.get_header("X-github-api-version") == "2022-11-28"


def test_only_post_is_exact_scoped_token_mint():
    api = client(Response(b"{}", status=201))
    api.mint("synthetic-jwt")
    request = api.opener.requests[0]
    assert request.get_method() == "POST"
    assert request.full_url == visibility.API + visibility.TOKEN_PATH
    assert json.loads(request.data) == {
        "repositories": ["atlas-connectors"],
        "permissions": {"administration": "write", "metadata": "read"},
    }
    assert request.get_header("X-github-api-version") == "2022-11-28"


@pytest.mark.parametrize("path", ["/releases", visibility.BASE + "/git/refs",
    visibility.TOKEN_PATH, "https://evil.example", visibility.BASE + "/rulesets/1",
    visibility.LIST_PATH + "&page=2", visibility.BASE + "/rulesets/../1?includes_parents=true"])
def test_evidence_transport_rejects_unapproved_endpoints(path):
    api = client(Response())
    with pytest.raises(visibility.EvidenceError):
        api.get(path, "synthetic-token")
    assert not api.opener.requests
    with pytest.raises(visibility.EvidenceError):
        api._json(visibility.LIST_PATH, "synthetic-jwt", mint=True)


@pytest.mark.parametrize("raw,headers,status", [
    (b"[]", [("Link", '<https://api.github.com/next>; rel="next"')], 200),
    (b"[]", [("Link", "malformed")], 200),
    (b"[]", [("Link", "")], 200),
    (b"[]", [("Link", 'anything; rel="prev"')], 200),
    (b"[]", [("Content-Encoding", "gzip")], 200),
    (b"[]", [("Content-Length", "1")], 200),
    (b"[]", [("Content-Length", "9999999")], 200),
    (b"[]", [("Content-Length", "invalid")], 200),
    (b"[]", [("Content-Length", "2"), ("Content-Length", "2")], 200),
    (b"x" * (visibility.MAX_BYTES + 1), [], 200),
    (b"[]", [], 201), (b"[]", [], 302), (b"[]", [], 403),
    (b'{"id":1,"id":2}', [], 200), (b'{"nested":{"x":1,"x":2}}', [], 200),
    (b"NaN", [], 200), (b"Infinity", [], 200), (b"-Infinity", [], 200),
    (b"\xff", [], 200), (b"<html>error</html>", [], 200), (b"[", [], 200),
])
def test_response_failures_are_sanitized(raw, headers, status):
    with pytest.raises(visibility.EvidenceError) as error:
        client(Response(raw, status=status, headers=headers)).get(visibility.LIST_PATH, "synthetic-token")
    assert str(error.value) == ""


def test_redirect_never_followed():
    with pytest.raises(visibility.EvidenceError):
        visibility.NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.example")


def test_http_error_never_exposes_remote_content(capsys):
    api = client(Response())
    def fail(*args, **kwargs):
        raise urllib.error.HTTPError("https://example", 403, "sensitive-remote-content", {}, None)
    api.opener.open = fail
    with pytest.raises(visibility.EvidenceError) as error:
        api.get(visibility.LIST_PATH, "synthetic-token")
    assert str(error.value) == ""
    assert capsys.readouterr() == ("", "")


def auth_fixture(monkeypatch):
    monkeypatch.setattr(visibility, "app_jwt", lambda key: "synthetic-jwt")
    class AuthAPI:
        def __init__(self):
            self.calls = []
            self.observed = {"id": 174088125, "app_id": 5424851,
                             "account": {"login": "benchristian88"},
                             "repository_selection": "selected", "suspended_at": None}
            self.issued = {"permissions": deepcopy(visibility.PERMISSIONS), "token": "synthetic_token",
                           "repositories": [{"full_name": visibility.REPOSITORY}]}
        def installation(self, jwt):
            self.calls.append("installation")
            return self.observed
        def mint(self, jwt):
            self.calls.append("mint")
            return self.issued
    return AuthAPI(), {"VERIFICATION_APP_ID": "5424851",
                       "VERIFICATION_APP_INSTALLATION_ID": "174088125",
                       "VERIFICATION_APP_PRIVATE_KEY": "synthetic-key"}


def test_auth_identity_and_token_scope(monkeypatch):
    api, environ = auth_fixture(monkeypatch)
    assert visibility.authenticate(api, environ) == "synthetic_token"
    assert api.calls == ["installation", "mint"]


@pytest.mark.parametrize("field", ["VERIFICATION_APP_ID", "VERIFICATION_APP_INSTALLATION_ID", "VERIFICATION_APP_PRIVATE_KEY"])
def test_bad_configuration_fails_before_auth(monkeypatch, field):
    api, environ = auth_fixture(monkeypatch)
    environ[field] = ""
    with pytest.raises(visibility.StageFailure) as error:
        visibility.authenticate(api, environ)
    assert error.value.code == "verifier_configuration_failed"
    assert api.calls == []


@pytest.mark.parametrize("change", [
    lambda value: value.update(id=1), lambda value: value.update(app_id=5422372),
    lambda value: value.update(account={"login": "other"}),
    lambda value: value.update(repository_selection="all"),
    lambda value: value.update(suspended_at="now"), lambda value: value.pop("suspended_at"),
])
@pytest.mark.parametrize("token", ["ghs_" + "a" * 36, STATELESS_TOKEN], ids=["legacy", "stateless"])
def test_wrong_installation_never_mints(monkeypatch, change, token):
    api, environ = auth_fixture(monkeypatch)
    api.issued["token"] = token
    change(api.observed)
    with pytest.raises(visibility.StageFailure) as error:
        visibility.authenticate(api, environ)
    assert error.value.code == "verifier_installation_failed"
    assert api.calls == ["installation"]


@pytest.mark.parametrize("change,code", [
    (lambda value: value["permissions"].update(contents="write"), "verifier_token_permissions_mismatch"),
    (lambda value: value["permissions"].update(administration="read"), "verifier_token_permissions_mismatch"),
    (lambda value: value.update(repositories=[]), "verifier_token_repositories_mismatch"),
    (lambda value: value["repositories"].append({"full_name": "other/repo"}), "verifier_token_repositories_mismatch"),
    (lambda value: value["repositories"][0].update(full_name="other/repo"), "verifier_token_repositories_mismatch"),
    (lambda value: value.update(token="bad\ntoken"), "verifier_token_value_invalid"),
    (lambda value: value.update(token=None), "verifier_token_value_invalid"),
])
@pytest.mark.parametrize("token", ["ghs_" + "a" * 36, STATELESS_TOKEN], ids=["legacy", "stateless"])
def test_bad_token_evidence_rejected(monkeypatch, change, code, token):
    api, environ = auth_fixture(monkeypatch)
    api.issued["token"] = token
    change(api.issued)
    with pytest.raises(visibility.StageFailure) as error:
        visibility.authenticate(api, environ)
    assert error.value.code == code


def test_jwt_has_expected_identity_lifetime_and_valid_signature(tmp_path, monkeypatch):
    # Generate an ephemeral test-only key; never store fixtures or use credentials.
    key = subprocess.run(["openssl", "genrsa", "2048"], capture_output=True, check=True).stdout
    monkeypatch.setattr(visibility.time, "time", lambda: 1000)
    jwt = visibility.app_jwt(key.decode())
    header, payload, signature = jwt.split(".")
    decode = lambda value: base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    assert json.loads(decode(header)) == {"alg": "RS256", "typ": "JWT"}
    assert json.loads(decode(payload)) == {"iss": "5424851", "iat": 940, "exp": 1300}
    public = subprocess.run(["openssl", "rsa", "-pubout"], input=key, capture_output=True, check=True).stdout
    (tmp_path / "public.pem").write_bytes(public)
    (tmp_path / "signature").write_bytes(decode(signature))
    subprocess.run(["openssl", "dgst", "-sha256", "-verify", str(tmp_path / "public.pem"),
                    "-signature", str(tmp_path / "signature")], input=f"{header}.{payload}".encode(),
                   capture_output=True, check=True)


def context(monkeypatch):
    for key, value in {"GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/main",
                       "GITHUB_REPOSITORY": visibility.REPOSITORY}.items():
        monkeypatch.setenv(key, value)


def test_cli_safe_exact_output(monkeypatch, capsys):
    context(monkeypatch)
    monkeypatch.setattr(visibility, "Transport", FakeAPI)
    monkeypatch.setattr(visibility, "authenticate", lambda *args: "synthetic-token")
    assert visibility.main() == 0
    out, err = capsys.readouterr()
    assert not err
    assert out == (
        '{"name":"atlas-main","id":1,"bypass_actors_present":true,"bypass_actor_count":0,"bypass_actors":[]}\n'
        '{"name":"atlas-history-lock","id":2,"bypass_actors_present":true,"bypass_actor_count":0,"bypass_actors":[]}\n'
        '{"name":"atlas-bootstrap-lock","id":3,"bypass_actors_present":true,"bypass_actor_count":0,"bypass_actors":[]}\n'
        '{"name":"atlas-catalogue-current","id":4,"bypass_actors_present":true,"bypass_actor_count":1,"bypass_actors":[{"actor_id":5422372,"actor_type":"Integration","bypass_mode":"always"}]}\n'
        '{"name":"atlas-publication-tags","id":5,"bypass_actors_present":true,"bypass_actor_count":1,"bypass_actors":[{"actor_id":5422372,"actor_type":"Integration","bypass_mode":"always"}]}\n'
    )
    assert "synthetic" not in out


def test_cli_suppresses_even_unexpected_exception_details(monkeypatch, capsys):
    context(monkeypatch)
    def fail(*args):
        raise RuntimeError("synthetic-sensitive-error")
    monkeypatch.setattr(visibility, "authenticate", fail)
    assert visibility.main() == 1
    assert capsys.readouterr() == ("", "verifier_unexpected_failed\n")


@pytest.mark.parametrize("index", range(5))
def test_missing_bypass_has_only_safe_code(monkeypatch, capsys, index):
    context(monkeypatch)
    api = FakeAPI()
    del api.rules[index]["bypass_actors"]
    monkeypatch.setattr(visibility, "Transport", lambda: api)
    monkeypatch.setattr(visibility, "authenticate", lambda *args: "synthetic-token")
    assert visibility.main() == 1
    assert capsys.readouterr() == ("", "ruleset_bypass_missing\n")


def test_unexpected_actor_diagnostic_excludes_untrusted_extra_fields(monkeypatch, capsys):
    context(monkeypatch)
    api = FakeAPI()
    api.rules[3]["bypass_actors"][0].update(actor_id=99, extra="synthetic-sensitive-content")
    monkeypatch.setattr(visibility, "Transport", lambda: api)
    monkeypatch.setattr(visibility, "authenticate", lambda *args: "synthetic-token")
    assert visibility.main() == 1
    assert capsys.readouterr() == ("", "ruleset_bypass_mismatch\n")


def test_untrusted_actor_strings_never_reach_logs(monkeypatch, capsys):
    context(monkeypatch)
    api = FakeAPI()
    api.rules[3]["bypass_actors"][0]["actor_type"] = "::error::synthetic-sensitive-content"
    monkeypatch.setattr(visibility, "Transport", lambda: api)
    monkeypatch.setattr(visibility, "authenticate", lambda *args: "synthetic-token")
    assert visibility.main() == 1
    assert capsys.readouterr() == ("", "ruleset_bypass_mismatch\n")


@pytest.mark.parametrize("key,value", [("GITHUB_REF", "refs/heads/dev"),
    ("GITHUB_REF", "refs/tags/main"), ("GITHUB_EVENT_NAME", "push"), ("GITHUB_REPOSITORY", "fork/repo")])
def test_cli_rejects_wrong_context_before_credentials(monkeypatch, capsys, key, value):
    context(monkeypatch)
    monkeypatch.setenv(key, value)
    monkeypatch.setattr(visibility, "authenticate", lambda *args: pytest.fail("must not authenticate"))
    assert visibility.main() == 1
    assert capsys.readouterr() == ("", "verifier_context_failed\n")


def pipeline(monkeypatch):
    """Exercise real authentication/transport/validation using offline responses."""
    context(monkeypatch)
    auth, environ = auth_fixture(monkeypatch)
    for key, value in environ.items():
        monkeypatch.setenv(key, value)
    rows = records()
    responses = [auth.observed, auth.issued, rows, *deepcopy(rows)]
    api = visibility.Transport()
    calls = []

    def open_response(request, timeout):
        index = len(calls)
        calls.append(request)
        response = responses[index]
        if isinstance(response, Exception):
            raise response
        if isinstance(response, Response):
            return response
        return Response(json.dumps(response).encode(), status=201 if index == 1 else 200)

    monkeypatch.setattr(api.opener, "open", open_response)
    monkeypatch.setattr(visibility, "Transport", lambda: api)
    return responses, calls


@pytest.mark.parametrize("index,code", [
    (0, "verifier_installation_failed"), (1, "verifier_token_request_failed"),
    (2, "ruleset_list_failed"),
    *[(index, "ruleset_detail_failed") for index in range(3, 8)],
])
@pytest.mark.parametrize("kind", ["http", "body", "unexpected"])
def test_each_retrieval_failure_emits_only_stage_code(monkeypatch, capsys, index, code, kind):
    responses, calls = pipeline(monkeypatch)
    sensitive = "synthetic-private-key synthetic-token Authorization: Bearer synthetic-secret"
    if kind == "http":
        responses[index] = urllib.error.HTTPError(
            "https://example/" + sensitive, 403, sensitive,
            {"Authorization": sensitive}, io.BytesIO(sensitive.encode()))
    elif kind == "body":
        responses[index] = Response(sensitive.encode(), status=201 if index == 1 else 200)
        if index == 1:
            code = "verifier_token_response_invalid"
    else:
        responses[index] = RuntimeError(sensitive)
    assert visibility.main() == 1
    assert capsys.readouterr() == ("", code + "\n")
    assert len(calls) == index + 1


@pytest.mark.parametrize("index,change,code", [
    (0, lambda value: value.update(app_id=5422372), "verifier_installation_failed"),
    (0, lambda value: value.update(repository_selection="all"), "verifier_installation_failed"),
    (1, lambda value: value["permissions"].update(contents="write"), "verifier_token_permissions_mismatch"),
    (1, lambda value: value.update(repositories=[]), "verifier_token_repositories_mismatch"),
    (2, lambda value: value.pop(), "ruleset_list_failed"),
    (2, lambda value: value.append(deepcopy(value[0])), "ruleset_list_failed"),
    (2, lambda value: value.__setitem__(1, deepcopy(value[0])), "ruleset_list_failed"),
    *[(index, lambda value: value.update(id=999), "ruleset_detail_failed") for index in range(3, 8)],
    *[(index, lambda value: value.update(bypass_actors=None), "ruleset_bypass_mismatch") for index in range(3, 8)],
    (6, lambda value: value.update(bypass_actors=[]), "ruleset_bypass_mismatch"),
    (6, lambda value: value["bypass_actors"][0].update(bypass_mode="pull_request"), "ruleset_bypass_mismatch"),
])
def test_validation_failures_emit_only_stage_code(monkeypatch, capsys, index, change, code):
    responses, _ = pipeline(monkeypatch)
    change(responses[index])
    assert visibility.main() == 1
    assert capsys.readouterr() == ("", code + "\n")


def test_configuration_failure_emits_only_code_before_network(monkeypatch, capsys):
    _, calls = pipeline(monkeypatch)
    monkeypatch.setenv("VERIFICATION_APP_ID", "synthetic-sensitive-config")
    assert visibility.main() == 1
    assert capsys.readouterr() == ("", "verifier_configuration_failed\n")
    assert not calls


def test_jwt_subprocess_failure_never_logs_captured_output(monkeypatch, capsys):
    real_jwt = visibility.app_jwt
    _, calls = pipeline(monkeypatch)
    monkeypatch.setattr(visibility, "app_jwt", real_jwt)
    def fail(command, **kwargs):
        assert kwargs["capture_output"] is True
        raise subprocess.CalledProcessError(1, command, output=b"synthetic-token",
                                            stderr=b"synthetic-private-key")
    monkeypatch.setattr(visibility.subprocess, "run", fail)
    assert visibility.main() == 1
    assert capsys.readouterr() == ("", "verifier_jwt_failed\n")
    assert not calls


@pytest.mark.parametrize("code", ["synthetic-sensitive-error", ["synthetic-sensitive-error"]])
def test_unknown_failure_codes_never_reach_logs(monkeypatch, capsys, code):
    context(monkeypatch)
    def fail(*args):
        raise visibility.StageFailure(code)
    monkeypatch.setattr(visibility, "authenticate", fail)
    assert visibility.main() == 1
    assert capsys.readouterr() == ("", "verifier_unexpected_failed\n")


@pytest.mark.parametrize("token", ACCEPTED_TOKENS)
def test_successful_pipeline_matches_documented_output(monkeypatch, capsys, token):
    responses, calls = pipeline(monkeypatch)
    responses[1]["token"] = token
    assert visibility.main() == 0
    out, err = capsys.readouterr()
    documented = (ROOT / "docs/ruleset-visibility-experiment.md").read_text()
    expected = documented.split('```text\n{"name":"atlas-main"', 1)[1].split("```", 1)[0]
    expected = '{"name":"atlas-main"' + expected
    for index, name in enumerate(("MAIN", "HISTORY", "BOOTSTRAP", "CURRENT", "TAGS"), 1):
        expected = expected.replace("<" + name + "_ID>", str(index))
    assert out == expected and err == ""
    assert [request.get_method() for request in calls] == ["GET", "POST"] + ["GET"] * 6
    # Every evidence GET carries the exact opaque bytes, without trimming,
    # truncation, JWT parsing, or format-dependent redaction/logging.
    assert all(request.get_header("Authorization") == "Bearer " + token for request in calls[2:])


def test_stateless_fixture_is_representative():
    assert len(STATELESS_TOKEN) == 520
    assert all(character in STATELESS_TOKEN for character in "._-")


@pytest.mark.parametrize("token", [
    pytest.param("", id="empty"), pytest.param(None, id="null"),
    pytest.param(True, id="boolean"), pytest.param(123, id="integer"),
    pytest.param(1.5, id="float"), pytest.param([], id="array"),
    pytest.param({}, id="object"),
    pytest.param("x" * (visibility.MAX_INSTALLATION_TOKEN_LENGTH + 1), id="oversized"),
    pytest.param("prefix\r\nAuthorization: Bearer synthetic-secret", id="header-injection"),
    *[pytest.param("prefix" + chr(code) + "suffix", id=f"control-{code}")
      for code in [*range(33), *range(127, 160)]],
    *[pytest.param("prefix" + character + "suffix", id=f"unicode-{ord(character)}")
      for character in ("\u00a0", "\u200b", "\u2028", "\u2029", "\u3000", "é", "🔑", "\ud800")],
    pytest.param(" leading", id="leading-space"),
    pytest.param("trailing ", id="trailing-space"),
])
def test_unsafe_token_emits_only_code_and_never_reaches_evidence_gets(monkeypatch, capsys, token):
    responses, calls = pipeline(monkeypatch)
    responses[1]["token"] = token
    assert visibility.main() == 1
    assert capsys.readouterr() == ("", "verifier_token_value_invalid\n")
    assert [request.get_method() for request in calls] == ["GET", "POST"]


@pytest.mark.parametrize("change,code", [
    (lambda value: value.pop("permissions"), "verifier_token_response_invalid"),
    (lambda value: value.update(permissions=None), "verifier_token_response_invalid"),
    (lambda value: value.update(permissions=[]), "verifier_token_response_invalid"),
    (lambda value: value.update(permissions="synthetic-secret"), "verifier_token_response_invalid"),
    (lambda value: value.update(permissions={}), "verifier_token_permissions_mismatch"),
    (lambda value: value["permissions"].pop("metadata"), "verifier_token_permissions_mismatch"),
    (lambda value: value["permissions"].update(administration="synthetic-secret"), "verifier_token_permissions_mismatch"),
    (lambda value: value.pop("repositories"), "verifier_token_repositories_missing"),
    (lambda value: value.update(repositories=None), "verifier_token_response_invalid"),
    (lambda value: value.update(repositories={}), "verifier_token_response_invalid"),
    (lambda value: value.update(repositories="synthetic-secret"), "verifier_token_response_invalid"),
    (lambda value: value.update(repositories=[None]), "verifier_token_response_invalid"),
    (lambda value: value.update(repositories=[{}]), "verifier_token_response_invalid"),
    (lambda value: value.update(repositories=[{"full_name": 123}]), "verifier_token_response_invalid"),
    (lambda value: value.update(repositories=[]), "verifier_token_repositories_mismatch"),
    (lambda value: value["repositories"].append(deepcopy(value["repositories"][0])), "verifier_token_repositories_mismatch"),
    (lambda value: value["repositories"][0].update(full_name="synthetic-secret"), "verifier_token_repositories_mismatch"),
    (lambda value: value.pop("token"), "verifier_token_value_invalid"),
])
@pytest.mark.parametrize("token", ["ghs_" + "a" * 36, STATELESS_TOKEN], ids=["legacy", "stateless"])
def test_token_contract_failures_have_precise_codes(monkeypatch, capsys, change, code, token):
    responses, calls = pipeline(monkeypatch)
    responses[1]["token"] = token
    change(responses[1])
    assert visibility.main() == 1
    assert capsys.readouterr() == ("", code + "\n")
    assert len(calls) == 2


@pytest.mark.parametrize("raw", [
    b"null", b"[]", b"true", b"123", b'"synthetic-secret"',
    b"{", b"\xff", b"NaN", b'{"token":"synthetic-secret","token":"another-secret"}',
])
def test_invalid_mint_json_has_response_code(monkeypatch, capsys, raw):
    responses, calls = pipeline(monkeypatch)
    responses[1] = Response(raw, status=201)
    assert visibility.main() == 1
    assert capsys.readouterr() == ("", "verifier_token_response_invalid\n")
    assert len(calls) == 2


@pytest.mark.parametrize("status", [200, 202, 301, 302, 307, 401, 403, 422, 429, 500])
def test_non_created_mint_response_is_request_failure(monkeypatch, capsys, status):
    responses, calls = pipeline(monkeypatch)
    responses[1] = Response(b"synthetic-secret", status=status)
    assert visibility.main() == 1
    assert capsys.readouterr() == ("", "verifier_token_request_failed\n")
    assert len(calls) == 2


@pytest.mark.parametrize("headers,raw", [
    ([("Content-Type", "text/html")], b"synthetic-secret"),
    ([("Content-Encoding", "gzip")], b"synthetic-secret"),
    ([("Link", "https://example/synthetic-secret")], b"{}"),
    ([("Link", "")], b"{}"),
    ([("Content-Length", "synthetic-secret")], b"{}"),
    ([("Content-Length", str(visibility.MAX_BYTES + 1))], b"{}"),
    ([("Content-Length", "1")], b"{}"),
    ([("Content-Length", "3")], b"{}"),
    ([("Content-Length", "2"), ("Content-Length", "2")], b"{}"),
    ([], b"x" * (visibility.MAX_BYTES + 1)),
])
def test_mint_header_and_size_rejections_are_distinct(monkeypatch, capsys, headers, raw):
    responses, calls = pipeline(monkeypatch)
    response = Response(raw, status=201)
    for key, value in headers:
        if key == "Content-Type":
            response.headers.replace_header(key, value)
        else:
            response.headers[key] = value
    responses[1] = response
    assert visibility.main() == 1
    assert capsys.readouterr() == ("", "verifier_token_response_rejected\n")
    assert len(calls) == 2


def test_mint_body_read_failure_is_request_failure(monkeypatch, capsys):
    responses, calls = pipeline(monkeypatch)
    response = Response(b"", status=201)
    def fail(*args):
        raise OSError("synthetic-secret Authorization: Bearer synthetic-token")
    response.read = fail
    responses[1] = response
    assert visibility.main() == 1
    assert capsys.readouterr() == ("", "verifier_token_request_failed\n")
    assert len(calls) == 2


def test_workflow_contract():
    path = WORKFLOW
    # BaseLoader preserves YAML's 'on' key (SafeLoader interprets YAML 1.1 booleans).
    workflow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
    assert workflow["on"] == {"workflow_dispatch": ""}
    assert workflow["permissions"] == {"contents": "read"}
    job = workflow["jobs"]["verify"]
    assert job["if"] == "github.repository == 'benchristian88/atlas-connectors' && github.ref == 'refs/heads/main'"
    assert job["environment"] == "catalogue-verification"
    assert len(job["steps"]) == 2
    assert all("uses" not in step for step in job["steps"])
    fetch, run = job["steps"]
    assert fetch["env"] == {"SOURCE_TOKEN": "${{ github.token }}"}
    assert run["env"] == {
        "VERIFICATION_APP_ID": "${{ vars.VERIFICATION_APP_ID }}",
        "VERIFICATION_APP_INSTALLATION_ID": "${{ vars.VERIFICATION_APP_INSTALLATION_ID }}",
        "VERIFICATION_APP_PRIVATE_KEY": "${{ secrets.VERIFICATION_APP_PRIVATE_KEY }}",
    }
    assert run["run"] == 'python3 "$RUNNER_TEMP/ruleset_visibility.py"'
    assert "2022-11-28" in fetch["run"] and "GITHUB_SHA" in fetch["run"]
    assert "method='GET'" in fetch["run"]


@pytest.mark.parametrize("failure", [None, "sha", "status", "link", "size", "redirect"])
def test_workflow_helper_download_is_pinned_get_and_silent_on_failure(monkeypatch, tmp_path, capsys, failure):
    workflow = yaml.load(WORKFLOW.read_text(),
                         Loader=yaml.BaseLoader)
    shell = workflow["jobs"]["verify"]["steps"][0]["run"]
    source = shell.split("\n", 1)[1].rsplit("\nPY", 1)[0]
    monkeypatch.setenv("GITHUB_SHA", "bad" if failure == "sha" else "a" * 40)
    monkeypatch.setenv("SOURCE_TOKEN", "synthetic-token")
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path))
    opener = Opener(Response(b"x" * 65537 if failure == "size" else b"# helper\n",
                            status=403 if failure == "status" else 200,
                            headers=[("Link", "ambiguous")] if failure == "link" else []))
    def build(handler):
        if failure == "redirect":
            handler.redirect_request(None, None, 302, "", {}, "https://evil.example")
        return opener
    monkeypatch.setattr(visibility.urllib.request, "build_opener", build)
    if failure:
        with pytest.raises(SystemExit) as error:
            exec(compile(source, "workflow-bootstrap", "exec"), {})
        assert error.value.code == 1
        assert not (tmp_path / "ruleset_visibility.py").exists()
    else:
        exec(compile(source, "workflow-bootstrap", "exec"), {})
        assert (tmp_path / "ruleset_visibility.py").read_bytes() == b"# helper\n"
        request = opener.requests[0]
        assert request.get_method() == "GET" and request.data is None
        assert request.full_url == (visibility.API + visibility.BASE +
                                    "/contents/tools/ruleset_visibility.py?ref=" + "a" * 40)
        assert request.get_header("X-github-api-version") == "2022-11-28"
    assert capsys.readouterr() == ("", "")
