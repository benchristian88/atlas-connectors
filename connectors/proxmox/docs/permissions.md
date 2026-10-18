# Proxmox VE 0.2.0 permissions

The unchanged discovery permission proof was exercised on the positive live path
against **Proxmox VE 9.2.11**. Other source versions remain untested. Use a
dedicated non-root API token with Privilege Separation. Effective rights are the
intersection of the backing user's and token's permissions; a user role alone
does not prove the token's whole-deployment visibility.

| Required privilege | Effective path / proof |
| --- | --- |
| `Sys.Audit` | `/` for deployment and `/nodes` with propagation for node inventory, including relevant node ACL subpaths. |
| `Sys.Audit` | `/access` to prove `/access/acl` is unfiltered; effective dumps omit hidden zero-permission paths. |
| `VM.Audit` | `/vms` with propagation and every relevant guest ACL subpath for inventory/current network config. |
| `SDN.Audit` | `/sdn/zones/localnetwork` with propagation and every relevant bridge subpath for bridge visibility. |

`/nodes/{node}/network` remains mandatory for host Interfaces, explicit CIDR
Networks, guest bridge validation and pending/current safety. SDN/bridge ACL proof
is required even though bridges are not Assets. `Datastore.Audit` and targeted
storage-root checks are not required: storage inventory/status calls, storage
Assets and uses_storage relationships are absent. No guest-agent privilege is
required; runtime guest IP enrichment is outside scope.

The bounded proof checks propagated roots and every relevant ACL path, retaining
raw ACL/effective snapshots only transiently for before/after comparison. Hidden
relevant NoAccess, nonpropagated roots, unknown visibility or incomplete reads
prevent COMPLETE. An empty guest list cannot substitute for authorization proof
and explicit per-node enumeration. Test Connection authenticates and returns
bounded capability/state/privilege/path-category readiness identifiers without
inventory enumeration or raw ACL output.

Verified TLS or a trusted SHA-256 certificate fingerprint is required. Fingerprint
trust is checked on the authenticated socket before credentials are sent. There
is no insecure fallback, password/SSH login, source write, allocation/control
privilege, raw source logging or transmission to discovered alternative hosts.
DNS pinning and fixed request/time/size bounds remain unchanged.

Live fingerprint mismatch failed closed and restoring the correct value restored
successful Test Connection. Authentication-secret negative testing was not
performed; additional ACL mutation/negative scenarios are fixture evidence unless
explicitly recorded as live in [qualification](qualification.md).
See the [source call matrix and COMPLETE rules](discovery.md).
