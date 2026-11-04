# Catalogue 2 Phase 1 — durable publication evidence engineering report

Date: 4 November 2026 (Pacific/Auckland). Repository:
`benchristian88/atlas-connectors`.

## A. Executive result — CONDITIONAL PASS

**Implemented for local review:** bounded permanent-release evidence contract,
original-byte preparation CLI, genuine offline authentication through the approved
verifiers, historical-time checks, successor stage/finalization candidate and
original-evidence recovery checks. The candidate is exercised end to end against
the existing synthetic provider and never activated in a workflow.

The condition is independent security acceptance and explicit decisions on the
proposed historical/selection/recovery rules. Owner approval of Option A authorizes
this development direction only. This report does **not** authorize sequence two,
production trust, publication, release creation, deployment or installation.
No commit, push, PR, merge, tag, dispatch, live release or settings operation occurred.

## B. Existing implementation and root security gap

The checkout was clean on the already-created intended development branch at
expected baseline `e58788a667c0c0006477ac149e8ad28aedda0745`; local main matched.
No branch creation or remote operation was needed. Inspection covered existing
Publisher stage/finish/recovery, preflight issuance/admission, authorization and
catalogue/package/selection Sigstore profiles, both catalogue workflows, producer
ADRs/runbooks/security evidence and Atlas ADRs 0012/0013 read only.

Existing S4 independently signs privileged security observations, C, exact policy
digest, original run/attempt and operation using `atlas-publication-preflight/v2`.
Publisher admission has a 900-second maximum startup window and a trusted local
receipt allowing up to 1,800 seconds of same-job work. The workflow exports only
`preflight.json` and `preflight.sigstore.json` with one-day Actions retention.
Its immutable catalogue release contains four catalogue/selection assets. Thus
the original preflight and matching exact policy bytes have no permanent public
release archive contract. A registered attestation or unsigned receipt cannot
recreate unavailable signed document bytes or privileged historical observations.

Atlas proposed ADR 0012 identifies this gap. Accepted ADR 0013 approves only the
exact original sequence-one bootstrap and its narrowly bounded exception; it is
not future-sequence authority. Those Atlas files and all historical producer
implementation/evidence are unchanged. Old runbook statements are preserved as
historical context, with current candidate handoff links added above them.

## C. Proposed and implemented evidence architecture

The [complete contract](../catalogue/publication/durable-evidence.md) specifies exact
filenames, formats, limits, retrieval and interruption behavior. New ordinary
snapshots would have seven assets: existing catalogue/build bundle/selection/bundle
plus exact `preflight.json`, `preflight.sigstore.json` and `policy.json`.

`Archive` preserves original bytes, enforces exactly three archive inputs and
computes independent size/digest inventories. `ArchiveVerifier` uses independently
provided signer trust and approved exact policy digests; an archive cannot choose
its own authority. It authenticates all existing signed source/actor/workflow/
run/attempt/security/ruleset fields. `HistoricalLimits` is an explicit review input,
without production defaults. Local preparation is reachable via
`python tools/publication_evidence.py --help` and performs no provider mutation.

`EvidencePublisher` extends the existing Publisher. Frozen S4's hard-coded stage
and finish inventories require two successor methods; unchanged authority,
selection, packages, current/history and recovery logic are inherited. The new
methods preserve S4 ordering and add archive/checkpoint/inventory checks. No base
tool is rewritten. The active workflow cannot import or execute this candidate
because its full-SHA code checkout and all existing pins are unchanged.

A future production driver/checkpoint persistence and coordinated reviewed
successor workflow pinning are deliberately absent. The candidate class and local
preparation CLI are the development deliverable, not an operational publication path.

## D. Original-byte and cryptographic verification guarantees

Policy bytes, preflight and bundles are never reserialized when retained. Exact
SHA-256 is recomputed from each original artifact. Duplicate filenames/JSON keys,
unexpected artifacts, malformed encodings, oversized/nonregular/symlink inputs,
policy mismatch and conflicting identities reject. Seven-asset release validation
also checks numeric IDs, names, exact repository REST/display URLs, App author/
uploader, sizes, uploaded state, provider digest and independently downloaded bytes.

