# SPDX-License-Identifier: Apache-2.0
"""Candidate orchestrator; source-specific policy stays inside this Connector."""
from datetime import datetime, timezone
import importlib
import json
import logging
import os
from pathlib import Path
import re
import signal
import sys
import time

from ansible.module_utils.atlas_transport import SourceError, PinnedAdapter, secure_api, endpoint
from ansible.module_utils.atlas_normalization import Inventory, CLASSES, identifier, guest_id
from ansible.module_utils.atlas_diagnostics import Diagnostics

MAX_ROWS = 1000
MAX_NODES = 32
MAX_ACL_PATHS = 256
ROOTS = {'/': 'Sys.Audit', '/nodes': 'Sys.Audit', '/vms': 'VM.Audit',
         '/storage': 'Datastore.Audit', '/sdn/zones/localnetwork': 'SDN.Audit'}
CAPABILITIES = {'/': ('deployment', 'root'), '/nodes': ('inventory.nodes', 'inventory'),
                '/vms': ('inventory.guests', 'inventory'), '/storage': ('inventory.storage', 'inventory'),
                '/sdn/zones/localnetwork': ('topology.bridges', 'topology')}


class CapabilityError(SourceError):
    def __init__(self, capability, privilege, path_category):
        super().__init__('permission_limited')
        self.diagnostic = {'capability': capability, 'state': 'permission_limited',
                           'privilege': privilege, 'path_category': path_category}


def collection(name):
    # Only the runtime-owned installed path, never input/config/package paths.
    root = os.environ['ANSIBLE_COLLECTIONS_PATH']
    if os.pathsep in root or not Path(root).is_absolute():
        raise SourceError('source_unavailable')
    if root not in sys.path:
        sys.path.insert(0, root)
    # AnsiballZ bundles the statically imported collection module_utils package.
    # Extend that package's plugins namespace with the SAME protected installed
    # collection so its info-module implementations remain reachable as well.
    plugins = importlib.import_module('ansible_collections.community.proxmox.plugins')
    installed = str(Path(root) / 'ansible_collections/community/proxmox/plugins')
    if installed not in plugins.__path__:
        plugins.__path__.append(installed)
    return importlib.import_module('ansible_collections.community.proxmox.plugins.modules.' + name)


