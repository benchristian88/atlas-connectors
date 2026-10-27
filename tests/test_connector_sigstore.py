# SPDX-License-Identifier: Apache-2.0
"""S2's genuine certificate drives policy regressions, not live acceptance.

The hosted subject bytes were not exported. Mocked CLI output below combines
the real decoded certificate with a modeled subject/statement; it must never be
presented as the original gh verification result or cryptographic admission.
"""
from copy import deepcopy
import base64
import json
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import ExtensionOID, ObjectIdentifier
import pytest

from test_connector_publication import (ROOT, REVIEWED_IMPLEMENTATION, admission_data,
    contract, crypto, issue, request, verified_output)
from test_authorization_sigstore import SYNTHETIC_BUNDLE
from publication_contract import canonical_json, digest
from publication_verify import ISSUER, ORIGIN

FIXTURE = ROOT / "tests/fixtures/connector_sigstore_s2"
CALLER = "c7299f9375ccf401c0cf69cb9022dc76a3556b48"
RUN = 40534608937
SUBJECT_DIGEST = "adb72b7a03f72b004bb3d60d22ca8cb98517888687b4a6d501c8c6adfefc230c"
IDENTITY = f"{ORIGIN}/{contract.SIGNER}@{REVIEWED_IMPLEMENTATION}"
EXTENSIONS = {
    "issuer": 8, "buildSignerURI": 9, "buildSignerDigest": 10,
    "runnerEnvironment": 11, "sourceRepositoryURI": 12,
    "sourceRepositoryDigest": 13, "sourceRepositoryRef": 14,
    "sourceRepositoryIdentifier": 15, "sourceRepositoryOwnerURI": 16,
    "sourceRepositoryOwnerIdentifier": 17, "buildConfigURI": 18,
    "buildConfigDigest": 19, "buildTrigger": 20, "runInvocationURI": 21,
    "sourceRepositoryVisibilityAtSigning": 22,
}


def certificate_claims():
    """Decode the preserved PEM for policy tests; decoding is not verification."""
    certificate = x509.load_pem_x509_certificate((FIXTURE / "certificate.pem").read_bytes())
    def extension(number):
        raw = certificate.extensions.get_extension_for_oid(
            ObjectIdentifier(f"1.3.6.1.4.1.57264.1.{number}")).value.value
        # Fulcio's current extensions are DER UTF8Strings, including long URIs.
        assert raw[0] == 12
        length, offset = raw[1], 2
        if length & 128:
            size = length & 127
            length, offset = int.from_bytes(raw[2:2 + size], "big"), 2 + size
        assert len(raw) == offset + length
        return raw[offset:].decode("utf-8")
    names = certificate.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME).value
    assert len(names) == 1
    return {"subjectAlternativeName": names.get_values_for_type(x509.UniformResourceIdentifier)[0],
            **{field: extension(number) for field, number in EXTENSIONS.items()}}


def hosted_policy_model(monkeypatch):
    """Real certificate, synthetic artifact and CLI result, independent context."""
    inputs = request(acceptance_only=True, commit=CALLER)
    data = admission_data(inputs, caller=CALLER)
    raw = issue(data, monkeypatch)
    expected = contract.context(data[1], inputs)
    expected.update(run_id=RUN)
    output = verified_output(raw)
    output[0]["verificationResult"]["signature"]["certificate"] = certificate_claims()
    monkeypatch.setattr(crypto, "bounded_run", lambda *args: canonical_json(output))
    return raw, expected, data[2], output


def verify_model(model):
    raw, expected, trust, _ = model
    return crypto.ConnectorSigstore().verify(raw, SYNTHETIC_BUNDLE, expected=expected, trust=trust)


