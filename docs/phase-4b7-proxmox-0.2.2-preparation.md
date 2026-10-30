# Phase 4B.7 — Clean Proxmox 0.2.2 preparation

Date: 31 October 2026 (Pacific/Auckland). Local metadata/packaging preparation
only. Changes remain unstaged and uncommitted for human review.

**PASS — local 0.2.2 preparation is complete. Publication remains blocked by
the separate review, qualification and approval gates below.**

## A. Base and branch identity

Repository: `/Users/Ben/Code/atlas-connectors`. The requested branch
`feature/proxmox-v0.2.2-preparation` already existed, clean at expected base
`f96db94827fae743f817f74fa39312b57a68e979`. Local `main` and HEAD matched that
exact base; the existing branch was selected without recreation. No fetch or
remote-state inspection was performed. The Atlas and SDK repositories were not
modified; the existing collection archive in Atlas was read only for test setup.

Approved frozen package implementation S4 remains
`dc79af8e3115e263c267989dfa9ba72599c25463`, distinct from the future reviewed
merged package source P and advancing current caller C. P is not assigned by
this dirty local preparation. HEAD is contextual local build metadata only;
these new files do not exist at that commit.

## B. Exact changed files

| Material file | Change |
| --- | --- |
| `connectors/proxmox/package.json` | Add exactly four 0.2.2 release overrides, retaining the 0.2.1 entry |
| `connectors/proxmox/releases/0.2.2/manifest.json` | Copy the historical patch Manifest with only version changed to 0.2.2 |
| `connectors/proxmox/releases/0.2.2/sbom.spdx.json` | New document name/namespace, own package version and actual metadata-preparation timestamp |
| `connectors/proxmox/releases/0.2.2/README.md` | Package identity, inherited capabilities, limits and future publication gates |
| `connectors/proxmox/releases/0.2.2/docs/qualification.md` | Historical 9.2.11 qualification inheritance, unchanged gaps and exact-artifact acceptance still outstanding |
| `tests/test_connector_release.py` | Exercise both patch versions, retain negative/security coverage and add exact payload/catalogue/signature regressions |
| `tests/test_connector_publication.py` | Remove the shared provider model's obsolete rewrite of generic Connector tags to historical Proxmox 0.2.1 |
| `README.md` | Add current preparation status; retain earlier preparation snapshots |
| `catalogue/publication/connector-packages.md` | Add current handoff and future gates; retain historical runbook/evidence text |
| `docs/phase-4b7-proxmox-0.2.2-preparation.md` | This A–J engineering report |

Five existing tracked files are modified and five files are new. No database
models or migrations are involved. No API/UI route, request, package format,
schema, authorization or tenancy contract changes. No Atlas feature ledger exists
in this repository; no ADR change is needed.

## C. Version and metadata changes

The explicitly registered release overlay selects version **0.2.2**, future tag
**proxmox-v0.2.2** and archive **proxmox-0.2.2.tar.gz**. Its Manifest differs from
0.2.1 only in `version`; no distribution/provenance or release asset ID is embedded.
The SPDX document remains SPDX-2.3/CC0-1.0, with name `atlas-proxmox-0.2.2`, namespace
`https://github.com/benchristian88/atlas-connectors/sbom/proxmox/0.2.2` and own
`versionInfo=0.2.2`. Local SPDX reference IDs, dependencies, checksums, licences,
notices, relationships and creators remain unchanged.

SPDX `creationInfo.created=2026-10-30T23:06:25Z` is the observed preparation time
(31 October in Pacific/Auckland), not a publication date. No production digest,
release/source identity P, tag, asset ID or publication date was invented.

## D. Implementation byte preservation

The new archive contains 19 regular files. Exactly four member bytes differ from
both 0.2.0 and 0.2.1: `manifest.json`, `sbom.spdx.json`, `README.md` and
`docs/qualification.md`. All 15 inherited members remain byte exact, including
LICENSE/NOTICE, both playbooks, readiness/discovery/probe modules, diagnostics,
transport, normalization/discovery helpers and other packaged domain docs.

