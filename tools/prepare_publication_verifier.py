# SPDX-License-Identifier: Apache-2.0
"""Install a hash-pinned public verifier; never run connector code or publish."""
import argparse
import hashlib
import io
import platform
import tarfile
import urllib.parse
import urllib.request
import zipfile

from atlas_connector_sdk.contracts import strict_json
from publication_contract import PublicationError, require
from publication_verify import TRUST, read_regular


class DistributionRedirect(urllib.request.HTTPRedirectHandler):
    """Only GitHub's public release distribution, with no credentials."""
    def __init__(self):
        self.count = 0

    def redirect_request(self, request, response, code, message, headers, destination):
        parsed = urllib.parse.urlsplit(destination)
        require(self.count < 2 and parsed.scheme == "https"
                and parsed.hostname in {"github.com", "release-assets.githubusercontent.com"}
                and parsed.port in {None, 443} and not parsed.username and not parsed.password
                and not parsed.fragment and "\\" not in destination, "verifier_download_redirect")
        self.count += 1
        return super().redirect_request(request, response, code, message, headers, destination)


def install(archive=None):
    lock = strict_json(read_regular(TRUST / "distribution.json", 16384))
    machine = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "amd64"}.get(platform.machine())
    key = platform.system().lower() + "-" + str(machine)
    require(key in lock["platforms"], "unsupported_verifier_platform")
    entry = lock["platforms"][key]
    maximum = 32 * 1024 * 1024
    if archive is None:
        url = "https://github.com/cli/cli/releases/download/v2.102.1/" + entry["archive"]
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), DistributionRedirect())
        with opener.open(url, timeout=30) as response:
            raw = response.read(maximum + 1)
    else:
        raw = read_regular(archive, maximum)
    require(len(raw) <= maximum and hashlib.sha256(raw).hexdigest() == entry["archive_sha256"], "verifier_archive_digest")
    # Read one regular member into memory. Never extract paths from the archive.
    if entry["archive"].endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(raw)) as package:
            members = [m for m in package.infolist() if m.filename.endswith("/bin/gh") or m.filename == "bin/gh"]
            require(len(members) == 1 and 0 < members[0].file_size <= 64 * 1024 * 1024, "verifier_archive_member")
            binary = package.read(members[0])
    else:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as package:
            members = [m for m in package if m.name.endswith("/bin/gh")]
            require(len(members) == 1 and members[0].isfile() and 0 < members[0].size <= 64 * 1024 * 1024, "verifier_archive_member")
            binary = package.extractfile(members[0]).read(64 * 1024 * 1024 + 1)
    require(hashlib.sha256(binary).hexdigest() == entry["binary_sha256"], "verifier_binary_digest")
    directory = TRUST / "bin"
    directory.mkdir(exist_ok=True)
    target = directory / "gh"
    require(not target.is_symlink(), "unsafe_verifier_target")
    if target.exists():
        require(read_regular(target, 64 * 1024 * 1024) == binary, "verifier_already_different")
    else:
        with target.open("xb") as stream:
            stream.write(binary)
    target.chmod(0o555)


if __name__ == "__main__":
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path)
    try:
        install(parser.parse_args().archive)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, (str(error) if isinstance(error, PublicationError) else "verifier_provisioning_failed") + "\n")