def test_original_hosted_evidence_is_consistent():
    bundle = json.loads((FIXTURE / "bundle.sigstore.json").read_bytes())
    response = json.loads((FIXTURE / "attestations.json").read_bytes())
    assert len(response["attestations"]) == 1
    assert response["attestations"][0]["bundle"] == bundle
    assert response["attestations"][0]["bundle_url"].endswith("/60446602.json.sn")
    certificate = x509.load_pem_x509_certificate((FIXTURE / "certificate.pem").read_bytes())
    assert certificate.public_bytes(Encoding.DER) == base64.b64decode(
        bundle["verificationMaterial"]["certificate"]["rawBytes"])
    claims = certificate_claims()
    assert claims["subjectAlternativeName"] == claims["buildSignerURI"] == IDENTITY
    assert claims["buildSignerDigest"] == REVIEWED_IMPLEMENTATION
    assert claims["sourceRepositoryDigest"] == claims["buildConfigDigest"] == CALLER
    assert claims["buildConfigURI"] == f"{ORIGIN}/{contract.WORKFLOW}@refs/heads/main"
    assert claims["runInvocationURI"] == f"{ORIGIN}/actions/runs/{RUN}/attempts/1"
    assert claims["issuer"] == ISSUER
    statement = json.loads(base64.b64decode(bundle["dsseEnvelope"]["payload"]))
    assert statement == {"_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": contract.SUBJECT, "digest": {"sha256": SUBJECT_DIGEST}}],
        "predicateType": contract.PREDICATE,
        "predicate": {"schema": contract.PREDICATE_SCHEMA, "preflight_sha256": SUBJECT_DIGEST}}
    run = json.loads((FIXTURE / "run.json").read_bytes())
    assert (run["id"], run["head_sha"], run["run_attempt"]) == (RUN, CALLER, 1)
    assert run["referenced_workflows"] == [{"path": f"{contract.REPOSITORY}/{contract.SIGNER}@{REVIEWED_IMPLEMENTATION}",
                                           "sha": REVIEWED_IMPLEMENTATION}]
    jobs = json.loads((FIXTURE / "jobs.json").read_bytes())["jobs"]
    assert jobs[0]["id"] == 122296352579
    assert [s["conclusion"] for s in jobs[0]["steps"] if s["number"] in {6, 7, 8, 9}] == [
        "success", "success", "failure", "skipped"]
    assert jobs[1]["name"] == "publisher" and jobs[1]["conclusion"] == "skipped"
    assert json.loads((FIXTURE / "artifacts.json").read_bytes()) == {"artifacts": []}


def test_genuine_hosted_certificate_matches_corrected_policy_model(monkeypatch):
    model = hosted_policy_model(monkeypatch)
    assert verify_model(model) == digest(model[0])


@pytest.mark.parametrize("field", ["subjectAlternativeName", "buildSignerURI", "both"])
@pytest.mark.parametrize("identity", [
    f"{ORIGIN}/{contract.SIGNER}@{revision}" for revision in (
        "0" * 40, "f" * 40, "d6601ad97815a85da164e4329766ea17b62bddc9",
        CALLER, "main", "refs/heads/main", "refs/heads/feature/correction", "refs/tags/v1")
] + [
    f"{ORIGIN}/{path}@{REVIEWED_IMPLEMENTATION}" for path in (
        contract.WORKFLOW, ".github/workflows/catalogue-verifier.yml",
        "other/connector-verifier.yml", contract.SIGNER + "/extra")
] + [f"https://github.com/other/atlas-connectors/{contract.SIGNER}@{REVIEWED_IMPLEMENTATION}",
     IDENTITY + "/extra", IDENTITY + "?ref=main", IDENTITY + "#fragment"])
def test_signer_identity_rejects_other_shas_paths_and_mutable_refs(monkeypatch, field, identity):
    model = hosted_policy_model(monkeypatch)
    certificate = model[3][0]["verificationResult"]["signature"]["certificate"]
    for key in (["subjectAlternativeName", "buildSignerURI"] if field == "both" else [field]):
        certificate[key] = identity
    with pytest.raises(ValueError, match="authorization_certificate"):
        verify_model(model)


