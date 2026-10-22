# P1 publication contract and P2 bootstrap runbook

Status: **local foundations implemented; publication disabled; no live acceptance**.
The [investigation](investigation.md) records pre-change evidence, the
[storage ADR](../../docs/decisions/0001-github-catalogue-publication.md) and
[single-maintainer ADR](../../docs/decisions/0002-single-maintainer-publication.md)
record the proposed decisions, and the [consumer handoff](consumer-handoff.md) defines required Atlas work.
No release, branch, tag, repository setting or remote asset was changed here.
P2 adds a separate [two-dispatch bootstrap procedure](bootstrap.md),
[ADR 0003](../../docs/decisions/0003-sequence-one-bootstrap.md) and
[implementation record](bootstrap-report.md); it has not performed the migration.

The [V1 signed verifier foundation](../../docs/signed-publication-verifier.md) and
[ADR 0004](../../docs/decisions/0004-isolated-signed-publication-verifier.md) correct
the Administration Read ruleset-visibility assumption. The current checked-in
policy enables bootstrap staging, but incomplete bypass evidence still fails
closed. The isolated verifier has no live signer acceptance and is not integrated
with publication; V2 and genuine acceptance remain required.

## Distribution and trust boundaries

1. A qualified package has a canonical SDK Manifest, reviewed source and independent
   `release.yml` build provenance. Its immutable release's actual asset ID/digest
   must match the registry. The publisher also requires a first-attempt App-triggered
   `connector-release` build, matching source commit and ancestry in protected main.
   The later maintainer dispatch authorizes package inclusion.
2. A catalogue candidate is built from the reviewed registry by `catalogue.yml`.
   Preparation has read-only contents permissions and signs original bytes. It
   has no publication authority, and an environment name is not used as proof.
3. `catalogue-publish.yml` authenticates the candidate, history, packages and
   publication authority before staging. It signs an exact selection descriptor
   separately. It verifies every staged file, finalises the snapshot, verifies
   `immutable: true`, exact IDs, tag/source and published bytes, and only then
   updates the current branch. An invalid or mutable release never becomes current.

Normal consumers need no GitHub credential. They download public assets and
bundles, verify with their pinned offline verifier, and read public identity/run/ref
metadata. Publishers use a short-lived installation token. No token enters a
pointer, receipt, attestation, package, log or ordinary consumer configuration.

## Exact pointer and endpoint

Canonical API identity:
`https://api.github.com/repos/benchristian88/atlas-connectors/git/ref/heads/catalogue-current`.
It is a **transport ref**, not signed pointer data. Resolve its 40-character commit
SHA and read `/contents/current.json?ref=SHA` and
`/contents/current.sigstore.json?ref=SHA` in that same repository. Never resolve
those files independently against a moving branch. Never use a response-provided
external URL as a publication or package destination.

`current.json` has **exactly seven fields**:

```json
{
  "asset_id": 123457,
  "previous_pointer_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "release_id": 123456,
  "release_tag": "catalogue-000002",
  "schema_version": "1.0",
  "sequence": 2,
  "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
}
```

Numbers above are examples, not published identities. IDs/sequence are literal
positive integers at most 9007199254740991; booleans, floats and strings fail.
Digest strings are exactly 64 lowercase hex characters. `release_tag` is
`catalogue-` plus the sequence padded to at least six digits (not a six-digit
maximum). `sha256` hashes original snapshot bytes. `asset_id` identifies that
snapshot JSON, not the pointer file. The predecessor is null only at sequence 1;
otherwise it hashes the complete previous canonical pointer bytes.

Limit: 1,024 bytes. Serialization is UTF-8, sorted object keys, two-space indent,
no non-finite numbers and one terminal newline. Noncanonical encodings, duplicate
keys, extra/missing fields and invalid UTF-8 fail. No URLs, secrets, connector
metadata, workflow roots, caller-selected signer or expiration appear here.
The existing six-field catalogue v1 envelope is unchanged.

