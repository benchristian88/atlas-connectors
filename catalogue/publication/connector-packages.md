# Controlled Connector package publication

Phase 4B.6 prepares human review of committed trust activation for qualified
package S4 `dc79af8e3115e263c267989dfa9ba72599c25463` (PR #44). Phase 4B.5 already
repinned all four bindings from S3 `be24042c4e7446c7d88d2f08608ab7f058bb24b6`.
Genuine S4 acceptance qualification has **passed**. This proposal changes only
committed package trust's `enabled` and `live_signer_accepted` from false to true;
the immutable signer revision, schema, five ruleset IDs, observation age and
verification environment remain exact. No workflow bytes or bindings change.

**The live `CONNECTOR_VERIFICATION_POLICY` still has both flags false.** This is
an intentional temporary mismatch with the proposed committed true/true profile;
no live settings are changed here. **No publication dispatch is permitted during
the mismatch.** Independent trust equality remains mandatory and fails closed.
The owner has disabled the independent `CONNECTOR_PUBLICATION_ENABLED` gate;
keep it disabled until separately authorized. Acceptance qualification, committed
trust review, live trust activation, the enable gate and individual release
operations are distinct approval boundaries.

## Current owner decision and historical 0.2.1

The owner has abandoned automated recovery of incomplete Proxmox 0.2.1. It will
remain **unpublished and untouched**, preserving these historical identities:

| Historical evidence | Identity |
| --- | --- |
| Protected tag / original Tag run | `proxmox-v0.2.1` / `41017433479` |
| Original source P | `d3f66b039e2027832be932cacd006d86442821ec` |
| Original signed successful build / artifact | `41017538114` / `12960302111` |
| Original ZIP SHA-256 | `e941e8108791d7d0bdaea7716eeccb5cfce0dd77440cc1b81faf77b414084602` |
| Original package SHA-256 | `96eaa736c2919e56e09b9613dddd8648ad1f43b77679899ab706261b2a38e509` |
| Incomplete draft / uploaded checksum asset | `428740362` / `691270692` |
| Checksum bytes / SHA-256 | 87 / `20f5c6f473a4908a97790e979baf0cf16f46532a6180325abc0f2cf18d71ab3f` |

These objects are historical evidence, **not valid catalogue publication
authority**. Do not resume, publish, delete, replace, retag or otherwise mutate
them. No interaction with that draft is required for this task or the new rollout.
The next candidate will be **Proxmox 0.2.2**, prepared from new reviewed source in
a later PR; this task does not create it or change version metadata.

[ADR 0007](../../docs/decisions/0007-post-tag-staging-recovery.md)'s proposed
workflow-mismatch relaxation is **rejected** and retained as design history.
[ADR 0006](../../docs/decisions/0006-connector-package-publication.md) remains in
force: the entire workflow directory at package source P must equal current caller
C for **every Tag, Stage and Finalize**, including an approved existing draft or
already-published identity. A reviewed pin-only change is still a mismatch.
Source review, ancestry, required CI and all original identity controls remain.
No Workflows Write expansion or conditional permission bypass is authorized.

## Qualified S4, proposed trust activation and future clean release

The [implementation report](../../docs/phase-4b4-draft-staging-recovery.md) preserves
the engine handoff; the [repinning A–J report](../../docs/phase-4b5-s4-repinning.md)
records historical disabled qualification preparation. The
[activation preparation A–J report](../../docs/phase-4b6-s4-activation-preparation.md)
records the current proposal and remaining approvals. Package **S4** below means exact
`dc79af8e3115e263c267989dfa9ba72599c25463`, distinct from frozen **catalogue S4**
`2dd1ffcd2f5677dc35bdbc8f68ea28275c91c285`. No action below is authorized by
repinning or implementation review alone.

1. **Completed genuine S4 qualification:** original run **41138855610**, attempt
   **1**, artifact **13018405524**, GitHub attestation **61962326**, caller C
   `af213a948a7d19aeaccf623c06e093f75a9e228b`. Genuine offline Fulcio, Sigstore and
   Rekor verification and all five complete signed ruleset/security checks passed;
   Publisher was skipped before its environment/key/token steps. Original evidence
   and the qualification report are archived outside the repository at
   `~/Atlas-evidence/s4-acceptance-41138855610`. This is completed historical
   qualification, not current admission, package-source/build qualification or
   publication authorization. Do not replay its expired signed preflight.
2. **Proposed committed trust activation:** review this separate PR's two boolean
   changes, tests and documentation; require hosted Python 3.12 `validate` CI and
   security review before merge. Retain exact S4 and all other trust fields and
   workflow bytes. Never substitute S3, catalogue S4 or a mutable ref.
3. **Separately controlled live trust activation:** after reviewed merge, obtain
   explicit owner approval to update repository `CONNECTOR_VERIFICATION_POLICY`
   to the complete matching committed profile. Independently check effective
   repository/environment configuration and absent or identical overrides, fresh
   protections and existing key custody. This task grants no such authority and
   changes no live variable. No publication dispatch is permitted while live
   false/false trust differs from the proposed committed true/true profile.
4. **Independent publication-enable gate:** keep `CONNECTOR_PUBLICATION_ENABLED`
   disabled. Opening it requires its own owner authorization after live trust and
   controls are reviewed; neither genuine acceptance nor true/true trust enables
   it. Retain baseline App permissions, including Workflows No access, the split
   credential boundary and fresh signed admission for each future operation.
5. **Future release authority:** neither this preparation nor later configuration
   approval authorizes a package release. The remaining steps require separate
   owner review and explicit operation approvals.
6. Prepare Proxmox **0.2.2 metadata/source in a subsequent reviewed PR**, after S4
   merge/repinning. Preserve all 0.2.1 evidence and existing discovery/dependencies.
7. Qualify 0.2.2 at its exact reviewed merge source **P**, retain successful required
   CI/main ancestry and reproduce the exact package digest **D** twice with trusted
   S4 tools reading P as data. Record advancing current caller **C** independently.
8. Confirm P's **entire workflow directory equals C's** before Tag, Stage and
   Finalize. Recheck live controls at each operation. If later caller changes break
   equality, stop for separately reviewed source/release selection; do not grant
   Workflows Write, roll workflows back, retarget or invoke the rejected exception.
9. Separately authorize and execute **Tag**, then inspect the original successful
   signed build/attempt/artifact and exact ZIP digest; separately authorize **Stage**
   of its five original files and stop; obtain another explicit human approval for
   **Finalize**, binding the successful Stage and complete exact asset inventory.
10. Independently authenticate the final tagged asset URLs, original bytes/signature,
    approved numeric identities and actual `immutable: true` release before **any
    catalogue update**. Catalogue publication/sequence/consumer authority remains
    a separate reviewed boundary with its frozen publisher unchanged.

## Draft asset verification and normal recovery

The admitted Publisher authenticates the official repository and numeric release
identity. A permitted opaque `untagged-…` selector is derived only from that exact
release's authenticated `html_url`, with matching numeric `assets_url`; never from
an asset URL. Final tagged draft URLs are also accepted. Browser URLs are validated
metadata and are never followed. The numeric asset API download permits one
restricted GitHub distribution redirect, without forwarded credentials, cookies,
ambient proxies or further redirects. Name, uploader, ID, state, size, mandatory
SHA-256 and exact original bytes remain required. Missing/conflicting metadata
fails closed. The independent anonymous final verifier requires final tagged URLs.

Normal Stage creates a draft and uploads all five originals. An explicitly
approved partial draft can resume **only with valid P/C workflow equality** and
an exact approved release ID/partial asset inventory. Verify and preserve existing
assets; upload only missing originals. Unexpected/substituted assets reject without
replacement. Every ambiguous write stops for review and is never retried
automatically. Stage never authorizes Finalize; separate human approval and actual
immutable final verification remain mandatory.

## Historical S3 qualification context

The S/S2/S3 qualification, activation preparation and evidence records below are
retained history. Their 0.2.1 examples are superseded by the owner decision above;
they do not authorize resuming 0.2.1 or reactivating S3. The shared controls and
symbolic request/recovery contracts remain applicable to future clean releases.

## Reused controls and new mechanisms

The unchanged `release.yml` remains package build/attestation authority. Trusted
implementation S reuses deterministic builders, qualified release selection,
archive/SPDX checks, original-bundle verification, existing complete ruleset
validation, pinned gh 2.102.1/frozen roots and the final GET-only verifier. The
catalogue authority validator is reused through a narrow path adapter: the actual
package workflow path is checked before adapting only its path for common
actor/CI/environment/repository validation. No catalogue run or signature is
accepted as package authority. The frozen S4 implementation and trust are unchanged.

New `connector-publish.yml` dispatches exactly one of `tag`, `stage`, `finalize`.
`acceptance_only` defaults true. Its separate Publisher job condition includes
`!inputs.acceptance_only`, successful preflight and repository variable
`CONNECTOR_PUBLICATION_ENABLED == 'true'`. The job cannot start or receive its
step-scoped Publisher key during acceptance. All package and catalogue writes
share the existing non-canceling `official-catalogue-publication` concurrency group.

`connector-verifier.yml` is an isolated SHA-pinned reusable workflow. Only its
Verifier key is explicitly forwarded; secrets are never inherited. It observes
complete ruleset/bypass data with the existing Verifier identity. Its only exports
are `connector-preflight.json` and the original Sigstore bundle. The distinct
schema/predicate, exact subject digest, independent signer S, caller C, original
run/attempt, request digest, actual producer-policy bytes, independent package
trust and complete observations are verified offline before Publisher credentials
are minted. Startup is at most 900 seconds from earliest observation; same-job
readmission is at most 1,800 seconds, with signature rechecks at every mutation
boundary. Acceptance-only evidence is never write authorization.

The `package` dispatch input is bounded JSON data, at most 16 KiB after canonical
serialization. No URL, executable reference or arbitrary command is accepted.
The package source checkout, selected by validated full SHA, is read as data by S;
none of its Python, requirements, workflows or Connector playbooks is executed.
Source metadata is compared against the exact original artifact before any key
use; final asset bytes are never reserialized, rebuilt or re-signed for publication.

## Failed acceptance and corrected workflow identity

Genuine [run 40523236413, attempt 1](https://github.com/benchristian88/atlas-connectors/actions/runs/40523236413),
[job 122255725484](https://github.com/benchristian88/atlas-connectors/actions/runs/40523236413/job/122255725484),
failed at `Require independently configured package signer before checkout or credentials`
with `connector_verification_trust_not_accepted`. Caller C was
`b2fcc15ce06b5b57ae3b3c7ecf6264bcd1d168f0`, implementation S was
`d6601ad97815a85da164e4329766ea17b62bddc9`, operation was `tag`, acceptance-only
was true and the proposal was Proxmox 0.2.1. The supplied genuine job context was:

```text
workflow_ref: benchristian88/atlas-connectors/.github/workflows/connector-verifier.yml@d6601ad97815a85da164e4329766ea17b62bddc9
workflow_sha: d6601ad97815a85da164e4329766ea17b62bddc9
workflow_repository: benchristian88/atlas-connectors
workflow_file_path: .github/workflows/connector-verifier.yml
```

The inline guard incorrectly required the reusable reference to end in
`@refs/heads/main`. Read-only original-attempt job metadata confirms checkout,
observation, attestation and upload were skipped; Publisher had no runner or
steps. No Publisher token, tag, release, original build or signed preflight was
created. The exact guard rejection is evidence of failed acceptance, not signer
acceptance or publication authority.

The corrected contract uses the independently configured package trust revision,
never the request's package source or an operator-supplied executable reference:

| Identity surface | Exact requirement |
| --- | --- |
| `github.workflow_ref` / `GITHUB_WORKFLOW_REF` | `benchristian88/atlas-connectors/.github/workflows/connector-publish.yml@refs/heads/main`; caller/source digest C remains separate |
| `job.workflow_ref` | `benchristian88/atlas-connectors/.github/workflows/connector-verifier.yml@` plus the complete trusted `signer_revision` |
| `job.workflow_sha` | Exactly that same independently configured revision |
| `job.workflow_repository` / `job.workflow_file_path` | Exactly `benchristian88/atlas-connectors` / `.github/workflows/connector-verifier.yml` |
| Guard output / `VERIFIER_WORKFLOW_REF` | That identical SHA-pinned reusable reference, checked again before Verifier credentials |

For the prepared S3 configuration the sole accepted job reference is
`benchristian88/atlas-connectors/.github/workflows/connector-verifier.yml@be24042c4e7446c7d88d2f08608ab7f058bb24b6`,
with `job.workflow_sha` exactly `be24042c4e7446c7d88d2f08608ab7f058bb24b6`.
The historical S context above is preserved as failed-run evidence and is rejected
under S3 trust, as is the genuine historical S2 identity. Main refs, tags,
wrong paths/repositories, inconsistent reference/digest pairs and a consistent
but untrusted SHA pair reject. The approved schema, strict Boolean security flags,
disabled-trust rejection, acceptance-only Publisher exclusion and first-attempt/main/
actor requirements remain enforced. The downstream preflight main-ref check is
also corrected: once the guard exports its pinned reference, its old exact
main-ref equality would otherwise reject before credential use. This second
mismatch is established by code; the failed run did not reach it.

**Genuine S2 certificate representation is now observed.** Original S never signed;
S2 run `40534608937` did. Its SAN and `buildSignerURI` both end in
`@c2b4ecb493160f0226b1724aa688d0f436d51489`. The correction requires each identity
to equal the full official repository/workflow URI plus the exact independently
trusted immutable SHA, and still requires `buildSignerDigest` to equal that SHA.
Caller `buildConfigURI` / `buildConfigDigest` remain bound to the publication
workflow at main / C. No branch identity, suffix matching or alternate profile is
accepted. The report separates authenticated bundle claims from the unavailable
original subject contents and unobserved hosted CLI exit status. Original S3
acceptance subsequently succeeded; the activation review above records
the current independent evidence and its archival limits.

## Historical S2 rollout — superseded by the S3 correction cycle

PR #40 merged S2 repinning at caller C
`c7299f9375ccf401c0cf69cb9022dc76a3556b48`; the owner subsequently ran the failing
S2 acceptance described above. The following sequence records the earlier S2
plan. Its pending steps are historical, not instructions to dispatch S2 again.

Original S and its historical evidence are immutable. PR #39's qualified correction
is merged at exact S2 `c2b4ecb493160f0226b1724aa688d0f436d51489`.
The sequence is:

1. **Completed correction:** PR #39 fixed the reusable job reference and downstream
   preflight check. Its local qualification is historical evidence, not genuine
   signing acceptance.
2. **Local S2 pinning:** this separate change sets the reusable `uses`, Publisher
   executable checkout, `ATLAS_IMPLEMENTATION_REVISION` and package trust
   `signer_revision` to exact S2. Tests and future evidence examples follow S2;
   trusted executable files and failed S evidence stay unchanged.
3. **Pending human PR:** commit/push, open the pinning PR, complete security review
   and required Python 3.12 CI, then merge. The advancing caller C is not S2 by
   definition; inspect all four literal bindings in the committed caller.
4. **Pending owner configuration, after pinning merge and before dispatch:** update
   the existing repository Actions variable `CONNECTOR_VERIFICATION_POLICY` to the
   complete JSON from the newly committed `catalogue/publication/connector-trust.json`.
   Keep `enabled` and `live_signer_accepted` false. Independently verify absent or
   identical environment overrides and an absent/false effective
   `CONNECTOR_PUBLICATION_ENABLED`, including organization inheritance.
5. **Pending separately authorized acceptance:** establish exact reviewed P and
   independently reproduce D as below, then perform a new original main
   acceptance-only run with Publisher skipped. Never rerun the failed run as
   acceptance. Preserve C/S2 and all genuine certificate/signature/isolation evidence
   before considering any separate activation decision.

## Historical S3 rollout — superseded activation sequence

PR #41 established exact S3 `be24042c4e7446c7d88d2f08608ab7f058bb24b6`;
PR #42 repinned reusable `uses`, Publisher executable checkout,
`ATLAS_IMPLEMENTATION_REVISION` and independent `signer_revision`. All six reviewed
S3 executable files remain frozen. The owner configured disabled S3 trust and
performed original acceptance run `40542954614`, attempt one, with Publisher skipped.
The unchanged genuine S2 fixtures and synthetic S3 unit tests retain their separate
meanings; actual S3 evidence is described in the activation review.

The following sequence records the historical S3 activation plan. It is
superseded by the clean S4/0.2.2 rollout above and must not be executed for 0.2.1:

1. Retain the **30 October 2026 owner acceptance** of ADR 0006's split permission
   boundary and existing residual risks. Retain the completed original-archive
   verification below and its outputs with the owner's preserved evidence before
   activation review; architecture acceptance does not authorize activation. Any new requirement for
   an independent effective-permission witness inside signed pre-token admission
   needs a separately reviewed design. Do not expand permissions or move/share keys.
2. Record exact merged caller **C**, green required CI and all four unchanged S3
   bindings. Keep the effective `CONNECTOR_PUBLICATION_ENABLED` absent/false while
   reviewing/configuring trust. Ensure no publication is running or queued before
   any owner-authorized configuration change.
3. Set the existing **repository Actions variable** `CONNECTOR_VERIFICATION_POLICY`
   to the complete JSON from C's `connector-trust.json` (true/true, exact S3 and
   unchanged controls). Prefer no same-name variable in either publication or
   verification environment. Any retained copy must parse identically to C and
   the repository value. Leave the original catalogue `VERIFICATION_POLICY` alone.
4. Independently reread repository and both environment variables, applicable
   inheritance, protected-main environment restrictions, App registration/installed
   scope, key custody and complete ruleset/bypass observations. Do not reveal keys
   or mint a Publisher token just to inspect configuration. Confirm effective
   evaluation at both the Publisher's job-level `env` and Verifier's step-level
   `env`; mismatch or unavailable evidence is a stop condition. Fresh live
   controls are required for each operation; the old acceptance is not replayable.
5. Only after a **separate explicit owner authorization to activate the live gate**,
   set repository `CONNECTOR_PUBLICATION_ENABLED` to literal `true` as the final
   configuration change. Reread its effective value, exact policy and overrides;
   confirm C/S3/CI and controls still match. This enables eligible manual requests;
   it does not authorize or dispatch one. An environment-only value cannot open
   this job-level gate. If verification fails, keep/return the gate to literal
   `false` and investigate. Disabling prevents new Publisher starts; it does not
   cancel an already running job or undo remote writes.
6. Reconfirm package **P/T/D** independently of advancing C. The qualified proposal
   is P `d3f66b039e2027832be932cacd006d86442821ec`, T `proxmox-v0.2.1`, D
   `96eaa736c2919e56e09b9613dddd8648ad1f43b77679899ab706261b2a38e509`.
   Local reproduction is evidence, not approval. Require P's merged PR, successful
   CI, clean source, qualification and workflow directory equality with C. This
   activation changes no workflow, so it can retain P without a new engine pin.
7. Obtain **separate tag authorization** for exact P/T/D and a fresh original main
   dispatch with `operation: tag`, `acceptance_only: false`. Recheck tag absence;
   the admitted Publisher additionally checks drafts. Stop after the verified tag.
   Inspect the resulting unchanged `release.yml` original build, attestation and
   exact artifact ID/ZIP digest. Do not rebuild or substitute its published bytes.
8. Obtain **separate stage authorization** binding that original build/artifact and
   P/T/D. Inspect the draft's five original assets and retain L/A, every asset
   ID/digest/size, canonical inventory digest and staging run ID. Stage stops at
   `staged_requires_separate_approval`; its receipt is not finalize authority.
9. Obtain **separate finalize authorization** of C/P/T/D/R/L/A, staging run and all
   five asset identities. Use a fresh original dispatch, never a rerun or inferred
   approval from current provider state. Require the independent anonymous GET-only
   verifier to confirm exact assets and `immutable: true` after publication. An
   ambiguous write requires read-only investigation, never a blind retry, deletion,
   replacement or retag. Catalogue sequence two and remote installation remain
   separately governed.

**Architecture acceptance and prepared trust are not live enablement or publication authority.**
A new original acceptance-only run is needed only if separately required by owner
review or a changed baseline; never rerun the old acceptance to obtain authority.

## Administration prerequisites — owner verification required

Historical read-only preparation inspected repository Actions Variables on
30 October 2026 (Pacific/Auckland): `CONNECTOR_VERIFICATION_POLICY` matches main's disabled S3
trust; `CONNECTOR_PUBLICATION_ENABLED` is absent. The complete environment-variable
list contains only the existing App IDs/install ID and catalogue `VERIFICATION_POLICY`,
with no package-policy or enable-gate overrides. The repository belongs to an
ordinary user, so organization-variable inheritance does not apply. This is a
point-in-time observation, not a continuing guarantee of effective configuration.

For this 31 October Phase 4B.6 preparation, the owner reports live package trust
false/false and publication disabled. Those settings are left untouched and are
not freshly queried here. The proposed committed true/true profile intentionally
differs until separately approved owner configuration; no publication dispatch
is permitted during the mismatch. The genuine S4 qualification snapshot is
historical evidence, not a fresh verification of future live controls.

Earlier environment/main-protection observations remain historical. Before any
future dispatch, the owner must freshly verify that protected-branch deployment
restrictions select only main, all protections/bypass arrays and App scopes remain
correct, and secret custody is intact without reading or moving any key. This
increment changes no live settings, catalogue trust, App permissions or protections.

| Control | Exact required configuration |
| --- | --- |
| Repository / owner | `benchristian88/atlas-connectors`, IDs `1414494920` / `93822871`, public |
| Human | Original and triggering ordinary user `benchristian88`, ID `93822871`; manual main dispatch, attempt one |
| Publisher | App `5422372`, slug `atlas-catalogue-publisher`, installation `174027755`, bot `346232650` |
| Publisher permissions | Contents Write; Actions, Administration, Metadata Read; Workflows No access; token restricted to repository `1414494920` |
| Verifier | App `5424851`, installation `174088125`; Administration Write; Contents, Actions, Checks, Metadata Read; one-repository token |
| Publisher environment | Existing `catalogue-publication`, ID `24999137498`; protected branches only, no required reviewers, admin bypass false |
| Verifier environment | Existing `catalogue-verification`, ID `25016263801`; same main deployment restrictions; isolated existing key custody |
| Build environment | Existing `connector-release`, ID `24617213627`; admin bypass false, no reviewers, exactly one custom tag policy `*-v*` |
| Rulesets | Main `25618213`, history `25618809`, bootstrap `25628137`, current `25618684`, publication tags `25618901`; complete exact bypass arrays required |
| Source protection | Existing PR requirement, zero required approvals, stale-review dismissal, last-push approval false, strict `validate` from Actions App `15368`, no main bypass, no force push/deletion |
| Package tag policy | Existing creation/update/deletion protection for `refs/tags/*-v*`; only Publisher Integration bypass; no Verifier bypass |
| Immutability | Repository immutable releases enabled; actual final release must separately report `immutable: true` |

Use existing `PUBLICATION_APP_PRIVATE_KEY` and `VERIFICATION_APP_PRIVATE_KEY`
in their existing environments, with existing App ID variables. Do not read,
copy, move or create keys/secrets to make this procedure work. Confirm availability
and custody administratively. If the existing caller forwarding/environment design
cannot supply the key, stop for a separate custody decision.

The Verifier observes Publisher **registration**, its approved identity and exact
expected permission profile. After authenticated admission and package preparation,
`mint_publisher` JWT-authenticates App `5422372` and installation `174027755`, checks
exact registered and installed permissions, selected-repository installation and
unsuspended state, requests only repository `1414494920` and the exact baseline
permissions, checks the issued permissions and GETs the token's one-repository
scope. A missing, additional or contradictory grant rejects before the client is
returned to any tag/release/upload operation. Admission and visible controls are
rechecked at mutation boundaries; the authentication transport allows only App/
installation GETs and the single fixed token-mint POST.

**Publisher installation permissions are independently validated by the admitted
Publisher before writes; they are not included as independently observed effective
permissions in the Verifier's signed pre-token admission.** The owner accepted
this split as the least-privilege boundary on **30 October 2026**, subject to
remaining evidence verification and live security checks, acknowledging the
existing documented residual risks. Acceptance does not give the Verifier
independent knowledge of the Publisher's effective grant. ADR 0006 architecture
acceptance and live activation are separate decisions.
No Verifier permission expansion, Publisher credential sharing or secret move is
part of this design. Local tests do not verify live installed scope, key custody,
or uninterrupted hidden bypass configuration.

Provider references: [ref creation permissions](https://docs.github.com/en/rest/git/refs#create-a-reference),
[release creation and conditional Workflows permissions](https://docs.github.com/en/rest/releases/releases#create-a-release),
[draft release visibility](https://docs.github.com/en/rest/releases/releases#list-releases),
[Actions artifact retrieval](https://docs.github.com/en/rest/actions/artifacts#download-an-artifact)
and [immutable release preparation](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases).
Package S4 requires the package source workflow directory to equal current main
for Tag, Stage and Finalize;
there is no post-tag repin exception. Never resolve a mismatch through permission
elevation. Provider-selected Actions download redirects are HTTPS-only
to Azure blob or Actions artifact hosts, without forwarded credentials, further
redirects, ambient proxies or operator-supplied URLs. Original ZIP SHA-256 and size
must match the independently approved artifact identity and run metadata.

## Independent configuration and historical baselines

Original S was `d6601ad97815a85da164e4329766ea17b62bddc9`; S2 was
`c2b4ecb493160f0226b1724aa688d0f436d51489`. Their failed acceptance records above
remain historical. All four current bindings select qualified package S4
`dc79af8e3115e263c267989dfa9ba72599c25463`; this proposal changes only its two
committed trust flags. Advancing caller **C**, trusted executable
**S** and package-source **P** remain distinct identities;
a commit becoming main does not become executable authority.

Use the repository policy variable as the common source. The Publisher captures
`${{ vars.CONNECTOR_VERIFICATION_POLICY }}` in **job-level `env`**, while the
reusable Verifier reads it in **step-level `env`** after entering
`catalogue-verification`. Environment-only configuration is insufficient.
Repository variables override organization variables; environment values become
available after job start and cannot replace contexts already captured at job
level. See GitHub's [variable precedence and timing](https://docs.github.com/en/actions/reference/workflows-and-actions/variables#configuration-variable-precedence)
and [vars context](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#vars-context).
Prefer absent environment overrides; retained copies must parse identically to C.

The Publisher job-level condition independently requires
`vars.CONNECTOR_PUBLICATION_ENABLED == 'true'`, successful preflight and
`!inputs.acceptance_only`, plus all original actor/main/attempt checks. GitHub string
[comparisons ignore case](https://docs.github.com/en/actions/reference/workflows-and-actions/expressions#operators),
so use literal lowercase `false`/`true` for administration;
do not rely on uppercase `TRUE` being disabled. The gate must remain absent/false
through this preparation and owner configuration review. Environment variables
cannot substitute for this pre-environment condition.

Keep explicit Verifier secret forwarding and existing environment key precedence.
A required secret mapping does not prove nonempty availability. Any custody or
availability discrepancy requires separate owner resolution, never key extraction,
copying, Publisher-to-Verifier credential sharing or permission elevation.

## Source reproduction for a future approved request — do not execute here

Original S3 acceptance remains historical. Use this source-data procedure only
after separate owner authorization and source review; it creates local unattested
proposal data. For 0.2.2 it additionally requires the later metadata/source PR and
qualification. It neither resumes historical 0.2.1 nor authorizes dispatch.

Establish P and D before approving any request:

1. Select exact committed **P** independently of S4 and the pinning merge commit.
   Preserve authenticated main ancestry, the merged reviewed PR whose merge SHA
   is P, successful required Python 3.12 `validate` for P and qualified Connector
   metadata for the separately approved version. Record current main caller C
   separately. The later
   Publisher also requires P's entire workflow directory to match C's; a source
   predating repinning may not meet that conservative permission rule. Resolve
   source selection through review, never by changing the trusted engine or App
   permissions.
2. Prepare separate clean detached local checkouts at exact S4 (trusted tools) and
   P (source data), using new directories. Verify both HEADs and clean inventories.
   Use S4's hash-pinned SDK and existing reviewed dependencies. Do not run P's
   helpers, requirements, workflows or playbooks. Store build output outside both
   checkouts. No tag is required for this source-only reproduction.
3. With `ATLAS_S4_TOOLS`, `ATLAS_PACKAGE_IMPLEMENTATION`, `ATLAS_PACKAGE_TAG`,
   `ATLAS_PACKAGE_SOURCE_DIR`, `ATLAS_PACKAGE_SOURCE` and
   `ATLAS_PACKAGE_REVIEW_OUTPUT` set to those reviewed paths/P and a new empty output
   directory, run the following local preparation from outside P. It uses S4's
   existing source-data adapter and exact-source checks. Review the two equal
   archives, Manifest, SPDX/licence/qualification validation and resulting D.

```python
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

S4 = os.environ["ATLAS_PACKAGE_IMPLEMENTATION"]  # Independently reviewed merged SHA
T = os.environ["ATLAS_PACKAGE_TAG"]  # Separately reviewed new release identity
tools = Path(os.environ["ATLAS_S4_TOOLS"]).resolve()
source = Path(os.environ["ATLAS_PACKAGE_SOURCE_DIR"]).resolve()
P = os.environ["ATLAS_PACKAGE_SOURCE"]
output = Path(os.environ["ATLAS_PACKAGE_REVIEW_OUTPUT"]).resolve()
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tools, text=True).strip() == S4
assert not subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=tools)
sys.path.insert(0, str(tools / "tools"))
from publish_connector import package_source
import release_connector
from connector_publication_contract import check_input
from publication_contract import canonical_json

with package_source(source):
    first = release_connector.prepare(T, output / "first", commit=P)
    second = release_connector.prepare(T, output / "second", commit=P)
name = first["id"] + "-" + first["version"] + ".tar.gz"
raw = (output / "first" / name).read_bytes()
assert raw == (output / "second" / name).read_bytes()
assert first == second
D = hashlib.sha256(raw).hexdigest()
assert first["distribution"]["bundle_digest"] == "sha256:" + D
assert first["distribution"]["provenance"]["source_commit"] == P
request = check_input({"operation": "tag", "acceptance_only": True,
    "package": {"tag": T, "source_commit": P, "sha256": D}})
with (output / "request.json").open("xb") as stream:
    stream.write(canonical_json(request))
print(json.dumps(request["package"], sort_keys=True))
```

These outputs are local, unattested proposal data. Independently reproduce D from
the same exact P and retain both build records before owner approval. Neither an
earlier recorded digest nor equality with a prior candidate authorizes this request.
No 0.2.2 P/D is assigned by this task. Later source qualification and separate
operation approval remain necessary.

After the prerequisites and separate owner authorization, use the reviewed
`connector-publish.yml` workflow from **main**, original attempt **1**, with original
and triggering ordinary user `benchristian88` (ID `93822871`). Do not rerun a failed
attempt as acceptance; investigate and obtain a separately approved new original
run. A separately reviewed future proposal has these symbolic inputs:

```text
operation: tag
acceptance_only: true
package: {"tag":"<APPROVED_CONNECTOR-vVERSION>","source_commit":"<REVIEWED_COMMITTED_SOURCE_P_40_LOWERCASE_HEX>","sha256":"<SOURCE_BUILT_PACKAGE_D_64_LOWERCASE_HEX>"}
```

This is a **non-executable example**, not an approved request. The tag must be a
separately reviewed future identity; angle-bracket strings are invalid placeholders.
P must be an exact approved committed source with qualified metadata;
D must be reproduced from that source by the reviewed source-only builder. Do not
reuse an earlier uncommitted candidate digest, including the PR1 local digest, as
approval. Preserve the exact approved `package` input string, `operation`, and
Boolean input before dispatch. Also retain canonical `request.json` containing
`{"operation":"tag","acceptance_only":true,"package":{...real approved fields...}}`;
the workflow canonicalizes this object for its request digest (16 KiB maximum).

Acceptance observes/signs the proposal and security controls. It authenticates
caller's C/CI and request binding; **the Publisher's package-source/build validation
is skipped**. It does not create a tag, prove draft absence, qualify the original
build, authorize finalization or make the package remotely installable. Even if
`CONNECTOR_PUBLICATION_ENABLED` were erroneously true, acceptance-only must skip
the entire Publisher job before environment entry, key injection or token mint.

## Historical S3 acceptance evidence — preserve original bytes

For original S3 run **40542954614**, the owner preserved the original ZIP
independently of GitHub's expired artifact retention. The recomputed original ZIP
SHA-256 is `3023e7abb9906a7cbdafabd8d31c83a261790c27f71f793aad696e99115dce47`;
the recomputed original preflight SHA-256 is
`e78819ff12f28d6dd218f43e14c91dc6ad5095ad335a5fd467f3c338b656e88b`.
The **30 October 2026 owner-approval review independently authenticated the original
bytes** after locating the retained ZIP in Finder and copying only that file to
the local verification directory. The 14,893-byte ZIP contains exactly two regular
members: 64,192-byte `connector-preflight.json` and 10,917-byte
`connector-preflight.sigstore.json`. The original bundle SHA-256 is
`ad40b88deaaac8ceaac1503903acbddd21205e444f611ff06d7c4146443b9b36`.

Frozen S3 `check_preflight` passed against independently established C/R/request,
original false/false trust and exact policy bytes from C, including canonical
preflight bytes, policy/trust/request bindings, all five complete signed ruleset
observations and the historical freshness interval. Frozen
`ConnectorSigstore.verify` and pinned **gh 2.102.1** offline verification passed
on both original members with S3's frozen root distribution and exact
certificate/statement/subject/predicate/transparency profile. The SDK was installed
only into a temporary target from S3's hash-pinned vendored wheel. The original
bundle and independently verified API bundle have equal parsed content but different
serialized hashes; neither was substituted for the other. See the activation
review for output locations and the remaining live security checks. This is
historical evidence authentication, not current admission or activation authority.

For any independent repeat, recompute the original ZIP's SHA-256 before inspecting
bounded regular members; require exactly `connector-preflight.json` and
`connector-preflight.sigstore.json`, and recompute the preflight digest above.
Use those original member bytes with the frozen S3 validators below, original
disabled trust and exact policy bytes at caller C
`d3f66b039e2027832be932cacd006d86442821ec`. Preserve the ZIP/member hashes,
`check_preflight` result and pinned offline `ConnectorSigstore.verify` result.
Do not reconstruct the preflight, reserialize its original bytes, substitute the
API-serialized bundle for the original member, or infer completion from a logged
digest. Unavailable or contradictory evidence remains a stop condition.

Record run ID R and `https://github.com/benchristian88/atlas-connectors/actions/runs/R`.
Save these observations immediately; artifact `connector-preflight-R` retains only
`connector-preflight.json` and `connector-preflight.sigstore.json` for **one day**.
Download them as original bytes. Policy, trust and request bytes are **not** in
that artifact; preserve them separately. Do not dump environment/secret contexts.

| Evidence | Exact inspection |
| --- | --- |
| Original dispatch | Save official API `GET /repos/benchristian88/atlas-connectors/actions/runs/R` and `/actions/runs/R/attempts/1`. Require both IDs R, `run_attempt: 1`, event `workflow_dispatch`, branch main, SHA C, official repository/owner IDs and both actors `benchristian88`/`93822871`/`User`. |
| Caller and reusable identities | Save workflow API record using the run's `workflow_id`; caller path must be `.github/workflows/connector-publish.yml`. Both run records must show exactly one `referenced_workflows` entry, with path `benchristian88/atlas-connectors/.github/workflows/connector-verifier.yml@be24042c4e7446c7d88d2f08608ab7f058bb24b6` and sha `be24042c4e7446c7d88d2f08608ab7f058bb24b6`. Save caller bytes at C, all four bindings and the exact SHA-pinned job context with `job.workflow_sha` S3. |
| Job isolation | Save `/actions/runs/R/attempts/1/jobs?per_page=100` (all pages), job steps/logs (`/actions/jobs/J/logs` for each job ID J) and run summary. The reusable preflight/verify job must succeed; `publisher` must have conclusion `skipped`, with no started runner/Publisher steps or `catalogue-publication` deployment for R. No authenticate/prepare/execute Publisher step, key use or installation-token mint may run. Do not mistake Verifier token mint or attestation OIDC for Publisher credentials. |
| Exact configuration bytes | Save raw `policy.json` and `connector-trust.json` from the official Contents API **at ref C**, base64-decode content without reserializing. Preserve the independently reviewed repository policy variable and any matching environment copies, original approved inputs and canonical `request.json`. Compare complete trust values, not just S. |
| Signed preflight | Verify canonical exact subject bytes, package schema `atlas-connector-package-preflight/v1`, implementation S, complete expected context/request/run/attempt, request SHA-256, SHA-256 of original policy bytes and canonical trust JSON. Check all security observations and all five complete `bypass_actors` arrays with existing validators; omission never means empty. Record observation start/end/issue/expiry and run timing. |
| Genuine certificate and statement | Save pinned gh offline verified JSON: issuer `https://token.actions.githubusercontent.com`, SAN and `buildSignerURI` each exactly the full `https://github.com/benchristian88/atlas-connectors/.github/workflows/connector-verifier.yml@` URI followed by trusted immutable S; `buildSignerDigest` S; official repository/owner URI and IDs, public visibility, source/config digest C, source ref main, caller `buildConfigURI`, hosted runner, dispatch trigger, invocation `/actions/runs/R/attempts/1`. Require sole subject `connector-preflight.json` with exact digest and package predicate `https://atlas-impact.dev/attestations/connector-package-preflight/v1`, schema `atlas-connector-package-preflight-predicate/v1` and repeated subject digest; verified allowed transparency timestamps. |
| No mutation | Preserve before/after `GET /git/ref/tags/proxmox-v0.2.1` (including 404 absence) and complete `/releases?per_page=100&page=N` published inventories plus any available authorized audit records; require no `proxmox-v0.2.1` ref/release creation or other publication mutation by R. Anonymous release listings cannot establish private draft absence. Do not mint a Publisher token merely to collect acceptance evidence; job exclusion is the credential boundary, inventories are corroboration. |

Use S's existing `ConnectorSigstore.verify` and `check_preflight` from a separate
reviewed checkout at **S**, with its hash-pinned SDK, gh and frozen roots. Do not
execute caller C's helpers. For the offline signature command, use this exact
profile (paths point to the preserved files and S's trusted-root distribution):

```text
./tools/publication_trust/bin/gh attestation verify connector-preflight.json --bundle connector-preflight.sigstore.json --custom-trusted-root <S_TRUSTED_ROOT_JSONL> --repo benchristian88/atlas-connectors --hostname github.com --signer-workflow benchristian88/atlas-connectors/.github/workflows/connector-verifier.yml --signer-digest be24042c4e7446c7d88d2f08608ab7f058bb24b6 --source-digest <ORIGINAL_CALLER_C> --source-ref refs/heads/main --cert-oidc-issuer https://token.actions.githubusercontent.com --deny-self-hosted-runners --predicate-type https://atlas-impact.dev/attestations/connector-package-preflight/v1 --digest-alg sha256 --format json
```

The pinned gh command verifies cryptography offline; it alone does not replace the
additional exact certificate, subject, predicate, context and security validators.
Construct expected context from independent R/C and the previously approved request,
not from unverified subject fields:

```python
# Run with S/tools on sys.path and S's pinned verifier provisioned.
from pathlib import Path
from atlas_connector_sdk.contracts import strict_json
from connector_publication_contract import check_input, check_preflight, parse, MAX_AUTHORIZATION_BYTES
from connector_publication_sigstore import ConnectorSigstore
from publication_contract import canonical_json, digest

C = "<INDEPENDENT_ORIGINAL_CALLER_C_40_HEX>"
S = "be24042c4e7446c7d88d2f08608ab7f058bb24b6"
R = int("<INDEPENDENT_ORIGINAL_RUN_ID>")
request = check_input(strict_json(Path("request.json").read_bytes(), maximum=16384))
assert request["acceptance_only"] is True
trust = strict_json(Path("connector-trust.json").read_bytes(), maximum=16384)
assert trust["signer_revision"] == S
assert trust["enabled"] is trust["live_signer_accepted"] is False
policy_raw = Path("policy.json").read_bytes()
raw = Path("connector-preflight.json").read_bytes()
bundle = Path("connector-preflight.sigstore.json").read_bytes()
expected = {"caller_sha": C, "run_id": R, "run_attempt": 1,
            "request_sha256": digest(canonical_json(request)), "request": request}
check_preflight(parse(raw, MAX_AUTHORIZATION_BYTES), expected, trust, policy_raw)
ConnectorSigstore().verify(raw, bundle, expected=expected, trust=trust)
print("Offline package profile and signed controls verified; owner isolation review still required")
```

Preserve stdout, verification JSON, file digests and exact verifier/root identity.
Do this promptly; `admit` additionally enforces a 900-second live startup window
and at most 1,800-second same-job continuation. A later archival signature review
is not live admission or replay authorization. Successful Actions execution,
artifact download, synthetic certificates or decoded DSSE claims alone do not
establish genuine signer acceptance. Any actual certificate/job claim differing
from the exact approved profile must fail closed and be reported. A code correction
requires a new reviewed implementation baseline and re-pinning cycle, never a
weakened comparison or changed code described as S.

This S3 evidence remains historical and cannot qualify package S4. The current
owner decision and separate clean-release rollout at the top govern future work.
Publication stays disabled; Tag, Stage and Finalize each require separate explicit
authority. Catalogue sequence two remains separate.

## Request format and separate publication ceremony

These reusable contracts apply only to a future separately approved clean release.
They do not authorize any operation on historical Proxmox 0.2.1. P/C workflow
directory equality is mandatory in preparation and execution for every operation.

The workflow supplies `operation` and `acceptance_only` separately. Paste only the
`package` object into its string input. All examples below are symbolic, **not
executable approved requests**: P/D/R/etc must be replaced with independently
reviewed real values; JSON hashes are lowercase hex without prefixes.

For **tag**, package fields are exactly:

```text
{"tag":"CONNECTOR-vVERSION","source_commit":"P (40 hex)","sha256":"D (64 hex)"}
```

Source P must be an exact reviewed merged main PR commit with successful required
CI and ancestry, qualified stable production metadata, compatible Manifest and
SPDX/licence records. Reproduce D from this committed source; an earlier local D
is not authoritative. For a later publication dispatch, tag and every draft-visible
release inventory must be empty for T. The admitted scoped App creates one lightweight ref to P, then verifies
it. It stops with `tag_created_build_pending`; App-originated push triggers the
unchanged build workflow. Do not rerun the tag operation when T exists.

For **stage**, add exactly:

```text
"build_run_id": R,
"artifact_id": ORIGINAL_ACTIONS_ARTIFACT_ID,
"artifact_sha256": "ORIGINAL_ZIP_SHA256",
"release_id": null,
"assets": {}
```

The original run and attempt one must both be completed/successful; source SHA,
tag, workflow and configured App bot actors must match. Inspect the exact retained
Actions artifact's ID/digest before approval. The helper selects that artifact
only from R, checks its metadata twice and rejects expired/replaced/duplicate
candidates. It independently authenticates the original package bundle and compares
all candidate bytes to the committed-source build. The ZIP must contain exactly
the archive, `manifest.json`, `index.json`, `SHA256SUMS`, `package.sigstore.json`.
Bounded decoding does not extract paths or execute package content.

The Publisher checks private draft absence and creates one non-prerelease draft
at T/P with `make_latest: "false"`. Every original file is uploaded unchanged and
reread with exact App uploader, ID, size and digest. Stage records P/T/D/R, original
Actions artifact identity, release **L**, archive **A**, complete name/ID/SHA-256/
byte inventory and its canonical SHA-256. Its `staged_requires_separate_approval`
receipt is an audit aid, not signed publication authority. **STAGE STOPS HERE.**

For **finalize**, replace the stage-only resume fields with these exact fields,
in addition to the same tag/source/digest/build/artifact fields:

```text
"release_id": L,
"asset_id": A,
"assets": {"EACH_OF_FIVE_NAMES": {"id": ID, "sha256": "HEX", "bytes": SIZE}},
"inventory_sha256": "SHA256_OF_CANONICAL_COMPLETE_ASSETS_OBJECT",
"staging_run_id": ORIGINAL_SUCCESSFUL_STAGE_DISPATCH
```

Independently inspect the retained stage receipt and all five staged identities;
the human explicitly approves this object in a new original main dispatch. Do not
construct it by querying current finalization state. Preserve the reviewed input
with its new signed preflight. Canonical JSON means sorted keys, two-space indent,
UTF-8, trailing newline, as `publication_contract.canonical_json` implements.
The previous staging dispatch must be a distinct successful original human run,
with matching package caller/signer identities; receipt metadata alone grants no
approval. There is no claim of a second human veto.

Immediately before the sole PATCH, revalidate admission, current protections,
source/build, exact draft L and every approved asset. PATCH sets only `draft:
false` and `make_latest: "false"`; there is no fabricated immutable switch. The
unchanged anonymous GET-only verifier then reauthenticates the original build,
both release lookup identities, exact T/P/L/A, all five approved IDs/bytes/digests/
uploaders, non-draft/non-prerelease and actual `immutable: true`, including final
rereads. Only then emit `immutable_package_verified_catalogue_pending`. A successful
PATCH is not a publication-success receipt.

## Failure recovery and retained evidence

| State | Required action |
| --- | --- |
| Tag response lost | Fresh GET; exact observed tag is reported for review, no second POST. Retain original first build; never retag. |
| Tag exists, no successful build | Wait and inspect. A failed/rerun first build cannot be substituted; separately review a new identity. |
| Artifact expired/unavailable | Stop. There is no local rebuild, alternate-run or re-signing fallback. This implementation requires the original Actions artifact for stage/finalize. |
| Draft creation response lost | Fresh private inventory, failure receipt; no blind second create. Review exact L before a fresh explicit resume. |
| Partial upload/accepted response lost | Reread draft/assets, retain safe observed IDs, stop. Fresh stage request must approve exact existing L and partial inventory in `assets`; append only missing original files. |
| Conflicting digest/ID/author/uploader/extra file | Stop without deleting/replacing anything. Investigate; immutable conflicts require a reviewed new version. |
| Missing/delayed asset digest | Stop without another write or a byte-only fallback. Reobserve metadata and approve a fresh exact resume after investigation. |
| Workflow mismatch, including a reviewed repin | Tag, Stage and Finalize all stop, including existing drafts and already-published identities. Select later reviewed source/release separately; no exception or Workflows Write grant. |
| Changed rules/App scope/CI/stale approval | Admission/state checks reject. Obtain fresh human review and genuine evidence; never bypass. |
| Final PATCH response lost | GET observation then the independent verifier; exact immutable identity can succeed without another PATCH. Otherwise fail. |
| Already published exact release | Fresh approved finalize request re-verifies immutable state with zero writes. Mutable or contradictory state rejects. |

Receipts include caller/implementation/request/admission digests; failure receipts
carry only bounded sanitized identities and safe observed inventories if available.
A failed draft create/upload also records an allowlisted primary diagnostic and
separate recovery-observation outcome; a secondary error cannot mask the primary.
Credentials, provider responses, keys and runner-local admission receipts are never
uploaded or printed. Successful and incomplete receipts have 90-day Actions
retention. Preserve original preflight/bundle/policy/trust, exact approved request,
receipts, all five original files and genuine offline/provider verification evidence
under the owner's existing evidence practice. Actions retention is not an immutable
public archive and does not satisfy future catalogue publication by itself.

No registry record, pointer or catalogue sequence is changed. After separately
authorized immutable publication and genuine final-artifact qualification, a later
review can prepare a catalogue entry. Sequence two still needs its separately
approved stronger evidence archive/consumer-authority contract and explicit handling
of historical mutable Proxmox 0.2.0. Publication alone grants no installation or
update authority. Atlas and SDK remain read-only references.
