# SPDX-License-Identifier: Apache-2.0
"""Candidate durable evidence contract; no trust activation or publication CLI.

The existing verifiers authenticate every signature. Historical checks describe
publication-time evidence only, and never call live admission with a past clock.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import argparse
import re
import tempfile

from atlas_connector_sdk.contracts import strict_json
from authorization_sigstore import AuthorizationSigstore
from publication_authorization import (MAX_AUTHORIZATION_BYTES, MAX_REQUEST_BYTES,
    PREDICATE, WORKFLOW, check_authorization, check_request, check_trust, parse)
from publication_contract import (MAX_BUNDLE_BYTES, MAX_CATALOGUE_BYTES, PUBLICATION_WORKFLOW, REPOSITORY,
    canonical_json, digest, hexadecimal, require)
from publication_verify import ISSUER, ORIGIN, bounded_run, read_regular

ARCHIVE_LIMITS = {"preflight.json": MAX_AUTHORIZATION_BYTES,
                  "preflight.sigstore.json": MAX_BUNDLE_BYTES,
                  "policy.json": MAX_REQUEST_BYTES}
# Admission margin for the existing 20-second provider request timeout plus ten
# seconds of scheduling/clock headroom. This cannot make provider writes atomic.
FINALIZATION_RESERVE_SECONDS = 30


@dataclass(frozen=True)
class Archive:
    preflight: bytes
    bundle: bytes
    policy: bytes

    @classmethod
    def from_files(cls, files):
        # Accept pairs, not just a dict: duplicate names must survive to validation.
        rows = []
        for row in files:
            require(len(rows) < 3, "archive_inventory")
            rows.append(row)
        require(len(rows) == 3 and all(type(row) in {tuple, list} and len(row) == 2
                and type(row[0]) is str for row in rows), "archive_inventory")
        require({row[0] for row in rows} == set(ARCHIVE_LIMITS), "archive_inventory")
        values = dict(rows)
        for name, maximum in ARCHIVE_LIMITS.items():
            require(type(values[name]) is bytes and 0 < len(values[name]) <= maximum, "archive_size")
        return cls(values["preflight.json"], values["preflight.sigstore.json"], values["policy.json"])

    @classmethod
    def read(cls, directory):
        directory = Path(directory)
        require(not directory.is_symlink() and directory.is_dir(), "archive_directory")
        require({p.name for p in directory.iterdir()} == set(ARCHIVE_LIMITS), "archive_inventory")
        return cls.from_files((name, read_regular(directory / name, maximum))
                              for name, maximum in ARCHIVE_LIMITS.items())

    def files(self):
        return {"preflight.json": self.preflight, "preflight.sigstore.json": self.bundle,
                "policy.json": self.policy}

    def inventory(self):
        return {name: {"sha256": digest(raw), "size": len(raw)} for name, raw in self.files().items()}

    def write(self, directory):
        """Exclusive local preparation; never replace evidence after interruption."""
        archive = self.from_files(self.files().items())
        directory = Path(directory)
        directory.mkdir(mode=0o700)
        for name, raw in archive.files().items():
            with (directory / name).open("xb") as stream:
                stream.write(raw)
        require(self.read(directory) == archive, "archive_local_round_trip")


def timestamp(value):
    """Only timezone-qualified provider/verifier timestamps; never local time."""
    require(type(value) is str and re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})",
        value) is not None, "archive_timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        require(False, "archive_timestamp")


def verified_times(verifier, raw, bundle, *, expected=None, trust=None, profile=None, name=None, commit=None):
    """Extract times through a second real offline verification of identical bytes.

    Frozen S4's public return value omits verified times. Preserve that code and
    first run its full profile checks; this companion invocation uses the same
    pinned binary/roots and constraints. Never extract times from decoded DSSE.
    Callers must first authenticate using AuthorizationSigstore or Verifier.
    """
    require(type(raw) is bytes and type(bundle) is bytes and 0 < len(bundle) <= MAX_BUNDLE_BYTES,
            "archive_size")
    maximum = MAX_AUTHORIZATION_BYTES if expected is not None else 1024 if profile == "pointer" else MAX_CATALOGUE_BYTES
    require(0 < len(raw) <= maximum, "archive_size")
    if expected is not None:
        check_request(expected)
        check_trust(trust)
        workflow, predicate = WORKFLOW, PREDICATE
        commit, signer = expected["source_commit"], trust["signer_revision"]
        identity_flags = ["--signer-workflow", REPOSITORY + "/" + workflow]
    else:
        require(profile in {"pointer", "catalogue"} and hexadecimal(commit, 40), "archive_time_profile")
        workflow = PUBLICATION_WORKFLOW if profile == "pointer" else ".github/workflows/catalogue.yml"
        predicate, signer = "https://slsa.dev/provenance/v1", commit
        identity_flags = ["--cert-identity", f"{ORIGIN}/{workflow}@refs/heads/main"]
    with tempfile.TemporaryDirectory(prefix="atlas-archive-times-") as work:
        directory = Path(work)
        for filename, value in (("artifact", raw), ("bundle.json", bundle), ("roots.jsonl", verifier.roots)):
            (directory / filename).write_bytes(value)
        command = [str(verifier.binary), "attestation", "verify", str(directory / "artifact"),
            "--bundle", str(directory / "bundle.json"), "--custom-trusted-root", str(directory / "roots.jsonl"),
            "--repo", REPOSITORY, "--hostname", "github.com", *identity_flags,
            "--signer-digest", signer, "--source-digest", commit, "--source-ref", "refs/heads/main",
            "--cert-oidc-issuer", ISSUER, "--deny-self-hosted-runners", "--predicate-type", predicate,
            "--digest-alg", "sha256", "--format", "json"]
        output = strict_json(bounded_run(command, directory), maximum=1024 * 1024)
    require(isinstance(output, list) and len(output) == 1, "archive_time_result")
    try:
        result = output[0]["verificationResult"]
        subjects = result["statement"]["subject"]
        subject_name = "preflight.json" if expected is not None else name
        require(isinstance(subjects, list) and len(subjects) <= 32, "archive_time_subject")
        matches = [s for s in subjects if s.get("name") == subject_name]
        require(len(matches) == 1 and matches[0]["digest"] == {"sha256": digest(raw)}, "archive_time_subject")
        witnesses = result["verifiedTimestamps"]
        require(isinstance(witnesses, list) and 1 <= len(witnesses) <= 8
                and all(t["type"] == "Tlog" and t["uri"] in {
                    "https://rekor.sigstore.dev", "https://log2025-1.rekor.sigstore.dev"} for t in witnesses),
                "archive_time_witness")
        return tuple(timestamp(t["timestamp"]) for t in witnesses)
    except (KeyError, TypeError, AttributeError):
        require(False, "archive_time_result")


@dataclass(frozen=True)
class HistoricalLimits:
    # Deliberately no defaults or production instance. These candidate bounds
    # require an owner decision; they do not extend startup expiry.
    selection_seconds: int
    publication_seconds: int

    def __post_init__(self):
        require(all(type(v) is int and 1 <= v <= 1800 for v in
                    (self.selection_seconds, self.publication_seconds)), "archive_historical_limits")


class ArchiveVerifier:
    def __init__(self, trust, approved_policy_digests, limits=None):
        check_trust(trust)
        self.trust = parse(canonical_json(trust), MAX_REQUEST_BYTES)
        require(type(approved_policy_digests) is frozenset and 0 < len(approved_policy_digests) <= 16
                and all(hexadecimal(v) for v in approved_policy_digests), "archive_policy_approval_required")
        require(limits is None or type(limits) is HistoricalLimits, "archive_historical_limits")
        self.approved_policy_digests, self.limits = approved_policy_digests, limits

    def authenticate(self, archive, expected):
        archive = Archive.from_files(archive.files().items())
        check_request(expected)
        require(expected["acceptance_only"] is False, "archive_acceptance_only")
        require(digest(archive.policy) == expected["policy_sha256"]
                and digest(archive.policy) in self.approved_policy_digests, "archive_policy_digest")
        policy = strict_json(archive.policy, maximum=MAX_REQUEST_BYTES)
        value = parse(archive.preflight, MAX_AUTHORIZATION_BYTES)
        require(check_authorization(value, self.trust, policy) == expected, "archive_context")
        verifier = AuthorizationSigstore()
        require(verifier.verify(archive.preflight, archive.bundle, expected=expected, trust=self.trust)
                == digest(archive.preflight), "archive_signature_digest")
        times = verified_times(verifier, archive.preflight, archive.bundle, expected=expected, trust=self.trust)
        fresh = value["freshness"]
        issued = datetime.fromtimestamp(fresh["issued_at"], timezone.utc)
        expires = datetime.fromtimestamp(fresh["expires_at"], timezone.utc)
        started = datetime.fromtimestamp(fresh["observation_started"], timezone.utc)
        require(all(issued <= t < expires for t in times), "archive_preflight_time")
        # This is a signed observation, not an independently timestamped API read.
        for run in (value["security"]["run"], value["security"]["attempt"]):
            require(timestamp(run.get("created_at")) <= started, "archive_run_time")
        return value, times

    def bind_selection(self, archive, selection, selection_times, *, published_at=None):
        """Selection is the existing verifier's authenticated Evidence result."""
        require(type(self.limits) is HistoricalLimits, "archive_historical_limits")
        match = re.fullmatch(re.escape(ORIGIN) + r"/actions/runs/([1-9][0-9]*)/attempts/1", selection.invocation)
        require(match is not None and selection.profile == "pointer", "archive_selection_invocation")
        expected = {"source_commit": selection.source_commit, "policy_sha256": digest(archive.policy),
                    "run_id": int(match[1]), "run_attempt": 1, "operation": "publish", "acceptance_only": False}
        value, preflight_times = self.authenticate(archive, expected)
        require(isinstance(selection_times, tuple) and 1 <= len(selection_times) <= 8
                and all(isinstance(t, datetime) and t.tzinfo is not None for t in selection_times),
                "archive_selection_time")
        issued = datetime.fromtimestamp(value["freshness"]["issued_at"], timezone.utc)
        require(max(preflight_times) <= min(selection_times)
                and max(selection_times) <= issued + timedelta(seconds=self.limits.selection_seconds),
                "archive_selection_time")
        if published_at is not None:
            published = timestamp(published_at)
            require(max(selection_times) <= published <= max(selection_times)
                    + timedelta(seconds=self.limits.publication_seconds), "archive_publication_time")
        return {"result": "authenticated_publication_time_evidence",
                "archive": archive.inventory(), "source_commit": expected["source_commit"],
                "run_id": expected["run_id"], "run_attempt": 1,
                "selection_witnessed_at": max(selection_times).isoformat(),
                "current_authorization": False, "consumer_acceptance": False}

    def require_finalization_window(self, authenticated, *, now):
        """Deny a new immutable write unless its original window has headroom.

        The caller supplies this verifier's authenticated binding result, never a
        downloaded receipt. Check immediately before PATCH, after all slow reads
        and cryptography. Actual published_at must still be verified afterward.
        """
        require(type(self.limits) is HistoricalLimits and type(now) in {int, float},
                "archive_finalization_time")
        selected = timestamp(authenticated["selection_witnessed_at"])
        current = datetime.fromtimestamp(now, timezone.utc)
        require(selected <= current and current + timedelta(seconds=FINALIZATION_RESERVE_SECONDS)
                <= selected + timedelta(seconds=self.limits.publication_seconds),
                "archive_finalization_deadline")


