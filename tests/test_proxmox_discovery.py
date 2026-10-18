# SPDX-License-Identifier: Apache-2.0
from copy import deepcopy
import io
import json
from pathlib import Path
import secrets
import sys
import tarfile
import uuid

import pytest
from atlas_connector_sdk.aip import validate_example_stream
from atlas_connector_sdk.contracts import validate_manifest
from ansible.module_utils.atlas_discovery import discover
from ansible.module_utils.atlas_diagnostics import Diagnostics
from ansible.module_utils.atlas_normalization import CLASSES, relationship, storage_id

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from build_bundle import build
from proxmox_fixture_transport import fixture, adapter_factory


@pytest.fixture
def inputs():
    return {'reference': {'connector_id': 'proxmox', 'version': build(candidate=True)[1]['version'], 'digest': build(candidate=True)[1]['distribution']['bundle_digest'][7:]},
            'config': {'endpoint': 'https://source.example.test:8006'},
            'credentials': {'token_id': 'fixture_' + secrets.token_hex(8) + '@pve!discovery', 'token_secret': secrets.token_urlsafe(32)},
            'run_id': str(uuid.uuid4()), 'integration_id': str(uuid.uuid4()), 'selected_scopes': ['inventory'], 'object_classes': CLASSES,
            'timeout_seconds': 120, 'coverage': {'key': 'fixture:inventory', 'snapshot_mode': 'full', 'domains': ['assets', 'networks', 'interfaces', 'relationships']}}


def run(inputs, scenario='complete', data=None):
    factory = adapter_factory(data or fixture(scenario))
    result = discover(inputs, adapter_factory=factory)
    validate_example_stream(result, build(candidate=True)[1])
    return result, factory.calls


@pytest.mark.parametrize('scenario,completeness', [
    ('complete','complete'), ('standalone','complete'), ('empty_authorized','complete'),
    ('empty_unproven','partial'), ('permission_filtered','partial'), ('acl_audit_missing','partial'),
    ('offline','partial'), ('source_failure','failed'), ('storage_failure','partial'),
    ('config_failure','partial'), ('pending','partial'), ('malformed','partial'), ('limits','failed')])
def test_coverage_requires_executed_calls_acl_consistency_and_valid_records(inputs, scenario, completeness):
    result, calls = run(inputs, scenario)
    assert result[-1]['completeness'] == completeness
    assert result[-1]['coverage'] == inputs['coverage']
    if completeness == 'complete':
        for node in ['node-a'] if scenario != 'complete' else ['node-a', 'node-b']:
            assert '/nodes/' + node + '/qemu' in calls
            assert '/nodes/' + node + '/lxc' in calls
            assert '/nodes/' + node + '/storage' in calls
            assert '/nodes/' + node + '/network' in calls
        assert calls.count('/access/acl') == 2
    serialized = json.dumps(result)
    for value in inputs['credentials'].values():
        assert value not in serialized
    assert 'FixtureAudit' not in serialized and 'fixture-account' not in serialized
    assert not any('/agent/' in path or 'current=0' in path or '/storage/shared' == path for path in calls)


def test_candidate_is_reproducible_unqualified_and_isolated_from_production():
    payload, manifest = build(candidate=True)
    assert payload == build(candidate=True)[0]
    validate_manifest(manifest)
    assert manifest['source_versions']['qualification'] == 'unqualified'
    assert not manifest['source_versions']['qualified_versions']
    assert manifest['implementation']['dependencies'][0]['version'] == '2.0.0'
    with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
        assert {'discover.yml', 'library/atlas_discover.py', 'module_utils/atlas_transport.py'} <= set(archive.getnames())
        assert not any('fixtures' in path or path.startswith('tests/') or path.startswith('candidate/') for path in archive.getnames())
    production, prod_manifest = build()
    assert prod_manifest['version'] == '0.1.0' and prod_manifest['capabilities']['discover'] is False
    with tarfile.open(fileobj=io.BytesIO(production)) as archive:
        assert 'discover.yml' not in archive.getnames()
        assert not any(path.startswith('module_utils/') for path in archive.getnames())


