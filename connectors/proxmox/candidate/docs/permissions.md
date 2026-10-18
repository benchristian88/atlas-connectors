# Proxmox MVP permissions — 0.2.0-i4b.5, unqualified

Reviewed **18 October 2026**. The existing source-derived proof applies to the
reduced declared MVP scope. **Proxmox VE 9.2.11 remains UNQUALIFIED**; this is
not a qualified installation procedure or authorization to change source ACLs.

| Required privilege | Effective path / proof |
| --- | --- |
| `Sys.Audit` | `/` for deployment and `/nodes` with propagation for node inventory, including relevant node ACL subpaths. |
| `Sys.Audit` | `/access` to prove `/access/acl` is unfiltered. Effective dumps alone omit hidden zero-permission paths. |
| `VM.Audit` | `/vms` with propagation and every relevant guest ACL subpath for inventory/current network config. |
| `SDN.Audit` | `/sdn/zones/localnetwork` with propagation and every relevant bridge subpath for bridge visibility. |

`Datastore.Audit` and targeted `/storage` permission checks are no longer required.
There are no storage inventory/status calls, storage Assets, capacity telemetry or
uses_storage relationships. No new privileges or endpoints are introduced.
Guest-agent/runtime IP enrichment remains outside scope and requires no new grant.

Effective permissions remain the backing-user/privilege-separated-token
intersection. Every relevant hidden NoAccess condition remains fail-closed.
The same bounded raw ACL/effective snapshots are compared before and after
inventory, retained only transiently and never emitted. An authorized empty guest
scope still requires actual per-node lists and whole-scope visibility proof.
Any remaining unproven capability prevents COMPLETE and therefore absence handling.

Use a dedicated non-root API token, existing verified TLS or trusted fingerprint,
DNS pinning and the unchanged request/time/size bounds. No passwords, SSH, writes,
allocation/control privileges or raw source logging are used. Readiness returns
only bounded capability/state/privilege/path-category identifiers.
See the [source call matrix and COMPLETE rules](discovery.md).
