# Phase 4B.6 — Controlled S4 activation preparation

Date: 31 October 2026 (Pacific/Auckland). Local, human-review preparation only.

**PASS — controlled local activation preparation is complete and validated.
Live activation and publication remain BLOCKED by separate owner approvals.**
Acceptance qualification is not authorization to publish. No live setting or
release action is authorized by this report.

## A. Base, branch and scope — PASS

Repository: `/Users/Ben/Code/atlas-connectors`. The requested branch
`feature/connector-publication-s4-activation` already existed, clean at expected
base `af213a948a7d19aeaccf623c06e093f75a9e228b`. Local `main`, local `origin/main`
and HEAD matched that exact base; no network fetch or remote-state verification
was performed. The branch was reused without recreation or history changes.

The only operational configuration proposal is two committed trust booleans.
This work prepares the next PR; it does not open a PR, commit, push, merge,
change GitHub configuration, dispatch a workflow or authorize live activation.

## B. Completed genuine S4 qualification — PASS

The owner-provided completed qualification and retained external report establish
genuine original S4 acceptance. This preparation inspected that report and
recomputed the three original evidence hashes below; it did not rerun the
historical cryptographic qualification or use expired evidence as live admission.

| Identity | Exact value |
| --- | --- |
| Approved package signer S4 | `dc79af8e3115e263c267989dfa9ba72599c25463` |
| Original caller C | `af213a948a7d19aeaccf623c06e093f75a9e228b` |
| Original run / attempt | `41138855610` / `1` |
| Original artifact | `13018405524` |
| GitHub attestation | `61962326` |
| Verifier / skipped Publisher jobs | `124347928723` / `124348062119` |
| Frozen catalogue S4, separate authority | `2dd1ffcd2f5677dc35bdbc8f68ea28275c91c285` |

