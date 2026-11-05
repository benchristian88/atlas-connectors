# SPDX-License-Identifier: Apache-2.0
"""Candidate policy/provider tests use synthetic verified output, never signatures.

Genuine offline tests at the end use only the approved historical fixtures.
"""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import authorization_sigstore as crypto
import publication_evidence as evidence
import publish_catalogue_evidence as candidate
from publication_contract import API, REPOSITORY, canonical_json, digest, parse_pointer, pointer_bytes
from publication_verify import Evidence, ORIGIN, Verifier
from test_authorization_sigstore import SYNTHETIC_BUNDLE, synthetic_verified_output
from test_publication_authorization import NOW, SOURCE, fixture, issue_fixture, file_response
from test_publication_state import MemoryGithub, structural_bundle, complete
from verification_github import BASE


def iso(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat()


def verified_output(raw, *, selection=False):
    output = synthetic_verified_output(raw)
    result = output[0]["verificationResult"]
    result["verifiedTimestamps"][0]["timestamp"] = iso(NOW + (100 if selection else 5))
    if selection:
        result["statement"]["subject"][0]["name"] = "current.json"
    else:
        value = json.loads(raw)
        certificate = result["signature"]["certificate"]
        certificate["sourceRepositoryDigest"] = certificate["buildConfigDigest"] = value["source"]["commit"]
        certificate["runInvocationURI"] = f"{ORIGIN}/actions/runs/{value['execution']['run_id']}/attempts/1"
    return output


@pytest.fixture
def signed(monkeypatch):
    import issue_publication_authorization as issuer
    monkeypatch.setattr(issuer, "app_jwt", lambda key: "synthetic-jwt")
    data = fixture("publish")
    for suffix in ("", "/attempts/1"):
        data[0].rows[BASE + "/actions/runs/60" + suffix]["created_at"] = iso(NOW - 20)
    raw = issue_fixture(data)
    archive = evidence.Archive.from_files([
        ("preflight.json", raw), ("preflight.sigstore.json", SYNTHETIC_BUNDLE), ("policy.json", data[4])])
    verifier = evidence.ArchiveVerifier(data[3], frozenset({digest(data[4])}), evidence.HistoricalLimits(900, 300))
    def run(command, directory):
        raw = (directory / "artifact").read_bytes()
        return canonical_json(verified_output(raw, selection="schema_version" in json.loads(raw)))
    monkeypatch.setattr(crypto, "bounded_run", run)
    monkeypatch.setattr(evidence, "bounded_run", run)
    return data, archive, verifier


def test_original_bytes_round_trip_and_recomputed_digests(signed, tmp_path):
    data, archive, verifier = signed
    # Policy is hashed as received, including insignificant whitespace.
    policy = data[4] + b" \n"
    value = json.loads(archive.preflight)
    value["source"]["policy_sha256"] = digest(policy)
    archive = evidence.Archive(canonical_json(value), SYNTHETIC_BUNDLE, policy)
    verifier.approved_policy_digests = frozenset({digest(policy)})
    expected = {**data[2], "policy_sha256": digest(policy)}
    verifier.authenticate(archive, expected)
    for name, raw in archive.files().items():
        (tmp_path / name).write_bytes(raw)
    restored = evidence.Archive.read(tmp_path)
    assert restored == archive
    assert restored.inventory() == {name: {"sha256": digest(raw), "size": len(raw)}
                                    for name, raw in archive.files().items()}
    assert restored.policy.endswith(b" \n")
    output = tmp_path / "round-trip"
    restored.write(output)
    assert evidence.Archive.read(output) == restored
    with pytest.raises(FileExistsError):
        restored.write(output)


@pytest.mark.parametrize("change", [lambda rows: rows.pop(), lambda rows: rows.append(rows[0]),
    lambda rows: rows.__setitem__(1, rows[0]), lambda rows: rows.append(("extra.json", b"{}")),
    lambda rows: rows.__setitem__(0, ("../preflight.json", rows[0][1]))])
def test_missing_duplicate_and_conflicting_inventory(signed, change):
    rows = list(signed[1].files().items())
    change(rows)
    with pytest.raises(ValueError, match="archive_inventory"):
        evidence.Archive.from_files(rows)


@pytest.mark.parametrize("name", evidence.ARCHIVE_LIMITS)
@pytest.mark.parametrize("kind", ["empty", "oversized", "text"])
def test_bounded_evidence(signed, name, kind):
    files = signed[1].files()
    files[name] = b"" if kind == "empty" else b"x" * (evidence.ARCHIVE_LIMITS[name] + 1) if kind == "oversized" else "text"
    with pytest.raises(ValueError, match="archive_size"):
        evidence.Archive.from_files(files.items())


@pytest.mark.parametrize("kind", ["symlink", "extra", "directory"])
def test_local_archive_rejects_unsafe_files(signed, tmp_path, kind):
    for name, raw in signed[1].files().items():
        (tmp_path / name).write_bytes(raw)
    if kind == "extra":
        (tmp_path / "receipt.json").write_bytes(b"{}")
    else:
        (tmp_path / "policy.json").unlink()
        if kind == "symlink":
            (tmp_path / "policy.json").symlink_to(tmp_path / "preflight.json")
        else:
            (tmp_path / "policy.json").mkdir()
    with pytest.raises((ValueError, OSError)):
        evidence.Archive.read(tmp_path)


@pytest.mark.parametrize("raw", [b"{}", b"[]", b'{"schema":1,"schema":2}', b"\xff", b"null"])
@pytest.mark.parametrize("name", evidence.ARCHIVE_LIMITS)
def test_malformed_or_substituted_evidence_is_never_authenticated(signed, raw, name):
    data, archive, verifier = signed
    files = archive.files()
    files[name] = raw
    with pytest.raises((ValueError, UnicodeError)):
        verifier.authenticate(evidence.Archive.from_files(files.items()), data[2])


@pytest.mark.parametrize("field", list(synthetic_verified_output(b"test")[0]["verificationResult"]["signature"]["certificate"]))
def test_every_signer_source_workflow_run_and_attempt_constraint(signed, monkeypatch, field):
    data, archive, verifier = signed
    output = verified_output(archive.preflight)
    output[0]["verificationResult"]["signature"]["certificate"][field] = "wrong"
    monkeypatch.setattr(crypto, "bounded_run", lambda *a: canonical_json(output))
    with pytest.raises(ValueError):
        verifier.authenticate(archive, data[2])


@pytest.mark.parametrize("path,value", [
    (("security", "run", "actor", "id"), 7),
    (("security", "attempt", "triggering_actor", "id"), 7),
    (("security", "repository", "id"), 7),
    (("security", "workflow", "path"), ".github/workflows/other.yml"),
    (("execution", "run_id"), 61), (("execution", "run_attempt"), 2),
    (("execution", "acceptance_only"), True),
    (("source", "policy_sha256"), "0" * 64),
    (("freshness", "observation_completed"), NOW - 1),
    (("freshness", "expires_at"), NOW + 901),
    (("security", "run", "created_at"), iso(NOW + 1)),
    (("security", "attempt", "created_at"), "missing-timezone"),
])
def test_signed_context_and_historical_order_are_revalidated(signed, path, value):
    data, archive, verifier = signed
    document = json.loads(archive.preflight)
    current = document
    for key in path[:-1]:
        current = current[key]
    current[path[-1]] = value
    with pytest.raises(ValueError):
        verifier.authenticate(evidence.Archive(canonical_json(document), archive.bundle, archive.policy), data[2])


@pytest.mark.parametrize("times", [[], [{"type": "Tlog", "uri": "https://evil.example", "timestamp": iso(NOW)}],
    [{"type": "Tlog", "uri": "https://rekor.sigstore.dev"}],
    [{"type": "Tlog", "uri": "https://rekor.sigstore.dev", "timestamp": "synthetic"}],
    [{"type": "Tlog", "uri": "https://rekor.sigstore.dev", "timestamp": iso(NOW - 1)}],
    [{"type": "Tlog", "uri": "https://rekor.sigstore.dev", "timestamp": iso(NOW + 900)}]])
def test_verified_transparency_time_must_fit_original_validity(signed, monkeypatch, times):
    data, archive, verifier = signed
    output = verified_output(archive.preflight)
    output[0]["verificationResult"]["verifiedTimestamps"] = times
    monkeypatch.setattr(evidence, "bounded_run", lambda *a: canonical_json(output))
    with pytest.raises(ValueError):
        verifier.authenticate(archive, data[2])


def test_companion_verified_output_must_authenticate_identical_subject_bytes(signed, monkeypatch):
    data, archive, verifier = signed
    output = verified_output(archive.preflight)
    output[0]["verificationResult"]["statement"]["subject"][0]["digest"]["sha256"] = "0" * 64
    monkeypatch.setattr(evidence, "bounded_run", lambda *a: canonical_json(output))
    with pytest.raises(ValueError, match="archive_time_subject"):
        verifier.authenticate(archive, data[2])


@pytest.mark.parametrize("profile,maximum", [("pointer", 1024), ("catalogue", 4 * 1024 * 1024)])
def test_companion_bounds_artifact_before_any_subprocess(signed, monkeypatch, profile, maximum):
    monkeypatch.setattr(evidence, "bounded_run", lambda *a: pytest.fail("oversized input reached verifier"))
    for raw in (b"", b"x" * (maximum + 1)):
        with pytest.raises(ValueError, match="archive_size"):
            evidence.verified_times(None, raw, SYNTHETIC_BUNDLE, profile=profile, commit=SOURCE)


def selection_evidence(run=60, commit=SOURCE):
    return Evidence("pointer", digest(b"pointer"), commit, f"{ORIGIN}/actions/runs/{run}/attempts/1")


@pytest.mark.parametrize("selection_time,published_time", [(NOW + 4, NOW + 200), (NOW + 901, NOW + 1000),
    (NOW + 100, NOW + 99), (NOW + 100, NOW + 401)])
def test_unsupported_selection_and_publication_delay(signed, selection_time, published_time):
    _, archive, verifier = signed
    with pytest.raises(ValueError):
        verifier.bind_selection(archive, selection_evidence(),
            (evidence.timestamp(iso(selection_time)),), published_at=iso(published_time))


@pytest.mark.parametrize("run,commit", [(61, SOURCE), (60, "c" * 40)])
def test_selection_cannot_rebind_another_source_or_run(signed, run, commit):
    _, archive, verifier = signed
    with pytest.raises(ValueError, match="archive_context"):
        verifier.bind_selection(archive, selection_evidence(run, commit),
            (evidence.timestamp(iso(NOW + 100)),), published_at=iso(NOW + 200))


def test_historical_result_does_not_renew_live_authorization(signed):
    data, archive, verifier = signed
    result = verifier.bind_selection(archive, selection_evidence(),
        (evidence.timestamp(iso(NOW + 100)),), published_at=iso(NOW + 200))
    assert result["current_authorization"] is False and result["consumer_acceptance"] is False
    from publication_authorization import AuthorizationVerifier
    with pytest.raises(ValueError, match="not_fresh"):
        AuthorizationVerifier(data[3], archive.policy).verify(archive.preflight, archive.bundle, data[2],
                                                             clock=lambda: NOW + 901)
    with pytest.raises(ValueError, match="archive_policy_digest"):
        evidence.ArchiveVerifier(data[3], frozenset({"0" * 64}), evidence.HistoricalLimits(900, 300)).authenticate(archive, data[2])


def test_selection_binding_requires_explicit_historical_decision_inputs(signed):
    data, archive, _ = signed
    verifier = evidence.ArchiveVerifier(data[3], frozenset({digest(archive.policy)}))
    verifier.authenticate(archive, data[2])
    with pytest.raises(ValueError, match="historical_limits"):
        verifier.bind_selection(archive, selection_evidence(), (evidence.timestamp(iso(NOW + 100)),))


def test_local_cli_copies_originals_only_after_verification(signed, tmp_path, monkeypatch, capsys):
    data, archive, _ = signed
    preflight = tmp_path / "input"
    preflight.mkdir()
    for name, raw in archive.files().items():
        (tmp_path / name if name == "policy.json" else preflight / name).write_bytes(raw)
    trust = tmp_path / "trust.json"
    trust.write_bytes(canonical_json(data[3]))
    output = tmp_path / "archive"
    argv = ["publication_evidence.py", "--preflight-directory", str(preflight), "--policy", str(tmp_path / "policy.json"),
        "--trust", str(trust), "--policy-sha256", digest(archive.policy), "--source-commit", SOURCE,
        "--run-id", "60", "--operation", "publish", "--output", str(output)]
    monkeypatch.setattr(sys, "argv", argv)
    evidence.main()
    assert evidence.Archive.read(output) == archive
    assert json.loads(capsys.readouterr().out)["result"] == "prepared_local_archive_not_publication_authority"
    with pytest.raises(SystemExit):
        evidence.main()
    assert evidence.Archive.read(output) == archive
    bad_output = tmp_path / "bad"
    argv[-1] = str(bad_output)
    argv[argv.index("--policy-sha256") + 1] = "0" * 64
    with pytest.raises(SystemExit):
        evidence.main()
    assert not bad_output.exists()


class EvidenceMemoryGithub(MemoryGithub):
    """Synthetic official metadata over the existing publication state model."""
    def actor(self):
        return {"id": 346232650, "type": "Bot", "login": "atlas-catalogue-publisher[bot]"}

    def new_release(self, tag):
        release = super().new_release(tag)
        release.update(author=self.actor(), assets_url=f"{API}/releases/{release['id']}/assets",
                       html_url=f"{ORIGIN}/releases/tag/{tag}")
        return release

    def add(self, release, name, raw):
        asset = super().add(release, name, raw)
        asset.update(url=f"{API}/releases/assets/{asset['id']}", uploader=self.actor(),
                     browser_download_url=f"{ORIGIN}/releases/download/{release['tag_name']}/{name}")
        return asset

    def json(self, method, path, **kwargs):
        if method == "GET" and path in {"/actions/runs/70", "/actions/runs/70/attempts/1"}:
            return deepcopy(self.recovery_run)
        if method == "GET" and path == "/users/benchristian88":
            return deepcopy(self.args[7])
        if method == "GET" and path == "/apps/atlas-catalogue-publisher":
            return deepcopy(self.app)
        result = super().json(method, path, **kwargs)
        if method == "PATCH" and path.startswith("/releases/"):
            self.releases[result["id"]]["published_at"] = iso(NOW + 200)
            result["published_at"] = iso(NOW + 200)
        return result


@pytest.fixture
def state(signed):
    data, _, _ = signed
    api = EvidenceMemoryGithub()
    api.verifier.roots = b"synthetic-roots-for-mocked-companion-output"
    api.verifier.binary = Path("/synthetic-not-executed")
    policy = json.loads(data[4])
    policy["bootstrap"]["pointer_sha256"] = digest(api.files["current.json"])
    policy_raw = canonical_json(policy)
    data[0].rows[BASE + "/contents/catalogue/publication/policy.json?ref=" + SOURCE] = file_response(
        policy_raw, "catalogue/publication/policy.json")
    raw = issue_fixture(data)
    value = json.loads(raw)
    security = value["security"]
    api.args = [policy, *(security[k] for k in
                         ("repository", "branch", "environment", "run", "attempt", "workflow", "user", "checks"))]
    api.rules = sorted(value["rulesets"]["observations"], key=lambda r: r["id"])
    api.app = security["publisher_app"]
    api.token_identity = {"app_slug": policy["app_slug"], "installation_id": policy["app_installation_id"]}
    archive = evidence.Archive(raw, SYNTHETIC_BUNDLE, policy_raw)
    verifier = evidence.ArchiveVerifier(data[3], frozenset({digest(policy_raw)}), evidence.HistoricalLimits(900, 300))
    publisher = candidate.EvidencePublisher(api, api.verifier, policy, 60, source_commit=SOURCE,
        token_identity=api.token_identity, preflight=value, policy_raw=policy_raw,
        archive=archive, archive_verifier=verifier, started_at=NOW + 10, clock=lambda: NOW + 150)
    next_doc = json.loads(api.previous)
    next_doc["sequence"] = 2
    return api, publisher, canonical_json(next_doc)


def test_stage_freezes_exact_original_evidence_before_immutable_boundary(state):
    api, publisher, raw = state
    original_root = deepcopy(api.by_release[parse_pointer(api.files["current.json"])["release_id"]])
    assert complete(publisher, raw)["result"] == "published"
    pointer = parse_pointer(api.files["current.json"])
    release = api.release_id(pointer["release_id"])
    assets = api.assets(release)
    assert len(assets) == 7 and release["immutable"] is True
    for name, original in publisher.archive.files().items():
        assert api.asset_bytes(assets[name], len(original)) == original
        assert api.writes.index(("upload", name)) < api.writes.index(("finalize", release["id"]))
    assert complete(publisher, raw)["result"] == "unchanged"
    assert api.by_release[next(r["id"] for r in api.releases.values() if r["tag_name"] == "catalogue-000001")] == original_root


@pytest.mark.parametrize("name", ["preflight.sigstore.json", "policy.json", "catalogue-000002.json",
                                 "catalogue.sigstore.json", "current.json", "current.sigstore.json"])
def test_partial_upload_resumes_only_same_job_original_bytes_and_ids(state, name):
    api, publisher, raw = state
    api.fail_upload = name
    with pytest.raises(ValueError, match="mock_upload_failed"):
        complete(publisher, raw)
    checkpoint = deepcopy(publisher.checkpoint)
    api.fail_upload = None
    assert complete(publisher, raw)["result"] == "published"
    final = publisher.checkpoint["assets"]
    assert all(final[name] == row for name, row in checkpoint["assets"].items())


def test_failure_before_original_preflight_leaves_orphan_draft_closed(state):
    api, publisher, raw = state
    api.fail_upload = "preflight.json"
    with pytest.raises(ValueError):
        complete(publisher, raw)
    api.fail_upload = None
    before = list(api.writes)
    with pytest.raises(ValueError, match="archive_original_missing"):
        complete(publisher, raw)
    assert api.writes == before


@pytest.mark.parametrize("name", evidence.ARCHIVE_LIMITS)
@pytest.mark.parametrize("kind", ["missing", "substituted", "new_id"])
def test_staged_evidence_change_never_finalizes_or_replaces(state, name, kind):
    api, publisher, raw = state
    stage = publisher.stage(raw)
    release = api.releases[stage.release_id]
    old = api.by_release[stage.release_id][name]
    if kind == "missing":
        del api.by_release[stage.release_id][name]
    else:
        api.add(release, name, api.data[old["id"]] + (b" " if kind == "substituted" else b""))
    before = list(api.writes)
    with pytest.raises(ValueError):
        publisher.finish(raw, stage.pointer, structural_bundle(stage.pointer, "pointer", "current.json"))
    assert api.writes == before and release["draft"] is True


def test_same_job_checkpoint_can_be_carried_between_phases_but_is_required(state):
    api, publisher, raw = state
    stage = publisher.stage(raw)
    def next_phase(checkpoint):
        return candidate.EvidencePublisher(api, api.verifier, publisher.policy, 60, source_commit=SOURCE,
            token_identity=api.token_identity, preflight=publisher.run_preflight, policy_raw=publisher.policy_raw,
            archive=publisher.archive, archive_verifier=publisher.archive_verifier, started_at=NOW + 10,
            clock=lambda: NOW + 150, checkpoint=checkpoint)
    before = list(api.writes)
    with pytest.raises(ValueError, match="checkpoint_mismatch"):
        next_phase(None).stage(raw)
    assert api.writes == before
    resumed = next_phase(publisher.checkpoint)
    assert resumed.finish(raw, stage.pointer, structural_bundle(stage.pointer, "pointer", "current.json"))["result"] == "published"


@pytest.mark.parametrize("mutation", [
    lambda a: a["policy.json"].update(id=a["preflight.json"]["id"]),
    lambda a: a["policy.json"].update(url="https://evil.example"),
    lambda a: a["policy.json"].update(browser_download_url="https://evil.example"),
    lambda a: a["policy.json"].update(size=16385),
    lambda a: a["policy.json"].update(name="different.json"),
    lambda a: a["policy.json"]["uploader"].update(id=7),
    lambda a: a.update(extra=deepcopy(a["policy.json"])),
])
def test_release_inventory_and_all_numeric_asset_identities_fail_closed(state, mutation):
    api, publisher, raw = state
    stage = publisher.stage(raw)
    mutation(api.by_release[stage.release_id])
    before = list(api.writes)
    with pytest.raises(ValueError):
        complete(publisher, raw)
    assert api.writes == before


def test_duplicate_provider_names_are_rejected_before_dictionary_collapse(state, monkeypatch):
    api, publisher, raw = state
    stage = publisher.stage(raw)
    original = api.json
    def json_call(method, path, **kwargs):
        rows = original(method, path, **kwargs)
        if path == f"/releases/{stage.release_id}/assets?per_page=100":
            rows.append(deepcopy(rows[0]))
        return rows
    monkeypatch.setattr(api, "json", json_call)
    with pytest.raises(ValueError, match="duplicate_asset_names"):
        complete(publisher, raw)


def test_replacement_preflight_even_for_same_context_is_not_original_evidence(state):
    api, publisher, raw = state
    publisher.stage(raw)
    value = json.loads(publisher.archive.preflight)
    value["freshness"]["issued_at"] += 1
    publisher.run_preflight = value
    publisher.archive = evidence.Archive(canonical_json(value), publisher.archive.bundle, publisher.archive.policy)
    before = list(api.writes)
    with pytest.raises(ValueError, match="archive_original_changed"):
        complete(publisher, raw)
    assert api.writes == before


def test_extra_archive_verification_cannot_extend_same_job_deadline(state):
    api, publisher, _ = state
    times = iter([NOW + 150, NOW + 150, NOW + 1811])
    publisher.clock = lambda: next(times)
    before = list(api.writes)
    with pytest.raises(ValueError, match="authorization_not_fresh"):
        publisher.require_preflight()
    assert api.writes == before


def test_supported_code_cannot_select_another_sequence_from_same_source(state):
    api, publisher, raw = state
    complete(publisher, raw)
    document = json.loads(raw)
    document["sequence"] = 3
    before = list(api.writes)
    with pytest.raises(ValueError, match="archive_one_selection_per_source"):
        publisher.stage(canonical_json(document))
    assert api.writes == before


@pytest.mark.parametrize('now', [NOW + 600, NOW + 371])
def test_expired_or_insufficient_finalization_budget_never_makes_release_immutable(state, now):
    api, publisher, raw = state
    original_current = deepcopy(api.files)
    publisher.clock = lambda: now
    # Selection is witnessed at issuance +100; its unchanged 300-second
    # publication bound ends at +400. At +371 the required 30-second reserve
    # is also unavailable. The reviewer's exact +600 case must never PATCH.
    with pytest.raises(ValueError, match='archive_finalization_deadline'):
        complete(publisher, raw)
    release = api.releases[publisher.checkpoint['release_id']]
    assert release['draft'] is True and release['immutable'] is False
    assert not any(kind in {'finalize', 'pointer'} for kind, _ in api.writes)
    assert api.files == original_current


def test_finalization_window_is_rechecked_after_last_slow_provider_read(state, monkeypatch):
    api, publisher, raw = state
    clock = [NOW + 150]
    publisher.clock = lambda: clock[0]
    original = candidate.source_tag
    def slow(*args, **kwargs):
        result = original(*args, **kwargs)
        if publisher.checkpoint and len(publisher.checkpoint['assets']) == 7:
            clock[0] = NOW + 600
        return result
    monkeypatch.setattr(candidate, 'source_tag', slow)
    with pytest.raises(ValueError, match='archive_finalization_deadline'):
        complete(publisher, raw)
    assert not any(kind in {'finalize', 'pointer'} for kind, _ in api.writes)


def test_finalization_reserve_boundary_and_future_clock_fail_closed(signed):
    _, archive, verifier = signed
    bound = verifier.bind_selection(archive, selection_evidence(),
        (evidence.timestamp(iso(NOW + 100)),))
    assert evidence.FINALIZATION_RESERVE_SECONDS == 30
    verifier.require_finalization_window(bound, now=NOW + 370)
    for now in (NOW + 370.001, NOW + 99, float('nan'), float('inf'), True):
        with pytest.raises((ValueError, OverflowError)):
            verifier.require_finalization_window(bound, now=now)


def test_provider_delay_after_admission_still_rejects_without_advancing_current(state, monkeypatch):
    api, publisher, raw = state
    before = deepcopy(api.files)
    original = api.json
    def delayed(method, path, **kwargs):
        result = original(method, path, **kwargs)
        if method == 'PATCH' and path.startswith('/releases/'):
            api.releases[result['id']]['published_at'] = iso(NOW + 600)
            result['published_at'] = iso(NOW + 600)
        return result
    monkeypatch.setattr(api, 'json', delayed)
    with pytest.raises(ValueError, match='archive_publication_time'):
        complete(publisher, raw)
    release = api.releases[publisher.checkpoint['release_id']]
    assert release['immutable'] is True and release['draft'] is False
    assert api.files == before and not any(kind == 'pointer' for kind, _ in api.writes)


@pytest.mark.parametrize("failure", ["finalize", "pointer"])
def test_interrupted_finalization_preserves_original_archive_and_signatures(state, failure):
    api, publisher, raw = state
    setattr(api, "fail_" + failure, True)
    with pytest.raises(ValueError, match="mock_" + failure + "_failed"):
        complete(publisher, raw)
    checkpoint = deepcopy(publisher.checkpoint)
    setattr(api, "fail_" + failure, False)
    assert complete(publisher, raw)["result"] == "published"
    assert publisher.checkpoint == checkpoint


def recovery_publisher(api, publisher):
    """Fresh recovery evidence is synthetic and distinct from original selection."""
    original = json.loads(publisher.archive.preflight)
    value = deepcopy(original)
    value["execution"].update(operation="recover", run_id=70)
    value["source"]["commit"] = "c" * 40
    for key in ("run", "attempt"):
        value["security"][key].update(id=70, head_sha="c" * 40, url=f"{API}/actions/runs/70",
                                      html_url=f"{ORIGIN}/actions/runs/70")
    value["security"]["branch"]["commit"]["sha"] = "c" * 40
    value["security"]["checks"]["check_runs"][0]["head_sha"] = "c" * 40
    api.args[2]["commit"]["sha"] = "c" * 40
    api.recovery_run = value["security"]["run"]
    archive = evidence.Archive(canonical_json(value), SYNTHETIC_BUNDLE, publisher.policy_raw)
    fresh = candidate.EvidencePublisher(api, api.verifier, publisher.policy, 70,
        source_commit="c" * 40, token_identity=api.token_identity, preflight=value,
        policy_raw=publisher.policy_raw, archive=archive, archive_verifier=publisher.archive_verifier,
        started_at=NOW + 10, clock=lambda: NOW + 150)
    fresh.policy_operation = "recover"
    return fresh


def test_recovery_checks_original_archive_and_never_writes_immutable_assets(state):
    api, publisher, raw = state
    api.fail_pointer = True
    with pytest.raises(ValueError):
        complete(publisher, raw)
    api.fail_pointer = False
    original_assets = deepcopy(api.by_release[publisher.checkpoint["release_id"]])
    before = len(api.writes)
    fresh = recovery_publisher(api, publisher)
    assert fresh.recover()["result"] == "recovered"
    assert api.by_release[publisher.checkpoint["release_id"]] == original_assets
    assert [kind for kind, _ in api.writes[before:]] == ["pointer"]


@pytest.mark.parametrize("name", evidence.ARCHIVE_LIMITS)
def test_recovery_refuses_missing_original_evidence(state, name):
    api, publisher, raw = state
    api.fail_pointer = True
    with pytest.raises(ValueError):
        complete(publisher, raw)
    api.fail_pointer = False
    del api.by_release[publisher.checkpoint["release_id"]][name]
    before = len(api.writes)
    with pytest.raises(ValueError):
        recovery_publisher(api, publisher).recover()
    assert len(api.writes) == before


def test_recovery_refuses_unfinalized_or_mutable_release(state):
    api, publisher, raw = state
    publisher.stage(raw)
    with pytest.raises(ValueError, match="release_not_immutable"):
        recovery_publisher(api, publisher).recover()


@pytest.mark.parametrize("published_at", [None, "invalid", iso(NOW + 99), iso(NOW + 401)])
def test_recovery_refuses_missing_or_unsupported_publication_time(state, published_at):
    api, publisher, raw = state
    api.fail_pointer = True
    with pytest.raises(ValueError):
        complete(publisher, raw)
    api.fail_pointer = False
    api.releases[publisher.checkpoint["release_id"]]["published_at"] = published_at
    before = list(api.writes)
    with pytest.raises(ValueError):
        recovery_publisher(api, publisher).recover()
    assert api.writes == before


def test_recovery_checks_original_run_against_signed_creation_time(state):
    api, publisher, raw = state
    api.fail_pointer = True
    with pytest.raises(ValueError):
        complete(publisher, raw)
    api.fail_pointer = False
    api.args[4]["created_at"] = iso(NOW - 19)
    with pytest.raises(ValueError, match="archive_run_time_changed"):
        recovery_publisher(api, publisher).recover()


def test_conflicting_same_id_release_observations_reject_recovery(state, monkeypatch):
    api, publisher, raw = state
    api.fail_pointer = True
    with pytest.raises(ValueError):
        complete(publisher, raw)
    api.fail_pointer = False
    original = api.json
    def json_call(method, path, **kwargs):
        result = original(method, path, **kwargs)
        if path == "/releases/tags/catalogue-000002":
            result["target_commitish"] = "f" * 40
        return result
    monkeypatch.setattr(api, "json", json_call)
    before = list(api.writes)
    with pytest.raises(ValueError, match="archive_release_identity"):
        recovery_publisher(api, publisher).recover()
    assert api.writes == before


def test_fresh_recovery_preflight_cannot_replace_original_selection_authorization(state):
    api, publisher, raw = state
    api.fail_pointer = True
    with pytest.raises(ValueError):
        complete(publisher, raw)
    api.fail_pointer = False
    fresh = recovery_publisher(api, publisher)
    release = api.releases[publisher.checkpoint["release_id"]]
    for name, value in fresh.archive.files().items():
        api.add(release, name, value)
    with pytest.raises(ValueError, match="archive_context"):
        fresh.recover()


@pytest.mark.parametrize("change", [lambda p: p.update(release_id=7), lambda p: p.update(asset_id=7),
    lambda p: p.update(sha256="0" * 64)])
def test_independent_release_and_selected_catalogue_binding(state, change):
    _, publisher, raw = state
    stage = publisher.stage(raw)
    pointer = parse_pointer(stage.pointer)
    change(pointer)
    substituted = pointer_bytes(pointer)
    with pytest.raises(ValueError):
        publisher.bind_archive(publisher.api.release_id(stage.release_id), substituted,
                              structural_bundle(substituted, "pointer", "current.json"))


def test_genuine_offline_companion_timestamp_verification_and_tamper_rejection(tmp_path):
    raw = (ROOT / "tests/fixtures/official_catalogue/catalogue-000001.json").read_bytes()
    bundle = (ROOT / "tests/fixtures/publication/catalogue.sigstore.json").read_bytes()
    verifier = Verifier()
    verified = verifier.verify(raw, bundle, profile="catalogue", name="catalogue-000001.json")
    times = evidence.verified_times(verifier, raw, bundle, profile="catalogue", name="catalogue-000001.json",
                                    commit=verified.source_commit)
    assert times == (evidence.timestamp("2026-10-18T16:07:56Z"),)
    with pytest.raises(ValueError):
        evidence.verified_times(verifier, raw + b" ", bundle, profile="catalogue", name="catalogue-000001.json",
                                commit=verified.source_commit)


def test_real_crypto_rejects_unsigned_archive(signed, monkeypatch):
    data, archive, verifier = signed
    monkeypatch.undo()
    with pytest.raises(ValueError, match="attestation_verification_failed"):
        verifier.authenticate(archive, data[2])


def test_frozen_safeguards_and_all_historical_implementation_files_unchanged():
    preserved = json.loads((ROOT / "tests/fixtures/publication_evidence/preserved.json").read_bytes())
    assert preserved["baseline"] == "e58788a667c0c0006477ac149e8ad28aedda0745"
    for path, expected in preserved["sha256"].items():
        assert digest((ROOT / path).read_bytes()) == expected, path
    workflow = (ROOT / ".github/workflows/connector-publish.yml").read_text()
    assert "CONNECTOR_PUBLICATION_ENABLED" in workflow
    assert "publish_catalogue_evidence" not in (ROOT / ".github/workflows/catalogue-publish.yml").read_text()
