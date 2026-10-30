# SPDX-License-Identifier: Apache-2.0
"""Local release regressions. Provider positives are models, never live acceptance."""
from copy import deepcopy
import gzip
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import build_bundle
import connector_release as contract
import release_connector as release
import verify_connector_release as verify
from build_catalogue import load_registry, validate_entry
from publication_contract import API, APP_PERMISSIONS, REPOSITORY, canonical_json, digest
from publication_github import Github
from publication_verify import Verifier
from test_publication_contract import authority_fixture
from test_publication_state import StructuralVerifier, structural_bundle

TAG = 'proxmox-v0.2.1'
RUN = 60


@pytest.fixture(params=['0.2.1', '0.2.2'])
def release_version(request):
    return request.param


@pytest.fixture
def release_tag(release_version):
    return 'proxmox-v' + release_version


@pytest.fixture
def package(release_version):
    return build_bundle.build(version=release_version)


def repack(files, *, extra=None, kind=None):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        rows = list(files.items())
        if extra:
            rows.append(extra)
        for name, raw in rows:
            info = tarfile.TarInfo(name)
            info.mode = 0o644
            info.size = len(raw)
            if kind is not None and name == rows[-1][0]:
                info.type = kind
                info.linkname = '../outside'
                info.size = 0
            archive.addfile(info, io.BytesIO(raw))
    return gzip.compress(output.getvalue(), mtime=0)


def validate_changed(files, manifest):
    raw = repack(files)
    manifest = deepcopy(manifest)
    manifest['distribution']['bundle_digest'] = 'sha256:' + digest(raw)
    return contract.validate_package(raw, manifest, 'proxmox-v' + manifest['version'])


def test_reproducible_patch_release_preserves_all_qualified_behavior(tmp_path, package, release_tag, release_version):
    raw, manifest = package
    first = release.prepare(release_tag, tmp_path / 'first')
    second = release.prepare(release_tag, tmp_path / 'second')
    assert first == second == manifest
    for path in (tmp_path / 'first').iterdir():
        assert path.read_bytes() == (tmp_path / 'second' / path.name).read_bytes()
    old_raw, old_manifest = build_bundle.build()
    old = contract.inspect_archive(old_raw)
    new = contract.validate_package(raw, manifest, release_tag)
    assert old.keys() == new.keys()
    changed = {name for name in old if old[name] != new[name]}
    assert changed == {'manifest.json', 'sbom.spdx.json', 'README.md', 'docs/qualification.md'}
    assert {k: v for k, v in manifest.items() if k not in {'version', 'distribution'}} == {
        k: v for k, v in old_manifest.items() if k not in {'version', 'distribution'}}
    assert digest(old_raw) == 'a14fec5ab485c980688ff5907e8835ddd3e9cecd1a6989ef252cbcb1b1dc4ef8'
    assert digest(build_bundle.build(candidate=True)[0]) == 'dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97'
    assert release.selection(release_tag) == ('proxmox', release_version)
    assert release.select(release_tag) == 'proxmox'
    assert first['version'] == release_version
    assert f'No live {release_version} artifact acceptance'.encode() in new['docs/qualification.md']


def test_new_release_changes_only_approved_metadata_and_preserves_historical_patch():
    old_raw, old_manifest = build_bundle.build(version='0.2.1')
    raw, manifest = build_bundle.build(version='0.2.2')
    old = contract.validate_package(old_raw, old_manifest, TAG)
    new = contract.validate_package(raw, manifest, 'proxmox-v0.2.2')
    overrides = ['README.md', 'docs/qualification.md', 'manifest.json', 'sbom.spdx.json']
    _, recipe = build_bundle.recipe('proxmox')
    assert recipe['release_overrides'] == {'0.2.1': overrides, '0.2.2': overrides}
    assert old.keys() == new.keys()
    assert {name for name in old if old[name] != new[name]} == set(overrides)
    assert digest(old_raw) == '96eaa736c2919e56e09b9613dddd8648ad1f43b77679899ab706261b2a38e509'

    old_domain = json.loads(old['manifest.json'])
    new_domain = json.loads(new['manifest.json'])
    assert old_domain.pop('version') == '0.2.1'
    assert new_domain.pop('version') == '0.2.2'
    assert old_domain == new_domain
    assert 'distribution' not in new_domain
    assert manifest['source_versions'] == {
        'qualification': 'qualified', 'qualified_versions': ['9.2.11'],
        'known_incompatible': [], 'newer_untested_policy': 'allow_with_warning'}
    assert manifest['distribution']['asset_uri'].endswith('/proxmox-v0.2.2/proxmox-0.2.2.tar.gz')

    old_sbom = json.loads(old['sbom.spdx.json'])
    new_sbom = json.loads(new['sbom.spdx.json'])
    assert new_sbom['name'] == 'atlas-proxmox-0.2.2'
    assert new_sbom['documentNamespace'] == f'https://github.com/{REPOSITORY}/sbom/proxmox/0.2.2'
    assert new_sbom['packages'][0]['versionInfo'] == '0.2.2'
    # Dependency versions, checksums, licences, notices, SPDX IDs and relationships stay exact.
    old_sbom['name'] = new_sbom['name']
    old_sbom['documentNamespace'] = new_sbom['documentNamespace']
    old_sbom['packages'][0]['versionInfo'] = new_sbom['packages'][0]['versionInfo']
    old_sbom['creationInfo']['created'] = new_sbom['creationInfo']['created']
    assert old_sbom == new_sbom


