# SPDX-License-Identifier: Apache-2.0
"""Deterministic issuer/contract tests. Provider and signer observations are synthetic."""
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
from publication_contract import (API, REPOSITORY, canonical_json, digest, pointer_bytes, snapshot_tag)
from test_publication_contract import authority_fixture, rules_fixture
from verification_github import BASE, INSTALLATION, LIST, PERMISSIONS

SOURCE, REVISION, NEXT, CURRENT = "a" * 40, "b" * 40, "c" * 40, "d" * 40
NOW = 1800000000


def file_response(raw, path):
    return {"type": "file", "path": path, "encoding": "base64", "size": len(raw),
            "content": base64.b64encode(raw).decode()}


def target_for(transition, operation):
    from bootstrap_catalogue import CATALOGUE_SHA256, BUNDLE_SHA256, SOURCE as BOOTSTRAP_SOURCE
    prior = {"kind": "bootstrap-empty"}
    if operation != "bootstrap":
        prior = {"kind": "selected", "channel_sha": CURRENT, "pointer_sha256": "e" * 64,
                 "sequence": 1, "release_id": 501, "catalogue_asset_id": 601, "catalogue_sha256": "f" * 64}
    if transition == "activate-create-current":
        prior = {"kind": "marker-created", "marker_sha": NEXT}
    target = {"sequence": 1 if operation == "bootstrap" else 2,
              "catalogue_sha256": CATALOGUE_SHA256 if operation == "bootstrap" else "1" * 64,
              "snapshot_source_commit": BOOTSTRAP_SOURCE if operation == "bootstrap" else SOURCE,
              "expected_prior": prior}
    extra = auth.TARGET_FIELDS[transition]
    for name, value in {"release_id": 700, "catalogue_asset_id": 800, "catalogue_bundle_asset_id": 801,
                        "catalogue_bundle_sha256": BUNDLE_SHA256 if operation == "bootstrap" else "3" * 64,
                        "pointer_sha256": "2" * 64,
                        "next_channel_sha": NEXT}.items():
        if name in extra:
            target[name] = value
    if "artifact_name" in extra:
        target.update(artifact_name="current.json" if transition == "seal-upload-selection"
                      else snapshot_tag(target["sequence"]) + ".json",
                      artifact_sha256="2" * 64 if transition == "seal-upload-selection" else target["catalogue_sha256"])
    if "assets" in extra:
        target["assets"] = {snapshot_tag(target["sequence"]) + ".json": {"id": 800, "sha256": target["catalogue_sha256"]},
                            "catalogue.sigstore.json": {"id": 801, "sha256": "3" * 64},
                            "current.json": {"id": 802, "sha256": "2" * 64},
                            "current.sigstore.json": {"id": 803, "sha256": "4" * 64}}
    return target


class SyntheticProvider:
    def __init__(self, rows):
        self.rows, self.calls = rows, []

    def get(self, path, token, *, missing=False):
        assert token in {"synthetic-jwt", "synthetic-installation-token"}
        self.calls.append(("GET", path, token))
        assert path in self.rows, path
        value = self.rows[path]
        assert value is not None or missing
        return deepcopy(value)

    def mint(self, jwt):
        assert jwt == "synthetic-jwt"
        self.calls.append(("POST", "mint", jwt))
        return deepcopy(self.rows["mint"])


