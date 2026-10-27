# Phase 4B.2 — S3 repinning local qualification

Date: 28 October 2026 (Pacific/Auckland). Local engineering only; publication disabled.

## A. Result

**PASS — S3 repinning prepared and fully validated locally.** All four bindings
identify exact reviewed S3; the six frozen executable files and historical signed
evidence remain unchanged. All changes are unstaged/uncommitted. Both trust flags
remain false. Genuine S3 acceptance and publication authority are not established.

## B. Source branch and baseline

Repository `benchristian88/atlas-connectors`, requested branch
`feature/connector-publication-s3-pinning`, initially clean at exact S3
`be24042c4e7446c7d88d2f08608ab7f058bb24b6`. The branch already existed; its
reflog records creation from HEAD. Local main and origin/main equal S3, independently
confirmed by read-only GitHub main metadata. No branch rewrite was necessary.
All original local refs/tags were recorded and preserved. No unrelated changes
were present. No repository, ancestor or nested AGENTS.md was found here.

[PR #41](https://github.com/benchristian88/atlas-connectors/pull/41) is merged at
S3, with one parent and the same tree as reviewed head
`3470971e4909fecd518aa02c87fda710e2741884`, confirming the squash merge. The
required [validate check](https://github.com/benchristian88/atlas-connectors/actions/runs/40538417883/job/122309864477)
completed successfully for S3. The reviewed implementation requires exact
SHA-pinned SAN/buildSignerURI plus the independent signer digest, with strict
caller, issuer, repository, statement and transparency checks retained.

Sibling baselines were clean: Atlas `dev` at
`808ee0f76f77c11e17a6c403806ce0666e30074e`, SDK `main` at
`8b0518c462289cca4758c3b9bf362f1130928a1c`. Both remain unchanged.

## C. Four exact S3 bindings

All four bindings use `be24042c4e7446c7d88d2f08608ab7f058bb24b6`:

| Binding | Location |
| --- | --- |
| Reusable Verifier workflow | `connector-publish.yml`, preflight `uses` |
| Publisher trusted executable checkout | First Publisher checkout `ref` |
| Trusted implementation revision | Publisher `ATLAS_IMPLEMENTATION_REVISION` |
| Independent package trust | `connector-trust.json`, `signer_revision` |

## D. Files changed

| File | Rationale |
| --- | --- |
| `.github/workflows/connector-publish.yml` | Three exact S3 bindings and reviewed-baseline comment |
| `catalogue/publication/connector-trust.json` | S3 signer revision only |
| `tests/test_connector_publication.py` | S3 assertions/guard/preflight negatives; explicit historical model revision |
| `tests/test_connector_sigstore.py` | Preserve genuine S2 assertions; separate synthetic S3 identity/digest tests |
| `tests/test_publication_packaging.py` | Exact S3 workflow allowlist, catalogue S4 unchanged |
| `README.md` | Current merged correction, local pinning and acceptance gates |
| `catalogue/publication/connector-packages.md` | Current S3 procedure and owner-only post-merge steps |
| This report | Validation evidence and human handoff |

No database migration, application API/UI, tenancy or package format changes.
No feature ledger exists in this repository; historical ADRs/reports are unchanged.
The pinning cycle upgrades the publication engine, not the Connector version.
Routine releases select package/version/source/digest as data and need new engine
pins only if the publication engine changes. Proxmox 0.2.1 remains the proposal.

## E. Security boundaries

Both `enabled` and `live_signer_accepted` remain false. Existing ruleset/environment
IDs, publication controls, concurrency, App identities/permissions and secret
mapping are preserved. Acceptance-only excludes the entire Publisher job and its
environment/key/token/operation steps. Real inline guard and downstream preflight
checks require S3 under S3 trust; mutable refs, S2, wrong SHAs and mismatches reject.
No trusted executable code or live settings are changed.

## F. Historical evidence

Failed original [run 40523236413](https://github.com/benchristian88/atlas-connectors/actions/runs/40523236413)
stopped before checkout/signing under original S, with Publisher skipped. Its
literal job context and historical report remain intact.

Original S2 [run 40534608937](https://github.com/benchristian88/atlas-connectors/actions/runs/40534608937)
completed observations and genuine signing, then failed local authentication.
The genuine certificate/statement/bundle and original job/run summaries remain
historical S2 evidence in `tests/fixtures/connector_sigstore_s2/`, with exact
S2 `c2b4ecb493160f0226b1724aa688d0f436d51489`. Its SHA-pinned signer URI explains
the previous main-ref certificate mismatch corrected by PR #41. Original subject
bytes and hosted gh output were not exported; the exact hosted CLI exit status
cannot be independently established. See the unchanged
[certificate qualification](phase-4b2-sigstore-qualification.md).

The historical policy model explicitly uses S2; prospective S3 certificate/CLI
models are synthetic and cannot establish cryptographic or hosted acceptance.
Genuine S2 evidence cannot authorize S3. No certificate or signed bytes are relabeled.

Independent offline archival authentication with official `sigstore==4.3.0`
again verified the original S2 DSSE signature/certificate/SCT/Rekor evidence using
the frozen public-good root. Exact S2 identity passed; main, a wrong SHA and S3
identities rejected. Bundle SHA-256 remains
`f85c122df49f2c49c0117830dc81c00a52670e982368407ba9b406c74c96eb80`;
PEM SHA-256 remains
`f4fa1cc084858a52e94e54adfc4a0a6852e14fee3c45fba26119ad524bf99d90`.
This authenticates the archived statement, not the unavailable original subject
contents, and is not genuine S3 or pinned-gh hosted acceptance.

## G. Testing and preservation

Commands ran from `/Users/Ben/Code/atlas-connectors`. Local Python is 3.14.7;
required Python 3.12 CI for the eventual pinning PR remains a human merge gate.
S3's existing required CI is successful. Logs, baseline/preservation inventories,
local detached clones and build outputs are retained under
`/private/tmp/atlas-phase4b2-s3-review` (WORK below).

| Executed command/check | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q tests/test_connector_publication.py tests/test_connector_sigstore.py -k 'reviewed_pin or inline_guard or caller_and_reusable_workflow or historical_failed_s or workflow_pins or acceptance_only or publisher_entrypoints or certificate or signer or s3 or preflight_model or pinned_cli'` | **369 passed**, 168 deselected, 8.04 seconds; `focused-pytest.log` |
| `.venv/bin/python -m pytest -q tests/test_connector_publication.py tests/test_connector_sigstore.py` | **537 passed**, 13.48 seconds; `connector-pytest.log`; historical certificate policy tests retained, synthetic S3 tests added |
| `.venv/bin/python -m pytest -q tests/test_publication*.py tests/test_authorization_sigstore.py tests/test_connector_release.py tests/test_ruleset_visibility.py tests/test_verification_github.py tests/test_verifier_signer_experiment.py tests/test_verifier_workflow.py tests/test_historical_workflows.py` | **1,373 passed**, 20.03 seconds; `historical-pytest.log`, including genuine historical offline signature regressions |
| `.venv/bin/python tools/test_collection.py --archive /Users/Ben/Code/atlas/vendor/collections/community-proxmox-2.0.0.tar.gz --output /private/tmp/atlas-phase4b2-s3-review/test-collections` | Passed approved collection archive hash `77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6`; read-only sibling input |
| `ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-phase4b2-s3-review/test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q` | **2,417 passed**, zero failures/skips, 66.21 seconds; `full-pytest.log`; 180 existing `ansible_runner` Python 3.14 `codecs.open` deprecation warnings |
| `/private/tmp/atlas-phase4b2-tools/actionlint -shellcheck= -pyflakes= .github/workflows/*.yml` | Passed all seven active workflows with actionlint 1.7.12; optional shellcheck/pyflakes disabled |
| `.venv/bin/python -m compileall -q tools tests` | Passed |
| `.venv/bin/python -m json.tool catalogue/publication/connector-trust.json /private/tmp/atlas-phase4b2-s3-review/trust-validated.json` | Passed JSON parsing; preservation script also checks canonical JSON, real `check_trust` schema/field types, exact controls and disabled-publication rejection |
| `.venv/bin/python -m pytest -q tests/test_documentation.py` | **1 passed**; Markdown links, fences, newlines and whitespace |
| `.venv/bin/python -m pip check` and `importlib.metadata.version` assertions | No broken requirements; all six development pins and SDK 1.1.0 match; unwritable pip-cache warning only |
| `.venv/bin/python /private/tmp/atlas-phase4b2-s3-review/verify-preservation.py` | Passed all 164-file inventory, exact bindings, unchanged controls/refs/siblings, frozen S3 executables, historical fixtures, S4/sequence-one and build checks; `preservation.json` / `preservation.log` |
| Runbook's first Python block executed verbatim with `.venv/bin/python -c`, clean detached S3 tools/source and test-only source=S3 | Passed exact committed-source checks, archive/SPDX/licence/qualification validation and two equal 0.2.1 builds; `runbook-reproduction.log`. This validates the procedure without selecting or approving future P/D |
| `/private/tmp/atlas-sigstore-correction-verifier/bin/python -` with the archival DSSE verification block | Passed original S2 signature and three wrong-identity rejections; `s2-archival-authentication.json` / `s2-authenticated-statement.json`; no production dependency or fixture change |
| `git diff --check` and `git diff --no-index --check -- /dev/null docs/phase-4b2-s3-local-qualification.md` | Clean tracked/new-file whitespace; no-index returns its normal difference status with no whitespace diagnostics |

No test failed. Initial shell `git ls-remote` could not resolve github.com and
`gh` was unavailable on PATH; read-only GitHub connector calls independently
confirmed main, PR #41 and successful validate. No fetch or privileged fallback
was needed, and no automatic approval rejection occurred.

Preservation covers all **164 original tracked files**: exactly seven authorized
files changed, **157 unchanged**, and one new report. All six named executables
match `git show be24042c4e7446c7d88d2f08608ab7f058bb24b6:<path>` byte for byte.
All tools, vendor SDK/hash locks, Connector source and fixture files are unchanged.
The original failed-run context/text, all historical reports/ADRs, catalogue S4
workflow/trust/policy and sequence one remain intact. Both trust JSON and caller
workflow parse identically to baseline after changing only the four intended pins;
no other controls changed.

Repeated current builds and separate committed S3 builds produce identical archive
and detached metadata bytes:

| Package | Preserved archive SHA-256 |
| --- | --- |
| Proxmox 0.2.1 | `96eaa736c2919e56e09b9613dddd8648ad1f43b77679899ab706261b2a38e509` |
| Historical Proxmox 0.2.0 | `a14fec5ab485c980688ff5907e8835ddd3e9cecd1a6989ef252cbcb1b1dc4ef8` |
| Historical candidate | `dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97` |

These local deterministic-build checks are unattested and confer no approval to
reuse a prior digest in a future request. No future P/D or dispatch is selected.
Live privileged configuration, hosted isolation and genuine S3 acceptance were
not exercised, as required by this local-only scope.

## H. Genuine acceptance readiness

Successful S3 genuine acceptance remains required. After human merge, update the
repository Actions variable `CONNECTOR_VERIFICATION_POLICY` from the newly committed
trust JSON with both false flags. Independently verify effective repository and
environment configuration, policy overrides and absent/false publication enable
gate. Select and independently reproduce exact P/D, then obtain separate authority
for a new original main acceptance-only run. Preserve/authenticate certificate,
statement, preflight, request/trust/policy and complete security observations;
confirm Publisher skipped, no credential operations and no tag/release created.
No privileged steps are performed by this increment. ADR 0006 owner acceptance
and any publication activation remain separate gates.

## I. Git state and remote activity

`git status --short` (also checked with `--untracked-files=all`):

```text
 M .github/workflows/connector-publish.yml
 M README.md
 M catalogue/publication/connector-packages.md
 M catalogue/publication/connector-trust.json
 M tests/test_connector_publication.py
 M tests/test_connector_sigstore.py
 M tests/test_publication_packaging.py
?? docs/phase-4b2-s3-local-qualification.md
```

Nothing is staged. HEAD, main and origin/main remain exact S3. All original
branches/tags and clean sibling baselines remain unchanged. Temporary detached
clones/builds are outside the working tree. No commit, push, PR, merge, reset,
rebase, tag, publication, workflow dispatch/rerun, variable or GitHub setting
change, secret access or live App token mint occurred. GitHub activity was GET-only.

## J. Human handoff

Review the local diff, then manually commit/push/open the S3 pinning PR. Require
security review and successful Python 3.12 `validate` on that PR before merging.
Only after merge may the owner perform the separately authorized configuration
and genuine acceptance procedure in the [runbook](../catalogue/publication/connector-packages.md).
Neither local pinning nor future acceptance grants publication authority.
