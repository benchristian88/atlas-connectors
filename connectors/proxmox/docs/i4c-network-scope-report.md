# Proxmox .6 network topology implementation report

**Status updated 18 October 2026:** operator-reported live positive-path
qualification of **0.2.0-i4b.6** against Proxmox VE **9.2.11** has passed repeatably,
including one fail-closed TLS negative test. The exact source checkpoint is
`73f539883fe1663c332b7e6cd1cb4c054e0eae75`; the archive digest is unchanged. The
[live qualification record](i4c-live-qualification.md) contains the complete
supplied evidence, including final permission revocation.

**Live qualification evidence accepted/passed** does not change published/global
qualification or authorize production promotion. Candidate Manifest/catalogue state
remains **UNQUALIFIED**; `source_versions.qualification=unqualified`, `qualified_versions=[]`.
Production/default 0.1.0 is unchanged and remains Test Connection-only.

The implementation and local validation evidence below preserves the pre-live pass
of **18 October 2026**, implemented only in `atlas-connectors` on
`feature/i4c-proxmox-qualification`, starting and remaining at HEAD
`a153d8804c89f5184e151cef51b5f9a961f20705`. Its changes were then uncommitted and
unstaged; that pass performed no commit, push, merge, tag, release, rebase,
staging/activation or live source call. Subsequent operator checkpoint/live evidence
is recorded separately below. Packaged qualification/completion documents remain
the frozen pre-live snapshot to preserve the exact candidate archive bytes.

## Implemented model and topology

Proxmox bridges are host networking constructs used to describe Interface and
Network topology. Atlas MVP does not model them as standalone Assets. Guest bridge
attachment remains bounded topology context on the guest Interface, and explicit
VLAN/static-network evidence is retained.

`proxmox.bridge` Assets and `proxmox.connected_to` Asset relationships are removed
from emission, Manifest declarations, required scope classes and qualification
mapping requirements. No replacement pseudo-Asset or generic Resource is created.
Remaining Asset classes: `proxmox.cluster`, `proxmox.node`, `proxmox.qemu`,
`proxmox.lxc`. Remaining relationship classes: `proxmox.member_of`,
`proxmox.runs_on`. `proxmox.network` and `proxmox.interface` remain canonical AIP
classes/domains. Storage Assets, dependencies and workload storage facts remain absent.

| Evidence | Exact `.6` representation |
| --- | --- |
| Host vmbr0 | `proxmox.interface`, external ID `node/{node}/interface/vmbr0`, owner `node/{node}`, name `vmbr0`, is_primary false. |
| Host bridge VLAN awareness | Existing boolean configuration fact `proxmox.vlan_aware`, now declared on `proxmox.interface`. |
| Host explicit CIDR | Existing `proxmox.network` ID `network/{node}/vmbr0`, normalized CIDR, linked from host Interface with its explicit current IP. |
| Guest net0 | `proxmox.interface`, ID `guest/{qemu-or-lxc}/{vmid}/interface/net0`, guest owner, configured name or slot. |
| Guest bridge attachment | Declared single string configuration fact `proxmox.bridge_name=vmbr0`, maximum 64 identifier characters, only after validating an active applicable bridge on that guest's node. |
| Explicit guest VLAN 99 | Existing single integer configuration fact `proxmox.vlan_tag=99`; strict 1–4094, no coercion or implicit VLAN 0. |
| Explicit guest trunks | Declared single string configuration fact `proxmox.vlan_trunks`, sorted semicolon-separated distinct 1–4094 VLANs, maximum 128 values / 639 characters. |
| Configured MAC | Canonical `mac_address`, retained and normalized to lowercase. |
| Supported static IP/subnet | Canonical `ip_address`; only an untagged, non-trunk matching explicit subnet can link the guest Interface to the host bridge Network. |

