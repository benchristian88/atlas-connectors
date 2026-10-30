# SPDX-License-Identifier: Apache-2.0
"""Independently verify a published package. GET-only; never publication authority."""
import argparse
from pathlib import Path
import re

from atlas_connector_sdk.contracts import strict_json
from connector_publication_github import ConnectorGithub
from connector_release import (authenticated_bundle, candidate, clean_source, filename)
from publication_contract import (API, APP_PERMISSIONS, MAX_BUNDLE_BYTES, OWNER_ID, REPOSITORY, PublicationError,
                                  canonical_json, digest, hexadecimal, positive_integer, require)
from publication_verify import Verifier, read_regular
from publish_catalogue import Publisher, release_identity, source_tag
from release_connector import ROOT, selection


class ReadOnlyGithub(ConnectorGithub):
    def __init__(self):
        # Anonymous public observation only. No ambient token/config fallback.
        super().__init__()

    def request(self, method, path, **kwargs):
        require(method == "GET" and kwargs.get("payload") is None and kwargs.get("binary") is None,
                "release_verifier_is_read_only")
        return super().request(method, path, **kwargs)


def app_actor(value, policy):
    require(isinstance(value, dict) and type(value.get("id")) is int
            and value["id"] == policy["app_bot_user_id"] and value.get("type") == "Bot"
            and value.get("login") == policy["app_slug"] + "[bot]", "release_unauthorized_actor")


def asset_download_identity(asset, release, *, name, tag, allow_draft=False):
    """Validate display URLs; downloads always use the fixed numeric REST route.

    A draft's opaque selector is authoritative only in metadata independently
    fetched from /releases/{approved_id} in the authenticated official repository.
    Never learn it from an asset URL, or use it as published-release authority.
    """
    require(type(name) is str and re.fullmatch(r"[A-Za-z0-9._-]{1,128}", name)
        and type(tag) is str and re.fullmatch(r"[a-z][a-z0-9._-]{0,127}", tag), "connector_asset_identity")
    require(positive_integer(release.get("id")) and release.get("url") == f"{API}/releases/{release['id']}"
        and release.get("tag_name") == tag and type(release.get("draft")) is bool, "connector_release_identity")
    origin = "https://github.com/" + REPOSITORY + "/releases/"
    selector = tag
    if release["draft"]:
        require(allow_draft is True, "release_not_immutable")
        require(release.get("assets_url") == f"{API}/releases/{release['id']}/assets", "connector_draft_url_identity")
        html = release.get("html_url")
        require(type(html) is str and (html == origin + "tag/" + tag
            or re.fullmatch(re.escape(origin + "tag/untagged-") + r"[a-f0-9]{8,64}", html)),
            "connector_draft_url_identity")
        selector = html.removeprefix(origin + "tag/")
    expected = {origin + "download/" + tag + "/" + name}
    if release["draft"]:
        expected.add(origin + "download/" + selector + "/" + name)
    require(asset.get("browser_download_url") in expected, "connector_asset_download_url")


def published_identity(release, *, tag, commit, release_id, policy):
    release_identity(release, tag, immutable=True)
    require(release["id"] == release_id and release.get("target_commitish") == commit, "release_expected_identity")
    app_actor(release.get("author"), policy)


def verify_build(api, verifier, directory, *, tag, commit, expected_digest, run_id):
    require(positive_integer(run_id), "release_expected_ids")
    clean_source(commit)
    connector, version = selection(tag)
    files, manifest = candidate(directory, tag=tag, commit=commit, expected_digest=expected_digest,
                                connector=connector, version=version)
    bundle = read_regular(directory / "package.sigstore.json", MAX_BUNDLE_BYTES)
    evidence = authenticated_bundle(files, manifest, bundle, verifier, tag=tag, commit=commit, run_id=run_id)
    policy = strict_json((ROOT / "catalogue/publication/policy.json").read_bytes())
    build_authority(api, verifier, policy, run_id=run_id, commit=commit, tag=tag)
    return {**files, "package.sigstore.json": bundle}, manifest, evidence, policy


def build_authority(api, verifier, policy, *, run_id, commit, tag):
    # Reuse existing package authority rules, without calling any Publisher mutation,
    # catalogue authority, preflight, selection or history transition.
    Publisher(api, verifier, policy, run_id, source_commit=commit).run_authority(
        run_id, commit, historical=True, package_tag=tag)
    for suffix in ("", "/attempts/1"):
        run = api.json("GET", f"/actions/runs/{run_id}" + suffix)
        require(run.get("status") == "completed" and run.get("conclusion") == "success"
                and type(run.get("run_attempt")) is int and run["run_attempt"] == 1, "release_build_not_successful")
    comparison = api.json("GET", f"/compare/{commit}...main")
    require(comparison.get("status") in {"ahead", "identical"}
            and comparison.get("merge_base_commit", {}).get("sha") == commit, "package_unreviewed_source")
    app = api.json("GET", "/apps/" + policy["app_slug"], api_global=True)
    require(app.get("id") == policy["app_id"] and app.get("slug") == policy["app_slug"]
            and app.get("owner", {}).get("id") == OWNER_ID and app.get("permissions") == APP_PERMISSIONS,
            "release_app_registration")
    source_tag(api, tag, commit)


