# Proxmox VE 0.2.2 qualification inheritance and limits

**Preparation only, 31 October 2026 (Pacific/Auckland).** The Manifest retains
the accepted **Proxmox VE 9.2.11** qualification declaration from 0.2.0 and its
0.2.1 overlay. Every executable playbook/module/helper and every domain declaration
except package version is unchanged. New SPDX identity, document creation time and
release documentation do not expand source coverage, capabilities or dependencies.

The original implementation was qualified as 0.2.0-i4b.6 at source
`73f539883fe1663c332b7e6cd1cb4c054e0eae75`, then promoted to 0.2.0 at
`456a5bfdd1398c19da9ffef29216029027e24278`. Accepted operator evidence on
18 October 2026: authenticated Test Connection/Inventory Ready, repeated COMPLETE
manual discovery with Debug On/Off, 100 observations, one batch and zero
warnings/errors. The repeat created no duplicate reconciliation work or unsafe
absence result. An incorrect SHA-256 certificate fingerprint failed closed;
restoring the correct fingerprint restored success. Host vmbr0 was an Interface;
guest bridge names and VLANs 3, 5 and 6 were observed. VLAN 99 remains fixture-only.

Historical 0.2.0, 0.2.1 and candidate metadata, qualification evidence and package
bytes remain unchanged. Historical 0.2.0 is remotely ineligible because its release
is mutable. The failed 0.2.1 Stage and incomplete private draft remain historical
evidence: do not reuse, repair, publish, delete, replace or retag that identity.
The separate 0.2.2 overlay neither replaces nor reinterprets those records.

**No live 0.2.2 artifact acceptance has occurred.** The qualified Manifest reflects
accepted unchanged implementation evidence, not deployment, signing or publication
of this new package. Before release acceptance, validate the exact final
committed/tagged/attested artifact and obtain operator acceptance of its packaging
and qualification inheritance. Repeat Test Connection and unchanged COMPLETE
discovery using that exact artifact to establish new-artifact acceptance.
Behavioral changes require renewed qualification rather than inheritance.

Authentication-secret negative testing was not performed. Native Debian/systemd
LIVE acceptance remains outstanding. Broader ACL/outage/migration/malformed-input
cases retain fixture evidence only. No live credentials, production discovery,
native deployment or new source versions were used in this preparation. Other
source versions remain untested with a warning; no broader Proxmox qualification
is claimed.

Human-reviewed PR and hosted Python 3.12 CI, merged source P, complete P/C workflow
equality, twice-reproduced authoritative digest D using frozen package S4 and fresh
security checks remain future prerequisites. Tag, Stage and Finalize each require
separate approval. Actual immutable release and signed asset verification must
precede separately authorized catalogue publication and consumer acceptance.
Keep `CONNECTOR_PUBLICATION_ENABLED=false` throughout preparation. SPDX creation
time is metadata-preparation time; no publication date or production digest is
asserted by this overlay.