AIP 1.0 has no dedicated bridge/trunk attachment field. Its existing declared
scalar fact mechanism preserves this context through Atlas's existing technical
Interface assertion/evidence path. There is **no architectural blocker**, SDK/schema
extension, new Atlas column/model or UI change. Bounded trunk lists outside the
reviewed grammar/limit are invalid evidence and force PARTIAL. Facts remain
reviewable source assertions, not automatic accepted knowledge or new canonical columns.

Focused tests and actual Runner retain VLAN **99**, MAC **02:00:00:00:00:01**,
static IP **10.20.0.10**, host IP **10.20.0.1**, Network **10.20.0.0/24**, and
validated bridge **vmbr0**. Tagged/trunk Interfaces never inherit that Network.
Absent/DHCP/manual IP or a different static subnet supplies no membership proof.
No DHCP inference, guest-agent call, arbitrary config ingestion or raw response
retention is introduced. Existing QEMU/LXC static-IP parsing scope is unchanged.

Missing/unresolved guest bridge references still emit the conservative warning and
prevent COMPLETE. Empty/malformed bridge identities, malformed VLAN/trunk values,
inactive/pending/offline/unavailable bridge evidence and invalid CIDR remain
fail-closed. Inactive/pending bridges emit no current Interface or validated guest
attachment. Non-bridge source rows retain existing skipped/out-of-scope behavior.

## Source calls, fixture counts and completeness

`/nodes/{node}/network` remains mandatory, with the existing pending check,
collection enumeration and pending recheck. No discovery call, endpoint, privilege
or collection/runtime dependency changes. The representative three-node sequence
is **46 requests**, byte-for-byte the same ordered paths as `.5`; ordinary two-node
is **40**, also identical.

| Deterministic fixture | Assets `.5` → `.6` | Networks | Interfaces | Relationships `.5` → `.6` | Total `.5` → `.6` | Removed evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Ordinary two-node / three guests | 8 → 6 | 2 | 5 | 10 → 5 | **25 → 18** | 2 bridge Assets + 5 connected_to links |
| Representative pve1/pve2/pve3 | 10 → 7 | 3 | 3 | 9 → 6 | **25 → 19** | 3 bridge Assets + 3 connected_to links |

Facts do not count as additional AIP observations. The representative three-node
fixture has no guest network configuration by default; the ordinary and dedicated
network_topology fixtures exercise guest/static/VLAN/trunk behavior. The `.5`
live count **136** is not hard-coded as a `.6` expected count. Later live differences
must be explained by removed bridge/connected_to observations or genuine source changes.

An archive-code audit ran the immutable `.5` implementation and `.6` on **19
scenarios each with Debug Off/On**. Every ordered request sequence, warning and
completeness result matched. Retained Assets, Networks, Interfaces and relationship
identities/fields matched after the intended removals and Interface fact additions/
relocation. The audit checks that host awareness transfers from the removed bridge
Asset and guest bridge_name agrees with the former validated attachment.
Both ordinary and three-node positive fixtures remain COMPLETE. All remaining
ACL/visibility, authentication/TLS, node/guest/placement/config, malformed-record,
pending/offline/source-limit and before/after proof protections remain in force.
Normal/debug AIP, relationships, warnings, completeness and source calls are identical.

## Generic coverage, mapping and absence proof

The read-only Atlas checks execute the actual qualification plan/mapping functions,
`scope_encoding`, baseline selector, PARTIAL absence gate and technical Interface
fact ingestion using in-memory doubles, no database connection or source call.
They inspect checked-in taxonomy seed keys: the plan has exactly **four required
Asset / two required relationship mappings**, node/QEMU/LXC/member_of/runs_on
auto-map, and only **proxmox.cluster → proxmox_cluster** needs an explicit override.
Removed bridge/network_bridge, connected_to/connected_via and storage mapping
choices are rejected. Actual instance taxonomy/applicability must still be reviewed live.

The actual generic scope encoding yields:

- `.5`: `connector:v1:39df04a5f719a955ddf87ea9794baa39cafaa29c14e4c073c7eb71b56cf2cc58`
- `.6`: `connector:v1:4f0baf29ddc6d05a01201477b68dfbf04975f920b8982ba448029258e33f2891`

