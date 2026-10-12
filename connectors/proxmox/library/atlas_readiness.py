#!/usr/bin/python
# SPDX-License-Identifier: Apache-2.0
"""Candidate-only bounded authentication and whole-scope ACL readiness probe."""
import json
import os
import re
import signal
import time

from ansible.module_utils.atlas_discovery import SafeModule, collection, acl_proof, CapabilityError
from ansible.module_utils.atlas_transport import SourceError, PinnedAdapter, secure_api


def readiness(config, credentials, *, adapter_factory=PinnedAdapter):
    api = None
    version = None
    try:
        collection('proxmox_cluster_status_info')
        module = SafeModule(config, credentials)
        api = secure_api(module, config, time.monotonic() + 12, adapter_factory=adapter_factory)
        candidate = api.version.get().get('version')
        if isinstance(candidate, str) and re.fullmatch(r'[0-9]{1,3}(?:\.[0-9]{1,3}){1,3}(?:-[0-9]{1,4})?', candidate):
            version = candidate
        try:
            acl_proof(api)
            diagnostic = {'capability': 'inventory', 'state': 'ready', 'path_category': 'inventory'}
            limited = False
        except CapabilityError as error:
            diagnostic, limited = error.diagnostic, True
        except SourceError as error:
            # /version may be public. A failed authenticated ACL read must not
            # turn an invalid token or transport failure into "connected".
            if error.code != 'permission_limited':
                raise
            diagnostic, limited = {'capability': 'inventory', 'state': 'unproven', 'path_category': 'authorization'}, True
        return {'success': True, 'category': 'connected', 'source_version': version,
                'tls': config.get('tls_policy', 'verify'), 'permission_limited': limited, 'capability_diagnostics': [diagnostic]}
    except SourceError as error:
        return {'success': False, 'category': error.code if error.code in {'authentication_failed', 'permission_limited', 'tls_trust_required', 'timeout'} else 'source_unavailable', 'source_version': None}
    except (OSError, ValueError, KeyError, TypeError, ImportError):
        return {'success': False, 'category': 'source_unavailable', 'source_version': None}
    finally:
        if api:
            api._store['session'].close()


def main(*, adapter_factory=PinnedAdapter):
    from ansible.module_utils.basic import AnsibleModule
    from atlas_connector_sdk.contracts import strict_json
    module = AnsibleModule(argument_spec={'input_file': {'type': 'path', 'required': True},
                                         'result_file': {'type': 'path', 'required': True}}, supports_check_mode=False)
    descriptor = os.open(module.params['input_file'], os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, 'rb') as source:
        inputs = strict_json(source.read(128 * 1024 + 1), maximum=128 * 1024)
    def expired(*args): raise SourceError('timeout')
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 12)
    try:
        result = readiness(inputs['config'], inputs['credentials'], adapter_factory=adapter_factory)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        inputs.clear()
    descriptor = os.open(module.params['result_file'], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        json.dump(result, output)
    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
