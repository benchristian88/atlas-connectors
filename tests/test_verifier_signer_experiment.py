# SPDX-License-Identifier: Apache-2.0
"""Local contracts and synthetic VERIFIED-output tests, not live signer acceptance."""
from copy import deepcopy
from pathlib import Path
import re
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import verifier_signer_experiment as experiment
from publication_contract import PublicationError, canonical_json, digest

COMMIT = "a" * 40
SIGNER_REVISION = "260d83d529f89d00646771f8e66f32efd34826a3"
EXPECTED = {"source_commit": COMMIT, "run_id": 60, "run_attempt": 1}
BUNDLE = canonical_json({"mediaType": "application/vnd.dev.sigstore.bundle.v0.3+json"})


def workflow(name):
    return yaml.load((ROOT / ".github/workflows" / name).read_text(), Loader=yaml.BaseLoader)


def environment(tmp_path):
    return {"GITHUB_REPOSITORY": experiment.REPOSITORY, "GITHUB_REPOSITORY_ID": "1414494920",
        "GITHUB_REPOSITORY_OWNER_ID": "93822871", "GITHUB_REF": "refs/heads/main",
        "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_RUN_ID": "60", "GITHUB_SHA": COMMIT, "RUNNER_ENVIRONMENT": "github-hosted",
        "GITHUB_WORKFLOW_REF": f"{experiment.REPOSITORY}/{experiment.CALLER}@refs/heads/main",
        "RUNNER_TEMP": str(tmp_path), "PROBE_WORKFLOW_REF": f"{experiment.REPOSITORY}/{experiment.SIGNER}@refs/heads/main",
        "PROBE_WORKFLOW_SHA": SIGNER_REVISION, "PROBE_WORKFLOW_REPOSITORY": experiment.REPOSITORY,
        "PROBE_WORKFLOW_FILE_PATH": experiment.SIGNER}


