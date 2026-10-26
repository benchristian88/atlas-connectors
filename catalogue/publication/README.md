# Official catalogue publication — Lean V2 operator runbook

Phase 4B.1 [security acceptance](../../docs/phase-4b1-security-acceptance.md) concluded
**GO FOR PR for preparation only**. Phase 4B.2 now locally implements the separate
[package publication mechanism](connector-packages.md) for review. Execution is
disabled. PR2 pins its reviewed implementation to
`d6601ad97815a85da164e4329766ea17b62bddc9`; genuine isolated acceptance and owner
security decisions remain required. Frozen S4 catalogue authorization cannot
authorize the package workflow. The assessment below preserves the Phase 4B preparation
baseline; the new runbook records current implementation and remaining controls.

## Phase 4B package release assessment (26 October 2026)

Inspection baseline: `b03405d6acfd562f75dbdf7aad91c94df9a1d32e`, identical to
local and independently queried remote `main`. The clean, already existing
`feature/proxmox-immutable-release` branch started at that same commit.
Related read-only references: Atlas `dev` at
`808ee0f76f77c11e17a6c403806ce0666e30074e`, SDK `main` at
`8b0518c462289cca4758c3b9bf362f1130928a1c`.

Before implementation, the checked-in release path established the following:

- A `*-v*` push runs `release.yml` on a hosted runner, attempt one, in
  `connector-release`. It selects qualified source by exact tag/Manifest,
  deterministically builds the package, tests, attests the archive with pinned
  `actions/attest`, then retains candidate files. It does not publish a Release.
- The configured Publisher App is the sole publication-tag ruleset bypass.
  Both original and triggering package-build actors must be its bot. Existing
  `Publisher.run_authority` checks both independent run records, workflow, account,
  source CI and package environment; `Publisher.packages` checks main ancestry.
  The later human catalogue dispatch authorizes inclusion, not the tag build.
- Package provenance binds repository/owner, `release.yml@refs/tags/ID-vVERSION`,
  source/signer/configuration SHA, hosted runner, issuer, SLSA subject digest and
  run/attempt. The pinned offline verifier authenticates these fields.
- The existing operator procedure assigns package staging/finalization to the
  scoped App. There is no package finalizer workflow. Missing local controls are
  clean exact-source enforcement, release-specific archive/SBOM/licence checks,
  retention of the package signature bundle, and independent final package
  release/asset verification. Configuration alone cannot prove immutability.
- S4's signed preflight authorizes only the existing catalogue caller/operations.
  It cannot authorize a new package workflow. Its code, pins, keys, permissions,
  catalogue policy and historical publication remain frozen in this increment.

The implementation extends the existing recipe/build/tag workflow with explicit
version metadata and verification, retaining operator-controlled App publication.
It introduces no new privilege path or authorization policy. Proxmox **0.2.1** is
a patch packaging identity: unchanged qualified behavior, new Manifest/SBOM/docs
and new bytes. The base 0.2.0 source and default build remain intact. Atlas ADRs
0006/0011 remain authoritative; accepted ADR 0013 permits only exact sequence one.
The stronger future-publication design in Atlas ADR 0012 remains Proposed and
blocks sequence-two consumer acceptance until separately approved and delivered.

**Provider-side sequence-1 bootstrap is completed; immutable catalogue publication is active.**
The closure policy sets `bootstrap_operation: disabled`, preserving `enabled: true`,
single-maintainer authorization, all IDs and the approved sequence/pointer pins.
Normal `publish` and `recover` remain available subject to existing signed preflight,
package, contiguous sequence, predecessor, immutable-release and history checks.
Atlas now accepts only exact sequence one under ADR 0013. Stronger future-sequence
consumer acceptance and Atlas B3 remote-installation readiness remain outstanding.

