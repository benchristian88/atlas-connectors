# SPDX-License-Identifier: Apache-2.0
import hashlib
import json
import secrets
import ssl
import time
from types import SimpleNamespace

import pytest
from requests import Request
from ansible.module_utils import atlas_transport as transport
from ansible.module_utils.atlas_discovery import SafeModule


def resolver(address='192.168.50.2'):
    return lambda *a, **kw: [(2,1,6,'',(address,8006))]


class Response:
    status = 200
    def __init__(self, raw=b'{"data":[]}', headers=None):
        self.raw, self.offset, self.headers = raw, 0, headers or {}
    def getheader(self, name, default=None): return self.headers.get(name,default)
    def read(self, maximum):
        value = self.raw[self.offset:self.offset+maximum]; self.offset += len(value); return value


def factory(response, seen):
    class Connection:
        def __init__(self, host, port, address, context, fingerprint, timeout):
            assert address == '192.168.50.2' and 0 < timeout <= transport.TIMEOUT
            seen.append((host,address,context.verify_mode))
        def request(self, method, path, headers):
            seen.append(method)
        def getresponse(self):
            from copy import deepcopy
            return deepcopy(response)
        def close(self): seen.append('closed')
    return Connection


def request(path='/nodes', method='GET', host='source.example.test:8006', body=None):
    return Request(method, 'https://' + host + '/api2/json' + path, headers={'Authorization':'fixture-generated-at-runtime'},data=body).prepare()


def adapter(response=None, seen=None, config=None):
    return transport.PinnedAdapter(config or {'endpoint':'https://source.example.test:8006'},time.monotonic()+30,
                                   resolver=resolver(),connection_factory=factory(response or Response(),seen if seen is not None else []))


@pytest.mark.parametrize('address',['127.0.0.1','::1','169.254.1.1','100.100.100.200','0.0.0.0','224.0.0.1','::ffff:127.0.0.1'])
def test_dns_is_vetted_before_credentials_or_source_calls(address):
    with pytest.raises(transport.SourceError):
        transport.PinnedAdapter({'endpoint':'https://source.example.test:8006'},time.monotonic()+30,resolver=resolver(address),
                                connection_factory=lambda *a: pytest.fail('unsafe DNS result used'))


def test_dns_is_resolved_once_and_every_actual_request_uses_that_peer():
    calls, peers = [], []
    def resolve(*args, **kwargs): calls.append(args); return resolver()()
    client = transport.PinnedAdapter({'endpoint':'https://source.example.test:8006'},time.monotonic()+30,
        resolver=resolve,connection_factory=factory(Response(),peers))
    client.send(request()); client.send(request('/nodes/node-a/network'))
    assert len(calls) == 1
    assert peers.count(('source.example.test','192.168.50.2',ssl.CERT_REQUIRED)) == 2


@pytest.mark.parametrize('status,code',[(301,'source_unavailable'),(302,'source_unavailable'),(307,'source_unavailable'),(401,'authentication_failed'),(403,'permission_limited'),(500,'source_unavailable')])
def test_redirect_and_error_payloads_are_rejected_safely(status,code):
    marker = secrets.token_urlsafe(32)
    response = Response(marker.encode()); response.status = status
    client = adapter(response)
    with pytest.raises(transport.SourceError) as error: client.send(request())
    assert str(error.value) == code and marker not in str(error.value)


@pytest.mark.parametrize('path,method,host,body',[
    ('/nodes','POST','source.example.test:8006',None),('/access/ticket','GET','source.example.test:8006',None),
    ('/nodes/node-a/qemu/100/config?current=0','GET','source.example.test:8006',None),
    ('/nodes/node-a/qemu/100/config','GET','source.example.test:8006',None),
    ('/nodes/node-a/qemu/100/agent/network-get-interfaces','GET','source.example.test:8006',None),
    ('/nodes','GET','other.example.test:8006',None),('/nodes','GET','source.example.test:8006','unexpected'),
    ('/nodes?arbitrary=1','GET','source.example.test:8006',None),
    ('/storage','GET','source.example.test:8006',None),
    ('/nodes/node-a/storage','GET','source.example.test:8006',None),
    ('/storage/shared','GET','source.example.test:8006',None)])