def generate(tmp_path, missing_context=False):
    env = environment(tmp_path)
    if missing_context:
        env = {key: value for key, value in env.items() if not key.startswith("PROBE_WORKFLOW_")}
    env["UNRELATED_SECRET"] = "must-not-export-this"
    step = workflow("verifier-signer-probe.yml")["jobs"]["probe"]["steps"][0]
    # Run the actual fixed inline generator, rather than an imitation of it.
    program = step["run"].split("python3 - <<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
    subprocess.run([sys.executable, "-c", program], env=env, check=True, capture_output=True, timeout=10)
    return (tmp_path / "signer-probe/probe.json").read_bytes()


def test_workflows_are_manual_main_first_attempt_and_isolated():
    caller, callee = workflow("verifier-signer-experiment.yml"), workflow("verifier-signer-probe.yml")
    assert caller["on"] == {"workflow_dispatch": ""}
    assert set(callee["on"]) == {"workflow_call"}
    assert set(callee["on"]["workflow_call"]) == {"outputs"}
    assert caller["permissions"] == callee["permissions"] == {}
    signing = {"id-token": "write", "attestations": "write"}
    assert experiment.SIGNER_REVISION == SIGNER_REVISION
    assert caller["jobs"]["sign"]["uses"] == f"{experiment.REPOSITORY}/{experiment.SIGNER}@{SIGNER_REVISION}"
    assert caller["jobs"]["sign"]["permissions"] == callee["jobs"]["probe"]["permissions"] == signing
    assert caller["jobs"]["inspect"]["permissions"] == {"contents": "read", "actions": "read"}
    assert caller["jobs"]["inspect"]["needs"] == "sign"
    for job in [*caller["jobs"].values(), *callee["jobs"].values()]:
        gate = job["if"]
        for item in ("benchristian88/atlas-connectors", "1414494920", "93822871", "workflow_dispatch",
                     "refs/heads/main", "github.run_attempt == 1", experiment.CALLER):
            assert item in gate
        assert "secrets" not in job and "environment" not in job and "with" not in job
        for step in job.get("steps", []):
            if "uses" in step:
                assert re.fullmatch(r"actions/[a-z-]+@[0-9a-f]{40}", step["uses"])
    probe = callee["jobs"]["probe"]
    assert probe["runs-on"] == caller["jobs"]["inspect"]["runs-on"] == "ubuntu-24.04"
    signer_source = (ROOT / ".github/workflows/verifier-signer-probe.yml").read_text()
    for forbidden in ("secrets.", "VERIFICATION_APP", "checkout@", "download-artifact@", "git clone",
                      "authorization.json", "catalogue-publication", "contents: write", "packages: write"):
        assert forbidden not in signer_source
    caller_source = (ROOT / ".github/workflows/verifier-signer-experiment.yml").read_text()
    for forbidden in ("secrets.", "APP_PRIVATE_KEY", "PUBLISHER_APP", "VERIFICATION_APP", "environment:",
                      "catalogue-verifier.yml", "catalogue-publish.yml", "authorization.json", "gh release",
                      "git push", "contents: write", "packages: write"):
        assert forbidden not in caller_source
    assert len(probe["steps"][0]["env"]) == 4
    assert all(re.fullmatch(r"\$\{\{ fromJSON\(toJSON\(job\)\)\.workflow_(ref|sha|repository|file_path) }}", value)
               for value in probe["steps"][0]["env"].values())
    attest = next(step for step in probe["steps"] if step.get("id") == "attest")
    assert attest["uses"] == "actions/attest@508db95dd578ae2727ebd6217d5ba78e4fbda05d"
    assert attest["with"]["predicate-type"] == experiment.PREDICATE
    assert attest["with"]["create-storage-record"] == attest["with"]["push-to-registry"] == "false"
    uploads = [step for job in [probe, caller["jobs"]["inspect"]] for step in job["steps"]
               if step.get("uses", "").startswith("actions/upload-artifact@")]
    assert all(step["with"]["retention-days"] == "1" for step in uploads)
    assert uploads[0]["with"]["path"].splitlines() == [
        "${{ runner.temp }}/signer-probe/" + name
        for name in ("probe.json", "probe.sigstore.json", "signer-timing.json")]
    steps = caller["jobs"]["inspect"]["steps"]
    checkout = steps[0]
    assert checkout["with"]["ref"] == "${{ github.sha }}"
    assert checkout["with"]["persist-credentials"] == "false"
    download = next(step for step in steps if "download-artifact@" in step.get("uses", ""))
    assert download["with"]["artifact-ids"] == "${{ needs.sign.outputs.artifact-id }}"
    assert steps[-1]["if"] == "${{ !cancelled() }}"


def test_caller_and_original_probe_at_s_keep_exact_caller_restriction():
    # Reviewed bytes at S; works in CI's shallow checkout without fetching S.
    original = (ROOT / experiment.SIGNER).read_bytes()
    assert digest(original) == "eb857b04baa61f4c1ba082ac2a8a614a2a1bceb4886b946d728bd815c24fdd05"
    callee = yaml.load(original, Loader=yaml.BaseLoader)
    for job in [callee["jobs"]["probe"], *workflow("verifier-signer-experiment.yml")["jobs"].values()]:
        assert ("github.workflow_ref == '" + experiment.REPOSITORY + "/" + experiment.CALLER
                + "@refs/heads/main'") in job["if"]


@pytest.mark.parametrize("moving", ["main", "refs/heads/main", "v1", "refs/tags/v1", "${{ github.sha }}"])
def test_moving_signer_references_cannot_satisfy_fixed_pin(moving):
    call = workflow("verifier-signer-experiment.yml")["jobs"]["sign"]["uses"]
    assert call.rsplit("@", 1)[1] == SIGNER_REVISION
    assert call != f"{experiment.REPOSITORY}/{experiment.SIGNER}@{moving}"


def test_actual_inline_subject_is_deterministic_bounded_and_allowlisted(tmp_path):
    left, right = tmp_path / "left", tmp_path / "right"
    left.mkdir()
    right.mkdir()
    raw = generate(left)
    assert raw == generate(right) and len(raw) <= 4096
    assert b"must-not-export-this" not in raw and b"authorization.json" not in raw
    assert experiment.check_subject(raw, EXPECTED)["note"] == "NOT a publication authorization"
    assert experiment.context(environment(tmp_path)) == EXPECTED


def test_missing_job_context_is_explicitly_unobservable(tmp_path):
    raw = generate(tmp_path, missing_context=True)
    assert set(experiment.check_subject(raw, EXPECTED)["job_context"].values()) == {None}


@pytest.mark.parametrize("field", ["GITHUB_REPOSITORY", "GITHUB_REPOSITORY_ID", "GITHUB_REPOSITORY_OWNER_ID",
    "GITHUB_REF", "GITHUB_EVENT_NAME", "GITHUB_RUN_ATTEMPT", "GITHUB_SHA", "GITHUB_RUN_ID",
    "GITHUB_WORKFLOW_REF", "RUNNER_ENVIRONMENT"])
def test_inspector_rejects_wrong_context(field, tmp_path):
    env = environment(tmp_path)
    env[field] = "wrong"
    with pytest.raises(PublicationError):
        experiment.context(env)


def test_caller_and_signer_must_differ_before_cli(monkeypatch, tmp_path):
    env = environment(tmp_path)
    env["GITHUB_SHA"] = SIGNER_REVISION
    with pytest.raises(PublicationError, match="revisions_must_differ"):
        experiment.context(env)
    monkeypatch.setattr(experiment, "bounded_run", lambda *args: pytest.fail("same revision reached CLI"))
    with pytest.raises(PublicationError, match="revisions_must_differ"):
        experiment.ProbeVerifier().verify(b"probe", BUNDLE, {**EXPECTED, "source_commit": SIGNER_REVISION})


def synthetic_verified_output(raw):
    cert = dict(sourceRepositoryURI=experiment.ORIGIN, sourceRepositoryRef="refs/heads/main",
        sourceRepositoryDigest=COMMIT, sourceRepositoryIdentifier="1414494920",
        sourceRepositoryOwnerIdentifier="93822871", sourceRepositoryOwnerURI="https://github.com/benchristian88",
        sourceRepositoryVisibilityAtSigning="public", runnerEnvironment="github-hosted",
        buildTrigger="workflow_dispatch", runInvocationURI=f"{experiment.ORIGIN}/actions/runs/60/attempts/1",
        buildConfigURI=f"{experiment.ORIGIN}/{experiment.CALLER}@refs/heads/main", buildConfigDigest=COMMIT,
        issuer=experiment.ISSUER, buildSignerDigest=SIGNER_REVISION,
        subjectAlternativeName=f"{experiment.ORIGIN}/{experiment.SIGNER}@refs/heads/main",
        buildSignerURI=f"{experiment.ORIGIN}/{experiment.SIGNER}@refs/heads/main")
    return [{"verificationResult": {"signature": {"certificate": cert}, "statement": {
        "_type": "https://in-toto.io/Statement/v1", "predicateType": experiment.PREDICATE,
        "subject": [{"name": "probe.json", "digest": {"sha256": digest(raw)}}],
        "predicate": {"schema": "atlas-verifier-signer-probe-predicate/v1",
                      "probe_sha256": digest(raw), "not_authorization": True}},
        "verifiedTimestamps": [{"type": "Tlog", "uri": "https://rekor.sigstore.dev", "timestamp": "synthetic"}]}}]


def test_synthetic_verified_output_uses_pinned_cryptographic_constraints(monkeypatch):
    commands = []
    raw = b"synthetic"
    def run(command, directory):
        commands.append(command)
        assert (directory / "artifact").read_bytes() == raw
        return canonical_json(synthetic_verified_output(raw))
    monkeypatch.setattr(experiment, "bounded_run", run)
    result = experiment.ProbeVerifier().verify(raw, BUNDLE, EXPECTED)
    assert result["subject"]["digest"] == {"sha256": digest(raw)}
    command, = commands
    for flag, value in {"--signer-workflow": experiment.REPOSITORY + "/" + experiment.SIGNER,
        "--signer-digest": SIGNER_REVISION, "--source-digest": COMMIT, "--source-ref": "refs/heads/main",
        "--cert-oidc-issuer": experiment.ISSUER, "--predicate-type": experiment.PREDICATE,
        "--repo": experiment.REPOSITORY}.items():
        assert command[command.index(flag) + 1] == value
    assert {"--deny-self-hosted-runners", "--custom-trusted-root", "--bundle"} <= set(command)
    assert "--cert-identity" not in command


@pytest.mark.parametrize("change", [
    lambda v: v.update(predicateType="https://atlas-impact.dev/attestations/publication-authorization/v1"),
    lambda v: v["subject"][0].update(name="authorization.json"),
    lambda v: v["subject"][0]["digest"].update(sha256="0" * 64),
    lambda v: v["subject"].append(deepcopy(v["subject"][0])),
    lambda v: v["predicate"].update(not_authorization=False),
    lambda v: v["predicate"].update(probe_sha256="0" * 64),
    lambda v: v.update(_type="wrong"), lambda v: v.update(extra="wrong"),
])
def test_synthetic_statement_policy_rejection(monkeypatch, change):
    output = synthetic_verified_output(b"probe")
    change(output[0]["verificationResult"]["statement"])
    monkeypatch.setattr(experiment, "bounded_run", lambda *args: canonical_json(output))
    with pytest.raises(PublicationError, match="probe_statement"):
        experiment.ProbeVerifier().verify(b"probe", BUNDLE, EXPECTED)


def test_no_unverified_certificate_claims_or_dsse_fallback(monkeypatch):
    def rejected(*args):
        raise PublicationError("attestation_verification_failed")
    monkeypatch.setattr(experiment, "bounded_run", rejected)
    bundle = canonical_json({"mediaType": "application/vnd.dev.sigstore.bundle.v0.3+json",
        "forged_certificate": synthetic_verified_output(b"probe"), "dsseEnvelope": {"payload": "forged"}})
    with pytest.raises(PublicationError, match="attestation_verification_failed"):
        experiment.ProbeVerifier().verify(b"probe", bundle, EXPECTED)


def test_genuine_pinned_cli_rejects_unsigned_and_other_workflow_bundles():
    verifier = experiment.ProbeVerifier()  # Real binary and roots. NO cryptographic mocks.
    with pytest.raises(PublicationError, match="attestation_verification_failed"):
        verifier.verify(b"probe", BUNDLE, EXPECTED)
    raw = (ROOT / "tests/fixtures/official_catalogue/catalogue-000001.json").read_bytes()
    bundle = (ROOT / "tests/fixtures/publication/catalogue.sigstore.json").read_bytes()
    with pytest.raises(PublicationError, match="attestation_verification_failed"):
        verifier.verify(raw, bundle, EXPECTED)


@pytest.mark.parametrize("outcome", ["accepted", "verifier_timeout", "verifier_output_limit", "probe_statement"])
def test_negative_tests_require_cli_subject_rejection(outcome):
    class FakeVerifier:
        def verify(self, *args):
            if outcome != "accepted":
                raise PublicationError(outcome)
    with pytest.raises(PublicationError, match="negative_check"):
        experiment.negative_checks(FakeVerifier(), b"probe", BUNDLE, EXPECTED)


def test_negative_tests_present_both_changed_subjects_to_verifier():
    seen = []
    class FakeVerifier:
        def verify(self, raw, bundle, expected):
            seen.append(raw)
            assert bundle == BUNDLE and expected == EXPECTED
            raise PublicationError("attestation_verification_failed")
    results = experiment.negative_checks(FakeVerifier(), b"probe", BUNDLE, EXPECTED)
    assert seen == [b"probe\n", b'{"not_the_signed_probe":true}\n']
    assert all(row["result"] == "REJECTED_BY_PINNED_CLI" for row in results.values())


def test_only_allowlisted_verified_fields_exported_and_mismatches_reported(monkeypatch):
    output = synthetic_verified_output(b"probe")
    cert = output[0]["verificationResult"]["signature"]["certificate"]
    cert["unknown"] = "must-not-export-this"
    monkeypatch.setattr(experiment, "bounded_run", lambda *args: canonical_json(output))
    result = experiment.ProbeVerifier().verify(b"probe", BUNDLE, EXPECTED)
    assert b"must-not-export-this" not in canonical_json(result)
    rows = experiment.comparisons(result, EXPECTED, {key: None for key in experiment.JOB_FIELDS}, None)
    by_name = {row["claim"]: row for row in rows}
    assert by_name["subjectAlternativeName"]["status"] == "MATCH"
    assert by_name["buildConfigDigest"]["expected"] == COMMIT
    assert by_name["buildSignerDigest"]["expected"] == SIGNER_REVISION
    assert by_name["sourceRepositoryDigest"]["status"] == "MATCH"
    assert by_name["job.workflow_sha"]["status"] == "NOT OBSERVABLE"
    assert by_name["referenced_workflows.sha"]["status"] == "NOT OBSERVABLE"
    assert not experiment.identity_accepted(rows)
    assert "NOT OBSERVABLE" in experiment.render_table(rows)


@pytest.mark.parametrize("value", ["bad\nvalue", "bad\rvalue", "\x1b[31m", "x" * 513, 1, {}])
def test_diagnostics_reject_unsafe_values(value):
    with pytest.raises(PublicationError, match="unsafe_public_diagnostic"):
        experiment.public_string(value)


def run_payload():
    return {"id": 60, "run_attempt": 1, "event": "workflow_dispatch", "head_sha": COMMIT,
        "head_branch": "main", "path": experiment.CALLER, "repository": {"id": experiment.REPOSITORY_ID},
        "referenced_workflows": [{"path": f"{experiment.REPOSITORY}/{experiment.SIGNER}@{SIGNER_REVISION}",
                                  "sha": SIGNER_REVISION, "unknown": "must-not-export-this"}],
        "unrelated": "must-not-export-this"}


def stub_api(monkeypatch, payload, headers=None, jobs=None):
    requests = []
    class Response:
        status = 200
        def __init__(self, value):
            self.raw = canonical_json(value)
            self.headers = headers or {}
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self, maximum):
            return self.raw[:maximum]
    class Opener:
        def open(self, request, timeout):
            requests.append(request)
            assert timeout == 20
            return Response(payload if len(requests) == 1 else (jobs or {"total_count": 0, "jobs": []}))
    monkeypatch.setattr(experiment.urllib.request, "build_opener", lambda *handlers: Opener())
    return requests


