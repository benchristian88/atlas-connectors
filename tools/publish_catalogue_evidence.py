# SPDX-License-Identifier: Apache-2.0
"""Successor catalogue publisher candidate, deliberately absent from workflows.

Stage/finish retain S4's ordering and checks and add the durable evidence boundary.
No bootstrap override, enable flag, trust defaults, signing or live CLI is added.
"""
import re
import time

from copy import deepcopy
from atlas_connector_sdk.contracts import strict_json
from publication_authorization import AuthorizationVerifier, MAX_RUN_SECONDS
from publication_contract import (API, MAX_BUNDLE_BYTES, MAX_CATALOGUE_BYTES, check_policy, digest,
    parse_catalogue, parse_pointer, pointer_bytes, pointer_transition, require,
    positive_integer, sequence_transition, snapshot_tag)
from publication_evidence import Archive, ARCHIVE_LIMITS, ArchiveVerifier, verified_times
from publish_catalogue import Publisher, Stage, release_identity, source_tag
from verify_connector_release import app_actor, asset_download_identity


class EvidencePublisher(Publisher):
    def __init__(self, *args, archive, archive_verifier, started_at, clock=time.time, checkpoint=None,
                 persist_checkpoint=None, **kwargs):
        require(type(archive) is Archive and type(archive_verifier) is ArchiveVerifier,
                "archive_verifier_required")
        require(type(started_at) is int and started_at > 0, "archive_job_admission_required")
        self.archive, self.archive_verifier = archive, archive_verifier
        self.started_at, self.clock = started_at, clock
        # Trusted same-job state, never a downloaded release receipt or admission.
        self.checkpoint = deepcopy(checkpoint)
        self.persist_checkpoint = persist_checkpoint
        super().__init__(*args, **kwargs)

    def require_preflight(self):
        # The same runner-local admission as S4; historical checks cannot supply it.
        super().require_preflight()
        require(self.policy_operation in {"publish", "recover"}, "archive_bootstrap_unsupported")
        require(self.archive.policy == self.policy_raw, "archive_live_policy_changed")
        expected = {"source_commit": self.source_commit, "policy_sha256": digest(self.policy_raw),
                    "run_id": self.run_id, "run_attempt": 1,
                    "operation": self.policy_operation, "acceptance_only": False}
        value = AuthorizationVerifier(self.archive_verifier.trust, self.policy_raw).verify(
            self.archive.preflight, self.archive.bundle, expected,
            clock=self.clock, started_at=self.started_at)
        require(value == self.run_preflight, "archive_live_preflight_changed")
        self.archive_verifier.authenticate(self.archive, expected)
        require(0 <= int(self.clock()) - self.started_at <= MAX_RUN_SECONDS, "authorization_not_fresh")

    @staticmethod
    def expected_names(tag):
        return {tag + ".json", "catalogue.sigstore.json", "current.json", "current.sigstore.json",
                *ARCHIVE_LIMITS}

    @staticmethod
    def asset_identities(assets):
        return {name: {key: row.get(key) for key in ("id", "name", "size", "digest")}
                for name, row in assets.items()}

    def checked_assets(self, release, *, exact=False):
        assets = self.api.assets(release)
        expected = self.expected_names(release["tag_name"])
        require(set(assets) == expected if exact else set(assets) <= expected, "archive_release_inventory")
        require(len({a.get("id") for a in assets.values()}) == len(assets), "archive_duplicate_asset_id")
        app_actor(release.get("author"), self.policy)
        limits = {release["tag_name"] + ".json": MAX_CATALOGUE_BYTES,
                  "catalogue.sigstore.json": MAX_BUNDLE_BYTES, "current.json": 1024,
                  "current.sigstore.json": MAX_BUNDLE_BYTES, **ARCHIVE_LIMITS}
        for name, asset in assets.items():
            require(positive_integer(asset.get("id")) and asset.get("name") == name
                    and asset.get("url") == f"{API}/releases/assets/{asset['id']}"
                    and type(asset.get("size")) is int and 0 < asset["size"] <= limits[name]
                    and asset.get("state") == "uploaded", "archive_asset_identity")
            asset_download_identity(asset, release, name=name, tag=release["tag_name"], allow_draft=True)
            app_actor(asset.get("uploader"), self.policy)
        return assets

    def retain_upload(self, release, name, raw):
        asset = self.api.upload(release, name, raw)
        self.checkpoint["assets"][name] = self.asset_identities({name: asset})[name]
        self.save_checkpoint()
        return asset

    def save_checkpoint(self):
        if self.persist_checkpoint is not None:
            self.persist_checkpoint(deepcopy(self.checkpoint))

    def bind_archive(self, release, pointer_raw, bundle, *, published=False, expected_archive=None):
        pointer = parse_pointer(pointer_raw)
        require(pointer["release_id"] == release["id"] and pointer["release_tag"] == release["tag_name"],
                "archive_release_identity")
        assets = self.checked_assets(release, exact=published)
        require(assets.get(pointer["release_tag"] + ".json", {}).get("id") == pointer["asset_id"],
                "archive_selected_asset")
        archive = Archive.from_files((name, self.api.asset_bytes(assets[name], maximum))
            for name, maximum in ARCHIVE_LIMITS.items() if name in assets)
        require(expected_archive is None or archive == expected_archive, "archive_original_changed")
        selection = self.verifier.verify(pointer_raw, bundle, profile="pointer", name="current.json")
        require(selection.sha256 == digest(pointer_raw), "archive_selection_digest")
        require(release.get("target_commitish") == selection.source_commit, "archive_release_source")
        self.selection(pointer_raw, bundle)  # Original latest-run/attempt/actor/CI checks.
        times = verified_times(self.verifier, pointer_raw, bundle, profile="pointer", name="current.json",
                               commit=selection.source_commit)
        result = self.archive_verifier.bind_selection(archive, selection, times,
            published_at=release.get("published_at") if published else None)
        if published:
            require(release.get("published_at") is not None, "archive_publication_time_missing")
        # Independently reread the run timestamps instead of trusting a receipt.
        value = strict_json(archive.preflight)
        run_id = result["run_id"]
        for key, path in (("run", f"/actions/runs/{run_id}"),
                          ("attempt", f"/actions/runs/{run_id}/attempts/1")):
            require(self.api.json("GET", path).get("created_at") == value["security"][key]["created_at"],
                    "archive_run_time_changed")
        catalogue_name = pointer["release_tag"] + ".json"
        raw = self.api.asset_bytes(assets[catalogue_name], MAX_CATALOGUE_BYTES)
        require(digest(raw) == pointer["sha256"] and parse_catalogue(raw)["sequence"] == pointer["sequence"],
                "archive_catalogue_digest")
        self.verifier.verify(raw, self.api.asset_bytes(assets["catalogue.sigstore.json"], MAX_BUNDLE_BYTES),
            profile="catalogue", name=catalogue_name, commit=selection.source_commit)
        require(self.api.assets(release) == assets, "archive_assets_changed")
        return result

    def snapshot(self, pointer):
        raw = super().snapshot(pointer)
        release = self.api.release_id(pointer["release_id"])
        assets = self.api.assets(release)
        if pointer["sequence"] == 1:
            # Existing root keeps its exact four assets and bootstrap pin checks.
            require(set(assets) == {pointer["release_tag"] + ".json", "catalogue.sigstore.json",
                                   "current.json", "current.sigstore.json"}, "bootstrap_asset_inventory")
            return raw
        by_tag = self.api.release(pointer["release_tag"])
        require(isinstance(by_tag, dict) and all(by_tag.get(key) == release.get(key) for key in
                ("id", "tag_name", "url", "target_commitish", "draft", "prerelease", "immutable",
                 "author", "published_at", "assets_url", "html_url")), "archive_release_identity")
        pointer_raw = self.api.asset_bytes(assets["current.json"], 1024) if "current.json" in assets else b""
        require(parse_pointer(pointer_raw) == pointer, "archive_original_selection")
        bundle = self.api.asset_bytes(assets["current.sigstore.json"], MAX_BUNDLE_BYTES) if "current.sigstore.json" in assets else b""
        self.bind_archive(release, pointer_raw, bundle, published=True)
        require(self.api.release_id(release["id"]) == release, "archive_release_changed")
        return raw

    def stage(self, raw):
        check_policy(self.policy)
        require(self.policy_operation == "publish", "preflight_operation_mismatch")
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
        inventory = self.release_inventory()
        catalogue_releases = [r for r in inventory if re.fullmatch(r"catalogue-[0-9]{6,16}", r["tag_name"])]
        require(not any(r["tag_name"] != tag and int(r["tag_name"][10:]) >= 2
                and r.get("target_commitish") == authority.source_commit for r in catalogue_releases),
                "archive_one_selection_per_source")
        require(not any(int(r["tag_name"][10:]) > candidate["sequence"] for r in catalogue_releases),
                "higher_snapshot_exists")
        matches = [r for r in catalogue_releases if r["tag_name"] == tag]
        require(len(matches) <= 1, "duplicate_snapshot_draft")
        require(self.api.channel()[0] == head, "channel_changed")
        source_tag(self.api, tag, authority.source_commit, allow_missing=True)
        release = matches[0] if matches else None
        created = release is None
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
        assets = self.checked_assets(release)
        # A surviving preflight is the draft's original run anchor. An existing
        # empty/orphan draft has no independently recoverable authorization.
        require(created or "preflight.json" in assets, "archive_original_missing")
        if created:
            self.checkpoint = {"release_id": release["id"], "assets": {}}
            self.save_checkpoint()
        require(isinstance(self.checkpoint, dict) and self.checkpoint.keys() == {"release_id", "assets"}
                and self.checkpoint["release_id"] == release["id"]
                and self.checkpoint["assets"] == self.asset_identities(assets), "archive_checkpoint_mismatch")
        for evidence_name, evidence_raw in self.archive.files().items():
            if evidence_name in assets:
                require(self.api.asset_bytes(assets[evidence_name], len(evidence_raw)) == evidence_raw,
                        "archive_original_changed")
        for evidence_name, evidence_raw in self.archive.files().items():
            self.retain_upload(release, evidence_name, evidence_raw)
        asset = self.retain_upload(release, name, raw)
        # Reuse a genuine matching bundle; re-signing identical bytes is not a
        # reason to overwrite or reject already-authenticated historical evidence.
        assets = self.api.assets(release)
        if "catalogue.sigstore.json" in assets:
            original = self.api.asset_bytes(assets["catalogue.sigstore.json"], MAX_BUNDLE_BYTES)
            self.verifier.verify(raw, original, profile="catalogue", name=name, commit=authority.source_commit)
        else:
            self.retain_upload(release, "catalogue.sigstore.json", catalogue_bundle)
        pointer = pointer_bytes({"schema_version": "1.0", "sequence": candidate["sequence"], "release_tag": tag,
            "release_id": release["id"], "asset_id": asset["id"], "sha256": digest(raw),
            "previous_pointer_sha256": digest(previous_files["current.json"])})
        pointer_transition(previous_files["current.json"], pointer)
        self.retain_upload(release, "current.json", pointer)
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
        # Authenticate the actual surviving bundle before upload or locking.
        self.bind_archive(release, pointer_raw, bundle, expected_archive=self.archive)
        self.retain_upload(release, "current.sigstore.json", bundle)
        authenticated = self.bind_archive(release, pointer_raw, bundle, expected_archive=self.archive)
        staged_assets = self.checked_assets(release, exact=True)
        staged_identity = self.asset_identities(staged_assets)
        self.authority()  # Detect a new main commit / policy change before finalisation.
        require(self.api.channel()[0] == head, "channel_changed")
        if release["draft"]:
            source_tag(self.api, pointer["release_tag"], release["target_commitish"], allow_missing=True)
            # Last local admission check, after every provider read/signature
            # check. Expired or nearly exhausted authority never starts PATCH.
            self.archive_verifier.require_finalization_window(authenticated, now=self.clock())
            self.api.json("PATCH", f"/releases/{stage.release_id}", payload={"draft": False, "make_latest": "false"})
        # The actual provider flag and exact IDs/bytes, not the tag name, prove
        # the GitHub publication boundary. Failure leaves current untouched.
        require(self.snapshot(pointer) == raw, "published_snapshot_changed")
        published = self.api.release_id(stage.release_id)
        assets = self.api.assets(published)
        files = {"current.json": pointer_raw, "current.sigstore.json": bundle}
        require(self.asset_identities(self.checked_assets(published, exact=True)) == staged_identity,
                "published_asset_identity_changed")
        for name, value in files.items():
            require(self.api.asset_bytes(assets[name], len(value)) == value, "published_selection_changed")
        self.selection(pointer_raw, bundle)
        self.authority()  # Recheck current protections before selecting the locked snapshot.
        require(self.api.channel()[0] == head, "channel_changed")
        revision = self.api.compare_and_swap(head, files)
        return {"result": "published", "sequence": pointer["sequence"], "release_id": pointer["release_id"],
                "asset_id": pointer["asset_id"], "sha256": pointer["sha256"], "channel_commit": revision}