def approved_asset_inventory(approved, files):
    """Explicit operator input, independent of the final provider observation.

    This records approval of staged identities; it is not a signed authorization
    or a provider receipt. Never construct it from the release being verified.
    """
    require(isinstance(approved, dict) and approved.keys() == files.keys(), "release_approved_asset_inventory")
    for name, expected in files.items():
        asset = approved[name]
        require(isinstance(asset, dict) and asset.keys() == {"id", "sha256", "bytes"}
                and positive_integer(asset.get("id")) and hexadecimal(asset.get("sha256"))
                and type(asset.get("bytes")) is int and asset["bytes"] == len(expected)
                and asset["sha256"] == digest(expected), "release_approved_asset_identity")
    require(len({a["id"] for a in approved.values()}) == len(files), "release_approved_asset_inventory")


def verify(api, verifier, directory, *, tag, commit, expected_digest, run_id, release_id, asset_id, approved_assets):
    require(all(positive_integer(v) for v in (release_id, asset_id)), "release_expected_ids")
    files, manifest, evidence, policy = verify_build(api, verifier, directory, tag=tag, commit=commit,
        expected_digest=expected_digest, run_id=run_id)
    approved_asset_inventory(approved_assets, files)
    require(approved_assets[filename(manifest)]["id"] == asset_id, "release_approved_asset_identity")
    release = api.release_id(release_id)
    published_identity(release, tag=tag, commit=commit, release_id=release_id, policy=policy)
    by_tag = api.release(tag)
    published_identity(by_tag, tag=tag, commit=commit, release_id=release_id, policy=policy)
    source_tag(api, tag, commit)
    assets = api.assets(release)
    require(assets.keys() == files.keys() and len({a.get("id") for a in assets.values()}) == len(files),
            "release_asset_inventory")
    require(assets[filename(manifest)].get("id") == asset_id, "release_expected_asset")
    receipt = {}
    for name, expected in files.items():
        asset = assets[name]
        require(asset.get("id") == approved_assets[name]["id"], "release_approved_asset_identity")
        require(positive_integer(asset.get("id")) and asset.get("name") == name
                and asset.get("url") == f"{API}/releases/assets/{asset['id']}"
                and asset.get("browser_download_url") == manifest["distribution"]["asset_uri"].rsplit("/", 1)[0] + "/" + name,
                "release_asset_identity")
        asset_download_identity(asset, release, name=name, tag=tag)
        app_actor(asset.get("uploader"), policy)
        require(asset.get("state") == "uploaded" and asset.get("size") == len(expected)
                and asset.get("digest") == "sha256:" + digest(expected)
                and api.asset_bytes(asset, len(expected)) == expected, "release_asset_bytes")
        receipt[name] = {"id": asset["id"], "sha256": digest(expected), "bytes": len(expected)}
    # Re-read provider state after downloads. An interruption, partial release or
    # contradictory observation produces no receipt and never triggers a repair.
    published_identity(api.release_id(release_id), tag=tag, commit=commit, release_id=release_id, policy=policy)
    published_identity(api.release(tag), tag=tag, commit=commit, release_id=release_id, policy=policy)
    require(api.assets(release) == assets, "release_assets_changed")
    build_authority(api, verifier, policy, run_id=run_id, commit=commit, tag=tag)
    entry = {"status": "active", "release_tag": tag, "release_asset_id": asset_id, "manifest": manifest}
    return {"result": "immutable_package_verified_catalogue_pending", "release_id": release_id,
            "immutable": True, "source_commit": commit, "build_invocation": evidence.invocation,
            "assets": receipt, "registry_entry": entry}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--expected-digest", required=True, help="Reviewed SHA-256 hex, without prefix")
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--candidate-only", action="store_true", help="Verify build before operator publication; grants no publication authority")
    parser.add_argument("--release-id", type=int)
    parser.add_argument("--asset-id", type=int)
    parser.add_argument("--approved-assets", type=Path,
                        help="Required for published verification: separately approved staged name/id/sha256/bytes JSON inventory")
    args = parser.parse_args()
    try:
        context = {"tag": args.tag, "commit": args.source_commit, "expected_digest": args.expected_digest,
                   "run_id": args.run_id}
        if args.candidate_only:
            require(args.release_id is args.asset_id is args.approved_assets is None, "release_conflicting_verification_mode")
            _, manifest, evidence, _ = verify_build(ReadOnlyGithub(), Verifier(), args.directory, **context)
            result = {"result": "authenticated_build_candidate_not_publication_authority",
                      "manifest": manifest, "build_invocation": evidence.invocation}
        else:
            require(args.approved_assets is not None, "release_approved_asset_inventory_required")
            approved_assets = strict_json(read_regular(args.approved_assets, 256 * 1024))
            result = verify(ReadOnlyGithub(), Verifier(), args.directory, **context,
                            release_id=args.release_id, asset_id=args.asset_id, approved_assets=approved_assets)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, (str(error) if isinstance(error, PublicationError) else "release_verification_failed") + "\n")
    print(canonical_json(result).decode(), end="")


if __name__ == "__main__":
    main()