def fixture(transition="stage-upload-catalogue", operation="bootstrap"):
    args = authority_fixture()
    policy, repo, branch, environment, run, attempt, workflow, user, checks = args
    policy.update(allowed_maintainer_id=93822871, app_id=5422372, app_installation_id=174027755,
                  app_slug="atlas-catalogue-publisher", app_bot_user_id=346232650,
                  bootstrap_operation="stage" if operation == "bootstrap" and not transition.startswith("activate-")
                      else "activate")
    policy["bootstrap"] = {"sequence": None, "pointer_sha256": None} if policy["bootstrap_operation"] == "stage" else {
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
    trust = {"schema": "atlas-publication-verifier-trust/v1", "live_signer_accepted": True,
             "signer_revision": REVISION, "ruleset_ids": {row["name"]: row["id"] for row in rules},
             "verification_environment_id": 123, "max_observation_age_seconds": 60}
    target = target_for(transition, operation)
    if operation != "bootstrap":
        raw_pointer = pointer_bytes({"schema_version": "1.0", "sequence": 1, "release_tag": "catalogue-000001",
            "release_id": 501, "asset_id": 601, "sha256": "f" * 64, "previous_pointer_sha256": None})
        target["expected_prior"]["pointer_sha256"] = digest(raw_pointer)
    policy_raw = canonical_json(policy)
    request = {"source_commit": SOURCE, "policy_sha256": digest(policy_raw), "run_id": 60, "run_attempt": 1,
               "operation": operation, "transition": transition, "challenge": "8" * 64, "target": target}
    env = {"GITHUB_REPOSITORY": REPOSITORY, "GITHUB_REPOSITORY_ID": "1414494920",
        "GITHUB_REPOSITORY_OWNER_ID": "93822871", "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REF": "refs/heads/main", "GITHUB_SHA": SOURCE, "GITHUB_RUN_ID": "60", "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_WORKFLOW_REF": REPOSITORY + "/" + auth.PUBLICATION_WORKFLOW + "@refs/heads/main",
        "RUNNER_ENVIRONMENT": "github-hosted", "VERIFIER_REVISION": REVISION,
        "VERIFIER_WORKFLOW_REF": REPOSITORY + "/" + auth.WORKFLOW + "@" + REVISION,
        "DISPATCH_OPERATION": operation, "VERIFICATION_APP_ID": "5424851",
        "VERIFICATION_APP_INSTALLATION_ID": "174088125", "VERIFICATION_APP_PRIVATE_KEY": "synthetic-key"}
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
                                          "owner": {"id": 93822871}, "permissions": auth_legacy_permissions()},
        BASE + "/environments/catalogue-verification": {**environment, "id": 123, "name": "catalogue-verification"},
        BASE + "/immutable-releases": {"enabled": True}, LIST: rules,
        BASE + "/releases?per_page=100&page=1": [],
        BASE + "/git/ref/heads/catalogue-current": None,
        BASE + "/git/ref/tags/catalogue-bootstrap-root": None,
        BASE + "/git/ref/tags/" + snapshot_tag(target["sequence"]): None,
        BASE + "/git/commits/" + NEXT: {"sha": NEXT, "parents": [] if operation == "bootstrap" else [{"sha": CURRENT}]}}
    for row in rules:
        rows[BASE + f"/rulesets/{row['id']}?includes_parents=true"] = row
    if operation != "bootstrap":
        rows[BASE + "/git/ref/heads/catalogue-current"] = {
            "ref": "refs/heads/catalogue-current", "object": {"type": "commit", "sha": CURRENT}}
        rows[BASE + "/contents/current.json?ref=" + CURRENT] = file_response(raw_pointer, "current.json")
    if transition == "activate-create-current":
        rows[BASE + "/git/ref/tags/catalogue-bootstrap-root"] = {
            "ref": "refs/tags/catalogue-bootstrap-root", "object": {"type": "commit", "sha": NEXT,
                "url": API + "/git/commits/" + NEXT}}
    if "release_id" in target:
        immutable = transition.endswith("current") or transition == "activate-create-marker"
        rows[BASE + "/releases/700"] = {"id": 700, "tag_name": snapshot_tag(target["sequence"]),
                                          "target_commitish": target["snapshot_source_commit"],
                                          "draft": not immutable, "immutable": immutable, "prerelease": False}
        assets = target.get("assets", {})
        if transition == "seal-upload-selection":
            assets = {snapshot_tag(target["sequence"]) + ".json": {"id": 800, "sha256": target["catalogue_sha256"]},
                      "catalogue.sigstore.json": {"id": 801, "sha256": target["catalogue_bundle_sha256"]}}
        rows[BASE + "/releases/700/assets?per_page=5&page=1"] = [
            {"name": name, "id": row["id"], "digest": "sha256:" + row["sha256"], "state": "uploaded", "size": 12}
            for name, row in assets.items()]
    return SyntheticProvider(deepcopy(rows)), env, request, trust, policy_raw


