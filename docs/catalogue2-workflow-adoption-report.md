# Catalogue 2 — Clean Workflow Adoption and Successor S Integration

Date: 5 November 2026 (Pacific/Auckland).
Scope: local producer changes on `feature/catalogue-v2-workflow-adoption` only.

## A. Executive assessment and result

**CONDITIONAL PASS — source adoption implemented; operational readiness withheld.**
The two existing active workflow files replace the historical four-asset S4
Publisher/build wiring with the seven-asset successor Publisher and sequence-two
candidate builder. Trusted executable S is exactly
`4be90c5292f931497473595a0958cc5e0f9d1beb`. Actual publication remains disabled:
checked-in successor signing acceptance is false and an independent external
publication gate must pass both workflow and driver admission.

This is ready for independent source review and human PR processing with the
validation in H. It does not establish genuine successor signing, anonymous
seven-asset publication acceptance, Atlas consumer approval or installation.
No commit, push, PR, dispatch, signing, release, tag, hosted configuration change,
deployment, LXC access or immutable-history modification was performed.

No unresolved Critical or High source security defect was identified. Findings:

| Severity | Finding and disposition |
| --- | --- |
| Medium, corrected | Generated Actions string equality alone also matched uppercase `TRUE`. Added JSON boolean conversion alongside literal string comparison. The existing driver already rejected case variants before minting; that independent exact-string check remains. |
| Medium, operational blocker | Hosted `VERIFICATION_POLICY` could not be read in this session. The last documented value selects S4; independently read and align the existing verification environment before any authorized qualification. No live mismatch was asserted as observed fact. |
| Low, validation limitation | Local Python is 3.14.7; Python 3.12 is unavailable. Required hosted 3.12 CI and genuine GitHub job/expression/isolation acceptance remain independent review gates. |

## B. Repository baseline and immutable S

Repository: `/Users/Ben/Code/atlas-connectors`. Initial branch:
`feature/catalogue-v2-workflow-adoption`; clean worktree and empty index.
Initial and final HEAD: `4be90c5292f931497473595a0958cc5e0f9d1beb`.
Local `origin/main` and `origin/HEAD` matched S; `git merge-base --is-ancestor`
succeeded. A read-only GitHub compare of S against remote main returned
`identical`, zero ahead/behind/commits/files. PR #49 was verified merged at S.
No fetch, branch switch, reset, commit or ref mutation was needed.

Read the accepted Atlas ADR 0018 at the exact locally checked-out Atlas commit
`76031dc6358a81c3babd15f74d407e22f0778dee`. The immutable successor contains
`SuccessorApproval`, the successor driver, isolated verifier, generator, candidate
registry/builder and original-evidence Publisher. Independently reproduced the
canonical dataclass fingerprint with standard-library JSON/SHA-256:

- Contract fingerprint: `8a1c69168ed22dc2f0bff385da182de9bae913e900df031d4b47aabccd7e9070`.
- Exact original policy SHA-256: `c9a88eeb6c7e6d0a7f1a08eaa07eeed5ea251449db7104f7757626842cf1bbe9`.
- Accepted selection/publication bounds: 900/300 seconds.
- Recovery disposition: `disabled-pending-permanent-archive-decision`.

No executable driver, authorization, verifier, evidence contract, original policy,
Sigstore root, verifier distribution, package source or registry file was changed.
The generator is review tooling; its local hardening does not substitute a new
trusted executable revision for S.

## C. Exact workflow replacement

First ran S's reviewed generator with the full exact S into exclusive files under
`/private/tmp/atlas-catalogue2-workflow-adoption-yd4grhzh/`, outside active Actions
paths. Read both YAML structures, inspected the historical-template differences,
steps, inputs, permissions, runners, environment boundaries, output subjects,
artifact selection and error paths. Added only generation-time admission
hardening: publish-only conditions on both Publisher caller jobs, and strict
external-gate JSON conversion. Generated again exclusively under
`/private/tmp/atlas-catalogue2-workflow-adoption-hardened-c28l1998/` and compared
against the initial S-generated output. The build output was identical; Publisher
differences were those three condition changes.

Adopted those two final outputs with only the explanatory first-line review
comment removed. Comments grant no authority. Tests compare adopted/generated
bytes excluding that comment and the complete parsed YAML structures.

