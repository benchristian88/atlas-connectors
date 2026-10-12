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
from ansible.module_utils.atlas_normalization import CLASSES

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from build_bundle import build
from proxmox_fixture_transport import fixture, adapter_factory


@pytest.fixture
def inputs():
    return {'reference': {'connector_id': 'proxmox', 'version': '0.2.0-i4b.1', 'digest': build(candidate=True)[1]['distribution']['bundle_digest'][7:]},
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
    for path,field in [('/storage','shared'),('/nodes/node-a/qemu','template'),('/nodes/node-a/network','bridge_vlan_aware')]:
        data=fixture(); data['responses'][path][0][field]=2
        result,_=run(inputs,data=data)
        assert result[-1]['completeness'] in {'partial','failed'}


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