@pytest.mark.parametrize('version', ['0.2.3', '0.3.0', '0.2.2-rc.1', '0.2.2+other', '../0.2.2'])
def test_unregistered_or_invalid_future_overlay_cannot_be_built(version):
    with pytest.raises(ValueError, match='unknown_release_version'):
        build_bundle.build(version=version)


def test_local_preparation_has_no_publication_or_catalogue_authority(tmp_path, monkeypatch, release_tag, release_version):
    def catalogue_bytes():
        return {str(p.relative_to(ROOT)): p.read_bytes() for p in (ROOT / 'catalogue').rglob('*') if p.is_file()}
    before = catalogue_bytes()
    registry = load_registry(ROOT / 'catalogue')
    manifest = release.prepare(release_tag, tmp_path / 'local')
    assert {p.name for p in (tmp_path / 'local').iterdir()} == {
        contract.filename(manifest), 'manifest.json', 'index.json', 'SHA256SUMS'}
    assert not (ROOT / 'catalogue/releases' / f'proxmox-{release_version}.json').exists()
    assert all(entry['release_tag'] != release_tag for entry in registry[1])
    assert load_registry(ROOT / 'catalogue') == registry
    assert catalogue_bytes() == before

    class NoProvider:
        def __getattr__(self, name):
            pytest.fail('Unattested local preparation reached provider access: ' + name)

    # Model clean-source admission to isolate the independent missing-signature gate.
    # The real dirty-source rejection is covered separately; this is not release evidence.
    monkeypatch.setattr(verify, 'clean_source', lambda commit: None)
    with pytest.raises(FileNotFoundError):
        verify.verify_build(NoProvider(), Verifier(), tmp_path / 'local', tag=release_tag,
            commit=manifest['distribution']['provenance']['source_commit'],
            expected_digest=manifest['distribution']['bundle_digest'][7:], run_id=RUN)
    assert catalogue_bytes() == before


@pytest.mark.parametrize('tag', ['proxmox-v0.2.0', 'proxmox-v0.2.3', 'proxmox-v0.3.0',
    'proxmox-v0.2.1\n', 'proxmox-v0.2.2\n', 'proxmox-v0.2.2-rc.1', 'proxmox-v0.2.2+other',
    'proxmox-v00.2.2', 'other-v0.2.1', 'other-v0.2.2'])
def test_wrong_or_registered_release_cannot_be_prepared(tmp_path, tag):
    with pytest.raises(ValueError):
        release.prepare(tag, tmp_path / 'output')
    assert not (tmp_path / 'output').exists()


def test_no_output_overwrite(tmp_path, release_tag):
    release.prepare(release_tag, tmp_path)
    (tmp_path / 'manifest.json').write_bytes(b'prior human reviewed bytes')
    with pytest.raises(ValueError, match='output_must_be_empty'):
        release.prepare(release_tag, tmp_path)
    assert (tmp_path / 'manifest.json').read_bytes() == b'prior human reviewed bytes'


@pytest.fixture
def source(tmp_path, monkeypatch):
    shutil.copytree(ROOT / 'connectors', tmp_path / 'connectors')
    shutil.copyfile(ROOT / 'LICENSE', tmp_path / 'LICENSE')
    monkeypatch.setattr(build_bundle, 'ROOT', tmp_path)
    monkeypatch.setattr(release, 'ROOT', tmp_path)
    monkeypatch.setattr(build_bundle.subprocess, 'check_output', lambda *a, **k: 'a' * 40 + '\n')
    return tmp_path / 'connectors/proxmox'


@pytest.mark.parametrize('version', ['../0.2.1', '0.2.0', '0.1.0', '0.2.1-rc.1', '0.2.1+other', '01.2.1'])
def test_overlay_version_rejects_aliases_and_historical_reinterpretation(source, version):
    recipe = json.loads((source / 'package.json').read_bytes())
    recipe['release_overrides'][version] = recipe['release_overrides'].pop('0.2.1')
    (source / 'package.json').write_text(json.dumps(recipe))
    with pytest.raises(ValueError):
        build_bundle.build(version=version)