@pytest.mark.parametrize("field", ["subjectAlternativeName", *EXTENSIONS])
@pytest.mark.parametrize("mutation", ["missing", "wrong"])
def test_every_hosted_certificate_constraint_remains_required(monkeypatch, field, mutation):
    model = hosted_policy_model(monkeypatch)
    certificate = model[3][0]["verificationResult"]["signature"]["certificate"]
    if mutation == "missing":
        certificate.pop(field)
    else:
        certificate[field] = "wrong"
    with pytest.raises(ValueError, match="authorization_certificate"):
        verify_model(model)


@pytest.mark.parametrize("case", ["subject_name", "subject_digest", "extra_subject", "predicate_type",
    "predicate_schema", "predicate_digest", "extra_predicate", "extra_statement",
    "no_transparency", "wrong_log", "wrong_witness", "too_many_witnesses"])
def test_hosted_policy_model_retains_statement_and_transparency_constraints(monkeypatch, case):
    model = hosted_policy_model(monkeypatch)
    verified = model[3][0]["verificationResult"]
    statement = verified["statement"]
    if case == "subject_name": statement["subject"][0]["name"] = "other.json"
    elif case == "subject_digest": statement["subject"][0]["digest"]["sha256"] = "0" * 64
    elif case == "extra_subject": statement["subject"].append(deepcopy(statement["subject"][0]))
    elif case == "predicate_type": statement["predicateType"] = "https://slsa.dev/provenance/v1"
    elif case == "predicate_schema": statement["predicate"]["schema"] = "other"
    elif case == "predicate_digest": statement["predicate"]["preflight_sha256"] = "0" * 64
    elif case == "extra_predicate": statement["predicate"]["extra"] = True
    elif case == "extra_statement": statement["extra"] = True
    elif case == "no_transparency": verified["verifiedTimestamps"] = []
    elif case == "wrong_log": verified["verifiedTimestamps"][0]["uri"] = "https://other.example"
    elif case == "wrong_witness": verified["verifiedTimestamps"][0]["type"] = "TimestampAuthority"
    else: verified["verifiedTimestamps"] *= 9
    with pytest.raises(ValueError):
        verify_model(model)


def test_signer_identity_uses_independent_trust_revision(monkeypatch):
    model = hosted_policy_model(monkeypatch)
    revision = "a" * 40
    model[2]["signer_revision"] = revision
    with pytest.raises(ValueError, match="authorization_certificate"):
        verify_model(model)
    certificate = model[3][0]["verificationResult"]["signature"]["certificate"]
    certificate.update(buildSignerDigest=revision,
        subjectAlternativeName=f"{ORIGIN}/{contract.SIGNER}@{revision}",
        buildSignerURI=f"{ORIGIN}/{contract.SIGNER}@{revision}")
    assert verify_model(model) == digest(model[0])


def test_pinned_cli_command_retains_every_constraint(monkeypatch):
    model = hosted_policy_model(monkeypatch)
    commands = []
    def run(command, directory):
        commands.append(command)
        assert (directory / "artifact").read_bytes() == model[0]
        assert (directory / "bundle.json").read_bytes() == SYNTHETIC_BUNDLE
        assert (directory / "roots.jsonl").read_bytes() == crypto.ConnectorSigstore().roots
        return canonical_json(model[3])
    monkeypatch.setattr(crypto, "bounded_run", run)
    verify_model(model)
    command = commands[0]
    assert command[1:3] == ["attestation", "verify"]
    assert Path(command[0]) == crypto.ConnectorSigstore().binary
    assert command[4:] == ["--bundle", str(Path(command[3]).parent / "bundle.json"),
        "--custom-trusted-root", str(Path(command[3]).parent / "roots.jsonl"),
        "--repo", contract.REPOSITORY, "--hostname", "github.com", "--signer-workflow",
        f"{contract.REPOSITORY}/{contract.SIGNER}", "--signer-digest", REVIEWED_IMPLEMENTATION,
        "--source-digest", CALLER, "--source-ref", "refs/heads/main", "--cert-oidc-issuer", ISSUER,
        "--deny-self-hosted-runners", "--predicate-type", contract.PREDICATE,
        "--digest-alg", "sha256", "--format", "json"]
