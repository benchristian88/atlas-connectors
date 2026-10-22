# SPDX-License-Identifier: Apache-2.0
"""Bounded GitHub-only transport. Writes are explicit; ambiguous writes never retry."""
import base64
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from atlas_connector_sdk.contracts import strict_json
from publication_contract import (API, MAX_BUNDLE_BYTES, REPOSITORY, REPOSITORY_ID,
                                  PublicationError, canonical_json, digest, hexadecimal,
                                  parse_pointer, positive_integer, require)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Github:
    def __init__(self, token=None):
        self.token = token
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        self.deadline = time.monotonic() + 600

    def request(self, method, path, *, payload=None, binary=None, maximum=1024 * 1024, missing=False, asset=False,
                api_global=False, public=False):
        require(isinstance(path, str) and path.startswith("/") and not path.startswith("//")
                and all(c not in path for c in "\\\r\n#")
                and not {".", ".."}.intersection(urllib.parse.unquote(path.split("?", 1)[0]).split("/")), "invalid_api_path")
        require(method in {"GET", "POST", "PATCH"}, "unsupported_api_method")
        require(not public or method == "GET" and payload is None and binary is None, "invalid_public_request")
        require(method == "GET" or bool(self.token), "publication_credentials_missing")
        # GitHub's repository metadata endpoint rejects a trailing slash.
        # Preserve every non-root path and the existing validation above.
        url = API if path == "/" else API + path
        if api_global:
            # Only identity/scope observations may escape the fixed repository;
            # never use a provider-selected URL or permit global writes.
            require(method == "GET" and payload is None and binary is None and not asset
                    and (re.fullmatch(r"/users/[A-Za-z0-9-]{1,100}(?:%5Bbot%5D)?", path)
                         or re.fullmatch(r"/apps/[a-z0-9][a-z0-9-]{0,99}", path)
                         or path == "/installation/repositories?per_page=100"), "invalid_identity_endpoint")
            url = "https://api.github.com" + path
        if binary is not None:
            require(method == "POST" and path.startswith("/releases/"), "invalid_upload")
            url = f"https://uploads.github.com/repos/{REPOSITORY}" + path
        data = binary if binary is not None else canonical_json(payload) if payload is not None else None
        headers = {"Accept": "application/octet-stream" if asset else "application/vnd.github+json",
                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "atlas-publication-p1", "Accept-Encoding": "identity"}
        if data is not None:
            headers["Content-Type"] = "application/octet-stream" if binary is not None else "application/json"
        if self.token and not public:
            headers["Authorization"] = "Bearer " + self.token
        for attempt in range(3):
            require(time.monotonic() < self.deadline, "github_deadline")
            request = urllib.request.Request(url, method=method, data=data, headers=headers)
            try:
                with self.opener.open(request, timeout=min(20, max(0.1, self.deadline - time.monotonic()))) as response:
                    require(response.status in {200, 201}, "github_status")
                    require(response.headers.get("Content-Encoding", "identity") == "identity", "github_encoding")
                    size = response.headers.get("Content-Length")
                    require(size is None or size.isdigit() and int(size) <= maximum, "github_response_limit")
                    raw = bytearray()
                    while True:
                        require(time.monotonic() < self.deadline, "github_deadline")
                        chunk = response.read(min(65536, maximum + 1 - len(raw)))
                        if not chunk:
                            break
                        raw.extend(chunk)
                        require(len(raw) <= maximum, "github_response_limit")
                    require(size is None or len(raw) == int(size), "github_truncated_response")
                    return bytes(raw)
            except urllib.error.HTTPError as error:
                if error.code == 404 and missing:
                    return None
                # Asset redirects only, with no bearer token on the distribution host.
                if error.code == 302 and asset and method == "GET" and path.startswith("/releases/assets/") and url.startswith(API):
                    destination = error.headers.get("Location", "")
                    parsed = urllib.parse.urlsplit(destination)
                    require(parsed.scheme == "https" and parsed.hostname == "release-assets.githubusercontent.com"
                            and parsed.port in {None, 443} and not parsed.username and not parsed.password
                            and not parsed.fragment and "\\" not in destination, "github_redirect")
                    url = destination
                    headers.pop("Authorization", None)
                    continue
                if error.code in {409, 422}:
                    raise PublicationError("github_conflict_reread_required") from None
                rate = error.code == 429 or error.code == 403 and error.headers.get("X-RateLimit-Remaining") == "0"
                if method == "GET" and attempt < 2 and (error.code in {500, 502, 503, 504} or rate):
                    delay = error.headers.get("Retry-After", "1")
                    require(delay.isdigit() and int(delay) <= 2, "github_rate_limited" if rate else "github_unavailable")
                    time.sleep(int(delay))
                    continue
                raise PublicationError("github_rate_limited" if rate else "github_request_failed") from None
            except (urllib.error.URLError, TimeoutError, OSError):
                raise PublicationError("github_transport_failure") from None
        raise PublicationError("github_retry_limit")

    def json(self, method, path, **kwargs):
        raw = self.request(method, path, **kwargs)
        if raw is None:
            return None
        value = strict_json(raw, maximum=1024 * 1024)
        require(isinstance(value, (dict, list)), "invalid_api_response")
        return value

    def release(self, tag):
        return self.json("GET", "/releases/tags/" + urllib.parse.quote(tag, safe=""), missing=True)

    def release_id(self, identity):
        require(positive_integer(identity), "invalid_release_id")
        return self.json("GET", f"/releases/{identity}")

    def asset_bytes(self, asset, maximum):
        require(positive_integer(asset.get("id")) and type(asset.get("size")) is int
                and 0 < asset["size"] <= maximum and asset.get("state") == "uploaded", "invalid_asset")
        raw = self.request("GET", f"/releases/assets/{asset['id']}", maximum=maximum, asset=True)
        require(len(raw) <= maximum and len(raw) == asset["size"]
                and asset.get("digest") == "sha256:" + digest(raw), "asset_bytes_mismatch")
        return raw

    def assets(self, release):
        require(positive_integer(release.get("id")), "invalid_release_id")
        assets = self.json("GET", f"/releases/{release['id']}/assets?per_page=100")
        require(isinstance(assets, list) and len(assets) < 100, "release_asset_limit")
        names = [a.get("name") for a in assets]
        require(len(names) == len(set(names)), "duplicate_asset_names")
        return {a["name"]: a for a in assets}

    def upload(self, release, name, raw):
        existing = self.assets(release).get(name)
        if existing is not None:
            require(self.asset_bytes(existing, len(raw)) == raw, "staged_asset_substitution")
            return existing
        require(release.get("draft") is True, "immutable_asset_missing")
        response = self.request("POST", f"/releases/{release['id']}/assets?name=" + urllib.parse.quote(name, safe=""), binary=raw)
        asset = strict_json(response)
        require(asset.get("name") == name and self.asset_bytes(asset, len(raw)) == raw, "staged_asset_mismatch")
        return asset

    def attestation(self, raw, verifier, **context):
        # Bounded pagination. Overflow is a diagnostic, never an unauthenticated fallback.
        for page in range(1, 5):
            response = self.json("GET", f"/attestations/sha256:{digest(raw)}?per_page=10&page={page}")
            rows = response.get("attestations")
            require(isinstance(rows, list) and len(rows) <= 10, "invalid_attestation_response")
            for row in rows:
                require(row.get("repository_id") == REPOSITORY_ID, "attestation_repository")
                bundle = canonical_json(row.get("bundle"))
                require(len(bundle) <= MAX_BUNDLE_BYTES, "attestation_size")
                try:
                    evidence = verifier.verify(raw, bundle, **context)
                    return bundle, evidence
                except (ValueError, KeyError, TypeError):
                    continue
            if len(rows) < 10:
                break
        raise PublicationError("matching_attestation_unavailable")

    def channel(self):
        reference = self.json("GET", "/git/ref/heads/catalogue-current", missing=True)
        require(reference is not None, "approved_bootstrap_required")
        require(reference.get("ref") == "refs/heads/catalogue-current"
                and reference.get("object", {}).get("type") == "commit", "channel_ref")
        sha = reference["object"]["sha"]
        require(hexadecimal(sha, 40), "channel_commit")
        commit = self.json("GET", f"/git/commits/{sha}")
        require(commit.get("sha") == sha and isinstance(commit.get("parents"), list)
                and len(commit["parents"]) <= 1, "channel_parent")
        files = {}
        for name, maximum in (("current.json", 1024), ("current.sigstore.json", MAX_BUNDLE_BYTES)):
            value = self.json("GET", f"/contents/{name}?ref={sha}")
            require(value.get("type") == "file" and value.get("path") == name and value.get("encoding") == "base64"
                    and type(value.get("size")) is int and 0 < value["size"] <= maximum, "channel_file")
            try:
                raw = base64.b64decode(value["content"].replace("\n", ""), validate=True)
            except (ValueError, TypeError):
                raise PublicationError("channel_encoding") from None
            require(len(raw) == value["size"], "channel_file_size")
            files[name] = raw
        pointer = parse_pointer(files["current.json"])
        if pointer["sequence"] == 1:
            require(not commit["parents"], "bootstrap_channel_parent")
        else:
            require(len(commit["parents"]) == 1, "channel_parent")
            parent = commit["parents"][0].get("sha")
            require(hexadecimal(parent, 40), "channel_parent")
            value = self.json("GET", f"/contents/current.json?ref={parent}")
            require(value.get("type") == "file" and value.get("encoding") == "base64"
                    and type(value.get("size")) is int and 0 < value["size"] <= 1024, "channel_parent_file")
            try:
                previous_raw = base64.b64decode(value["content"].replace("\n", ""), validate=True)
            except (ValueError, TypeError):
                raise PublicationError("channel_parent_encoding") from None
            require(len(previous_raw) == value["size"] and digest(previous_raw) == pointer["previous_pointer_sha256"]
                    and parse_pointer(previous_raw)["sequence"] + 1 == pointer["sequence"], "channel_parent_binding")
        return sha, files

    def compare_and_swap(self, expected, files):
        require(self.channel()[0] == expected, "channel_changed")
        tree = self.json("POST", "/git/trees", payload={"tree": [
            {"path": name, "mode": "100644", "type": "blob", "content": raw.decode("utf-8")}
            for name, raw in sorted(files.items())]})
        require(hexadecimal(tree.get("sha"), 40), "invalid_tree_response")
        commit = self.json("POST", "/git/commits", payload={"message": "Advance authenticated catalogue selection",
                           "tree": tree["sha"], "parents": [expected]})
        require(hexadecimal(commit.get("sha"), 40), "invalid_commit_response")
        # If another publisher wins, this single-parent sibling cannot fast-forward.
        self.json("PATCH", "/git/refs/heads/catalogue-current", payload={"sha": commit["sha"], "force": False})
        observed, actual = self.channel()
        require(observed == commit["sha"] and actual == files, "channel_changed_after_update")
        return observed

    def bootstrap_absent(self):
        """A missing branch alone never reopens consumed bootstrap authority."""
        require(self.json("GET", "/git/ref/heads/catalogue-current", missing=True) is None,
                "bootstrap_current_exists_review_required")
        require(self.json("GET", "/git/ref/tags/catalogue-bootstrap-root", missing=True) is None,
                "bootstrap_consumed_review_required")

    def verify_root(self, sha, files):
        """Verify a true root with exactly two ordinary blobs, including their bytes."""
        import hashlib
        require(hexadecimal(sha, 40), "bootstrap_root_identity")
        commit = self.json("GET", f"/git/commits/{sha}")
        require(commit.get("sha") == sha and commit.get("parents") == [], "bootstrap_root_parent")
        tree_sha = commit.get("tree", {}).get("sha")
        require(hexadecimal(tree_sha, 40), "bootstrap_root_tree")
        tree = self.json("GET", f"/git/trees/{tree_sha}")
        require(tree.get("sha") == tree_sha and tree.get("truncated") is False
                and isinstance(tree.get("tree"), list) and len(tree["tree"]) == 2, "bootstrap_root_tree")
        actual = {}
        for row in tree["tree"]:
            require(row.get("type") == "blob" and row.get("mode") == "100644"
                    and row.get("path") not in actual, "bootstrap_root_tree")
            actual[row["path"]] = row.get("sha")
        expected = {name: hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
                    for name, raw in files.items()}
        require(actual == expected, "bootstrap_root_bytes")

    def create_root(self, files, *, reauthorize):
        """Create-only refs. A durable no-bypass intent tag fences ambiguous retries.

        Marker-without-current requires a separate reviewed recovery, never an
        automatic retry. A lost current creation response is inspected, not replayed.
        """
        require(set(files) == {"current.json", "current.sigstore.json"}, "bootstrap_root_files")
        require(parse_pointer(files["current.json"])["sequence"] == 1, "bootstrap_root_sequence")
        require(0 < len(files["current.sigstore.json"]) <= MAX_BUNDLE_BYTES, "attestation_size")
        self.bootstrap_absent()
        tree = self.json("POST", "/git/trees", payload={"tree": [
            {"path": name, "mode": "100644", "type": "blob", "content": raw.decode("utf-8")}
            for name, raw in sorted(files.items())]})
        require(hexadecimal(tree.get("sha"), 40), "invalid_tree_response")
        commit = self.json("POST", "/git/commits", payload={"message": "Establish authenticated catalogue root",
                           "tree": tree["sha"], "parents": []})
        sha = commit.get("sha")
        self.verify_root(sha, files)
        reauthorize()
        self.bootstrap_absent()
        # Separate no-bypass update/deletion rules preserve this consumption marker.
        # No catch/retry here: a lost marker response consumes authority conservatively.
        self.json("POST", "/git/refs", payload={"ref": "refs/tags/catalogue-bootstrap-root", "sha": sha})
        marker = self.json("GET", "/git/ref/tags/catalogue-bootstrap-root")
        require(marker.get("ref") == "refs/tags/catalogue-bootstrap-root"
                and marker.get("object", {}).get("type") == "commit"
                and marker.get("object", {}).get("sha") == sha,
                "bootstrap_marker_conflict")
        reauthorize()
        require(self.json("GET", "/git/ref/heads/catalogue-current", missing=True) is None,
                "bootstrap_current_exists_review_required")
        try:
            self.json("POST", "/git/refs", payload={"ref": "refs/heads/catalogue-current", "sha": sha})
        except PublicationError:
            # Even a timeout may have committed. Read exact state without retrying.
            reference = self.json("GET", "/git/ref/heads/catalogue-current", missing=True)
            require(reference is not None and reference.get("object", {}).get("sha") == sha,
                    "bootstrap_root_ambiguous_review_required")
        observed, actual = self.channel()
        require(observed == sha and actual == files, "bootstrap_root_conflict")
        self.verify_root(sha, files)
        marker = self.json("GET", "/git/ref/tags/catalogue-bootstrap-root")
        require(marker.get("object", {}).get("sha") == sha, "bootstrap_marker_conflict")
        require(self.channel() == (sha, files), "bootstrap_root_conflict")
        return sha
