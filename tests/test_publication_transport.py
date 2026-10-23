# SPDX-License-Identifier: Apache-2.0
"""Controlled HTTP transcripts, never GitHub write operations."""
from email.message import Message
from io import BytesIO
from pathlib import Path
import sys
import urllib.error

import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from publication_github import Github
import publication_github
from publication_contract import PublicationError, canonical_json, digest


class Response(BytesIO):
    def __init__(self,raw=b'{}',headers=None,status=200):
        super().__init__(raw)
        self.status=status
        self.headers=headers or {}


class Opener:
    def __init__(self,*responses):
        self.responses=iter(responses)
        self.calls=[]
    def open(self,request,timeout):
        self.calls.append(request)
        response=next(self.responses)
        if isinstance(response,Exception): raise response
        return response


def failure(status,**headers):
    message=Message()
    for k,v in headers.items(): message[k]=v
    return urllib.error.HTTPError('https://api.github.com/private?secret=do-not-log',status,'do-not-log',message,BytesIO(b'do-not-log'))


def client(*responses):
    api=Github('synthetic-not-a-credential')
    api.opener=Opener(*responses)
    return api


@pytest.mark.parametrize('token,public', [(None, False), ('synthetic-not-a-credential', False),
                                        ('synthetic-not-a-credential', True)])
def test_repository_root_uses_canonical_url_and_preserves_authentication(token, public):
    api = client(Response(b'{"id":1414494920}'))
    api.token = token
    assert api.json('GET', '/', public=public) == {'id': 1414494920}
    request, = api.opener.calls
    assert request.full_url == 'https://api.github.com/repos/benchristian88/atlas-connectors'
    assert request.get_method() == 'GET' and request.data is None
    assert request.get_header('Authorization') == ('Bearer ' + token if token and not public else None)


@pytest.mark.parametrize('bootstrap', [False, True])
def test_publication_authority_reads_canonical_repository_root(bootstrap):
    from bootstrap_catalogue import BootstrapPublisher
    from publish_catalogue import Publisher
    from test_publication_contract import authority_fixture
    policy, repo, branch, environment, run, attempt, workflow, user, checks = authority_fixture()
    if bootstrap:
        policy.update(bootstrap_operation='stage', bootstrap={'sequence': None, 'pointer_sha256': None})
    # Exercise the real authority caller and transport together, with only HTTP
    # responses simulated. No signatures, credentials or GitHub writes are used.
    api = client(*(Response(canonical_json(value)) for value in
                   (run, user, repo, branch, environment, attempt, workflow, checks)))
    publisher_type = BootstrapPublisher if bootstrap else Publisher
    publisher = publisher_type(api, None, policy, run['id'], source_commit=run['head_sha'])
    authority = publisher.run_authority(run['id'], run['head_sha'])
    assert authority.actor_id == policy['allowed_maintainer_id']
    assert api.opener.calls[2].full_url == 'https://api.github.com/repos/benchristian88/atlas-connectors'
    assert all(request.get_method() == 'GET' for request in api.opener.calls)
    assert api.opener.calls[2].get_header('Authorization') == 'Bearer synthetic-not-a-credential'
    assert api.opener.calls[-1].get_header('Authorization') is None  # Public CI read.


@pytest.mark.parametrize('path', ['/branches/main', '/releases/', '/releases?per_page=100&page=1',
                                '/contents/current.json?ref=' + 'a'*40])
def test_nonroot_repository_paths_are_preserved_exactly(path):
    api = client(Response())
    assert api.json('GET', path) == {}
    request, = api.opener.calls
    assert request.full_url == 'https://api.github.com/repos/benchristian88/atlas-connectors' + path
    assert request.get_header('Authorization') == 'Bearer synthetic-not-a-credential'


@pytest.mark.parametrize('method,options,code', [
    ('GET', {'api_global': True}, 'invalid_identity_endpoint'),
    ('POST', {'binary': b'bytes'}, 'invalid_upload'),
    ('POST', {'public': True}, 'invalid_public_request'),
])
def test_repository_root_does_not_bypass_transport_scope(method, options, code):
    api = client()
    with pytest.raises(PublicationError, match=code):
        api.request(method, '/', **options)
    assert not api.opener.calls


