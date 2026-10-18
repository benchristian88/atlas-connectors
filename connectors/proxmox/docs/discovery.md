# Proxmox VE 0.2.0 discovery contract

This production contract promotes the exact **0.2.0-i4b.6** discovery
implementation qualified against **Proxmox VE 9.2.11**. Only 9.2.11 is declared
qualified; every other source version remains untested and allowed with a warning.
The [qualification record](qualification.md) distinguishes accepted live evidence
from fixture coverage and outstanding deployment acceptance.

## Source access and collection reuse

The fixed `discover.yml` invokes `library/atlas_discover.py`, writing canonical
AIP NDJSON only to the private runtime-provided destination. `test_connection.yml`
invokes `library/atlas_readiness.py` for bounded authentication/version/ACL readiness
without inventory enumeration. Paths and operations are fixed by the package;
there are no callbacks, source writes, commands or input-selected entry points.

The runtime supplies community.proxmox **2.0.0**, exact SHA-256
`77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6`.
The qualified runtime baseline is `atlas-ansible-i4a-v1` / **1.2.0**, runtime
**0.3.1**, with proxmoxer **2.3.0**, ansible-core **2.19.7**, ansible-runner
**2.4.3**, SDK **1.1.0** and AIP **1.0**. The Manifest requires runtime capability
`integration-runtime-v1`, baseline >=1.2.0,<2.0.0 and SDK >=1.1.0,<2.0.0.
Atlas owns dependency installation, verification, licences and notices; collection
contents are not bundled and the Connector performs no dependency installation.

`ProxmoxAnsible._connect` constructs token authentication. The secured session is
installed before its first authenticated version read. Runtime-owned collection
methods supply cluster status, guest inventory/current config and node network
reads. The same Proxmoxer resource/session supplies bounded direct node and ACL
reads. Explicit node/kind enumeration includes empty resource seeds; failed guest
enrichment preserves validated seed inventory and prevents COMPLETE. Node version
enrichment and storage info modules are not used. Raw upstream exception strings,
response bodies and tracebacks are discarded.

## Source call matrix

All routes use GET under `/api2/json` on the configured endpoint. Discovery makes
40 requests in the ordinary two-node fixture and 46 in the representative
three-node fixture, unchanged from the qualified candidate. These are fixture
counts, not live observation counts.

| Read | Execution / required proof |
| --- | --- |
| `/version` | Collection construction and bounded AIP source version. |
| `/access/permissions?path=/access` | Before/after inventory; Sys.Audit proves unfiltered ACL visibility. |
| `/access/permissions`, `/access/acl` | Bounded transient effective-permission and unfiltered ACL snapshots before/after inventory. |
| `/access/permissions?path={root-or-relevant-ACL-path}` | Roots `/`, `/nodes`, `/vms`, `/sdn/zones/localnetwork` and relevant node/guest/bridge subpaths, before/after inventory. |
| `/cluster/status` | Initial actual deployment membership and final consistency, through cluster-status methods. |
| `/nodes` | Initial/final membership; node-network collection validation also reads it per online node. |
| `/cluster/resources?type=vm` | Initial guest seed and final guest identity/placement consistency. |
| `/nodes/{node}/network` | Pending check, collection list and pending recheck for every online node. |
| `/nodes/{node}/qemu`, `/nodes/{node}/lxc` | Explicit every-online-node/kind lists, including authorized empties; enrichment repeats nonempty seeded lists. |
| `/nodes/{node}/{qemu-or-lxc}/{vmid}/config?current=1` | Required bounded current config for every expected guest. |

`/storage` and `/nodes/{node}/storage` are neither called nor allowlisted.
There are no guest-agent calls, automatic endpoint failover or source-derived
node/bridge addresses used as alternative API destinations.

## Transport protections and limits

Verified certificates are the default. Trusted SHA-256 fingerprint mode checks
the certificate on the authenticated TLS socket before HTTP credentials are sent.
Insecure TLS is rejected and never used as fallback. DNS answers are vetted before
token use, then pinned to a permitted peer with original host/SNI checks. Private
LAN/ULA is supported; loopback, link-local, multicast, reserved/unspecified and
metadata addresses are blocked. The adapter rejects writes, redirects, endpoint
changes, unexpected routes/queries, pending guest config and compression.
Environment proxies/netrc, retries and password/ticket fallback are excluded.

Limits remain six-second connection/socket timeouts, at most 90 seconds total
discovery within the runtime budget, 12-second readiness, 1 MiB per response,
24 MiB total, 4,096 calls, 32 nodes, 1,000 list rows, 256 ACL rows/paths and
4,000 observations. Batches contain at most 200 observations and 512 KiB.
DNS/module alarms and the runtime process deadline bound execution. Limits never
silently truncate to COMPLETE. Runtime cancellation and private workspace cleanup
remain Atlas-owned.

## Classes, identity and managed mappings

| Asset class | External ID | Recommended managed Asset Type key |
| --- | --- | --- |
| `proxmox.cluster` | `cluster/deployment`, actual cluster only | `cluster` |
| `proxmox.node` | `node/{source-node-name}` | `hypervisor_node` |
| `proxmox.qemu` | `guest/qemu/{vmid}` | `virtual_machine` |
| `proxmox.lxc` | `guest/lxc/{vmid}` | `lxc_container` |

