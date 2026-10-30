# SPDX-License-Identifier: Apache-2.0
"""Successor regressions. Provider fixtures are models, never live authority."""
from copy import deepcopy
from email.message import Message
import hashlib
import json
from pathlib import Path
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import connector_publication_contract as contract
import publish_connector as engine
from connector_publication_github import ConnectorGithub
from publication_contract import API, PublicationError, canonical_json, digest
from publication_verify import ORIGIN
from test_connector_publication import (REVIEWED_IMPLEMENTATION, finalize_input, publication, publisher, request,
    staged)
from test_publication_authorization import file_response
from test_publication_state import StructuralVerifier
from test_publication_transport import Opener, Response, failure
from verify_connector_release import asset_download_identity


@pytest.fixture
def draft():
    return json.loads((ROOT / "tests/fixtures/connector_draft_provider/draft.json").read_bytes())


@pytest.mark.parametrize("published", [False, True])
@pytest.mark.parametrize("tagged", [False, True])
def test_draft_selector_has_no_published_authority(draft, published, tagged):
    asset = draft["assets"][0]
    if tagged:
        asset["browser_download_url"] = ORIGIN + "/releases/download/proxmox-v0.2.1/SHA256SUMS"
    draft["draft"] = not published
    if published and not tagged:
        with pytest.raises(PublicationError, match="download_url"):
            asset_download_identity(asset, draft, name="SHA256SUMS", tag=draft["tag_name"], allow_draft=True)
    else:
        asset_download_identity(asset, draft, name="SHA256SUMS", tag=draft["tag_name"], allow_draft=True)


@pytest.mark.parametrize("tag", ["docker-v1.2.3", "unifi-v7.8.9", "future-hypervisor-v3.4.5"])
def test_draft_url_validation_is_generic_across_connectors_and_versions(draft, tag):
    draft.update(tag_name=tag, name=tag)
    asset = draft["assets"][0]
    name = tag.replace("-v", "-") + ".tar.gz"
    asset["browser_download_url"] = draft["html_url"].replace("/tag/", "/download/") + "/" + name
    asset_download_identity(asset, draft, name=name, tag=tag, allow_draft=True)
    with pytest.raises(PublicationError, match="release_not_immutable"):
        asset_download_identity(asset, draft, name=name, tag=tag)


@pytest.mark.parametrize("change", ["host", "repository", "release_api", "assets_api", "selector", "name", "path",
    "userinfo", "port", "query", "fragment", "encoded", "traversal", "backslash", "foreign_html", "arbitrary_html"])
def test_draft_url_is_bound_to_authenticated_release_and_official_structure(draft, change):
    asset = draft["assets"][0]
    url = asset["browser_download_url"]
    if change == "host": url = url.replace("github.com", "github.com.attacker.example")
    elif change == "repository": url = url.replace("/atlas-connectors/", "/other-repository/")
    elif change == "release_api": draft["url"] = API + "/releases/101"
    elif change == "assets_api": draft["assets_url"] = API + "/releases/101/assets"
    elif change == "selector": url = url.replace("0123456789abcdef0123", "abcdef0123456789abcd")
    elif change == "name": url = url.replace("SHA256SUMS", "manifest.json")
    elif change == "path": url = url.replace("/download/", "/tag/")
    elif change == "userinfo": url = url.replace("https://", "https://token@")
    elif change == "port": url = url.replace("github.com/", "github.com:443/")
    elif change == "query": url += "?download=1"
    elif change == "fragment": url += "#SHA256SUMS"
    elif change == "encoded": url = url.replace("SHA256SUMS", "%53HA256SUMS")
    elif change == "traversal": url = url.replace("/SHA256SUMS", "/../SHA256SUMS")
    elif change == "backslash": url = url.replace("/SHA256SUMS", "\\SHA256SUMS")
    elif change == "foreign_html": draft["html_url"] = draft["html_url"].replace("atlas-connectors", "other")
    else: draft["html_url"] = ORIGIN + "/releases/tag/arbitrary"
    asset["browser_download_url"] = url
    with pytest.raises(PublicationError):
        asset_download_identity(asset, draft, name="SHA256SUMS", tag="proxmox-v0.2.1", allow_draft=True)


@pytest.mark.parametrize("change", ["id", "api", "name", "state", "size", "digest_missing", "digest_null",
    "digest_wrong", "uploader_id", "uploader_login", "uploader_type", "bytes", "truncated", "duplicate_id", "extra"])
