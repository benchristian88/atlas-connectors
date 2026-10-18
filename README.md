# Atlas official Connectors

Apache-2.0 by default for Atlas-authored code. Connector source lives here;
Atlas application/domain/runtime source remains in the AGPL Atlas project.
Third-party dependencies retain their licences and are inventoried by their
own distribution. No AGPL application/plugin implementation was copied here.

Each `connectors/<id>/` package owns its independent SemVer Manifest, fixed
entry-point playbooks, `library/`, README, NOTICE and SPDX SBOM. Repository-level
LICENSE is included in every bundle. Fixtures/unit tests live in `tests/`.
Production [Proxmox 0.2.0](connectors/proxmox/README.md) promotes the unchanged
**0.2.0-i4b.6** discovery implementation, qualified against **Proxmox VE 9.2.11**.
It supports Test Connection, read-only discovery, scheduling and complete snapshots:
cluster, node, QEMU and LXC Assets, canonical Networks/Interfaces and
member_of/runs_on relationships. There are no bridge or storage Assets,
connected_to or uses_storage relationships. Other source versions remain untested
with a warning; this does not claim all Proxmox 9.x versions are supported.
0.2.0 is the first production Connector release being prepared. **0.1.0** was an
internal development/probe baseline, never tagged or published as a GitHub Release;
Git history preserves that state. No release is published by this promotion.

Proxmox bridges are host networking constructs used to describe Interface and
Network topology. Atlas MVP does not model them as standalone Assets. Guest bridge
attachment remains bounded topology context on the guest Interface, and explicit
VLAN/static-network evidence is retained.

Host bridge Interfaces remain node-owned; guest Interfaces retain validated
`proxmox.bridge_name`, MAC, explicit VLAN tags, bounded trunk VLANs and known
static IP/subnet evidence. Canonical Networks require explicit subnet proof;
tagged/trunk interfaces never inherit the bridge subnet. No DHCP or guest-agent
addresses are inferred. The node network endpoint remains mandatory.
The [discovery specification and source call matrix](connectors/proxmox/docs/discovery.md)
describe its exact scope and unchanged fail-closed COMPLETE/PARTIAL rules.

Proxmox storage definitions are configuration/resources exposed by the
virtualisation platform. Atlas MVP does not model them as standalone Assets.
Backing storage infrastructure should be discovered by the integration responsible
for that infrastructure where available.

The release, like `.6`/`.5`, emits no storage-pool Assets, uses_storage relationships,
storage capacity telemetry or workload storage facts. No storage dependencies are represented;
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
The **.1/.2/.3/.4/.5** candidate artifacts retain their historical identities;
the internal **0.1.0** baseline remains available in Git history.
On **18 October 2026**, operator-reported `.6` live positive-path qualification
against Proxmox VE **9.2.11** passed repeatably: Debug On and Debug Off manual runs
each completed with **Coverage Complete / Full scope, 100 observations, one batch
and zero warnings/errors**. Live evidence confirms host vmbr0 as an Interface,
guest `proxmox.bridge_name=vmbr0` and VLAN tags **3, 5 and 6**, with no bridge/storage
Assets or connected_to/uses_storage links. VLAN **99** remains fixture/test evidence
only. A deliberately incorrect TLS certificate fingerprint failed Test Connection;
restoring the correct fingerprint restored success. The temporary `.6` qualification authority was later restored for post-qualification
regression verification and remains time-bounded pending replacement by the released
Connector or automatic expiry.

Production **0.2.0** now records that accepted qualification with
`source_versions.qualification=qualified`, `qualified_versions=["9.2.11"]`,
`known_incompatible=[]` and `newer_untested_policy=allow_with_warning`.
Authentication-secret negative testing was not performed. Native Debian/systemd
LIVE acceptance remains outstanding. All candidate Manifests retain
`source_versions.qualification=unqualified` and `qualified_versions=[]`.
The [historical .6 candidate](connectors/proxmox/candidate/README.md) and its
pre-live packaged docs remain unchanged, with exact archive SHA-256
`dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97`.
See [production qualification](connectors/proxmox/docs/qualification.md) for the
accepted evidence and its limits. Docker/UniFi implementations remain absent.

[I4C-A preparation](connectors/proxmox/docs/i4c-a-preparation.md) preserves the exact
original candidate bytes. The [historical live qualification record](connectors/proxmox/docs/i4c-live-qualification.md)
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

The per-release `index.json` is immutable detached metadata, not the aggregate
global catalogue. [Official catalogue maintenance](catalogue/README.md) documents
the separate checked-in release registry, deterministic catalogue builder and
manual protected preparation/attestation workflow. Stage A prepares
`dist/catalogue/catalogue.json` and an identical numbered audit snapshot for the
eventual `catalogue-v1` channel; publication remains a separate operator step.
This does not implement Atlas remote catalogue consumption or installation.

The test collection archive above is the exact I4A artefact from a sibling Atlas
checkout. CI downloads the same archive and verifies its reviewed SHA-256 before
test installation. This tooling never installs dependencies into a production
Connector bundle. The normal **0.2.0** archive includes the qualified discovery
playbook, readiness/discovery modules and discovery/normalization/transport/
diagnostics helpers. Production Test Connection uses the qualified readiness
module. Candidate metadata and docs are explicit historical overrides under
`connectors/proxmox/candidate/`, excluded as paths from the production archive.
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

Remote acceptance still requires reviewed committed/pushed release source,
immutable assets and attestation/trust-root verification. Source qualification
does not complete those publication steps. Atlas's remote verifier remains
fail-closed. Local acceptance uses the existing Atlas bootstrap trust path with an exact packaged allowlist;
it is not a substitute claim of remote attestation verification.
