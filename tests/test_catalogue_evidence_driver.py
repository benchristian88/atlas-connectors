# SPDX-License-Identifier: Apache-2.0
"""Release-owned contract and isolated local denials; no live signing/publication."""
from dataclasses import FrozenInstanceError, asdict, fields, replace
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import subprocess

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import catalogue_evidence_driver as driver
from publication_contract import canonical_json, digest, parse_catalogue, retain_history
from publication_evidence import Archive
from prepare_evidence_workflow import prepare
from test_publication_authorization import fixture, SOURCE, REVISION
from test_publication_evidence import signed  # Required by the imported state fixture.

ROOT = Path(__file__).resolve().parents[1]
POLICY_SHA256 = 'c9a88eeb6c7e6d0a7f1a08eaa07eeed5ea251449db7104f7757626842cf1bbe9'
ADR = ('https://github.com/benchristian88/atlas/blob/76031dc6358a81c3babd15f74d407e22f0778dee/'
       'docs/decisions/0018-catalogue-durable-publication-evidence.md')
EXPECTED_APPROVAL = {
    'policy_sha256': POLICY_SHA256,
    'selection_seconds': 900,
    'publication_seconds': 300,
    'historical_decision': ADR + '#historical-authorization',
    'selection_binding_decision': ADR + '#selection-binding',
    'recovery_decision': 'disabled-pending-permanent-archive-decision',
}
APPROVAL_SHA256 = '8a1c69168ed22dc2f0bff385da182de9bae913e900df031d4b47aabccd7e9070'


def test_production_approval_has_exact_immutable_owner_decision_and_independent_fingerprint():
    record = driver.APPROVED_SUCCESSOR
    assert type(record) is driver.SuccessorApproval
    assert {f.name for f in fields(record)} == EXPECTED_APPROVAL.keys()
    assert asdict(record) == EXPECTED_APPROVAL
    assert hashlib.sha256((ROOT / 'catalogue/publication/policy.json').read_bytes()).hexdigest() == POLICY_SHA256
    # Independent stdlib reproduction pins formatting as well as all six values.
    raw = (json.dumps(EXPECTED_APPROVAL, sort_keys=True, indent=2, ensure_ascii=False,
                      allow_nan=False) + '\n').encode('utf-8')
    assert raw == canonical_json(asdict(record))
    assert hashlib.sha256(raw).hexdigest() == APPROVAL_SHA256 == driver.APPROVED_SUCCESSOR_SHA256
    assert digest(canonical_json(asdict(record))) == APPROVAL_SHA256 != POLICY_SHA256
    assert driver.approved_successor() is record
    with pytest.raises(FrozenInstanceError):
        record.selection_seconds = 901


@pytest.fixture
def denied_job(monkeypatch, tmp_path):
    """In-memory job context; credentials and all publication effects are tripwires."""
    credentials = {'ATLAS_PUBLICATION_TOKEN', 'ATLAS_APP_SLUG', 'ATLAS_APP_INSTALLATION_ID'}
    class Environment(dict):
        def get(self, key, default=None):
            assert key not in credentials, 'denied job accessed publication credentials'
            return super().get(key, default)
        def __getitem__(self, key):
            assert key not in credentials, 'denied job accessed publication credentials'
            return super().__getitem__(key)
    env = Environment(fixture('publish')[1])
    env.update(RUNNER_TEMP=str(tmp_path), GITHUB_OUTPUT=str(tmp_path / 'job-output'),
               ATLAS_PUBLICATION_TOKEN='DO-NOT-DISCLOSE', ATLAS_APP_SLUG='forged-publisher',
               ATLAS_APP_INSTALLATION_ID='174027755')
    monkeypatch.setattr(driver.os, 'environ', env)
    def forbidden(*args, **kwargs):
        pytest.fail('denied job reached a publication client, artifact or provider boundary')
    for name in ('Github', 'Verifier', 'EvidencePublisher', 'CheckpointStore', 'build_candidate'):
        monkeypatch.setattr(driver, name, forbidden)
    return env


def assert_job_rejected(monkeypatch, capsys, phase):
    monkeypatch.setattr(sys, 'argv', ['catalogue_evidence_driver.py', phase])
    with pytest.raises(SystemExit) as error:
        driver.main()
    assert error.value.code == 1
    output = capsys.readouterr()
    assert output.out == '' and output.err == 'catalogue_evidence_driver_rejected\n'


