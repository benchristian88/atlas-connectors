# SPDX-License-Identifier: Apache-2.0
"""Three separately dispatched package operations. No catalogue writes or fallback."""
import argparse
from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import sys

from atlas_connector_sdk.contracts import strict_json
import build_bundle
import release_connector
import verify_connector_release
from connector_publication_contract import (POLICY_PATH, TRUST_PATH, check_input, check_policy_identity,
    dispatch_authority, inventory, parse)
from connector_publication_github import ConnectorGithub, mint_publisher, unpack_artifact
from connector_publication_preflight import configuration, inputs_from_env, job_admission
from connector_release import (authenticated_bundle, candidate, clean_source,
    filename, metadata_files, validate_package)
from publication_contract import (API, MAX_BUNDLE_BYTES, PublicationError, canonical_json, check_repository,
    digest, hexadecimal, positive_integer, require)
from publication_verify import Verifier, read_regular
from publish_catalogue import Publisher, check_checkouts, release_identity, source_tag
from verify_connector_release import app_actor, approved_asset_inventory, build_authority

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def package_source(directory):
    """Trusted builders read an exact source checkout as data. Never import from it."""
    modules = (build_bundle, release_connector, verify_connector_release)
    previous = [module.ROOT for module in modules]
    try:
        for module in modules:
            module.ROOT = directory
        yield
    finally:
        for module, root in zip(modules, previous):
            module.ROOT = root


def source_authority(api, commit, caller):
    require(hexadecimal(commit, 40) and hexadecimal(caller, 40), "connector_source_identity")
    comparison = api.json("GET", f"/compare/{commit}...main")
    require(comparison.get("status") in {"ahead", "identical"}
        and comparison.get("merge_base_commit", {}).get("sha") == commit, "connector_unmerged_source")
    checks = api.json("GET", f"/commits/{commit}/check-runs?check_name=validate&filter=latest&per_page=100", public=True)
    rows = checks.get("check_runs")
    require(type(checks.get("total_count")) is int and checks["total_count"] == 1
        and isinstance(rows, list) and len(rows) == 1 and rows[0].get("name") == "validate"
        and rows[0].get("head_sha") == commit and rows[0].get("status") == "completed"
        and rows[0].get("conclusion") == "success" and rows[0].get("app", {}).get("id") == 15368,
        "connector_source_ci")
    pulls = api.json("GET", f"/commits/{commit}/pulls?per_page=100&page=1")
    require(isinstance(pulls, list) and 0 < len(pulls) < 100, "connector_source_review")
    merged = [p for p in pulls if p.get("merge_commit_sha") == commit and p.get("state") == "closed"
        and type(p.get("merged_at")) is str and bool(p["merged_at"]) and p.get("base", {}).get("ref") == "main"]
    require(len(merged) == 1, "connector_source_review")
    check_repository(merged[0]["base"].get("repo"))
    # Conservative sufficient condition for the provider's conditional Workflows
    # Write requirement: the entire workflow directory must equal default main.
    def workflows(sha):
        rows = api.json("GET", f"/contents/.github/workflows?ref={sha}")
        require(isinstance(rows, list) and 0 < len(rows) < 100, "connector_workflow_tree")
        require(all(r.get("type") == "file" and hexadecimal(r.get("sha"), 40)
            and type(r.get("path")) is str and r["path"].startswith(".github/workflows/") for r in rows),
            "connector_workflow_tree")
        return sorted((r["path"], r["sha"], r["type"]) for r in rows)
    require(workflows(commit) == workflows(caller), "connector_workflows_write_required")


