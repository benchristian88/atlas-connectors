# SPDX-License-Identifier: Apache-2.0
"""Isolated issuer. No publication writes, caller code execution or artifact input."""
import base64
import os
from pathlib import Path
import sys
import time

from atlas_connector_sdk.contracts import strict_json
from publication_authorization import (AUTHORITY, EXPECTED, MAX_REQUEST_BYTES, SCHEMA,
    WORKFLOW, check_authorization, check_observations, check_publication_policy,
    check_request, check_trust, parse)
from publication_contract import (APP_PERMISSIONS, ENVIRONMENT, OWNER_ID, PUBLICATION_WORKFLOW,
    REPOSITORY, PublicationError, canonical_json, check_authority, check_repository, digest, hexadecimal,
    parse_pointer, positive_integer, require, snapshot_tag)
from ruleset_visibility import app_jwt
from verification_github import (BASE, INSTALLATION, LIST, PERMISSIONS, VerificationGithub, credential)


def check_context(environ, request, trust):
    check_trust(trust)
    check_request(request)
    require(request["transition"] != "stage-create-draft", "draft_visibility_unproven")
    expected = {"GITHUB_REPOSITORY": REPOSITORY, "GITHUB_REPOSITORY_ID": "1414494920",
        "GITHUB_REPOSITORY_OWNER_ID": str(OWNER_ID), "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REF": "refs/heads/main", "GITHUB_SHA": request["source_commit"],
        "GITHUB_RUN_ID": str(request["run_id"]), "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_WORKFLOW_REF": REPOSITORY + "/" + PUBLICATION_WORKFLOW + "@refs/heads/main",
        "RUNNER_ENVIRONMENT": "github-hosted", "VERIFIER_REVISION": trust["signer_revision"],
        "VERIFIER_WORKFLOW_REF": REPOSITORY + "/" + WORKFLOW + "@" + trust["signer_revision"],
        "DISPATCH_OPERATION": request["operation"]}
    require(all(environ.get(key) == value for key, value in expected.items()), "verification_context")


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


def observe_authority(api, token, request, trust):
    def get(path):
        return api.get(BASE + path, token)

    source, run_id = request["source_commit"], request["run_id"]
    policy_raw = content_bytes(get("/contents/catalogue/publication/policy.json?ref=" + source),
                               "catalogue/publication/policy.json")
    require(digest(policy_raw) == request["policy_sha256"], "verification_policy_digest")
    policy = strict_json(policy_raw.decode("utf-8"), maximum=MAX_REQUEST_BYTES)
    check_publication_policy(policy, request["operation"])
    if request["operation"] == "bootstrap":
        mode = "activate" if request["transition"].startswith("activate-") else "stage"
        require(policy.get("bootstrap_operation") == mode, "verification_bootstrap_mode")
    run = get(f"/actions/runs/{run_id}")
    require(positive_integer(run.get("workflow_id")), "verification_run")
    check_authority(policy, get(""), get("/branches/main"), get("/environments/" + ENVIRONMENT), run,
        get(f"/actions/runs/{run_id}/attempts/1"), get(f"/actions/workflows/{run['workflow_id']}"),
        api.get("/users/benchristian88", token),
        get(f"/commits/{source}/check-runs?check_name=validate&filter=latest&per_page=2&page=1"),
        run_id=run_id, source_commit=source, operation=request["operation"])
    # A SHA-pinned reusable call must appear in GitHub's own run observation.
    referenced = run.get("referenced_workflows")
    expected_ref = REPOSITORY + "/" + WORKFLOW + "@" + trust["signer_revision"]
    require(isinstance(referenced, list) and len(referenced) == 1
            and referenced[0].get("path") == expected_ref
            and referenced[0].get("sha") == trust["signer_revision"], "verification_reusable_workflow")
    app = api.get("/apps/atlas-catalogue-publisher", token)
    require(type(app.get("id")) is int and app["id"] == 5422372
            and app.get("slug") == policy["app_slug"] == "atlas-catalogue-publisher"
            and app.get("owner", {}).get("id") == OWNER_ID
            and app.get("permissions") == APP_PERMISSIONS, "verification_publisher_app")
    environment = get("/environments/catalogue-verification")
    require(type(environment.get("id")) is int and environment["id"] == trust["verification_environment_id"]
            and environment.get("name") == "catalogue-verification"
            and environment.get("can_admins_bypass") is False
            and environment.get("deployment_branch_policy") ==
                {"protected_branches": True, "custom_branch_policies": False}
            and isinstance(environment.get("protection_rules"), list)
            and not any(row.get("type") == "required_reviewers" for row in environment["protection_rules"]),
            "verification_environment")
    require(get("/immutable-releases").get("enabled") is True, "verification_immutable_releases")
    return policy