@pytest.mark.parametrize('record_missing,fingerprint_missing', [(True, False), (False, True), (True, True)])
def test_missing_approval_still_fails_before_context_credentials_or_provider(
        monkeypatch, capsys, denied_job, tmp_path, record_missing, fingerprint_missing):
    denied_job.update(APPROVED_SUCCESSOR=json.dumps(EXPECTED_APPROVAL),
                      APPROVED_SUCCESSOR_SHA256=APPROVAL_SHA256)
    if record_missing:
        monkeypatch.setattr(driver, 'APPROVED_SUCCESSOR', None)
    if fingerprint_missing:
        monkeypatch.setattr(driver, 'APPROVED_SUCCESSOR_SHA256', None)
    monkeypatch.setattr(driver, 'check_checkouts', lambda *a: pytest.fail('missing approval reached checkout'))
    with pytest.raises(ValueError, match='^successor_owner_approval_required$'):
        driver.approved_successor()
    assert_job_rejected(monkeypatch, capsys, 'stage')
    assert list(tmp_path.iterdir()) == []


def test_driver_fails_before_any_publication_credential_or_provider(monkeypatch):
    monkeypatch.setenv('ATLAS_PUBLICATION_TOKEN', 'DO-NOT-DISCLOSE')
    monkeypatch.delenv('ATLAS_IMPLEMENTATION_REVISION', raising=False)
    result = subprocess.run([sys.executable, 'tools/catalogue_evidence_driver.py', 'stage'],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 1
    assert result.stderr == 'catalogue_evidence_driver_rejected\n'
    assert 'DO-NOT-DISCLOSE' not in result.stdout + result.stderr
    assert driver.approved_successor() is driver.APPROVED_SUCCESSOR


def test_checkpoint_durable_reopen_and_context(tmp_path):
    path = tmp_path / 'checkpoint.json'
    store = driver.CheckpointStore(path, {'run_id': 60})
    assert store.load() is None
    value = {'release_id': 123, 'assets': {'preflight.json': {'id': 456, 'size': 42, 'digest': 'sha256:' + 'a' * 64}}}
    store.save(value)
    assert path.stat().st_mode & 0o777 == 0o600
    assert driver.CheckpointStore(path, {'run_id': 60}).load() == value
    with pytest.raises(ValueError, match='checkpoint_context'):
        driver.CheckpointStore(path, {'run_id': 61}).load()
    path.chmod(0o644)
    with pytest.raises(ValueError, match='checkpoint_permissions'):
        store.load()


@pytest.mark.parametrize('field', ['run_id', 'source_commit', 'preflight_sha256',
                                  'policy_sha256', 'implementation_revision'])
def test_checkpoint_cannot_authorize_another_job_source_or_original_evidence(tmp_path, field):
    context = {'run_id': 60, 'source_commit': 'a' * 40, 'preflight_sha256': 'b' * 64,
               'policy_sha256': POLICY_SHA256, 'implementation_revision': 'c' * 40}
    path = tmp_path / 'checkpoint'
    store = driver.CheckpointStore(path, context)
    store.save({'release_id': 123, 'assets': {}})
    original = path.read_bytes()
    changed = {**context, field: 61 if field == 'run_id' else 'd' * len(context[field])}
    with pytest.raises(ValueError, match='^checkpoint_context$'):
        driver.CheckpointStore(path, changed).load()
    assert path.read_bytes() == original


@pytest.mark.parametrize('raw', [b'{', b'{}', b'{"schema":1,"schema":2}'])
def test_checkpoint_torn_or_ambiguous_never_reinitializes(tmp_path, raw):
    path = tmp_path / 'checkpoint.json'; path.write_bytes(raw); path.chmod(0o600)
    with pytest.raises(ValueError):
        driver.CheckpointStore(path, {}).load()
    assert path.read_bytes() == raw


def test_checkpoint_symlink_rejects(tmp_path):
    target = tmp_path / 'target'; target.write_text('{}')
    path = tmp_path / 'checkpoint'; path.symlink_to(target)
    with pytest.raises(ValueError, match='checkpoint_path'):
        driver.CheckpointStore(path, {})


def test_candidate_retains_history_and_exact_real_published_package():
    root = Path(__file__).resolve().parents[1]
    raw = driver.build_candidate(root)
    candidate = parse_catalogue(raw)
    original = json.loads((root / 'tests/fixtures/official_catalogue/catalogue-000001.json').read_bytes())
    retain_history(original, candidate)
    assert candidate['sequence'] == 2
    old, new = candidate['entries']
    assert old == {**original['entries'][0], 'status': 'withdrawn'}
    assert old['manifest']['version'] == '0.2.0'
    assert new['manifest']['version'] == '0.2.2' and new['release_asset_id'] == 693849044
    assert new['status'] == 'active' and new['release_tag'] == 'proxmox-v0.2.2'
    assert new['manifest']['distribution']['bundle_digest'] == 'sha256:2d66fc69b9cf9c70d7df117fe41bff3e3e056299f1908cde965e9e3f75e59abf'
    assert new['manifest']['distribution']['provenance']['source_commit'] == 'e58788a667c0c0006477ac149e8ad28aedda0745'
    # The catalogue adds distribution metadata to the unchanged package manifest.
    assert {k: v for k, v in new['manifest'].items() if k != 'distribution'} == json.loads(
        (root / 'connectors/proxmox/releases/0.2.2/manifest.json').read_bytes())
    assert (root / 'catalogue/sequence.txt').read_text() == '1\n'


def test_workflow_preparation_does_not_activate_or_use_mutable_pins():
    raw = prepare('a' * 40)
    assert raw.startswith('# INACTIVE REVIEW OUTPUT')
    assert 'tools/catalogue_evidence_driver.py stage' in raw
    assert '2dd1ffcd2f5677dc35bdbc8f68ea28275c91c285' not in raw
    with pytest.raises(ValueError):
        prepare('main')


from test_publication_evidence import state


def test_each_observed_upload_is_durable_and_resumable(state, tmp_path):
    api, publisher, raw = state
    store = driver.CheckpointStore(tmp_path / 'checkpoint', {'run_id': 60})
    observed = []
    def save(value):
        store.save(value)
        observed.append(deepcopy(value))
    publisher.persist_checkpoint = save
    staged = publisher.stage(raw)
    assert len(observed) == 7  # created release plus six staged assets
    assert store.load() == publisher.checkpoint
    publisher.checkpoint = driver.CheckpointStore(tmp_path / 'checkpoint', {'run_id': 60}).load()
    assert publisher.stage(raw).pointer == staged.pointer
    assert publisher.checkpoint == store.load()


def test_candidate_build_workflow_and_cli_share_exact_registry(tmp_path):
    from prepare_evidence_workflow import prepare_build
    assert 'python tools/build_catalogue_candidate.py' in prepare_build()
    result = subprocess.run([sys.executable, 'tools/build_catalogue_candidate.py', '--output', str(tmp_path / 'build')],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / 'build/catalogue-000002.json').read_bytes() == driver.build_candidate(Path(__file__).resolve().parents[1])
    assert (tmp_path / 'build/catalogue.json').read_bytes() == (tmp_path / 'build/catalogue-000002.json').read_bytes()


def test_successor_contract_approval_requires_exact_release_owned_fingerprint(monkeypatch):
    proposal = driver.SuccessorApproval('a' * 64, 900, 300, 'SYNTHETIC historical decision',
        'SYNTHETIC selection decision', 'disabled-pending-permanent-archive-decision')
    monkeypatch.setattr(driver, 'APPROVED_SUCCESSOR', proposal)
    monkeypatch.setattr(driver, 'APPROVED_SUCCESSOR_SHA256', None)
    with pytest.raises(ValueError, match='owner_approval_required'):
        driver.approved_successor()
    monkeypatch.setattr(driver, 'APPROVED_SUCCESSOR_SHA256', digest(canonical_json(asdict(proposal))))
    assert driver.approved_successor() == proposal
    monkeypatch.setattr(driver, 'APPROVED_SUCCESSOR_SHA256', 'b' * 64)
    with pytest.raises(ValueError, match='pin_mismatch'):
        driver.approved_successor()


@pytest.mark.parametrize('field,value', [
    ('policy_sha256', 'a' * 64),
    ('historical_decision', ADR + '#recovery'),
    ('selection_binding_decision', ADR.replace('76031dc6358a81c3babd15f74d407e22f0778dee', 'dev')
     + '#selection-binding'),
    ('selection_seconds', 901), ('publication_seconds', 301),
    ('recovery_decision', 'enabled'),
])
def test_modified_record_cannot_repair_its_release_fingerprint(
        monkeypatch, capsys, denied_job, tmp_path, field, value):
    record = replace(driver.APPROVED_SUCCESSOR, **{field: value})
    monkeypatch.setattr(driver, 'APPROVED_SUCCESSOR', record)
    with pytest.raises(ValueError, match='^successor_approval_pin_mismatch$'):
        driver.approved_successor()
    assert driver.APPROVED_SUCCESSOR_SHA256 == APPROVAL_SHA256
    assert_job_rejected(monkeypatch, capsys, 'stage')
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('fingerprint', ['0' * 64, '', 'A' * 64, '8a1c', 1, {}])
def test_wrong_fingerprint_fails_closed(monkeypatch, capsys, denied_job, tmp_path, fingerprint):
    monkeypatch.setattr(driver, 'APPROVED_SUCCESSOR_SHA256', fingerprint)
    with pytest.raises(ValueError, match='^successor_approval_pin_mismatch$'):
        driver.approved_successor()
    assert_job_rejected(monkeypatch, capsys, 'stage')
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('field,value,code', [
    ('policy_sha256', '', 'successor_approval_identity'),
    ('policy_sha256', 'A' * 64, 'successor_approval_identity'),
    ('policy_sha256', None, 'successor_approval_identity'),
    ('policy_sha256', 123, 'successor_approval_identity'),
    ('selection_seconds', True, 'archive_historical_limits'),
    ('selection_seconds', 0, 'archive_historical_limits'),
    ('selection_seconds', 1801, 'archive_historical_limits'),
    ('publication_seconds', '300', 'archive_historical_limits'),
    ('publication_seconds', -1, 'archive_historical_limits'),
    ('publication_seconds', 1801, 'archive_historical_limits'),
    ('historical_decision', '', 'successor_decisions_required'),
    ('historical_decision', None, 'successor_decisions_required'),
    ('historical_decision', 'x' * 257, 'successor_decisions_required'),
    ('selection_binding_decision', '', 'successor_decisions_required'),
    ('selection_binding_decision', 1, 'successor_decisions_required'),
    ('selection_binding_decision', 'x' * 257, 'successor_decisions_required'),
    ('recovery_decision', 'enabled', 'successor_recovery_decision_required'),
    ('recovery_decision', '', 'successor_recovery_decision_required'),
    ('recovery_decision', None, 'successor_recovery_decision_required'),
])
def test_invalid_approval_is_rejected_even_under_test_only_repinning(
        monkeypatch, capsys, denied_job, tmp_path, field, value, code):
    record = replace(driver.APPROVED_SUCCESSOR, **{field: value})
    monkeypatch.setattr(driver, 'APPROVED_SUCCESSOR', record)
    monkeypatch.setattr(driver, 'APPROVED_SUCCESSOR_SHA256', digest(canonical_json(asdict(record))))
    with pytest.raises(ValueError, match='^' + code + '$'):
        driver.approved_successor()
    assert_job_rejected(monkeypatch, capsys, 'stage')
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('kind', ['dict', 'other-dataclass', 'subclass', 'string'])
def test_approval_requires_exact_dataclass_type(monkeypatch, capsys, denied_job, tmp_path, kind):
    from dataclasses import make_dataclass
    other_type = make_dataclass('OtherApproval', [(k, object) for k in EXPECTED_APPROVAL], frozen=True)
    class Subclass(driver.SuccessorApproval):
        pass
    value = {'dict': EXPECTED_APPROVAL, 'other-dataclass': other_type(**EXPECTED_APPROVAL),
             'subclass': Subclass(**EXPECTED_APPROVAL), 'string': APPROVAL_SHA256}[kind]
    monkeypatch.setattr(driver, 'APPROVED_SUCCESSOR', value)
    with pytest.raises(ValueError, match='^successor_owner_approval_required$'):
        driver.approved_successor()
    assert_job_rejected(monkeypatch, capsys, 'stage')
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('claimed_recovery', [None, 'true', 'enabled', 'approved'])
def test_successor_recovery_stays_disabled_with_real_production_approval(
        monkeypatch, capsys, denied_job, tmp_path, claimed_recovery):
    assert driver.approved_successor() is driver.APPROVED_SUCCESSOR
    # Only this isolated dictionary claims gate/recovery authority; no real gate is set.
    denied_job.update(ATLAS_CATALOGUE_EVIDENCE_ENABLED='true', PUBLICATION_OPERATION='recover')
    if claimed_recovery is not None:
        denied_job.update(ATLAS_RECOVERY_ENABLED=claimed_recovery, RECOVERY_DECISION=claimed_recovery,
                          APPROVED_SUCCESSOR=json.dumps({**EXPECTED_APPROVAL, 'recovery_decision': claimed_recovery}),
                          APPROVED_SUCCESSOR_SHA256='0' * 64)
    monkeypatch.setattr(driver, 'check_checkouts', lambda *a: pytest.fail('recovery reached checkout'))
    assert_job_rejected(monkeypatch, capsys, 'recover')
    assert list(tmp_path.iterdir()) == []
    assert driver.approved_successor().recovery_decision == 'disabled-pending-permanent-archive-decision'


@pytest.mark.parametrize('phase', ['authorize', 'stage', 'finish'])
@pytest.mark.parametrize('gate', [None, 'false', 'False', '1'])
def test_valid_approval_and_forged_environment_cannot_bypass_disabled_gate(
        monkeypatch, capsys, denied_job, tmp_path, phase, gate):
    if gate is not None:
        denied_job['ATLAS_CATALOGUE_EVIDENCE_ENABLED'] = gate
    denied_job.update(APPROVED_SUCCESSOR=json.dumps(EXPECTED_APPROVAL),
                      APPROVED_SUCCESSOR_SHA256=APPROVAL_SHA256, POLICY_SHA256=POLICY_SHA256,
                      ATLAS_IMPLEMENTATION_REVISION=REVISION, GITHUB_SHA=SOURCE)
    # Isolate the gate with otherwise admitted checkouts. No preflight/file is read.
    monkeypatch.setattr(driver, 'check_checkouts', lambda *a: None)
    monkeypatch.setattr(driver, 'read_regular', lambda *a: pytest.fail('gate-off job read source or preflight'))
    monkeypatch.setattr(driver, 'job_preflight', lambda *a, **kw: pytest.fail('gate-off job reached preflight'))
    assert_job_rejected(monkeypatch, capsys, phase)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('boundary', ['checkout', 'policy', 'signer', 'original-preflight'])
@pytest.mark.parametrize('phase', ['authorize', 'stage', 'finish'])
def test_production_approval_does_not_replace_checkout_policy_signer_or_original_preflight(
        monkeypatch, capsys, denied_job, tmp_path, boundary, phase):
    denied_job['ATLAS_CATALOGUE_EVIDENCE_ENABLED'] = 'true'  # Isolated job dictionary only.
    if boundary == 'checkout':
        # The inherited real checker rejects missing implementation S.
        denied_job.pop('ATLAS_IMPLEMENTATION_REVISION')
    else:
        monkeypatch.setattr(driver, 'check_checkouts', lambda *a: None)
        raw_policy = (ROOT / 'catalogue/publication/policy.json').read_bytes()
        trust = json.loads((ROOT / 'catalogue/publication/verifier-trust.json').read_bytes())
        if boundary == 'signer':
            denied_job['ATLAS_IMPLEMENTATION_REVISION'] = 'c' * 40
        else:
            denied_job['ATLAS_IMPLEMENTATION_REVISION'] = trust['signer_revision']
        def read(path, maximum):
            if path.name == 'policy.json':
                return raw_policy + b' ' if boundary == 'policy' else raw_policy
            assert path.name == 'verifier-trust.json'
            return canonical_json(trust)
        monkeypatch.setattr(driver, 'read_regular', read)
    # Real job_preflight rejects an absent original artifact directory. Other
    # boundaries must fail before admission, irrespective of a matching policy.
    if boundary != 'original-preflight':
        monkeypatch.setattr(driver, 'job_preflight', lambda *a, **kw: pytest.fail('invalid context reached preflight'))
    assert_job_rejected(monkeypatch, capsys, phase)
    assert list(tmp_path.iterdir()) == []
