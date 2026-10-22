# SPDX-License-Identifier: Apache-2.0
"""One-time sequence-1 transition using P1 authority, transport and signatures.

No builder or package eligibility path is invoked. Stage and activate require
separate reviewed policy revisions and separate first-attempt manual dispatches.
"""
import re

from publication_contract import (API, AUTHORIZATION_MODE, MAX_BUNDLE_BYTES, PUBLICATION_WORKFLOW,
    REPOSITORY, canonical_json, check_policy, digest, parse_catalogue, parse_pointer,
    pointer_bytes, require)
from publication_verify import read_regular
from publish_catalogue import ROOT, Publisher, Stage, release_identity, source_tag

LEGACY_TAG = "catalogue-v1"
LEGACY_RELEASE_ID = 416561696
LEGACY_ASSETS = {"catalogue.json": 653915685, "catalogue-000001.json": 653915743}
SOURCE = "91dfd86f18d0b59ff977bb1e8a5fef42c5329943"
CATALOGUE_SHA256 = "55533ca67e7e9a14f82961e0a8c34ad78e2596049b3db02fde787494e3975afd"
BUNDLE_SHA256 = "0a404de77a6c47dc2f08e3acecf835a01313e924f6883a4b13d720c57610f72f"
TAG = "catalogue-000001"
NAME = TAG + ".json"
ASSETS = {NAME, "catalogue.sigstore.json", "current.json", "current.sigstore.json"}
OPERATION_ID = digest(canonical_json({"operation": "sequence-1-bootstrap-v1", "source_commit": SOURCE,
                                     "legacy_release_id": LEGACY_RELEASE_ID, "sha256": CATALOGUE_SHA256,
                                     "bundle_sha256": BUNDLE_SHA256}))
RELEASE_BODY = "Atlas sequence-1 bootstrap operation sha256:" + OPERATION_ID
WARNING = "Historical Proxmox 0.2.0 package release is mutable and ineligible for B3 remote installation."


def frozen_source(verifier):
    raw = read_regular(ROOT / "tests/fixtures/official_catalogue/catalogue-000001.json", 10585)
    bundle = read_regular(ROOT / "tests/fixtures/publication/catalogue.sigstore.json", MAX_BUNDLE_BYTES)
    verify_source(verifier, raw, bundle)
    return raw, bundle


def verify_source(verifier, raw, bundle):
    require(len(raw) == 10585 and digest(raw) == CATALOGUE_SHA256, "bootstrap_historical_bytes")
    require(digest(bundle) == BUNDLE_SHA256, "bootstrap_historical_bundle")
    document = parse_catalogue(raw)
    require(document["schema_version"] == "1.0" and document["sequence"] == 1, "bootstrap_historical_schema")
    return verifier.verify(raw, bundle, profile="catalogue", name=NAME, commit=SOURCE)


def local_preflight(policy, verifier):
    """Offline and write-free; disabled configuration is explicitly reported."""
    check_policy(policy, operation="bootstrap", local=True)
    frozen_source(verifier)
    return {"result": "local_preflight", "operation_id": OPERATION_ID,
            "enabled": policy["enabled"], "bootstrap_operation": policy.get("bootstrap_operation", "disabled"),
            "sequence": 1, "sha256": CATALOGUE_SHA256, "catalogue_bytes": 10585,
            "source_commit": SOURCE, "catalogue_attestation_reference": "57152061",
            "remote_checks_performed": False, "legacy_package_warning": WARNING}


