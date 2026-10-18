# Proxmox qualification status — 0.2.0-i4b.5

As of **18 October 2026**, `.5` is an **unqualified, unpublished** successor
candidate. `source_versions.qualification` remains `unqualified` and
`qualified_versions` remains empty. **Proxmox VE 9.2.11 remains UNQUALIFIED**.
Production/default 0.1.0 remains the exact probe-only package; I4 is incomplete.

`.5` implements the deliberate [MVP product boundary](discovery.md): cluster,
node, QEMU, LXC and bridge Assets; canonical Networks/Interfaces; member_of,
runs_on and connected_to relationships. No storage definitions/pools, capacity
telemetry, uses_storage links or storage dependencies are represented.
The `.4` inactive/non-applicable pve3/local-zfs normalization fix remains valid
historical qualification work under its earlier scope. `.1`–`.4` remain unchanged.

Qualification plans now require exactly five Asset and three relationship
mappings; no storage mappings. Runtime, SDK 1.1.0, AIP 1.0 and exact collection
dependency are unchanged. The normal Atlas catalogue/activation still rejects
unqualified discovery. Only the separately authorized isolated operator
qualification process may stage/activate an exact reviewed candidate.

Fixture tests, actual Ansible Runner and reproducible packaging establish local
implementation evidence only. The synthetic `i4b-fixture` bundle's fixture-only
qualification does not qualify this candidate or a Proxmox release.

Next: review uncommitted `.5`, then separately establish a reviewed clean source
checkpoint, rebuild twice, compare and independently verify its exact digest.
Use the active live runbook in the repository to plan only the remaining mappings,
then stage/activate only in the isolated qualification instance. Test Connection
and manual discovery must prove every remaining ACL, inventory and topology rule;
PARTIAL must preserve accepted knowledge without absence processing. Review
observations in the correct Customer/Site before any explicit acceptance.
No live qualification, source calls, commit/push, release or promotion is performed
by this contained implementation. Native Debian/systemd LIVE acceptance remains open.
