# SPDX-License-Identifier: Apache-2.0
"""Approved immutable publication and explicitly separated historical bootstrap.

Normal stage/finish/recover never initialise history; bootstrap has its own phases.

Only the CLI with an enabled owner-reviewed policy may mutate GitHub. Tests use
explicit in-memory providers, not live releases, and do not constitute approval.
"""
from dataclasses import dataclass
import argparse
import os
from pathlib import Path
import re
import urllib.parse

from atlas_connector_sdk.contracts import strict_json
import build_catalogue
from publication_contract import (API, ENVIRONMENT, MAX_BUNDLE_BYTES, MAX_CATALOGUE_BYTES,
    AUTHORIZATION_MODE, REPOSITORY, PublicationError, canonical_json, check_app, check_authority, check_policy, check_rulesets,
    digest, hexadecimal, parse_catalogue, parse_pointer, pointer_bytes, pointer_transition,
    positive_integer, require, sequence_transition, snapshot_tag)
from publication_github import Github
from publication_verify import Verifier, read_regular

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "catalogue/publication/policy.json"


def release_identity(release, tag, *, immutable=False):
    require(isinstance(release, dict) and positive_integer(release.get("id"))
            and release.get("tag_name") == tag and release.get("url") == f"{API}/releases/{release['id']}"
            and release.get("prerelease") is False and type(release.get("draft")) is bool, "release_identity")
    if immutable:
        require(release["draft"] is False and release.get("immutable") is True, "release_not_immutable")


def source_tag(api, tag, commit, *, allow_missing=False):
    result = api.json("GET", "/git/ref/tags/" + urllib.parse.quote(tag, safe=""), missing=allow_missing)
    if result is None:
        require(allow_missing, "tag_missing")
        return
    value = result["object"]
    for _ in range(2):
        require(hexadecimal(value.get("sha"), 40), "tag_identity")
        if value.get("type") == "commit":
            require(value["sha"] == commit, "tag_source_mismatch")
            return
        require(value.get("type") == "tag", "tag_type")
        value = api.json("GET", "/git/tags/" + value["sha"])["object"]
    raise PublicationError("tag_depth")


@dataclass(frozen=True)
class Stage:
    pointer: bytes
    bundle: bytes | None
    release_id: int
    unchanged: bool = False


