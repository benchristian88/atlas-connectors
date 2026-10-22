# SPDX-License-Identifier: Apache-2.0
"""Simulated GitHub/bootstrap transitions. These are NOT signature acceptance.

Original files are genuine frozen evidence; the transition fixture verifier below
models the original result. Actual crypto acceptance lives in test_publication_crypto.
"""
from copy import deepcopy
import base64
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from bootstrap_catalogue import *
from publication_contract import PublicationError, check_rulesets
from publication_github import Github
from publication_verify import Evidence
from test_publication_state import MemoryGithub, StructuralVerifier, structural_bundle, COMMIT, admit_model, recover_model

RAW = (ROOT / 'tests/fixtures/official_catalogue/catalogue-000001.json').read_bytes()
BUNDLE = (ROOT / 'tests/fixtures/publication/catalogue.sigstore.json').read_bytes()


class ModelVerifier(StructuralVerifier):
    def verify(self, raw, bundle, **context):
        if context['profile'] == 'catalogue':
            assert raw == RAW and bundle == BUNDLE and context['commit'] == SOURCE
            return Evidence('catalogue', digest(raw), SOURCE, 'simulated-original-result')
        return super().verify(raw, bundle, **context)


class BootstrapGithub(MemoryGithub):
    def __init__(self):
        super().__init__()
        self.releases, self.by_release, self.tags, self.data = {}, {}, {}, {}
        self.ref, self.marker, self.files = None, None, {}
        self.tree, self.commit = None, None
        self.verifier = ModelVerifier()
        self.args[0].update(bootstrap_operation='stage', bootstrap={'sequence': None, 'pointer_sha256': None})
        self.rules.append({'id': 5, 'name': 'atlas-bootstrap-lock', 'target': 'tag', 'enforcement': 'active',
            'conditions': {'ref_name': {'include': ['refs/tags/catalogue-bootstrap-root'], 'exclude': []}},
            'bypass_actors': [], 'rules': [{'type': 'update'}, {'type': 'deletion'}]})
        release = {'id': LEGACY_RELEASE_ID, 'url': f'{API}/releases/{LEGACY_RELEASE_ID}', 'tag_name': LEGACY_TAG,
                   'target_commitish': SOURCE, 'draft': False, 'prerelease': False, 'immutable': False}
        self.releases[LEGACY_RELEASE_ID] = release
        self.by_release[LEGACY_RELEASE_ID] = {}
        self.tags[LEGACY_TAG] = SOURCE
        for name, identity in LEGACY_ASSETS.items():
            asset = {'id': identity, 'name': name, 'size': len(RAW), 'digest': 'sha256:' + digest(RAW), 'state': 'uploaded'}
            self.by_release[LEGACY_RELEASE_ID][name] = asset
            self.data[identity] = RAW
        self.lose_response = None
        self.parent = []
        self.next_source = 'b' * 40

    def json(self, method, path, *, payload=None, **kwargs):
        if method == 'GET':
            if path in {'/actions/runs/70', '/actions/runs/70/attempts/1'}:
                return {**deepcopy(self.args[4]), 'id': 70, 'head_sha': self.next_source,
                        'url': f'{API}/actions/runs/70', 'html_url': f'https://github.com/{REPOSITORY}/actions/runs/70'}
            if path == '/git/ref/heads/catalogue-current':
                return None if self.ref is None else {'ref': 'refs/heads/catalogue-current', 'object': {'type': 'commit', 'sha': self.ref}}
            if path == '/git/ref/tags/catalogue-bootstrap-root':
                return None if self.marker is None else {'ref': 'refs/tags/catalogue-bootstrap-root', 'object': {'type': 'commit', 'sha': self.marker}}
            if path == '/git/matching-refs/tags/catalogue-':
                return [{'ref': 'refs/tags/' + tag} for tag in self.tags if tag.startswith('catalogue-')]
            if path.startswith('/releases?'):
                return deepcopy(list(self.releases.values()))
            if path.startswith('/git/commits/'):
                return deepcopy(self.commit)
            if path.startswith('/git/trees/'):
                return deepcopy(self.tree)
            if path.startswith('/contents/'):
                name = path.split('/')[2].split('?')[0]
                raw = self.files[name]
                return {'type': 'file', 'path': name, 'encoding': 'base64', 'size': len(raw),
                        'content': base64.b64encode(raw).decode()}
        if method == 'POST' and path == '/releases':
            value = super().json(method, path, payload=payload, **kwargs)
            self.releases[value['id']].update(target_commitish=SOURCE, body=payload['body'])
            self.tags.pop(TAG)  # Draft creation need not create its tag.
            result = deepcopy(self.releases[value['id']])
        elif method == 'PATCH' and path.startswith('/releases/'):
            assert payload == {'draft': False, 'make_latest': 'false'}
            result = super().json(method, path, payload=payload, **kwargs)
            self.tags[TAG] = SOURCE
        elif method == 'POST' and path == '/git/trees':
            assert set(payload) == {'tree'}
            rows = []
            self.files = {}
            for row in payload['tree']:
                raw = row['content'].encode()
                self.files[row['path']] = raw
                rows.append({k: v for k, v in row.items() if k != 'content'} | {
                    'sha': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()})
            self.tree = {'sha': 'c'*40, 'truncated': False, 'tree': rows}
            self.writes.append(('tree', payload))
            result = self.tree
        elif method == 'POST' and path == '/git/commits':
            assert payload['parents'] == []
            self.commit = {'sha': 'd'*40, 'parents': self.parent, 'tree': {'sha': self.tree['sha']}}
            self.writes.append(('commit', payload))
            result = self.commit
        elif method == 'POST' and path == '/git/refs':
            assert 'force' not in payload
            if payload['ref'] == 'refs/tags/catalogue-bootstrap-root':
                assert self.marker is None
                self.marker = payload['sha']
            else:
                assert payload['ref'] == 'refs/heads/catalogue-current' and self.ref is None
                assert self.release(TAG)['immutable']
                self.ref = payload['sha']
            self.writes.append(('ref', payload))
            result = {}
        else:
            return super().json(method, path, payload=payload, **kwargs)
        if self.lose_response == (method, path):
            raise PublicationError('github_transport_failure')
        return deepcopy(result)

    def channel(self):
        return Github.channel(self)


