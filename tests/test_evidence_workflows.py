# SPDX-License-Identifier: Apache-2.0
"""Adopted/generated successor contracts and adversarial local mutations.

No hosted expression evaluation, live signing or publication is performed.
"""
from copy import deepcopy
import json
import hashlib
from pathlib import Path
import re
import subprocess
import sys

import pytest
import yaml

from workflow_cases import S4, SUCCESSOR, SYNTHETIC_SUCCESSOR
from prepare_evidence_workflow import prepare, prepare_build, template, ROOT
import catalogue_evidence_driver as driver

ACTIVE = ROOT / '.github/workflows'
ACTION_PINS = {
    'actions/checkout': '3d3c42e5aac5ba805825da76410c181273ba90b1',
    'actions/setup-python': '5fda3b95a4ea91299a34e894583c3862153e4b97',
    'actions/download-artifact': 'd3f86a106a0bac45b974a628896c90dbdf5c8093',
    'actions/create-github-app-token': 'fee1f7d63c2ff003460e3d139729b119787bc349',
    'actions/attest': '508db95dd578ae2727ebd6217d5ba78e4fbda05d',
    'actions/upload-artifact': 'ea165f8d65b6e75b540449e92b4886f43607fa02',
}


def load(raw):
    return yaml.load(raw, Loader=yaml.BaseLoader)


def assert_actions(steps):
    for step in steps:
        if 'uses' in step:
            action, pin = step['uses'].split('@')
            assert ACTION_PINS[action] == pin
            assert re.fullmatch('[a-f0-9]{40}', pin)


