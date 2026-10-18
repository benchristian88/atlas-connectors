# SPDX-License-Identifier: Apache-2.0
"""Opt-in read-only checks against the sibling Atlas implementation, no database.

Run explicitly with Atlas's API test environment and PYTHONPATH; the normal
Connector suite has no dependency on the AGPL application or a sibling checkout.
No application implementation is copied into the Connector.
"""
import ast
from contextlib import contextmanager, redirect_stdout
from copy import deepcopy
from io import StringIO
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import uuid

import pytest
from app.models import AssetType, RelationshipType, ConnectorMapping, Integration
from app.services.discovery_orchestration import scope_encoding
from app.services.discovery_observations import _previous_complete_run, reconcile_complete_snapshot
from app.services import simulated_discovery
from scripts import qualify_connector as cli

ROOT = Path(__file__).resolve().parents[1]
ATLAS = Path(cli.__file__).resolve().parents[3]
MANIFEST = json.loads((ROOT / 'connectors/proxmox/candidate/manifest.json').read_text())
ASSETS = {'proxmox.cluster', 'proxmox.node', 'proxmox.qemu', 'proxmox.lxc'}
RELATIONSHIPS = {'proxmox.member_of', 'proxmox.runs_on'}


def seed_keys(name):
    path = ATLAS / 'apps/api/migrations/versions/20260714_0004_auth_rbac_reference_data.py'
    tree = ast.parse(path.read_text())
    value = next(node.value for node in tree.body if isinstance(node, ast.AnnAssign)
                 and isinstance(node.target, ast.Name) and node.target.id == name)
    return {row[0] for row in ast.literal_eval(value)}


class MemoryDB:
    def __init__(self):
        self.rows = []
        self.rolled_back = False

    def scalars(self, statement):
        entity = statement.column_descriptions[0]['entity']
        if entity is ConnectorMapping:
            return self.rows
        assert entity is Integration
        return []

    def scalar(self, statement):
        entity = statement.column_descriptions[0]['entity']
        if entity in {AssetType, RelationshipType}:
            key = statement._where_criteria[0].right.value
            if entity is AssetType:
                return AssetType(key=key, name=key, active=True) if key in seed_keys('ASSET_TYPES') else None
            if key in seed_keys('RELATIONSHIP_TYPES'):
                return RelationshipType(key=key, name=key, active=True, directional=True,
                    allowed_source_asset_type_keys=[], allowed_target_asset_type_keys=[])
            return None
        if entity is ConnectorMapping:
            matches = [row for row in self.rows if all(getattr(row, clause.left.key) == clause.right.value
                       for clause in statement._where_criteria)]
            return matches[0] if matches else None
        return 0  # No active runs.

    def add(self, row):
        self.rows.append(row)

    def flush(self):
        pass

    def execute(self, statement, params):
        assert params == {'key': 'atlas-connector:proxmox'}

    def rollback(self):
        self.rolled_back = True


def qualification_plan(db, mappings=None):
    @contextmanager
    def session():
        yield db
    output = StringIO()
    with patch.object(cli, 'selected', return_value=(ROOT, SimpleNamespace(manifest=MANIFEST))), \
            patch.object(cli, 'authorize'), patch('app.database.SessionLocal', session), redirect_stdout(output):
        cli.plan(SimpleNamespace(scope=['inventory'], mappings=mappings))
    assert db.rolled_back
    return json.loads(output.getvalue())


def test_actual_plan_requires_four_assets_two_relationships_and_only_cluster_override(tmp_path):
    preview = qualification_plan(MemoryDB())
    assert {row['source_key'] for row in preview['mappings'] if row['kind'] == 'asset'} == ASSETS
    assert {row['source_key'] for row in preview['mappings'] if row['kind'] == 'relationship'} == RELATIONSHIPS
    assert {row['source_key'] for row in preview['mappings'] if not row['resolved']} == {'proxmox.cluster'}
    choices = tmp_path / 'mappings.json'
    choices.write_text(json.dumps([{'kind': 'asset', 'source_key': 'proxmox.cluster', 'target_key': 'proxmox_cluster'}]))
    resolved = qualification_plan(MemoryDB(), choices)
    assert all(row['required'] and row['resolved'] for row in resolved['mappings'])
    assert resolved['dependent_configuration_ready']


@pytest.mark.parametrize('kind,key,target', [('asset', 'proxmox.bridge', 'network_bridge'),
    ('relationship', 'proxmox.connected_to', 'connected_via'), ('asset', 'proxmox.storage', 'storage_pool'),
    ('relationship', 'proxmox.uses_storage', 'uses_storage')])
