# SPDX-License-Identifier: Apache-2.0
"""Explicit current-state mapping. No payload blobs or business conclusions."""
import hashlib
import ipaddress
import json
import re

from ansible.module_utils.atlas_transport import SourceError, SEGMENT
from ansible.module_utils.atlas_diagnostics import Diagnostics

CLASSES = ['proxmox.' + name for name in ['cluster', 'node', 'qemu', 'lxc', 'network', 'interface']]
FACTS = {
    'vmid': ('integer', 'identity'), 'template': ('boolean', 'configuration'),
    'deployment_mode': ('string', 'informational'), 'power_state': ('string', 'operational'),
    'online': ('boolean', 'operational'), 'vlan_aware': ('boolean', 'configuration'),
    'vlan_tag': ('integer', 'configuration'), 'bridge_name': ('string', 'configuration'),
    'vlan_trunks': ('string', 'configuration'),
}


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(SEGMENT, value):
        raise SourceError('invalid_source_record', reason='identifier_invalid')
    return value


def integer(value, maximum=10**18):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise SourceError('invalid_source_record', reason='integer_invalid')
    return value


def flag(value):
    if value not in (0, 1, False, True) or not isinstance(value, (int, bool)):
        raise SourceError('invalid_source_record', reason='boolean_invalid')
    return bool(value)


def fact(name, value):
    kind, classification = FACTS[name]
    return {'key': 'proxmox.' + name, 'value_type': kind, 'class': classification, 'cardinality': 'single', 'value': value}


def node_id(name):
    return 'node/' + identifier(name)


def guest_id(kind, vmid):
    if kind not in {'qemu', 'lxc'} or integer(vmid, 999999999) < 1:
        raise SourceError('invalid_source_record', reason='guest_identity_invalid')
    return 'guest/' + kind + '/' + str(vmid)


def vlan_tag(value):
    # Config values are decimal strings; never coerce booleans, floats,
    # whitespace, signs or Unicode numerals into topology evidence.
    if isinstance(value, str):
        if not re.fullmatch(r'[0-9]{1,4}', value):
            raise SourceError('invalid_source_record', reason='vlan_tag_invalid')
        value = int(value)
    if integer(value, 4094) < 1:
        raise SourceError('invalid_source_record', reason='vlan_tag_invalid')
    return value


def relationship(kind, source, target):
    # Length-safe, ordered semantic inputs; display labels and array order excluded.
    identity = hashlib.sha256(json.dumps([kind, source, target], separators=(',', ':')).encode()).hexdigest()
    return {'external_id': 'relationship/' + identity, 'relationship_class': 'proxmox.' + kind,
            'source': {'kind': 'asset', 'external_id': source}, 'target': {'kind': 'asset', 'external_id': target},
            'truth_classification': 'observed', 'confidence': 1.0}