def auth_legacy_permissions():
    from publication_contract import APP_PERMISSIONS
    return deepcopy(APP_PERMISSIONS)


@pytest.fixture(autouse=True)
def synthetic_jwt(monkeypatch):
    monkeypatch.setattr(issuer, "app_jwt", lambda key: "synthetic-jwt")


def issue_fixture(data):
    api, env, request, trust, policy = data
    return issuer.issue(api, deepcopy(env), request, trust, clock=lambda: NOW)


ALL_TRANSITIONS = [(transition, operation) for transition in auth.TARGET_FIELDS
                   for operation in sorted(auth.OPERATIONS[transition])]
ISSUABLE_TRANSITIONS = [(transition, operation) for transition, operation in ALL_TRANSITIONS
                       if transition != "stage-create-draft"]


@pytest.mark.parametrize("transition,operation", ISSUABLE_TRANSITIONS)
def test_every_issuable_transition_has_complete_independent_observations(transition, operation):
    data = fixture(transition, operation)
    api, env, request, trust, policy = data
    raw = issue_fixture(data)
    value = auth.parse(raw, auth.MAX_AUTHORIZATION_BYTES)
    assert auth.check_authorization(value, trust, json.loads(policy)) == request
    assert len(value["rulesets"]["observations"]) == 5
    assert [call[0] for call in api.calls].count("POST") == 1
    assert all(call[0] == "GET" for call in api.calls if call[1] != "mint")
    assert not any(secret.encode() in raw for secret in ("synthetic-key", "synthetic-jwt", "synthetic-installation-token"))


@pytest.mark.parametrize("key", list(fixture()[1]))
def test_context_and_configuration_substitution_fails_closed(key):
    data = fixture()
    data[1][key] = "" if key == "VERIFICATION_APP_PRIVATE_KEY" else "wrong"
    with pytest.raises(ValueError):
        issue_fixture(data)
    if key not in {"VERIFICATION_APP_PRIVATE_KEY", "VERIFICATION_APP_ID", "VERIFICATION_APP_INSTALLATION_ID"}:
        assert data[0].calls == []


@pytest.mark.parametrize("workflow", [
    REPOSITORY + "/" + auth.WORKFLOW + "@refs/heads/main",
    REPOSITORY + "/.github/workflows/verifier-signer-experiment.yml@refs/heads/main",
    REPOSITORY + "/" + auth.PUBLICATION_WORKFLOW + "@refs/heads/other",
])
def test_wrong_caller_workflow_is_rejected_before_credentials(workflow):
    data = fixture()
    data[1]["GITHUB_WORKFLOW_REF"] = workflow
    with pytest.raises(ValueError, match="verification_context"):
        issue_fixture(data)
    assert data[0].calls == []


def test_referenced_workflow_api_contract_remains_sha_path_and_sha():
    data = fixture()
    references = data[0].rows[BASE + "/actions/runs/60"]["referenced_workflows"]
    assert references == [{"path": REPOSITORY + "/" + auth.WORKFLOW + "@" + REVISION, "sha": REVISION}]
    assert issue_fixture(data)


@pytest.mark.parametrize("path,sha", [
    (REPOSITORY + "/" + auth.WORKFLOW + "@refs/heads/main", REVISION),
    (REPOSITORY + "/" + auth.WORKFLOW + "@" + SOURCE, REVISION),
    (REPOSITORY + "/" + auth.WORKFLOW + "@" + REVISION, SOURCE),
    (REPOSITORY + "/.github/workflows/verifier-signer-probe.yml@" + REVISION, REVISION),
])
def test_referenced_workflow_api_rejects_branch_path_and_pin_or_path_substitution(path, sha):
    data = fixture()
    data[0].rows[BASE + "/actions/runs/60"]["referenced_workflows"] = [{"path": path, "sha": sha}]
    with pytest.raises(ValueError, match="verification_reusable_workflow"):
        issue_fixture(data)


