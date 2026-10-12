# SPDX-License-Identifier: Apache-2.0
"""Tests use the exact reviewed installed collection; production never installs it."""
import os
from pathlib import Path
import sys
import subprocess

import pytest

import ansible.module_utils

ROOT = Path(__file__).resolve().parents[1]
ansible.module_utils.__path__.append(str(ROOT / 'connectors/proxmox/module_utils'))
path = os.getenv('ATLAS_TEST_COLLECTIONS_PATH')
if path:
    os.environ['ANSIBLE_COLLECTIONS_PATH'] = path
    sys.path.insert(0, path)


@pytest.fixture(autouse=True)
def exported_source_context(monkeypatch):
    """Runtime images intentionally have no Git; use explicit test-only context.

    Bundle byte reproducibility is also tested in the real Git checkout. This
    exported-source metadata is never publisher attestation or a release build.
    """
    commit = os.getenv('ATLAS_TEST_SOURCE_COMMIT')
    if commit:
        import re
        assert re.fullmatch(r'[a-f0-9]{40}', commit)
        original = subprocess.check_output
        def output(args, **kwargs):
            if args == ['git', 'rev-parse', 'HEAD']:
                return commit + '\n'
            return original(args, **kwargs)
        monkeypatch.setattr(subprocess, 'check_output', output)
