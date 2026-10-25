# SPDX-License-Identifier: Apache-2.0
"""Select an explicitly packaged, qualified Connector by exact tag/Manifest identity."""
import os
import argparse
from pathlib import Path
import subprocess

from atlas_connector_sdk.contracts import strict_json
from build_bundle import ROOT, build, recipe, source_bytes
from connector_release import clean_source, retain_bundle, validate_package
from publication_contract import OWNER_ID, REPOSITORY, REPOSITORY_ID, PublicationError, require
from publication_verify import Verifier


def selection(tag):
    matches = []
    for source in sorted((ROOT / "connectors").iterdir()):
        if source.is_symlink() or not source.is_dir() or not (source / "package.json").is_file():
            continue
        _, package = recipe(source.name)
        for version in (None, *package.get("release_overrides", {})):
            metadata = source if version is None else source / "releases" / version
            manifest = strict_json(source_bytes(metadata, "manifest.json"))
            if tag != f"{source.name}-v{manifest['version']}":
                continue
            if (manifest["id"] != source.name or version is not None and manifest["version"] != version
                    or manifest.get("source_versions", {}).get("qualification") != "qualified"
                    or not manifest["source_versions"].get("qualified_versions")):
                raise ValueError("release_requires_recorded_qualification")
            matches.append((source.name, version))
    if len(matches) != 1:
        raise ValueError("tag_has_no_unique_qualified_connector")
    return matches[0]


def select(tag):
    return selection(tag)[0]


def prepare(tag, output, *, commit=None):
    if commit is not None:
        clean_source(commit)
    connector, version = selection(tag)
    raw, manifest = build(connector=connector, version=version)
    require(not (ROOT / "catalogue/releases" / f"{connector}-{manifest['version']}.json").exists(),
            "release_identity_already_registered")
    validate_package(raw, manifest, tag)
    # Check every consumed file is committed, including ignored-path injection.
    if commit is not None:
        source, package = recipe(connector)
        overrides = set(package.get("release_overrides", {}).get(version, []))
        paths = ["LICENSE", str((source / "package.json").relative_to(ROOT))]
        for name in package["files"]:
            path = source / "releases" / version / name if name in overrides else source / name
            paths.append(str(path.relative_to(ROOT)))
        subprocess.check_output(["git", "ls-files", "--error-unmatch", "--", *paths], cwd=ROOT, stderr=subprocess.DEVNULL)
    require(not output.is_symlink()
            and (not output.exists() or output.is_dir() and not any(output.iterdir())), "release_output_must_be_empty")
    build(connector=connector, version=version, output=output)
    return manifest


def workflow_context(environ, tag):
    policy = strict_json((ROOT / "catalogue/publication/policy.json").read_bytes())
    expected = {"GITHUB_REPOSITORY": REPOSITORY, "GITHUB_REPOSITORY_ID": str(REPOSITORY_ID),
        "GITHUB_REPOSITORY_OWNER_ID": str(OWNER_ID), "GITHUB_EVENT_NAME": "push",
        "GITHUB_RUN_ATTEMPT": "1", "GITHUB_REF": "refs/tags/" + tag,
        "GITHUB_WORKFLOW_REF": REPOSITORY + "/.github/workflows/release.yml@refs/tags/" + tag,
        "RUNNER_ENVIRONMENT": "github-hosted", "GITHUB_ACTOR_ID": str(policy["app_bot_user_id"]),
        "GITHUB_ACTOR": policy["app_slug"] + "[bot]", "GITHUB_TRIGGERING_ACTOR": policy["app_slug"] + "[bot]"}
    require(all(environ.get(k) == v for k, v in expected.items()), "release_workflow_context")
    commit = environ.get("GITHUB_SHA")
    clean_source(commit)
    require(subprocess.check_output(["git", "rev-parse", "refs/tags/" + tag + "^{commit}"],
                                    cwd=ROOT, text=True).strip() == commit, "release_tag_source")
    return commit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default=os.getenv("RELEASE_TAG"))
    parser.add_argument("--output", type=Path, default=ROOT / "dist/release")
    parser.add_argument("--local", action="store_true", help="Unattested local preparation; never publication evidence")
    parser.add_argument("--retain-bundle", type=Path, help="Authenticate and retain the existing actions/attest output")
    args = parser.parse_args()
    try:
        require(isinstance(args.tag, str) and bool(args.tag), "release_tag_required")
        if args.local:
            require(args.retain_bundle is None, "release_local_cannot_attest")
            manifest = prepare(args.tag, args.output)
            print("LOCAL UNATTESTED " + manifest["distribution"]["bundle_digest"])
        else:
            commit = workflow_context(os.environ, args.tag)
            if args.retain_bundle is None:
                manifest = prepare(args.tag, args.output, commit=commit)
                print(manifest["distribution"]["bundle_digest"])
            else:
                connector, version = selection(args.tag)
                _, manifest = build(connector, version=version)
                retain_bundle(args.output, args.retain_bundle, tag=args.tag, commit=commit,
                    expected_digest=manifest["distribution"]["bundle_digest"][7:], connector=connector, version=version,
                    run_id=int(os.environ["GITHUB_RUN_ID"]), verifier=Verifier())
                print("Retained authenticated package build bundle; publication requires separate authorization")
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        parser.exit(1, (str(error) if isinstance(error, PublicationError) else "release_preparation_failed") + "\n")


if __name__ == "__main__":
    main()