@pytest.fixture
def bootstrap():
    api = BootstrapGithub()
    publisher = BootstrapPublisher(api, api.verifier, api.args[0], 60, source_commit=COMMIT,
                                   token_identity=api.token_identity)
    admit_model(publisher)
    return api, publisher


def sealed(publisher):
    stage = publisher.stage_bootstrap()
    bundle = stage.bundle or structural_bundle(stage.pointer, 'pointer', 'current.json')
    receipt = publisher.seal_bootstrap(stage.pointer, bundle)
    return stage, receipt


def approve(api, publisher, stage):
    publisher.policy.update(bootstrap_operation='activate', bootstrap={'sequence': 1, 'pointer_sha256': digest(stage.pointer)})
    publisher.run_id = 70
    publisher.source_commit = api.next_source
    api.args[2]['commit']['sha'] = api.next_source
    admit_model(publisher)


def test_empty_history_preflight_has_no_writes(bootstrap):
    api, publisher = bootstrap
    assert publisher.preflight() == (RAW, BUNDLE, None)
    assert api.writes == []


def test_two_dispatch_activation_exact_assets_root_and_receipt(bootstrap):
    api, publisher = bootstrap
    legacy = deepcopy((api.releases[LEGACY_RELEASE_ID], api.by_release[LEGACY_RELEASE_ID]))
    stage, staged = sealed(publisher)
    assert staged['result'] == 'staged_requires_separate_approval'
    assert not staged['immutable'] and staged['channel_commit'] is None
    assert api.release(TAG)['draft'] and api.ref is None
    assert parse_pointer(stage.pointer)['previous_pointer_sha256'] is None
    assert digest(stage.pointer) != CATALOGUE_SHA256
    approve(api, publisher, stage)
    result = publisher.activate_bootstrap()
    assert result['channel_commit'] == api.ref == api.marker
    assert result['immutable'] and result['published'] and result['selection_run_id'] == 60
    assert result['authorization_run_id'] == 70 and not result['package_eligibility_granted']
    assert result['legacy_package_warning'] == WARNING
    assert legacy == (api.releases[LEGACY_RELEASE_ID], api.by_release[LEGACY_RELEASE_ID])
    assert set(api.assets(api.release(TAG))) == ASSETS
    assert api.asset_bytes(api.assets(api.release(TAG))[NAME], 10585) == RAW
    assert all(w[0] != 'pointer' for w in api.writes)  # No ordinary CAS or force update.


@pytest.mark.parametrize('name', sorted(ASSETS))
def test_partial_draft_exact_byte_resume(bootstrap, name):
    api, publisher = bootstrap
    api.fail_upload = name
    with pytest.raises(PublicationError, match='upload_failed'):
        sealed(publisher)
    existing = deepcopy(api.by_release[api.release(TAG)['id']])
    api.fail_upload = None
    stage, _ = sealed(publisher)
    assert all(api.by_release[stage.release_id][n] == a for n, a in existing.items())
    assert len(api.releases) == 2
    writes = deepcopy(api.writes)
    sealed(publisher)
    assert api.writes == writes


