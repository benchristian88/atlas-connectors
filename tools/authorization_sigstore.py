# SPDX-License-Identifier: Apache-2.0
"""Distinct, offline verifier authorization signer profile. No decoded-DSSE trust.

The reusable-workflow certificate profile below is deliberately exact. Genuine
live evidence is a production acceptance prerequisite, never a reason to relax it.
"""
from pathlib import Path
import tempfile

from atlas_connector_sdk.contracts import strict_json
from publication_authorization import (MAX_AUTHORIZATION_BYTES, PREDICATE, SUBJECT, WORKFLOW,
                                       check_request, check_trust)
from publication_contract import (MAX_BUNDLE_BYTES, OWNER_ID, PUBLICATION_WORKFLOW,
    REPOSITORY, REPOSITORY_ID, digest, require)
from publication_verify import ISSUER, ORIGIN, Verifier, bounded_run


class AuthorizationSigstore(Verifier):
    def verify(self, artifact, bundle, *, expected, trust):
        check_request(expected)
        check_trust(trust)
        require(type(artifact) is bytes and 0 < len(artifact) <= MAX_AUTHORIZATION_BYTES,
                "authorization_size")
        require(type(bundle) is bytes and 0 < len(bundle) <= MAX_BUNDLE_BYTES, "attestation_size")
        envelope = strict_json(bundle.decode("utf-8"), maximum=MAX_BUNDLE_BYTES)
        require(isinstance(envelope, dict)
                and envelope.get("mediaType") == "application/vnd.dev.sigstore.bundle.v0.3+json",
                "attestation_format")
        revision, commit = trust["signer_revision"], expected["source_commit"]
        identity = f"{ORIGIN}/{WORKFLOW}@{revision}"
        with tempfile.TemporaryDirectory(prefix="atlas-authorization-verify-") as work:
            directory = Path(work)
            for name, raw in (("artifact", artifact), ("bundle.json", bundle), ("roots.jsonl", self.roots)):
                (directory / name).write_bytes(raw)
            command = [str(self.binary), "attestation", "verify", str(directory / "artifact"),
                "--bundle", str(directory / "bundle.json"), "--custom-trusted-root", str(directory / "roots.jsonl"),
                "--repo", REPOSITORY, "--hostname", "github.com",
                "--signer-workflow", REPOSITORY + "/" + WORKFLOW, "--signer-digest", revision,
                "--source-digest", commit, "--source-ref", "refs/heads/main",
                "--cert-oidc-issuer", ISSUER, "--deny-self-hosted-runners",
                "--predicate-type", PREDICATE, "--digest-alg", "sha256", "--format", "json"]
            output = strict_json(bounded_run(command, directory), maximum=1024 * 1024)
        require(isinstance(output, list) and len(output) == 1, "verifier_result")
        try:
            verified = output[0]["verificationResult"]
            certificate = verified["signature"]["certificate"]
            invocation = f"{ORIGIN}/actions/runs/{expected['run_id']}/attempts/{expected['run_attempt']}"
            required = {"issuer": ISSUER, "subjectAlternativeName": identity,
                "buildSignerURI": identity, "buildSignerDigest": revision,
                "sourceRepositoryURI": ORIGIN, "sourceRepositoryIdentifier": str(REPOSITORY_ID),
                "sourceRepositoryOwnerIdentifier": str(OWNER_ID),
                "sourceRepositoryOwnerURI": "https://github.com/benchristian88",
                "sourceRepositoryDigest": commit, "sourceRepositoryRef": "refs/heads/main",
                "sourceRepositoryVisibilityAtSigning": "public", "runnerEnvironment": "github-hosted",
                "buildConfigURI": f"{ORIGIN}/{PUBLICATION_WORKFLOW}@refs/heads/main",
                "buildConfigDigest": commit, "buildTrigger": "workflow_dispatch", "runInvocationURI": invocation}
            require(all(certificate.get(key) == value for key, value in required.items()), "authorization_certificate")
            statement = verified["statement"]
            require(statement.keys() == {"_type", "subject", "predicateType", "predicate"}
                    and statement["_type"] == "https://in-toto.io/Statement/v1"
                    and statement["predicateType"] == PREDICATE
                    and statement["subject"] == [{"name": SUBJECT, "digest": {"sha256": digest(artifact)}}]
                    and statement["predicate"] == {"schema": "atlas-publication-decision/v1",
                                                   "authorization_sha256": digest(artifact)},
                    "authorization_attestation_statement")
            timestamps = verified["verifiedTimestamps"]
            require(isinstance(timestamps, list) and 1 <= len(timestamps) <= 8
                    and all(t["type"] == "Tlog" and t["uri"] in
                        {"https://rekor.sigstore.dev", "https://log2025-1.rekor.sigstore.dev"}
                        for t in timestamps), "attestation_witness")
        except (KeyError, TypeError, AttributeError):
            require(False, "authorization_verification_result")
        return digest(artifact)
