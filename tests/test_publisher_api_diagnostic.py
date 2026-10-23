# SPDX-License-Identifier: Apache-2.0
"""Offline checks for the temporary GET probe; never live API or publishing evidence."""
import ast
from email.message import Message
import io
import json
from pathlib import Path
import urllib.error

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/diagnose-catalogue-publisher.yml'
PREFIX = '/repos/benchristian88/atlas-connectors'


def workflow():
    return yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)


def program():
    return workflow()['jobs']['diagnose']['steps'][1]['run'].split("python3 - <<'PY'\n", 1)[1].rsplit('\nPY', 1)[0]


class Response(io.BytesIO):
    def __init__(self, raw):
        super().__init__(raw)
        self.status = 200
        self.headers = {'X-GitHub-Request-Id': 'ABCD:1234'}


def failure(status, **headers):
    message = Message()
    for name, value in headers.items():
        message[name] = value
    return urllib.error.HTTPError('https://never-log.example/private?secret=opaque', status,
                                 'never-log-reason', message, io.BytesIO(b'never-log-body'))


class FakeOpener:
    def __init__(self, probe):
        self.probe, self.calls, self.overrides = probe, [], {}

    def open(self, request, timeout):
        self.calls.append(request)
        assert request.get_method() == 'GET' and request.data is None
        assert 0 < timeout <= 20
        url = request.full_url
        if url.startswith('https://release-assets.githubusercontent.com/'):
            value = self.overrides.get('download', Response(b'historical-bytes'))
        else:
            route = url.removeprefix('https://api.github.com')
            if route in self.overrides:
                value = self.overrides[route]
            elif route in (self.probe['CURRENT'], self.probe['MARKER']):
                value = failure(404)
            elif route == self.probe['LIST']:
                value = [{'id': identity} for identity in reversed(self.probe['RULES'])]
            elif route == PREFIX + '/git/ref/tags/catalogue-v1':
                value = {'object': {'type': 'commit', 'sha': '91dfd86f18d0b59ff977bb1e8a5fef42c5329943'}}
            elif route.startswith(PREFIX + '/releases/assets/'):
                value = failure(302, Location='https://release-assets.githubusercontent.com/download?signature=never-log-signed-query')
            elif route.startswith(PREFIX + '/releases?'):
                value = []
            else:
                value = {}
        if isinstance(value, Exception):
            raise value
        return value if isinstance(value, Response) else Response(json.dumps(value).encode())


@pytest.fixture
def probe(monkeypatch):
    monkeypatch.setenv('ATLAS_PUBLICATION_TOKEN', 'synthetic-not-a-credential')
    monkeypatch.setenv('ATLAS_APP_SLUG', 'atlas-catalogue-publisher')
    monkeypatch.setenv('ATLAS_APP_INSTALLATION_ID', '174027755')
    namespace = {'__name__': 'offline_diagnostic'}
    exec(compile(program(), str(WORKFLOW), 'exec'), namespace)
    namespace['opener'] = FakeOpener(namespace)
    return namespace


def events(capsys):
    captured = capsys.readouterr()
    assert not captured.err
    assert all(secret not in captured.out for secret in (
        'synthetic-not-a-credential', 'never-log', 'Bearer', 'signature=', 'Location'))
    rows = [json.loads(line) for line in captured.out.splitlines()]
    assert all(set(row) == {'method', 'route', 'status', 'request_id', 'expected', 'authentication'} for row in rows)
    return rows


def authority_routes(probe):
    return [probe['RUN'], '/users/benchristian88', PREFIX, PREFIX + '/branches/main',
            PREFIX + '/environments/catalogue-publication', probe['RUN'] + '/attempts/1',
            PREFIX + '/actions/workflows/392548804', probe['CHECKS'], '/apps/atlas-catalogue-publisher',
            '/installation/repositories?per_page=100', PREFIX + '/immutable-releases', probe['LIST'],
            *(PREFIX + '/rulesets/' + str(identity) for identity in reversed(probe['RULES']))]


