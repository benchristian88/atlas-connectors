# 0004 — Isolated signed publication transition verifier

Superseded for authorization granularity by [ADR 0005](0005-lean-run-preflight.md). The V1 status and decision below are historical; P1/P2 integrity and credential-isolation principles remain in force.

Status: **V1 foundation implemented; production acceptance BLOCKED; V2 not integrated**

Date: 2026-10-23

Amends the ruleset-observation assumption in [ADR 0001](0001-github-catalogue-publication.md)
and [ADR 0002](0002-single-maintainer-publication.md). Their historical text is retained.
The immutable catalogue, selection signer, single-maintainer model and
[ADR 0003 bootstrap fence](0003-sequence-one-bootstrap.md) remain in force.

## Context and correction

Administration Read does **not** establish complete ruleset evidence. GitHub's
[ruleset API](https://docs.github.com/en/rest/repos/rules#get-a-repository-ruleset)
conditions visibility of `bypass_actors` on write access. The separately performed
visibility experiment, reported by the owner, established that the verifier App
can retrieve explicit arrays with Administration Write. Local tests do not
independently reproduce that experiment or prove current live settings.

The existing publisher must continue to reject absent `bypass_actors`; omission
must never mean an empty bypass list. Do not expand Publisher App permissions or
introduce a temporary incomplete-evidence exception.

## Decision

Introduce `catalogue-verifier.yml` as a SHA-pinned reusable workflow running a
single isolated GitHub-hosted job. Its only input is bounded canonical transition
request data. It checks out its own accepted implementation revision, installs
only the hash-pinned vendored SDK without dependencies/network, independently
reads policy/run/attempt/actor/workflow/CI/protections/provider state, and observes
all five pinned ruleset IDs including explicit bypass arrays. It calls the existing
`check_rulesets` protection checks with the bootstrap lock required for every
operation. No second protection policy is introduced.

The `catalogue-verification` environment supplies the Verifier App key and IDs.
App **5424851**, installation **174088125**, must have exactly Administration Write,
Contents Read, Actions Read, Checks Read and Metadata Read. Its minted token is
restricted to repository **1414494920**, owner **93822871**, and those permissions.
JWT-authenticated App/installation reads and an installation-token-authenticated
repository listing independently bind the credential. No verifier bypass actor is
permitted in any of the five rulesets.

The privileged transport has only GET evidence operations and the single fixed
installation-token mint POST. It has no ref/release/settings mutation interface,
redirects, proxies or retries. Native attestation registration subsequently uses
the separate job `GITHUB_TOKEN`, not the App token. This is intentionally distinct
from the rule that repository evidence fetches use GET only.

Publisher App **5422372**, installation **174027755**, keeps its existing permissions
and narrow publication bypass. V1 does not modify its workflow or publication
policy, and does not consume new authorizations in existing publication commands.
GitHub itself does not enforce these signed grants on API writes. They are gates
in trusted publisher code, not provider-issued reduced-capability credentials.
A stolen Publisher credential still has its configured write/bypass capabilities;
consumers must independently reject unauthenticated or inconsistent publication.

## Isolation and its limits

[Reusable workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations)
are called as jobs, providing a separate runner filesystem/process boundary.
Environment secrets are used in the called job; an environment alone does not
create that boundary. The key is injected into one issuer step only, removed from
the process environment before OpenSSL, and temporarily stored in a mode-0600
file during JWT signing. Token/JWT stay within that process. Only authorization
bytes and a verified bundle are exported. No caller checkout, artifact download,
connector execution, caller commands, cache or credential outputs exist.

Administration Write remains a powerful credential: compromise can alter repository
rulesets, even though this client never calls a mutation endpoint. Same-repository
main-workflow or administrator compromise can expose environment secrets in a
different job. GitHub environments do not provide a workflow-file secret ACL.
The independent exact reusable signer identity prevents another workflow from
passing verification, but cannot make a leaked Administration Write key harmless.
Review/protect main, minimize trusted code, use ephemeral hosted runners, protect
environment administration and retain one-maintainer account security. A stronger
administrative boundary would need a separately reviewed architecture change.

## Authorization and signer trust

`atlas-publication-authorization/v1` is separate from both existing catalogue and
pointer schemas. Exact discriminated targets bind a single transition, random
challenge, original run/attempt, operation, policy-byte digest, source revision,
prior channel/pointer and known release/asset identities. Before draft creation
there are deliberately no release/asset IDs. Bundle-upload variants must name the
IDs assigned to preceding assets. Complete ruleset observations and their digest,
approved bypass actors and all authority numeric IDs are signed.

The custom predicate is
`https://atlas-impact.dev/attestations/publication-authorization/v1`.
The sole subject is the SHA-256 of exact canonical UTF-8 `authorization.json` bytes.
The predicate independently repeats that digest. Catalogue/package/selection
signers cannot authenticate this profile.

Use the existing hash-pinned offline **gh 2.102.1**, roots, bounded subprocess and
bundle limits. Require the exact reusable workflow path and implementation SHA,
OIDC issuer, numeric source repository/owner IDs, hosted runner, caller workflow,
source commit/ref, dispatch trigger, invocation run/attempt, subject digest,
predicate and verified transparency evidence. `--signer-workflow` and
`--cert-identity` are mutually exclusive in the
[pinned CLI implementation](https://github.com/cli/cli/blob/v2.102.1/pkg/cmd/attestation/verify/verify.go).
Use the former plus independent signer/source digests; check the exact certificate
SAN in verified output. No DSSE decoding is accepted as cryptographic verification.

[GitHub's guidance](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/increase-security-rating)
identifies the reusable workflow as signer. The original V1 assumption that the
certificate signer URI and `job.workflow_ref` end in `@<PINNED_SHA>` is corrected
by the genuine evidence below. This is a representation correction; exact
implementation pinning and the production acceptance block remain in force.

### Evidence correction — 2026-10-23

Successful public experiment
[run 39846232008, attempt 1](https://github.com/benchristian88/atlas-connectors/actions/runs/39846232008)
used source `e5287c3229f5b9a1dc4c3dbcda0f4193fe221c3c` and a same-commit local
reusable call. Its exact public [probe and bundle](../../tests/fixtures/verifier_signer_probe/README.md)
were independently reverified offline with unchanged pinned gh/roots. The run API
was separately read; its representation must not be confused with job context.

| Identity surface | Observed experimental representation | Corrected V1 requirement |
| --- | --- | --- |
| Certificate SAN / buildSignerURI | `verifier-signer-probe.yml@refs/heads/main` | Exact `https://github.com/benchristian88/atlas-connectors/.github/workflows/catalogue-verifier.yml@refs/heads/main` |
| Certificate buildSignerDigest | Exact experiment source SHA | Independently trusted `signer_revision`, also enforced by `--signer-digest` |
| Reusable job workflow_ref / workflow_sha | Probe workflow at `@refs/heads/main` / exact source SHA | Exact production workflow at `@refs/heads/main` / independently trusted signer SHA; reject before checkout or credential injection |
| Caller API referenced_workflows.path / sha | Probe workflow at `@<source SHA>` / exact source SHA | Exact production workflow at `@<trusted signer SHA>` / that same SHA; unchanged |

The observed buildConfig URI identifies the experimental **caller** workflow at
`refs/heads/main`; its digest is the caller source commit. V1 continues requiring
`catalogue-publish.yml@refs/heads/main` and that original caller commit, independently
of the verifier revision. Repository/owner IDs, issuer, source/ref, hosted runner,
trigger, invocation/attempt, production subject/predicate and transparency checks
are retained. Arbitrary branches, workflow paths, old SHA-suffixed certificate
URIs and wrong signer digests are rejected; there is no alternate-ref fallback.

This genuine probe is not a genuine production authorization. Its workflow,
predicate and subject remain distinct, and production verification rejects it.
`live_signer_accepted` remains false and all signer/ruleset/environment pins remain
unset. Synthetic production-profile tests establish policy behavior only.

### Verifier revision lifecycle — V2 design requirement

[GitHub documents](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows#calling-a-reusable-workflow)
that a local `uses: ./.github/workflows/catalogue-verifier.yml` resolves to the
caller's commit. If accepted signer revision S is fixed and main advances to C,
that call executes workflow C and reports workflow_sha/buildSignerDigest C. The
unchanged exact S pin must reject it, even when the verifier files were untouched.
Checking out S later does not pin the workflow steps already selected at C.

V2 must decouple catalogue source C from independently reviewed verifier code S.
The intended approach remains a literal
`benchristian88/atlas-connectors/.github/workflows/catalogue-verifier.yml@<reviewed 40-character SHA>`
job call, with S separately pinned in consumer trust and the verifier environment;
ordinary catalogue changes may advance C without approving S again. New verifier
code requires an explicit security-reviewed pin update, never automatic trust in
current main. Caller identity/buildConfig/source stay bound to C; signer digest,
job SHA, verifier checkout and API reference stay bound to S.

The local-call experiment used C = S. It does **not** establish certificate/job
URI spelling or separate source/signer claims for an explicit `@S` call with
C different from S. A separate harmless, credential-free pinned-call experiment
must demonstrate these before V2 integration. If an explicit call produces
SHA-suffixed certificate/job URIs, today's exact main-ref profile must fail;
any specific profile correction needs that evidence and separate security review.
Do not preemptively accept both forms, remove digest constraints, change this
correction's pins or modify the publisher to work around the lifecycle gate.

## Freshness, replay, races and recovery

Whole UTC Unix seconds record observation start/completion, issuance and expiry.
Expiry is at most 60 seconds after the **earliest** observation, including App
authentication. The configurable value may only narrow that bound. Expiry/future
checks run before and after offline verification. Sixty seconds is an unmeasured
prototype budget; signing, log inclusion, artifact transfer, job scheduling and
verification may exhaust it. Expired decisions require fresh observations.

`AuthorizationVerifier.verify_and_consume` rejects duplicate challenges only within
one single-threaded in-memory verifier object. This is not durable consumption,
not cross-job enforcement, and not global exactly once. V2 must establish each
challenge and expected state independently, consume it immediately before one
specific provider mutation and never replay ambiguous writes. Existing provider
constraints supply create-only asset/ref behavior, immutable releases,
single-parent non-force updates and the protected bootstrap consumption fence.

GitHub offers no transaction spanning ruleset observation and publication writes.
Protection or provider state can change after observation, even with a signature.
V2 must re-read exact state, recheck freshness immediately before mutation, verify
read-back and stop on ambiguity. Signatures do not attest continuous protection,
operator independence, currentness after withholding, or package eligibility.
Missing evidence, changed state, stale grants, interrupted marker creation or
unavailable verification stop progress; there is no repair-by-bypass path.

## Acceptance boundary

The [V1 foundation and V2 handoff](../signed-publication-verifier.md) specify the
schemas, actual checks, production blockers and separate stage/seal/activate/
finish/recover job requirements. Existing genuine catalogue/package fixtures
exercise real cryptography. The preserved genuine experimental probe verifies
only its separate experimental profile and is rejected as production authorization;
positive production signer-policy tests still use synthetic verified output only.
This correction reads an existing run; it creates no live token, workflow run,
publication or settings change. V2 integration and independent genuine acceptance
of the exact production signer remain required before publication readiness.
