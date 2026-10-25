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

from atlas_connector_sdk.contracts import strict_json, validate_manifest, version_key

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "benchristian88/atlas-connectors"
WORKFLOW = ".github/workflows/release.yml"


def recipe(connector):
    """Explicit reviewed package paths; no discovery of incidental source files."""
    import re
    if not isinstance(connector, str) or re.fullmatch(r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*", connector) is None:
        raise ValueError("unknown_connector")
    source = ROOT / "connectors" / connector
    if source.is_symlink() or not source.is_dir():
        raise ValueError("unknown_connector")
    value = strict_json(source_bytes(source, "package.json"))
    if (value.keys() not in ({"schema_version", "files", "candidate_overrides"},
                            {"schema_version", "files", "candidate_overrides", "release_overrides"})
            or value["schema_version"] != "1.0"):
        raise ValueError("invalid_package_recipe")
    releases = value.get("release_overrides", {})
    if not isinstance(releases, dict) or len(releases) > 100:
        raise ValueError("invalid_release_overrides")
    base = strict_json(source_bytes(source, "manifest.json"))
    for version in releases:
        if (not version_key(version)[3] or version == base["version"]
                or "+" in version or version_key(version) <= version_key(base["version"])):
            raise ValueError("invalid_release_version")
    for paths in (value["files"], value["candidate_overrides"], *releases.values()):
        if (not isinstance(paths, list) or len(paths) > 200 or any(not isinstance(p, str) for p in paths)
                or paths != sorted(set(paths))):
            raise ValueError("invalid_package_paths")
        for name in paths:
            path = Path(name)
            if (re.fullmatch(r"[A-Za-z0-9._/-]+", name) is None or path.is_absolute() or ".." in path.parts or "\\" in name
                    or str(path) != name or not path.parts or path.parts[0] in {"candidate", "releases", ".git", "tests", "fixtures"}
                    or name in {"LICENSE", "package.json"}):
                raise ValueError("invalid_package_path")
    if (not {"NOTICE", "README.md", "manifest.json", "sbom.spdx.json", "test_connection.yml",
             "docs/qualification.md"} <= set(value["files"])
            or not set(value["candidate_overrides"]) <= set(value["files"])):
        raise ValueError("missing_package_contract")
    for paths in releases.values():
        if (not {"manifest.json", "sbom.spdx.json", "README.md", "docs/qualification.md"} <= set(paths)
                or not set(paths) <= set(value["files"])):
            raise ValueError("invalid_release_overrides")
    return source, value


def source_bytes(source, name):
    path = source / name
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError("unsafe_package_file")
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("package_file_limit")
    return path.read_bytes()


def build(connector="proxmox", output=None, *, candidate=False, version=None):
    source, package = recipe(connector)
    if candidate and version is not None:
        raise ValueError("conflicting_package_selection")
    metadata = source / "candidate" if candidate else source
    if version is not None:
        if version not in package.get("release_overrides", {}):
            raise ValueError("unknown_release_version")
        metadata = source / "releases" / version
    manifest = strict_json(source_bytes(metadata, "manifest.json"))
    if manifest["id"] != connector or version is not None and manifest["version"] != version:
        raise ValueError("package_manifest_identity")
    names = package["files"]
    files = {name: source_bytes(source, name) for name in names}
    if candidate:
        for name in package["candidate_overrides"]:
            files[name] = source_bytes(metadata, name)
    if version is not None:
        for name in package["release_overrides"][version]:
            files[name] = source_bytes(metadata, name)
    files["LICENSE"] = source_bytes(ROOT, "LICENSE")
    if sum(map(len, files.values())) > 20 * 1024 * 1024:
        raise ValueError("package_total_limit")
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
    if len(payload) > 20 * 1024 * 1024:
        raise ValueError("package_archive_limit")
    digest = "sha256:" + hashlib.sha256(payload).hexdigest()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    combined = {**manifest, "distribution": {"bundle_digest": digest,
        "asset_uri": f"https://github.com/{REPOSITORY}/releases/download/{connector}-v{manifest['version']}/{connector}-{manifest['version']}.tar.gz",
        "provenance": {"method": "github-artifact-attestation-sigstore", "publisher_id": "atlas-official",
            "repository": REPOSITORY, "workflow": WORKFLOW, "source_commit": commit,
            "evidence_uri": f"https://github.com/{REPOSITORY}/attestations"}}}
    validate_manifest(combined)
    if output:
        output.mkdir(parents=True, exist_ok=True)
        filename = f"{connector}-{manifest['version']}.tar.gz"
        (output / filename).write_bytes(payload)
        (output / "manifest.json").write_text(json.dumps(combined, indent=2) + "\n")
        (output / "SHA256SUMS").write_text(digest[7:] + "  " + filename + "\n")
        (output / "index.json").write_text(json.dumps({"schema_version": "1.0", "entries": [combined]}, indent=2) + "\n")
    return payload, combined


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--connector", default="proxmox")
    parser.add_argument("--version", help="Explicit reviewed release metadata overlay; default preserves the base package")
    parser.add_argument("--candidate", action="store_true", help="Build unqualified I4B candidate; never publish or activate")
    args = parser.parse_args()
    recipe(args.connector)
    output = args.output
    if output is None:
        if args.candidate:
            version = json.loads((ROOT / "connectors" / args.connector / "candidate/manifest.json").read_bytes())["version"]
            output = ROOT / "dist" / (args.connector + "-candidate-" + version)
        else:
            output = ROOT / "dist" / (args.connector + "-" + args.version if args.version else args.connector)
    payload, manifest = build(connector=args.connector, output=output, candidate=args.candidate, version=args.version)
    print(manifest["distribution"]["bundle_digest"])
