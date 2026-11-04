# Catalogue 2 — final acceptance remediation

Date: 4 November 2026 (Pacific/Auckland).

## Result and preserved authority

The producer's H2 and M1 findings are remediated on the existing
`feature/catalogue-v2-publication-evidence` branch, HEAD
`e58788a667c0c0006477ac149e8ad28aedda0745`. All prior development and tests remain.
The seven active workflows, original publication tools, trust/policy files,
registry/sequence, historical artifacts and all owner approval records remain
unchanged. No commit, push, PR, merge, publication, signing, deployment, live
installation or LXC access occurred. No live workflow candidate was adopted.

The companion Atlas report is `docs/catalogue2-security-remediation-report.md` in
its existing `feature/catalogue-v2-consumption` checkout, HEAD
`9c10e96da10ebf7108c88f632d77beaab5051b6c`. It describes H1's measured 34 refresh +
6 installation = **40 anonymous REST requests**, with fourteen release downloads
and fourteen CDN transfers counted separately. All original-run and cryptographic
checks, numeric immutable identities and final uncached current rereads remain.

## H2

The original issuance +600-second reproduction rejected after immutable
finalization. It now rejects before PATCH with `archive_finalization_deadline`,
leaving the draft mutable and current unchanged. The original authenticated
selection witness determines the deadline. A last local check after all slow
reads requires a fixed thirty-second reserve inside the proposed 300-second
publication window. This covers the existing twenty-second provider request
timeout plus ten seconds of scheduling/clock headroom; it does not extend the
proposed 900-second selection bound, original expiry or same-job lifetime.

Actual provider publication time and immutable original bytes/identities are
still independently checked afterward. Tests cover the +600 case, insufficient
reserve, exact boundary, invalid/backward clocks and delay during the final read.
A separate provider-delay regression demonstrates the unavoidable residual:
publication can become immutable after admission but outside its permitted time;
verification then rejects and current never advances. Ambiguous writes and such
stranded releases require preserved evidence and a separately reviewed disposition.
No retrospective acceptance or recovery activation is supplied.

## M1

The generator reads exact hash-pinned historical S4 templates, so future active
workflow adoption cannot invalidate its generation input. Existing security tests
exercise both historical and successor profiles with explicit independent test
pins. The complete old S4 bootstrap and token assertions remain, using the retained
historical workflow/trust inputs. Original active-control hashes still protect
all unchanged live workflows/trust. Updating those active-control fingerprints
belongs to the later separately approved pin/adoption PR; historical hashes stay.

Generated Publisher tests assert signer/checkout/environment SHA agreement, C as
data only, download/admission before credentials, baseline permissions and secret
isolation, publish-only operations/commands, acceptance-only skip, separate gate,
and driver denial of recovery even under synthetic accepted contract inputs.
Unsupported bootstrap/recovery steps and temporary Workflows permission input are
absent from the generated candidate. Mutation tests reject changes to these guards.
Candidate-build tests assert manual-only preparation, exact candidate builder,
existing attestation subject/profile and absence of Publisher credentials.
Both CLI outputs require exclusive inactive files and preserve live controls.

## Remediation files

- `tools/publication_evidence.py`, `tools/publish_catalogue_evidence.py`: authenticated
  window result and final pre-PATCH admission margin; post-publication checks retained.
- `tools/prepare_evidence_workflow.py`: pinned stable templates and publish-only output.
- `tools/templates/catalogue-publish-s4.yml`, `tools/templates/catalogue-build-s4.yml`:
  byte-exact historical generation/test inputs, outside active Actions paths.
- `tests/fixtures/publication_evidence/s4-verifier-trust.json`: historical trust fixture.
- `tests/workflow_cases.py`, `tests/test_evidence_workflows.py`: explicit test profiles,
  both outputs, strict successor assertions and hostile mutations.
- `tests/test_verifier_workflow.py`, `tests/test_publication_packaging.py`: preserve
  historical assertions and exercise successor admission/permission/pin boundaries.
