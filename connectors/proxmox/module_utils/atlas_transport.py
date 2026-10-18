# SPDX-License-Identifier: Apache-2.0
"""GET-only adapter for the reviewed Proxmoxer HTTPS session.

No independent API client: collection resource methods, serializer and token auth
remain in use. Every authenticated request is carried over the vetted TLS socket.
"""
import hashlib
import http.client
import ipaddress
import re
import socket
import ssl
import time
from urllib.parse import urlsplit

from requests import Response
from requests.adapters import BaseAdapter
from proxmoxer.backends.https import ProxmoxHttpSession

MAX_RESPONSE = 1024 * 1024
MAX_CALLS = 4096
MAX_TOTAL_BYTES = 24 * 1024 * 1024
TIMEOUT = 6
SEGMENT = r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}'
ROUTES = re.compile(r'/api2/json/(?:version|access/(?:permissions|acl)|cluster/(?:status|resources)|nodes|nodes/'
                    + SEGMENT + r'/(?:network|(?:qemu|lxc)(?:/[1-9][0-9]{0,8}/config)?))')


class SourceError(ValueError):
    def __init__(self, code, *, reason=None):
        self.code = code
        self.reason = reason
        super().__init__(code)


def diagnostic_object(category, parts, row):
    """Only explicit durable identities; never names/comments/config values."""
    result = {}
    name = row.get('iface') if category == 'network' else row.get('node') or row.get('name')
    if isinstance(name, str) and re.fullmatch(SEGMENT, name):
        if category == 'network' and len(parts) > 4:
            result = {'object_class': 'proxmox.interface', 'external_id': 'node/' + parts[4] + '/interface/' + name}
        elif category in {'nodes', 'deployment'}:
            result = {'object_class': 'proxmox.node', 'external_id': 'node/' + name}
    kind = row.get('type') if category == 'guest_resources' else parts[5] if len(parts) > 5 else None
    vmid = row.get('vmid')
    if isinstance(kind, str) and kind in {'qemu', 'lxc'} and type(vmid) is int and 1 <= vmid <= 999999999:
        result = {'object_class': 'proxmox.' + kind, 'external_id': 'guest/' + kind + '/' + str(vmid)}
    return result


def endpoint(value):
    try:
        url = urlsplit(value)
        if (url.scheme != 'https' or not url.hostname or url.username is not None or url.password is not None
                or url.path not in {'', '/'} or url.query or url.fragment or url.port == 0
                or '\\' in value or any(ord(c) <= 32 or ord(c) == 127 for c in value)
                or url.hostname.lower() == 'localhost' or url.hostname.lower().endswith('.localhost')):
            raise ValueError
        return url.hostname, url.port or 443
    except (ValueError, TypeError):
        raise SourceError('source_unavailable') from None


def allowed_address(value):
    address = ipaddress.ip_address(value.split('%', 1)[0])
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        address = address.ipv4_mapped
    return not (address.is_loopback or address.is_link_local or address.is_multicast or address.is_unspecified
                or address.is_reserved or str(address) == '100.100.100.200')


