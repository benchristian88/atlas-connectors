# SPDX-License-Identifier: Apache-2.0
"""Release-specific package checks; no execution, credentials or publication."""
import io
import json
from datetime import datetime
from pathlib import Path
import re
import subprocess
import tarfile
import zlib

from atlas_connector_sdk import __version__ as SDK_VERSION
from atlas_connector_sdk.contracts import strict_json, version_in_range, version_key

import build_bundle
from build_catalogue import validate_entry
from publication_contract import MAX_BUNDLE_BYTES, REPOSITORY, digest, hexadecimal, require
from publication_verify import read_regular

MAX_ARCHIVE = 20 * 1024 * 1024
MAX_METADATA = 256 * 1024
MAX_FILE = 1024 * 1024
MAX_FILES = 201
RUNTIME_BASELINE = "1.2.0"


def filename(manifest):
    return f"{manifest['id']}-{manifest['version']}.tar.gz"


def metadata_files(manifest):
    """Identical serialization to the existing builder, without rebuilding JSON inputs."""
    name = filename(manifest)
    return {
        "manifest.json": (json.dumps(manifest, indent=2) + "\n").encode(),
        "index.json": (json.dumps({"schema_version": "1.0", "entries": [manifest]}, indent=2) + "\n").encode(),
        "SHA256SUMS": (manifest["distribution"]["bundle_digest"][7:] + "  " + name + "\n").encode(),
    }


def inspect_archive(raw):
    """Bound decompression BEFORE parsing; inspect plain USTAR without extracting."""
    require(type(raw) is bytes and 0 < len(raw) <= MAX_ARCHIVE, "release_archive_limit")
    try:
        decoder = zlib.decompressobj(31)
        decoded = decoder.decompress(raw, MAX_ARCHIVE + 1)
        require(len(decoded) <= MAX_ARCHIVE and decoder.eof and not decoder.unused_data
                and not decoder.unconsumed_tail, "release_decompression_limit")
        files, offset = {}, 0
        while offset < len(decoded):
            header = decoded[offset:offset + 512]
            if header == b"\0" * 512:
                require(len(decoded) - offset >= 1024 and not any(decoded[offset:]), "release_archive_trailer")
                return files
            require(len(files) < MAX_FILES and len(header) == 512
                    and header[257:265] == b"ustar\x0000", "release_archive_header")
            member = tarfile.TarInfo.frombuf(header, "utf-8", "strict")
            name = member.name
            require(re.fullmatch(r"[A-Za-z0-9._/-]+", name) is not None and str(Path(name)) == name
                    and not Path(name).is_absolute() and not {".", ".."}.intersection(Path(name).parts)
                    and not {"tests", "fixtures", "candidate", "releases", ".git", "__pycache__"}.intersection(Path(name).parts)
                    and not name.endswith((".pyc", ".pyo")), "release_archive_path")
            require(name not in files, "release_duplicate_member")
            require(member.type == tarfile.REGTYPE and member.mode == 0o644
                    and member.uid == member.gid == member.mtime == 0
                    and member.uname == member.gname == member.linkname == ""
                    and 0 < member.size <= MAX_FILE, "release_archive_member")
            start = offset + 512
            end = start + member.size
            offset = start + ((member.size + 511) // 512) * 512
            require(offset <= len(decoded) and not any(decoded[end:offset]), "release_archive_truncated")
            files[name] = decoded[start:end]
        require(False, "release_archive_trailer")
    except (zlib.error, tarfile.HeaderError, UnicodeError):
        require(False, "release_archive_invalid")


def validate_package(raw, manifest, tag):
    # Registry validation is structural, never authentication. Asset ID 1 is an
    # internal validation placeholder and is never emitted as provider evidence.
    validate_entry({"status": "active", "release_tag": tag, "release_asset_id": 1, "manifest": manifest})
    require(all(len(value) <= MAX_METADATA for value in metadata_files(manifest).values()), "release_metadata_limit")
    require(version_key(manifest["version"])[3] and "+" not in manifest["version"], "release_requires_stable_version")
    require(manifest["source_versions"]["qualification"] == "qualified"
            and bool(manifest["source_versions"]["qualified_versions"]), "release_requires_recorded_qualification")
    compatibility = manifest["compatibility"]
    require(compatibility["aip"] == ["1.0"] and version_in_range(SDK_VERSION, compatibility["sdk"])
            and compatibility["runtime"]["capability"] == "integration-runtime-v1"
            and version_in_range(RUNTIME_BASELINE, compatibility["runtime"]["baseline"]), "release_incompatible_baseline")
    require(manifest["distribution"]["bundle_digest"] == "sha256:" + digest(raw), "release_digest_mismatch")
    files = inspect_archive(raw)
    require({"LICENSE", "README.md", "docs/qualification.md", "manifest.json"} <= files.keys(), "release_required_files")
    require(strict_json(files["manifest.json"]) == {k: v for k, v in manifest.items() if k != "distribution"},
            "release_manifest_mismatch")
    for operation in manifest["implementation"]["entry_points"].values():
        require(operation + ".yml" in files, "release_entrypoint_missing")
    require(all(version.encode() in files["docs/qualification.md"]
                for version in manifest["source_versions"]["qualified_versions"]), "release_qualification_document")
    licensing = manifest["licensing"]
    require(licensing["sbom"]["format"] == "SPDX" and licensing["sbom"]["path"] in files
            and licensing["notices"] and all(name in files for name in licensing["notices"]), "release_licence_files")
    sbom = strict_json(files[licensing["sbom"]["path"]])
    require(isinstance(sbom, dict) and sbom.get("spdxVersion") == "SPDX-2.3"
            and sbom.get("dataLicense") == "CC0-1.0" and sbom.get("SPDXID") == "SPDXRef-DOCUMENT"
            and sbom.get("name") == f"atlas-{manifest['id']}-{manifest['version']}"
            and sbom.get("documentNamespace") == f"https://github.com/{REPOSITORY}/sbom/{manifest['id']}/{manifest['version']}",
            "release_sbom_identity")
    creation = sbom.get("creationInfo", {})
    require(isinstance(creation, dict) and isinstance(creation.get("creators"), list)
            and 1 <= len(creation["creators"]) <= 32
            and all(isinstance(value, str) and re.fullmatch(r"(?:Organization|Person|Tool): [^\r\n]{1,200}", value)
                    for value in creation["creators"])
            and isinstance(creation.get("created"), str)
            and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", creation["created"]),
            "release_sbom_creation")
    try:
        datetime.strptime(creation["created"], "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        require(False, "release_sbom_creation")
    packages = sbom.get("packages")
    require(isinstance(packages, list) and all(isinstance(p, dict) for p in packages)
            and len(packages) == 1 + len(manifest["implementation"]["dependencies"]), "release_sbom_packages")
    require(all(isinstance(p.get("SPDXID"), str) and re.fullmatch(r"SPDXRef-[A-Za-z0-9.-]+", p["SPDXID"])
                and p.get("filesAnalyzed") is False for p in packages), "release_sbom_package_fields")
    require(len({p.get("name") for p in packages}) == len(packages)
            and len({p.get("SPDXID") for p in packages}) == len(packages)
            and all(p["SPDXID"] != sbom["SPDXID"] for p in packages), "release_sbom_duplicates")
    by_name = {p.get("name"): p for p in packages}
    own = by_name.get("atlas-" + manifest["id"], {})
    require(own.get("versionInfo") == manifest["version"] and own.get("licenseDeclared") == licensing["licence"]
            and own.get("licenseConcluded") == licensing["licence"], "release_sbom_licence")
    expected_relationships = []
    for dependency in manifest["implementation"]["dependencies"]:
        package = by_name.get(dependency["name"], {})
        require(package.get("versionInfo") == dependency["version"]
                and package.get("checksums") == [{"algorithm": "SHA256", "checksumValue": dependency["digest"][7:]}]
                and dependency["licence"] in re.split(r"[ ()]+", package.get("licenseDeclared", "")), "release_sbom_dependency")
        expected_relationships.append({"spdxElementId": own["SPDXID"], "relationshipType": "DEPENDS_ON",
                                       "relatedSpdxElement": package["SPDXID"]})
    require(sbom.get("relationships") == expected_relationships, "release_sbom_relationships")
    return files


def clean_source(commit):
    require(hexadecimal(commit, 40), "release_source_commit")
    require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=build_bundle.ROOT, text=True).strip() == commit
            and not subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"],
                                            cwd=build_bundle.ROOT), "release_requires_clean_exact_source")