def test_workflow_has_only_owner_protected_main_dispatch_and_existing_publisher_token():
    definition = workflow()
    assert definition['on'] == {'workflow_dispatch': ''}
    assert definition['permissions'] == {}
    job, = definition['jobs'].values()
    assert job['environment'] == 'catalogue-publication' and job['timeout-minutes'] == '5'
    for clause in ("github.event_name == 'workflow_dispatch'", "github.ref == 'refs/heads/main'",
                   'github.ref_protected', 'github.run_attempt == 1',
                   "github.repository == 'benchristian88/atlas-connectors'",
                   "github.repository_id == '1414494920'", "github.repository_owner == 'benchristian88'",
                   "github.repository_owner_id == '93822871'", "github.actor_id == '93822871'",
                   "github.actor == 'benchristian88'", "github.triggering_actor == 'benchristian88'"):
        assert clause in job['if']
    production = yaml.load((ROOT / '.github/workflows/catalogue-publish.yml').read_text(), Loader=yaml.BaseLoader)
    mint = next(step for step in production['jobs']['publish']['steps'] if step.get('id') == 'app')
    assert job['steps'][0] == mint
    assert len(job['steps']) == 2 and job['steps'][1]['shell'] == 'bash'
    assert job['steps'][1]['env'] == {
        'ATLAS_PUBLICATION_TOKEN': '${{ steps.app.outputs.token }}',
        'ATLAS_APP_SLUG': '${{ steps.app.outputs.app-slug }}',
        'ATLAS_APP_INSTALLATION_ID': '${{ steps.app.outputs.installation-id }}'}
    assert 'VERIFICATION_APP' not in WORKFLOW.read_text()
    assert 'outputs' not in job and 'secrets' not in job


def test_inline_program_has_only_standard_library_and_one_guarded_get_transport():
    tree = ast.parse(program())
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    assert imports == {'json', 'os', 're', 'sys', 'time', 'urllib.error', 'urllib.parse', 'urllib.request'}
    assert not any(isinstance(node, ast.ImportFrom) for node in ast.walk(tree))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    assert not any(isinstance(node.func, ast.Name) and node.func.id in {'exec', 'eval', 'compile', 'open', '__import__'} for node in calls)
    network = [node for node in calls if isinstance(node.func, ast.Attribute) and node.func.attr in {'open', 'urlopen'}]
    assert len(network) == 1 and ast.unparse(network[0].func) == 'opener.open'
    constructors = [node for node in calls if ast.unparse(node.func) == 'urllib.request.Request']
    assert len(constructors) == 1
    assert next(item.value.value for item in constructors[0].keywords if item.arg == 'method') == 'GET'
    assert 'ProxyHandler({})' in program() and 'NoRedirect()' in program()


def test_complete_production_order_is_get_only_and_anonymous_reads_stay_anonymous(probe, capsys):
    probe['main']()
    rows = events(capsys)
    prefix = authority_routes(probe)
    expected = prefix + [PREFIX + '/releases/tags/catalogue-v1', PREFIX + '/git/ref/tags/catalogue-v1',
        PREFIX + '/releases/416561696/assets?per_page=100']
    for identity in probe['ASSETS']:
        expected.extend([PREFIX + '/releases/assets/' + str(identity),
                         'release-assets.githubusercontent.com/asset/' + str(identity)])
    expected += [probe['CURRENT'], probe['MARKER'], PREFIX + '/git/matching-refs/tags/catalogue-',
                 PREFIX + '/releases?per_page=100&page=1'] + prefix + [probe['CURRENT'], probe['MARKER']]
    assert [row['route'] for row in rows] == expected and len(rows) == 47
    assert all(row['method'] == 'GET' and row['expected'] for row in rows)
    assert sum(row['status'] == 404 for row in rows) == 4
    assert probe['CALLER'] == '1d3e217ff9d6d8c202815abd8fd5c51c34e14855'
    for row, request in zip(rows, probe['opener'].calls):
        anonymous = row['route'] == probe['CHECKS'] or row['route'].startswith('release-assets.')
        assert row['authentication'] == ('anonymous' if anonymous else 'Publisher App')
        assert request.get_header('Authorization') == (None if anonymous else 'Bearer synthetic-not-a-credential')


@pytest.mark.parametrize('method', ['POST', 'PATCH', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'get'])
def test_method_allowlist_rejects_every_non_get_before_network(probe, method):
    with pytest.raises(probe['ProbeFailed']):
        probe['request'](method, PREFIX)
    assert not probe['opener'].calls


