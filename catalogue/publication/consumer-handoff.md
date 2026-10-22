# Atlas consumer handoff — P1 single-maintainer authorization

No Atlas or SDK files were modified. B1.2 does not accept the selection profile.
Atlas must retain publication rejection until this producer contract and the
**single-maintainer-v1** trust policy are explicitly reviewed and independently
implemented. Manual dispatch provides **single-maintainer authorization**, not
independent human approval. GitHub API account evidence and cryptographic workflow
provenance establish different parts of the decision.

## Trust configuration belongs to the consumer

Atlas needs its own approved policy identifier, numeric `allowed_maintainer_id`,
repository ID **1414494920**, owner ID **93822871**, environment IDs, dedicated App
ID/slug/bot-user ID, and approved bootstrap sequence/pointer SHA-256. Record the
reviewed producer workflow/policy source revision at activation. Neither pointer
fields nor a downloaded `policy.json` may supply authoritative identity, roots,
mode or bootstrap values. The producer defaults disabled; publisher identities are configured in source,
while the bootstrap sequence/pointer pins remain null.
Do not assume that the repository owner's numeric ID is the authorized maintainer.

Only the explicit single-maintainer mode is implemented. A future independent-
reviewer policy needs a new reviewed identifier/ADR, producer and consumer changes,
real independent approval evidence, activation/history migration rules and genuine
acceptance. Never automatically fall back between modes or reinterpret already
accepted signatures under a different assurance level. A new mode is not implied
by an added GitHub environment reviewer or a successful deployment status.

## Exact independent identity verification

Use fixed `https://api.github.com/repos/benchristian88/atlas-connectors` endpoints
and bounded transport. The following checks supplement, never replace, B1.2
cryptographic verification. API records are GitHub's observations, not signatures
made by a human. Deleted, unavailable, malformed, conflicting or unsupported
records must fail closed without replacing last-known-good state.

1. Authenticate the original `current.json` bytes with a distinct
   `official-catalogue-selection` profile: `.github/workflows/catalogue-publish.yml`,
   `refs/heads/main`, subject `current.json`, exact SHA-256. Retain B1.2's issuer,
   numeric repository/owner identities, hosted-runner constraint, SLSA v1 predicate,
   certificate/predicate/source consistency, transparency timestamps, pinned gh
   2.102.1 and frozen roots. Preserve catalogue and package signer profiles unchanged.
2. Read the **verified** certificate/SLSA invocation, exactly
   `https://github.com/benchristian88/atlas-connectors/actions/runs/RUN/attempts/1`.
   Reject every other attempt or origin. Take the expected source SHA from the
   authenticated certificate, never a pointer-supplied field or receipt.
3. Independently GET `/actions/runs/RUN` **and** `/actions/runs/RUN/attempts/1`.
   Both must be objects with the same requested numeric `id`, literal integer
   `run_attempt: 1`, event `workflow_dispatch`, `head_branch: main`, exact expected
   SHA and fixed run API/HTML URLs. Their `repository` and `head_repository` must
   both match numeric repository/owner IDs, full name and public visibility.
   A latest run record showing attempt 2 invalidates the attempt-1 acceptance;
   fetching the old attempt alone must not hide a rerun.
4. Require both records' `actor` **and** `triggering_actor` to be objects with type
   `User`, literal numeric ID equal to the consumer-configured maintainer ID, and
   a valid matching login. Neither an App/Bot/team, missing original actor nor a
   different triggering actor is supported. Independently GET
   `https://api.github.com/users/LOGIN`, using bounded encoded login routing, and
   require that public account's ID/type/login to match. The login only routes a
   lookup; the externally configured numeric ID authorizes it. Account renames
   that make historical observations inconsistent fail closed pending review.
5. Both runs must have the same numeric `workflow_id`. Independently GET
   `/actions/workflows/WORKFLOW_ID`; require that ID, fixed API URL, `state: active`
   and path `.github/workflows/catalogue-publish.yml`. The run path must be exactly
   that path, that path plus `@main`, or that path plus `@refs/heads/main`, the
   supported provider representations. No suffix/prefix, fork or reusable-workflow
   substitution is allowed. The certificate separately binds signer/config path.
6. GET the repository and `/branches/main`: exact repository/owner/public identity,
   name main and `protected: true`. GET `/commits/SHA/check-runs?check_name=validate&filter=latest&per_page=100`:
   exactly one result and `total_count: 1`, name validate, exact source SHA,
   completed/success and GitHub Actions App ID 15368. Ambiguous results fail.
   This public CI read is anonymous in the producer too, avoiding Checks permission
   on the App. Rate-limit/availability failure must not trigger an auth fallback.
   A consumer verifying historical selection must **not** require its source SHA
   to remain current main HEAD. A producing fresh dispatch must match both current
   main and `GITHUB_SHA`; recovery independently authorizes the current run and
   verifies the historical selection against its original signed SHA.