Manifest dependency and domain metadata are identical except package version.
community.proxmox stays **2.0.0**, SHA-256
`77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6`, with no
collection bundled. SDK >=1.1.0/<2.0.0, AIP 1.0, Atlas >=0.1.0/<1.0.0 and runtime
>=1.2.0/<2.0.0 remain unchanged. Credentials, TLS verification, Test Connection,
readiness, Assets, Networks, Interfaces and relationships retain all prior behavior.

No source versions or capabilities were added. The Manifest retains only accepted
**Proxmox VE 9.2.11** implementation qualification; other versions remain untested
with a warning. No live 0.2.2 artifact acceptance occurred. Authentication-secret
negative testing and native Debian/systemd LIVE acceptance remain outstanding;
broader ACL/outage/migration/malformed cases retain fixture evidence only.

## E. Historical evidence and frozen controls

The before-edit inventory covers 173 tracked files and 234 existing ignored
`dist/` files. Exact-byte audit passed: 168 tracked files remain unchanged; only
the five listed tracked files differ and the five listed additions are new.
All 234 existing artifacts, 35 historical Connector files, 26 fixture files,
seven workflows and 30 frozen S4 tool files remain exact. The recipe change is
strictly additive. HEAD, all local refs/tags and index bytes remain unchanged;
nothing is staged. The original README/runbook text remains byte exact after
removing each current-status insertion. All 38 original release test functions
remain, with three new regression functions and expanded version parameters.
No existing 0.2.0, 0.2.1 or candidate file is edited. Existing fixtures and
historical reports remain preserved; only the release regressions and their shared
publication provider model change.
The README and runbook receive current-status additions; their old text remains
intact as historical preparation context.

All seven workflows, every trusted tool, trust/configuration, SDK distribution,
catalogue registry/sequence and existing artifact are outside the change set.
All four bindings remain exact package S4: reusable verifier `uses`, Publisher
checkout `ref`, `ATLAS_IMPLEMENTATION_REVISION` and committed trust's
`signer_revision`. Frozen catalogue implementation/trust remains separate and
unchanged. HEAD, local refs/tags and the index must remain unchanged.

Historical 0.2.0 remains remotely ineligible because its release is mutable. The
failed 0.2.1 Stage, original signed build, protected tag, incomplete private draft
and uploaded checksum are preserved as evidence. No GitHub draft endpoint was
accessed and no historical identity was reused, repaired, deleted or modified.
External historical evidence was not accessed or changed by this task.

## F. Package determinism and Manifest/SPDX validation

Local artifacts and logs are outside the repository at
`/private/tmp/atlas-phase4b7-proxmox-review` (`WORK` below). Two local builds used
the existing release CLI. A separate script exported `tools/` from immutable
package S4 and verified every exported file against current tool bytes, then
built twice more using frozen S4 while reading this checkout's package data.
All four output inventories and bytes matched, including archive, detached
Manifest, index and SHA256SUMS. Canonical SDK Manifest and existing strict
SPDX/archive/dependency validation passed.

| Local package | Bytes | Reproduced archive SHA-256 |
| --- | ---: | --- |
| Historical 0.2.0 | 33,071 | `a14fec5ab485c980688ff5907e8835ddd3e9cecd1a6989ef252cbcb1b1dc4ef8` |
| Historical 0.2.1 | 32,145 | `96eaa736c2919e56e09b9613dddd8648ad1f43b77679899ab706261b2a38e509` |
| Historical 0.2.0-i4b.6 candidate | 33,657 | `dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97` |
| Prepared 0.2.2, provisional only | 32,620 | `2d66fc69b9cf9c70d7df117fe41bff3e3e056299f1908cde965e9e3f75e59abf` |

