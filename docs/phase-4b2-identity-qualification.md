# Phase 4B.2 — genuine acceptance workflow identity correction

Date: 28 October 2026 (Pacific/Auckland). Local implementation and validation only.

## A. Result

**PASS for local correction and qualification.** This change corrects a demonstrated
hosted job identity defect and the provable downstream preflight mismatch.
Publication remains disabled, current
production pins remain at original S, and genuine package signing acceptance is
still outstanding. No remote mutation or privileged operation is authorized here.

## B. Git baseline

Repository: `benchristian88/atlas-connectors`. Source branch main, local main,
origin/main and starting HEAD all identify caller C:
`b2fcc15ce06b5b57ae3b3c7ecf6264bcd1d168f0`. A read-only GitHub branch API request
independently confirmed current remote main at that same SHA.

Requested branch `fix/connector-verifier-workflow-identity` already existed and was
checked out at exactly C with a clean tracked/untracked tree. It was reused without
recreation, reset, rebase, stash or commit. The initial tracked inventory contained
152 files. Baseline hashes, refs and status were captured before edits in
`/private/tmp/atlas-phase4b2-identity-review`.

Atlas was clean on dev at `808ee0f76f77c11e17a6c403806ce0666e30074e`; SDK was clean
on main at `8b0518c462289cca4758c3b9bf362f1130928a1c`. Neither is modified.
No repository/ancestor/nested AGENTS.md exists in atlas-connectors; the supplied
scope and repository safety requirements were followed.

## C. Root cause and genuine evidence

