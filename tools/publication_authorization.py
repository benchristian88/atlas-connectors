# SPDX-License-Identifier: Apache-2.0
"""Versioned transition authorizations. Parsing/validation is not authentication.

No publication integration: callers must establish their own expected context and
provider state. A consumed challenge is only remembered within one verifier object.
"""
import time

from atlas_connector_sdk.contracts import strict_json
from publication_contract import (OWNER_ID, REPOSITORY_ID, PUBLICATION_WORKFLOW,
    canonical_json, check_policy, check_rulesets, digest, hexadecimal,
    positive_integer, require, snapshot_tag)
from ruleset_visibility import EXPECTED, validate_detail, validate_list

SCHEMA = "atlas-publication-authorization/v1"
WORKFLOW = ".github/workflows/catalogue-verifier.yml"
PREDICATE = "https://atlas-impact.dev/attestations/publication-authorization/v1"
SUBJECT = "authorization.json"
VERIFIER_APP_ID = 5424851
VERIFIER_INSTALLATION_ID = 174088125
PUBLISHER_APP_ID = 5422372
PUBLISHER_INSTALLATION_ID = 174027755
MAX_AUTHORIZATION_BYTES = 256 * 1024
MAX_REQUEST_BYTES = 16384
AUTHORITY = {"repository_id": REPOSITORY_ID, "owner_id": OWNER_ID,
             "maintainer_id": OWNER_ID, "publisher_app_id": PUBLISHER_APP_ID,
             "publisher_installation_id": PUBLISHER_INSTALLATION_ID,
             "verifier_app_id": VERIFIER_APP_ID,
             "verifier_installation_id": VERIFIER_INSTALLATION_ID}
# Exact fields: unknown GitHub-assigned IDs never appear in pre-creation grants.
TARGET_FIELDS = {
    "stage-create-draft": set(),
    "stage-upload-catalogue": {"release_id", "artifact_name", "artifact_sha256"},
    "seal-upload-selection": {"release_id", "catalogue_asset_id", "catalogue_bundle_asset_id",
                              "catalogue_bundle_sha256", "pointer_sha256",
                              "artifact_name", "artifact_sha256"},
    "finish-finalize-release": {"release_id", "assets", "pointer_sha256"},
    "activate-finalize-release": {"release_id", "assets", "pointer_sha256"},
    "finish-advance-current": {"release_id", "assets", "pointer_sha256", "next_channel_sha"},
    "recover-advance-current": {"release_id", "assets", "pointer_sha256", "next_channel_sha"},
    "activate-create-marker": {"release_id", "assets", "pointer_sha256", "next_channel_sha"},
    "activate-create-current": {"release_id", "assets", "pointer_sha256", "next_channel_sha"},
}
OPERATIONS = {
    "stage-create-draft": {"publish", "bootstrap"},
    "stage-upload-catalogue": {"publish", "bootstrap"},
    "seal-upload-selection": {"publish", "bootstrap"},
    "finish-finalize-release": {"publish"}, "finish-advance-current": {"publish"},
    "recover-advance-current": {"recover"},
    "activate-finalize-release": {"bootstrap"}, "activate-create-marker": {"bootstrap"},
    "activate-create-current": {"bootstrap"},
}


def fields(value, names):
    require(isinstance(value, dict) and value.keys() == set(names), "authorization_fields")


def integer(value):
    require(positive_integer(value), "authorization_integer")


def hash_value(value, length=64):
    require(hexadecimal(value, length), "authorization_digest")


def parse(raw, maximum):
    require(type(raw) is bytes and 0 < len(raw) <= maximum, "authorization_size")
    # Decode explicitly: JSON's UTF-16/32 auto-detection is not this UTF-8 contract.
    value = strict_json(raw.decode("utf-8"), maximum=maximum)
    require(canonical_json(value) == raw, "authorization_noncanonical")
    return value


def check_trust(trust):
    fields(trust, {"schema", "live_signer_accepted", "signer_revision", "ruleset_ids",
                   "verification_environment_id", "max_observation_age_seconds"})
    require(trust["schema"] == "atlas-publication-verifier-trust/v1"
            and trust["live_signer_accepted"] is True, "verifier_live_acceptance_required")
    hash_value(trust["signer_revision"], 40)
    fields(trust["ruleset_ids"], EXPECTED)
    for identity in trust["ruleset_ids"].values():
        integer(identity)
    require(len(set(trust["ruleset_ids"].values())) == 5, "authorization_ruleset_ids")
    integer(trust["verification_environment_id"])
    age = trust["max_observation_age_seconds"]
    require(type(age) is int and 1 <= age <= 60, "authorization_age_policy")


def check_publication_policy(policy, operation):
    check_policy(policy, operation=operation)
    require(policy["allowed_maintainer_id"] == OWNER_ID
            and policy["app_id"] == PUBLISHER_APP_ID
            and policy["app_installation_id"] == PUBLISHER_INSTALLATION_ID,
            "authorization_publication_identity")


