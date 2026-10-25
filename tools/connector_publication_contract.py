# SPDX-License-Identifier: Apache-2.0
"""Package-only admission contract. No catalogue publication authority is granted."""
from copy import deepcopy
import re

from atlas_connector_sdk.contracts import strict_json

from publication_authorization import (AUTHORITY, MAX_AUTHORIZATION_BYTES, MAX_REQUEST_BYTES,
    check_observations, fields, hash_value, integer, parse)
from publication_contract import (APP_PERMISSIONS, OWNER_ID, PUBLICATION_WORKFLOW as CATALOGUE_WORKFLOW,
    REPOSITORY, canonical_json, check_authority, check_policy, digest, require)
from ruleset_visibility import EXPECTED

WORKFLOW = ".github/workflows/connector-publish.yml"
SIGNER = ".github/workflows/connector-verifier.yml"
SCHEMA = "atlas-connector-package-preflight/v1"
TRUST_SCHEMA = "atlas-connector-package-trust/v1"
PREDICATE = "https://atlas-impact.dev/attestations/connector-package-preflight/v1"
PREDICATE_SCHEMA = "atlas-connector-package-preflight-predicate/v1"
SUBJECT = "connector-preflight.json"
TRUST_PATH = "catalogue/publication/connector-trust.json"
POLICY_PATH = "catalogue/publication/policy.json"
ARTIFACT_NAME = "immutable-connector-release-candidate"


def check_trust(trust, *, acceptance_only):
    fields(trust, {"schema", "enabled", "live_signer_accepted", "signer_revision", "ruleset_ids",
                   "verification_environment_id", "max_observation_age_seconds"})
    require(trust["schema"] == TRUST_SCHEMA and type(acceptance_only) is bool
        and type(trust["enabled"]) is bool and type(trust["live_signer_accepted"]) is bool,
        "connector_trust_profile")
    hash_value(trust["signer_revision"], 40)
    require(trust["signer_revision"] != "0" * 40, "connector_implementation_not_pinned")
    require(acceptance_only or trust["enabled"] and trust["live_signer_accepted"], "connector_publication_disabled")
    fields(trust["ruleset_ids"], EXPECTED)
    for value in trust["ruleset_ids"].values():
        integer(value)
    require(len(set(trust["ruleset_ids"].values())) == 5, "connector_ruleset_ids")
    integer(trust["verification_environment_id"])
    require(type(trust["max_observation_age_seconds"]) is int
        and 1 <= trust["max_observation_age_seconds"] <= 900, "connector_freshness_policy")


def check_policy_identity(policy):
    # Reuse the existing producer controls, including their approved identities;
    # the historical bootstrap pins confer no package or catalogue authority here.
    check_policy(policy)
    require({k: policy.get(k) for k in ("allowed_maintainer_id", "app_id", "app_installation_id",
        "app_bot_user_id", "app_slug", "environment_id", "package_environment_id")} == {
        "allowed_maintainer_id": 93822871, "app_id": 5422372, "app_installation_id": 174027755,
        "app_bot_user_id": 346232650, "app_slug": "atlas-catalogue-publisher",
        "environment_id": 24999137498, "package_environment_id": 24617213627}, "connector_policy_identity")


def inventory(value, *, complete=True):
    require(isinstance(value, dict) and (len(value) == 5 if complete else len(value) <= 5), "connector_inventory")
    for name, asset in value.items():
        require(type(name) is str and re.fullmatch(r"[a-zA-Z0-9._-]{1,128}", name), "connector_asset_name")
        fields(asset, {"id", "sha256", "bytes"})
        integer(asset["id"])
        integer(asset["bytes"])
        require(asset["bytes"] <= 20 * 1024 * 1024, "connector_asset_limit")
        hash_value(asset["sha256"])
    require(len({a["id"] for a in value.values()}) == len(value), "connector_duplicate_asset_id")
    return digest(canonical_json(value))


