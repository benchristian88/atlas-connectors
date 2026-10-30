# Proxmox VE Connector 0.2.2

This is a separate package identity prepared for future immutable publication as
`proxmox-v0.2.2`. It inherits the qualified 0.2.0 implementation and unchanged
0.2.1 executable payload. Only the package version, SPDX identity/document creation
time and release documentation differ. Playbooks, modules, diagnostics, readiness,
credentials, TLS verification, discovery scope, dependencies and licences are
unchanged. Historical 0.2.0, 0.2.1 and candidate bytes remain preserved; the failed
0.2.1 release identity must remain unpublished and untouched.

The accepted implementation was qualified against **Proxmox VE 9.2.11**: repeat
COMPLETE discovery, 100 observations, zero warnings/errors and fail-closed incorrect
certificate fingerprint. Other source versions remain untested with a warning.
See [qualification inheritance and limits](docs/qualification.md). This historical
implementation qualification does not establish live acceptance of a 0.2.2 artifact.

Test Connection/readiness, cluster/node and QEMU/LXC Assets, canonical Networks and
Interfaces, and member_of/runs_on relationships retain their existing contracts.
Host bridges are node-owned Interfaces; storage and bridge Assets remain excluded.
The package retains unchanged `docs/discovery.md`, `docs/capability-matrix.md`
and `docs/permissions.md` contracts.
Runtime supplies pinned community.proxmox 2.0.0; no collection is bundled or installed.
AIP 1.0, SDK >=1.1.0/<2.0.0, Atlas >=0.1.0/<1.0.0 and runtime >=1.2.0/<2.0.0
compatibility remain unchanged, as do Apache-2.0 licensing and all notices.

**Preparation only: 0.2.2 is not published or remotely installable.** Keep
`CONNECTOR_PUBLICATION_ENABLED=false` throughout preparation. No merged release
source P, authoritative digest D, release asset ID or publication date is assigned
here. The SPDX creation timestamp records this metadata preparation, not publication.
Local archive hashes are provisional and local detached source metadata records
the checkout HEAD, which does not contain these uncommitted changes.

Future publication requires human-reviewed merged source and successful hosted
Python 3.12 CI, exact P/C workflow-directory equality, two independent reproductions
of D from P using frozen package S4, current security controls and separate Tag,
Stage and Finalize approvals. Independently verify the actual immutable release
and signed original assets before separately authorized catalogue publication.
Atlas consumer eligibility remains a further acceptance boundary.
