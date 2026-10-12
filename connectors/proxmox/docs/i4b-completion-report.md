# I4B implementation report

12 October 2026. **0.2.0-i4b.1 is a production-quality discovery candidate**,
with deterministic collection/Ansible/AIP/I3 fixture acceptance. It is unpublished
and unqualified. **Proxmox 9.2.11 remains UNQUALIFIED; I4 is incomplete.**
Atlas production bootstrap remains **0.1.0 probe-only**. Native Debian/systemd
live acceptance remains outstanding. SDK 1.1.0/AIP 1.0 and the SDK repository
are unchanged. No commit, push, merge, Connector release or source qualification
was performed.

The [implemented behavior](discovery.md) documents source calls, collection reuse,
each isolated fallback, transport security, object/relationship/fact mapping,
identity limitations, ACL visibility proof, COMPLETE/PARTIAL rules and live gates.
The [permissions](permissions.md) and [qualification](qualification.md) documents
state the unqualified operator boundary.

All source-specific implementation lives in atlas-connectors: the fixed
playbooks/modules, secured Requests/Proxmoxer adapter, collection orchestration,
raw-flag validation, normalization, completeness and ACL readiness. Atlas changes
are approximately **8% of added executable implementation**, with **92% in this
repository**: generic source-endpoint locking and bounded probe diagnostics only.
Atlas also carries test-only candidate-derived acceptance artefacts and tests;
there is no vendor API client, normalization or completeness policy in core.

The primary tests cover clustered/standalone deployments, QEMU/LXC/templates,
rename/migration, local/shared storage, source-local subnets/bridges, duplicate
MACs, offline/permission-filtered/empty/malformed sources, API/config failures,
staging and limits. Transport tests verify credential-before-trust exclusion,
DNS pinning, redirect/write/host/query rejection, response/runtime limits,
certificate/fingerprint policies and safe errors. Actual Runner tests validate
canonical NDJSON against the unchanged SDK. Reproducible normal/candidate/test
bundles exclude fixtures from production bundles.

Atlas's test-only `i4b-fixture` bundle contains the candidate implementations with
fixture I/O injection. Its synthetic `fixture-only` qualification is solely a
harness installation marker; the actual candidate remains unqualified and normal
Atlas activation rejects it. PostgreSQL acceptance covers authenticated runtime
control, real Runner, SDK output validation, I3 receipt ingestion, evidence,
reconciliation, COMPLETE/PARTIAL seals, preservation of accepted Assets, replay,
malformed AIP, failure, limits and process-tree cancellation/cleanup.

The full cross-repository command/results, file inventory, database/API/security
review and final repository state are recorded in Atlas's
[I4B report](https://github.com/benchristian88/atlas/blob/feature/integrations-i4b-proxmox-discovery/docs/architecture/integrations/i4b-completion-report.md).
This link identifies the intended report location; the working changes are not
committed or pushed by this work.

Live qualification remains required for exact Proxmox API/ACL behavior, dedicated
privilege-separated tokens/backing users and hidden NoAccess, TLS/DNS/pins,
offline endpoints/nodes, migration/recreation/join/leave/rename, storage locality,
staging/VLAN/trunks, limits/cancellation and repeated COMPLETE/PARTIAL runs.
Physical disks, optional guest-agent enrichment and automatic endpoint failover
remain excluded. The identity policy cannot detect deployment replacement behind
an unchanged endpoint or VMID reuse as a durable recreation identity.
