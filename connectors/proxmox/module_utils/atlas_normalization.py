# SPDX-License-Identifier: Apache-2.0
"""Explicit current-state mapping. No payload blobs or business conclusions."""
import hashlib
import ipaddress
import json
import re

from ansible.module_utils.atlas_transport import SourceError, SEGMENT
from ansible.module_utils.atlas_diagnostics import Diagnostics

CLASSES = ['proxmox.' + name for name in ['cluster', 'node', 'qemu', 'lxc', 'storage', 'bridge', 'network', 'interface']]
FACTS = {
    'vmid': ('integer', 'identity'), 'template': ('boolean', 'configuration'),
    'deployment_mode': ('string', 'informational'), 'power_state': ('string', 'operational'),
    'online': ('boolean', 'operational'), 'storage_type': ('string', 'configuration'),
    'shared': ('boolean', 'configuration'), 'capacity_bytes': ('integer', 'operational'),
    'available_bytes': ('integer', 'operational'), 'vlan_aware': ('boolean', 'configuration'),
    'vlan_tag': ('integer', 'configuration'),
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


def storage_id(node, name, shared):
    return 'storage/shared/' + identifier(name) if shared else 'storage/local/' + identifier(node) + '/' + identifier(name)


def bridge_id(node, name):
    return 'bridge/' + identifier(node) + '/' + identifier(name)


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
        self.nodes, self.storages, self.bridges, self.networks = {}, {}, {}, {}
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

    def storage(self, definitions, node, statuses):
        expected = {name for name, row in definitions.items() if not row.get('nodes') or node in row['nodes']}
        seen, encountered = set(), set()
        for row in statuses:
            self.at('storage_status', object_class='proxmox.storage', parent_external_id=node_id(node),
                    external_id='storage/' + str(row.get('storage', '')))
            try:
                self.check('storage_identity_invalid', 'storage', row.get('storage'), 'identifier')
                name = identifier(row['storage'])
                if name in encountered:
                    self.reason = 'duplicate_source_record'
                    raise SourceError('invalid_source_record')
                encountered.add(name)
                if name not in expected:
                    # Proxmox can expose disabled/inactive rows on nodes where
                    # a pool is not configured. Both flags must explicitly prove
                    # this exclusion; missing or malformed evidence fails closed.
                    self.check('storage_status_invalid', 'enabled', row.get('enabled'), 'boolean')
                    enabled = flag(row['enabled']) if 'enabled' in row else None
                    self.check('storage_status_invalid', 'active', row.get('active'), 'boolean')
                    active = flag(row['active']) if 'active' in row else None
                    if enabled is False and active is False:
                        self.diagnostics.rule('storage', name, 'inactive_disabled_without_applicable_definition', 'out_of_scope')
                        self.diagnostics.emit('skipped', 'storage_record_out_of_scope', record_count=1, action='skip')
                        continue
                    self.check('storage_definition_missing', 'storage', name, 'applicable_definition')
                    raise SourceError('invalid_source_record')
                seen.add(name)
                self.check('storage_definition_missing', 'storage', name, 'known_storage')
                definition = definitions[name]
                self.check('storage_definition_invalid', 'shared', definition.get('shared', False), 'boolean')
                shared = flag(definition.get('shared', False))
                if 'shared' in row and flag(row['shared']) != shared:
                    self.check('storage_definition_mismatch', 'shared', row['shared'], 'matching_definition')
                    raise SourceError('invalid_source_record')
                kind = identifier(definition['type'])
                if 'type' in row and row['type'] != kind:
                    self.check('storage_definition_mismatch', 'type', row['type'], 'matching_definition')
                    raise SourceError('invalid_source_record')
                facts = [fact('shared', shared), fact('storage_type', kind)]
                self.check('storage_status_invalid', 'active', row.get('active', 0), 'boolean')
                # Shared totals can vary between node reads. Keep source-level inventory;
                # optional per-node capacity remains only on local pools.
                if not shared and flag(row.get('active', 0)):
                    self.check('storage_capacity_invalid', 'avail', row.get('avail'), 'capacity_range')
                    if 'total' in row and 'avail' in row and integer(row['avail']) > integer(row['total']):
                        self.check('storage_capacity_invalid', 'avail', row['avail'], 'capacity_range')
                        raise SourceError('invalid_source_record')
                    for field, source in [('capacity_bytes', 'total'), ('available_bytes', 'avail')]:
                        if source in row:
                            self.check('storage_capacity_invalid', source, row[source], 'nonnegative_integer')
                            facts.append(fact(field, integer(row[source])))
                external = storage_id(node, name, shared)
                self.asset(external, 'storage', name, facts)
                self.storages[(node, name)] = external
                self.accepted()
            except (SourceError, KeyError, TypeError):
                self.warning(reason=self.reason)
                self.diagnostics.emit('skipped', 'source_record_rejected', record_count=1)
        if seen != expected:
            self.at('storage_status', parent_external_id=node_id(node))
            self.warning(reason='storage_inventory_mismatch')

    def network(self, node, rows, pending=False):
        self.at('network', parent_external_id=node_id(node))
        if pending:
            self.warning(reason='network_changes_pending')
            return  # list configuration can be staged even if device is active
        seen = set()
        for row in rows:
            self.at('network', object_class='proxmox.bridge', parent_external_id=node_id(node),
                    external_id='bridge/' + node + '/' + str(row.get('iface', '')))
            try:
                self.check('network_identity_invalid', 'type', row.get('type'), 'identifier')
                kind = identifier(row['type'])
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
                external = bridge_id(node, name)
                facts = [fact('vlan_aware', flag(row['bridge_vlan_aware']))] if 'bridge_vlan_aware' in row else []
                self.asset(external, 'bridge', name, facts)
                if not active:
                    # Keep the known configured identity; unavailable current
                    # device topology cannot justify a complete absence scan.
                    self.warning('source_unavailable', reason='bridge_inactive')
                    self.accepted()
                    continue
                self.bridges[(node, name)] = external
                self.link('connected_to', node_id(node), external)
                interface = {'external_id': node_id(node) + '/interface/' + name, 'object_class': 'proxmox.interface',
                             'asset_external_id': node_id(node), 'name': name, 'is_primary': False, 'facts': []}
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
                if re.fullmatch(r'(?:ide|sata|scsi|virtio|mp)\d{1,2}|rootfs', key):
                    self.at('guest_storage', object_class='proxmox.' + kind, external_id=external, parent_external_id=node_id(node))
                    self.check('guest_storage_reference_invalid', key, value, 'storage_reference')
                    if not isinstance(value, str) or len(value) > 8192:
                        self.warning(reason='guest_storage_reference_invalid'); continue
                    volume = value.split(',', 1)[0]
                    if volume in {'none', 'cdrom'} or volume.startswith('/'):
                        continue  # no mount contents/host paths ingested
                    if ':' not in volume:
                        self.warning(reason='guest_storage_reference_invalid'); continue
                    storage = volume.split(':', 1)[0]
                    target = self.storages.get((node, storage))
                    if target:
                        self.link('uses_storage', external, target)
                    else:
                        self.warning(reason='guest_storage_unresolved')
                elif re.fullmatch(r'net\d{1,2}', key):
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
                if not tag.isdigit() or not 1 <= int(tag) <= 4094:
                    raise SourceError('invalid_source_record')
                result['facts'].append(fact('vlan_tag', int(tag)))
            bridge = fields.get('bridge')
            if bridge:
                self.check('guest_bridge_invalid', 'bridge', bridge, 'identifier')
                bridge = identifier(bridge)
                target = self.bridges.get((node, bridge))
                if target:
                    self.link('connected_to', owner, target)
                    network = self.networks.get((node, bridge))
                    if (tag is None and not fields.get('trunks') and network and guest_subnet
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
