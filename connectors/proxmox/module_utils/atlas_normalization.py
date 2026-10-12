# SPDX-License-Identifier: Apache-2.0
"""Explicit current-state mapping. No payload blobs or business conclusions."""
import hashlib
import ipaddress
import json
import re

from ansible.module_utils.atlas_transport import SourceError, SEGMENT

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
        raise SourceError('invalid_source_record')
    return value


def integer(value, maximum=10**18):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise SourceError('invalid_source_record')
    return value


def flag(value):
    if value not in (0, 1, False, True) or not isinstance(value, (int, bool)):
        raise SourceError('invalid_source_record')
    return bool(value)


def fact(name, value):
    kind, classification = FACTS[name]
    return {'key': 'proxmox.' + name, 'value_type': kind, 'class': classification, 'cardinality': 'single', 'value': value}


def node_id(name):
    return 'node/' + identifier(name)


def guest_id(kind, vmid):
    if kind not in {'qemu', 'lxc'} or integer(vmid, 999999999) < 1:
        raise SourceError('invalid_source_record')
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
    def __init__(self, sensitive=(), maximum=4000):
        self.domains = {key: {} for key in ['assets', 'networks', 'interfaces', 'relationships']}
        self.warnings = set()
        self.sensitive = tuple(value for value in sensitive if value)
        self.maximum = maximum
        self.nodes, self.storages, self.bridges, self.networks = {}, {}, {}, {}
        self.mode = 'standalone'

    def warning(self, code='invalid_source_record'):
        self.warnings.add(code)

    def add(self, domain, value):
        if sum(len(rows) for rows in self.domains.values()) >= self.maximum:
            raise SourceError('invalid_source_record')
        raw = json.dumps(value, allow_nan=False)
        if any(secret in raw for secret in self.sensitive):
            raise SourceError('invalid_source_record')
        key = value['external_id']
        previous = self.domains[domain].get(key)
        if previous is not None and previous != value:
            raise SourceError('invalid_source_record')
        self.domains[domain][key] = value

    def asset(self, external_id, kind, name, facts):
        if not isinstance(name, str) or not 1 <= len(name) <= 255 or any(ord(c) < 32 or ord(c) == 127 for c in name):
            raise SourceError('invalid_source_record')
        # Source power/availability is never an Atlas lifecycle status.
        self.add('assets', {'external_id': external_id, 'object_class': 'proxmox.' + kind, 'name': name, 'facts': facts})

    def link(self, kind, source, target):
        self.add('relationships', relationship(kind, source, target))

    def deployment(self, status, nodes):
        clusters = [row for row in status if row.get('type') == 'cluster']
        members = [row for row in status if row.get('type') == 'node']
        if len(clusters) + len(members) != len(status):
            self.warning()
        if len(clusters) > 1 or len(nodes) != len({identifier(row['node']) for row in nodes}):
            raise SourceError('invalid_source_record')
        self.mode = 'clustered' if clusters else 'standalone'
        if clusters:
            self.asset('cluster/deployment', 'cluster', clusters[0]['name'], [fact('deployment_mode', self.mode)])
        elif len(nodes) != 1:
            self.warning()
        if {row.get('name') for row in members} != {row['node'] for row in nodes}:
            self.warning()
        for row in nodes:
            try:
                node = identifier(row['node'])
                online = row.get('status') == 'online'
                if row.get('status') not in {'online', 'offline'}:
                    raise SourceError('invalid_source_record')
                self.asset(node_id(node), 'node', node, [fact('deployment_mode', self.mode), fact('online', online)])
                self.nodes[node] = online
                if clusters:
                    self.link('member_of', node_id(node), 'cluster/deployment')
                if not online:
                    self.warning('source_unavailable')
            except (SourceError, KeyError, TypeError):
                self.warning()

    def storage(self, definitions, node, statuses):
        seen = set()
        for row in statuses:
            try:
                name = identifier(row['storage'])
                if name in seen:
                    raise SourceError('invalid_source_record')
                seen.add(name)
                definition = definitions[name]
                shared = flag(definition.get('shared', False))
                if 'shared' in row and flag(row['shared']) != shared:
                    raise SourceError('invalid_source_record')
                kind = identifier(definition['type'])
                if 'type' in row and row['type'] != kind:
                    raise SourceError('invalid_source_record')
                facts = [fact('shared', shared), fact('storage_type', kind)]
                # Shared totals can vary between node reads. Keep source-level inventory;
                # optional per-node capacity remains only on local pools.
                if not shared and flag(row.get('active', 0)):
                    if 'total' in row and 'avail' in row and integer(row['avail']) > integer(row['total']):
                        raise SourceError('invalid_source_record')
                    for field, source in [('capacity_bytes', 'total'), ('available_bytes', 'avail')]:
                        if source in row:
                            facts.append(fact(field, integer(row[source])))
                external = storage_id(node, name, shared)
                self.asset(external, 'storage', name, facts)
                self.storages[(node, name)] = external
            except (SourceError, KeyError, TypeError):
                self.warning()
        expected = {name for name, row in definitions.items() if not row.get('nodes') or node in row['nodes']}
        if seen != expected:
            self.warning()

    def network(self, node, rows, pending=False):
        if pending:
            self.warning()
            return  # list configuration can be staged even if device is active
        seen = set()
        for row in rows:
            try:
                kind = identifier(row['type'])
                name = identifier(row['iface'])
                if kind == 'unknown':
                    self.warning()
                if kind not in {'bridge', 'OVSBridge'}:
                    continue
                if name in seen:
                    raise SourceError('invalid_source_record')
                seen.add(name)
                active = flag(row.get('active', False))
                external = bridge_id(node, name)
                facts = [fact('vlan_aware', flag(row['bridge_vlan_aware']))] if 'bridge_vlan_aware' in row else []
                self.asset(external, 'bridge', name, facts)
                if not active:
                    # Keep the known configured identity; unavailable current
                    # device topology cannot justify a complete absence scan.
                    self.warning('source_unavailable')
                    continue
                self.bridges[(node, name)] = external
                self.link('connected_to', node_id(node), external)
                interface = {'external_id': node_id(node) + '/interface/' + name, 'object_class': 'proxmox.interface',
                             'asset_external_id': node_id(node), 'name': name, 'is_primary': False, 'facts': []}
                # A currently configured subnet is explicit evidence. Identity remains
                # source/node/bridge local; never merge across nodes by name or CIDR.
                if row.get('cidr'):
                    address = ipaddress.ip_interface(row['cidr'])
                    network = 'network/' + identifier(node) + '/' + name
                    self.add('networks', {'external_id': network, 'object_class': 'proxmox.network',
                                         'name': name, 'network_type': 'lan', 'cidr': str(address.network), 'facts': []})
                    self.networks[(node, name)] = network
                    interface.update(network_external_id=network, ip_address=str(address.ip))
                self.add('interfaces', interface)
            except (SourceError, KeyError, TypeError, ValueError):
                self.warning()

    def guest(self, row):
        try:
            kind, vmid, node = row['type'], row['vmid'], identifier(row['node'])
            external = guest_id(kind, vmid)
            if node not in self.nodes:
                raise SourceError('invalid_source_record')
            facts = [fact('vmid', vmid), fact('template', flag(row.get('template', 0)))]
            state = row.get('status')
            if state in {'running', 'stopped', 'paused'}:
                facts.append(fact('power_state', state))
            else:
                self.warning()
            self.asset(external, kind, row.get('name') or external, facts)
            self.link('runs_on', external, node_id(node))
            config = row.get('config')
            if not isinstance(config, dict):
                self.warning()
                return
            for key, value in sorted(config.items()):
                if re.fullmatch(r'(?:ide|sata|scsi|virtio|mp)\d{1,2}|rootfs', key):
                    if not isinstance(value, str) or len(value) > 8192:
                        self.warning(); continue
                    volume = value.split(',', 1)[0]
                    if volume in {'none', 'cdrom'} or volume.startswith('/'):
                        continue  # no mount contents/host paths ingested
                    if ':' not in volume:
                        self.warning(); continue
                    storage = volume.split(':', 1)[0]
                    target = self.storages.get((node, storage))
                    if target:
                        self.link('uses_storage', external, target)
                    else:
                        self.warning()
                elif re.fullmatch(r'net\d{1,2}', key):
                    self.guest_interface(external, node, key, value)
        except (SourceError, KeyError, TypeError, ValueError):
            self.warning()

    def guest_interface(self, owner, node, slot, value):
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
                if not re.fullmatch(r'(?:[a-fA-F0-9]{2}:){5}[a-fA-F0-9]{2}', mac):
                    raise SourceError('invalid_source_record')
                result['mac_address'] = mac.lower()
            if fields.get('ip') not in {None, 'dhcp', 'manual'}:
                address = ipaddress.ip_interface(fields['ip'])
                result['ip_address'] = str(address.ip)
                guest_subnet = str(address.network)
            tag = fields.get('tag')
            if tag is not None:
                if not tag.isdigit() or not 1 <= int(tag) <= 4094:
                    raise SourceError('invalid_source_record')
                result['facts'].append(fact('vlan_tag', int(tag)))
            bridge = fields.get('bridge')
            if bridge:
                bridge = identifier(bridge)
                target = self.bridges.get((node, bridge))
                if target:
                    self.link('connected_to', owner, target)
                    network = self.networks.get((node, bridge))
                    if (tag is None and not fields.get('trunks') and network and guest_subnet
                            and self.domains['networks'][network]['cidr'] == guest_subnet):
                        result['network_external_id'] = network
                else:
                    self.warning()
            self.add('interfaces', result)
        except (SourceError, KeyError, TypeError, ValueError):
            self.warning()

    def output(self):
        return {domain: [rows[key] for key in sorted(rows)] for domain, rows in self.domains.items()}