def test_overlay_requires_manifest_match_and_safe_regular_files(source, release_version):
    path = source / 'releases' / release_version / 'manifest.json'
    manifest = json.loads(path.read_bytes())
    manifest['version'] = '0.2.3'
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='identity'):
        build_bundle.build(version=release_version)
    path.unlink()
    path.symlink_to(source / 'manifest.json')
    with pytest.raises(ValueError, match='unsafe_package_file'):
        build_bundle.build(version=release_version)


@pytest.mark.parametrize('missing', ['manifest.json', 'sbom.spdx.json', 'README.md', 'docs/qualification.md'])
def test_release_overlay_requires_versioned_metadata(source, missing, release_version):
    recipe = json.loads((source / 'package.json').read_bytes())
    recipe['release_overrides'][release_version].remove(missing)
    (source / 'package.json').write_text(json.dumps(recipe))
    with pytest.raises(ValueError, match='release_overrides'):
        build_bundle.build(version=release_version)


@pytest.mark.parametrize('connector', ['docker', 'unifi', 'future-hypervisor'])
def test_future_connector_uses_same_release_contract(source, tmp_path, connector, release_version):
    future = source.with_name(connector)
    source.rename(future)
    for directory in [future, *sorted((future / 'releases').iterdir())]:
        path = directory / 'manifest.json'
        manifest = json.loads(path.read_bytes())
        manifest['id'] = connector
        path.write_text(json.dumps(manifest))
        path = directory / 'sbom.spdx.json'
        sbom = json.loads(path.read_bytes())
        sbom['name'] = sbom['name'].replace('atlas-proxmox-', f'atlas-{connector}-')
        sbom['documentNamespace'] = sbom['documentNamespace'].replace('/proxmox/', f'/{connector}/')
        sbom['packages'][0]['name'] = 'atlas-' + connector
        path.write_text(json.dumps(sbom))
    manifest = release.prepare(f'{connector}-v{release_version}', tmp_path / 'output')
    assert manifest['id'] == connector


@pytest.mark.parametrize('dirty,head', [(b' M tools/release_connector.py\n', 'a' * 40),
                                        (b'?? ignored-release-source.py\n', 'a' * 40), (b'', 'b' * 40)])
def test_clean_source_is_exact_and_rejects_uncommitted_work(monkeypatch, dirty, head):
    def output(args, **kwargs):
        if args == ['git', 'rev-parse', 'HEAD']:
            return head + '\n'
        assert args == ['git', 'status', '--porcelain=v1', '--untracked-files=all']
        return dirty
    monkeypatch.setattr(subprocess, 'check_output', output)
    with pytest.raises(ValueError, match='clean_exact_source'):
        contract.clean_source('a' * 40)


@pytest.mark.parametrize('name', ['../escape', '/absolute', 'a/../escape', 'tests/a.py', 'fixtures/a.json'])
def test_archive_unsafe_paths_fail_before_any_extraction(package, name):
    files = contract.inspect_archive(package[0])
    with pytest.raises(ValueError, match='archive_path'):
        contract.inspect_archive(repack(files, extra=(name, b'x')))


@pytest.mark.parametrize('kind', [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.DIRTYPE,
                                 tarfile.XHDTYPE, tarfile.GNUTYPE_LONGNAME, tarfile.CHRTYPE])
def test_nonregular_and_hidden_extension_headers_rejected(package, kind):
    files = contract.inspect_archive(package[0])
    with pytest.raises(ValueError):
        contract.inspect_archive(repack(files, extra=('extra', b'x'), kind=kind))


def test_duplicates_compression_bombs_truncated_and_concatenated_archives(package):
    files = contract.inspect_archive(package[0])
    cases = [repack(files, extra=('manifest.json', b'{}')), package[0][:-4], package[0] * 2,
             gzip.compress(b'x' * (contract.MAX_ARCHIVE + 1)), b'not gzip']
    for raw in cases:
        with pytest.raises(ValueError):
            contract.inspect_archive(raw)


@pytest.mark.parametrize('change', ['manifest_version', 'qualification', 'sdk', 'runtime', 'aip', 'digest'])
def test_invalid_manifest_qualification_compatibility_or_digest(package, change, release_tag):
    raw, manifest = package
    if change == 'manifest_version': manifest['version'] = '0.2.3'
    elif change == 'qualification': manifest['source_versions'].update(qualification='unqualified', qualified_versions=[])
    elif change == 'sdk': manifest['compatibility']['sdk'] = {'minimum': '2.0.0', 'exclusive_maximum': '3.0.0'}
    elif change == 'runtime': manifest['compatibility']['runtime']['baseline'] = {'minimum': '2.0.0', 'exclusive_maximum': '3.0.0'}
    elif change == 'aip': manifest['compatibility']['aip'] = ['9.0']
    elif change == 'digest': manifest['distribution']['bundle_digest'] = 'sha256:' + '0' * 64
    with pytest.raises(ValueError):
        contract.validate_package(raw, manifest, release_tag)