- `tests/test_publication_bootstrap.py`, `tests/test_publication_authorization.py`:
  preserve historical S4 bootstrap/trust coverage independently of future adoption.
- `tests/test_publication_evidence.py`, `tests/test_catalogue_evidence_driver.py`:
  deadline, remaining-budget, provider-delay and disabled-recovery regressions.
- This report, the prior completion report, durable contract and fixture provenance:
  explain remediation and residual risks without granting activation authority.

No migration, database, public API, SDK/package schema or active signing profile
changed. Phase 1's original 128 evidence regressions remain present. Production
recovery and all successor/Atlas approvals remain disabled/unset.

Implementation references: the authenticated witness and admission helper are at
`tools/publication_evidence.py:206` and `tools/publication_evidence.py:209`;
`tools/publish_catalogue_evidence.py:245` calls the helper directly before PATCH.
`tests/test_publication_evidence.py:469` retains the exact +600-second case;
`:511` verifies provider-delay/current-pointer rejection.
`tools/prepare_evidence_workflow.py:20`, `:28` and `:52` hold stable templates and
both generators. `tests/test_evidence_workflows.py:61`, `:68`, `:90` and `:108`
cover successor guards, mutations, build and both CLI outputs;
`tests/workflow_cases.py:26` provides the historical and successor profiles.

## Validation and readiness

Evidence directory: `/private/tmp/atlas-catalogue2-remediation`.

| Executed validation | Result |
| --- | --- |
| Complete producer `pytest` suite, `connectors-full-final.xml` | **2,897 passed**, zero failed/errors/skipped |
| Original and added publication-evidence cases within that suite | **133 passed**; original 128 retained |
| Dedicated generated-workflow contracts, including twelve hostile mutations | **19 passed** |
| Historical/successor verifier-workflow and packaging cases | **21 + 13 passed** |
| Historical bootstrap and publication authorization cases | **115 + 131 passed** |
| Evidence driver, including gated recovery rejection | **12 passed** |
| Actionlint 1.7.12, seven active workflows and both generated candidates | Passed; shellcheck/pyflakes disabled |
| Both repository `git diff --check` checks and remediation-file whitespace scan | Passed |
| Frozen producer safeguards, branch/HEAD and approval-record audit | 27 exact hashes; unchanged HEADs; all approval records unset |

The focused counts above are subsets of the complete producer suite, not additional
unique tests. Its 180 warnings are existing Ansible Python deprecation warnings.
The companion Atlas report records the complete API/PostgreSQL, Docker, frontend
and browser regressions and the real request-budget measurement. Original and
fixed +600-second reproductions are retained in `h2-before.log` and `h2-after.log`;
the latter confirms no finalize/PATCH or current-pointer write.

Passing synthetic future tests cannot establish genuine successor signing,
platform isolation or publication timing.
Inactive PR review is the next permitted step; this report does not authorize it
to be created, committed or pushed by this remediation task. Hosted CI, owner
decisions, reviewed S/policy/identity pins and genuine acceptance remain mandatory
before Publisher activation. Live installation has separate Atlas/operator gates.

## Repository state

`git status --short` (includes all preserved pre-remediation development):

```text
 M catalogue/publication/README.md
 M catalogue/publication/consumer-handoff.md
 M tests/test_publication_authorization.py
 M tests/test_publication_bootstrap.py
 M tests/test_publication_packaging.py
 M tests/test_verifier_workflow.py
?? catalogue/candidate-v2/
?? catalogue/publication/durable-evidence.md
?? docs/catalogue2-completion-engineering-report.md
?? docs/catalogue2-phase1-engineering-report.md
?? docs/catalogue2-security-remediation-report.md
?? tests/fixtures/publication_evidence/
?? tests/test_catalogue_evidence_driver.py
?? tests/test_evidence_workflows.py
?? tests/test_publication_evidence.py
?? tests/workflow_cases.py
?? tools/build_catalogue_candidate.py
?? tools/catalogue_evidence_driver.py
?? tools/prepare_evidence_workflow.py
?? tools/publication_evidence.py
?? tools/publish_catalogue_evidence.py
?? tools/templates/
```
