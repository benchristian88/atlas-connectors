# Atlas official Connectors

Apache-2.0 by default for Atlas-authored code. Connector source lives here;
Atlas application/domain/runtime source remains in the AGPL Atlas project.
Third-party dependencies retain their licences and are inventoried by their
own distribution. No AGPL application/plugin implementation was copied here.

Each `connectors/<id>/` package owns its independent SemVer Manifest, fixed
entry-point playbooks, `library/`, README, NOTICE and SPDX SBOM. Repository-level
LICENSE is included in every bundle. Fixtures/unit tests live in `tests/`.

**Phase 4B: Proxmox 0.2.1 is prepared locally for immutable release, not published.**
Explicit version metadata in `connectors/proxmox/releases/0.2.1/` reuses all
qualified executable source. `python tools/build_bundle.py --version 0.2.1`
selects it; the default 0.2.0 and historical candidate builds retain their exact
bytes. `python tools/release_connector.py --local --tag proxmox-v0.2.1 --output dist/proxmox-0.2.1-review`
also performs release archive, qualification, compatibility, SPDX and licence
checks. Local output is unattested. The
[operator-controlled package release procedure](catalogue/publication/README.md#phase-4b-package-finalization--separate-human-authorization-required)
defines the approved App identity, retained build signature, exact-byte draft
staging, provider immutability checks and read-only independent verifier.
The historical 0.2.0 source, package, registry and catalogue history remain intact.

**Phase 4B.2: package publication mechanisms are locally implemented for review,
with privileged execution disabled.** The separate
[package publication runbook](catalogue/publication/connector-packages.md) documents
signed isolated admission, independent tag/stage/finalize dispatches, immutable
verification, reviewed implementation S
`d6601ad97815a85da164e4329766ea17b62bddc9`. Genuine acceptance run `40523236413`
failed before checkout/signing with Publisher skipped. The local
[workflow identity correction](docs/phase-4b2-identity-qualification.md) requires a
new reviewed S2, a separate four-binding pinning PR, Python 3.12 CI and a new
approved original acceptance-only run; current pins and disabled trust remain unchanged.
[Proposed ADR 0006](docs/decisions/0006-connector-package-publication.md) records the
proposed split effective-permission boundary, pending owner acceptance. No package
has been published and no catalogue or remote-installation authority is added.

Production [Proxmox 0.2.0](connectors/proxmox/README.md) promotes the unchanged
**0.2.0-i4b.6** discovery implementation, qualified against **Proxmox VE 9.2.11**.
It supports Test Connection, read-only discovery, scheduling and complete snapshots:
cluster, node, QEMU and LXC Assets, canonical Networks/Interfaces and
member_of/runs_on relationships. There are no bridge or storage Assets,
connected_to or uses_storage relationships. Other source versions remain untested
with a warning; this does not claim all Proxmox 9.x versions are supported.
0.2.0 is published as the first production Connector release under the
tag `proxmox-v0.2.0` (its GitHub Release currently reports mutable). **0.1.0** was an
internal development/probe baseline, never tagged or published as a GitHub Release;
Git history preserves that state.

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
python tools/prepare_publication_verifier.py
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

The per-release `index.json` is detached version metadata governed by the
historical identity policy, not the aggregate global catalogue. [Official catalogue maintenance](catalogue/README.md) documents
the separate checked-in release registry, deterministic catalogue builder and
preparation/attestation workflow. [Lean V2 publication](catalogue/publication/README.md)
adds one isolated signed security preflight before Publisher credentials, preserving
P1 immutable snapshots, separately signed selection, single-maintainer authority
and recovery. Executable code is pinned to reviewed Lean V2 commit
`2dd1ffcd2f5677dc35bdbc8f68ea28275c91c285` (S4), merged through PR #30 with temporary
bootstrap-only Workflows Write support and S3's preserved sanitized diagnostics.
S4 passed genuine signing acceptance in run **39893809663**, with Publisher skipped
and the Publisher App at baseline permissions. Committed trust now has
`live_signer_accepted: true`, approving S4 for live publication subject to matching
independent environment trust. S3's acceptance run **39887360792** remains historical
evidence. Provider-side sequence-1 bootstrap is **completed**. Genuine
[staging run 39896288128](https://github.com/benchristian88/atlas-connectors/actions/runs/39896288128)
returned `staged_requires_separate_approval`; [activation run 39912401767](https://github.com/benchristian88/atlas-connectors/actions/runs/39912401767)
from `51f8693fbcca1e4c6c9615662bca368839ea0757` returned `bootstrapped`,
`published: true`, `immutable: true`. Release **421426993**, tag `catalogue-000001`,
is published and immutable, with its original four assets unchanged. Both
`catalogue-current` and `catalogue-bootstrap-root` resolve to parentless root
`a1597730687be993d766ddb465a0d3362aef2d02`, containing exactly `current.json`
and `current.sigstore.json`. The approved sequence **1** pointer SHA-256 remains
`a275f63d0ac818a193826478328ee324be62353addc5c97a2ed0a28d217b5372`.

The closure policy sets `bootstrap_operation: disabled`, retaining `enabled: true`,
all identities and both approved root pins. Immutable catalogue publication is
active; authorized normal `publish` and `recover` remain available under existing
signed preflight, contiguous sequence, predecessor and immutability checks.
The owner removed Publisher Workflows Write. Genuine first-attempt
[rollback verification run 39913094643](https://github.com/benchristian88/atlas-connectors/actions/runs/39913094643)
passed preflight/verify with Publisher skipped, confirming the **App registration**
at baseline; it did not independently test the installed App's effective access.
See the [production evidence and remaining operator actions](catalogue/publication/README.md#s4-deployment-and-mandatory-rollback--owner-actions-only)
for exact IDs, digests and baseline permissions. Atlas now accepts only the exact
sequence-one bootstrap under ADR 0013. Stronger future-sequence acceptance and
Atlas B3 remote installation remain outstanding. The historical closure changed
no executable code and performed no remote mutation.
Historical Proxmox **0.2.0 remains ineligible for remote installation** because its
package release is mutable. Existing catalogue-v1 assets
are preserved; that mutable legacy channel is not an accepted current source.
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

CI validates contracts, fixtures and build. The `ID-v<SemVer>` release preparation
workflow selects an explicitly packaged, qualified Connector, verifies exact
tag/Manifest identity, builds and attests the exact
bundle with the pinned GitHub `actions/attest` action, then retains a release
candidate artifact. The operator publishes those unchanged files as immutable
GitHub Release assets only after qualification. Production **0.2.0** is published
under tag `proxmox-v0.2.0`; its existing GitHub Release reports mutable. Repository identity is **benchristian88/atlas-connectors** and
signer workflow is **.github/workflows/release.yml**; Atlas must bind both, the
exact digest/source commit and authenticated Sigstore issuer/predicate evidence.

Remote acceptance still requires reviewed committed/pushed release source,
immutable assets and attestation/trust-root verification. Source qualification
does not complete those publication steps. Atlas's remote verifier remains
fail-closed. Local acceptance uses the existing Atlas bootstrap trust path with an exact packaged allowlist;
it is not a substitute claim of remote attestation verification.
