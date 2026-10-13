# SPDX-License-Identifier: Apache-2.0
"""Independent checkpoint inspection; no install, credentials or source calls."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

from atlas_connector_sdk.contracts import validate_manifest

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FILES = {
    "LICENSE", "NOTICE", "README.md", "discover.yml", "test_connection.yml", "manifest.json", "sbom.spdx.json",
    "docs/capability-matrix.md", "docs/discovery.md", "docs/i4b-completion-report.md",
    "docs/permissions.md", "docs/qualification.md", "library/atlas_probe.py", "library/atlas_readiness.py",
    "library/atlas_discover.py", "module_utils/atlas_discovery.py", "module_utils/atlas_normalization.py",
    "module_utils/atlas_transport.py",
}
COLLECTION_DIGEST = "77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6"


def verify(directory, expected_digest, *, source_commit=None):
    manifest = json.loads((directory / "manifest.json").read_bytes())
    validate_manifest(manifest)
    if manifest["id"] != "proxmox" or manifest["version"] != "0.2.0-i4b.2":
        raise ValueError("candidate_identity_mismatch")
    archive_path = directory / "proxmox-0.2.0-i4b.2.tar.gz"
    if archive_path.stat().st_size > 20 * 1024 * 1024:
        raise ValueError("candidate_archive_limit")
    actual = "sha256:" + hashlib.sha256(archive_path.read_bytes()).hexdigest()
    if actual != expected_digest or manifest["distribution"]["bundle_digest"] != expected_digest:
        raise ValueError("candidate_digest_mismatch")
    if (directory / "SHA256SUMS").read_text() != actual[7:] + "  " + archive_path.name + "\n":
        raise ValueError("candidate_checksum_mismatch")
    with tarfile.open(archive_path) as archive:
        members = archive.getmembers()
        if len(members) != len(EXPECTED_FILES) or {m.name for m in members} != EXPECTED_FILES:
            raise ValueError("candidate_unreviewed_contents")
        for member in members:
            if (not member.isfile() or member.size > 10 * 1024 * 1024 or member.mode != 0o644
                    or member.mtime != 0 or member.uid != 0 or member.gid != 0):
                raise ValueError("candidate_noncanonical_member")
            if member.name == "LICENSE":
                path = ROOT / "LICENSE"
            elif member.name in {"manifest.json", "sbom.spdx.json", "test_connection.yml"}:
                path = ROOT / "connectors/proxmox/candidate" / member.name
            else:
                path = ROOT / "connectors/proxmox" / member.name
            raw = archive.extractfile(member).read()
            if raw != path.read_bytes():
                raise ValueError("candidate_source_mismatch")
            if member.name == "manifest.json" and json.loads(raw) != {k: v for k, v in manifest.items() if k != "distribution"}:
                raise ValueError("candidate_manifest_mismatch")
            if member.name == "sbom.spdx.json":
                sbom = json.loads(raw)
    if (manifest["source_versions"]["qualification"] != "unqualified"
            or manifest["source_versions"]["qualified_versions"]
            or manifest["compatibility"]["aip"] != ["1.0"]
            or manifest["compatibility"]["sdk"] != {"minimum": "1.1.0", "exclusive_maximum": "2.0.0"}
            or manifest["compatibility"]["runtime"]["baseline"] != {"minimum": "1.2.0", "exclusive_maximum": "2.0.0"}
            or manifest["implementation"]["dependencies"] != [{"kind": "collection", "name": "community.proxmox",
                "version": "2.0.0", "digest": "sha256:" + COLLECTION_DIGEST, "licence": "GPL-3.0-or-later"}]
            or sbom["packages"][0]["versionInfo"] != "0.2.0-i4b.2"
            or sbom["packages"][1]["versionInfo"] != "2.0.0"
            or sbom["packages"][1]["checksums"] != [{"algorithm": "SHA256", "checksumValue": COLLECTION_DIGEST}]):
        raise ValueError("candidate_contract_mismatch")
    if source_commit:
        if (subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip()
                or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() != source_commit
                or manifest["distribution"]["provenance"]["source_commit"] != source_commit):
            raise ValueError("candidate_requires_clean_exact_commit")
    return {"candidate_version": manifest["version"], "bundle_digest": actual,
            "source_qualification": "unqualified", "files": len(members),
            "source_commit": manifest["distribution"]["provenance"]["source_commit"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--expected-digest", required=True)
    parser.add_argument("--source-commit", help="Require a clean checkout at this exact committed revision")
    args = parser.parse_args()
    print(json.dumps(verify(args.directory, args.expected_digest, source_commit=args.source_commit), sort_keys=True))
