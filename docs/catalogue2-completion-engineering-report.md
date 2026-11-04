# Catalogue 2 — Atlas Connectors engineering completion report

Date: 4 November 2026 (Pacific/Auckland).

The subsequent [security remediation report](catalogue2-security-remediation-report.md)
records H2/M1 corrections and validation. The implementation/evidence below remains
the prior completion handoff; all successor approvals remain unset.

## A. Result

**Inactive producer candidate; operational feature closure remains blocked.**
Phase 1 is preserved and extended with a real driver, durable same-job checkpoint
persistence, separate candidate registry, candidate builder and inactive workflow
preparation. No publication, signing credential use, live setting change, tag,
release, push, commit, merge, deployment or LXC access occurred.

The [Phase 1 report](catalogue2-phase1-engineering-report.md) remains historical
validation of that increment; this report describes its successor extension.

## B. Baseline and preservation

Branch remains `feature/catalogue-v2-publication-evidence`, HEAD
`e58788a667c0c0006477ac149e8ad28aedda0745`. All nine uncommitted Phase 1 files
were preserved before editing under local review evidence. The archive/verifier,
seven-asset contract and all 128 Phase 1 regressions remain. Only the successor
publisher gains a checkpoint callback; frozen pre-existing publication/signing
controls, seven active workflows, policy/trust pins, active registry/sequence and
published historical fixture hashes remain unchanged and are regression-pinned.

## C. Producer implementation

`catalogue_evidence_driver.py` admits the original signed preflight before write
credentials using the existing trusted runner-local startup receipt. It binds
checkpoints to source/run/original preflight/policy/implementation, atomically
writes mode-0600 state and fsyncs after every observed upload. A reopened same-job
checkpoint must agree with all surviving numeric asset identities. Torn, missing,
wrong-context, ambiguous or substituted evidence fails closed.

Existing `EvidencePublisher` preserves original bytes before selection, validates
seven exact assets, signs through existing independently pinned workflow profiles,
checks original run/times and immutable provider state, then uses the existing
channel compare-and-swap. It inherits the existing package/authority/history and
original-evidence recovery evaluators. No signature or authorization receipt is
invented, and immutable evidence is never repaired by replacement uploads.

`build_catalogue_candidate.py` and the driver share the separate
`catalogue/candidate-v2` registry. Candidate 2 retains Proxmox 0.2.0 with identical
manifest/tag/asset identity and an explicit withdrawal, and includes immutable
Proxmox 0.2.2. The active sequence-one registry remains byte-exact. Publication
must use the separately prepared candidate build workflow to obtain the matching
catalogue build signature at C.

`prepare_evidence_workflow.py` creates exclusively local, inactive review outputs
for both existing workflow paths. The publisher output uses a caller-supplied
reviewed full SHA S, the successor driver, publish-only dispatch and a separate
`CATALOGUE_EVIDENCE_ENABLED` gate. It does not edit `.github/workflows`, trust,
GitHub settings or credentials. The existing reusable preflight signing format
remains exact; a frozen successor containing this implementation must be separately
reviewed and pinned before use.

## D. Authority and unresolved security decisions

`APPROVED_SUCCESSOR` and its fingerprint are unset; the driver rejects before any
provider mutation. No production historical defaults or accepted decision IDs
are supplied. An eventual release-owned approval selects policy digest and explicit
historical/selection/recovery decisions. Existing independent caller/workflow/trust
pins authenticate S; S is not embedded in its own approval record.

Proposed selection/publication bounds remain 900/300 seconds, not approved defaults.
Original preflight and selection are separate signatures correlated by C/run/
attempt and immutable release content plus reviewed one-selection-per-source code.
The preflight does not directly sign later pointer/asset IDs. Independent Atlas
approval of that binding is required. Downloaded evidence cannot select Atlas trust.

The production driver **rejects recovery** pending a permanent recovery-archive
decision. Inherited recovery tests still authenticate the original snapshot and
separate fresh recovery authorization without immutable writes. They do not
implement a permanent archive for that later authorization. If owner review
requires one, it is a remaining implementation blocker; an enable flag cannot
supply it. The narrow sequence-one exception is not extended.

## E. Exact file inventory

No SDK, package format, database or migration changes. No current API/UI route
or existing active publication contract is replaced. The seven-asset contract is
an inactive coordinated producer/consumer extension.

