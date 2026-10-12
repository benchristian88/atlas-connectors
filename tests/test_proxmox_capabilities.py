# SPDX-License-Identifier: Apache-2.0
from test_proxmox_discovery import inputs, run
from proxmox_fixture_transport import fixture


def test_hidden_noaccess_override_is_detected_even_when_effective_dump_omits_it(inputs):
    data = fixture('permission_filtered')
    assert data['permissions']['/vms/999'] == {}
    result, calls = run(inputs, data=data)
    assert result[-1]['completeness'] == 'partial'
    assert '/access/permissions?path=%2Fvms%2F999' in calls
    assert {'code':'permission_limited'} in result[-1]['warnings']


def test_nonpropagated_grants_and_user_token_intersection_cannot_prove_whole_scope(inputs):
    for path, privilege in [('/vms','VM.Audit'),('/storage','Datastore.Audit'),('/sdn/zones/localnetwork','SDN.Audit'),('/nodes','Sys.Audit')]:
        for grants in [{privilege:0}, {}]:
            data = fixture(); data['permissions'][path] = grants
            result, _ = run(inputs, data=data)
            assert result[-1]['completeness'] == 'partial'


def test_empty_lists_are_insufficient_without_acl_audit_permission(inputs):
    result, calls = run(inputs, 'acl_audit_missing')
    assert result[-1]['completeness'] == 'partial'
    assert '/access/acl' not in calls


def test_candidate_readiness_is_bounded_sanitized_and_does_not_enumerate_inventory(inputs):
    import importlib.util
    from pathlib import Path
    from proxmox_fixture_transport import adapter_factory
    path=Path(__file__).resolve().parents[1]/'connectors/proxmox/library/atlas_readiness.py'
    spec=importlib.util.spec_from_file_location('candidate_readiness',path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    for scenario in ['complete','permission_filtered','acl_audit_missing']:
        factory=adapter_factory(fixture(scenario))
        result=module.readiness(inputs['config'],inputs['credentials'],adapter_factory=factory)
        assert result['success'] and result['permission_limited']==(scenario!='complete')
        assert not any(path.startswith('/nodes') or path.startswith('/cluster') or path=='/storage' for path in factory.calls)
        diagnostic=result['capability_diagnostics'][0]
        assert set(diagnostic)<= {'capability','state','path_category','privilege'}
        if scenario=='permission_filtered':
            assert diagnostic['capability']=='inventory.guests' and diagnostic['privilege']=='VM.Audit'


def test_public_version_does_not_make_invalid_token_a_successful_connection(inputs):
    import importlib.util
    from pathlib import Path
    from proxmox_fixture_transport import adapter_factory
    path=Path(__file__).resolve().parents[1]/'connectors/proxmox/library/atlas_readiness.py'
    spec=importlib.util.spec_from_file_location('candidate_readiness_auth',path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    data=fixture(); data['failures']['/access/permissions?path=%2Faccess']=401
    factory=adapter_factory(data)
    result=module.readiness(inputs['config'],inputs['credentials'],adapter_factory=factory)
    assert result['success'] is False and result['category']=='authentication_failed'
    messages,calls=run(inputs,data=data)
    assert messages[-1]['completeness']=='failed'
    assert not any(path.startswith('/nodes') or path.startswith('/cluster') for path in calls)