def assert_successor(value, pin):
    assert value['permissions'] == {'contents': 'read'}
    assert 'env' not in value and 'defaults' not in value
    assert value['on']['workflow_dispatch']['inputs']['operation']['options'] == ['publish']
    assert value['on']['workflow_dispatch']['inputs']['operation']['default'] == 'publish'
    assert value['on']['workflow_dispatch']['inputs']['acceptance_only']['default'] == 'true'
    assert set(value['on']) == {'workflow_dispatch'}
    assert set(value['jobs']) == {'preflight', 'publish'}
    signer, publisher = value['jobs']['preflight'], value['jobs']['publish']
    assert signer['uses'] == f'benchristian88/atlas-connectors/.github/workflows/catalogue-verifier.yml@{pin}'
    assert signer['secrets'] == {'VERIFICATION_APP_PRIVATE_KEY': '${{ secrets.VERIFICATION_APP_PRIVATE_KEY }}'}
    assert signer['with'] == {'request': '${{ toJSON(inputs) }}'}
    assert signer['if'] == ("github.repository == 'benchristian88/atlas-connectors' && "
        "github.repository_id == '1414494920' && github.repository_owner_id == '93822871' && "
        "github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main' && "
        "github.run_attempt == 1 && inputs.operation == 'publish'")
    assert signer['permissions'] == {'contents': 'read', 'id-token': 'write', 'attestations': 'write'}
    assert set(signer) == {'if', 'permissions', 'uses', 'with', 'secrets'}
    assert publisher['needs'] == 'preflight' and publisher['environment'] == 'catalogue-publication'
    assert publisher['if'] == ("!inputs.acceptance_only && vars.CATALOGUE_EVIDENCE_ENABLED == 'true' && "
        "fromJSON(vars.CATALOGUE_EVIDENCE_ENABLED) == true && "
        "github.repository == 'benchristian88/atlas-connectors' && github.ref == 'refs/heads/main' && "
        "github.run_attempt == 1 && inputs.operation == 'publish'")
    assert publisher['runs-on'] == 'ubuntu-24.04' and publisher['timeout-minutes'] == '30'
    assert set(publisher) == {'needs', 'if', 'environment', 'runs-on', 'timeout-minutes', 'env', 'permissions', 'steps'}
    assert publisher['env'] == {'ATLAS_CATALOGUE_EVIDENCE_ENABLED': '${{ vars.CATALOGUE_EVIDENCE_ENABLED }}',
        'PUBLICATION_OPERATION': '${{ inputs.operation }}', 'ATLAS_SOURCE_DIRECTORY': 'publication-source',
        'ATLAS_IMPLEMENTATION_REVISION': pin}
    assert publisher['permissions'] == {'contents': 'read', 'actions': 'read', 'id-token': 'write', 'attestations': 'write'}
    steps = publisher['steps']
    assert len(steps) == 15
    assert_actions(steps)
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
    assert 'if' not in steps[authorize] and 'if' not in steps[mint]
    assert set(steps[mint]) == {'uses', 'id', 'with'}
    assert steps[download]['with'] == {'artifact-ids': '${{ needs.preflight.outputs.artifact-id }}',
        'merge-multiple': 'true', 'path': '${{ runner.temp }}/publication-preflight'}
    assert steps[authorize].keys() == {'name', 'run'}
    phases = [step.get('run') for step in steps if 'tools/catalogue_evidence_driver.py ' in step.get('run', '')]
    assert phases == ['python tools/catalogue_evidence_driver.py ' + p for p in ('authorize', 'stage', 'finish')]
    for phase in ('stage', 'finish'):
        step, = [s for s in steps if s.get('run') == 'python tools/catalogue_evidence_driver.py ' + phase]
        assert step['if'] == "inputs.operation == 'publish'"
        assert step['env'] == {'ATLAS_PUBLICATION_TOKEN': '${{ steps.app.outputs.token }}',
            'ATLAS_APP_SLUG': '${{ steps.app.outputs.app-slug }}',
            'ATLAS_APP_INSTALLATION_ID': '${{ steps.app.outputs.installation-id }}'}
    attest, = [s for s in steps if s.get('id') == 'attest']
    assert attest['with'] == {'subject-path': 'dist/publication/current.json'}
    assert attest['if'] == "steps.stage.outputs.needs_attestation == 'true'"
    for step in steps[:mint]:
        assert 'secrets.' not in str(step) and 'ATLAS_PUBLICATION_TOKEN' not in str(step)
    for step in steps:
        assert 'continue-on-error' not in step
        assert 'tools/publish_catalogue.py' not in step.get('run', '')
        assert 'publication-source/tools' not in step.get('run', '')
        assert 'bootstrap' not in step.get('run', '') and 'recover' not in step.get('run', '')
        assert 'VERIFICATION_APP_PRIVATE_KEY' not in str(step)
        assert 'working-directory' not in step and 'shell' not in step
        assert '${{ inputs.' not in step.get('run', '')
    assert value['concurrency'] == {'group': 'official-catalogue-publication', 'cancel-in-progress': 'false'}
    # Contract acceptance cannot supply a reviewed S or activate a generated job.
    # Missing/tampered owner approvals are exercised separately by driver tests.
    assert driver.approved_successor() is driver.APPROVED_SUCCESSOR
    assert driver.approved_successor().recovery_decision == 'disabled-pending-permanent-archive-decision'


def test_generated_successor_enforces_independent_pins_admission_and_publish_only_gate():
    assert_successor(yaml.load(prepare(SYNTHETIC_SUCCESSOR), Loader=yaml.BaseLoader), SYNTHETIC_SUCCESSOR)
    assert S4 not in prepare(SYNTHETIC_SUCCESSOR)


@pytest.mark.parametrize('profile', ['generated', 'adopted'])
@pytest.mark.parametrize('kind', ['signer', 'signer-branch', 'checkout', 'environment-pin', 'source', 'source-is-S',
    'admission-order', 'skip-authorize', 'mint-on-failure', 'gate', 'case-sensitive-gate', 'acceptance',
    'recover', 'bootstrap', 'operation', 'preflight-operation', 'preflight-rerun', 'workflows-write',
    'global-write', 'job-write', 'literal-enable', 'old-driver', 'secret-before-admission', 'verifier-key',
    'mutable-action', 'unreviewed-action', 'source-executable', 'untrusted-working-directory'])