def prepare_candidate(api, verifier, directory, package, operation, caller):
    source_authority(api, package["source_commit"], caller)
    clean_source(package["source_commit"])
    manifest = release_connector.prepare(package["tag"], directory, commit=package["source_commit"])
    require(manifest["distribution"]["bundle_digest"] == "sha256:" + package["sha256"], "connector_expected_digest")
    if operation == "tag":
        return {p.name: p.read_bytes() for p in directory.iterdir()}, manifest
    # Successful original run, App actors and source/tag are checked BEFORE
    # selecting or downloading an Actions artifact.
    policy = strict_json(read_regular(release_connector.ROOT / POLICY_PATH, 16384))
    check_policy_identity(policy)
    build_authority(api, verifier, policy, run_id=package["build_run_id"], commit=package["source_commit"], tag=package["tag"])
    names = {filename(manifest), "manifest.json", "index.json", "SHA256SUMS", "package.sigstore.json"}
    files = unpack_artifact(api.artifact(package), names)
    connector, version = release_connector.selection(package["tag"])
    expected = {filename(manifest): build_bundle.build(connector, version=version)[0], **metadata_files(manifest)}
    require(all(files[name] == raw for name, raw in expected.items()), "connector_original_build_bytes")
    authenticated_bundle(files, manifest, files["package.sigstore.json"], verifier,
        tag=package["tag"], commit=package["source_commit"], run_id=package["build_run_id"])
    for name, raw in files.items():
        (directory / name).write_bytes(raw)
    build_authority(api, verifier, policy, run_id=package["build_run_id"], commit=package["source_commit"], tag=package["tag"])
    return files, manifest


