# SPDX-License-Identifier: Apache-2.0
"""Select an explicitly packaged, qualified Connector by exact tag/Manifest identity."""
import os

from atlas_connector_sdk.contracts import strict_json
from build_bundle import ROOT, build, recipe


def select(tag):
    matches = []
    for source in sorted((ROOT / "connectors").iterdir()):
        if source.is_symlink() or not source.is_dir() or not (source / "package.json").is_file():
            continue
        recipe(source.name)
        manifest = strict_json((source / "manifest.json").read_bytes())
        if tag != f"{source.name}-v{manifest['version']}":
            continue
        if (manifest["id"] != source.name or manifest.get("source_versions", {}).get("qualification") != "qualified"
                or not manifest["source_versions"].get("qualified_versions")):
            raise ValueError("release_requires_recorded_qualification")
        matches.append(source.name)
    if len(matches) != 1:
        raise ValueError("tag_has_no_unique_qualified_connector")
    return matches[0]


if __name__ == "__main__":
    connector = select(os.environ["RELEASE_TAG"])
    build(connector=connector, output=ROOT / "dist/release")
    print("Prepared qualified Connector: " + connector)
