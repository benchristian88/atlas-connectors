# Candidate change record — 0.2.0-i4b.6 network topology MVP

**18 October 2026.** `.6` is a deliberate product scope decision after `.5`'s
repeatable operator-reported live COMPLETE baseline. `.3` diagnosed the storage
mismatch, `.4` correctly handled disabled/inactive non-applicable storage and `.5`
removed storage definitions from the MVP. Those explanations remain valid;
production 0.1.0 and all `.1`–`.5` artifacts remain immutable.

Proxmox bridges are host networking constructs used to describe Interface and
Network topology. Atlas MVP does not model them as standalone Assets. Guest bridge
attachment remains bounded topology context on the guest Interface, and explicit
VLAN/static-network evidence is retained.

The Manifest and normalizer remove `proxmox.bridge` and `proxmox.connected_to`.
Only cluster/node/QEMU/LXC Assets and member_of/runs_on relationships remain.
Host bridges become node-owned canonical Interfaces with their existing durable
identity/name and explicit current CIDR-derived IP/Network association. VLAN
awareness moves from the bridge Asset to the host Interface as the same declared
boolean fact. Valid guest attachment becomes single configuration string fact
`proxmox.bridge_name`, bounded by the existing identifier grammar and resolved on
the owning guest's node. It is not a new schema/model or hidden vendor payload.

Guest canonical MAC and explicit static IP remain. `proxmox.vlan_tag` retains
strict integer 1–4094 semantics, with no default VLAN 0 or arbitrary coercion.
`proxmox.vlan_trunks` safely retains at most 128 unique VLANs as a sorted,
semicolon-separated single string (maximum 639 characters). Invalid evidence
prevents COMPLETE. Tagged/trunk interfaces cannot inherit the bridge Network;
only untagged explicit matching static subnets prove membership. No DHCP or guest
agent IPs are inferred. No storage Assets/dependencies or workload storage facts
are emitted.

Network endpoint enumeration, relevant ACL proof, pending/current safety, source
limits and before/after consistency remain mandatory and unchanged. Missing,
inactive, pending, invalid or unavailable bridge evidence prevents unsafe COMPLETE.
Diagnostics identify host Interfaces and retain bridge/VLAN/reference validation;
normal/debug observations, warnings, completeness and source calls are identical.
The representative three-node sequence remains **46** requests; two-node **40**.

Qualification requires four Asset and two relationship mappings, with only the
cluster→proxmox_cluster override expected for current taxonomy. Removing the
bridge object class changes Atlas's existing generic coverage hash: `.5` cannot
be an absence baseline for `.6`. PARTIAL/failed absence prohibition and historical
accepted knowledge are preserved without any Proxmox policy in Atlas.

Deterministic fixtures change only their Asset/relationship observation counts:
ordinary two-node **25 → 18** (two bridge Assets and five connected_to links
removed); representative three-node **25 → 19** (three bridge Assets and three
connected_to links removed). Networks and Interface counts remain **2/5** and
**3/3**, respectively. New facts do not increase the AIP observation count.
The `.5` live count of 136 is not a `.6` fixture or live expectation.

Focused normalization/network/VLAN/discovery/diagnostics/capability/transport tests,
actual Runner and full suite, checkpoint verification, read-only Atlas mapping/
coverage/absence checks, archive audits and deterministic dual builds supply local
evidence. Exact executed commands/results, immutable-byte audits and `.6` digest
are recorded in the active repository live qualification record, outside package
contents so the archive never includes its own digest.

No Atlas core, SDK/AIP, database, taxonomy, API/UI, tenancy, credential, licensing,
source write, privilege, endpoint or dynamic dependency installation change is
required. Source authority remains Atlas-owned. Candidate-specific README/docs
still override the frozen production documents using the existing reviewed file
list; operator runbooks/tests/fixtures stay outside the archive.
`.6` and Proxmox 9.2.11 remain unqualified with qualified_versions empty. No
commit/push/merge/tag/release/staging/activation or production promotion occurs.