@pytest.mark.parametrize('change', ['version', 'digest', 'licence', 'duplicate', 'missing', 'relationship', 'namespace'])
def test_sbom_identity_dependency_licence_and_relationship_must_match(package, change):
    raw, manifest = package
    files = contract.inspect_archive(raw)
    sbom = json.loads(files['sbom.spdx.json'])
    if change == 'version': sbom['packages'][0]['versionInfo'] = '0.2.0'
    elif change == 'digest': sbom['packages'][1]['checksums'][0]['checksumValue'] = 'a' * 64
    elif change == 'licence': sbom['packages'][0]['licenseDeclared'] = 'NOASSERTION'
    elif change == 'duplicate': sbom['packages'].append(sbom['packages'][1])
    elif change == 'missing': sbom['packages'].pop()
    elif change == 'relationship': sbom['relationships'] = []
    elif change == 'namespace': sbom['documentNamespace'] += '-other'
    files['sbom.spdx.json'] = json.dumps(sbom).encode()
    with pytest.raises(ValueError, match='sbom'):
        validate_changed(files, manifest)


@pytest.mark.parametrize('missing', ['LICENSE', 'NOTICE', 'sbom.spdx.json', 'discover.yml', 'docs/qualification.md'])
def test_required_licence_qualification_and_entrypoint_files(package, missing):
    files = contract.inspect_archive(package[0])
    del files[missing]
    with pytest.raises(ValueError):
        validate_changed(files, package[1])


def test_archive_manifest_and_metadata_bounds(package):
    files = contract.inspect_archive(package[0])
    files['manifest.json'] = files['manifest.json'].replace(package[1]['version'].encode(), b'0.2.0')
    with pytest.raises(ValueError, match='manifest_mismatch'):
        validate_changed(files, package[1])
    files['manifest.json'] = b' ' * (contract.MAX_METADATA + 1)
    with pytest.raises(ValueError, match='metadata_too_large'):
        validate_changed(files, package[1])
    files['manifest.json'] = b'{"id":"proxmox","id":"other"}'
    with pytest.raises(ValueError, match='duplicate_metadata_key'):
        validate_changed(files, package[1])


class PackageProvider(Github):
    """Deterministic responses; no sockets, keys, tokens or provider mutations."""
    def __init__(self, files, manifest):
        self.calls = []
        self.read_count = 0
        self.change_after_download = False
        self.source = manifest['distribution']['provenance']['source_commit']
        self.tag = manifest['id'] + '-v' + manifest['version']
        policy = json.loads((ROOT / 'catalogue/publication/policy.json').read_bytes())
        args = authority_fixture()
        _, repo, branch, environment, run, attempt, workflow, _, checks = args
        self.actor = {'id': policy['app_bot_user_id'], 'type': 'Bot', 'login': policy['app_slug'] + '[bot]'}
        branch['commit']['sha'] = self.source
        environment.update(id=policy['package_environment_id'], name='connector-release',
                           deployment_branch_policy={'protected_branches': False, 'custom_branch_policies': True})
        workflow['path'] = '.github/workflows/release.yml'
        for row in (run, attempt):
            row.update(head_sha=self.source, head_branch=self.tag, event='push', path=workflow['path'],
                       actor=deepcopy(self.actor), triggering_actor=deepcopy(self.actor), status='completed', conclusion='success')
        checks['check_runs'][0]['head_sha'] = self.source
        self.rows = {'/': repo, '/branches/main': branch, '/environments/connector-release': environment,
            '/environments/connector-release/deployment-branch-policies?per_page=100':
                {'total_count': 1, 'branch_policies': [{'id': 52, 'name': '*-v*', 'type': 'tag'}]},
            '/actions/runs/60': run, '/actions/runs/60/attempts/1': attempt, '/actions/workflows/80': workflow,
            '/users/atlas-catalogue-publisher%5Bbot%5D': self.actor,
            '/users/benchristian88': {'id': 93822871, 'login': 'benchristian88', 'type': 'User'},
            f'/commits/{self.source}/check-runs?check_name=validate&filter=latest&per_page=100': checks,
            f'/compare/{self.source}...main': {'status': 'identical', 'merge_base_commit': {'sha': self.source}},
            '/apps/atlas-catalogue-publisher': {'id': policy['app_id'], 'slug': policy['app_slug'],
                                              'owner': {'id': 93822871}, 'permissions': deepcopy(APP_PERMISSIONS)},
            '/git/ref/tags/' + self.tag: {'object': {'type': 'commit', 'sha': self.source}}}
        self.release_row = {'id': 100, 'url': API + '/releases/100', 'tag_name': self.tag, 'target_commitish': self.source,
                            'draft': False, 'prerelease': False, 'immutable': True, 'author': deepcopy(self.actor)}
        self.assets_list, self.data = [], {}
        for i, (name, raw) in enumerate(files.items(), 200):
            self.assets_list.append({'id': i, 'name': name, 'url': API + f'/releases/assets/{i}',
                'browser_download_url': manifest['distribution']['asset_uri'].rsplit('/', 1)[0] + '/' + name,
                'uploader': deepcopy(self.actor), 'state': 'uploaded', 'size': len(raw), 'digest': 'sha256:' + digest(raw)})
            self.data[i] = raw

    def json(self, method, path, **kwargs):
        assert method == 'GET', 'Verifier attempted a provider mutation'
        self.calls.append(path)
        if path in {'/releases/100', '/releases/tags/' + self.tag}:
            row = deepcopy(self.release_row)
            if self.change_after_download and self.read_count:
                row['immutable'] = False
            return row
        if path == '/releases/100/assets?per_page=100': return deepcopy(self.assets_list)
        assert path in self.rows, path
        return deepcopy(self.rows[path])

    def request(self, method, path, **kwargs):
        assert method == 'GET'
        self.calls.append(path)
        self.read_count += 1
        return self.data[int(path.rsplit('/', 1)[1])]