def observe_target(api, token, request):
    """Check provider identities; V2 must ALSO verify all P1/P2 artifact semantics."""
    # Contents Read cannot establish draft absence. No caller claim or trust toggle
    # enables this transition; it needs a separately reviewed V2 evidence design.
    require(request["transition"] != "stage-create-draft", "draft_visibility_unproven")
    def get(path, **kwargs):
        return api.get(BASE + path, token, **kwargs)

    target, transition = request["target"], request["transition"]
    prior = target["expected_prior"]
    current = get("/git/ref/heads/catalogue-current", missing=True)
    if request["operation"] == "bootstrap":
        require(current is None, "verification_current_exists")
        marker = get("/git/ref/tags/catalogue-bootstrap-root", missing=True)
        if transition == "activate-create-current":
            require(isinstance(marker, dict) and marker.get("ref") == "refs/tags/catalogue-bootstrap-root"
                    and marker.get("object") == {"type": "commit", "sha": prior["marker_sha"],
                        "url": "https://api.github.com" + BASE + "/git/commits/" + prior["marker_sha"]},
                    "verification_marker")
        else:
            require(marker is None, "verification_marker_exists")
    else:
        require(isinstance(current, dict) and current.get("ref") == "refs/heads/catalogue-current"
                and current.get("object", {}).get("type") == "commit"
                and current["object"].get("sha") == prior["channel_sha"], "verification_prior_channel")
        raw = content_bytes(get("/contents/current.json?ref=" + prior["channel_sha"]), "current.json")
        pointer = parse_pointer(raw)
        require(digest(raw) == prior["pointer_sha256"]
                and all(pointer[key] == prior[key] for key in ("sequence", "release_id"))
                and pointer["asset_id"] == prior["catalogue_asset_id"]
                and pointer["sha256"] == prior["catalogue_sha256"], "verification_prior_pointer")
    tag = snapshot_tag(target["sequence"])
    release = get(f"/releases/{target['release_id']}")
    immutable = transition.endswith("current") or transition == "activate-create-marker"
    require(type(release.get("id")) is int and release["id"] == target["release_id"]
            and release.get("tag_name") == tag and release.get("prerelease") is False
            and release.get("target_commitish") == target["snapshot_source_commit"]
            and release.get("draft") is (not immutable)
            and (not immutable or release.get("immutable") is True), "verification_release_state")
    rows = get(f"/releases/{target['release_id']}/assets?per_page=5&page=1")
    require(isinstance(rows, list) and len(rows) <= 4, "verification_asset_inventory")
    assets = {}
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get("name"), str) and row["name"] not in assets
                and positive_integer(row.get("id")) and row.get("state") == "uploaded"
                and positive_integer(row.get("size")), "verification_asset_inventory")
        provider_digest = row.get("digest")
        require(isinstance(provider_digest, str) and provider_digest.startswith("sha256:")
                and hexadecimal(provider_digest[7:]), "verification_asset_digest")
        assets[row["name"]] = {"id": row["id"], "sha256": provider_digest[7:]}
    require(len({row["id"] for row in assets.values()}) == len(assets), "verification_asset_inventory")
    if "assets" in target:
        require(assets == target["assets"], "verification_asset_identity")
    else:
        require(target["artifact_name"] not in assets, "verification_asset_exists")
        allowed = set()
        if target["artifact_name"] == "catalogue.sigstore.json" or transition == "seal-upload-selection":
            require(assets.get(tag + ".json") == {"id": target["catalogue_asset_id"],
                                                  "sha256": target["catalogue_sha256"]},
                    "verification_catalogue_asset")
            allowed.add(tag + ".json")
        if transition == "seal-upload-selection":
            require(assets.get("catalogue.sigstore.json") == {"id": target["catalogue_bundle_asset_id"],
                                                             "sha256": target["catalogue_bundle_sha256"]},
                    "verification_catalogue_bundle")
            allowed.add("catalogue.sigstore.json")
            if target["artifact_name"] == "current.sigstore.json":
                require(assets.get("current.json") == {"id": target["pointer_asset_id"],
                                                        "sha256": target["pointer_sha256"]},
                        "verification_pointer_asset")
                allowed.add("current.json")
        require(assets.keys() == allowed, "verification_asset_inventory")
    if "next_channel_sha" in target:
        commit = get("/git/commits/" + target["next_channel_sha"])
        require(commit.get("sha") == target["next_channel_sha"] and isinstance(commit.get("parents"), list),
                "verification_next_commit")
        parents = commit["parents"]
        require(parents == [] if request["operation"] == "bootstrap" else
                len(parents) == 1 and parents[0].get("sha") == prior["channel_sha"], "verification_next_parent")


