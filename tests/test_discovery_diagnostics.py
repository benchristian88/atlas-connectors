# SPDX-License-Identifier: Apache-2.0
"""Diagnostic visibility must never change the discovered knowledge or scope."""
from copy import deepcopy
import json
import os
from pathlib import Path
import secrets
import uuid

import pytest
from ansible.module_utils.atlas_diagnostics import Diagnostics, MAX_EVENT_BYTES
from ansible.module_utils.atlas_discovery import discover
from ansible.module_utils.atlas_normalization import CLASSES
from proxmox_fixture_transport import fixture, adapter_factory


def inputs():
    version = json.loads((Path(__file__).resolve().parents[1] / 'connectors/proxmox/candidate/manifest.json').read_text())['version']
    return {'reference': {'connector_id': 'proxmox', 'version': version, 'digest': 'a' * 64},
            'config': {'endpoint': 'https://source.example.test:8006'},
            'credentials': {'token_id': 'fixture_' + secrets.token_hex(8) + '@pve!discovery', 'token_secret': secrets.token_urlsafe(32)},
            'run_id': str(uuid.uuid4()), 'integration_id': str(uuid.uuid4()), 'selected_scopes': ['inventory'], 'object_classes': CLASSES,
            'timeout_seconds': 120, 'coverage': {'key': 'fixture:inventory', 'snapshot_mode': 'full', 'domains': ['assets', 'networks', 'interfaces', 'relationships']}}


@pytest.mark.parametrize('scenario', ['complete', 'network_topology', 'standalone', 'empty_authorized', 'empty_unproven', 'permission_filtered',
    'offline', 'source_failure', 'storage_failure', 'config_failure', 'pending', 'malformed', 'limits', 'heterogeneous_storage'])
def test_debug_only_changes_diagnostic_detail_not_aip_or_source_calls(scenario):
    source = inputs()
    messages, traces, calls = [], [], []
    for debug in [False, True]:
        diagnostics = Diagnostics(debug=debug, sensitive=source['credentials'].values())
        adapter = adapter_factory(fixture(scenario))
        output = discover({**source, 'debug_enabled': debug}, adapter_factory=adapter, diagnostics=diagnostics)
        for row in output:
            row.pop('observed_at')
        messages.append(output); calls.append(adapter.calls); traces.append(diagnostics.events)
    assert messages[0] == messages[1]
    assert calls[0] == calls[1]
    assert not any('storage' in path for path in calls[0])
    assert not any('storage' in json.dumps(event) for trace in traces for event in trace)
    assert not any(event.get('object_class') == 'proxmox.bridge' for trace in traces for event in trace)
    assert all(row['reason_code'] != 'invalid_source_record' for row in traces[0])
    assert [{k: v for k, v in row.items() if k not in {'field', 'encountered_type', 'validation_rule', 'expected', 'action'}}
            for row in traces[1]] == traces[0]
    if messages[0][-1]['completeness'] != 'complete':
        assert any(row['result'] in {'warning', 'error'} for row in traces[0])
    assert all(len(json.dumps(row, separators=(',', ':')).encode()) + 1 <= MAX_EVENT_BYTES for row in traces[1])