def test_api_is_two_fixed_gets_and_drops_unrequested_data(monkeypatch):
    requests = stub_api(monkeypatch, run_payload())
    references, timing = experiment.get_run_evidence("synthetic-job-token", EXPECTED)
    assert len(requests) == 2 and all(request.method == "GET" for request in requests)
    base = "https://api.github.com/repos/benchristian88/atlas-connectors/actions/runs/60"
    assert [request.full_url for request in requests] == [base, base + "/attempts/1/jobs?per_page=10&page=1"]
    assert references[0]["ref"] is None
    assert b"must-not-export-this" not in canonical_json([references, timing])


def test_missing_references_are_not_invented(monkeypatch):
    payload = run_payload()
    payload.pop("referenced_workflows")
    stub_api(monkeypatch, payload)
    assert experiment.get_run_evidence("synthetic-job-token", EXPECTED)[0] is None


@pytest.mark.parametrize("field", ["id", "run_attempt", "event", "head_sha", "head_branch", "path", "repository"])
def test_api_run_substitution_rejected(monkeypatch, field):
    payload = run_payload()
    payload.pop(field)
    stub_api(monkeypatch, payload)
    with pytest.raises(PublicationError, match="experiment_run_identity"):
        experiment.get_run_evidence("synthetic-job-token", EXPECTED)


