# SPDX-License-Identifier: Apache-2.0
"""Package publication models. No live tokens, provider writes or acceptance claims."""
from copy import deepcopy
import base64
import io
import json
import shutil
from pathlib import Path
import stat
import subprocess
import sys
import urllib.error
import zipfile
from email.message import Message

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import connector_publication_contract as contract
import connector_publication_github as transport
import connector_publication_preflight as preflight
import connector_publication_sigstore as crypto
import issue_publication_authorization as old_issuer
import publish_connector as engine
import verify_connector_release as final_verifier
from publication_contract import API, APP_PERMISSIONS, PublicationError, REPOSITORY, canonical_json, digest
from publication_verify import ORIGIN, Verifier
from test_authorization_sigstore import SYNTHETIC_BUNDLE, synthetic_verified_output
from test_connector_release import PackageProvider, TAG
from test_publication_authorization import (NOW, REVISION, SOURCE, SyntheticProvider, file_response,
    fixture as old_fixture)
from test_publication_state import StructuralVerifier, structural_bundle
from verification_github import BASE


def request(operation="tag", *, acceptance_only=False, commit=SOURCE, sha256="c" * 64):
    package = {"tag": TAG, "source_commit": commit, "sha256": sha256}
    if operation != "tag":
        package.update(build_run_id=60, artifact_id=70, artifact_sha256="d" * 64)
    if operation == "stage":
        package.update(release_id=None, assets={})
    if operation == "finalize":
        assets = {n: {"id": i, "sha256": "c" * 64, "bytes": 10} for i, n in enumerate(
            ["proxmox-0.2.1.tar.gz", "manifest.json", "index.json", "SHA256SUMS", "package.sigstore.json"], 200)}
        package.update(release_id=100, asset_id=200, assets=assets,
            inventory_sha256=contract.inventory(assets), staging_run_id=89)
    return {"operation": operation, "acceptance_only": acceptance_only, "package": package}


def admission_data(inputs=None, *, caller=SOURCE):
    inputs = deepcopy(inputs or request())
    api, env, _, old_trust, _ = old_fixture("publish", acceptance_only=inputs["acceptance_only"])
    policy_raw = (ROOT / contract.POLICY_PATH).read_bytes()
    policy = json.loads(policy_raw)
    trust = {**old_trust, "schema": contract.TRUST_SCHEMA, "enabled": True}
    env.update(GITHUB_WORKFLOW_REF=REPOSITORY + "/" + contract.WORKFLOW + "@refs/heads/main",
        GITHUB_ACTOR_ID="93822871", GITHUB_ACTOR="benchristian88", GITHUB_TRIGGERING_ACTOR="benchristian88",
        GITHUB_SHA=caller, GITHUB_RUN_ID="90", ATLAS_IMPLEMENTATION_REVISION=REVISION,
        VERIFIER_WORKFLOW_REF=REPOSITORY + "/" + contract.SIGNER + "@refs/heads/main",
        CONNECTOR_VERIFICATION_POLICY=json.dumps(trust), CONNECTOR_REQUEST=json.dumps(inputs),
        DISPATCH_OPERATION=inputs["operation"], DISPATCH_ACCEPTANCE_ONLY=str(inputs["acceptance_only"]).lower(),
        DISPATCH_PACKAGE=json.dumps(inputs["package"]))
    rows = api.rows
    rows[BASE + "/branches/main"]["commit"]["sha"] = caller
    rows[BASE + "/environments/catalogue-publication"]["id"] = policy["environment_id"]
    for suffix in ("", "/attempts/1"):
        row = deepcopy(rows[BASE + "/actions/runs/60" + suffix])
        row.update(id=90, workflow_id=81, path=contract.WORKFLOW, head_sha=caller,
            url=API + "/actions/runs/90", html_url=ORIGIN + "/actions/runs/90",
            referenced_workflows=[{"path": REPOSITORY + "/" + contract.SIGNER + "@" + REVISION, "sha": REVISION}])
        rows[BASE + "/actions/runs/90" + suffix] = row
    rows[BASE + "/actions/workflows/81"] = {"id": 81, "path": contract.WORKFLOW,
        "state": "active", "url": API + "/actions/workflows/81"}
    checks = deepcopy(rows[BASE + f"/commits/{SOURCE}/check-runs?check_name=validate&filter=latest&per_page=2&page=1"])
    checks["check_runs"][0]["head_sha"] = caller
    rows[BASE + f"/commits/{caller}/check-runs?check_name=validate&filter=latest&per_page=2&page=1"] = checks
    rows[BASE + f"/contents/{contract.POLICY_PATH}?ref={caller}"] = file_response(policy_raw, contract.POLICY_PATH)
    rows[BASE + f"/contents/{contract.TRUST_PATH}?ref={caller}"] = file_response(canonical_json(trust), contract.TRUST_PATH)
    rows[BASE + f"/contents/.github/workflows/connector-publish.yml?ref={caller}"] = file_response(
        (REPOSITORY + "/" + contract.SIGNER + "@" + REVISION).encode(), ".github/workflows/connector-publish.yml")
    return SyntheticProvider(rows), env, trust, policy_raw


def issue(data, monkeypatch):
    monkeypatch.setattr(old_issuer, "app_jwt", lambda key: "synthetic-jwt")
    return preflight.issue(data[0], deepcopy(data[1]), clock=lambda: NOW)


@pytest.mark.parametrize("operation", ["tag", "stage", "finalize"])
@pytest.mark.parametrize("acceptance", [True, False])
def test_signed_contract_binds_each_distinct_operation(monkeypatch, operation, acceptance):
    data = admission_data(request(operation, acceptance_only=acceptance))
    raw = issue(data, monkeypatch)
    value = contract.parse(raw, contract.MAX_AUTHORIZATION_BYTES)
    expected = contract.context(data[1], request(operation, acceptance_only=acceptance))
    contract.check_preflight(value, expected, data[2], data[3])
    assert value["context"]["request_sha256"] == digest(canonical_json(expected["request"]))
    assert value["implementation_sha"] == REVISION != SOURCE
    assert b"synthetic-key" not in raw and b"synthetic-installation-token" not in raw
    assert all("/releases" not in path and "/git/" not in path for _, path, _ in data[0].calls)


