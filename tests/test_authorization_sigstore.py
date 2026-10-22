# SPDX-License-Identifier: Apache-2.0
"""Synthetic VERIFIED-OUTPUT policy tests plus genuine old-profile rejection.

Mocking bounded_run never proves a signature. Genuine verification is marked
separately and uses the hash-pinned gh executable and unchanged trust fixtures.
"""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import authorization_sigstore as crypto
from publication_authorization import AuthorizationVerifier, SUBJECT, WORKFLOW, PREDICATE
from publication_contract import (OWNER_ID, REPOSITORY_ID, PUBLICATION_WORKFLOW, canonical_json, digest)
from publication_verify import ISSUER, ORIGIN
from test_publication_authorization import ROOT, SOURCE, REVISION, NOW, fixture, issue_fixture

SYNTHETIC_BUNDLE = canonical_json({"mediaType": "application/vnd.dev.sigstore.bundle.v0.3+json"})


def synthetic_verified_output(raw):
    identity = f"{ORIGIN}/{WORKFLOW}@refs/heads/main"
    return [{"verificationResult": {
        "signature": {"certificate": {"issuer": ISSUER, "subjectAlternativeName": identity,
            "buildSignerURI": identity, "buildSignerDigest": REVISION,
            "sourceRepositoryURI": ORIGIN, "sourceRepositoryIdentifier": str(REPOSITORY_ID),
            "sourceRepositoryOwnerIdentifier": str(OWNER_ID),
            "sourceRepositoryOwnerURI": "https://github.com/benchristian88", "sourceRepositoryDigest": SOURCE,
            "sourceRepositoryRef": "refs/heads/main", "sourceRepositoryVisibilityAtSigning": "public",
            "runnerEnvironment": "github-hosted",
            "buildConfigURI": f"{ORIGIN}/{PUBLICATION_WORKFLOW}@refs/heads/main",
            "buildConfigDigest": SOURCE, "buildTrigger": "workflow_dispatch",
            "runInvocationURI": f"{ORIGIN}/actions/runs/60/attempts/1"}},
        "statement": {"_type": "https://in-toto.io/Statement/v1", "subject": [{"name": SUBJECT,
            "digest": {"sha256": digest(raw)}}], "predicateType": PREDICATE,
            "predicate": {"schema": "atlas-publication-decision/v1", "authorization_sha256": digest(raw)}},
        "verifiedTimestamps": [{"type": "Tlog", "uri": "https://rekor.sigstore.dev", "timestamp": "synthetic"}]}}]


@pytest.fixture
def decision(monkeypatch):
    import issue_publication_authorization as issuer
    monkeypatch.setattr(issuer, "app_jwt", lambda key: "synthetic-jwt")
    data = fixture()
    return data, issue_fixture(data)


def test_synthetic_branch_ref_and_independent_pinned_digest_enforce_all_cli_constraints(monkeypatch, decision):
    data, raw = decision
    commands = []
    def run(command, directory):
        commands.append(command)
        assert (directory / "artifact").read_bytes() == raw
        assert (directory / "bundle.json").read_bytes() == SYNTHETIC_BUNDLE
        return canonical_json(synthetic_verified_output(raw))
    monkeypatch.setattr(crypto, "bounded_run", run)
    AuthorizationVerifier(data[3], data[4]).verify_and_consume(raw, SYNTHETIC_BUNDLE, data[2], clock=lambda: NOW)
    command = commands[0]
    flags = {"--signer-digest": REVISION,
             "--source-digest": SOURCE, "--source-ref": "refs/heads/main", "--cert-oidc-issuer": ISSUER,
             "--predicate-type": PREDICATE, "--signer-workflow": "benchristian88/atlas-connectors/" + WORKFLOW}
    for flag, expected in flags.items():
        assert command[command.index(flag) + 1] == expected
    for flag in ("--deny-self-hosted-runners", "--custom-trusted-root", "--bundle"):
        assert flag in command
    # gh 2.102.1 makes these mutually exclusive. Exact SAN is checked in verified output.
    assert "--cert-identity" not in command
    assert SOURCE != REVISION  # Verifier revision is not automatically the source SHA.