def test_api_redirect_and_incomplete_results_rejected(monkeypatch):
    with pytest.raises(PublicationError, match="redirect"):
        experiment.NoRedirect().redirect_request(None)
    stub_api(monkeypatch, run_payload(), headers={"Link": "next"})
    with pytest.raises(PublicationError, match="incomplete"):
        experiment.get_run_evidence("synthetic-job-token", EXPECTED)
    stub_api(monkeypatch, run_payload(), jobs={"total_count": 1, "jobs": []})
    with pytest.raises(PublicationError, match="incomplete"):
        experiment.get_run_evidence("synthetic-job-token", EXPECTED)


def test_provider_timing_distinguishes_steps_and_scheduling():
    def job(step, start, end, job_start, job_end):
        return {"started_at": f"2026-10-23T10:00:{job_start:02d}Z",
            "completed_at": f"2026-10-23T10:00:{job_end:02d}Z", "steps": [{"name": step,
            "started_at": f"2026-10-23T10:00:{start:02d}Z", "completed_at": f"2026-10-23T10:00:{end:02d}Z"}]}
    timing = experiment.step_timings([
        job("Create public experimental subject", 1, 2, 0, 20),
        job("Download public probe", 35, 40, 30, 50)])
    assert timing["between_jobs_scheduling_gap_ms"] == 10000
    assert timing["provider_steps"]["Download public probe"] == {"elapsed_ms": 5000, "resolution_ms": 1000}


