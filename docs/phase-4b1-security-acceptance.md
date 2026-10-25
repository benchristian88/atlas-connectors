# Phase 4B.1 — release security acceptance and publication authority

Review date: 26 October 2026. Scope: the complete tracked and untracked Phase 4B
working tree, contained local corrections, read-only GitHub observations and the
read-only Atlas reference. This document records engineering acceptance, not
permission to publish or change GitHub configuration.

## A. Executive decision

**GO FOR PR as a release-preparation increment, after the corrections below.**
The preparation implementation does not depend on a new privileged publisher.
Publication remains blocked by its missing approved execution path and the genuine
acceptance gates below. Python 3.12 CI must pass before merge. No Proxmox 0.2.1
authenticated build, immutable publication, final-artifact live qualification,
catalogue advancement or installation eligibility is claimed.

## B. Git and baseline

- Branch remains `feature/proxmox-immutable-release`.
- HEAD remains `b03405d6acfd562f75dbdf7aad91c94df9a1d32e`. Independently read remote
  `main` has that exact SHA and reports `protected: true`.
- Initial inventory: 131 tracked files, nine tracked modifications, seven
  untracked files. All seven were reviewed, including both new tools and the new
  security tests. No existing user work was discarded.
- Atlas remains clean on `dev` at
  `808ee0f76f77c11e17a6c403806ce0666e30074e`; no Atlas file was modified.

| Identity | Evidence and state |
| --- | --- |
| Historical Proxmox 0.2.0 | Source `456a5bfdd1398c19da9ffef29216029027e24278`; archive SHA-256 `a14fec5ab485c980688ff5907e8835ddd3e9cecd1a6989ef252cbcb1b1dc4ef8`; release `416290807`; package asset `652745908`; live release remains mutable |
| Historical candidate 0.2.0-i4b.6 | Archive SHA-256 `dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97`, unchanged |
| Local Proxmox 0.2.1 candidate | Archive SHA-256 `96eaa736c2919e56e09b9613dddd8648ad1f43b77679899ab706261b2a38e509`; reproducible but unattested; detached metadata's HEAD is contextual while changes are uncommitted |
| Existing catalogue sequence one | Release `421426993`, `catalogue-000001`, live `immutable: true`; four original assets, unchanged by this work |

## C. Code review findings

| Severity | Affected file | Finding and disposition |
| --- | --- | --- |
| Medium | `tools/verify_connector_release.py` | Final verification pinned only the archive asset ID. The four accompanying assets could have different IDs with identical bytes and still pass, contrary to approval of all five staged identities. Fixed: require a separately approved complete name/ID/SHA-256/size inventory; compare every final asset with it. Four substitution regressions failed before the correction. |
| Low | `tools/connector_release.py` | Package SPDX IDs were unique among packages but could equal the document's `SPDXRef-DOCUMENT`, making relationship endpoints ambiguous. Fixed: enforce uniqueness against the document too. The regression failed before the correction. |
| Publication blocker, deferred | `.github/workflows/release.yml`, `.github/workflows/catalogue-publish.yml`, operator runbook | The release job only prepares/attests. The catalogue publisher is not an approved package tagger/finalizer. No implemented, authenticated, approved package publication path was found. Resolve in the separately reviewed increment in F/J; this does not invalidate preparation. |

No other merge-blocking implementation defect was established in the reviewed
scope. The SPDX checks enforce this repository's supported package metadata
contract; they are not a general SPDX conformance or legal licensing assessment.

## D. Security and provenance assessment

Implemented controls and their actual guarantees:

- The recipe remains explicit. Release overlays require a stable version newer
  than the base, exact version/Manifest agreement, safe paths and complete versioned
  metadata. Default 0.2.0 and candidate construction remain byte-identical. Registered
  historical identities cannot be prepared again. Overlays are not independent
  frozen code snapshots: future shared-source changes must continue respecting
  historical digest regressions or reproduce from the original source revision.
- Release preparation uses the SDK's full Manifest validation and official registry
  identity/URI constraints. It checks qualification declarations, supported AIP,
  SDK/runtime baseline, embedded Manifest agreement, entry points, licence/notice
  paths and bounded SPDX identity/dependencies/relationships. These declarations
  do not themselves prove source qualification or authorize installation.