@pytest.mark.parametrize('mutation,code', [
    (lambda a: setattr(a, 'ref', 'e'*40), 'current_exists'),
    (lambda a: setattr(a, 'marker', 'e'*40), 'consumed'),
    (lambda a: a.new_release('catalogue-000002'), 'historical_ref_conflict'),
    (lambda a: a.tags.update({TAG: SOURCE}), 'orphan_tag'),
    (lambda a: a.tags.update({LEGACY_TAG: COMMIT}), 'tag_source'),
    (lambda a: a.args[4]['actor'].update(id=99), 'triggering_identity'),
    (lambda a: a.args[5].update(run_attempt=2), 'fresh_dispatch'),
    (lambda a: a.args[8]['check_runs'][0].update(conclusion='failure'), 'ci_failed'),
    (lambda a: a.args[2]['commit'].update(sha='f'*40), 'source_changed'),
    (lambda a: a.args[3].update(can_admins_bypass=True), 'environment_protection'),
    (lambda a: a.args[3].update(protection_rules=[{'type': 'required_reviewers'}]), 'environment_reviewers'),
    (lambda a: a.rules.pop(), 'ruleset_missing'),
    (lambda a: a.rules[4]['bypass_actors'].append({'actor_id': 30}), 'ruleset_bypass'),
    (lambda a: a.rules[2].update(enforcement='disabled'), 'ruleset_scope'),
    (lambda a: a.app['permissions'].update(workflows='write'), 'app_identity'),
    (lambda a: a.token_identity.update(installation_id=999), 'app_installation'),
    (lambda a: a.app_scope.update(total_count=2), 'app_scope'),
    (lambda a: setattr(a, 'immutable_enabled', False), 'not_enabled'),
])
def test_bootstrap_uses_p1_authority_and_history_gates(bootstrap, mutation, code):
    api, publisher = bootstrap
    mutation(api)
    with pytest.raises(PublicationError, match=code): publisher.stage_bootstrap()
    assert not api.writes


def test_wrong_draft_body_source_or_existing_bytes_never_overwritten(bootstrap):
    api, publisher = bootstrap
    stage = publisher.stage_bootstrap()
    release = api.releases[stage.release_id]
    writes = deepcopy(api.writes)
    for field, value in [('body', 'foreign operation'), ('target_commitish', COMMIT)]:
        old = release[field]
        release[field] = value
        with pytest.raises(PublicationError, match='release_conflict'): publisher.stage_bootstrap()
        release[field] = old
    asset = api.by_release[stage.release_id][NAME]
    api.data[asset['id']] = RAW[:-1] + b' '
    with pytest.raises(PublicationError): publisher.stage_bootstrap()
    assert api.writes == writes


def test_missing_wrong_selection_and_catalogue_bundle_cannot_seal(bootstrap):
    api, publisher = bootstrap
    stage = publisher.stage_bootstrap()
    for bundle in [b'{}', BUNDLE, structural_bundle(stage.pointer, 'catalogue', 'current.json')]:
        with pytest.raises(PublicationError): publisher.seal_bootstrap(stage.pointer, bundle)
    assert api.release(TAG)['draft'] and api.ref is None


@pytest.mark.parametrize('field,value', [('release_id', 9), ('asset_id', 9), ('sha256', 'f'*64)])
def test_wrong_pointer_binding_rejected(bootstrap, field, value):
    api, publisher = bootstrap
    stage = publisher.stage_bootstrap()
    pointer = pointer_bytes({**parse_pointer(stage.pointer), field: value})
    with pytest.raises(PublicationError, match='pointer_changed'):
        publisher.seal_bootstrap(pointer, structural_bundle(pointer, 'pointer', 'current.json'))
    assert api.release(TAG)['draft']


def test_activation_requires_actual_digest_and_separate_revision_dispatch(bootstrap):
    api, publisher = bootstrap
    stage, _ = sealed(publisher)
    publisher.policy.update(bootstrap_operation='activate', bootstrap={'sequence': 1, 'pointer_sha256': 'f'*64})
    admit_model(publisher)
    with pytest.raises(PublicationError, match='approval_mismatch'): publisher.activate_bootstrap()
    publisher.policy['bootstrap']['pointer_sha256'] = digest(stage.pointer)
    admit_model(publisher)
    with pytest.raises(PublicationError, match='separate_approval'): publisher.activate_bootstrap()
    assert api.release(TAG)['draft']