@pytest.mark.parametrize("field", ["GITHUB_REPOSITORY", "GITHUB_REPOSITORY_ID", "GITHUB_REPOSITORY_OWNER_ID",
    "GITHUB_ACTOR_ID", "GITHUB_ACTOR", "GITHUB_TRIGGERING_ACTOR", "GITHUB_REF", "GITHUB_RUN_ATTEMPT",
    "GITHUB_WORKFLOW_REF", "ATLAS_IMPLEMENTATION_REVISION", "VERIFIER_WORKFLOW_REF", "DISPATCH_OPERATION",
    "DISPATCH_ACCEPTANCE_ONLY", "DISPATCH_PACKAGE"])
def test_invalid_context_cannot_reach_verifier_credentials(monkeypatch, field):
    data = admission_data()
    data[1][field] = "wrong"
    with pytest.raises(ValueError):
        issue(data, monkeypatch)
    assert data[0].calls == []


@pytest.mark.parametrize("path,field,value", [
    (BASE, "id", 1), (BASE + "/branches/main", "protected", False),
    (BASE + "/actions/runs/90", "run_attempt", 2),
    (BASE + "/actions/runs/90/attempts/1", "triggering_actor", {"id": 1}),
    (BASE + "/actions/workflows/81", "path", ".github/workflows/catalogue-publish.yml"),
    (BASE + "/environments/catalogue-publication", "can_admins_bypass", True),
    (BASE + "/environments/catalogue-verification", "id", 1),
    (BASE + "/immutable-releases", "enabled", False),
    ("/apps/atlas-catalogue-publisher", "permissions", {**APP_PERMISSIONS, "workflows": "write"}),
    ("/app", "id", 1), ("mint", "permissions", APP_PERMISSIONS),
])
def test_complete_admission_rejects_identity_and_authority_changes(monkeypatch, path, field, value):
    data = admission_data()
    data[0].rows[path][field] = value
    with pytest.raises(ValueError):
        issue(data, monkeypatch)


@pytest.mark.parametrize("change", ["omitted", "changed", "ci_failed", "ci_missing", "wrong_owner", "source_pin"])
def test_hidden_bypass_and_source_controls_fail_closed(monkeypatch, change):
    data = admission_data()
    if change in {"omitted", "changed"}:
        row = data[0].rows[BASE + "/rulesets/3?includes_parents=true"]
        if change == "omitted": row.pop("bypass_actors")
        else: row["bypass_actors"] = []
    elif change in {"ci_failed", "ci_missing"}:
        row = data[0].rows[BASE + f"/commits/{SOURCE}/check-runs?check_name=validate&filter=latest&per_page=2&page=1"]
        if change == "ci_failed": row["check_runs"][0]["conclusion"] = "failure"
        else: row["check_runs"] = []
    elif change == "wrong_owner": data[0].rows[BASE]["owner"]["id"] = 1
    else: data[0].rows[BASE + f"/contents/{contract.TRUST_PATH}?ref={SOURCE}"] = file_response(b"{}", contract.TRUST_PATH)
    with pytest.raises(ValueError):
        issue(data, monkeypatch)


def verified_output(raw):
    result = synthetic_verified_output(raw)
    verified = result[0]["verificationResult"]
    cert = verified["signature"]["certificate"]
    cert.update(subjectAlternativeName=ORIGIN + "/" + contract.SIGNER + "@refs/heads/main",
        buildSignerURI=ORIGIN + "/" + contract.SIGNER + "@refs/heads/main",
        buildConfigURI=ORIGIN + "/" + contract.WORKFLOW + "@refs/heads/main",
        runInvocationURI=ORIGIN + "/actions/runs/90/attempts/1")
    verified["statement"].update(subject=[{"name": contract.SUBJECT, "digest": {"sha256": digest(raw)}}],
        predicateType=contract.PREDICATE, predicate={"schema": contract.PREDICATE_SCHEMA, "preflight_sha256": digest(raw)})
    return result


def test_package_admission_uses_real_constraints_and_rechecks_freshness(monkeypatch):
    data = admission_data()
    raw = issue(data, monkeypatch)
    expected = contract.context(data[1], request())
    commands = []
    def run(command, directory):
        commands.append(command)
        assert (directory / "artifact").read_bytes() == raw
        return canonical_json(verified_output(raw))
    monkeypatch.setattr(crypto, "bounded_run", run)
    preflight.admit(raw, SYNTHETIC_BUNDLE, expected, data[2], data[3], clock=lambda: NOW)
    assert commands[0][commands[0].index("--signer-digest") + 1] == REVISION
    assert commands[0][commands[0].index("--predicate-type") + 1] == contract.PREDICATE
    for timestamp in (NOW - 1, NOW + 900):
        with pytest.raises(ValueError, match="expired"):
            preflight.admit(raw, SYNTHETIC_BUNDLE, expected, data[2], data[3], clock=lambda: timestamp)
    preflight.admit(raw, SYNTHETIC_BUNDLE, expected, data[2], data[3], clock=lambda: NOW + 1800, started_at=NOW)
    with pytest.raises(ValueError, match="expired"):
        preflight.admit(raw, SYNTHETIC_BUNDLE, expected, data[2], data[3], clock=lambda: NOW + 1801, started_at=NOW)


@pytest.mark.parametrize("field", ["issuer", "buildSignerDigest", "sourceRepositoryIdentifier", "sourceRepositoryOwnerIdentifier",
    "buildConfigURI", "buildConfigDigest", "sourceRepositoryDigest", "sourceRepositoryRef", "buildTrigger",
    "runInvocationURI", "subjectAlternativeName", "buildSignerURI", "runnerEnvironment"])