def test_successor_contract_rejects_security_regressions(kind, profile):
    pin = SUCCESSOR if profile == 'adopted' else SYNTHETIC_SUCCESSOR
    value = load((ACTIVE / 'catalogue-publish.yml').read_text() if profile == 'adopted' else prepare(pin))
    publisher = value['jobs']['publish']; steps = publisher['steps']
    mint = next(s for s in steps if s.get('id') == 'app')
    if kind == 'signer': value['jobs']['preflight']['uses'] = value['jobs']['preflight']['uses'].replace(pin, 'b' * 40)
    elif kind == 'signer-branch': value['jobs']['preflight']['uses'] = value['jobs']['preflight']['uses'].replace(pin, 'main')
    elif kind == 'checkout': steps[0]['with']['ref'] = 'main'
    elif kind == 'environment-pin': publisher['env']['ATLAS_IMPLEMENTATION_REVISION'] = 'b' * 40
    elif kind == 'source': steps[1]['with']['ref'] = 'main'
    elif kind == 'source-is-S': steps[1]['with']['ref'] = pin
    elif kind == 'admission-order':
        authorize = next(s for s in steps if s.get('run') == 'python tools/catalogue_evidence_driver.py authorize')
        steps.remove(authorize); steps.insert(steps.index(mint) + 1, authorize)
    elif kind == 'gate': publisher['if'] = publisher['if'].replace("vars.CATALOGUE_EVIDENCE_ENABLED == 'true' && ", '')
    elif kind == 'case-sensitive-gate': publisher['if'] = publisher['if'].replace('fromJSON(vars.CATALOGUE_EVIDENCE_ENABLED) == true && ', '')
    elif kind == 'acceptance': publisher['if'] = publisher['if'].replace('!inputs.acceptance_only && ', '')
    elif kind == 'recover': value['on']['workflow_dispatch']['inputs']['operation']['options'].append('recover')
    elif kind == 'bootstrap': value['on']['workflow_dispatch']['inputs']['operation']['options'].append('bootstrap')
    elif kind == 'operation': publisher['if'] = publisher['if'].replace(" && inputs.operation == 'publish'", '')
    elif kind == 'preflight-operation': value['jobs']['preflight']['if'] = value['jobs']['preflight']['if'].replace(" && inputs.operation == 'publish'", '')
    elif kind == 'preflight-rerun': value['jobs']['preflight']['if'] = value['jobs']['preflight']['if'].replace('github.run_attempt == 1', 'true')
    elif kind == 'skip-authorize': next(s for s in steps if s.get('run', '').endswith('driver.py authorize'))['if'] = 'false'
    elif kind == 'mint-on-failure': mint['if'] = 'always()'
    elif kind == 'workflows-write': mint['with']['permission-workflows'] = 'write'
    elif kind == 'global-write': value['permissions']['contents'] = 'write'
    elif kind == 'job-write': publisher['permissions']['contents'] = 'write'
    elif kind == 'literal-enable': publisher['env']['ATLAS_CATALOGUE_EVIDENCE_ENABLED'] = 'true'
    elif kind == 'old-driver': steps[-2]['run'] = 'python tools/publish_catalogue.py finish'
    elif kind == 'verifier-key': steps[-2]['env']['KEY'] = '${{ secrets.VERIFICATION_APP_PRIVATE_KEY }}'
    elif kind == 'mutable-action': steps[0]['uses'] = 'actions/checkout@main'
    elif kind == 'unreviewed-action': steps[0]['uses'] = 'actions/checkout@' + 'b' * 40
    elif kind == 'source-executable': steps[-2]['run'] = 'python publication-source/tools/catalogue_evidence_driver.py finish'
    elif kind == 'untrusted-working-directory': steps[-2]['working-directory'] = 'publication-source'
    else: steps[0]['env'] = {'KEY': '${{ secrets.PUBLICATION_APP_PRIVATE_KEY }}'}
    with pytest.raises((AssertionError, ValueError)):
        assert_successor(value, pin)