The branch contains `current.json` and `current.sigstore.json`. A sequence-1
bootstrap selection uses a root commit. Later transport commits have exactly one
parent, whose pointer bytes/digest/sequence match the signed predecessor. A stale
signed selection inserted as a child of a newer selection fails this binding.
The parent ref SHA is transport metadata; it is not a certificate or signature.
The signature subject is `current.json`, not the Git SHA or branch name.

## Snapshot assets and sequence allocation

Each numbered Release has exactly:

- `catalogue-NNNNNN.json`: original canonical catalogue bytes.
- `catalogue.sigstore.json`: preserved original catalogue build evidence.
- `current.json`: selection of this exact release ID, catalogue asset ID and digest.
- `current.sigstore.json`: approved publication workflow's selection evidence.

Create as draft, attach and read back all assets, authenticate evidence, publish
with `make_latest=false`, then read back and verify actual immutability. GitHub
also generates its own release attestation; this implementation does not claim
to cryptographically verify that separate predicate. The publication profile binds
release/asset IDs; the GitHub API's enforced immutable flag remains a provider
claim, distinct from the original build signature. Tag resolution must match the
catalogue build's authenticated source commit, including annotated-tag bounds.

`sequence.txt` remains a reviewed source value. The publisher checks it against
current authenticated history: exactly current + 1, or an unchanged same-byte
resume. Gaps, rollback, exhausted numeric range and changed same-sequence bytes
fail. It does not auto-increment files or allocate based on unauthenticated tags.
A conflicting next/higher snapshot stops publication. The supported single
publisher cannot create further sequences until selection advances. Arbitrary
out-of-band release names confer no authority; tag rulesets prevent that path.
Work remains bounded per publication rather than scanning all historical releases.
The 200-entry v1 ceiling still limits retained Connector/version records; reaching
it needs a later reviewed contract evolution, never silent history deletion.

Every existing entry remains present. Full canonical Manifest, package digest,
source identity, release tag and asset ID are immutable. Active can become
withdrawn; withdrawn cannot reactivate. Withdrawn entries retain explicit history
and convey no executable eligibility. No running Connector is automatically killed.

## Signing profiles and single-maintainer authorization

| Purpose | Workflow | Source ref | Subject |
| --- | --- | --- | --- |
| Catalogue build | `.github/workflows/catalogue.yml` | `refs/heads/main` | numbered catalogue JSON (legacy also catalogue.json) |
| Package build | `.github/workflows/release.yml` | exact `refs/tags/ID-vVERSION` | `ID-VERSION.tar.gz` |
| Approved selection | `.github/workflows/catalogue-publish.yml` | `refs/heads/main` | `current.json` |

All profiles require issuer `https://token.actions.githubusercontent.com`, repository
URI `https://github.com/benchristian88/atlas-connectors`, repository ID **1414494920**,
owner ID **93822871**, hosted runner and exact signer/configuration/source identity.
Use Sigstore bundle v0.3, in-toto Statement v1 and
`https://slsa.dev/provenance/v1`, with GitHub workflow build type. Original-byte
SHA-256 subject and certificate/source/predicate consistency are mandatory.

The pinned verifier is gh **2.102.1**, with reviewed per-platform binary/archive
hashes and frozen Public Good roots from the existing B1.2 acceptance. The
`tools/publication_trust` directory contains public distribution data and upstream
licence only; no Atlas application source was copied. Preparation installs the
verified binary; verification runs offline with no token or ambient CLI config.

The explicit policy mode is `single-maintainer-v1`. The maintainer reviews the
candidate and manually dispatches `catalogue-publish.yml` **from protected main**,
choosing `publish`, `recover`, or the separately gated `bootstrap` operation. That dispatch is the authorization action. This
provides **single-maintainer authorization**, not independent human approval or a
human cryptographic signature. GitHub records an account action; it cannot prove
that a person clicked the UI rather than using that account's API credential.