@pytest.mark.parametrize("field", ["subjectAlternativeName", "buildSignerURI"])
@pytest.mark.parametrize("identity", [
    f"{ORIGIN}/{WORKFLOW}@{REVISION}",  # Old, unsupported SHA-suffixed URI.
    f"{ORIGIN}/{WORKFLOW}@refs/heads/other",
    f"{ORIGIN}/{WORKFLOW}@refs/tags/main",
    f"{ORIGIN}/.github/workflows/verifier-signer-probe.yml@refs/heads/main",
    f"{ORIGIN}/{PUBLICATION_WORKFLOW}@refs/heads/main",
])
def test_synthetic_signer_uri_is_exact_even_with_correct_pinned_digest(monkeypatch, decision, field, identity):
    data, raw = decision
    value = synthetic_verified_output(raw)
    certificate = value[0]["verificationResult"]["signature"]["certificate"]
    certificate[field] = identity
    assert certificate["buildSignerDigest"] == data[3]["signer_revision"]
    monkeypatch.setattr(crypto, "bounded_run", lambda *a: canonical_json(value))
    with pytest.raises(ValueError, match="authorization_certificate"):
        crypto.AuthorizationSigstore().verify(raw, SYNTHETIC_BUNDLE, expected=data[2], trust=data[3])


def test_synthetic_correct_branch_ref_cannot_substitute_signer_revision(monkeypatch, decision):
    data, raw = decision
    value = synthetic_verified_output(raw)
    value[0]["verificationResult"]["signature"]["certificate"]["buildSignerDigest"] = SOURCE
    monkeypatch.setattr(crypto, "bounded_run", lambda *a: canonical_json(value))
    with pytest.raises(ValueError, match="authorization_certificate"):
        crypto.AuthorizationSigstore().verify(raw, SYNTHETIC_BUNDLE, expected=data[2], trust=data[3])


def test_genuine_probe_evidence_remains_distinct_from_production_authorization(decision):
    from verifier_signer_experiment import ProbeVerifier, SIGNER, check_subject, negative_checks
    expected = {"source_commit": "e5287c3229f5b9a1dc4c3dbcda0f4193fe221c3c",
                "run_id": 39846232008, "run_attempt": 1}
    base = ROOT / "tests/fixtures/verifier_signer_probe"
    raw, bundle = (base / "probe.json").read_bytes(), (base / "probe.sigstore.json").read_bytes()
    assert digest(raw) == "75052edaed33fda77502ed2ecac49515f9e22f96f7a009ef6cb4ad3f9041e08a"
    assert digest(bundle) == "02fa47cde8e739dad47dfe8e902b2759f9eb2f1488cd60bebd8865ef5730d199"
    subject = check_subject(raw, expected)
    verifier = ProbeVerifier()  # Real pinned CLI, unchanged roots. No mocks.
    verified = verifier.verify(raw, bundle, expected)
    certificate = verified["certificate"]
    assert certificate["subjectAlternativeName"] == certificate["buildSignerURI"] == f"{ORIGIN}/{SIGNER}@refs/heads/main"
    assert certificate["buildSignerDigest"] == certificate["sourceRepositoryDigest"] == expected["source_commit"]
    assert subject["job_context"]["workflow_ref"] == f"benchristian88/atlas-connectors/{SIGNER}@refs/heads/main"
    assert subject["job_context"]["workflow_sha"] == expected["source_commit"]
    assert verified["predicate_type"] != PREDICATE and verified["subject"]["name"] != SUBJECT
    assert len(negative_checks(verifier, raw, bundle, expected)) == 2
    # Matching genuine source/signer digests cannot turn the probe's distinct
    # workflow, predicate and subject into a production grant. Test-only trust.
    data, _ = decision
    request, trust = deepcopy(data[2]), deepcopy(data[3])
    request.update(expected)
    trust["signer_revision"] = expected["source_commit"]
    with pytest.raises(ValueError, match="attestation_verification_failed"):
        crypto.AuthorizationSigstore().verify(raw, bundle, expected=request, trust=trust)


