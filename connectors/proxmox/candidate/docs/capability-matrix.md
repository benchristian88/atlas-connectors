# Proxmox MVP capability matrix — 0.2.0-i4b.6

Reviewed **18 October 2026** against the checked-in Connector and the same pinned
community.proxmox 2.0.0 artifact reviewed for I4A/I4B. This is an implemented
candidate boundary, not new upstream API/version qualification. **Proxmox 9.2.11
remains UNQUALIFIED**. Production/default 0.1.0 remains probe-only and immutable.

| Capability | Existing implementation / collection reuse | COMPLETE requirement |
| --- | --- | --- |
| Actual cluster | `ProxmoxClusterStatusInfoAnsible.get_cluster_status` | Coherent actual deployment/member records and final consistency check; no synthetic standalone cluster. |
| Nodes | Same secured Proxmoxer `/nodes` resource | Unique bounded identities, status, membership and final consistency; offline members force PARTIAL. |
| QEMU VMs and LXC containers | `ProxmoxVmInfoAnsible` resource seed, node lists and current config | Explicit every-online-node/kind enumeration including empties, matching seed/list identities, valid placement, successful bounded current config and final consistency. |
| Host bridge Interfaces | `ProxmoxNodeNetworkInfoAnsible.run` and `check_network_changes` | Before/after pending checks, valid flags/identity/CIDR, applicable active topology and bridge ACL proof. Inactive bridges force PARTIAL with no current topology; no bridge Asset is emitted. |
| Networks / Interfaces | Existing explicit canonical AIP normalization | Explicit host CIDR/IP association, guest MAC/static IP, validated bridge_name and VLAN tag/trunk facts; no inferred DHCP/tagged/trunk membership. |
| Relationships | Explicit observed member_of, runs_on only; no connected_to | Stable ordered semantic identity and resolvable retained endpoints. |
| ACL coverage / readiness | Existing bounded effective/targeted permission reads and unfiltered ACL proof | Propagated remaining roots, hidden relevant NoAccess checks and unchanged before/after snapshots. |
| Storage definitions/pools | **Outside MVP; not Assets/resources in AIP** | No storage mapping, inventory/status reads, capacity telemetry, uses_storage relationship or storage-specific completeness requirement. |

Proxmox storage definitions are configuration/resources exposed by the
virtualisation platform. Atlas MVP does not model them as standalone Assets.
Backing storage infrastructure should be discovered by the integration responsible
for that infrastructure where available.

No backing NAS/backup system is inferred from a storage name. No storage dependencies
are represented. Atlas may introduce a richer resource/dependency model later.
Guest disks/rootfs/mounts are ignored without storage resolution warnings.

The [discovery specification](discovery.md) contains the complete source call
matrix, four Asset classes, two relationship classes, nine fact declarations,
identity boundaries, exact dependency/runtime pins and unchanged safety limits.
The [permission baseline](permissions.md) removes only storage-specific privileges
and checks. The fixed transport no longer allowlists `/storage` or per-node storage.

`.4` remains valid historical work for disabled/inactive non-applicable local-zfs
on pve3. `.5` removed storage definitions and achieved repeatable live COMPLETE.
`.6` separately removes bridge Assets while preserving topology. Production 0.1.0,
all `.1`–`.5` artifacts and the original dated production documents remain unchanged.

Proxmox bridges are host networking constructs used to describe Interface and
Network topology. Atlas MVP does not model them as standalone Assets. Guest bridge
attachment remains bounded topology context on the guest Interface, and explicit
VLAN/static-network evidence is retained.
