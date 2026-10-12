# Proxmox permission baseline — I4A, unqualified

Reviewed 12 October 2026 against the exact collection and official API sources
in the [capability matrix](capability-matrix.md). **Proxmox 9.2.11 remains
UNQUALIFIED; production discovery is disabled.** These are proposed privilege
requirements, not a qualified operator installation procedure.

Production 0.1.0 still reads only its own `/access/permissions` and `/version`.
It needs no new discovery role or collection dependency. Preserve its dedicated
`pve` account/token, Privilege Separation, certificate verification/fingerprint,
DNS peer pinning, redirect rejection and response/time bounds.

For future whole-deployment discovery, the source-derived candidate minimum is:

| Privilege | Effective ACL path | Purpose / qualification condition |
| --- | --- | --- |
| `Sys.Audit` | `/` for cluster status; inherited `/nodes/{node}` for node stats | Cluster status checks `/` directly. Node-only grants do not satisfy that read. |
| `VM.Audit` | `/vms` with propagation, or every explicitly in-scope `/vms/{vmid}` | Guest resource/list visibility and current QEMU/LXC configuration. A few per-guest grants prove only that explicit guest scope, not whole-cluster coverage. |
| `Datastore.Audit` | `/storage` with propagation, or each in-scope `/storage/{id}` | Filtered storage definitions/list and future per-node status reads. |
| `SDN.Audit` | `/sdn/zones/localnetwork` with propagation, or each `/sdn/zones/localnetwork/{bridge}` | Reviewed node network code always filters bridge/OVSBridge rows through SDN bridge permission checks. Verify path/privilege inheritance on every supported version. Wider SDN discovery is outside this baseline. |
| Optional `VM.GuestAgent.Audit` | Only opted-in QEMU `/vms/{vmid}` | Runtime IP enrichment, with running/configured agent. Do not require for base discovery. Older releases may use different privileges; no old-version compatibility is claimed. |

Effective privileges are the intersection of backing-user and privilege-separated
token permissions. Verify the token's own effective permissions, not merely the
user's role. No root/admin, password fallback, SSH, VM control, storage allocation
or unrestricted guest-agent permission is proposed. `SDN.Use`,
`Datastore.AllocateSpace` and `VM.GuestAgent.Unrestricted` may satisfy certain API
checks but are broader alternatives, not Atlas's proposed read-only baseline.

The named storage-definition route requires `Datastore.Allocate`; avoid it and
use the definition list route. Its module also reports permission/transport
errors as "does not exist". That message is never trustworthy absence evidence.

An empty success can hide guests, storage or bridges. Future I4 must prove all
required paths and scoped visibility before COMPLETE. Unknown/unproven coverage
stays partial/failed and must not trigger absence or deletion. A final copyable
role/token setup is deferred until live source qualification establishes the
actual required paths. No operator ACL changes are performed by I4A.