@pytest.mark.parametrize('route', [PREFIX + suffix for suffix in (
    '/releases', '/git/trees', '/git/commits', '/git/refs', '/contents/anything',
    '/releases?per_page=100&page=5', '/rulesets/999', '/git/tags/../../other')]
    + ['/user', '/repos/another/repository', 'https://evil.example', '//evil.example'])
def test_unapproved_and_mutating_routes_never_reach_network(probe, route):
    with pytest.raises(probe['ProbeFailed']):
        probe['request']('GET', route)
    assert not probe['opener'].calls


@pytest.mark.parametrize('status', [301, 302, 401, 403, 404, 422, 500, 503])
def test_first_unexpected_status_stops_without_body_or_error_disclosure(probe, capsys, status):
    probe['opener'].overrides[probe['RUN']] = failure(status)
    with pytest.raises(probe['ProbeFailed']):
        probe['main']()
    row, = events(capsys)
    assert row['status'] == status and row['expected'] is False
    assert len(probe['opener'].calls) == 1


@pytest.mark.parametrize('destination', ['http://release-assets.githubusercontent.com/x',
    'https://evil.example/x', 'https://release-assets.githubusercontent.com.evil.example/x',
    'https://user:password@release-assets.githubusercontent.com/x',
    'https://release-assets.githubusercontent.com:444/x',
    'https://release-assets.githubusercontent.com/x#fragment',
    'https://release-assets.githubusercontent.com/x\r\nsecret', '/relative'])
def test_asset_redirect_allowlist_never_sends_credentials_elsewhere(probe, capsys, destination):
    route = PREFIX + '/releases/assets/653915685'
    probe['opener'].overrides[route] = failure(302, Location=destination)
    with pytest.raises(probe['ProbeFailed']):
        probe['get'](route)
    assert len(probe['opener'].calls) == 1
    row, = events(capsys)
    assert row['expected'] is False and destination not in json.dumps(row)


def test_second_asset_redirect_is_not_followed(probe, capsys):
    probe['opener'].overrides['download'] = failure(302, Location='https://release-assets.githubusercontent.com/again?secret=opaque')
    with pytest.raises(probe['ProbeFailed']):
        probe['get'](PREFIX + '/releases/assets/653915685')
    first, second = events(capsys)
    assert first['expected'] and second['expected'] is False
    assert second['authentication'] == 'anonymous' and len(probe['opener'].calls) == 2
    assert probe['NoRedirect']().redirect_request(None, None, 302, '', {}, 'https://evil.example') is None


def test_tag_dereference_is_bounded_and_cannot_select_an_arbitrary_endpoint(probe, capsys):
    sha = 'a' * 40
    probe['opener'].overrides[PREFIX + '/git/ref/tags/catalogue-v1'] = {'object': {'type': 'tag', 'sha': sha}}
    probe['opener'].overrides[PREFIX + '/git/tags/' + sha] = {'object': {'type': 'tag', 'sha': sha}}
    with pytest.raises(probe['ProbeFailed']):
        probe['main']()
    assert sum(row['route'] == PREFIX + '/git/tags/' + sha for row in events(capsys)) == 2


def test_release_listing_stops_at_four_pages(probe, capsys):
    for page in range(1, 5):
        probe['opener'].overrides[PREFIX + '/releases?per_page=100&page=' + str(page)] = [{'tag_name': 'unrelated'}] * 100
    with pytest.raises(probe['ProbeFailed']):
        probe['main']()
    rows = events(capsys)
    assert sum('/releases?per_page' in row['route'] for row in rows) == 4
    assert sum(row['route'] == probe['RUN'] for row in rows) == 1


@pytest.mark.parametrize('limit', ['budget', 'deadline', 'json-size', 'asset-size'])
def test_request_and_response_bounds_fail_without_unbounded_reads(probe, capsys, limit):
    route = PREFIX
    if limit == 'budget':
        probe['requests_left'] = 0
    elif limit == 'deadline':
        probe['deadline'] = 0
    elif limit == 'json-size':
        probe['opener'].overrides[route] = Response(b'x' * (1024 * 1024 + 1))
    else:
        route = PREFIX + '/releases/assets/653915685'
        probe['opener'].overrides[route] = Response(b'x' * 10586)
    with pytest.raises(probe['ProbeFailed']):
        probe['get'](route)
    row, = events(capsys)
    assert row['expected'] is False