@pytest.mark.parametrize("path,change", [
    ("/app", lambda v: v.update(id=5422372)),
    ("/app", lambda v: v["owner"].update(id=1)),
    ("/app", lambda v: v["permissions"].update(contents="write")),
    (INSTALLATION, lambda v: v.update(id=1)),
    (INSTALLATION, lambda v: v.update(app_id=1)),
    (INSTALLATION, lambda v: v["account"].update(id=1)),
    (INSTALLATION, lambda v: v.update(repository_selection="all")),
    (INSTALLATION, lambda v: v.update(suspended_at="2026-01-01")),
    ("mint", lambda v: v.update(token="secret\r\n")),
    ("mint", lambda v: v["permissions"].update(administration="read")),
    ("/installation/repositories?per_page=2&page=1", lambda v: v.update(total_count=2)),
    ("/installation/repositories?per_page=2&page=1", lambda v: v["repositories"][0].update(id=1)),
    (BASE, lambda v: v.update(id=1)),
    (BASE + "/actions/runs/60", lambda v: v["actor"].update(id=1)),
    (BASE + "/actions/runs/60/attempts/1", lambda v: v["triggering_actor"].update(id=1)),
    (BASE + "/actions/runs/60", lambda v: v.update(run_attempt=2)),
    (BASE + "/actions/runs/60", lambda v: v.update(head_sha=NEXT)),
    (BASE + "/actions/runs/60", lambda v: v.update(path=auth.WORKFLOW)),
    (BASE + "/actions/runs/60", lambda v: v.update(referenced_workflows=[])),
    (BASE + "/actions/runs/60", lambda v: v["referenced_workflows"][0].update(sha=SOURCE)),
    (BASE + "/actions/workflows/80", lambda v: v.update(state="disabled_manually")),
    (BASE + "/branches/main", lambda v: v["commit"].update(sha=NEXT)),
    (BASE + "/environments/catalogue-verification", lambda v: v.update(can_admins_bypass=True)),
    (BASE + "/environments/catalogue-verification", lambda v: v.update(id=1)),
    (BASE + "/environments/catalogue-publication", lambda v: v.update(can_admins_bypass=True)),
    (BASE + f"/commits/{SOURCE}/check-runs?check_name=validate&filter=latest&per_page=2&page=1",
        lambda v: v["check_runs"][0].update(conclusion="failure")),
    (BASE + "/immutable-releases", lambda v: v.update(enabled=False)),
    ("/apps/atlas-catalogue-publisher", lambda v: v["permissions"].update(administration="write")),
])
def test_independent_evidence_rejects_substitution(path, change):
    data = fixture()
    change(data[0].rows[path])
    with pytest.raises(ValueError):
        issue_fixture(data)


@pytest.mark.parametrize("index", range(1, 6))
@pytest.mark.parametrize("change", [lambda v: v.pop("bypass_actors"),
    lambda v: v.update(bypass_actors=[{"actor_id": 5424851, "actor_type": "Integration", "bypass_mode": "always"}]),
    lambda v: v.update(rules=[]), lambda v: v.update(enforcement="disabled"),
    lambda v: v.update(id=1234), lambda v: v.update(source="another/repo")])
def test_complete_five_rulesets_and_original_protections_are_mandatory(index, change):
    data = fixture()
    change(data[0].rows[BASE + f"/rulesets/{index}?includes_parents=true"])
    with pytest.raises(ValueError):
        issue_fixture(data)


@pytest.mark.parametrize("change", [lambda v: v.pop(), lambda v: v.append(deepcopy(v[0])),
                                  lambda v: v[0].update(id=999)])
def test_ruleset_enumeration_and_pinned_ids(change):
    data = fixture()
    change(data[0].rows[LIST])
    with pytest.raises(ValueError):
        issue_fixture(data)


