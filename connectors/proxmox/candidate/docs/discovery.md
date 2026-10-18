# Proxmox MVP discovery specification — 0.2.0-i4b.5

Reviewed **18 October 2026**. This candidate is **unqualified and unpublished**;
**Proxmox VE 9.2.11 remains UNQUALIFIED**, with no qualified source versions.
Production/default 0.1.0 remains byte-identical and probe-only.

## Product model

Proxmox storage definitions are configuration/resources exposed by the
virtualisation platform. Atlas MVP does not model them as standalone Assets.
Backing storage infrastructure should be discovered by the integration responsible
for that infrastructure where available.

Names such as local, local-lvm, local-zfs, synology-vmdata, synology-backup,
synology-immich and pbs-backup do not identify independent infrastructure Assets.
The Connector makes no inference about a NAS, backup server or SAN behind them.
No storage capacity telemetry, storage-pool Assets, `proxmox.uses_storage`
relationships or workload storage facts are collected/emitted. Storage dependencies
are not represented. Atlas may introduce a richer resource/dependency model later.

The `.4` fix correctly excluded the non-applicable disabled/inactive local-zfs
status row on pve3 under its then-declared storage scope. `.5` deliberately removes
that entire capability. `.4` and all previous artifacts remain immutable.

## Source access and collection reuse

The fixed `discover.yml` invokes `library/atlas_discover.py`, writing AIP NDJSON
only to the private runtime-provided destination. The runtime supplies the exact
reviewed community.proxmox **2.0.0** collection, SHA-256
`77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6`,
proxmoxer **2.3.0**, SDK **1.1.0**, AIP **1.0**, ansible-core **2.19.7** and Runner
**2.4.3**, on `atlas-ansible-i4a-v1` / **1.2.0**, runtime **0.3.1**.
Atlas owns dependency installation, verification, licences and notices.

`ProxmoxAnsible._connect` constructs token authentication. The secured session is
installed before its authenticated version read. Runtime-owned collection methods
provide cluster status, guest inventory/current config and node network reads;
the same Proxmoxer resource/session supplies bounded direct nodes and ACL reads.
No storage info module is loaded. Upstream exception strings/bodies are discarded.

## Source call matrix

All routes have prefix `/api2/json`, use GET, and stay on the configured endpoint.
The actual representative three-node fixture performs **46 requests**, compared
with `.4`'s 52. The removed requests are one `/storage`, three per-node storage
lists and two targeted storage-root ACL checks. No new source endpoint is added.

| Read | Execution / retained proof |
| --- | --- |
| `/version` | Once during collection construction and once for the bounded AIP source version. |
| `/access/permissions?path=/access` | Before and after inventory; requires Sys.Audit for unfiltered ACL visibility. |
| `/access/permissions` | Before and after inventory; transient effective-permission snapshot. |
| `/access/acl` | Before and after inventory; bounded unfiltered ACL snapshot. |
| `/access/permissions?path={root-or-relevant-ACL-path}` | Roots `/`, `/nodes`, `/vms`, `/sdn/zones/localnetwork`, plus relevant node/guest/bridge ACL subpaths, before and after inventory. No storage-root/subpath checks. |
| `/cluster/status` | Initial deployment membership and final consistency check, via cluster-status info methods. |
| `/nodes` | Initial/final membership; existing node-network collection validation also reads it once per online node. |
| `/cluster/resources?type=vm` | Initial guest seed and final guest identity/placement consistency check. |
| `/nodes/{node}/network` | Three reads per online node: pending-change check, collection list, pending-change recheck. |
| `/nodes/{node}/qemu` and `/nodes/{node}/lxc` | Explicit lists for every online node/kind including authorized empties; collection enrichment repeats each nonempty seeded list. |
| `/nodes/{node}/{qemu-or-lxc}/{vmid}/config?current=1` | Bounded current config read for each expected guest, required for interface parsing/topology. |
| `/storage`, `/nodes/{node}/storage` | **Not called or allowlisted in .5.** Definitions/status/availability/capacity are outside its declared scope. |

Before/after ACL snapshots retain the existing generic consistency protection.
Storage-specific visibility is not required. Existing list/ACL/request bounds
remain fail-closed; permissions alone never substitute for inventory execution.

## Transport and safety

Verified TLS is the default. Fingerprint mode checks the leaf certificate on the
authenticated socket before credentials are sent; discovery rejects insecure TLS.
DNS answers are vetted before token use and pinned to one permitted peer, retaining
host/SNI checks. Private LAN/ULA is supported; loopback, link-local, multicast,
reserved/unspecified and metadata addresses are blocked. No redirects, retries,
proxies/netrc, password fallback, guest agent, commands or source writes are used.

Existing limits are unchanged: six-second connection/socket timeout, total
discovery budget at most 90 seconds (also bounded by runtime/process alarms),
12-second readiness, 1 MiB per response, 24 MiB total, 4,096 calls, 32 nodes,
1,000 list rows, 256 ACL rows/paths and 4,000 observations. Batches contain at
most 200 observations and 512 KiB. No silent truncation can earn COMPLETE.
No credentials, raw source responses, arbitrary configuration or volume strings
are logged, serialized into facts or retained in diagnostic detail.

## Manifest classes, identity and mapping

