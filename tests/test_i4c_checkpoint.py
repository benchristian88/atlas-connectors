# SPDX-License-Identifier: Apache-2.0
import importlib.util
import json
from pathlib import Path
import sys

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_bundle import build

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verify_candidate", ROOT / "tools/verify_candidate.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


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
    payload, manifest = build(output=tmp_path, candidate=True)
    assert manifest["version"] == "0.2.0-i4b.5"
    assert (tmp_path / "proxmox-0.2.0-i4b.5.tar.gz").read_bytes() == payload
    assert original.read_bytes() == b"immutable prior candidate fixture"
    assert second.read_bytes() == b"immutable second candidate fixture"
    assert third.read_bytes() == b"immutable diagnostic candidate fixture"
    assert fourth.read_bytes() == b"immutable storage-normalization candidate fixture"
    assert manifest["source_versions"]["qualification"] == "unqualified"
    assert manifest["source_versions"]["qualified_versions"] == []


def test_default_production_archive_remains_exact_probe_only_release():
    _, manifest = build()
    assert manifest["version"] == "0.1.0"
    assert manifest["distribution"]["bundle_digest"] == "sha256:b83ec2b3938b1747d12be5f0675dbc3e9da13c6259c2ab40f5daa994ee59ea60"
    assert manifest["capabilities"]["discover"] is False
    assert set(manifest["implementation"]["entry_points"]) == {"test_connection"}


def test_candidate_recommends_existing_lxc_type_and_retains_vm_mapping():
    _, manifest = build(candidate=True)
    mappings = {row["key"]: row.get("recommended_asset_type_key") for row in manifest["object_classes"]}
    assert mappings["proxmox.lxc"] == "lxc_container"
    assert mappings["proxmox.qemu"] == "virtual_machine"


def test_qualification_mapping_plan_requires_only_five_assets_and_three_relationships():
    _, manifest = build(candidate=True)
    assets = {row['key']: row['recommended_asset_type_key'] for row in manifest['object_classes'] if row['kind'] == 'asset'}
    relationships = {row['key']: row['recommended_relationship_type_key'] for row in manifest['relationship_classes']}
    assert assets == {'proxmox.cluster': 'cluster', 'proxmox.node': 'hypervisor_node',
                      'proxmox.qemu': 'virtual_machine', 'proxmox.lxc': 'lxc_container',
                      'proxmox.bridge': 'network_device'}
    assert relationships == {'proxmox.member_of': 'member_of', 'proxmox.runs_on': 'runs_on',
                             'proxmox.connected_to': 'connected_to'}
    assert all(row['required'] for row in manifest['object_classes'] + manifest['relationship_classes'])
    assert {row['key']: row['kind'] for row in manifest['object_classes'] if row['kind'] != 'asset'} == {
        'proxmox.network': 'network', 'proxmox.interface': 'interface'}
    assert set(manifest['discovery_scopes'][0]['object_classes']) == {row['key'] for row in manifest['object_classes']}
    assert {row['key'] for row in manifest['facts']} == {'proxmox.vmid', 'proxmox.template', 'proxmox.deployment_mode',
        'proxmox.power_state', 'proxmox.online', 'proxmox.vlan_aware', 'proxmox.vlan_tag'}
    assert 'proxmox.storage' not in json.dumps(manifest) and 'proxmox.uses_storage' not in json.dumps(manifest)


def test_candidate_packages_current_mvp_docs_without_changing_frozen_production_docs():
    import io
    import tarfile
    candidate, _ = build(candidate=True)
    production, _ = build()
    with tarfile.open(fileobj=io.BytesIO(candidate)) as archive:
        assert b'0.2.0-i4b.5' in archive.extractfile('README.md').read()
        assert b'Not called or allowlisted in .5' in archive.extractfile('docs/discovery.md').read()
        assert b'lxc_container' in archive.extractfile('docs/discovery.md').read()
    with tarfile.open(fileobj=io.BytesIO(production)) as archive:
        assert archive.extractfile('README.md').read() == (ROOT / 'connectors/proxmox/README.md').read_bytes()