Canonical Networks (`proxmox.network`, `network/{node}/{bridge}`) and Interfaces
(`proxmox.interface`, owner ID plus source interface slot/name) are not Asset
classes. Same bridge name/CIDR on different nodes does not merge Networks;
duplicate MACs do not merge Interfaces. Standalone nodes create no fake cluster.

| Relationship class | Source → target | Recommended managed relationship key |
| --- | --- | --- |
| `proxmox.member_of` | node → cluster | `member_of` |
| `proxmox.runs_on` | QEMU/LXC guest → node | `runs_on` |

All six object classes and both relationships are required. The required
`inventory` scope covers assets, networks, interfaces and relationships.
There are exactly four Asset mappings and two relationship mappings. Managed key
recommendations never create taxonomy. The live qualification selected
`proxmox.cluster → proxmox_cluster` explicitly; the other recommended mappings
resolved directly. Administrators must inspect actual managed keys/applicability.
There is no bridge, connected_to, storage or uses_storage mapping.

Identities are local to the retained Atlas DataSource, independent of endpoint,
display labels and list order. Guest rename/migration preserves identity; VMID
reuse and genuine node renames remain source limitations. No durable deployment
UUID or cross-source identity is invented. Deployment replacement behind the same
endpoint requires a new Integration. Relationship identity hashes the ordered
class/source/target tuple. Placement changes produce a new observed edge.

## Network topology and facts

Active Linux/OVS bridges produce node-owned host Interfaces at
`node/{node}/interface/{iface}`, with explicit CIDR-derived IP/Network association.
Bridges are not Assets. Guest Interfaces retain validated `proxmox.bridge_name`,
MAC and explicit static IP evidence. Only `net0`–`net99` config entries are parsed,
using bounded strings, unique keys and strict MAC/IP/VLAN/bridge validation.
Inactive or pending bridges supply no current topology or validated attachment
and prevent COMPLETE. Pending configuration is never accepted as current state.

Only untagged, non-trunk guest interfaces with an explicit static subnet matching
the current bridge subnet gain Network membership. Tagged/trunk interfaces,
unknown/DHCP IPs and different subnets do not inherit the bridge Network.
No guest-agent addressing is inferred. Disk/rootfs/mount entries, unused volumes,
bind paths, descriptions, notes and arbitrary config are ignored. There are no
storage Assets, dependencies, capacity telemetry or storage-specific facts.

The exact Manifest fact allowlist is:

| Fact | Type / meaning |
| --- | --- |
| `proxmox.vmid` | Integer guest identity. |
| `proxmox.template` | Boolean configuration. |
| `proxmox.deployment_mode` | Informational clustered/standalone string. |
| `proxmox.power_state` | Operational running/stopped/paused string. |
| `proxmox.online` | Operational node boolean. |
| `proxmox.vlan_aware` | Boolean host Interface configuration. |
| `proxmox.vlan_tag` | Integer Interface configuration, 1–4094. |
| `proxmox.bridge_name` | Bounded validated Interface configuration identifier. |
| `proxmox.vlan_trunks` | At most 128 unique VLANs, 1–4094, sorted into a semicolon-separated string of at most 639 characters. |

No booleans, floats, signs, whitespace or Unicode digits are coerced into VLAN
integers. Invalid, empty, duplicate or oversized trunks prevent COMPLETE.
All facts are declared single scalars. Power/online state is not an Atlas
lifecycle status or an impact conclusion. Source version stays in the AIP envelope.

## COMPLETE, PARTIAL and retained knowledge

COMPLETE requires every declared class/domain and mandatory read, unique valid
identities, coherent cluster/node/guest membership and placement, successful current
guest config/interface parsing, applicable active topology, stable before/after
inventory and ACL proof, and all source/observation limits. HTTP 200 or empty lists
alone never prove complete visibility. Authorized empty guest scopes still require
per-node lists and whole-scope proof.

Effective permission dumps omit zero-permission paths. Require Sys.Audit on
`/access`, propagated inventory roots and targeted permissions for every relevant
ACL subpath, including hidden NoAccess. Effective rights are the backing-user/token
intersection. Bounded raw ACL/effective snapshots remain transient, are compared
before/after reads and are never emitted. Storage-specific permission proof is
outside scope; generic snapshot consistency remains enforced.

Unproven visibility, offline members, mandatory config/network failures, malformed
records, pending state or unresolved topology yield PARTIAL or failure. Only
Atlas's successful COMPLETE seal can invoke existing absence processing. The
Connector owns no deletion, reconciliation, acceptance or tenancy policy.
PARTIAL/failed runs preserve validated evidence and cannot cause absence.
The generic coverage identity includes declared classes/domains/scopes; the older
bridge/storage candidate scopes cannot serve as this release's absence baseline.

Diagnostics contain bounded safe reasons, never source credentials, raw responses,
ACL dumps or arbitrary config. Debug changes diagnostic detail only; observations,
relationships, warnings, completeness and ordered calls remain identical.
