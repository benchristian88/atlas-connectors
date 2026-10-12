# I4B discovery candidate

Implemented candidate **0.2.0-i4b.1**, reviewed 12 October 2026. This is a
production-quality candidate implementation with deterministic fixture acceptance.
**It is not a published or qualified production Connector. Proxmox 9.2.11 remains
UNQUALIFIED; I4 is incomplete.** Atlas's production bootstrap remains **0.1.0,
probe-only**. Native Debian/systemd live acceptance remains outstanding.

## Source access and collection reuse

The fixed `discover.yml` invokes `library/atlas_discover.py`. It emits only AIP
NDJSON into the private runtime-provided destination. No callbacks, Atlas tokens,
source writes, guest-agent calls, commands or input-selected paths are supported.

The runtime supplies the reviewed community.proxmox **2.0.0** archive identity
`sha256:77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6`,
proxmoxer **2.3.0**, SDK **1.1.0** and AIP **1.0**, on
`atlas-ansible-i4a-v1` / **1.2.0**, runtime **0.3.1**, ansible-core **2.19.7**,
ansible-runner **2.4.3**. The candidate declares the exact collection dependency.
Atlas owns dependency installation, content verification, licences and notices.
No upstream source or legacy AGPL plugin code is copied into this Connector.

The Connector reuses `ProxmoxAnsible._connect`, Proxmoxer's HTTPS token auth,
resource routing and JSON serializer. Its secured session is installed **before**
the collection's constructor performs its first authenticated `/version` read.
Info-module methods are loaded from the same protected installed collection.
The AnsiballZ package namespace is extended only to that runtime-owned path.
The safe module adapter discards upstream exception strings and tracebacks.

| Capability | Reviewed collection implementation reused | Narrow exception and reason |
| --- | --- | --- |
| Deployment | `ProxmoxClusterStatusInfoAnsible.get_cluster_status` | None. Constructor double invocation in upstream `main` is avoided. |
| Nodes | Collection `ProxmoxAnsible`/Proxmoxer resource access | Direct `/nodes` separates inventory from node-info's coupled network/version calls, preserving offline members. Node version enrichment is omitted. |
| QEMU/LXC | `ProxmoxVmInfoAnsible.get_vms_from_cluster_resources`, `get_vms_from_nodes(config=current, network=false)` | Execute each online node's QEMU and LXC list even for empty resource seeds; upstream otherwise skips them. Compare node lists to resource seeds and require every guest config. Failed aggregate enrichment retains seed inventory and makes coverage partial. |
| Storage definitions | `ProxmoxStorageInfoAnsible.get_storages` | Only list `/storage`; never named configuration requiring Datastore.Allocate. |
| Storage operational status | Same secured Proxmoxer resource/session | Read `/nodes/{node}/storage`, which has no suitable contained collection info module. No storage contents or named status/config calls. Local active pools may carry capacity/availability; shared per-node totals are omitted. |
| Bridges | `ProxmoxNodeNetworkInfoAnsible.run`, `check_network_changes` | Read changes before and after the collection list; discard affected topology if either indicates staging. |
| ACL proof | Same secured Proxmoxer resource/session | Read own effective permissions, targeted permissions and unfiltered `/access/acl`. Info modules supply no coverage proof. |

All direct reads are allowlisted inside the same session. There is no parallel
long-lived client, automatic endpoint failover or credential transmission to
node/storage/bridge addresses discovered in responses.

## Transport protections and bounds

Certificate verification is the default. Fingerprint mode hashes the certificate
on the **actual authenticated TLS socket**, before any HTTP headers are sent.
Discovery rejects `insecure`; the shipped 0.1.0 probe remains unchanged.
The DNS answer set is vetted before token use: loopback, link-local, multicast,
unspecified, reserved and metadata addresses are rejected. Private LAN/ULA peers
are supported. Every connection uses one chosen vetted IP with original-host
SNI/certificate hostname checking. Resolver results never choose another API host.

