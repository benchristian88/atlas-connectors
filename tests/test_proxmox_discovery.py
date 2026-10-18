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
from ansible.module_utils.atlas_normalization import CLASSES, relationship

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
    ('offline','partial'), ('source_failure','failed'), ('storage_failure','complete'),
    ('config_failure','partial'), ('pending','partial'), ('malformed','partial'), ('limits','failed')])
def test_coverage_requires_executed_calls_acl_consistency_and_valid_records(inputs, scenario, completeness):
    result, calls = run(inputs, scenario)
    assert result[-1]['completeness'] == completeness
    assert result[-1]['coverage'] == inputs['coverage']
    if completeness == 'complete':
        for node in ['node-a'] if scenario in {'standalone', 'empty_authorized'} else ['node-a', 'node-b']:
            assert '/nodes/' + node + '/qemu' in calls
            assert '/nodes/' + node + '/lxc' in calls
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
    for path,field in [('/cluster/status','online'),('/nodes/node-a/qemu','template'),
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
    for path in ['/nodes/node-a/qemu','/nodes/node-a/network']:
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


def without_time(messages):
    return [{key: value for key, value in message.items() if key != 'observed_at'} for message in messages]


def test_mvp_keeps_exact_cluster_node_guest_bridge_network_and_interface_inventory(inputs):
    result, _ = run(inputs)
    assets = {row['external_id']: row['object_class'] for batch in result[:-1] for row in batch['assets']}
    assert assets == {
        'cluster/deployment': 'proxmox.cluster', 'node/node-a': 'proxmox.node', 'node/node-b': 'proxmox.node',
        'guest/qemu/100': 'proxmox.qemu', 'guest/qemu/101': 'proxmox.qemu', 'guest/lxc/102': 'proxmox.lxc',
        'bridge/node-a/vmbr0': 'proxmox.bridge', 'bridge/node-b/vmbr0': 'proxmox.bridge',
    }
    links = [row for batch in result[:-1] for row in batch['relationships']]
    expected = [relationship('member_of', 'node/' + node, 'cluster/deployment') for node in ['node-a', 'node-b']]
    for node, guests in [('node-a', ['guest/qemu/100', 'guest/lxc/102']), ('node-b', ['guest/qemu/101'])]:
        expected.append(relationship('connected_to', 'node/' + node, 'bridge/' + node + '/vmbr0'))
        for guest in guests:
            expected.extend([relationship('runs_on', guest, 'node/' + node),
                             relationship('connected_to', guest, 'bridge/' + node + '/vmbr0')])
    assert sorted(links, key=lambda row: row['external_id']) == sorted(expected, key=lambda row: row['external_id'])
    assert sum(len(batch['networks']) for batch in result[:-1]) == 2
    assert sum(len(batch['interfaces']) for batch in result[:-1]) == 5
    assert result[-1]['completeness'] == 'complete' and 'warnings' not in result[-1]


@pytest.mark.parametrize('scenario', ['complete', 'heterogeneous_storage'])
@pytest.mark.parametrize('condition', ['absent', 'denied', 'unavailable', 'malformed'])
def test_storage_is_not_read_required_emitted_or_diagnosed(inputs, scenario, condition):
    data = fixture(scenario)
    baseline, baseline_calls = run(inputs, data=data)
    storage_paths = [path for path in data['responses'] if path == '/storage' or path.endswith('/storage')]
    for path in storage_paths:
        if condition == 'absent':
            del data['responses'][path]
        elif condition in {'denied', 'unavailable'}:
            data['failures'][path] = 403 if condition == 'denied' else 500
        else:
            data['responses'][path] = {'arbitrary': 'not-an-inventory-list'}
    # Neither missing Datastore.Audit nor a hidden storage-only NoAccess needs
    # storage-specific visibility proof for the reduced declared scope.
    data['permissions']['/storage'] = {}
    data['permissions']['/storage/hidden'] = {}
    data['acl'].append({'path': '/storage/hidden', 'roleid': 'NoAccess', 'type': 'user',
                        'ugid': 'fixture-account', 'propagate': 1})
    diagnostics = Diagnostics(debug=True)
    factory = adapter_factory(data)
    result = discover(inputs, adapter_factory=factory, diagnostics=diagnostics)
    validate_example_stream(result, build(candidate=True)[1])
    assert without_time(result) == without_time(baseline)
    assert factory.calls == baseline_calls
    assert result[-1]['completeness'] == 'complete' and 'warnings' not in result[-1]
    assert not any('storage' in path for path in factory.calls)
    assert not any(row['object_class'] == 'proxmox.storage' for batch in result[:-1] for row in batch['assets'])
    assert not any(row['relationship_class'] == 'proxmox.uses_storage' for batch in result[:-1] for row in batch['relationships'])
    assert not any('storage' in json.dumps(event) for event in diagnostics.events)


@pytest.mark.parametrize('slot', ['ide0', 'sata1', 'scsi0', 'virtio2', 'rootfs', 'mp0'])
@pytest.mark.parametrize('value', ['unresolved:private-volume,size=8G', '/mnt/private,mp=/private',
                                  '', None, {'arbitrary': 'ignored'}, 'x' * 8193])
def test_guest_disk_rootfs_mount_config_is_ignored_without_changing_networks_or_warnings(inputs, slot, value):
    baseline, expected_calls = run(inputs)
    data = fixture()
    for path, config in data['responses'].items():
        if path.endswith('/config?current=1'):
            config[slot] = value
    diagnostics = Diagnostics(debug=True)
    factory = adapter_factory(data)
    result = discover(inputs, adapter_factory=factory, diagnostics=diagnostics)
    validate_example_stream(result, build(candidate=True)[1])
    assert without_time(result) == without_time(baseline)
    assert factory.calls == expected_calls
    assert not any('storage' in json.dumps(event) for event in diagnostics.events)
    assert 'private-volume' not in json.dumps(result) + json.dumps(diagnostics.events)
    assert '/mnt/private' not in json.dumps(result) + json.dumps(diagnostics.events)


@pytest.mark.parametrize('scenario,count', [('complete', 40), ('heterogeneous_storage', 46)])
def test_actual_mvp_source_request_sequence_has_only_declared_capability_reads(inputs, scenario, count):
    result, calls = run(inputs, scenario)
    proof = ['/access/permissions?path=%2Faccess', '/access/permissions', '/access/acl',
             '/access/permissions?path=%2F', '/access/permissions?path=%2Fnodes',
             '/access/permissions?path=%2Fsdn%2Fzones%2Flocalnetwork', '/access/permissions?path=%2Fvms']
    expected = ['/version', '/version', *proof, '/cluster/status', '/nodes', '/cluster/resources?type=vm']
    guests = [('node-a', [100], [102]), ('node-b', [101], [])] if scenario == 'complete' else [
        ('pve1', [101], []), ('pve2', [102], []), ('pve3', [103], [])]
    for node, qemu, lxc in guests:
        network = '/nodes/' + node + '/network'
        expected.extend([network, '/nodes', network, network])
        for kind, ids in [('qemu', qemu), ('lxc', lxc)]:
            listing = '/nodes/' + node + '/' + kind
            expected.append(listing)
            if ids:
                expected.extend([listing, *[listing + '/' + str(vmid) + '/config?current=1' for vmid in ids]])
    expected.extend(['/cluster/resources?type=vm', '/nodes', '/cluster/status', *proof])
    assert calls == expected and len(calls) == count
    assert not any('storage' in path for path in calls)
    assert result[-1]['completeness'] == 'complete'
