# Proxmox 0.2.0 production promotion report

**18 October 2026 — I4C-B.** The production package promotes the unchanged
**0.2.0-i4b.6** discovery implementation to **0.2.0**, qualified for the exact
source version **Proxmox VE 9.2.11**. Other versions remain untested with a warning.
This is the first production Connector release contract; 0.1.0 was an unpublished
internal probe baseline and gains no retroactive tag/release.

## Promotion changes

The production Manifest now carries the qualified candidate's runtime baseline,
exact community.proxmox 2.0.0 dependency/digest, read-only discovery, scheduling,
complete snapshots, both entry points, required classes/scopes/mappings, nine
facts and verified/fingerprint-only TLS. The SPDX SBOM identifies 0.2.0 and retains
the runtime-owned collection dependency and licensing statements without claiming
collection contents are bundled.

The normal bundle includes discover.yml, atlas_discover/atlas_readiness and the
shared discovery, normalization, transport and diagnostics helpers. Production
Test Connection selects the qualified readiness module. Shared executable source
is unchanged from qualified checkpoint `73f539883fe1663c332b7e6cd1cb4c054e0eae75`;
only the production Test Connection playbook's module selection changes from the
old probe. Sorted USTAR members, fixed mode/owner/time and gzip mtime zero preserve
reproducibility. Tests, fixtures, candidate paths and incidental files are excluded.

The release model remains four Asset classes, canonical Networks/Interfaces and
member_of/runs_on relationships. No bridge/storage Asset, connected_to or
uses_storage relationship is introduced. TLS, ACL visibility, completeness,
normalization, topology, source identity and fail-closed protections are preserved.
Atlas owns customer/site authority, acceptance, reconciliation and absence;
PARTIAL/failed runs cannot trigger absence and discovery never auto-accepts knowledge.

## Qualification and regression boundary

Accepted live evidence includes Test Connection / 9.2.11 / Inventory Ready,
repeatable COMPLETE runs with 100 observations and zero warnings/errors each,
Debug Off repeatability, no duplicate reconciliation work and no unsafe absence.
A wrong certificate fingerprint failed closed and restoring the correct value
restored successful Test Connection. Authentication-secret negative testing was
not performed. Native Debian/systemd LIVE acceptance remains outstanding.
See [qualification](qualification.md) for evidence and limits.

Regression coverage checks canonical Manifest/source compatibility semantics,
exact classes/facts/dependencies, production archive contents/provenance and
reproducibility, unchanged discovery streams, historical candidate digest and
pre-live docs, prior candidate output preservation and detached-Manifest tampering
rejection. Existing transport/ACL/normalization/diagnostics/Runner coverage remains.
Fixture and package checks do not claim additional live source qualification.

Candidate files remain version 0.2.0-i4b.6, unqualified with no qualified versions.
Their archive retains the accepted SHA-256
`dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97`.
Historical failed/partial qualification records and candidate documents remain
unchanged. This report updates the production package's former I4B status document.

## Release boundary

No database, Atlas, SDK, API/UI, tenancy, source ACL, credential or discovery-model
change is required. The protected `proxmox-v<SemVer>` workflow retains its
tag/Manifest identity check, normal build, attestation and exact retained assets
for later operator publication. Its test setup now provisions the same
digest-verified collection as CI and enables Runner tests: a clean-environment
check proved discovery tests fail without that dependency/path configuration.
No commit, push, tag, merge, staging/activation or GitHub Release publication is
performed here. Remote Atlas catalogue/download work is outside this promotion.
