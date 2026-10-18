# SPDX-License-Identifier: Apache-2.0
"""Fixed candidate playbook through actual Ansible Runner, no live source."""
import io
import json
import os
from pathlib import Path
import secrets
import sys
import tarfile
import uuid

import pytest
from atlas_connector_sdk.aip import validate_example_stream

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from build_acceptance_fixture import build_fixture


@pytest.mark.skipif(not os.getenv('ATLAS_TEST_RUN_ANSIBLE'),reason='enable with pinned Ansible Runner installed')
@pytest.mark.parametrize('scenario,expected',[('complete','complete'),('permission_filtered','partial'),('source_failure','failed'),('limits','failed'),('heterogeneous_storage','complete'),('storage_failure','complete'),('config_failure','partial'),('malformed','partial'),('pending','partial')])
@pytest.mark.parametrize('debug', [False, True])
def test_fixed_candidate_playbook_real_runner_and_sdk_stream(tmp_path,scenario,expected,debug):
    import ansible_runner
    payload,manifest=build_fixture(tmp_path/'bundle')
    project=tmp_path/'project'; project.mkdir(mode=0o700)
    with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
        archive.extractall(project,filter='data')
    values={'token_id':'fixture_'+secrets.token_hex(8)+'@pve!discovery','token_secret':secrets.token_urlsafe(32)}
    inputs={'reference':{'connector_id':manifest['id'],'version':manifest['version'],'digest':manifest['distribution']['bundle_digest'][7:]},
            'run_id':str(uuid.uuid4()),'integration_id':str(uuid.uuid4()),'config':{'endpoint':'https://source.example.test:8006','fixture_scenario':scenario},
            'credentials':values,'selected_scopes':['inventory'],'object_classes':[row['key'] for row in manifest['object_classes']],
            'coverage':{'key':'fixture:inventory','snapshot_mode':'full','domains':['assets','networks','interfaces','relationships']},'timeout_seconds':120}
    inputs['debug_enabled'] = debug
    input_file=tmp_path/'input.json'; input_file.write_text(json.dumps(inputs)); input_file.chmod(0o600)
    trace=tmp_path/'diagnostics.ndjson'; trace.touch(mode=0o600)
    output=tmp_path/'aip.ndjson'
    runner=ansible_runner.interface.init_runner(private_data_dir=str(tmp_path),playbook='discover.yml',inventory='localhost,',quiet=True,
        extravars={'atlas_input_file':str(input_file),'atlas_aip_file':str(output),'atlas_diagnostics_file':str(trace),'ansible_python_interpreter':sys.executable},
        envvars={'ANSIBLE_COLLECTIONS_PATH':os.environ['ATLAS_TEST_COLLECTIONS_PATH'],'ANSIBLE_COLLECTIONS_SCAN_SYS_PATH':'False',
                 'PATH':str(Path(sys.executable).parent)+':/usr/bin:/bin','HOME':str(tmp_path),
                 'ANSIBLE_LOCAL_TEMP':str(tmp_path/'local-tmp'),'ANSIBLE_REMOTE_TEMP':str(tmp_path/'remote-tmp')},
        settings={'job_timeout':30,'idle_timeout':30,'suppress_output_file':True,'suppress_ansible_output':True,'omit_event_data':True},event_handler=lambda _:False)
    runner.runner_mode=runner.config.runner_mode='subprocess'; runner.config.subprocess_timeout=30
    runner.run()
    assert runner.rc==0
    messages=[json.loads(line) for line in output.read_text().splitlines()]
    validate_example_stream(messages,manifest)
    assert messages[-1]['completeness']==expected
    assert all(value not in output.read_text() for value in values.values())
    events=[json.loads(line) for line in trace.read_text().splitlines()]
    assert events[0]['reason_code']=='discovery_started' and events[-1]['reason_code']=='discovery_finished'
    assert all(value not in trace.read_text() for value in values.values())
    assets = [row for batch in messages[:-1] for row in batch['assets']]
    links = [row for batch in messages[:-1] for row in batch['relationships']]
    assert not any(row['object_class'] == 'proxmox.storage' for row in assets)
    assert not any(row['relationship_class'] == 'proxmox.uses_storage' for row in links)
    assert not any('storage' in event.get('stage', '') or 'storage' in event.get('source_category', '')
                   or 'storage' in event['reason_code'] for event in events)
    if expected == 'complete':
        assert not any(event['result'] in {'warning', 'error'} for event in events)