@pytest.fixture
def publication(tmp_path, monkeypatch, release_tag):
    manifest = release.prepare(release_tag, tmp_path)
    commit = manifest['distribution']['provenance']['source_commit']
    files = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    raw = files[contract.filename(manifest)]
    bundle = structural_bundle(raw, 'package', contract.filename(manifest), commit=commit, run=RUN)
    (tmp_path / 'package.sigstore.json').write_bytes(bundle)
    files['package.sigstore.json'] = bundle
    api = PackageProvider(files, manifest)
    # Model only the clean checkout admission here; actual Git rejection has its own tests.
    monkeypatch.setattr(verify, 'clean_source', lambda source: None)
    context = {'tag': release_tag, 'commit': commit, 'expected_digest': digest(raw), 'run_id': RUN,
               'release_id': 100, 'asset_id': next(a['id'] for a in api.assets_list if a['name'] == contract.filename(manifest)),
               'approved_assets': {a['name']: {'id': a['id'], 'sha256': a['digest'][7:], 'bytes': a['size']}
                                   for a in api.assets_list}}
    return api, tmp_path, context


def verified(publication):
    api, directory, context = publication
    return verify.verify(api, StructuralVerifier(), directory, **context)


def test_verified_provider_identity_yields_existing_four_field_registry_and_repeat_is_read_only(publication, release_version):
    first = verified(publication)
    assert first == verified(publication)
    assert first['result'] == 'immutable_package_verified_catalogue_pending'
    assert first['immutable'] is True
    entry = first['registry_entry']
    assert entry.keys() == {'status', 'release_tag', 'release_asset_id', 'manifest'}
    validate_entry(entry)
    assert entry['manifest']['version'] == release_version
    assert not (ROOT / 'catalogue/releases' / f'proxmox-{release_version}.json').exists()
    assert first['assets']['package.sigstore.json']['sha256']


@pytest.mark.parametrize('field,value', [('immutable', False), ('immutable', None), ('immutable', 'true'),
    ('draft', True), ('prerelease', True), ('tag_name', 'proxmox-v0.2.0'), ('target_commitish', 'b' * 40),
    ('id', 101), ('author', {'id': 93822871, 'login': 'benchristian88', 'type': 'User'})])
def test_mutable_draft_wrong_source_tag_id_or_publisher_rejected(publication, field, value):
    publication[0].release_row[field] = value
    with pytest.raises(ValueError):
        verified(publication)


@pytest.mark.parametrize('change', ['missing', 'wrong_id', 'wrong_name', 'digest', 'size', 'uploader', 'url', 'bytes', 'duplicate'])
def test_partial_conflicting_or_tampered_release_assets_rejected_without_repair(publication, change):
    api, _, context = publication
    asset = next(a for a in api.assets_list if a['id'] == context['asset_id'])
    if change == 'missing': api.assets_list.remove(asset)
    elif change == 'wrong_id': asset['id'] += 1000
    elif change == 'wrong_name': asset['name'] = 'proxmox-latest.tar.gz'
    elif change == 'digest': asset['digest'] = 'sha256:' + '0' * 64
    elif change == 'size': asset['size'] += 1
    elif change == 'uploader': asset['uploader'] = {'id': 93822871, 'login': 'benchristian88', 'type': 'User'}
    elif change == 'url': asset['browser_download_url'] = 'https://example.test/package.tar.gz'
    elif change == 'bytes': api.data[asset['id']] += b'tampered'
    elif change == 'duplicate': api.assets_list.append(deepcopy(asset))
    for _ in range(2):
        with pytest.raises(ValueError):
            verified(publication)


