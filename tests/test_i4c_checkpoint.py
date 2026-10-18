# SPDX-License-Identifier: Apache-2.0
import importlib.util
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_bundle import build

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verify_candidate", ROOT / "tools/verify_candidate.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)
QUALIFIED_CANDIDATE_DIGEST = "sha256:dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97"


def test_exact_candidate_and_default_bytes_survive_unrelated_files(tmp_path, monkeypatch):
    import build_bundle
    import shutil
    staged = tmp_path / "source"
    shutil.copytree(ROOT / "connectors", staged / "connectors")
    shutil.copy(ROOT / "LICENSE", staged / "LICENSE")
    # Keep Git provenance in the real checkout while testing a staged tree.
    original = build_bundle.subprocess.check_output
    monkeypatch.setattr(build_bundle.subprocess, "check_output", lambda args, **kw: original(args, cwd=ROOT, text=True))
    monkeypatch.setattr(build_bundle, "ROOT", staged)
    candidate, _ = build(candidate=True)
    production, _ = build()
    (staged / "connectors/proxmox/docs/unreviewed.md").write_text("operator report\n")
    (staged / "connectors/proxmox/library/local_fixture.py").write_text("test transport\n")
    assert build(candidate=True)[0] == candidate
    assert build()[0] == production


def test_independent_candidate_verification_and_digest_failure(tmp_path):
    first, manifest = build(output=tmp_path, candidate=True)
    second, _ = build(candidate=True)
    assert first == second
    digest = manifest["distribution"]["bundle_digest"]
    assert digest == QUALIFIED_CANDIDATE_DIGEST
    assert "sha256:" + hashlib.sha256(first).hexdigest() == QUALIFIED_CANDIDATE_DIGEST
    assert verifier.verify(tmp_path, digest)["files"] == 19
    with pytest.raises(ValueError, match="candidate_digest_mismatch"):
        verifier.verify(tmp_path, "sha256:" + "0" * 64)
    detached = json.loads((tmp_path / "manifest.json").read_text())
    detached["source_versions"]["qualification"] = "qualified"
    detached["source_versions"]["qualified_versions"] = ["9.2.11"]
    (tmp_path / "manifest.json").write_text(json.dumps(detached))
    with pytest.raises(ValueError, match="candidate_manifest_mismatch"):
        verifier.verify(tmp_path, digest)


def test_successor_candidate_uses_new_identity_and_preserves_existing_original_archive(tmp_path):
    original = tmp_path / "proxmox-0.2.0-i4b.1.tar.gz"
    original.write_bytes(b"immutable prior candidate fixture")
    second = tmp_path / "proxmox-0.2.0-i4b.2.tar.gz"
    second.write_bytes(b"immutable second candidate fixture")
    third = tmp_path / "proxmox-0.2.0-i4b.3.tar.gz"
    third.write_bytes(b"immutable diagnostic candidate fixture")
    fourth = tmp_path / "proxmox-0.2.0-i4b.4.tar.gz"
    fourth.write_bytes(b"immutable storage-normalization candidate fixture")
    fifth = tmp_path / "proxmox-0.2.0-i4b.5.tar.gz"
    fifth.write_bytes(b"immutable storage-scope candidate fixture")
    payload, manifest = build(output=tmp_path, candidate=True)
    assert manifest["version"] == "0.2.0-i4b.6"
    assert (tmp_path / "proxmox-0.2.0-i4b.6.tar.gz").read_bytes() == payload
    assert original.read_bytes() == b"immutable prior candidate fixture"
    assert second.read_bytes() == b"immutable second candidate fixture"
    assert third.read_bytes() == b"immutable diagnostic candidate fixture"
    assert fourth.read_bytes() == b"immutable storage-normalization candidate fixture"
    assert fifth.read_bytes() == b"immutable storage-scope candidate fixture"
    assert manifest["source_versions"]["qualification"] == "unqualified"
    assert manifest["source_versions"]["qualified_versions"] == []


def test_default_production_archive_contains_only_reviewed_release_files(tmp_path):
    payload, manifest = build(output=tmp_path)
    second, descriptor = build()
    assert (payload, manifest) == (second, descriptor)
    assert manifest["version"] == "0.2.0"
    distribution = manifest["distribution"]
    assert distribution["bundle_digest"] == "sha256:" + hashlib.sha256(payload).hexdigest()
    assert distribution["asset_uri"] == (
        "https://github.com/benchristian88/atlas-connectors/releases/download/"
        "proxmox-v0.2.0/proxmox-0.2.0.tar.gz"
    )
    import subprocess
    assert distribution["provenance"] == {
        "method": "github-artifact-attestation-sigstore", "publisher_id": "atlas-official",
        "repository": "benchristian88/atlas-connectors", "workflow": ".github/workflows/release.yml",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "evidence_uri": "https://github.com/benchristian88/atlas-connectors/attestations",
    }
    assert (tmp_path / "proxmox-0.2.0.tar.gz").read_bytes() == payload
    assert json.loads((tmp_path / "manifest.json").read_bytes()) == manifest
    assert json.loads((tmp_path / "index.json").read_bytes()) == {"schema_version": "1.0", "entries": [manifest]}
    assert (tmp_path / "SHA256SUMS").read_text() == distribution["bundle_digest"][7:] + "  proxmox-0.2.0.tar.gz\n"
    assert payload[3:8] == b'\x00' * 5  # No optional gzip fields and mtime zero.
    with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
        names = archive.getnames()
        assert names == sorted(verifier.EXPECTED_FILES)
        assert not any("candidate" in Path(name).parts or "tests" in Path(name).parts
                       or "fixtures" in name or "__pycache__" in name or name.endswith(".pyc") for name in names)
        for member in archive.getmembers():
            assert member.isfile() and member.mode == 0o644 and member.mtime == 0
            assert member.uid == member.gid == 0 and member.uname == member.gname == ""
            path = ROOT / "LICENSE" if member.name == "LICENSE" else ROOT / "connectors/proxmox" / member.name
            assert archive.extractfile(member).read() == path.read_bytes()
        packaged = json.loads(archive.extractfile("manifest.json").read())
        assert packaged == {key: value for key, value in manifest.items() if key != "distribution"}
        from atlas_connector_sdk.contracts import validate_manifest
        validate_manifest({**packaged, "distribution": distribution})
        from yaml import safe_load
        playbook = safe_load(archive.extractfile("test_connection.yml").read())
        assert "atlas_readiness" in playbook[0]["tasks"][0]
        assert playbook[0]["tasks"][0]["no_log"] is True


