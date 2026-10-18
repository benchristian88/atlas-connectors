# SPDX-License-Identifier: Apache-2.0
"""Offline catalogue contract tests, independent of mutable Connector source."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import urllib.request

import pytest
from atlas_connector_sdk.contracts import strict_json, validate_manifest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_catalogue as catalogue

COMMIT = "456a5bfdd1398c19da9ffef29216029027e24278"
DIGEST = "sha256:a14fec5ab485c980688ff5907e8835ddd3e9cecd1a6989ef252cbcb1b1dc4ef8"
GENERATED = datetime(2026, 10, 18, 6, 45, 1, tzinfo=timezone.utc)


@pytest.fixture
def entry():
    return strict_json((ROOT / "catalogue/releases/proxmox-0.2.0.json").read_bytes())


@pytest.fixture
def fixed_commit(monkeypatch):
    monkeypatch.setattr(catalogue, "commit_timestamp", lambda: GENERATED)


@pytest.fixture
def document(fixed_commit):
    return catalogue.build()[1]


def release(entry, version, asset_id):
    result = deepcopy(entry)
    result["manifest"]["version"] = version
    result["release_asset_id"] = asset_id
    result["release_tag"] = f"proxmox-v{version}"
    result["manifest"]["distribution"]["asset_uri"] = (
        "https://github.com/benchristian88/atlas-connectors/releases/download/"
        f"proxmox-v{version}/proxmox-{version}.tar.gz"
    )
    return result


def write_registry(root, entries, sequence="1\n"):
    source = root / "catalogue"
    (source / "releases").mkdir(parents=True)
    (source / "sequence.txt").write_text(sequence, encoding="ascii")
    for entry in entries:
        path = source / "releases" / f"{entry['manifest']['id']}-{entry['manifest']['version']}.json"
        path.write_bytes(catalogue.canonical_json(entry))
    return source


def change(value, path, replacement):
    for name in path[:-1]:
        value = value[name]
    value[path[-1]] = replacement


def test_exact_proxmox_production_identity_and_complete_frozen_manifest(entry):
    assert entry["status"] == "active"
    assert entry["release_tag"] == "proxmox-v0.2.0"
    assert entry["release_asset_id"] == 652745908
    manifest = entry["manifest"]
    validate_manifest(manifest)
    assert (manifest["id"], manifest["version"]) == ("proxmox", "0.2.0")
    assert manifest["publisher"] == {"id": "atlas-official", "name": "Atlas Impact"}
    assert manifest["distribution"] == {
        "bundle_digest": DIGEST,
        "asset_uri": "https://github.com/benchristian88/atlas-connectors/releases/download/"
                     "proxmox-v0.2.0/proxmox-0.2.0.tar.gz",
        "provenance": {
            "method": "github-artifact-attestation-sigstore",
            "publisher_id": "atlas-official", "repository": "benchristian88/atlas-connectors",
            "workflow": ".github/workflows/release.yml", "source_commit": COMMIT,
            "evidence_uri": "https://github.com/benchristian88/atlas-connectors/attestations",
        },
    }
    # Pin every field of the released combined Manifest, without reading HEAD's
    # Connector source or depending on historical commits in a shallow checkout.
    frozen = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    assert hashlib.sha256(frozen).hexdigest() == "bfe5664094ffb88a774872603be4b0ba3697d93059b0c17a74773dc2d3b0fe8e"


def test_deterministic_bytes_identical_alias_and_snapshot(tmp_path, fixed_commit, monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1")
    first, document = catalogue.build(output=tmp_path)
    second, again = catalogue.build(output=tmp_path)
    assert first == second and document == again
    assert sorted(path.name for path in tmp_path.iterdir()) == ["catalogue-000001.json", "catalogue.json"]
    assert (tmp_path / "catalogue.json").read_bytes() == (tmp_path / "catalogue-000001.json").read_bytes() == first
    assert strict_json(first, maximum=catalogue.MAX_CATALOGUE_BYTES) == document
    assert first == (json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False,
                                allow_nan=False) + "\n").encode("utf-8")


def test_commit_timestamp_uses_only_fixed_git_arguments(monkeypatch):
    calls = []
    def output(args, **kwargs):
        calls.append((args, kwargs))
        return "1792305901\n"
    monkeypatch.setattr(catalogue.subprocess, "check_output", output)
    assert catalogue.commit_timestamp() == GENERATED
    assert calls == [(["git", "show", "-s", "--format=%ct", "HEAD"], {"cwd": ROOT, "text": True})]


@pytest.mark.parametrize("value", ["", "NaN", "123.0", "-1", "9999999999999999999999", "1\n2"])
def test_invalid_git_timestamp_fails_closed(monkeypatch, value):
    monkeypatch.setattr(catalogue.subprocess, "check_output", lambda *a, **k: value)
    with pytest.raises(ValueError, match="catalogue_commit_time_unavailable"):
        catalogue.commit_timestamp()


def test_git_failure_fails_closed(monkeypatch):
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, ["git"])
    monkeypatch.setattr(catalogue.subprocess, "check_output", fail)
    with pytest.raises(ValueError, match="catalogue_commit_time_unavailable"):
        catalogue.commit_timestamp()


def test_times_are_utc_seconds_and_exactly_seven_days(document):
    assert document["generated_at"] == "2026-10-18T06:45:01Z"
    assert document["expires_at"] == "2026-10-25T06:45:01Z"
    assert catalogue.parse_timestamp(document["expires_at"]) - GENERATED == timedelta(days=7)


def test_build_uses_only_historical_registry_not_current_connector_source(tmp_path, monkeypatch, fixed_commit):
    shutil.copytree(ROOT / "catalogue", tmp_path / "catalogue")
    monkeypatch.setattr(catalogue, "ROOT", tmp_path)
    assert not (tmp_path / "connectors").exists()
    _, document = catalogue.build()
    assert document["entries"][0]["manifest"]["distribution"]["bundle_digest"] == DIGEST
    assert document["entries"][0]["manifest"]["distribution"]["provenance"]["source_commit"] == COMMIT


def test_registry_entries_are_sorted_independently_of_file_creation_order(tmp_path, entry, monkeypatch, fixed_commit):
    entries = [release(entry, "0.3.0", 3), release(entry, "0.1.0", 1), release(entry, "0.2.0", 2)]
    write_registry(tmp_path, entries, sequence="12\n")
    monkeypatch.setattr(catalogue, "ROOT", tmp_path)
    first, document = catalogue.build(output=tmp_path / "output")
    assert [row["manifest"]["version"] for row in document["entries"]] == ["0.1.0", "0.2.0", "0.3.0"]
    assert document["sequence"] == 12
    assert (tmp_path / "output/catalogue-000012.json").read_bytes() == first


def test_sdk_validation_is_required_for_each_entry(tmp_path, entry, monkeypatch, fixed_commit):
    calls = []
    real_validate = catalogue.validate_manifest
    def validate(manifest):
        calls.append(manifest["version"])
        return real_validate(manifest)
    write_registry(tmp_path, [entry, release(entry, "0.3.0", 123)])
    monkeypatch.setattr(catalogue, "ROOT", tmp_path)
    monkeypatch.setattr(catalogue, "validate_manifest", validate)
    catalogue.build()
    assert set(calls) == {"0.2.0", "0.3.0"}


@pytest.mark.parametrize("path,replacement", [
    (("manifest_version",), "9.9"),
    (("compatibility", "sdk", "minimum"), "2.0.0"),
    (("compatibility", "aip"), []),
    (("implementation", "entry_points", "discover"), "../execute"),
    (("discovery_scopes", 0, "object_classes"), ["missing.class"]),
    (("facts", 0, "object_classes"), ["missing.class"]),
    (("capabilities", "test_connection"), "yes"),
])
def test_invalid_sdk_contract_is_rejected(entry, path, replacement):
    change(entry["manifest"], path, replacement)
    with pytest.raises(ValueError):
        catalogue.validate_entry(entry)


def test_other_publisher_rejected_even_when_sdk_publisher_fields_agree(entry):
    entry["manifest"]["publisher"]["id"] = "other-publisher"
    entry["manifest"]["distribution"]["provenance"]["publisher_id"] = "other-publisher"
    validate_manifest(entry["manifest"])
    with pytest.raises(ValueError, match="invalid_official_publisher"):
        catalogue.validate_entry(entry)


@pytest.mark.parametrize("field,value", [
    ("publisher_id", "other-publisher"),
    ("repository", "other/atlas-connectors"),
    ("repository", "benchristian88/other"),
    ("method", "approved-publisher-signature"),
    ("method", "unknown"),
    ("workflow", ".github/workflows/catalogue.yml"),
    ("evidence_uri", "https://example.test/attestations"),
])
def test_official_provenance_policy(entry, field, value):
    entry["manifest"]["distribution"]["provenance"][field] = value
    with pytest.raises(ValueError):
        catalogue.validate_entry(entry)


def test_sdk_valid_alternative_provenance_method_is_not_official_policy(entry):
    provenance = entry["manifest"]["distribution"]["provenance"]
    provenance.update(method="approved-publisher-signature", signature_format="fixture-format")
    validate_manifest(entry["manifest"])
    with pytest.raises(ValueError, match="invalid_official_provenance"):
        catalogue.validate_entry(entry)


@pytest.mark.parametrize("value", ["", "a" * 39, "a" * 41, "A" * 40, "g" * 40, "a" * 40 + "\n", None, 123])
def test_source_commit_is_exact_lowercase_sha1(entry, value):
    entry["manifest"]["distribution"]["provenance"]["source_commit"] = value
    with pytest.raises(ValueError):
        catalogue.validate_entry(entry)


@pytest.mark.parametrize("value", ["", "sha512:" + "a" * 64, "sha256:" + "A" * 64,
                                   "sha256:" + "a" * 63, DIGEST + "\n"])
def test_bundle_digest_is_exact_sha256(entry, value):
    entry["manifest"]["distribution"]["bundle_digest"] = value
    with pytest.raises(ValueError):
        catalogue.validate_entry(entry)


@pytest.mark.parametrize("value", ["proxmox-v0.2.1", "other-v0.2.0", "v0.2.0", "proxmox-v0.2.0\n", 123])
def test_release_tag_must_match_connector_version(entry, value):
    entry["release_tag"] = value
    with pytest.raises(ValueError, match="invalid_release_tag"):
        catalogue.validate_entry(entry)


@pytest.mark.parametrize("uri", [
    "https://github.com/other/atlas-connectors/releases/download/proxmox-v0.2.0/proxmox-0.2.0.tar.gz",
    "https://github.com/benchristian88/atlas-connectors/releases/download/proxmox-v0.2.1/proxmox-0.2.0.tar.gz",
    "https://github.com/benchristian88/atlas-connectors/releases/download/proxmox-v0.2.0/proxmox-0.2.1.tar.gz",
    "https://github.com/benchristian88/atlas-connectors/releases/download/proxmox-v0.2.0/other-0.2.0.tar.gz",
    "https://github.com/benchristian88/atlas-connectors/releases/latest/download/proxmox-0.2.0.tar.gz",
    "https://api.github.com/repos/benchristian88/atlas-connectors/releases/assets/652745908",
    "https://github.com/benchristian88/atlas-connectors/releases/download/proxmox-v0.2.0/proxmox-0.2.0.tar.gz?download=1",
    "file:///tmp/proxmox-0.2.0.tar.gz",
])
def test_immutable_asset_uri_and_filename_must_match(entry, uri):
    entry["manifest"]["distribution"]["asset_uri"] = uri
    with pytest.raises(ValueError):
        catalogue.validate_entry(entry)


@pytest.mark.parametrize("field,value", [
    ("id", ""), ("id", "../proxmox"), ("id", "proxmox\n"), ("id", True),
    ("version", ""), ("version", "latest"), ("version", "01.2.0"), ("version", "0.2.0/other"),
])
def test_invalid_connector_version_identity(entry, field, value):
    entry["manifest"][field] = value
    with pytest.raises(ValueError):
        catalogue.validate_entry(entry)


def test_duplicate_connector_version_is_rejected(document):
    duplicate = deepcopy(document["entries"][0])
    duplicate["release_asset_id"] += 1
    document["entries"].append(duplicate)
    with pytest.raises(ValueError, match="duplicate_connector_version"):
        catalogue.validate_catalogue(document)


def test_duplicate_release_asset_is_rejected(document):
    entry = document["entries"][0]
    document["entries"].append(release(entry, "0.3.0", entry["release_asset_id"]))
    with pytest.raises(ValueError, match="duplicate_release_asset_id"):
        catalogue.validate_catalogue(document)


def test_duplicate_registry_asset_fails_before_artifact_creation(tmp_path, entry, monkeypatch, fixed_commit):
    write_registry(tmp_path, [entry, release(entry, "0.3.0", entry["release_asset_id"])])
    monkeypatch.setattr(catalogue, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="duplicate_release_asset_id"):
        catalogue.build(output=tmp_path / "output")
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("value", [0, -1, True, False, 652745908.0, "652745908", None, [], 2**53])
def test_release_asset_id_must_be_positive_literal_integer(entry, value):
    entry["release_asset_id"] = value
    with pytest.raises(ValueError, match="invalid_release_asset_id"):
        catalogue.validate_entry(entry)


@pytest.mark.parametrize("value", [0, -1, True, False, 1.0, "1", None, [], 2**53])
def test_invalid_document_sequence(document, value):
    document["sequence"] = value
    with pytest.raises(ValueError, match="invalid_catalogue_sequence"):
        catalogue.validate_catalogue(document)


@pytest.mark.parametrize("value", ["", "0\n", "-1\n", "1.0\n", "01\n", "+1\n", "true\n", " 1\n",
                                   "1\n2\n", "1\n\n", "１\n", "9007199254740992\n", "1" * 100])
def test_invalid_source_sequence(tmp_path, value):
    source = write_registry(tmp_path, [])
    (source / "sequence.txt").write_text(value, encoding="utf-8")
    with pytest.raises(ValueError, match="invalid_catalogue_sequence"):
        catalogue.load_registry(source)


@pytest.mark.parametrize("value", ["unknown", "revoked", "", None, True, [], {}])
def test_unsupported_status(entry, value):
    entry["status"] = value
    with pytest.raises(ValueError, match="invalid_release_status"):
        catalogue.validate_entry(entry)


def test_explicit_withdrawal_retains_entire_release(tmp_path, entry, monkeypatch, fixed_commit):
    entry["status"] = "withdrawn"
    write_registry(tmp_path, [entry], sequence="2\n")
    monkeypatch.setattr(catalogue, "ROOT", tmp_path)
    _, document = catalogue.build()
    assert document["entries"] == [entry]
    assert document["entries"][0]["manifest"]["distribution"]["bundle_digest"] == DIGEST


def test_omission_does_not_generate_a_withdrawal_from_previous_output(tmp_path, entry, monkeypatch, fixed_commit):
    source = write_registry(tmp_path, [entry])
    monkeypatch.setattr(catalogue, "ROOT", tmp_path)
    output = tmp_path / "output"
    first, _ = catalogue.build(output=output)
    (source / "releases/proxmox-0.2.0.json").unlink()
    (source / "sequence.txt").write_text("2\n", encoding="ascii")
    _, current = catalogue.build(output=output)
    assert current["entries"] == []
    assert (output / "catalogue-000001.json").read_bytes() == first
    assert (output / "catalogue.json").read_bytes() == (output / "catalogue-000002.json").read_bytes()


@pytest.mark.parametrize("field,value", [
    ("schema_version", "2.0"), ("schema_version", 1.0),
    ("publisher_id", "other-publisher"), ("repository", "other/repository"),
    ("generated_at", "2026-10-18T06:45:01+00:00"), ("generated_at", "2026-10-18T06:45:01.0Z"),
    ("generated_at", "2026-02-30T06:45:01Z"), ("generated_at", None),
    ("generated_at", "2026-10-18T06:45:01Z\n"),
    ("expires_at", "2026-10-25T06:45:02Z"), ("expires_at", "2026-10-24T06:45:01Z"),
    ("entries", {}),
])
def test_strict_catalogue_document_contract(document, field, value):
    document[field] = value
    with pytest.raises(ValueError):
        catalogue.validate_catalogue(document)


@pytest.mark.parametrize("target", ["catalogue", "entry"])
@pytest.mark.parametrize("mutation", ["missing", "unknown"])
def test_fields_must_match_strict_schema(document, target, mutation):
    value = document if target == "catalogue" else document["entries"][0]
    if mutation == "missing":
        value.pop("schema_version" if target == "catalogue" else "status")
    else:
        value["unexpected"] = "extra"
    with pytest.raises(ValueError):
        catalogue.validate_catalogue(document)


def test_unsorted_document_is_rejected(document):
    document["entries"].insert(0, release(document["entries"][0], "0.3.0", 123))
    with pytest.raises(ValueError, match="unsorted_catalogue_entries"):
        catalogue.validate_catalogue(document)


def test_catalogue_metadata_and_entry_bounds_are_explicit():
    assert catalogue.MAX_CATALOGUE_BYTES == 4 * 1024 * 1024
    assert catalogue.MAX_METADATA_BYTES == 256 * 1024
    assert catalogue.MAX_ENTRIES == 200


@pytest.mark.parametrize("size_delta", [-1, 0, 1])
def test_aggregate_catalogue_size_boundary(document, size_delta):
    entry = document["entries"][0]
    document["entries"] = [release(entry, f"0.3.{i}", i + 1) for i in range(20)]
    document["entries"].sort(key=lambda row: (row["manifest"]["id"], row["manifest"]["version"]))
    target_size = catalogue.MAX_CATALOGUE_BYTES + size_delta
    padding, remainder = divmod(target_size - len(catalogue.canonical_json(document)),
                                len(document["entries"]))
    # Grow schema-valid URLs while keeping each release below the SDK bound.
    for i, row in enumerate(document["entries"]):
        row["manifest"]["display"]["documentation_uri"] += "a" * (padding + (i < remainder))
        assert len(catalogue.canonical_json(row)) <= catalogue.MAX_METADATA_BYTES
    assert len(catalogue.canonical_json(document)) == target_size
    if size_delta > 0:
        with pytest.raises(ValueError, match="^catalogue_too_large$"):
            catalogue.validate_catalogue(document)
    else:
        assert catalogue.validate_catalogue(document) == document


def test_hard_entry_count_accepts_limit_rejects_excess(document):
    entry = document["entries"][0]
    document["entries"] = [release(entry, f"0.3.{i}", i + 1) for i in range(catalogue.MAX_ENTRIES)]
    document["entries"].sort(key=lambda row: (row["manifest"]["id"], row["manifest"]["version"]))
    catalogue.validate_catalogue(document)
    document["entries"].append(release(entry, "0.4.0", catalogue.MAX_ENTRIES + 1))
    with pytest.raises(ValueError, match="invalid_catalogue_entry_count"):
        catalogue.validate_catalogue(document)


def test_registry_entry_ceiling_applies_before_parsing(tmp_path):
    source = write_registry(tmp_path, [])
    for i in range(catalogue.MAX_ENTRIES + 1):
        (source / "releases" / f"invalid-{i}.json").write_bytes(b"invalid")
    with pytest.raises(ValueError, match="invalid_catalogue_entry_count"):
        catalogue.load_registry(source)


@pytest.mark.parametrize("raw", [
    b"", b"{", b"[]", b"null", b"true", b"{} {}", b'{"status": "active",}',
    b'{"status": "active", "status": "withdrawn"}',
    b'{"status": "active", "sta\\u0074us": "withdrawn"}',
    b'{"manifest": {"version": "0.2.0", "version": "0.3.0"}}',
    b'{"release_asset_id": NaN}', b'{"release_asset_id": Infinity}',
    b'{"release_asset_id": -Infinity}', b'{"release_asset_id": 1e400}',
    b'\xff', b'\xef\xbb\xbf{}', '{}'.encode('utf-16'),
])
def test_malformed_or_ambiguous_release_json_fails_without_output(tmp_path, raw, monkeypatch, fixed_commit):
    source = write_registry(tmp_path, [])
    (source / "releases/proxmox-0.2.0.json").write_bytes(raw)
    monkeypatch.setattr(catalogue, "ROOT", tmp_path)
    with pytest.raises(ValueError):
        catalogue.build(output=tmp_path / "output")
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), 2**53, {1: "ambiguous"}, object()])
def test_json_generation_rejects_non_finite_or_ambiguous_values(value):
    with pytest.raises(ValueError, match="invalid_catalogue_json"):
        catalogue.canonical_json({"value": value})


@pytest.mark.parametrize("number", ["NaN", "Infinity", "-Infinity", "1e400"])
def test_non_finite_number_in_complete_manifest_is_rejected(tmp_path, entry, number):
    source = write_registry(tmp_path, [])
    entry["manifest"]["connection_fields"][0]["validation"] = {"maximum": 123456789}
    raw = json.dumps(entry).replace('"maximum": 123456789', '"maximum": ' + number)
    (source / "releases/proxmox-0.2.0.json").write_text(raw, encoding="utf-8")
    with pytest.raises(ValueError, match="invalid_metadata_number"):
        catalogue.load_registry(source)


def test_invalid_unicode_in_an_otherwise_valid_manifest_fails_closed(document):
    document["entries"][0]["manifest"]["display"]["description"] = "\ud800"
    with pytest.raises(ValueError, match="invalid_catalogue_json"):
        catalogue.validate_catalogue(document)


@pytest.mark.parametrize("size_delta", [-1, 0, 1])
def test_release_metadata_size_is_bounded(tmp_path, entry, size_delta):
    source = write_registry(tmp_path, [])
    raw = catalogue.canonical_json(entry)
    raw += b" " * (catalogue.MAX_METADATA_BYTES + size_delta - len(raw))
    (source / "releases/proxmox-0.2.0.json").write_bytes(raw)
    if size_delta > 0:
        with pytest.raises(ValueError, match="metadata_too_large"):
            catalogue.load_registry(source)
    else:
        assert catalogue.load_registry(source) == (1, [entry])


@pytest.mark.parametrize("kind", ["wrong_name", "symlink", "directory", "non_json"])
def test_registry_contains_only_identity_named_regular_json_files(tmp_path, entry, kind):
    source = write_registry(tmp_path, [])
    path = source / "releases/proxmox-0.2.0.json"
    if kind == "wrong_name":
        path = source / "releases/proxmox-0.3.0.json"
        path.write_bytes(catalogue.canonical_json(entry))
    elif kind == "symlink":
        outside = tmp_path / "outside.json"
        outside.write_bytes(catalogue.canonical_json(entry))
        path.symlink_to(outside)
    elif kind == "directory":
        path.mkdir()
    else:
        (source / "releases/notes.txt").write_text("not release metadata", encoding="ascii")
    with pytest.raises(ValueError):
        catalogue.load_registry(source)


def test_builder_needs_no_network_or_commands_other_than_fixed_git(monkeypatch):
    def fail(*args, **kwargs):
        pytest.fail("catalogue attempted network access")
    monkeypatch.setattr(socket, "socket", fail)
    monkeypatch.setattr(socket, "create_connection", fail)
    monkeypatch.setattr(socket, "getaddrinfo", fail)
    monkeypatch.setattr(urllib.request, "urlopen", fail)
    calls = []
    def only_git(args, **kwargs):
        assert args == ["git", "show", "-s", "--format=%ct", "HEAD"]
        assert kwargs == {"cwd": ROOT, "text": True}
        calls.append(args)
        return "1792305901\n"
    monkeypatch.setattr(catalogue.subprocess, "check_output", only_git)
    payload, document = catalogue.build()
    assert calls and payload and document["entries"]
