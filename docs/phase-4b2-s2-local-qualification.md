# Phase 4B.2 — S2 repinning local qualification

Date: 28 October 2026 (Pacific/Auckland). Local engineering only; publication disabled.

## A. Executive result

**S2 REPIN LOCAL PASS.** All four production bindings identify exact reviewed S2;
trusted executable files and historical evidence are preserved. Complete local
security and Ansible-enabled regression testing passed. Changes remain local,
uncommitted and unpushed on the requested feature branch. Publication remains
disabled. This is not genuine signer acceptance or publication authority.

## B. Repository baseline

Repository `benchristian88/atlas-connectors`, origin
`https://github.com/benchristian88/atlas-connectors.git`. Initial tracked/untracked
working tree was clean, with 153 tracked files. The requested feature branch
already existed at `94f9e88844090a7de97028a62254accd5ec93d6c`, PR #39's source
commit. Local main initially identified `b2fcc15ce06b5b57ae3b3c7ecf6264bcd1d168f0`.

A safe fetch independently obtained origin/main at exact S2
`c2b4ecb493160f0226b1724aa688d0f436d51489`. Read-only GitHub PR metadata confirmed
[PR #39](https://github.com/benchristian88/atlas-connectors/pull/39) is merged into
main with that merge SHA; the separate commit API confirmed the same correction.
The PR was squash-merged: source and S2 have identical tree
`35ac2c12b268c0fa61ced46348ca686f1d2caf2a` but neither is the other's ancestor.

To preserve the existing branch without rewriting history, it was renamed
`feature/connector-publication-s2-pinning-pr39-source`, retaining its original SHA.
Local main was fast-forwarded by fetch. The requested
`feature/connector-publication-s2-pinning` was then created from synchronized main;
HEAD, main and origin/main all equal S2. No reset, stash, merge or rebase occurred.
No repository, ancestor or nested AGENTS.md was found in atlas-connectors.

Read-only siblings started clean: Atlas dev at
`808ee0f76f77c11e17a6c403806ce0666e30074e`, SDK main at
`8b0518c462289cca4758c3b9bf362f1130928a1c`. Neither is in the change scope.

## C. Exact implementation bindings

All four literals equal `c2b4ecb493160f0226b1724aa688d0f436d51489`:

| Binding | Location |
| --- | --- |
| Reusable workflow | `connector-publish.yml` preflight `uses`: `benchristian88/atlas-connectors/.github/workflows/connector-verifier.yml@c2b4ecb493160f0226b1724aa688d0f436d51489` |
| Publisher executable checkout | First Publisher checkout `ref` |
| Implementation revision | Publisher `ATLAS_IMPLEMENTATION_REVISION` |
| Independent package trust | `connector-trust.json` `signer_revision` |

Caller C and package source P remain separate inputs. Neither supplies executable
authority. Both trust flags remain false; the complete schema, 900-second freshness,
five ruleset IDs and verification environment ID remain unchanged.

## D. Material changes

| File | Rationale |
| --- | --- |
| `.github/workflows/connector-publish.yml` | Three exact S2 executable bindings and explanatory comment |
| `catalogue/publication/connector-trust.json` | S2 signer revision only |
| `tests/test_connector_publication.py` | S2 production fixture, preserved literal historical S fixture, exact pin/guard/preflight rejection coverage |
| `tests/test_publication_packaging.py` | Exact S2 reusable-workflow allowlist; original S4 unchanged |
| `catalogue/publication/connector-packages.md` | Completed correction, local repinning, pending owner configuration, exact P/D preparation and genuine evidence procedure |
| `README.md` | Current status and links to historical/current qualification |
| This report | Local qualification and human handoff |

No database migration, application API, UI, route, tenancy, SDK, Connector source
or package format changes. Historical ADRs/reports remain unchanged; ADR 0006 is
still Proposed. The repository has no Atlas-style feature ledger to update here.

## E. Security preservation

The S2 inline guard requires the exact independently trusted SHA-suffixed reusable
reference and matching job SHA before checkout/credentials. Downstream preflight
requires the same reference before authentication. The original caller must still
identify official `connector-publish.yml@refs/heads/main`. Original attempt one,
approved human, official repository/owner, independent trust/policy/request and
complete ruleset/bypass checks remain intact.

Acceptance defaults true and excludes the entire Publisher job even with an
erroneously true publication gate. Publisher environment entry, key injection,
token mint and operation entrypoints remain excluded. Local tests model scheduling
and execute real guards/entrypoints; they do not certify hosted isolation.
The existing signed package admission, strict certificate comparisons, source/build
preparation and admitted Publisher permission checks are unchanged. No App IDs,
scopes or proposed ADR 0006 authority split change.

## F. Historical evidence and immutable source

Failed [run 40523236413](https://github.com/benchristian88/atlas-connectors/actions/runs/40523236413),
attempt one, job `122255725484`, used C
`b2fcc15ce06b5b57ae3b3c7ecf6264bcd1d168f0` and original S
`d6601ad97815a85da164e4329766ea17b62bddc9`, `operation=tag`, acceptance-only true.
Its exact S-based context remains in the runbook and historical report, and is
retained literally in `HISTORICAL_FAILED_JOB_CONTEXT`. The prospective S2 fixture
models the demonstrated format; it is not evidence of a genuine S2 run.
The failed run stopped before signing with Publisher skipped and no publication.

S2 executable files are frozen: `connector-verifier.yml`,
`connector_publication_preflight.py`, `connector_publication_contract.py`,
`connector_publication_sigstore.py`, `connector_publication_github.py` and
`publish_connector.py`. Preservation checks and package digests are recorded in G.
Historical catalogue identities, sequence one, original policy and S4 remain intact.
The failed run produced no package-preflight certificate. Exact SAN/buildSignerURI
comparisons remain strict; any genuine discrepancy must fail closed for a new
reviewed implementation and pinning cycle.

## G. Tests and validation

Local interpreter is Python 3.14.7; required Python 3.12 GitHub CI remains a merge
gate. Commands below ran from `/Users/Ben/Code/atlas-connectors`. Evidence and
complete tracked/untracked inventories are retained under
`/private/tmp/atlas-phase4b2-s2-review`. All test credentials/providers are synthetic;
genuine historical signature verification is offline.

| Executed command/check | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q tests/test_connector_publication.py -k 'reviewed_pin or inline_guard or caller_and_reusable_workflow or historical_failed_s or workflow_pins or acceptance_only or publisher_entrypoints'` | **194 passed**, 168 deselected, 3.43 seconds; `focused-pytest.log` |
| `.venv/bin/python -m pytest -q tests/test_connector_publication.py` | **362 passed**, 8.22 seconds; 56 added cases, no removed adversarial coverage; `connector-pytest.log` |
| `.venv/bin/python -m pytest -q tests/test_publication*.py tests/test_authorization_sigstore.py tests/test_connector_release.py tests/test_ruleset_visibility.py tests/test_verification_github.py tests/test_verifier_signer_experiment.py tests/test_verifier_workflow.py tests/test_historical_workflows.py` | **1,373 passed**, 19.22 seconds; `historical-pytest.log` |
| `ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-phase4b2-s2-review/test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q` | **2,242 passed**, zero failures/skips, 61.79 seconds; 180 inherited `ansible_runner` Python 3.14 `codecs.open` deprecation warnings; `full-pytest.log` |
| `.venv/bin/python tools/test_collection.py --archive /Users/Ben/Code/atlas/vendor/collections/community-proxmox-2.0.0.tar.gz --output /private/tmp/atlas-phase4b2-s2-review/test-collections` | Passed exact approved community.proxmox 2.0.0 SHA-256 `77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6` before provisioning |
| `/private/tmp/atlas-phase4b2-tools/actionlint -shellcheck= -pyflakes= .github/workflows/*.yml` | Passed all seven active workflows; actionlint 1.7.12; optional shellcheck/pyflakes disabled |
| `.venv/bin/python -m compileall -q tools tests` | Passed |
| `.venv/bin/python -m json.tool catalogue/publication/connector-trust.json /private/tmp/atlas-phase4b2-s2-review/trust-validated.json` | Passed; exact trust schema/field types, canonical JSON and disabled-publication validation also pass through real `check_trust` and preservation checks |
| `.venv/bin/python -m pytest -q tests/test_documentation.py` | **1 passed**; repository Markdown links, whitespace, newlines and fences |
| `.venv/bin/python -m pip check` and installed-version assertions using `importlib.metadata` | No broken requirements; all six pinned development requirements and SDK 1.1.0 match; unwritable pip-cache warning only |
| `.venv/bin/python /private/tmp/atlas-phase4b2-s2-review/verify-preservation.py` | Passed complete inventory, immutable S2 files, exact bindings, unchanged trust controls, historical text, S4/sequence-one policy, refs, siblings and deterministic package comparisons; `preservation.json` / `preservation.log` |
| Runbook's first Python block executed verbatim using `.venv/bin/python`, clean detached S2 tools/source checkouts and test-only P=S2 | Passed exact committed-source checks and two identical 0.2.1 builds; `runbook-reproduction.log`. This exercises the procedure, not approval of P/D or a dispatch |
| `git diff --check` and `git diff --no-index --check -- /dev/null docs/phase-4b2-s2-local-qualification.md` | Clean tracked/new-file whitespace |

No test failed. An initial local runbook harness resolved the virtualenv Python
symlink to the base interpreter and exited before preparation; using the virtualenv
interpreter directly passed without a product-code change. The initial sandboxed
fetch could not write `.git/FETCH_HEAD`; the authorized fetch succeeded after
sandbox escalation. No automatic approval rejection occurred.

Preservation covered all 153 original tracked files: exactly six permitted files
changed, 147 unchanged, one new report. All six named S2 implementation files match
`git show c2b4ecb493160f0226b1724aa688d0f436d51489:<path>` byte for byte; all tools,
vendor distributions and Connector source also match S2. The literal historical
failed-run block, all prior reports/ADRs and signed fixtures remain unchanged.
The original catalogue policy, four S4 bindings, historical accepted sequence-one
pointer `a275f63d0ac818a193826478328ee324be62353addc5c97a2ed0a28d217b5372`,
release metadata and original release workflow are unchanged.

Builds from current inputs and clean committed S2 inputs reproduce equal bytes:

| Archive | Preserved SHA-256 |
| --- | --- |
| Historical Proxmox 0.2.0 | `a14fec5ab485c980688ff5907e8835ddd3e9cecd1a6989ef252cbcb1b1dc4ef8` |
| Historical candidate | `dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97` |
| Local unattested Proxmox 0.2.1 | `96eaa736c2919e56e09b9613dddd8648ad1f43b77679899ab706261b2a38e509` |

These are byte-preservation results, not authorization to reuse a digest in the
next workflow request. Python 3.12 CI, live privileged configuration verification
and genuine acceptance/certificate qualification were not run locally. They remain
owner-operated gates. No genuine positive package certificate was fabricated.

## H. Acceptance readiness

The [operator runbook](../catalogue/publication/connector-packages.md) separates
the failed S run, merged S2 correction, local pinning and pending genuine signing
qualification. It records owner-reported environment/protection/variable state
without presenting it as independently authenticated privileged verification.

After the pinning PR is merged, and before any new acceptance dispatch, the owner
must update the existing repository Actions variable `CONNECTOR_VERIFICATION_POLICY`
to the exact complete new committed `connector-trust.json`. Both flags stay false.
Verify absent/identical environment overrides and absent/false effective
`CONNECTOR_PUBLICATION_ENABLED`, including organization inheritance. Leave original
catalogue `VERIFICATION_POLICY`, secrets, App permissions, environments and rulesets
unchanged. No configuration change is performed by this local increment.

The future request is workflow `connector-publish.yml`, branch main, operation tag,
acceptance-only true, package `proxmox-v0.2.1` with independently reviewed exact P
and reproduced D. The runbook uses S2's existing builders against committed source
as data; it does not select P, equate it with S2/C or authorize an earlier digest.

Preserve the new original attempt-one run, actors, C/S2, pinned job identity,
successful isolated preflight, authentic package-specific signature/certificate/
statement claims, exact policy/trust/request, privileged observations with all
bypass arrays, Publisher conclusion skipped and evidence of no credential use or
tag/release/repository mutation. Preflight artifacts expire after one day. A green
check alone is insufficient; genuine certificate qualification remains pending.

## I. Repository state

`git status --short` (also checked with `--untracked-files=all`):

```text
 M .github/workflows/connector-publish.yml
 M README.md
 M catalogue/publication/connector-packages.md
 M catalogue/publication/connector-trust.json
 M tests/test_connector_publication.py
 M tests/test_publication_packaging.py
?? docs/phase-4b2-s2-local-qualification.md
```

This is the complete changed/new file inventory. Nothing is staged. HEAD, main
and origin/main still identify S2; the preserved old branch retains its source
commit. All other local refs, including every tag, match the recorded baseline.
Atlas and SDK remain clean at their original branches/SHAs in B.
All intended changes are local and uncommitted. Remote activity is read-only fetch
and GitHub PR/commit metadata. Temporary local clones and build outputs are
outside the working tree.
No commit, push, PR creation, merge, rebase, tag, release, workflow dispatch/rerun,
GitHub setting/variable change, secret access or live App token mint occurred.

## J. Human handoff

Review the local diff and qualification results, then manually commit/push/open the
pinning PR. Complete security review and required Python 3.12 CI before merge.
Next perform the owner variable update and privileged configuration verification.
Only a separately approved new original acceptance-only dispatch may follow exact
P/D approval. Preserve and review genuine evidence before any separate activation
decision. Neither this work nor acceptance authorizes package publication,
catalogue sequence two or remote installation.