class SafeModule:
    def __init__(self, config, credentials):
        host, port = endpoint(config['endpoint'])
        token_id, secret = credentials['token_id'], credentials['token_secret']
        if (not isinstance(token_id, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+![A-Za-z0-9_.-]+', token_id)
                or not isinstance(secret, str) or not 1 <= len(secret) <= 2048
                or any(ord(c) <= 32 or ord(c) > 126 for c in secret)):
            raise SourceError('authentication_failed')
        user, token = token_id.split('!', 1)
        if user == 'root@pam':
            raise SourceError('authentication_failed')
        self.params = {'api_host': host, 'api_port': port, 'api_user': user, 'api_token_id': token,
                       'api_token_secret': secret, 'api_password': None, 'api_otp': None, 'ca_path': None,
                       'validate_certs': True, 'api_timeout': 6}
        self.adapter = None

    def fail_json(self, **kwargs):
        # Upstream modules attach source values/tracebacks. Discard everything.
        raise SourceError(self.adapter.last_error if self.adapter and self.adapter.last_error else 'source_unavailable')


def reader(name, classname, api, module):
    cls = getattr(collection(name), classname)
    instance = cls.__new__(cls)
    instance.proxmox_api, instance.module = api, module
    return instance


def rows(value, maximum=MAX_ROWS):
    if not isinstance(value, list) or len(value) > maximum or any(not isinstance(row, dict) for row in value):
        raise SourceError('invalid_source_record', reason='source_response_limit' if isinstance(value, list) and len(value) > maximum else 'source_response_invalid')
    return value


def permissions(api, path):
    value = api.access.permissions.get(path=path)
    if not isinstance(value, dict) or not isinstance(value.get(path, {}), dict):
        raise SourceError('invalid_source_record', reason='permission_response_invalid')
    grants = value.get(path, {})
    if any(not isinstance(key, str) or type(flag) not in {int, bool} or flag not in {0, 1} for key, flag in grants.items()):
        raise SourceError('invalid_source_record', reason='permission_flag_invalid')
    return grants


def acl_proof(api):
    """Prove propagated scope visibility AND inspect otherwise hidden ACL overrides.

    The unscoped effective-permission dump omits paths with zero permissions.
    It cannot alone rule out a hidden NoAccess guest/storage/bridge subtree.
    Sys.Audit on /access proves the ACL read is unfiltered; no write privilege.
    Raw ACL data is retained only transiently and never emitted.
    """
    if 'Sys.Audit' not in permissions(api, '/access'):
        raise CapabilityError('inventory.authorization', 'Sys.Audit', 'authorization')
    effective = api.access.permissions.get()
    if not isinstance(effective, dict) or len(effective) > MAX_ACL_PATHS:
        raise SourceError('invalid_source_record', reason='permission_response_invalid')
    acl = rows(api.access.acl.get(), MAX_ACL_PATHS)
    if not acl:
        raise SourceError('permission_limited')
    paths = set(ROOTS)
    for row in acl:
        path = row.get('path')
        if (not isinstance(path, str) or len(path) > 255 or not path.startswith('/')
                or any(c in path for c in ['?', '#', '\\']) or any(ord(c) < 33 for c in path)):
            raise SourceError('invalid_source_record', reason='acl_path_invalid')
        if any(path == root or path.startswith(root + '/') for root in ROOTS if root != '/'):
            paths.add(path)
    if len(paths) > MAX_ACL_PATHS:
        raise SourceError('invalid_source_record', reason='acl_path_limit')
    for path in sorted(paths):
        grants = permissions(api, path)
        applicable = [(root, privilege) for root, privilege in ROOTS.items()
                      if path == root or root != '/' and path.startswith(root + '/')]
        for root, privilege in applicable:
            if privilege not in grants or path == root and grants[privilege] != 1:
                capability, category = CAPABILITIES[root]
                raise CapabilityError(capability, privilege, category)
    return json.dumps([effective, sorted(acl, key=lambda row: json.dumps(row, sort_keys=True))], sort_keys=True, separators=(',', ':'))


def signature(resources):
    values = [(guest_id(row['type'], row['vmid']), identifier(row['node'])) for row in resources]
    if len(values) != len(set(key for key, node in values)) or len(resources) != len({row['vmid'] for row in resources}):
        raise SourceError('invalid_source_record', reason='duplicate_source_record')
    return sorted(values)


def node_signature(nodes):
    return sorted((identifier(row['node']), row.get('status')) for row in nodes)


def deployment_signature(status):
    return sorted(json.dumps({key: row.get(key) for key in ['type', 'name', 'id', 'nodeid', 'online', 'quorate']},
                             sort_keys=True) for row in status)


def discover(inputs, *, adapter_factory=PinnedAdapter, diagnostics=None):
    diagnostics = diagnostics or Diagnostics(debug=inputs.get('debug_enabled', False), sensitive=inputs.get('credentials', {}).values())
    inventory = Inventory(inputs.get('credentials', {}).values(), diagnostics=diagnostics)
    diagnostics.emit('accepted', 'discovery_started')
    failed = None
    version = None
    api = None
    try:
        if (inputs['selected_scopes'] != ['inventory'] or set(inputs['object_classes']) != set(CLASSES)
                or set(inputs['coverage']['domains']) != set(inventory.domains)):
            raise SourceError('invalid_source_record', reason='discovery_scope_invalid')
        deadline = time.monotonic() + max(1, min(90, inputs['timeout_seconds'] - 42))
        # Block debug output from dependencies, including raw response bodies.
        for name in ['proxmoxer', 'proxmoxer.core', 'proxmoxer.backends.https', 'urllib3', 'requests']:
            logging.getLogger(name).setLevel(logging.CRITICAL)
        collection('proxmox_cluster_status_info')
        module = SafeModule(inputs['config'], inputs['credentials'])
        module.diagnostics = diagnostics
        api = secure_api(module, inputs['config'], deadline, adapter_factory=adapter_factory)
        source = api.version.get()
        candidate = source.get('version') if isinstance(source, dict) else None
        if isinstance(candidate, str) and re.fullmatch(r'[0-9]{1,3}(?:\.[0-9]{1,3}){1,3}(?:-[0-9]{1,4})?', candidate):
            version = candidate
        else:
            inventory.warning(reason='source_version_invalid')
        try:
            diagnostics.at('authorization')
            proof = acl_proof(api)
        except SourceError as error:
            if error.code == 'authentication_failed':
                raise
            inventory.warning(error.code, reason=error.reason or 'authorization_unproven')
            proof = None
        cluster_reader = reader('proxmox_cluster_status_info', 'ProxmoxClusterStatusInfoAnsible', api, module)
        diagnostics.at('deployment')
        status = rows(cluster_reader.get_cluster_status(), MAX_NODES + 1)
        nodes = rows(api.nodes.get(), MAX_NODES)  # avoid node-info's network/version coupling
        inventory.deployment(status, nodes)
        vm_reader = reader('proxmox_vm_info', 'ProxmoxVmInfoAnsible', api, module)
        diagnostics.at('guest_resources')
        resources = rows(vm_reader.get_vms_from_cluster_resources())
        initial = signature(resources)
        storage_reader = reader('proxmox_storage_info', 'ProxmoxStorageInfoAnsible', api, module)
        definitions = {}
        try:
            diagnostics.at('storage_definition')
            definitions_list = storage_reader.get_storages()
            if len(definitions_list) > MAX_ROWS:
                raise SourceError('invalid_source_record', reason='source_response_limit')
            for item in definitions_list:
                row = item.storage
                diagnostics.at('storage_definition', object_class='proxmox.storage', external_id='storage/' + str(row.get('storage', '')))
                diagnostics.rule('storage', row.get('storage'), 'storage_definition', 'identifier')
                name = identifier(row['storage'])
                if name in definitions:
                    raise SourceError('invalid_source_record', reason='duplicate_source_record')
                if row.get('nodes') and (not isinstance(row['nodes'], list)
                        or any(identifier(node) not in inventory.nodes for node in row['nodes'])):
                    raise SourceError('invalid_source_record', reason='storage_node_unresolved')
                definitions[name] = row
        except (SourceError, ValueError, KeyError, TypeError) as error:
            inventory.warning('invalid_source_record', reason=getattr(error, 'reason', None) or 'storage_definition_invalid')
        for node in sorted(inventory.nodes):
            if not inventory.nodes[node]:
                continue
            try:
                diagnostics.at('storage_status', parent_external_id='node/' + node)
                storage = rows(api.nodes(node).storage.get())  # permitted collection gap, same session
                inventory.storage(definitions, node, storage)
            except SourceError as error:
                inventory.warning(error.code, reason=error.reason or 'storage_read_failed')
            try:
                diagnostics.at('network', parent_external_id='node/' + node)
                network_reader = reader('proxmox_node_network_info', 'ProxmoxNodeNetworkInfoAnsible', api, module)
                module.params.update(node=node, iface=None, iface_type=None, check_changes=False)
                changes = network_reader.check_network_changes(node)
                if changes is not None and not isinstance(changes, str):
                    raise SourceError('invalid_source_record', reason='network_changes_invalid')
                networks = rows(network_reader.run()['proxmox_node_networks'])
                # Changes are requested again to catch staging during network reads.
                later_changes = network_reader.check_network_changes(node)
                if later_changes is not None and not isinstance(later_changes, str):
                    raise SourceError('invalid_source_record', reason='network_changes_invalid')
                inventory.network(node, networks, pending=bool(changes or later_changes))
            except (SourceError, KeyError, TypeError) as error:
                inventory.warning(error.code if isinstance(error, SourceError) else 'invalid_source_record',
                                  reason=getattr(error, 'reason', None) or 'network_read_failed')
            for kind in ['qemu', 'lxc']:
                selected = {row['vmid']: dict(row) for row in resources if row['node'] == node and row['type'] == kind}
                try:
                    diagnostics.at('guest_config', object_class='proxmox.' + kind, parent_external_id='node/' + node)
                    # Collection skips node calls on empty resource seeds; explicitly
                    # execute every selected node/kind, including authorized empties.
                    node_guests = rows(getattr(api.nodes(node), kind).get())
                    node_ids = [guest_id(kind, row['vmid']) for row in node_guests]
                    expected_ids = [guest_id(kind, row['vmid']) for row in selected.values()]
                    if len(node_ids) != len(set(node_ids)) or set(node_ids) != set(expected_ids):
                        inventory.warning(reason='guest_inventory_mismatch')
                    enriched = vm_reader.get_vms_from_nodes(selected, kind, config='current', network=False)
                    for row in enriched.values():
                        if not isinstance(row.get('config'), dict):
                            diagnostics.at('guest_config', object_class='proxmox.' + kind, external_id='guest/' + kind + '/' + str(row.get('vmid', '')), parent_external_id='node/' + node)
                            diagnostics.rule('config', row.get('config'), 'guest_current_config', 'object')
                            inventory.warning(reason='guest_config_missing')
                        selected[row['vmid']] = row
                except (SourceError, KeyError, TypeError, ValueError) as error:
                    inventory.warning(error.code if isinstance(error, SourceError) else 'invalid_source_record',
                                      reason=getattr(error, 'reason', None) or 'guest_config_read_failed')
                for row in sorted(selected.values(), key=lambda row: row['vmid']):
                    inventory.guest(row)
        # Preserve offline guest inventory from the cluster seed with unknown topology.
        for row in resources:
            if row['node'] not in inventory.nodes or not inventory.nodes[row['node']]:
                inventory.guest(row)
        diagnostics.at('consistency')
        if (signature(rows(vm_reader.get_vms_from_cluster_resources())) != initial
                or node_signature(rows(api.nodes.get(), MAX_NODES)) != node_signature(nodes)
                or deployment_signature(rows(cluster_reader.get_cluster_status(), MAX_NODES + 1)) != deployment_signature(status)):
            inventory.warning(reason='inventory_changed_during_discovery')
        if proof is not None:
            try:
                if acl_proof(api) != proof:
                    inventory.warning('permission_limited', reason='authorization_changed_during_discovery')
            except SourceError as error:
                inventory.warning(error.code, reason=error.reason or 'authorization_recheck_failed')
    except SourceError as error:
        failed = error.code
        diagnostics.emit('error', error.reason or (inventory.reason if error.code == 'invalid_source_record' else error.code))
    except (KeyError, TypeError, ValueError, OSError, ImportError):
        failed = 'invalid_source_record'
        diagnostics.emit('error', 'discovery_stage_failed')
    finally:
        if api:
            api._store['session'].close()
    diagnostics.at('discovery')
    diagnostics.emit('accepted' if not failed else 'error', 'discovery_finished')
    return stream(inputs, inventory, version, failed)


def stream(inputs, inventory, version, failed):
    envelope = {'protocol_version': '1.0', 'connector': {'id': inputs['reference']['connector_id'],
                'version': inputs['reference']['version'], 'bundle_digest': 'sha256:' + inputs['reference']['digest']},
                'run_id': inputs['run_id'], 'integration_id': inputs['integration_id'],
                'observed_at': datetime.now(timezone.utc).isoformat(), 'coverage': inputs['coverage']}
    if version:
        envelope['source'] = {'version': version}
    messages = []
    batch = None
    for domain, values in inventory.output().items():
        for value in values:
            if batch is None:
                batch = {**envelope, 'message_type': 'observations', 'batch': {'sequence': len(messages) + 1},
                         'assets': [], 'networks': [], 'interfaces': [], 'relationships': []}
            trial = {**batch, domain: [*batch[domain], value]}
            if sum(len(batch[key]) for key in inventory.domains) >= 200 or len(json.dumps(trial).encode()) > 512 * 1024:
                messages.append(batch)
                batch = {**envelope, 'message_type': 'observations', 'batch': {'sequence': len(messages) + 1},
                         'assets': [], 'networks': [], 'interfaces': [], 'relationships': []}
            batch[domain].append(value)
    messages.append(batch or {**envelope, 'message_type': 'observations', 'batch': {'sequence': 1},
                             'assets': [], 'networks': [], 'interfaces': [], 'relationships': []})
    # A failed seal safely retains validated evidence, with no absence finalisation.
    completion = {**envelope, 'message_type': 'completion', 'last_sequence': len(messages),
                  'status': 'failed' if failed else 'completed',
                  'completeness': 'failed' if failed else 'partial' if inventory.warnings else 'complete'}
    if inventory.warnings:
        completion['warnings'] = [{'code': code} for code in sorted(inventory.warnings)]
    if failed:
        completion['errors'] = [{'code': failed}]
    messages.append(completion)
    return messages


def main(*, adapter_factory=PinnedAdapter):
    from ansible.module_utils.basic import AnsibleModule
    from atlas_connector_sdk.contracts import strict_json
    module = AnsibleModule(argument_spec={'input_file': {'type': 'path', 'required': True},
                                         'aip_file': {'type': 'path', 'required': True},
                                         'diagnostics_file': {'type': 'path'}}, supports_check_mode=False)
    descriptor = os.open(module.params['input_file'], os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, 'rb') as source:
        inputs = strict_json(source.read(128 * 1024 + 1), maximum=128 * 1024)
    diagnostics = Diagnostics.open(module.params.get('diagnostics_file'), module.params['input_file'],
        debug=inputs.get('debug_enabled', False), sensitive=inputs.get('credentials', {}).values())
    def expired(*_args):
        raise SourceError('timeout')
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(1, min(90, inputs['timeout_seconds'] - 42)))
    try:
        messages = discover(inputs, adapter_factory=adapter_factory, diagnostics=diagnostics)
    except SourceError:
        messages = stream(inputs, Inventory(), None, 'timeout')
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        diagnostics.close()
        inputs.clear()
    descriptor = os.open(module.params['aip_file'], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        for message in messages:
            output.write(json.dumps(message, separators=(',', ':'), sort_keys=True, allow_nan=False) + '\n')
    module.exit_json(changed=False)