@pytest.mark.parametrize("field", list(synthetic_verified_output(b"test")[0]["verificationResult"]["signature"]["certificate"]))
def test_each_synthetic_certificate_constraint_rejects_wrong_or_absent_value(monkeypatch, decision, field):
    data, raw = decision
    for remove in (False, True):
        value = synthetic_verified_output(raw)
        certificate = value[0]["verificationResult"]["signature"]["certificate"]
        if remove:
            certificate.pop(field)
        else:
            certificate[field] = "wrong"
        monkeypatch.setattr(crypto, "bounded_run", lambda *a: canonical_json(value))
        with pytest.raises(ValueError):
            crypto.AuthorizationSigstore().verify(raw, SYNTHETIC_BUNDLE, expected=data[2], trust=data[3])


@pytest.mark.parametrize("change", [
    lambda v: v.update(predicateType="https://slsa.dev/provenance/v1"),
    lambda v: v.update(_type="wrong"), lambda v: v.update(extra="wrong"),
    lambda v: v.update(subject=[]), lambda v: v["subject"].append(deepcopy(v["subject"][0])),
    lambda v: v["subject"][0].update(name="current.json"),
    lambda v: v["subject"][0]["digest"].update(sha256="0" * 64),
    lambda v: v["predicate"].update(authorization_sha256="0" * 64),
    lambda v: v["predicate"].update(extra="wrong"), lambda v: v.update(predicate={}),
])
def test_synthetic_statement_digest_subject_and_predicate_rejection(monkeypatch, decision, change):
    data, raw = decision
    value = synthetic_verified_output(raw)
    change(value[0]["verificationResult"]["statement"])
    monkeypatch.setattr(crypto, "bounded_run", lambda *a: canonical_json(value))
    with pytest.raises(ValueError):
        crypto.AuthorizationSigstore().verify(raw, SYNTHETIC_BUNDLE, expected=data[2], trust=data[3])


@pytest.mark.parametrize("timestamps", [[], [{"type": "TimestampAuthority", "uri": "https://rekor.sigstore.dev"}],
    [{"type": "Tlog", "uri": "https://evil.example"}], [{"type": "Tlog", "uri": "https://rekor.sigstore.dev"}] * 9])
def test_synthetic_transparency_evidence_rejection(monkeypatch, decision, timestamps):
    data, raw = decision
    value = synthetic_verified_output(raw)
    value[0]["verificationResult"]["verifiedTimestamps"] = timestamps
    monkeypatch.setattr(crypto, "bounded_run", lambda *a: canonical_json(value))
    with pytest.raises(ValueError):
        crypto.AuthorizationSigstore().verify(raw, SYNTHETIC_BUNDLE, expected=data[2], trust=data[3])


@pytest.mark.parametrize("output", [b"[]", b"{}", b"[{}]", b"null", b'{"a":1,"a":2}', b"NaN"])
def test_malformed_verified_output_fails_closed(monkeypatch, decision, output):
    data, raw = decision
    monkeypatch.setattr(crypto, "bounded_run", lambda *a: output)
    with pytest.raises(ValueError):
        crypto.AuthorizationSigstore().verify(raw, SYNTHETIC_BUNDLE, expected=data[2], trust=data[3])


def test_existing_publisher_signer_cannot_authenticate_decision_even_in_synthetic_output(monkeypatch, decision):
    data, raw = decision
    value = synthetic_verified_output(raw)
    cert = value[0]["verificationResult"]["signature"]["certificate"]
    cert.update(subjectAlternativeName=f"{ORIGIN}/{PUBLICATION_WORKFLOW}@refs/heads/main",
                buildSignerURI=f"{ORIGIN}/{PUBLICATION_WORKFLOW}@refs/heads/main", buildSignerDigest=SOURCE)
    monkeypatch.setattr(crypto, "bounded_run", lambda *a: canonical_json(value))
    with pytest.raises(ValueError, match="certificate"):
        crypto.AuthorizationSigstore().verify(raw, SYNTHETIC_BUNDLE, expected=data[2], trust=data[3])