@pytest.mark.parametrize("transition,operation", ALL_TRANSITIONS)
def test_every_variant_rejects_extra_missing_fields_and_unassigned_ids(transition, operation):
    target = target_for(transition, operation)
    auth.check_target(target, transition, operation)
    for key in target:
        broken = deepcopy(target)
        del broken[key]
        with pytest.raises(ValueError):
            auth.check_target(broken, transition, operation)
    with pytest.raises(ValueError):
        auth.check_target({**target, "unassigned_asset_id": 123}, transition, operation)


@pytest.mark.parametrize("raw", [b"{}", b"[]", b"\xff", b"{}\n ", b'{"a":1,"a":1}',
    b'{"a":NaN}', b'{"a":Infinity}', b'{"a":1e9999}', b"[" * 2000,
    b"x" * (auth.MAX_AUTHORIZATION_BYTES + 1), "{}".encode("utf-16")])
def test_malformed_noncanonical_json(raw):
    with pytest.raises(ValueError):
        auth.check_request(auth.parse(raw, auth.MAX_REQUEST_BYTES))


@pytest.mark.parametrize("field", ["schema", "authority", "source", "execution", "rulesets", "target", "freshness"])
def test_authorization_envelope_exact_fields(field):
    data = fixture()
    value = json.loads(issue_fixture(data))
    value.pop(field)
    with pytest.raises(ValueError):
        auth.check_authorization(value, data[3], json.loads(data[4]))


@pytest.mark.parametrize("section", [None, "authority", "source", "execution", "rulesets", "freshness", "target"])
def test_no_unsigned_extension_fields(section):
    data = fixture()
    value = json.loads(issue_fixture(data))
    (value if section is None else value[section])["extra"] = True
    with pytest.raises(ValueError):
        auth.check_authorization(value, data[3], json.loads(data[4]))


def test_default_trust_is_blocked_before_credentials():
    data = fixture()
    data = (*data[:3], json.loads((ROOT / "catalogue/publication/verifier-trust.json").read_bytes()), data[4])
    with pytest.raises(ValueError, match="acceptance"):
        issue_fixture(data)
    assert data[0].calls == []


def test_local_replay_and_context_checks_with_synthetic_signature_boundary(monkeypatch):
    from authorization_sigstore import AuthorizationSigstore
    data = fixture()
    raw = issue_fixture(data)
    calls = []
    monkeypatch.setattr(AuthorizationSigstore, "verify", lambda *a, **kw: calls.append(kw))
    verifier = auth.AuthorizationVerifier(data[3], data[4])
    expected = data[2]
    for key, other in {"run_id": 61, "run_attempt": 2, "operation": "recover", "challenge": "7" * 64,
                       "source_commit": NEXT, "policy_sha256": "0" * 64,
                       "transition": "seal-upload-selection"}.items():
        with pytest.raises(ValueError):
            verifier.verify_and_consume(raw, b"synthetic", {**expected, key: other}, clock=lambda: NOW)
    for now in (NOW - 1, NOW + 60, NOW + 1000):
        with pytest.raises(ValueError, match="fresh"):
            verifier.verify_and_consume(raw, b"synthetic", expected, clock=lambda: now)
    assert calls == []
    verifier.verify_and_consume(raw, b"synthetic", expected, clock=lambda: NOW + 1)
    with pytest.raises(ValueError, match="consumed"):
        verifier.verify_and_consume(raw, b"synthetic", expected, clock=lambda: NOW + 1)
    # A new object has no durable consumption knowledge; explicitly no global once-only claim.
    auth.AuthorizationVerifier(data[3], data[4]).verify_and_consume(raw, b"synthetic", expected, clock=lambda: NOW + 1)