The 0.2.2 hash is **provisional local evidence**, not authoritative publication D.
It must be independently reproduced twice from final reviewed merged source P,
using frozen S4, after PR merge. Local detached provenance records base HEAD;
it is not authenticated committed/tagged/attested source. No Sigstore bundle,
production asset inventory or publication receipt is generated here.

## G. Tests and validation

Local interpreter: **Python 3.14.7**. Existing pinned dependencies and offline
verifier were available; no dependency or lockfile changes were needed. Required
hosted **Python 3.12** CI has not run as part of this preparation.

| Executed command/check | Result |
| --- | --- |
| `.venv/bin/python tools/test_collection.py --archive /Users/Ben/Code/atlas/vendor/collections/community-proxmox-2.0.0.tar.gz --output WORK/test-collections` | PASS: installer verifies exact reviewed collection SHA-256 before extraction |
| `ATLAS_TEST_COLLECTIONS_PATH=WORK/test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q tests/test_connector_release.py tests/test_publication_packaging.py tests/test_catalogue.py` | PASS: **469 passed**, 19.36 seconds; `focused-release-packaging.log` |
| `ATLAS_TEST_COLLECTIONS_PATH=WORK/test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q tests/test_connector_release.py tests/test_publication_packaging.py tests/test_catalogue.py tests/test_connector_publication.py tests/test_connector_sigstore.py tests/test_connector_draft_recovery.py` | PASS after shared model correction: **1,178 passed**, 35.55 seconds; `focused-final.log` |
| `ATLAS_TEST_COLLECTIONS_PATH=WORK/test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q` | PASS: **2,730 passed**, no failures/skips, 79.75 seconds; 180 inherited Python 3.14 `ansible_runner` deprecation warnings; `full-ansible-final.log` |
| `.venv/bin/python tools/release_connector.py --tag proxmox-v0.2.2 --local --output WORK/build-first` and separately `WORK/build-second` | PASS: identical provisional archive digest |
| `.venv/bin/python WORK/validate-packages.py` | PASS: two more independent frozen-S4 builds, all four inventories byte equal, canonical Manifest and strict SPDX validation, exact inherited members and historical archive hashes; `package-validation.json` and `.log` |
| `/private/tmp/atlas-phase4b2-tools/actionlint -shellcheck= -pyflakes= .github/workflows/*.yml` | PASS: actionlint **1.7.12**, all seven workflows; optional shellcheck/pyflakes disabled; `actionlint.log` |
| `.venv/bin/python -m pytest -q tests/test_documentation.py` | PASS: **1 passed**, 0.03 seconds; links/newlines/whitespace/fences; `documentation.log` |
| `.venv/bin/python WORK/verify-preservation.py` | PASS: exact inventory, package metadata changes, all workflows/tools/bindings, historical artifacts, refs/HEAD/index; `preservation.json` and `.log` |
| `git diff --check` | PASS: clean |

Release regressions exercise selection, deterministic construction and isolated
exports, Manifest/SPDX/compatibility/qualification, unsafe archive and overlay
rejection, untracked-source protection, authenticated bundle retention, immutable
release/asset/build identity checks and historical signature rejection for both
patch versions. The 0.2.2 invalid-selection expectation is replaced by unregistered
0.2.3/0.3.0 and malformed versions, preserving equivalent negative coverage.

New regressions compare entire 0.2.1/0.2.2 member sets and bytes, complete domain
metadata and SPDX dependency/licence relationships. Local preparation leaves the
catalogue unchanged and fails independent verification without its signed bundle
before provider access. Modeled immutable verification grants only
`immutable_package_verified_catalogue_pending` and writes no registry entry.
Synthetic providers and fixture tests are not live release acceptance. Existing
enable-gate, trust-equality and security controls remain unmodified.

The initial full run had **2,727 passed, three failed**, with 180 inherited
Python 3.14 `ansible_runner` deprecation warnings (78.91 seconds). The three generic
Connector model failures exposed a historical test-provider tag rewrite to
`proxmox-v0.2.1`; that rewrite became obsolete when the shared provider began using
the actual Manifest identity for both patch versions. Removed the two-line rewrite
and made the base model Connector identity generic. No assertion or production
gate was removed or relaxed. Final rerun results are recorded above.