def test_production_sbom_promotes_runtime_owned_collection_without_bundling_it():
    sbom = json.loads((ROOT / "connectors/proxmox/sbom.spdx.json").read_bytes())
    assert sbom["name"] == "atlas-proxmox-0.2.0"
    assert sbom["documentNamespace"] == "https://github.com/benchristian88/atlas-connectors/sbom/proxmox/0.2.0"
    candidate = json.loads((ROOT / "connectors/proxmox/candidate/sbom.spdx.json").read_bytes())
    candidate.update(name=sbom["name"], documentNamespace=sbom["documentNamespace"])
    candidate["packages"][0]["versionInfo"] = "0.2.0"
    assert sbom == candidate
    dependency = sbom["packages"][1]
    assert dependency["versionInfo"] == "2.0.0"
    assert dependency["checksums"] == [{"algorithm": "SHA256", "checksumValue": verifier.COLLECTION_DIGEST}]
    assert "runtime-owned" in dependency["comment"] and "not bundled" in dependency["comment"]
    assert sbom["relationships"] == [{
        "spdxElementId": "SPDXRef-proxmox", "relationshipType": "DEPENDS_ON",
        "relatedSpdxElement": "SPDXRef-community-proxmox",
    }]


def test_candidate_recommends_existing_lxc_type_and_retains_vm_mapping():
    _, manifest = build(candidate=True)
    mappings = {row["key"]: row.get("recommended_asset_type_key") for row in manifest["object_classes"]}
    assert mappings["proxmox.lxc"] == "lxc_container"
    assert mappings["proxmox.qemu"] == "virtual_machine"


@pytest.mark.parametrize("candidate", [False, True])
def test_release_and_candidate_require_only_four_assets_and_two_relationships(candidate):
    _, manifest = build(candidate=candidate)
    assets = {row['key']: row['recommended_asset_type_key'] for row in manifest['object_classes'] if row['kind'] == 'asset'}
    relationships = {row['key']: row['recommended_relationship_type_key'] for row in manifest['relationship_classes']}
    assert assets == {'proxmox.cluster': 'cluster', 'proxmox.node': 'hypervisor_node',
                      'proxmox.qemu': 'virtual_machine', 'proxmox.lxc': 'lxc_container'}
    assert relationships == {'proxmox.member_of': 'member_of', 'proxmox.runs_on': 'runs_on'}
    assert all(row['required'] for row in manifest['object_classes'] + manifest['relationship_classes'])
    assert {row['key']: row['kind'] for row in manifest['object_classes'] if row['kind'] != 'asset'} == {
        'proxmox.network': 'network', 'proxmox.interface': 'interface'}
    assert set(manifest['discovery_scopes'][0]['object_classes']) == {row['key'] for row in manifest['object_classes']}
    assert {row['key'] for row in manifest['facts']} == {'proxmox.vmid', 'proxmox.template', 'proxmox.deployment_mode',
        'proxmox.power_state', 'proxmox.online', 'proxmox.vlan_aware', 'proxmox.vlan_tag',
        'proxmox.bridge_name', 'proxmox.vlan_trunks'}
    assert all(row['object_classes'] == ['proxmox.interface'] for row in manifest['facts']
               if row['key'] in {'proxmox.vlan_aware', 'proxmox.vlan_tag', 'proxmox.bridge_name', 'proxmox.vlan_trunks'})
    assert 'proxmox.bridge' not in {row['key'] for row in manifest['object_classes']}
    assert 'proxmox.connected_to' not in relationships
    assert 'proxmox.storage' not in json.dumps(manifest) and 'proxmox.uses_storage' not in json.dumps(manifest)


def test_candidate_keeps_pre_live_snapshot_while_production_packages_qualified_docs():
    candidate, _ = build(candidate=True)
    production, _ = build()
    with tarfile.open(fileobj=io.BytesIO(candidate)) as archive:
        assert b'0.2.0-i4b.6' in archive.extractfile('README.md').read()
        assert b'Not called or allowlisted in .6' in archive.extractfile('docs/discovery.md').read()
        assert b'lxc_container' in archive.extractfile('docs/discovery.md').read()
        qualification = archive.extractfile('docs/qualification.md').read()
        assert b'UNQUALIFIED' in qualification and b'has no live results yet' in qualification
    with tarfile.open(fileobj=io.BytesIO(production)) as archive:
        assert archive.extractfile('README.md').read() == (ROOT / 'connectors/proxmox/README.md').read_bytes()
        qualification = archive.extractfile('docs/qualification.md').read()
        assert b'9.2.11' in qualification and b'100 observations' in qualification
        assert b'Authentication-secret negative testing was not performed' in qualification
        assert b'Native Debian/systemd LIVE acceptance remains outstanding' in qualification