@pytest.mark.parametrize('name', ['manifest.json', 'index.json', 'SHA256SUMS', 'package.sigstore.json'])
def test_approved_nonpackage_asset_ids_cannot_be_substituted(publication, name):
    api, _, _ = publication
    asset = next(a for a in api.assets_list if a['name'] == name)
    raw = api.data.pop(asset['id'])
    asset['id'] += 1000
    asset['url'] = API + f"/releases/assets/{asset['id']}"
    api.data[asset['id']] = raw
    with pytest.raises(ValueError, match='approved_asset'):
        verified(publication)


@pytest.mark.parametrize('change', ['missing', 'extra', 'bool_id', 'duplicate_id', 'sha256', 'bytes', 'fields', 'not_object'])
def test_incomplete_or_conflicting_operator_inventory_fails_closed(publication, change):
    approved = publication[2]['approved_assets']
    asset = approved['manifest.json']
    if change == 'missing': del approved['manifest.json']
    elif change == 'extra': approved['unexpected'] = deepcopy(asset)
    elif change == 'bool_id': asset['id'] = True
    elif change == 'duplicate_id': asset['id'] = approved['index.json']['id']
    elif change == 'sha256': asset['sha256'] = '0' * 64
    elif change == 'bytes': asset['bytes'] += 1
    elif change == 'fields': asset['untrusted'] = 'ignored?'
    elif change == 'not_object': publication[2]['approved_assets'] = []
    with pytest.raises(ValueError, match='approved_asset'):
        verified(publication)


def test_published_cli_requires_operator_inventory_before_provider_reads(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['verify_connector_release.py', '--directory', 'unused', '--tag', TAG,
        '--source-commit', 'a' * 40, '--expected-digest', 'b' * 64, '--run-id', str(RUN),
        '--release-id', '100', '--asset-id', '200'])
    def unexpected_network():
        pytest.fail('Provider access before required operator identity input')
    monkeypatch.setattr(verify, 'ReadOnlyGithub', unexpected_network)
    with pytest.raises(SystemExit) as error:
        verify.main()
    assert error.value.code == 1
    assert 'release_approved_asset_inventory_required' in capsys.readouterr().err


def test_sbom_package_ids_cannot_collide_with_document_id(package):
    files = contract.inspect_archive(package[0])
    sbom = json.loads(files['sbom.spdx.json'])
    sbom['packages'][0]['SPDXID'] = sbom['SPDXID']
    sbom['relationships'][0]['spdxElementId'] = sbom['SPDXID']
    files['sbom.spdx.json'] = json.dumps(sbom).encode()
    with pytest.raises(ValueError, match='sbom'):
        validate_changed(files, package[1])


@pytest.mark.parametrize('record', ['/actions/runs/60', '/actions/runs/60/attempts/1'])
@pytest.mark.parametrize('field,value', [('run_attempt', 2), ('head_sha', 'b' * 40), ('head_branch', 'proxmox-v0.2.0'),
    ('event', 'workflow_dispatch'), ('path', '.github/workflows/other.yml'), ('conclusion', 'failure'),
    ('actor', {'id': 93822871, 'login': 'benchristian88', 'type': 'User'}),
    ('triggering_actor', {'id': 93822871, 'login': 'benchristian88', 'type': 'User'})])
def test_run_and_first_attempt_authority_fail_closed(publication, record, field, value):
    publication[0].rows[record][field] = value
    with pytest.raises(ValueError):
        verified(publication)


@pytest.mark.parametrize('change', ['ci', 'ancestry', 'environment', 'app', 'tag_source', 'tag_policy'])
def test_missing_or_wrong_independent_authority_evidence(publication, change):
    api, _, context = publication
    if change == 'ci': api.rows[f'/commits/{context["commit"]}/check-runs?check_name=validate&filter=latest&per_page=100']['check_runs'][0]['conclusion'] = 'failure'
    elif change == 'ancestry': api.rows[f'/compare/{context["commit"]}...main']['status'] = 'diverged'
    elif change == 'environment': api.rows['/environments/connector-release']['can_admins_bypass'] = True
    elif change == 'app': api.rows['/apps/atlas-catalogue-publisher']['permissions']['workflows'] = 'write'
    elif change == 'tag_source': api.rows['/git/ref/tags/' + context['tag']]['object']['sha'] = 'b' * 40
    elif change == 'tag_policy': api.rows['/environments/connector-release/deployment-branch-policies?per_page=100']['total_count'] = 2
    with pytest.raises(ValueError):
        verified(publication)


@pytest.mark.parametrize('field,value', [('expected_digest', '0' * 64), ('commit', 'b' * 40), ('run_id', 61),
                                        ('release_id', True), ('asset_id', 99999)])
def test_reviewed_expected_identity_cannot_be_substituted(publication, field, value):
    publication[2][field] = value
    with pytest.raises(ValueError):
        verified(publication)