A Requests adapter carries the actual collection/Proxmoxer requests. It rejects
writes, redirects, endpoint changes, unexpected routes/query parameters, pending
guest configuration and compression. Environment proxies/netrc and retries are
excluded. Only API-token authentication is constructed, with no ticket/password
fallback. TLS errors never trigger a weaker policy.

Bounds: six-second connect/socket timeouts; at most 90 seconds total discovery
(or the smaller runtime budget), including DNS via a module alarm plus the
runtime's process deadline; 12-second readiness probes; 1 MiB per source response;
24 MiB cumulative source bytes; 4,096 calls; 32 nodes; 1,000 rows per source list;
256 ACL rows/paths; 4,000 emitted observations. Batches use at most 200 observations
and 512 KiB, below I3's limits. Facts have fixed scalar types and small fixed
counts. Limits never silently truncate to COMPLETE. Invalid/over-limit data causes
PARTIAL or a failed seal. Runtime cancellation and workspace cleanup remain I3's.

## Identity boundary

Every identity is local to the retained Atlas DataSource. Proxmox provides no
proven durable deployment UUID through these reads. Endpoint URLs and mutable
labels are not included in external IDs. Separate Integrations remain separate
sources; canonical cross-source linking remains an operator decision in Atlas.

| Object | External ID policy | Consequence |
| --- | --- | --- |
| Actual cluster | `cluster/deployment` | Stable across cluster display rename within this source. No fake cluster for standalone. |
| Node | `node/{source-node-name}` | Reviewed reads provide no durable physical host UUID. A genuine source node rename changes identity; corosync numeric IDs are deployment-local/reusable and are not invented host IDs. |
| QEMU/LXC | `guest/{qemu\|lxc}/{vmid}` | Rename and migration preserve identity. VMID reuse after destruction is a source limitation; no speculative merge or recreation identity is invented. |
| Shared storage | `storage/shared/{storage-id}` | Deduplicate only when the source definition explicitly marks shared and node status agrees when it supplies that flag. |
| Local storage | `storage/local/{node}/{storage-id}` | Same names on two nodes remain distinct. |
| Bridge | `bridge/{node}/{iface}` | A technical Asset, never automatically a logical cross-node Network. |
| Network | `network/{node}/{bridge}` | Only an explicit current bridge CIDR supplies a source-local subnet. Same bridge name, CIDR or VLAN on another node does not merge Networks. |
| Interface | Owner external ID plus source interface slot/name | Duplicate MACs do not collapse interfaces. Guest `net0` identity survives migration and rename. |
| Relationship | SHA-256 of ordered class/source/target tuple | Labels and enumeration order do not affect identity. Placement changes produce a new observed placement edge. |

Standalone-to-cluster retains source node/guest IDs and adds actual cluster context.
Replacing/reinstalling a deployment behind an unchanged address is not detectable
as a durable UUID change by these reads. Operators must create a new Integration
for another source. Atlas now conservatively locks all generic URL connection
fields after any successful source-backed discovery, including PARTIAL history.
Before that history exists, existing endpoint-edit rules apply.

## AIP mapping and current topology

Assets: `proxmox.cluster`, `proxmox.node` → `hypervisor_node`, `proxmox.qemu` →
`virtual_machine`, `proxmox.lxc` → `container`, `proxmox.storage` → `storage_pool`,
and `proxmox.bridge` → recommended `network_device`. Cluster recommends `cluster`.
Recommendations use managed stable keys; unresolved/incompatible required mappings
need explicit administrator choices. They do not create taxonomy automatically.

Networks and Interfaces use canonical fields: CIDR, interface ownership,
source-local Network membership, MAC, static IP and primary flag. Guest VLAN tags
are bounded configuration facts; tagged/trunk attachments do not acquire an
unsupported Network membership. Only untagged, non-trunk attachments with an explicit guest static subnet
matching the current bridge CIDR receive `network_external_id`. Unknown guest
IPs and differing subnets do not assert logical Network membership. Guest-agent/runtime IP enrichment is omitted.

