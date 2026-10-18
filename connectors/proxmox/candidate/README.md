# Proxmox VE MVP discovery candidate 0.2.0-i4b.6

This separate candidate is **unqualified and unpublished**. Proxmox VE 9.2.11
remains **UNQUALIFIED** and `qualified_versions` is empty. Production/default
0.1.0 remains the exact Test Connection-only package.

The MVP discovers only Proxmox clusters, nodes, QEMU VMs and LXC containers as
Assets. It emits node→cluster `proxmox.member_of` and guest→node `proxmox.runs_on`.
There are no `proxmox.bridge` Assets or `proxmox.connected_to` Asset relationships.

Proxmox bridges are host networking constructs used to describe Interface and
Network topology. Atlas MVP does not model them as standalone Assets. Guest bridge
attachment remains bounded topology context on the guest Interface, and explicit
VLAN/static-network evidence is retained.

Active host bridges remain node-owned `proxmox.interface` observations with stable
identity, name, VLAN awareness and explicit IP/Network association where CIDR is
known. Guest Interfaces keep owner/slot identity, configured name/MAC/static IP,
validated `proxmox.bridge_name`, integer `proxmox.vlan_tag` (1–4094), and bounded
`proxmox.vlan_trunks` where explicitly configured. Only an untagged, non-trunk
static subnet match proves guest Network membership. No DHCP or guest-agent IPs
are inferred. `/nodes/{node}/network` and all existing network proofs remain.

Proxmox storage definitions are configuration/resources exposed by the
virtualisation platform. Atlas MVP does not model them as standalone Assets.
Backing storage infrastructure should be discovered by the integration responsible
for that infrastructure where available.

No storage-pool Assets, `proxmox.uses_storage` relationships, storage capacity
telemetry or workload storage facts are produced. No storage dependencies are
represented. Disk/rootfs/mount values are ignored; raw volumes and arbitrary
configuration never enter observations or diagnostics. Atlas may introduce a
richer resource/dependency model later. A storage definition is not proof of a
Synology NAS, Proxmox Backup Server or other backing infrastructure Asset.

See the [discovery specification and source call matrix](docs/discovery.md),
[capabilities](docs/capability-matrix.md), [permissions](docs/permissions.md),
[qualification status](docs/qualification.md) and
[candidate change record](docs/i4b-completion-report.md).

The `.4` normalization fix remains valid historical qualification work. It handled
the legitimate disabled/inactive, non-applicable pve3/local-zfs status row. `.5`
is a subsequent storage scope decision and achieved two operator-reported live
COMPLETE runs (136 observations each). `.6` makes a separate bridge Asset scope
decision. Production 0.1.0 and `.1`–`.5` artifacts remain immutable; positive-path
`.5` evidence does not qualify `.5`, `.6` or Proxmox 9.2.11.

All source operations remain bounded read-only GETs through the existing pinned
TLS session. No new endpoints, privileges, credentials, SDK/AIP extensions,
licensing changes or Atlas core changes are introduced. Debug only changes
diagnostic detail. COMPLETE still requires proof for every declared capability;
PARTIAL/failed discovery cannot authorize absence processing.
