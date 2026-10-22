# Pinned reusable-workflow signer experiment (C != S)

This experiment gathers signing evidence and cannot publish a catalogue. Local
tests do not establish genuine C != S signer acceptance. A real GitHub-hosted run,
after these changes reach protected `main`, is required. The production
`live_signer_accepted` flag remains false; no trust pins or production validation
are changed by this experiment.

Genuine run [39846232008](https://github.com/benchristian88/atlas-connectors/actions/runs/39846232008)
previously succeeded with a local reusable call: caller and signer used the same
commit `e5287c3229f5b9a1dc4c3dbcda0f4193fe221c3c`. Its evidence prompted the separately scoped
[V1 identity correction](signed-publication-verifier.md#genuine-identity-evidence-and-corrected-representations).
The [original genuine probe and bundle](../tests/fixtures/verifier_signer_probe/README.md)
remain byte-for-byte unchanged and retain real offline verification, tampering,
subject-substitution and production-rejection regression coverage. That historical
same-commit verification is explicitly test-only; the current inspector has no
same-commit or historical-profile fallback. The previous successful run does not
prove the separate revision bindings below.

- **S** is the fixed reviewed signer revision
  `260d83d529f89d00646771f8e66f32efd34826a3`.
- **C** is the future protected-main merge commit containing these changes, as
  reported by the dispatched caller's `GITHUB_SHA` and independently checked
  against the run API's `head_sha`. Record its actual value from the fresh run;
  it is unknown during local implementation.
- **C must differ from S.** S is a literal pin in the workflow and inspector,
  never derived from C, the current branch, a tag, or latest main.

## Architecture and boundaries

The manual caller is
[verifier-signer-experiment.yml](../.github/workflows/verifier-signer-experiment.yml).
It has no inputs, runs only in `benchristian88/atlas-connectors` with the pinned
numeric repository/owner identities, and requires `refs/heads/main`,
`workflow_dispatch`, the exact caller workflow identity, and attempt one.

Its `sign` job calls
[verifier-signer-probe.yml](../.github/workflows/verifier-signer-probe.yml) using
the literal immutable reference:

```yaml
uses: benchristian88/atlas-connectors/.github/workflows/verifier-signer-probe.yml@260d83d529f89d00646771f8e66f32efd34826a3
```

The former local call resolved to C. The explicit reference selects S even when
main advances to C, without following later probe changes. The probe at S is
unchanged. Its caller restriction still requires the exact original
`verifier-signer-experiment.yml@refs/heads/main` path; a differently named caller
would not run. The probe repeats the caller restrictions and accepts no inputs or secrets.
It runs on GitHub-hosted Ubuntu 24.04 with only `id-token: write` and
`attestations: write`. It has no checkout, caller code execution, artifact
downloads, environment, App credentials, caches, or repository-content writes.

Only fixed inline Python creates the deterministic, bounded `probe.json`.
It includes public repository IDs, source commit, run and attempt, a fixed
`NOT a publication authorization` note, and four allowlisted job properties.
The optional job fields are recorded individually: `job.workflow_ref`,
`job.workflow_sha`, `job.workflow_repository`, and `job.workflow_file_path`.
A JSON round trip in each expression accommodates older actionlint context
schemas; only the selected property reaches an environment variable. A missing
property becomes JSON null, explicitly reported as NOT OBSERVABLE. No complete
job or GitHub context is exported.

The unchanged pinned `actions/attest` v4.2.1 signs the exact subject bytes with
the custom predicate
`https://atlas-impact.dev/attestations/verifier-signer-experiment/v1`.
Its predicate also binds the probe digest and says `not_authorization: true`.
Registry push and storage-record creation are explicitly disabled. Therefore
the artifact-metadata permission used for storage records is unnecessary here;
there is no `artifact-metadata: write` or `packages: write` permission. All
external actions are pinned to full commit SHAs.

The native attestation is a genuine public GitHub/Sigstore operation. Its
attestation/transparency records can persist beyond the one-day artifact
retention period. The signed subject contains only public experimental data.

The separate `inspect` job has only `contents: read` and `actions: read`, with
no OIDC signing permission. It checks out the caller's exact source SHA with
persisted Git credentials disabled, installs the hash-pinned vendored SDK
offline, and prepares the existing hash-pinned GitHub CLI 2.102.1. It downloads
only the probe artifact by its ID returned from the reusable job. The signer
never consumes the inspection job's code or artifacts.

[The inspector](../tools/verifier_signer_experiment.py) uses the unchanged
Sigstore trusted roots and the existing bounded subprocess runner. The CLI
receives no ambient tokens, configuration or proxies, and verifies the local
bundle offline with the exact repository and reusable-workflow path,
`--source-digest C`, `--signer-digest S`, main source ref, exact GitHub OIDC issuer,
hosted-runner and experiment predicate filters. These independent constraints are
also checked against the authenticated certificate fields after verification.
It checks the verified statement's exact subject name, digest and predicate.
There is no unverified DSSE decoding or synthetic-signature fallback.

Two further real CLI invocations must reject changed subject bytes and an
unrelated substitute subject. A timeout or policy/parser failure does not count
as cryptographic rejection. No acceptance artifact is exported unless positive
verification and both negative checks succeed.

The inspection job's ordinary scoped GitHub token is used only for two bounded
GETs against the same repository/run: the caller run and its attempt-one jobs
listing. Redirects and incomplete/paginated results fail closed. Only allowlisted
`referenced_workflows` fields and named step timings are retained; raw responses
and tokens are never exported. No App transport or credentials are involved.

## Run after merge

1. Review and merge these changes into protected `main`, preserving literal S in
   both the caller and inspector. The probe at S already exists and must remain
   unchanged. Record the merge commit C and confirm C != S. Do not run this
   feature branch as a substitute or update S to the new merge commit.
2. Open the repository's **Actions** tab and select **Reusable signer acceptance
   experiment** (`verifier-signer-experiment.yml`).
3. Select **Run workflow**, select branch **main**, then **Run workflow**. There
   are no inputs. This is a deliberate live signing experiment, with no release
   or publication action. The equivalent single dispatch command is:

   ```bash
   gh workflow run verifier-signer-experiment.yml --repo benchristian88/atlas-connectors --ref main
   ```
4. Inspect the fresh run's `sign / probe` and `inspect` jobs. Only attempt one
   is permitted. To gather another sample, dispatch a new run from main; do not
   use **Re-run jobs**.
5. Download both one-day artifacts from the run summary before they expire:
   `verifier-signer-probe-<run_id>` and
   `verifier-signer-evidence-<run_id>`. Preserve the public evidence with the
   security review if longer retention is needed.
6. Compare `evidence.json`'s `context.source_commit` with the run's actual commit
   C and the recorded merge commit, and `signer_revision` with fixed S. Require
   the genuine PASS conditions below; a green signing job alone is insufficient.

The probe artifact contains exactly `probe.json`, `probe.sigstore.json` and
`signer-timing.json`. The evidence artifact contains `evidence.json` and
`comparison.md`. No `authorization.json` is ever created. Failed cryptographic,
negative or API checks fail the inspection job without uploading acceptance
evidence; the already uploaded public probe remains available for diagnosis.
After successful cryptographic, negative and API checks, identity mismatches or
missing identity fields produce sanitized diagnostics with `experiment_result:
BLOCKED` and `identity_accepted: false`, then fail the inspection step. The upload
step runs after failure to preserve those diagnostics. If no report was produced,
its required-file upload also fails; it never fabricates evidence.
The experiment has not been dispatched as part of local implementation.

## Interpret evidence

`authenticated` contains only fields returned after genuine pinned-CLI
verification: certificate SAN, build signer/configuration URI and digest,
source repository URI/ref/digest, repository and owner IDs, issuer, runner,
trigger, run invocation URI, subject, predicate and verified transparency
timestamps. Missing certificate fields are listed explicitly. Invocation attempt
is encoded in `runInvocationURI`; compare it with `/attempts/1` and the
independently checked run metadata. Unrecognized certificate fields are dropped.

The four `workflow_reported_job_context` values are bound into the signed subject
but are workflow-reported diagnostics, not certificate extensions.
`caller_run_referenced_workflows` is an independent provider representation from
the ordinary job-token GET, not a signed certificate claim. Each entry retains
only `path`, `sha` and `ref`; missing fields remain null. A missing top-level
field is explicitly NOT OBSERVABLE; an empty array is an observed empty array,
not affirmative evidence of the reusable workflow identity.

The current comparison table replaces the historical inspector's V1-assumption
columns with explicit C/S binding, expectation, actual observation and **MATCH**,
**MISMATCH** or **NOT OBSERVABLE** columns. It includes:

| Evidence field | Required binding | Authority |
| --- | --- | --- |
| `sourceRepositoryDigest` | C | Authenticated certificate; CLI source pin |
| `buildConfigDigest` | C | Authenticated certificate |
| `buildConfigURI` | Exact caller workflow at `refs/heads/main` | Authenticated certificate |
| SAN / `buildSignerURI` | Exact probe workflow path, same URI in both fields | Authenticated certificate; CLI signer-workflow constraint |
| `buildSignerDigest` | Fixed S | Authenticated certificate; separate CLI signer pin |
| `job.workflow_ref` | Exact probe workflow path; full textual ref recorded | Signed workflow-reported subject |
| `job.workflow_sha` | Fixed S | Signed workflow-reported subject |
| `referenced_workflows.path` | Exactly one reference, probe workflow at literal `@S` | Independent run API; not signed |
| `referenced_workflows.sha` | Fixed S | Independent run API; not signed |
| `runInvocationURI` | Exact original run ID and `/attempts/1` | Authenticated certificate |
| Probe source/run/attempt | C and the original run/attempt | Exact signed subject, separately checked against caller context |

Signer URI and job-ref rows compare the exact workflow path before `@` and record
the nonempty textual ref without treating it as a revision pin. The previous
same-commit run used `@refs/heads/main`; the actual spelling for an explicit `@S`
call is **unknown until this run**. No suffix spelling is inferred from S, and no
alternative workflow path or signer digest is accepted. S must independently
match the certificate digest, job SHA and API reference. Source/caller refs remain
exactly main. The API's optional `referenced_workflows.ref` is retained verbatim
as a diagnostic, independently of the required path/SHA checks.

### Genuine PASS and failure conditions

A genuine PASS requires a fresh manual main run, attempt one, C != S, successful
pinned-CLI verification with independent C/S constraints, the exact experimental
subject and predicate, trusted verified transparency evidence, both real subject
rejection tests, complete bounded API reads, and **every comparison row MATCH**.
`experiment_result` must be `PASS` and `identity_accepted` must be true.
Missing certificate/job/reference identities, wrong or swapped C/S digests,
wrong workflow paths, non-main caller/source refs, a different invocation or
attempt, invalid signatures, absent transparency evidence or failed/inconclusive
negative checks prevent PASS. A cryptographically valid signature with incorrect
C/S bindings is **BLOCKED**, never successful identity acceptance.

Unknown/missing platform representations require review of actual evidence. Do
not change pins, invent fields or introduce a permissive fallback to pass the run.
`production_accepted` is always false, including on experimental PASS. No action
in either workflow changes production trust configuration.

### Implications for production V2

If genuine evidence establishes these independent bindings, a literal reusable
call at reviewed S can support future catalogue changes at newer C without
changing the accepted verifier implementation. Future verifier changes still
require explicit security review and signer-pin updates. A caller-local workflow
or later checkout of S cannot provide that separation.

This experiment is evidence for that design, not a V2 integration or production
signer acceptance. The exact production signer, its own textual URI profile,
credential isolation, trust/environment pins and remaining authorization gates
need separate genuine acceptance and review. Unexpected platform bindings block
the design's acceptance until understood; the production profile is unchanged.

## Timing and the 60-second prototype budget

Subject creation, attestation generation and independent cryptographic
verification use monotonic elapsed times on their respective runners. Signer
timing is unsigned diagnostic data. The signing interval includes the action's
startup and bundle-preservation overhead. Provider step timestamps separately
show subject creation, signing, probe upload, download and verifier/dependency
preparation at one-second resolution. Missing steps are explicitly listed.

The provider job gap measures scheduling between signer completion and inspector
start. The total from subject creation to positive verification completion uses
cross-host UTC clocks; it includes signer upload, job scheduling, inspector setup,
installation and download. It excludes later negative tests, API inspection and
evidence upload. Clock skew is a limitation; these intervals must not be added
as though they were disjoint. Upload/download durations include their action
overhead, and setup/queue/transfer time is not cryptographic verification time.

The report compares this single positive-path sample with 60 seconds. Exceeding
60 seconds is evidence of an operational problem for an analogous grant flow.
A sample below 60 seconds does not establish a safe budget: future production
authorization evidence observation, additional integration work and variance
remain unmeasured. This probe performs **no authorization evidence observation**.
Gather multiple fresh runs and review scheduling, transfer, setup and observation
costs before V2 integration. Do not automatically increase the freshness budget.

## Local validation and remaining acceptance gates

[Focused tests](../tests/test_verifier_signer_experiment.py) exercise workflow
boundaries, the actual inline subject generator, sanitized output, exact CLI
constraints and fail-closed behavior. Synthetic verified-output policy tests are
explicitly synthetic. Real local pinned-CLI negative tests reject unsigned data
and an existing genuine attestation from another workflow. Existing genuine
P1/P2 and genuine same-commit probe fixtures remain unchanged. The historical
probe test still performs genuine positive and tampering/substitution verification
with its explicit archived C = S profile; the new C != S verifier rejects that
old signer revision. Neither synthetic C/S tests nor that historical positive
prove C != S acceptance or explicit pinned-call GitHub permission/context behavior.

The post-merge run must demonstrate successful OIDC issuance, native attestation
creation with these minimal permissions, artifact transport and independent
verification. Actual job-context availability, certificate fields and API
`referenced_workflows` shape are platform observations, not guaranteed by tests.
Failure requires investigation; never add credentials, broader publication
permissions, unverified claim acceptance or production policy changes to make
the experiment pass.

Production acceptance remains disabled. The experiment cannot issue a grant:
its subject, predicate, workflows and payload schema differ from production,
and it has no publication credentials, environment or contents-write permission.
P1 immutable publication, P2 bootstrap/history/current-pointer verification,
normal publication/recovery and legacy Proxmox restrictions are untouched.
V2 integration, genuine acceptance of the exact production reusable-workflow
revision, complete ruleset/authority evidence and the unresolved
`draft_visibility_unproven` gate remain separate work. Draft creation remains
unconditionally blocked. Neither workflow calls the publisher or production
verifier workflow.

## Platform references

- [GitHub reusable-workflow references and same-commit local resolution](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows).
- [GitHub job context, including workflow identity properties](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts).
- [GitHub token permissions and artifact-metadata storage records](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).
- [Pinned attest action inputs and storage-record prerequisites](https://github.com/actions/attest/blob/508db95dd578ae2727ebd6217d5ba78e4fbda05d/action.yml).
- [GitHub CLI attestation verification](https://cli.github.com/manual/gh_attestation_verify).
