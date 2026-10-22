# SPDX-License-Identifier: Apache-2.0
"""Isolated run-level preflight issuer. No draft observation or publication writes."""
import base64
import os
from pathlib import Path
import sys
import time

from atlas_connector_sdk.contracts import strict_json
from publication_authorization import (AUTHORITY, EXPECTED, MAX_REQUEST_BYTES, SCHEMA,
    WORKFLOW, check_authorization, check_trust, dispatch_context, fields, workflow_identity)
from publication_contract import (OWNER_ID, PUBLICATION_WORKFLOW, REPOSITORY,
    canonical_json, check_repository, digest, positive_integer, require)
from ruleset_visibility import app_jwt
from verification_github import (BASE, INSTALLATION, LIST, PERMISSIONS, VerificationGithub, credential)


def check_context(environ, operation, trust, *, acceptance_only=False):
    check_trust(trust, acceptance_only=acceptance_only)
    request = dispatch_context(environ, operation, acceptance_only=acceptance_only)
    require(environ.get("VERIFIER_REVISION") == trust["signer_revision"]
        and workflow_identity(environ.get("VERIFIER_WORKFLOW_REF"), REPOSITORY + "/" + WORKFLOW)
        and environ.get("DISPATCH_OPERATION") == operation
        and environ.get("DISPATCH_ACCEPTANCE_ONLY") == str(acceptance_only).lower(), "verification_context")
    return request


def authenticate(api, environ):
    require(environ.get("VERIFICATION_APP_ID") == "5424851"
            and environ.get("VERIFICATION_APP_INSTALLATION_ID") == "174088125", "verification_configuration")
    # Remove the step-scoped key before invoking OpenSSL; never persist it outside
    # app_jwt's mode-0600 temporary file or transmit it to any later step.
    key = environ.pop("VERIFICATION_APP_PRIVATE_KEY", None)
    require(isinstance(key, str) and bool(key), "verification_configuration")
    jwt = app_jwt(key)
    app = api.get("/app", jwt)
    require(isinstance(app, dict) and type(app.get("id")) is int and app["id"] == 5424851
            and app.get("owner", {}).get("id") == OWNER_ID
            and app.get("owner", {}).get("login") == "benchristian88"
            and app.get("permissions") == PERMISSIONS, "verification_app")
    installation = api.get(INSTALLATION, jwt)
    require(type(installation.get("id")) is int and installation["id"] == 174088125
            and type(installation.get("app_id")) is int and installation["app_id"] == 5424851
            and installation.get("account", {}).get("id") == OWNER_ID
            and installation.get("account", {}).get("login") == "benchristian88"
            and installation.get("repository_selection") == "selected"
            and installation.get("permissions") == PERMISSIONS
            and "suspended_at" in installation and installation["suspended_at"] is None,
            "verification_installation")
    issued = api.mint(jwt)
    require(issued.get("permissions") == PERMISSIONS, "verification_permissions")
    token = credential(issued.get("token"))
    scope = api.get("/installation/repositories?per_page=2&page=1", token)
    require(type(scope.get("total_count")) is int and scope["total_count"] == 1
            and isinstance(scope.get("repositories"), list) and len(scope["repositories"]) == 1,
            "verification_repository_scope")
    check_repository(scope["repositories"][0])
    return token


def content_bytes(value, path):
    require(isinstance(value, dict) and value.get("type") == "file" and value.get("path") == path
            and value.get("encoding") == "base64" and positive_integer(value.get("size"))
            and value["size"] <= MAX_REQUEST_BYTES, "verification_source_file")
    raw = base64.b64decode(value["content"].replace("\n", ""), validate=True)
    require(len(raw) == value["size"], "verification_source_file")
    return raw


def observe_authority(api, token, request):
    def get(path):
        return api.get(BASE + path, token)
    source, run_id = request["source_commit"], request["run_id"]
    policy_raw = content_bytes(get("/contents/catalogue/publication/policy.json?ref=" + source),
                               "catalogue/publication/policy.json")
    request["policy_sha256"] = digest(policy_raw)
    policy = strict_json(policy_raw.decode("utf-8"), maximum=MAX_REQUEST_BYTES)
    run = get(f"/actions/runs/{run_id}")
    require(isinstance(run, dict) and positive_integer(run.get("workflow_id")), "verification_run")
    security = {"repository": get(""), "branch": get("/branches/main"),
        "environment": get("/environments/catalogue-publication"), "run": run,
        "attempt": get(f"/actions/runs/{run_id}/attempts/1"),
        "workflow": get(f"/actions/workflows/{run['workflow_id']}"),
        "user": api.get("/users/benchristian88", token),
        "checks": get(f"/commits/{source}/check-runs?check_name=validate&filter=latest&per_page=2&page=1"),
        "publisher_app": api.get("/apps/atlas-catalogue-publisher", token),
        "verification_environment": get("/environments/catalogue-verification"),
        "immutable_releases": get("/immutable-releases")}
    return policy, security


def issue(api, environ, operation, trust, *, acceptance_only=False, clock=time.time):
    request = check_context(environ, operation, trust, acceptance_only=acceptance_only)  # Before credentials/network.
    started = int(clock())
    token = authenticate(api, environ)
    policy, security = observe_authority(api, token, request)
    from ruleset_visibility import validate_list
    require(validate_list(api.get(LIST, token)) == trust["ruleset_ids"], "verification_ruleset_ids")
    observations = [api.get(BASE + f"/rulesets/{trust['ruleset_ids'][name]}?includes_parents=true", token)
                    for name in sorted(EXPECTED)]
    completed = int(clock())
    value = {"schema": SCHEMA, "authority": AUTHORITY,
        "source": {"commit": request["source_commit"], "policy_sha256": request["policy_sha256"],
                   "verifier_revision": trust["signer_revision"], "signer_workflow": WORKFLOW},
        "execution": {"workflow": PUBLICATION_WORKFLOW,
            **{k: request[k] for k in ("run_id", "run_attempt", "operation", "acceptance_only")}},
        "rulesets": {"ids": trust["ruleset_ids"], "observations": observations,
            "sha256": digest(canonical_json(observations)), "approved_bypass_actors": EXPECTED},
        "security": security, "freshness": {"observation_started": started,
            "observation_completed": completed, "issued_at": completed,
            "expires_at": started + trust["max_observation_age_seconds"]}}
    check_authorization(value, trust, policy)
    raw = canonical_json(value)
    require(len(raw) <= 256 * 1024, "authorization_size")
    return raw


def main():
    try:
        inputs = strict_json(os.environ["AUTHORIZATION_REQUEST"], maximum=MAX_REQUEST_BYTES)
        fields(inputs, {"operation", "acceptance_only"})
        trust = strict_json(os.environ["VERIFICATION_POLICY"], maximum=MAX_REQUEST_BYTES)
        raw = issue(VerificationGithub(), os.environ, inputs["operation"], trust,
                    acceptance_only=inputs["acceptance_only"])
        destination = Path(os.environ["RUNNER_TEMP"]) / "publication-authorization"
        destination.mkdir(mode=0o700)
        (destination / "preflight.json").write_bytes(raw)
        (destination / "predicate.json").write_bytes(canonical_json({
            "schema": "atlas-publication-preflight-predicate/v2", "preflight_sha256": digest(raw)}))
    except Exception:
        print("publication_preflight_failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