| Active path | Result |
| --- | --- |
| `.github/workflows/catalogue-publish.yml` | Dispatch only; `publish` only; acceptance defaults true; original first-attempt main dispatch; isolated reusable signer at S; separate protected Publisher; seven-asset driver authorize/stage/finish at S. |
| `.github/workflows/catalogue.yml` | Existing dispatch/build identity; `build_catalogue_candidate.py`; shared `catalogue/candidate-v2`, sequence 2; catalogue JSON attestation and artifact only. |

The build retains `dist/catalogue/*.json`, numbered `catalogue-000002.json` and
`catalogue.json` outputs, and `.github/workflows/catalogue.yml` provenance identity.
S builds canonical bytes from C's candidate registry and checks the authenticated
build source, tag and catalogue digest. Tests execute the actual adopted build
command into an exclusive temporary output and compare its bytes with the driver.
It has no App secret, token mint, protected publication environment, publication
command or Contents Write. Its OIDC/attestation writes authorize build provenance
only. Publisher recovery/bootstrap dispatch options, phases, mode output and
conditional Workflows Write input are removed. There is no duplicate workflow.

## D. Verifier and Publisher identity alignment

The following checked-in bindings all equal exact S, independently of source C:

1. Reusable `catalogue-verifier.yml@S` call.
2. Publisher's first checkout `ref` (trusted executable root).
3. Publisher `ATLAS_IMPLEMENTATION_REVISION`.
4. Source-owned `catalogue/publication/verifier-trust.json` `signer_revision`.

The source checkout remains `${{ github.sha }}` at `publication-source`, with
credentials not persisted. No commands execute from that directory. S verifies
both actual checkout HEADs. S contains no future C, mutable implementation fallback
or branch/tag executable reference. Advancing main cannot advance trusted S.

The source trust changes exactly `signer_revision` and
`live_signer_accepted: true` to **false**. Historical S4 trust remains immutable in
`tests/fixtures/publication_evidence/s4-verifier-trust.json`. All five numeric
ruleset IDs, verification environment **25016263801**, schema and 900-second
freshness remain unchanged. The original policy still pins publication environment
**24999137498**, package environment **24617213627**, maintainer **93822871**,
Publisher App **5422372**, installation **174027755** and bot **346232650**.
Verifier App **5424851** / installation **174088125**, repository **1414494920**,
owner **93822871** and workflow identities remain checked by unchanged S code.

The fifth, independently administered binding is the complete `VERIFICATION_POLICY`
JSON in **catalogue-verification**. It was not changed. The available GitHub
connector cannot read Actions environment variables; a read-only attempt with the
existing pinned CLI failed because no CLI authentication was available (exit 4).
No credentials were requested, printed or configured. Its current value is unknown;
prior documentation describes S4. Alignment to exact S and false must precede
separately authorized acceptance-only signing. Never move that variable or key to
the publication environment, caller inputs or inherited secrets.

## E. Security gate and permission analysis

