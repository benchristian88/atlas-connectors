# SPDX-License-Identifier: Apache-2.0
"""Narrow package transport extensions; ambiguous writes are never retried."""
import base64
import io
import json
import re
import stat
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

from atlas_connector_sdk.contracts import strict_json
from connector_publication_contract import ARTIFACT_NAME
from publication_contract import (API, APP_PERMISSIONS, OWNER_ID, REPOSITORY_ID, PublicationError, canonical_json,
    check_repository, digest, positive_integer, require)
from publication_github import Github, NoRedirect, _http_failure
from verification_github import credential

MAX_ZIP = 24 * 1024 * 1024


def publisher_jwt(private_key):
    """Same bounded OpenSSL pattern as the Verifier, with the Publisher issuer.

    The frozen verifier helper hardcodes its own App ID and cannot sign for this
    separate identity. Never patch its module globals or share either credential.
    """
    encode = lambda raw: base64.urlsafe_b64encode(raw).rstrip(b"=")
    now = int(time.time())
    message = encode(b'{"alg":"RS256","typ":"JWT"}') + b"." + encode(json.dumps({
        "iss": "5422372", "iat": now - 60, "exp": now + 300}).encode())
    with tempfile.NamedTemporaryFile() as key:
        key.write(private_key.encode())
        key.flush()
        signature = subprocess.run(["/usr/bin/openssl", "dgst", "-sha256", "-sign", key.name],
            input=message, capture_output=True, check=True, timeout=10,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}).stdout
    return (message + b"." + encode(signature)).decode("ascii")


def unpack_artifact(raw, names):
    """No filesystem extraction, duplicate normalization or unbounded decompression."""
    require(type(raw) is bytes and 0 < len(raw) <= MAX_ZIP, "connector_artifact_limit")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = archive.infolist()
            require(len(members) == 5 and {m.filename for m in members} == names, "connector_artifact_inventory")
            files, total = {}, 0
            for member in members:
                mode = member.external_attr >> 16
                require(not member.is_dir() and member.flag_bits & 1 == 0
                    and stat.S_IFMT(mode) in {0, stat.S_IFREG}
                    and member.compress_type in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                    and 0 < member.file_size <= 20 * 1024 * 1024, "connector_artifact_member")
                total += member.file_size
                require(total <= MAX_ZIP, "connector_artifact_expansion")
                with archive.open(member) as source:
                    data = source.read(member.file_size + 1)
                    require(len(data) == member.file_size, "connector_artifact_size")
                files[member.filename] = data
            return files
    except (zipfile.BadZipFile, RuntimeError, OSError, NotImplementedError):
        require(False, "connector_artifact_invalid")