@pytest.mark.parametrize('name', ['manifest.json', 'index.json', 'SHA256SUMS', 'archive', 'package.sigstore.json'])
def test_local_bytes_modified_after_attestation_or_metadata_malformed_fail_closed(publication, name):
    if name == 'archive': name = publication[2]['tag'].replace('-v', '-') + '.tar.gz'
    path = publication[1] / name
    path.write_bytes(b'{"duplicate":1,"duplicate":2}' if name.endswith('.json') else b'changed')
    with pytest.raises(ValueError):
        verified(publication)


def test_provider_state_change_or_missing_final_bundle_does_not_generate_evidence(publication):
    publication[0].change_after_download = True
    with pytest.raises(ValueError):
        verified(publication)
    (publication[1] / 'package.sigstore.json').unlink()
    with pytest.raises(OSError):
        verified(publication)


def test_genuine_historical_signature_cannot_authenticate_new_version(package, release_tag):
    bundle = (ROOT / 'tests/fixtures/publication/package.sigstore.json').read_bytes()
    with pytest.raises(ValueError):
        Verifier().verify(package[0], bundle, profile='package', name=contract.filename(package[1]),
                          tag=release_tag, commit=package[1]['distribution']['provenance']['source_commit'])


def test_read_only_transport_cannot_mutate_or_accept_credentials():
    api = verify.ReadOnlyGithub()
    assert api.token is None
    for method in ['POST', 'PATCH', 'DELETE']:
        with pytest.raises(ValueError, match='read_only'):
            api.request(method, '/releases')


def test_workflow_retains_verified_bundle_without_new_publication_privilege():
    import yaml
    workflow = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text())
    job = workflow['jobs']['prepare']
    assert job['permissions'] == {'contents': 'read', 'id-token': 'write', 'attestations': 'write'}
    attestation = next(s for s in job['steps'] if s.get('id') == 'package_attestation')
    assert attestation['uses'] == 'actions/attest@508db95dd578ae2727ebd6217d5ba78e4fbda05d'
    retention = next(s for s in job['steps'] if '--retain-bundle' in s.get('run', ''))
    assert retention['env']['PACKAGE_BUNDLE_PATH'] == '${{ steps.package_attestation.outputs.bundle-path }}'
    assert '"$PACKAGE_BUNDLE_PATH"' in retention['run']
    assert all('create-github-app-token' not in s.get('uses', '') for s in job['steps'])


def test_retained_bundle_is_authenticated_before_writing_and_cannot_be_replaced(tmp_path, package, release_tag):
    manifest = release.prepare(release_tag, tmp_path / 'candidate')
    directory = tmp_path / 'candidate'
    commit = manifest['distribution']['provenance']['source_commit']
    raw = package[0]
    bundle = tmp_path / 'from-action.json'
    bundle.write_bytes(structural_bundle(raw, 'package', contract.filename(manifest), commit=commit, run=RUN))
    context = {'tag': release_tag, 'commit': commit, 'expected_digest': digest(raw), 'connector': 'proxmox',
               'version': manifest['version'], 'run_id': RUN, 'verifier': StructuralVerifier()}
    contract.retain_bundle(directory, bundle, **context)
    contract.retain_bundle(directory, bundle, **context)
    assert (directory / 'package.sigstore.json').read_bytes() == bundle.read_bytes()
    bundle.write_bytes(structural_bundle(raw, 'package', contract.filename(manifest), commit=commit, run=61))
    with pytest.raises(ValueError, match='build_invocation'):
        contract.retain_bundle(directory, bundle, **context)


def test_wrong_signer_profile_and_missing_bundle_reject_before_retention(tmp_path, package, release_tag):
    manifest = release.prepare(release_tag, tmp_path / 'candidate')
    commit = manifest['distribution']['provenance']['source_commit']
    bundle = tmp_path / 'from-action.json'
    context = {'tag': release_tag, 'commit': commit, 'expected_digest': digest(package[0]), 'connector': 'proxmox',
               'version': manifest['version'], 'run_id': RUN, 'verifier': StructuralVerifier()}
    for profile in ['pointer', 'catalogue', 'other']:
        bundle.write_bytes(structural_bundle(package[0], profile, contract.filename(manifest), commit=commit, run=RUN))
        with pytest.raises(ValueError):
            contract.retain_bundle(tmp_path / 'candidate', bundle, **context)
        assert not (tmp_path / 'candidate/package.sigstore.json').exists()