@pytest.mark.parametrize('path', ['/users/maintainer', '/users/publication-app%5Bbot%5D',
    '/apps/publication-app', '/installation/repositories?per_page=100'])
def test_identity_reads_use_fixed_github_api_origin(path):
    api = client(Response())
    assert api.json('GET', path, api_global=True) == {}
    assert api.opener.calls[0].full_url == 'https://api.github.com' + path


@pytest.mark.parametrize('method,path', [('POST', '/apps/publication-app'),
    ('PATCH', '/users/maintainer'), ('GET', '/repos/another/repository'), ('GET', '/user'),
    ('GET', '/users/a/repos'), ('GET', '/users/a?redirect=evil'), ('GET', '/apps/a/../b'),
    ('GET', '/installation/repositories?per_page=1000')])
def test_identity_transport_cannot_widen_write_or_read_scope(method, path):
    api = client()
    with pytest.raises(PublicationError):
        api.json(method, path, api_global=True)
    assert not api.opener.calls


def test_public_ci_read_does_not_expand_app_permissions_or_send_credentials():
    api = client(Response())
    api.json('GET', '/commits/'+'a'*40+'/check-runs?check_name=validate&filter=latest&per_page=100', public=True)
    assert not api.opener.calls[0].get_header('Authorization')
    with pytest.raises(PublicationError, match='invalid_public_request'):
        api.request('POST', '/releases', payload={}, public=True)


def test_asset_redirect_drops_credentials_and_preserves_exact_bytes():
    raw=b'bytes'
    api=client(failure(302,Location='https://release-assets.githubusercontent.com/asset?sig=opaque'),Response(raw))
    asset={'id':1,'size':len(raw),'state':'uploaded','digest':'sha256:'+digest(raw)}
    assert api.asset_bytes(asset,100)==raw
    assert api.opener.calls[0].get_header('Authorization')
    assert not api.opener.calls[1].get_header('Authorization')
    assert api.opener.calls[0].get_header('Accept')=='application/octet-stream'


@pytest.mark.parametrize('url',['http://release-assets.githubusercontent.com/x','https://evil.example/x',
    'https://user:secret@release-assets.githubusercontent.com/x','https://release-assets.githubusercontent.com:8443/x',
    'https://release-assets.githubusercontent.com/x#fragment','/relative','https://127.0.0.1/x'])
def test_redirect_destinations_rejected(url):
    api=client(failure(302,Location=url))
    with pytest.raises(PublicationError): api.request('GET','/releases/assets/1')


def test_metadata_redirect_and_double_asset_redirect_are_rejected():
    redirect=failure(302,Location='https://release-assets.githubusercontent.com/x')
    for path,responses in [('/',[redirect]),('/releases/1',[redirect]),('/releases/assets/1',[redirect,redirect])]:
        api=client(*responses)
        with pytest.raises(PublicationError): api.request('GET',path,asset=path.startswith('/releases/assets/'))


@pytest.mark.parametrize('path',['https://evil.example','//evil.example','/../x','/x\\x','/x#x','/x\nx'])
def test_no_arbitrary_publication_destination(path):
    api=client()
    with pytest.raises(PublicationError): api.request('POST',path,payload={})
    assert not api.opener.calls


@pytest.mark.parametrize('response,code',[
    (Response(b'x'*11),'response_limit'),(Response(b'{}',{'Content-Length':'999'}),'response_limit'),
    (Response(b'{}',{'Content-Length':'3'}),'truncated'),(Response(b'{}',{'Content-Encoding':'gzip'}),'encoding'),
    (Response(b'{}',status=206),'status'),(failure(403),'request_failed'),(failure(422),'conflict'),
    (failure(429,**{'Retry-After':'999'}),'rate_limited'),(failure(500,**{'Retry-After':'99'}),'unavailable'),
])
def test_bounded_sanitized_failures(response,code):
    api=client(response)
    with pytest.raises(PublicationError,match=code) as error: api.request('GET','/releases',maximum=10)
    assert 'do-not-log' not in str(error.value)


