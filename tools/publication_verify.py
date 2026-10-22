# SPDX-License-Identifier: Apache-2.0
"""Publisher-owned offline gh/Sigstore verifier, compatible with B1.2 identities.

Public trust material is independently pinned data, not application code. Never
accept a decoded DSSE payload as verification. Only gh's verified output is read.
"""
from dataclasses import dataclass
import os
from pathlib import Path
import platform
import selectors
import signal
import subprocess
import tempfile
import time

from atlas_connector_sdk.contracts import strict_json
from publication_contract import (MAX_BUNDLE_BYTES, OWNER_ID, PUBLICATION_WORKFLOW,
                                  REPOSITORY, REPOSITORY_ID, digest, hexadecimal, require)

TRUST = Path(__file__).resolve().parent / "publication_trust"
ISSUER = "https://token.actions.githubusercontent.com"
PREDICATE = "https://slsa.dev/provenance/v1"
ORIGIN = "https://github.com/" + REPOSITORY
PROFILES = {"catalogue": ".github/workflows/catalogue.yml", "package": ".github/workflows/release.yml",
            "pointer": PUBLICATION_WORKFLOW}


def bounded_run(command, directory, maximum=1024 * 1024, seconds=30):
    """No ambient tokens, config, proxies or PATH; bounded combined output/time."""
    env = {"HOME": str(directory), "GH_CONFIG_DIR": str(directory), "PATH": "/nonexistent",
           "GH_PROMPT_DISABLED": "1", "GH_NO_UPDATE_NOTIFIER": "1", "GH_HOST": "github.com"}
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               cwd=directory, env=env, start_new_session=True)
    result, count, deadline = bytearray(), 0, time.monotonic() + seconds
    try:
        with selectors.DefaultSelector() as selector:
            for pipe in (process.stdout, process.stderr):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ)
            while selector.get_map():
                require(time.monotonic() < deadline, "verifier_timeout")
                for key, _ in selector.select(0.1):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                    else:
                        count += len(chunk)
                        require(count <= maximum, "verifier_output_limit")
                        if key.fileobj is process.stdout:
                            result.extend(chunk)
        try:
            process.wait(timeout=max(0.01, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            require(False, "verifier_timeout")
        require(process.returncode == 0, "attestation_verification_failed")
        return bytes(result)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        process.stdout.close()
        process.stderr.close()


def read_regular(path, maximum):
    import stat
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_size <= maximum, "unsafe_input_file")
        raw = stream.read(maximum + 1)
        require(len(raw) <= maximum, "input_size_limit")
        return raw


@dataclass(frozen=True)
class Evidence:
    profile: str
    sha256: str
    source_commit: str
    invocation: str


class Verifier:
    def __init__(self):
        lock = strict_json(read_regular(TRUST / "distribution.json", 16384))
        require(lock["version"] == "2.102.1", "verifier_version")
        machine = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "amd64"}.get(platform.machine())
        key = platform.system().lower() + "-" + str(machine)
        require(key in lock["platforms"], "verifier_platform")
        self.binary = TRUST / "bin/gh"
        self.roots = read_regular(TRUST / "trusted-root.jsonl", 128 * 1024)
        require(digest(self.roots) == lock["root_sha256"], "verifier_roots")
        require(digest(read_regular(self.binary, 64 * 1024 * 1024)) == lock["platforms"][key]["binary_sha256"],
                "verifier_binary")
        require(self.binary.stat().st_mode & 0o222 == 0, "verifier_permissions")

    def verify(self, artifact, bundle, *, profile, name, commit=None, tag=None):
        require(profile in PROFILES and type(artifact) is bytes and 0 < len(artifact) <= 20 * 1024 * 1024,
                "invalid_verification_context")
        require(commit is None or hexadecimal(commit, 40), "invalid_source_commit")
        require(type(bundle) is bytes and 0 < len(bundle) <= MAX_BUNDLE_BYTES, "attestation_size")
        value = strict_json(bundle, maximum=MAX_BUNDLE_BYTES)
        require(value.get("mediaType") == "application/vnd.dev.sigstore.bundle.v0.3+json", "attestation_format")
        ref = "refs/tags/" + tag if profile == "package" and tag else "refs/heads/main"
        require(profile != "package" or tag is not None, "missing_package_tag")
        workflow = PROFILES[profile]
        identity = f"{ORIGIN}/{workflow}@{ref}"
        with tempfile.TemporaryDirectory(prefix="atlas-publisher-verify-") as work:
            directory = Path(work)
            for filename, raw in (("artifact", artifact), ("bundle.json", bundle), ("roots.jsonl", self.roots)):
                (directory / filename).write_bytes(raw)
            command = [str(self.binary), "attestation", "verify", str(directory / "artifact"),
                       "--bundle", str(directory / "bundle.json"), "--custom-trusted-root", str(directory / "roots.jsonl"),
                       "--repo", REPOSITORY, "--hostname", "github.com", "--cert-identity", identity,
                       "--cert-oidc-issuer", ISSUER, "--source-ref", ref, "--deny-self-hosted-runners",
                       "--predicate-type", PREDICATE, "--digest-alg", "sha256", "--format", "json"]
            if commit is not None:
                command += ["--source-digest", commit, "--signer-digest", commit]
            output = strict_json(bounded_run(command, directory), maximum=1024 * 1024)
        require(isinstance(output, list) and len(output) == 1, "verifier_result")
        verified = output[0]["verificationResult"]
        certificate = verified["signature"]["certificate"]
        expected = {"issuer": ISSUER, "sourceRepositoryURI": ORIGIN,
                    "sourceRepositoryIdentifier": str(REPOSITORY_ID), "sourceRepositoryOwnerIdentifier": str(OWNER_ID),
                    "sourceRepositoryOwnerURI": "https://github.com/benchristian88",
                    "subjectAlternativeName": identity, "buildSignerURI": identity, "buildConfigURI": identity,
                    "sourceRepositoryRef": ref, "runnerEnvironment": "github-hosted"}
        require(all(certificate.get(k) == v for k, v in expected.items()), "attestation_identity")
        source = certificate["sourceRepositoryDigest"]
        require(hexadecimal(source, 40) and certificate["buildConfigDigest"] == source
                and certificate["buildSignerDigest"] == source and (commit is None or commit == source), "attestation_source")
        statement = verified["statement"]
        require(statement.get("_type") == "https://in-toto.io/Statement/v1"
                and statement.get("predicateType") == PREDICATE, "attestation_predicate")
        subjects = statement["subject"]
        require(isinstance(subjects, list) and 1 <= len(subjects) <= 32, "attestation_subjects")
        matches = [s for s in subjects if s.get("name") == name]
        require(len(matches) == 1 and matches[0]["digest"] == {"sha256": digest(artifact)}, "attestation_subject")
        predicate = statement["predicate"]
        definition = predicate["buildDefinition"]
        require(definition["buildType"] == "https://actions.github.io/buildtypes/workflow/v1"
                and definition["externalParameters"]["workflow"] == {"path": workflow, "ref": ref, "repository": ORIGIN}
                and definition["resolvedDependencies"] == [{"uri": f"git+{ORIGIN}@{ref}", "digest": {"gitCommit": source}}],
                "attestation_build_definition")
        invocation = certificate["runInvocationURI"]
        import re
        require(re.fullmatch(re.escape(ORIGIN) + r"/actions/runs/[1-9][0-9]{0,19}/attempts/[1-9][0-9]{0,7}", invocation)
                and predicate["runDetails"]["builder"]["id"] == identity
                and predicate["runDetails"]["metadata"]["invocationId"] == invocation, "attestation_invocation")
        timestamps = verified["verifiedTimestamps"]
        require(1 <= len(timestamps) <= 8 and all(t["type"] == "Tlog" and t["uri"] in
                {"https://rekor.sigstore.dev", "https://log2025-1.rekor.sigstore.dev"} for t in timestamps), "attestation_witness")
        return Evidence(profile, digest(artifact), source, invocation)