def test_wrong_verified_certificate_claims_are_rejected(monkeypatch, field):
    data = admission_data()
    raw = issue(data, monkeypatch)
    output = verified_output(raw)
    output[0]["verificationResult"]["signature"]["certificate"][field] = "wrong"
    monkeypatch.setattr(crypto, "bounded_run", lambda *args: canonical_json(output))
    with pytest.raises(ValueError):
        preflight.admit(raw, SYNTHETIC_BUNDLE, contract.context(data[1], request()), data[2], data[3], clock=lambda: NOW)


def test_catalogue_s4_profile_is_not_package_authority_and_genuine_old_evidence_rejects(monkeypatch):
    data = admission_data()
    raw = issue(data, monkeypatch)
    expected = contract.context(data[1], request())
    with monkeypatch.context() as patch:
        patch.setattr(crypto, "bounded_run", lambda *args: canonical_json(synthetic_verified_output(raw)))
        with pytest.raises(ValueError):
            preflight.admit(raw, SYNTHETIC_BUNDLE, expected, data[2], data[3], clock=lambda: NOW)
    for path in ("tests/fixtures/publication/package.sigstore.json", "tests/fixtures/publication/catalogue.sigstore.json",
                 "tests/fixtures/verifier_signer_probe/probe.sigstore.json"):
        with pytest.raises(ValueError):
            crypto.ConnectorSigstore().verify(raw, (ROOT / path).read_bytes(), expected=expected, trust=data[2])


@pytest.mark.parametrize("change", ["operation", "sha256", "commit", "run", "attempt", "acceptance", "implementation", "trust"])
def test_signed_preflight_cannot_be_replayed_for_changed_request(monkeypatch, change):
    data = admission_data()
    raw = issue(data, monkeypatch)
    expected = contract.context(data[1], request())
    if change == "operation": expected["request"]["operation"] = "stage"
    elif change == "sha256": expected["request"]["package"]["sha256"] = "f" * 64
    elif change == "commit": expected["caller_sha"] = "f" * 40
    elif change == "run": expected["run_id"] = 91
    elif change == "attempt": expected["run_attempt"] = 2
    elif change == "acceptance": expected["request"]["acceptance_only"] = True
    elif change == "implementation": data[2]["signer_revision"] = "f" * 40
    else: data[2]["schema"] = "atlas-publication-verifier-trust/v2"
    with pytest.raises(ValueError):
        contract.check_preflight(json.loads(raw), expected, data[2], data[3])


class PublicationModel(PackageProvider):
    def __init__(self, files, manifest, signed, data):
        super().__init__(files, manifest)
        self.tag = manifest["id"] + "-v" + manifest["version"]
        for path in ("/actions/runs/60", "/actions/runs/60/attempts/1"):
            self.rows[path]["head_branch"] = self.tag
        self.rows["/git/ref/tags/" + self.tag] = {"ref": "refs/tags/" + self.tag, "object": {"type": "commit", "sha": self.source}}
        self.draft_visibility = True
        self.token = "model-token"
        self.writes = []
        self.exists = False
        self.release_row.update(name=self.tag, tag_name=self.tag, draft=True, immutable=False)
        self.assets_list, self.data = [], {}
        self.lost = None
        self.mutable = False
        self.model_files = files
        for path, value in data[0].rows.items():
            if path.startswith(BASE) and not path.startswith(BASE + "/actions/runs/60"):
                self.rows[path[len(BASE):] or "/"] = deepcopy(value)
            elif not path.startswith(BASE):
                self.rows[path] = deepcopy(value)
        # Preserve the genuine build-model workflow; caller has independent ID 81.
        self.rows["/actions/workflows/80"]["path"] = ".github/workflows/release.yml"
        self.rows["/installation/repositories?per_page=100"] = {"total_count": 1, "repositories": [self.rows["/"]]}
        self.rows["/rulesets?includes_parents=true&per_page=6&page=1"] = signed["rulesets"]
        for row in signed["rulesets"]:
            self.rows[f"/rulesets/{row['id']}?includes_parents=true"] = row
        self.rows[f"/commits/{self.source}/pulls?per_page=100&page=1"] = [
            {"merge_commit_sha": self.source, "state": "closed", "merged_at": "2026-10-26T00:00:00Z",
             "base": {"ref": "main", "repo": self.rows["/"]}}]
        self.rows[f"/contents/.github/workflows?ref={self.source}"] = [
            {"path": ".github/workflows/release.yml", "sha": "a" * 40, "type": "file"}]
        self.rows[f"/commits/{self.source}/check-runs?check_name=validate&filter=latest&per_page=100"]["check_runs"][0]["head_sha"] = self.source
        prior = deepcopy(self.rows["/actions/runs/90"])
        prior.update(id=89, url=API + "/actions/runs/89", html_url=ORIGIN + "/actions/runs/89", status="completed", conclusion="success")
        self.rows["/actions/runs/89"] = prior
        self.rows["/actions/runs/89/attempts/1"] = deepcopy(prior)

    def json(self, method, path, **kwargs):
        if method == "GET":
            if path.startswith("/releases?per_page="):
                return [deepcopy(self.release_row)] if self.exists else []
            if path == "/git/ref/tags/" + self.tag and self.rows.get(path) is None:
                return None
            if path.startswith("/releases/") and not self.exists:
                return None
            if path == "/releases/tags/" + self.tag:
                path = "/releases/tags/" + TAG
            return super().json(method, path, **kwargs)
        self.writes.append((method, path, deepcopy(kwargs.get("payload"))))
        payload = kwargs["payload"]
        if path == "/git/refs":
            assert method == "POST"
            self.rows["/git/ref/tags/" + self.tag] = {"ref": "refs/tags/" + self.tag, "object": {"type": "commit", "sha": payload["sha"]}}
            result = self.rows["/git/ref/tags/" + self.tag]
        elif path == "/releases":
            assert payload["draft"] is True and payload["prerelease"] is False and payload["make_latest"] == "false"
            self.exists = True
            result = self.release_row
        else:
            assert method == "PATCH" and path == "/releases/100"
            assert payload == {"draft": False, "make_latest": "false"}
            self.release_row.update(draft=False, immutable=not self.mutable)
            result = self.release_row
        if self.lost == path:
            raise PublicationError("github_transport_failure")
        return deepcopy(result)

    def upload(self, release, name, raw):
        assert name not in {r["name"] for r in self.assets_list}
        self.writes.append(("POST", "upload:" + name, None))
        identity = 200 + len(self.assets_list)
        row = {"id": identity, "name": name, "url": API + f"/releases/assets/{identity}",
            "browser_download_url": ORIGIN + "/releases/download/" + self.tag + "/" + name,
            "uploader": deepcopy(self.actor), "state": "uploaded", "size": len(raw), "digest": "sha256:" + digest(raw)}
        self.assets_list.append(row)
        self.data[identity] = raw
        if self.lost == "upload:" + name:
            raise PublicationError("github_transport_failure")
        return deepcopy(row)