- Archive validation bounds compressed and decompressed bytes before parsing;
  rejects concatenation, unsafe paths, duplicate members, links, extension headers,
  nonregular members and malformed padding/trailers; and never extracts or executes
  the archive. Source reads reject symlinks and oversized files.
- Production preparation requires clean exact committed source, tracked package
  inputs, exact tag resolution, official numeric repository/owner context, hosted
  runner, configured App actor and first attempt. Local mode explicitly grants no
  attestation or publication authority.
- The pinned offline verifier authenticates original Sigstore evidence with
  repository/owner IDs, issuer, hosted runner, `release.yml@refs/tags/ID-vVERSION`,
  source/signer/configuration SHA, subject name/digest and original invocation.
  Retention copies the authenticated `actions/attest` output bytes unchanged into
  `package.sigstore.json`; it neither reserializes nor replaces the signature.
- Candidate verification requires exact source reproduction, original signature,
  completed successful first run and attempt one, both App actors, source CI/main
  ancestry, package environment and tag binding. Its result explicitly says it is
  not publication authority.
- Final verification additionally requires actual `immutable: true`, published
  non-prerelease state, exact release/tag/source identity, App author/uploaders,
  all five approved asset identities and independently downloaded identical bytes.
  It rereads release/assets/tag/run authority after downloads and fails without a
  receipt on contradiction. The transport has no credentials or mutation path.
- Generic package tests exercise Docker, UniFi and another future identifier using
  renamed synthetic package metadata, without Connector-ID code allowlists. These
  are contract tests, not implementations or qualification of those connectors.
- Provider-positive tests explicitly use `StructuralVerifier` and modeled HTTP;
  their clean-checkout admission is mocked deliberately and is not authenticated
  release evidence. Separate genuine offline tests authenticate only the original
  historical bytes/digest/source. The historical signature is rejected for 0.2.1.

Residual boundaries: current public metadata cannot prove historical or continuous
protection, complete hidden bypass arrays, effective installation permissions,
secret custody, independent human review or freedom from administrator/App-key
compromise. App author/uploader identity does not prove the maintainer's separate
approval. `--approved-assets` is explicit trusted operator input, not signed human
proof. The receipt is a report, not catalogue or executable authorization. No
Atlas installer, runtime, trust policy, schema, API or tenant boundary changed.

## E. Publication authority investigation

The repository's policy, current workflows, producer ADRs 0001–0005, security
contract and runbooks were compared with Atlas accepted ADRs 0006/0011/0013 and
proposed ADR 0012. Historical ADR status prose was not rewritten as implementation
status. Current code and evidence determine the implemented boundary.

**Independently observed through read-only GitHub APIs:**

