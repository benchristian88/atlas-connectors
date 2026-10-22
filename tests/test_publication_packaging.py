# SPDX-License-Identifier: Apache-2.0
"""Generic packaging and workflow contracts; no execution or real signatures."""
from copy import deepcopy
from pathlib import Path
import json
import shutil
import sys
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_bundle
import release_connector


def test_frozen_archives_remain_exact():
    import hashlib
    assert hashlib.sha256(build_bundle.build()[0]).hexdigest()=='a14fec5ab485c980688ff5907e8835ddd3e9cecd1a6989ef252cbcb1b1dc4ef8'
    assert hashlib.sha256(build_bundle.build(candidate=True)[0]).hexdigest()=='dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97'


@pytest.fixture
def future(tmp_path,monkeypatch):
    source=tmp_path/'connectors/future-hypervisor'
    shutil.copytree(ROOT/'connectors/proxmox',source)
    shutil.copyfile(ROOT/'LICENSE',tmp_path/'LICENSE')
    manifest=json.loads((source/'manifest.json').read_bytes())
    manifest.update(id='future-hypervisor',version='12.3.4')
    (source/'manifest.json').write_text(json.dumps(manifest))
    monkeypatch.setattr(build_bundle,'ROOT',tmp_path)
    monkeypatch.setattr(release_connector,'ROOT',tmp_path)
    monkeypatch.setattr(build_bundle.subprocess,'check_output',lambda *a,**k:'a'*40+'\n')
    return source


def test_future_qualified_connector_needs_no_code_allowlist(future,tmp_path):
    assert release_connector.select('future-hypervisor-v12.3.4')=='future-hypervisor'
    raw,manifest=build_bundle.build('future-hypervisor',output=tmp_path/'output')
    assert raw==build_bundle.build('future-hypervisor')[0]
    assert manifest['distribution']['asset_uri'].endswith('/future-hypervisor-v12.3.4/future-hypervisor-12.3.4.tar.gz')
    assert (tmp_path/'output/future-hypervisor-12.3.4.tar.gz').read_bytes()==raw


def test_tag_requires_actual_qualified_manifest(future):
    with pytest.raises(ValueError):release_connector.select('future-hypervisor-v12.3.5')
    manifest=json.loads((future/'manifest.json').read_bytes())
    manifest['source_versions'].update(qualification='unqualified',qualified_versions=[])
    (future/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='qualification'):release_connector.select('future-hypervisor-v12.3.4')


@pytest.mark.parametrize('name',['../LICENSE','/etc/passwd','a\\b','a\nb','candidate/manifest.json','tests/a.py','x/../y'])
def test_package_recipe_paths_fail_closed(future,name):
    recipe=json.loads((future/'package.json').read_bytes())
    recipe['files']=sorted(set(recipe['files']+[name]))
    (future/'package.json').write_text(json.dumps(recipe))
    with pytest.raises(ValueError):build_bundle.build('future-hypervisor')


def test_symlink_source_rejected(future):
    (future/'NOTICE').unlink()
    (future/'NOTICE').symlink_to(future/'README.md')
    with pytest.raises(ValueError):build_bundle.build('future-hypervisor')


def test_workflows_have_explicit_security_boundaries():
    import yaml
    workflows={p.stem:yaml.safe_load(p.read_text()) for p in (ROOT/'.github/workflows').glob('*.yml')}
    publish=workflows['catalogue-publish']
    assert publish['concurrency']=={'group':'official-catalogue-publication','cancel-in-progress':False}
    job=publish['jobs']['publish']
    assert job['environment']=='catalogue-publication'
    assert "github.ref == 'refs/heads/main'" in job['if']
    assert 'github.run_attempt == 1' in job['if']
    assert job['permissions']=={'contents':'read','actions':'read','id-token':'write','attestations':'write'}
    steps = job['steps']
    preflight = next(i for i, step in enumerate(steps) if step.get('run') == 'python tools/publish_catalogue.py authorize')
    mint = next(i for i, step in enumerate(steps) if step.get('uses', '').startswith('actions/create-github-app-token@'))
    assert preflight < mint
    assert steps[preflight]['env']['ATLAS_PUBLICATION_TOKEN'] == '${{ github.token }}'
    assert steps[mint]['with'] == {
        'app-id': '${{ vars.PUBLICATION_APP_ID }}', 'private-key': '${{ secrets.PUBLICATION_APP_PRIVATE_KEY }}',
        'owner': 'benchristian88', 'repositories': 'atlas-connectors',
        'permission-contents': 'write', 'permission-actions': 'read', 'permission-administration': 'read'}
    for step in steps:
        if step.get('run') in {'python tools/publish_catalogue.py ' + phase for phase in ('stage', 'finish', 'recover')}:
            assert step['env']['ATLAS_APP_SLUG'] == '${{ steps.app.outputs.app-slug }}'
            assert step['env']['ATLAS_APP_INSTALLATION_ID'] == '${{ steps.app.outputs.installation-id }}'
    # Owner activation is an explicit reviewed policy change, not a reason to
    # edit a regression test. Runtime tests exercise disabled-policy rejection.
    assert type(json.loads((ROOT/'catalogue/publication/policy.json').read_bytes())['enabled']) is bool
    for workflow in workflows.values():
        for job in workflow['jobs'].values():
            if 'uses' in job:
                # The experiment's local reusable call resolves to the caller's
                # same commit. Continue enforcing full SHAs on action steps.
                assert job['uses']=='./.github/workflows/verifier-signer-probe.yml'
                assert 'steps' not in job and 'secrets' not in job
                continue
            for step in job['steps']:
                if 'uses' in step:
                    assert len(step['uses'].split('@')[1])==40
                    if step['uses'].startswith('actions/checkout@'):
                        assert step['with']['persist-credentials'] is False
    assert workflows['catalogue']['jobs']['prepare']['permissions']['contents']=='read'
    assert workflows['release']['jobs']['prepare']['permissions']['contents']=='read'
