# SPDX-License-Identifier: Apache-2.0
"""Workflow isolation contracts; not a substitute for a genuine platform run."""
from pathlib import Path
import json
import re
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def run_context_guard(tmp_path, changes=None, *, remove=None, accepted=True, acceptance_only=False):
    """Execute the actual pre-credential inline Python with synthetic context.

    This tests the local guard, not GitHub's runner/environment isolation.
    """
    from test_publication_authorization import REVISION, fixture
    trust = fixture()[3]
    trust["live_signer_accepted"] = accepted
    job = {"workflow_ref": "benchristian88/atlas-connectors/.github/workflows/catalogue-verifier.yml@refs/heads/main",
           "workflow_sha": REVISION, "workflow_repository": "benchristian88/atlas-connectors",
           "workflow_file_path": ".github/workflows/catalogue-verifier.yml"}
    job.update(changes or {})
    if remove:
        job.pop(remove)
    workflow = yaml.load((ROOT / ".github/workflows/catalogue-verifier.yml").read_text(), Loader=yaml.BaseLoader)
    steps = workflow["jobs"]["verify"]["steps"]
    assert steps[0]["id"] == "context" and "VERIFICATION_APP_PRIVATE_KEY" not in steps[0]["env"]
    assert not any("VERIFICATION_APP_PRIVATE_KEY" in step.get("env", {}) for step in steps[:2])
    program = steps[0]["run"].split("python3 - <<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
    output = tmp_path / "output"
    result = subprocess.run([sys.executable, "-c", program], cwd=tmp_path, capture_output=True, timeout=10,
        env={"JOB_CONTEXT": json.dumps(job), "VERIFICATION_POLICY": json.dumps(trust), "GITHUB_OUTPUT": str(output), "ACCEPTANCE_ONLY": str(acceptance_only).lower()})
    return result, output


def test_actual_guard_accepts_main_job_ref_and_independently_pinned_sha(tmp_path):
    from test_publication_authorization import REVISION, SOURCE
    assert REVISION != SOURCE
    result, output = run_context_guard(tmp_path)
    assert result.returncode == 0 and not result.stdout and not result.stderr
    assert output.read_text().splitlines() == ["revision=" + REVISION, "workflow_ref=benchristian88/atlas-connectors/.github/workflows/catalogue-verifier.yml@refs/heads/main"]


@pytest.mark.parametrize("changes", [
    {"workflow_ref": "benchristian88/atlas-connectors/.github/workflows/catalogue-verifier.yml@"},
    {"workflow_ref": "benchristian88/atlas-connectors/.github/workflows/verifier-signer-probe.yml@refs/heads/main"},
    {"workflow_sha": "a" * 40},  # Advancing caller/main does not update the trusted pin.
    {"workflow_sha": "B" * 40}, {"workflow_sha": None},
    {"workflow_repository": "another/repository"},
    {"workflow_file_path": ".github/workflows/verifier-signer-probe.yml"},
])
def test_actual_guard_rejects_wrong_identity_before_credentials_or_output(tmp_path, changes):
    result, output = run_context_guard(tmp_path, changes)
    assert result.returncode != 0 and result.stderr == b"verification_trust_not_accepted\n"
    assert not output.exists()


@pytest.mark.parametrize("field", ["workflow_ref", "workflow_sha", "workflow_repository", "workflow_file_path"])
def test_actual_guard_rejects_missing_job_fields(tmp_path, field):
    result, output = run_context_guard(tmp_path, remove=field)
    assert result.returncode != 0 and not output.exists()


def test_actual_guard_still_requires_live_acceptance(tmp_path):
    result, output = run_context_guard(tmp_path, accepted=False)
    assert result.returncode != 0 and not output.exists()


def test_verifier_is_reusable_only_isolated_and_uses_no_caller_code():
    workflow = yaml.load((ROOT / ".github/workflows/catalogue-verifier.yml").read_text(), Loader=yaml.BaseLoader)
    assert set(workflow["on"]) == {"workflow_call"}
    assert set(workflow["on"]["workflow_call"]["inputs"]) == {"request"}
    assert "secrets" not in workflow["on"]["workflow_call"]
    job = workflow["jobs"]["verify"]
    assert job["runs-on"] == "ubuntu-24.04" and job["environment"] == "catalogue-verification"
    assert job["permissions"] == {"contents": "read", "id-token": "write", "attestations": "write"}
    assert "1414494920" in job["if"] and "93822871" in job["if"]
    assert "catalogue-publish.yml@refs/heads/main" in job["if"]
    steps = job["steps"]
    assert "live_signer_accepted" in steps[0]["run"]
    checkout = next(s for s in steps if s.get("uses", "").startswith("actions/checkout@"))
    assert checkout["with"] == {"repository": "benchristian88/atlas-connectors",
                              "ref": "${{ steps.context.outputs.revision }}", "persist-credentials": "false"}
    for step in steps:
        if "uses" in step:
            assert re.fullmatch(r"actions/[a-z-]+@[a-f0-9]{40}", step["uses"])
        assert not any(word in step.get("uses", "") for word in ("cache", "download-artifact"))
        assert "${{ inputs." not in step.get("run", "")  # No shell interpolation of data.
    privileged = [s for s in steps if "VERIFICATION_APP_PRIVATE_KEY" in s.get("env", {})]
    assert len(privileged) == 1
    assert privileged[0]["run"] == "python3 tools/issue_publication_authorization.py"
    attest = next(s for s in steps if s.get("id") == "attest")
    assert attest["with"]["predicate-type"] == "https://atlas-impact.dev/attestations/publication-preflight/v2"
    assert "subject-path" in attest["with"] and "subject-digest" not in attest["with"]
    upload = next(s for s in steps if s.get("id") == "upload")
    assert upload["with"]["path"].splitlines() == [
        "${{ runner.temp }}/publication-authorization/preflight.json",
        "${{ runner.temp }}/publication-authorization/preflight.sigstore.json"]
    assert "always()" not in upload.get("if", "")
    assert "token" not in str(job["outputs"])


def test_publisher_depends_on_isolated_preflight_before_credentials_and_executes_pinned_code():
    caller = yaml.load((ROOT / ".github/workflows/catalogue-publish.yml").read_text(), Loader=yaml.BaseLoader)
    assert set(caller["jobs"]) == {"preflight", "publish"}
    signer, publisher = caller["jobs"]["preflight"], caller["jobs"]["publish"]
    match = re.fullmatch(r"benchristian88/atlas-connectors/\.github/workflows/catalogue-verifier\.yml@([a-f0-9]{40})", signer["uses"])
    assert match and signer["with"] == {"request": "${{ toJSON(inputs) }}"}
    assert match[1] == "d12d47111dec137e4a6af261879f1e49b8db05e2"
    trust = json.loads((ROOT / "catalogue/publication/verifier-trust.json").read_text())
    assert trust["signer_revision"] == match[1] and trust["live_signer_accepted"] is False
    workflow_source = (ROOT / ".github/workflows/catalogue-publish.yml").read_text()
    assert workflow_source.count(match[1]) == 3
    assert "da5562eeb21d5c1cc653cfea7ae8d025d2a9174a" not in workflow_source
    assert "secrets" not in signer and "environment" not in signer
    assert publisher["needs"] == "preflight" and "!inputs.acceptance_only" in publisher["if"]
    steps = publisher["steps"]
    implementation, source = steps[:2]
    assert implementation["with"]["ref"] == match[1] == publisher["env"]["ATLAS_IMPLEMENTATION_REVISION"]
    assert source["with"]["ref"] == "${{ github.sha }}" and source["with"]["path"] == "publication-source"
    verify = next(i for i, step in enumerate(steps) if step.get("run") == "python tools/publish_catalogue.py authorize")
    mint = next(i for i, step in enumerate(steps) if step.get("id") == "app")
    download = next(i for i, step in enumerate(steps) if "download-artifact@" in step.get("uses", ""))
    assert download < verify < mint
    assert steps[download]["with"]["artifact-ids"] == "${{ needs.preflight.outputs.artifact-id }}"
    assert "VERIFICATION_APP" not in (ROOT / ".github/workflows/catalogue-publish.yml").read_text()
    assert "PUBLICATION_APP_PRIVATE_KEY" not in (ROOT / ".github/workflows/catalogue-verifier.yml").read_text()
    for step in steps[:mint]:
        assert "secrets." not in str(step)
        assert "publication-source/tools" not in step.get("run", "")



def test_installed_dependencies_are_vendored_and_offline():
    source = (ROOT / ".github/workflows/catalogue-verifier.yml").read_text()
    assert "--no-index --no-deps --require-hashes --find-links vendor/sdk" in source
    assert "setup-python" not in source and "pip install -r requirements-dev" not in source


def test_issuer_imports_with_only_standard_library_and_vendored_sdk():
    wheel, = (ROOT / "vendor/sdk").glob("*.whl")
    result = subprocess.run([sys.executable, "-S", "-c",
        "import sys; sys.path[:0] = sys.argv[1:]; import issue_publication_authorization" ,
        str(ROOT / "tools"), str(wheel)], capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr.decode()


def test_unaccepted_signer_can_only_gather_explicit_acceptance_evidence(tmp_path):
    result, output = run_context_guard(tmp_path, accepted=False, acceptance_only=True)
    assert result.returncode == 0 and output.exists()
    # The Publisher's unconditional acceptance-only skip and signed mode binding
    # are asserted separately; this is not a production acceptance override.