7. Independently GET `/environments/catalogue-publication`: approved numeric ID,
   exact name, `can_admins_bypass: false`, protected-branches-only deployment policy
   and an explicit protection-rule list with **no required_reviewers**. No approval
   API call is required in this mode. A self-approved environment record is not an
   alternative authorization path. Main must have the exact active ruleset scopes
   and bypass configuration in the [runbook](README.md), including required PRs,
   zero required approvals, last-push approval false, strict GitHub Actions validate
   checks, no bypass and no force push/deletion. Read `/rulesets?per_page=100` and
   each `/rulesets/ID`; do not infer enforcement from names or a CI badge.
8. Check the protected current branch and publication-tag rulesets with the
   independently configured numeric App Integration bypass ID and the separate
   no-bypass current history lock. Public `https://api.github.com/apps/SLUG` must
   match that App ID, owner ID and exactly Contents write, Actions read,
   Administration read and Metadata read. Package runs must match the configured
   bot-user ID/slug through public user lookup. The producer additionally checks
   JWT-authenticated token-action installation outputs and installation-token
   repository scope. Those are not public consumer evidence and a producer receipt
   cannot substitute for them. Consumers rely on the reviewed pinned workflow for
   that token-issuance behavior; never require a maintainer's key or token.

[GitHub's run/attempt API](https://docs.github.com/en/rest/actions/workflow-runs),
[workflow API](https://docs.github.com/en/rest/actions/workflows#get-a-workflow),
[user API](https://docs.github.com/en/rest/users/users#get-a-user) and
[check-run API](https://docs.github.com/en/rest/checks/runs#list-check-runs-for-a-git-reference)
are the provider observations above. These checks establish current policy state;
they cannot prove that settings were never temporarily disabled. Workflow run
completion is not required for an interrupted signed selection: its valid dispatch
and signature can survive a later job failure. The separate source CI must succeed.

## Selection, immutability and history remain unchanged

- Parse exactly the seven fields specified in the [runbook](README.md): schema 1.0,
  canonical UTF-8/sorted/two-space/newline JSON, 1,024-byte limit, positive literal
  safe integers, lowercase digests and predecessor null only for sequence 1.
  The six-field catalogue v1 envelope and sequence-1 bytes remain unchanged.
- Resolve the fixed `/git/ref/heads/catalogue-current` endpoint. Fetch both
  selection files at that exact transport commit via bounded Contents API reads.
  Require a root bootstrap commit or one parent with the preceding pointer
  sequence/digest. The Git ref/commit is transport evidence, not a signature.
- After authentication, resolve signed release/asset IDs in the fixed repository.
  Require exact numbered tag, non-draft/non-prerelease, actual `immutable: true`,
  bounded exact original asset bytes/digest, existing B1.1 structure and B1.2 build
  provenance. Resolve the release tag to the authenticated catalogue build source.
  The immutable release must retain the identical pointer and selection bundle.
  The producer also reads `/immutable-releases` with Administration read; this
  setting endpoint is not anonymous consumer evidence. Consumers require the
  actual selected release's immutable flag and never infer it from a setting.
- Retain contiguous sequences, signed predecessor chain, equal-sequence exact-byte
  confirmation, rollback/substitution rejection, complete manifests and explicit
  sticky withdrawals. Authenticate bounded intermediate numbered snapshots when
  catching up; never skip a gap to fit a bound. Preserve last-known-good on failure.
- Persist original pointer/catalogue/bundles, digests, selected release/asset IDs,
  transport revision, policy identifier and sanitized observed run/actor/workflow/
  CI/protection evidence with the trusted revision/high-water state. Reread current
  before transactional acceptance; retry if it changes. Preserve cooldown, leases,
  stale-worker rejection, backup handling and daily refresh/local 72-hour freshness.
  Currentness cannot be proven cryptographically after loss of all trusted state.

## Package inclusion and compatibility

Package signatures remain `.github/workflows/release.yml@refs/tags/ID-vVERSION`.
Verify exact qualified Manifest, source/tag/digest, immutable package release and
recorded asset ID. Bind the signed invocation to both first-attempt API records,
release workflow ID/path, push event, exact tag and SHA. Both actors must be the
configured App bot, independently resolved through its public account; verify
`connector-release` environment ID, no reviewers/admin bypass and custom tag policy.
GET `/environments/connector-release/deployment-branch-policies?per_page=100` must
report exactly one policy (`total_count: 1`), positive ID, name `*-v*`, type `tag`.
Require successful source validate CI and `/compare/SHA...main` to report ahead or
identical with merge-base SHA equal to source. These checks authenticate the build;
the manual selection run authorizes inclusion. There is no claimed independent
package reviewer and no inference of the person behind App-triggered tag creation.

New compatible Connector IDs/versions require no vendor-specific Atlas changes.
Incompatible SDK/runtime contracts still require explicit support. No remote install
capability is enabled; the later B3 eligibility/approval path remains separate.
Legacy Proxmox 0.2.0 is mutable and cannot be made installable by this policy change.
Do not rewrite its frozen Manifest, tag, digest, asset ID or attestations.

## Acceptance work still required in Atlas

Implement the above trust policy separately and test allowed/unauthorized/missing
maintainer identities, both actors, missing/conflicting API observations, wrong
run/workflow/event/repository/ref/SHA, reruns, disabled protections/failed CI,
unexpected or compromised App paths, and every existing immutable/history/recovery
boundary. Include future compatible Connector fixtures without vendor conditionals.

Producer tests simulate these GitHub responses and selection signatures. Genuine
frozen B1.2 catalogue/package signatures are tested separately; **there is no new
genuine signed pointer or live immutable-publication acceptance evidence**. Obtain
real public run/identity/workflow/CI observations and verify a genuine signed
selection with the pinned verifier after configuration and explicit live-test
approval. Confirm anonymous consumer evidence availability; any inaccessible
required endpoint blocks acceptance rather than introducing a token fallback.

Remaining prerequisites are actual reviewed identities/settings/App credentials,
an approved bootstrap migration and digest, non-installable legacy history handling,
consumer policy implementation and genuine acceptance. The one-human model removes
the second-maintainer blocker; it adds no independent human veto against maintainer
account compromise. Unknown policy modes fail closed until deliberately reviewed.

## P2 bootstrap handoff — still requires independent Atlas work

The [two-dispatch producer bootstrap](bootstrap.md) and
[ADR 0003](../../docs/decisions/0003-sequence-one-bootstrap.md) implement source
preservation, signed draft staging, separate pointer-digest approval, immutable
finalisation and create-only root selection. No migration has run. The producer
policy retains `enabled: false`, `bootstrap_operation: disabled`, sequence null
and pointer digest null. No actual target release/asset IDs, new signature or root
SHA may be invented for consumer configuration.

Atlas's existing B1.3 adapter still targets legacy catalogue-v1 and rejects
`publication_not_immutable`; even an immutable legacy release reaches
`current_channel_policy_unavailable`. Neither gate was modified. A later Atlas
change must implement this advancing channel and distinct selection profile,
independently approve the **actual canonical pointer digest**, preserve the frozen
catalogue digest/source/build profile, and retain root pointer/bundle and historical
trust state. Authorize using the configured single maintainer and authenticated
first-attempt selection invocation, then verify immutable snapshot identity and
original build evidence. The activation dispatch is separately recorded in the
producer receipt; it is not the signer invocation and the receipt is not trust.

Configured producer inputs: maintainer 93822871; repository 1414494920; owner
93822871; environments 24999137498 and 24617213627; App 5422372,
`atlas-catalogue-publisher`, installation 174027755, bot 346232650. Atlas must
review its own configuration rather than download these as authoritative policy.

The new no-bypass `atlas-bootstrap-lock` protects the write-once
`refs/tags/catalogue-bootstrap-root` intent tag. It points to the parentless root
with exactly current.json and current.sigstore.json. It prevents producer bootstrap
from reopening after current disappears. Consumers may use it as corroborating
provider evidence; it is neither a signature nor a replacement for independent
high-water/history storage. Missing current or lost database state requires reviewed
recovery, never publisher rebootstrap. Keep immutable revisions, exact IDs, sticky
withdrawal history and normal predecessor checks across restarts and restores.

The frozen active Proxmox 0.2.0 entry is authenticated catalogue history only.
Its mutable package remains non-installable. There is no Connector-specific B3
exception or package promotion. A later sequence may deliberately withdraw that
entry without changing its identity, and include a newly qualified immutable
release through ordinary generic gates. P1 checks all active entries and will
otherwise reject advancement carrying that mutable package as active.

Genuine new pointer verification, live public API/protection observations, immutable
release/root receipt, explicit consumer root approval, durable first acceptance,
unchanged confirmation, advancement and restart/last-known-good acceptance remain
outstanding. Offline original-source verification and model tests do not satisfy
those boundaries.