The domains are unchanged. Removing the bridge object class alone changes the
hash; version/fact/relationship-specific logic is unnecessary. With `.5`'s scope
class selection narrowed it yields the same `.6` hash; class ordering does not
change it. The actual baseline selector requires equal coverage key, DataSource,
Customer and Site; the actual PARTIAL gate performs zero absence database access.
Historical bridge observations and accepted knowledge are preserved. No Proxmox
absence policy is introduced into Atlas, and no history is deleted.

## Validation actually executed

The existing pinned environment was reused: Python **3.14.7**, SDK **1.1.0**,
pytest **8.4.1**, ansible-core **2.19.7**, Runner **2.4.3**, proxmoxer **2.3.0**,
requests **2.34.2**, reviewed community.proxmox **2.0.0**. No dependency installation
was performed. Commands from `atlas-connectors`:

```bash
ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-i4c-diagnostics/collections /private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python -m pytest tests/test_proxmox_normalization.py tests/test_proxmox_discovery.py tests/test_proxmox_network.py tests/test_discovery_diagnostics.py tests/test_proxmox_capabilities.py tests/test_proxmox_transport.py -q --tb=short
ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-i4c-diagnostics/collections ATLAS_TEST_RUN_ANSIBLE=1 /private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python -m pytest tests/test_proxmox_ansible.py -q --tb=short
ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-i4c-diagnostics/collections ATLAS_TEST_RUN_ANSIBLE=1 /private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python -m pytest -q --tb=short --junitxml=/private/tmp/atlas-i4c-network-scope/full-suite.xml
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/Ben/Code/atlas/apps/api DATABASE_URL=sqlite:// /Users/Ben/Code/atlas/apps/api/.venv/bin/python -m pytest tools/atlas_reference_checks.py -q -p no:cacheprovider --tb=short --junitxml=/private/tmp/atlas-i4c-network-scope/atlas-reference.xml
/private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python tools/build_bundle.py --candidate --output /private/tmp/atlas-i4c-network-scope/candidate-a
/private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python tools/build_bundle.py --candidate --output /private/tmp/atlas-i4c-network-scope/candidate-b
cmp /private/tmp/atlas-i4c-network-scope/candidate-a/proxmox-0.2.0-i4b.6.tar.gz /private/tmp/atlas-i4c-network-scope/candidate-b/proxmox-0.2.0-i4b.6.tar.gz
cmp /private/tmp/atlas-i4c-network-scope/candidate-a/manifest.json /private/tmp/atlas-i4c-network-scope/candidate-b/manifest.json
cmp /private/tmp/atlas-i4c-network-scope/candidate-a/SHA256SUMS /private/tmp/atlas-i4c-network-scope/candidate-b/SHA256SUMS
cmp /private/tmp/atlas-i4c-network-scope/candidate-a/index.json /private/tmp/atlas-i4c-network-scope/candidate-b/index.json
/private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python tools/verify_candidate.py --directory /private/tmp/atlas-i4c-network-scope/candidate-a --expected-digest sha256:dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97
/private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python tools/build_bundle.py --output /private/tmp/atlas-i4c-network-scope/production
cmp /private/tmp/atlas-i4c-network-scope/production/proxmox-0.1.0.tar.gz dist/proxmox/proxmox-0.1.0.tar.gz
/private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python tools/build_bundle.py --candidate
git diff --check
```

Focused tests: **228 passed**. Actual Runner: **20 passed**. Full Connector suite:
**280 passed, no skips**, including checkpoint/qualification, documentation,
transport/security and all Runner cases; **180 existing Runner codecs.open
DeprecationWarnings**. Read-only Atlas checks: **8 passed**. The full-suite
JUnit and reference JUnit files are in `/private/tmp/atlas-i4c-network-scope/`.
`shasum -a 256 -c SHA256SUMS` from candidate-a also passed. Archive, detached
Manifest, SHA256SUMS and index compare exactly between both builds and the default
`.6` review output. The independent verifier accepts all **19** reviewed package
files. Native systemd/live qualification was not run or claimed by that pre-live
implementation pass; the subsequent isolated operator live evidence is recorded below.

