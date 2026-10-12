# SPDX-License-Identifier: Apache-2.0
"""Build isolated test harness from the candidate, never a release artefact."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

from atlas_connector_sdk.contracts import validate_manifest
from build_bundle import build, ROOT


def build_fixture(output):
    payload, candidate = build(candidate=True)
    with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
        files = {member.name: archive.extractfile(member).read() for member in archive.getmembers()}
    manifest = json.loads(json.dumps(candidate))
    manifest['id'] = 'i4b-fixture'
    manifest['version'] = '1.0.0'
    manifest['display'].update(name='I4B deterministic test harness',description='Test-only transport; no live Proxmox qualification.')
    manifest['source_versions'].update(qualification='qualified',qualified_versions=['fixture-only'])
    manifest['connection_fields'].append({'key':'fixture_scenario','label':'Fixture scenario','type':'text','required':False,'secret':False})
    source = (ROOT / 'tests/proxmox_fixture_transport.py').read_text()
    for name in ['clustered.json','scenarios.json']:
        source = source.replace("(FIXTURES / '" + name + "').read_text()", repr((ROOT / 'tests/fixtures/proxmox' / name).read_text()))
    source += '''\n\ndef fixture_adapter(config, deadline):
    scenario = config.get('fixture_scenario', 'complete')
    if scenario == 'malformed_aip':
        from ansible.module_utils import atlas_discovery
        original = atlas_discovery.stream
        def corrupt(*args):
            messages = original(*args)
            messages[0]['customer_id'] = 'forbidden'
            return messages
        atlas_discovery.stream = corrupt
    return adapter_factory(fixture(scenario))(config, deadline)
'''
    files['module_utils/atlas_fixture_transport.py'] = source.encode()
    files['library/atlas_readiness.py'] = (files['library/atlas_readiness.py'].decode().replace(
        "if __name__ == '__main__':\n    main()",
        "from ansible.module_utils.atlas_fixture_transport import fixture_adapter\nif __name__ == '__main__':\n    main(adapter_factory=fixture_adapter)")).encode()
    files['library/atlas_discover.py'] = b'''# SPDX-License-Identifier: Apache-2.0
# TEST ONLY: production does not include a fixture adapter or scenario input.
from ansible.module_utils.atlas_discovery import main
from ansible.module_utils.atlas_fixture_transport import fixture_adapter
if __name__ == '__main__':
    main(adapter_factory=fixture_adapter)
'''
    files['manifest.json'] = json.dumps({key:value for key,value in manifest.items() if key != 'distribution'},indent=2).encode() + b'\n'
    sbom = json.loads(files['sbom.spdx.json'])
    sbom['name'] = 'i4b-fixture-test-only'
    sbom['packages'][0].update(name='i4b-fixture',versionInfo='1.0.0')
    files['sbom.spdx.json'] = json.dumps(sbom,indent=2).encode() + b'\n'
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw,mode='w',format=tarfile.USTAR_FORMAT) as archive:
        for name,data in sorted(files.items()):
            info=tarfile.TarInfo(name); info.size=len(data); info.mode=0o644; info.mtime=0
            archive.addfile(info,io.BytesIO(data))
    result=gzip.compress(raw.getvalue(),mtime=0)
    manifest['distribution']['bundle_digest']='sha256:'+hashlib.sha256(result).hexdigest()
    validate_manifest(manifest)
    output.mkdir(parents=True,exist_ok=True)
    (output/'bundle.tar.gz').write_bytes(result)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (output/'candidate-manifest.json').write_text(json.dumps(candidate,indent=2)+'\n')
    return result,manifest


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    build_fixture(args.output)
