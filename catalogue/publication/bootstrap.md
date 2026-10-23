# Sequence-one bootstrap operator runbook

Status: **Provider-side sequence-1 bootstrap completed; bootstrap operation disabled;
immutable catalogue publication active.** Independent Atlas consumer verification
and acceptance remain outstanding; Atlas B3 remote installation is not ready.
See [production evidence and remaining operator actions](README.md#s4-deployment-and-mandatory-rollback--owner-actions-only).
Every publication dispatch first needs the [Lean V2 preflight and acceptance gates](README.md). Acceptance-only signing never executes the Publisher job.
The [bootstrap ADR](../../docs/decisions/0003-sequence-one-bootstrap.md) records the
new two-dispatch approval boundary and one-time fence. The [P1 runbook](README.md)
remains authoritative for identities, protections, signing profiles and transport.
The [completion record](bootstrap-report.md) separates local tests from live evidence.

## Fixed historical identity

| Property | Pinned value |
| --- | --- |
| Repository / owner | benchristian88/atlas-connectors / benchristian88 |
| Numeric repository / owner | 1414494920 / 93822871 |
| Legacy release / tag | 416561696 / catalogue-v1 |
| Original assets | catalogue.json: 653915685; catalogue-000001.json: 653915743 |
| Original bytes / schema / sequence | 10,585 / 1.0 / 1 |
| Catalogue SHA-256 | 55533ca67e7e9a14f82961e0a8c34ad78e2596049b3db02fde787494e3975afd |
| Source commit | 91dfd86f18d0b59ff977bb1e8a5fef42c5329943 |
| Build signer | .github/workflows/catalogue.yml@refs/heads/main |
| Original attestation reference | 57152061 |
| Original bundle SHA-256 | 0a404de77a6c47dc2f08e3acecf835a01313e924f6883a4b13d720c57610f72f |

Reference 57152061 identifies the captured original evidence. The production
verifier authenticates the pinned original bundle itself; it does not trust that
reference number as proof. Legacy public release identity, both exact assets and
tag source are independently checked. No package is downloaded or executed by
bootstrap; the six-field catalogue and complete embedded Manifest stay unchanged.

## Configuration checklist and authority

The closure policy has `enabled: true`, `bootstrap_operation: disabled`,
`bootstrap.sequence: 1` and exactly
`bootstrap.pointer_sha256: a275f63d0ac818a193826478328ee324be62353addc5c97a2ed0a28d217b5372`.
All IDs and approved pins are retained. New bootstrap staging/activation is rejected;
normal `publish` and `recover` remain authorized subject to existing checks, with
no alternative initialization when current is missing. V2 verifier trust still pins
S4 (`2dd1ffcd2f5677dc35bdbc8f68ea28275c91c285`) with `live_signer_accepted: true`.

Genuine staging run **39896288128**, from
`8ce0b80c74d6ceb8ce75ac7ec8693f5bba78b305`, returned
`staged_requires_separate_approval`. Activation run **39912401767**, from
`51f8693fbcca1e4c6c9615662bca368839ea0757`, returned `bootstrapped`,
`published: true`, `immutable: true`. The owner verified published immutable
`catalogue-000001` (**421426993**), all four unchanged assets and parentless root
`a1597730687be993d766ddb465a0d3362aef2d02`. Both `refs/heads/catalogue-current`
and `refs/tags/catalogue-bootstrap-root` resolve to that root, containing exactly
`current.json` and `current.sigstore.json`. Catalogue SHA-256 remains
`55533ca67e7e9a14f82961e0a8c34ad78e2596049b3db02fde787494e3975afd`.
See the [full production evidence table](README.md) for all original asset IDs.
Earlier POST failures and S3/S4 signer acceptance remain historical evidence in
that runbook; they are not current activation blockers.

The owner removed temporary Publisher Workflows Write. Genuine first-attempt
acceptance-only run **39913094643** passed preflight/verify with Publisher skipped,
confirming **App registration** baseline: Contents Write, Actions Read,
Administration Read, Metadata Read, Workflows **No access**. It did not independently
test installed effective access. Verifier App permissions are unchanged. Ordinary
publish/recover use only baseline permissions and a fresh signed preflight; the
frozen historical elevated bootstrap profile is no longer authorized by policy.

Configured identities are maintainer **93822871**, publication environment
**24999137498**, package environment **24617213627**, App **5422372** /
`atlas-catalogue-publisher`, installation **174027755**, bot **346232650**.
They are reviewed source-policy inputs, not claims read from catalogue content.
The completed runs supply the owner-verified production evidence above, not a
claim that protections remain continuously unchanged. Both dispatch actors must
be the configured human.

Historical bootstrap prerequisites (retained for audit; bootstrap is now disabled):

- All four existing P1 rulesets, immutable-release capability, protected-main
  required PR/validate CI, exact environment/ref restrictions, no environment
  reviewers/admin bypass, App permissions and installation scope.
- New active repository ruleset `atlas-bootstrap-lock`: target `tag`, include
  exactly `refs/tags/catalogue-bootstrap-root`, no excludes, rules `update` and
  `deletion`, **no bypass actors**. App creation is permitted only by the existing
  `atlas-publication-tags` App bypass. Do not add `creation` to this no-bypass rule.
- No current ref, no root-intent fence, no conflicting catalogue history, and
  correct pinned legacy bytes/source. A missing consumer database does not grant
  publication bootstrap authority. A previously removed branch requires review.
- The staging and activation policy revisions, all workflow changes, and a later
  independent Atlas consumer trust decision. No self-approval or fake identity
  substitutes for the explicit single-maintainer policy.

## Completed two-dispatch procedure (historical)

These steps record the completed procedure; they do not authorize another bootstrap.

1. **Source validation (offline).** The original stage/activate policies supported
   `python tools/publish_catalogue.py bootstrap-preflight`, authenticating frozen
   original evidence without GitHub requests or writes. Frozen S4's offline disabled
   mode expects null pins; the closed policy deliberately retains approved pins and
   that command now rejects it with `bootstrap_staging_pins_must_be_unset`. This
   bootstrap-only diagnostic limitation does not block normal publish/recover.
   Do not clear pins or change executable code to bypass it. Remote preflight
   separately checked live protections, legacy identity and empty history before writes.
2. **Approve historical identity and staging — completed.** Review the table above, P1 settings,
   new fence rule and ADR were reviewed through the human-controlled protected-main
   process. The staging policy set `enabled: true`, `bootstrap_operation: stage`,
   leaving both bootstrap pins null, with successful exact-source validate CI.
   That policy authorized only draft staging; normal publish/recover cannot initialize a channel.
3. **Live draft staging — completed in run 39896288128, attempt 1.** The configured maintainer manually dispatched
   `catalogue-publish.yml` on main with `operation=bootstrap`, `acceptance_only=false`.
   Attempt 1 only. The workflow validates policy/App ID and independent dispatch
   records before minting its bootstrap-only Workflows Write App token, requiring
   installation approval with no ordinary-token fallback. It verifies source offline before
   that token, then repeats complete P1 authority/settings and legacy/history
   checks before writes. The draft targets the historical source SHA, not the
   dispatch SHA. Its deterministic operation body allows exact-byte recovery.
4. **Genuine selection evidence and approval checkpoint — completed and verified.** GitHub assigns the real
   release and snapshot asset IDs. The workflow writes the seven-field canonical
   pointer with sequence 1 and null predecessor, then uses the pinned existing
   `actions/attest` in catalogue-publish.yml to attest `current.json`. It verifies
   the pointer signature and original dispatch, stages the fourth asset and reads
   back all four. The run ends with `staged_requires_separate_approval` in the
   `catalogue-publication-receipt` artifact. **At that staging checkpoint the release
   was a draft and there was no current ref; activation has since completed.**
   Preserve the exact files and inspect them independently
   using the pinned verifier, release/asset IDs, original source and public signing
   run/attempt/actor/workflow/CI evidence. Compute SHA-256 over actual canonical
   `current.json` bytes. Do not use the catalogue digest as the pointer digest.
5. **Separate trust activation approval — completed.** Through a later protected-main policy
   change, set `bootstrap.sequence: 1`, `bootstrap.pointer_sha256` to that exact
   verified pointer digest, and `bootstrap_operation: activate`. This later commit
   must differ from the authenticated selection-signing source. Wait for CI and
   dispatch a **new** `operation=bootstrap` run on main; never rerun the old run.
   No release IDs, URLs, digests, source refs or signers are workflow inputs.
6. **Immutable finalisation — completed in run 39912401767.** Activation obtains the existing fully staged release
   from complete bounded provider inventory, reauthenticates both signatures and
   checks the approved digest, fresh dispatch and protections. It publishes with
   `make_latest=false` and requires non-draft/non-prerelease, `immutable: true`,
   exact tag/source, unchanged four asset IDs and exact original bytes. A mutable
   result stops; no branch is created. Activation does not repair incomplete drafts.
7. **Root creation and rechecks — completed.** Only after those checks does it create a Git tree
   containing exactly the pointer/bundle, create a parentless commit, and verify
   its tree/blob identities. After renewed authority checks it creates the protected
   root-intent tag, then creates `catalogue-current` at that SHA using POST only.
   It verifies root, current, fence, exact files and immutable evidence again. No
   forced update, existing-ref overwrite, deletion or ordinary-publish fallback exists.
8. **Activation receipt and owner verification — completed.** Preserve the sanitized receipt:
   catalogue identity, original signer/source/bundle, actual release and all asset
   IDs, pointer digest, root SHA, selection signer/run/source, activation run/source,
   observed published/immutable state and explicit legacy warning. A receipt is
   diagnostic evidence, not Atlas authorization. Independently verify the immutable
   release, parentless root, current branch, fence and exact files before cleanup.
9. **Close bootstrap and complete consumer acceptance.** Workflows Write removal
   and baseline App-registration verification completed in run **39913094643**;
   installed effective-access verification remains outstanding. This separately
   reviewed closure sets `bootstrap_operation: disabled`, retaining approved pins.
   The existing current and fence already terminate bootstrap authority. Independent
   Atlas consumer verification, root approval, implementation and live acceptance
   remain outstanding. Future authorized manual publish/recover dispatches enforce
   contiguous sequence and predecessor validation; there is no scheduled publisher.
   To advance past mutable Proxmox, deliberately retain its full identity as a
   withdrawn entry in a later catalogue and include a new qualified immutable
   version through generic package gates. No package exception is introduced.
10. **Legacy restriction.** Sequence-one trust never makes Proxmox 0.2.0 remotely
    installable. Do not replace its Manifest, digest, tag, package or asset ID, or
    create a vendor-specific eligibility exception. Atlas B3 remains separate.

## State transitions and interruption handling

The table below preserves historical interruption handling while stage/activate
were separately authorized. The closed policy rejects every new bootstrap dispatch;
these rows do not reopen authority or permit retrying completed initialization.
Normal publish/recover retain their existing authorization and recovery checks.

Each API write is a distinct provider transaction. There is no claim of a distributed
atomic release/ref transaction. The shared workflow concurrency group serializes
normal operations; create-only refs, strict inventory, immutable identity and the
root-intent fence reject conflicts. Transport writes are never blindly retried.
Use fresh manual dispatches, not rerun attempts, after inspecting sanitized errors.

| Observed state or interruption | Permitted action |
| --- | --- |
| Disabled/unconfigured, wrong actor/App, failed CI, settings missing | No writes; repair through reviewed operator process |
| Before draft creation, or ambiguous draft-create response | Fresh stage dispatch lists drafts before deciding to create |
| Partial original upload, pointer missing, signing interrupted | Fresh stage dispatch verifies every existing byte and adds only missing assets |
| Main advanced during staging | Current run stops at authority recheck; a fresh stage dispatch can preserve historical source and exact existing files |
| Complete signed draft | Stop for separate digest approval; same-byte stage retries preserve existing genuine bundle |
| Wrong source/bundle/Manifest, extra assets, conflicting draft/release/tag, duplicate draft, inventory overflow | Stop; no overwrite/delete/second identity |
| Finalisation failed or response lost | Fresh activate dispatch inspects release; finalises only an exact draft, or verifies the exact already immutable release |
| Immutable release but neither current nor fence exists | Fresh activate dispatch reauthenticates original selection, approved digest and immutable bytes, then creates root |
| Fence exists but current absent (including lost fence response) | Bootstrap authority consumed; separate reviewed incident/recovery decision required; no automatic branch recreation |
| Current create response lost | Same invocation inspects exact current/root/fence without repeating POST; exact match can return success |
| Current exists on a later request, even if exact | Stop; independently inspect evidence, never reinitialize |
| Root has parent/extra files or competing current appears | Stop; no force update or repair |
| Rate limit, permission failure, unavailable approval/run evidence | Stop without granting trust; inspect state before fresh dispatch |
| Consumer checkpoint lost | Consumer recovery decision; never rerun publisher bootstrap |

No automated fence recovery is supplied. Current settings and the protected fence
cannot defeat an administrator who removes all provider evidence/protections; that
case needs an independent audit. No tool action can infer safe global freshness
from absence alone.

## Test and live-evidence boundary

`test_publication_bootstrap.py` models provider state and selection binding with
explicitly labelled synthetic signatures. `test_publication_crypto.py` invokes
actual hash-pinned gh 2.102.1 and frozen roots for real original catalogue/package
evidence, rejects cross-profile use and tampered evidence, and performs the genuine
offline source preflight. There is no genuine new selection fixture. Workflow/CLI
routing is exercised deterministically without triggering Actions. Ansible tests
exercise fixture-only packages, not live bootstrap or Proxmox installation.