The separate fixture audit command uses the retained local `audit_discovery.py`,
ANSIBLE_COLLECTIONS_PATH set to the reviewed collection, and isolated module paths
for preserved `.5` and current `.6`. Its 19-case JSON outputs and
`compatibility-comparison.json` are retained alongside `coverage-identity.json`,
`before.json` and `preservation.json`. These contain sanitized fixtures only.

## Candidate identity and immutable artifacts

`.6` deterministic archive SHA-256:

```text
sha256:dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97
```

Review output: `dist/proxmox-candidate-0.2.0-i4b.6/`, containing archive,
combined detached Manifest, SHA256SUMS and index. Detached provenance still carries
starting HEAD `a153d8804c89f5184e151cef51b5f9a961f20705` as context; the `.6`
implementation was then uncommitted and was **not** represented by that clean commit
or an authenticated remote attestation. The required subsequent clean checkpoint
and LXC rebuilds were completed by the operator at
`73f539883fe1663c332b7e6cd1cb4c054e0eae75`; the independent live-checkpoint verifier
returned the same digest and **19** files, with `source_qualification=unqualified`.
Historical local artifacts retain their original bytes/provenance.

Before/after SHA-256 checks preserve **28 historical artifact files**: the existing
20 dist files plus both retained four-file `.2` directories. All six historical
archive identities are unchanged; the default 0.1.0 rebuild also matches exactly.

| Immutable archive | Unchanged SHA-256 |
| --- | --- |
| `0.1.0` | `b83ec2b3938b1747d12be5f0675dbc3e9da13c6259c2ab40f5daa994ee59ea60` |
| `0.2.0-i4b.1` | `d283441dfa70d8e589fd3da868075bdb795a8cda938a78931437432b572166c8` |
| `0.2.0-i4b.2` | `3dcf374e487a65a4398fe3ec2b3c0158c9fbdeaa5c8f885b85d8c3361904ffb5` |
| `0.2.0-i4b.3` | `05c8ccb44b3964b780d3ffcef9a71a89b80ed2a5b7f4de22806ea7b0f62cf626` |
| `0.2.0-i4b.4` | `62d25b92cf694dd7a8fde320961ccd887dc29b85497c084a44fab08fe1d7d645` |
| `0.2.0-i4b.5` | `bff4a3c9c4b824ed46622153b52c433c3bf03d926bc47d8249ae8831f68fa69b` |

`.2` is preserved in `/private/tmp/atlas-i4c-diagnostics/original-2/` and its
matching reconstructed directory; the other originals remain in their existing
dist directories. Earlier artifacts are not rebuilt into or overwritten by `.6`.
Historical `.3` diagnosis, `.4` fix and `.5` product scope/live success stay truthful.

All **804 tracked Atlas files** and **16 tracked SDK files** match their pre-edit
hashes, branches and HEADs. Atlas remains clean at
`85d750b626cdfe772706a92d1f9678f26c5f4e97`; SDK remains clean at
`8b0518c462289cca4758c3b9bf362f1130928a1c` on main. No migration is required.
No API/UI route, SDK/AIP contract, tenancy/customer/site authority, token/TLS policy,
licensing boundary, runtime-control secret handling or production taxonomy changes.
Apache-2.0 Connector ownership and AGPL Atlas ownership remain intact.

## Pre-live changed files and purpose

The historical status below is the complete changed-file list for the pre-live
implementation pass. Normalization/transport files
remove Asset/link emission and update only network diagnostic identities;
Manifest/SBOM identify `.6` and declare Interface facts. Candidate README and all
five candidate docs describe the new reachable boundary and packaged completion
record. Root README, active diagnostics/live records and this report preserve
history and document the next qualification. Tests/fixtures add network/VLAN/
trunk/safety/Runner coverage and four/two mapping assertions. The verifier follows
the `.6` identity. `tools/atlas_reference_checks.py` is explicitly invoked only
with Atlas's test environment; the ordinary Connector suite does not depend on a
sibling checkout, database or copied Atlas implementation. No feature ledger in
Atlas is edited because Atlas is explicitly read-only for this task.