@pytest.mark.parametrize('lost', ['draft', 'finalise', 'root'])
def test_ambiguous_writes_reread_without_duplicate_release_or_ref(bootstrap, lost):
    api, publisher = bootstrap
    if lost == 'draft':
        api.lose_response = ('POST', '/releases')
        with pytest.raises(PublicationError): publisher.stage_bootstrap()
        api.lose_response = None
    stage, _ = sealed(publisher)
    approve(api, publisher, stage)
    if lost == 'finalise':
        api.lose_response = ('PATCH', f'/releases/{stage.release_id}')
        with pytest.raises(PublicationError): publisher.activate_bootstrap()
        assert api.release(TAG)['immutable'] and api.ref is None
        api.lose_response = None  # Fresh authorized dispatch, never Actions rerun.
    elif lost == 'root':
        # Only fail the branch creation, not the prior fence creation.
        original = api.json
        def response(method, path, **kwargs):
            value = original(method, path, **kwargs)
            if method == 'POST' and path == '/git/refs' and kwargs['payload']['ref'].startswith('refs/heads/'):
                raise PublicationError('github_transport_failure')
            return value
        api.json = response
    assert publisher.activate_bootstrap()['result'] == 'bootstrapped'
    assert len(api.releases) == 2
    assert sum(w[0] == 'draft' for w in api.writes) == 1
    assert sum(w[0] == 'ref' for w in api.writes) == 2


def test_consumed_root_never_reopens_even_after_branch_loss(bootstrap):
    api, publisher = bootstrap
    stage, _ = sealed(publisher)
    approve(api, publisher, stage)
    publisher.activate_bootstrap()
    writes = deepcopy(api.writes)
    with pytest.raises(PublicationError, match='current_exists'): publisher.activate_bootstrap()
    api.ref = None
    with pytest.raises(PublicationError, match='consumed'): publisher.activate_bootstrap()
    assert api.writes == writes


def test_marker_response_loss_requires_review_no_automatic_branch_retry(bootstrap):
    api, publisher = bootstrap
    stage, _ = sealed(publisher)
    approve(api, publisher, stage)
    api.lose_response = ('POST', '/git/refs')
    with pytest.raises(PublicationError): publisher.activate_bootstrap()
    assert api.marker is not None and api.ref is None
    api.lose_response = None
    with pytest.raises(PublicationError, match='consumed'): publisher.activate_bootstrap()


@pytest.mark.parametrize('mutable,parent', [(True, []), (False, [{'sha': 'f'*40}])])
def test_mutable_or_nonroot_never_selected(bootstrap, mutable, parent):
    api, publisher = bootstrap
    stage, _ = sealed(publisher)
    approve(api, publisher, stage)
    api.mutable_finalize, api.parent = mutable, parent
    with pytest.raises(PublicationError, match='not_immutable|root_parent'): publisher.activate_bootstrap()
    assert api.ref is None and api.marker is None


def test_normal_publish_recover_stay_closed_before_bootstrap(bootstrap):
    api, publisher = bootstrap
    normal = Publisher(api, api.verifier, api.args[0], 60, source_commit=COMMIT, token_identity=api.token_identity)
    for operation in [lambda: normal.stage(RAW), lambda: recover_model(normal)]:
        with pytest.raises(PublicationError, match='approved_bootstrap_required'): operation()
    # Even approved pins alone cannot initialize history via ordinary recover.
    api.args[0]['bootstrap'] = {'sequence': 1, 'pointer_sha256': 'f'*64}
    with pytest.raises(PublicationError, match='approved_bootstrap_required'): recover_model(normal)
    assert not api.writes


def test_legacy_entry_is_not_promoted_through_package_gate(bootstrap):
    api, publisher = bootstrap
    with pytest.raises(PublicationError): publisher.packages(parse_catalogue(RAW))
    assert not api.writes
    assert parse_catalogue(RAW)['entries'][0]['status'] == 'active'


def test_local_disabled_preflight_and_unauthorized_inputs(bootstrap):
    api, publisher = bootstrap
    policy = deepcopy(publisher.policy)
    policy.update(enabled=False, bootstrap_operation='disabled')
    result = local_preflight(policy, api.verifier)
    assert result['enabled'] is False and result['bootstrap_operation'] == 'disabled'
    assert result['remote_checks_performed'] is False
    for operation in ['bootstrap', 'publish', 'recover']:
        with pytest.raises(PublicationError, match='^publication_disabled$'):
            check_policy(policy, operation=operation)
    assert not api.writes
    for operation in ['BOOTSTRAP', 'bootstrap-any-source', '', None]:
        with pytest.raises(PublicationError): check_policy(api.args[0], operation=operation)


