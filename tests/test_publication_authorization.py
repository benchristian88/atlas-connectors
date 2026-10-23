# SPDX-License-Identifier: Apache-2.0
"""Lean V2 deterministic tests. API and positive signer observations are synthetic."""
import base64
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import issue_publication_authorization as issuer
import publication_authorization as auth
from publication_contract import REPOSITORY, canonical_json, digest
from test_publication_contract import authority_fixture, rules_fixture
from verification_github import BASE, INSTALLATION, LIST, PERMISSIONS

SOURCE, REVISION = "a" * 40, "b" * 40
NOW = 1800000000


def file_response(raw, path):
    return {"type": "file", "path": path, "encoding": "base64", "size": len(raw),
            "content": base64.b64encode(raw).decode()}


class SyntheticProvider:
    def __init__(self, rows):
        self.rows, self.calls = rows, []
    def get(self, path, token, *, missing=False):
        assert token in {"synthetic-jwt", "synthetic-installation-token"}
        self.calls.append(("GET", path, token))
        assert path in self.rows, path
        return deepcopy(self.rows[path])
    def mint(self, jwt):
        assert jwt == "synthetic-jwt"
        self.calls.append(("POST", "mint", jwt))
        return deepcopy(self.rows["mint"])


def fixture(operation="bootstrap"):
    policy, repo, branch, environment, run, attempt, workflow, user, checks = authority_fixture()
    policy.update(allowed_maintainer_id=93822871, app_id=5422372, app_installation_id=174027755,
        app_slug="atlas-catalogue-publisher", app_bot_user_id=346232650, bootstrap_operation="stage")
    policy["bootstrap"] = {"sequence": None, "pointer_sha256": None} if operation == "bootstrap" else {
        "sequence": 1, "pointer_sha256": "2" * 64}
    user.update(id=93822871, login="benchristian88")
    for observed in (run, attempt):
        observed.update(actor=deepcopy(user), triggering_actor=deepcopy(user))
    run["referenced_workflows"] = [{"path": REPOSITORY + "/" + auth.WORKFLOW + "@" + REVISION, "sha": REVISION}]
    rules = rules_fixture()
    rules.append({"id": 5, "name": "atlas-bootstrap-lock", "target": "tag", "enforcement": "active",
        "conditions": {"ref_name": {"include": ["refs/tags/catalogue-bootstrap-root"], "exclude": []}},
        "bypass_actors": [], "rules": [{"type": "update"}, {"type": "deletion"}]})
    for row in rules:
        row.update(source_type="Repository", source=REPOSITORY)
        for bypass in row["bypass_actors"]:
            bypass["actor_id"] = 5422372
    trust = {"schema": "atlas-publication-verifier-trust/v2", "live_signer_accepted": True,
        "signer_revision": REVISION, "ruleset_ids": {r["name"]: r["id"] for r in rules},
        "verification_environment_id": 123, "max_observation_age_seconds": 900}
    policy_raw = canonical_json(policy)
    request = {"source_commit": SOURCE, "policy_sha256": digest(policy_raw), "run_id": 60,
        "run_attempt": 1, "operation": operation, "acceptance_only": False}
    env = {"GITHUB_REPOSITORY": REPOSITORY, "GITHUB_REPOSITORY_ID": "1414494920",
        "GITHUB_REPOSITORY_OWNER_ID": "93822871", "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REF": "refs/heads/main", "GITHUB_SHA": SOURCE, "GITHUB_RUN_ID": "60", "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_WORKFLOW_REF": REPOSITORY + "/" + auth.PUBLICATION_WORKFLOW + "@refs/heads/main",
        "RUNNER_ENVIRONMENT": "github-hosted", "VERIFIER_REVISION": REVISION,
        "VERIFIER_WORKFLOW_REF": REPOSITORY + "/" + auth.WORKFLOW + "@" + REVISION,
        "DISPATCH_OPERATION": operation, "DISPATCH_ACCEPTANCE_ONLY": "false", "PUBLICATION_OPERATION": operation,
        "ATLAS_IMPLEMENTATION_REVISION": REVISION, "VERIFICATION_APP_ID": "5424851",
        "VERIFICATION_APP_INSTALLATION_ID": "174088125", "VERIFICATION_APP_PRIVATE_KEY": "synthetic-key"}
    from publication_contract import APP_PERMISSIONS
    rows = {BASE: repo, BASE + "/branches/main": branch,
        BASE + "/environments/catalogue-publication": environment,
        BASE + "/actions/runs/60": run, BASE + "/actions/runs/60/attempts/1": attempt,
        BASE + "/actions/workflows/80": workflow, "/users/benchristian88": user,
        BASE + f"/commits/{SOURCE}/check-runs?check_name=validate&filter=latest&per_page=2&page=1": checks,
        BASE + "/contents/catalogue/publication/policy.json?ref=" + SOURCE:
            file_response(policy_raw, "catalogue/publication/policy.json"),
        "/app": {"id": 5424851, "owner": {"id": 93822871, "login": "benchristian88"}, "permissions": PERMISSIONS},
        INSTALLATION: {"id": 174088125, "app_id": 5424851, "account": {"id": 93822871, "login": "benchristian88"},
            "repository_selection": "selected", "suspended_at": None, "permissions": PERMISSIONS},
        "mint": {"permissions": PERMISSIONS, "token": "synthetic-installation-token"},
        "/installation/repositories?per_page=2&page=1": {"total_count": 1, "repositories": [repo]},
        "/apps/atlas-catalogue-publisher": {"id": 5422372, "slug": policy["app_slug"],
            "owner": {"id": 93822871}, "permissions": deepcopy(APP_PERMISSIONS)},
        BASE + "/environments/catalogue-verification": {**environment, "id": 123, "name": "catalogue-verification"},
        BASE + "/immutable-releases": {"enabled": True}, LIST: rules}
    for row in rules:
        rows[BASE + f"/rulesets/{row['id']}?includes_parents=true"] = row
    return SyntheticProvider(deepcopy(rows)), env, request, trust, policy_raw