Publication requires `acceptance_only=false`, successful original preflight,
main/first attempt/publish-only admission and the existing publication environment.
The workflow requires both `vars.CATALOGUE_EVIDENCE_ENABLED == 'true'` and
`fromJSON(vars.CATALOGUE_EVIDENCE_ENABLED) == true`. The literal comparison rejects
missing, false, numeric, null and whitespace variants; JSON conversion rejects
uppercase boolean variants that Actions' case-insensitive string comparison would
otherwise admit. Invalid JSON fails evaluation closed. The raw variable is passed
without fallback to `ATLAS_CATALOGUE_EVIDENCE_ENABLED`; S independently requires
Python exact string `true` before source/preflight admission or publication access.
See [GitHub's expression semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/expressions).
No hosted gate was set or queried. Owner must independently confirm the repository
publication gate is absent/false and account for environment overrides before use.

The verifier retains `catalogue-verification`, its own App key and pre-credential
independent workflow-S/context guard. Acceptance mode may gather genuine evidence
with unaccepted trust, but signed mode binding and the Publisher's job condition
prevent using that evidence for publication. Checked-in false also blocks ordinary
Publisher admission even if an isolated test supplies an enabled gate.

Publisher order is trusted S checkout, data C checkout, pinned dependencies, exact
policy/App check, pinned public verifier provisioning, download only the preflight
artifact ID returned by this run, cryptographic original-run admission, then one
Publisher App token mint. Authorization cannot be skipped or continued on error.
No secret is referenced in earlier steps. The verifier key never enters Publisher.
Only stage/finish receive that minted token. The final always-run artifact upload
exports public JSON diagnostics, has no publication credentials and cannot mutate
releases/current. No failure/recovery token path or credential fallback exists.

Workflow token permissions remain Contents Read plus job-scoped Actions Read,
OIDC/attestation writes where required. The Publisher App token requests Contents
Write, Actions Read and Administration Read, with no Workflows permission, no
inheritance and no bypass expansion. All Actions retain reviewed immutable SHAs;
the only reusable call is exact S. Hosted Ubuntu 24.04 and existing environments
remain. Separately authenticated actor, actor/triggering-actor, repository, workflow,
source, validate check, protections, five complete rulesets, App/install identity and
release-immutability observations remain enforced by unchanged S code.

Exactly seven assets remain required: numbered catalogue, catalogue bundle,
original current pointer/bundle, original preflight/bundle and exact policy bytes.
Independent Sigstore verification, authenticated root-to-successor history,
original source/run/attempt correlation, original selection bytes, numeric immutable
release/asset verification, 900/300-second bounds, thirty-second pre-finalization
reserve, post-publication verification and compare-and-swap current protection
are unchanged. No automatic Connector installation or new bootstrap exception.

## F. Historical controls retained, removed or replaced

| Class | Treatment |
| --- | --- |
| A — permanent security invariants | Retain all authorization, crypto, source/selection, actor/protection/App, immutable release, timing, history and CAS tests. Shared isolation/token tests now run on archived S4, synthetic generated successor and actual adopted successor profiles. Add explicit actual-workflow and mutation checks. |
| B — historical immutable evidence | Keep `preserved.json` unchanged with all 27 original hashes. Exactly three old active-path assertions resolve to original Publisher/build templates and archived S4 trust; other 24 still check original paths. Catalogue 1, bootstrap, original package signatures and release fixtures remain unchanged and cryptographically tested. |
| C — obsolete executable behaviour | Retire S4-byte equality at the two adopted workflow paths and current trust path; replace with explicit S semantics and separately pinned adopted file hashes. Remove active bootstrap/recover options, phases and temporary elevated permission. Keep historical bootstrap tests scoped to templates. |

No preservation fixture was mass-regenerated, no test deleted and no historical
ADR rewritten. `successor-workflows.json` is regression data, not production trust.
The old negative active-driver assertion is replaced with positive successor wiring.
Legacy implementation modules remain because frozen S imports their Publisher,
checkout, historical verification and authority abstractions; deleting them would
break S rather than simplify the executable boundary. They are not active
bootstrap/recovery workflow entry points.

## G. New adversarial regression coverage

Actual adopted and generated profiles enforce exact S signer/checkout/environment,
data-only C, default acceptance mode, event/first attempt/publish-only conditions,
protected environments, original artifact-ID selection, admission-before-mint,
scoped credentials, immutable Actions, no Workflows Write and no verifier key.
Mutations remove either operational-gate term, acceptance or operation checks;
restore bootstrap/recovery; change S to main, another commit or source C; move
credentials before authorization; skip authorization; mint on failure; elevate
workflow/job/App permissions; use a mutable/unreviewed Action; invoke the old driver
or C-owned commands; redirect working directory; or expose either key early.
All must be rejected by the same semantic assertions applied to actual files.

Additional build mutations select the historical builder, add credentials/token
minting, elevate Contents or unpin an Action. The actual build command must produce
sequence-two bytes and unchanged Proxmox 0.2.2 asset **693849044**, source
`e58788a667c0c0006477ac149e8ad28aedda0745`, digest
`2d66fc69b9cf9c70d7df117fe41bff3e3e056299f1908cde965e9e3f75e59abf`.
Existing package/source-manifest and historical-catalogue tests remain intact.

A local constrained expression harness evaluates the actual conjunction for 13
external values in acceptance/non-acceptance modes, including missing, false,
uppercase, malformed, numeric and whitespace. This models documented string/JSON
semantics; it is not a hosted Actions execution claim. Driver tests exercise exact
raw gate rejection across all three phases with credential/provider tripwires,
bootstrap/recover/invalid-operation denial, missing/mutable/future trust pins and
checked-in unaccepted trust denial. The actual verifier inline guard is executed
with exact checked-in S/false, allowing acceptance mode only and denying missing,
mutable, old, uppercase and future pins before output/credentials.

## H. Executed tests and environment limitations

Validation completed locally. No local test result is genuine successor signing/publication
acceptance. No tests access a live Proxmox endpoint or either LXC.

Initial focused run: 197 passed (before the final expanded cases). Initial full
run: 108 failed, 2998 passed, zero skipped, 180 dependency warnings, 96.80 seconds.
All failures were in discovery/Ansible tests: an existing cached collection tree
selected for testing lacked `proxmox_cluster_status_info.py`. No production code
was changed to suppress those failures. Provisioned a fresh collection using
`tools/test_collection.py` from the local reviewed archive, enforcing SHA-256
`77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6`.
The fresh-dependency run passed 3105 tests and failed only documentation because
the report linked by the updated runbook had not yet been created (96.43 seconds,
180 warnings). After writing this report, the documentation check passed. The
final complete rerun and focused authorization/crypto/mutation run both passed:

| Executed command/check | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q --tb=short --junitxml=/private/tmp/atlas-catalogue2-workflow-adoption-hardened-c28l1998/full-producer-final.xml` with `ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-catalogue2-workflow-adoption-hardened-c28l1998/test-collections`, `ATLAS_TEST_RUN_ANSIBLE=1` | **3106 passed**, zero errors/failures/skips, 180 Ansible Runner `codecs.open` deprecation warnings, 102.43 seconds. |
| `.venv/bin/python -m pytest --noconftest -q tests/test_evidence_workflows.py tests/test_catalogue_evidence_driver.py tests/test_verifier_workflow.py tests/test_publication_authorization.py tests/test_publication_evidence.py tests/test_publication_crypto.py tests/test_publication_bootstrap.py tests/test_authorization_sigstore.py tests/test_historical_workflows.py --junitxml=/private/tmp/atlas-catalogue2-workflow-adoption-hardened-c28l1998/focused-final.xml` | **716 passed**, zero skips, 22.17 seconds. Includes actual/generation equivalence, mutation, original authorization, seven-asset, historical crypto/bootstrap and isolation coverage. |
| `.venv/bin/python -m pytest --noconftest -q tests/test_documentation.py` | **1 passed** after final report edits, 0.03 seconds. Covers all repository Markdown links, whitespace and fences. |
| `/private/tmp/atlas-phase4b2-tools/actionlint -color` | Passed all seven actual active workflows (1.7.12). |
| Independent stdlib canonical approval/policy fingerprint reproduction and `Verifier()` construction | Passed exact contract/policy hashes and hash-pinned verifier/root checks. |
| Byte comparison with `git show S:path` | Unchanged frozen driver/evidence/policy/roots/templates/fixtures; all 40 Connector files, three candidate-registry files, historical registry and original catalogue/publication fixtures identical to S. |
| `git diff --check`, `git diff --cached --check`, `git diff --cached --quiet` | Passed; index empty. |
| Read-only remote compare S → main, repeated before delivery | Identical; no newer baseline reconciliation required. |

Final focused coverage contains 106 workflow, 131 driver, 23 verifier-workflow,
131 authorization, 133 seven-asset evidence, 115 bootstrap, 61 authorization
Sigstore, 12 workflow-archive and four genuine historical crypto cases. The full
suite adds 2390 other tests. Logs/XML are outside the repository in the hardened
review directory above; no test artifact is part of this change.

Local pinned verifier binary/root/approval/policy checks passed. Actionlint 1.7.12
passed against all seven actual active workflows; optional ShellCheck is not
installed, so no separate shellcheck result is claimed. Python 3.12 is not installed
in the available local environments; local pytest uses 3.14.7, pytest 8.4.1 and
Ansible Core 2.19.7 with real local Runner enabled. Hosted CI remains required.
Hosted variable read failed as described in D. Genuine new signer evidence,
provider latency/interruption and actual publication tests were deliberately not
performed: they require separate owner authorization.

## I. Remaining signing, activation and publication gates

1. Independent human review, human commit/PR processing, hosted Python 3.12 CI and
   human merge of these exact source changes; retain immutable S unchanged.
2. Independently read the existing hosted verifier policy, numeric identities and
   protected environments. With separate owner authorization, align complete
   `catalogue-verification` `VERIFICATION_POLICY` to checked-in S/false. Reconfirm
   publication enablement absent/false; do not set it true for qualification.
3. Only after alignment and explicit authorization, use original first-attempt
   main-branch `operation=publish`, `acceptance_only=true`. The new Publisher job
   is unconditionally skipped in this mode, even if a gate were misconfigured.
   The isolated verifier may sign qualification evidence with false trust.
4. Independently review genuine Sigstore evidence, signer workflow/job identity S,
   observed source C, first attempt, all App/ruleset/environment isolation and
   signed protections. Archive public evidence. This local work grants no such
   acceptance. If accepted later, coordinate a separate reviewed source-trust
   `live_signer_accepted=true` change and identical hosted policy update, still
   holding the independent publication gate disabled.
5. Independently authorize any candidate-build dispatch at the intended immutable
   publication C. Its signed catalogue bytes must match S's sequence-two builder;
   preserve original package identity and root/history. Build provenance alone
   does not authorize publishing.
6. Only a later explicit publication authorization may enable the exact external
   publication gate and dispatch `acceptance_only=false`. Independently align
   consumer-owned signer/policy/fingerprint acceptance and obtain anonymous
   seven-asset/provider-interruption acceptance as separately required. The fresh
   Atlas installation and remote installation authority are outside this task.

**Source readiness:** the existing approved S implements the seven-asset path and
can be selected by this caller after separate approvals/configuration and genuine
acceptance. **Operational readiness:** withheld; hosted alignment is unverified,
live acceptance is false and publication is disabled by design. There is no safe
cross-job recovery or fresh-root fallback for a stranded immutable successor.
No database model/migration, Manifest, published package format or Docker-specific
catalogue field changed. Future systemd installation compatibility is preserved;
publication adoption grants no installation or consumer activation authority.

## J. Changed-file inventory and human operator next steps

Exactly 15 material files (13 modified, 2 new):

| File | Purpose |
| --- | --- |
| `.github/workflows/catalogue-publish.yml` | Replace active S4 caller with exact-S, gated, publish-only successor. |
| `.github/workflows/catalogue.yml` | Build sequence-two candidate through existing provenance identity. |
| `catalogue/publication/verifier-trust.json` | Pin S with live signing false; retain numeric identities. |
| `tools/prepare_evidence_workflow.py` | Harden generated job conditions and exact external boolean admission. |
| `tests/workflow_cases.py` | Add exact-S adopted profile alongside historical/generated profiles. |
| `tests/test_evidence_workflows.py` | Actual/generator equivalence, gates, pins, build, trust and mutations. |
| `tests/test_catalogue_evidence_driver.py` | Expand denied gate/operation/trust/acceptance cases with effect tripwires. |
| `tests/test_verifier_workflow.py` | Reuse actual inline guard harness with explicit successor trust. |
| `tests/test_publication_evidence.py` | Archive three retired active-path hash assertions; preserve remaining controls. |
| `tests/fixtures/publication_evidence/successor-workflows.json` (new) | Review-only hashes for adopted workflows and unaccepted S trust. |
| `tests/fixtures/publication_evidence/README.md` | Explain immutable historical and successor regression fixtures. |
| `README.md` | Current disabled successor adoption status. |
| `catalogue/publication/README.md` | Current alignment/qualification boundary; mark old operations historical. |
| `catalogue/publication/durable-evidence.md` | Link current approval/adoption; preserve earlier candidate history. |
| `docs/catalogue2-workflow-adoption-report.md` (new) | This A–J assessment and operator handoff. |

Diff summary including both untracked new files: **15 files, 722
insertions, 80 deletions**. The 13 tracked modified files account for 363 insertions
and 80 deletions; the new fixture has eight lines and this report 351 lines.
No files are staged; no generated test artifacts or temporary dependency trees are included.
The next operator action is independent review and human PR processing, followed
only by the separately authorized steps in I. Do not dispatch, activate signing,
enable publication, rebuild Atlas, reset Catalogue 1, touch the historical Docker
instance or republish Proxmox 0.2.2 as part of this review.

Final `git status --short`:

```text
 M .github/workflows/catalogue-publish.yml
 M .github/workflows/catalogue.yml
 M README.md
 M catalogue/publication/README.md
 M catalogue/publication/durable-evidence.md
 M catalogue/publication/verifier-trust.json
 M tests/fixtures/publication_evidence/README.md
 M tests/test_catalogue_evidence_driver.py
 M tests/test_evidence_workflows.py
 M tests/test_publication_evidence.py
 M tests/test_verifier_workflow.py
 M tests/workflow_cases.py
 M tools/prepare_evidence_workflow.py
?? docs/catalogue2-workflow-adoption-report.md
?? tests/fixtures/publication_evidence/successor-workflows.json
```

Atlas consumer and Connector SDK sibling worktrees remain clean. HEAD and branch
remain the baseline in B. Database migrations: none. Existing workflow filenames,
build provenance identity, Connector Manifest and public catalogue/signing formats
are preserved; the authorized removal of bootstrap/recovery dispatch operations
is deliberate. No Atlas API/UI or tenancy boundary changed. The producer has no
application feature ledger to update; current runbook/status documentation is
updated and historical engineering/decision records remain intact.