- Repository/owner IDs `1414494920` / `93822871`; protected main at the SHA in B.
- Public [Publisher App registration](https://api.github.com/apps/atlas-catalogue-publisher):
  App **5422372**, slug **atlas-catalogue-publisher**, owner **93822871**,
  Contents Write, Actions Read, Administration Read, Metadata Read; no Workflows
  permission. The pinned policy requires installation **174027755**, bot
  **346232650**. Registration was verified; installation scope/effective access
  were not independently established.
- Environments: `catalogue-publication` **24999137498** and
  `catalogue-verification` **25016263801** require protected branches;
  `connector-release` **24617213627** allows exactly one custom tag policy `*-v*`.
  All report `can_admins_bypass: false` and no required reviewers.
- Five active rulesets are listed: main **25618213**, history **25618809**,
  bootstrap **25628137**, current **25618684**, publication tags **25618901**.
  Publication-tag detail covers `catalogue-*` and `*-v*` and blocks creation,
  update/deletion/non-fast-forward. Its public response omits `bypass_actors`.
  App-only bypass is required by policy, not established by this response.
- Release workflow **381528148** is active at `.github/workflows/release.yml`.
  The live workflow inventory contains CI, package preparation, catalogue build,
  catalogue publication and catalogue verification; no package finalizer.
- `proxmox-v0.2.1` ref lookup returned 404. Public release inventory contains no
  0.2.1 release; anonymous inventory cannot exclude hidden drafts.
- `/immutable-releases` returned 401 anonymously. Repository-wide enablement was
  not verified; actual existing immutable catalogue state is a separate observation.

**Existing approved custody/execution design, evidenced by code and runbooks:**

| Credential or job | Approved location/access | Limit of this review |
| --- | --- | --- |
| Publisher key `PUBLICATION_APP_PRIVATE_KEY` and ID variable | `catalogue-publication`; only injected into the pinned token action in its Publisher job, after authenticated startup admission | Did not read keys, enumerate real secret metadata, mint tokens or verify effective installed scope |
| Verifier key `VERIFICATION_APP_PRIVATE_KEY` and verification policy | `catalogue-verification`; explicitly mapped into the SHA-pinned isolated reusable verifier; no inherited secret set | Approved Verifier App/installation **5424851 / 174088125** uses Administration Write and Contents/Actions/Checks/Metadata Read; live custody/scope not independently verified |
| Package build | `connector-release`; Contents Read plus job-token OIDC/attestations Write | No Publisher or Verifier key is consumed by this workflow |
| Frozen catalogue execution | S4 **`2dd1ffcd2f5677dc35bdbc8f68ea28275c91c285`**, reusable verifier plus separately pinned executable Publisher | Only catalogue caller and bootstrap/publish/recover operations are accepted. It cannot authorize a Connector package workflow |

Environment restrictions are not workflow-file secret ACLs. Protected source,
fixed actors, pinned executable code, narrow secret injection, credential isolation
and runtime admission all remain necessary. Existing package policy requires the
Publisher App to create a tag; its push triggers `release.yml`, whose attestation
establishes the exact package identity. A build is not human publication consent.

## F. Preferred publication architecture

**Choose B: add a narrowly scoped Connector package publication workflow using
the existing approved App identities and existing environment credential custody.**
No new App, PAT, key store, bypass, permission elevation, signing service or consumer
trust policy is needed. Existing catalogue execution cannot simply be reused as
a package command. This recommendation is a design for separate approval; no
privileged workflow or authorization profile was implemented here.

Minimum next implementation boundary:

1. Add one main-only, fresh single-maintainer dispatch entry point with explicit
   `tag`, `stage`, and `finalize` operations. Pin its executable implementation at
   a separately reviewed full SHA. Read advancing source/request data as data;
   never execute operator-selected refs, candidate code or arbitrary commands.
   Enforce repository/owner/maintainer IDs, original and triggering human actor,
   run attempt one, hosted runner, required CI and concurrency without cancellation.
2. Reuse the isolated two-App security observation pattern. Add a separately
   reviewed package caller/request admission profile and SHA-pinned reusable
   verifier, using the existing Verifier credential only in its current environment.
   Reuse existing canonicalization, bounded transport, complete ruleset checks,
   signature verification and run-level preflight/freshness mechanics. Bind the
   exact operation, package request digest, policy/source and fresh invocation;
   do not broaden or consume frozen S4 catalogue grants. No new human signature,
   per-write grant, distributed replay store or new trust service is necessary.
   Keep the Publisher key inaccessible to that isolated verifier, and verify the
   package-specific admission before minting the Publisher installation token.
3. Keep Publisher scope to this repository, Contents Write plus existing
   Actions/Administration/Metadata Read, **Workflows No access**. Keep Verifier
   permissions and no-bypass status unchanged. Recheck actual App/installation/token
   identity and repository scope. Complete hidden ruleset evidence must come from
   the isolated privileged observer, never anonymous omission. Fail closed if any
   installation, permission or custody prerequisite cannot be established.
4. `tag`: approve reviewed merged source **C**, exact **T**, version and expected
   archive digest **D** from clean builds. Check CI/main ancestry, tag absence and
   complete draft-visible release inventory before create-only `refs/tags/T` at C.
   Never delete/retarget existing refs. Use the Publisher token so GitHub emits the
   required App-originated push run **R**, attempt one. Do not substitute a dispatch
   build, job-token-created tag, rerun or local signature.
5. `stage`: independently authenticate completed R, exact source/tag/digest and
   original bundle. Select the exact Actions artifact ID from that run; download
   and validate exactly five files without executing/rebuilding/reserializing them.
   Retain those original files promptly because Actions artifacts can expire.
   Create a draft only for existing T, at C, non-prerelease, `make_latest: "false"`.
   Upload only those bytes through the scoped App. Independently retrieve all five
   staged files; record **L**, archive **A** and every name/ID/SHA-256/size.
6. Stop for the maintainer's separate inspection and fresh `finalize` dispatch
   approving exact **C/T/D/R/L/A** and the complete staged inventory, including its
   canonical digest. Preserve the approval/run record outside the five candidate
   files. This is explicit single-maintainer approval, not an independent veto or
   a portable signed human proof. No automatic `workflow_run` publication.
7. `finalize`: bind the fresh approval to the original staged record and all five
   current draft identities/bytes; repeat source, provenance, scope and protection
   checks before the single PATCH of exact L to `draft: false`, leaving latest
   selection untouched. The GitHub API provides no caller-settable immutable flag.
   Require actual `immutable: true`, published non-prerelease state and exact
   tag-to-C resolution after publication. Run independent GET-only verification
   with the approved inventory; save final observations and receipt. Any partial,
   contradictory or mutable result blocks handoff and catalogue eligibility.
8. Recovery uses a fresh approved dispatch and the same exact C/T/D/R/L and
   existing asset identities. After an ambiguous write, observe first; never blindly
   retry. An exact existing tag can only be reconciled with its original first
   build; never create a second build identity. Add only missing expected draft
   assets from retained original bytes. Reject conflicts; no asset replacement,
   deletion, retagging, partial-publication acceptance or identity reuse. A complete
   immutable publication can be reverified unchanged. Failed/rerun build identity
   or irreparable immutable state requires a separately reviewed new version.

Before release creation, check that C's workflow tree does not differ from the
current default branch in a way requiring Workflows Write. GitHub documents that
[conditional permission requirement](https://docs.github.com/en/rest/releases/releases#create-a-release).
Resolve such a conflict through reviewed source/release planning; do not repeat
the historical temporary bootstrap elevation. Preserve draft → attach all assets →
publish as [GitHub recommends](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases).
App-token events can trigger a push workflow, unlike most job-token events;
see [GitHub's trigger rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).

Manual administration prerequisites: owner confirms actual installations are
single-repository and at baseline permissions, key custody/availability in the
existing environments, exact environment/ref restrictions, full ruleset/bypass
configuration, immutable-release enablement and separately approved new workflow
pins/admission policy. Do not silently copy keys, add repository secrets, change
permissions or enable a workflow to overcome missing evidence. Genuine isolated
acceptance-only execution with Publisher skipped must precede activation. Actual
publication needs separate explicit authority after that engineering increment.

## G. Implementation changes

This review changed only:

- `tools/verify_connector_release.py`: required approved inventory and all-asset ID
  comparison; candidate mode rejects final-publication approval arguments.
- `tools/connector_release.py`: document/package SPDX identity uniqueness.
- `tests/test_connector_release.py`: demonstrated both prior defects; added
  malformed approval inventory/CLI negatives and Docker/UniFi contract cases.
- `catalogue/publication/README.md` and `consumer-handoff.md`: explicit approved
  inventory format, separate storage and updated final-verification command.
- This report: decision, evidence limits and the scoped next increment.

All other Phase 4B changes were pre-existing and retained. No database migration,
Atlas/API/UI/SDK/runtime/discovery change, release registry edit or privileged
publisher was introduced. The new, previously untracked verifier's local CLI now
requires `--approved-assets` for published verification; this is a deliberate
fail-closed correction before its first merge. Existing published contracts remain
unchanged. Feature-ledger changes are inapplicable: Atlas is read-only.

## H. Validation

Executed in `atlas-connectors`, using Python **3.14.7**, pinned SDK **1.1.0**,
Ansible **2.19.7**, Runner **2.4.3** and the approved community.proxmox **2.0.0**
archive. The collection was freshly provisioned with `tools/test_collection.py`
from Atlas's read-only vendored archive, after matching SHA-256
`77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6`.

| Command/check | Executed result |
| --- | --- |
| `.venv/bin/python -m pytest -q tests/test_connector_release.py tests/test_publication_packaging.py` before correction | **139 passed** |
| Full suite before correction, approved collection and Ansible enabled | **1,862 passed**, 180 dependency deprecation warnings |
| `.venv/bin/python -m pytest -q tests/test_connector_release.py -k 'approved_nonpackage or collide_with_document'` before correction | **5 failed**, demonstrating both defects |
| `.venv/bin/python -m pytest -q tests/test_connector_release.py tests/test_publication_packaging.py tests/test_publication_crypto.py tests/test_publication_transport.py tests/test_publication_authorization.py` after correction | **424 passed**; includes genuine historical offline signature verification |
| `ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-phase4b1-test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q` after correction | **1,878 passed**, no skips; 180 `ansible_runner` Python 3.14 `codecs.open` deprecation warnings |
| `.venv/bin/python tools/release_connector.py --local --tag proxmox-v0.2.1 --output /private/tmp/atlas-phase4b1-review/candidate-first` | Local unattested preparation succeeds |
| `.venv/bin/python tools/build_bundle.py --version 0.2.1 --output /private/tmp/atlas-phase4b1-review/candidate-second` | Same candidate digest; all four local output files byte-identical |
| Archive comparison / historical regression | 19 safe members; only Manifest, SBOM, README and qualification differ; both historical archive digests unchanged |
| `git diff --exit-code HEAD -- connectors/proxmox/library connectors/proxmox/module_utils connectors/proxmox/discover.yml connectors/proxmox/test_connection.yml connectors/proxmox/manifest.json connectors/proxmox/sbom.spdx.json connectors/proxmox/candidate` | Clean: qualified discovery/base/candidate inputs unchanged |
| `git diff --check`, plus `git diff --no-index --check -- /dev/null FILE` for every untracked file | Clean |
| Complete tracked/untracked inventory and local Markdown link targets | Checked; retained with local review evidence |

Python 3.12 was not found on PATH, in Homebrew or the checked local managed-Python
locations. The existing Python 3.12 `validate` CI and final tag workflow remain
required gates; no 3.12 pass is claimed. No remote workflows were dispatched.
No genuine 0.2.1 attestation/provider-finalization acceptance was attempted.

## I. Git state and complete inventory

Final `git status --short --untracked-files=all`:

```text
 M .github/workflows/release.yml
 M README.md
 M catalogue/README.md
 M catalogue/publication/README.md
 M catalogue/publication/consumer-handoff.md
 M connectors/proxmox/package.json
 M tests/test_publication_packaging.py
 M tools/build_bundle.py
 M tools/release_connector.py
?? connectors/proxmox/releases/0.2.1/README.md
?? connectors/proxmox/releases/0.2.1/docs/qualification.md
?? connectors/proxmox/releases/0.2.1/manifest.json
?? connectors/proxmox/releases/0.2.1/sbom.spdx.json
?? docs/phase-4b1-security-acceptance.md
?? tests/test_connector_release.py
?? tools/connector_release.py
?? tools/verify_connector_release.py
```

The material Phase 4B files above comprise the six-line evidence-retention workflow
addition; root/catalogue/runbook/handoff documentation; recipe and four release
metadata files; builders/release selectors; new package contract/verifier; and
release/generic packaging tests. The review's own modifications are enumerated in G.

Local evidence directory `/private/tmp/atlas-phase4b1-review` retains the baseline
tracked diff and complete initial inventory/hashes, final tracked/untracked path
inventory and hashes, ignored-file inventory, final tracked diff, reproducibility
record/candidate bytes, full test log and validation record. There are 131 tracked
files and eight final untracked files. Ignored virtualenv, caches, prior `dist`
outputs and pinned verifier binary are local support data, not PR inputs.
The original input hashes verify that unrelated pre-existing work was preserved.
No branch creation, commit, push, merge, rebase, tag, publication, secret/settings
change or remote mutation occurred.

## J. Human handoff

Proceed to human review and a preparation-only PR through the prescribed
commit/push/PR/green-CI/main process. Commit/push remain human actions outside this
task's authority. Include every new file; ordinary `git diff` omits them. Require
Python 3.12 CI and honest preparation-only release wording before merge.

The exact next separately authorized engineering phase is **Phase 4B.2 — scoped
Connector package publication workflow and custody acceptance**, implementing F
with existing Apps/environments, immutable S pins, package-specific isolated
admission, tag/stage/finalize operations and failure/recovery tests. Its initial
acceptance is read-only/acceptance-only with no publication. Owner administration
and actual immutable Proxmox 0.2.1 publication require subsequent explicit authority.
Retain final-artifact Test Connection/COMPLETE discovery and the inherited live
qualification gaps as separate genuine acceptance gates.

Do not advance the catalogue as part of that package increment. Phase 4C must
separately address public immutable publication-evidence archival, future-sequence
consumer policy approval and explicit historical 0.2.0 withdrawal while preserving
its exact identity. Accepted Atlas ADR 0013 only approves the original sequence-one
exception; proposed ADR 0012 does not authorize sequence two. Neither package
publication nor catalogue metadata alone grants installation authority.