The unmodified approved `AuthorizationSigstore` verifies the original v2 preflight
profile with pinned gh 2.102.1/roots, issuer, hosted runner, repository/owner IDs,
independent signer S, source C, workflow, caller configuration, original invocation,
predicate and exact subject digest. The existing selection/catalogue verifiers
authenticate their separate profiles. The companion runs a second bounded offline
verification to extract gh's **verified** Tlog timestamps without altering S4's
digest-only return API; decoded DSSE is never treated as authentication.

Historical checks validate signed observation/issuance/expiry ordering, run creation
before observation, Tlog integration within original preflight validity, subsequent
selection timing and public release publication timing. They do not renew expired
admission. Test-only 900/300-second selection/publication bounds are not accepted
production settings. Missing time evidence fails; no historical observation is
fabricated. Result flags explicitly deny current authorization and consumer acceptance.

The preflight does not directly sign pointer/release/asset identity. Binding relies
on the original authenticated selection's same C/run/attempt, independently checked
immutable release/catalogue identities, identical retained selection and the
reviewed one-selection-per-source implementation constraint. This proposal needs
separate owner/Atlas approval. Genuine old fixtures prove verifier behavior only;
there is no newly obtained genuine future-publication preflight fixture or live
candidate acceptance evidence in this task.

## E. Publication and recovery safety

Stage retains original archive bytes before catalogue/selection publication.
The same-job checkpoint pins every observed upload ID/size/digest. A partial retry
requires that checkpoint, the same original run evidence and unchanged surviving
bytes/IDs; it fills missing files without replacing existing assets. An orphan
draft without original preflight, lost checkpoint or ambiguous upload fails closed.
The checkpoint is neither portable authorization nor a downloaded receipt.

Finish verifies the original archive/selection and seven assets before finalizing,
then checks actual immutability, identical original bytes and stable numeric IDs
before the existing channel compare-and-swap. Finalization or pointer failures
leave original evidence inspectable. Once immutable, a release cannot be repaired
by adding evidence, regenerating a signature or substituting a newer preflight.

Recovery inherits the immutable-immediate-successor/history/package/live-authority
checks and additionally verifies the original archive. A separate fresh recovery
run/source/preflight authorizes recovery only; it cannot replace original selection
authorization. Tests use distinct original and recovery run/source identities.
Recovery performs no immutable asset writes. Whether its own authorization must
also have a separate permanent archive remains an unresolved owner audit decision;
this increment does not create a second release or claim that audit contract.

Original sequence one keeps exactly four assets and its approved bootstrap pins.
Bootstrap is unsupported by the candidate. No original release/root/pointer or
Proxmox 0.2.2 immutable release was accessed or changed. Local historical
metadata, fixture and implementation hashes are preserved.

## F. Exact changed-file inventory

| File | Reason |
| --- | --- |
| `tools/publication_evidence.py` | Original-byte archive, existing-profile authentication, verified times, explicit historical limits and local preparation CLI |
| `tools/publish_catalogue_evidence.py` | Inactive successor subclass with seven-asset staging/finalization and original-evidence snapshot/recovery validation |
| `tests/test_publication_evidence.py` | Permanent synthetic policy/provider regressions plus genuine offline verification/tamper rejection |
| `tests/fixtures/publication_evidence/preserved.json` | Baseline SHA-256 regression for 27 frozen controls and historical evidence files |
| `tests/fixtures/publication_evidence/README.md` | Fixture provenance and acceptance limits |
| `catalogue/publication/durable-evidence.md` | Full proposed producer archive/retrieval/recovery contract |
| `catalogue/publication/README.md` | Add current candidate link without rewriting original runbook |
| `catalogue/publication/consumer-handoff.md` | Add current consumer handoff without changing historical evidence |
| `docs/catalogue2-phase1-engineering-report.md` | This A–J report and proposed separate consumer ADR amendment |

Two existing documentation files change and seven files are new. No database
models or migrations are involved. Existing API/UI routes, SDK/package formats,
catalogue/pointer signing schemas and active four-asset contracts are unchanged.
The proposed seven-asset future release contract requires coordinated consumer
review and is not silently substituted for the active frozen contract. No Atlas
authorization/tenancy code changes; all existing producer authority and source/
repository/actor boundaries are reused. No Atlas feature-ledger update is warranted.

## G. Tests and reproducible evidence