def test_existing_draft_assets_retain_full_identity_and_bytes_checks(publication, change):
    api, files, _, _, _, _, _ = publication
    api.exists = True
    api.upload(api.release_row, "SHA256SUMS", files["SHA256SUMS"])
    asset = api.assets_list[0]
    if change == "id": asset["id"] = False
    elif change == "api": asset["url"] = API + "/releases/assets/201"
    elif change == "name": asset["name"] = "manifest.json"
    elif change == "state": asset["state"] = "starter"
    elif change == "size": asset["size"] += 1
    elif change == "digest_missing": asset.pop("digest")
    elif change == "digest_null": asset["digest"] = None
    elif change == "digest_wrong": asset["digest"] = "sha256:" + "f" * 64
    elif change.startswith("uploader_"):
        asset["uploader"][change.removeprefix("uploader_")] = "wrong"
    elif change == "bytes": api.data[asset["id"]] = b"x" * len(files["SHA256SUMS"])
    elif change == "truncated": api.data[asset["id"]] = files["SHA256SUMS"][:-1]
    elif change == "duplicate_id":
        api.upload(api.release_row, "manifest.json", files["manifest.json"])
        api.assets_list[1]["id"] = asset["id"]
        api.assets_list[1]["url"] = asset["url"]
    else:
        api.upload(api.release_row, "extra", b"unexpected")
    with pytest.raises((PublicationError, KeyError)):
        publisher(publication).assets(api.release_row, files, complete=False)


def resume_input(publication):
    api, files = publication[:2]
    inputs = deepcopy(publication[4])
    inputs["package"].update(release_id=100, assets=publisher(publication).assets(api.release_row, files, complete=False))
    return inputs


def test_delayed_digest_stops_then_requires_new_explicit_resume(publication):
    api, files, manifest = publication[:3]
    api.exists = True
    api.upload(api.release_row, "SHA256SUMS", files["SHA256SUMS"])
    before = len(api.writes)
    expected = api.assets_list[0].pop("digest")
    with pytest.raises(PublicationError, match="asset_digest"):
        publisher(publication).assets(api.release_row, files, complete=False)
    assert len(api.writes) == before
    api.assets_list[0]["digest"] = expected
    with pytest.raises(PublicationError, match="release_exists"):
        staged(publication)
    result = publisher(publication, resume_input(publication)).stage(files, manifest)
    assert result["result"] == "staged_requires_separate_approval"
    assert len(api.writes) - before == 4
    assert not any(method == "PATCH" for method, _, _ in api.writes)


@pytest.mark.parametrize("observation_fails", [False, True])
def test_upload_failure_preserves_primary_and_secondary_diagnostics(publication, monkeypatch, observation_fails):
    api, files, manifest = publication[:3]
    subject = publisher(publication)
    original_assets = subject.assets
    failed = False
    def upload(*args):
        nonlocal failed
        failed = True
        raise PublicationError("asset_bytes_mismatch")
    def assets(*args, **kwargs):
        if failed and observation_fails:
            raise PublicationError("connector_asset_download_url")
        return original_assets(*args, **kwargs)
    monkeypatch.setattr(api, "upload", upload)
    monkeypatch.setattr(subject, "assets", assets)
    with pytest.raises(PublicationError, match="connector_upload_ambiguous_review_required"):
        subject.stage(files, manifest)
    assert subject.write_diagnostic["primary_reason"] == "asset_bytes_mismatch"
    if observation_fails:
        assert subject.write_diagnostic["observation_reason"] == "connector_asset_download_url"
    assert len(api.writes) == 1  # Draft creation only; no upload retry.


@pytest.mark.parametrize("error", [RuntimeError("private body\nsecret"),
    PublicationError("https://provider.example/private?token=secret"), PublicationError("secret"),
    PublicationError("connector_asset_digest\nsecret")])
def test_diagnostics_cannot_emit_arbitrary_exception_text(error):
    assert engine.safe_reason(error) == "connector_publication_failed_read_only_review_required"


