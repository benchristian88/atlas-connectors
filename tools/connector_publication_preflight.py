# SPDX-License-Identifier: Apache-2.0
"""Isolated package observer and independent startup admission. No release writes."""
import os
from pathlib import Path
import re
import sys
import time

from atlas_connector_sdk.contracts import strict_json
from connector_publication_contract import (AUTHORITY, MAX_AUTHORIZATION_BYTES, MAX_REQUEST_BYTES,
    POLICY_PATH, PREDICATE_SCHEMA, REPOSITORY, SCHEMA, SIGNER, SUBJECT, TRUST_PATH, check_input,
    check_preflight, check_trust, context, fields, parse)
from connector_publication_sigstore import ConnectorSigstore
from issue_publication_authorization import authenticate, content_bytes
from publication_contract import MAX_BUNDLE_BYTES, canonical_json, digest, require
from publication_github import Github
from publication_verify import read_regular
from verification_github import BASE, LIST, VerificationGithub, allowed


class PackageVerificationGithub(VerificationGithub):
    """Extend only GET data routes; reuse the isolated credential mint unchanged."""
    def get(self, path, token, *, missing=False):
        if allowed(path):
            return super().get(path, token, missing=missing)
        require(re.fullmatch(re.escape(BASE) + r"/contents/catalogue/publication/connector-trust\.json\?ref=[a-f0-9]{40}", path)
            or re.fullmatch(re.escape(BASE) + r"/contents/\.github/workflows/connector-publish\.yml\?ref=[a-f0-9]{40}", path),
            "connector_verification_endpoint")
        client = Github(token)
        client.deadline = self.deadline
        return client.json("GET", path[len(BASE):], maximum=256 * 1024)


def inputs_from_env(environ):
    value = strict_json(environ["CONNECTOR_REQUEST"], maximum=MAX_REQUEST_BYTES)
    return check_input(value)


def configuration(environ, inputs):
    trust = strict_json(environ["CONNECTOR_VERIFICATION_POLICY"], maximum=MAX_REQUEST_BYTES)
    check_trust(trust, acceptance_only=inputs["acceptance_only"])
    expected = context(environ, inputs)
    require(environ.get("ATLAS_IMPLEMENTATION_REVISION") == trust["signer_revision"], "connector_implementation_pin")
    return trust, expected


def observe(api, token, expected, trust):
    get = lambda path: api.get(BASE + path, token)
    caller, run_id = expected["caller_sha"], expected["run_id"]
    policy_raw = content_bytes(get(f"/contents/{POLICY_PATH}?ref={caller}"), POLICY_PATH)
    observed_trust = content_bytes(get(f"/contents/{TRUST_PATH}?ref={caller}"), TRUST_PATH)
    require(parse(observed_trust, MAX_REQUEST_BYTES) == trust, "connector_independent_trust_mismatch")
    # Authenticate the literal caller-to-S wiring as data, before signing.
    caller_raw = content_bytes(get(f"/contents/.github/workflows/connector-publish.yml?ref={caller}"),
        ".github/workflows/connector-publish.yml")
    require((REPOSITORY + "/" + SIGNER + "@" + trust["signer_revision"]).encode() in caller_raw,
        "connector_caller_pin")
    run = get(f"/actions/runs/{run_id}")
    require(isinstance(run, dict) and type(run.get("workflow_id")) is int, "connector_run")
    security = {"repository": get(""), "branch": get("/branches/main"),
        "environment": get("/environments/catalogue-publication"), "run": run,
        "attempt": get(f"/actions/runs/{run_id}/attempts/1"),
        "workflow": get(f"/actions/workflows/{run['workflow_id']}"),
        "user": api.get("/users/benchristian88", token),
        "checks": get(f"/commits/{caller}/check-runs?check_name=validate&filter=latest&per_page=2&page=1"),
        "publisher_app": api.get("/apps/atlas-catalogue-publisher", token),
        "verification_environment": get("/environments/catalogue-verification"),
        "immutable_releases": get("/immutable-releases")}
    from ruleset_visibility import validate_list
    require(validate_list(api.get(LIST, token)) == trust["ruleset_ids"], "connector_ruleset_ids")
    rulesets = [get(f"/rulesets/{trust['ruleset_ids'][name]}?includes_parents=true")
                for name in sorted(trust["ruleset_ids"])]
    return policy_raw, security, rulesets


