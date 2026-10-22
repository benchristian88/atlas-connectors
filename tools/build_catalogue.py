# SPDX-License-Identifier: Apache-2.0
"""Prepare the official aggregate catalogue offline; never publish or run bundles."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

from atlas_connector_sdk.contracts import MAX_METADATA_BYTES, strict_json, validate_manifest

ROOT = Path(__file__).resolve().parents[1]
PUBLISHER = "atlas-official"
REPOSITORY = "benchristian88/atlas-connectors"
RELEASE_WORKFLOW = ".github/workflows/release.yml"
MAX_ENTRIES = 200
MAX_INTEGER = 2**53 - 1
MAX_CATALOGUE_BYTES = 4 * 1024 * 1024
ENTRY_FIELDS = {"status", "release_tag", "release_asset_id", "manifest"}
CATALOGUE_FIELDS = {
    "schema_version", "sequence", "generated_at", "publisher_id",
    "repository", "entries",
}


def positive_integer(value):
    # JSON Schema's integer type also accepts 1.0; identities must be literal
    # integers, never booleans or floats, and lossless in JSON consumers.
    return type(value) is int and 0 < value <= MAX_INTEGER


def check_json_values(value):
    if isinstance(value, dict):
        if any(type(key) is not str for key in value):
            raise ValueError("invalid_catalogue_json")
        for item in value.values():
            check_json_values(item)
    elif isinstance(value, list):
        for item in value:
            check_json_values(item)
    elif type(value) is int:
        if abs(value) > MAX_INTEGER:
            raise ValueError("invalid_catalogue_json")
    elif type(value) is float:
        if not math.isfinite(value):
            raise ValueError("invalid_catalogue_json")
    elif value is not None and type(value) not in {str, bool}:
        raise ValueError("invalid_catalogue_json")


def canonical_json(value):
    """Sorted UTF-8 JSON with fixed whitespace and no non-finite numbers."""
    try:
        check_json_values(value)
        return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                           allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise ValueError("invalid_catalogue_json") from None


def entry_size(entry):
    """Standalone registry representation, including envelope and final newline."""
    return len(canonical_json(entry))


def validate_entry(entry):
    """Strict catalogue envelope plus the canonical SDK's complete Manifest."""
    if not isinstance(entry, dict) or entry.keys() != ENTRY_FIELDS:
        raise ValueError("invalid_release_fields")
    if not isinstance(entry["status"], str) or entry["status"] not in {"active", "withdrawn"}:
        raise ValueError("invalid_release_status")
    if not positive_integer(entry["release_asset_id"]):
        raise ValueError("invalid_release_asset_id")
    if entry_size(entry) > MAX_METADATA_BYTES:
        raise ValueError("release_entry_too_large")
    manifest = entry["manifest"]
    if not isinstance(manifest, dict):
        raise ValueError("invalid_manifest")
    validate_manifest(manifest)
    connector, version = manifest["id"], manifest["version"]
    if re.fullmatch(r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*", connector) is None:
        raise ValueError("invalid_connector_id")
    distribution = manifest["distribution"]
    provenance = distribution["provenance"]
    if manifest["publisher"]["id"] != PUBLISHER or provenance["publisher_id"] != PUBLISHER:
        raise ValueError("invalid_official_publisher")
    if provenance.get("repository") != REPOSITORY:
        raise ValueError("invalid_official_repository")
    if provenance["method"] != "github-artifact-attestation-sigstore":
        raise ValueError("invalid_official_provenance")
    if provenance.get("workflow") != RELEASE_WORKFLOW:
        raise ValueError("invalid_release_workflow")
    if provenance.get("evidence_uri") != f"https://github.com/{REPOSITORY}/attestations":
        raise ValueError("invalid_attestation_uri")
    if re.fullmatch(r"[a-f0-9]{40}", provenance["source_commit"]) is None:
        raise ValueError("invalid_source_commit")
    if re.fullmatch(r"sha256:[a-f0-9]{64}", distribution["bundle_digest"]) is None:
        raise ValueError("invalid_bundle_digest")
    tag = f"{connector}-v{version}"
    if entry["release_tag"] != tag:
        raise ValueError("invalid_release_tag")
    expected_uri = (f"https://github.com/{REPOSITORY}/releases/download/"
                    f"{tag}/{connector}-{version}.tar.gz")
    if distribution["asset_uri"] != expected_uri:
        raise ValueError("invalid_release_asset_uri")
    return connector, version


def parse_timestamp(value):
    if (not isinstance(value, str)
            or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value) is None):
        raise ValueError("invalid_catalogue_timestamp")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise ValueError("invalid_catalogue_timestamp") from None