class ConnectorGithub(Github):
    def request(self, method, path, **kwargs):
        if not kwargs.get("asset"):
            return super().request(method, path, **kwargs)
        require(method == "GET" and type(path) is str and re.fullmatch(r"/releases/assets/[1-9][0-9]*", path)
            and set(kwargs) <= {"asset", "maximum"}, "connector_asset_endpoint")
        maximum = kwargs.get("maximum", 1024 * 1024)
        require(type(maximum) is int and 0 < maximum <= MAX_ZIP, "connector_asset_limit")
        headers = {"Accept": "application/octet-stream", "X-GitHub-Api-Version": "2022-11-28",
            "Accept-Encoding": "identity"}
        if self.token:
            headers["Authorization"] = "Bearer " + credential(self.token)
        try:
            require(time.monotonic() < self.deadline, "github_deadline")
            try:
                response = self.opener.open(urllib.request.Request(API + path, headers=headers), timeout=20)
            except urllib.error.HTTPError as error:
                if error.code != 302:
                    _http_failure(method, path, "repository", error.code, error.headers)
                    require(False, "github_request_failed")
                destination = error.headers.get("Location", "")
                require(type(destination) is str and len(destination) <= 16384
                    and not any(c.isspace() or ord(c) < 32 for c in destination) and "\\" not in destination,
                    "github_redirect")
                parsed = urllib.parse.urlsplit(destination)
                require(parsed.scheme == "https" and parsed.netloc == "release-assets.githubusercontent.com"
                    and not parsed.fragment and re.fullmatch(
                        rf"/github-production-release-asset/{REPOSITORY_ID}/[a-f0-9]{{8}}(?:-[a-f0-9]{{4}}){{3}}-[a-f0-9]{{12}}",
                        parsed.path), "github_redirect")
                # The numeric API request authenticates this one redirect. Require
                # the official distribution host and repository path as well.
                # A fresh request has no bearer/cookie and cannot redirect again.
                response = self.opener.open(urllib.request.Request(destination,
                    headers={"Accept-Encoding": "identity"}), timeout=20)
            with response:
                require(response.status == 200 and response.headers.get("Content-Encoding", "identity") == "identity",
                    "github_status")
                lengths = response.headers.get_all("Content-Length")
                require(lengths is None or len(lengths) == 1 and lengths[0].isascii()
                    and lengths[0].isdigit() and int(lengths[0]) <= maximum, "github_response_limit")
                raw = bytearray()
                while True:
                    require(time.monotonic() < self.deadline, "github_deadline")
                    chunk = response.read(min(65536, maximum + 1 - len(raw)))
                    if not chunk:
                        break
                    raw.extend(chunk)
                    require(len(raw) <= maximum, "github_response_limit")
                require(lengths is None or len(raw) == int(lengths[0]), "github_truncated_response")
                return bytes(raw)
        except (urllib.error.URLError, OSError, TimeoutError, ValueError) as error:
            # Preserve our own diagnostic constants; never propagate provider text.
            if isinstance(error, PublicationError):
                raise
            require(False, "github_transport_failure")

    def artifact(self, package):
        run, identity = package["build_run_id"], package["artifact_id"]
        rows = self.json("GET", f"/actions/runs/{run}/artifacts?per_page=100&page=1")
        require(type(rows.get("total_count")) is int and 0 < rows["total_count"] < 100
            and isinstance(rows.get("artifacts"), list) and len(rows["artifacts"]) == rows["total_count"],
            "connector_artifact_listing")
        matches = [r for r in rows["artifacts"] if r.get("name") == ARTIFACT_NAME]
        require(len(matches) == 1 and matches[0].get("id") == identity, "connector_artifact_identity")
        detail = self.json("GET", f"/actions/artifacts/{identity}")
        require(positive_integer(detail.get("id")) and detail == matches[0] and detail.get("expired") is False
            and detail.get("url") == f"{API}/actions/artifacts/{identity}"
            and detail.get("archive_download_url") == f"{API}/actions/artifacts/{identity}/zip"
            and detail.get("digest") == "sha256:" + package["artifact_sha256"], "connector_artifact_identity")
        origin = detail.get("workflow_run", {})
        require(positive_integer(origin.get("id")) and origin.get("id") == run and origin.get("repository_id") == REPOSITORY_ID
            and origin.get("head_repository_id") == REPOSITORY_ID
            and origin.get("head_sha") == package["source_commit"]
            and origin.get("head_branch") == package["tag"], "connector_artifact_run")
        size = detail.get("size_in_bytes")
        require(type(size) is int and 0 < size <= MAX_ZIP, "connector_artifact_limit")
        raw = self.artifact_zip(identity, size)
        require(len(raw) == size and digest(raw) == package["artifact_sha256"], "connector_artifact_digest")
        require(self.json("GET", f"/actions/artifacts/{identity}") == detail, "connector_artifact_changed")
        return raw

    def artifact_zip(self, identity, size):
        require(positive_integer(identity) and type(size) is int and 0 < size <= MAX_ZIP,
            "connector_artifact_identity")
        headers = {"Accept": "application/vnd.github+json", "Authorization": "Bearer " + credential(self.token),
            "X-GitHub-Api-Version": "2022-11-28", "Accept-Encoding": "identity"}
        try:
            try:
                response = self.opener.open(urllib.request.Request(f"{API}/actions/artifacts/{identity}/zip",
                    headers=headers), timeout=20)
            except urllib.error.HTTPError as error:
                require(error.code == 302, "connector_artifact_redirect")
                destination = error.headers.get("Location", "")
                parsed = urllib.parse.urlsplit(destination)
                host = parsed.hostname or ""
                require(parsed.scheme == "https" and parsed.port in {None, 443}
                    and not parsed.username and not parsed.password and not parsed.fragment
                    and "\\" not in destination and not any(c in destination for c in "\r\n")
                    and (host.endswith(".blob.core.windows.net") or host.endswith(".actions.githubusercontent.com")),
                    "connector_artifact_redirect")
                # No Authorization, cookies, ambient proxies or further redirects.
                response = self.opener.open(urllib.request.Request(destination,
                    headers={"Accept-Encoding": "identity"}), timeout=20)
            with response:
                require(response.status == 200 and response.headers.get("Content-Encoding", "identity") == "identity",
                    "connector_artifact_response")
                length = response.headers.get("Content-Length")
                require(length is None or length == str(size), "connector_artifact_size")
                raw = bytearray()
                while True:
                    require(time.monotonic() < self.deadline, "github_deadline")
                    chunk = response.read(min(65536, size + 1 - len(raw)))
                    if not chunk:
                        break
                    raw.extend(chunk)
                    require(len(raw) <= size, "connector_artifact_limit")
                require(len(raw) == size, "connector_artifact_size")
                return bytes(raw)
        except (urllib.error.URLError, OSError, TimeoutError):
            require(False, "connector_artifact_transport_failed")