def check_target(target, transition, operation):
    require(type(transition) is str and transition in TARGET_FIELDS, "authorization_transition")
    require(type(operation) is str and operation in OPERATIONS[transition], "authorization_operation")
    require(isinstance(target, dict), "authorization_fields")
    extra = set()
    if transition == "stage-upload-catalogue" and target.get("artifact_name") == "catalogue.sigstore.json":
        extra = {"catalogue_asset_id"}
    if transition == "seal-upload-selection" and target.get("artifact_name") == "current.sigstore.json":
        extra = {"pointer_asset_id"}
    fields(target, {"sequence", "catalogue_sha256", "snapshot_source_commit", "expected_prior"}
           | TARGET_FIELDS[transition] | extra)
    integer(target["sequence"])
    hash_value(target["catalogue_sha256"])
    hash_value(target["snapshot_source_commit"], 40)
    prior = target["expected_prior"]
    require(isinstance(prior, dict), "authorization_prior")
    if operation == "bootstrap":
        from bootstrap_catalogue import CATALOGUE_SHA256, SOURCE
        require(target["catalogue_sha256"] == CATALOGUE_SHA256
                and target["snapshot_source_commit"] == SOURCE, "authorization_frozen_bootstrap")
        kind = "marker-created" if transition == "activate-create-current" else "bootstrap-empty"
        fields(prior, {"kind", "marker_sha"} if kind == "marker-created" else {"kind"})
        require(prior["kind"] == kind and target["sequence"] == 1, "authorization_bootstrap_prior")
        if kind == "marker-created":
            hash_value(prior["marker_sha"], 40)
            require(prior["marker_sha"] == target["next_channel_sha"], "authorization_marker")
    else:
        fields(prior, {"kind", "channel_sha", "pointer_sha256", "sequence", "release_id",
                       "catalogue_asset_id", "catalogue_sha256"})
        require(prior["kind"] == "selected", "authorization_prior")
        hash_value(prior["channel_sha"], 40)
        for key in ("pointer_sha256", "catalogue_sha256"):
            hash_value(prior[key])
        for key in ("sequence", "release_id", "catalogue_asset_id"):
            integer(prior[key])
        require(target["sequence"] == prior["sequence"] + 1, "authorization_sequence")
    for key in ("release_id", "catalogue_asset_id", "catalogue_bundle_asset_id", "pointer_asset_id"):
        if key in target:
            integer(target[key])
    known_assets = [target[key] for key in ("catalogue_asset_id", "catalogue_bundle_asset_id", "pointer_asset_id")
                    if key in target]
    require(len(set(known_assets)) == len(known_assets), "authorization_asset_ids")
    for key in ("pointer_sha256", "artifact_sha256", "catalogue_bundle_sha256"):
        if key in target:
            hash_value(target[key])
    if "next_channel_sha" in target:
        hash_value(target["next_channel_sha"], 40)
        require(operation == "bootstrap" or target["next_channel_sha"] != prior["channel_sha"],
                "authorization_no_advance")
    if "artifact_name" in target:
        names = {snapshot_tag(target["sequence"]) + ".json", "catalogue.sigstore.json"}
        if transition == "seal-upload-selection":
            names = {"current.json", "current.sigstore.json"}
        require(target["artifact_name"] in names, "authorization_artifact_name")
        if target["artifact_name"].endswith(".json") and not target["artifact_name"].endswith("sigstore.json"):
            expected = target["pointer_sha256"] if transition == "seal-upload-selection" else target["catalogue_sha256"]
            require(target["artifact_sha256"] == expected, "authorization_artifact_digest")
        if operation == "bootstrap" and target["artifact_name"] == "catalogue.sigstore.json":
            from bootstrap_catalogue import BUNDLE_SHA256
            require(target["artifact_sha256"] == BUNDLE_SHA256, "authorization_frozen_bootstrap")
        if operation == "bootstrap" and transition == "seal-upload-selection":
            from bootstrap_catalogue import BUNDLE_SHA256
            require(target["catalogue_bundle_sha256"] == BUNDLE_SHA256, "authorization_frozen_bootstrap")
    if "assets" in target:
        assets = target["assets"]
        fields(assets, {snapshot_tag(target["sequence"]) + ".json", "catalogue.sigstore.json",
                       "current.json", "current.sigstore.json"})
        ids = []
        for row in assets.values():
            fields(row, {"id", "sha256"})
            integer(row["id"])
            hash_value(row["sha256"])
            ids.append(row["id"])
        require(len(set(ids)) == 4, "authorization_asset_ids")
        require(assets["current.json"]["sha256"] == target["pointer_sha256"]
                and assets[snapshot_tag(target["sequence"]) + ".json"]["sha256"] == target["catalogue_sha256"],
                "authorization_asset_digest")


def check_request(value):
    fields(value, {"source_commit", "policy_sha256", "run_id", "run_attempt", "operation",
                   "transition", "challenge", "target"})
    hash_value(value["source_commit"], 40)
    hash_value(value["policy_sha256"])
    integer(value["run_id"])
    require(type(value["run_attempt"]) is int and value["run_attempt"] == 1, "authorization_attempt")
    hash_value(value["challenge"])  # 256 random bits, established by the future consumer.
    check_target(value["target"], value["transition"], value["operation"])
    require(value["operation"] != "publish" or value["target"]["snapshot_source_commit"] == value["source_commit"],
            "authorization_snapshot_source")
    return value