def validate_catalogue(document):
    """Validate the entire v1 contract, including sorted, unique identities."""
    if not isinstance(document, dict) or document.keys() != CATALOGUE_FIELDS:
        raise ValueError("invalid_catalogue_fields")
    if document["schema_version"] != "1.0":
        raise ValueError("invalid_catalogue_schema")
    if not positive_integer(document["sequence"]):
        raise ValueError("invalid_catalogue_sequence")
    if document["publisher_id"] != PUBLISHER:
        raise ValueError("invalid_official_publisher")
    if document["repository"] != REPOSITORY:
        raise ValueError("invalid_official_repository")
    parse_timestamp(document["generated_at"])
    entries = document["entries"]
    if not isinstance(entries, list) or len(entries) > MAX_ENTRIES:
        raise ValueError("invalid_catalogue_entry_count")
    identities, assets = [], set()
    for entry in entries:
        identities.append(validate_entry(entry))
        if entry["release_asset_id"] in assets:
            raise ValueError("duplicate_release_asset_id")
        assets.add(entry["release_asset_id"])
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate_connector_version")
    if identities != sorted(identities):
        raise ValueError("unsorted_catalogue_entries")
    # Also check JSON encodability for callers supplying Python values directly.
    if len(canonical_json(document)) > MAX_CATALOGUE_BYTES:
        raise ValueError("catalogue_too_large")
    return document


def load_registry(source):
    """Read only fixed local registry files, never current Connector source."""
    releases, sequence_path = source / "releases", source / "sequence.txt"
    if (source.is_symlink() or releases.is_symlink() or not releases.is_dir()
            or sequence_path.is_symlink() or not sequence_path.is_file()):
        raise ValueError("invalid_catalogue_source")
    with sequence_path.open("rb") as stream:
        sequence_raw = stream.read(32)
    if re.fullmatch(rb"[1-9][0-9]{0,15}\n?", sequence_raw) is None:
        raise ValueError("invalid_catalogue_sequence")
    sequence = int(sequence_raw)
    if not positive_integer(sequence):
        raise ValueError("invalid_catalogue_sequence")
    paths = sorted(releases.iterdir())
    if len(paths) > MAX_ENTRIES:
        raise ValueError("invalid_catalogue_entry_count")
    entries = []
    for path in paths:
        if path.is_symlink() or not path.is_file() or path.suffix != ".json":
            raise ValueError("invalid_release_file")
        with path.open("rb") as stream:
            raw = stream.read(MAX_METADATA_BYTES + 1)
        try:
            entry = strict_json(raw.decode("utf-8"))
        except UnicodeError:
            raise ValueError("invalid_release_json") from None
        connector, version = validate_entry(entry)
        if path.name != f"{connector}-{version}.json":
            raise ValueError("invalid_release_filename")
        entries.append(entry)
    return sequence, sorted(entries, key=lambda entry: (entry["manifest"]["id"], entry["manifest"]["version"]))


def commit_timestamp(source_root=None):
    """Fixed read-only Git command; no arguments come from catalogue data."""
    try:
        raw = subprocess.check_output(
            ["git", "show", "-s", "--format=%ct", "HEAD"], cwd=source_root or ROOT, text=True,
        ).strip()
        if re.fullmatch(r"[0-9]{1,12}", raw) is None:
            raise ValueError
        return datetime.fromtimestamp(int(raw), timezone.utc)
    except (OSError, subprocess.CalledProcessError, ValueError, OverflowError):
        raise ValueError("catalogue_commit_time_unavailable") from None


def build(output=None, *, source_root=None):
    sequence, entries = load_registry((source_root or ROOT) / "catalogue")
    generated = commit_timestamp(source_root) if source_root is not None else commit_timestamp()
    document = validate_catalogue({
        "schema_version": "1.0", "sequence": sequence,
        "generated_at": generated.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publisher_id": PUBLISHER, "repository": REPOSITORY, "entries": entries,
    })
    payload = canonical_json(document)
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
        (output / "catalogue.json").write_bytes(payload)
        (output / f"catalogue-{sequence:06d}.json").write_bytes(payload)
    return payload, document


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/catalogue")
    args = parser.parse_args()
    try:
        payload, document = build(output=args.output)
    except ValueError as error:
        parser.exit(1, f"catalogue_build_failed: {error}\n")
    except OSError:
        parser.exit(1, "catalogue_source_or_output_unavailable\n")
    print(f"sequence={document['sequence']} entries={len(document['entries'])} "
          f"sha256:{hashlib.sha256(payload).hexdigest()}")
