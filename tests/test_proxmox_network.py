# SPDX-License-Identifier: Apache-2.0
"""Bridges remain validated Interface topology, without an Asset lifecycle."""
import pytest

from ansible.module_utils.atlas_normalization import vlan_tag
from ansible.module_utils.atlas_transport import SourceError
from proxmox_fixture_transport import fixture
from test_proxmox_discovery import inputs, run
from test_proxmox_normalization import domains

HOST = 'node/node-a/interface/vmbr0'
GUEST = 'guest/lxc/102/interface/net0'
CONFIG = '/nodes/node-a/lxc/102/config?current=1'


def facts(interface):
    return {row['key']: row['value'] for row in interface['facts']}


@pytest.mark.parametrize('kind', ['bridge', 'OVSBridge'])
def test_host_bridge_is_an_owned_interface_with_explicit_network_and_ip(inputs, kind):
    data = fixture()
    data['responses']['/nodes/node-a/network'][0]['type'] = kind
    result, _ = run(inputs, data=data)
    output = domains(result)
    assert result[-1]['completeness'] == 'complete'
    host = output['interfaces'][HOST]
    assert host == {'external_id': HOST, 'object_class': 'proxmox.interface',
        'asset_external_id': 'node/node-a', 'name': 'vmbr0', 'is_primary': False,
        'network_external_id': 'network/node-a/vmbr0', 'ip_address': '10.20.0.1',
        'facts': [{'key': 'proxmox.vlan_aware', 'value_type': 'boolean', 'class': 'configuration',
                   'cardinality': 'single', 'value': True}]}
    assert output['networks']['network/node-a/vmbr0']['cidr'] == '10.20.0.0/24'
    assert {row['object_class'] for row in output['assets'].values()} == {
        'proxmox.cluster', 'proxmox.node', 'proxmox.qemu', 'proxmox.lxc'}
    assert {row['relationship_class'] for row in output['relationships'].values()} == {
        'proxmox.member_of', 'proxmox.runs_on'}


def test_guest_tag_99_mac_bridge_and_static_ip_are_explicit_topology(inputs):
    data = fixture()
    data['responses'][CONFIG]['net0'] += ',tag=99'
    result, _ = run(inputs, data=data)
    guest = domains(result)['interfaces'][GUEST]
    assert result[-1]['completeness'] == 'complete'
    assert guest['asset_external_id'] == 'guest/lxc/102' and guest['name'] == 'eth0'
    assert guest['mac_address'] == '02:00:00:00:00:01'
    assert guest['ip_address'] == '10.20.0.10'
    assert facts(guest) == {'proxmox.vlan_tag': 99, 'proxmox.bridge_name': 'vmbr0'}
    assert type(facts(guest)['proxmox.vlan_tag']) is int
    assert 'network_external_id' not in guest  # Tag alone cannot prove membership.


@pytest.mark.parametrize('suffix,expected', [('', 'network/node-a/vmbr0'), (',tag=99', None),
                                          (',trunks=100;99', None), (',tag=99,trunks=100;101', None)])
def test_static_subnet_membership_remains_fail_closed_for_tagged_and_trunked_interfaces(inputs, suffix, expected):
    data = fixture()
    data['responses'][CONFIG]['net0'] += suffix
    result, _ = run(inputs, data=data)
    guest = domains(result)['interfaces'][GUEST]
    assert result[-1]['completeness'] == 'complete'
    assert guest.get('network_external_id') == expected
    assert facts(guest)['proxmox.bridge_name'] == 'vmbr0'
    assert ('proxmox.vlan_tag' in facts(guest)) == ('tag=' in suffix)
    if 'trunks=' in suffix:
        assert facts(guest)['proxmox.vlan_trunks'] == ('99;100' if 'tag=' not in suffix else '100;101')


@pytest.mark.parametrize('ip', [None, 'dhcp', 'manual', '10.30.0.10/24'])
def test_no_inferred_dhcp_or_unmatched_network_membership(inputs, ip):
    data = fixture()
    data['responses'][CONFIG]['net0'] = 'name=eth0,bridge=vmbr0' + ('' if ip is None else ',ip=' + ip)
    result, calls = run(inputs, data=data)
    guest = domains(result)['interfaces'][GUEST]
    assert result[-1]['completeness'] == 'complete'
    assert 'network_external_id' not in guest
    assert ('ip_address' in guest) == (ip == '10.30.0.10/24')
    assert not any('/agent' in path for path in calls)


def test_bridge_without_cidr_has_interface_and_attachment_but_no_network(inputs):
    data = fixture()
    del data['responses']['/nodes/node-a/network'][0]['cidr']
    result, _ = run(inputs, data=data)
    output = domains(result)
    assert result[-1]['completeness'] == 'complete'
    assert HOST in output['interfaces']
    assert 'ip_address' not in output['interfaces'][HOST]
    assert 'network/node-a/vmbr0' not in output['networks']
    assert facts(output['interfaces'][GUEST]) == {'proxmox.bridge_name': 'vmbr0'}
    assert 'network_external_id' not in output['interfaces'][GUEST]


