# 0004 — Isolated signed publication transition verifier

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
identifies the reusable workflow as signer. The exact SAN/buildSigner URI is
required to be `https://github.com/benchristian88/atlas-connectors/.github/workflows/catalogue-verifier.yml@<PINNED_SHA>`;
buildSignerDigest is that SHA, while buildConfig URI/digest describe the original
`catalogue-publish.yml@refs/heads/main` caller and its source commit. These exact
certificate expectations have **not** been demonstrated by a genuine verifier
attestation. The checked-in trust template rejects issuance and verification until
a separately authorized live experiment confirms them. Never weaken constraints
to fit synthetic output. Unexpected platform behavior needs evidence and review.

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
exercise real cryptography; new positive signer-policy tests use synthetic
verified output only. No new genuine signer fixture, live token, workflow run,
publication or settings change is performed here. V2 integration and independent
genuine acceptance are required before declaring the publication pipeline ready.