GitHub's [environment self-review rule](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments#required-reviewers)
prevents the initiator approving their own deployment. With one person there is
no additional independent approval. Neither environment uses required reviewers;
self-approval and admin bypass are not workarounds. Environments still restrict
refs and hold scoped secrets. Adding reviewers without a deliberate new policy is
rejected, rather than silently changing assurance or stranding the sole maintainer.

The exact verification procedure is in the [consumer handoff](consumer-handoff.md).
The producer reads GitHub's current run and attempt-1 records, workflow definition,
public user identity, repository, protected main, environment and source CI records.
Both `actor` and `triggering_actor` must be `User`, have the **same configured numeric
`allowed_maintainer_id`**, and agree with the independent user lookup. Missing,
inconsistent, App/Bot/team or unsupported identities fail. The pointer cannot name
a maintainer or authorize itself. Run ID, first attempt, manual event, workflow ID
and exact path, repository/owner IDs, main ref and SHA are checked. Before writes,
the SHA must equal both the runner's `GITHUB_SHA` and current main. On selection
verification it must equal the certificate's source SHA; historical main need not
still be HEAD. Required `validate` CI must be completed/successful for that SHA,
from GitHub Actions App 15368, with one unambiguous current check result. The
public CI read omits credentials, preserving the App's existing permissions;
anonymous rate limits or unavailable evidence fail closed, with no token fallback.

The signed invocation binds these API observations to the authenticated pointer.
The first-attempt rule rejects both reruns and a current run record contradicting
its attempt-1 record. Never rerun historical publication runs: doing so also
invalidates their current API evidence and can block subsequent chain verification.
A failed publication may still have a valid signed selection for recovery; workflow
success is not substituted for signature or dispatch verification. Fresh dispatches
are required for retries. CI success remains mandatory independently.