@pytest.fixture(autouse=True)
def synthetic_jwt(monkeypatch):
    monkeypatch.setattr(issuer, "app_jwt", lambda key: "synthetic-jwt")


def issue_fixture(data):
    api, env, request, trust, policy = data
    return issuer.issue(api, deepcopy(env), request["operation"], trust,
        acceptance_only=request["acceptance_only"], clock=lambda: NOW)


@pytest.mark.parametrize("operation", ["bootstrap", "publish", "recover"])
def test_each_operation_has_one_complete_run_preflight_and_no_draft_claim(operation):
    data = fixture(operation)
    raw = issue_fixture(data)
    value = auth.parse(raw, auth.MAX_AUTHORIZATION_BYTES)
    assert auth.check_authorization(value, data[3], json.loads(data[4])) == data[2]
    assert value["freshness"]["expires_at"] == NOW + 900
    assert set(value["rulesets"]["ids"]) == set(auth.EXPECTED)
    assert "target" not in value and "transition" not in value["execution"] and "challenge" not in value["execution"]
    assert all("/releases" not in path and "/git/" not in path for method, path, token in data[0].calls)
    assert b"synthetic-key" not in raw and b"synthetic-installation-token" not in raw


@pytest.mark.parametrize("field", ["GITHUB_REPOSITORY", "GITHUB_REPOSITORY_ID", "GITHUB_REPOSITORY_OWNER_ID",
    "GITHUB_EVENT_NAME", "GITHUB_REF", "GITHUB_SHA", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_WORKFLOW_REF",
    "RUNNER_ENVIRONMENT", "VERIFIER_REVISION", "VERIFIER_WORKFLOW_REF", "DISPATCH_OPERATION", "DISPATCH_ACCEPTANCE_ONLY"])
def test_bad_context_never_reaches_credentials(field):
    data = fixture()
    data[1][field] = "wrong"
    with pytest.raises(ValueError):
        issue_fixture(data)
    assert data[0].calls == []