def synthetic_comparisons(certificate=None, job=None, references=None):
    cert = synthetic_verified_output(b"probe")[0]["verificationResult"]["signature"]["certificate"]
    cert.update(certificate or {})
    context = {"workflow_ref": f"{experiment.REPOSITORY}/{experiment.SIGNER}@refs/heads/main",
               "workflow_sha": SIGNER_REVISION, "workflow_repository": experiment.REPOSITORY,
               "workflow_file_path": experiment.SIGNER}
    context.update(job or {})
    return experiment.comparisons({"certificate": cert, "predicate_type": experiment.PREDICATE,
        "subject": {"name": "probe.json"}}, EXPECTED, context,
        run_payload()["referenced_workflows"] if references is None else references)


@pytest.mark.parametrize("textual_ref", ["refs/heads/main", SIGNER_REVISION])
def test_synthetic_signer_textual_ref_does_not_replace_separate_digest_pin(textual_ref):
    uri = f"{experiment.ORIGIN}/{experiment.SIGNER}@{textual_ref}"
    rows = synthetic_comparisons({"subjectAlternativeName": uri, "buildSignerURI": uri},
        {"workflow_ref": f"{experiment.REPOSITORY}/{experiment.SIGNER}@{textual_ref}"})
    assert experiment.identity_accepted(rows)  # Synthetic policy behavior only.
    assert {row["status"] for row in rows} == {"MATCH"}
    assert "S revision" in experiment.render_table(rows) and "C revision" in experiment.render_table(rows)


