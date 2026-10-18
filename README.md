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
**0.2.0-i4b.6**, discovers only cluster, node, QEMU and LXC Assets, with canonical
Networks/Interfaces and member_of/runs_on relationships. There are no bridge
Assets or connected_to Asset relationships.

Proxmox bridges are host networking constructs used to describe Interface and
Network topology. Atlas MVP does not model them as standalone Assets. Guest bridge
attachment remains bounded topology context on the guest Interface, and explicit
VLAN/static-network evidence is retained.

Host bridge Interfaces remain node-owned; guest Interfaces retain validated
`proxmox.bridge_name`, MAC, explicit VLAN tags, bounded trunk VLANs and known
static IP/subnet evidence. Canonical Networks require explicit subnet proof;
tagged/trunk interfaces never inherit the bridge subnet. No DHCP or guest-agent
addresses are inferred. The node network endpoint remains mandatory.
The [discovery specification and source call matrix](connectors/proxmox/candidate/docs/discovery.md)
describe its exact scope and unchanged fail-closed COMPLETE/PARTIAL rules.

Proxmox storage definitions are configuration/resources exposed by the
virtualisation platform. Atlas MVP does not model them as standalone Assets.
Backing storage infrastructure should be discovered by the integration responsible
for that infrastructure where available.

`.6`, like `.5`, emits no storage-pool Assets, uses_storage relationships, storage capacity
telemetry or workload storage facts. No storage dependencies are represented;
Atlas may introduce a richer resource/dependency model later. Both storage
inventory endpoints and storage-specific permission checks are removed. Guest
current-config reads and network parsing remain required; disk/rootfs/mount values
are ignored without storage resolution warnings.

The operator-reported .1/.2 9.2.11 runs were PARTIAL (140/179 observations).
The .3 trace isolated storage_inventory_mismatch on pve3: an inactive/disabled
local-zfs status row without an applicable definition. The valid **.4** fix
handled exactly that condition under its historical scope. `.5` is a later product
scope decision and achieved repeatable operator-reported live COMPLETE against
9.2.11: two runs, 136 observations/one batch/zero warnings or errors each, the second
with Debug Off. `.6` makes a subsequent product scope decision about bridges.
Production **0.1.0** and **.1/.2/.3/.4/.5** artifacts remain immutable.
On **18 October 2026**, operator-reported `.6` live positive-path qualification
against Proxmox VE **9.2.11** passed repeatably: Debug On and Debug Off manual runs
each completed with **Coverage Complete / Full scope, 100 observations, one batch
and zero warnings/errors**. Live evidence confirms host vmbr0 as an Interface,
guest `proxmox.bridge_name=vmbr0` and VLAN tags **3, 5 and 6**, with no bridge/storage
Assets or connected_to/uses_storage links. VLAN **99** remains fixture/test evidence
only. A deliberately incorrect TLS certificate fingerprint failed Test Connection;
restoring the correct fingerprint restored success. Temporary `.6` qualification
permission was revoked after evidence collection, retaining history.

**Live qualification evidence accepted/passed** is distinct from published/global
qualification or production promotion. All candidate Manifests retain
`source_versions.qualification=unqualified` and `qualified_versions=[]`; no candidate
is published or released as 0.2.0, and production/default **0.1.0** is unchanged.
Docker/UniFi implementations remain absent.

[I4C-A preparation](connectors/proxmox/docs/i4c-a-preparation.md) preserves the exact
original candidate bytes. The [active live runbook](connectors/proxmox/docs/i4c-live-qualification.md)
records historical PARTIAL results, the positive `.5` baseline and the completed
`.6` checkpoint, exact digest, live runs, TLS negative test and cleanup.
[The implementation report](connectors/proxmox/docs/i4c-network-scope-report.md)
preserves pre-live validation and records the subsequent live completion evidence.
[Discovery diagnostics](connectors/proxmox/docs/i4c-discovery-diagnostics.md) describes
always-on safe reasons and administrator-only next-run debug, with 48-hour retention,
no raw source logging and debug-independent behavior. `.6` retains all network
source reads, validation and diagnostics, identifying host Interfaces in place of
bridge Assets. The representative three-node sequence remains 46 requests, the
same as `.5`; every remaining declared capability retains its safety rules.
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
Packaged `.6` qualification/completion documents preserve their pre-live snapshot
to retain the exact archive bytes; the repository live record carries later evidence.
Candidate output goes to `dist/proxmox-candidate-0.2.0-i4b.6/`, so the legacy
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