def test_generated_candidate_build_only_attests_exact_candidate_registry():
    assert_candidate_build(load(prepare_build()))


def assert_candidate_build(value):
    assert value['permissions'] == {'contents': 'read'}
    assert set(value['on']) == {'workflow_dispatch'} and set(value['jobs']) == {'prepare'}
    job = value['jobs']['prepare']
    assert job['if'] == "github.repository == 'benchristian88/atlas-connectors' && github.ref == 'refs/heads/main'"
    assert job['permissions'] == {'contents': 'read', 'id-token': 'write', 'attestations': 'write'}
    steps = job['steps']
    assert len(steps) == 8 and job['runs-on'] == 'ubuntu-24.04'
    assert 'environment' not in job and 'env' not in job
    assert_actions(steps)
    assert sum(s.get('run') == 'python tools/build_catalogue_candidate.py' for s in steps) == 1
    assert not any(s.get('run') == 'python tools/build_catalogue.py' for s in steps)
    attest, = [s for s in steps if s.get('uses', '').startswith('actions/attest@')]
    assert attest['with'] == {'subject-path': 'dist/catalogue/*.json'}
    assert 'secrets.' not in str(value) and 'create-github-app-token' not in str(value)
    assert 'catalogue_evidence_driver.py' not in str(value)
    assert 'publish_catalogue' not in str(value)
    assert steps[0]['with']['persist-credentials'] == 'false'


