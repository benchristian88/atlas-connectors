# Proxmox qualification status — 0.2.0-i4b.6

As of **18 October 2026**, `.6` is an **unqualified, unpublished** successor
candidate. `source_versions.qualification` remains `unqualified` and
`qualified_versions` remains empty. **Proxmox VE 9.2.11 remains UNQUALIFIED**.
Production/default 0.1.0 remains the exact probe-only package; I4 is incomplete.

Proxmox bridges are host networking constructs used to describe Interface and
Network topology. Atlas MVP does not model them as standalone Assets. Guest bridge
attachment remains bounded topology context on the guest Interface, and explicit
VLAN/static-network evidence is retained.

`.6` declares only cluster, node, QEMU and LXC Assets; member_of and runs_on
relationships; canonical Networks and Interfaces. There are no bridge Assets,
connected_to Asset relationships, storage Assets or storage dependencies. Host
bridge Interfaces, validated guest `proxmox.bridge_name`, explicit integer VLAN
tags, bounded trunks and conservative static Network/IP/MAC evidence remain.
No DHCP or guest-agent addressing is inferred.

Qualification plans require exactly four Asset and two relationship mappings.
No bridge/network_bridge, connected_to/connected_via or old storage mapping is
accepted. With the current taxonomy the only deliberate override remains
`proxmox.cluster → proxmox_cluster`; other recommendations exact-auto-map.
Runtime, SDK 1.1.0, AIP 1.0 and collection pins are unchanged. Normal Atlas
catalogue/activation still rejects unqualified discovery. Only the separately
authorized isolated operator process may stage/activate an exact reviewed candidate.

Historical `.3` diagnosed the storage mismatch; `.4` correctly handled legitimate
node-scoped inactive/non-applicable status; `.5` removed storage from the MVP.
The operator reports two `.5` COMPLETE runs against 9.2.11, 136 observations each,
one batch, zero warnings/errors, including a second run with Debug Off. This is
repeatable positive-path evidence, not qualification or production promotion.
Production 0.1.0 and `.1`–`.5` artifacts remain immutable. `.6` is a new product
scope decision and has no live results yet.

Fixture tests, actual Ansible Runner and reproducible packaging establish local
implementation evidence only. The synthetic `i4b-fixture` bundle's fixture-only
qualification does not qualify this candidate or any Proxmox release.

Next: review uncommitted `.6`, then separately establish a reviewed clean source
checkpoint, rebuild twice, compare and independently verify its exact digest.
Use the active live runbook to preview the four/two mapping plan, stage/activate
only in the isolated qualification instance, and run Test Connection plus manual
Debug On discovery. Inspect host vmbr0, guest bridge_name/MAC/VLAN 99/static IP,
subnet exclusions, remaining ACL proof and COMPLETE/PARTIAL behavior. Explain any
count difference from `.5` by removed bridge Assets/connected_to relationships or
actual source changes, then repeat unchanged with Debug Off. `.6` uses a different
generic coverage identity; no `.5` baseline may trigger absence for bridge objects.
Review observations in the correct Customer/Site before any explicit acceptance.
No live calls, staging/activation, commit/push, release or promotion are performed
by this implementation. Native Debian/systemd LIVE acceptance remains open.