def test_mandatory_scope_and_classes_cannot_be_silently_skipped(inputs):
    for field, value in [('selected_scopes', []), ('object_classes', ['proxmox.node'])]:
        changed = deepcopy(inputs); changed[field] = value
        result, calls = run(changed)
        assert result[-1]['completeness'] == 'failed' and not calls


def test_all_source_facts_are_allowlisted_and_power_is_not_lifecycle(inputs):
    result, _ = run(inputs)
    payload = json.dumps(result)
    assert 'ignored' not in payload and 'unused' not in payload and '/mnt/private' not in payload
    manifest = build(candidate=True)[1]
    allowed = {row['key'] for row in manifest['facts']}
    entities = [row for batch in result[:-1] for domain in ['assets','interfaces','networks'] for row in batch[domain]]
    assert all(fact['key'] in allowed for row in entities for fact in row['facts'])
    assert all('status' not in row for batch in result[:-1] for row in batch['assets'])


def test_failed_enrichment_retains_base_inventory_and_aggregate_is_partial(inputs):
    result, _ = run(inputs, 'config_failure')
    assert result[-1]['completeness'] == 'partial'
    assert 'guest/qemu/100' in {row['external_id'] for row in result[0]['assets']}


def test_inactive_or_pending_bridge_configuration_never_becomes_topology(inputs):
    result, _ = run(inputs, 'pending')
    assert 'bridge/node-a/vmbr0' not in {row['external_id'] for row in result[0]['assets']}
    assert not any(row['target']['external_id'] == 'bridge/node-a/vmbr0' for row in result[0]['relationships'])


def test_malformed_required_identity_and_inventory_consistency_prevent_complete(inputs):
    for mutation in ['duplicate', 'missing_node_list', 'bad_id', 'missing_config', 'wrong_node']:
        data = fixture()
        if mutation == 'duplicate': data['responses']['/cluster/resources?type=vm'].append(deepcopy(data['responses']['/cluster/resources?type=vm'][0]))
        elif mutation == 'missing_node_list': data['responses']['/nodes/node-a/qemu'] = []
        elif mutation == 'bad_id': data['responses']['/cluster/resources?type=vm'][0]['vmid'] = 'invalid'
        elif mutation == 'missing_config': data['responses']['/nodes/node-a/qemu/100/config?current=1'] = []
        else: data['responses']['/cluster/resources?type=vm'][0]['node'] = 'unknown-node'
        result, _ = run(inputs, data=data)
        assert result[-1]['completeness'] in {'partial','failed'}


def test_lossy_collection_boolean_normalization_cannot_hide_malformed_source_flags(inputs):
    for path,field in [('/storage','shared'),('/nodes/node-a/qemu','template'),
                       ('/nodes/node-a/network','bridge_vlan_aware'),
                       ('/nodes/node-a/network','active'), ('/nodes/node-a/network','autostart')]:
        data=fixture(); data['responses'][path][0][field]=2
        result,_=run(inputs,data=data)
        assert result[-1]['completeness'] in {'partial','failed'}


def test_proxmox_9_2_11_vlan_exists_null_does_not_poison_bridge_discovery(inputs):
    data = fixture()
    # Preserve the ordinary vmbr0 fixture; this is a separate legitimate row.
    data['responses']['/nodes/node-a/network'].append({
        'active': 1, 'address': '192.168.99.27', 'cidr': '192.168.99.27/24',
        'exists': None, 'iface': 'vmbr0.99', 'type': 'vlan',
        'vlan-id': '99', 'vlan-raw-device': 'vmbr0',
    })
    result, _ = run(inputs, data=data)
    assert result[-1]['completeness'] == 'complete'
    assert 'bridge/node-a/vmbr0' in {row['external_id'] for batch in result[:-1] for row in batch['assets']}
    assert any(row['target']['external_id'] == 'bridge/node-a/vmbr0'
               for batch in result[:-1] for row in batch['relationships'])


