# Official catalogue publication — Lean V2 operator runbook

**Production activation is blocked.** The current policy remains stage-enabled,
with no approved root digest; verifier trust is unaccepted and its real pins are
unset. The current workflow implementation literals refer to pre-V2
`da5562eeb21d5c1cc653cfea7ae8d025d2a9174a` as an inert safety lock. No live operation
was performed by local implementation. Do not dispatch until the pinning steps below.

The [security contract](../../docs/signed-publication-verifier.md) and
[ADR 0005](../../docs/decisions/0005-lean-run-preflight.md) define the one-preflight
design. [Historical configuration tables](publication-v1-reference.md), the
[consumer handoff](consumer-handoff.md) and detailed [P2 bootstrap rules](bootstrap.md)
remain reference material; the current workflow and runbook take precedence over
old per-transition grants and disabled-policy descriptions.

## Configure and freeze once

1. Review the V2 implementation and freeze it in commit **S**. In a separate
   protected-main commit **C**, pin the reusable workflow call, Publisher executable
   checkout and `ATLAS_IMPLEMENTATION_REVISION` to that exact full SHA. Never use
   a moving branch/tag, a local reusable call, latest-main lookup or an invented SHA.
   Update the explicit pin regression assertion in the same review. The source
   checkout remains C and is read only as catalogue/policy/trust data.
2. Independently verify repository **1414494920**, owner/human maintainer
   **93822871**; Publisher App/installation **5422372 / 174027755**, bot **346232650**;
   Verifier App/installation **5424851 / 174088125**. Preserve the existing App
   permissions: Publisher Contents Write, Actions/Administration/Metadata Read;
   Verifier Administration Write, Contents/Actions/Checks/Metadata Read. Both
   installations must be selected for exactly this repository.
3. Check protected main and all five active repository rulesets, complete bypass
   arrays, exact environment IDs/ref restrictions, no required reviewers/admin
   bypass, required successful `validate` CI, and release immutability. Keep the
   Verifier out of all bypass lists. The Publisher alone bypasses current-update
   and publication-tag rules; main, history-lock and bootstrap-lock have no bypass.
   See the [configuration tables](publication-v1-reference.md#operator-configuration--do-not-execute-publication-yet)
   and [bootstrap fence](bootstrap.md#configuration-checklist-and-authority).
4. Fill the real S, five ruleset IDs and verification environment ID in
   `catalogue/publication/verifier-trust.json` at C and its independently administered
   `VERIFICATION_POLICY` environment variable in `catalogue-verification`. Keep
   `live_signer_accepted: false` in both. The maximum startup age is 900 seconds;
   do not extend it to accommodate stalled runs. Store each App key only in its
   own existing environment, never a caller input or inherited secret.

## Minimum genuine signing/isolation acceptance

After the above review, the owner may separately authorize one fresh dispatch of
`catalogue-publish.yml` from main with **operation bootstrap, acceptance_only true**.
This is the default safe mode. The Publisher job must be skipped entirely. Its
key and token action must never run; no catalogue assets or refs may be written.
The isolated verifier uses real credentials to observe protections and signs only
public preflight evidence. No production acceptance flag is needed for this mode.

Before accepting the implementation, independently review:

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
After review, separately approve identical real trust with `live_signer_accepted:
true` in both locations. This task performs none of these owner actions.

## Bootstrap in two publication dispatches

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
