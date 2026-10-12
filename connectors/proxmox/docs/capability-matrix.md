# Proxmox I4A capability, call and ACL review

Reviewed **12 October 2026**. This is dependency/runtime groundwork, not an
implemented discovery Connector. Production 0.1.0 remains probe-only;
**Proxmox 9.2.11 is UNQUALIFIED**. No live source acceptance was performed.

This document preserves the I4A source review. The follow-on
[I4B candidate](discovery.md) now implements secured collection reuse and records
each contained fallback, ACL proof, mapping and exclusion. Production 0.1.0 and
the unqualified live-source boundary remain unchanged.

## Exact evidence

The inspected artefact is the [Galaxy community.proxmox 2.0.0 archive](https://galaxy.ansible.com/api/v3/plugin/ansible/content/published/collections/artifacts/community-proxmox-2.0.0.tar.gz),
SHA-256 `77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6`.
Its MANIFEST and FILES identities are pinned in Atlas's
`apps/runtime/ansible/collections.lock.json`; the original archive is retained
under `vendor/collections`. The [release source](https://github.com/ansible-collections/community.proxmox/tree/988661033eaba978379f1b47f5324200e262f974)
is commit `988661033eaba978379f1b47f5324200e262f974`, tag 2.0.0, published
21 May 2026. Galaxy publishes no signature for this archive; the annotated
Git tag is unsigned. The digest establishes reviewed byte identity, not an
independent publisher attestation.

Shipped `meta/runtime.yml` requires `ansible-core >=2.17.0`; shipped README
lists testing with 2.17–2.20. Atlas retains 2.19.7. The actual shared
`plugins/module_utils/proxmox.py` enforces **proxmoxer >=2.3**. README's
installation example still says >=2.0 and must not override that source check.
Requests has no collection-imposed version bound. HTTPS needs proxmoxer and
requests; SSH extras and developer/unit-test packages are unnecessary.
Atlas pins proxmoxer 2.3.0 and requests 2.34.2, with charset-normalizer 3.5.2,
idna 3.20, urllib3 2.8.0 and certifi 2026.7.22. No collection dependencies are
declared in MANIFEST. The archive carries GPL-3.0-or-later and BSD-2-Clause
licence material, retained in the isolated Atlas runtime.

API/ACL evidence is the [official API schema](https://pve.proxmox.com/pve-docs/api-viewer/index.html)
and official source reviewed that day: pve-manager commit
`76177f3d466d9a3b6fc5180d2cf03aff1b02fecb` and pve-storage commit
`75b36a49f57fa7119a45bb69118c8c6eb58102d7`. These revisions are reference
evidence, **not proof of the exact API implementation on Proxmox 9.2.11**.
Recheck against each qualified server release and effective token ACLs.

## Calls from the shipped modules

All paths below have the prefix `/api2/json`; all listed reads use GET.
Every reviewed info module constructs `ProxmoxAnsible`, which first reads
**`/version`** to test token validity. This is an additional call even when a
module's own read is another version endpoint. API-token authentication avoids
the password `/access/ticket` workflow.

| Proposed Atlas capability/object | Exact shipped module/path and reads after `/version` | Silent permission filtering / privilege and path | Failure semantics | COMPLETE claim / later fallback |
| --- | --- | --- | --- | --- |
| Deployment / cluster context | `plugins/modules/proxmox_cluster_status_info.py`: `/cluster/status` | `Sys.Audit` on `/`; permission denial is explicit | Catches exceptions and fails the module; returns cluster/node status otherwise | No unconditional COMPLETE claim. Cluster name/corosync IDs are not a durable deployment UUID. Single-node/non-cluster identity requires a deliberate Connector identity policy; a client alone cannot manufacture stable identity. |
| Node inventory | `proxmox_node_info.py`: `/nodes`, then `/nodes/{node}/network` and `/nodes/{node}/version` **for every returned node** | `/nodes` is authenticated-user accessible, but `Sys.Audit` on `/nodes/{node}` controls stats detail. Network bridges can be silently omitted without SDN permission | No per-node exception isolation; an offline node/network/version failure aborts the aggregate module | Conditional coverage only after membership/detail/bridge visibility proof. A later isolated node-enumeration fallback may be necessary to keep offline-node inventory separate from enrichment failures. |
| Node version | Same node-info module: `/nodes/{node}/version` (plus all calls above) | Authenticated user; node availability still matters | Coupled to network/all-node enrichment | Cannot independently prove all node versions if any node is unreachable; a narrow per-node version fallback may be needed. |
| QEMU inventory | `proxmox_vm_info.py`, `type=qemu`: `/cluster/resources?type=vm`; `/nodes/{node}/qemu` for nodes seeded by visible QEMU resources. `node` argument additionally reads `/nodes` | Both resource seed and per-node guest lists omit guests lacking `VM.Audit` on `/vms/{vmid}` | QEMU exceptions fail the whole module; empty results can succeed. Seed records survive missing entries in a node list | COMPLETE requires explicit whole-scope VM visibility and node/enumeration consistency proof. No general inventory fallback is yet justified; fallback does not itself prove visibility. |
| LXC inventory | Same VM-info module, `type=lxc`: `/cluster/resources?type=vm`; `/nodes/{node}/lxc` for nodes seeded by visible LXC resources; optional `/nodes` validation | Same `VM.Audit` filtering on `/vms/{vmid}` | LXC exceptions fail the module; invisible records can produce successful empty results | Same conditional completeness requirement as QEMU. |
| Guest current configuration | VM-info with `config=current`: above inventory calls, then `/nodes/{node}/{qemu|lxc}/{vmid}/config?current=1` for each matching node-list record | `VM.Audit` on `/vms/{vmid}`; preceding lists remain filtered | One configuration read failure aborts that module invocation. A seed-only record may lack config without explicit module failure | Require current config on every expected guest. `config` defaults to `none`; `pending` uses current=0 and must not be treated as accepted current operational state. Later per-guest isolation may be needed; no fallback implemented. |
| Storage definitions, list route | `proxmox_storage_info.py` **without `storage`**: `/storage`, optionally `?type={type}` | List silently filters without `Datastore.Audit` (or write-capable `Datastore.AllocateSpace`) on `/storage/{storage}` | List exceptions propagate. Returns normalized shared/content/nodes/prune fields | Conditional COMPLETE after storage visibility proof. This is the preferred read-only definition route. No per-node availability is collected. |
| Storage definition, named route | Same module with `storage={id}`: `/storage/{storage}` through `storage.get(storage)` | **`Datastore.Allocate`**, not `Datastore.Audit`, on `/storage/{storage}` | Catches *all* exceptions and labels them "does not exist", including ACL/network errors | Do not use this route as an absence/completeness signal or grant Allocate merely to discover. Prefer the list route; document any insufficient field as a future gap. |
| Per-node storage status / availability | No suitable read-only info module in this artefact. Needed reads: `/nodes/{node}/storage` and/or `/nodes/{node}/storage/{storage}/status` | List filters by `Datastore.Audit` or `Datastore.AllocateSpace` on `/storage/{storage}`; status requires either privilege explicitly | No shipped info-module coverage to assess; node/storage failures must remain partial/failed later | **Gap: later narrow Connector-owned fallback required** if this capability is included. Storage contents/info and the broad inventory plugin do not substitute for a contained status path. |
| Bridge / node network configuration | `proxmox_node_network_info.py`: `/nodes` validation, then `/nodes/{node}/network`, optionally `?type={iface_type}`. `iface` filtering happens locally. `check_changes=true` instead makes a raw session GET to the same network endpoint | Authenticated list, **bridge rows silently filtered** by `SDN.Audit` or `SDN.Use` via `/sdn/zones/localnetwork/{bridge}` (inheritable at `/sdn/zones/localnetwork`). Sys.Audit alone is insufficient in reviewed source. SDN-inclusive filters have additional zone/fabric ACLs | Validation/read errors fail the module with exception text; named iface with no match can return an empty success | COMPLETE needs bridge visibility proof. Pending-change text is not active configuration; preserve active/pending distinction. No general network fallback currently required, but raw-session pending mode needs transport review. |
| Optional QEMU runtime IPs | VM-info with `network=true`: inventory/config reads above, then `/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces` | `VM.GuestAgent.Audit` or broader `VM.GuestAgent.Unrestricted` on `/vms/{vmid}` in reviewed schema | Agent unavailable/stopped/unconfigured or ACL failure can fail the entire QEMU call | Optional enrichment only; **never part of mandatory base inventory**. Later per-guest isolation may need a narrow fallback. Guest runtime IP absence is not interface/guest deletion. |
| Optional LXC runtime IPs | VM-info with `network=true`: `/nodes/{node}/lxc/{vmid}/interfaces` after inventory calls | `VM.Audit` on `/vms/{vmid}` | Read/offline failure can fail the LXC invocation | Optional enrichment, separated from base coverage; do not infer absence. |

## Completeness and transport boundaries

No module returns an Atlas coverage/ACL proof. HTTP 200, an empty list or two
agreeing permission-filtered lists cannot prove absence. Future I4 must inspect
the token's own effective `/access/permissions`, establish visibility for the
declared scope, reconcile cluster/member/enumeration/config outcomes and make
every required subread succeed before claiming COMPLETE. Unknown privilege
coverage, offline members, missing config or partial enrichment must preserve
prior knowledge through existing I3 partial/failed semantics. No SDK, AIP or I3
semantics change is needed for that future work.

The five reviewed modules do not reproduce Atlas's established DNS peer pinning,
redirect rejection, fingerprint-before-credential verification or response-size
limits. `validate_certs`/`ca_path` alone do not satisfy that model. A fingerprint
precheck followed by independently resolving Proxmoxer would weaken protection.
Future discovery needs a transport design and tests inside the isolated runtime;
I4A adds no transport wrapper, direct client, playbook or inventory implementation.

## External operational reference review

- [Official access control](https://pve.proxmox.com/pve-docs/chapter-pveum.html)
  and the endpoint source above govern privilege-separated token intersection,
  filtering and ACL paths. Consequence: test visibility explicitly, and include
  bridge SDN ACLs rather than assuming the provisional three-privilege role.
- [Home Assistant setup](https://www.home-assistant.io/integrations/proxmoxve/),
  reviewed 12 October 2026, recommends monitor/control roles for its broader
  feature set. Consequence: keep Atlas's dedicated token and read-only custom
  role; do not adopt its VM control privileges or password workflow.
- [Community permissions](https://github.com/dougiteixeira/proxmoxve/blob/main/docs/permissions.md)
  and [release 5.3.3](https://github.com/dougiteixeira/proxmoxve/releases/tag/5.3.3)
  (5 October 2026) distinguish optional guest-agent permissions and warn about
  root-scoped reads. Consequence: isolate optional guest IP failures and qualify
  privilege names per supported release. No community or legacy AGPL code copied.
- [Issue 613](https://github.com/dougiteixeira/proxmoxve/issues/613), reporting
  blocking synchronous reads with integration 4.0.2 / Proxmox 9.1.4, reinforces
  bounded source timeouts and the existing I3 cancellation/process cleanup
  boundary. It is secondary failure evidence, not a demonstrated Atlas defect.
- [Discussion 587](https://github.com/dougiteixeira/proxmoxve/discussions/587),
  started 15 November 2025 with replies in March 2026, reports configured-host
  outage and duplicate entities when adding another cluster endpoint. Shared
  storage deduplication and stable deployment identity need future qualification
  fixtures. Its suggested source-side VIP script was explicitly untested and
  disputed; Atlas adopts no source-side script or write operation. The current
  [issue index](https://github.com/dougiteixeira/proxmoxve/issues) also lists
  startup fallback issue 692 (22 September 2026); no unseen details are assumed.

The capability matrix is source-derived groundwork. Every conditional COMPLETE
criterion remains unqualified until proved against an actual supported source.