def test_checked_in_policy_authorizes_only_bootstrap_staging(bootstrap):
    api, _ = bootstrap
    policy = json.loads((ROOT / 'catalogue/publication/policy.json').read_bytes())
    assert policy['enabled'] is True and policy['bootstrap_operation'] == 'stage'
    assert policy['bootstrap'] == {'sequence': None, 'pointer_sha256': None}
    check_policy(policy, operation='bootstrap')
    assert local_preflight(policy, api.verifier)['remote_checks_performed'] is False
    for operation in ['publish', 'recover']:
        with pytest.raises(PublicationError, match='^approved_bootstrap_required$'):
            check_policy(policy, operation=operation)


@pytest.mark.parametrize('pins', [
    {'sequence': 1, 'pointer_sha256': None},
    {'sequence': None, 'pointer_sha256': 'f'*64},
    {'sequence': 1, 'pointer_sha256': 'f'*64},
    {'sequence': None}, {'pointer_sha256': None},
])
def test_staging_requires_both_pins_explicitly_null(bootstrap, pins):
    _, publisher = bootstrap
    publisher.policy['bootstrap'] = pins
    with pytest.raises(PublicationError, match='^bootstrap_staging_pins_must_be_unset$'):
        check_policy(publisher.policy, operation='bootstrap')


@pytest.mark.parametrize('enabled,mode,code', [
    (False, 'disabled', 'publication_disabled'),
    (False, 'stage', 'publication_disabled'),
    (False, 'activate', 'publication_disabled'),
    (False, 'unknown', 'publication_disabled'),
    (True, 'disabled', 'bootstrap_operation_disabled'),
    (True, 'unknown', 'bootstrap_operation_disabled'),
    (True, None, 'bootstrap_operation_disabled'),
    (True, 'activate', 'bootstrap_sequence'),  # Null pins do not authorize activation.
    (1, 'stage', 'publication_disabled'),
    ('true', 'stage', 'publication_disabled'),
    (None, 'stage', 'publication_disabled'),
])
def test_invalid_bootstrap_policy_fails_before_api_access(bootstrap, monkeypatch, enabled, mode, code):
    api, publisher = bootstrap
    publisher.policy.update(enabled=enabled, bootstrap_operation=mode)
    def forbidden(*args, **kwargs): pytest.fail('invalid policy reached GitHub')
    monkeypatch.setattr(api, 'json', forbidden)
    with pytest.raises(PublicationError, match='^' + code + '$'):
        publisher.preflight()
    assert not api.writes


def test_stage_and_seal_cannot_finalise_or_create_bootstrap_refs(bootstrap, monkeypatch):
    api, publisher = bootstrap
    original = api.json
    def draft_only(method, path, **kwargs):
        if method != 'GET':
            assert (method, path) == ('POST', '/releases')
            assert kwargs['payload']['draft'] is True
        return original(method, path, **kwargs)
    monkeypatch.setattr(api, 'json', draft_only)
    _, receipt = sealed(publisher)
    assert receipt['result'] == 'staged_requires_separate_approval'
    assert not receipt['published'] and not receipt['immutable']
    assert receipt['channel_commit'] is None
    assert api.release(TAG)['draft'] and api.ref is None and api.marker is None
    assert api.tree is None and api.commit is None
    def forbidden(*args, **kwargs): pytest.fail('stage policy activation reached GitHub')
    monkeypatch.setattr(api, 'json', forbidden)
    with pytest.raises(PublicationError, match='^bootstrap_activation_not_authorized$'):
        publisher.activate_bootstrap()


def test_source_byte_manifest_and_bundle_changes_rejected_before_verification(bootstrap):
    _, publisher = bootstrap
    modified = parse_catalogue(RAW)
    modified['entries'][0]['manifest']['description'] = 'changed'
    for raw, bundle in [(RAW+b' ', BUNDLE), (canonical_json(modified), BUNDLE), (RAW, BUNDLE+b' ')]:
        with pytest.raises(PublicationError, match='historical'): verify_source(publisher.verifier, raw, bundle)


@pytest.mark.parametrize('code', ['github_rate_limited', 'github_request_failed', 'github_transport_failure'])
def test_read_failure_cannot_authorize_writes(bootstrap, monkeypatch, code):
    api, publisher = bootstrap
    original = api.json
    def response(method, path, **kwargs):
        if path == '/immutable-releases': raise PublicationError(code)
        return original(method, path, **kwargs)
    monkeypatch.setattr(api, 'json', response)
    with pytest.raises(PublicationError, match=code): publisher.stage_bootstrap()
    assert not api.writes


