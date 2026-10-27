# Phase 4B.2 — Genuine Sigstore certificate correction

Date: 28 October 2026 (Pacific/Auckland). Local engineering; publication disabled.

## A. Result

**PARTIAL evidence reconstruction; local correction passes validation.** The
original signed bundle was independently authenticated, and the genuine certificate
proves S2's exact-main signer identity expectation is incorrect. Original subject
bytes and hosted gh output were not exported, so the original CLI command cannot
be replayed or its exit status established independently. No genuine acceptance
is claimed. A future successful original hosted run and independent signed-evidence
authentication remain required.

## B. Git baseline and branch

Repository `benchristian88/atlas-connectors`; base `main` and HEAD
`c7299f9375ccf401c0cf69cb9022dc76a3556b48` (PR #40). The requested new branch
`fix/connector-sigstore-signer-identity` was already checked out clean at that
baseline. Its reflog records creation from main. Read-only GitHub main metadata
independently confirmed the same SHA. No branch/history rewrite occurred.

## C. Genuine evidence and independent authentication

Original [run 40534608937](https://github.com/benchristian88/atlas-connectors/actions/runs/40534608937),
attempt 1, caller C `c7299f9375ccf401c0cf69cb9022dc76a3556b48`, reused signer S2
`c2b4ecb493160f0226b1724aa688d0f436d51489`.
[Job 122296352579](https://github.com/benchristian88/atlas-connectors/actions/runs/40534608937/job/122296352579)
completed the guard, security observations and signing. Step 8, local profile
authentication, failed with `connector_preflight_failed`; artifact upload was
skipped. Publisher job `122296584523` was skipped. The run's artifact list is empty.

The original [attestation 60446602](https://github.com/benchristian88/atlas-connectors/attestations/60446602)
was obtained by anonymous GET using its signed subject digest:

```text
GET https://api.github.com/repos/benchristian88/atlas-connectors/attestations/sha256:adb72b7a03f72b004bb3d60d22ca8cb98517888687b4a6d501c8c6adfefc230c
```

Its bundle certificate equals the PEM printed by the successful signing step,
byte for byte in DER. The API storage path identifies attestation `60446602`.
The fixture API response removes only the temporary storage URL's query; no
temporary access signature is retained in the repository. The original signed
bundle, PEM, job log, run/job summaries and empty artifact list are preserved in
[the evidence directory](../tests/fixtures/connector_sigstore_s2/README.md).

OpenSSL independently decoded the certificate. An isolated temporary environment
with official `sigstore==4.3.0` authenticated the original DSSE envelope with
`Verifier.verify_dsse`, exact SHA-based `policy.Identity`, GitHub OIDC issuer and
the public-good root from the repository's frozen `trusted-root.jsonl`. Root-file
SHA-256 is `3c2cc7f357dc064ec527fdcd78da6e9245c21a381e1abaa0f2b62b186bcac1a1`.
This verified the certificate/signature, SCT and Rekor evidence and authenticated
the statement. It did not authenticate the unavailable preflight contents or
constitute pinned-gh admission. No repository dependency or production verifier
was replaced. The temporary script and authenticated statement are retained under
`/private/tmp/atlas-sigstore-correction-*`.

| Authenticated certificate/statement claim | Value |
| --- | --- |
| SAN and build signer URI | `https://github.com/benchristian88/atlas-connectors/.github/workflows/connector-verifier.yml@c2b4ecb493160f0226b1724aa688d0f436d51489` |
| Signer digest | Exact S2 above |
| Caller source and build configuration digest | Exact C above |
| Source ref | `refs/heads/main` |
| Build configuration URI | `https://github.com/benchristian88/atlas-connectors/.github/workflows/connector-publish.yml@refs/heads/main` |
| Repository / owner IDs | `1414494920` / `93822871`, official URIs |
| OIDC issuer / runner / visibility | `https://token.actions.githubusercontent.com` / `github-hosted` / `public` |
| Trigger / invocation | `workflow_dispatch` / `https://github.com/benchristian88/atlas-connectors/actions/runs/40534608937/attempts/1` |
| Certificate validity | 27 October 2026, 15:48:37–15:58:37 UTC |
| Sole subject | `connector-preflight.json`, SHA-256 `adb72b7a03f72b004bb3d60d22ca8cb98517888687b4a6d501c8c6adfefc230c` |
| Predicate | `https://atlas-impact.dev/attestations/connector-package-preflight/v1`, schema `atlas-connector-package-preflight-predicate/v1`, same subject digest |
| Rekor | `dsse/0.0.1`, log index `3520629471`, integrated time `1793116118` |

## D. Root cause, CLI distinction and remaining unverified fields

S2's Python profile requires SAN `connector-verifier.yml@refs/heads/main` and
requires `buildSignerURI` equal that SAN. Both genuine fields contain `@S2`.
An isolated load of the unchanged baseline module, given the genuine decoded
certificate in explicitly modeled CLI output, reproduces `authorization_certificate`.
The corrected module accepts those same certificate claims. All other currently
required certificate fields match; no additional checked-claim mismatch was found.

The pinned gh command remains exactly:

```text
./tools/publication_trust/bin/gh attestation verify connector-preflight.json --bundle connector-preflight.sigstore.json --custom-trusted-root tools/publication_trust/trusted-root.jsonl --repo benchristian88/atlas-connectors --hostname github.com --signer-workflow benchristian88/atlas-connectors/.github/workflows/connector-verifier.yml --signer-digest c2b4ecb493160f0226b1724aa688d0f436d51489 --source-digest c7299f9375ccf401c0cf69cb9022dc76a3556b48 --source-ref refs/heads/main --cert-oidc-issuer https://token.actions.githubusercontent.com --deny-self-hosted-runners --predicate-type https://atlas-impact.dev/attestations/connector-package-preflight/v1 --digest-alg sha256 --format json
```

Paths above name preserved inputs; the hosted helper uses equivalent temporary
paths. gh is version 2.102.1 with hash-pinned executable and frozen roots. The
command's signer path/digest and caller constraints are compatible with the genuine
certificate; it does not demand a main-based signer SAN. This supports the
post-CLI profile mismatch as the cause, but is not a claim that the hosted CLI
exit status was observed. `bounded_run` discards stderr and the preflight entrypoint
collapses exceptions to one safe error. No CLI stdout/exit status or original
preflight file survives in this run's artifacts. **A separate CLI failure cannot
be excluded from these logs.** Neither reconstructed JSON nor a supplied digest
is substituted for original subject bytes in production verification.

Additional certificate extensions are present but are not explicitly pinned by
this application profile: workflow environment name (OID `1.3.6.1.4.1.57264.1.23`)
is `catalogue-verification`; workflow identity subject (OID `.24`) is
`repo:benchristian88@93822871/atlas-connectors@1414494920:environment:catalogue-verification`.
The legacy workflow display name and duplicate legacy claims (OIDs `.2`–`.6`)
are not independently compared; modern trigger/source/repository/ref claims are
strictly checked. Signature authentication covers these certificate extensions,
but no new application policy for them is introduced here. Environment controls
remain separately enforced by the existing signed-preflight contract; their
original complete observation bytes cannot be independently checked without the
missing preflight file. Historical privileged settings and continuous isolation
are not inferred from the certificate. These are explicit verification limits,
not newly accepted alternate identities.

## E. Narrow correction and material files

`tools/connector_publication_sigstore.py` now forms the complete signer identity
from official repository, exact workflow path and `trust["signer_revision"]`,
then independently requires both SAN and `buildSignerURI` equal it. No command,
issuer, caller/main identity, predicate, trust pin or workflow changes.

`tests/test_connector_publication.py` updates only the modeled signer identities
and clarifies the prospective job fixture's age. `tests/test_connector_sigstore.py`
adds genuine-PEM policy regressions and preserved-evidence consistency checks.
These tests explicitly distinguish decoded certificate policy models from real
cryptographic admission. New fixture files retain the original public evidence.
`README.md`, the package runbook and this report describe current reality and the
separate S3 lifecycle. Existing historical qualification reports/ADRs are unchanged.
No database migration, API, UI, tenancy or package format change.

## F. Security controls retained

Exact repository/owner IDs and URIs, path, independent signer digest, caller
source/ref, configuration URI/digest, issuer, runner, visibility, trigger,
invocation, subject/predicate and bounded transparency requirements remain.
No suffix matching, branch acceptance or fallback. The offline bounded subprocess
still excludes ambient tokens/configuration/proxies. Existing guards, credential
isolation, fresh signed observations, original-attempt/main/human checks,
acceptance-only Publisher exclusion and negative security tests remain intact.
All four production S2 bindings and both false trust flags are unchanged. Live
trust variables/settings were neither read with credentials nor changed.

## G. Executed regression and complete validation

Local Python is 3.14.7; required Python 3.12 hosted CI remains a human PR gate.
Commands run from the repository; logs use `/private/tmp/atlas-sigstore-correction-*`.

| Command | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q tests/test_connector_sigstore.py` | 96 passed; wrong/missing values for every required certificate field, wrong SHA/path/branch identities individually and together, independent trust revision, exact CLI flags, statement/predicate/transparency constraints |
| `.venv/bin/python -m pytest -q tests/test_connector_publication.py tests/test_connector_sigstore.py` | 458 passed; all 362 existing Connector publication cases retained |
| `.venv/bin/python -m pytest -q tests/test_publication*.py tests/test_authorization_sigstore.py tests/test_connector_release.py tests/test_ruleset_visibility.py tests/test_verification_github.py tests/test_verifier_signer_experiment.py tests/test_verifier_workflow.py tests/test_historical_workflows.py` | 1,373 passed, including genuine historical offline signature tests |
| `ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-phase4b2-s2-review/test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q` | 2,338 passed, zero failures/skips, 65.72 seconds; 180 existing `ansible_runner` Python 3.14 deprecation warnings |
| `/private/tmp/atlas-phase4b2-tools/actionlint -shellcheck= -pyflakes= .github/workflows/*.yml` | Passed all seven active workflows; actionlint 1.7.12; optional shellcheck/pyflakes disabled |
| `.venv/bin/python -m compileall -q tools tests` | Passed |
| `.venv/bin/python -m pytest -q tests/test_documentation.py` | 1 passed |
| `.venv/bin/python -m pip check` | Passed; no broken requirements |
| `git diff --check` | Passed |
| Evidence README archival-authentication Python example, executed verbatim with isolated Sigstore interpreter | Passed; authenticated original statement; separate temporary verifier also rejected main, wrong SHA and wrong path identities |

An initial full run passed 2,337 tests and failed one documentation-link check
while the new report target was still being created. Completing the report fixed
that check; the documentation regression passed and the entire suite was rerun.

## H. Historical and package preservation

Original S/S2 Git objects and historical failed-S context remain unchanged. Prior
signed fixtures/reports, catalogue S4 bindings, policies, sequence-one history,
SDK wheel/locks, discovery source, release workflow and all four S2 production
bindings remain byte-identical to the baseline. Only the prospective correction
is edited in this uncommitted branch; it is not described as rewriting S2.
The preservation inventory compared all 154 baseline tracked files: exactly the
four files identified in E changed; 150 remain byte-identical. The independent
trust flags/pins, historical failed-S context and original S/S2 commit objects
were explicitly checked. Evidence is in
`/private/tmp/atlas-sigstore-correction-preservation.json`.

Executed rebuilds using `.venv/bin/python tools/build_bundle.py` preserve:

| Arguments (output paths under `/private/tmp/atlas-sigstore-correction-build-*`) | Archive SHA-256 |
| --- | --- |
| `--version 0.2.1 --output /private/tmp/atlas-sigstore-correction-build-021` | `96eaa736c2919e56e09b9613dddd8648ad1f43b77679899ab706261b2a38e509` |
| `--output /private/tmp/atlas-sigstore-correction-build-historical` | `a14fec5ab485c980688ff5907e8835ddd3e9cecd1a6989ef252cbcb1b1dc4ef8` |
| `--candidate --output /private/tmp/atlas-sigstore-correction-build-candidate` | `dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97` |

These are local unattested byte-preservation results, not publication authority.

## I. Git status and remote activity

Changes remain local, uncommitted and unpushed at the baseline SHA. GitHub activity
was GET-only run/job/log/artifact/main and official CLI source inspection, plus
anonymous public attestation download. An isolated temporary Sigstore package was
installed for archival authentication. No credential access/mint, dispatch/rerun,
publication, commit, push, PR creation, merge, tag, setting or trust change occurred.
Final `git status --short`:

```text
 M README.md
 M catalogue/publication/connector-packages.md
 M tests/test_connector_publication.py
 M tools/connector_publication_sigstore.py
?? docs/phase-4b2-sigstore-qualification.md
?? tests/fixtures/connector_sigstore_s2/
?? tests/test_connector_sigstore.py
```

## J. Human PR handoff and S3 repinning

1. Human reviews/commits/pushes this corrective branch, opens a PR against main,
   completes security review and required Python 3.12 CI, then merges. Record its
   exact immutable merge SHA as **S3**; do not use the branch/PR head or caller C.
2. A separate reviewed PR updates all four bindings together: reusable workflow
   `uses`, Publisher checkout `ref`, `ATLAS_IMPLEMENTATION_REVISION`, and package
   trust `signer_revision`. Update binding tests/allowlist to S3. Both trust flags
   stay false. Do not repin inside this corrective PR.
3. After that PR passes CI/review and merges, the owner independently configures
   the complete repository `CONNECTOR_VERIFICATION_POLICY` to its reviewed S3
   trust. Environment copies must be absent or identical; effective publication
   gate stays absent/false. No live settings are changed by this work.
4. Under separate owner authorization, run a new original acceptance-only hosted
   run, attempt 1, with Publisher skipped. Preserve original subject, signed bundle,
   approved request, C/S3/policy/trust and isolation evidence; independently run
   pinned-gh verification and the exact S3 profile/contract checks.
5. Claim genuine acceptance only after that future original run succeeds and its
   signed evidence is independently authenticated. Any further mismatch requires
   another immutable corrective review. Activation/publication remain separate.