class PinnedConnection(http.client.HTTPSConnection):
    def __init__(self, host, port, address, context, fingerprint, timeout):
        super().__init__(host, port, context=context, timeout=timeout)
        self.address, self.fingerprint = address, fingerprint

    def connect(self):
        raw = socket.create_connection((self.address, self.port), self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
            if self.fingerprint and hashlib.sha256(self.sock.getpeercert(binary_form=True)).hexdigest() != self.fingerprint:
                raise SourceError('tls_trust_required')
        except BaseException:
            raw.close()
            if self.sock:
                self.sock.close()
            raise


class PinnedAdapter(BaseAdapter):
    def __init__(self, config, deadline, *, resolver=None, connection_factory=None):
        super().__init__()
        self.host, self.port = endpoint(config['endpoint'])
        self.deadline = deadline
        self.factory = connection_factory or PinnedConnection
        self.fingerprint = None
        mode = config.get('tls_policy', 'verify')
        if mode == 'verify':
            self.context = ssl.create_default_context()
        elif mode == 'fingerprint':
            self.fingerprint = config.get('fingerprint', '').lower().replace(':', '')
            if not re.fullmatch(r'[a-f0-9]{64}', self.fingerprint):
                raise SourceError('tls_trust_required')
            self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            self.context.check_hostname = False
            self.context.verify_mode = ssl.CERT_NONE
        else:
            # Candidate discovery never accepts the probe's advanced insecure exception.
            raise SourceError('tls_trust_required')
        addresses = (resolver or socket.getaddrinfo)(self.host, self.port, type=socket.SOCK_STREAM)
        if not addresses or len(addresses) > 32 or any(not allowed_address(row[4][0]) for row in addresses):
            raise SourceError('source_unavailable')
        self.address = addresses[0][4][0]
        self.calls = self.total_bytes = 0
        self.last_error = None

    def send(self, request, **kwargs):
        connection = None
        diagnostics = getattr(self, 'diagnostics', None)
        reason = 'source_request_invalid'
        try:
            from atlas_connector_sdk.contracts import strict_json
            url = urlsplit(request.url)
            from urllib.parse import parse_qs
            query = parse_qs(url.query, strict_parsing=True)
            permitted = {}
            if url.path.endswith('/access/permissions'):
                permitted = {'path': None}
            elif url.path.endswith('/cluster/resources'):
                permitted = {'type': ['vm']}
            elif url.path.endswith('/config'):
                permitted = {'current': ['1']}
            if (request.method != 'GET' or request.body or url.scheme != 'https' or url.hostname != self.host
                    or (url.port or 443) != self.port or not ROUTES.fullmatch(url.path)
                    or url.username or url.password or url.fragment or set(query) - set(permitted)
                    or any(len(values) != 1 or permitted[key] is not None and values != permitted[key]
                           for key, values in query.items())
                    or url.path.endswith('/config') and query.get('current') != ['1']):
                raise SourceError('source_unavailable')
            category = ('version' if url.path.endswith('/version') else 'authorization' if '/access/' in url.path else
                        'deployment' if url.path.endswith('/cluster/status') else 'guest_resources' if '/cluster/' in url.path else
                        'guest_config' if url.path.endswith('/config') else 'network' if url.path.endswith('/network') else
                        'nodes' if url.path == '/api2/json/nodes' else 'guest_list')
            if diagnostics:
                diagnostics.at('source_read', source_category=category)
                parts = url.path.split('/')
                if len(parts) >= 6 and parts[3] == 'nodes':
                    diagnostics.context['parent_external_id'] = 'node/' + parts[4]
                    if len(parts) >= 8 and parts[5] in {'qemu', 'lxc'}:
                        diagnostics.context.update(object_class='proxmox.' + parts[5], external_id='guest/' + parts[5] + '/' + parts[6])
            reason = 'source_response_invalid'
            remaining = self.deadline - time.monotonic()
            self.calls += 1
            if remaining <= 0:
                raise SourceError('timeout')
            if self.calls > MAX_CALLS:
                reason = 'source_call_limit'
                raise SourceError('invalid_source_record')
            connection = self.factory(self.host, self.port, self.address, self.context, self.fingerprint, min(TIMEOUT, remaining))
            # http.client calls connect (including pin verification) before it sends headers.
            connection.request('GET', url.path + ('?' + url.query if url.query else ''), headers={
                'Authorization': request.headers['Authorization'], 'Accept': 'application/json', 'Accept-Encoding': 'identity'})
            response = connection.getresponse()
            if 300 <= response.status < 400:
                raise SourceError('source_unavailable')
            if response.status != 200:
                raise SourceError('authentication_failed' if response.status == 401 else
                                  'permission_limited' if response.status == 403 else 'source_unavailable')
            if response.getheader('Content-Encoding', 'identity') != 'identity':
                raise SourceError('source_unavailable')
            length = response.getheader('Content-Length')
            if length is not None and (not length.isdigit() or int(length) > MAX_RESPONSE):
                reason = 'source_response_limit'
                raise SourceError('invalid_source_record')
            raw = bytearray()
            while True:
                remaining = self.deadline - time.monotonic()
                if remaining <= 0:
                    raise SourceError('timeout')
                if getattr(connection, 'sock', None):
                    connection.sock.settimeout(min(TIMEOUT, remaining))
                chunk = response.read(min(65536, MAX_RESPONSE + 1 - len(raw)))
                raw.extend(chunk)
                if len(raw) > MAX_RESPONSE:
                    reason = 'source_response_limit'
                    raise SourceError('invalid_source_record')
                if not chunk:
                    break
            self.total_bytes += len(raw)
            if self.total_bytes > MAX_TOTAL_BYTES:
                reason = 'source_total_bytes_limit'
                raise SourceError('invalid_source_record')
            reason = 'source_json_invalid'
            value = strict_json(bytes(raw), maximum=MAX_RESPONSE)
            reason = 'source_response_invalid'
            if not isinstance(value, dict) or not isinstance(value.get('data'), (dict, list)):
                raise SourceError('invalid_source_record')
            mapping = url.path.endswith('/version') or url.path.endswith('/access/permissions') or url.path.endswith('/config')
            if (mapping and not isinstance(value['data'], dict)
                    or not mapping and (not isinstance(value['data'], list) or len(value['data']) > 1000
                                        or any(not isinstance(row, dict) for row in value['data']))):
                raise SourceError('invalid_source_record')
            # The reviewed collection converts several malformed non-boolean
            # values silently to False. Validate raw source flags before that
            # lossy conversion, so malformed inventory cannot earn COMPLETE.
            flags = set()
            if url.path.endswith('/cluster/status'):
                flags = {'online', 'local', 'quorate'}
            elif url.path.endswith('/cluster/resources') or re.search(r'/(qemu|lxc)$', url.path):
                flags = {'template'}
            elif url.path.endswith('/network'):
                # Proxmox can report exists: null on unrelated VLAN rows.
                # It is unused by discovery; retain strict topology flag checks.
                flags = {'active', 'autostart', 'bridge_vlan_aware'}
            if flags and isinstance(value['data'], list):
                for row in value['data']:
                    if not isinstance(row, dict) or any(type(row[key]) not in {int, bool} or row[key] not in {0, 1}
                                                        for key in flags & row.keys()):
                        reason = 'source_boolean_invalid'
                        if diagnostics and isinstance(row, dict):
                            diagnostics.context.update(diagnostic_object(category, parts, row))
                            field = next(key for key in sorted(flags & row.keys()) if type(row[key]) not in {int, bool} or row[key] not in {0, 1})
                            diagnostics.rule(field, row[field], 'strict_source_boolean', 'boolean_0_1')
                        raise SourceError('invalid_source_record')
            if diagnostics:
                diagnostics.emit('accepted', 'source_response_valid')
            result = Response()
            result.status_code, result._content = 200, bytes(raw)
            result.headers['Content-Type'] = 'application/json'
            return result
        except SourceError as error:
            if diagnostics:
                diagnostics.emit('warning', reason if error.code == 'invalid_source_record' else error.code)
            self.last_error = error.code
            raise
        except ssl.SSLError:
            if diagnostics:
                diagnostics.emit('warning', 'tls_trust_required')
            self.last_error = 'tls_trust_required'
            raise SourceError(self.last_error) from None
        except TimeoutError:
            if diagnostics:
                diagnostics.emit('warning', 'source_timeout')
            self.last_error = 'timeout'
            raise SourceError(self.last_error) from None
        except (OSError, ValueError, TypeError, KeyError, http.client.HTTPException):
            if diagnostics:
                diagnostics.emit('warning', reason)
            self.last_error = 'source_unavailable'
            raise SourceError(self.last_error) from None
        finally:
            if connection:
                connection.close()

    def close(self):
        pass


class SecuredSession(ProxmoxHttpSession):
    def request(self, method, url, *args, **kwargs):
        kwargs['allow_redirects'] = False
        return super().request(method, url, *args, **kwargs)


def secure_api(module, config, deadline, *, adapter_factory=PinnedAdapter):
    from ansible_collections.community.proxmox.plugins.module_utils.proxmox import ProxmoxAnsible

    class SecuredProxmox(ProxmoxAnsible):
        def _connect(self):
            adapter = adapter_factory(config, deadline)
            module.adapter = adapter
            adapter.diagnostics = getattr(module, 'diagnostics', None)
            api = super()._connect()  # token construction makes no network request
            original = api._store['session']
            session = SecuredSession()
            session.auth, session.trust_env = original.auth, False
            session.adapters.clear()
            session.mount('https://', adapter)
            original.close()
            api._store['session'] = session
            return api

    return SecuredProxmox(module).proxmox_api