@pytest.mark.parametrize('value', [1, 99, 4094, '1', '99', '4094'])
def test_vlan_accepts_only_valid_integer_or_decimal_source_evidence(value):
    result = vlan_tag(value)
    assert type(result) is int and result == int(value)


@pytest.mark.parametrize('value', [True, False, 99.0, None, [], {}, 0, -1, 4095,
                                   '', '0', '-1', '4095', '99.0', '+99', ' 99', '99 ', '9e1', '\u0669\u0669', '\u00b2'])
def test_vlan_rejects_malformed_or_coerced_evidence(value):
    with pytest.raises(SourceError):
        vlan_tag(value)


@pytest.mark.parametrize('tag', ['', '0', '4095', '-1', '99.0', '+99', ' 99', 'true', '\u0669\u0669', '\u00b2'])
def test_malformed_vlan_prevents_complete_and_emits_no_guest_interface(inputs, tag):
    data = fixture()
    data['responses'][CONFIG]['net0'] += ',tag=' + tag
    result, _ = run(inputs, data=data)
    assert result[-1]['completeness'] == 'partial'
    assert {'code': 'invalid_source_record'} in result[-1]['warnings']
    assert GUEST not in domains(result)['interfaces']


@pytest.mark.parametrize('trunks', ['', '0', '99;4095', '99;99', '99;;100', '99-100', '99;private-config',
                                  ';'.join(str(value) for value in range(1, 130))])
def test_trunk_facts_are_bounded_validated_source_evidence(inputs, trunks):
    data = fixture()
    data['responses'][CONFIG]['net0'] += ',trunks=' + trunks
    result, _ = run(inputs, data=data)
    assert result[-1]['completeness'] == 'partial'
    assert GUEST not in domains(result)['interfaces']


def test_trunk_fact_has_a_safe_deterministic_maximum(inputs):
    data = fixture()
    vlans = list(range(3967, 4095))
    data['responses'][CONFIG]['net0'] += ',trunks=' + ';'.join(map(str, reversed(vlans)))
    result, _ = run(inputs, data=data)
    guest = domains(result)['interfaces'][GUEST]
    assert result[-1]['completeness'] == 'complete'
    assert facts(guest)['proxmox.vlan_trunks'] == ';'.join(map(str, vlans))
    assert len(facts(guest)['proxmox.vlan_trunks']) == 639
    assert 'network_external_id' not in guest


@pytest.mark.parametrize('bridge', ['', '../vmbr0', 'vmbr0/other', 'vmbr0\n', 'x' * 65])
@pytest.mark.parametrize('owner', ['host', 'guest'])
def test_malformed_bridge_identity_is_never_accepted(inputs, bridge, owner):
    data = fixture()
    if owner == 'host':
        data['responses']['/nodes/node-a/network'][0]['iface'] = bridge
    else:
        data['responses'][CONFIG]['net0'] = 'name=eth0,bridge=' + bridge
    result, _ = run(inputs, data=data)
    assert result[-1]['completeness'] in {'partial', 'failed'}
    assert not any(row['key'] == 'proxmox.bridge_name' for row in domains(result)['interfaces'].get(GUEST, {}).get('facts', []))


@pytest.mark.parametrize('condition', ['missing', 'inactive', 'pending', 'unavailable', 'offline', 'invalid_cidr'])
def test_guest_bridge_requires_current_applicable_node_evidence(inputs, condition):
    data = fixture('offline' if condition == 'offline' else 'complete')
    if condition == 'missing':
        data['responses']['/nodes/node-a/network'] = []  # Same name on node-b is insufficient.
    elif condition == 'inactive':
        data['responses']['/nodes/node-a/network'][0]['active'] = 0
    elif condition == 'pending':
        data['changes']['/nodes/node-a/network'] = 'staged'
    elif condition == 'unavailable':
        data['failures']['/nodes/node-a/network'] = 500
    elif condition == 'invalid_cidr':
        data['responses']['/nodes/node-a/network'][0]['cidr'] = 'invalid'
    result, calls = run(inputs, data=data)
    assert result[-1]['completeness'] == 'partial'
    output = domains(result)
    if condition == 'offline':
        assert 'node/node-b/interface/vmbr0' not in output['interfaces']
        assert '/nodes/node-b/network' not in calls
    else:
        assert HOST not in output['interfaces']
        assert 'proxmox.bridge_name' not in facts(output['interfaces'][GUEST])


@pytest.mark.parametrize('scenario,counts', [('complete', (6, 2, 5, 5)), ('heterogeneous_storage', (7, 3, 3, 6))])
def test_deterministic_fixture_observation_counts(inputs, scenario, counts):
    result, _ = run(inputs, scenario)
    assert tuple(len(rows) for rows in domains(result).values()) == counts
    assert result[-1]['completeness'] == 'complete'
