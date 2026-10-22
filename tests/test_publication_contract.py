# SPDX-License-Identifier: Apache-2.0
"""Pure protocol tests: no signatures, provider acceptance or human approval claims."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from publication_contract import *

FROZEN = (ROOT / 'tests/fixtures/official_catalogue/catalogue-000001.json').read_bytes()


def pointer(sequence=1, **values):
    return {'schema_version': '1.0', 'sequence': sequence, 'release_tag': snapshot_tag(sequence),
            'release_id': 100, 'asset_id': 200, 'sha256': digest(FROZEN),
            'previous_pointer_sha256': None if sequence == 1 else 'a' * 64, **values}


def document(sequence=1):
    value = parse_catalogue(FROZEN)
    value['sequence'] = sequence
    return value


def authority_fixture():
    policy = {'enabled': True, 'authorization_mode': AUTHORIZATION_MODE, 'allowed_maintainer_id': 10,
              'environment_id': 50, 'package_environment_id': 51, 'app_id': 30, 'app_slug': 'publication-app',
              'app_installation_id': 40, 'app_bot_user_id': 31,
              'bootstrap': {'sequence': 1, 'pointer_sha256': 'c'*64}}
    repo = {'id': REPOSITORY_ID, 'owner': {'id': OWNER_ID}, 'full_name': REPOSITORY, 'private': False}
    branch = {'name': 'main', 'protected': True, 'commit': {'sha': 'a' * 40}}
    env = {'id': 50, 'name': ENVIRONMENT, 'can_admins_bypass': False,
           'deployment_branch_policy': {'protected_branches': True, 'custom_branch_policies': False},
           'protection_rules': []}
    user = {'id': 10, 'type': 'User', 'login': 'maintainer'}
    run = {'id': 60, 'event': 'workflow_dispatch', 'head_branch': 'main', 'path': PUBLICATION_WORKFLOW,
           'repository': deepcopy(repo), 'head_repository': deepcopy(repo), 'run_attempt': 1, 'head_sha': 'a' * 40,
           'workflow_id': 80, 'url': f'{API}/actions/runs/60',
           'html_url': f'https://github.com/{REPOSITORY}/actions/runs/60',
           'actor': deepcopy(user), 'triggering_actor': deepcopy(user)}
    workflow = {'id': 80, 'path': PUBLICATION_WORKFLOW, 'state': 'active', 'url': f'{API}/actions/workflows/80'}
    checks = {'total_count': 1, 'check_runs': [{'name': 'validate', 'head_sha': 'a'*40,
               'status': 'completed', 'conclusion': 'success', 'app': {'id': 15368}}]}
    return [policy, repo, branch, env, run, deepcopy(run), workflow, user, checks]


def authorize(args, **kwargs):
    return check_authority(*args, run_id=60, source_commit='a'*40, **kwargs)


def rules_fixture():
    rules = []
    for i, (name, target, include, types) in enumerate([
        ('atlas-main', 'branch', ['refs/heads/main'], ['pull_request', 'required_status_checks', 'deletion', 'non_fast_forward']),
        ('atlas-catalogue-current', 'branch', [CHANNEL_REF], ['creation', 'update', 'deletion', 'non_fast_forward']),
        ('atlas-publication-tags', 'tag', ['refs/tags/catalogue-*', 'refs/tags/*-v*'], ['creation', 'update', 'deletion']),
        ('atlas-history-lock', 'branch', [CHANNEL_REF], ['deletion', 'non_fast_forward']),
    ]):
        rules.append({'id': i + 1, 'name': name, 'target': target, 'enforcement': 'active',
                      'conditions': {'ref_name': {'include': include, 'exclude': []}},
                      'bypass_actors': [] if i in {0,3} else [{'actor_id': 30, 'actor_type': 'Integration', 'bypass_mode': 'always'}],
                      'rules': [{'type': t} for t in types]})
    rules[0]['rules'][0]['parameters'] = {'required_approving_review_count': 0, 'dismiss_stale_reviews_on_push': True,
                                        'require_last_push_approval': False}
    rules[0]['rules'][1]['parameters'] = {'strict_required_status_checks_policy': True,
                                        'required_status_checks': [{'context': 'validate', 'integration_id': 15368}]}
    return rules


def test_exact_pointer_bytes_and_independent_six_field_catalogue():
    raw = pointer_bytes(pointer())
    assert raw == ('{\n  "asset_id": 200,\n  "previous_pointer_sha256": null,\n  "release_id": 100,\n'
                   '  "release_tag": "catalogue-000001",\n  "schema_version": "1.0",\n  "sequence": 1,\n'
                   '  "sha256": "' + digest(FROZEN) + '"\n}\n').encode()
    assert parse_pointer(raw) == pointer()
    assert len(parse_catalogue(FROZEN)) == 6
    assert len(FROZEN) == 10585
    assert digest(FROZEN) == '55533ca67e7e9a14f82961e0a8c34ad78e2596049b3db02fde787494e3975afd'


@pytest.mark.parametrize('field', sorted(POINTER_FIELDS))
def test_missing_field(field):
    value = pointer()
    del value[field]
    with pytest.raises(ValueError):
        pointer_bytes(value)


@pytest.mark.parametrize('field', ['sequence', 'release_id', 'asset_id'])
@pytest.mark.parametrize('value', [0, -1, True, False, 1.0, '1', MAX_INTEGER + 1, None, [], {}])
def test_integer_rules(field, value):
    with pytest.raises(ValueError):
        pointer_bytes(pointer(**{field: value}))


@pytest.mark.parametrize('value', ['', 'a' * 63, 'a' * 65, 'A' * 64, 'sha256:' + 'a' * 64, None, 1])
def test_digest_rules(value):
    with pytest.raises(ValueError):
        pointer_bytes(pointer(sha256=value))


def test_exact_schema_size_duplicate_keys_and_canonical_input():
    for value in [pointer(extra=1), pointer(schema_version=1), pointer(release_tag='catalogue-v1'),
                  pointer(previous_pointer_sha256='a'*64), pointer(2, previous_pointer_sha256=None)]:
        with pytest.raises(ValueError):
            pointer_bytes(value)
    for raw in [b' ' * 1025, pointer_bytes(pointer()) + b' ', b'{"sequence":1,"sequence":2}', b'\xff', b'[]',
                pointer_bytes(pointer()).replace(b'100', b'NaN')]:
        with pytest.raises(ValueError):
            parse_pointer(raw)
    assert parse_pointer(pointer_bytes(pointer(MAX_INTEGER)))['sequence'] == MAX_INTEGER


def test_sequence_transitions_and_maximum():
    one, two = FROZEN, canonical_json(document(2))
    assert sequence_transition(None, one) == 'first'
    assert sequence_transition(one, one) == 'unchanged'
    assert sequence_transition(one, two) == 'advance'
    assert sequence_transition(canonical_json(document(MAX_INTEGER - 1)), canonical_json(document(MAX_INTEGER))) == 'advance'
    for previous, candidate, code in [(None, two, 'gap'), (two, one, 'rollback'), (one, canonical_json(document(3)), 'gap')]:
        with pytest.raises(PublicationError, match=code):
            sequence_transition(previous, candidate)
    changed = document()
    changed['generated_at'] = '2026-10-22T00:00:00Z'
    with pytest.raises(PublicationError, match='substitution'):
        sequence_transition(one, canonical_json(changed))


def test_history_omission_withdrawal_and_manifest_substitution():
    old, new = document(), document(2)
    new['entries'][0]['status'] = 'withdrawn'
    retain_history(old, new)
    with pytest.raises(PublicationError, match='reactivated'):
        retain_history(new, old)
    with pytest.raises(PublicationError, match='missing'):
        retain_history(new, {**new, 'entries': []})
    for field in ['manifest', 'release_tag', 'release_asset_id']:
        altered = deepcopy(new)
        if field == 'manifest':
            altered['entries'][0][field]['display']['description'] += ' changed'
        else:
            altered['entries'][0][field] = 'changed'
        with pytest.raises(PublicationError, match='identity_changed'):
            retain_history(old, altered)


def test_pointer_chain_replay_and_repetition():
    one = pointer_bytes(pointer())
    two = pointer_bytes(pointer(2, previous_pointer_sha256=digest(one)))
    assert pointer_transition(None, one) == 'first'
    assert pointer_transition(one, two) == 'advance'
    assert pointer_transition(two, two) == 'unchanged'
    for old, new, code in [(two, one, 'rollback'), (one, pointer_bytes(pointer(asset_id=201)), 'substitution'),
                           (one, pointer_bytes(pointer(3)), 'gap'), (one, pointer_bytes(pointer(2)), 'chain_mismatch')]:
        with pytest.raises(PublicationError, match=code):
            pointer_transition(old, new)


def test_single_maintainer_dispatch_is_api_observation_with_exact_identity():
    args = authority_fixture()
    result = authorize(args)
    assert result == Authority(60, 'a'*40, 50, 10)
    args[2]['commit']['sha'] = 'b' * 40
    with pytest.raises(PublicationError, match='source_changed'):
        authorize(args)
    assert authorize(args, historical=True).source_commit == 'a'*40


@pytest.mark.parametrize('suffix', ['', '@main', '@refs/heads/main'])
def test_only_exact_provider_workflow_path_forms(suffix):
    args = authority_fixture()
    for index in (4, 5):
        args[index]['path'] = PUBLICATION_WORKFLOW + suffix
    assert authorize(args).actor_id == 10


@pytest.mark.parametrize('which,key,value,code', [
    (0, 'enabled', False, 'disabled'), (0, 'allowed_maintainer_id', None, 'maintainer_unconfigured'),
    (0, 'allowed_maintainer_id', True, 'maintainer_unconfigured'),
    (0, 'allowed_maintainer_id', '10', 'maintainer_unconfigured'),
    (0, 'authorization_mode', 'independent-reviewer-v2', 'unsupported_authorization_mode'),
    (0, 'reviewer_ids', [10], 'unsupported_authorization_mode'),
    (0, 'environment_id', 51, 'environment_protection'), (1, 'id', 1, 'repository'),
    (1, 'private', True, 'repository'), (2, 'protected', False, 'unprotected'),
    (4, 'event', 'pull_request', 'untrusted'), (4, 'event', 'push', 'untrusted'),
    (4, 'path', '.github/workflows/evil.yml', 'untrusted'),
    (4, 'path', PUBLICATION_WORKFLOW+'@refs/heads/dev', 'untrusted'),
    (4, 'head_sha', 'b'*40, 'source_changed'), (4, 'head_branch', 'dev', 'untrusted'),
    (4, 'run_attempt', 2, 'fresh_dispatch'), (4, 'run_attempt', True, 'fresh_dispatch'),
    (4, 'id', 61, 'invalid_run_identity'), (4, 'repository', {}, 'repository'),
    (4, 'head_repository', {}, 'repository'), (4, 'url', 'https://example.com/run', 'run_identity'),
    (4, 'workflow_id', 99, 'workflow_identity'), (5, 'workflow_id', 99, 'workflow_identity'),
    (5, 'head_sha', 'b'*40, 'source_changed'), (5, 'run_attempt', 2, 'fresh_dispatch'),
    (6, 'path', '.github/workflows/evil.yml', 'workflow_identity'),
    (6, 'state', 'disabled_manually', 'workflow_identity'),
    (7, 'id', 20, 'unsupported_actor'), (7, 'type', 'Bot', 'unsupported_actor'),
    (3, 'can_admins_bypass', True, 'environment_protection'),
    (3, 'protection_rules', [{'type': 'required_reviewers', 'prevent_self_review': False}], 'environment_reviewers'),
    (3, 'protection_rules', [{'type': 'required_reviewers', 'prevent_self_review': True}], 'environment_reviewers'),
    (3, 'deployment_branch_policy', None, 'environment_branches'),
    (8, 'total_count', 2, 'required_ci_evidence'), (8, 'check_runs', [], 'required_ci_evidence'),
])
def test_dispatch_failures(which, key, value, code):
    args = authority_fixture()
    args[which][key] = value
    with pytest.raises(PublicationError, match=code):
        authorize(args)


@pytest.mark.parametrize('record', [4, 5])
@pytest.mark.parametrize('field', ['actor', 'triggering_actor'])
@pytest.mark.parametrize('actor', [None, {}, {'id': 10}, {'id': '10', 'type': 'User', 'login': 'maintainer'},
    {'id': 20, 'type': 'User', 'login': 'maintainer'}, {'id': 10, 'type': 'User', 'login': 'someone-else'},
    {'id': 31, 'type': 'Bot', 'login': 'publication-app[bot]'}, {'id': 10, 'type': 'Bot', 'login': 'maintainer'}])
def test_original_and_triggering_identities_cannot_be_missing_ambiguous_or_app(record, field, actor):
    args = authority_fixture()
    args[record][field] = actor
    with pytest.raises(PublicationError, match='triggering_identity'):
        authorize(args)


@pytest.mark.parametrize('index', range(1, 9))
@pytest.mark.parametrize('value', [None, [], {}])
def test_missing_or_ambiguous_api_evidence(index, value):
    args = authority_fixture()
    args[index] = value
    with pytest.raises(PublicationError):
        authorize(args)


@pytest.mark.parametrize('key,value', [('conclusion', 'failure'), ('status', 'in_progress'),
    ('head_sha', 'b'*40), ('app', {'id': 999}), ('name', 'another-check')])
def test_required_ci_observation(key, value):
    args = authority_fixture()
    args[8]['check_runs'][0][key] = value
    with pytest.raises(PublicationError, match='required_ci_failed'):
        authorize(args)


def test_ruleset_permissions_fail_closed():
    policy = authority_fixture()[0]
    check_rulesets(policy, rules_fixture())
    for modification in [lambda r: r.pop(), lambda r: r[1].update(enforcement='evaluate'),
                         lambda r: r[1].update(bypass_actors=[]), lambda r: r[1]['rules'].pop(),
                         lambda r: r[0]['rules'][0]['parameters'].update(required_approving_review_count=1),
                         lambda r: r[0]['rules'][0]['parameters'].update(require_last_push_approval=True),
                         lambda r: r[0]['rules'][1]['parameters'].update(required_status_checks=[]),
                         lambda r: r[0].update(bypass_actors=[{'actor_id':30,'actor_type':'Integration','bypass_mode':'always'}]),
                         lambda r: r[1]['bypass_actors'][0].update(actor_id=99),
                         lambda r: r[2]['conditions']['ref_name']['exclude'].append('refs/tags/*')]:
        rules = rules_fixture()
        modification(rules)
        with pytest.raises(PublicationError):
            check_rulesets(policy, rules)


def app_fixture():
    policy, repo, *_ = authority_fixture()
    app = {'id': 30, 'slug': 'publication-app', 'owner': {'id': OWNER_ID}, 'permissions': dict(APP_PERMISSIONS)}
    scope = {'total_count': 1, 'repositories': [repo]}
    identity = {'app_slug': 'publication-app', 'installation_id': 40}
    return [policy, app, scope, identity]


def test_expected_app_and_single_repository_installation_observations():
    check_app(*app_fixture())


@pytest.mark.parametrize('which,key,value', [
    (1, 'id', 99), (1, 'owner', {'id': 99}), (1, 'slug', 'unexpected'), (1, 'permissions', {}),
    (1, 'permissions', {**APP_PERMISSIONS, 'administration': 'write'}),
    (2, 'total_count', 2), (2, 'repositories', []), (2, 'repositories', [{'id': 99}]),
    (3, 'app_slug', 'unexpected'), (3, 'installation_id', 99), (3, 'installation_id', None),
])
def test_unexpected_or_overprivileged_app_rejected(which, key, value):
    args = app_fixture()
    args[which][key] = value
    with pytest.raises(PublicationError):
        check_app(*args)
