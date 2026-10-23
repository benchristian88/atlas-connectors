# SPDX-License-Identifier: Apache-2.0
"""Retired workflow bytes remain test data outside the active Actions directory."""
import hashlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / ".github/workflows"
HISTORICAL = ROOT / "tests/fixtures/historical_workflows"
PRODUCTION = {
    "catalogue-publish.yml", "catalogue-verifier.yml", "catalogue.yml",
    "release.yml", "ci.yml",
}
# Original bytes at source branch HEAD 632f5e5f9f297549b1d54c5b6fc1a5c8a086b38d.
HISTORICAL_SHA256 = {
    "diagnose-catalogue-publisher.yml": "c25b73fdd9a8bb1e9b09bd6ae598ae5d68e3270717235c9dbe9a8667a4aee29a",
    "ruleset-visibility-experiment.yml": "c84d8de6f689a6c66dbf801d8d8e1b40510e6b73935596721437f9bd641ee5dc",
    "verifier-signer-experiment.yml": "435c08512450e3c7ca0dac1454fd0bd8cd3803bb9a21ce89b7b247678eea4dab",
    "verifier-signer-probe.yml": "eb857b04baa61f4c1ba082ac2a8a614a2a1bceb4886b946d728bd815c24fdd05",
}


def test_exactly_five_production_workflows_are_active():
    assert {path.name for path in ACTIVE.iterdir()} == PRODUCTION


@pytest.mark.parametrize("filename", HISTORICAL_SHA256)
def test_historical_workflow_is_archived_with_original_bytes(filename):
    assert not (ACTIVE / filename).exists()
    archived = HISTORICAL / filename
    assert archived.is_file() and not archived.is_symlink()
    assert hashlib.sha256(archived.read_bytes()).hexdigest() == HISTORICAL_SHA256[filename]


@pytest.mark.parametrize("filename", sorted(PRODUCTION))
def test_production_workflow_does_not_invoke_archived_experiments(filename):
    source = (ACTIVE / filename).read_text()
    assert "tests/fixtures/historical_workflows" not in source
    assert not any(name in source for name in HISTORICAL_SHA256)