<!-- INVENTORY_START -->
| File | Purpose |
| --- | --- |
| `catalogue/publication/README.md` | Preserved Phase 1 handoff link. |
| `catalogue/publication/consumer-handoff.md` | Preserved Phase 1 consumer handoff link. |
| `catalogue/candidate-v2/releases/proxmox-0.2.0.json` | Retain original identity with withdrawal; active registry untouched. |
| `catalogue/candidate-v2/releases/proxmox-0.2.2.json` | Exact existing immutable 0.2.2 manifest/package asset candidate. |
| `catalogue/candidate-v2/sequence.txt` | Separate sequence-two candidate allocation; active sequence remains one. |
| `catalogue/publication/durable-evidence.md` | Retained seven-asset proposal plus current successor-report link. |
| `docs/catalogue2-completion-engineering-report.md` | Producer A–J successor report. |
| `docs/catalogue2-phase1-engineering-report.md` | Unchanged uncommitted Phase 1 historical report retained. |
| `tests/fixtures/publication_evidence/README.md` | Unchanged Phase 1 frozen-control preservation fixture and provenance notice. |
| `tests/fixtures/publication_evidence/preserved.json` | Unchanged Phase 1 frozen-control preservation fixture and provenance notice. |
| `tests/test_catalogue_evidence_driver.py` | 11 new checkpoint/authority/workflow/candidate regressions. |
| `tests/test_publication_evidence.py` | All 128 unchanged Phase 1 regressions retained. |
| `tools/build_catalogue_candidate.py` | Local canonical candidate builder matching publication driver. |
| `tools/catalogue_evidence_driver.py` | Gated production driver and atomic private same-job checkpoints. |
| `tools/prepare_evidence_workflow.py` | Inactive full-SHA publisher/build workflow review output only. |
| `tools/publication_evidence.py` | Unchanged Phase 1 original-byte archive/verifier retained. |
| `tools/publish_catalogue_evidence.py` | Retained Phase 1 publisher plus per-observation durable checkpoint callback. |
<!-- INVENTORY_END -->

## F. Validation

Local evidence: `/private/tmp/atlas-catalogue2-completion`; original Phase 1
validation remains under `/private/tmp/atlas-catalogue2-evidence-review`.
Genuine existing cryptographic artifacts remain distinct from synthetic future
verified-output/provider tests. No new release was published for testing.

| Executed command/check | Result |
| --- | --- |
| `ATLAS_TEST_COLLECTIONS_PATH=WORK_PHASE1/test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q --junitxml=WORK/connectors-full-final.xml` | **2,869 passed, 0 skipped/failures/errors**, 128.52 s; includes all 128 retained Phase 1 regressions and 11 new driver/candidate tests |
| Focused evidence/driver run, then final driver run | **136 passed**, then **11 driver tests passed** after candidate build/approval coverage was added |
| `.venv/bin/python -m pytest -q tests/test_documentation.py` | **1 passed** |
| `actionlint -shellcheck= -pyflakes= .github/workflows/*.yml` | **PASS**; all seven unchanged active workflows |
| Both `prepare_evidence_workflow.py` outputs at explicitly synthetic `a`×40 review SHA, then actionlint on those inactive files | **PASS**; full-SHA publisher and matching candidate-build syntax, no active workflow edited |
| `tools/catalogue_evidence_driver.py --help` and default `stage` rejection | **PASS** help; **expected exit 1** before credentials/provider calls with approvals unset |
| `git diff --check`, `git diff --cached --quiet`, original preservation fixture and original Phase 1 copies | **PASS**; 27 frozen controls unchanged; only planned publisher checkpoint callback and current-contract note extend Phase 1; no staged changes |

`WORK` is `/private/tmp/atlas-catalogue2-completion`; `WORK_PHASE1` is
`/private/tmp/atlas-catalogue2-evidence-review`. An earlier complete run passed
2,867 cases before the last two new driver regressions were added; the final
2,869-case run includes them. All 180 warnings are inherited Python 3.14
`ansible_runner` deprecation warnings, not failed/skipped tests. Hosted producer
Python 3.12/signing acceptance was not dispatched; Atlas's separate Docker
consumer/security acceptance did run on Python 3.12.