The scoped App is an automation identity, never the allowed human. Pin its numeric
App, installation and bot-user IDs plus slug. The pinned token action authenticates
its private key as that App, reads the repository installation using App JWT auth,
and creates a token restricted to this repository and the declared permissions.
Its API-derived slug/installation outputs must match policy. Independently check
public `/apps/SLUG` ID/owner/permissions and the token's `/installation/repositories`
response (exactly this repository). A wrong App, changed permissions, installation,
bot identity or ruleset bypass fails. These outputs alone are not standalone token
introspection: the reviewed, pinned action binds the key/token to them. See the
[pinned action implementation](https://github.com/actions/create-github-app-token/blob/fee1f7d63c2ff003460e3d139729b119787bc349/lib/main.js).

Package provenance remains the B1.2 tag workflow. Both actors of its first-attempt
`push` run must match the configured App bot and independent public user lookup;
its exact source/tag/workflow, CI and protected-main ancestry remain required.
A tag build is **not** human authorization. The later authenticated maintainer
catalogue dispatch authorizes inclusion of those exact immutable package bytes.
The App's identity cannot reveal which human operated a tag creation. No second
reviewer is hidden in the package process and no package signing profile changes.

## Deliberate policy evolution

Only `single-maintainer-v1` is supported. Unknown modes and legacy `reviewer_ids`
configuration fail closed. The mode lives in reviewed producer configuration and
in Atlas's independently approved trust policy; it is not a pointer field. A future
independent-reviewer mode requires a new ADR/policy identifier, distinct original
and approving numeric identities, enforced environment/PR review rules, independently
bound review evidence, deterministic tests and genuine acceptance. Producer and
consumer owners must agree an activation boundary and which historical signatures
remain valid under each policy. Do not silently reinterpret old signatures, infer
mode from available approvals, or fall back to single-maintainer authorization.
The pointer schema and signer may remain compatible only after that review.

## Operator configuration — do not execute publication yet

Public metadata on 22 October 2026 showed main unprotected, no rulesets,
connector-release without protection, and both legacy releases mutable. The plan
of the personal account was not exposed. Public repositories on current GitHub
Free/Pro/Team plans support environment protection and branch/tag
rulesets; actual supported API evidence is still required. Private-repository feature availability differs.
No paid upgrade is assumed and no configuration is claimed to be present.

Owner actions, separately reviewed:

1. Enable **Settings → General → Releases → Enable release immutability** for
   future releases. Existing mutable releases do not become immutable. Verify
   `GET /repos/benchristian88/atlas-connectors/immutable-releases` with admin-read
   authority returns `enabled: true`. Anonymous HTTP 401 cannot establish it.
2. Create a GitHub App installed **only** on this repository: Contents write,
   Actions read, Administration read, automatic Metadata read; no administration
   write or other permission. Protect its private key as an environment secret
   `PUBLICATION_APP_PRIVATE_KEY`, and set `PUBLICATION_APP_ID` for that environment.
   Installation tokens expire and the pinned token action revokes them after use.
   A long-lived App key is still a secret; rotate and audit it. No PAT is needed.
3. Create exactly the following supported active repository rulesets (the code
   rejects weaker/different combinations rather than guessing equivalence):

| Name | Target/includes, with no excludes | Required rules | Bypass |
| --- | --- | --- | --- |
| atlas-main | branch, refs/heads/main | pull_request: 0 required approvals, dismiss stale, last-push approval false; required_status_checks: validate from GitHub Actions (integration_id 15368), strict; deletion; non_fast_forward | none |
| atlas-catalogue-current | branch, refs/heads/catalogue-current | creation; update; deletion; non_fast_forward | publication App Integration ID, always |
| atlas-history-lock | branch, refs/heads/catalogue-current | deletion; non_fast_forward | **none, including the App** |
| atlas-publication-tags | tag, refs/tags/catalogue-* then refs/tags/*-v* | creation; update; deletion | publication App Integration ID, always |

   Extra protections may be added; required scope/bypass must remain exact.
   Protect publication policy, recipes and workflows through the main PR checks.
   Inspect `/rulesets?per_page=100` and each `/rulesets/ID`, and `/branches/main`.
   Immutability additionally locks finalized tags/assets regardless of naming.
4. Create environment **catalogue-publication**, allowed protected branches,
   **no required reviewers**, no admin bypass. Only main is accepted by the workflow.
   Configure **connector-release** with no required reviewers or admin bypass and
   custom **tag** deployment policies matching `*-v*`. Do not permit branch rules
   there. Package runs must also pass exact tag and protected-main ancestry checks.
   The main PR rule deliberately requires zero approvals and disables last-push
   approval: the earlier proposal was impossible for one author. PRs, strict CI,
   no main bypass and no deletion/force push remain required. This is a documented
   assurance change, not independent source review.
5. Choose the one actual numeric maintainer user ID, both environment IDs, and
   actual App/installation/bot-user IDs and slug. Do not infer the allowed maintainer
   from a run, pointer, login or repository owner. Confirm the selected account
   independently, then record `allowed_maintainer_id` through a reviewed policy PR.
   The current source policy records reviewed identities; independently verify
   their live validity before activation. Enforce MFA/passkeys on the maintainer
   account and protect its credentials; this design has one human trust root.
6. Keep default Actions permissions read-only. Catalogue preparation receives
   contents read + attestations write + id-token write. Publication's GITHUB_TOKEN
   also gets Actions read; only the ref-restricted App token grants contents
   write. No PR trigger runs publication code with these credentials. Workflow
   dispatch accepts only `publish`, `recover` or `bootstrap`, never a
   repository/ref/digest.
7. Approve the implemented two-dispatch [bootstrap procedure](bootstrap.md),
   including its new no-bypass root-intent tag ruleset. Record the
   actual approved sequence/pointer digest in `policy.json` only after the
   bootstrap runbook staging checkpoint. The stage-only activation deliberately
   leaves those pins null; separate activation approves the real bytes. Fill environment,
   maintainer and App identities through a reviewed PR; change `enabled` only after
   configuration and the Atlas profile/bootstrap decisions, for an explicitly
   approved first live acceptance. Normal production readiness still requires
   that genuine acceptance to pass. Do not insert dummy IDs.
8. Confirm the Application can create/update only the intended refs under rules,
   cannot force-push/delete current, and cannot change settings. Its installation
   contents permission is repository-wide: GitHub does not offer per-path tokens.
   Rulesets and protected secret access provide the additional restriction.

Read-only verification commands (owner supplies authentication as appropriate):

```bash
gh api repos/benchristian88/atlas-connectors/immutable-releases
gh api repos/benchristian88/atlas-connectors/branches/main
gh api repos/benchristian88/atlas-connectors/rulesets
gh api repos/benchristian88/atlas-connectors/environments/catalogue-publication
gh api repos/benchristian88/atlas-connectors/environments/connector-release
```

After an explicitly authorized test run, inspect the run and attempt-1 records,
workflow/user/CI evidence, `/releases/ID`,
`/releases/ID/assets`, exact asset bytes/bundles, tag commit and the current ref's
single-parent chain. Do not use a release title, checksum or successful CI badge
as proof of immutability or independent human approval. Nothing in this checklist
was changed automatically by P1.

## Publication and failure recovery

Review registry changes and their evidence in a PR. Increment sequence once.
Run catalogue preparation from main; inspect its digest and reviewable artifacts.
Review the exact main commit and manually dispatch publication from it as the
configured maintainer. No extra environment approval is requested. The publisher
rebuilds deterministically and retrieves genuine matching
catalogue provenance by digest/source, rather than trusting workflow ZIP contents.
It downloads packages for hashing/verification but never extracts or executes them.

Workflow concurrency is repository-wide `official-catalogue-publication` with no
cancellation of a running publication. GitHub may replace an older pending run;
source/sequence checks reject stale work. Ref CAS supplies a second concurrency
boundary. Calls use fixed repository paths, TLS, time/byte/pagination limits,
bounded GET retries and sanitized errors. An ambiguous write is never blindly
retried; a fresh maintainer dispatch rereads actual provider state.

| Interrupted state | Safe next action |
| --- | --- |
| Preparation rerun | Same commit reproduces bytes; different genuine bundles may bind the same bytes |
| No draft yet | Fresh maintainer-authorized publish from the same source |
| Partial draft | Fresh maintainer-authorized publish verifies existing bytes and adds missing assets; never overwrites |
| Conflicting draft/tag/asset | Stop and investigate; do not delete or replace through this tool |
| Published but mutable | Stop; current stays unchanged; no in-place immutability claim |
| Immutable snapshot, pointer stale | Fresh maintainer-authorized `recover` verifies original snapshot, original dispatch identity and packages, then CAS |
| Main advanced after immutable publication | `recover` uses original bytes and build evidence, not a rebuild at new HEAD |
| Main advanced with an unfinished draft | Stop; a separately reviewed recovery decision is required |
| Pointer already advanced | Same-byte publish returns unchanged; recover reports no pending immediate successor |
| Newer sequence already current | Older publish fails rollback; no force update |
| API timeout/rate limit/run or identity evidence missing | Stop without claiming currentness; retry later with a fresh maintainer dispatch |
| Workflow rerun attempt > 1 | Rejected; dispatch a fresh run; do not rerun signed history |

The signed pointer/bundle are stored in the immutable snapshot before finalisation,
so selection failures do not lose them. Recovery preserves them exactly. Pointer
signing expresses authorization to select the named bytes once they are immutable;
it is not a claim that the draft was already immutable at signing time.

## Legacy bootstrap and package history

Sequence 1 stays exactly 10,585 bytes at SHA-256
`55533ca67e7e9a14f82961e0a8c34ad78e2596049b3db02fde787494e3975afd`.
Preserve catalogue-v1's two JSON assets, attestation 57152061 and original source
`91dfd86f18d0b59ff977bb1e8a5fef42c5329943`. Do not rebuild from current HEAD.

The implemented [bootstrap operation](bootstrap.md) copies these authenticated
bytes and the exact original bundle into a new draft targeting the original source.
It signs a new seven-field selection through catalogue-publish.yml using real
provider IDs, then stops. A separate reviewed policy commit pins the actual pointer
digest; a fresh activation dispatch verifies and finalises the immutable release
before creating a true root. A protected no-bypass root-intent tag fences consumed
bootstrap authority even if current is later removed. See the bootstrap runbook
for the extra ruleset, bounded recovery and operator checkpoints. This task leaves
publication disabled, bootstrap operation disabled and both root pins unset.

The legacy catalogue contains Proxmox 0.2.0 whose package release also reports
mutable. Copying that package to a different tag/asset would change its recorded
version identity. Do not edit that old Manifest. The owner must separately decide
how to retain it as non-installable history and publish a new qualified version
under the secure package process. Migrating the catalogue alone cannot enable
legacy package installation. Bootstrap migration must expressly state that
limitation and must not assert package eligibility.

## Dynamic Connector process

Add a canonical SDK-compatible Connector, explicit `package.json` reviewed file
recipe, source-version qualification and evidence docs. The recipe excludes
incidental/test/candidate files, rejects unsafe paths and bounds package size.
`release.yml` accepts `*-v*` but selects only a unique exact ID/version Manifest
with recorded qualification and a valid recipe. All existing qualification/Ansible
regressions still run. Default local build commands retain Proxmox compatibility;
there is no Proxmox allowlist or distribution-path special case in the builder.

The operator creates the reviewed tag using the scoped publication App authority
under the ruleset, then reviews release preparation. P1 generalizes preparation;
it does not add automatic executable-package release finalisation. The owner
stages those exact authenticated artifacts into a draft and verifies actual
immutable finalisation. Capture the real package asset ID and combined Manifest
in the registry only afterwards. The catalogue gate checks qualification, digest,
source, package provenance, App build identity, immutable release and exact asset ID.
The explicit catalogue dispatch authorizes inclusion; preparation has no human
approval claim. The operator can perform tag creation and draft finalisation alone
using the dedicated App, but must follow its scope and evidence checks. There is
no automated package finaliser. The distinct bootstrap command never publishes
or qualifies executable packages.
New IDs/versions conforming to supported contracts require no Atlas source edits.

## Residual limitations and acceptance

A compromised maintainer account can authorize malicious reviewed-source changes
and publication; there is no independent human veto. A compromised correct App key
cannot be distinguished from legitimate key use, but cannot pass the human dispatch
identity check or forge the existing Sigstore signer. It can cause denial of service,
stage conflicting drafts/tags and operate within its contents permission. Rotation,
audit and incident recovery remain necessary. API observations are current provider
claims, not cryptographic proof that protections were continuously enabled in the
past. Actor/login changes or deleted/re-run historical runs may block verification;
never recover by taking an identity from a pointer or skipping the failing evidence.

No cryptographic mechanism here proves global freshness or that GitHub will never
withhold a newer signed pointer. Persist high-water marks; after database rollback
or complete loss, require audited bootstrap/recovery. API availability/rate limits
and run/identity/CI evidence retention can block safe progress. An authorized
administrator
can change policy or compromise workflows; audit and review are part of the trust
root. App credentials cannot forge Sigstore signatures, but compromise remains an
availability and source-control risk. GitHub is the sole hosted authority.

Deterministic tests exercise modeled API/state behavior and genuine frozen B1.2
verification separately. There is **no genuine new signed pointer, immutable
snapshot or live single-maintainer acceptance fixture** yet. Real provider acceptance
must demonstrate allowed/disallowed actors, rerun rejection, App restrictions, actual locking,
anonymous consumer verification, advance, stale-worker rejection, retry/recovery,
unchanged confirmation and restored high-water state before declaring B1.3 live.