@pytest.mark.parametrize("change", [
    lambda v: v["authority"].update(maintainer_id=1),
    lambda v: v["rulesets"].update(sha256="0" * 64),
    lambda v: v["rulesets"]["ids"].update({"atlas-main": 1.0}),
    lambda v: v["rulesets"]["approved_bypass_actors"]["atlas-catalogue-current"][0].update(actor_id=5422372.0),
    lambda v: v["rulesets"]["observations"].pop(),
    lambda v: v["freshness"].update(observation_started=NOW - 100),
    lambda v: v["freshness"].update(issued_at=NOW + 1),
    lambda v: v["freshness"].update(expires_at=NOW + 61),
    lambda v: v["freshness"].update(observation_completed=NOW - 1),
    lambda v: v["source"].update(verifier_revision=SOURCE),
    lambda v: v["execution"].update(workflow=auth.WORKFLOW),
])
def test_modified_decisions_fail_before_signature_boundary(change):
    data = fixture()
    value = json.loads(issue_fixture(data))
    change(value)
    with pytest.raises(ValueError):
        auth.AuthorizationVerifier(data[3], data[4]).verify_and_consume(
            canonical_json(value), b"synthetic", data[2], clock=lambda: NOW)


def test_signature_time_counts_against_observation_age_and_does_not_consume(monkeypatch):
    from authorization_sigstore import AuthorizationSigstore
    data = fixture()
    raw = issue_fixture(data)
    monkeypatch.setattr(AuthorizationSigstore, "verify", lambda *a, **kw: None)
    verifier = auth.AuthorizationVerifier(data[3], data[4])
    times = iter([NOW + 1, NOW + 60])
    with pytest.raises(ValueError, match="fresh"):
        verifier.verify_and_consume(raw, b"synthetic", data[2], clock=lambda: next(times))
    assert verifier.consumed == set()


def test_earliest_authentication_observation_not_issuance_sets_expiry():
    data = fixture()
    times = iter([NOW, NOW + 61])
    with pytest.raises(ValueError, match="freshness"):
        issuer.issue(data[0], deepcopy(data[1]), data[2], data[3], clock=lambda: next(times))


@pytest.mark.parametrize("transition,operation", ISSUABLE_TRANSITIONS)
def test_provider_target_state_is_independently_checked(transition, operation):
    data = fixture(transition, operation)
    data[0].rows[BASE + "/releases/700"]["id"] = 701
    with pytest.raises(ValueError):
        issue_fixture(data)


def test_cli_errors_and_artifacts_cannot_expose_credentials(monkeypatch, tmp_path, capsys):
    data = fixture()
    for key, value in data[1].items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path))
    monkeypatch.setenv("AUTHORIZATION_REQUEST", canonical_json(data[2]).decode())
    monkeypatch.setenv("VERIFICATION_POLICY", json.dumps(data[3]))
    monkeypatch.setattr(issuer, "VerificationGithub", lambda: data[0])
    assert issuer.main() == 0
    assert capsys.readouterr() == ("", "")
    assert "VERIFICATION_APP_PRIVATE_KEY" not in __import__("os").environ
    assert sorted(p.name for p in (tmp_path / "publication-authorization").iterdir()) == ["authorization.json", "predicate.json"]
    for path in tmp_path.rglob("*.json"):
        assert b"synthetic-installation-token" not in path.read_bytes()
    monkeypatch.setattr(issuer, "issue", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("synthetic-secret")))
    assert issuer.main() == 1
    assert capsys.readouterr() == ("", "publication_verification_failed\n")


@pytest.mark.parametrize("transition", ["stage-upload-catalogue", "seal-upload-selection"])
@pytest.mark.parametrize("operation", ["bootstrap", "publish"])
def test_bundle_upload_variant_requires_previously_assigned_ids(transition, operation):
    from bootstrap_catalogue import BUNDLE_SHA256
    data = fixture(transition, operation)
    target = data[2]["target"]
    rows = data[0].rows[BASE + "/releases/700/assets?per_page=5&page=1"]
    if transition == "stage-upload-catalogue":
        target.update(artifact_name="catalogue.sigstore.json", catalogue_asset_id=800,
                      artifact_sha256=BUNDLE_SHA256 if operation == "bootstrap" else "3" * 64)
        rows.append({"name": snapshot_tag(target["sequence"]) + ".json", "id": 800,
                     "digest": "sha256:" + target["catalogue_sha256"], "state": "uploaded", "size": 12})
        field = "catalogue_asset_id"
    else:
        target.update(artifact_name="current.sigstore.json", pointer_asset_id=802, artifact_sha256="4" * 64)
        rows.append({"name": "current.json", "id": 802, "digest": "sha256:" + target["pointer_sha256"],
                     "state": "uploaded", "size": 12})
        field = "pointer_asset_id"
    auth.check_request(data[2])
    issue_fixture(data)
    for value in (None, 999):
        broken = deepcopy(data[2])
        if value is None:
            del broken["target"][field]
            with pytest.raises(ValueError):
                auth.check_request(broken)
        else:
            broken["target"][field] = value
            with pytest.raises(ValueError):
                issuer.issue(data[0], deepcopy(data[1]), broken, data[3], clock=lambda: NOW)