def test_read_retries_and_write_ambiguity(monkeypatch):
    monkeypatch.setattr('publication_github.time.sleep',lambda _:None)
    api=client(failure(429,**{'Retry-After':'1'}),failure(503),Response(b'{}'))
    assert api.json('GET','/')=={}
    assert len(api.opener.calls)==3
    assert all(request.full_url == 'https://api.github.com/repos/benchristian88/atlas-connectors'
               for request in api.opener.calls)
    api=client(failure(503),Response())
    with pytest.raises(PublicationError):api.json('POST','/releases',payload={})
    assert len(api.opener.calls)==1


def test_invalid_json_duplicate_keys_and_absent_credentials():
    for raw in [b'{"x":1,"x":2}',b'NaN',b'\xff']:
        with pytest.raises(ValueError):client(Response(raw)).json('GET','/')
    with pytest.raises(PublicationError,match='credentials'):Github().json('POST','/releases',payload={})


def test_actual_cas_uses_single_parent_nonforce_and_reports_race(monkeypatch):
    api=Github('not-a-credential')
    head='a'*40
    files={'current.json':b'{}','current.sigstore.json':b'{}'}
    observations=iter([(head,{}),('c'*40,files)])
    monkeypatch.setattr(api,'channel',lambda:next(observations))
    calls=[]
    def request(method,path,**kwargs):
        calls.append((method,path,kwargs['payload']))
        return {'sha': 'b'*40 if path=='/git/trees' else 'c'*40}
    monkeypatch.setattr(api,'json',request)
    assert api.compare_and_swap(head,files)=='c'*40
    assert calls[1][2]['parents']==[head]
    assert calls[2][2]=={'sha':'c'*40,'force':False}
    monkeypatch.setattr(api,'channel',lambda:('d'*40,{}))
    with pytest.raises(PublicationError,match='channel_changed'):api.compare_and_swap(head,files)
    assert len(calls)==3


def test_attestation_pagination_is_bounded(monkeypatch):
    api=Github()
    calls=[]
    def response(*args,**kwargs):
        calls.append(args)
        return {'attestations':[{'repository_id':1414494920,'bundle':{}}]*10}
    monkeypatch.setattr(api,'json',response)
    class Reject:
        def verify(self,*args,**kwargs):raise ValueError('invalid')
    with pytest.raises(PublicationError,match='unavailable'):api.attestation(b'bytes',Reject(),profile='catalogue')
    assert len(calls)==4


def test_channel_commit_parent_binding_rejects_replayed_signed_bytes(monkeypatch):
    import base64
    from test_publication_contract import pointer
    from publication_contract import pointer_bytes
    previous=pointer_bytes(pointer())
    current=pointer_bytes(pointer(2,previous_pointer_sha256=digest(previous)))
    api=Github()
    head,parent='a'*40,'b'*40
    parent_raw=[previous]
    def encoded(raw,path):
        return {'type':'file','path':path,'encoding':'base64','size':len(raw),'content':base64.b64encode(raw).decode()}
    def response(method,path,**kwargs):
        if path=='/git/ref/heads/catalogue-current':
            return {'ref':'refs/heads/catalogue-current','object':{'type':'commit','sha':head}}
        if path=='/git/commits/'+head:return {'sha':head,'parents':[{'sha':parent}]}
        if path==f'/contents/current.json?ref={head}':return encoded(current,'current.json')
        if path==f'/contents/current.sigstore.json?ref={head}':return encoded(b'{}','current.sigstore.json')
        if path==f'/contents/current.json?ref={parent}':return encoded(parent_raw[0],'current.json')
        pytest.fail('unexpected path')
    monkeypatch.setattr(api,'json',response)
    assert api.channel()[1]['current.json']==current
    parent_raw[0]=current
    with pytest.raises(PublicationError,match='parent_binding'):api.channel()


def test_fixed_repository_compare_path_is_not_path_traversal():
    api=client(Response(b'{"status":"ahead"}'))
    assert api.json('GET','/compare/'+'a'*40+'...main')=={'status':'ahead'}