class PackagePublisher:
    def __init__(self, api, verifier, inputs, trust, policy, expected, *, reauthorize, read_only):
        check_input(inputs)
        require(inputs["acceptance_only"] is False, "connector_acceptance_has_no_publisher")
        self.api, self.verifier, self.inputs = api, verifier, inputs
        self.package, self.operation = inputs["package"], inputs["operation"]
        self.trust, self.policy, self.expected = trust, policy, expected
        self.reauthorize, self.read_only = reauthorize, read_only

    def authority(self):
        signed = self.reauthorize()  # Genuine signature + job-local freshness every time.
        require(signed.get("context") == self.expected and signed.get("implementation_sha") == self.trust["signer_revision"],
            "connector_readmission_binding")
        p, api = self.package, self.api
        run_id, caller = self.expected["run_id"], self.expected["caller_sha"]
        run = api.json("GET", f"/actions/runs/{run_id}")
        security = {"repository": api.json("GET", "/"), "branch": api.json("GET", "/branches/main"),
            "environment": api.json("GET", "/environments/catalogue-publication"), "run": run,
            "attempt": api.json("GET", f"/actions/runs/{run_id}/attempts/1"),
            "workflow": api.json("GET", f"/actions/workflows/{run['workflow_id']}"),
            "user": api.json("GET", "/users/benchristian88", api_global=True),
            "checks": api.json("GET", f"/commits/{caller}/check-runs?check_name=validate&filter=latest&per_page=100", public=True),
            "publisher_app": api.json("GET", "/apps/atlas-catalogue-publisher", api_global=True),
            "verification_environment": api.json("GET", "/environments/catalogue-verification"),
            "immutable_releases": api.json("GET", "/immutable-releases")}
        dispatch_authority(security, self.policy, self.expected, self.trust)
        scope = api.json("GET", "/installation/repositories?per_page=100", api_global=True)
        require(type(scope.get("total_count")) is int and scope["total_count"] == 1
            and isinstance(scope.get("repositories"), list) and len(scope["repositories"]) == 1,
            "connector_publisher_scope")
        check_repository(scope["repositories"][0])
        listed = api.json("GET", "/rulesets?includes_parents=true&per_page=6&page=1")
        require(isinstance(listed, list) and len(listed) == 5
            and {r.get("id") for r in listed} == set(self.trust["ruleset_ids"].values()), "connector_ruleset_changed")
        for prior in signed["rulesets"]:
            now = api.json("GET", f"/rulesets/{prior['id']}?includes_parents=true")
            require(all(now.get(k) == prior[k] for k in ("id", "name", "target", "enforcement", "conditions", "rules")),
                "connector_ruleset_changed")
            if "bypass_actors" in now:
                require(now["bypass_actors"] == prior["bypass_actors"], "connector_bypass_changed")
        source_authority(api, p["source_commit"], caller)
        if self.operation != "tag":
            build_authority(api, self.verifier, self.policy, run_id=p["build_run_id"],
                commit=p["source_commit"], tag=p["tag"])
        if self.operation == "finalize":
            stage_id = p["staging_run_id"]
            prior = api.json("GET", f"/actions/runs/{stage_id}")
            require(prior.get("status") == "completed" and prior.get("conclusion") == "success",
                "connector_staging_run_incomplete")
            prior_security = {**security, "run": prior,
                "attempt": api.json("GET", f"/actions/runs/{stage_id}/attempts/1"),
                "workflow": api.json("GET", f"/actions/workflows/{prior['workflow_id']}"),
                "checks": api.json("GET", f"/commits/{prior['head_sha']}/check-runs?check_name=validate&filter=latest&per_page=100", public=True)}
            dispatch_authority(prior_security, self.policy,
                {"run_id": stage_id, "caller_sha": prior["head_sha"]}, self.trust, historical=True)

    def releases(self):
        return Publisher(self.api, self.verifier, self.policy, self.expected["run_id"],
            source_commit=self.expected["caller_sha"]).release_inventory()

    def owned(self):
        rows = [r for r in self.releases() if r["tag_name"] == self.package["tag"]]
        require(len(rows) <= 1, "connector_conflicting_releases")
        return rows[0] if rows else None

    def tag(self):
        require(self.operation == "tag", "connector_operation_boundary")
        self.authority()
        p = self.package
        require(self.api.json("GET", "/git/ref/tags/" + p["tag"], missing=True) is None, "connector_tag_exists")
        require(self.owned() is None, "connector_release_exists")
        self.authority()
        require(self.api.json("GET", "/git/ref/tags/" + p["tag"], missing=True) is None and self.owned() is None,
            "connector_identity_changed")
        try:
            self.api.json("POST", "/git/refs", payload={"ref": "refs/tags/" + p["tag"], "sha": p["source_commit"]})
        except PublicationError:
            # Fresh observation, never an automatic second POST. This result
            # requires owner review and is not permission to tag/stage again.
            source_tag(self.api, p["tag"], p["source_commit"])
            return {"result": "tag_observed_after_ambiguous_write_review_required", **p}
        source_tag(self.api, p["tag"], p["source_commit"])
        return {"result": "tag_created_build_pending", **p}

    def release_identity(self, release, *, draft):
        p = self.package
        release_identity(release, p["tag"], immutable=not draft)
        require(release.get("draft") is draft and release.get("target_commitish") == p["source_commit"]
            and release.get("name") == p["tag"], "connector_release_identity")
        require(not draft or release.get("immutable") is False, "connector_draft_state")
        app_actor(release.get("author"), self.policy)
        source_tag(self.api, p["tag"], p["source_commit"])

    def assets(self, release, files, *, complete):
        self.release_identity(self.api.release_id(release["id"]), draft=release["draft"])
        actual = self.api.assets(release)
        require(actual.keys() == files.keys() if complete else actual.keys() <= files.keys(), "connector_asset_inventory")
        result = {}
        for name, asset in actual.items():
            require(asset.get("name") == name and positive_integer(asset.get("id"))
                and asset.get("url") == f"{API}/releases/assets/{asset['id']}"
                and asset.get("browser_download_url") ==
                    f"https://github.com/benchristian88/atlas-connectors/releases/download/{self.package['tag']}/{name}"
                and asset.get("size") == len(files[name]) and asset.get("state") == "uploaded"
                and asset.get("digest") == "sha256:" + digest(files[name]), "connector_asset_identity")
            app_actor(asset.get("uploader"), self.policy)
            require(self.api.asset_bytes(asset, len(files[name])) == files[name], "connector_asset_bytes")
            result[name] = {"id": asset["id"], "sha256": digest(files[name]), "bytes": len(files[name])}
        inventory(result, complete=complete)
        require(self.api.assets(release) == actual, "connector_assets_changed")
        self.release_identity(self.api.release_id(release["id"]), draft=release["draft"])
        return result

    def authenticate_files(self, files, manifest):
        p = self.package
        require(files.keys() == {filename(manifest), "manifest.json", "index.json", "SHA256SUMS", "package.sigstore.json"},
            "connector_original_inventory")
        raw = files[filename(manifest)]
        require(digest(raw) == p["sha256"]
            and manifest["distribution"]["provenance"]["source_commit"] == p["source_commit"],
            "connector_original_identity")
        validate_package(raw, manifest, p["tag"])
        require(all(files[name] == expected for name, expected in metadata_files(manifest).items()),
            "connector_original_metadata")
        authenticated_bundle(files, manifest, files["package.sigstore.json"], self.verifier,
            tag=p["tag"], commit=p["source_commit"], run_id=p["build_run_id"])

    def stage(self, files, manifest):
        require(self.operation == "stage", "connector_operation_boundary")
        self.authenticate_files(files, manifest)
        self.authority()
        p, release = self.package, self.owned()
        if p["release_id"] is None:
            require(release is None, "connector_release_exists")
            self.authority()
            require(self.owned() is None, "connector_release_exists")
            try:
                release = self.api.json("POST", "/releases", payload={"tag_name": p["tag"],
                    "target_commitish": p["source_commit"], "name": p["tag"], "body": "Authenticated Connector package; catalogue pending.",
                    "draft": True, "prerelease": False, "make_latest": "false"})
            except PublicationError:
                self.owned()  # Observe before the owner can consider resuming.
                raise PublicationError("connector_draft_ambiguous_review_required") from None
        else:
            require(release is not None and release.get("id") == p["release_id"], "connector_resume_identity")
        self.release_identity(release, draft=True)
        approved = self.assets(release, files, complete=False)
        require(approved == p["assets"], "connector_resume_inventory")
        for name, raw in sorted(files.items()):
            if name in approved:
                continue
            self.authority()
            require(self.owned().get("id") == release["id"]
                and self.assets(release, files, complete=False) == approved, "connector_staging_changed")
            try:
                self.api.upload(release, name, raw)
            except PublicationError:
                self.assets(release, files, complete=False)
                raise PublicationError("connector_upload_ambiguous_review_required") from None
            current = self.assets(release, files, complete=False)
            require(current.keys() == approved.keys() | {name}
                and all(current[k] == v for k, v in approved.items()), "connector_staging_changed")
            approved = current
        final = self.assets(release, files, complete=True)
        self.authority()
        require(self.owned().get("id") == release["id"]
            and self.assets(release, files, complete=True) == final, "connector_staging_changed")
        return {"result": "staged_requires_separate_approval", "staging_run_id": self.expected["run_id"],
            **{k: p[k] for k in ("tag", "source_commit", "sha256", "build_run_id", "artifact_id", "artifact_sha256")},
            "release_id": release["id"], "asset_id": final[filename(manifest)]["id"],
            "assets": final, "inventory_sha256": inventory(final)}

    def finalize(self, directory, files, manifest):
        require(self.operation == "finalize", "connector_operation_boundary")
        self.authenticate_files(files, manifest)
        p = self.package
        require(p["staging_run_id"] != self.expected["run_id"], "connector_separate_approval_required")
        approved_asset_inventory(p["assets"], files)
        require(p["assets"][filename(manifest)]["id"] == p["asset_id"], "connector_approved_asset")
        self.authority()
        release = self.owned()
        require(release is not None and release.get("id") == p["release_id"], "connector_approved_release")
        if release.get("draft") is True:
            self.release_identity(release, draft=True)
            require(self.assets(release, files, complete=True) == p["assets"], "connector_approved_inventory")
            self.authority()
            require(self.owned().get("id") == p["release_id"]
                and self.assets(release, files, complete=True) == p["assets"], "connector_approved_inventory")
            try:
                self.api.json("PATCH", f"/releases/{p['release_id']}", payload={"draft": False, "make_latest": "false"})
            except PublicationError:
                # The response may be lost after publication. The independent
                # GET-only verifier decides, and no PATCH is ever repeated here.
                self.api.release_id(p["release_id"])
        result = verify_connector_release.verify(self.read_only(), self.verifier, directory,
            tag=p["tag"], commit=p["source_commit"], expected_digest=p["sha256"], run_id=p["build_run_id"],
            release_id=p["release_id"], asset_id=p["asset_id"], approved_assets=p["assets"])
        return {**result, "inventory_sha256": p["inventory_sha256"], "approval_run_id": self.expected["run_id"],
            "staging_run_id": p["staging_run_id"], "package_tag": p["tag"], "package_sha256": p["sha256"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["authorize", "prepare", "execute"])
    args = parser.parse_args()
    try:
        environ = os.environ
        inputs = inputs_from_env(environ)
        trust, expected = configuration(environ, inputs)
        caller_source, source = ROOT / "publication-source", ROOT / "package-source"
        check_checkouts(caller_source, trust["signer_revision"], expected["caller_sha"])
        policy_raw = read_regular(caller_source / POLICY_PATH, 16384)
        require(parse(read_regular(caller_source / TRUST_PATH, 16384), 16384) == trust,
            "connector_independent_trust_mismatch")
        signed = job_admission(environ, policy_raw, startup=args.command == "authorize")
        if args.command == "authorize":
            return 0
        package = inputs["package"]
        policy = strict_json(policy_raw)
        directory = Path(environ["RUNNER_TEMP"]) / "connector-candidate"
        with package_source(source):
            if args.command == "prepare":
                prepare_candidate(ConnectorGithub(environ.get("GH_READ_TOKEN")), Verifier(), directory,
                    package, inputs["operation"], expected["caller_sha"])
                return 0
            # Rebuild/compare with committed source using trusted S, offline, BEFORE
            # exposing the Publisher key to the mint. Never execute C's tools.
            clean_source(package["source_commit"])
            connector, version = release_connector.selection(package["tag"])
            files, manifest = candidate(directory, tag=package["tag"], commit=package["source_commit"],
                expected_digest=package["sha256"], connector=connector, version=version)
            if inputs["operation"] != "tag":
                bundle = read_regular(directory / "package.sigstore.json", MAX_BUNDLE_BYTES)
                authenticated_bundle(files, manifest, bundle, Verifier(), tag=package["tag"],
                    commit=package["source_commit"], run_id=package["build_run_id"])
                files["package.sigstore.json"] = bundle
            job_admission(environ, policy_raw)
            api = mint_publisher(environ)
            publisher = PackagePublisher(api, Verifier(), inputs, trust, policy, expected,
                reauthorize=lambda: job_admission(environ, policy_raw), read_only=verify_connector_release.ReadOnlyGithub)
            if inputs["operation"] == "tag":
                result = publisher.tag()
            elif inputs["operation"] == "stage":
                result = publisher.stage(files, manifest)
            else:
                result = publisher.finalize(directory, files, manifest)
        result = {**result, "schema": "atlas-connector-package-receipt/v1", "caller_sha": expected["caller_sha"],
            "implementation_sha": trust["signer_revision"], "request_sha256": expected["request_sha256"],
            "admission_sha256": digest(canonical_json(signed))}
        destination = ROOT / "dist/connector-publication"
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "receipt.json").write_bytes(canonical_json(result))
        print(canonical_json(result).decode(), end="")
    except Exception as error:
        # Provider exception text, response bodies and credentials never become output.
        failure = {"schema": "atlas-connector-package-receipt/v1",
            "result": "failed_incomplete_or_ambiguous_read_only_review_required", "command": args.command}
        if isinstance(error, PublicationError):
            # These exceptions carry only application-owned diagnostic constants.
            failure["reason"] = str(error)
        if "expected" in locals():
            failure.update({k: expected[k] for k in ("caller_sha", "run_id", "request_sha256")})
        if "publisher" in locals():
            try:
                observed = publisher.owned()
                if observed is not None:
                    publisher.release_identity(observed, draft=observed["draft"])
                    failure["observed_release_id"] = observed["id"]
                    failure["observed_assets"] = publisher.assets(observed, files, complete=False)
            except Exception:
                failure["observation"] = "unavailable_or_conflicting"
        destination = ROOT / "dist/connector-publication"
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "receipt.json").write_bytes(canonical_json(failure))
        print(failure.get("reason", "connector_publication_failed_read_only_review_required"), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
