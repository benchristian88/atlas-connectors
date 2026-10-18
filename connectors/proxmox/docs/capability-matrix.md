# Proxmox VE 0.2.0 capability matrix

The production contract promotes the unchanged implementation qualified live
against **Proxmox VE 9.2.11** on **18 October 2026**. Only that exact source
version is supported by the SDK compatibility check. Other versions are untested
and allowed with a warning. The pinned community.proxmox **2.0.0** collection is
runtime-owned, not bundled in the Connector.

| Capability | Implementation / collection reuse | COMPLETE requirement |
| --- | --- | --- |
| Actual cluster | `ProxmoxClusterStatusInfoAnsible.get_cluster_status` | Coherent actual deployment/member records and final consistency; no synthetic cluster for standalone nodes. |
| Nodes | Secured Proxmoxer `/nodes` resource | Unique bounded identity, status and membership; offline members force PARTIAL. |
| QEMU VMs and LXC containers | `ProxmoxVmInfoAnsible` resource seed, per-node lists and current config | Enumerate every online node/kind, including empty lists; match seed/list identities and placement; validate current config and final consistency. |
| Host bridge Interfaces | `ProxmoxNodeNetworkInfoAnsible.run` and `check_network_changes` | Pending checks before/after reads, valid flags/identity/CIDR, active topology and bridge ACL proof. Inactive bridges force PARTIAL without current topology. |
| Networks / Interfaces | Explicit canonical AIP normalization | Host CIDR/IP evidence, guest MAC/static IP, validated bridge_name and VLAN facts; no inferred DHCP or tagged/trunk subnet membership. |
| Asset relationships | `proxmox.member_of`, `proxmox.runs_on` only | Stable ordered semantic identity and resolvable retained endpoints. |
| ACL coverage | Effective/targeted permissions and unfiltered ACL proof | Propagated roots, hidden relevant NoAccess checks and unchanged before/after snapshots. |
| Test Connection | `atlas_readiness` bounded version/authentication/ACL probe | Authentication and readiness reported separately; no inventory enumeration. |
| Scheduling / complete snapshots | Manifest declarations consumed by the existing Atlas runtime | Successful execution of all declared scope/domain proofs; PARTIAL/failed runs cannot trigger absence. |
| Storage | Outside the release scope | No storage Assets, calls, capacity telemetry, facts, dependencies or storage-specific permission checks. |

The Asset classes are cluster, node, QEMU and LXC. Networks and Interfaces are
separate canonical domains. Bridges are host network constructs, not Assets;
there is no connected_to Asset relationship. Guest disk/rootfs/mount values are
ignored without storage resolution warnings. No backing NAS or backup system is
inferred from a source storage name.

The [discovery specification](discovery.md) records all source reads, identities,
four Asset and two relationship mappings, nine facts, dependency pins and limits.
The [permission baseline](permissions.md) retains SDN/bridge visibility proof even
though bridges are no longer Assets.

Repeatable positive live qualification and the fail-closed fingerprint mismatch
are recorded in [qualification](qualification.md). Fixture/Runner checks cover
additional failure and topology cases; they do not establish live execution of
those scenarios. Authentication-secret negative testing was not performed.
Native Debian/systemd LIVE acceptance remains outstanding.