def test_test_bundle_is_reproducible_and_runtime_fixtures_are_test_only(tmp_path):
    from build_acceptance_fixture import build_fixture
    first,manifest=build_fixture(tmp_path/'first')
    second,_=build_fixture(tmp_path/'second')
    assert first==second and manifest['id']=='i4b-fixture'
    assert manifest['source_versions']['qualified_versions']==['fixture-only']
    assert '9.2.11' not in manifest['source_versions']['qualified_versions']


def test_malformed_empty_mapping_is_never_an_authorized_empty_inventory_list(inputs):
    for path in ['/storage','/nodes/node-a/network']:
        for malformed in [{}, [{}]]:
            data=fixture(); data['responses'][path]=malformed
            result,_=run(inputs,data=data)
            assert result[-1]['completeness'] in {'partial','failed'}


def test_empty_acl_cannot_be_visibility_proof(inputs):
    data=fixture(); data['acl']=[]
    result,_=run(inputs,data=data)
    assert result[-1]['completeness']=='partial'


def test_inactive_bridge_preserves_identity_without_current_topology_or_complete_absence(inputs):
    data=fixture('empty_authorized'); data['responses']['/nodes/node-a/network'][0]['active']=0
    result,_=run(inputs,data=data)
    assert result[-1]['completeness']=='partial'
    assert 'bridge/node-a/vmbr0' in {row['external_id'] for batch in result[:-1] for row in batch['assets']}
    assert not any(row['target']['external_id']=='bridge/node-a/vmbr0' for batch in result[:-1] for row in batch['relationships'])


def test_three_node_storage_scope_preserves_complete_and_local_shared_and_guest_identities(inputs):
    data = fixture('heterogeneous_storage')
    result, calls = run(inputs, data=data)
    assert result[-1]['completeness'] == 'complete' and 'warnings' not in result[-1]
    assets = {row['external_id']: row for batch in result[:-1] for row in batch['assets']}
    links = [row for batch in result[:-1] for row in batch['relationships']]
    for index, node in enumerate(['pve1', 'pve2', 'pve3'], 1):
        local = 'local-lvm' if node == 'pve3' else 'local-zfs'
        external = storage_id(node, local, False)
        assert external in assets
        assert {'key': 'proxmox.shared', 'value_type': 'boolean', 'class': 'configuration',
                'cardinality': 'single', 'value': False} in assets[external]['facts']
        assert relationship('uses_storage', f'guest/qemu/{100 + index}', external) in links
        assert relationship('uses_storage', f'guest/qemu/{100 + index}', 'storage/shared/synology-vmdata') in links
    assert 'storage/local/pve3/local-zfs' not in assets
    assert len([key for key in assets if key.startswith('storage/shared/')]) == 4
    assert len([key for key in assets if key.startswith('storage/local/')]) == 6
    # Removing only the irrelevant row has no effect on AIP or source requests.
    data['responses']['/nodes/pve3/storage'].pop()
    baseline, baseline_calls = run(inputs, data=data)
    assert [{k: v for k, v in row.items() if k != 'observed_at'} for row in result] == [
        {k: v for k, v in row.items() if k != 'observed_at'} for row in baseline]
    assert calls == baseline_calls


@pytest.mark.parametrize('enabled,active', [(1, 0), (0, 1), (1, 1)])
@pytest.mark.parametrize('defined_elsewhere', [False, True])
def test_non_applicable_enabled_or_active_storage_prevents_complete(inputs, enabled, active, defined_elsewhere):
    data = fixture('heterogeneous_storage')
    if not defined_elsewhere:
        # Other nodes also now lack a definition: all such rows must fail closed.
        data['responses']['/storage'].pop()
    data['responses']['/nodes/pve3/storage'][-1].update(enabled=enabled, active=active)
    diagnostics = Diagnostics()
    result = discover(inputs, adapter_factory=adapter_factory(data), diagnostics=diagnostics)
    assert result[-1]['completeness'] == 'partial'
    assert result[-1]['warnings'] == [{'code': 'invalid_source_record'}]
    assert 'storage/local/pve3/local-zfs' not in {row['external_id'] for batch in result[:-1] for row in batch['assets']}
    assert any(event['reason_code'] == 'storage_definition_missing' and event['parent_external_id'] == 'node/pve3'
               for event in diagnostics.events)