@pytest.fixture
def workflow_context(monkeypatch, release_tag):
    policy = json.loads((ROOT / 'catalogue/publication/policy.json').read_bytes())
    commit = 'a' * 40
    env = {'GITHUB_REPOSITORY': REPOSITORY, 'GITHUB_REPOSITORY_ID': '1414494920',
           'GITHUB_REPOSITORY_OWNER_ID': '93822871', 'GITHUB_EVENT_NAME': 'push',
           'GITHUB_RUN_ATTEMPT': '1', 'GITHUB_REF': 'refs/tags/' + release_tag,
           'GITHUB_WORKFLOW_REF': REPOSITORY + '/.github/workflows/release.yml@refs/tags/' + release_tag,
           'RUNNER_ENVIRONMENT': 'github-hosted', 'GITHUB_ACTOR_ID': str(policy['app_bot_user_id']),
           'GITHUB_ACTOR': policy['app_slug'] + '[bot]', 'GITHUB_TRIGGERING_ACTOR': policy['app_slug'] + '[bot]',
           'GITHUB_SHA': commit}
    def output(args, **kwargs):
        if args in [['git', 'rev-parse', 'HEAD'], ['git', 'rev-parse', 'refs/tags/' + release_tag + '^{commit}']]:
            return commit + '\n'
        assert args == ['git', 'status', '--porcelain=v1', '--untracked-files=all']
        return b''
    monkeypatch.setattr(subprocess, 'check_output', output)
    return env


def test_expected_first_attempt_app_tag_context_admitted(workflow_context, release_tag):
    assert release.workflow_context(workflow_context, release_tag) == 'a' * 40


@pytest.mark.parametrize('key,value', [('GITHUB_REPOSITORY_ID', '1'), ('GITHUB_REPOSITORY_OWNER_ID', '1'),
    ('GITHUB_REPOSITORY', 'other/atlas-connectors'), ('GITHUB_RUN_ATTEMPT', '2'), ('GITHUB_REF', 'refs/heads/main'),
    ('GITHUB_EVENT_NAME', 'workflow_dispatch'), ('RUNNER_ENVIRONMENT', 'self-hosted'),
    ('GITHUB_ACTOR_ID', '93822871'), ('GITHUB_TRIGGERING_ACTOR', 'benchristian88'),
    ('GITHUB_WORKFLOW_REF', REPOSITORY + '/.github/workflows/other.yml@refs/tags/' + TAG)])
def test_invalid_workflow_execution_context_rejected(workflow_context, key, value, release_tag):
    workflow_context[key] = value
    with pytest.raises(ValueError):
        release.workflow_context(workflow_context, release_tag)


def test_missing_untracked_source_file_fails_release_before_output(tmp_path, monkeypatch, release_tag):
    monkeypatch.setattr(release, 'clean_source', lambda commit: None)
    original = subprocess.check_output
    def output(args, **kwargs):
        if args[:3] == ['git', 'ls-files', '--error-unmatch']:
            raise subprocess.CalledProcessError(1, args)
        return original(args, **kwargs)
    monkeypatch.setattr(subprocess, 'check_output', output)
    with pytest.raises(subprocess.CalledProcessError):
        release.prepare(release_tag, tmp_path / 'out', commit='a' * 40)
    assert not (tmp_path / 'out').exists()


@pytest.mark.parametrize('change', ['created', 'creators', 'spdxid', 'files_analyzed'])
def test_sbom_supported_document_fields_are_validated(package, change):
    files = contract.inspect_archive(package[0])
    sbom = json.loads(files['sbom.spdx.json'])
    if change == 'created': sbom['creationInfo']['created'] = '2026-02-30T00:00:00Z'
    elif change == 'creators': sbom['creationInfo']['creators'] = []
    elif change == 'spdxid': sbom['packages'][0]['SPDXID'] = ''
    elif change == 'files_analyzed': sbom['packages'][1]['filesAnalyzed'] = True
    files['sbom.spdx.json'] = json.dumps(sbom).encode()
    with pytest.raises(ValueError, match='sbom'):
        validate_changed(files, package[1])


def test_build_attempt_is_rechecked_after_asset_download(publication):
    api = publication[0]
    original = api.request
    def request(method, path, **kwargs):
        raw = original(method, path, **kwargs)
        api.rows['/actions/runs/60']['run_attempt'] = 2
        return raw
    api.request = request
    with pytest.raises(ValueError, match='fresh_dispatch_run_required'):
        verified(publication)


def test_clean_isolated_package_exports_reproduce_current_local_bytes(tmp_path, monkeypatch, package):
    original = subprocess.check_output
    def output(args, **kwargs):
        assert args == ['git', 'rev-parse', 'HEAD']
        return original(args, cwd=ROOT, text=True)
    monkeypatch.setattr(subprocess, 'check_output', output)
    for name, timestamp in [('first', 1), ('second', 1800000000)]:
        directory = tmp_path / name
        shutil.copytree(ROOT / 'connectors', directory / 'connectors')
        shutil.copyfile(ROOT / 'LICENSE', directory / 'LICENSE')
        import os
        for path in directory.rglob('*'):
            if path.is_file(): os.utime(path, (timestamp, timestamp))
        monkeypatch.setattr(build_bundle, 'ROOT', directory)
        raw, _ = build_bundle.build(version=package[1]['version'])
        assert raw == package[0]
    # Isolated uncommitted exports; this does not claim committed/tagged source.