class PublisherAuthentication:
    """App JWT stays local. Only the one approved installation mint can POST."""
    def __init__(self):
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def json(self, path, token, *, mint=False):
        require(path == "/app/installations/174027755/access_tokens" if mint else path in {
            "/app", "/app/installations/174027755"}, "connector_publisher_auth_endpoint")
        headers = {"Authorization": "Bearer " + credential(token), "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "Accept-Encoding": "identity"}
        data = canonical_json({"repository_ids": [REPOSITORY_ID], "permissions": APP_PERMISSIONS}) if mint else None
        if mint:
            headers["Content-Type"] = "application/json"
        try:
            with self.opener.open(urllib.request.Request("https://api.github.com" + path,
                    headers=headers, data=data, method="POST" if mint else "GET"), timeout=20) as response:
                require(response.status == (201 if mint else 200)
                    and response.headers.get_content_type() == "application/json"
                    and response.headers.get("Content-Encoding", "identity") == "identity"
                    and response.headers.get_all("Link") is None, "connector_publisher_auth_response")
                lengths = response.headers.get_all("Content-Length")
                require(lengths is None or len(lengths) == 1 and lengths[0].isascii()
                    and lengths[0].isdigit() and int(lengths[0]) <= 262144, "connector_publisher_auth_limit")
                raw = response.read(262145)
                require(len(raw) <= 262144 and (lengths is None or len(raw) == int(lengths[0])),
                    "connector_publisher_auth_limit")
                return strict_json(raw, maximum=262144)
        except Exception:
            require(False, "connector_publisher_auth_failed")


def mint_publisher(environ, *, auth=None, client=ConnectorGithub):
    require(environ.get("PUBLICATION_APP_ID") == "5422372", "connector_publisher_configuration")
    key = environ.pop("PUBLICATION_APP_PRIVATE_KEY", None)
    require(type(key) is str and bool(key), "connector_publisher_configuration")
    jwt = publisher_jwt(key)
    auth = auth or PublisherAuthentication()
    app = auth.json("/app", jwt)
    require(type(app.get("id")) is int and app["id"] == 5422372
        and app.get("slug") == "atlas-catalogue-publisher" and app.get("owner", {}).get("id") == OWNER_ID
        and app.get("permissions") == APP_PERMISSIONS, "connector_publisher_identity")
    installation = auth.json("/app/installations/174027755", jwt)
    require(type(installation.get("id")) is int and installation["id"] == 174027755
        and installation.get("app_id") == 5422372 and installation.get("account", {}).get("id") == OWNER_ID
        and installation.get("repository_selection") == "selected"
        and installation.get("permissions") == APP_PERMISSIONS
        and "suspended_at" in installation and installation["suspended_at"] is None,
        "connector_publisher_installation")
    issued = auth.json("/app/installations/174027755/access_tokens", jwt, mint=True)
    require(issued.get("permissions") == APP_PERMISSIONS, "connector_publisher_effective_permissions")
    api = client(credential(issued.get("token")), draft_visibility=True)
    scope = api.json("GET", "/installation/repositories?per_page=100", api_global=True)
    require(type(scope.get("total_count")) is int and scope["total_count"] == 1
        and isinstance(scope.get("repositories"), list) and len(scope["repositories"]) == 1,
        "connector_publisher_scope")
    check_repository(scope["repositories"][0])
    return api