@pytest.fixture
def publication(tmp_path, monkeypatch):
    manifest = engine.release_connector.prepare(TAG, tmp_path)
    commit = manifest["distribution"]["provenance"]["source_commit"]
    files = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    bundle = structural_bundle(files["proxmox-0.2.1.tar.gz"], "package", "proxmox-0.2.1.tar.gz", commit=commit, run=60)
    (tmp_path / "package.sigstore.json").write_bytes(bundle)
    files["package.sigstore.json"] = bundle
    inputs = request("stage", commit=commit, sha256=digest(files["proxmox-0.2.1.tar.gz"]))
    data = admission_data(inputs, caller=commit)
    signed = json.loads(issue(data, monkeypatch))
    api = PublicationModel(files, manifest, signed, data)
    monkeypatch.setattr(final_verifier, "clean_source", lambda commit: None)
    monkeypatch.setattr(engine, "clean_source", lambda commit: None)
    return api, files, manifest, tmp_path, inputs, data, signed


def publisher(publication, inputs=None, *, reauthorize=None):
    api, files, manifest, directory, original, data, signed = publication
    inputs = deepcopy(inputs or original)
    expected = contract.context(data[1], inputs)
    signed = {**signed, "context": expected}
    return engine.PackagePublisher(api, StructuralVerifier(), inputs, data[2], json.loads(data[3]), expected,
        reauthorize=reauthorize or (lambda: signed), read_only=lambda: api)


def staged(publication):
    return publisher(publication).stage(publication[1], publication[2])


def finalize_input(receipt):
    return {"operation": "finalize", "acceptance_only": False,
        "package": {k: receipt[k] for k in ("tag", "source_commit", "sha256", "build_run_id", "artifact_id",
            "artifact_sha256", "release_id", "asset_id", "assets", "inventory_sha256", "staging_run_id")}}


def test_stage_stops_and_finalization_needs_new_explicit_dispatch(publication):
    receipt = staged(publication)
    api = publication[0]
    assert receipt["result"] == "staged_requires_separate_approval"
    assert len(receipt["assets"]) == 5 and api.release_row["draft"] is True
    assert not any(method == "PATCH" for method, _, _ in api.writes)
    inputs = finalize_input(receipt)
    with pytest.raises(ValueError, match="separate_approval"):
        publisher(publication, inputs)
    inputs["package"]["staging_run_id"] = 89
    result = publisher(publication, inputs).finalize(publication[3], publication[1], publication[2])
    assert result["result"] == "immutable_package_verified_catalogue_pending"
    assert sum(method == "PATCH" for method, _, _ in api.writes) == 1
    again = publisher(publication, inputs).finalize(publication[3], publication[1], publication[2])
    assert again == result
    assert sum(method == "PATCH" for method, _, _ in api.writes) == 1


@pytest.mark.parametrize("case", ["exists", "wrong_target", "conflicting_draft", "lost_response", "changed_rules", "changed_scope"])
def test_tag_is_create_only_and_stops_after_verified_tag(publication, case):
    api, _, _, _, original, _, _ = publication
    inputs = request("tag", commit=original["package"]["source_commit"], sha256=original["package"]["sha256"])
    api.rows["/git/ref/tags/" + TAG] = None
    if case == "exists": api.rows["/git/ref/tags/" + TAG] = {"object": {"type": "commit", "sha": api.source}}
    if case == "wrong_target": api.rows["/git/ref/tags/" + TAG] = {"object": {"type": "commit", "sha": "d" * 40}}
    if case == "conflicting_draft": api.exists = True
    if case == "lost_response": api.lost = "/git/refs"
    if case == "changed_rules": api.rows["/rulesets/3?includes_parents=true"] = {"id": 3}
    if case == "changed_scope": api.rows["/installation/repositories?per_page=100"]["total_count"] = 2
    if case == "lost_response":
        assert publisher(publication, inputs).tag()["result"] == "tag_observed_after_ambiguous_write_review_required"
        assert len(api.writes) == 1
    else:
        with pytest.raises(ValueError): publisher(publication, inputs).tag()
        assert api.writes == []


def test_authorized_tag_performs_exactly_one_ref_creation(publication):
    api = publication[0]
    api.rows["/git/ref/tags/" + TAG] = None
    inputs = request("tag", commit=api.source, sha256=publication[4]["package"]["sha256"])
    result = publisher(publication, inputs).tag()
    assert result["result"] == "tag_created_build_pending"
    assert api.writes == [("POST", "/git/refs", {"ref": "refs/tags/" + TAG, "sha": api.source})]