def issue(api, environ, request, trust, *, clock=time.time):
    check_context(environ, request, trust)  # Before credentials or any network operation.
    started = int(clock())  # Earliest observation includes App authentication/scope.
    token = authenticate(api, environ)
    policy = observe_authority(api, token, request, trust)
    listed = api.get(LIST, token)
    from ruleset_visibility import validate_list
    require(validate_list(listed) == trust["ruleset_ids"], "verification_ruleset_ids")
    observations = [api.get(BASE + f"/rulesets/{trust['ruleset_ids'][name]}?includes_parents=true", token)
                    for name in sorted(EXPECTED)]
    check_observations(observations, policy, request["operation"], trust["ruleset_ids"])
    observe_target(api, token, request)
    completed = int(clock())
    value = {"schema": SCHEMA, "authority": AUTHORITY,
        "source": {"commit": request["source_commit"], "policy_sha256": request["policy_sha256"],
                   "verifier_revision": trust["signer_revision"], "signer_workflow": WORKFLOW},
        "execution": {"workflow": PUBLICATION_WORKFLOW, **{key: request[key] for key in
            ("run_id", "run_attempt", "operation", "transition", "challenge")}},
        "rulesets": {"ids": trust["ruleset_ids"], "observations": observations,
                     "sha256": digest(canonical_json(observations)), "approved_bypass_actors": EXPECTED},
        "target": request["target"], "freshness": {"observation_started": started,
            "observation_completed": completed, "issued_at": completed,
            "expires_at": started + trust["max_observation_age_seconds"]}}
    check_authorization(value, trust, policy)
    return canonical_json(value)


def main():
    try:
        request = check_request(parse(os.environ["AUTHORIZATION_REQUEST"].encode("utf-8"), MAX_REQUEST_BYTES))
        trust = strict_json(os.environ["VERIFICATION_POLICY"], maximum=MAX_REQUEST_BYTES)
        raw = issue(VerificationGithub(), os.environ, request, trust)
        destination = Path(os.environ["RUNNER_TEMP"]) / "publication-authorization"
        destination.mkdir(mode=0o700)
        (destination / "authorization.json").write_bytes(raw)
        (destination / "predicate.json").write_bytes(canonical_json({
            "schema": "atlas-publication-decision/v1", "authorization_sha256": digest(raw)}))
    except Exception as error:
        code = "publication_verification_failed"
        if isinstance(error, PublicationError) and error.args == ("draft_visibility_unproven",):
            code = "draft_visibility_unproven"
        print(code, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