def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def repin(publication):
    """Independently reviewed S and C; only three literal caller pins differ."""
    api, _, _, _, _, data, signed = publication
    successor, caller = "e" * 40, "d" * 40
    raw = (ROOT / ".github/workflows/connector-publish.yml").read_bytes()
    after = raw.replace(REVIEWED_IMPLEMENTATION.encode(), successor.encode())
    tree = [{"path": ".github/workflows/" + p.name, "sha": blob(p.read_bytes()), "type": "file"}
            for p in sorted((ROOT / ".github/workflows").glob("*.yml"))]
    for sha in (api.source, successor, caller):
        api.rows[f"/contents/.github/workflows?ref={sha}"] = deepcopy(tree)
        content = after if sha == caller else raw
        next(r for r in api.rows[f"/contents/.github/workflows?ref={sha}"] if r["path"] == contract.WORKFLOW)["sha"] = blob(content)
        api.rows[f"/contents/{contract.WORKFLOW}?ref={sha}"] = file_response(content, contract.WORKFLOW)
        api.rows[f"/compare/{sha}...main"] = {"status": "ahead", "merge_base_commit": {"sha": sha}}
        checks = deepcopy(api.rows[f"/commits/{api.source}/check-runs?check_name=validate&filter=latest&per_page=100"])
        checks["check_runs"][0]["head_sha"] = sha
        api.rows[f"/commits/{sha}/check-runs?check_name=validate&filter=latest&per_page=100"] = checks
        review = deepcopy(api.rows[f"/commits/{api.source}/pulls?per_page=100&page=1"])
        review[0]["merge_commit_sha"] = sha
        api.rows[f"/commits/{sha}/pulls?per_page=100&page=1"] = review
    data[1].update(GITHUB_SHA=caller, ATLAS_IMPLEMENTATION_REVISION=successor)
    data[2]["signer_revision"] = successor
    api.rows["/branches/main"]["commit"]["sha"] = caller
    for identity in (89, 90):
        for suffix in ("", "/attempts/1"):
            run = api.rows[f"/actions/runs/{identity}" + suffix]
            run.update(head_sha=caller, referenced_workflows=[{
                "path": "benchristian88/atlas-connectors/" + contract.SIGNER + "@" + successor, "sha": successor}])
    signed["implementation_sha"] = successor
    return successor, caller


def test_same_workflows_partial_resume_preserves_existing_asset_and_original_bytes(publication):
    api, files, manifest = publication[:3]
    api.exists = True
    api.upload(api.release_row, "SHA256SUMS", files["SHA256SUMS"])
    existing = deepcopy(api.assets_list[0])
    inputs = resume_input(publication)
    before = len(api.writes)
    receipt = publisher(publication, inputs).stage(files, manifest)
    assert receipt["result"] == "staged_requires_separate_approval"
    assert len(api.writes) - before == 4
    assert api.assets_list[0] == existing
    assert api.data == {receipt["assets"][n]["id"]: raw for n, raw in files.items()}
    assert all(method == "POST" and path.startswith("upload:") for method, path, _ in api.writes)
    assert sum(path == "upload:SHA256SUMS" for _, path, _ in api.writes) == 1


def test_complete_staging_creates_draft_and_uploads_all_five_original_assets(publication):
    api, files = publication[:2]
    receipt = staged(publication)
    assert receipt["result"] == "staged_requires_separate_approval"
    assert api.writes[0][0:2] == ("POST", "/releases")
    assert [path for _, path, _ in api.writes[1:]] == ["upload:" + n for n in sorted(files)]
    assert len(receipt["assets"]) == 5 and api.release_row["draft"] is True
    assert api.data == {receipt["assets"][n]["id"]: raw for n, raw in files.items()}


def test_finalize_independent_verifier_rejects_stale_draft_download_url(publication, monkeypatch):
    receipt = staged(publication)
    api = publication[0]
    approve = finalize_input(receipt)
    approve["package"]["staging_run_id"] = 89
    original = api.json
    def json_response(method, path, **kwargs):
        result = original(method, path, **kwargs)
        if method == "PATCH":
            api.assets_list[0]["browser_download_url"] = ORIGIN + "/releases/download/untagged-" + "a" * 40 + "/SHA256SUMS"
        return result
    monkeypatch.setattr(api, "json", json_response)
    with pytest.raises(PublicationError, match="release_asset_identity"):
        publisher(publication, approve).finalize(publication[3], publication[1], publication[2])
    assert sum(method == "PATCH" for method, _, _ in api.writes) == 1


@pytest.mark.parametrize("changed", [False, True])
def test_independent_published_verification_after_repin_remains_read_only(publication, changed):
    receipt = staged(publication)
    api, files, manifest, directory = publication[:4]
    approve = finalize_input(receipt)
    approve["package"]["staging_run_id"] = 89
    publisher(publication, approve).finalize(directory, files, manifest)
    repin(publication)
    before = list(api.writes)
    if changed: api.assets_list[0]["digest"] = "sha256:" + "f" * 64
    package = approve["package"]
    def verify():
        return engine.verify_connector_release.verify(api, StructuralVerifier(), directory,
            tag=package["tag"], commit=package["source_commit"], expected_digest=package["sha256"],
            run_id=package["build_run_id"], release_id=package["release_id"],
            asset_id=package["asset_id"], approved_assets=package["assets"])
    if changed:
        with pytest.raises(PublicationError): verify()
    else:
        assert verify()["immutable"] is True
    assert api.writes == before