@pytest.mark.parametrize("path,change", [
    (BASE, lambda x: x.update(id=7)),
    (BASE + "/branches/main", lambda x: x.update(protected=False)),
    (BASE + "/branches/main", lambda x: x["commit"].update(sha="c" * 40)),
    (BASE + "/actions/runs/60", lambda x: x.update(event="push")),
    (BASE + "/actions/runs/60", lambda x: x.update(run_attempt=2)),
    (BASE + "/actions/runs/60", lambda x: x["actor"].update(id=7)),
    (BASE + "/actions/runs/60/attempts/1", lambda x: x["triggering_actor"].update(type="Bot")),
    (BASE + "/actions/runs/60", lambda x: x["referenced_workflows"][0].update(sha=SOURCE)),
    (BASE + "/actions/workflows/80", lambda x: x.update(path=".github/workflows/other.yml")),
    (BASE + "/environments/catalogue-publication", lambda x: x.update(can_admins_bypass=True)),
    (BASE + "/environments/catalogue-publication", lambda x: x.update(protection_rules=[{"type": "required_reviewers"}])),
    (BASE + "/environments/catalogue-verification", lambda x: x.update(id=999)),
    (BASE + "/immutable-releases", lambda x: x.update(enabled=False)),
    (BASE + f"/commits/{SOURCE}/check-runs?check_name=validate&filter=latest&per_page=2&page=1",
        lambda x: x["check_runs"][0].update(conclusion="failure")),
    ("/app", lambda x: x["permissions"].update(contents="write")),
    (INSTALLATION, lambda x: x.update(suspended_at="now")),
    ("mint", lambda x: x["permissions"].update(administration="read")),
    ("/installation/repositories?per_page=2&page=1", lambda x: x.update(total_count=2)),
])
def test_incomplete_or_unexpected_independent_security_state_is_rejected(path, change):
    data = fixture()
    change(data[0].rows[path])
    with pytest.raises(ValueError):
        issue_fixture(data)


@pytest.mark.parametrize("index", range(1, 6))
@pytest.mark.parametrize("change", [lambda x: x.pop("bypass_actors"),
    lambda x: x.update(bypass_actors=[{"actor_id": 5424851, "actor_type": "Integration", "bypass_mode": "always"}]),
    lambda x: x.update(enforcement="disabled"), lambda x: x.update(source="other/repository")])
def test_all_five_rulesets_require_exact_complete_bypass_evidence(index, change):
    data = fixture()
    change(data[0].rows[BASE + f"/rulesets/{index}?includes_parents=true"])
    with pytest.raises(ValueError):
        issue_fixture(data)


@pytest.mark.parametrize("change", [lambda x: x.pop(), lambda x: x.append(deepcopy(x[0])),
    lambda x: x[0].update(id=999)])
def test_incomplete_or_changed_ruleset_inventory_blocks_issuance(change):
    data = fixture()
    change(data[0].rows[LIST])
    with pytest.raises(ValueError):
        issue_fixture(data)


def verified(monkeypatch, data, *, clock=lambda: NOW, expected=None, raw=None, started_at=None):
    from authorization_sigstore import AuthorizationSigstore
    monkeypatch.setattr(AuthorizationSigstore, "verify", lambda *args, **kwargs: "synthetic-verification")
    return auth.AuthorizationVerifier(data[3], data[4]).verify(raw or issue_fixture(data), b"synthetic-bundle",
        expected or data[2], clock=clock, started_at=started_at)


@pytest.mark.parametrize("field,value", [("source_commit", "c" * 40), ("policy_sha256", "c" * 64),
    ("run_id", 61), ("run_attempt", 2), ("operation", "publish"), ("acceptance_only", True)])
def test_signed_run_context_cannot_be_reused(monkeypatch, field, value):
    data = fixture()
    with pytest.raises(ValueError):
        verified(monkeypatch, data, expected={**data[2], field: value})


def test_changed_actual_policy_bytes_are_rejected(monkeypatch):
    data = fixture()
    raw = issue_fixture(data)
    data = (*data[:4], data[4] + b" ")
    with pytest.raises(ValueError, match="policy_digest"):
        verified(monkeypatch, data, raw=raw)


@pytest.mark.parametrize("now", [NOW - 1, NOW + 900, NOW + 901])
def test_stale_or_future_preflight_cannot_admit_a_new_job(monkeypatch, now):
    with pytest.raises(ValueError, match="not_fresh"):
        verified(monkeypatch, fixture(), clock=lambda: now)


def test_verification_crossing_expiry_rejects_startup(monkeypatch):
    clock = iter([NOW + 899, NOW + 900])
    with pytest.raises(ValueError, match="not_fresh"):
        verified(monkeypatch, fixture(), clock=lambda: next(clock))


def test_started_job_can_finish_after_startup_window_but_not_run_deadline(monkeypatch):
    verified(monkeypatch, fixture(), clock=lambda: NOW + 1200, started_at=NOW + 100)
    with pytest.raises(ValueError, match="not_fresh"):
        verified(monkeypatch, fixture(), clock=lambda: NOW + 1901, started_at=NOW + 100)
    with pytest.raises(ValueError, match="not_fresh"):
        verified(monkeypatch, fixture(), clock=lambda: NOW + 1200, started_at=NOW + 901)