@pytest.mark.parametrize("change", [
    lambda target: target.update(release_id=0), lambda target: target.update(release_id=True),
    lambda target: target["assets"]["current.json"].update(id=801),
    lambda target: target["assets"]["current.json"].update(sha256="0" * 64),
    lambda target: target["assets"].pop("catalogue.sigstore.json"),
    lambda target: target["assets"]["current.json"].update(extra=123),
    lambda target: target["expected_prior"].update(channel_sha="x" * 40),
    lambda target: target["expected_prior"].update(sequence=True),
    lambda target: target.update(sequence=3), lambda target: target.update(next_channel_sha=CURRENT),
])
def test_target_identifiers_digests_and_predecessors_are_strict(change):
    target = target_for("finish-advance-current", "publish")
    change(target)
    with pytest.raises(ValueError):
        auth.check_target(target, "finish-advance-current", "publish")


@pytest.mark.parametrize("path,change", [
    (BASE + "/releases/700/assets?per_page=5&page=1", lambda rows: rows[0].update(id=999)),
    (BASE + "/releases/700/assets?per_page=5&page=1", lambda rows: rows[0].update(digest="sha256:" + "0" * 64)),
    (BASE + "/releases/700/assets?per_page=5&page=1", lambda rows: rows.pop()),
    (BASE + "/releases/700/assets?per_page=5&page=1", lambda rows: rows.append(deepcopy(rows[0]))),
    (BASE + "/git/ref/heads/catalogue-current", lambda row: row["object"].update(sha=NEXT)),
    (BASE + "/git/commits/" + NEXT, lambda row: row.update(parents=[])),
    (BASE + "/releases/700", lambda row: row.update(immutable=False)),
])
def test_substituted_target_provider_evidence(path, change):
    data = fixture("finish-advance-current", "publish")
    change(data[0].rows[path])
    with pytest.raises(ValueError):
        issue_fixture(data)


def test_bootstrap_cannot_approve_different_frozen_bytes_or_unapproved_pointer():
    data = fixture("activate-finalize-release", "bootstrap")
    for key, value in (("catalogue_sha256", "0" * 64), ("snapshot_source_commit", SOURCE),
                       ("pointer_sha256", "5" * 64)):
        modified = deepcopy(data[2])
        modified["target"][key] = value
        with pytest.raises(ValueError):
            issuer.issue(data[0], deepcopy(data[1]), modified, data[3], clock=lambda: NOW)


def test_policy_digest_binds_exact_source_file_bytes_not_reencoded_json():
    data = fixture()
    raw = issue_fixture(data)
    reencoded = json.dumps(json.loads(data[4])).encode()
    assert reencoded != data[4]
    with pytest.raises(ValueError, match="policy_digest"):
        auth.AuthorizationVerifier(data[3], reencoded).verify_and_consume(
            raw, b"synthetic", data[2], clock=lambda: NOW)


def test_observation_and_request_duplicate_fields_and_utf8_are_rejected():
    data = fixture()
    raw = issue_fixture(data)
    for malformed in [raw.replace(b'"schema":', b'"schema": "duplicate", "schema":'),
                      raw + b" ", raw.decode().encode("utf-16")]:
        with pytest.raises(ValueError):
            auth.parse(malformed, auth.MAX_AUTHORIZATION_BYTES)


@pytest.mark.parametrize("operation,transition", [("publish", "finish-advance-current"),
                                                  ("recover", "recover-advance-current")])