| Asset class | External ID | Recommended managed Asset Type key |
| --- | --- | --- |
| `proxmox.cluster` | `cluster/deployment` for an actual cluster only | `cluster` |
| `proxmox.node` | `node/{source-node-name}` | `hypervisor_node` |
| `proxmox.qemu` | `guest/qemu/{vmid}` | `virtual_machine` |
| `proxmox.lxc` | `guest/lxc/{vmid}` | `lxc_container` |
| `proxmox.bridge` | `bridge/{node}/{iface}` | `network_device` |

Networks (`proxmox.network`, `network/{node}/{bridge}`) and Interfaces
(`proxmox.interface`, owner external ID plus interface slot/name) remain canonical
AIP domains, not Asset classes requiring taxonomy mappings. Same bridge/CIDR on
different nodes does not merge Networks; duplicate MACs do not merge Interfaces.

| Relationship class | Source → target | Recommended managed relationship key |
| --- | --- | --- |
| `proxmox.member_of` | node → cluster | `member_of` |
| `proxmox.runs_on` | QEMU/LXC guest → node | `runs_on` |
| `proxmox.connected_to` | node/QEMU/LXC guest → bridge | `connected_to` |

Every mapping is required; recommendations use stable keys and never create or
delete global taxonomy. Qualification plans require exactly five Asset mappings
and three relationship mappings. No `proxmox.storage → storage_pool` or
`proxmox.uses_storage → uses_storage` mapping is declared or required.

Identities remain local to the retained Atlas DataSource, independent of endpoint,
display names and list order. Guest rename/migration preserve identity; VMID reuse
and genuine node renames remain documented source limitations. No deployment UUID
or cross-source identity is invented. Relationship identity remains SHA-256 of
the ordered class/source/target tuple. Standalone nodes create no fake cluster.

## Guest parsing, topology and fact allowlist

Guest config must remain an object and every required bounded read must succeed.
Only `net0`–`net99` entries are parsed, with the existing bounded string, unique
key/value, MAC/IP, VLAN and bridge checks. Disk/mount entries (`ide*`, `sata*`,
`scsi*`, `virtio*`, `rootfs`, `mp*`), unused volumes, bind paths and arbitrary
config are ignored. They create no Assets, relationships, storage warnings or
PARTIAL result solely because a storage identifier cannot be resolved.

Bridge CIDRs provide explicit source-local Networks. Only an untagged, non-trunk
guest interface with a matching explicit static subnet gains Network membership.
DHCP/unknown IPs, tagged/trunk links and different subnets do not infer membership.
Inactive bridges retain identity, force PARTIAL and assert no running topology;
pending configuration is excluded from current topology. Guest/node→bridge
connectivity and guest placement keep their existing semantics.

The only declared facts are `proxmox.vmid` (integer), `proxmox.template` (boolean),
`proxmox.deployment_mode` (clustered/standalone), `proxmox.power_state`
(running/stopped/paused), `proxmox.online` (boolean), `proxmox.vlan_aware`
(boolean) and `proxmox.vlan_tag` (1–4094). No storage-specific fact remains.
Source power/online state is an operational fact, never an Atlas lifecycle status
or impact conclusion. Source version remains in the canonical AIP envelope.

## COMPLETE and PARTIAL

COMPLETE means complete for every class/domain `.5` actually declares and
dispatches in its required `inventory` scope. All mandatory reads, ACL proof,
unique source identities, coherent cluster/node/guest membership and placement,
guest config/interface parsing, bridge/applicable network topology, before/after
inventory and ACL consistency, and all source/observation limits must pass.
Offline/unavailable required state, malformed records, hidden relevant NoAccess,
unproven visibility, pending network state and unresolved topology remain PARTIAL
or failed. Nothing makes a retained capability easier to mark COMPLETE.

Storage inventory/status/resolution is outside this declared scope and no longer
participates in storage-specific completeness decisions. Storage API failures
cannot affect discovery because those endpoints are never requested.
The generic ACL snapshot consistency rule is retained unchanged.

Effective permission dumps omit zero-permission paths. The existing proof requires
Sys.Audit on `/access`, propagated permissions on all remaining roots, checks on
every relevant ACL subpath, and unchanged transient snapshots before/after reads.
No ACL dump is emitted. HTTP 200/empty lists alone cannot prove completeness.

Only Atlas's successful COMPLETE seal can invoke existing absence processing.
PARTIAL/failed seals preserve validated evidence and prohibit absence processing
exactly as before. The Connector has no deletion, reconciliation or acceptance
policy. No database, tenancy, API/UI, SDK/AIP or licensing change is needed.

## Diagnostics and live gates

Normal/debug discovery produces identical observations, relationships, warnings,
completeness and ordered source calls; only bounded safe diagnostic detail differs.
There are no storage-definition/status/guest-storage diagnostic stages in `.5`.
The generic sidecar architecture, redaction, one-shot admin debug and retention
remain unchanged. Historical `.3`/`.4` storage diagnostics remain historical evidence.

Fixture/Runner validation does not qualify a source. Live qualification must
separately verify the exact `.5` digest, mappings, token/backing-user intersection,
NoAccess handling, TLS/fingerprint/DNS protections, cluster/standalone inventory,
VM/LXC/templates and retained topology, offline/pending/partial behavior,
identity/repeatability and limits. Native Debian/systemd LIVE acceptance remains
outstanding. No automatic reconciliation acceptance or 0.2.0 promotion is authorized.