def check_observations(observations, policy, operation, ids):
    require(isinstance(observations, list), "authorization_rulesets")
    listed = validate_list(observations)
    require(listed == ids, "authorization_ruleset_ids")
    require([row["name"] for row in observations] == sorted(EXPECTED), "authorization_ruleset_order")
    for row in observations:
        validate_detail(row, row["name"], listed[row["name"]])
    # One definition of protection semantics, including the bootstrap fence on ALL operations.
    check_rulesets(policy, observations, operation=operation, include_bootstrap_lock=True)


def check_authorization(value, trust, policy):
    check_trust(trust)
    fields(value, {"schema", "authority", "source", "execution", "rulesets", "target", "freshness"})
    require(value["schema"] == SCHEMA, "authorization_schema")
    fields(value["authority"], AUTHORITY)
    require(all(type(value["authority"][key]) is int and value["authority"][key] == expected
                for key, expected in AUTHORITY.items()), "authorization_authority")
    source = value["source"]
    fields(source, {"commit", "policy_sha256", "verifier_revision", "signer_workflow"})
    hash_value(source["commit"], 40)
    hash_value(source["policy_sha256"])
    require(source["verifier_revision"] == trust["signer_revision"]
            and source["signer_workflow"] == WORKFLOW, "authorization_signer")
    execution = value["execution"]
    fields(execution, {"workflow", "run_id", "run_attempt", "operation", "transition", "challenge"})
    require(execution["workflow"] == PUBLICATION_WORKFLOW, "authorization_workflow")
    request = {key: execution[key] for key in ("run_id", "run_attempt", "operation", "transition", "challenge")}
    request.update(source_commit=source["commit"], policy_sha256=source["policy_sha256"], target=value["target"])
    check_request(request)
    check_publication_policy(policy, execution["operation"])
    if execution["operation"] == "bootstrap" and execution["transition"].startswith("activate-"):
        require(value["target"]["pointer_sha256"] == policy["bootstrap"]["pointer_sha256"],
                "authorization_bootstrap_approval")
    rules = value["rulesets"]
    fields(rules, {"ids", "observations", "sha256", "approved_bypass_actors"})
    require(canonical_json(rules["ids"]) == canonical_json(trust["ruleset_ids"])
            and canonical_json(rules["approved_bypass_actors"]) == canonical_json(EXPECTED),
            "authorization_ruleset_policy")
    check_observations(rules["observations"], policy, execution["operation"], trust["ruleset_ids"])
    require(rules["sha256"] == digest(canonical_json(rules["observations"])), "authorization_ruleset_digest")
    fresh = value["freshness"]
    fields(fresh, {"observation_started", "observation_completed", "issued_at", "expires_at"})
    for timestamp in fresh.values():
        integer(timestamp)  # Whole UTC Unix seconds, never ambiguous date strings.
    start, end, issued, expires = (fresh[key] for key in
        ("observation_started", "observation_completed", "issued_at", "expires_at"))
    require(start <= end <= issued < expires <= start + trust["max_observation_age_seconds"],
            "authorization_freshness_order")
    return request


class AuthorizationVerifier:
    """Offline cryptography plus local context; no provider writes or global replay claim."""
    def __init__(self, trust, policy_raw):
        check_trust(trust)
        self.trust = parse(canonical_json(trust), MAX_REQUEST_BYTES)
        require(type(policy_raw) is bytes and 0 < len(policy_raw) <= MAX_REQUEST_BYTES, "authorization_policy_size")
        self.policy = strict_json(policy_raw.decode("utf-8"), maximum=MAX_REQUEST_BYTES)
        self.policy_sha256 = digest(policy_raw)
        self.consumed = set()

    def verify_and_consume(self, raw, bundle, expected, *, clock=time.time):
        from authorization_sigstore import AuthorizationSigstore
        check_request(expected)
        value = parse(raw, MAX_AUTHORIZATION_BYTES)
        actual = check_authorization(value, self.trust, self.policy)
        require(actual == expected, "authorization_context_mismatch")
        require(self.policy_sha256 == expected["policy_sha256"], "authorization_policy_digest")
        fresh = value["freshness"]
        def check_time():
            now = int(clock())
            integer(now)
            require(fresh["issued_at"] <= now < fresh["expires_at"]
                    and 0 <= now - fresh["observation_started"] <= self.trust["max_observation_age_seconds"],
                    "authorization_not_fresh")
        check_time()
        challenge = expected["challenge"]
        require(challenge not in self.consumed, "authorization_challenge_consumed")
        AuthorizationSigstore().verify(raw, bundle, expected=expected, trust=self.trust)
        check_time()  # Cryptographic verification itself can consume the freshness budget.
        self.consumed.add(challenge)
        return value