Validation artifacts are local under `/private/tmp/atlas-catalogue2-evidence-review`
(`WORK` below), outside the repository. Python is 3.14.7; hosted Python 3.12 CI was
not dispatched. Dependencies and the hash-pinned offline verifier were already
available. The exact reviewed collection was installed offline from the read-only
Atlas vendor archive using the existing hash-verifying test installer.

The following commands were executed; `WORK` abbreviates the directory above.

| Executed command/check | Final result |
| --- | --- |
| `.venv/bin/python tools/test_collection.py --archive /Users/Ben/Code/atlas/vendor/collections/community-proxmox-2.0.0.tar.gz --output WORK/test-collections` | PASS: existing installer verified the pinned collection before extraction |
| `.venv/bin/python -m pytest -q tests/test_publication_evidence.py --tb=short` | PASS: **128 passed, 0 failed, 0 skipped**, 15.27 seconds; `focused-reviewed.log` |
| `ATLAS_TEST_COLLECTIONS_PATH=WORK/test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q --junitxml=WORK/full-final.xml` | PASS: **2,858 passed, 0 failed, 0 errors, 0 skipped**, 94.73 seconds; `full-final.log` / `full-final.xml` |
| `/private/tmp/atlas-phase4b2-tools/actionlint -shellcheck= -pyflakes= .github/workflows/*.yml` | PASS: actionlint 1.7.12, all seven workflows; optional shellcheck/pyflakes disabled; `actionlint.log` |
| `.venv/bin/python -m pytest -q tests/test_documentation.py` | PASS: **1 passed, 0 failed, 0 skipped**; links/newlines/whitespace/fences; `documentation.log` |
| `.venv/bin/python tools/publication_evidence.py --help` | PASS: local CLI reachable without credential or provider access; `cli-help.log` |
| `.venv/bin/python WORK/verify-preservation.py` | PASS: 178 original tracked files audited, 176 byte exact, only two planned documentation additions; seven new files; unchanged HEAD/refs/index; all nine changed files whitespace-clean; `preservation.json`, `preservation.log`, `handoff-manifest.json` |
| `git diff --check` | PASS: clean |

The full suite includes every existing catalogue/publication/authorization test,
bootstrap and recovery suite, workflow/gate tests, genuine catalogue/package/probe
cryptography and Connector publication/release/signature/draft regressions, plus
the 128 new tests. It reports 180 inherited Python 3.14 `ansible_runner` deprecation
warnings; none are failures. Required hosted Python 3.12 validation and genuine
candidate live security acceptance were not run or claimed.

The first complete run passed **2,852 tests, 0 failures, 0 skips** in 101.85 seconds
(`full.log` / `full.xml`). Final review added six regressions and tightened companion
artifact bounds and same-ID release-observation consistency. The focused 128-test
run and final 2,858-test run above include those changes. The original 2,730 tests
remain present and pass; no existing test file was edited.

The initial focused development run had **76 passed, 27 failed, 0 skipped**:
a candidate import was missing and the pinned gh requires a `.json` bundle suffix.
After correcting those, a second run had **89 passed, 14 failed, 0 skipped** because
the inherited synthetic provider needed explicit synthetic verifier metadata for
the companion timestamp path. Those fixture issues were fixed, yielding
**103 passed, 0 failed, 0 skipped**. Expanded checkpoint, metadata, recovery and CLI
coverage then passed **122 tests, 0 failed, 0 skipped** before the final full run.
No assertions or existing tests were removed or weakened.

## H. Existing publication compatibility and regression results

All pre-existing production tools and seven workflows remain byte exact. Catalogue
S4, package S4, independent trust and original sequence/pointer/registry values are
unchanged. The permanent fixture pins 27 material existing files without requiring
deep Git history in hosted shallow checkouts. A separate whole-tree audit compares
all 178 original tracked files, local refs/HEAD and index with the pre-edit snapshot.

Existing genuine catalogue/package/probe fixtures remain unchanged and are tested
through the pinned executable. New profile-positive tests use synthetic verified
output and provider state; genuine cryptographic tests separately verify original
catalogue time evidence and reject altered/unsigned bytes. Original sequence-one
four-asset behavior remains exercised through the inherited bootstrap/publication
suites and the candidate's root-compatibility regression. No live provider state
was refreshed, so current live gate/configuration values are not asserted.

## I. Remaining risks, owner decisions and future acceptance gates