@pytest.mark.parametrize('field', ['active', 'enabled', 'shared'])
@pytest.mark.parametrize('value', [None, '0', 'false', 2, -1, 0.0, [], {}])
def test_malformed_storage_boolean_never_becomes_out_of_scope_or_complete(inputs, field, value):
    data = fixture('heterogeneous_storage')
    data['responses']['/nodes/pve3/storage'][-1][field] = value
    result, _ = run(inputs, data=data)
    assert result[-1]['completeness'] == 'partial'
    assert {'code': 'invalid_source_record'} in result[-1]['warnings']


def test_missing_applicable_storage_status_preserves_partial_mismatch(inputs):
    data = fixture('heterogeneous_storage')
    data['responses']['/nodes/pve3/storage'] = [
        row for row in data['responses']['/nodes/pve3/storage'] if row['storage'] != 'pbs-backup']
    diagnostics = Diagnostics()
    result = discover(inputs, adapter_factory=adapter_factory(data), diagnostics=diagnostics)
    assert result[-1]['completeness'] == 'partial'
    assert any(event['reason_code'] == 'storage_inventory_mismatch' and event['parent_external_id'] == 'node/pve3'
               for event in diagnostics.events)


def test_applicable_disabled_inactive_storage_remains_inventory_and_resolves_guest_links(inputs):
    data = fixture('heterogeneous_storage')
    data['responses']['/storage'][-1]['disable'] = 1
    for node in ['pve1', 'pve2']:
        data['responses']['/nodes/' + node + '/storage'][-1].update(enabled=0, active=0)
    result, _ = run(inputs, data=data)
    assert result[-1]['completeness'] == 'complete'
    assets = {row['external_id']: row for batch in result[:-1] for row in batch['assets']}
    links = [row for batch in result[:-1] for row in batch['relationships']]
    for index, node in enumerate(['pve1', 'pve2'], 1):
        external = 'storage/local/' + node + '/local-zfs'
        assert external in assets
        assert {fact['key'] for fact in assets[external]['facts']} == {'proxmox.shared', 'proxmox.storage_type'}
        assert relationship('uses_storage', f'guest/qemu/{100 + index}', external) in links


@pytest.mark.parametrize('field,value', [('shared', 1), ('type', 'dir')])
def test_applicable_storage_definition_status_inconsistency_remains_partial(inputs, field, value):
    data = fixture('heterogeneous_storage')
    data['responses']['/nodes/pve1/storage'][-1][field] = value
    result, _ = run(inputs, data=data)
    assert result[-1]['completeness'] == 'partial'


@pytest.mark.parametrize('field,value', [('avail', -1), ('avail', 100001), ('total', '100000'), ('total', None)])
def test_active_local_storage_capacity_validation_remains_partial(inputs, field, value):
    data = fixture('heterogeneous_storage')
    data['responses']['/nodes/pve1/storage'][-1][field] = value
    result, _ = run(inputs, data=data)
    assert result[-1]['completeness'] == 'partial'


def test_guest_reference_to_out_of_scope_storage_still_prevents_complete(inputs):
    data = fixture('heterogeneous_storage')
    data['responses']['/nodes/pve3/qemu/103/config?current=1']['scsi0'] = 'local-zfs:fixture-disk'
    diagnostics = Diagnostics()
    result = discover(inputs, adapter_factory=adapter_factory(data), diagnostics=diagnostics)
    assert result[-1]['completeness'] == 'partial'
    assert any(event['reason_code'] == 'guest_storage_unresolved' for event in diagnostics.events)
