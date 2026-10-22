# Official Connector Catalogue maintenance

The [P1 publication contract](publication/README.md) defines separate immutable
numbered releases and a separately authenticated current-pointer branch. Local
foundations use explicit single-maintainer authorization behind disabled policy. Owner settings, bootstrap
migration, package-history decisions and Atlas consumer support remain required;
no live publication or settings changes were performed by this implementation.

The legacy aggregate v1 sequence 1 remains at the
[official release](https://github.com/benchristian88/atlas-connectors/releases/tag/catalogue-v1).
The [frozen publication fixture](../tests/fixtures/official_catalogue/README.md)
preserves its 10,585 bytes and SHA-256 independently of HEAD. **The legacy release
and the Proxmox 0.2.0 package release both report immutable=false.** Earlier
references to immutable assets described an intended publication policy, not
actual GitHub enforcement. Do not rebuild, replace or republish sequence 1.

The legacy catalogue.json alias and catalogue-000001.json assets stay unchanged.
Their build attestations authenticate bytes but do not establish release approval,
immutable publication or currentness. Atlas B1.3 correctly rejects that channel.
The proposed P1 source adapter is a separate reviewed consumer change; no fallback
to unauthenticated legacy discovery is introduced.

Per-package index.json remains detached release metadata, not the aggregate
catalogue. See [the investigation](publication/investigation.md) for verified code
and provider state, [the ADR](../docs/decisions/0001-github-catalogue-publication.md)
for storage, [single-maintainer policy](../docs/decisions/0002-single-maintainer-publication.md)
for authorization, and [consumer handoff](publication/consumer-handoff.md).

## Checked-in registry and policy

The catalogue has no calendar expiry and requires no periodic regeneration while
its state is unchanged. Publication occurs when catalogue state changes, such as a
Connector release, explicit withdrawal or other authenticated catalogue-policy
change.

`sequence.txt` starts at `1`. Every newly published catalogue document must use a
strictly increasing sequence; sequence numbers must never be decreased or reused.
Sequence and asset IDs must be literal positive integers no larger than
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
Its legacy release is `proxmox-v0.2.0` (release ID `416290807`), with asset ID
`652745908` and filename `proxmox-0.2.0.tar.gz`. No historical release files need
modification. Tests pin the entire combined Manifest independently of current
Connector source and without requiring old Git objects in CI's shallow checkout.

Releases remain in the catalogue for rollback unless explicitly withdrawn. Keep
older active entries when adding new versions. A withdrawal changes `status` from
`active` to `withdrawn`, retaining the entire release as an explicit tombstone in a
new authenticated catalogue sequence. Explicit authenticated withdrawal controls
future install/activation eligibility; **absence is not revocation**. The builder
does not convert an omission into withdrawal or infer status from previous output.

The v1 document has exactly `schema_version`, `sequence`, `generated_at`,
`publisher_id`, `repository` and `entries`. Schema version is `1.0`;
publisher is exclusively `atlas-official`, repository exclusively
`benchristian88/atlas-connectors`. Entries sort lexically by Connector ID and
literal version, with unique Connector/version and release asset identities, and
a hard ceiling of 200 entries. Every Manifest is validated by the canonical pinned
SDK; no SDK schema is copied here. Each release must have an exact `sha256:` bundle
digest, the matching release tag/filename/asset URI, a 40-character lowercase hex
source commit, and `github-artifact-attestation-sigstore` provenance from
`.github/workflows/release.yml` in the approved repository.

Only UTF-8, bounded, regular JSON registry files are accepted (256 KiB raw bytes
per file, unchanged). In addition, `validate_entry` independently limits the
canonical standalone entry to **262,144 bytes**, including when called through
`validate_catalogue` with an in-memory aggregate. `entry_size` measures exactly
`(json.dumps(entry, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")`.
This includes the complete four-field envelope, Manifest, whitespace and one final
newline at root indentation. Indentation added by placement inside the aggregate
array is excluded from entry sizing. Compact files must satisfy this canonical
entry bound as well as the original raw file bound.

The complete canonical aggregate uses the same serialization and has a separate
**4,194,304-byte** (4 MiB) bound. Atlas B1.1 also enforces 4 MiB on received raw
bytes before decoding. These bounds and the 200-entry ceiling are inclusive and
independent; the aggregate allowance is not derived by multiplying entry limits.
Hashing and future attestation verification use original publication bytes, never
reconstructed JSON. Producer and consumer tests cover below, at and above the
limits; the frozen published sequence 1 remains valid.
Duplicate JSON keys, non-finite numbers, malformed JSON, unexpected fields,
symlinks and inconsistent identity filenames fail closed. Deterministic output is
UTF-8 JSON with sorted object keys, two-space indentation and a final newline.
`generated_at` is an audit/provenance timestamp derived deterministically from the
publication source commit's committer timestamp (the current repository Git HEAD),
formatted as UTC seconds. There is no wall-clock or environment-variable timestamp
override. Local uncommitted changes still use HEAD's time and carry no claim of
authenticated provenance.

`generated_at` must be exactly `YYYY-MM-DDTHH:MM:SSZ`, without offsets or
fractional seconds. Entry status is exactly `active` or `withdrawn`; unknown or
missing fields in either envelope fail. Lexical entry ordering is not semantic
version precedence and must not be used for future update selection.

Atlas B1.1 only validates structure and official identity declarations with the
pinned SDK 1.1.0. No SDK release or dependency on this checkout is required. It
does not verify attestations or label packages trusted. Its existing three-field
release-packaged bootstrap format (`catalogue_version`, `release_identity`,
`entries`) remains separate from this six-field aggregate; bundled installation
and fail-closed remote verification are unchanged. Catalogue provenance uses
`.github/workflows/catalogue.yml`, distinct from package provenance's
`.github/workflows/release.yml`. Declared publisher IDs are not authenticated
identities. B1.2 has qualified cryptographic verification in Atlas; P1 publication authority
and B1.3 source-policy acceptance remain separate requirements.

## Consumer freshness boundary

Future Atlas Stage B will attempt authenticated catalogue refresh daily, remember
the highest authenticated sequence accepted, and reject sequence rollback. A
successful authenticated refresh can confirm the unchanged document at that same
sequence; this does not require a newly published document.

Stage B will impose its own local install/update freshness policy independently of
catalogue document expiry: after 72 hours without a successful authenticated
refresh, Atlas will block new remote Connector install/update operations. An
unavailable catalogue must not disable already-installed Connectors; they continue
operating offline. These consumer policies are not implemented by Stage A.

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
execution to the official repository and main, uses Python 3.12 on Ubuntu 24.04,
validates and builds without a publication environment, attests both JSON
files with pinned `actions/attest`, then uploads them as a workflow artifact.
Artifact upload fails when files are absent. Its token has only `contents: read`,
`id-token: write` and `attestations: write`; it uses no PAT. It has no Release
publication, remote asset replacement, tag mutation or repository-write step.
