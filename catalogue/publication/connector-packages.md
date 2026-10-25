# Controlled Connector package publication

Phase 4B.2 supplies local implementation for review. **Remote execution is not
authorized.** Package trust is disabled and its implementation pin is deliberately
all zeros. No Proxmox 0.2.1 tag, workflow run, draft, release or catalogue entry was
created by this increment. See [proposed ADR 0006](../../docs/decisions/0006-connector-package-publication.md)
and the [qualification report](../../docs/phase-4b2-local-qualification.md).

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

## Administration prerequisites — owner verification required

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

The Verifier observes Publisher **registration**, not its effective installation
grant. The admitted Publisher independently JWT-authenticates its App/installation,
compares exact registered/installed/issued permissions and observes its token's
single repository before any repository write. This is an explicit unresolved
policy boundary if effective permissions must be independently observed in signed
pre-token admission. Neither current local tests nor the Phase 4B.1 public
observations verify installed scope, live key custody or uninterrupted hidden
bypass configuration. No such verification is claimed here.

Provider references: [ref creation permissions](https://docs.github.com/en/rest/git/refs#create-a-reference),
[release creation and conditional Workflows permissions](https://docs.github.com/en/rest/releases/releases#create-a-release),
[draft release visibility](https://docs.github.com/en/rest/releases/releases#list-releases),
[Actions artifact retrieval](https://docs.github.com/en/rest/actions/artifacts#download-an-artifact)
and [immutable release preparation](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases).
The implementation conservatively requires the package source workflow directory
to equal current main. Resolve mismatches with reviewed source planning, never
permission elevation. Provider-selected Actions download redirects are HTTPS-only
to Azure blob or Actions artifact hosts, without forwarded credentials, further
redirects, ambient proxies or operator-supplied URLs. Original ZIP SHA-256 and size
must match the independently approved artifact identity and run metadata.

## Review, pinning and first acceptance — no publication

1. Review PR1's complete implementation, proposed ADR and negative tests. The human
   alone commits, pushes, opens the PR and merges after required Python 3.12 CI.
   Record the immutable reviewed implementation commit **S** containing these
   helpers, the reusable workflow and vendored dependencies. Do not invent S from
   an uncommitted tree or use S4 `2dd1ffcd...` for package authority.
2. In separate controlled PR2, replace every all-zero implementation pin in the
   caller (reusable `uses`, executable checkout, implementation environment) and
   `connector-trust.json` with exact full S. Update the exact reviewed pin
   assertions in `tests/test_connector_publication.py` and
   `tests/test_publication_packaging.py` in that same controlled PR; do not loosen
   them to arbitrary refs. Keep `enabled: false` and
   `live_signer_accepted: false`. The reusable workflow checks `job.workflow_sha`
   against separately configured S before checkout or key access. It executes
   only S even as caller main advances to **C**.
3. The owner reviews and configures `CONNECTOR_VERIFICATION_POLICY` as the complete
   matching package-trust JSON in the existing Verifier and Publisher environments.
   It is public trust configuration, never a secret or downloaded authority. Leave
   repository `CONNECTOR_PUBLICATION_ENABLED` absent/false. Verify all prerequisites
   above, including the unresolved effective-permission decision. Do not change
   existing catalogue `VERIFICATION_POLICY` or `verifier-trust.json`.
4. Only with separate owner authority, manually dispatch the reviewed caller from
   main with `acceptance_only=true`, `operation=tag` and a bounded real proposal.
   This observes/signs the request and controls; it does **not** qualify a build,
   prove draft absence or create a tag. No workflow was dispatched in local work.
5. Preserve original caller C, signer S, run ID and attempt one; both actors and
   referenced-workflow metadata; exact preflight/bundle/policy/trust/request bytes;
   genuine offline verification output and timing; complete bypass arrays; and the
   jobs/steps record showing Publisher **skipped**, no Publisher key step, no
   Publisher token mint and no repository mutation. Download evidence within its
   one-day retention. An artifact download or successful attest action alone is
   insufficient. Compare independent observations and inspect contradictory or
   unavailable fields. A changed certificate/job URI must reject; any correction
   needs genuine evidence and security review, with a newly pinned S if code changes.
6. The next separate human decision reviews that genuine acceptance and ADR 0006's
   unresolved boundary. Only a later reviewed activation changes both package
   trust flags, matching environment trust and the repository enabling variable.
   Update the explicit trust-state regression assertions to the genuinely reviewed
   acceptance evidence in that activation PR; keep all negative tests enforced.
   Do not enable on modeled tests or this document's authority. Actual tag/stage/
   finalization need subsequent explicit owner publication authorization.

## Request format and separate publication ceremony

The workflow supplies `operation` and `acceptance_only` separately. Paste only the
`package` object into its string input. All examples below are symbolic, **not
executable approved requests**: C/D/R/etc must be replaced with independently
reviewed real values; JSON hashes are lowercase hex without prefixes.

For **tag**, package fields are exactly:

```text
{"tag":"CONNECTOR-vVERSION","source_commit":"C (40 hex)","sha256":"D (64 hex)"}
```

Source C must be an exact reviewed merged main PR commit with successful required
CI and ancestry, qualified stable production metadata, compatible Manifest and
SPDX/licence records. Reproduce D from this committed source; an earlier local D
is not authoritative. Tag and every draft-visible release inventory must be empty
for T. The admitted scoped App creates one lightweight ref to C, then verifies
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
at T/C with `make_latest: "false"`. Every original file is uploaded unchanged and
reread with exact App uploader, ID, size and digest. Stage records C/T/D/R, original
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
both release lookup identities, exact T/C/L/A, all five approved IDs/bytes/digests/
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
| Changed rules/App scope/CI/stale approval | Admission/state checks reject. Obtain fresh human review and genuine evidence; never bypass. |
| Final PATCH response lost | GET observation then the independent verifier; exact immutable identity can succeed without another PATCH. Otherwise fail. |
| Already published exact release | Fresh approved finalize request re-verifies immutable state with zero writes. Mutable or contradictory state rejects. |

Receipts include caller/implementation/request/admission digests; failure receipts
carry only bounded sanitized identities and safe observed inventories if available.
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