@pytest.mark.parametrize("field", experiment.CERT_FIELDS)
@pytest.mark.parametrize("value", [None, "wrong"])
def test_each_synthetic_certificate_binding_is_required(field, value):
    rows = synthetic_comparisons({field: value})
    assert not experiment.identity_accepted(rows)
    row = next(row for row in rows if row["claim"] == field)
    assert row["status"] == ("NOT OBSERVABLE" if value is None else "MISMATCH")


@pytest.mark.parametrize("certificate", [
    {"buildSignerDigest": COMMIT},
    {"buildSignerDigest": "b" * 40},
    {"sourceRepositoryDigest": SIGNER_REVISION},
    {"sourceRepositoryDigest": "b" * 40},
    {"buildConfigDigest": SIGNER_REVISION},
    {"buildSignerDigest": COMMIT, "sourceRepositoryDigest": SIGNER_REVISION, "buildConfigDigest": SIGNER_REVISION},
    {"buildConfigURI": f"{experiment.ORIGIN}/{experiment.SIGNER}@refs/heads/main"},
    {"buildSignerURI": f"{experiment.ORIGIN}/{experiment.CALLER}@refs/heads/main"},
    {"subjectAlternativeName": f"{experiment.ORIGIN}/{experiment.SIGNER}-other@refs/heads/main"},
    {"runInvocationURI": f"{experiment.ORIGIN}/actions/runs/60/attempts/2"},
    {"runInvocationURI": f"{experiment.ORIGIN}/actions/runs/61/attempts/1"},
])
def test_synthetic_wrong_swapped_revisions_paths_and_invocations_are_not_identity_acceptance(certificate):
    assert not experiment.identity_accepted(synthetic_comparisons(certificate))


@pytest.mark.parametrize("field", experiment.JOB_FIELDS)
@pytest.mark.parametrize("value", [None, "wrong", COMMIT])
def test_synthetic_missing_or_substituted_signer_job_context_blocks_acceptance(field, value):
    assert not experiment.identity_accepted(synthetic_comparisons(job={field: value}))