@pytest.mark.parametrize('destination',['http://github.com/x','https://evil.example/x','https://user@github.com/x',
                                      'https://github.com:444/x','https://github.com/x#fragment'])
def test_verifier_distribution_redirect_is_github_only(destination):
    import urllib.request
    from prepare_publication_verifier import DistributionRedirect
    handler=DistributionRedirect()
    with pytest.raises(PublicationError):
        handler.redirect_request(urllib.request.Request('https://github.com/x'),None,302,'',{},destination)


REQUEST_ID = 'F076:1D8066:29BC837:2C58523:666EAA62'


def diagnostic(capsys):
    captured = capsys.readouterr()
    assert captured.out == ''
    assert all(value not in captured.err for value in (
        'do-not-log', 'synthetic-not-a-credential', 'Authorization', 'Bearer',
        'https://', 'Location', 'Set-Cookie', 'private-key', '?', 'sig='))
    return captured.err


@pytest.mark.parametrize('status', [401, 403, 404, 500])
@pytest.mark.parametrize('method,path,label', [
    ('GET', '/releases', 'release_list'),
    ('POST', '/releases', 'release_create'),
    ('PATCH', '/releases/23', 'release_update'),
])
def test_terminal_http_failure_has_one_fixed_record_and_same_error_code(capsys, monkeypatch, status, method, path, label):
    monkeypatch.setattr(publication_github.time, 'sleep', lambda _: None)
    count = 3 if method == 'GET' and status == 500 else 1
    api = client(*(failure(status, **{'X-GitHub-Request-Id': REQUEST_ID,
        'Authorization': 'Bearer do-not-log', 'Set-Cookie': 'do-not-log',
        'Location': 'https://release-assets.githubusercontent.com/private?sig=do-not-log'}) for _ in range(count)))
    with pytest.raises(PublicationError) as error:
        api.request(method, path, payload={'private-key': 'do-not-log'} if method != 'GET' else None)
    assert str(error.value) == 'github_request_failed'
    assert len(api.opener.calls) == count
    assert diagnostic(capsys) == f'github_http_failure method={method} route={label} status={status} request_id={REQUEST_ID}\n'


@pytest.mark.parametrize('method,status', [('GET', 200), ('POST', 201), ('PATCH', 200)])
def test_successful_requests_have_no_failure_record(capsys, method, status):
    api = client(Response(status=status))
    assert api.request(method, '/releases', payload={} if method != 'GET' else None) == b'{}'
    assert diagnostic(capsys) == ''


@pytest.mark.parametrize('path', ['/git/ref/heads/catalogue-current', '/git/ref/tags/catalogue-bootstrap-root',
                                  '/releases/tags/not-present'])
def test_expected_missing_404_has_no_failure_record(capsys, path):
    api = client(failure(404, **{'X-GitHub-Request-Id': REQUEST_ID}))
    assert api.request('GET', path, missing=True) is None
    assert len(api.opener.calls) == 1 and diagnostic(capsys) == ''


@pytest.mark.parametrize('status,headers', [(500, {}), (502, {}), (503, {}), (504, {}),
    (429, {'Retry-After': '1'}), (403, {'X-RateLimit-Remaining': '0', 'Retry-After': '2'})])
def test_recovered_read_retries_emit_no_terminal_record(capsys, monkeypatch, status, headers):
    sleeps = []
    monkeypatch.setattr(publication_github.time, 'sleep', sleeps.append)
    api = client(failure(status, **headers), failure(status, **headers), Response())
    assert api.request('GET', '/releases') == b'{}'
    assert len(api.opener.calls) == 3 and sleeps == [int(headers.get('Retry-After', '1'))] * 2
    assert diagnostic(capsys) == ''


def test_exhausted_read_retries_report_only_the_last_response(capsys, monkeypatch):
    monkeypatch.setattr(publication_github.time, 'sleep', lambda _: None)
    api = client(failure(500, **{'X-GitHub-Request-Id': 'AA:BB'}), failure(502),
                 failure(503, **{'X-GitHub-Request-Id': REQUEST_ID}))
    with pytest.raises(PublicationError, match='^github_request_failed$'):
        api.request('GET', '/releases')
    assert len(api.opener.calls) == 3
    assert diagnostic(capsys) == f'github_http_failure method=GET route=release_list status=503 request_id={REQUEST_ID}\n'


