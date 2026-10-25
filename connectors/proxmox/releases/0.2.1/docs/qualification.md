# Proxmox VE 0.2.1 qualification inheritance and limits

**Preparation only, 26 October 2026.** Source version **9.2.11** retains the
accepted qualification declaration from production 0.2.0. Every executable
playbook/module/helper and every domain declaration except package version is
unchanged. The new SPDX identity and packaged release documentation do not expand
source coverage or change runtime dependencies.

The original implementation was qualified as 0.2.0-i4b.6 at source
`73f539883fe1663c332b7e6cd1cb4c054e0eae75`, then promoted to 0.2.0 at
`456a5bfdd1398c19da9ffef29216029027e24278`. Accepted operator evidence on
18 October 2026: authenticated Test Connection/Inventory Ready, repeated COMPLETE
manual discovery with Debug On/Off, 100 observations, one batch and zero
warnings/errors. The repeat created no duplicate reconciliation work or unsafe
absence result. An incorrect SHA-256 certificate fingerprint failed closed;
restoring the correct fingerprint restored success. Host vmbr0 was an Interface;
guest bridge names and VLANs 3, 5 and 6 were observed. VLAN 99 remains fixture-only.

The historical 0.2.0 archive SHA-256 is
`a14fec5ab485c980688ff5907e8835ddd3e9cecd1a6989ef252cbcb1b1dc4ef8`.
Its mutable GitHub release is not eligible for remote installation. Neither this
version nor its qualification reinterprets or replaces those historical bytes.
The repository's original 0.2.0 and candidate qualification reports are preserved.

**No live 0.2.1 artifact acceptance has occurred.** The qualified Manifest reflects
accepted unchanged implementation evidence, not a claim that a new package has
already been deployed, signed or published. Before release acceptance, validate
the exact committed/tagged/attested artifact and obtain operator acceptance of its
packaging/qualification inheritance. Repeat Test Connection and unchanged COMPLETE
discovery using the exact final artifact to establish its new-artifact acceptance.
Behavioral changes would require renewed qualification rather than inheritance.

Authentication-secret negative testing was not performed. Native Debian/systemd
LIVE acceptance remains outstanding. Those historical gaps remain open. Broader
ACL/outage/migration/malformed-input cases retain fixture evidence only. No new
source versions, live credentials, production discovery or native deployment were
used by this preparation. Other source versions remain untested with a warning.