class BootstrapPublisher(Publisher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.policy_operation = "bootstrap"

    def inventory(self):
        """List drafts explicitly: get-by-tag is documented for published releases.

        Bounded complete enumeration prevents hidden duplicate drafts or higher
        history from being treated as absence. Overflow blocks, never truncates.
        """
        self.api.bootstrap_absent()
        refs = self.api.json("GET", "/git/matching-refs/tags/catalogue-")
        require(isinstance(refs, list) and len(refs) < 100, "bootstrap_ref_limit")
        allowed = {"refs/tags/" + LEGACY_TAG, "refs/tags/" + TAG}
        require(all(isinstance(r, dict) and r.get("ref") in allowed for r in refs), "bootstrap_historical_ref_conflict")
        releases = []
        for page in range(1, 5):
            rows = self.api.json("GET", f"/releases?per_page=100&page={page}")
            require(isinstance(rows, list) and len(rows) <= 100
                    and all(isinstance(r, dict) and isinstance(r.get("tag_name"), str) for r in rows),
                    "bootstrap_release_evidence")
            releases.extend(rows)
            if len(rows) < 100:
                break
        else:
            require(False, "bootstrap_release_limit")
        require(all(not r["tag_name"].startswith("catalogue-") or r["tag_name"] in {TAG, LEGACY_TAG}
                    for r in releases), "bootstrap_historical_release_conflict")
        matches = [r for r in releases if r["tag_name"] == TAG]
        require(len(matches) <= 1, "bootstrap_duplicate_release")
        release = matches[0] if matches else None
        if release is None:
            require(not any(r["ref"] == "refs/tags/" + TAG for r in refs), "bootstrap_orphan_tag")
        return release

    def legacy(self, raw):
        release = self.api.release(LEGACY_TAG)
        release_identity(release, LEGACY_TAG)
        require(release["id"] == LEGACY_RELEASE_ID and release["draft"] is False, "bootstrap_legacy_release")
        source_tag(self.api, LEGACY_TAG, SOURCE)
        assets = self.api.assets(release)
        for name, identity in LEGACY_ASSETS.items():
            require(name in assets and assets[name]["id"] == identity, "bootstrap_legacy_asset")
            require(self.api.asset_bytes(assets[name], 10585) == raw, "bootstrap_legacy_bytes")

    def inspect(self, release, raw, bundle, *, complete=False, immutable=False):
        release_identity(release, TAG, immutable=immutable)
        require(release.get("target_commitish") == SOURCE and release.get("body") == RELEASE_BODY,
                "bootstrap_release_conflict")
        source_tag(self.api, TAG, SOURCE, allow_missing=release["draft"])
        if not release["draft"]:
            require(release.get("immutable") is True, "release_not_immutable")
        assets = self.api.assets(release)
        require(assets.keys() <= ASSETS and (not complete or assets.keys() == ASSETS), "bootstrap_asset_set")
        require(len({a.get("id") for a in assets.values()}) == len(assets), "bootstrap_duplicate_asset_id")
        expected = {NAME: raw, "catalogue.sigstore.json": bundle}
        pointer = None
        if NAME in assets:
            pointer = pointer_bytes({"schema_version": "1.0", "sequence": 1, "release_tag": TAG,
                "release_id": release["id"], "asset_id": assets[NAME]["id"], "sha256": CATALOGUE_SHA256,
                "previous_pointer_sha256": None})
            expected["current.json"] = pointer
        require("current.json" not in assets or pointer is not None, "bootstrap_pointer_without_snapshot")
        require("current.sigstore.json" not in assets or "current.json" in assets, "bootstrap_bundle_without_pointer")
        for name, value in expected.items():
            if name in assets:
                require(self.api.asset_bytes(assets[name], len(value)) == value, "bootstrap_staged_bytes_changed")
        selection_bundle = None
        if "current.sigstore.json" in assets:
            selection_bundle = self.api.asset_bytes(assets["current.sigstore.json"], MAX_BUNDLE_BYTES)
            self.selection(pointer, selection_bundle)
        if complete:
            verify_source(self.verifier, raw, bundle)
        return Stage(pointer, selection_bundle, release["id"]), assets

    def preflight(self):
        """Phase A: all API operations are GETs; no absence implies normal publish."""
        self.authority()
        raw, bundle = frozen_source(self.verifier)
        self.legacy(raw)
        release = self.inventory()
        mode = self.policy["bootstrap_operation"]
        if release is not None:
            self.inspect(release, raw, bundle, complete=mode == "activate")
            require(mode == "activate" or release["draft"], "bootstrap_finalised_requires_activation")
        require(mode != "activate" or release is not None, "bootstrap_staged_release_required")
        return raw, bundle, release

    def stage_bootstrap(self):
        require(self.policy.get("bootstrap_operation") == "stage", "bootstrap_stage_not_authorized")
        raw, bundle, release = self.preflight()
        self.authority()
        self.api.bootstrap_absent()
        if release is None:
            release = self.api.json("POST", "/releases", payload={"tag_name": TAG, "target_commitish": SOURCE,
                "name": TAG, "body": RELEASE_BODY, "draft": True, "prerelease": False, "make_latest": "false"})
        self.inspect(release, raw, bundle)
        self.api.upload(release, NAME, raw)
        self.api.upload(release, "catalogue.sigstore.json", bundle)
        stage, _ = self.inspect(release, raw, bundle)
        self.api.upload(release, "current.json", stage.pointer)
        self.api.bootstrap_absent()
        return self.inspect(self.api.release_id(release["id"]), raw, bundle)[0]

    def seal_bootstrap(self, pointer, selection_bundle):
        """Complete only the draft. Never finalise in the signing dispatch."""
        stage = self.stage_bootstrap()
        require(pointer == stage.pointer, "bootstrap_pointer_changed")
        self.selection(pointer, selection_bundle)
        bundle = stage.bundle if stage.bundle is not None else selection_bundle
        self.authority()
        self.api.bootstrap_absent()
        self.api.upload(self.api.release_id(stage.release_id), "current.sigstore.json", bundle)
        raw, original = frozen_source(self.verifier)
        stage, assets = self.inspect(self.api.release_id(stage.release_id), raw, original, complete=True)
        self.api.bootstrap_absent()
        return self.receipt("staged_requires_separate_approval", stage, assets)

    def activate_bootstrap(self):
        require(self.policy.get("bootstrap_operation") == "activate", "bootstrap_activation_not_authorized")
        raw, original, release = self.preflight()
        stage, assets = self.inspect(release, raw, original, complete=True)
        require(digest(stage.pointer) == self.policy["bootstrap"]["pointer_sha256"], "bootstrap_approval_mismatch")
        evidence = self.verifier.verify(stage.pointer, stage.bundle, profile="pointer", name="current.json")
        # A reviewed policy commit with the actual digest must follow staging.
        require(evidence.source_commit != self.source_commit
                and evidence.invocation != f"https://github.com/{REPOSITORY}/actions/runs/{self.run_id}/attempts/1",
                "bootstrap_separate_approval_required")
        self.authority()
        observed = self.inventory()
        require(observed is not None and observed["id"] == release["id"], "bootstrap_release_conflict")
        if release["draft"]:
            self.api.json("PATCH", f"/releases/{release['id']}", payload={"draft": False, "make_latest": "false"})
        final, final_assets = self.inspect(self.api.release_id(release["id"]), raw, original,
                                           complete=True, immutable=True)
        require(final == stage and {n: a["id"] for n, a in final_assets.items()} == {n: a["id"] for n, a in assets.items()},
                "bootstrap_finalisation_changed")
        self.authority()
        observed = self.inventory()
        require(observed is not None and observed["id"] == release["id"], "bootstrap_release_conflict")
        revision = self.api.create_root({"current.json": stage.pointer, "current.sigstore.json": stage.bundle},
                                        reauthorize=self.authority)
        # Reauthenticate publication after the ref transaction too.
        accepted, accepted_assets = self.inspect(self.api.release_id(release["id"]), raw, original,
                                                  complete=True, immutable=True)
        require(accepted == final and {n: a["id"] for n, a in accepted_assets.items()}
                == {n: a["id"] for n, a in final_assets.items()}, "bootstrap_finalisation_changed")
        require(self.api.channel() == (revision, {"current.json": stage.pointer, "current.sigstore.json": stage.bundle}),
                "bootstrap_root_conflict")
        return self.receipt("bootstrapped", stage, final_assets, revision=revision)

    def receipt(self, result, stage, assets, *, revision=None):
        evidence = self.verifier.verify(stage.pointer, stage.bundle, profile="pointer", name="current.json")
        match = re.fullmatch(r"https://github.com/" + re.escape(REPOSITORY) + r"/actions/runs/([1-9][0-9]*)/attempts/1",
                             evidence.invocation)
        require(match is not None, "fresh_dispatch_run_required")
        return {"result": result, "operation_id": OPERATION_ID, "sequence": 1, "sha256": CATALOGUE_SHA256,
                "source_commit": SOURCE, "catalogue_signer": ".github/workflows/catalogue.yml@refs/heads/main",
                "catalogue_attestation_reference": "57152061", "catalogue_bundle_sha256": BUNDLE_SHA256,
                "release_id": stage.release_id, "release_tag": TAG, "asset_id": parse_pointer(stage.pointer)["asset_id"],
                "asset_ids": {n: a["id"] for n, a in sorted(assets.items())}, "pointer_sha256": digest(stage.pointer),
                "channel_commit": revision, "selection_signer": PUBLICATION_WORKFLOW + "@refs/heads/main",
                "selection_run_id": int(match[1]), "selection_source_commit": evidence.source_commit,
                "authorization_mode": AUTHORIZATION_MODE, "authorization_run_id": self.run_id,
                "authorization_source_commit": self.source_commit, "allowed_maintainer_id": self.policy["allowed_maintainer_id"],
                "published": revision is not None, "immutable": revision is not None,
                "legacy_package_warning": WARNING, "package_eligibility_granted": False,
                "consumer_independent_verification_required": True}
