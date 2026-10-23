# SPDX-License-Identifier: Apache-2.0
"""Deterministic mocked provider state, NOT cryptographic or live GitHub acceptance."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit, parse_qs

import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from publication_contract import *
from publication_github import Github
from publication_verify import Evidence
from publish_catalogue import Publisher
from test_publication_contract import authority_fixture, rules_fixture, document, app_fixture

COMMIT = 'a' * 40


def structural_bundle(raw, profile, name, commit=COMMIT, run=60):
    return canonical_json({'TEST_ONLY_NO_SIGNATURE': True, 'sha256': digest(raw), 'profile': profile,
                           'name': name, 'commit': commit, 'run': run})


class StructuralVerifier:
    """Only models identity binding; never mistaken for Sigstore verification."""
    def verify(self, raw, bundle, *, profile, name, commit=None, tag=None):
        data = json.loads(bundle)
        require(data.get('TEST_ONLY_NO_SIGNATURE') is True and data.get('sha256') == digest(raw)
                and data.get('profile') == profile and data.get('name') == name
                and (commit is None or data.get('commit') == commit), 'mock_evidence_mismatch')
        return Evidence(profile, digest(raw), data['commit'],
                        f'https://github.com/{REPOSITORY}/actions/runs/{data["run"]}/attempts/1')


class MemoryGithub(Github):
    def __init__(self):
        self.draft_visibility = True
        self.args = authority_fixture()
        self.rules = rules_fixture()
        _, self.app, self.app_scope, self.token_identity = app_fixture()
        self.releases, self.data, self.by_release, self.tags = {}, {}, {}, {}
        self.counter = 1000
        self.writes = []
        self.fail_upload = None
        self.fail_finalize = False
        self.mutable_finalize = False
        self.fail_pointer = False
        self.immutable_enabled = True
        self.ref = '1'*40
        self.verifier = StructuralVerifier()
        previous = document()
        # Model only, not the legacy fixture or any real accepted publication.
        previous['entries'][0]['status'] = 'withdrawn'
        self.previous = canonical_json(previous)
        release = self.new_release('catalogue-000001')
        a = self.add(release, 'catalogue-000001.json', self.previous)
        self.add(release, 'catalogue.sigstore.json', structural_bundle(self.previous, 'catalogue', 'catalogue-000001.json'))
        pointer = pointer_bytes({'schema_version':'1.0', 'sequence':1, 'release_tag':'catalogue-000001',
                                 'release_id':release['id'], 'asset_id':a['id'], 'sha256':digest(self.previous),
                                 'previous_pointer_sha256':None})
        bundle = structural_bundle(pointer, 'pointer', 'current.json')
        self.files = {'current.json':pointer, 'current.sigstore.json':bundle}
        for name, raw in self.files.items():
            self.add(release, name, raw)
        release.update(draft=False, immutable=True)
        self.args[0]['bootstrap'] = {'sequence':1, 'pointer_sha256':digest(pointer)}

    def new_release(self, tag):
        self.counter += 1
        release = {'id':self.counter, 'url':f'{API}/releases/{self.counter}', 'tag_name':tag,
                   'target_commitish':COMMIT, 'draft':True, 'immutable':False, 'prerelease':False}
        self.releases[release['id']] = release
        self.by_release[release['id']] = {}
        self.tags[tag] = COMMIT
        return release

    def add(self, release, name, raw):
        self.counter += 1
        value = {'id':self.counter, 'name':name, 'size':len(raw), 'digest':'sha256:'+digest(raw), 'state':'uploaded'}
        self.data[value['id']] = raw
        self.by_release[release['id']][name] = value
        return value

    def request(self, method, path, *, payload=None, binary=None, **kwargs):
        if method == 'POST' and '/assets?name=' in path:
            name = parse_qs(urlsplit(path).query)['name'][0]
            if self.fail_upload == name:
                raise PublicationError('mock_upload_failed')
            release = self.releases[int(path.split('/')[2])]
            assert release['draft']
            assert name not in self.by_release[release['id']]
            self.writes.append(('upload', name))
            return canonical_json(self.add(release, name, binary))
        if method == 'GET' and path.startswith('/releases/assets/'):
            return self.data[int(path.split('/')[-1])]
        raise AssertionError((method,path))

    def json(self, method, path, *, payload=None, **kwargs):
        if method == 'GET':
            if path == '/': return deepcopy(self.args[1])
            if path == '/branches/main': return deepcopy(self.args[2])
            if path == '/environments/'+ENVIRONMENT: return deepcopy(self.args[3])
            if path == '/immutable-releases': return {'enabled':self.immutable_enabled}
            if path == '/rulesets?per_page=100': return [{'id':r['id']} for r in self.rules]
            if path.startswith('/rulesets/'): return deepcopy(self.rules[int(path.split('/')[-1])-1])
            if path.startswith('/compare/'):
                return {'status':'ahead','merge_base_commit':{'sha':COMMIT}}
            if path == '/environments/connector-release/deployment-branch-policies?per_page=100':
                return {'total_count':1,'branch_policies':[{'id':52,'name':'*-v*','type':'tag'}]}
            if path == '/environments/connector-release':
                env=deepcopy(self.args[3]); env.update(id=51,name='connector-release',deployment_branch_policy={'protected_branches':False,'custom_branch_policies':True}); return env
            if path == '/apps/publication-app': return deepcopy(self.app)
            if path == '/installation/repositories?per_page=100': return deepcopy(self.app_scope)
            if path == '/users/maintainer': return deepcopy(self.args[7])
            if path == '/users/publication-app%5Bbot%5D':
                return {'id': 31, 'type': 'Bot', 'login': 'publication-app[bot]'}
            if path in {'/actions/runs/61', '/actions/runs/61/attempts/1'}:
                run=deepcopy(self.args[4])
                actor={'id': 31, 'type': 'Bot', 'login': 'publication-app[bot]'}
                run.update(id=61, event='push', head_branch=self.package_tag, path='.github/workflows/release.yml',
                           workflow_id=81, actor=actor, triggering_actor=deepcopy(actor),
                           url=f'{API}/actions/runs/61', html_url=f'https://github.com/{REPOSITORY}/actions/runs/61')
                return run
            if path == '/actions/runs/60': return deepcopy(self.args[4])
            if path == '/actions/runs/60/attempts/1': return deepcopy(self.args[5])
            if path == '/actions/workflows/80': return deepcopy(self.args[6])
            if path == '/actions/workflows/81':
                return {**self.args[6], 'id': 81, 'path': '.github/workflows/release.yml', 'url': f'{API}/actions/workflows/81'}
            if path.startswith('/commits/') and '/check-runs?' in path:
                checks=deepcopy(self.args[8]); checks['check_runs'][0]['head_sha']=path.split('/')[2]; return checks
            if path.startswith('/git/ref/tags/'):
                if unquote(path.split('/')[-1]) not in self.tags and kwargs.get('missing'):
                    return None
                return {'object':{'sha':self.tags[unquote(path.split('/')[-1])], 'type':'commit'}}
            if path.startswith('/releases?per_page=100&page='):
                return deepcopy(list(self.releases.values()))
            if path.startswith('/releases/tags/'):
                tag = unquote(path.split('/')[-1])
                return deepcopy(next((r for r in self.releases.values() if r['tag_name']==tag), None))
            if path.startswith('/releases/'):
                identity = int(path.split('/')[2])
                if '/assets?' in path:
                    return deepcopy(list(self.by_release[identity].values()))
                return deepcopy(self.releases[identity])
        if method == 'POST' and path == '/releases':
            self.writes.append(('draft',payload['tag_name']))
            assert self.release(payload['tag_name']) is None
            return deepcopy(self.new_release(payload['tag_name']))
        if method == 'PATCH' and path.startswith('/releases/'):
            if self.fail_finalize:
                raise PublicationError('mock_finalize_failed')
            self.writes.append(('finalize',int(path.split('/')[-1])))
            release = self.releases[int(path.split('/')[-1])]
            release.update(draft=False, immutable=not self.mutable_finalize)
            return deepcopy(release)
        raise AssertionError((method,path))

    def attestation(self, raw, verifier, **context):
        bundle = structural_bundle(raw, context['profile'], context['name'], context.get('commit') or COMMIT,run=61 if context['profile']=='package' else 60)
        return bundle, verifier.verify(raw,bundle,**context)

    def channel(self):
        return self.ref, dict(self.files)

    def compare_and_swap(self, expected, files):
        if self.fail_pointer:
            raise PublicationError('mock_pointer_failed')
        require(expected==self.ref, 'channel_changed')
        pointer = parse_pointer(files['current.json'])
        assert self.releases[pointer['release_id']]['immutable'] is True
        self.ref = str(int(self.ref[0])+1)*40
        self.files = dict(files)
        self.writes.append(('pointer',self.ref))
        return self.ref


def admit_model(publisher, operation=None):
    """Synthetic admission only; real startup cryptography is tested separately."""
    if operation is not None:
        publisher.policy_operation = operation
    publisher.policy_raw = canonical_json(publisher.policy)
    publisher.run_preflight = {"source": {"commit": publisher.source_commit,
        "policy_sha256": digest(publisher.policy_raw)}, "execution": {"run_id": publisher.run_id,
        "run_attempt": 1, "operation": publisher.policy_operation, "acceptance_only": False},
        "rulesets": {"observations": deepcopy(publisher.api.rules)}}


def recover_model(publisher):
    admit_model(publisher, "recover")
    return publisher.recover()


@pytest.fixture
def state():
    api = MemoryGithub()
    publisher = Publisher(api, api.verifier, api.args[0], 60, source_commit=COMMIT, token_identity=api.token_identity)
    admit_model(publisher)
    next_doc = parse_catalogue(api.previous)
    next_doc['sequence'] = 2
    return api, publisher, canonical_json(next_doc)


def complete(publisher, raw):
    stage = publisher.stage(raw)
    bundle = stage.bundle or structural_bundle(stage.pointer,'pointer','current.json')
    return publisher.finish(raw,stage.pointer,bundle)


def test_publish_order_and_repeat_after_success(state):
    api,publisher,raw=state
    receipt=complete(publisher,raw)
    assert receipt['result']=='published'
    assert [w[0] for w in api.writes][-2:]==['finalize','pointer']
    writes=list(api.writes)
    assert complete(publisher,raw)['result']=='unchanged'
    assert api.writes==writes
    assert len(api.releases)==2


def test_preparation_and_staging_retry(state):
    api,publisher,raw=state
    one=publisher.stage(raw)
    writes=list(api.writes)
    assert publisher.stage(raw)==one
    assert api.writes==writes
    assert one.bundle is None


@pytest.mark.parametrize('name',['catalogue-000002.json','catalogue.sigstore.json','current.json','current.sigstore.json'])
def test_interrupted_upload_resumes_without_overwrite(state,name):
    api,publisher,raw=state
    before=dict(api.files)
    api.fail_upload=name
    with pytest.raises(PublicationError,match='upload_failed'):
        complete(publisher,raw)
    assert api.files==before
    api.fail_upload=None
    assert complete(publisher,raw)['result']=='published'


def test_finalize_failure_then_retry(state):
    api,publisher,raw=state
    api.fail_finalize=True
    with pytest.raises(PublicationError,match='finalize_failed'):
        complete(publisher,raw)
    assert parse_pointer(api.files['current.json'])['sequence']==1
    api.fail_finalize=False
    assert complete(publisher,raw)['result']=='published'


def test_mutable_finalization_never_selects_and_cannot_be_repaired_by_overwrite(state):
    api,publisher,raw=state
    api.mutable_finalize=True
    with pytest.raises(PublicationError,match='not_immutable'):
        complete(publisher,raw)
    assert parse_pointer(api.files['current.json'])['sequence']==1
    with pytest.raises(PublicationError,match='not_immutable'):
        complete(publisher,raw)


def test_snapshot_published_pointer_failed_then_resume_exact_history(state):
    api,publisher,raw=state
    api.fail_pointer=True
    with pytest.raises(PublicationError,match='pointer_failed'):
        complete(publisher,raw)
    release=api.release('catalogue-000002')
    assert release['immutable'] is True
    asset_ids=deepcopy(api.by_release[release['id']])
    api.fail_pointer=False
    assert complete(publisher,raw)['result']=='published'
    assert api.by_release[release['id']]==asset_ids


def test_wrong_pointer_authentication_never_finalizes(state):
    api,publisher,raw=state
    stage=publisher.stage(raw)
    wrong=structural_bundle(stage.pointer,'catalogue','current.json')
    with pytest.raises(PublicationError,match='mock_evidence'):
        publisher.finish(raw,stage.pointer,wrong)
    assert api.release('catalogue-000002')['draft'] is True


def test_stale_publisher_cannot_overwrite_newer_pointer(state):
    api,publisher,raw=state
    stale=publisher.stage(raw)
    complete(publisher,raw)
    newer=parse_catalogue(raw)
    newer['sequence']=3
    complete(publisher,canonical_json(newer))
    with pytest.raises(PublicationError,match='rollback'):
        publisher.finish(raw,stale.pointer,structural_bundle(stale.pointer,'pointer','current.json'))
    assert parse_pointer(api.files['current.json'])['sequence']==3


def test_current_changes_during_publication(state,monkeypatch):
    api,publisher,raw=state
    original=api.upload
    def race(*args):
        value=original(*args)
        api.ref='e'*40
        return value
    monkeypatch.setattr(api,'upload',race)
    with pytest.raises(PublicationError,match='channel_changed'):
        publisher.stage(raw)
    assert parse_pointer(api.files['current.json'])['sequence']==1


def test_duplicate_sequence_changed_bytes_and_gap(state):
    api,publisher,raw=state
    complete(publisher,raw)
    value=parse_catalogue(raw)
    value['generated_at']='2026-10-22T00:00:00Z'
    with pytest.raises(PublicationError,match='substitution'):
        publisher.stage(canonical_json(value))
    value['sequence']=4
    with pytest.raises(PublicationError,match='gap'):
        publisher.stage(canonical_json(value))


@pytest.mark.parametrize('mutation,code',[
    (lambda a:a.releases[next(iter(a.releases))].update(immutable=False),'not_immutable'),
    (lambda a:a.releases[next(iter(a.releases))].update(tag_name='other'),'release_identity'),
    (lambda a:a.by_release[next(iter(a.releases))]['catalogue-000001.json'].update(id=99),'asset_identity'),
    (lambda a:a.by_release[next(iter(a.releases))]['catalogue-000001.json'].update(digest='sha256:'+'f'*64),'bytes_mismatch'),
    (lambda a:a.by_release[next(iter(a.releases))].pop('catalogue.sigstore.json'),'attestation_missing'),
    (lambda a:a.by_release[next(iter(a.releases))].pop('current.json'),'release_evidence'),
    (lambda a:setattr(a,'immutable_enabled',False),'not_enabled'),
    (lambda a:a.args[5].clear(),'invalid_run_identity'),
    (lambda a:a.args[0].update(allowed_maintainer_id=None),'maintainer_unconfigured'),
    (lambda a:a.args[4]['triggering_actor'].update(id=99),'triggering_identity'),
    (lambda a:a.args[4].update(run_attempt=2),'fresh_dispatch'),
    (lambda a:a.args[2].update(protected=False),'unprotected'),
    (lambda a:a.rules[0].update(enforcement='disabled'),'ruleset_scope'),
    (lambda a:a.app.update(id=99),'app_identity'),
    (lambda a:a.app['permissions'].update(workflows='write'),'app_identity'),
    (lambda a:a.app_scope.update(total_count=2),'app_scope'),
    (lambda a:a.token_identity.update(installation_id=99),'app_installation'),
])
def test_provider_and_authority_failures_before_writes(state,mutation,code):
    api,publisher,raw=state
    mutation(api)
    with pytest.raises(PublicationError,match=code):
        publisher.stage(raw)
    assert api.writes==[]


def test_recover_rejects_temporary_bootstrap_app_permissions_before_writes(state):
    api, publisher, _ = state
    api.app['permissions']['workflows'] = 'write'
    with pytest.raises(PublicationError, match='publication_app_identity'):
        recover_model(publisher)
    assert api.writes == []


def test_conflicting_existing_draft_or_higher_snapshot(state):
    api,publisher,raw=state
    api.new_release('catalogue-000003')
    with pytest.raises(PublicationError,match='higher_snapshot'):
        publisher.stage(raw)


def test_wrong_staged_bytes_cannot_be_replaced(state):
    api,publisher,raw=state
    release=api.new_release('catalogue-000002')
    api.add(release,'catalogue-000002.json',raw+b' ')
    with pytest.raises(PublicationError):
        publisher.stage(raw)
    assert api.writes==[]


def test_historical_withdrawal_cannot_disappear_or_reactivate(state):
    api,publisher,raw=state
    value=parse_catalogue(raw)
    for entries,code in [([], 'missing'), (deepcopy(value['entries']), 'reactivated')]:
        if entries: entries[0]['status']='active'
        value['entries']=entries
        with pytest.raises(PublicationError,match=code):
            publisher.stage(canonical_json(value))


def test_dynamic_future_connector_structural_publication(state):
    api,publisher,raw=state
    value=parse_catalogue(raw)
    hypothetical=deepcopy(value['entries'][0])
    manifest=hypothetical['manifest']
    manifest['id']='future-hypervisor'
    manifest['version']='12.3.4'
    hypothetical.update(release_tag='future-hypervisor-v12.3.4',release_asset_id=987654)
    manifest['distribution']['asset_uri']=f'https://github.com/{REPOSITORY}/releases/download/future-hypervisor-v12.3.4/future-hypervisor-12.3.4.tar.gz'
    # Withdrawn structural fixture does not fabricate installable package proof.
    value['entries'].append(hypothetical)
    value['entries'].sort(key=lambda e:(e['manifest']['id'],e['manifest']['version']))
    assert complete(publisher,canonical_json(value))['result']=='published'


def active_future(api, raw):
    value=parse_catalogue(raw)
    entry=deepcopy(value['entries'][0])
    manifest=entry['manifest']
    manifest.update(id='future-hypervisor',version='12.3.4')
    manifest['distribution']['provenance']['source_commit']=COMMIT
    api.package_tag='future-hypervisor-v12.3.4'
    package=api.new_release(api.package_tag)
    archive=b'synthetic archive bytes; never executed'
    asset=api.add(package,'future-hypervisor-12.3.4.tar.gz',archive)
    package.update(draft=False,immutable=True)
    entry.update(status='active',release_tag=api.package_tag,release_asset_id=asset['id'])
    manifest['distribution']['bundle_digest']='sha256:'+digest(archive)
    manifest['distribution']['asset_uri']=f'https://github.com/{REPOSITORY}/releases/download/{api.package_tag}/future-hypervisor-12.3.4.tar.gz'
    value['entries'].append(entry)
    value['entries'].sort(key=lambda e:(e['manifest']['id'],e['manifest']['version']))
    return value,package,asset


def test_future_active_connector_uses_generic_package_checks_mock_evidence(state):
    api,publisher,raw=state
    value,_,_=active_future(api,raw)
    assert complete(publisher,canonical_json(value))['result']=='published'


@pytest.mark.parametrize('mutation,code',[
    (lambda value,release,asset:release.update(immutable=False),'not_immutable'),
    (lambda value,release,asset:asset.update(id=999),'asset_identity'),
    (lambda value,release,asset:value['entries'][0]['manifest']['distribution'].update(bundle_digest='sha256:'+'f'*64),'package_digest'),
    (lambda value,release,asset:value['entries'][0]['manifest']['source_versions'].update(qualification='unqualified',qualified_versions=[]),'unqualified'),
])
def test_active_package_rejections(state,mutation,code):
    api,publisher,raw=state
    value,release,asset=active_future(api,raw)
    mutation(value,release,asset)
    with pytest.raises(PublicationError,match=code):publisher.stage(canonical_json(value))
    assert not api.writes


def test_recovery_uses_original_snapshot_not_rebuilt_head(state):
    api,publisher,raw=state
    api.fail_pointer=True
    with pytest.raises(PublicationError):complete(publisher,raw)
    api.fail_pointer=False
    api.args[2]['commit']['sha']='b'*40
    # Historical run 60 stays at the signing commit. A fresh maintainer dispatch authorizes recovery.
    original=api.json
    def response(method,path,**kwargs):
        if path in {'/actions/runs/70', '/actions/runs/70/attempts/1'}:
            return {**api.args[4], 'id':70, 'head_sha':'b'*40, 'url':f'{API}/actions/runs/70',
                    'html_url':f'https://github.com/{REPOSITORY}/actions/runs/70'}
        return original(method,path,**kwargs)
    api.json=response
    publisher.run_id=70
    publisher.source_commit='b'*40
    before=deepcopy(api.by_release)
    assert recover_model(publisher)['result']=='recovered'
    assert api.by_release==before
    assert recover_model(publisher)['result']=='no_interrupted_snapshot'


def test_recovery_refuses_unfinished_mutable_release(state):
    api,publisher,raw=state
    publisher.stage(raw)
    with pytest.raises(PublicationError,match='not_immutable'):recover_model(publisher)


@pytest.mark.parametrize('change', [lambda p:p.update(enabled=False),
    lambda p:p.update(allowed_maintainer_id=None), lambda p:p.update(app_installation_id=None),
    lambda p:p.update(bootstrap={'sequence':None,'pointer_sha256':None}),
    lambda p:p.update(authorization_mode='independent-reviewer-v2')])
def test_unconfigured_startup_never_contacts_github(state, change, monkeypatch):
    api,publisher,raw=state
    change(api.args[0])
    def forbidden(*args, **kwargs):
        pytest.fail('disabled or incomplete policy must fail before API access')
    monkeypatch.setattr(api, 'json', forbidden)
    with pytest.raises(PublicationError): publisher.stage(raw)
    assert api.writes == []


def test_app_cannot_impersonate_maintainer_even_with_expected_credentials(state):
    api,publisher,raw=state
    for run in (api.args[4], api.args[5]):
        run['actor'] = run['triggering_actor'] = {'id':31,'type':'Bot','login':'publication-app[bot]'}
    with pytest.raises(PublicationError, match='unsupported_actor'):
        publisher.stage(raw)
    assert api.writes == []


def test_protections_removed_before_finalization_prevent_publication(state, monkeypatch):
    api,publisher,raw=state
    original=api.upload
    def disable_after_signing(release, name, body):
        result=original(release,name,body)
        if name == 'current.sigstore.json': api.rules[0]['enforcement']='disabled'
        return result
    monkeypatch.setattr(api,'upload',disable_after_signing)
    with pytest.raises(PublicationError,match='ruleset_scope'): complete(publisher,raw)
    assert api.release('catalogue-000002')['draft'] is True
    assert parse_pointer(api.files['current.json'])['sequence'] == 1


def test_selection_source_must_match_authenticated_attestation(state):
    api,publisher,_=state
    bundle=structural_bundle(api.files['current.json'],'pointer','current.json',commit='b'*40)
    with pytest.raises(PublicationError,match='source_changed'):
        publisher.selection(api.files['current.json'],bundle)
    assert api.writes == []


def test_unexpected_package_app_actor_is_rejected(state,monkeypatch):
    api,publisher,raw=state
    value,_,_=active_future(api,raw)
    original=api.json
    def response(method,path,**kwargs):
        result=original(method,path,**kwargs)
        if path.startswith('/actions/runs/61'):
            result['triggering_actor']['id']=999
        return result
    monkeypatch.setattr(api,'json',response)
    with pytest.raises(PublicationError,match='triggering_identity'):
        publisher.stage(canonical_json(value))
    assert api.writes == []


def test_current_protection_removed_after_finalization_leaves_snapshot_recoverable(state,monkeypatch):
    api,publisher,raw=state
    original=api.json
    def disable_after_finalize(method,path,**kwargs):
        result=original(method,path,**kwargs)
        if method == 'PATCH' and path.startswith('/releases/'):
            api.rules[1]['enforcement']='disabled'
        return result
    monkeypatch.setattr(api,'json',disable_after_finalize)
    with pytest.raises(PublicationError,match='ruleset_scope'): complete(publisher,raw)
    assert api.release('catalogue-000002')['immutable'] is True
    assert parse_pointer(api.files['current.json'])['sequence'] == 1
    api.rules[1]['enforcement']='active'
    assert recover_model(publisher)['result'] == 'recovered'


@pytest.mark.parametrize('evidence', [None, {}, {'total_count':0,'branch_policies':[]},
    {'total_count':1,'branch_policies':[{'id':52,'name':'*','type':'tag'}]},
    {'total_count':1,'branch_policies':[{'id':52,'name':'*-v*','type':'branch'}]}])
def test_package_environment_restriction_evidence_failures(state,monkeypatch,evidence):
    api,publisher,raw=state
    value,_,_=active_future(api,raw)
    original=api.json
    def response(method,path,**kwargs):
        if path.endswith('/deployment-branch-policies?per_page=100'): return evidence
        return original(method,path,**kwargs)
    monkeypatch.setattr(api,'json',response)
    with pytest.raises(PublicationError,match='package_environment_tag_policy'):
        publisher.stage(canonical_json(value))
    assert api.writes == []


def test_missing_or_acceptance_only_preflight_prevents_publisher_writes(state):
    api, publisher, raw = state
    proof = publisher.run_preflight
    publisher.run_preflight = None
    with pytest.raises(PublicationError, match='signed_preflight_required'):
        publisher.stage(raw)
    publisher.run_preflight = proof
    proof['execution']['acceptance_only'] = True
    with pytest.raises(PublicationError, match='preflight_context_mismatch'):
        publisher.stage(raw)
    assert not api.writes


def test_draft_visibility_is_explicitly_required_before_creating_a_snapshot(state):
    api, publisher, raw = state
    api.draft_visibility = False
    with pytest.raises(PublicationError, match='draft_visibility_required'):
        publisher.stage(raw)
    assert not api.writes


def test_hidden_duplicate_and_higher_drafts_are_found_by_complete_inventory(state, monkeypatch):
    api, publisher, raw = state
    # get-by-tag can omit drafts; the authenticated Contents Write list cannot.
    api.new_release('catalogue-000002')
    api.new_release('catalogue-000002')
    monkeypatch.setattr(api, 'release', lambda tag: None)
    with pytest.raises(PublicationError, match='duplicate_snapshot_draft'):
        publisher.stage(raw)
    assert not api.writes


def test_publisher_read_scope_omission_uses_only_previously_signed_bypass_observation(state, monkeypatch):
    api, publisher, raw = state
    original = api.json
    def read_without_bypass(method, path, **kwargs):
        value = original(method, path, **kwargs)
        if method == 'GET' and path.startswith('/rulesets/'):
            value.pop('bypass_actors')
        return value
    monkeypatch.setattr(api, 'json', read_without_bypass)
    assert complete(publisher, raw)['result'] == 'published'
    # The signed startup observation is retained intact, never rewritten to []
    # or represented as a fresh complete observation from the read-scoped App.
    assert publisher.run_preflight['rulesets']['observations'][1]['bypass_actors']