@pytest.mark.parametrize('mutation,code', [
    (lambda a: a.args[4].update(path='.github/workflows/catalogue.yml'), 'untrusted_publication_run'),
    (lambda a: a.args[4].update(event='push'), 'untrusted_publication_run'),
    (lambda a: a.args[5]['repository'].update(id=1), 'publication_repository'),
    (lambda a: a.args[5].update(head_branch='dev'), 'untrusted_publication_run'),
    (lambda a: a.args[3].update(id=999), 'environment_protection'),
    (lambda a: a.args[4]['triggering_actor'].update(id=99), 'triggering_identity'),
    (lambda a: a.args[5].clear(), 'invalid_run_identity'),
    (lambda a: a.args[0].update(authorization_mode='other'), 'authorization_mode'),
    (lambda a: a.args[0].update(enabled=False), 'disabled'),
])
def test_more_missing_or_inconsistent_authority_evidence(bootstrap, mutation, code):
    api, publisher = bootstrap
    mutation(api)
    with pytest.raises(PublicationError, match=code): publisher.stage_bootstrap()
    assert not api.writes


@pytest.mark.parametrize('operation', ['stage', 'activate'])
def test_conflicting_extra_draft_or_finalised_release(bootstrap, operation):
    api, publisher = bootstrap
    stage, _ = sealed(publisher)
    if operation == 'activate': approve(api, publisher, stage)
    duplicate = deepcopy(api.releases[stage.release_id])
    duplicate['id'] += 100
    api.releases[duplicate['id']] = duplicate
    with pytest.raises(PublicationError, match='duplicate_release'): publisher.preflight()


def test_main_advances_during_staging_no_finalization(bootstrap, monkeypatch):
    api, publisher = bootstrap
    original = api.upload
    def upload(release, name, raw):
        result = original(release, name, raw)
        api.args[2]['commit']['sha'] = 'f'*40
        return result
    monkeypatch.setattr(api, 'upload', upload)
    with pytest.raises(PublicationError, match='source_changed'): sealed(publisher)
    assert api.release(TAG)['draft'] and api.ref is None


def test_current_appears_during_staging(bootstrap, monkeypatch):
    api, publisher = bootstrap
    original = api.upload
    def upload(release, name, raw):
        result = original(release, name, raw)
        api.ref = 'f'*40
        return result
    monkeypatch.setattr(api, 'upload', upload)
    with pytest.raises(PublicationError, match='current_exists'): publisher.stage_bootstrap()
    assert api.release(TAG)['draft']


def test_conflicting_root_after_ref_creation_fails(bootstrap, monkeypatch):
    api, publisher = bootstrap
    stage, _ = sealed(publisher)
    approve(api, publisher, stage)
    original = api.json
    def response(method, path, **kwargs):
        result = original(method, path, **kwargs)
        if method == 'POST' and path == '/git/refs' and kwargs['payload']['ref'].startswith('refs/heads/'):
            api.ref = 'f'*40
        return result
    monkeypatch.setattr(api, 'json', response)
    with pytest.raises(PublicationError): publisher.activate_bootstrap()
    assert api.ref == 'f'*40  # Never repaired or force-updated.


@pytest.mark.parametrize('change', [
    lambda a: a.tree['tree'].append({'path': 'extra', 'type': 'blob', 'mode': '100644', 'sha': 'f'*40}),
    lambda a: a.tree['tree'][0].update(mode='120000'),
    lambda a: a.tree['tree'][0].update(sha='f'*40),
])
def test_root_tree_must_contain_only_exact_ordinary_files(bootstrap, monkeypatch, change):
    api, publisher = bootstrap
    stage, _ = sealed(publisher)
    approve(api, publisher, stage)
    original = api.json
    def response(method, path, **kwargs):
        result = original(method, path, **kwargs)
        if method == 'POST' and path == '/git/trees': change(api)
        return result
    monkeypatch.setattr(api, 'json', response)
    with pytest.raises(PublicationError, match='root_tree|root_bytes'): publisher.activate_bootstrap()
    assert api.ref is None and api.marker is None


def test_missing_selection_cannot_activate(bootstrap):
    api, publisher = bootstrap
    stage = publisher.stage_bootstrap()
    approve(api, publisher, stage)
    with pytest.raises(PublicationError, match='asset_set'): publisher.activate_bootstrap()
    assert api.release(TAG)['draft']


