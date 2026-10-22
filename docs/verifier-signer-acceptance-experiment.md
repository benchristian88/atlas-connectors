# Reusable-workflow signer acceptance experiment

This experiment gathers signing evidence and cannot publish a catalogue. Local
tests do not establish genuine signer acceptance. A real GitHub-hosted run, after both
experimental workflows reach protected `main`, is required. The production
`live_signer_accepted` flag remains false; no trust pins or production validation
are changed by this experiment.

Genuine run [39846232008](https://github.com/benchristian88/atlas-connectors/actions/runs/39846232008)
has since succeeded. Its evidence prompted the separately scoped
[V1 identity correction](signed-publication-verifier.md#genuine-identity-evidence-and-corrected-representations).
The experiment inspector and its comparison table retain the original V1 SHA-ref
assumption as the recorded baseline; they no longer describe the corrected
production URI checks. No experiment code or workflow is changed by that correction.
The preserved probe remains distinct from production authorization evidence.

## Architecture and boundaries

The manual caller is
[verifier-signer-experiment.yml](../.github/workflows/verifier-signer-experiment.yml).
It has no inputs, runs only in `benchristian88/atlas-connectors` with the pinned
numeric repository/owner identities, and requires `refs/heads/main`,
`workflow_dispatch`, the exact caller workflow identity, and attempt one.

Its `sign` job calls
[verifier-signer-probe.yml](../.github/workflows/verifier-signer-probe.yml) using
`./.github/workflows/verifier-signer-probe.yml`. GitHub documents that this local
reference resolves to the caller's **same commit**. This pins implementation
bytes without presuming that the certificate's textual ref is an `@SHA` ref.
The probe repeats the caller restrictions and accepts no inputs or secrets.
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
bundle offline with repository, reusable-workflow path, exact signer/source
commit, main ref, OIDC issuer, hosted-runner and experiment predicate filters.
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

1. Merge the reviewed PR containing both workflows and the inspector into
   protected `main`. Do not run this feature branch as a substitute.
2. Open the repository's **Actions** tab and select **Reusable signer acceptance
   experiment** (`verifier-signer-experiment.yml`).
3. Select **Run workflow**, select branch **main**, then **Run workflow**. There
   are no inputs. This is a deliberate live signing experiment, with no release
   or publication action.
4. Inspect the fresh run's `sign / probe` and `inspect` jobs. Only attempt one
   is permitted. To gather another sample, dispatch a new run from main; do not
   use **Re-run jobs**.
5. Download both one-day artifacts from the run summary before they expire:
   `verifier-signer-probe-<run_id>` and
   `verifier-signer-evidence-<run_id>`. Preserve the public evidence with the
   security review if longer retention is needed.

The probe artifact contains exactly `probe.json`, `probe.sigstore.json` and
`signer-timing.json`. The evidence artifact contains `evidence.json` and
`comparison.md`. No `authorization.json` is ever created. Failed cryptographic,
negative or API checks fail the inspection job without uploading acceptance
evidence; the already uploaded public probe remains available for diagnosis.
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

The comparison table transcribes the pre-correction V1 expectations in
[AuthorizationSigstore.verify()](../tools/authorization_sigstore.py). Each row
contains the V1 expectation, actual observation, and MATCH, MISMATCH or
NOT OBSERVABLE. V1's unset signer revision is displayed as
`<PINNED_VERIFIER_SHA>` and cannot match a production pin that does not yet exist.
Different experimental workflow names, subject and predicate are intentional.

Additional probe-role columns map the two workflow names to their experimental
equivalents while retaining V1's **SHA-ref signer identity** assumption. These
columns expose meaningful identity differences that literal path differences
could otherwise hide. In particular, compare SAN/buildSignerURI textual refs,
the independently pinned buildSignerDigest, caller versus callee buildConfigURI,
buildConfigDigest, source commit/ref, run/attempt and numeric IDs. A mismatching
or unobservable identity must be investigated using the preserved verified
evidence. Do not silently relax V1 checks. Any correction requires a separate
security-reviewed change and genuine evidence for the exact production signer
configuration; this local-reference experiment is not that production run.

Comparison mismatches do not suppress otherwise valid experimental evidence.
`production_accepted` is always false, even if every applicable probe-role row
matches. No action in either workflow changes production trust configuration.

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
P1/P2 fixtures remain unchanged. Neither kind of local test proves a positive
reusable-workflow signature or GitHub permission/context behavior.

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
