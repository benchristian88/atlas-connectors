# SPDX-License-Identifier: Apache-2.0
"""Generate an INACTIVE successor workflow for separate pin/authority review.

Never writes .github/workflows or updates existing authority settings. The same
reviewed immutable successor S must contain the isolated signer and driver.
"""
import argparse
from pathlib import Path
import re
from publication_contract import require, digest

ROOT = Path(__file__).resolve().parents[1]
OLD_PIN = '2dd1ffcd2f5677dc35bdbc8f68ea28275c91c285'
TEMPLATES = {
    'catalogue-publish-s4.yml': '52fbc2775d3e718fdc4e1b8ebf1e97fe44767c3214c649d3a11578b01d189bee',
    'catalogue-build-s4.yml': '111387fd0c74d3b9e123c8555e9e514312031504749338080f3a2b316f884aa1',
}


def template(name):
    # Historical inputs stay stable when a later separately approved caller is
    # adopted. They are never Actions entry points or new implementation pins.
    raw = (ROOT / 'tools/templates' / name).read_bytes()
    require(digest(raw) == TEMPLATES[name], 'workflow_template_changed')
    return raw.decode('utf-8')


def prepare(revision):
    require(type(revision) is str and re.fullmatch('[a-f0-9]{40}', revision)
            and revision != OLD_PIN, 'successor_revision_required')
    raw = template('catalogue-publish-s4.yml')
    require(OLD_PIN in raw and 'tools/publish_catalogue.py' in raw, 'workflow_template_changed')
    raw = raw.replace(OLD_PIN, revision).replace('tools/publish_catalogue.py', 'tools/catalogue_evidence_driver.py')
    raw = raw.replace('options: [publish, recover, bootstrap]', 'options: [publish]')
    raw = raw.replace('Publish, recover, or explicitly bootstrap the historical root', 'Publish a seven-asset immutable successor')
    # Actions string equality ignores case. The JSON parse additionally rejects
    # TRUE/True; the string comparison rejects whitespace, numbers and null.
    # An invalid parse fails job admission, never falling back to an enabled gate.
    raw = raw.replace("!inputs.acceptance_only && github.repository",
        "!inputs.acceptance_only && vars.CATALOGUE_EVIDENCE_ENABLED == 'true' && "
        "fromJSON(vars.CATALOGUE_EVIDENCE_ENABLED) == true && github.repository")
    raw = raw.replace("github.run_attempt == 1", "github.run_attempt == 1 && inputs.operation == 'publish'")
    raw = raw.replace('      PUBLICATION_OPERATION:', "      ATLAS_CATALOGUE_EVIDENCE_ENABLED: ${{ vars.CATALOGUE_EVIDENCE_ENABLED }}\n      PUBLICATION_OPERATION:")
    # Remove unsupported phases and their temporary elevated token input from the
    # generated candidate. Historical bootstrap remains covered by the template.
    parts = raw.split('      - ')
    raw = parts[0] + ''.join('      - ' + part for part in parts[1:]
        if "if: inputs.operation == 'bootstrap'" not in part and "if: inputs.operation == 'recover'" not in part)
    raw = raw.replace(" || steps.bootstrap_stage.outputs.needs_attestation == 'true'", '')
    raw = raw.replace("          permission-workflows: ${{ inputs.operation == 'bootstrap' && 'write' || '' }}\n", '')
    raw = raw.replace('          # This pinned action omits empty inputs; baseline permissions stay explicit.\n', '')
    raw = raw.replace("          with open(os.environ['GITHUB_OUTPUT'], 'a') as stream:\n"
                      "              stream.write('bootstrap_mode=' + policy.get('bootstrap_operation', 'disabled') + '\\n')\n", '')
    # The driver independently denies bootstrap/recovery even for hostile inputs.
    return '# INACTIVE REVIEW OUTPUT: requires separate authority/pin approvals.\n' + raw


def prepare_build():
    raw = template('catalogue-build-s4.yml')
    require('python tools/build_catalogue.py' in raw, 'workflow_template_changed')
    return '# INACTIVE REVIEW OUTPUT: candidate build provenance only.\n' + raw.replace(
        'python tools/build_catalogue.py', 'python tools/build_catalogue_candidate.py')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--kind', choices=('publisher', 'catalogue-build'), default='publisher')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        require(args.output.resolve().parent != (ROOT / '.github/workflows').resolve(), 'inactive_output_required')
        raw = prepare(args.revision) if args.kind == 'publisher' else prepare_build()
        with args.output.open('x') as stream:
            stream.write(raw)
    except (ValueError, OSError):
        parser.exit(1, 'workflow_preparation_rejected\n')


if __name__ == '__main__':
    main()
