# Official Connector Catalogue maintenance

Stage A prepares and attests aggregate catalogue artifacts. It does not publish
them, change Connector discovery/runtime behavior, or make Atlas consume a remote
catalogue or install/update/roll back remote Connectors.

Each Connector release's `index.json` remains an immutable, detached per-release
descriptor. It is **not** the aggregate global catalogue. Connector bundles and
their combined Manifests retain their independent release identities.

The eventual fixed aggregate distribution channel is the GitHub Release/tag
`catalogue-v1` in `benchristian88/atlas-connectors`:

- `catalogue.json` is the current authenticated catalogue document, once published
  with verifiable GitHub Artifact Attestation / Sigstore provenance.
- `catalogue-000001.json`, `catalogue-000002.json`, etc. are immutable numbered
  historical/audit copies. For any sequence, the current alias and that sequence's
  snapshot must have identical document bytes.

Publication remains a separate operator/protected step outside Stage A. This
repository change neither creates that Release/tag nor replaces remote assets.
An unverified local file or workflow artifact alone is not authenticated catalogue
state. Future consumers must verify the catalogue attestation, approved repository
and catalogue workflow identity, freshness and increasing sequence before trusting
it. Bundle attestations retain their separate release workflow identity.

## Checked-in registry and policy

`sequence.txt` starts at `1`. Maintainers must increase it for every publication,
including expiry refreshes and withdrawals; never decrease or reuse a published
sequence. Sequence and asset IDs must be literal positive integers no larger than
`2^53 - 1`, avoiding rounding in JSON consumers. Snapshot numbers use at least six
digits. The builder reads the checked-in sequence; it does not allocate numbers
or consult remote state to enforce publication history.

`releases/<connector_id>-<version>.json` contains exactly `status`, `release_tag`,
`release_asset_id` and the complete SDK-validated combined `manifest`. Capture the
Manifest from the immutable release, including its distribution digest and
provenance. Never reconstruct an old Manifest from mutable Connector source at a
future HEAD. All release identity and Manifest fields are historical metadata:
preserve them. Only an explicit reviewed status transition may change eligibility.

The initial `proxmox-0.2.0.json` preserves the production Manifest at source commit
`456a5bfdd1398c19da9ffef29216029027e24278`, reconstructed from that exact Git object
and the released distribution identity. The original bundle build at that commit
reproduced SHA-256
`a14fec5ab485c980688ff5907e8835ddd3e9cecd1a6989ef252cbcb1b1dc4ef8`.
Its immutable release is `proxmox-v0.2.0` (release ID `416290807`), with asset ID
`652745908` and filename `proxmox-0.2.0.tar.gz`. No historical release files need
modification. Tests pin the entire combined Manifest independently of current
Connector source and without requiring old Git objects in CI's shallow checkout.

Releases remain in the catalogue for rollback unless explicitly withdrawn. Keep
older active entries when adding new versions. A withdrawal changes `status` from
`active` to `withdrawn`, retaining the entire release as an explicit tombstone in a
new authenticated catalogue sequence. Withdrawal must be explicit and
authenticated; **absence is not revocation**. The builder does not convert an
omission into withdrawal or infer status from previous output.

The v1 document has exactly `schema_version`, `sequence`, `generated_at`,
`expires_at`, `publisher_id`, `repository` and `entries`. Schema version is `1.0`;
publisher is exclusively `atlas-official`, repository exclusively
`benchristian88/atlas-connectors`. Entries sort lexically by Connector ID and
literal version, with unique Connector/version and release asset identities, and
a hard ceiling of 200 entries. Every Manifest is validated by the canonical pinned
SDK; no SDK schema is copied here. Each release must have an exact `sha256:` bundle
digest, the matching release tag/filename/asset URI, a 40-character lowercase hex
source commit, and `github-artifact-attestation-sigstore` provenance from
`.github/workflows/release.yml` in the approved repository.

Only UTF-8, bounded, regular JSON registry files are accepted (256 KiB per entry).
The complete serialized aggregate catalogue has a separate 4 MiB (4,194,304-byte)
bound, inclusive. This deliberately limits the total catalogue payload independently
of the SDK's 256 KiB bound for each release descriptor/Manifest; it is not derived
by multiplying that per-entry allowance by the 200-entry ceiling. All three bounds
apply independently.
Duplicate JSON keys, non-finite numbers, malformed JSON, unexpected fields,
symlinks and inconsistent identity filenames fail closed. Deterministic output is
UTF-8 JSON with sorted object keys, two-space indentation and a final newline.
`generated_at` is the current repository Git commit's committer timestamp, formatted
as UTC seconds; `expires_at` is exactly seven days later. There is no wall-clock or
environment-variable timestamp override. An old commit can yield an already
expired catalogue: refresh with a new reviewed commit and sequence before
publication. Local uncommitted changes still use HEAD's time and carry no claim of
authenticated provenance.

## Prepare and validate

From the repository root, using Python 3.12+:

```bash
python -m pip install --no-index --no-deps --require-hashes --find-links vendor/sdk -r vendor/sdk/requirements.txt
python -m pip install 'jsonschema[format-nongpl]==4.25.1' pytest==8.4.1
python -m pytest --noconftest -q tests/test_catalogue.py tests/test_documentation.py
python tools/build_catalogue.py
```

The focused suite omits the Connector-only conftest so no Ansible runtime or
collection is needed. The normal repository suite also runs these tests. The
builder and catalogue tests do not download bundles or contact GitHub, and never
execute a Connector. Git runs only with fixed read-only timestamp arguments.
Install the canonical vendored SDK exactly as for release preparation; the only
additional focused test/build dependencies are the reviewed versions above.

Sequence 1 emits identical bytes at:

```text
dist/catalogue/catalogue.json
dist/catalogue/catalogue-000001.json
```

An optional `--output <directory>` changes only the local artifact destination.
The CLI prints the sequence, entry count and document SHA-256; it does not print
the full Manifests. Validation failures occur before writing catalogue documents.

The manual-only [catalogue workflow](../.github/workflows/catalogue.yml) restricts
execution to the official repository, uses Python 3.12 on Ubuntu 24.04 and the
protected `connector-release` environment, validates and builds, attests both JSON
files with pinned `actions/attest`, then uploads them as a workflow artifact.
Artifact upload fails when files are absent. Its token has only `contents: read`,
`id-token: write` and `attestations: write`; it uses no PAT. It has no Release
publication, remote asset replacement, tag mutation or repository-write step.