@pytest.mark.parametrize('status,headers,method,code,count', [
    (409, {}, 'POST', 'github_conflict_reread_required', 1),
    (422, {}, 'PATCH', 'github_conflict_reread_required', 1),
    (429, {}, 'POST', 'github_rate_limited', 1),
    (429, {}, 'GET', 'github_rate_limited', 3),
    (403, {'X-RateLimit-Remaining': '0'}, 'PATCH', 'github_rate_limited', 1),
    (429, {'Retry-After': '999'}, 'GET', 'github_rate_limited', 1),
    (500, {'Retry-After': '99'}, 'GET', 'github_unavailable', 1),
    (503, {}, 'POST', 'github_request_failed', 1),
    (503, {}, 'PATCH', 'github_request_failed', 1),
])
def test_existing_terminal_categories_and_no_ambiguous_write_retry(capsys, monkeypatch, status, headers, method, code, count):
    monkeypatch.setattr(publication_github.time, 'sleep', lambda _: None)
    api = client(*(failure(status, **headers) for _ in range(count)), Response())
    with pytest.raises(PublicationError) as error:
        api.request(method, '/releases', payload={} if method != 'GET' else None)
    assert str(error.value) == code and len(api.opener.calls) == count
    assert diagnostic(capsys).splitlines() == [
        f'github_http_failure method={method} route={"other" if method == "PATCH" else "release_list" if method == "GET" else "release_create"} status={status}']


@pytest.mark.parametrize('path,label', [
    ('/do-not-log?secret=do-not-log', 'other'),
    ('/releases/do-not-log?private-key=do-not-log', 'other'),
    ('/unknown/%0A%3A%3Aerror%3A%3Ado-not-log?secret=do-not-log', 'other'),
    ('/releases?unknown=sensitive&sig=do-not-log', 'release_list'),
])
def test_unknown_paths_and_queries_are_never_echoed(capsys, path, label):
    api = client(failure(403))
    with pytest.raises(PublicationError, match='^github_request_failed$'):
        api.request('GET', path)
    assert diagnostic(capsys) == f'github_http_failure method=GET route={label} status=403\n'


@pytest.mark.parametrize('path', ['https://do-not-log.example/?token=do-not-log', '//do-not-log.example',
                                 '/x\n::error::do-not-log', '/x\\do-not-log', '/%2e%2e/do-not-log'])
def test_rejected_paths_remain_silent_and_do_not_make_requests(capsys, path):
    api = client()
    with pytest.raises(PublicationError, match='^invalid_api_path$'):
        api.request('GET', path)
    assert not api.opener.calls and diagnostic(capsys) == ''


@pytest.mark.parametrize('identity', [None, '', 'A' * 129, 'A' * 33 + ':B', '::',
    'AA:BB\n::error::do-not-log', 'AA:BB\rdo-not-log', 'AA:BB\x1b[31m',
    'Authorization: Bearer do-not-log', 'https://do-not-log.example', 'ＡＡ:BB', 'AA：BB'])
def test_invalid_request_ids_are_omitted(capsys, identity):
    api = client(failure(403, **{'X-GitHub-Request-Id': identity}))
    with pytest.raises(PublicationError, match='^github_request_failed$'):
        api.request('POST', '/releases', payload={})
    assert diagnostic(capsys) == 'github_http_failure method=POST route=release_create status=403\n'


@pytest.mark.parametrize('identity', [REQUEST_ID, 'aa:12:bb:34', ':'.join(['A' * 32] * 3 + ['B' * 29])])
def test_valid_bounded_request_ids_are_retained(capsys, identity):
    assert len(identity) <= 128
    api = client(failure(403, **{'X-GitHub-Request-Id': identity}))
    with pytest.raises(PublicationError):
        api.request('POST', '/releases', payload={})
    assert diagnostic(capsys) == f'github_http_failure method=POST route=release_create status=403 request_id={identity}\n'