def test_actual_workflows_match_generated_security_semantics_and_exact_reviewed_controls():
    for name, generated in [('catalogue-publish.yml', prepare(SUCCESSOR)), ('catalogue.yml', prepare_build())]:
        actual = (ACTIVE / name).read_text()
        assert not actual.startswith('# INACTIVE REVIEW OUTPUT')
        assert actual == generated.split('\n', 1)[1]
        assert load(actual) == load(generated)
    assert_successor(load((ACTIVE / 'catalogue-publish.yml').read_text()), SUCCESSOR)
    assert_candidate_build(load((ACTIVE / 'catalogue.yml').read_text()))
    controls = json.loads((ROOT / 'tests/fixtures/publication_evidence/successor-workflows.json').read_bytes())
    assert controls['implementation_revision'] == SUCCESSOR
    for path, expected in controls['sha256'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path


def test_source_trust_prepares_only_S_without_accepting_live_signing_or_changing_numeric_pins():
    historical = json.loads((ROOT / 'tests/fixtures/publication_evidence/s4-verifier-trust.json').read_bytes())
    trust = json.loads((ROOT / 'catalogue/publication/verifier-trust.json').read_bytes())
    assert historical['signer_revision'] == S4 and historical['live_signer_accepted'] is True
    assert trust == {**historical, 'signer_revision': SUCCESSOR, 'live_signer_accepted': False}


@pytest.mark.parametrize('kind', ['old-builder', 'build-secret', 'build-write', 'mutable-action', 'publisher-token'])
def test_actual_candidate_build_rejects_publication_authority_and_wrong_builder(kind):
    value = load((ACTIVE / 'catalogue.yml').read_text())
    job = value['jobs']['prepare']
    if kind == 'old-builder':
        next(s for s in job['steps'] if s.get('run') == 'python tools/build_catalogue_candidate.py')['run'] = 'python tools/build_catalogue.py'
    elif kind == 'build-secret': job['env'] = {'KEY': '${{ secrets.PUBLICATION_APP_PRIVATE_KEY }}'}
    elif kind == 'build-write': job['permissions']['contents'] = 'write'
    elif kind == 'mutable-action': job['steps'][0]['uses'] = 'actions/checkout@main'
    else: job['steps'].append({'uses': 'actions/create-github-app-token@' + ACTION_PINS['actions/create-github-app-token']})
    with pytest.raises(AssertionError):
        assert_candidate_build(value)


def test_actual_build_cli_and_frozen_driver_select_identical_sequence_two_bytes(tmp_path):
    # Exercise the actual adopted build command, not the sequence-one builder.
    workflow = load((ACTIVE / 'catalogue.yml').read_text())
    step, = [s for s in workflow['jobs']['prepare']['steps'] if s.get('run', '').startswith('python tools/build_')]
    command = [sys.executable, *step['run'].split()[1:], '--output', str(tmp_path / 'candidate')]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    raw = (tmp_path / 'candidate/catalogue-000002.json').read_bytes()
    assert raw == (tmp_path / 'candidate/catalogue.json').read_bytes() == driver.build_candidate(ROOT)
    value = json.loads(raw)
    assert value['sequence'] == 2 and (ROOT / 'catalogue/candidate-v2/sequence.txt').read_text() == '2\n'
    entry, = [e for e in value['entries'] if e['status'] == 'active']
    assert entry['manifest']['version'] == '0.2.2' and entry['release_asset_id'] == 693849044
    assert entry['manifest']['distribution']['provenance']['source_commit'] == 'e58788a667c0c0006477ac149e8ad28aedda0745'


@pytest.mark.parametrize('acceptance_only', [True, False])
def test_actual_unaccepted_S_guard_qualifies_only_acceptance_mode(tmp_path, acceptance_only):
    from test_verifier_workflow import run_context_guard
    trust = json.loads((ROOT / 'catalogue/publication/verifier-trust.json').read_bytes())
    result, output = run_context_guard(tmp_path, trust=trust, accepted=False, acceptance_only=acceptance_only)
    assert (result.returncode == 0) is acceptance_only
    assert output.exists() is acceptance_only


@pytest.mark.parametrize('pin', [None, '', 'main', 'refs/heads/main', S4, 'a' * 40, SUCCESSOR.upper()])
def test_actual_S_guard_rejects_missing_mutable_old_or_future_policy_pin(tmp_path, pin):
    from test_verifier_workflow import run_context_guard
    trust = json.loads((ROOT / 'catalogue/publication/verifier-trust.json').read_bytes())
    if pin is None: trust.pop('signer_revision')
    else: trust['signer_revision'] = pin
    result, output = run_context_guard(tmp_path, {'workflow_sha': SUCCESSOR}, trust=trust,
                                       accepted=False, acceptance_only=True)
    assert result.returncode != 0 and not output.exists()


@pytest.mark.parametrize('gate', ['', 'false', 'False', 'FALSE', 'TRUE', 'True', 'tRuE', '1', 'null', ' true ', 'true\n', 'garbage', 'true'])
@pytest.mark.parametrize('acceptance_only', [True, False])
def test_actual_publication_condition_requires_exact_true_and_non_acceptance(gate, acceptance_only):
    # Execute this constrained conjunction's actual terms using the documented
    # Actions case-insensitive string equality and JSON conversion. Not a claim
    # of hosted job execution. Structural tests reject any expression change.
    condition = load((ACTIVE / 'catalogue-publish.yml').read_text())['jobs']['publish']['if']
    context = {'inputs.acceptance_only': acceptance_only, 'vars.CATALOGUE_EVIDENCE_ENABLED': gate,
        'github.repository': 'benchristian88/atlas-connectors', 'github.ref': 'refs/heads/main',
        'github.run_attempt': 1, 'inputs.operation': 'publish'}
    def resolve(term):
        if term.startswith('fromJSON('):
            return json.loads(context[term[9:-1]])
        if term.startswith("'"): return term[1:-1]
        if term == 'true': return True
        if term == '1': return 1
        return context[term]
    def evaluate():
        for term in condition.split(' && '):
            if term.startswith('!'):
                if resolve(term[1:]): return False
            else:
                left, right = map(resolve, term.split(' == '))
                if isinstance(left, str) and isinstance(right, str):
                    left, right = left.casefold(), right.casefold()
                if left != right: return False
        return True
    try:
        admitted = evaluate()
    except json.JSONDecodeError:
        admitted = False  # Invalid JSON cannot schedule a Publisher job.
    assert admitted is (gate == 'true' and not acceptance_only)


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