@pytest.mark.parametrize("path,field,value", [
    ("/actions/runs/60", "run_attempt", 2), ("/actions/runs/60/attempts/1", "conclusion", "failure"),
    ("/actions/runs/60", "actor", {"id": 1}), ("/actions/runs/60", "triggering_actor", {"id": 1}),
    ("/actions/runs/60", "head_sha", "f" * 40), ("/actions/runs/60", "path", contract.WORKFLOW),
    ("/environments/connector-release", "id", 1),
])
def test_failed_or_substituted_build_cannot_stage(publication, path, field, value):
    publication[0].rows[path][field] = value
    with pytest.raises(ValueError): staged(publication)
    assert publication[0].writes == []


@pytest.mark.parametrize("case", ["lost_create", "lost_upload", "partial_resume", "changed_id", "extra_asset", "bad_uploader"])
def test_draft_recovery_requires_approved_identity_and_original_bytes(publication, case):
    api, files, manifest, _, inputs, _, _ = publication
    if case == "lost_create":
        api.lost = "/releases"
        with pytest.raises(ValueError, match="ambiguous"): staged(publication)
        assert api.exists and len(api.writes) == 1
        with pytest.raises(ValueError, match="release_exists"): staged(publication)
        return
    api.lost = "upload:SHA256SUMS"
    with pytest.raises(ValueError, match="ambiguous"): staged(publication)
    assert len(api.assets_list) == 1 and api.release_row["draft"] is True
    if case == "lost_upload":
        assert len(api.writes) == 2
        return
    api.lost = None
    resume = deepcopy(inputs)
    resume["package"].update(release_id=100, assets=publisher(publication).assets(api.release_row, files, complete=False))
    if case == "changed_id": api.assets_list[0]["id"] += 100
    elif case == "extra_asset": api.assets_list[0]["name"] = "extra"
    elif case == "bad_uploader": api.assets_list[0]["uploader"] = {"id": 1}
    if case == "partial_resume":
        result = publisher(publication, resume).stage(files, manifest)
        assert len(result["assets"]) == 5
        assert sum(path == "upload:SHA256SUMS" for _, path, _ in api.writes) == 1
    else:
        with pytest.raises((ValueError, KeyError)): publisher(publication, resume).stage(files, manifest)


@pytest.mark.parametrize("case", ["mutable", "changed_id", "changed_digest", "changed_release", "changed_inventory", "lost_patch",
    "bad_author", "contradictory", "failed_reread", "bad_stage_actor"])
def test_finalize_rejects_approval_and_provider_conflicts_without_retry(publication, monkeypatch, case):
    receipt = staged(publication)
    api = publication[0]
    inputs = finalize_input(receipt)
    inputs["package"]["staging_run_id"] = 89
    if case == "mutable": api.mutable = True
    elif case == "changed_id": api.assets_list[0]["id"] += 10
    elif case == "changed_digest": inputs["package"]["sha256"] = "e" * 64
    elif case == "changed_release": inputs["package"]["release_id"] = 101
    elif case == "changed_inventory": inputs["package"]["assets"]["SHA256SUMS"]["id"] += 1
    elif case == "lost_patch": api.lost = "/releases/100"
    elif case == "bad_author": api.release_row["author"] = {"id": 1}
    elif case == "contradictory": api.change_after_download = True
    elif case == "failed_reread":
        monkeypatch.setattr(api, "asset_bytes", lambda *args: (_ for _ in ()).throw(PublicationError("unavailable")))
    elif case == "bad_stage_actor": api.rows["/actions/runs/89"]["triggering_actor"] = {"id": 1}
    if case == "lost_patch":
        assert publisher(publication, inputs).finalize(publication[3], publication[1], publication[2])["immutable"] is True
        assert sum(method == "PATCH" for method, _, _ in api.writes) == 1
    else:
        with pytest.raises((ValueError, KeyError)):
            publisher(publication, inputs).finalize(publication[3], publication[1], publication[2])
        assert sum(method == "PATCH" for method, _, _ in api.writes) <= 1


@pytest.mark.parametrize("case", ["unmerged", "unreviewed", "ci_failed", "workflow_changes"])
def test_source_review_ci_and_workflow_permissions_are_required(publication, case):
    api = publication[0]
    if case == "unmerged": api.rows[f"/compare/{api.source}...main"]["status"] = "diverged"
    elif case == "unreviewed": api.rows[f"/commits/{api.source}/pulls?per_page=100&page=1"][0]["merged_at"] = None
    elif case == "ci_failed": api.rows[f"/commits/{api.source}/check-runs?check_name=validate&filter=latest&per_page=100"]["check_runs"][0]["conclusion"] = "failure"
    else:
        caller = "d" * 40
        api.rows[f"/contents/.github/workflows?ref={caller}"] = [{"path": ".github/workflows/release.yml", "sha": caller, "type": "file"}]
        with pytest.raises(ValueError, match="workflows_write_required"):
            engine.source_authority(api, api.source, caller)
        return
    with pytest.raises(ValueError): engine.source_authority(api, api.source, api.source)


def zip_bytes(files, *, duplicate=False, mode=None):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in files.items():
            info = zipfile.ZipInfo(name)
            if mode is not None: info.external_attr = mode << 16
            archive.writestr(info, raw)
        if duplicate:
            with pytest.warns(UserWarning, match="Duplicate name"):
                archive.writestr(next(iter(files)), b"duplicate")
    return output.getvalue()


@pytest.mark.parametrize("case", ["valid", "extra", "duplicate", "symlink", "truncated", "oversized", "traversal"])
def test_actions_artifact_inventory_and_decompression_are_bounded(publication, case):
    files = deepcopy(publication[1])
    names = set(files)
    mode = None
    if case == "extra": files["extra"] = b"x"
    if case == "traversal": files["../manifest.json"] = files.pop("manifest.json")
    if case == "symlink": mode = stat.S_IFLNK | 0o777
    if case == "oversized": files["manifest.json"] = b"x" * (20 * 1024 * 1024 + 1)
    raw = zip_bytes(files, duplicate=case == "duplicate", mode=mode)
    if case == "truncated": raw = raw[:-10]
    if case == "valid": assert transport.unpack_artifact(raw, names) == files
    else:
        with pytest.raises(ValueError): transport.unpack_artifact(raw, names)


