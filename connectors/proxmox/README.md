# Proxmox VE Connector 0.2.0

**0.2.0** is the first production release contract for the Atlas Proxmox VE
Connector, qualified against **Proxmox VE 9.2.11**. Other source versions remain
**untested**, with `allow_with_warning`; qualification does not cover all 9.x.
The earlier 0.1.0 connection probe was an internal development baseline, never
tagged or published as a GitHub Release. This promotion prepares release assets;
it does not publish them or update Atlas's catalogue/bootstrap.

The package supports Test Connection, read-only discovery, scheduling through the
Atlas runtime and complete snapshots. Test Connection uses the qualified bounded
readiness module to authenticate, report the source version and distinguish
Inventory Ready from limited/unproven ACL coverage without enumerating inventory.

Discovery emits exactly four Asset classes: `proxmox.cluster`, `proxmox.node`,
`proxmox.qemu` and `proxmox.lxc`. Canonical `proxmox.network` and
`proxmox.interface` observations describe explicit topology. The only Asset
relationships are `proxmox.member_of` and `proxmox.runs_on`.

Proxmox bridges produce node-owned Interfaces, with validated guest bridge
attachment represented by `proxmox.bridge_name`. They are not standalone Assets.
VLAN tags/trunks, MAC and explicit static subnet evidence retain conservative
normalization. There are no bridge or storage Assets, connected_to or uses_storage
relationships, storage inventory calls, guest-agent reads or inferred DHCP IPs.

Use a dedicated non-root, privilege-separated API token and the
[required read-only permissions](docs/permissions.md). Token ID and secret are
write-only credentials supplied through private runtime files. Verified TLS is
the default; trusted SHA-256 fingerprint mode verifies the authenticated socket
before credentials are sent. Insecure TLS is not offered. DNS peer pinning,
redirect rejection, bounded reads and sanitized diagnostics remain enforced.

The runtime owns the exact community.proxmox **2.0.0** dependency, SHA-256
`77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6`.
Collection contents are not bundled here. The package requires runtime baseline
**1.2.0** or later below 2.0.0, SDK **1.1.0** or later below 2.0.0, and AIP **1.0**.
Atlas-authored code is Apache-2.0; third-party licences remain with the runtime
and are identified in the SPDX SBOM.

Accepted operator live evidence for the unchanged **0.2.0-i4b.6** implementation
includes successful Test Connection / 9.2.11 / Inventory Ready, two COMPLETE runs
with 100 observations and zero warnings/errors each, unchanged Debug Off
repeatability, no duplicate reconciliation work and no unsafe absence result.
A deliberately incorrect certificate fingerprint failed closed; restoring the
correct value restored success. Authentication-secret negative testing was not
performed. Native Debian/systemd LIVE acceptance remains outstanding.

See the [discovery contract](docs/discovery.md), [capability matrix](docs/capability-matrix.md),
[qualification evidence and limits](docs/qualification.md) and
[promotion report](docs/i4b-completion-report.md). Historical candidate metadata
and packaged pre-live documentation remain under `candidate/`, with version
0.2.0-i4b.6, unqualified status and no qualified source versions. They are excluded
from the normal production archive.