## H. Release-readiness gaps

No reviewed/merged source P, hosted Python 3.12 result, authoritative digest D,
0.2.2 tag, signed build/run/artifact, staged release inventory or actual immutable
release exists as a result of this work. Exact-final-artifact Test Connection and
COMPLETE discovery acceptance remain future operator work; historical qualification
does not establish them. Catalogue publication and Atlas executable eligibility
remain outstanding and unchanged.

The earlier activation report records a temporary live/committed trust mismatch.
Live settings were not re-queried here, so their current values are not asserted.
Before any future dispatch, independently verify complete matching trust, current
protections and baseline App permissions; no dispatch is permitted during a
mismatch. Keep `CONNECTOR_PUBLICATION_ENABLED=false` throughout this preparation.
No GitHub variables, App permissions or credentials were accessed or changed.

## I. Outstanding human approval gates and future S4 sequence

1. Review these ten files in a human-reviewed PR, require successful hosted
   Python 3.12 CI and approve merge separately. This task does not create or submit
   that PR, commit, push or merge.
2. Record exact final merged source **P**, distinct from frozen package **S4**;
   record current caller **C** independently.
3. Verify P and C have byte-equal **entire `.github/workflows` directories**.
   Repeat for every Tag, Stage and Finalize. A later workflow mismatch requires
   stopping; no repin exception or Workflows Write expansion is permitted.
4. Independently reproduce exact 0.2.2 package digest **D twice from P** using
   frozen S4 tools. Local dirty-checkout digests do not assign D.
5. Freshly verify security controls, full committed/live trust equality, baseline
   App permissions and exact approved `proxmox-v0.2.2` P/D identity. Any live trust
   activation or opening of the independent publication-enable gate requires its
   own explicit owner approval. Prior genuine S4 acceptance is historical evidence,
   not fresh admission or authority to publish.
6. Separately authorize **Tag**, **Stage** and **Finalize**. Inspect the original
   successful attempt-one signed build/artifact before Stage; bind original bytes
   and separately approved numeric asset inventory, stop after Stage, then seek
   Finalize approval. Each operation requires fresh signed admission and controls.
7. Independently verify the actual published **immutable** release and signed
   original assets, tag/source/digest and approved numeric identities. Obtain
   exact-artifact qualification inheritance/operator acceptance, including live
   Test Connection and unchanged COMPLETE discovery, without expanding source scope.
8. Obtain **separate catalogue-publication authorization** only after immutable
   release verification. Catalogue sequence/pointers and consumer acceptance remain
   distinct gates under the unchanged frozen catalogue process.

## J. Final repository state and conclusion

Final preservation audit passed. HEAD remains
`f96db94827fae743f817f74fa39312b57a68e979` on
`feature/proxmox-v0.2.2-preparation`; local refs/tags and exact index bytes are
unchanged. Nothing is staged or committed. `git status --short`:

```text
 M README.md
 M catalogue/publication/connector-packages.md
 M connectors/proxmox/package.json
 M tests/test_connector_publication.py
 M tests/test_connector_release.py
?? connectors/proxmox/releases/0.2.2/
?? docs/phase-4b7-proxmox-0.2.2-preparation.md
```

The untracked release directory contains exactly the four new files listed in
section B. No unrelated files changed. No staging, commit, push, merge, tag/release
creation, Actions dispatch, GitHub variable/App change, Publisher credential use,
live Proxmox discovery or catalogue publication occurred. The independent live
publication-enable gate was left untouched; this task grants no authority to open
it. Final documentation/link, preservation and whitespace checks are clean.

**Conclusion: PASS for Phase 4B.7 local preparation. Release and catalogue
publication remain BLOCKED pending the separately authorized future sequence.**