def test_upload_failure_has_fixed_host_label_and_never_echoes_asset_name(capsys):
    api = client(failure(403))
    with pytest.raises(PublicationError, match='^github_request_failed$'):
        api.request('POST', '/releases/23/assets?name=do-not-log.json', binary=b'do-not-log')
    assert api.opener.calls[0].full_url.startswith('https://uploads.github.com/')
    assert diagnostic(capsys) == 'github_http_failure method=POST route=asset_upload status=403\n'


@pytest.mark.parametrize('redirected', [False, True])
def test_asset_failure_distinguishes_api_and_distribution_hosts_without_urls(capsys, redirected):
    responses = [failure(302, Location='https://release-assets.githubusercontent.com/private?sig=do-not-log')] if redirected else []
    api = client(*responses, failure(403, **{'X-GitHub-Request-Id': REQUEST_ID}))
    with pytest.raises(PublicationError, match='^github_request_failed$'):
        api.request('GET', '/releases/assets/23', asset=True)
    assert len(api.opener.calls) == (2 if redirected else 1)
    assert api.opener.calls[-1].get_header('Authorization') == (None if redirected else 'Bearer synthetic-not-a-credential')
    label = 'asset_download_distribution' if redirected else 'asset_download_api'
    assert diagnostic(capsys) == f'github_http_failure method=GET route={label} status=403 request_id={REQUEST_ID}\n'


def test_successful_asset_redirect_and_download_emit_no_failure_record(capsys):
    api = client(failure(302, Location='https://release-assets.githubusercontent.com/private?sig=do-not-log'), Response(b'bytes'))
    assert api.request('GET', '/releases/assets/23', asset=True) == b'bytes'
    assert diagnostic(capsys) == ''


def test_rejected_asset_redirect_logs_only_original_api_route_and_status(capsys):
    api = client(failure(302, Location='https://do-not-log.example/private?sig=do-not-log'))
    with pytest.raises(PublicationError, match='^github_redirect$'):
        api.request('GET', '/releases/assets/23', asset=True)
    assert len(api.opener.calls) == 1
    assert diagnostic(capsys) == 'github_http_failure method=GET route=asset_download_api status=302\n'


@pytest.mark.parametrize('error', [urllib.error.URLError('do-not-log'), TimeoutError('do-not-log'), OSError('do-not-log')])
def test_transport_failures_keep_their_category_without_inventing_http_status(capsys, error):
    api = client(error)
    with pytest.raises(PublicationError, match='^github_transport_failure$'):
        api.request('POST', '/releases', payload={})
    assert len(api.opener.calls) == 1 and diagnostic(capsys) == ''


def test_transient_http_then_transport_failure_does_not_log_an_obsolete_http_status(capsys, monkeypatch):
    monkeypatch.setattr(publication_github.time, 'sleep', lambda _: None)
    api = client(failure(500), urllib.error.URLError('do-not-log'))
    with pytest.raises(PublicationError, match='^github_transport_failure$'):
        api.request('GET', '/releases')
    assert len(api.opener.calls) == 2 and diagnostic(capsys) == ''


def test_stderr_failure_cannot_replace_the_original_http_error(capsys, monkeypatch):
    class Unwritable:
        def write(self, value):
            raise OSError('do-not-log')
    api = client(failure(403))
    with monkeypatch.context() as context:
        context.setattr(publication_github.sys, 'stderr', Unwritable())
        with pytest.raises(PublicationError, match='^github_request_failed$'):
            api.request('POST', '/releases', payload={})
    assert len(api.opener.calls) == 1 and diagnostic(capsys) == ''


@pytest.mark.parametrize('changes', [{'status': '403 do-not-log'}, {'status': True}, {'status': 999},
    {'method': 'POST\ndo-not-log'}, {'scope': 'https://do-not-log.example'}, {'path': None}])
def test_unsafe_diagnostic_metadata_is_suppressed(capsys, changes):
    arguments = dict(method='POST', path='/releases', scope='repository', status=403, headers={})
    arguments.update(changes)
    publication_github._http_failure(**arguments)
    assert diagnostic(capsys) == ''