def test_request_allowlist_blocks_writes_discovered_hosts_and_unreviewed_reads(path,method,host,body):
    seen=[]; client=adapter(seen=seen)
    with pytest.raises(transport.SourceError): client.send(request(path,method,host,body))
    assert not seen


@pytest.mark.parametrize('response',[
    Response(b'x'*(transport.MAX_RESPONSE+1)),Response(headers={'Content-Length':str(transport.MAX_RESPONSE+1)}),
    Response(headers={'Content-Encoding':'gzip'}),Response(b'{"data":[],"data":[]}'),Response(b'{"data":NaN}'),Response(b'not json')])
def test_response_limits_compression_and_malformed_json_fail_closed(response):
    with pytest.raises(transport.SourceError): adapter(response).send(request())


def test_connect_read_and_overall_deadlines_are_bounded(monkeypatch):
    for exception in [TimeoutError(),ssl.SSLCertVerificationError(),OSError()]:
        def failure(*args): raise exception
        client=transport.PinnedAdapter({'endpoint':'https://source.example.test:8006'},time.monotonic()+30,
                                      resolver=resolver(),connection_factory=failure)
        with pytest.raises(transport.SourceError) as error: client.send(request())
        assert error.value.code == ('timeout' if isinstance(exception,TimeoutError) else 'tls_trust_required' if isinstance(exception,ssl.SSLError) else 'source_unavailable')
    client=adapter(); client.deadline=time.monotonic()-1
    with pytest.raises(transport.SourceError,match='timeout'): client.send(request())
    client=adapter(); monkeypatch.setattr(transport,'MAX_CALLS',0)
    with pytest.raises(transport.SourceError,match='invalid_source_record'): client.send(request())


def test_fingerprint_is_checked_on_authenticated_socket_before_headers(monkeypatch):
    certificate=secrets.token_bytes(96)
    events=[]
    class Socket:
        def close(self): events.append('closed')
        def getpeercert(self,binary_form): return certificate
        def sendall(self,raw): events.append('credential sent')
    raw=Socket()
    monkeypatch.setattr(transport.socket,'create_connection',lambda peer,timeout: (events.append(peer) or raw))
    context=SimpleNamespace(wrap_socket=lambda sock,server_hostname: (events.append(server_hostname) or raw))
    connection=transport.PinnedConnection('source.example.test',8006,'192.168.50.2',context,'0'*64,6)
    with pytest.raises(transport.SourceError,match='tls_trust_required'):
        connection.request('GET','/api2/json/nodes',headers={'Authorization':secrets.token_urlsafe(32)})
    assert 'credential sent' not in events and ('192.168.50.2',8006) in events
    connection=transport.PinnedConnection('source.example.test',8006,'192.168.50.2',context,hashlib.sha256(certificate).hexdigest(),6)
    connection.request('GET','/api2/json/nodes',headers={'Authorization':secrets.token_urlsafe(32)})
    assert events[-1] == 'credential sent'


@pytest.mark.parametrize('config',[{'tls_policy':'insecure'},{'tls_policy':'fingerprint','fingerprint':'invalid'}])
def test_tls_trust_is_never_silently_disabled(config):
    with pytest.raises(transport.SourceError,match='tls_trust_required'):
        adapter(config={'endpoint':'https://source.example.test:8006',**config})


def test_token_only_credentials_are_validated_and_never_echoed():
    marker=secrets.token_urlsafe(32)
    for creds in [{'token_id':'invalid','token_secret':marker},{'token_id':'fixture@pve!token','token_secret':'bad\nvalue'}]:
        with pytest.raises(transport.SourceError) as error: SafeModule({'endpoint':'https://source.example.test:8006'},creds)
        assert marker not in str(error.value)


def test_candidate_rejects_privileged_root_account_tokens():
    with pytest.raises(transport.SourceError,match='authentication_failed'):
        SafeModule({'endpoint':'https://source.example.test:8006'},
                   {'token_id':'root@pam!fixture_'+secrets.token_hex(8),'token_secret':secrets.token_urlsafe(32)})
