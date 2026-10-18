# SPDX-License-Identifier: Apache-2.0
"""Deterministic independent Connector bundle and detached catalogue descriptor."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

from atlas_connector_sdk.contracts import validate_manifest

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "benchristian88/atlas-connectors"
WORKFLOW = ".github/workflows/release.yml"
# Reviewed package contents. Operator runbooks, checkpoints, tests and incidental
# local files never enter either immutable package.
COMMON_FILES = (
    "NOTICE", "README.md", "docs/capability-matrix.md", "docs/discovery.md",
    "docs/i4b-completion-report.md", "docs/permissions.md", "docs/qualification.md",
    "library/atlas_probe.py", "manifest.json", "sbom.spdx.json", "test_connection.yml",
)
DISCOVERY_FILES = (
    "discover.yml", "library/atlas_discover.py", "library/atlas_readiness.py",
    "module_utils/atlas_discovery.py", "module_utils/atlas_normalization.py",
    "module_utils/atlas_transport.py",
    "module_utils/atlas_diagnostics.py",
)
# Preserve the historical qualification contract and pre-live documentation when
# rebuilding the candidate; production uses its promoted metadata and docs.
CANDIDATE_OVERRIDES = (
    "manifest.json", "sbom.spdx.json", "test_connection.yml", "README.md",
    "docs/capability-matrix.md", "docs/discovery.md", "docs/permissions.md",
    "docs/qualification.md", "docs/i4b-completion-report.md",
)


def build(connector="proxmox", output=None, *, candidate=False):
    if connector != "proxmox":
        raise ValueError("unknown_connector")
    source = ROOT / "connectors" / connector
    metadata = source / "candidate" if candidate else source
    manifest = json.loads((metadata / "manifest.json").read_bytes())
    names = COMMON_FILES + DISCOVERY_FILES
    files = {name: (source / name).read_bytes() for name in names}
    if candidate:
        for name in CANDIDATE_OVERRIDES:
            files[name] = (metadata / name).read_bytes()
    files["LICENSE"] = (ROOT / "LICENSE").read_bytes()
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name, raw in sorted(files.items()):
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(raw), 0o644, 0
            archive.addfile(info, io.BytesIO(raw))
    compressed = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode="wb", mtime=0, filename="") as target:
        target.write(stream.getvalue())
    payload = compressed.getvalue()
    digest = "sha256:" + hashlib.sha256(payload).hexdigest()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    combined = {**manifest, "distribution": {"bundle_digest": digest,
        "asset_uri": f"https://github.com/{REPOSITORY}/releases/download/proxmox-v{manifest['version']}/proxmox-{manifest['version']}.tar.gz",
        "provenance": {"method": "github-artifact-attestation-sigstore", "publisher_id": "atlas-official",
            "repository": REPOSITORY, "workflow": WORKFLOW, "source_commit": commit,
            "evidence_uri": f"https://github.com/{REPOSITORY}/attestations"}}}
    validate_manifest(combined)
    if output:
        output.mkdir(parents=True, exist_ok=True)
        filename = f"proxmox-{manifest['version']}.tar.gz"
        (output / filename).write_bytes(payload)
        (output / "manifest.json").write_text(json.dumps(combined, indent=2) + "\n")
        (output / "SHA256SUMS").write_text(digest[7:] + "  " + filename + "\n")
        (output / "index.json").write_text(json.dumps({"schema_version": "1.0", "entries": [combined]}, indent=2) + "\n")
    return payload, combined


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--candidate", action="store_true", help="Build unqualified I4B candidate; never publish or activate")
    args = parser.parse_args()
    output = args.output
    if output is None:
        if args.candidate:
            version = json.loads((ROOT / "connectors/proxmox/candidate/manifest.json").read_bytes())["version"]
            output = ROOT / "dist" / ("proxmox-candidate-" + version)
        else:
            output = ROOT / "dist/proxmox"
    payload, manifest = build(output=output, candidate=args.candidate)
    print(manifest["distribution"]["bundle_digest"])