def test_bootstrap_fence_protection_is_required_even_outside_bootstrap(operation, transition):
    data = fixture(transition, operation)
    data[0].rows[BASE + "/rulesets/5?includes_parents=true"]["rules"] = [{"type": "update"}]
    with pytest.raises(ValueError, match="protection"):
        issue_fixture(data)


@pytest.mark.parametrize("operation", ["bootstrap", "publish"])
@pytest.mark.parametrize("value", [[], [{"id": 700, "tag_name": "other", "draft": False}],
    [None], [{"id": 700}], [{"id": 700, "tag_name": "other"}] * 2,
    [{"id": n + 1, "tag_name": "other"} for n in range(100)]])
def test_empty_filtered_or_malformed_inventory_never_authorizes_draft_creation(operation, value, monkeypatch):
    data = fixture("stage-create-draft", operation)
    data[0].rows[BASE + "/releases?per_page=100&page=1"] = value
    # Even a claimed proof in environment/token metadata cannot enable the transition.
    data[1]["DRAFT_VISIBILITY_PROVEN"] = "true"
    data[0].rows["mint"]["draft_visibility_proven"] = True
    monkeypatch.setattr(issuer, "authenticate", lambda *a: pytest.fail("blocked transition reached credentials"))
    with pytest.raises(ValueError, match="^draft_visibility_unproven$"):
        issue_fixture(data)
    assert data[0].calls == []
    # Direct use of the provider-state checker also rejects before consulting a listing.
    with pytest.raises(ValueError, match="^draft_visibility_unproven$"):
        issuer.observe_target(data[0], "synthetic-installation-token", data[2])
    assert data[0].calls == []


@pytest.mark.parametrize("operation", ["bootstrap", "publish"])
def test_cli_draft_rejection_exports_nothing_and_has_fixed_diagnostic(operation, monkeypatch, tmp_path, capsys):
    data = fixture("stage-create-draft", operation)
    for key, value in data[1].items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path))
    monkeypatch.setenv("AUTHORIZATION_REQUEST", canonical_json(data[2]).decode())
    monkeypatch.setenv("VERIFICATION_POLICY", json.dumps(data[3]))
    monkeypatch.setattr(issuer, "VerificationGithub", lambda: data[0])
    monkeypatch.setattr(issuer, "authenticate", lambda *a: pytest.fail("blocked transition reached credentials"))
    assert issuer.main() == 1
    assert capsys.readouterr() == ("", "draft_visibility_unproven\n")
    assert data[0].calls == [] and list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("provider_digest", [
    "1" * 64, "sha512:" + "1" * 64, "SHA256:" + "1" * 64,
    "sha256:" + "A" * 64, "sha256:" + "g" * 64,
    1, int("1" * 64), 1.0, True, [], {}, None,
    "sha256:", "sha256:" + "1" * 63, "sha256:" + "1" * 65,
    " sha256:" + "1" * 64, "sha256:" + "1" * 64 + " ",
    "sha256:" + "1" * 64 + "\n", "sha256:\t" + "1" * 64,
    "sha256:" + "1" * 64 + ":extra",
])
def test_provider_asset_digest_requires_exact_algorithm_qualified_string(provider_digest):
    data = fixture("finish-advance-current", "publish")
    data[0].rows[BASE + "/releases/700/assets?per_page=5&page=1"][0]["digest"] = provider_digest
    with pytest.raises(ValueError, match="^verification_asset_digest$"):
        issue_fixture(data)


def test_provider_asset_digest_is_required():
    data = fixture("finish-advance-current", "publish")
    del data[0].rows[BASE + "/releases/700/assets?per_page=5&page=1"][0]["digest"]
    with pytest.raises(ValueError, match="^verification_asset_digest$"):
        issue_fixture(data)


def test_exact_provider_asset_digests_continue_to_issue_decisions():
    data = fixture("finish-advance-current", "publish")
    value = json.loads(issue_fixture(data))
    assert value["target"]["assets"] == data[2]["target"]["assets"]
