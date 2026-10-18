# Atlas official Connectors

Apache-2.0 by default for Atlas-authored code. Connector source lives here;
Atlas application/domain/runtime source remains in the AGPL Atlas project.
Third-party dependencies retain their licences and are inventoried by their
own distribution. No AGPL application/plugin implementation was copied here.

Each `connectors/<id>/` package owns its independent SemVer Manifest, fixed
entry-point playbooks, `library/`, README, NOTICE and SPDX SBOM. Repository-level
LICENSE is included in every bundle. Fixtures/unit tests live in `tests/`.
Production [Proxmox 0.1.0](connectors/proxmox/README.md) is Test Connection-only.
The separate [MVP candidate](connectors/proxmox/candidate/README.md),
**0.2.0-i4b.5**, discovers cluster, node, QEMU, LXC and bridge Assets with
canonical Networks/Interfaces and member_of, runs_on and connected_to relationships.
The [discovery specification and source call matrix](connectors/proxmox/candidate/docs/discovery.md)
describe its exact scope and unchanged fail-closed COMPLETE/PARTIAL rules.

Proxmox storage definitions are configuration/resources exposed by the
virtualisation platform. Atlas MVP does not model them as standalone Assets.
Backing storage infrastructure should be discovered by the integration responsible
for that infrastructure where available.

`.5` emits no storage-pool Assets, uses_storage relationships, storage capacity
telemetry or workload storage facts. No storage dependencies are represented;
Atlas may introduce a richer resource/dependency model later. Both storage
inventory endpoints and storage-specific permission checks are removed. Guest
current-config reads and network parsing remain required; disk/rootfs/mount values
are ignored without storage resolution warnings.

The operator-reported .1/.2 9.2.11 runs were PARTIAL (140/179 observations).
The .3 trace isolated storage_inventory_mismatch on pve3: an inactive/disabled
local-zfs status row without an applicable definition. The valid **.4** fix
handled exactly that condition under its historical scope. `.5` is a later product
scope decision. Production **0.1.0** and **.1/.2/.3/.4** artifacts remain immutable.
All candidates and Proxmox **9.2.11** remain unqualified; no candidate is published.
Docker/UniFi implementations remain absent.

[I4C-A preparation](connectors/proxmox/docs/i4c-a-preparation.md) preserves the exact
original candidate bytes. The [active live runbook](connectors/proxmox/docs/i4c-live-qualification.md)
records the PARTIAL results and the next candidate checkpoint.
[Discovery diagnostics](connectors/proxmox/docs/i4c-discovery-diagnostics.md) describes
always-on safe reasons and administrator-only next-run debug, with 48-hour retention,
no raw source logging and debug-independent behavior. `.5` removes storage-specific
stages/calls only; every remaining declared capability retains its safety rules.
Qualification documents/checkpoints and incidental files are excluded by the
reviewed bundle file list. Neither local preparation nor fixture tests qualify a source.

Python 3.12+ development:

```bash
python -m pip install --no-index --no-deps --require-hashes --find-links vendor/sdk -r vendor/sdk/requirements.txt
python -m pip install -r requirements-dev.txt
python tools/test_collection.py --archive ../atlas/vendor/collections/community-proxmox-2.0.0.tar.gz --output /tmp/atlas-connector-test-collections
export ATLAS_TEST_COLLECTIONS_PATH=/tmp/atlas-connector-test-collections
export ATLAS_TEST_RUN_ANSIBLE=1
python -m pytest -q
python tools/build_bundle.py
python tools/build_bundle.py --candidate
```

The same SDK **1.1.0 wheel/hash** is staged in Atlas and here. Canonical schemas
remain exclusively in atlas-connector-sdk; the wheel is a pinned distribution
artifact. Update that artifact in both consumers together after reproducibility
and package-data checks, never via mutable source URLs or copied schemas.

The USTAR/gzip builder sorts paths and fixes modes, owners and timestamps.
`dist/proxmox/` contains the exact bundle, SHA256SUMS, detached combined Manifest
and an index. The archive contains the domain Manifest without its own digest.
Build twice and compare bytes. A local dirty-tree candidate has no authenticated
remote provenance; its recorded source HEAD is contextual, not a claim that the
uncommitted implementation exists at that commit.

The test collection archive above is the exact I4A artefact from a sibling Atlas
checkout. CI downloads the same archive and verifies its reviewed SHA-256 before
test installation. This tooling never installs dependencies into a production
Connector bundle. Candidate metadata and executable helpers are excluded from the
normal 0.1.0 build. Current candidate README/docs are explicit overrides under
`connectors/proxmox/candidate/`; shared production package docs remain frozen.
Candidate output goes to `dist/proxmox-candidate-0.2.0-i4b.5/`, so the legacy
`.1` output directory and earlier candidate descriptors are not overwritten.
`tools/build_acceptance_fixture.py --output <test-directory>` creates a separate
deterministic `i4b-fixture` harness for Atlas tests. Its source adapter and embedded
sanitized fixtures exist only in that test bundle; its `fixture-only` qualification
does not qualify Proxmox or allow candidate activation.

CI validates contracts, fixtures and build. The protected `proxmox-v<SemVer>`
release workflow verifies tag/Manifest identity, builds and attests the exact
bundle with the pinned GitHub `actions/attest` action, then retains a release
candidate artifact. The operator publishes those unchanged files as immutable
GitHub Release assets only after qualification. No release has been published
by this work. Repository identity is **benchristian88/atlas-connectors** and
signer workflow is **.github/workflows/release.yml**; Atlas must bind both, the
exact digest/source commit and authenticated Sigstore issuer/predicate evidence.

Remote acceptance remains blocked on an actual reviewed pushed workflow,
immutable release, attestation/trust-root verification and operator
qualification. Atlas's remote verifier remains fail-closed. Local acceptance
uses the existing Atlas bootstrap trust path with an exact packaged allowlist;
it is not a substitute claim of remote attestation verification.
