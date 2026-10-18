# SPDX-License-Identifier: Apache-2.0
from copy import deepcopy

from ansible.module_utils.atlas_normalization import node_id, guest_id, Inventory
from test_proxmox_discovery import inputs, run
from proxmox_fixture_transport import fixture


def domains(result):
    return {key: {row['external_id']: row for batch in result[:-1] for row in batch[key]} for key in ['assets','networks','interfaces','relationships']}


def test_rename_migration_endpoint_edit_and_order_preserve_guest_identity(inputs):
    original = domains(run(inputs)[0])
    renamed = domains(run(inputs, 'renamed')[0])
    migrated = domains(run(inputs, 'migrated')[0])
    key = guest_id('qemu', 100)
    assert key in original['assets'] and key in renamed['assets'] and key in migrated['assets']
    assert renamed['assets'][key]['name'] == 'renamed-vm'
    assert key + '/interface/net0' in migrated['interfaces']
    moved = [row for row in migrated['relationships'].values() if row['source']['external_id'] == key and row['relationship_class'] == 'proxmox.runs_on']
    assert moved[0]['target']['external_id'] == node_id('node-b')
    changed = deepcopy(inputs); changed['config']['endpoint'] = 'https://different.example.test:8006'
    assert set(domains(run(changed)[0])['assets']) == set(original['assets'])
    data = fixture()
    for value in data['responses'].values():
        if isinstance(value, list): value.reverse()
    assert domains(run(inputs, data=data)[0]) == original


def test_existing_network_interface_and_duplicate_mac_identity(inputs):
    output = domains(run(inputs)[0])
    interfaces = [row for row in output['interfaces'].values() if row.get('mac_address') == '02:00:00:00:00:01']
    assert len(interfaces) == len({row['external_id'] for row in interfaces}) == 3
    assert len(output['networks']) == 2  # same name AND CIDR do not merge node segments
    tagged = output['interfaces']['guest/qemu/101/interface/net0']
    assert 'network_external_id' not in tagged
    assert tagged['facts'][0]['value'] == 22
    assert output['interfaces']['guest/lxc/102/interface/net0']['network_external_id'] == 'network/node-a/vmbr0'


def test_standalone_has_no_fake_cluster_and_node_rename_limitation_is_explicit(inputs):
    output = domains(run(inputs, 'standalone')[0])
    assert not any(row['object_class'] == 'proxmox.cluster' for row in output['assets'].values())
    assert node_id('old-node') != node_id('new-node')
    assert 'node/node-a' in output['assets']
    clustered = domains(run(inputs)[0])
    assert set(output['assets']) <= set(clustered['assets'])


def test_limits_malformed_facts_and_credential_echo_never_allow_complete():
    inventory = Inventory(maximum=1)
    inventory.deployment([{'type':'node','name':'a'}], [{'node':'a','status':'online'}])
    inventory.network('a', [{'type':'bridge','iface':'vmbr0','active':1}])
    assert inventory.warnings
    inventory = Inventory(sensitive=('generated-sensitive-marker',))
    inventory.deployment([{'type':'node','name':'a'}], [{'node':'a','status':'online'}])
    inventory.guest({'type':'qemu','vmid':100,'node':'a','name':'generated-sensitive-marker','status':'running','config':{}})
    assert 'guest/qemu/100' not in inventory.domains['assets'] and inventory.warnings


def test_guest_network_membership_requires_explicit_matching_static_subnet_and_no_trunk(inputs):
    original=domains(run(inputs)[0])
    assert 'network_external_id' not in original['interfaces']['guest/qemu/100/interface/net0']
    for extra in [',trunks=22;23',',tag=22']:
        data=fixture(); data['responses']['/nodes/node-a/lxc/102/config?current=1']['net0']+=extra
        result=domains(run(inputs,data=data)[0])
        assert 'network_external_id' not in result['interfaces']['guest/lxc/102/interface/net0']
    data=fixture(); data['responses']['/nodes/node-a/lxc/102/config?current=1']['net0']=data['responses']['/nodes/node-a/lxc/102/config?current=1']['net0'].replace('10.20.0.10/24','10.30.0.10/24')
    result=domains(run(inputs,data=data)[0])
    assert 'network_external_id' not in result['interfaces']['guest/lxc/102/interface/net0']