@pytest.mark.parametrize("case", ["tag", "stage_new", "stage_resume", "finalize_draft", "finalize_published"])
def test_every_publication_operation_rejects_even_reviewed_pin_only_workflow_differences(publication, case):
    api, files, manifest, directory, original = publication[:5]
    if case == "tag":
        inputs = request("tag", commit=api.source, sha256=original["package"]["sha256"])
        api.rows["/git/ref/tags/" + api.tag] = None
    elif case == "stage_new":
        inputs = original
    elif case == "stage_resume":
        api.exists = True
        api.upload(api.release_row, "SHA256SUMS", files["SHA256SUMS"])
        inputs = resume_input(publication)
    else:
        receipt = staged(publication)
        inputs = finalize_input(receipt)
        inputs["package"]["staging_run_id"] = 89
        if case == "finalize_published":
            publisher(publication, inputs).finalize(directory, files, manifest)
    repin(publication)
    before = list(api.writes)
    subject = publisher(publication, inputs)
    with pytest.raises(PublicationError, match="^connector_workflows_write_required$"):
        if case == "tag": subject.tag()
        elif case.startswith("stage"): subject.stage(files, manifest)
        else: subject.finalize(directory, files, manifest)
    assert api.writes == before


@pytest.mark.parametrize("operation", ["tag", "stage", "finalize"])
@pytest.mark.parametrize("release_id", [None, 100])
def test_workflow_mismatch_rejects_preparation_before_build_or_artifact_download(publication, tmp_path, monkeypatch,
        operation, release_id):
    api = publication[0]
    _, caller = repin(publication)
    package = {**publication[4]["package"], "release_id": release_id}
    def forbidden(*args, **kwargs):
        pytest.fail("workflow mismatch reached package preparation or artifact download")
    monkeypatch.setattr(engine.release_connector, "prepare", forbidden)
    monkeypatch.setattr(api, "artifact", forbidden, raising=False)
    with pytest.raises(PublicationError, match="^connector_workflows_write_required$"):
        engine.prepare_candidate(api, StructuralVerifier(), tmp_path / "prepared", package, operation, caller)
    assert api.writes == []


@pytest.mark.parametrize("change", ["extra", "deleted", "duplicate", "directory", "non_file", "bad_sha",
    "foreign_path", "invalid_row", "empty"])
def test_whole_workflow_directory_is_required_and_malformed_trees_fail_closed(publication, change):
    api = publication[0]
    caller = "d" * 40
    tree = deepcopy(api.rows[f"/contents/.github/workflows?ref={api.source}"])
    api.rows[f"/contents/.github/workflows?ref={caller}"] = tree
    if change == "extra": tree.append({"path": ".github/workflows/new.yml", "sha": "f" * 40, "type": "file"})
    elif change == "deleted": tree.clear()
    elif change == "duplicate": tree.append(deepcopy(tree[0]))
    elif change == "directory": tree[0]["type"] = "dir"
    elif change == "non_file": tree[0]["type"] = "symlink"
    elif change == "bad_sha": tree[0]["sha"] = "main"
    elif change == "foreign_path": tree[0]["path"] = ".github/workflows/../other.yml"
    elif change == "invalid_row": tree[0] = None
    else: api.rows[f"/contents/.github/workflows?ref={api.source}"] = []
    with pytest.raises(PublicationError): engine.source_authority(api, api.source, caller)
    assert api.writes == []


@pytest.mark.parametrize("change", ["failed", "retried", "failed_first_attempt", "stale_admission"])
def test_same_workflows_resume_rejects_failed_builds_and_stale_admission(publication, change):
    api, files, manifest = publication[:3]
    api.exists = True
    api.upload(api.release_row, "SHA256SUMS", files["SHA256SUMS"])
    inputs = resume_input(publication)
    before = list(api.writes)
    if change == "failed": api.rows["/actions/runs/60"]["conclusion"] = "failure"
    elif change == "retried": api.rows["/actions/runs/60"]["run_attempt"] = 2
    elif change == "failed_first_attempt": api.rows["/actions/runs/60/attempts/1"]["conclusion"] = "failure"
    def expired(): raise PublicationError("connector_admission_expired")
    subject = publisher(publication, inputs, reauthorize=expired if change == "stale_admission" else None)
    with pytest.raises(PublicationError): subject.stage(files, manifest)
    assert api.writes == before