def candidate(directory, *, tag, commit, expected_digest, connector, version):
    """Compare bounded local candidate bytes against a separately checked source tree."""
    require(hexadecimal(commit, 40) and hexadecimal(expected_digest), "release_expected_identity")
    raw, manifest = build_bundle.build(connector, version=version)
    require(manifest["distribution"]["provenance"]["source_commit"] == commit, "release_source_mismatch")
    files = {filename(manifest): raw, **metadata_files(manifest)}
    require(directory.is_dir() and not directory.is_symlink()
            and {p.name for p in directory.iterdir()} in (files.keys(), {*files, "package.sigstore.json"}), "release_candidate_inventory")
    for name, expected in files.items():
        observed = read_regular(directory / name, MAX_ARCHIVE if name == filename(manifest) else MAX_METADATA)
        require(observed == expected, "release_candidate_bytes")
    require(digest(raw) == expected_digest, "release_expected_digest")
    validate_package(raw, manifest, tag)
    return files, manifest


def authenticated_bundle(files, manifest, bundle, verifier, *, tag, commit, run_id):
    require(type(run_id) is int and run_id > 0, "release_expected_run")
    evidence = verifier.verify(files[filename(manifest)], bundle, profile="package", name=filename(manifest), commit=commit, tag=tag)
    require(evidence.source_commit == commit and evidence.sha256 == digest(files[filename(manifest)])
            and evidence.invocation == f"https://github.com/{REPOSITORY}/actions/runs/{run_id}/attempts/1", "release_build_invocation")
    return evidence


def retain_bundle(directory, bundle_path, *, tag, commit, expected_digest, connector, version, run_id, verifier):
    files, manifest = candidate(directory, tag=tag, commit=commit, expected_digest=expected_digest,
                                connector=connector, version=version)
    bundle = read_regular(bundle_path, MAX_BUNDLE_BYTES)
    authenticated_bundle(files, manifest, bundle, verifier, tag=tag, commit=commit, run_id=run_id)
    target = directory / "package.sigstore.json"
    if target.exists() or target.is_symlink():
        require(read_regular(target, MAX_BUNDLE_BYTES) == bundle, "release_bundle_substitution")
    else:
        with target.open("xb") as stream:
            stream.write(bundle)
