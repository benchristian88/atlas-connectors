# Official catalogue publication — Lean V2 operator runbook

**Provider-side sequence-1 bootstrap is completed; immutable catalogue publication is active.**
The closure policy sets `bootstrap_operation: disabled`, preserving `enabled: true`,
single-maintainer authorization, all IDs and the approved sequence/pointer pins.
Normal `publish` and `recover` remain available subject to existing signed preflight,
package, contiguous sequence, predecessor, immutable-release and history checks.
Independent Atlas consumer verification and acceptance remain outstanding; this
completion does not establish Atlas B3 remote-installation readiness.

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
