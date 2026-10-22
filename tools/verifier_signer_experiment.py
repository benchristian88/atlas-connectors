# SPDX-License-Identifier: Apache-2.0
"""Non-production signer evidence. Trust only the pinned CLI's VERIFIED output.

This module is used exclusively by the manual experimental inspection job. It
neither imports the authorization issuer nor changes production signer policy.
"""
from datetime import datetime
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import urllib.request

from atlas_connector_sdk.contracts import strict_json
from publication_contract import (MAX_BUNDLE_BYTES, OWNER_ID, REPOSITORY, REPOSITORY_ID,
    PublicationError, canonical_json, digest, hexadecimal, require)
from publication_verify import ISSUER, ORIGIN, Verifier, bounded_run, read_regular

CALLER = ".github/workflows/verifier-signer-experiment.yml"
SIGNER = ".github/workflows/verifier-signer-probe.yml"
PREDICATE = "https://atlas-impact.dev/attestations/verifier-signer-experiment/v1"
JOB_FIELDS = ("workflow_ref", "workflow_sha", "workflow_repository", "workflow_file_path")
CERT_FIELDS = ("subjectAlternativeName", "buildSignerURI", "buildSignerDigest",
    "buildConfigURI", "buildConfigDigest", "sourceRepositoryURI", "sourceRepositoryRef",
    "sourceRepositoryDigest", "sourceRepositoryIdentifier", "sourceRepositoryOwnerIdentifier",
    "sourceRepositoryOwnerURI", "sourceRepositoryVisibilityAtSigning", "issuer",
    "runnerEnvironment", "buildTrigger", "runInvocationURI")


def public_string(value):
    require(value is None or (type(value) is str and len(value) <= 512
            and all(32 <= ord(c) <= 126 for c in value)), "unsafe_public_diagnostic")
    return value


def context(env):
    expected = {"GITHUB_REPOSITORY": REPOSITORY, "GITHUB_REPOSITORY_ID": str(REPOSITORY_ID),
        "GITHUB_REPOSITORY_OWNER_ID": str(OWNER_ID), "GITHUB_REF": "refs/heads/main",
        "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_WORKFLOW_REF": f"{REPOSITORY}/{CALLER}@refs/heads/main",
        "RUNNER_ENVIRONMENT": "github-hosted"}
    require(all(env.get(key) == value for key, value in expected.items()), "experiment_context")
    commit, run = env.get("GITHUB_SHA"), env.get("GITHUB_RUN_ID", "")
    require(hexadecimal(commit, 40) and re.fullmatch(r"[1-9][0-9]{0,14}", run), "experiment_source")
    return {"source_commit": commit, "run_id": int(run), "run_attempt": 1}


def check_subject(raw, expected):
    value = strict_json(raw, maximum=4096)
    require(isinstance(value, dict) and isinstance(value.get("job_context"), dict), "probe_shape")
    job = value["job_context"]
    require(set(job) == set(JOB_FIELDS), "probe_job_context")
    for field in JOB_FIELDS:
        public_string(job[field])
    require(all(type(value.get(key)) is int for key in ("repository_id", "owner_id", "run_id", "run_attempt")),
            "probe_identifiers")
    require(value == {"schema": "atlas-verifier-signer-experiment/v1",
        "repository": REPOSITORY, "repository_id": REPOSITORY_ID, "owner_id": OWNER_ID,
        **expected, "note": "NOT a publication authorization", "job_context": job}
        and canonical_json(value) == raw, "probe_subject")
    return value


