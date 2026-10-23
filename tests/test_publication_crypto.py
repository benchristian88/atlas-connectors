# SPDX-License-Identifier: Apache-2.0
"""Genuine offline verification of frozen evidence, never fake pointer signatures."""
from pathlib import Path
import sys
import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from publication_verify import Verifier
from publication_contract import digest


def test_genuine_frozen_catalogue_and_wrong_profile_bytes_commit():
    verifier = Verifier()  # Mandatory in CI; provision pinned binary explicitly.
    raw = (ROOT / 'tests/fixtures/official_catalogue/catalogue-000001.json').read_bytes()
    bundle = (ROOT / 'tests/fixtures/publication/catalogue.sigstore.json').read_bytes()
    evidence = verifier.verify(raw, bundle, profile='catalogue', name='catalogue-000001.json')
    assert evidence.sha256 == digest(raw)
    assert evidence.source_commit == '91dfd86f18d0b59ff977bb1e8a5fef42c5329943'
    for artifact, context in [(raw+b' ', {'profile': 'catalogue', 'name': 'catalogue.json'}),
                              (raw, {'profile': 'pointer', 'name': 'current.json'}),
                              (raw, {'profile': 'catalogue', 'name': 'catalogue.json', 'commit': 'a'*40}),
                              (raw, {'profile': 'catalogue', 'name': 'wrong.json'})]:
        with pytest.raises(ValueError):
            verifier.verify(artifact, bundle, **context)


def test_genuine_package_evidence_cannot_authenticate_catalogue():
    verifier = Verifier()
    with pytest.raises(ValueError):
        verifier.verify((ROOT / 'tests/fixtures/official_catalogue/catalogue-000001.json').read_bytes(),
                        (ROOT / 'tests/fixtures/publication/package.sigstore.json').read_bytes(),
                        profile='catalogue', name='catalogue.json')


def test_genuine_original_package_bytes_and_build_profile():
    from build_bundle import build
    from publication_contract import parse_catalogue
    entry = parse_catalogue((ROOT / 'tests/fixtures/official_catalogue/catalogue-000001.json').read_bytes())['entries'][0]
    raw, _ = build()  # Deterministic original archive bytes; never execute/extract it.
    assert 'sha256:' + digest(raw) == entry['manifest']['distribution']['bundle_digest']
    bundle = (ROOT / 'tests/fixtures/publication/package.sigstore.json').read_bytes()
    evidence = Verifier().verify(raw, bundle, profile='package', name='proxmox-0.2.0.tar.gz',
        tag=entry['release_tag'], commit=entry['manifest']['distribution']['provenance']['source_commit'])
    assert evidence.profile == 'package'
    assert evidence.source_commit == '456a5bfdd1398c19da9ffef29216029027e24278'


def test_genuine_bootstrap_source_preflight_and_no_catalogue_as_selection():
    """Pinned gh really verifies the source; no genuine selection is claimed."""
    import json
    from bootstrap_catalogue import local_preflight, CATALOGUE_SHA256
    from publication_contract import pointer_bytes
    verifier = Verifier()
    policy = json.loads((ROOT / 'catalogue/publication/policy.json').read_bytes())
    assert policy['bootstrap_operation'] == 'disabled'
    # Historical activation fixture only; the closed production policy must not
    # be reopened just to run the offline source-verification regression.
    policy['bootstrap_operation'] = 'activate'
    result = local_preflight(policy, verifier)
    assert result['catalogue_bytes'] == 10585 and result['sha256'] == CATALOGUE_SHA256
    assert result['enabled'] is True and result['bootstrap_operation'] == 'activate'
    assert policy['bootstrap'] == {'sequence': 1,
        'pointer_sha256': 'a275f63d0ac818a193826478328ee324be62353addc5c97a2ed0a28d217b5372'}
    assert result['remote_checks_performed'] is False
    pointer = pointer_bytes({'schema_version': '1.0', 'sequence': 1, 'release_tag': 'catalogue-000001',
                            'release_id': 123, 'asset_id': 456, 'sha256': CATALOGUE_SHA256,
                            'previous_pointer_sha256': None})  # Test-only IDs, never approval.
    bundle = (ROOT / 'tests/fixtures/publication/catalogue.sigstore.json').read_bytes()
    for selection_bundle in [b'{}', bundle]:  # Unsigned or catalogue evidence cannot sign a pointer.
        with pytest.raises(ValueError):
            verifier.verify(pointer, selection_bundle, profile='pointer', name='current.json')
    tampered = json.loads(bundle)
    tampered['dsseEnvelope']['signatures'][0]['sig'] = 'AAAA'
    with pytest.raises(ValueError):
        verifier.verify((ROOT / 'tests/fixtures/official_catalogue/catalogue-000001.json').read_bytes(),
                        json.dumps(tampered).encode(), profile='catalogue', name='catalogue-000001.json')