@pytest.mark.parametrize("operation", ["tag", "stage", "finalize"])
def test_acceptance_only_cannot_enter_any_publisher_operation(publication, operation):
    inputs = request(operation, acceptance_only=True)
    with pytest.raises(ValueError): publisher(publication, inputs)
    assert publication[0].writes == []


def test_workflow_pins_and_credential_isolation_are_inert_and_explicit():
    load = lambda name: yaml.load((ROOT / ".github/workflows" / name).read_text(), Loader=yaml.BaseLoader)
    caller, signer = load("connector-publish.yml"), load("connector-verifier.yml")
    assert caller["on"]["workflow_dispatch"]["inputs"]["acceptance_only"]["default"] == "true"
    publisher_job = caller["jobs"]["publisher"]
    assert "!inputs.acceptance_only" in publisher_job["if"] and "needs.preflight.result == 'success'" in publisher_job["if"]
    assert "CONNECTOR_PUBLICATION_ENABLED" in publisher_job["if"]
    assert caller["concurrency"] == {"group": "official-catalogue-publication", "cancel-in-progress": "false"}
    assert caller["jobs"]["preflight"]["uses"].endswith("@" + "0" * 40)
    assert publisher_job["env"]["ATLAS_IMPLEMENTATION_REVISION"] == "0" * 40
    steps = publisher_job["steps"]
    credentials = [i for i, step in enumerate(steps) if "PUBLICATION_APP_PRIVATE_KEY" in step.get("env", {})]
    authorize = next(i for i, step in enumerate(steps) if step.get("run") == "python tools/publish_connector.py authorize")
    prepare = next(i for i, step in enumerate(steps) if step.get("run") == "python tools/publish_connector.py prepare")
    assert credentials == [prepare + 1] and authorize < prepare
    assert caller["jobs"]["preflight"]["secrets"].keys() == {"VERIFICATION_APP_PRIVATE_KEY"}
    assert "workflow_call" in signer["on"] and len(signer["on"]) == 1
    assert "PUBLICATION_APP_PRIVATE_KEY" not in (ROOT / ".github/workflows/connector-verifier.yml").read_text()
    assert "secrets: inherit" not in (ROOT / ".github/workflows/connector-publish.yml").read_text()
    checked = json.loads((ROOT / contract.TRUST_PATH).read_bytes())
    assert checked["enabled"] is checked["live_signer_accepted"] is False
    with pytest.raises(ValueError, match="not_pinned"): contract.check_trust(checked, acceptance_only=True)


@pytest.mark.parametrize("acceptance,accepted,enabled,valid", [(True, False, False, True),
    (False, False, True, False), (False, True, False, False), (False, True, True, True)])
def test_actual_inline_guard_requires_reviewed_pin_and_acceptance_boundaries(tmp_path, acceptance, accepted, enabled, valid):
    trust = admission_data()[2]
    trust.update(enabled=enabled, live_signer_accepted=accepted)
    job = {"workflow_ref": REPOSITORY + "/" + contract.SIGNER + "@refs/heads/main", "workflow_sha": REVISION,
        "workflow_repository": REPOSITORY, "workflow_file_path": contract.SIGNER}
    workflow = yaml.load((ROOT / ".github/workflows/connector-verifier.yml").read_text(), Loader=yaml.BaseLoader)
    program = workflow["jobs"]["verify"]["steps"][0]["run"].split("python3 - <<'PY'\n")[1].rsplit("\nPY", 1)[0]
    result = subprocess.run([sys.executable, "-c", program], capture_output=True, timeout=10,
        env={"JOB_CONTEXT": json.dumps(job), "CONNECTOR_VERIFICATION_POLICY": json.dumps(trust),
             "ACCEPTANCE_ONLY": str(acceptance).lower(), "GITHUB_OUTPUT": str(tmp_path / "output")})
    assert (result.returncode == 0) == valid


@pytest.mark.parametrize("case", ["missing_bundle", "wrong_bundle_run", "modified_archive", "wrong_source", "reserialized_metadata"])
def test_stage_authenticates_original_build_bytes_before_any_write(publication, case):
    api, original, manifest, _, _, _, _ = publication
    files = deepcopy(original)
    manifest = deepcopy(manifest)
    if case == "missing_bundle": files.pop("package.sigstore.json")
    elif case == "wrong_bundle_run":
        files["package.sigstore.json"] = structural_bundle(files["proxmox-0.2.1.tar.gz"], "package", "proxmox-0.2.1.tar.gz", commit=api.source, run=61)
    elif case == "modified_archive": files["proxmox-0.2.1.tar.gz"] += b"tampered"
    elif case == "wrong_source": manifest["distribution"]["provenance"]["source_commit"] = "c" * 40
    else: files["manifest.json"] = json.dumps(manifest).encode()
    with pytest.raises(ValueError): publisher(publication).stage(files, manifest)
    assert api.writes == []