class ProbeVerifier(Verifier):
    def verify(self, artifact, bundle, expected):
        require(type(artifact) is bytes and 0 < len(artifact) <= 65536, "probe_size")
        require(type(bundle) is bytes and 0 < len(bundle) <= MAX_BUNDLE_BYTES, "attestation_size")
        envelope = strict_json(bundle, maximum=MAX_BUNDLE_BYTES)
        require(isinstance(envelope, dict) and envelope.get("mediaType") ==
                "application/vnd.dev.sigstore.bundle.v0.3+json", "attestation_format")
        commit = expected["source_commit"]
        require(hexadecimal(commit, 40), "experiment_source")
        with tempfile.TemporaryDirectory(prefix="atlas-probe-verification-") as work:
            directory = Path(work)
            for name, raw in (("artifact", artifact), ("bundle.json", bundle), ("roots.jsonl", self.roots)):
                (directory / name).write_bytes(raw)
            command = [str(self.binary), "attestation", "verify", str(directory / "artifact"),
                "--bundle", str(directory / "bundle.json"), "--custom-trusted-root", str(directory / "roots.jsonl"),
                "--repo", REPOSITORY, "--hostname", "github.com",
                "--signer-workflow", REPOSITORY + "/" + SIGNER, "--signer-digest", commit,
                "--source-digest", commit, "--source-ref", "refs/heads/main",
                "--cert-oidc-issuer", ISSUER, "--deny-self-hosted-runners",
                "--predicate-type", PREDICATE, "--digest-alg", "sha256", "--format", "json"]
            # No certificate or DSSE payload is inspected before this succeeds.
            output = strict_json(bounded_run(command, directory), maximum=1024 * 1024)
        require(isinstance(output, list) and len(output) == 1, "probe_verified_result")
        try:
            verified = output[0]["verificationResult"]
            certificate = verified["signature"]["certificate"]
            require(isinstance(certificate, dict), "probe_certificate")
            statement = verified["statement"]
            require(statement == {"_type": "https://in-toto.io/Statement/v1",
                "subject": [{"name": "probe.json", "digest": {"sha256": digest(artifact)}}],
                "predicateType": PREDICATE, "predicate": {
                    "schema": "atlas-verifier-signer-probe-predicate/v1",
                    "probe_sha256": digest(artifact), "not_authorization": True}}, "probe_statement")
            timestamps = verified["verifiedTimestamps"]
            require(isinstance(timestamps, list) and 1 <= len(timestamps) <= 8 and all(
                isinstance(t, dict) and t.get("type") == "Tlog" and t.get("uri") in
                {"https://rekor.sigstore.dev", "https://log2025-1.rekor.sigstore.dev"}
                for t in timestamps), "probe_transparency")
            return {"certificate": {key: public_string(certificate.get(key)) for key in CERT_FIELDS},
                "predicate_type": statement["predicateType"], "subject": statement["subject"][0],
                "verified_timestamps": [{key: public_string(t.get(key))
                    for key in ("type", "uri", "timestamp")} for t in timestamps]}
        except (KeyError, TypeError, AttributeError):
            raise PublicationError("probe_verified_result") from None