@pytest.mark.parametrize("change", ["release_id", "assets_api_reread", "selector_reread", "published_during_download"])
def test_draft_release_identity_cannot_change_around_asset_verification(publication, monkeypatch, change):
    api, files = publication[:2]
    api.exists = True
    api.upload(api.release_row, "SHA256SUMS", files["SHA256SUMS"])
    if change == "release_id":
        api.release_row["id"] = 101
    else:
        original = api.asset_bytes
        def download(*args, **kwargs):
            raw = original(*args, **kwargs)
            if change == "assets_api_reread": api.release_row["assets_url"] = API + "/releases/101/assets"
            elif change == "selector_reread": api.release_row["html_url"] = ORIGIN + "/releases/tag/untagged-" + "b" * 40
            else: api.release_row.update(draft=False, immutable=True)
            return raw
        monkeypatch.setattr(api, "asset_bytes", download)
    with pytest.raises(PublicationError):
        publisher(publication).assets({**api.release_row, "id": 100, "draft": True}, files, complete=False)


@pytest.mark.parametrize("change", ["valid", "host", "repo", "path", "userinfo", "port", "fragment", "relative", "whitespace",
    "encoded", "double", "oversize", "truncated", "length", "digest", "http"])
def test_numeric_asset_download_is_repository_bound_and_credential_safe(change):
    raw = b"original signed bytes"
    destination = "https://release-assets.githubusercontent.com/github-production-release-asset/1414494920/01234567-89ab-cdef-0123-456789abcdef?sig=model"
    if change == "host": destination = destination.replace("release-assets.githubusercontent.com", "attacker.example")
    elif change == "repo": destination = destination.replace("1414494920", "1414494921")
    elif change == "path": destination = destination.replace("github-production-release-asset", "arbitrary")
    elif change == "userinfo": destination = destination.replace("https://", "https://token@")
    elif change == "port": destination = destination.replace(".com/", ".com:443/")
    elif change == "fragment": destination += "#part"
    elif change == "relative": destination = "/relative"
    elif change == "whitespace": destination += "\nsecret"
    elif change == "encoded": destination = destination.replace("1414494920", "%311414494920")
    elif change == "http": destination = destination.replace("https:", "http:")
    headers = Message()
    headers["Content-Type"] = "application/octet-stream"
    if change == "length": headers["Content-Length"] = str(len(raw) + 1)
    body = raw + b"x" if change == "oversize" else raw[:-1] if change == "truncated" else raw
    response = failure(302, Location=destination) if change == "double" else Response(body, headers=headers)
    api = ConnectorGithub("model-token-never-log")
    api.opener = Opener(failure(302, Location=destination), response)
    asset = {"id": 200, "size": len(raw), "state": "uploaded", "digest": "sha256:" + digest(raw)}
    if change == "digest": asset["digest"] = "sha256:" + "f" * 64
    if change == "valid": assert api.asset_bytes(asset, len(raw)) == raw
    else:
        with pytest.raises(PublicationError): api.asset_bytes(asset, len(raw))
    assert len(api.opener.calls) <= 2
    assert api.opener.calls[0].full_url == API + "/releases/assets/200"
    if len(api.opener.calls) == 2:
        assert not api.opener.calls[1].has_header("Authorization")
        assert not api.opener.calls[1].has_header("Cookie")