@pytest.mark.parametrize("references", [[], [{"path": "wrong", "sha": SIGNER_REVISION}],
    [{"path": f"{experiment.REPOSITORY}/{experiment.SIGNER}@{SIGNER_REVISION}", "sha": COMMIT}],
    [{"path": f"{experiment.REPOSITORY}/{experiment.SIGNER}@refs/heads/main", "sha": SIGNER_REVISION}],
    [{}, {}], [{}]])
def test_synthetic_references_cannot_substitute_caller_or_moving_signer(references):
    assert not experiment.identity_accepted(synthetic_comparisons(references=references))


@pytest.mark.parametrize("identity_failure", [None, "signer", "source", "swapped", "job", "references"])
def test_inspection_exports_only_after_crypto_and_negative_checks(monkeypatch, tmp_path, identity_failure):
    raw = generate(tmp_path)
    (tmp_path / "signer-probe/predicate.json").unlink()  # Not in the uploaded artifact.
    (tmp_path / "signer-probe").rename(tmp_path / "received-probe")
    (tmp_path / "received-probe/probe.sigstore.json").write_bytes(BUNDLE)
    (tmp_path / "received-probe/signer-timing.json").write_bytes(canonical_json({
        "subject_started_utc_ms": 1, "subject_creation_ms": 1,
        "attestation_generation_ms": 2, "attestation_finished_utc_ms": 3}))
    for key, value in environment(tmp_path).items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("GH_TOKEN", "synthetic-job-token")
    def run(command, directory):
        if (directory / "artifact").read_bytes() != raw:
            raise PublicationError("attestation_verification_failed")
        output = synthetic_verified_output(raw)
        cert = output[0]["verificationResult"]["signature"]["certificate"]
        if identity_failure in {"signer", "swapped"}:
            cert["buildSignerDigest"] = COMMIT
        if identity_failure in {"source", "swapped"}:
            cert["sourceRepositoryDigest"] = SIGNER_REVISION
        return canonical_json(output)
    monkeypatch.setattr(experiment, "bounded_run", run)
    payload = run_payload()
    if identity_failure == "job":
        # The actual subject generator can report absent context; that is signed
        # diagnostic evidence, but cannot satisfy the identity acceptance gate.
        probe = experiment.check_subject(raw, EXPECTED)
        probe["job_context"]["workflow_sha"] = None
        raw = canonical_json(probe)
        (tmp_path / "received-probe/probe.json").write_bytes(raw)
    if identity_failure == "references":
        payload.pop("referenced_workflows")
    stub_api(monkeypatch, payload)
    if identity_failure:
        with pytest.raises(PublicationError, match="pinned_experiment_identity_not_accepted"):
            experiment.main()
    else:
        experiment.main()
    report = (tmp_path / "signer-evidence/evidence.json").read_bytes()
    assert b'"production_accepted": false' in report
    assert (b'"identity_accepted": false' if identity_failure else b'"identity_accepted": true') in report
    assert (b'"experiment_result": "BLOCKED"' if identity_failure else b'"experiment_result": "PASS"') in report
    assert b'"cryptographic_verification": "VERIFIED_BY_PINNED_CLI"' in report
    assert b"synthetic-job-token" not in report and b"must-not-export-this" not in report
    assert b"NOT MEASURED" in report and b"EXCEEDS 60s" in report


def test_failed_crypto_cannot_export_acceptance_evidence(monkeypatch, tmp_path):
    generate(tmp_path)
    (tmp_path / "signer-probe/predicate.json").unlink()
    (tmp_path / "signer-probe").rename(tmp_path / "received-probe")
    (tmp_path / "received-probe/probe.sigstore.json").write_bytes(BUNDLE)
    (tmp_path / "received-probe/signer-timing.json").write_bytes(canonical_json({
        "subject_started_utc_ms": 1, "subject_creation_ms": 1,
        "attestation_generation_ms": 2, "attestation_finished_utc_ms": 3}))
    for key, value in environment(tmp_path).items():
        monkeypatch.setenv(key, value)
    def rejected(*args):
        raise PublicationError("attestation_verification_failed")
    monkeypatch.setattr(experiment, "bounded_run", rejected)
    with pytest.raises(PublicationError, match="attestation_verification_failed"):
        experiment.main()
    assert not (tmp_path / "signer-evidence").exists()