[Run 40523236413, attempt 1](https://github.com/benchristian88/atlas-connectors/actions/runs/40523236413)
used caller C above and reviewed implementation S
`d6601ad97815a85da164e4329766ea17b62bddc9`. The supplied acceptance request was
`operation=tag`, `acceptance_only=true`, proposing Proxmox 0.2.1, with correct
independent trust configuration. The prompt supplies the genuine job context:

```text
workflow_ref: benchristian88/atlas-connectors/.github/workflows/connector-verifier.yml@d6601ad97815a85da164e4329766ea17b62bddc9
workflow_sha: d6601ad97815a85da164e4329766ea17b62bddc9
workflow_repository: benchristian88/atlas-connectors
workflow_file_path: .github/workflows/connector-verifier.yml
```

[Job 122255725484](https://github.com/benchristian88/atlas-connectors/actions/runs/40523236413/job/122255725484)
failed at `Require independently configured package signer before checkout or credentials`
with `connector_verification_trust_not_accepted`. The guard instead required
`benchristian88/atlas-connectors/.github/workflows/connector-verifier.yml@refs/heads/main`.
Executing the baseline guard from HEAD against the supplied pinned context locally
reproduced that exact rejection before creating a GITHUB_OUTPUT file.

Read-only GitHub original-attempt metadata independently confirms main, C, dispatch,
attempt 1, both human actors and exactly one referenced reusable workflow at S/S.
Original-attempt job metadata confirms the initial guard failure; checkout,
observation, signing and upload were skipped. Publisher job 122255809992 was
skipped with an empty step list and no runner assigned. No Publisher token, tag,
release, original build or signed preflight was created by that run. The local
reproduction is a regression, not a second hosted execution or signing acceptance.

## D. Corrective implementation and material files

| File | Change |
| --- | --- |
| `.github/workflows/connector-verifier.yml` | Build the expected exact reusable reference from the fixed repository/path and independently configured signer SHA; preserve all other checks and output only the matched pinned reference |
| `tools/connector_publication_preflight.py` | Require that same exact SHA-pinned reference before authentication; preserve separate caller checks |
| `tests/test_connector_publication.py` | Use the supplied genuine job identity; execute the revised inline guard and its output through synthetic preflight; add explicit negative regressions without removing prior coverage |
| `catalogue/publication/connector-packages.md` | Record failed run, corrected identity surfaces, safe outcome, certificate uncertainty and separate S2 rollout |
| `docs/phase-4b2-pr2-local-qualification.md` | Add a historical-status notice linking this correction; preserve the original qualification record |
| `README.md` | Update current acceptance status and link the correction |
| This report | A–J evidence, validation, preservation and human handoff |

Executable changes are two equality-reference corrections. No database changes or
migrations are needed. No application APIs, UI, routes, authorization or customer/
site tenancy contracts change. The workflow's corrected identity contract rejects
mutable reusable main refs; the caller main identity remains required.

## E. Trust-model impact

The inline guard still requires exact trusted repository and workflow path,
approved package-trust schema, strict Boolean `enabled` / `live_signer_accepted`,
a nonzero lowercase 40-character trusted SHA, exact job SHA equality and exact
reference equality to that same SHA. With the current configuration, the only
accepted job reference is the complete S-suffixed reference recorded in C.
No suffix matching, dual-ref fallback, arbitrary valid-SHA acceptance, operator
executable input, main/tag checkout or privilege expansion is introduced.

Both checked-in package flags remain false. All four production S bindings are
unchanged: reusable call, Publisher executable checkout, implementation environment
literal and package trust revision. The independent repository policy variable is
not changed. `CONNECTOR_PUBLICATION_ENABLED` is not changed. Acceptance-only still
excludes the entire Publisher job/environment/key/token path, regardless of its
gate; malformed acceptance fails request validation. First-attempt, main, actor,
repository/owner, complete ruleset/bypass and independent trust checks remain.

Regressions execute actual inline Python with the genuine pinned context, reject
main/tags/wrong references, wrong digest, wrong repository/path, inconsistent ref/
digest pairs, consistent but untrusted pairs, unsupported schema/flags/revisions
and false/malformed acceptance under disabled trust. Existing negative security,
Publisher exclusion/entrypoint, permission and four-binding coverage is retained.

## F. Downstream and certificate analysis

`github.workflow_ref` / `GITHUB_WORKFLOW_REF` identify the main caller
`connector-publish.yml`; caller/source digest C is separate from implementation S.
`job.workflow_ref` identifies the pinned reusable `connector-verifier.yml` at S,
and `job.workflow_sha` must equal independently configured S. Guard output becomes
`VERIFIER_WORKFLOW_REF`. Its old preflight main-ref equality would reject the
corrected output before credentials. That downstream incompatibility is proven
from code and covered by executing the output through preflight; the failed hosted
run never reached it.

`tools/connector_publication_sigstore.py` is byte-identical to baseline. Its current
profile requires exact reusable SAN / buildSignerURI ending `@refs/heads/main`,
independent buildSignerDigest S, caller buildConfigURI at `connector-publish.yml@refs/heads/main`,
buildConfigDigest/source digest C, official numeric identities, hosted runner,
dispatch, original invocation/attempt, exact package subject/predicate and verified
transparency witnesses. The CLI still enforces signer workflow/digest and source
digest/ref with pinned gh 2.102.1 and frozen roots.

No genuine package-preflight certificate exists from the failed run. Its job
context proves no certificate spelling or claim representation. A future genuine
S2 bundle must establish those claims independently. The existing strict profile
fails closed on disagreement; any certificate correction needs actual evidence,
security review and another immutable implementation/pinning cycle. Existing
synthetic verified-output tests establish policy behavior only; genuine historical
catalogue/package/probe bundles remain negative package-admission evidence.
ADR 0006 remains Proposed and is not modified or activated.

## G. Regression testing and validation

Local Python is 3.14.7; required Python 3.12 CI remains a human PR gate. The approved
community.proxmox 2.0.0 archive was provisioned into the temporary test collection
path after enforcing SHA-256
`77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6`.
All test credentials/providers are synthetic; genuine historical bundles are
verified offline. No test dispatches or publishes.

| Executed command/check | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q tests/test_connector_publication.py -k 'inline_guard or caller_and_reusable_workflow'` | **57 passed**, 249 deselected, 1.59 seconds |
| `.venv/bin/python -m pytest -q tests/test_connector_publication.py` | **306 passed**, 7.56 seconds; 45 added cases, all previous negative coverage retained |
| `.venv/bin/python -m pytest -q tests/test_publication*.py tests/test_authorization_sigstore.py tests/test_connector_release.py tests/test_ruleset_visibility.py tests/test_verification_github.py tests/test_verifier_signer_experiment.py tests/test_verifier_workflow.py tests/test_historical_workflows.py` | **1,373 passed**, 18.42 seconds; log `historical-pytest.log` |
| `ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-phase4b2-identity-review/test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q` | **2,186 passed**, zero failures/skips, 61.00 seconds; 180 inherited ansible_runner Python 3.14 deprecation warnings; log `full-pytest.log` |
| `.venv/bin/python tools/test_collection.py --archive /Users/Ben/Code/atlas/vendor/collections/community-proxmox-2.0.0.tar.gz --output /private/tmp/atlas-phase4b2-identity-review/test-collections` | Passed reviewed archive digest validation and collection provisioning |
| `/private/tmp/atlas-phase4b2-tools/actionlint -shellcheck= -pyflakes= .github/workflows/*.yml` | Passed all active workflows with existing actionlint 1.7.12; optional shellcheck/pyflakes disabled |
| `.venv/bin/python -m compileall -q tools tests` | Passed, including changed preflight and regression code |
| `.venv/bin/python -m pytest -q tests/test_documentation.py` | **1 passed**; repository Markdown links, whitespace, newline and fences |
| `.venv/bin/python -m pip check` | No broken requirements; unwritable pip-cache warning only |
| `git diff --check` | Clean tracked whitespace |
| `git diff --no-index --check -- /dev/null docs/phase-4b2-identity-qualification.md` | Clean new-file whitespace; expected difference exit status 1 without diagnostics |
| Baseline guard execution against the supplied hosted job context | Reproduced `connector_verification_trust_not_accepted`, nonzero status, no output file |
| Complete tracked SHA-256/refs/HEAD/untracked inventory against starting C | Exactly six allowed tracked modifications, 146 unchanged files, one new report; all refs and HEAD unchanged |
| Final Atlas/SDK status/branch/HEAD checks | Clean at the read-only baseline branches and SHAs in B |

Logs, initial hashes/status/refs, final inventory and rebuilt archives are retained
under `/private/tmp/atlas-phase4b2-identity-review`. Python 3.12 CI and future genuine
signing/isolation acceptance were not run locally; they remain explicit handoff
gates. No certificate representation is inferred from successful synthetic tests.

## H. Historical preservation

The unchanged builders were executed with these exact arguments (prefix each with
`.venv/bin/python tools/build_bundle.py`):

| Arguments | Archive SHA-256 |
| --- | --- |
| `--output /private/tmp/atlas-phase4b2-identity-review/historical` | Proxmox 0.2.0: `a14fec5ab485c980688ff5907e8835ddd3e9cecd1a6989ef252cbcb1b1dc4ef8` |
| `--candidate --output /private/tmp/atlas-phase4b2-identity-review/historical-candidate` | Historical candidate: `dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97` |
| `--version 0.2.1 --output /private/tmp/atlas-phase4b2-identity-review/proxmox-0.2.1` | Local unattested 0.2.1: `96eaa736c2919e56e09b9613dddd8648ad1f43b77679899ab706261b2a38e509` |

All three match their previously recorded PR2 values exactly. The 0.2.1 digest is
local byte-preservation evidence, not approval of a future committed-source request.
The complete 152-file baseline inventory establishes unchanged tracked package,
catalogue and signed fixture bytes; genuine historical cryptographic regressions
also pass. No new signing fixture was fabricated.

No historical signed evidence, package source/metadata, catalogue identities,
sequence-one registry/pointer, frozen S4 workflow/helpers/policy/trust, SDK wheel/
hash lock, release workflow or Atlas/SDK code is changed. Original implementation
S is not rewritten. The local correction is not executable authority until the
human establishes S2 and separately repins the caller and independent trust.

## I. Git state and remote activity

Final tracked/untracked inventory is limited to these six modified tracked files
and this one new untracked qualification report:

```text
 M .github/workflows/connector-verifier.yml
 M README.md
 M catalogue/publication/connector-packages.md
 M docs/phase-4b2-pr2-local-qualification.md
 M tests/test_connector_publication.py
 M tools/connector_publication_preflight.py
?? docs/phase-4b2-identity-qualification.md
```

All edits are local and uncommitted on `fix/connector-verifier-workflow-identity`,
HEAD C. Remote activity was read-only GitHub branch search/main metadata and
original failed run/attempt/job metadata. No commits, pushes, PRs, merges, rebases,
tags, releases, workflow dispatches/reruns, settings changes, App permission changes,
secret access or live credential mints were performed.

## J. Human handoff

The local correction is ready for human commit/PR and security review. It is not
ready for hosted acceptance using the unchanged S pins: that original immutable
workflow still contains the demonstrated defect. Remaining work is the authorized
human review/pinning lifecycle and genuine certificate/isolation qualification,
not a local test failure.

1. Human reviews, commits/pushes and opens the corrective PR; after required CI
   and review, merge it into main and record exact new implementation **S2**.
2. In a separate reviewed pinning PR, replace original S with that exact S2 in all
   four production bindings: reusable `uses`, Publisher executable checkout,
   `ATLAS_IMPLEMENTATION_REVISION`, package trust `signer_revision`. Update explicit
   binding tests/allowlist and future operator examples to the same S2. Do not
   guess a merge SHA or change historical evidence. Both trust flags stay false.
3. Qualify that PR through required Python 3.12 CI, review and merge. Independently
   configure the complete repository `CONNECTOR_VERIFICATION_POLICY` to the reviewed
   disabled S2 trust; same-name environment overrides must be absent or match
   exactly. Keep effective `CONNECTOR_PUBLICATION_ENABLED` absent/false.
4. Under separate owner authority, perform a new original acceptance-only main
   run, original attempt 1, with Publisher skipped. Never rerun the failed run as
   acceptance. Retain the original bundle/subject, C/S2/request/policy/trust, verified
   certificate/statement and isolation evidence before one-day expiry.
5. Resolve any genuine certificate discrepancy through a separately reviewed
   immutable correction; only actual signing/isolation review and a separate owner
   decision can authorize later activation. This correction grants no publication
   authority and makes no genuine signing acceptance claim.