def test_interrupted_signing_resumes_after_main_advances(bootstrap):
    api, publisher = bootstrap
    first = publisher.stage_bootstrap()
    publisher.run_id, publisher.source_commit = 70, api.next_source
    api.args[2]['commit']['sha'] = api.next_source
    admit_model(publisher)
    second = publisher.stage_bootstrap()
    assert first == second
    bundle = structural_bundle(second.pointer, 'pointer', 'current.json', commit=api.next_source, run=70)
    assert publisher.seal_bootstrap(second.pointer, bundle)['selection_run_id'] == 70
    assert api.release(TAG)['target_commitish'] == SOURCE


def test_frozen_finalised_release_cannot_resume_staging(bootstrap):
    api, publisher = bootstrap
    stage, _ = sealed(publisher)
    api.releases[stage.release_id].update(draft=False, immutable=True)
    api.tags[TAG] = SOURCE
    with pytest.raises(PublicationError, match='requires_activation'): publisher.stage_bootstrap()


def test_partial_snapshot_upload_timeout_rereads_asset_identity(bootstrap, monkeypatch):
    api, publisher = bootstrap
    original = api.upload
    def upload(*args):
        result = original(*args)
        raise PublicationError('github_transport_failure')
    monkeypatch.setattr(api, 'upload', upload)
    with pytest.raises(PublicationError): publisher.stage_bootstrap()
    asset = deepcopy(api.assets(api.release(TAG))[NAME])
    monkeypatch.setattr(api, 'upload', original)
    sealed(publisher)
    assert api.assets(api.release(TAG))[NAME] == asset


def test_workflow_dispatch_cli_path_simulated_provider_only(bootstrap, tmp_path, monkeypatch, capsys):
    """Execute workflow CLI phases with a model provider, never GitHub or OIDC."""
    import publish_catalogue as cli
    api, publisher = bootstrap
    policy_path = tmp_path / 'policy.json'
    policy_path.write_bytes(canonical_json(api.args[0]))
    monkeypatch.setattr(cli, 'POLICY', policy_path)
    monkeypatch.setattr(cli, 'ROOT', tmp_path)
    monkeypatch.setattr(cli, 'Github', lambda token, **kwargs: api)
    import publication_authorization as preflight
    monkeypatch.setattr(preflight, 'job_preflight', lambda *args, **kwargs: publisher.run_preflight)
    trust_path = tmp_path / 'catalogue/publication/verifier-trust.json'
    trust_path.parent.mkdir(parents=True)
    trust_path.write_text('{}')
    monkeypatch.setattr(cli, 'Verifier', lambda: api.verifier)
    def never_build(*args, **kwargs): pytest.fail('bootstrap must never invoke a builder')
    monkeypatch.setattr(cli.build_catalogue, 'build', never_build)
    for name, value in {'PUBLICATION_OPERATION': 'bootstrap', 'GITHUB_REPOSITORY': REPOSITORY,
                        'GITHUB_REF': 'refs/heads/main', 'GITHUB_EVENT_NAME': 'workflow_dispatch',
                        'GITHUB_RUN_ATTEMPT': '1', 'GITHUB_RUN_ID': '60', 'GITHUB_SHA': COMMIT,
                        'ATLAS_APP_SLUG': api.token_identity['app_slug'],
                        'ATLAS_APP_INSTALLATION_ID': str(api.token_identity['installation_id']),
                        'GITHUB_OUTPUT': str(tmp_path / 'output')}.items():
        monkeypatch.setenv(name, value)
    def run(phase):
        monkeypatch.setattr(sys, 'argv', ['publish_catalogue.py', phase])
        cli.main()
    run('authorize')
    assert not api.writes
    run('bootstrap-stage')
    files = tmp_path / 'dist/publication'
    assert (tmp_path / 'output').read_text() == 'needs_attestation=true\n'
    pointer = (files / 'current.json').read_bytes()
    (files / 'current.sigstore.json').write_bytes(structural_bundle(pointer, 'pointer', 'current.json'))
    run('bootstrap-seal')
    assert json.loads((files / 'receipt.json').read_bytes())['result'] == 'staged_requires_separate_approval'
    assert api.ref is None
    stage = Stage(pointer, None, parse_pointer(pointer)['release_id'])
    approve(api, publisher, stage)
    policy_path.write_bytes(canonical_json(api.args[0]))
    monkeypatch.setenv('GITHUB_RUN_ID', '70')
    monkeypatch.setenv('GITHUB_SHA', api.next_source)
    run('authorize')
    run('bootstrap-activate')
    assert json.loads((files / 'receipt.json').read_bytes())['result'] == 'bootstrapped'
    assert 'simulated-original-result' not in capsys.readouterr().out


@pytest.mark.parametrize('operation,phase', [('publish', 'bootstrap-stage'), ('recover', 'bootstrap-activate'),
    ('bootstrap', 'stage'), ('bootstrap', 'recover'), ('untrusted', 'authorize')])