Relationships are observed source→target: node→cluster `proxmox.member_of`,
guest→node `proxmox.runs_on`, guest→storage `proxmox.uses_storage`, and
node/guest→bridge `proxmox.connected_to`. Source power/online state is an
operational fact, never an Atlas lifecycle status or a failure-impact conclusion.
Current guest configuration uses `current=1`. Unused disks, mount contents, host
bind paths, arbitrary descriptions, command arguments, notes and raw config blobs
are not observations. Offline nodes remain observed and force aggregate partial
coverage; seed guests remain observed without claiming successful config coverage.

## Fact allowlist

Manifest-declared single scalars only: `proxmox.vmid` (integer), `template`
(boolean), `deployment_mode` (clustered/standalone), `power_state`
(running/stopped/paused), `online` (boolean), `storage_type` (bounded identifier),
`shared` (boolean), `capacity_bytes`/`available_bytes` (bounded non-negative
integers, local active pools only), `vlan_aware` (boolean), `vlan_tag` (1–4094).
The source version is carried in the canonical AIP envelope. Names are bounded;
known credential echoes are rejected before output, and I3 checks again.

## COMPLETE decision

One required `inventory` scope uses I3's dispatched aggregate key unchanged.
All declared object classes/domains must be selected and all mandatory inventory,
current configuration and topology calls must execute successfully. COMPLETE also
requires unique valid source identities, coherent node membership/guest lists,
valid applicable storage definitions/status, no offline member, no pending bridge
configuration, no unresolved required topology, no discarded malformed inventory,
no limit breach, stable inventory membership/placement between source reads, and
an unchanged ACL proof before/after collection. Volatile CPU/capacity counters and
list ordering are excluded from membership comparisons.

Effective permission dumps alone cannot prove whole-source coverage: the reviewed
[official RPCEnvironment source](https://github.com/proxmox/pve-access-control/blob/master/src/PVE/RPCEnvironment.pm)
**omits zero-permission paths**, including hidden NoAccess overrides. Require
`Sys.Audit` on `/access` to prove the
[ACL list](https://github.com/proxmox/pve-access-control/blob/master/src/PVE/API2/ACL.pm)
is unfiltered. Check the token's own targeted effective permissions (the backing
user/token intersection) on propagated inventory roots and every relevant ACL
path, including invisible objects. Exact object privileges may have propagation
zero; whole-scope roots require propagation one. Compare bounded transient ACL
and effective-permission snapshots at the end. No ACL dump is emitted or persisted.
This source-derived policy still needs qualification on the actual server release.

Any unproven visibility or mandatory per-node/enrichment failure produces PARTIAL.
An initial mandatory inventory failure or exceeded top-level limit produces a
failed seal. A completed empty guest scope is possible only with authorized
coverage and actual per-node list calls; HTTP 200/empty lists alone never qualify.
Only Atlas's successful COMPLETE seal can invoke existing Asset absence handling.
The Connector implements no absence, deletion, acceptance or reconciliation logic.

Candidate Test Connection uses bounded version/ACL reads without inventory
collection. It returns authentication success separately from readiness and
sanitized capability/privilege/path-category diagnostics. Atlas's additive generic
probe transport retains at most 16 validated identifier-only diagnostics; AIP's
unchanged diagnostic contract still uses code/domain only.

## Exclusions and live qualification

No physical disks/WWNs, storage contents, node software-version enrichment,
guest-agent calls, automatic failover, SDN logical network federation, writable
operations, cross-source merge, business objects or impact-analysis conclusions.
Inactive bridge definitions retain their known Asset identity, make coverage
partial and assert no current running topology.
No pending configuration is accepted as current topology.

Live gates remain: dedicated privilege-separated token/backing-user tests;
unfiltered ACL proof including NoAccess; exact Proxmox 9.2.11 API behavior;
verified and fingerprint TLS with changed certificates, mixed/unsafe DNS and
redirects; offline nodes/configured endpoint; migration, template/VMID reuse,
join/leave/node rename, shared/local storage and storage restrictions; staging,
VLAN/trunks/duplicate MACs; limits, cancellation and repeat COMPLETE/PARTIAL runs.
Native Debian/systemd live deployment remains a separate outstanding gate.
