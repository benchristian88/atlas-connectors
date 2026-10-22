# SPDX-License-Identifier: Apache-2.0
"""Workflow isolation contracts; not a substitute for a genuine platform run."""
from pathlib import Path
import re
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]


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
    assert attest["with"]["predicate-type"] == "https://atlas-impact.dev/attestations/publication-authorization/v1"
    assert "subject-path" in attest["with"] and "subject-digest" not in attest["with"]
    upload = next(s for s in steps if s.get("id") == "upload")
    assert upload["with"]["path"].splitlines() == [
        "${{ runner.temp }}/publication-authorization/authorization.json",
        "${{ runner.temp }}/publication-authorization/authorization.sigstore.json"]
    assert "always()" not in upload.get("if", "")
    assert "token" not in str(job["outputs"])


def test_existing_publisher_has_no_new_authorization_integration_or_verifier_secret():
    publisher = (ROOT / ".github/workflows/catalogue-publish.yml").read_text()
    assert "catalogue-verifier" not in publisher and "VERIFICATION_APP" not in publisher
    for filename in ("publish_catalogue.py", "bootstrap_catalogue.py"):
        source = (ROOT / "tools" / filename).read_text()
        assert "publication_authorization" not in source and "verification_github" not in source


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
