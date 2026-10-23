# Sequence-one bootstrap operator runbook

Status: **P2 machinery retained under Lean V2; production activation and live P2 acceptance remain blocked**.
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

The checked-in policy currently has `enabled: true`, `bootstrap_operation: stage`,
and null `bootstrap.sequence` / `bootstrap.pointer_sha256`. V2 verifier trust pins
S3 with `live_signer_accepted: true` after genuine acceptance run **39887360792**,
which skipped Publisher. Bootstrap staging remains uncompleted.
S3 adds sanitized HTTP diagnostics for the unresolved staging failure in run
**39880692187**. Successful GET-only run **39883753194** did not test release creation.
After this approval merges, the owner must update `VERIFICATION_POLICY` to match
the committed accepted trust JSON, then use a new controlled staging dispatch to
observe the actual Publisher HTTP result; see the [current operator runbook](README.md).
S3 diagnostics change neither publication authority nor permissions. Actual pointer
approval remains a separate owner action. No real target release ID, asset ID, pointer
digest, selection signature or root commit exists as a result of this task.

Configured identities are maintainer **93822871**, publication environment
**24999137498**, package environment **24617213627**, App **5422372** /
`atlas-catalogue-publisher`, installation **174027755**, bot **346232650**.
They are reviewed source-policy inputs, not claims read from catalogue content.
They are configured locally; current live validity/protections are not established
by this implementation. Both dispatch actors must be the configured human.

Before any live dispatch, the owner must review and validate:

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

## Exact future procedure — owner actions, not performed here

1. **Source validation (offline).** With the pinned SDK/verifier installed, run
   `python tools/publish_catalogue.py bootstrap-preflight`. This supports the
   current stage-enabled configuration as well as disabled policy, authenticates real original evidence and
   prints sanitized JSON. It makes no GitHub requests or writes. It does not prove
   live protections, legacy release identity or empty history. The workflow's
   read-only remote preflight performs those checks with the scoped App after
   dispatch authorization; all remote checks must succeed before its first write.
2. **Approve historical identity and staging.** Review the table above, P1 settings,
   new fence rule and ADR. Through the human-controlled protected-main process,
   set `enabled: true`, `bootstrap_operation: stage`, leaving both bootstrap pins
   null. Wait for exact-source successful validate CI. This authorizes only draft
   staging; normal publish/recover still cannot initialize a channel.
3. **Live draft staging.** The configured maintainer manually dispatches
   `catalogue-publish.yml` on main with the sole input `operation=bootstrap`.
   Attempt 1 only. The workflow validates policy/App ID and independent dispatch
   records before minting its scoped App token. It verifies source offline before
   that token, then repeats complete P1 authority/settings and legacy/history
   checks before writes. The draft targets the historical source SHA, not the
   dispatch SHA. Its deterministic operation body allows exact-byte recovery.
4. **Genuine selection evidence and approval checkpoint.** GitHub assigns the real
   release and snapshot asset IDs. The workflow writes the seven-field canonical
   pointer with sequence 1 and null predecessor, then uses the pinned existing
   `actions/attest` in catalogue-publish.yml to attest `current.json`. It verifies
   the pointer signature and original dispatch, stages the fourth asset and reads
   back all four. The run ends with `staged_requires_separate_approval` in the
   `catalogue-publication-receipt` artifact. **The release is still a draft; there
   is no current ref.** Preserve the exact files and inspect them independently
   using the pinned verifier, release/asset IDs, original source and public signing
   run/attempt/actor/workflow/CI evidence. Compute SHA-256 over actual canonical
   `current.json` bytes. Do not use the catalogue digest as the pointer digest.
5. **Separate trust activation approval.** Through a later protected-main policy
   change, set `bootstrap.sequence: 1`, `bootstrap.pointer_sha256` to that exact
   verified pointer digest, and `bootstrap_operation: activate`. This later commit
   must differ from the authenticated selection-signing source. Wait for CI and
   dispatch a **new** `operation=bootstrap` run on main; never rerun the old run.
   No release IDs, URLs, digests, source refs or signers are workflow inputs.
6. **Immutable finalisation.** Activation obtains the existing fully staged release
   from complete bounded provider inventory, reauthenticates both signatures and
   checks the approved digest, fresh dispatch and protections. It publishes with
   `make_latest=false` and requires non-draft/non-prerelease, `immutable: true`,
   exact tag/source, unchanged four asset IDs and exact original bytes. A mutable
   result stops; no branch is created. Activation does not repair incomplete drafts.
7. **Root creation and rechecks.** Only after those checks does it create a Git tree
   containing exactly the pointer/bundle, create a parentless commit, and verify
   its tree/blob identities. After renewed authority checks it creates the protected
   root-intent tag, then creates `catalogue-current` at that SHA using POST only.
   It verifies root, current, fence, exact files and immutable evidence again. No
   forced update, existing-ref overwrite, deletion or ordinary-publish fallback exists.
8. **Acceptance receipt and consumer trust approval.** Preserve the sanitized receipt:
   catalogue identity, original signer/source/bundle, actual release and all asset
   IDs, pointer digest, root SHA, selection signer/run/source, activation run/source,
   observed published/immutable state and explicit legacy warning. A receipt is
   diagnostic evidence, not Atlas authorization. Independently implement/review
   the [consumer handoff](consumer-handoff.md), approve its own root digest and
   policy identities, and demonstrate live acceptance before claiming P2 complete.
9. **Close bootstrap and advance normally.** Set `bootstrap_operation: disabled`
   through reviewed source while retaining the approved root pins. The provider
   fence and existing current already terminate bootstrap authority regardless of
   this cleanup. Future manual publish/recover dispatches automatically enforce
   contiguous sequence and predecessor validation; there is no scheduled publisher.
   P1 still checks every active package. To advance past legacy mutable Proxmox,
   deliberately retain its full identity as a withdrawn entry in a later catalogue
   and publish a new qualified immutable version through the generic package path.
10. **Legacy restriction.** Sequence-one trust never makes Proxmox 0.2.0 remotely
    installable. Do not replace its Manifest, digest, tag, package or asset ID, or
    create a vendor-specific eligibility exception. Atlas B3 remains separate.

## State transitions and interruption handling

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