The [original run](https://github.com/benchristian88/atlas-connectors/actions/runs/41138855610)
and [attestation](https://github.com/benchristian88/atlas-connectors/attestations/61962326)
are evidence references, not new dispatch instructions. Original evidence and
`qualification-report.md` remain outside the repository at
`~/Atlas-evidence/s4-acceptance-41138855610`.

| Retained original object | Bytes | SHA-256 recomputed here |
| --- | ---: | --- |
| Artifact ZIP | 14,969 | `d9528b43536680465e8cfb68b452d316aba81201d56bd463ecce7ec6a3e2aa10` |
| `connector-preflight.json` | 64,245 | `77b29138bced8902945ba82e6530582170559e8a752b78a2c82cfb23398b4199` |
| `connector-preflight.sigstore.json` | 11,003 | `4d5cc4722dcaad952ef538f029aaa0776cad308748119fbc78ac54f360613255` |

The archived qualification records genuine offline Fulcio/DSSE/Sigstore and Rekor
verification, exact immutable S4 certificate/statement identities, caller C,
original false/false trust and policy bindings, all five complete signed ruleset
and security observations, historical freshness and Publisher job exclusion.
It grants no current admission, effective Publisher installation/token grant,
package-source/build qualification or release authority. Historical S3 evidence
and synthetic test certificates are not substituted for that genuine S4 result.

## C. Exact committed trust proposal — PASS

`catalogue/publication/connector-trust.json` changes only:

```diff
-  "enabled": false,
-  "live_signer_accepted": false,
+  "enabled": true,
+  "live_signer_accepted": true,
```

All remaining fields and bytes are preserved:

| Field | Preserved value |
| --- | --- |
| `schema` | `atlas-connector-package-trust/v1` |
| `signer_revision` | `dc79af8e3115e263c267989dfa9ba72599c25463` |
| `max_observation_age_seconds` | `900` |
| `verification_environment_id` | `25016263801` |
| `atlas-bootstrap-lock` | `25628137` |
| `atlas-catalogue-current` | `25618684` |
| `atlas-history-lock` | `25618809` |
| `atlas-main` | `25618213` |
| `atlas-publication-tags` | `25618901` |

The three workflow SHA bindings remain exactly S4: reusable signer `uses`,
Publisher executable checkout `ref` and `ATLAS_IMPLEMENTATION_REVISION`.
No workflow SHA, source selection, security policy or verification rule changes.

## D. Trust and publication regressions — PASS

The active baseline assertion now expects true/true while retaining the exact
complete trust profile and credential/workflow isolation assertions. It checks
both acceptance and publication configuration using that committed profile.

All pre-existing test functions except that active baseline remain unchanged.
In particular, false/false, false/true and true/false still reject publication.
The actual authorize/prepare/execute entrypoint regressions cover all three flag
states across Tag/Stage/Finalize (27 cases), failing before source/admission,
preparation or `mint_publisher`. Acceptance-only still cannot enter publication.

Nine added actual-entrypoint cases keep both flags true and signer exact, but
change one valid independent freshness setting. They establish that full
independent trust equality still rejects before admission/preparation/credentials
for every command and operation. The internal rejection is checked alongside the
existing sanitized receipt; no diagnostic or production code was changed.

Existing enabled/accepted-trust tests retain exact signer SAN/URI/digest and
certificate constraints, signed admission/context/request/policy/trust bindings,
freshness/replay, complete five-ruleset/bypass/security checks, reviewed source,
required CI/main ancestry, original build/artifact bytes, full P/C workflow
equality, draft/asset identity and scoped App/token permission checks. Enabling
the two trust flags bypasses none of those gates.

## E. Workflow and credential controls — PASS

All seven active workflow files remain byte-for-byte equal to the expected base,
including permissions, concurrency, signing, job conditions and secret mappings.
The independent Publisher condition still requires
`vars.CONNECTOR_PUBLICATION_ENABLED == 'true'`, successful preflight and
`!inputs.acceptance_only`, plus official repository/owner/human, main, manual
dispatch and original-attempt checks. Existing executable gate-model regressions
cover missing/nontrue variables, failed/skipped dependencies and acceptance-only
job exclusion. True/true committed trust cannot enable that condition.

Acceptance-only still skips the entire Publisher job before its protected
environment and credential steps. Explicit Verifier-only secret forwarding,
authorize/prepare before Publisher credentials, isolated signing, shared
non-canceling publication concurrency and fresh mutation-boundary rechecks remain.
Publisher retains Contents Write plus Actions/Administration/Metadata Read,
Workflows No access and single-official-repository scope. Accepted ADR 0006's
split permission model and rejected ADR 0007's status remain unchanged.

## F. Executed validation — PASS

Commands run from the Connector repository. `WORK` below means
`/private/tmp/atlas-phase4b6-s4-review`; logs and preservation tooling are outside
the repository. Local interpreter is Python **3.14.7**. Required hosted Python
**3.12** PR CI remains a separate outstanding gate.

| Executed command/check | Result |
| --- | --- |
| `.venv/bin/python tools/test_collection.py --archive /Users/Ben/Code/atlas/vendor/collections/community-proxmox-2.0.0.tar.gz --output WORK/test-collections` | PASS: reviewed collection SHA-256 `77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6`; sibling input read only |
| `.venv/bin/python -m pytest -q tests/test_connector_publication.py tests/test_connector_sigstore.py tests/test_connector_draft_recovery.py tests/test_publication_packaging.py` | PASS: **721 passed**, 16.79 seconds; `focused-publication-signing-final.log` |
| `ATLAS_TEST_COLLECTIONS_PATH=WORK/test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q` | PASS: **2,589 passed**, zero failures/skips, 68.82 seconds; 180 inherited Python 3.14 `ansible_runner` deprecation warnings; `full-ansible-final.log` |
| `/private/tmp/atlas-phase4b2-tools/actionlint -shellcheck= -pyflakes= .github/workflows/*.yml` | PASS: all seven workflows, actionlint **1.7.12**; optional shellcheck/pyflakes disabled; `actionlint.log` |
| `.venv/bin/python -m pytest -q tests/test_documentation.py` | PASS: **1 passed**, repository Markdown links/whitespace/newlines/fences; `documentation.log` |
| `.venv/bin/python WORK/verify-preservation.py` | PASS: exact trust diff, all workflow bytes, complete preservation inventory and unchanged HEAD/refs/index; `preservation.json` and `preservation.log` |
| `git diff --check` | PASS: clean tracked-file whitespace |

The initial focused run had 712 passed and nine new-test assertion failures:
the test expected an internal mismatch code directly in the public receipt.
The frozen publisher intentionally sanitizes that code. The corrected test
records the actual exception and asserts both its exact reason and the existing
generic safe receipt. All 721 cases then passed; no production behavior changed.

The first full run had 2,588 passed and one documentation-link failure because it
reached the new README link before this report was created. The report now exists
and the separate documentation check passed. The complete full-suite rerun passed
as recorded above. Documentation and preservation checks were repeated after the
final report update.

## G. Preservation, changed files and compatibility — PASS

The preservation inventory was captured before editing: 172 tracked files,
234 existing ignored `dist/` files and 93 files in the external S4 evidence
archive. Exact-byte verification passed: only the four authorized tracked files
below changed, 168 tracked files remain exact and this report is the only new
file. All seven workflows, 26 tracked fixture files, 234 existing `dist/` files
and 93 external evidence files remain exact. HEAD, refs and index are unchanged;
nothing is staged. Every original tracked file also matched its expected-base
Git bytes before comparison. All existing test functions apart from the active
baseline remain structurally identical, including false-flag and enable-gate
regressions; the historical 0.2.1 and S2/S3 evidence sections remain byte exact.

| Material file | Reason |
| --- | --- |
| `catalogue/publication/connector-trust.json` | Only the two proposed false-to-true trust flags |
| `tests/test_connector_publication.py` | Active trust baseline and nine independent-mismatch regressions |
| `README.md` | Completed qualification, proposed trust and separate live/release gates |
| `catalogue/publication/connector-packages.md` | Current controlled runbook and temporary mismatch; historical evidence retained |
| `docs/phase-4b6-s4-activation-preparation.md` | This A–J engineering and owner-handoff report |

No database changes or migrations. No API/UI routes, schemas, requests, package
format, authorization/tenancy rules, source metadata or dependencies change.
Official repository identity and credential scope remain enforced by the existing
backend tooling. This repository has no feature ledger; no Atlas/SDK change or
ADR revision is required. Historical reports and genuine fixtures remain history.

The frozen catalogue publisher/trust, package S4 implementation, trusted roots,
SDK wheel/locks, all existing Connector/package bytes and incomplete Proxmox
0.2.1 history are preserved. The protected 0.2.1 tag, original build/artifact,
incomplete draft and checksum asset are historical evidence, not catalogue
authority. No draft endpoint was accessed. No 0.2.2 source, metadata, artifact,
tag or release is introduced.

## H. Human PR review and hosted CI — BLOCKED pending owner action

The local preparation does not satisfy the human approval gate. Review the exact
five-file diff, original qualification evidence, tests and preservation results;
submit the PR separately and require successful hosted Python 3.12 `validate` CI
and security review before approving merge. Local Python 3.14 results do not
claim that hosted CI ran or passed. Changes remain unstaged and uncommitted.

## I. Live configuration and independent enable gate — BLOCKED

The owner states that live repository `CONNECTOR_VERIFICATION_POLICY` currently
has `enabled: false` and `live_signer_accepted: false`. This task does not freshly
query or change live settings. The proposed committed true/true profile therefore
has an intentional temporary mismatch with live policy. **No publication dispatch
is permitted during that mismatch**, including after a merge that precedes owner
configuration. Independent equality and false-flag rejection remain enforced.

After reviewed merge, separate explicit owner authorization is required to set
the complete matching live repository trust. Freshly verify repository and
environment values/overrides, protections, complete bypass inventories and
existing key custody without extracting or moving credentials. Do not silently
reconcile settings. Separately authorize any later change to the independent
`CONNECTOR_PUBLICATION_ENABLED` gate; it must remain disabled through preparation.
Neither completed acceptance nor committed true/true trust authorizes that action.

## J. Future release approvals and repository state — BLOCKED for publication

Prepare Proxmox **0.2.2** only in a future separately reviewed source/metadata PR.
Qualify it, retain successful required CI and reviewed main source P, reproduce
exact digest D and confirm the entire P/C workflow directory equality before
each operation. Preserve all 0.2.1 objects and history. Obtain distinct explicit
human authorization for **Tag**, **Stage** and **Finalize**, with fresh signed
admission and live control checks each time. Require independent immutable
release verification before any separately authorized catalogue publication.

No commit, staging, push, merge, tag, workflow dispatch/rerun, GitHub variable or
permission change, live Publisher activation, live Publisher credential use or
token mint, release-draft interaction or publication occurred. Local synthetic
tests do not create or use live credentials. No release approval is implied.

Final `git status --short`:

```text
 M README.md
 M catalogue/publication/connector-packages.md
 M catalogue/publication/connector-trust.json
 M tests/test_connector_publication.py
?? docs/phase-4b6-s4-activation-preparation.md
```

Outstanding human gates are PR/security review and hosted CI/merge, matching live
trust approval, independent publication-enable approval, future 0.2.2 preparation/qualification
and separate Tag/Stage/Finalize and catalogue approvals.