@pytest.mark.parametrize("case", ["valid", "different_run", "different_id", "expired", "extra_match", "wrong_digest", "changed_detail"])
def test_exact_actions_artifact_is_bound_to_original_run(publication, case, monkeypatch):
    files = publication[1]
    package = deepcopy(publication[4]["package"])
    raw = zip_bytes(files)
    package["artifact_sha256"] = digest(raw)
    detail = {"id": 70, "name": contract.ARTIFACT_NAME, "size_in_bytes": len(raw), "expired": False,
        "digest": "sha256:" + digest(raw), "url": API + "/actions/artifacts/70",
        "archive_download_url": API + "/actions/artifacts/70/zip", "workflow_run": {"id": 60,
            "repository_id": 1414494920, "head_repository_id": 1414494920,
            "head_branch": TAG, "head_sha": package["source_commit"]}}
    if case == "different_run": detail["workflow_run"]["id"] = 61
    if case == "different_id": detail["id"] = 71
    if case == "expired": detail["expired"] = True
    if case == "wrong_digest": detail["digest"] = "sha256:" + "f" * 64
    listings = [detail, deepcopy(detail)] if case == "extra_match" else [detail]
    client = transport.ConnectorGithub("model-read-token")
    reads, downloads = [], []
    def get(method, path, **kwargs):
        assert method == "GET"
        reads.append(path)
        if "/runs/60/artifacts" in path: return {"total_count": len(listings), "artifacts": deepcopy(listings)}
        result = deepcopy(detail)
        if case == "changed_detail" and reads.count(path) == 2: result["expired"] = True
        return result
    monkeypatch.setattr(client, "json", get)
    monkeypatch.setattr(client, "artifact_zip", lambda *args: downloads.append(args) or raw)
    if case == "valid": assert client.artifact(package) == raw
    else:
        with pytest.raises(ValueError): client.artifact(package)
    assert len(downloads) <= 1


@pytest.mark.parametrize("case", ["valid", "app", "installation", "excessive", "effective", "scope"])
def test_publisher_app_installation_and_token_scope_are_checked_locally(monkeypatch, case):
    repo = admission_data()[0].rows[BASE]
    rows = {"/app": {"id": 5422372, "slug": "atlas-catalogue-publisher", "owner": {"id": 93822871},
        "permissions": deepcopy(APP_PERMISSIONS)}, "/app/installations/174027755": {"id": 174027755,
        "app_id": 5422372, "account": {"id": 93822871}, "repository_selection": "selected",
        "permissions": deepcopy(APP_PERMISSIONS), "suspended_at": None},
        "/app/installations/174027755/access_tokens": {"permissions": deepcopy(APP_PERMISSIONS), "token": "model-token"}}
    if case == "app": rows["/app"]["id"] = 1
    if case == "installation": rows["/app/installations/174027755"]["id"] = 1
    if case == "excessive": rows["/app/installations/174027755"]["permissions"]["workflows"] = "write"
    if case == "effective": rows["/app/installations/174027755/access_tokens"]["permissions"]["workflows"] = "write"
    calls = []
    class Auth:
        def json(self, path, token, **kwargs):
            assert token == "model-jwt"
            calls.append(path)
            return deepcopy(rows[path])
    class Client:
        def __init__(self, token, **kwargs):
            assert token == "model-token" and kwargs == {"draft_visibility": True}
        def json(self, method, path, **kwargs):
            assert method == "GET" and path == "/installation/repositories?per_page=100"
            return {"total_count": 2 if case == "scope" else 1, "repositories": [repo]}
    monkeypatch.setattr(transport, "publisher_jwt", lambda key: "model-jwt")
    environ = {"PUBLICATION_APP_ID": "5422372", "PUBLICATION_APP_PRIVATE_KEY": "model-key"}
    if case == "valid": assert isinstance(transport.mint_publisher(environ, auth=Auth(), client=Client), Client)
    else:
        with pytest.raises(ValueError): transport.mint_publisher(environ, auth=Auth(), client=Client)
    assert "PUBLICATION_APP_PRIVATE_KEY" not in environ
    assert calls.count("/app/installations/174027755/access_tokens") <= 1
    if case in {"app", "installation", "excessive"}:
        assert "/app/installations/174027755/access_tokens" not in calls


@pytest.mark.parametrize("connector", ["docker", "unifi", "future-hypervisor"])
def test_generic_connector_uses_identical_stage_and_finalize_boundaries(tmp_path, monkeypatch, connector):
    source = tmp_path / "source"
    target = source / "connectors" / connector
    shutil.copytree(ROOT / "connectors/proxmox", target)
    shutil.copyfile(ROOT / "LICENSE", source / "LICENSE")
    (source / "catalogue/publication").mkdir(parents=True)
    shutil.copyfile(ROOT / contract.POLICY_PATH, source / contract.POLICY_PATH)
    for directory in (target, target / "releases/0.2.1"):
        path = directory / "manifest.json"
        value = json.loads(path.read_bytes())
        value["id"] = connector
        path.write_text(json.dumps(value))
        path = directory / "sbom.spdx.json"
        value = json.loads(path.read_bytes())
        value["name"] = value["name"].replace("atlas-proxmox-", "atlas-" + connector + "-")
        value["documentNamespace"] = value["documentNamespace"].replace("/proxmox/", "/" + connector + "/")
        value["packages"][0]["name"] = "atlas-" + connector
        path.write_text(json.dumps(value))
    original_output = subprocess.check_output
    def source_head(args, **kwargs):
        if args == ["git", "rev-parse", "HEAD"] and kwargs.get("cwd") == source:
            return SOURCE + "\n"
        return original_output(args, **kwargs)
    monkeypatch.setattr(subprocess, "check_output", source_head)
    tag = connector + "-v0.2.1"
    directory = tmp_path / "candidate"
    with engine.package_source(source):
        manifest = engine.release_connector.prepare(tag, directory)
        files = {p.name: p.read_bytes() for p in directory.iterdir()}
        name = connector + "-0.2.1.tar.gz"
        bundle = structural_bundle(files[name], "package", name, commit=SOURCE, run=60)
        files["package.sigstore.json"] = bundle
        (directory / "package.sigstore.json").write_bytes(bundle)
        inputs = request("stage", sha256=digest(files[name]))
        inputs["package"]["tag"] = tag
        data = admission_data(inputs)
        signed = json.loads(issue(data, monkeypatch))
        api = PublicationModel(files, manifest, signed, data)
        monkeypatch.setattr(final_verifier, "clean_source", lambda commit: None)
        publication = api, files, manifest, directory, inputs, data, signed
        receipt = staged(publication)
        assert receipt["tag"] == tag and api.release_row["draft"] is True
        approve = finalize_input(receipt)
        approve["package"]["staging_run_id"] = 89
        result = publisher(publication, approve).finalize(directory, files, manifest)
        assert result["registry_entry"]["manifest"]["id"] == connector
        assert result["result"] == "immutable_package_verified_catalogue_pending"