def negative_checks(verifier, raw, bundle, expected):
    results = {}
    for name, changed in (("tampered_subject", raw + b"\n"),
                          ("substituted_subject", b'{"not_the_signed_probe":true}\n')):
        start = time.monotonic_ns()
        try:
            verifier.verify(changed, bundle, expected)
        except PublicationError as error:
            # Timeouts, malformed output and postverification policy rejection
            # are NOT proof that cryptographic subject binding was enforced.
            require(str(error) == "attestation_verification_failed", "negative_check_inconclusive")
        else:
            raise PublicationError("negative_check_accepted")
        results[name] = {"result": "REJECTED_BY_PINNED_CLI",
                         "elapsed_ms": (time.monotonic_ns() - start) // 1000000}
    return results


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise PublicationError("experiment_api_redirect")


def get_run_evidence(token, expected):
    """Two fixed GETs using only the read-scoped inspection job token."""
    require(type(token) is str and 0 < len(token) <= 4096, "experiment_job_token_missing")
    base = f"https://api.github.com/repos/{REPOSITORY}/actions/runs/{expected['run_id']}"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    def get(suffix):
        request = urllib.request.Request(base + suffix, method="GET", headers={
            "Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "atlas-signer-experiment"})
        with opener.open(request, timeout=20) as response:
            require(response.status == 200 and not response.headers.get("Link"), "experiment_api_incomplete")
            raw = response.read(1024 * 1024 + 1)
        return strict_json(raw, maximum=1024 * 1024)
    run = get("")
    require(isinstance(run, dict) and run.get("id") == expected["run_id"]
        and run.get("run_attempt") == 1 and run.get("event") == "workflow_dispatch"
        and run.get("head_sha") == expected["source_commit"] and run.get("head_branch") == "main"
        and run.get("path") == CALLER and run.get("repository", {}).get("id") == REPOSITORY_ID,
        "experiment_run_identity")
    references = run.get("referenced_workflows")
    require(references is None or (isinstance(references, list) and len(references) <= 32
            and all(isinstance(row, dict) for row in references)), "experiment_references")
    sanitized = None if references is None else [
        {key: public_string(row.get(key)) for key in ("path", "sha", "ref")} for row in references]
    jobs = get("/attempts/1/jobs?per_page=10&page=1")
    require(isinstance(jobs, dict) and isinstance(jobs.get("jobs"), list)
        and jobs.get("total_count") == len(jobs["jobs"]) <= 10, "experiment_jobs_incomplete")
    return sanitized, step_timings(jobs["jobs"])


def utc_ms(value):
    require(type(value) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value),
            "experiment_timestamp")
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)


def step_timings(jobs):
    # Allowlist step names. Never export arbitrary job/step names or API payloads.
    names = {"Create public experimental subject", "Attest experimental subject",
        "Upload public probe", "Download public probe", "Install pinned offline SDK and verifier"}
    result, starts, ends = {}, {}, {}
    for job in jobs:
        require(isinstance(job, dict) and isinstance(job.get("steps"), list), "experiment_jobs")
        for step in job["steps"]:
            if step.get("name") in names and step.get("started_at") and step.get("completed_at"):
                name = step["name"]
                require(name not in result, "experiment_duplicate_phase")
                start, end = utc_ms(step["started_at"]), utc_ms(step["completed_at"])
                require(end >= start, "experiment_phase_time")
                result[name] = {"elapsed_ms": end - start, "resolution_ms": 1000}
                starts[name], ends[name] = start, end
                if name == "Create public experimental subject":
                    ends["sign_job"] = utc_ms(job["completed_at"])
                if name == "Download public probe":
                    starts["inspect_job"] = utc_ms(job["started_at"])
    gap = None
    if "inspect_job" in starts and "sign_job" in ends:
        gap = max(0, starts["inspect_job"] - ends["sign_job"])
    return {"provider_steps": result, "between_jobs_scheduling_gap_ms": gap,
            "missing_steps": sorted(names - result.keys())}


def comparisons(verified, expected, job_context):
    """Literal V1 comparison plus mapped workflow roles; never changes V1 policy."""
    commit = expected["source_commit"]
    production_signer = f"{ORIGIN}/.github/workflows/catalogue-verifier.yml@<PINNED_VERIFIER_SHA>"
    probe_signer = f"{ORIGIN}/{SIGNER}@{commit}"
    common = {"sourceRepositoryURI": ORIGIN, "sourceRepositoryRef": "refs/heads/main",
        "sourceRepositoryDigest": commit, "sourceRepositoryIdentifier": str(REPOSITORY_ID),
        "sourceRepositoryOwnerIdentifier": str(OWNER_ID),
        "sourceRepositoryOwnerURI": "https://github.com/benchristian88",
        "sourceRepositoryVisibilityAtSigning": "public", "issuer": ISSUER,
        "runnerEnvironment": "github-hosted", "buildTrigger": "workflow_dispatch",
        "runInvocationURI": f"{ORIGIN}/actions/runs/{expected['run_id']}/attempts/1"}
    v1 = {**common, "subjectAlternativeName": production_signer, "buildSignerURI": production_signer,
        "buildSignerDigest": "<PINNED_VERIFIER_SHA>",
        "buildConfigURI": f"{ORIGIN}/.github/workflows/catalogue-publish.yml@refs/heads/main",
        "buildConfigDigest": commit}
    mapped = {**common, "subjectAlternativeName": probe_signer, "buildSignerURI": probe_signer,
        "buildSignerDigest": commit, "buildConfigURI": f"{ORIGIN}/{CALLER}@refs/heads/main",
        "buildConfigDigest": commit}
    observed = verified["certificate"]
    rows = []
    def add(claim, wanted, analogue, actual):
        def status(expectation):
            if actual is None or "<PINNED_VERIFIER_SHA>" in str(expectation):
                return "NOT OBSERVABLE"
            return "MATCH" if actual == expectation else "MISMATCH"
        rows.append({"claim": claim, "expected_v1": wanted, "probe_role_expectation": analogue,
                     "observed": actual, "v1_status": status(wanted), "probe_role_status": status(analogue)})
    for key in CERT_FIELDS:
        add(key, v1[key], mapped[key], observed[key])
    add("predicateType", "https://atlas-impact.dev/attestations/publication-authorization/v1",
        PREDICATE, verified["predicate_type"])
    add("subject.name", "authorization.json", "probe.json", verified["subject"]["name"])
    for field, value in job_context.items():
        wanted = {"workflow_ref": f"{REPOSITORY}/.github/workflows/catalogue-verifier.yml@<PINNED_VERIFIER_SHA>",
            "workflow_sha": "<PINNED_VERIFIER_SHA>", "workflow_repository": REPOSITORY,
            "workflow_file_path": ".github/workflows/catalogue-verifier.yml"}[field]
        analogue = {"workflow_ref": f"{REPOSITORY}/{SIGNER}@{commit}", "workflow_sha": commit,
                    "workflow_repository": REPOSITORY, "workflow_file_path": SIGNER}[field]
        add("job." + field + " (workflow-reported)", wanted, analogue, value)
    return rows


def render_table(rows):
    def cell(value):
        return str(value if value is not None else "NOT OBSERVABLE").replace("|", "&#124;").replace("<", "&lt;")
    columns = ("claim", "expected_v1", "observed", "v1_status", "probe_role_expectation", "probe_role_status")
    return ("# Experimental signer comparison\n\n"
        "No production acceptance. Workflow names, predicate and subject differ intentionally. "
        "The probe-role columns preserve V1's SHA-ref assumption while mapping workflow names; "
        "a mismatch there requires investigation and a separate security-reviewed correction. "
        "Job context is signed workflow-reported data, not a certificate extension.\n\n"
        + "| " + " | ".join(columns) + " |\n| " + " | ".join(["---"] * len(columns)) + " |\n"
        + "".join("| " + " | ".join(cell(row[key]) for key in columns) + " |\n" for row in rows))


def main():
    expected = context(os.environ)
    source = Path(os.environ["RUNNER_TEMP"]) / "received-probe"
    require({p.name for p in source.iterdir()} == {"probe.json", "probe.sigstore.json", "signer-timing.json"},
            "experiment_artifact_inventory")
    raw = read_regular(source / "probe.json", 4096)
    probe = check_subject(raw, expected)
    bundle = read_regular(source / "probe.sigstore.json", MAX_BUNDLE_BYTES)
    timing = strict_json(read_regular(source / "signer-timing.json", 4096))
    timing_fields = {"subject_started_utc_ms", "subject_creation_ms", "attestation_generation_ms",
                     "attestation_finished_utc_ms"}
    require(isinstance(timing, dict) and set(timing) == timing_fields
            and all(type(v) is int and 0 <= v <= 2**53 - 1 for v in timing.values()), "experiment_timing")
    verifier = ProbeVerifier()
    start = time.monotonic_ns()
    verified = verifier.verify(raw, bundle, expected)
    elapsed = (time.monotonic_ns() - start) // 1000000
    finished = time.time_ns() // 1000000
    negative = negative_checks(verifier, raw, bundle, expected)
    references, provider_timing = get_run_evidence(os.environ.get("GH_TOKEN"), expected)
    total = finished - timing["subject_started_utc_ms"]
    require(total >= 0, "experiment_clock_skew")
    rows = comparisons(verified, expected, probe["job_context"])
    report = {"schema": "atlas-verifier-signer-evidence/v1", "production_accepted": False,
        "context": expected, "authenticated": verified, "workflow_reported_job_context": probe["job_context"],
        "caller_run_referenced_workflows": references,
        "missing_certificate_fields": [key for key, value in verified["certificate"].items() if value is None],
        "missing_job_context_fields": [key for key, value in probe["job_context"].items() if value is None],
        "referenced_workflows_status": "NOT OBSERVABLE" if references is None else "OBSERVED",
        "negative_checks": negative, "comparison": rows,
        "timing": {"signer_reported": timing, "independent_verification_monotonic_ms": elapsed,
            "subject_start_to_positive_verification_end_ms": total, **provider_timing,
            "authorization_observation_time": "NOT MEASURED; probe observes no authorization evidence",
            "freshness_budget_seconds": 60,
            "single_sample_assessment": "EXCEEDS 60s" if total >= 60000 else "BELOW 60s; feasibility NOT established",
            "limitations": "Cross-host UTC elapsed includes setup, queue and transfer; clock skew possible. "
                "Unsigned timing/API diagnostics are not certificate claims. Negative tests and API inspection excluded "
                "from positive-path total. Evidence upload occurs afterward and is excluded."}}
    destination = Path(os.environ["RUNNER_TEMP"]) / "signer-evidence"
    destination.mkdir(mode=0o700)
    (destination / "evidence.json").write_bytes(canonical_json(report))
    (destination / "comparison.md").write_text(render_table(rows))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit("signer_experiment_not_verified; no acceptance evidence exported")
