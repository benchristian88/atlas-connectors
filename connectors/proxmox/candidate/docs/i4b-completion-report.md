# Candidate change record — 0.2.0-i4b.5 MVP scope

**18 October 2026.** `.5` is a deliberate product scope decision after the valid
`.4` normalization fix, not a reinterpretation of that earlier defect. All prior
candidate artifacts and production/default 0.1.0 remain immutable.

The active Manifest and normalizer remove `proxmox.storage`,
`proxmox.uses_storage`, and the storage-only storage_type/shared/capacity_bytes/
available_bytes facts. Discovery removes the definition reader, per-node storage
status reads and storage-specific ACL roots/checks. The transport rejects those
inventory routes. Guest config still supplies bounded network-interface topology,
while disk/rootfs/mount values are ignored without storage resolution warnings.

The remaining five Asset classes and three relationships, canonical Networks and
Interfaces, source identity/placement, authorization proof, consistency checks,
TLS, limits and PARTIAL/failed absence prohibition retain their existing behavior.
See [discovery and source call matrix](discovery.md), [capabilities](capability-matrix.md),
[permissions](permissions.md) and [qualification status](qualification.md).

Proxmox storage definitions are configuration/resources exposed by the
virtualisation platform. Atlas MVP does not model them as standalone Assets.
Backing storage infrastructure should be discovered by the integration responsible
for that infrastructure where available.

No storage capacity telemetry, storage-pool Assets, uses_storage relationships,
workload storage facts or current storage dependencies are represented. Atlas may
introduce a richer resource/dependency model later. There is no SDK/AIP, Atlas core,
global taxonomy, database, API/UI, licensing or generic diagnostics architecture
change. No source writes, new privileges or new source endpoints are introduced.

Candidate-specific README/docs override the historical shared production package
documents using an explicit reviewed file list. This keeps default 0.1.0 bytes
unchanged and makes `.5`'s packaged contract/documentation agree. Operator runbooks,
tests, fixtures and local reports remain excluded from the candidate archive.
Local validation results and exact artifact hashes are recorded in the active
repository live qualification record, outside immutable package contents.