def test_main_failure_receipt_preserves_both_errors_and_safe_observation(publication, tmp_path, monkeypatch, capsys):
    api, files, manifest = publication[:3]
    subject = publisher(publication)
    subject.write_diagnostic = {"operation": "upload", "primary_reason": "asset_bytes_mismatch",
        "observation": "unavailable_or_conflicting", "observation_reason": "connector_asset_download_url"}
    # Enter main's genuine receipt path, without credentials or provider calls.
    data = publication[5]
    env = {**data[1], "RUNNER_TEMP": str(tmp_path), "CONNECTOR_REQUEST": json.dumps(publication[4])}
    policy_dir = tmp_path / "publication-source/catalogue/publication"
    policy_dir.mkdir(parents=True)
    (policy_dir / "policy.json").write_bytes(data[3])
    (policy_dir / "connector-trust.json").write_bytes(canonical_json(data[2]))
    monkeypatch.setattr(engine, "ROOT", tmp_path)
    monkeypatch.setattr(engine.os, "environ", env)
    monkeypatch.setattr(engine, "check_checkouts", lambda *args: None)
    monkeypatch.setattr(engine, "job_admission", lambda *args, **kwargs: publication[6])
    monkeypatch.setattr(engine, "candidate", lambda *args, **kwargs: ({k: v for k, v in files.items() if k != "package.sigstore.json"}, manifest))
    monkeypatch.setattr(engine.release_connector, "selection", lambda *args: ("proxmox", "0.2.1"))
    (tmp_path / "connector-candidate").mkdir()
    (tmp_path / "connector-candidate/package.sigstore.json").write_bytes(files["package.sigstore.json"])
    monkeypatch.setattr(engine, "authenticated_bundle", lambda *args, **kwargs: None)
    monkeypatch.setattr(engine, "mint_publisher", lambda *args: api)
    monkeypatch.setattr(engine, "PackagePublisher", lambda *args, **kwargs: subject)
    def fail(*args, **kwargs): raise PublicationError("connector_upload_ambiguous_review_required")
    monkeypatch.setattr(subject, "stage", fail)
    monkeypatch.setattr(subject, "owned", lambda: (_ for _ in ()).throw(RuntimeError("private body secret")))
    monkeypatch.setattr(sys, "argv", ["publish_connector.py", "execute"])
    assert engine.main() == 1
    receipt = json.loads((tmp_path / "dist/connector-publication/receipt.json").read_bytes())
    assert receipt["write_failure"] == subject.write_diagnostic
    assert receipt["reason"] == "connector_upload_ambiguous_review_required"
    assert receipt["observation"] == "unavailable_or_conflicting"
    assert "secret" not in json.dumps(receipt) + capsys.readouterr().err


@pytest.mark.parametrize("command", ["authorize", "prepare", "execute"])
@pytest.mark.parametrize("evidence", ["missing", "unsigned"])
def test_actual_entrypoints_cannot_use_publisher_credentials_without_signed_admission(publication, tmp_path,
        monkeypatch, command, evidence):
    # Exercise the real job_admission/admit/ConnectorSigstore path, including an
    # otherwise valid fresh subject and a matching local receipt. No CLI mock
    # can turn the unsigned bundle into signature evidence.
    inputs, data, signed = publication[4:7]
    env = {**data[1], "RUNNER_TEMP": str(tmp_path), "CONNECTOR_REQUEST": json.dumps(inputs),
        "PUBLICATION_APP_PRIVATE_KEY": "synthetic-key-must-remain-unused"}
    policy_dir = tmp_path / "publication-source/catalogue/publication"
    policy_dir.mkdir(parents=True)
    (policy_dir / "policy.json").write_bytes(data[3])
    (policy_dir / "connector-trust.json").write_bytes(canonical_json(data[2]))
    if evidence == "unsigned":
        now = int(time.time())
        signed = deepcopy(signed)
        signed["freshness"] = {"observation_started": now, "observation_completed": now,
            "issued_at": now, "expires_at": now + 900}
        raw = canonical_json(signed)
        # Establish that structural checks succeed, so signature verification is
        # the rejection point, rather than an unrelated request mismatch.
        contract.check_preflight(signed, contract.context(env, inputs), data[2], data[3])
        directory = tmp_path / "connector-preflight"
        directory.mkdir()
        (directory / contract.SUBJECT).write_bytes(raw)
        (directory / "connector-preflight.sigstore.json").write_bytes(b"{}")
        (tmp_path / "connector-admitted.json").write_bytes(canonical_json({
            "context": contract.context(env, inputs), "sha256": digest(raw), "started_at": now}))
    monkeypatch.setattr(engine, "ROOT", tmp_path)
    monkeypatch.setattr(engine.os, "environ", env)
    monkeypatch.setattr(engine, "check_checkouts", lambda *args: None)
    monkeypatch.setattr(sys, "argv", ["publish_connector.py", command])
    def forbidden(*args, **kwargs):
        pytest.fail("unsigned admission reached Publisher preparation or credential mint")
    monkeypatch.setattr(engine, "mint_publisher", forbidden)
    monkeypatch.setattr(engine, "prepare_candidate", forbidden)
    assert engine.main() == 1
    assert env["PUBLICATION_APP_PRIVATE_KEY"] == "synthetic-key-must-remain-unused"
    assert publication[0].writes == []