@pytest.mark.parametrize("raw", [b"{}", b"[]", b"{}\n ", b'{"a":1,"a":1}', b"NaN", b"\xff", b"\xff\xfe{\0}\0"])
def test_noncanonical_or_old_transition_contracts_fail(raw):
    with pytest.raises((ValueError, UnicodeError)):
        auth.parse(raw, auth.MAX_REQUEST_BYTES)


def test_v1_transition_paths_are_removed():
    assert not hasattr(auth, "TARGET_FIELDS") and not hasattr(auth, "OPERATIONS")
    assert not hasattr(issuer, "observe_target") and not hasattr(auth.AuthorizationVerifier, "verify_and_consume")
    with pytest.raises(ValueError):
        auth.check_request({**fixture()[2], "transition": "stage-create-draft", "target": {}, "challenge": "e" * 64})


def test_acceptance_only_evidence_is_signed_but_never_admits_publication(monkeypatch):
    data = fixture()
    data[3]["live_signer_accepted"] = False
    data[2]["acceptance_only"] = True
    data[1]["DISPATCH_ACCEPTANCE_ONLY"] = "true"
    raw = issue_fixture(data)
    assert json.loads(raw)["execution"]["acceptance_only"] is True
    with pytest.raises(ValueError, match="live_acceptance"):
        auth.AuthorizationVerifier(data[3], data[4])
    data[3]["live_signer_accepted"] = True
    with pytest.raises(ValueError, match="context_mismatch"):
        verified(monkeypatch, data, raw=raw, expected={**data[2], "acceptance_only": False})


@pytest.mark.parametrize("operation", ["bootstrap", "publish", "recover"])
def test_job_local_startup_receipt_is_not_a_cross_run_or_cross_operation_grant(monkeypatch, tmp_path, operation):
    from authorization_sigstore import AuthorizationSigstore
    data = fixture(operation)
    raw = issue_fixture(data)
    data[1]["RUNNER_TEMP"] = str(tmp_path)
    directory = tmp_path / "publication-preflight"
    directory.mkdir()
    (directory / "preflight.json").write_bytes(raw)
    (directory / "preflight.sigstore.json").write_bytes(b"synthetic-bundle")
    monkeypatch.setattr(AuthorizationSigstore, "verify", lambda *args, **kwargs: "synthetic-verification")
    with pytest.raises(OSError):
        auth.job_preflight(data[1], data[4], data[3], clock=lambda: NOW)
    auth.job_preflight(data[1], data[4], data[3], startup=True, clock=lambda: NOW + 10)
    auth.job_preflight(data[1], data[4], data[3], clock=lambda: NOW + 1000)
    data[1]["GITHUB_RUN_ID"] = "61"
    with pytest.raises(ValueError, match="startup_mismatch"):
        auth.job_preflight(data[1], data[4], data[3], clock=lambda: NOW + 1000)
    data[1]["GITHUB_RUN_ID"] = "60"
    data[1]["PUBLICATION_OPERATION"] = "recover" if operation != "recover" else "publish"
    with pytest.raises(ValueError, match="startup_mismatch"):
        auth.job_preflight(data[1], data[4], data[3], clock=lambda: NOW + 1000)


@pytest.mark.parametrize("operation,phase", [("bootstrap", "authorize"), ("bootstrap", "bootstrap-stage"),
    ("bootstrap", "bootstrap-seal"), ("bootstrap", "bootstrap-activate"), ("publish", "authorize"),
    ("publish", "stage"), ("publish", "finish"), ("recover", "authorize"), ("recover", "recover")])
def test_all_cli_paths_require_the_signed_preflight_before_publication_transport(monkeypatch, tmp_path, capsys, operation, phase):
    import publish_catalogue as cli
    data = fixture(operation)
    if phase == "bootstrap-activate":
        policy = json.loads(data[4])
        policy.update(bootstrap_operation="activate", bootstrap={"sequence": 1, "pointer_sha256": "2" * 64})
        data = (*data[:4], canonical_json(policy))
    policy_path = tmp_path / "policy.json"
    policy_path.write_bytes(data[4])
    trust_path = tmp_path / "catalogue/publication/verifier-trust.json"
    trust_path.parent.mkdir(parents=True)
    trust_path.write_bytes(canonical_json(data[3]))
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "POLICY", policy_path)
    monkeypatch.setattr(sys, "argv", ["publish_catalogue.py", phase])
    for key, value in data[1].items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path))
    def no_publisher_transport(*args, **kwargs):
        pytest.fail("unverified/missing preflight reached Publisher transport")
    monkeypatch.setattr(cli, "Github", no_publisher_transport)
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 1 and not (tmp_path / "publication-preflight-started.json").exists()
    assert "publication_validation_failed" in capsys.readouterr().err