def issue(api, environ, *, clock=time.time):
    inputs = inputs_from_env(environ)
    trust, expected = configuration(environ, inputs)
    require(environ.get("VERIFIER_WORKFLOW_REF") == REPOSITORY + "/" + SIGNER + "@refs/heads/main",
        "connector_signer_context")
    require(environ.get("DISPATCH_OPERATION") == inputs["operation"]
        and environ.get("DISPATCH_ACCEPTANCE_ONLY") == str(inputs["acceptance_only"]).lower()
        and strict_json(environ["DISPATCH_PACKAGE"], maximum=MAX_REQUEST_BYTES) == inputs["package"],
        "connector_dispatch_substitution")
    started = int(clock())
    token = authenticate(api, environ)
    policy_raw, security, rulesets = observe(api, token, expected, trust)
    now = int(clock())
    value = {"schema": SCHEMA, "authority": AUTHORITY, "context": expected,
        "implementation_sha": trust["signer_revision"], "trust_sha256": digest(canonical_json(trust)),
        "policy_sha256": digest(policy_raw), "security": security, "rulesets": rulesets,
        "freshness": {"observation_started": started, "observation_completed": now,
            "issued_at": now, "expires_at": started + trust["max_observation_age_seconds"]}}
    check_preflight(value, expected, trust, policy_raw)
    raw = canonical_json(value)
    require(len(raw) <= MAX_AUTHORIZATION_BYTES and now < value["freshness"]["expires_at"], "connector_preflight_size_or_age")
    return raw


def admit(raw, bundle, expected, trust, policy_raw, *, clock=time.time, started_at=None):
    value = parse(raw, MAX_AUTHORIZATION_BYTES)
    check_preflight(value, expected, trust, policy_raw)
    def fresh():
        now = int(clock())
        admitted = now if started_at is None else started_at
        require(type(admitted) is int and value["freshness"]["issued_at"] <= admitted < value["freshness"]["expires_at"]
            and 0 <= now - admitted <= 1800, "connector_admission_expired")
    fresh()
    ConnectorSigstore().verify(raw, bundle, expected=expected, trust=trust)
    fresh()
    return value


def job_admission(environ, policy_raw, *, startup=False):
    inputs = inputs_from_env(environ)
    require(inputs["acceptance_only"] is False, "connector_acceptance_has_no_publisher")
    trust, expected = configuration(environ, inputs)
    directory = Path(environ["RUNNER_TEMP"]) / "connector-preflight"
    require({p.name for p in directory.iterdir()} == {SUBJECT, "connector-preflight.sigstore.json"},
        "connector_preflight_inventory")
    raw = read_regular(directory / SUBJECT, MAX_AUTHORIZATION_BYTES)
    bundle = read_regular(directory / "connector-preflight.sigstore.json", MAX_BUNDLE_BYTES)
    receipt = Path(environ["RUNNER_TEMP"]) / "connector-admitted.json"
    started = None
    if not startup:
        previous = parse(read_regular(receipt, MAX_REQUEST_BYTES), MAX_REQUEST_BYTES)
        fields(previous, {"context", "sha256", "started_at"})
        require(previous["context"] == expected and previous["sha256"] == digest(raw), "connector_admission_replay")
        started = previous["started_at"]
    value = admit(raw, bundle, expected, trust, policy_raw, started_at=started)
    if startup:
        now = int(time.time())
        require(value["freshness"]["issued_at"] <= now < value["freshness"]["expires_at"], "connector_admission_expired")
        with receipt.open("xb") as stream:
            stream.write(canonical_json({"context": expected, "sha256": digest(raw), "started_at": now}))
    return value


def main():
    try:
        directory = Path(os.environ["RUNNER_TEMP"]) / "connector-authorization"
        if sys.argv[1:] == ["seal"]:
            raw = read_regular(directory / SUBJECT, MAX_AUTHORIZATION_BYTES)
            bundle = read_regular(os.environ["BUNDLE_PATH"], MAX_BUNDLE_BYTES)
            value = parse(raw, MAX_AUTHORIZATION_BYTES)
            trust, expected = configuration(os.environ, inputs_from_env(os.environ))
            ConnectorSigstore().verify(raw, bundle, expected=expected, trust=trust)
            require(value["freshness"]["issued_at"] <= int(time.time()) < value["freshness"]["expires_at"],
                "connector_admission_expired")
            (directory / "connector-preflight.sigstore.json").write_bytes(bundle)
        else:
            require(not sys.argv[1:], "connector_preflight_command")
            raw = issue(PackageVerificationGithub(), os.environ)
            directory.mkdir(mode=0o700)
            (directory / SUBJECT).write_bytes(raw)
            (directory / "predicate.json").write_bytes(canonical_json({"schema": PREDICATE_SCHEMA,
                "preflight_sha256": digest(raw)}))
    except Exception:
        print("connector_preflight_failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