class Publisher:
    def __init__(self, api, verifier, policy, run_id, *, source_commit, token_identity=None):
        self.api, self.verifier, self.policy, self.run_id = api, verifier, policy, run_id
        self.source_commit, self.token_identity = source_commit, token_identity
        self.policy_operation = "publish"

    def run_authority(self, run_id, source_commit, *, historical=False, package_tag=None):
        check_policy(self.policy, operation=self.policy_operation)
        require(positive_integer(run_id) and hexadecimal(source_commit, 40), "invalid_run_context")
        run = self.api.json("GET", f"/actions/runs/{run_id}")
        require(isinstance(run, dict) and positive_integer(run.get("workflow_id")), "missing_run_evidence")
        actor = run.get("actor")
        require(isinstance(actor, dict) and isinstance(actor.get("login"), str)
                and re.fullmatch(r"[A-Za-z0-9-]{1,100}(?:\[bot\])?", actor["login"]), "unsupported_actor_identity")
        user = self.api.json("GET", "/users/" + urllib.parse.quote(actor["login"], safe=""), api_global=True)
        if package_tag:
            deployment = self.api.json("GET", "/environments/connector-release/deployment-branch-policies?per_page=100")
            require(isinstance(deployment, dict) and type(deployment.get("total_count")) is int
                    and deployment["total_count"] == 1, "package_environment_tag_policy")
            policies = deployment.get("branch_policies")
            require(isinstance(policies, list) and len(policies) == 1 and isinstance(policies[0], dict)
                    and positive_integer(policies[0].get("id")) and policies[0].get("name") == "*-v*"
                    and policies[0].get("type") == "tag", "package_environment_tag_policy")
        return check_authority(self.policy, self.api.json("GET", "/"),
            self.api.json("GET", "/branches/main"),
            self.api.json("GET", "/environments/" + ("connector-release" if package_tag else ENVIRONMENT)), run,
            self.api.json("GET", f"/actions/runs/{run_id}/attempts/1"),
            self.api.json("GET", f"/actions/workflows/{run['workflow_id']}"), user,
            # Public repository: an anonymous CI read avoids expanding the
            # publication App's permissions to Checks read. No auth fallback.
            self.api.json("GET", f"/commits/{source_commit}/check-runs?check_name=validate&filter=latest&per_page=100", public=True),
            run_id=run_id, source_commit=source_commit, historical=historical, package_tag=package_tag, operation=self.policy_operation)

    def authority(self):
        check_policy(self.policy, operation=self.policy_operation)
        authority = self.run_authority(self.run_id, self.source_commit)
        check_app(self.policy,
            self.api.json("GET", "/apps/" + self.policy["app_slug"], api_global=True),
            self.api.json("GET", "/installation/repositories?per_page=100", api_global=True), self.token_identity, operation=self.policy_operation)
        immutable = self.api.json("GET", "/immutable-releases")
        require(immutable.get("enabled") is True, "release_immutability_not_enabled")
        rules = self.api.json("GET", "/rulesets?per_page=100")
        require(isinstance(rules, list) and len(rules) < 100 and all(positive_integer(r.get("id")) for r in rules),
                "ruleset_response_limit")
        check_rulesets(self.policy, [self.api.json("GET", f"/rulesets/{r['id']}") for r in rules], operation=self.policy_operation)
        return authority

    def selection(self, raw, bundle):
        pointer = parse_pointer(raw)
        evidence = self.verifier.verify(raw, bundle, profile="pointer", name="current.json")
        # The authenticated invocation selects API evidence, never the allowed user.
        # Historical main need not still be HEAD. Both API actors remain mandatory.
        match = re.fullmatch(r"https://github.com/" + re.escape(REPOSITORY)
                             + r"/actions/runs/([1-9][0-9]*)/attempts/1", evidence.invocation)
        require(match is not None, "fresh_dispatch_run_required")
        self.run_authority(int(match[1]), evidence.source_commit, historical=True)
        return pointer

    def snapshot(self, pointer):
        release = self.api.release_id(pointer["release_id"])
        release_identity(release, pointer["release_tag"], immutable=True)
        assets = self.api.assets(release)
        name = pointer["release_tag"] + ".json"
        require(name in assets and assets[name]["id"] == pointer["asset_id"], "snapshot_asset_identity")
        require("catalogue.sigstore.json" in assets, "snapshot_attestation_missing")
        raw = self.api.asset_bytes(assets[name], MAX_CATALOGUE_BYTES)
        require(digest(raw) == pointer["sha256"] and parse_catalogue(raw)["sequence"] == pointer["sequence"],
                "snapshot_digest")
        bundle = self.api.asset_bytes(assets["catalogue.sigstore.json"], MAX_BUNDLE_BYTES)
        evidence = self.verifier.verify(raw, bundle, profile="catalogue", name=name)
        source_tag(self.api, pointer["release_tag"], evidence.source_commit)
        return raw

    def current(self):
        head, files = self.api.channel()
        pointer = self.selection(files["current.json"], files["current.sigstore.json"])
        bootstrap = self.policy.get("bootstrap", {})
        require(positive_integer(bootstrap.get("sequence")) and hexadecimal(bootstrap.get("pointer_sha256")),
                "approved_bootstrap_required")
        require(pointer["sequence"] >= bootstrap["sequence"], "bootstrap_rollback")
        if pointer["sequence"] == bootstrap["sequence"]:
            require(digest(files["current.json"]) == bootstrap["pointer_sha256"], "bootstrap_substitution")
        raw = self.snapshot(pointer)
        release = self.api.release_id(pointer["release_id"])
        assets = self.api.assets(release)
        for name, expected in files.items():
            require(name in assets and self.api.asset_bytes(assets[name], len(expected)) == expected,
                    "selection_release_evidence_missing")
        return head, files, raw

    def packages(self, document):
        for entry in document["entries"]:
            if entry["status"] == "withdrawn":
                continue  # Historical tombstones convey no executable eligibility.
            manifest = entry["manifest"]
            require(manifest.get("source_versions", {}).get("qualification") == "qualified"
                    and bool(manifest["source_versions"].get("qualified_versions")), "package_unqualified")
            release = self.api.release(entry["release_tag"])
            release_identity(release, entry["release_tag"], immutable=True)
            distribution = manifest["distribution"]
            source = distribution["provenance"]["source_commit"]
            source_tag(self.api, entry["release_tag"], source)
            name = f"{manifest['id']}-{manifest['version']}.tar.gz"
            assets = self.api.assets(release)
            require(name in assets and assets[name]["id"] == entry["release_asset_id"], "package_asset_identity")
            raw = self.api.asset_bytes(assets[name], 20 * 1024 * 1024)
            require("sha256:" + digest(raw) == distribution["bundle_digest"], "package_digest")
            _, evidence = self.api.attestation(raw, self.verifier, profile="package", name=name, commit=source, tag=entry["release_tag"])
            invocation = re.fullmatch(r"https://github.com/" + re.escape(REPOSITORY)
                                      + r"/actions/runs/([0-9]+)/attempts/1", evidence.invocation)
            require(invocation is not None, "package_build_attempt")
            self.run_authority(int(invocation[1]), source, historical=True, package_tag=entry["release_tag"])
            comparison = self.api.json("GET", f"/compare/{source}...main")
            require(comparison.get("status") in {"ahead", "identical"}
                    and comparison.get("merge_base_commit", {}).get("sha") == source, "package_unreviewed_source")

    def stage(self, raw):
        check_policy(self.policy)
        authority = self.authority()
        candidate = parse_catalogue(raw)
        name = snapshot_tag(candidate["sequence"]) + ".json"
        catalogue_bundle, _ = self.api.attestation(raw, self.verifier, profile="catalogue", name=name,
                                                  commit=authority.source_commit)
        head, previous_files, previous_raw = self.current()
        transition = sequence_transition(previous_raw, raw)
        if transition == "unchanged":
            return Stage(previous_files["current.json"], previous_files["current.sigstore.json"],
                         parse_pointer(previous_files["current.json"])["release_id"], True)
        self.packages(candidate)
        tag = snapshot_tag(candidate["sequence"])
        # Supported publishers cannot allocate another sequence before selecting this
        # one. A pre-existing higher tag is an explicit operator conflict, never ignored.
        if candidate["sequence"] < build_catalogue.MAX_INTEGER:
            require(self.api.release(snapshot_tag(candidate["sequence"] + 1)) is None, "higher_snapshot_exists")
        require(self.api.channel()[0] == head, "channel_changed")
        source_tag(self.api, tag, authority.source_commit, allow_missing=True)
        release = self.api.release(tag)
        if release is None:
            release = self.api.json("POST", "/releases", payload={"tag_name": tag,
                "target_commitish": authority.source_commit, "name": tag, "draft": True,
                "prerelease": False, "make_latest": "false"})
        release_identity(release, tag)
        if not release["draft"]:
            require(release.get("immutable") is True, "release_not_immutable")
            source_tag(self.api, tag, authority.source_commit)
        else:
            require(release.get("target_commitish") == authority.source_commit, "draft_source_mismatch")
        expected_names = {name, "catalogue.sigstore.json", "current.json", "current.sigstore.json"}
        require(self.api.assets(release).keys() <= expected_names, "unexpected_staged_assets")
        asset = self.api.upload(release, name, raw)
        # Reuse a genuine matching bundle; re-signing identical bytes is not a
        # reason to overwrite or reject already-authenticated historical evidence.
        assets = self.api.assets(release)
        if "catalogue.sigstore.json" in assets:
            original = self.api.asset_bytes(assets["catalogue.sigstore.json"], MAX_BUNDLE_BYTES)
            self.verifier.verify(raw, original, profile="catalogue", name=name, commit=authority.source_commit)
        else:
            self.api.upload(release, "catalogue.sigstore.json", catalogue_bundle)
        pointer = pointer_bytes({"schema_version": "1.0", "sequence": candidate["sequence"], "release_tag": tag,
            "release_id": release["id"], "asset_id": asset["id"], "sha256": digest(raw),
            "previous_pointer_sha256": digest(previous_files["current.json"])})
        pointer_transition(previous_files["current.json"], pointer)
        self.api.upload(release, "current.json", pointer)
        assets = self.api.assets(release)
        bundle = None
        if "current.sigstore.json" in assets:
            bundle = self.api.asset_bytes(assets["current.sigstore.json"], MAX_BUNDLE_BYTES)
            self.selection(pointer, bundle)
        require(self.api.channel()[0] == head, "channel_changed")
        return Stage(pointer, bundle, release["id"])

    def finish(self, raw, pointer_raw, bundle):
        stage = self.stage(raw)  # Re-authenticate source, dispatch, history and bytes.
        require(stage.pointer == pointer_raw, "staged_pointer_changed")
        if stage.unchanged:
            return {"result": "unchanged", "sequence": parse_pointer(pointer_raw)["sequence"]}
        pointer = self.selection(pointer_raw, bundle)
        head, previous_files, _ = self.current()
        pointer_transition(previous_files["current.json"], pointer_raw)
        release = self.api.release_id(stage.release_id)
        release_identity(release, pointer["release_tag"])
        # Always preserve an existing authenticated bundle on resume.
        bundle = stage.bundle if stage.bundle is not None else bundle
        self.api.upload(release, "current.sigstore.json", bundle)
        self.authority()  # Detect a new main commit / policy change before finalisation.
        require(self.api.channel()[0] == head, "channel_changed")
        if release["draft"]:
            source_tag(self.api, pointer["release_tag"], release["target_commitish"], allow_missing=True)
            self.api.json("PATCH", f"/releases/{stage.release_id}", payload={"draft": False, "make_latest": "false"})
        # The actual provider flag and exact IDs/bytes, not the tag name, prove
        # the GitHub publication boundary. Failure leaves current untouched.
        require(self.snapshot(pointer) == raw, "published_snapshot_changed")
        published = self.api.release_id(stage.release_id)
        assets = self.api.assets(published)
        files = {"current.json": pointer_raw, "current.sigstore.json": bundle}
        require(set(assets) == {pointer["release_tag"] + ".json", "catalogue.sigstore.json", *files},
                "published_asset_set")
        for name, value in files.items():
            require(self.api.asset_bytes(assets[name], len(value)) == value, "published_selection_changed")
        self.selection(pointer_raw, bundle)
        self.authority()  # Recheck current protections before selecting the locked snapshot.
        require(self.api.channel()[0] == head, "channel_changed")
        revision = self.api.compare_and_swap(head, files)
        return {"result": "published", "sequence": pointer["sequence"], "release_id": pointer["release_id"],
                "asset_id": pointer["asset_id"], "sha256": pointer["sha256"], "channel_commit": revision}

    def recover(self):
        """Select only the already approved immutable immediate successor.

        This supports recovery after main has advanced without rebuilding old
        bytes or dispatching an arbitrary source ref. It never repairs a draft.
        """
        check_policy(self.policy)
        self.authority()
        head, previous_files, previous_raw = self.current()
        previous = parse_pointer(previous_files["current.json"])
        require(previous["sequence"] < build_catalogue.MAX_INTEGER, "sequence_exhausted")
        release = self.api.release(snapshot_tag(previous["sequence"] + 1))
        if release is None:
            return {"result": "no_interrupted_snapshot", "sequence": previous["sequence"]}
        release_identity(release, snapshot_tag(previous["sequence"] + 1), immutable=True)
        assets = self.api.assets(release)
        require({"current.json", "current.sigstore.json"} <= assets.keys(), "selection_release_evidence_missing")
        files = {name: self.api.asset_bytes(assets[name], maximum) for name, maximum in
                 (("current.json", 1024), ("current.sigstore.json", MAX_BUNDLE_BYTES))}
        pointer = self.selection(files["current.json"], files["current.sigstore.json"])
        require(pointer["release_id"] == release["id"], "recovery_release_identity")
        pointer_transition(previous_files["current.json"], files["current.json"])
        raw = self.snapshot(pointer)
        sequence_transition(previous_raw, raw)
        self.packages(parse_catalogue(raw))
        self.authority()
        require(self.api.channel()[0] == head, "channel_changed")
        revision = self.api.compare_and_swap(head, files)
        return {"result": "recovered", "sequence": pointer["sequence"], "release_id": pointer["release_id"],
                "asset_id": pointer["asset_id"], "sha256": pointer["sha256"], "channel_commit": revision}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("authorize", "stage", "finish", "recover",
        "bootstrap-preflight", "bootstrap-stage", "bootstrap-seal", "bootstrap-activate"))
    parser.add_argument("--bundle", type=Path)
    args = parser.parse_args()
    try:
        policy = strict_json(read_regular(POLICY, 16384))
        from bootstrap_catalogue import BootstrapPublisher, local_preflight
        if args.phase == "bootstrap-preflight":
            print(canonical_json(local_preflight(policy, Verifier())).decode(), end="")
            return
        operation = os.environ.get("PUBLICATION_OPERATION")
        allowed = {"publish": {"authorize", "stage", "finish"}, "recover": {"authorize", "recover"},
                   "bootstrap": {"authorize", "bootstrap-stage", "bootstrap-seal", "bootstrap-activate"}}
        require(operation in allowed and args.phase in allowed[operation], "unauthorized_publication_phase")
        check_policy(policy, operation=operation)
        require(os.environ.get("GITHUB_REPOSITORY") == REPOSITORY
                and os.environ.get("GITHUB_REF") == "refs/heads/main"
                and os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
                and os.environ.get("GITHUB_RUN_ATTEMPT") == "1", "untrusted_workflow_context")
        publisher_type = BootstrapPublisher if operation == "bootstrap" else Publisher
        publisher = publisher_type(Github(os.environ.get("ATLAS_PUBLICATION_TOKEN")),
                              None if args.phase == "authorize" else Verifier(), policy,
                              int(os.environ.get("GITHUB_RUN_ID", "0")), source_commit=os.environ.get("GITHUB_SHA"),
                              token_identity={"app_slug": os.environ.get("ATLAS_APP_SLUG"),
                                              "installation_id": int(os.environ.get("ATLAS_APP_INSTALLATION_ID", "0"))})
        if args.phase == "authorize":
            publisher.run_authority(publisher.run_id, publisher.source_commit)
            print("single-maintainer dispatch identity verified against GitHub API")
            return
        output = ROOT / "dist/publication"
        output.mkdir(parents=True, exist_ok=True)
        if args.phase == "bootstrap-stage":
            staged = publisher.stage_bootstrap()
            (output / "current.json").write_bytes(staged.pointer)
            if staged.bundle is not None:
                (output / "current.sigstore.json").write_bytes(staged.bundle)
            receipt = {"result": "bootstrap_signing_pending", "needs_attestation": staged.bundle is None,
                       "release_id": staged.release_id, "pointer_sha256": digest(staged.pointer)}
            if os.environ.get("GITHUB_OUTPUT"):
                with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
                    stream.write(f"needs_attestation={str(staged.bundle is None).lower()}\n")
        elif args.phase == "bootstrap-seal":
            receipt = publisher.seal_bootstrap(read_regular(output / "current.json", 1024),
                                               read_regular(output / "current.sigstore.json", MAX_BUNDLE_BYTES))
        elif args.phase == "bootstrap-activate":
            receipt = publisher.activate_bootstrap()
        elif args.phase == "recover":
            receipt = publisher.recover()
        elif args.phase == "stage":
            raw, _ = build_catalogue.build()
            staged = publisher.stage(raw)
            (output / "current.json").write_bytes(staged.pointer)
            if staged.bundle is not None:
                (output / "current.sigstore.json").write_bytes(staged.bundle)
            receipt = {"needs_attestation": staged.bundle is None, "release_id": staged.release_id,
                       "sequence": parse_pointer(staged.pointer)["sequence"], "sha256": digest(raw)}
            (output / "stage.json").write_bytes(canonical_json(receipt))
            if os.environ.get("GITHUB_OUTPUT"):
                with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
                    stream.write(f"needs_attestation={str(staged.bundle is None).lower()}\n")
        else:
            raw, _ = build_catalogue.build()
            bundle_path = args.bundle or output / "current.sigstore.json"
            receipt = publisher.finish(raw, read_regular(output / "current.json", 1024),
                                       read_regular(bundle_path, MAX_BUNDLE_BYTES))
        receipt.update(authorization_mode=AUTHORIZATION_MODE, authorization_run_id=publisher.run_id,
                       authorization_source_commit=publisher.source_commit,
                       allowed_maintainer_id=policy["allowed_maintainer_id"])
        (output / "receipt.json").write_bytes(canonical_json(receipt))
        print(canonical_json(receipt).decode(), end="")
    except (ValueError, OSError, KeyError, TypeError, AttributeError, IndexError) as error:
        code = str(error) if isinstance(error, PublicationError) else "publication_validation_failed"
        parser.exit(1, code + "\n")


if __name__ == "__main__":
    main()