`git status --short`:

```text
 M README.md
 M connectors/proxmox/candidate/README.md
 M connectors/proxmox/candidate/docs/capability-matrix.md
 M connectors/proxmox/candidate/docs/discovery.md
 M connectors/proxmox/candidate/docs/i4b-completion-report.md
 M connectors/proxmox/candidate/docs/permissions.md
 M connectors/proxmox/candidate/docs/qualification.md
 M connectors/proxmox/candidate/manifest.json
 M connectors/proxmox/candidate/sbom.spdx.json
 M connectors/proxmox/docs/i4c-discovery-diagnostics.md
 M connectors/proxmox/docs/i4c-live-qualification.md
 M connectors/proxmox/module_utils/atlas_normalization.py
 M connectors/proxmox/module_utils/atlas_transport.py
 M tests/fixtures/proxmox/scenarios.json
 M tests/proxmox_fixture_transport.py
 M tests/test_discovery_diagnostics.py
 M tests/test_i4c_checkpoint.py
 M tests/test_proxmox_ansible.py
 M tests/test_proxmox_discovery.py
 M tools/verify_candidate.py
?? connectors/proxmox/docs/i4c-network-scope-report.md
?? tests/test_proxmox_network.py
?? tools/atlas_reference_checks.py
```

The new four-file `.6` dist output is ignored by Git, as earlier build outputs are.
No historical artifact, SDK file, Atlas file or production package source changed.

## Remaining limits and completed live qualification

No architectural blocker was found. Bridge attachment/trunks remain declared
Interface facts, not new canonical fields; unsupported/malformed/oversized topology
stays PARTIAL. Fixture/reference checks do not qualify a live database/runtime or
Proxmox version. Existing node rename/VMID reuse/source identity limitations remain.

The operator has now completed the clean-source dual LXC rebuild, independent
verification, exact four/two mapping plan, isolated staging/activation, Test
Connection, two manual discovery runs and permission revocation. Atlas was at
`85d750b626cdfe772706a92d1f9678f26c5f4e97`; Connector was at
`73f539883fe1663c332b7e6cd1cb4c054e0eae75`. A fresh Customer/Site and fresh Integration
were used, with the existing source identity/credential stored as a new secret
instance. No secret or certificate fingerprint value is recorded.

Both **Debug On** and **Debug Off** runs completed with **Coverage Complete / Full
scope, 100 observations, one batch and zero warnings/errors**. First-run diagnostic
counts were **75 processed / 66 accepted / 9 skipped / 0 warning / 0 error**; debug
arming automatically returned to Off. Host vmbr0 was `proxmox.interface`, guest
Interfaces retained `proxmox.bridge_name=vmbr0`, and real guest VLAN tags were
**3, 5 and 6**. No bridge Asset was observed; live searches found no `connected_to`,
`uses_storage` or `proxmox.storage`. **VLAN 99 remains fixture/test evidence only.**

The first run had `baseline_run_id=null`; the second used that first `.6` run as
baseline and created **100 evidence records, 0 reconciliation items, 0 assertions,
0 reobservations and 0 no-longer-observed results**. There was no duplicate
reconciliation work or unsafe absence. No reconciliation decisions were
accepted/rejected, so zero assertions/reobservations were expected.

A deliberately incorrect TLS certificate fingerprint failed Test Connection;
restoring the correct fingerprint restored **9.2.11 / Inventory Ready**. This is
live fail-closed TLS evidence. Authentication-secret negative testing was **not
performed** because the stored secret is hidden/non-readable and Integration fields
become immutable after successful discovery. Other live negative/mutation scenarios
are not claimed. Temporary `.6` qualification permission was revoked with history
retained. No candidate version/Manifest state, published/global qualification,
catalogue, licensing, release or production/default 0.1.0 promotion changed.