def test_issuer_erases_step_scoped_key_before_openssl_and_exports_no_credentials(monkeypatch):
    data = fixture()
    env = deepcopy(data[1])
    def jwt(key):
        assert key == "synthetic-key" and "VERIFICATION_APP_PRIVATE_KEY" not in env
        return "synthetic-jwt"
    monkeypatch.setattr(issuer, "app_jwt", jwt)
    raw = issuer.issue(data[0], env, data[2]["operation"], data[3], clock=lambda: NOW)
    for secret in (b"synthetic-key", b"synthetic-jwt", b"synthetic-installation-token"):
        assert secret not in raw


def test_checked_in_trust_cannot_enable_publication():
    trust = json.loads((ROOT / "catalogue/publication/verifier-trust.json").read_bytes())
    assert trust == {"schema": "atlas-publication-verifier-trust/v2", "live_signer_accepted": False,
        "signer_revision": "00c85f688a43fb6da44acb3fa713d938e30a6da9",
        "ruleset_ids": {"atlas-main": 25618213, "atlas-history-lock": 25618809,
            "atlas-bootstrap-lock": 25628137, "atlas-catalogue-current": 25618684,
            "atlas-publication-tags": 25618901},
        "verification_environment_id": 25016263801, "max_observation_age_seconds": 900}
    auth.check_trust(trust, acceptance_only=True)
    with pytest.raises(ValueError, match="live_acceptance"):
        auth.check_trust(trust)
    with pytest.raises(ValueError, match="live_acceptance"):
        auth.AuthorizationVerifier(trust, fixture()[4])
    incomplete = deepcopy(trust)
    incomplete["signer_revision"] = None
    with pytest.raises(ValueError):
        auth.check_trust(incomplete, acceptance_only=True)


def test_executable_and_data_checkouts_are_independently_checked_before_credentials(monkeypatch, tmp_path):
    import publish_catalogue as cli
    calls = []
    def head(command, **kwargs):
        assert command == ['git', 'rev-parse', 'HEAD'] and kwargs['timeout'] == 10
        calls.append(kwargs['cwd'])
        return REVISION if kwargs['cwd'] == cli.ROOT else SOURCE
    monkeypatch.setattr(cli.subprocess, 'check_output', head)
    cli.check_checkouts(tmp_path, REVISION, SOURCE)
    assert calls == [cli.ROOT, tmp_path]
    with pytest.raises(ValueError, match='checkout_identity'):
        cli.check_checkouts(tmp_path, SOURCE, REVISION)


def test_genuine_cli_rejects_unsigned_preflight_before_any_publisher_transport(monkeypatch, tmp_path, capsys):
    """Real pinned gh rejection, synthetic claims; never positive live acceptance."""
    import publish_catalogue as cli
    import time
    data = fixture()
    value = json.loads(issue_fixture(data))
    now = int(time.time())
    value['freshness'] = {'observation_started': now, 'observation_completed': now,
                          'issued_at': now, 'expires_at': now + 900}
    raw = canonical_json(value)
    monkeypatch.setattr(cli, 'ROOT', tmp_path)
    policy_path = tmp_path / 'policy.json'
    policy_path.write_bytes(data[4])
    monkeypatch.setattr(cli, 'POLICY', policy_path)
    trust = tmp_path / 'catalogue/publication/verifier-trust.json'
    trust.parent.mkdir(parents=True)
    trust.write_bytes(canonical_json(data[3]))
    directory = tmp_path / 'publication-preflight'
    directory.mkdir()
    (directory / 'preflight.json').write_bytes(raw)
    (directory / 'preflight.sigstore.json').write_bytes(canonical_json({
        'mediaType': 'application/vnd.dev.sigstore.bundle.v0.3+json'}))
    for key, value in data[1].items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path))
    monkeypatch.setattr(sys, 'argv', ['publish_catalogue.py', 'authorize'])
    monkeypatch.setattr(cli, 'Github', lambda *args, **kwargs: pytest.fail('unsigned preflight reached Publisher'))
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 1 and 'attestation_verification_failed' in capsys.readouterr().err
    assert not (tmp_path / 'publication-preflight-started.json').exists()
