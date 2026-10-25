# Proxmox VE Connector 0.2.1

This is a new package identity for immutable distribution of the qualified
0.2.0 discovery implementation. The playbooks, modules, transport, normalization,
diagnostics, credentials, TLS rules, discovery scope and dependencies are unchanged.
Only versioned Manifest, SPDX package identity and release documentation differ.

The accepted implementation was qualified against **Proxmox VE 9.2.11**: repeat
COMPLETE discovery, 100 observations, zero warnings/errors and fail-closed incorrect
certificate fingerprint. Other source versions remain untested with a warning.
See [qualification](docs/qualification.md). The package also retains the unchanged
`docs/discovery.md`, `docs/capability-matrix.md` and `docs/permissions.md` contracts.

This package supports Test Connection/readiness, clusters/nodes, QEMU/LXC Assets,
canonical Networks/Interfaces and member_of/runs_on relationships. Host bridges
are node-owned Interfaces; storage and bridge Assets remain excluded. Runtime
provides pinned community.proxmox 2.0.0; no collection is bundled or installed here.
AIP 1.0, SDK >=1.1.0/<2.0.0 and runtime >=1.2.0/<2.0.0 remain required.

0.2.1 is locally prepared, not published or remotely installable yet. Historical
0.2.0 remains unchanged and remotely ineligible because its release is mutable.
Historical source qualification is not complete live acceptance of this new
artifact. Publication requires reviewed committed source, an App-created exact
tag, authenticated attempt-one build, separate operator authorization, unchanged
assets and independent confirmation of GitHub `immutable: true`. Catalogue
inclusion and Atlas executable eligibility require later separate acceptance.