@pytest.mark.parametrize("case", ["valid", "modified_bytes", "wrong_digest", "wrong_invocation"])
def test_precredential_preparation_authenticates_the_original_artifact(publication, tmp_path, monkeypatch, case):
    api, files, manifest, _, inputs, _, _ = publication
    original_prepare = engine.release_connector.prepare
    # Source cleanliness and tracked-input rejection are covered by real Git tests
    # in test_connector_release. This modeled checkout runs the production package,
    # artifact and provenance checks without pretending the working tree is clean.
    monkeypatch.setattr(engine.release_connector, "prepare",
        lambda tag, directory, **kwargs: original_prepare(tag, directory))
    observed = deepcopy(files)
    package = deepcopy(inputs["package"])
    if case == "modified_bytes": observed["manifest.json"] += b" "
    if case == "wrong_digest": package["sha256"] = "f" * 64
    if case == "wrong_invocation": observed["package.sigstore.json"] = structural_bundle(
        files["proxmox-0.2.1.tar.gz"], "package", "proxmox-0.2.1.tar.gz", commit=api.source, run=61)
    monkeypatch.setattr(api, "artifact", lambda package: zip_bytes(observed), raising=False)
    directory = tmp_path / "new-candidate"
    if case == "valid":
        result, observed_manifest = engine.prepare_candidate(api, StructuralVerifier(), directory,
            package, "stage", api.source)
        assert result == files and observed_manifest == manifest
        assert {p.name: p.read_bytes() for p in directory.iterdir()} == files
    else:
        with pytest.raises(ValueError): engine.prepare_candidate(api, StructuralVerifier(), directory,
            package, "stage", api.source)
    assert api.writes == []


def test_different_readmission_cannot_reach_a_write(publication):
    signed = deepcopy(publication[6])
    signed["context"]["run_id"] = 91
    with pytest.raises(ValueError, match="readmission_binding"):
        publisher(publication, reauthorize=lambda: signed).stage(publication[1], publication[2])
    assert publication[0].writes == []


@pytest.mark.parametrize("case", ["valid", "http", "host", "userinfo", "port", "fragment", "oversized", "truncated", "timeout"])
def test_artifact_redirect_is_bounded_and_never_forwards_credentials(monkeypatch, case):
    destination = "https://productionresultssa.blob.core.windows.net/retained/zip?sig=model"
    if case == "http": destination = destination.replace("https:", "http:")
    elif case == "host": destination = "https://attacker.example/zip"
    elif case == "userinfo": destination = "https://token@productionresultssa.blob.core.windows.net/zip"
    elif case == "port": destination = "https://productionresultssa.blob.core.windows.net:444/zip"
    elif case == "fragment": destination += "#fragment"
    payload = b"model-zip-bytes"
    body = payload + b"x" if case == "oversized" else payload[:-1] if case == "truncated" else payload
    calls = []
    class Response(io.BytesIO):
        status = 200
        headers = Message()
    class Opener:
        def open(self, request, **kwargs):
            calls.append(request)
            if len(calls) == 1:
                assert request.full_url == API + "/actions/artifacts/70/zip"
                assert request.get_header("Authorization") == "Bearer model-token"
                if case == "timeout": raise TimeoutError()
                headers = Message()
                headers["Location"] = destination
                raise urllib.error.HTTPError(request.full_url, 302, "model", headers, None)
            assert not request.has_header("Authorization")
            assert request.full_url == destination
            return Response(body)
    client = transport.ConnectorGithub("model-token")
    client.opener = Opener()
    if case == "valid": assert client.artifact_zip(70, len(payload)) == payload
    else:
        with pytest.raises(ValueError): client.artifact_zip(70, len(payload))
    assert len(calls) == (2 if case in {"valid", "oversized", "truncated"} else 1)


def test_publisher_auth_transport_cannot_be_used_for_repository_writes():
    client = transport.PublisherAuthentication()
    for path, mint in (("/repos/benchristian88/atlas-connectors/git/refs", True),
                       ("/app/installations/1/access_tokens", True), ("/app/installations/174027755/access_tokens", False)):
        with pytest.raises(ValueError, match="auth_endpoint"):
            client.json(path, "model-token", mint=mint)


def test_publisher_jwt_genuine_ephemeral_signature_has_the_publisher_issuer(tmp_path):
    # Generated ephemeral test key, never an App credential or committed fixture.
    key = subprocess.run(["/usr/bin/openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048"],
        capture_output=True, check=True, timeout=10).stdout
    token = transport.publisher_jwt(key.decode())
    header, claims, signature = token.split(".")
    decode = lambda value: base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    assert json.loads(decode(header)) == {"alg": "RS256", "typ": "JWT"}
    value = json.loads(decode(claims))
    assert value["iss"] == "5422372" and value["iss"] != "5424851"
    assert value["exp"] - value["iat"] == 360
    public = subprocess.run(["/usr/bin/openssl", "pkey", "-pubout"], input=key,
        capture_output=True, check=True, timeout=10).stdout
    (tmp_path / "public.pem").write_bytes(public)
    (tmp_path / "signature").write_bytes(decode(signature))
    verified = subprocess.run(["/usr/bin/openssl", "dgst", "-sha256", "-verify", str(tmp_path / "public.pem"),
        "-signature", str(tmp_path / "signature")], input=(header + "." + claims).encode(),
        capture_output=True, check=True, timeout=10)
    assert verified.stdout.strip() == b"Verified OK"