def test_actual_mapping_choices_reject_removed_classes(tmp_path, kind, key, target):
    path = tmp_path / 'removed.json'
    path.write_text(json.dumps([{'kind': kind, 'source_key': key, 'target_key': target}]))
    with pytest.raises(ValueError, match='qualification_invalid_mappings'):
        cli.apply_mappings(MemoryDB(), MANIFEST, path)


def test_actual_coverage_identity_distinguishes_5_from_6_without_version_special_cases():
    path = Path(os.getenv('ATLAS_TEST_PREVIOUS_MANIFEST',
        str(ROOT / 'dist/proxmox-candidate-0.2.0-i4b.5/manifest.json')))
    previous = json.loads(path.read_text())
    assert previous['version'] == '0.2.0-i4b.5'
    row = SimpleNamespace(selected_scopes=['inventory'])
    old, _ = scope_encoding(row, previous, [])
    current, classes = scope_encoding(row, MANIFEST, [])
    assert current['key'] != old['key'] and current['domains'] == old['domains']
    assert set(classes) == ASSETS | {'proxmox.network', 'proxmox.interface'}
    renamed = deepcopy(MANIFEST)
    renamed['version'] = previous['version']
    assert scope_encoding(row, renamed, [])[0] == current
    # With the old selection narrowed, actual .5 produces the same identity:
    # version, relationship and fact changes do not require special cases.
    narrowed = deepcopy(previous)
    narrowed['discovery_scopes'][0]['object_classes'].remove('proxmox.bridge')
    assert scope_encoding(row, narrowed, [])[0] == current
    reordered = deepcopy(MANIFEST)
    reordered['discovery_scopes'][0]['object_classes'].reverse()
    assert scope_encoding(row, reordered, [])[0] == current
    # Exercise the actual baseline selector's equal-key and tenant/source gates.
    class BaselineDB:
        def scalar(self, statement):
            clauses = {clause.left.key: clause.right.value for clause in statement._where_criteria
                       if clause.left.key in {'coverage_key', 'data_source_id', 'customer_id', 'site_id'}}
            assert clauses['coverage_key'] == current['key'] != old['key']
            assert all(clauses[key] == getattr(run, key) for key in ['data_source_id', 'customer_id', 'site_id'])
            return None
    run = SimpleNamespace(id=uuid.uuid4(), data_source_id=uuid.uuid4(), customer_id=uuid.uuid4(),
                          site_id=uuid.uuid4(), coverage_key=current['key'])
    assert _previous_complete_run(BaselineDB(), run) is None


def test_actual_partial_gate_performs_no_absence_database_access():
    class NoAccessDB:
        def __getattr__(self, name):
            raise AssertionError('PARTIAL attempted DB operation: ' + name)
    result = reconcile_complete_snapshot(NoAccessDB(),
        run=SimpleNamespace(status='completed', is_complete_snapshot=True, completeness_status='partial'), user_id=uuid.uuid4())
    assert result.no_longer_observed_count == 0 and result.baseline_run_id is None


def test_actual_interface_ingestion_preserves_declared_bridge_vlan_and_trunk_facts():
    seen = []
    def record(db, **values):
        seen.append(values)
        return SimpleNamespace(is_accepted=True), True
    observation = {'external_id': 'guest/qemu/100/interface/net0', 'name': 'net0',
        'asset_external_id': 'guest/qemu/100', 'is_primary': False, 'mac_address': '02:00:00:00:00:01',
        'facts': [{'key': key, 'value': value, 'value_type': kind, 'class': 'configuration', 'cardinality': 'single'}
                  for key, value, kind in [('proxmox.bridge_name', 'vmbr0', 'string'),
                      ('proxmox.vlan_tag', 99, 'integer'), ('proxmox.vlan_trunks', '100;101', 'string')]]}
    run = SimpleNamespace(id=uuid.uuid4(), customer_id=uuid.uuid4(), site_id=uuid.uuid4())
    evidence = SimpleNamespace(id=uuid.uuid4(), observed_at=None)
    with patch.object(simulated_discovery, 'technical_link', return_value=None), \
            patch.object(simulated_discovery, 'record_assertion', record), \
            patch.object(simulated_discovery, 'create_item', return_value=(SimpleNamespace(), False)):
        simulated_discovery.ingest_technical_observation(None, run=run, source=SimpleNamespace(id=uuid.uuid4()),
            evidence=evidence, observation=observation, entity_type='asset_interface', user_id=uuid.uuid4())
    assert {row['predicate']: row['value'] for row in seen[1:]} == {
        'proxmox.bridge_name': 'vmbr0', 'proxmox.vlan_tag': 99, 'proxmox.vlan_trunks': '100;101'}
    assert all(row['subject_type'] == 'asset_interface' and row['customer_id'] == run.customer_id
               and row['site_id'] == run.site_id and row['evidence_record_id'] == evidence.id for row in seen)