def check_input(value):
    fields(value, {"operation", "acceptance_only", "package"})
    operation, package = value["operation"], value["package"]
    require(operation in {"tag", "stage", "finalize"} and type(value["acceptance_only"]) is bool,
        "connector_operation")
    names = {"tag", "source_commit", "sha256"}
    if operation != "tag":
        names |= {"build_run_id", "artifact_id", "artifact_sha256"}
    if operation == "stage":
        names |= {"release_id", "assets"}
    if operation == "finalize":
        names |= {"release_id", "asset_id", "assets", "inventory_sha256", "staging_run_id"}
    fields(package, names)
    require(type(package["tag"]) is str and len(package["tag"]) <= 128
        and re.fullmatch(r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*-v[0-9]+\.[0-9]+\.[0-9]+", package["tag"]),
        "connector_tag")
    hash_value(package["source_commit"], 40)
    hash_value(package["sha256"])
    if operation != "tag":
        integer(package["build_run_id"])
        integer(package["artifact_id"])
        hash_value(package["artifact_sha256"])
    if operation == "stage":
        inventory(package["assets"], complete=False)
        if package["release_id"] is None:
            require(package["assets"] == {}, "connector_resume_approval")
        else:
            integer(package["release_id"])
    if operation == "finalize":
        for key in ("release_id", "asset_id", "staging_run_id"):
            integer(package[key])
        require(inventory(package["assets"]) == package["inventory_sha256"], "connector_inventory_digest")
    require(len(canonical_json(value)) <= MAX_REQUEST_BYTES, "connector_request_size")
    return value


def context(environ, inputs):
    check_input(inputs)
    expected = {"GITHUB_REPOSITORY": REPOSITORY, "GITHUB_REPOSITORY_ID": "1414494920",
        "GITHUB_REPOSITORY_OWNER_ID": "93822871", "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REF": "refs/heads/main", "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_WORKFLOW_REF": REPOSITORY + "/" + WORKFLOW + "@refs/heads/main",
        "GITHUB_ACTOR_ID": "93822871", "GITHUB_ACTOR": "benchristian88",
        "GITHUB_TRIGGERING_ACTOR": "benchristian88", "RUNNER_ENVIRONMENT": "github-hosted"}
    require(all(environ.get(k) == v for k, v in expected.items()), "connector_dispatch_context")
    caller, run = environ.get("GITHUB_SHA"), environ.get("GITHUB_RUN_ID", "")
    hash_value(caller, 40)
    require(type(run) is str and run.isascii() and run.isdigit() and str(int(run)) == run,
        "connector_dispatch_context")
    integer(int(run))
    if inputs["operation"] == "finalize":
        require(inputs["package"]["staging_run_id"] != int(run), "connector_separate_approval_required")
    return {"caller_sha": caller, "run_id": int(run), "run_attempt": 1,
        "request_sha256": digest(canonical_json(inputs)), "request": inputs}


def dispatch_authority(security, policy, expected, trust, *, historical=False):
    """Validate the package path first, then adapt only that path to shared rules.

    The frozen catalogue validator hardcodes its caller path. This adapter keeps
    all its actor, attempt, CI, environment and repository checks without granting
    a catalogue signature or accepting a catalogue run as a package dispatch.
    """
    actual = deepcopy(security)
    for key in ("run", "attempt"):
        row = actual[key]
        require(row.get("path") in {WORKFLOW, WORKFLOW + "@main", WORKFLOW + "@refs/heads/main"},
            "connector_caller_workflow")
        row["path"] = CATALOGUE_WORKFLOW
    require(actual["workflow"].get("path") == WORKFLOW, "connector_caller_workflow")
    actual["workflow"]["path"] = CATALOGUE_WORKFLOW
    check_authority(policy, *(actual[k] for k in
        ("repository", "branch", "environment", "run", "attempt", "workflow", "user", "checks")),
        run_id=expected["run_id"], source_commit=expected["caller_sha"], historical=historical)
    for key in ("run", "attempt"):
        require(security[key].get("referenced_workflows") == [{
            "path": REPOSITORY + "/" + SIGNER + "@" + trust["signer_revision"],
            "sha": trust["signer_revision"]}], "connector_reusable_workflow")
    app = security["publisher_app"]
    require(app.get("id") == 5422372 and app.get("slug") == "atlas-catalogue-publisher"
        and app.get("owner", {}).get("id") == OWNER_ID and app.get("permissions") == APP_PERMISSIONS,
        "connector_publisher_permissions")
    env = security["verification_environment"]
    require(type(env.get("id")) is int and env["id"] == trust["verification_environment_id"]
        and env.get("name") == "catalogue-verification" and env.get("can_admins_bypass") is False
        and env.get("deployment_branch_policy") == {"protected_branches": True, "custom_branch_policies": False}
        and isinstance(env.get("protection_rules"), list)
        and all(isinstance(r, dict) and r.get("type") != "required_reviewers" for r in env["protection_rules"]),
        "connector_verification_environment")
    require(security["immutable_releases"].get("enabled") is True, "connector_immutability_disabled")


def check_preflight(value, expected, trust, policy_raw):
    fields(value, {"schema", "authority", "context", "implementation_sha", "trust_sha256", "policy_sha256",
                   "security", "rulesets", "freshness"})
    require(value["schema"] == SCHEMA and canonical_json(value["authority"]) == canonical_json(AUTHORITY),
        "connector_preflight_profile")
    check_trust(trust, acceptance_only=expected["request"]["acceptance_only"])
    require(value["context"] == expected and value["implementation_sha"] == trust["signer_revision"]
        and value["trust_sha256"] == digest(canonical_json(trust))
        and value["policy_sha256"] == digest(policy_raw), "connector_preflight_binding")
    policy = strict_json(policy_raw, maximum=MAX_REQUEST_BYTES)
    check_policy_identity(policy)
    dispatch_authority(value["security"], policy, expected, trust)
    check_observations(value["rulesets"], policy, "publish", trust["ruleset_ids"])
    fresh = value["freshness"]
    fields(fresh, {"observation_started", "observation_completed", "issued_at", "expires_at"})
    for timestamp in fresh.values():
        integer(timestamp)
    start, end, issued, expires = (fresh[k] for k in
        ("observation_started", "observation_completed", "issued_at", "expires_at"))
    require(start <= end <= issued < expires <= start + trust["max_observation_age_seconds"],
        "connector_preflight_freshness")
