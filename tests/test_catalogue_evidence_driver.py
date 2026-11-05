# SPDX-License-Identifier: Apache-2.0
"""Isolated local driver/checkpoint tests; no publication or owner approval."""
from dataclasses import asdict
from copy import deepcopy
import json
from pathlib import Path
import os
import sys
import subprocess

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import catalogue_evidence_driver as driver
from publication_contract import canonical_json, digest, parse_catalogue, retain_history
from publication_evidence import Archive
from prepare_evidence_workflow import prepare
from test_publication_evidence import signed, iso


def test_driver_fails_before_any_publication_credential_or_provider(monkeypatch):
    monkeypatch.setenv('ATLAS_PUBLICATION_TOKEN', 'DO-NOT-DISCLOSE')
    result = subprocess.run([sys.executable, str(driver.ROOT / 'tools/catalogue_evidence_driver.py') if hasattr(driver, 'ROOT') else 'tools/catalogue_evidence_driver.py', 'stage'], capture_output=True, text=True)
    assert result.returncode == 1
    assert result.stderr == 'catalogue_evidence_driver_rejected\n'
    assert 'DO-NOT-DISCLOSE' not in result.stdout + result.stderr
    assert driver.APPROVED_SUCCESSOR is None and driver.APPROVED_SUCCESSOR_SHA256 is None


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
    assert old['status'] == 'withdrawn' and old['manifest'] == original['entries'][0]['manifest']
    assert new['manifest']['version'] == '0.2.2' and new['release_asset_id'] == 693849044
    assert new['manifest']['distribution']['bundle_digest'] == 'sha256:2d66fc69b9cf9c70d7df117fe41bff3e3e056299f1908cde965e9e3f75e59abf'
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
    with pytest.raises(ValueError, match='owner_approval_required'):
        driver.approved_successor()
    monkeypatch.setattr(driver, 'APPROVED_SUCCESSOR_SHA256', digest(canonical_json(asdict(proposal))))
    assert driver.approved_successor() == proposal
    monkeypatch.setattr(driver, 'APPROVED_SUCCESSOR_SHA256', 'b' * 64)
    with pytest.raises(ValueError, match='pin_mismatch'):
        driver.approved_successor()


def test_successor_recovery_stays_disabled_even_with_valid_test_only_contract_approval(monkeypatch, capsys):
    proposal = driver.SuccessorApproval('a' * 64, 900, 300, 'SYNTHETIC historical decision',
        'SYNTHETIC selection decision', 'disabled-pending-permanent-archive-decision')
    monkeypatch.setattr(driver, 'APPROVED_SUCCESSOR', proposal)
    monkeypatch.setattr(driver, 'APPROVED_SUCCESSOR_SHA256', digest(canonical_json(asdict(proposal))))
    monkeypatch.setattr(sys, 'argv', ['catalogue_evidence_driver.py', 'recover'])
    monkeypatch.setenv('ATLAS_CATALOGUE_EVIDENCE_ENABLED', 'true')
    monkeypatch.setattr(driver, 'Github', lambda *a, **kw: pytest.fail('recovery reached credentials/provider'))
    with pytest.raises(SystemExit) as error:
        driver.main()
    assert error.value.code == 1
    assert capsys.readouterr().err == 'catalogue_evidence_driver_rejected\n'
