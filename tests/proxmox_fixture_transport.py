# SPDX-License-Identifier: Apache-2.0
"""Only tests import this module. Never included in a normal candidate bundle."""
from copy import deepcopy
import json
from pathlib import Path
import time
from urllib.parse import parse_qs, urlsplit

from ansible.module_utils.atlas_transport import PinnedAdapter

FIXTURES = Path(__file__).parent / 'fixtures/proxmox'


def fixture(scenario='complete'):
    data = json.loads((FIXTURES / 'clustered.json').read_text())
    changes = json.loads((FIXTURES / 'scenarios.json').read_text())[scenario]
    responses = data['responses']
    data['failures'].update(changes.get('failures', {}))
    data['changes'].update(changes.get('changes', {}))
    if changes.get('denied'):
        path = changes['denied']
        data['acl'].append({'path': path, 'roleid': 'NoAccess', 'type': 'user', 'ugid': 'fixture-account', 'propagate': 1})
        data['permissions'][path] = {}
    if changes.get('acl_audit_missing'):
        data['permissions']['/access'] = {}
    if changes.get('unproven'):
        data['permissions']['/vms'] = {}
    if changes.get('standalone'):
        responses['/cluster/status'] = [row for row in responses['/cluster/status'] if row.get('name') == 'node-a']
        responses['/nodes'] = responses['/nodes'][:1]
        responses['/cluster/resources?type=vm'] = [row for row in responses['/cluster/resources?type=vm'] if row['node'] == 'node-a']
    if changes.get('empty_guests'):
        responses['/cluster/resources?type=vm'] = []
        responses['/nodes/node-a/qemu'] = responses['/nodes/node-a/lxc'] = []
    if changes.get('offline'):
        for row in responses['/nodes']:
            if row['node'] == changes['offline']: row['status'] = 'offline'
        for row in responses['/cluster/status']:
            if row.get('name') == changes['offline']: row['online'] = 0
    if changes.get('malformed'):
        responses['/nodes/node-a/qemu/100/config?current=1']['net0'] = 'invalid'
    if changes.get('limits'):
        responses['/nodes'] = [{'node': f'node-{index}', 'status': 'online'} for index in range(33)]
    if changes.get('rename'):
        responses['/cluster/resources?type=vm'][0]['name'] = 'renamed-vm'
        responses['/nodes/node-a/qemu'][0]['name'] = 'renamed-vm'
    if changes.get('migration'):
        responses['/cluster/resources?type=vm'][0]['node'] = 'node-b'
        responses['/nodes/node-b/qemu'].append(responses['/nodes/node-a/qemu'].pop())
        responses['/nodes/node-b/qemu/100/config?current=1'] = responses.pop('/nodes/node-a/qemu/100/config?current=1')
    data['slow'] = changes.get('slow', False)
    return data


class FixtureResponse:
    def __init__(self, data, path):
        self.status = data['failures'].get(path, 200)
        if path.startswith('/access/permissions'):
            query = parse_qs(urlsplit(path).query)
            if query.get('path'):
                key = query['path'][0]
                prefixes = [p for p in data['permissions'] if key == p or key.startswith(p.rstrip('/') + '/')]
                selected = max(prefixes, key=len, default=None)
                value = {key: deepcopy(data['permissions'][selected]) if selected else {}}
            else:
                # Real API drops zero-permission paths: exercise hidden NoAccess.
                value = {key: grants for key, grants in data['permissions'].items() if grants}
        elif path == '/access/acl':
            value = deepcopy(data['acl'])
        else:
            value = deepcopy(data['responses'][path])
        self.raw = json.dumps({'data': value, 'changes': data['changes'].get(path)}).encode()
        self.offset = 0

    def getheader(self, name, default=None):
        return str(len(self.raw)) if name == 'Content-Length' else default

    def read(self, maximum):
        result = self.raw[self.offset:self.offset + maximum]
        self.offset += len(result)
        return result


def adapter_factory(data):
    calls = []
    class Connection:
        def __init__(self, host, port, address, context, fingerprint, timeout):
            assert address == '192.168.50.2'
            self.path = None
        def request(self, method, path, headers):
            assert method == 'GET' and headers['Authorization'].startswith('PVEAPIToken=')
            self.path = path.removeprefix('/api2/json')
            calls.append(self.path)
        def getresponse(self):
            if data.get('slow') and self.path == '/cluster/status':
                (Path.cwd().parent / 'fixture.pid').write_text(str(__import__('os').getpid()))
                time.sleep(120)
            return FixtureResponse(data, self.path)
        def close(self): pass
    def build(config, deadline):
        return PinnedAdapter(config, deadline, resolver=lambda *a, **kw: [(2, 1, 6, '', ('192.168.50.2', 8006))], connection_factory=Connection)
    build.calls = calls
    return build