Reviewed implementation **S = S4 = `2dd1ffcd2f5677dc35bdbc8f68ea28275c91c285`**
was merged through [PR #30](https://github.com/benchristian88/atlas-connectors/pull/30)
and remains frozen. All three executable workflow pins and
[verifier trust](verifier-trust.json), including `live_signer_accepted: true`, are
unchanged. Caller/source **C** advances independently and must differ from S.
This closure changes no executable code and performs no remote operation.

Owner-reviewed genuine [S4 acceptance run 39893809663](https://github.com/benchristian88/atlas-connectors/actions/runs/39893809663)
passed on attempt **1**, with caller `605553a556632ace6f21216bf6cd22fdc17ed528`,
baseline Publisher permissions and Publisher **skipped**. The owner subsequently
verified the following production evidence; local regression tests do not replace it.

| Production evidence | Exact value |
| --- | --- |
| Staging run / source C | [39896288128](https://github.com/benchristian88/atlas-connectors/actions/runs/39896288128) / `8ce0b80c74d6ceb8ce75ac7ec8693f5bba78b305` |
| Staging result | `staged_requires_separate_approval` |
| Activation run / source C | [39912401767](https://github.com/benchristian88/atlas-connectors/actions/runs/39912401767) / `51f8693fbcca1e4c6c9615662bca368839ea0757` |
| Activation result | `bootstrapped`, `published: true`, `immutable: true` |
| Release tag / ID | `catalogue-000001` / **421426993** |
| GitHub release state | `draft: false`, `immutable: true` |
| `catalogue-000001.json` asset ID | **667867351** |
| `catalogue.sigstore.json` asset ID | **667867380** |
| `current.json` asset ID | **667867419** |
| `current.sigstore.json` asset ID | **667868363** |
| Catalogue SHA-256 | `55533ca67e7e9a14f82961e0a8c34ad78e2596049b3db02fde787494e3975afd` |
| Approved bootstrap sequence | **1** |
| Approved pointer SHA-256 | `a275f63d0ac818a193826478328ee324be62353addc5c97a2ed0a28d217b5372` |
| Parentless root commit | `a1597730687be993d766ddb465a0d3362aef2d02` |
| Root refs | `refs/heads/catalogue-current` and `refs/tags/catalogue-bootstrap-root`, both at that root |
| Exact root files | `current.json`, `current.sigstore.json` |

All four original assets were independently verified unchanged. The root and pins
remain the existing trust anchor, not a new initialization authority. Disabled
bootstrap rejects new staging/activation; absent current never enables a fallback.
Do not rerun bootstrap or reset its pins to null.

The repository owner removed Publisher Workflows Write. Genuine first-attempt,
independent signed acceptance-only [verification run 39913094643](https://github.com/benchristian88/atlas-connectors/actions/runs/39913094643)
passed preflight/verify with Publisher **skipped**, confirming the Publisher **App
registration** matched baseline: Contents Write, Actions Read, Administration Read,
Metadata Read, **Workflows No access**. It did not independently test the installed
App's effective access. The Verifier App remains unchanged.

Previously accepted **S3 = `5c66a50f61d013204eada0234c3389323b4a3f71`** succeeded
in owner-reviewed [run 39887360792](https://github.com/benchristian88/atlas-connectors/actions/runs/39887360792),
attempt **1**, with caller **C = `2e2ddb70a1da254c0adaa857deb121aa2b0f7dfa`**.
Preflight, Verifier App authentication, Sigstore attestation and offline
cryptographic verification passed; Publisher was **skipped**. This accepts S3's
signer identity and isolation, not completed bootstrap staging or live Publisher
HTTP behavior. Publication authority and App permissions are unchanged.

Previously accepted **S2 = `00c85f688a43fb6da44acb3fa713d938e30a6da9`** passed
genuine production-profile verification in [run 39878342565](https://github.com/benchristian88/atlas-connectors/actions/runs/39878342565),
with Publisher skipped. S3's separate acceptance is recorded above. The first live
bootstrap staging attempt, [run 39880692187](https://github.com/benchristian88/atlas-connectors/actions/runs/39880692187),
passed signed authorization, offline historical verification and Publisher token
creation, then failed with `github_request_failed`; no new draft was observed.
The subsequent GET-only [diagnostic run 39883753194](https://github.com/benchristian88/atlas-connectors/actions/runs/39883753194)
passed all 35 API requests. Those reads do not establish whether release creation
was attempted or why it failed. The later controlled S3 [run 39888883962](https://github.com/benchristian88/atlas-connectors/actions/runs/39888883962)
confirmed `github_http_failure method=POST route=release_create status=403` at
`POST /repos/benchristian88/atlas-connectors/releases`. The historical target
`91dfd86f18d0b59ff977bb1e8a5fef42c5329943` differs from current main under
`.github/workflows/`. GitHub's documented conditional Workflows Write requirement
motivated the temporary profile below. The later successful staging run above
provides live evidence of draft creation/sealing with that profile. Activation,
immutable finalisation and permission rollback subsequently completed as recorded above.
These earlier failures are historical incident evidence.

The [security contract](../../docs/signed-publication-verifier.md) and
[ADR 0005](../../docs/decisions/0005-lean-run-preflight.md) define the one-preflight
design. [Historical configuration tables](publication-v1-reference.md), the
[consumer handoff](consumer-handoff.md) and detailed [P2 bootstrap rules](bootstrap.md)
remain reference material; the current workflow and runbook take precedence over
old per-transition grants and disabled-policy descriptions.

## Configured pins and ongoing authorization

1. The reviewed V2 implementation is frozen at S above. The reusable workflow
   call, Publisher executable checkout and `ATLAS_IMPLEMENTATION_REVISION` all
   pin that exact full S4 SHA and are unchanged by this approval. Caller C
   advances independently. Keep the source checkout
   at `${{ github.sha }}`; it advances independently and is read only as
   catalogue/policy/trust data. Never replace executable S with a moving branch,
   tag, local reusable call or latest-main lookup.
2. Independently verify repository **1414494920**, owner/human maintainer
   **93822871**; Publisher App/installation **5422372 / 174027755**, bot **346232650**;
   Verifier App/installation **5424851 / 174088125**. Preserve the existing App
   baseline permissions: Publisher Contents Write, Actions/Administration/Metadata Read;
   Verifier Administration Write, Contents/Actions/Checks/Metadata Read. Both
   installations must be selected for exactly this repository. The Publisher's
   temporary bootstrap Workflows Write has been removed. Registration rollback
   is verified above; independently checking installed effective access remains an
   operator action. Normal publish/recover require no Workflows permission.
3. Check protected main and all five active repository rulesets, complete bypass
   arrays, exact environment IDs/ref restrictions, no required reviewers/admin
   bypass, required successful `validate` CI, and release immutability. Keep the
   Verifier out of all bypass lists. The Publisher alone bypasses current-update
   and publication-tag rules; main, history-lock and bootstrap-lock have no bypass.
   See the [configuration tables](publication-v1-reference.md#operator-configuration--do-not-execute-publication-yet)
   and [bootstrap fence](bootstrap.md#configuration-checklist-and-authority).
4. Before any authorized publish/recover dispatch, independently reconfirm that the GitHub environment variable
   `VERIFICATION_POLICY` in environment **catalogue-verification** is JSON
   identical to the unchanged committed [verifier-trust.json](verifier-trust.json),
   preserving `live_signer_accepted: true`; do not set
   this variable in a different environment or pass it as a workflow input.
   This task does not create or modify the GitHub variable. The configured
   verification environment ID is **25016263801**, with `can_admins_bypass: false`
   and branch policy `protected_branches: true`, `custom_branch_policies: false`.
   The maximum startup age remains **900 seconds**. Store each App key only in
   its existing environment, never a caller input or inherited secret.

The caller explicitly passes exactly one named secret to the reusable verifier:

```yaml
secrets:
  VERIFICATION_APP_PRIVATE_KEY: ${{ secrets.VERIFICATION_APP_PRIVATE_KEY }}
```

S4 retains that secret as required under `on.workflow_call.secrets`. The called
verifier job retains `environment: catalogue-verification`, including its existing
restrictions, and injects the key only into the issuer step. Keep the key in that
environment; do not copy it to a repository-level secret or `catalogue-publication`.
Never use `secrets: inherit`, pass either App's credentials to the other job, or
put the key in an input, output, artifact, command-line argument or log.

## Historical bootstrap permission profile (closed)

Bootstrap is now disabled; the stage/activate row below describes the frozen
implementation's historical requirements, not current authorization. Both the
isolated issuer's signed preflight validation and the Publisher's live
App checks require exact permission dictionaries; missing, additional or unknown
fields fail closed. The independent Verifier App and its token remain unchanged.

| Operation/mode | Required Publisher App registration | Requested Publisher token |
| --- | --- | --- |
| Acceptance-only, including S4 bootstrap acceptance | Baseline only | None; Publisher skipped |
| Live bootstrap stage or activate | Baseline plus Workflows Write | Baseline plus Workflows Write |
| Ordinary publish or recover | Baseline only | Baseline only |

Baseline is Contents Write, Actions Read, Administration Read and automatic
Metadata Read. The temporary exception to the original baseline-permissions
assumption changes no signed authority, bypass list, policy or historical bytes.
The existing `bootstrap_operation: stage` / `activate` controls remain mandatory.
Ordinary publication fails closed while the App registration is elevated.

GitHub [documents Workflows Write for release targets with workflow differences](https://docs.github.com/en/rest/releases/releases#create-a-release).
The unchanged pinned token action explicitly requests Contents Write and
Actions/Administration Read, and requests Workflows Write only for `bootstrap`.
Its [pinned input parser](https://github.com/actions/create-github-app-token/blob/fee1f7d63c2ff003460e3d139729b119787bc349/lib/get-permissions-from-inputs.js)
ignores the empty workflows input for publish/recover; the three other explicit
permission inputs prevent inheritance of all App permissions. Its pinned bundled
`dist/main.cjs` contains the same parser. The repository is always explicitly
`benchristian88/atlas-connectors`; automatic token revocation remains enabled.

Registration alone is insufficient: GitHub must grant Workflows Write to the
installation before it can [mint the explicitly requested token](https://docs.github.com/en/rest/apps/apps#create-an-installation-access-token-for-an-app).
Mint failure stops the job, with no ordinary-token fallback or continued writes.
Local tests do not prove the installation's real approval or a successful release.

## S4 deployment and mandatory rollback — owner actions only

S4 acceptance, staging, separate exact-pointer approval, immutable activation and
owner removal of Publisher Workflows Write are complete. The production evidence
above records the actual release, unchanged assets, root, digests and rollback
verification. This closure disables bootstrap while retaining approved pins and
ordinary publication/recovery. The existing root/fence also prevent rebootstrap.

Remaining operator actions:

1. Review and merge this closure policy through protected main with successful
   `validate` CI. No bootstrap dispatch is required or authorized by this closure.
2. Independently check the installed Publisher App's effective baseline access.
   Run **39913094643** verified App registration only and skipped Publisher;
   it did not exercise an installation token or normal publication/recovery.
3. Complete independent Atlas consumer verification, explicit consumer root approval,
   implementation and genuine acceptance using the [consumer handoff](consumer-handoff.md).
   Producer activation grants no Atlas trust or package eligibility.
4. Preserve the retired GET-only diagnostic's unchanged
   [historical fixture](../../tests/fixtures/historical_workflows/diagnose-catalogue-publisher.yml)
   and regression coverage. It is no longer an active Actions entry point.

Keep Contents Write, Actions/Administration/Metadata Read and Workflows **No access**
as the Publisher baseline. Token revocation alone is not a permissions rollback.
Preserve partial-operation evidence and investigate failures before any fresh
normal dispatch or reviewed recovery decision. Never use **Re-run jobs**, change
the historical target, bypass the signed preflight or force-update protected history.
No settings, secrets, releases, refs or workflow runs are changed by this closure.

The committed trust pins these verified ruleset identities:

| Ruleset | ID |
| --- | --- |
| atlas-main | 25618213 |
| atlas-history-lock | 25618809 |
| atlas-bootstrap-lock | 25628137 |
| atlas-catalogue-current | 25618684 |
| atlas-publication-tags | 25618901 |

## Minimum genuine signing/isolation acceptance

S4's genuine signing acceptance is complete in run 39893809663 above, with
Publisher skipped and baseline Publisher App permissions. For a future frozen
implementation, keep the Publisher App at its exact baseline permissions and
perform **one manual dispatch** of
`catalogue-publish.yml`, branch **main**, **operation publish**, and
**acceptance_only true**; bootstrap remains disabled. Record actual C and require C != S.
This is the default safe mode. The Publisher job must be skipped entirely. Its
key and token action must never run; no catalogue assets or refs may be written.
The isolated verifier uses real credentials to observe protections and signs only
public preflight evidence. No production acceptance flag is needed for this mode.
Only attempt one is permitted; do not use **Re-run jobs**. This task does not
perform the dispatch.

Before accepting a future implementation, independently review:

- Exact executed S, checked-out S and caller C; no caller code or downloads in
  the Verifier job, no inherited secrets, and only the issuer step receives its key.
- The two public one-day artifact files `preflight.json` and
  `preflight.sigstore.json`; no credential-bearing outputs, logs or artifacts.
- Genuine offline gh/roots verification: exact production workflow/predicate/
  subject, signer digest S, source/buildConfig digest C, GitHub issuer and hosted
  runner, original run/attempt one and verified trusted transparency evidence.
- Signed actual policy digest, operation publish, acceptance-only true, exact
  human/Apps, required CI, both environments, all five complete rulesets/bypass
  lists and release immutability. Cross-check these against independent provider reads.
- Signing timing and the remaining 15-minute startup budget. Measure actual
  cross-job download/admission during controlled staging. Local synthetic
  verified-output tests and the earlier C/S experiment are not this evidence.

Preserve public evidence before retention expires. Wrong/missing claims, failed
signing, unexpected isolation, unavailable complete configuration or an unexpected
Publisher job blocks acceptance. Do not broaden permissions or bypass checks to pass.
S4's genuine review is recorded in the unchanged committed accepted trust. Before
normal publication/recovery, reconfirm matching independent environment trust. Future frozen
implementations need their own genuine review and separate approval; local tests
are not live acceptance evidence.
This task performs no merge, environment update or workflow dispatch.

## Bootstrap in two publication dispatches

The following is the completed historical procedure, not authorization to repeat
bootstrap. Current `bootstrap_operation: disabled` rejects staging and activation.

1. **Stage — completed:** run **39896288128**, attempt **1**, used the reviewed
   `bootstrap_operation: stage` policy with both root pins null. A fresh signed
   preflight passed before Publisher token creation. P2 authenticated the original
   10,585 catalogue bytes and attestation, checked complete draft-visible inventory,
   staged a newly signed pointer, sealed the draft and stopped without publication.
2. **Approve actual pointer — completed:** a later protected-main policy source
   approved sequence **1** and the actual staged pointer SHA-256 above, with
   `bootstrap_operation: activate`. Approval was separate in time/source/run by
   the same sole human; it did not imply independent second-person approval.
3. **Activate — completed:** fresh run **39912401767** revalidated original bytes,
   approved pointer and fresh preflight; it finalized the immutable snapshot before
   creating the protected bootstrap-root marker and parentless current root.
   The owner verified the exact root, files, refs and unchanged four assets.
4. **Close — prepared here:** Workflows Write was removed and baseline registration
   verification passed in run **39913094643**. Disable bootstrap while retaining
   approved pins; consumer acceptance and installed effective-access verification
   remain separate outstanding work.

The [detailed P2 procedure](bootstrap.md) governs conflicts, bounded recovery and
exact historical identities. Legacy Proxmox **0.2.0 remains ineligible** for secure
remote installation because its package release is mutable. Bootstrap grants no
package eligibility and does not change Atlas consumer trust automatically.

## Routine publish and recover after accepted bootstrap

Review registry changes, increment sequence once, merge through protected main/CI,
and run catalogue preparation to obtain genuine catalogue provenance at C. Dispatch
**publish, acceptance_only false** from that main commit. The single preflight
admits startup; P1 still verifies packages, bytes, complete predecessor/history
bindings, immutable release identity and non-force current CAS. Ordinary catalogue
changes advance C without updating S. Never rerun a signed publication attempt.

If an immutable immediate successor exists but current was not advanced, dispatch
**recover, acceptance_only false** from current reviewed main. Recovery authenticates
original snapshot/pointer bytes and their old invocation; it does not rebuild them
at the newer source or repair a mutable draft. Stage partial drafts with a fresh
matching-source publish dispatch only; bootstrap staging is disabled. Conflicts, changed policy,
stale evidence, incomplete inventory, mutable publication, missing history or an
ambiguous write require investigation and a fresh reviewed dispatch. No automatic
ref/release deletion, forced update or authorization fallback exists.

A signature authorizes startup, not continuous protections or atomic later writes.
The Publisher rechecks visible protections/state; complete hidden bypass evidence
remains the startup snapshot. Review the explicit [race and credential limitations](../../docs/signed-publication-verifier.md#freshness-later-validation-and-explicit-trade-offs).

## Phase 4B package finalization — separate human authorization required

**Prepared locally; no new package release, tag, attestation or catalogue has been
published by this increment.** The patch version **0.2.1** gives the unchanged
qualified implementation a new historical distribution identity. Explicit
`release_overrides` in `connectors/proxmox/package.json` select only versioned
Manifest, SPDX identity, README and qualification limits; default 0.2.0 and `.6`
archives retain their original bytes. `build_bundle.py --version 0.2.1` uses the
same reviewed file list and USTAR/gzip construction. No tests, fixtures, candidate
paths, release-preparation tooling or operator evidence enter the archive.

The 0.2.1 Manifest preserves AIP 1.0, SDK >=1.1.0/<2.0.0, Atlas >=0.1.0/<1.0.0,
runtime capability integration-runtime-v1 and baseline >=1.2.0/<2.0.0, and the exact
community.proxmox 2.0.0 digest/licence. No dependency is upgraded. The retained
source qualification is for unchanged behavior against **9.2.11**, not complete
live acceptance of the new artifact. Its packaged qualification document states
that distinction and retains authentication-secret and native-systemd live gaps.

### Local preparation and review

Use the existing pinned SDK, development dependencies and reviewed test collection.
The workflow still uses Python 3.12 and the same pinned actions. This increment
adds no execution dependency. From the feature working tree:

```bash
python tools/release_connector.py --local --tag proxmox-v0.2.1 --output dist/proxmox-0.2.1-review
python tools/build_bundle.py --version 0.2.1 --output dist/proxmox-0.2.1-repeat
cmp dist/proxmox-0.2.1-review/proxmox-0.2.1.tar.gz dist/proxmox-0.2.1-repeat/proxmox-0.2.1.tar.gz
```

`--local` grants no signing/publication authority. Its detached source HEAD is
contextual while edits are uncommitted. The production tag workflow does not use
that mode: it requires clean exact committed source, matching tag, official
repository/owner/hosted-runner context, first attempt and configured App actor.
It rejects an already registered identity before emitting release files. Before
attestation it validates the full SDK Manifest, stable version, recorded source
qualification, supported SDK/runtime, bounded regular USTAR members, embedded
Manifest agreement, SPDX identity/dependencies and licence/notice paths. Every
consumed package file must be tracked. The historical base source and recipe remain
reviewed inputs; version overlays do not silently promote a new source version.

### Controlled operator ceremony after review, CI and merge

These steps are a **design for the existing scoped-App operator procedure**,
not a newly authorized workflow. There is no automated package finalizer, token
minting CLI, credential override, PAT path or package-specific S4 authorization.
The following ceremony must be separately authorized and performed by the owner.
If the existing credential custody/approved operator path cannot perform it,
publication is blocked pending a separately reviewed mechanism. Do not extract
an environment key into a laptop, add a new secret location, dispatch catalogue
publication as a substitute, or widen permissions to get past that boundary.

1. Review the branch, commit/push through the normal PR process, obtain green
   `validate` CI, and merge into protected `main`. Record exact reviewed source
   **C**, tag **T = proxmox-v0.2.1**, package name **proxmox-0.2.1.tar.gz** and
   expected SHA-256 **D** from independent clean builds. C is not the uncommitted
   preparation HEAD. Record owner acceptance of qualification inheritance; repeat
   Test Connection and unchanged COMPLETE discovery with the exact final artifact
   before claiming new-artifact live acceptance.
2. Independently reconfirm repository/owner, maintainer, both environments,
   complete rulesets/bypasses and existing App/installation identities listed
   above. Confirm the installed Publisher has only its existing baseline scope
   for this repository, and `GET /immutable-releases` reports enabled. This is a
   prerequisite, not proof of final immutability. The baseline effective
   installation permissions still require operator confirmation. Keep Workflows
   **No access**. A permissions failure requires investigation and separate review;
   the historical temporary bootstrap elevation is not permission to repeat it.
3. Separately authorize **create-only** T at C through the configured Publisher
   App, not a human-pushed tag. Confirm T does not exist and no release with T
   exists, including drafts. The App creates `refs/tags/T` at exact C; never
   retarget/delete a pre-existing tag. This must trigger a fresh **attempt-one**
   `release.yml` push run **R**, whose original and triggering actors are the
   configured App bot. A tag build establishes provenance, not human publication
   approval. Do not use Re-run jobs to repair its identity.
4. The workflow prepares/tests the package, attests the exact archive and retains
   `immutable-connector-release-candidate` with exactly **five** files:
   archive, `manifest.json`, `index.json`, `SHA256SUMS`, `package.sigstore.json`.
   The fifth file is the unchanged pinned `actions/attest` bundle output, verified
   offline against C/T/D/R before upload. It is not a new signature profile.
   Historical 0.2.0 retains its original four assets. Retain the artifact promptly;
   Actions artifact availability is not an immutable archive guarantee.
5. Obtain those exact candidate bytes into `dist/release` in a clean checkout at
   C, with this reviewed verifier implementation and its pinned gh/roots. Run the
   read-only prepublication verification, replacing the explicit reviewed values:

   ```bash
   python tools/verify_connector_release.py --candidate-only --directory dist/release --tag proxmox-v0.2.1 --source-commit C --expected-digest D --run-id R
   ```

   This independently verifies the signature, exact source/tag/digest/run binding,
   completed successful original run and attempt one, both App actors, official
   workflow/repository, source CI/main ancestry and package environment/tag policy.
   Missing public observations fail closed with no credential fallback. The result
   is `authenticated_build_candidate_not_publication_authority`; CI success alone
   is insufficient. Signature verification uses the approved release.yml package
   profile, never a decoded JSON assertion or checksum-only fallback.
6. Through the existing approved App operator path, create a **draft** release
   for existing T with `target_commitish: C`, `prerelease: false` and
   `make_latest: false`. Upload exactly the five verified files without rebuilding,
   reserializing or modifying them. Record release ID **L**, package asset ID **A**
   and every asset's name/ID/size/provider digest. Independently retrieve all staged
   bytes through that authorized draft-visible path and compare with the verified
   candidate. Require App author/uploader identities, exact C/T and no extra assets.
   Draft state and matching checksums do not establish immutable publication.
7. The maintainer explicitly approves **C/T/D/R/L/A and all five asset identities**
   after inspecting the staged bytes and provenance. Preserve that approval in the
   operator's release record. Save the approved asset inventory separately from the
   five candidate files as `dist/approved-assets.json` (or outside the checkout): an object keyed by exact asset
   name, each value containing exactly `id` (positive integer), `sha256` (64 lowercase
   hex characters without prefix), and `bytes` (integer size). Include all five
   files and their distinct staged IDs. Verify this inventory against the downloaded
   staged bytes before approval; never derive it from final-release observations.
   The final verifier requires it and rejects a changed ID even when bytes match.
   It is an explicit operator authorization record, not an
   independently signed human proof or a portable S4 grant. Using the same approved
   App path, finalize only L (`draft: false`, `make_latest: false`). Do not set an
   invented `immutable` input or infer success from the PATCH response.
8. Independently GET L and the T release, resolve T to C, and require **actual
   `immutable: true`, `draft: false`, `prerelease: false`**. GitHub documents
   [draft, attach, publish](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
   for immutable releases. Immutability locks assets/tag; title, notes and
   prerelease state can still change, so continue checking actual state.
   Run the anonymous, GET-only verifier:

   ```bash
   python tools/verify_connector_release.py --directory dist/release --tag proxmox-v0.2.1 --source-commit C --expected-digest D --run-id R --release-id L --asset-id A --approved-assets dist/approved-assets.json
   ```

   It repeats build authentication, checks exact App release/asset actors and all
   five IDs/filenames/digests/bytes, retrieves the assets independently and rereads
   release/asset/tag state. Only successful verification emits
   `immutable_package_verified_catalogue_pending`, with the full validated Manifest,
   build invocation, release ID and asset inventory. Save original bytes/bundle,
   exact command/expected values, observed API records, approval and receipt.
   The receipt is a report, not signed publication authority. Public App metadata
   corroborates registration, not historical/effective token permissions or
   uninterrupted protection. Simulated provider tests prove neither real
   immutability nor new cryptographic acceptance.

### Failure, retry and acceptance

A missing/invalid signature, changed source, wrong actor, rerun, incompatible
Manifest, unsafe archive, missing qualification, draft/prerelease/mutable final
release, wrong asset or ambiguous response blocks acceptance. Do not emit a trusted
handoff or change catalogue state. The read-only verifier never repairs publication.
If a write response is lost, independently reread exact L/T/assets first; do not
blindly retry create/upload/finalize. Partial draft recovery requires fresh operator
review and exact same C/T/D/R/L/existing asset IDs and bytes. Only missing expected
assets may be added, with original verified bytes and existing App authority.
Conflicting assets are not deleted/replaced by this procedure. An already published
immutable release may be reverified unchanged; missing/conflicting immutable assets
require a new version or separate incident decision. A mutable final release fails;
never repair it by reattesting, retagging or overwriting historical bytes.
A failed/rerun tag build requires investigation and a separately reviewed new
release identity, not a manual unsigned substitute. Preserve all failed-state
observations and approval history.

**Published Release PASS** requires separate owner authorization, genuine C/T/D/R
package signature acceptance, provider L/A/asset evidence with immutable true,
exact-byte independent retrieval and explicit final-artifact qualification
acceptance. None is claimed for 0.2.1 by local preparation. Historical 0.2.0 remains
at source `456a5bfdd1398c19da9ffef29216029027e24278`, archive SHA-256
`a14fec5ab485c980688ff5907e8835ddd3e9cecd1a6989ef252cbcb1b1dc4ef8`, release
`416290807`, asset `652745908`, mutable and remotely ineligible.

### Phase 4C handoff boundary

The verifier's proposed `registry_entry` has exactly the existing four fields:
`status`, `release_tag`, `release_asset_id`, full `manifest`. Release ID, all asset
names/IDs/digests, source, original build bundle/run and current package verification
status are retained in separate evidence. No IDs are invented and no registry entry
is written during preparation. Do not copy a local unattested Manifest into it.

Future catalogue sequence 2 needs separate publication authorization and a reviewed
stronger **public immutable publication-evidence archival contract**, including
exact genuine signed preflight/bundle and policy bytes with context/historical
verification rules independently approved by Atlas. The frozen S4 implementation
and four-asset catalogue inventory are not modified here to supply that contract.
Atlas ADR 0013 accepts only the exact original sequence-one bootstrap; the broader
ADR 0012 design is still Proposed. Sequence-one's missing historical bypass
exception never authorizes a future sequence, even one referring to sequence one.
Atlas dev's exact sequence-one ingestion/read-only metadata does not enable remote
package installation. Do not publish sequence 2 or update `catalogue-current` here.

The next catalogue change must retain the exact 0.2.0 entry/identity as history.
Under P1 every **active** package must pass immutability checks: an explicit reviewed
withdrawal of mutable 0.2.0 is therefore needed before advancement can succeed.
Do not omit it or silently reinterpret it as remotely installable. Preserve the
original sequence/root/pointer/policy, sticky withdrawals and prior immutable
versions for permitted rollback. No Atlas/SDK/store/runtime/consumer trust changes
are made by Phase 4B.