Coordinated Atlas evidence: complete API **2,599 passed/233 host skips**, final
focused publication/install/RBAC/restore **104 passed**, Docker full security/
installation **184 passed/zero skips**, final narrow Docker consumer **101 passed/
zero skips**, frontend **331 passed**, production build passed, existing browser
**576 checks** and new final browser **8 scenarios** passed. Exact host skip and
initial environment-failure disclosures are in the Atlas report. No live
publication, interruption-provider exercise, new LXC or Proxmox source acceptance
is inferred from these local results.


## G. Consumer handoff and compatibility

Atlas implementation remains separate on `feature/catalogue-v2-consumption` from
clean dev `9c10e96da10ebf7108c88f632d77beaab5051b6c`. It authenticates original
preflight/policy under independently reviewed Atlas pins, verifies complete bounded
selection history and transactional 1→2 acceptance, and separately gates remote
executable eligibility/confirmation. It reuses PackageStore/runtime/mappings and
activation, preserves offline installed operation and denies native remote writing.
Both consumer approval records/fingerprints remain unset.

No producer archive or unsigned receipt can approve the consumer. The original
bootstrap approval and local-release native/security restrictions remain intact.
See the Atlas checkout's `docs/catalogue2-engineering-report.md`, Proposed ADR 0018
and `docs/deployment/catalogue2.md` for exact consumer review/operational steps.

## H. Owner approvals

Outstanding: accept the seven-asset contract and exact historical limits/witness
semantics; accept the selection correlation or require stronger binding; decide
permanent recovery audit versus explicitly disabled recovery; review/freeze S;
accept genuine successor signing/isolation; independently approve producer trust/
workflow pin changes and catalogue live gate; and separately approve both Atlas
publication and executable-eligibility policies. Existing authority pins and
`CONNECTOR_PUBLICATION_ENABLED` remain unchanged. Do not enable package publishing
merely to publish Catalogue 2: 0.2.2 is already immutable.

## I. Publication and operational actions

After those approvals only: populate the release-owned contract approval/fingerprint,
freeze S, generate/review both workflow outputs, coordinate all independent pins,
qualify signing while catalogue publication is disabled, build/sign candidate 2 at
final source C and a successful required CI, then authorize one fresh publish run.
Independently retrieve by numeric IDs, verify all seven assets/original signatures,
immutable tag/release/source and full pointer chain before Atlas acceptance.
Never amend existing immutable releases or invoke the old four-asset publisher on
seven-asset snapshots. Lost/ambiguous checkpoints and interrupted immutable
publication require inspection; cross-job recovery remains disabled.

The package candidate binds published release `429608780`, package asset
`693849044`, source `e58788a667c0c0006477ac149e8ad28aedda0745`, SHA-256
`2d66fc69b9cf9c70d7df117fe41bff3e3e056299f1908cde965e9e3f75e59abf`.
Only read-only metadata observation and unchanged existing local artifacts were
used. Actual future catalogue S/C/run/release IDs cannot be assigned in this task.

Follow the Atlas runbook for the exact commands and separately authorized fresh
Docker installation at `192.168.3.220`, normal Catalogue review/confirmation,
managed mappings, scoped configuration and real-source/offline/restart/restore
qualification. Rebuild needs explicit operator approval. `atlas-test-docker` is
excluded and was not accessed. No live operational acceptance is claimed.

## J. Repository state and remaining blockers

All work remains unstaged/uncommitted on the existing producer branch. No SDK
changes. Frozen controls and original history remain preserved. Remaining blockers
are owner/security decisions, genuine successor acceptance, separately authorized
publication and new-instance/source operational qualification; permanent recovery
archive remains unimplemented if required. This is not a declaration of feature closure.

Final `git status --short`:

```text
 M catalogue/publication/README.md
 M catalogue/publication/consumer-handoff.md
?? catalogue/candidate-v2/
?? catalogue/publication/durable-evidence.md
?? docs/catalogue2-completion-engineering-report.md
?? docs/catalogue2-phase1-engineering-report.md
?? tests/fixtures/publication_evidence/
?? tests/test_catalogue_evidence_driver.py
?? tests/test_publication_evidence.py
?? tools/build_catalogue_candidate.py
?? tools/catalogue_evidence_driver.py
?? tools/prepare_evidence_workflow.py
?? tools/publication_evidence.py
?? tools/publish_catalogue_evidence.py
```