def test_cli_rejects_cross_operation_phases_before_transport(monkeypatch, operation, phase):
    import publish_catalogue as cli
    monkeypatch.setenv('PUBLICATION_OPERATION', operation)
    monkeypatch.setattr(sys, 'argv', ['publish_catalogue.py', phase])
    def no_transport(*args): pytest.fail('invalid operation reached transport')
    monkeypatch.setattr(cli, 'Github', no_transport)
    with pytest.raises(SystemExit) as error: cli.main()
    assert error.value.code == 1


def test_workflow_bootstrap_has_fixed_dispatch_and_two_exclusive_modes():
    import yaml
    workflow = yaml.safe_load((ROOT / '.github/workflows/catalogue-publish.yml').read_text())
    triggers = workflow.get('on', workflow.get(True))
    assert set(triggers) == {'workflow_dispatch'}
    inputs = triggers['workflow_dispatch']['inputs']
    assert set(inputs) == {'operation', 'acceptance_only'}
    assert inputs['acceptance_only']['default'] is True
    assert inputs['operation']['options'] == ['publish', 'recover', 'bootstrap']
    assert inputs['operation']['default'] == 'publish'
    job = workflow['jobs']['publish']
    assert job['env']['PUBLICATION_OPERATION'] == '${{ inputs.operation }}'
    steps = job['steps']
    phases = {s.get('run'): s for s in steps}
    for phase in ['bootstrap-stage', 'bootstrap-seal']:
        assert phases['python tools/publish_catalogue.py ' + phase]['if'] == (
            "inputs.operation == 'bootstrap' && steps.policy.outputs.bootstrap_mode == 'stage'")
    assert phases['python tools/publish_catalogue.py bootstrap-activate']['if'].endswith("== 'activate'")
    mint = next(i for i, s in enumerate(steps) if s.get('id') == 'app')
    local = steps.index(phases['python tools/publish_catalogue.py bootstrap-preflight'])
    assert local < mint
    signer = next(s for s in steps if s.get('id') == 'attest')
    assert signer['with'] == {'subject-path': 'dist/publication/current.json'}
    assert "bootstrap_stage.outputs.needs_attestation == 'true'" in signer['if']
    assert 'bootstrap-activate' not in signer['if']


@pytest.mark.parametrize('endpoint', ['releases', 'refs'])
def test_bootstrap_inventory_overflow_is_not_absence(bootstrap, monkeypatch, endpoint):
    api, publisher = bootstrap
    original = api.json
    def response(method, path, **kwargs):
        if endpoint == 'releases' and path.startswith('/releases?'):
            return [{'tag_name': 'unrelated-package-v1', 'id': i} for i in range(100)]
        if endpoint == 'refs' and path == '/git/matching-refs/tags/catalogue-':
            return [{'ref': 'refs/tags/' + LEGACY_TAG} for _ in range(100)]
        return original(method, path, **kwargs)
    monkeypatch.setattr(api, 'json', response)
    with pytest.raises(PublicationError, match='release_limit|ref_limit'): publisher.stage_bootstrap()
    assert not api.writes


@pytest.mark.parametrize('name', ['current.json', 'current.sigstore.json', 'catalogue.sigstore.json'])
def test_finalisation_cannot_change_any_asset_identity(bootstrap, monkeypatch, name):
    api, publisher = bootstrap
    stage, _ = sealed(publisher)
    approve(api, publisher, stage)
    original = api.json
    def response(method, path, **kwargs):
        result = original(method, path, **kwargs)
        if method == 'PATCH' and path.startswith('/releases/'):
            asset = api.by_release[stage.release_id][name]
            old = asset['id']
            asset['id'] += 100
            api.data[asset['id']] = api.data[old]
        return result
    monkeypatch.setattr(api, 'json', response)
    with pytest.raises(PublicationError, match='finalisation_changed'): publisher.activate_bootstrap()
    assert api.ref is None and api.marker is None


def test_root_protection_removed_after_immutable_publication(bootstrap, monkeypatch):
    api, publisher = bootstrap
    stage, _ = sealed(publisher)
    approve(api, publisher, stage)
    original = api.json
    def response(method, path, **kwargs):
        result = original(method, path, **kwargs)
        if method == 'PATCH' and path.startswith('/releases/'):
            api.rules[4]['enforcement'] = 'disabled'
        return result
    monkeypatch.setattr(api, 'json', response)
    with pytest.raises(PublicationError, match='ruleset_scope'): publisher.activate_bootstrap()
    assert api.release(TAG)['immutable'] and api.ref is None and api.marker is None
