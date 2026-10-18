# Proxmox VE MVP discovery candidate 0.2.0-i4b.5

This separate candidate is **unqualified and unpublished**. Proxmox VE 9.2.11
remains **UNQUALIFIED** and `qualified_versions` is empty. Production/default
0.1.0 remains the exact Test Connection-only package.

The MVP discovers Proxmox clusters, nodes, QEMU VMs, LXC containers and network
bridges as Assets, with supported canonical Networks and Interfaces. It emits
node→cluster `proxmox.member_of`, guest→node `proxmox.runs_on` and
node/guest→bridge `proxmox.connected_to` relationships.

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
is a subsequent product scope decision; the `.1`–`.4` artifacts remain immutable.

All source operations remain bounded read-only GETs through the existing pinned
TLS session. No new endpoints, privileges, credentials, SDK/AIP extensions,
licensing changes or Atlas core changes are introduced. Debug only changes
diagnostic detail. COMPLETE still requires proof for every declared capability;
PARTIAL/failed discovery cannot authorize absence processing.