@pytest.mark.parametrize("bundle", [b"", b"{}", b"[]", b"\xff", b" " * (1024 * 1024 + 1)])
def test_invalid_bundles_never_reach_cli(monkeypatch, decision, bundle):
    data, raw = decision
    monkeypatch.setattr(crypto, "bounded_run", lambda *a: pytest.fail("invalid bundle reached CLI"))
    with pytest.raises(ValueError):
        crypto.AuthorizationSigstore().verify(raw, bundle, expected=data[2], trust=data[3])


def test_genuine_pinned_gh_rejects_unsigned_synthetic_and_existing_genuine_profiles(decision):
    data, raw = decision
    verifier = crypto.AuthorizationSigstore()  # Real pinned executable/roots, NO mocks here.
    for bundle in [SYNTHETIC_BUNDLE,
                   (ROOT / "tests/fixtures/publication/catalogue.sigstore.json").read_bytes(),
                   (ROOT / "tests/fixtures/publication/package.sigstore.json").read_bytes()]:
        with pytest.raises(ValueError):
            verifier.verify(raw, bundle, expected=data[2], trust=data[3])
    original = (ROOT / "tests/fixtures/official_catalogue/catalogue-000001.json").read_bytes()
    with pytest.raises(ValueError):
        verifier.verify(original, (ROOT / "tests/fixtures/publication/catalogue.sigstore.json").read_bytes(),
                        expected=data[2], trust=data[3])


def test_genuine_fixture_proves_pinned_cli_accepts_separate_signer_and_source_flags(tmp_path):
    from atlas_connector_sdk.contracts import strict_json
    from publication_verify import bounded_run, TRUST
    verifier = crypto.AuthorizationSigstore()
    source = "91dfd86f18d0b59ff977bb1e8a5fef42c5329943"
    output = bounded_run([str(verifier.binary), "attestation", "verify",
        str(ROOT / "tests/fixtures/official_catalogue/catalogue-000001.json"),
        "--bundle", str(ROOT / "tests/fixtures/publication/catalogue.sigstore.json"),
        "--custom-trusted-root", str(TRUST / "trusted-root.jsonl"), "--repo", "benchristian88/atlas-connectors",
        "--signer-workflow", "benchristian88/atlas-connectors/.github/workflows/catalogue.yml",
        "--signer-digest", source, "--source-digest", source, "--source-ref", "refs/heads/main",
        "--cert-oidc-issuer", ISSUER, "--deny-self-hosted-runners",
        "--predicate-type", "https://slsa.dev/provenance/v1", "--digest-alg", "sha256", "--format", "json"], tmp_path)
    assert strict_json(output)[0]["verificationResult"]["signature"]["certificate"]["buildSignerDigest"] == source


def test_real_verifier_subprocess_has_no_ambient_credentials(monkeypatch, tmp_path):
    import json
    from publication_verify import bounded_run
    monkeypatch.setenv("GH_TOKEN", "synthetic-sensitive-token")
    monkeypatch.setenv("VERIFICATION_APP_PRIVATE_KEY", "synthetic-sensitive-key")
    output = bounded_run([sys.executable, "-c", "import os,json; print(json.dumps(dict(os.environ)))"], tmp_path)
    environment = json.loads(output)
    assert "GH_TOKEN" not in environment and "VERIFICATION_APP_PRIVATE_KEY" not in environment
    assert environment["PATH"] == "/nonexistent" and environment["GH_CONFIG_DIR"] == str(tmp_path)


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_real_verifier_subprocess_combined_output_limit(tmp_path, stream):
    from publication_verify import bounded_run
    with pytest.raises(ValueError, match="output_limit"):
        bounded_run([sys.executable, "-c", f"import sys; sys.{stream}.write('x'*4096)"], tmp_path, maximum=512)


def test_real_verifier_subprocess_timeout(tmp_path):
    from publication_verify import bounded_run
    with pytest.raises(ValueError, match="timeout"):
        bounded_run([sys.executable, "-c", "import time; time.sleep(2)"], tmp_path, seconds=0.1)