**Proposed but not approved:** the seven-asset public archive contract; precise
historical rules and maximum selection/publication delays; Tlog-within-expiry
requirement; accepted witnesses/time representation; sufficiency of same-source/
run/immutable-co-location selection binding; and permanent audit of recovery's
separate authorization. Public `published_at` is transport metadata, not a signed
publication timestamp. The archive proves authenticated publication-time evidence,
not uninterrupted protections or complete present-day hidden bypass state.

**Requiring independent security acceptance:** code/contract review, shallow/hosted
Python 3.12 CI, future workflow/checkpoint driver, reviewed frozen successor S and
separate pin changes, genuine exact-profile signing/isolation evidence, anonymous
seven-asset retrieval and interrupted-provider acceptance. Test fixtures cannot
establish live App permissions, key custody, GitHub guarantees or operator approval.
Single-maintainer/admin/provider/trusted-code/credential compromise and whole-state
withholding/rollback risks remain. Do not introduce consumer administrative keys.

**Requiring live authorization:** any repository/environment trust change,
`CONNECTOR_PUBLICATION_ENABLED` change, credential use, workflow dispatch, catalogue
registry/sequence change, release/tag creation, publication, deployment or install.
Obtain independent Atlas trust/history implementation and explicit owner acceptance
before sequence two. Never reuse ADR 0013's exception or mutate historical releases.

### Proposed Atlas ADR 0012 amendment — separate owner review only

Do not apply or accept this text automatically:

> For future ordinary catalogue sequences, Atlas may evaluate original producer
> publication-time evidence from the seven-asset immutable release contract after
> independently approving the producer implementation, signer, exact policy
> digests and historical-time/selection-binding rules. Authenticate original
> preflight, bundle and exact policy bytes using the existing v2 profile and
> release-owned verifier/roots. Require full signed privileged ruleset observations,
> original human/run/attempt/source/workflow identity and independent public
> catalogue/selection/release/asset verification. A downloaded policy or receipt
> cannot nominate authority. The preflight does not directly sign a later pointer:
> explicitly approve its correlation through the original authenticated selection
> invocation and reviewed one-selection implementation, or require stronger binding.
> Keep historical evaluation separate from live startup admission and present-day
> public checks. Specify accepted transparency/issuance/selection/publication
> ordering and maximum delays before activation. Do not extend expiry or infer
> continuous protection/current hidden bypass state. Decide separately how fresh
> recovery authorization is permanently archived without mutating the original
> immutable snapshot. Preserve ADR 0013's exact original sequence-one exception
> without extending it. Consumer acceptance, durable history/currentness and package
> executable eligibility remain separate approved boundaries.

This is engineering amendment text, not an accepted Atlas decision. Atlas ADRs
0012 and 0013 are untouched. Option A approval does not resolve every listed rule.

## J. Exact Git state and handoff

Branch: `feature/catalogue-v2-publication-evidence`.
HEAD and local main: `e58788a667c0c0006477ac149e8ad28aedda0745`.
Changes remain unstaged and uncommitted. Preservation audit passed: all local
refs/tags, HEAD and index bytes match the initial snapshot; 176 original files
remain byte exact and only the two planned documentation additions differ.
The sibling Atlas checkout remains clean on dev at
`9c10e96da10ebf7108c88f632d77beaab5051b6c`. No SDK file was modified.
No database, enrollment authority, protected installation, production credential,
live GitHub configuration, historical release or current pointer was accessed.

Final `git status --short`:

```text
 M catalogue/publication/README.md
 M catalogue/publication/consumer-handoff.md
?? catalogue/publication/durable-evidence.md
?? docs/catalogue2-phase1-engineering-report.md
?? tests/fixtures/publication_evidence/
?? tests/test_publication_evidence.py
?? tools/publication_evidence.py
?? tools/publish_catalogue_evidence.py
```

The new fixture directory contains exactly `README.md` and `preserved.json`.
The full nine-file size/digest handoff is recorded outside the repository in
`WORK/handoff-manifest.json`; it is review evidence, not signed authority.
No additional work is authorized by this handoff.

Review the nine listed files and reproducible local evidence. Resolve the owner
decisions in I, independently accept the successor implementation and prepare
workflow/checkpoint wiring in a later separately reviewed increment. Any eventual
consumer trust or live publication requires its own explicit authorization.
Stop after local implementation, validation and this report; do not publish.
