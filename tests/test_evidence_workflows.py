# SPDX-License-Identifier: Apache-2.0
"""Generated successor security contracts; no live workflow/pin/approval changes."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from workflow_cases import S4, SYNTHETIC_SUCCESSOR
from prepare_evidence_workflow import prepare, prepare_build, template, ROOT
import catalogue_evidence_driver as driver


def assert_successor(value, pin):
    assert value['on']['workflow_dispatch']['inputs']['operation']['options'] == ['publish']
    assert value['on']['workflow_dispatch']['inputs']['operation']['default'] == 'publish'
    assert value['on']['workflow_dispatch']['inputs']['acceptance_only']['default'] == 'true'
    assert set(value['on']) == {'workflow_dispatch'}
    assert set(value['jobs']) == {'preflight', 'publish'}
    signer, publisher = value['jobs']['preflight'], value['jobs']['publish']
    assert signer['uses'] == f'benchristian88/atlas-connectors/.github/workflows/catalogue-verifier.yml@{pin}'
    assert signer['secrets'] == {'VERIFICATION_APP_PRIVATE_KEY': '${{ secrets.VERIFICATION_APP_PRIVATE_KEY }}'}
    assert signer['with'] == {'request': '${{ toJSON(inputs) }}'}
    assert publisher['needs'] == 'preflight' and publisher['environment'] == 'catalogue-publication'
    assert publisher['if'] == ("!inputs.acceptance_only && vars.CATALOGUE_EVIDENCE_ENABLED == 'true' && "
        "github.repository == 'benchristian88/atlas-connectors' && github.ref == 'refs/heads/main' && github.run_attempt == 1")
    assert publisher['env'] == {'ATLAS_CATALOGUE_EVIDENCE_ENABLED': '${{ vars.CATALOGUE_EVIDENCE_ENABLED }}',
        'PUBLICATION_OPERATION': '${{ inputs.operation }}', 'ATLAS_SOURCE_DIRECTORY': 'publication-source',
        'ATLAS_IMPLEMENTATION_REVISION': pin}
    assert publisher['permissions'] == {'contents': 'read', 'actions': 'read', 'id-token': 'write', 'attestations': 'write'}
    steps = publisher['steps']
    assert steps[0]['with'] == {'repository': 'benchristian88/atlas-connectors', 'ref': pin, 'persist-credentials': 'false'}
    assert steps[1]['with'] == {'repository': 'benchristian88/atlas-connectors', 'ref': '${{ github.sha }}',
        'path': 'publication-source', 'persist-credentials': 'false'}
    authorize, = [i for i, step in enumerate(steps) if step.get('run') == 'python tools/catalogue_evidence_driver.py authorize']
    mint, = [i for i, step in enumerate(steps) if step.get('id') == 'app']
    download, = [i for i, step in enumerate(steps) if 'download-artifact@' in step.get('uses', '')]
    assert download < authorize < mint
    assert steps[download]['with']['artifact-ids'] == '${{ needs.preflight.outputs.artifact-id }}'
    assert steps[mint]['with'] == {'app-id': '${{ vars.PUBLICATION_APP_ID }}',
        'private-key': '${{ secrets.PUBLICATION_APP_PRIVATE_KEY }}', 'owner': 'benchristian88',
        'repositories': 'atlas-connectors', 'permission-contents': 'write',
        'permission-actions': 'read', 'permission-administration': 'read'}
    phases = [step.get('run') for step in steps if 'tools/catalogue_evidence_driver.py ' in step.get('run', '')]
    assert phases == ['python tools/catalogue_evidence_driver.py ' + p for p in ('authorize', 'stage', 'finish')]
    for step in steps[:mint]:
        assert 'secrets.' not in str(step) and 'ATLAS_PUBLICATION_TOKEN' not in str(step)
    for step in steps:
        assert 'continue-on-error' not in step
        assert 'tools/publish_catalogue.py' not in step.get('run', '')
        assert 'publication-source/tools' not in step.get('run', '')
        assert 'bootstrap' not in step.get('run', '') and 'recover' not in step.get('run', '')
        assert 'VERIFICATION_APP_PRIVATE_KEY' not in str(step)
    assert value['concurrency'] == {'group': 'official-catalogue-publication', 'cancel-in-progress': 'false'}
    assert driver.APPROVED_SUCCESSOR is None and driver.APPROVED_SUCCESSOR_SHA256 is None


def test_generated_successor_enforces_independent_pins_admission_and_publish_only_gate():
    assert_successor(yaml.load(prepare(SYNTHETIC_SUCCESSOR), Loader=yaml.BaseLoader), SYNTHETIC_SUCCESSOR)
    assert S4 not in prepare(SYNTHETIC_SUCCESSOR)


@pytest.mark.parametrize('kind', ['signer', 'checkout', 'environment-pin', 'source', 'admission-order',
    'gate', 'acceptance', 'recover', 'workflows-write', 'literal-enable', 'old-driver', 'secret-before-admission'])
def test_successor_contract_rejects_security_regressions(kind):
    value = yaml.load(prepare(SYNTHETIC_SUCCESSOR), Loader=yaml.BaseLoader)
    publisher = value['jobs']['publish']; steps = publisher['steps']
    mint = next(s for s in steps if s.get('id') == 'app')
    if kind == 'signer': value['jobs']['preflight']['uses'] = value['jobs']['preflight']['uses'].replace(SYNTHETIC_SUCCESSOR, 'b' * 40)
    elif kind == 'checkout': steps[0]['with']['ref'] = 'main'
    elif kind == 'environment-pin': publisher['env']['ATLAS_IMPLEMENTATION_REVISION'] = 'b' * 40
    elif kind == 'source': steps[1]['with']['ref'] = 'main'
    elif kind == 'admission-order':
        authorize = next(s for s in steps if s.get('run') == 'python tools/catalogue_evidence_driver.py authorize')
        steps.remove(authorize); steps.insert(steps.index(mint) + 1, authorize)
    elif kind == 'gate': publisher['if'] = publisher['if'].replace("vars.CATALOGUE_EVIDENCE_ENABLED == 'true' && ", '')
    elif kind == 'acceptance': publisher['if'] = publisher['if'].replace('!inputs.acceptance_only && ', '')
    elif kind == 'recover': value['on']['workflow_dispatch']['inputs']['operation']['options'].append('recover')
    elif kind == 'workflows-write': mint['with']['permission-workflows'] = 'write'
    elif kind == 'literal-enable': publisher['env']['ATLAS_CATALOGUE_EVIDENCE_ENABLED'] = 'true'
    elif kind == 'old-driver': steps[-2]['run'] = 'python tools/publish_catalogue.py finish'
    else: steps[0]['env'] = {'KEY': '${{ secrets.PUBLICATION_APP_PRIVATE_KEY }}'}
    with pytest.raises((AssertionError, ValueError)):
        assert_successor(value, SYNTHETIC_SUCCESSOR)


def test_generated_candidate_build_only_attests_exact_candidate_registry():
    value = yaml.load(prepare_build(), Loader=yaml.BaseLoader)
    assert set(value['on']) == {'workflow_dispatch'} and set(value['jobs']) == {'prepare'}
    job = value['jobs']['prepare']
    assert job['if'] == "github.repository == 'benchristian88/atlas-connectors' && github.ref == 'refs/heads/main'"
    assert job['permissions'] == {'contents': 'read', 'id-token': 'write', 'attestations': 'write'}
    steps = job['steps']
    assert sum(s.get('run') == 'python tools/build_catalogue_candidate.py' for s in steps) == 1
    assert not any(s.get('run') == 'python tools/build_catalogue.py' for s in steps)
    attest, = [s for s in steps if s.get('uses', '').startswith('actions/attest@')]
    assert attest['with'] == {'subject-path': 'dist/catalogue/*.json'}
    assert 'secrets.' not in str(value) and 'create-github-app-token' not in str(value)
    assert 'catalogue_evidence_driver.py' not in str(value)
    assert 'publish_catalogue' not in str(value)
    assert steps[0]['with']['persist-credentials'] == 'false'


@pytest.mark.parametrize('kind', ['publisher', 'catalogue-build'])
def test_both_cli_outputs_are_inactive_exclusive_and_leave_live_controls_byte_exact(tmp_path, kind):
    paths = [*ROOT.glob('.github/workflows/*.yml'), *ROOT.glob('catalogue/publication/*trust.json'),
        ROOT / 'catalogue/publication/policy.json']
    before = {p: p.read_bytes() for p in paths}
    output = tmp_path / (kind + '.yml')
    command = [sys.executable, 'tools/prepare_evidence_workflow.py', '--revision', SYNTHETIC_SUCCESSOR,
               '--kind', kind, '--output', str(output)]
    assert subprocess.run(command, cwd=ROOT, capture_output=True).returncode == 0
    assert output.read_text().startswith('# INACTIVE REVIEW OUTPUT')
    assert subprocess.run(command, cwd=ROOT, capture_output=True).returncode == 1
    assert {p: p.read_bytes() for p in paths} == before


def test_generation_and_historical_security_tests_do_not_depend_on_adopted_live_workflows(monkeypatch):
    read = Path.read_bytes
    def isolated(path):
        assert path.parent != ROOT / '.github/workflows', 'Historical template must not follow the active caller'
        return read(path)
    monkeypatch.setattr(Path, 'read_bytes', isolated)
    assert_successor(yaml.load(prepare(SYNTHETIC_SUCCESSOR), Loader=yaml.BaseLoader), SYNTHETIC_SUCCESSOR)
    assert 'python tools/build_catalogue_candidate.py' in prepare_build()
    assert 'options: [publish, recover, bootstrap]' in template('catalogue-publish-s4.yml')


@pytest.mark.parametrize('kind', ['publisher', 'catalogue-build'])
def test_generation_rejects_output_into_active_workflow_directory(kind):
    result = subprocess.run([sys.executable, 'tools/prepare_evidence_workflow.py', '--revision', SYNTHETIC_SUCCESSOR,
        '--kind', kind, '--output', str(ROOT / '.github/workflows/DO-NOT-CREATE.yml')], cwd=ROOT, capture_output=True)
    assert result.returncode == 1 and not (ROOT / '.github/workflows/DO-NOT-CREATE.yml').exists()