class Inventory:
    def __init__(self, sensitive=(), maximum=4000, diagnostics=None):
        self.domains = {key: {} for key in ['assets', 'networks', 'interfaces', 'relationships']}
        self.warnings = set()
        self.sensitive = tuple(value for value in sensitive if value)
        self.maximum = maximum
        self.nodes, self.bridges, self.networks = {}, set(), {}
        self.mode = 'standalone'
        self.diagnostics = diagnostics or Diagnostics(sensitive=sensitive)
        self.reason = 'normalization_invalid'

    def at(self, stage, **context):
        self.diagnostics.at(stage, **context)
        self.reason = stage + '_invalid'

    def check(self, reason, field, value, expected, *, rule=None):
        self.reason = reason
        self.diagnostics.rule(field, value, rule or reason, expected)

    def accepted(self):
        self.diagnostics.emit('accepted', 'source_record_accepted', record_count=1)

    def warning(self, code='invalid_source_record', *, reason=None):
        self.diagnostics.emit('warning', reason or self.reason)
        self.warnings.add(code)

    def add(self, domain, value):
        if sum(len(rows) for rows in self.domains.values()) >= self.maximum:
            self.reason = 'observation_limit'
            raise SourceError('invalid_source_record')
        raw = json.dumps(value, allow_nan=False)
        if any(secret in raw for secret in self.sensitive):
            self.reason = 'sensitive_material_rejected'
            raise SourceError('invalid_source_record')
        key = value['external_id']
        previous = self.domains[domain].get(key)
        if previous is not None and previous != value:
            self.reason = 'duplicate_observation'
            raise SourceError('invalid_source_record')
        self.domains[domain][key] = value

    def asset(self, external_id, kind, name, facts):
        if not isinstance(name, str) or not 1 <= len(name) <= 255 or any(ord(c) < 32 or ord(c) == 127 for c in name):
            self.check('object_name_invalid', 'name', name, 'bounded_string')
            raise SourceError('invalid_source_record')
        # Source power/availability is never an Atlas lifecycle status.
        self.add('assets', {'external_id': external_id, 'object_class': 'proxmox.' + kind, 'name': name, 'facts': facts})

    def link(self, kind, source, target):
        self.add('relationships', relationship(kind, source, target))

    def deployment(self, status, nodes):
        self.at('deployment')
        clusters = [row for row in status if row.get('type') == 'cluster']
        members = [row for row in status if row.get('type') == 'node']
        if len(clusters) + len(members) != len(status):
            self.warning(reason='deployment_record_unknown')
        if len(clusters) > 1 or len(nodes) != len({identifier(row['node']) for row in nodes}):
            self.reason = 'duplicate_source_record'
            raise SourceError('invalid_source_record')
        self.mode = 'clustered' if clusters else 'standalone'
        if clusters:
            self.asset('cluster/deployment', 'cluster', clusters[0]['name'], [fact('deployment_mode', self.mode)])
        elif len(nodes) != 1:
            self.warning(reason='standalone_node_count_invalid')
        if {row.get('name') for row in members} != {row['node'] for row in nodes}:
            self.warning(reason='node_membership_mismatch')
        for row in nodes:
            self.at('node_status', object_class='proxmox.node', external_id='node/' + str(row.get('node', '')))
            try:
                self.check('node_identity_invalid', 'node', row.get('node'), 'identifier')
                node = identifier(row['node'])
                online = row.get('status') == 'online'
                self.check('node_status_invalid', 'status', row.get('status'), 'power_state')
                if row.get('status') not in {'online', 'offline'}:
                    raise SourceError('invalid_source_record')
                self.asset(node_id(node), 'node', node, [fact('deployment_mode', self.mode), fact('online', online)])
                self.nodes[node] = online
                if clusters:
                    self.link('member_of', node_id(node), 'cluster/deployment')
                if not online:
                    self.warning('source_unavailable', reason='node_not_visible')
                self.accepted()
            except (SourceError, KeyError, TypeError):
                self.warning(reason=self.reason)
                self.diagnostics.emit('skipped', 'source_record_rejected', record_count=1)

    def network(self, node, rows, pending=False):
        self.at('network', parent_external_id=node_id(node))
        if pending:
            self.warning(reason='network_changes_pending')
            return  # list configuration can be staged even if device is active
        seen = set()
        for row in rows:
            self.at('network', object_class='proxmox.interface', parent_external_id=node_id(node),
                    external_id=node_id(node) + '/interface/' + str(row.get('iface', '')))
            try:
                self.check('network_identity_invalid', 'type', row.get('type'), 'identifier')
                kind = identifier(row['type'])
                self.check('bridge_identity_invalid', 'iface', row.get('iface'), 'identifier')
                name = identifier(row['iface'])
                if kind == 'unknown':
                    self.warning(reason='network_type_unknown')
                if kind not in {'bridge', 'OVSBridge'}:
                    self.diagnostics.emit('skipped', 'network_record_out_of_scope', record_count=1)
                    continue
                if name in seen:
                    self.reason = 'bridge_duplicate'
                    raise SourceError('invalid_source_record')
                seen.add(name)
                self.check('bridge_status_invalid', 'active', row.get('active', False), 'boolean')
                active = flag(row.get('active', False))
                facts = [fact('vlan_aware', flag(row['bridge_vlan_aware']))] if 'bridge_vlan_aware' in row else []
                if not active:
                    # Unavailable current device topology cannot justify a
                    # complete absence scan or a validated guest attachment.
                    self.warning('source_unavailable', reason='bridge_inactive')
                    self.accepted()
                    continue
                interface = {'external_id': node_id(node) + '/interface/' + name, 'object_class': 'proxmox.interface',
                             'asset_external_id': node_id(node), 'name': name, 'is_primary': False, 'facts': facts}
                # A currently configured subnet is explicit evidence. Identity remains
                # source/node/bridge local; never merge across nodes by name or CIDR.
                if row.get('cidr'):
                    self.check('bridge_cidr_invalid', 'cidr', row['cidr'], 'ip_interface')
                    address = ipaddress.ip_interface(row['cidr'])
                    network = 'network/' + identifier(node) + '/' + name
                    self.add('networks', {'external_id': network, 'object_class': 'proxmox.network',
                                         'name': name, 'network_type': 'lan', 'cidr': str(address.network), 'facts': []})
                    self.networks[(node, name)] = network
                    interface.update(network_external_id=network, ip_address=str(address.ip))
                self.add('interfaces', interface)
                self.bridges.add((node, name))
                self.accepted()
            except (SourceError, KeyError, TypeError, ValueError):
                self.warning(reason=self.reason)
                self.diagnostics.emit('skipped', 'source_record_rejected', record_count=1)

    def guest(self, row):
        self.at('guest', object_class='proxmox.' + str(row.get('type', '')),
                external_id='guest/' + str(row.get('type', '')) + '/' + str(row.get('vmid', '')),
                parent_external_id='node/' + str(row.get('node', '')))
        try:
            self.check('guest_identity_invalid', 'vmid', row.get('vmid'), 'guest_identity')
            kind, vmid, node = row['type'], row['vmid'], identifier(row['node'])
            external = guest_id(kind, vmid)
            if node not in self.nodes:
                self.reason = 'guest_node_unresolved'
                raise SourceError('invalid_source_record')
            self.check('guest_template_invalid', 'template', row.get('template', 0), 'boolean')
            facts = [fact('vmid', vmid), fact('template', flag(row.get('template', 0)))]
            state = row.get('status')
            if state in {'running', 'stopped', 'paused'}:
                facts.append(fact('power_state', state))
            else:
                self.check('guest_power_state_invalid', 'status', state, 'power_state')
                self.warning(reason='guest_power_state_invalid')
            self.asset(external, kind, row.get('name') or external, facts)
            self.link('runs_on', external, node_id(node))
            self.accepted()
            config = row.get('config')
            if not isinstance(config, dict):
                self.check('guest_config_missing', 'config', config, 'object')
                self.warning(reason='guest_config_missing')
                return
            for key, value in sorted(config.items()):
                # Storage volumes, mounts and arbitrary config are outside the
                # MVP contract. Only bounded network-interface fields are parsed.
                if re.fullmatch(r'net\d{1,2}', key):
                    self.guest_interface(external, node, key, value)
        except (SourceError, KeyError, TypeError, ValueError):
            self.warning(reason=self.reason)

    def guest_interface(self, owner, node, slot, value):
        self.at('guest_interface', object_class='proxmox.interface', external_id=owner + '/interface/' + slot,
                parent_external_id=node_id(node))
        self.check('guest_interface_invalid', slot, value, 'bounded_string', rule='guest_interface_config')
        try:
            if not isinstance(value, str) or len(value) > 8192:
                raise SourceError('invalid_source_record')
            pairs = [part.split('=', 1) for part in value.split(',')]
            if any(len(pair) != 2 for pair in pairs) or len({pair[0] for pair in pairs}) != len(pairs):
                raise SourceError('invalid_source_record')
            fields = dict(pairs)
            name = identifier(fields.get('name', slot))
            result = {'external_id': owner + '/interface/' + slot, 'object_class': 'proxmox.interface',
                      'asset_external_id': owner, 'name': name, 'is_primary': False, 'facts': []}
            guest_subnet = None
            mac = fields.get('hwaddr')
            if mac is None:
                mac = next((fields.get(model) for model in ['virtio', 'e1000', 'e1000e', 'rtl8139', 'vmxnet3'] if fields.get(model)), None)
            if mac:
                self.check('guest_mac_invalid', 'hwaddr', mac, 'mac_address')
                if not re.fullmatch(r'(?:[a-fA-F0-9]{2}:){5}[a-fA-F0-9]{2}', mac):
                    raise SourceError('invalid_source_record')
                result['mac_address'] = mac.lower()
            if fields.get('ip') not in {None, 'dhcp', 'manual'}:
                self.check('guest_ip_invalid', 'ip', fields['ip'], 'ip_interface')
                address = ipaddress.ip_interface(fields['ip'])
                result['ip_address'] = str(address.ip)
                guest_subnet = str(address.network)
            tag = fields.get('tag')
            if tag is not None:
                self.check('vlan_tag_invalid', 'tag', tag, 'vlan_1_4094')
                result['facts'].append(fact('vlan_tag', vlan_tag(tag)))
            trunks = fields.get('trunks')
            if trunks is not None:
                self.check('vlan_trunks_invalid', 'trunks', trunks, 'vlan_list_1_4094_max128')
                values = trunks.split(';')
                if len(values) > 128:
                    raise SourceError('invalid_source_record')
                vlans = [vlan_tag(value) for value in values]
                if len(vlans) != len(set(vlans)):
                    raise SourceError('invalid_source_record')
                # A single bounded scalar avoids introducing multi-value
                # assertion semantics; never retain arbitrary config text.
                result['facts'].append(fact('vlan_trunks', ';'.join(str(value) for value in sorted(vlans))))
            bridge = fields.get('bridge')
            if bridge is not None:
                self.check('guest_bridge_invalid', 'bridge', bridge, 'identifier')
                bridge = identifier(bridge)
                if (node, bridge) in self.bridges:
                    result['facts'].append(fact('bridge_name', bridge))
                    network = self.networks.get((node, bridge))
                    if (tag is None and trunks is None and network and guest_subnet
                            and self.domains['networks'][network]['cidr'] == guest_subnet):
                        result['network_external_id'] = network
                else:
                    self.warning(reason='guest_bridge_unresolved')
            self.add('interfaces', result)
            self.accepted()
        except (SourceError, KeyError, TypeError, ValueError):
            self.warning(reason=self.reason)
            self.diagnostics.emit('skipped', 'source_record_rejected', record_count=1)

    def output(self):
        return {domain: [rows[key] for key in sorted(rows)] for domain, rows in self.domains.items()}