def main():
    parser = argparse.ArgumentParser(description="Prepare original public archive bytes locally; no publication authority")
    parser.add_argument("--preflight-directory", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--trust", type=Path, required=True, help="Independently reviewed trust input, never from the archive")
    parser.add_argument("--policy-sha256", required=True, help="Independently reviewed exact policy digest")
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--operation", choices=("publish", "recover"), required=True)
    parser.add_argument("--output", type=Path, required=True, help="New local directory; existing directories fail closed")
    args = parser.parse_args()
    try:
        directory = args.preflight_directory
        require(not directory.is_symlink() and directory.is_dir()
                and {p.name for p in directory.iterdir()} == {"preflight.json", "preflight.sigstore.json"},
                "preflight_artifact_inventory")
        archive = Archive.from_files([
            ("preflight.json", read_regular(directory / "preflight.json", MAX_AUTHORIZATION_BYTES)),
            ("preflight.sigstore.json", read_regular(directory / "preflight.sigstore.json", MAX_BUNDLE_BYTES)),
            ("policy.json", read_regular(args.policy, MAX_REQUEST_BYTES))])
        trust = strict_json(read_regular(args.trust, MAX_REQUEST_BYTES))
        # Preparation only needs original preflight validity, not selection or
        # publication delay policy. No historical limits are selected by this CLI.
        verifier = ArchiveVerifier(trust, frozenset({args.policy_sha256}))
        verifier.authenticate(archive, {"source_commit": args.source_commit,
            "policy_sha256": args.policy_sha256, "run_id": args.run_id, "run_attempt": 1,
            "operation": args.operation, "acceptance_only": False})
        archive.write(args.output)
    except (ValueError, TypeError, KeyError, OSError, OverflowError):
        parser.exit(1, "publication_evidence_preparation_failed\n")
    print(canonical_json({"result": "prepared_local_archive_not_publication_authority",
                          "archive": archive.inventory()}).decode(), end="")


if __name__ == "__main__":
    main()