@pytest.mark.parametrize('mutation,reason', [
    ('interface', 'guest_interface_invalid'), ('ip', 'guest_ip_invalid'), ('tag', 'vlan_tag_invalid'),
    ('cidr', 'bridge_cidr_invalid'), ('inactive', 'bridge_inactive'), ('boolean', 'source_boolean_invalid'),
    ('power', 'guest_power_state_invalid'), ('bridge', 'guest_bridge_invalid'),
    ('missing_bridge', 'guest_bridge_unresolved'), ('trunks', 'vlan_trunks_invalid'),
])
def test_independent_normalization_failures_have_specific_rule_and_identity(mutation, reason):
    data, source = fixture(), inputs()
    if mutation in {'interface', 'ip', 'tag', 'bridge', 'missing_bridge', 'trunks'}:
        data['responses']['/nodes/node-a/qemu/100/config?current=1']['net0'] = {
            'interface': 'invalid', 'ip': 'name=eth0,bridge=vmbr0,ip=invalid',
            'tag': 'name=eth0,bridge=vmbr0,tag=4095', 'bridge': 'bridge=../vmbr0',
            'missing_bridge': 'bridge=vmbr9', 'trunks': 'bridge=vmbr0,trunks=99;invalid'}[mutation]
    elif mutation == 'cidr': data['responses']['/nodes/node-a/network'][0]['cidr'] = 'invalid'
    elif mutation == 'inactive': data['responses']['/nodes/node-a/network'][0]['active'] = 0
    elif mutation == 'boolean': data['responses']['/nodes/node-a/network'][0]['active'] = 2
    elif mutation == 'power':
        data['responses']['/cluster/resources?type=vm'][0]['status'] = 'invalid'
        data['responses']['/nodes/node-a/qemu'][0]['status'] = 'invalid'
    diagnostic = Diagnostics(debug=True)
    result = discover(source, adapter_factory=adapter_factory(data), diagnostics=diagnostic)
    assert result[-1]['completeness'] in {'partial', 'failed'}
    event = next(row for row in diagnostic.events if row['reason_code'] == reason)
    assert event.get('external_id') or event.get('parent_external_id')
    if mutation in {'interface', 'ip', 'tag', 'boolean', 'bridge', 'trunks'}:
        assert event['field'] and event['validation_rule'] and event['encountered_type']


@pytest.mark.parametrize('debug', [False, True])
def test_secret_headers_comments_body_and_arbitrary_config_never_enter_trace(debug, tmp_path):
    source, data = inputs(), fixture('malformed')
    markers = [*source['credentials'].values(), secrets.token_hex(32), secrets.token_hex(32)]
    data['responses']['/nodes/node-a/qemu/100/config?current=1'].update(
        description=markers[2], net0='invalid=' + markers[3] + ',invalid')
    data['responses']['/nodes/node-a/network'][0]['comments'] = markers[2]
    source['config']['unused'] = markers[3]
    path = tmp_path / 'diagnostics.ndjson'; path.touch(mode=0o600)
    diagnostic = Diagnostics.open(path, tmp_path / 'input.json', debug=debug, sensitive=source['credentials'].values())
    discover(source, adapter_factory=adapter_factory(data), diagnostics=diagnostic)
    raw = path.read_text()  # Visible before close: append is unbuffered.
    diagnostic.close()
    assert all(marker not in raw for marker in markers)
    assert 'Authorization' not in raw and 'PVEAPIToken' not in raw and 'description' not in raw
    assert 'guest_interface_invalid' in raw


@pytest.mark.parametrize('trick', ['symlink', 'hardlink', 'outside', 'fifo'])
def test_destination_must_be_private_precreated_regular_file_beside_inputs(tmp_path, trick):
    private = tmp_path / 'job'; private.mkdir(mode=0o700)
    other = tmp_path / 'outside'; other.write_text('unchanged'); other.chmod(0o600)
    path = private / 'diagnostics.ndjson'
    if trick == 'symlink': path.symlink_to(other)
    elif trick == 'hardlink': os.link(other, path)
    elif trick == 'fifo': os.mkfifo(path, mode=0o600)
    else: path = other
    with pytest.raises((ValueError, OSError)):
        Diagnostics.open(path, private / 'input.json')
    assert other.read_text() == 'unchanged'


def test_event_count_limit_is_flushed_and_does_not_capture_arbitrary_scalars(tmp_path, monkeypatch):
    from ansible.module_utils import atlas_diagnostics
    monkeypatch.setattr(atlas_diagnostics, 'MAX_EVENTS', 4)
    path = tmp_path / 'diagnostics.ndjson'; path.touch(mode=0o600)
    diagnostic = Diagnostics.open(path, tmp_path / 'input.json')
    for _ in range(10): diagnostic.emit('accepted', 'source_record_accepted', arbitrary=secrets.token_hex(8))
    assert len(path.read_text().splitlines()) == 4
    assert diagnostic.events[-1]['reason_code'] == 'diagnostic_limit'
    assert 'arbitrary' not in path.read_text()
    diagnostic.close()
