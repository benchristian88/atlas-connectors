# SPDX-License-Identifier: Apache-2.0
import importlib.util
import json
from pathlib import Path
import sys

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_bundle import build

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verify_candidate", ROOT / "tools/verify_candidate.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def test_exact_candidate_and_default_bytes_survive_unrelated_files(tmp_path, monkeypatch):
    import build_bundle
    import shutil
    staged = tmp_path / "source"
    shutil.copytree(ROOT / "connectors", staged / "connectors")
    shutil.copy(ROOT / "LICENSE", staged / "LICENSE")
    # Keep Git provenance in the real checkout while testing a staged tree.
    original = build_bundle.subprocess.check_output
    monkeypatch.setattr(build_bundle.subprocess, "check_output", lambda args, **kw: original(args, cwd=ROOT, text=True))
    monkeypatch.setattr(build_bundle, "ROOT", staged)
    candidate, _ = build(candidate=True)
    production, _ = build()
    (staged / "connectors/proxmox/docs/unreviewed.md").write_text("operator report\n")
    (staged / "connectors/proxmox/library/local_fixture.py").write_text("test transport\n")
    assert build(candidate=True)[0] == candidate
    assert build()[0] == production


def test_independent_candidate_verification_and_digest_failure(tmp_path):
    first, manifest = build(output=tmp_path, candidate=True)
    second, _ = build(candidate=True)
    assert first == second
    digest = manifest["distribution"]["bundle_digest"]
    assert verifier.verify(tmp_path, digest)["files"] == 18
    with pytest.raises(ValueError, match="candidate_digest_mismatch"):
        verifier.verify(tmp_path, "sha256:" + "0" * 64)
    detached = json.loads((tmp_path / "manifest.json").read_text())
    detached["source_versions"]["qualification"] = "qualified"
    detached["source_versions"]["qualified_versions"] = ["9.2.11"]
    (tmp_path / "manifest.json").write_text(json.dumps(detached))
    with pytest.raises(ValueError, match="candidate_manifest_mismatch"):
        verifier.verify(tmp_path, digest)
