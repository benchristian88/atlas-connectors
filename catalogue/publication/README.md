# Official catalogue publication — Lean V2 operator runbook

**S4 is pinned for signing acceptance, but remains unaccepted; live publication is blocked.**
Bootstrap staging and activation remain incomplete. The current policy remains
stage-enabled, with no approved root digest. Reviewed implementation
**S = S4 = `2dd1ffcd2f5677dc35bdbc8f68ea28275c91c285`** was merged through
[PR #30](https://github.com/benchristian88/atlas-connectors/pull/30) and is frozen.
Committed trust has `live_signer_accepted: false`. S4 adds temporary bootstrap-only
Workflows Write support and preserves S3's sanitized HTTP diagnostics.
Caller/source **C** advances independently and must differ from S. Genuine S4
signing acceptance has not completed; S3 acceptance does not accept S4. This
adoption performs no live operation or GitHub environment change.

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
motivates the temporary profile below; its success still needs live verification.
The HTTP 403 remains unresolved.

The [security contract](../../docs/signed-publication-verifier.md) and
[ADR 0005](../../docs/decisions/0005-lean-run-preflight.md) define the one-preflight
design. [Historical configuration tables](publication-v1-reference.md), the
[consumer handoff](consumer-handoff.md) and detailed [P2 bootstrap rules](bootstrap.md)
remain reference material; the current workflow and runbook take precedence over
old per-transition grants and disabled-policy descriptions.

## Configured pins and next operator action

1. The reviewed V2 implementation is frozen at S above. The reusable workflow
   call, Publisher executable checkout and `ATLAS_IMPLEMENTATION_REVISION` all
   pin that exact full S4 SHA. Merge this adoption through protected main and green
   CI to establish a separate advancing caller C. Keep the source checkout
   at `${{ github.sha }}`; it advances independently and is read only as
   catalogue/policy/trust data. Never replace executable S with a moving branch,
   tag, local reusable call or latest-main lookup.
2. Independently verify repository **1414494920**, owner/human maintainer
   **93822871**; Publisher App/installation **5422372 / 174027755**, bot **346232650**;
   Verifier App/installation **5424851 / 174088125**. Preserve the existing App
   baseline permissions: Publisher Contents Write, Actions/Administration/Metadata Read;
   Verifier Administration Write, Contents/Actions/Checks/Metadata Read. Both
   installations must be selected for exactly this repository. Do not enable
   Workflows Write until genuine S4 acceptance and subsequent separate approval.
3. Check protected main and all five active repository rulesets, complete bypass
   arrays, exact environment IDs/ref restrictions, no required reviewers/admin
   bypass, required successful `validate` CI, and release immutability. Keep the
   Verifier out of all bypass lists. The Publisher alone bypasses current-update
   and publication-tag rules; main, history-lock and bootstrap-lock have no bypass.
   See the [configuration tables](publication-v1-reference.md#operator-configuration--do-not-execute-publication-yet)
   and [bootstrap fence](bootstrap.md#configuration-checklist-and-authority).
4. **After this adoption merges, next operator action:** update the GitHub environment variable
   `VERIFICATION_POLICY` in environment **catalogue-verification** with JSON
   identical to the committed [verifier-trust.json](verifier-trust.json). Copy the
   complete file verbatim, preserving `live_signer_accepted: false`. A later true
   flag requires genuine review and separate approval; do not set
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

## Temporary historical-bootstrap permission profile

Both the isolated issuer's signed preflight validation and the Publisher's live
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

The implementation merge and freezing below are complete. This task prepares only
the separate adoption; remaining deployment actions are not performed here.

1. **Complete:** the reviewed implementation merged through PR #30.
2. **Complete:** its frozen implementation **S4** is
   `2dd1ffcd2f5677dc35bdbc8f68ea28275c91c285`.
3. Review and merge this separate adoption of all three executable workflow pins
   and trust `signer_revision` at S4, with `live_signer_accepted: false`. Caller C
   advances independently and must differ from S4.
4. Update `catalogue-verification`'s `VERIFICATION_POLICY` to that exact unaccepted
   trust JSON, preserving all other trust values.
5. With the Publisher App still at baseline, perform one fresh protected-main
   `catalogue-publish.yml`, `operation: bootstrap`, `acceptance_only: true`
   dispatch. Review genuine S4 signing/isolation evidence; require Publisher skipped.
6. Separately approve S4 through protected main, then synchronize
   `VERIFICATION_POLICY` to the complete accepted trust JSON.
7. Add **Workflows: Read and write** to Publisher App **5422372** and approve the
   permission change on existing installation **174027755**, selected for this
   repository only. Do not change the Verifier App, keys or bypass permissions.
8. Independently verify exact App/installation identity, single-repository scope
   and the complete elevated permission profile before attempting a write.
9. With reviewed policy still `bootstrap_operation: stage` and root pins null,
   dispatch a fresh protected-main **bootstrap, acceptance_only false**, attempt 1.
   It must obtain its own signed authorization and explicitly elevated token.
10. Inspect the real draft release, exact historical assets, signatures, receipt
    and actual pointer digest. If staging fails, investigate the sanitized HTTP
    evidence and any legitimate partial draft before considering another attempt.
11. Separately approve the actual staged pointer digest through protected main,
    set `bootstrap_operation: activate`, and execute a new first-attempt bootstrap
    dispatch. Revalidate immutability, root/fence protections and exact current root.
12. Immediately after successful activation, remove Workflows Write from the
    Publisher App registration; do not leave a Workflows Read permission behind.
13. Verify removal from both App and installation. Disable bootstrap through
    reviewed policy (`bootstrap_operation: disabled`, retaining the approved root
    pins), and verify normal publication uses only the exact baseline profile.
14. Remove the temporary GET-only diagnostic workflow in a separate reviewed
    cleanup PR.

GitHub App elevation has no automatic expiry. Explicit rollback and independent
verification are mandatory; token revocation alone does not remove App permissions.
On staging failure, do not automatically revoke or alter App/installation
permissions or delete a partial draft. Preserve evidence and investigate before
any new attempt or reviewed recovery decision. Never use **Re-run jobs**, change
the historical target, bypass the signed preflight or force-update protected history.

The committed trust pins these verified ruleset identities:

| Ruleset | ID |
| --- | --- |
| atlas-main | 25618213 |
| atlas-history-lock | 25618809 |
| atlas-bootstrap-lock | 25628137 |
| atlas-catalogue-current | 25618684 |
| atlas-publication-tags | 25618901 |

## Minimum genuine signing/isolation acceptance

S3's acceptance above remains historical evidence. S4 has not completed genuine
signing acceptance. After this adoption merges and the environment trust matches,
keep the Publisher App at its exact baseline permissions and perform **one manual dispatch** of
`catalogue-publish.yml`, branch **main**, **operation bootstrap**, and
**acceptance_only true**. Record actual C and require C != S.
This is the default safe mode. The Publisher job must be skipped entirely. Its
key and token action must never run; no catalogue assets or refs may be written.
The isolated verifier uses real credentials to observe protections and signs only
public preflight evidence. No production acceptance flag is needed for this mode.
Only attempt one is permitted; do not use **Re-run jobs**. This task does not
perform the dispatch.

Before accepting S4, independently review:

- Exact executed S, checked-out S and caller C; no caller code or downloads in
  the Verifier job, no inherited secrets, and only the issuer step receives its key.
- The two public one-day artifact files `preflight.json` and
  `preflight.sigstore.json`; no credential-bearing outputs, logs or artifacts.
- Genuine offline gh/roots verification: exact production workflow/predicate/
  subject, signer digest S, source/buildConfig digest C, GitHub issuer and hosted
  runner, original run/attempt one and verified trusted transparency evidence.
- Signed actual policy digest, operation bootstrap, acceptance-only true, exact
  human/Apps, required CI, both environments, all five complete rulesets/bypass
  lists and release immutability. Cross-check these against independent provider reads.
- Signing timing and the remaining 15-minute startup budget. Measure actual
  cross-job download/admission during controlled staging. Local synthetic
  verified-output tests and the earlier C/S experiment are not this evidence.

Preserve public evidence before retention expires. Wrong/missing claims, failed
signing, unexpected isolation, unavailable complete configuration or an unexpected
Publisher job blocks acceptance. Do not broaden permissions or bypass checks to pass.
Keep both S4 trust copies unaccepted until its genuine baseline-permission review
succeeds and separate protected-main approval is merged. Then synchronize the
environment trust. Do not enable Workflows Write before that separate approval.
This task performs no merge, environment update or workflow dispatch.

## Bootstrap in two publication dispatches

The next staging attempt remains gated on S4 adoption, genuine acceptance,
matching approved trust and the exact elevated bootstrap permission profile above.

1. **Stage:** with current policy `bootstrap_operation: stage` and both root pins
   null, dispatch **bootstrap, acceptance_only false** from reviewed main. A fresh
   signed preflight must pass before Publisher token creation. P2 authenticates
   the exact original 10,585 catalogue bytes and original attestation, checks
   complete draft-visible inventory, resumes matching partial drafts and stages
   a newly signed pointer. This is also controlled live acceptance of artifact
   download, startup admission, Publisher scope and actual draft visibility. Review
   those boundaries before activation. It seals the draft and stops without finalization,
   root marker or current ref. Download and inspect the receipt and actual assets.
2. **Approve actual pointer:** independently verify that staged pointer's signature,
   original invocation, exact release/asset IDs and digest. Review a separate policy
   PR setting `bootstrap_operation: activate`, `bootstrap.sequence: 1` and the
   **actual staged pointer SHA-256**. Do not substitute the catalogue digest or
   fabricate IDs. This approval is separate in time/source/run, by the same sole
   human; it does not imply independent second-person approval.
3. **Activate:** after the approval merge and CI, dispatch a fresh **bootstrap,
   acceptance_only false** run. It gets a new run-level preflight, revalidates
   original bytes and the approved pointer, finalizes and verifies the immutable
   snapshot, then creates the protected bootstrap-root marker and true current
   root. Independently verify exact root files/parentlessness and consumer anchor.
   A lost/ambiguous root write requires the existing explicit review procedure;
   never delete the fence, force-update current or blindly retry.

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
matching-source publish/bootstrap-stage dispatch only. Conflicts, changed policy,
stale evidence, incomplete inventory, mutable publication, missing history or an
ambiguous write require investigation and a fresh reviewed dispatch. No automatic
ref/release deletion, forced update or authorization fallback exists.

A signature authorizes startup, not continuous protections or atomic later writes.
The Publisher rechecks visible protections/state; complete hidden bypass evidence
remains the startup snapshot. Review the explicit [race and credential limitations](../../docs/signed-publication-verifier.md#freshness-later-validation-and-explicit-trade-offs).
