# Phase 4B.4 — Corrected S4 engine for clean publication

Date: 31 October 2026 (Pacific/Auckland).

**Implementation readiness: PASS (local review scope).** The corrected successor
retains secure draft asset verification and normal partial-draft recovery while
requiring source/caller workflow equality for Tag, Stage and Finalize. It is local,
uncommitted, unpinned and not activated. The owner has disabled
`CONNECTOR_PUBLICATION_ENABLED`; keep it disabled.

## A. Scope and owner decision

The owner has abandoned automated recovery of incomplete Proxmox 0.2.1. Its
protected tag, original successful signed build/artifact, incomplete draft and
uploaded checksum remain **unpublished and untouched historical evidence**, not
valid catalogue publication authority. The next candidate is a clean **0.2.2**,
prepared from new reviewed source only after the corrected engine is merged and
repinned. No 0.2.2 metadata, source identity, tag, release or digest is created here.

The requested repository is `/Users/Ben/Code/atlas-connectors`, existing branch
`fix/connector-draft-staging-recovery`, unchanged base/HEAD
`ebd5f67a72b99291f41748ef2dba007e80c141e4`. The pre-existing Phase 4B.4 working-tree
changes were inspected and revised within this task’s scope. No Git mutation,
remote operation, credential use or draft interaction is part of this correction.

## B. Implementation changes and material files

| File | Final change |
| --- | --- |
| `tools/publish_connector.py` | Original inline source review/CI/ancestry and strict workflow equality for every preparation/authority call; authenticated draft assets, release rereads and bounded dual-error failure receipts. |
| `tools/connector_publication_github.py` | Restricted numeric asset download with one authenticated repository-bound distribution redirect, no forwarded credentials and bounded transfer. |
| `tools/verify_connector_release.py` | Shared draft URL identity validator; independent anonymous final verifier requires tagged URLs and exact approved immutable release/assets. |
| `tests/test_connector_publication.py` | Provider model represents opaque draft URLs and their transition to final tagged URLs; historical security, signer, isolation and packaging regressions remain. |
| `tests/test_connector_draft_recovery.py` | Equality rejection for every operation, no pin-only exemption, original bytes/digests, generic URLs, normal recovery, safe diagnostics and actual unsigned-admission rejection. |
| `tests/fixtures/connector_draft_provider/draft.json`, `README.md` | Retained explicitly synthetic draft representation; no original historical fixture changed. |
| `docs/decisions/0007-post-tag-staging-recovery.md` | Proposed relaxation marked rejected/superseded, with its original reasoning preserved as rejected design history. |
| `README.md`, `catalogue/publication/connector-packages.md`, this report | Clean 0.2.2 direction, historical 0.2.1 treatment, current operating contract and exact S4 handoff. |

`tools/connector_publication_source.py` was an untracked Phase 4B.4 addition. Its
remaining source checks duplicate the original trusted implementation, so it has
been removed. Source authority remains in the original `publish_connector.py`
location. There is no additional source-authority module or parallel policy.

## C. Removed exception and preserved security controls

There is **no post-tag workflow-mismatch or cross-repin exception**. Package source
P and current caller C must have identical complete workflow directories for
**Tag, Stage and Finalize**, including existing-draft recovery and a finalize
request for an already-published identity. An exact reviewed three-pin replacement
still rejects with `connector_workflows_write_required`, before preparation or
writes. The implementation SHA and release ID cannot relax that condition.

Source authority retains exact merged-main PR identity, ancestry, required
successful `validate` CI from Actions App 15368 and official repository/owner
checks. Workflow listings are bounded, require valid file/blob identities and
reject duplicate paths, malformed entries and empty or unequal directories.
Every mutation boundary reauthenticates signed admission and provider controls.

[ADR 0007](decisions/0007-post-tag-staging-recovery.md)’s relaxation is **not
accepted**. [ADR 0006](decisions/0006-connector-package-publication.md) remains
unchanged and authoritative. Publisher App 5422372 retains Contents Write and
Actions/Administration/Metadata Read; Workflows Write remains unavailable. Exact
App registration, installation, issued permissions and one-repository scope still
reject excessive grants. No conditional Workflows permission bypass is introduced.

Publisher credentials cannot be used before genuine signed admission and committed
source/package checks. Stage and Finalize additionally authenticate the original
bundle before minting credentials. The isolated Verifier
never receives Publisher credentials. Acceptance-only skips the entire Publisher
job before environment/key use or token mint. Signer SAN/URI/digest, caller,
request, policy/trust, first-attempt, freshness, rulesets and repository identities
remain strict. The historical Sigstore/packaging tests and frozen verifier remain.

## D. Draft asset identity and restricted bytes

The admitted Publisher independently authenticates the official repository and
fetches the exact numeric release ID. Its source/tag/name/author/draft state must
match existing controls. Asset enumeration uses that fixed release's numeric REST
route, and metadata is reread around downloads.

A draft asset may have the expected final tagged URL or an opaque selector taken
from that release's official `html_url`, shaped as `untagged-` plus 8–64 lowercase
hex characters. Its `assets_url` must independently bind the same numeric release.
The opaque selector is never learned from the asset URL or accepted by pattern
alone. Unknown provider representations fail closed pending review. Alternate
repository, host, path, name, userinfo, port, encoding, query and fragment variants
reject. Published assets accept only the exact final tag/name URL.

Browser URLs are metadata only. All byte requests use the official numeric asset
REST endpoint. A single redirect from that authenticated response may reach only
`release-assets.githubusercontent.com/github-production-release-asset/1414494920/`
with a UUID-shaped object path. No bearer token, cookie, proxy or further redirect
is used on that request. The redirect's authority derives from the authenticated
numeric API response, its restricted structure, and mandatory original digest/bytes;
the opaque object UUID is not independently interpreted as an asset ID.

Positive asset ID, official API URL, expected name, uploaded state, integer exact
size, exact SHA-256, official App uploader and downloaded bytes remain mandatory.
Absent/null/delayed digest metadata stops processing. It never becomes permission
for a digest-free fallback or an automatic retry. Recovery receipts contain no raw
URL, response body, provider exception, credential or unvalidated asset data.

## E. Normal Stage, recovery and Finalize

Normal Stage creates a new non-prerelease draft and uploads **all five original
files**: archive, `manifest.json`, `index.json`, `SHA256SUMS` and
`package.sigstore.json`. Trusted tools read package source as data, reconstruct
the unsigned files for exact comparison, authenticate the original successful
first-attempt build/artifact and Sigstore bundle, and preserve original bytes.
Failed, rerun, expired, substituted or unavailable original artifacts reject.

General-purpose partial-draft recovery remains available when P/C workflows match.
A fresh explicitly approved request must identify the exact existing release and
partial `name -> {id, sha256, bytes}` inventory. Each existing asset is verified
without replacement; only missing original files are uploaded. Unexpected or
substituted assets, missing/conflicting digests and changed release metadata stop.
Tests retain an existing checksum’s exact ID/metadata/bytes while uploading only
four missing originals. The old cross-repin path rejects before any upload.

Stage stops at `staged_requires_separate_approval`. Finalize requires a distinct
successful original Stage dispatch and new human approval of all five exact
asset IDs/digests/sizes, package asset ID and canonical inventory digest. The sole
PATCH changes only `draft: false` and `make_latest: "false"`. An independent
anonymous GET-only verifier must authenticate final tagged URLs, original build,
all approved identities/bytes and actual `immutable: true` before success. A
successful PATCH alone is insufficient. Mutable or contradictory state rejects.

Ambiguous writes are never retried automatically. Safe primary diagnostics and
independent observation outcomes are retained separately; failed observation
cannot mask the initial upload/create failure. Receipts/logs never contain raw
provider errors, response bodies, secrets, bearer tokens or signed redirect URLs.
The anonymous verifier remains independently usable without publication authority;
a publication operation cannot use it to bypass P/C equality.

## F. Historical 0.2.1 treatment and root-cause limits

These identities are frozen historical evidence and must remain untouched:

| Identity | Value |
| --- | --- |
| Tag / original Tag run | `proxmox-v0.2.1` / `41017433479` |
| Source P | `d3f66b039e2027832be932cacd006d86442821ec` |
| Package D | `96eaa736c2919e56e09b9613dddd8648ad1f43b77679899ab706261b2a38e509` |
| Original build / artifact | `41017538114` / `12960302111` |
| Original ZIP SHA-256 | `e941e8108791d7d0bdaea7716eeccb5cfce0dd77440cc1b81faf77b414084602` |

The earlier Phase 4B.4 investigation reported that GET observation reconfirmed the
original build was successful, attempt one, at P,
tag T, `.github/workflows/release.yml`, and official Publisher actor/triggering actor
`346232650`. The artifact download connector returned an internal error; direct
artifact metadata fetch was unsupported. This task did not retrieve/reverify that
original ZIP's genuine Sigstore bundle. The clean-release decision removes any
need to recover this historical artifact;
no local reconstruction is publication authority.

The earlier investigation’s trusted builder code read an existing clean detached
checkout at exact P as data and produced two identical four-file reconstructions:

| File | Bytes | SHA-256 |
| --- | --- | --- |
| `proxmox-0.2.1.tar.gz` | 32145 | `96eaa736c2919e56e09b9613dddd8648ad1f43b77679899ab706261b2a38e509` |
| `manifest.json` | 8247 | `80775acdc59dd9a0c4bf8c714e7a36d23db20fb653084a1f61e2f41de941dba1` |
| `index.json` | 9641 | `ca46f93a782b721dc685122915d45889dca6edb4ab3cfa658b92beb716a2cff7` |
| `SHA256SUMS` | 87 | `20f5c6f473a4908a97790e979baf0cf16f46532a6180325abc0f2cf18d71ab3f` |

No P helper, workflow, requirement installer or playbook was executed. No
replacement `package.sigstore.json`, build run, ZIP or tag was created. Preparation
still authenticates original run/attempt/actor/tag before downloading the approved
artifact, verifies original ZIP digest/identity, reconstructs all four unsigned
files exactly, verifies the original package bundle with pinned Sigstore, and
retains the five original files byte for byte. Failed or rerun builds reject.

The incomplete draft is `428740362`; its uploaded `SHA256SUMS` asset is
`691270692` (87 bytes, SHA-256
`20f5c6f473a4908a97790e979baf0cf16f46532a6180325abc0f2cf18d71ab3f`).
The owner’s clean-release decision supersedes all former Stage-resume instructions
and candidate recovery JSON. There is no future recovery approval request for
these objects in this handoff.

The following root-cause observations are retained from the **earlier Phase 4B.4
investigation**, not new provider observations or current authority:

S3 requires every asset's browser URL to contain the final package tag, including
while the release is draft. The owner reports an authenticated `untagged-…` URL,
and that the downloaded checksum asset matches the original signed build. This is
a credible explanation for failed Stage `41018185523` / `connector_asset_identity`.
The original condition also includes size/state/digest, so the error alone cannot
prove a URL mismatch was the sole cause. Missing or delayed digest metadata is a
second plausible cause, explicitly tested without weakening digest enforcement.

Connected GET-only requests for draft `428740362` and its asset list returned
403 `Resource not accessible by integration`. No Publisher credentials were minted
or supplied to obtain draft visibility. The exact failure-time REST response is
unavailable; the synthetic provider fixture is clearly labeled, not live evidence.

Independent GET observation of existing published `proxmox-v0.2.0` confirmed that
its four browser asset URLs use the final `proxmox-v0.2.0` tag. That older release
reports mutable and does not qualify 0.2.1 or establish its future immutability.
Tests separately establish final tagged URL acceptance and stale draft URL rejection
by the independent final verifier. The actual 0.2.1 transition remains unobserved.

The masking defect is established from code: an upload-verification exception
could be replaced by a different exception from the recovery `assets()` call.
The successor records both outcomes independently and never retries the write.

No GitHub request or draft interaction was performed during this correction.
Synthetic fixtures remain labeled models and establish no live permission,
signature acceptance or immutable publication evidence.

## G. Tests and validation

Evidence directory: `/private/tmp/atlas-phase4b4-clean-publication`.

| Check actually executed | Result |
| --- | --- |
| Complete Ansible-enabled test suite | **2,522 passed**, zero skips/failures, 69.94 s; `full-pytest.log`. 180 Ansible Runner `codecs.open()` deprecation warnings on Python 3.14. |
| Focused security/publication/release/Sigstore/transport/crypto/packaging/documentation suite | **936 passed**, 25.90 s; `focused-security.log`. |
| `.venv/bin/python -m pytest -q tests/test_documentation.py` | **1 passed**; links, whitespace and fences valid; repeated after final report edits. |
| `/private/tmp/atlas-phase4b2-tools/actionlint -shellcheck= -pyflakes= .github/workflows/*.yml` | **Passed**, Actionlint 1.7.12, all seven unchanged workflows. Optional shellcheck and pyflakes checks disabled and not claimed. |
| `.venv/bin/python /private/tmp/atlas-phase4b4-clean-publication/verify-preservation.py` | **PASS**; `preservation.json`: 166 base tracked files, 160 unchanged, exactly six authorized tracked edits and five new files; source helper absent and index empty. |
| Pinned dependencies and collection | **Passed**: exact installed dev pins, SDK 1.1.0 wheel SHA-256/installed version, reviewed collection archive SHA-256 and all 189 installed collection files. `.venv/bin/python -m pip check`: no broken requirements. |
| Historical package reproduction in preservation script | **Passed**: two identical in-memory builds each for 0.2.0, 0.2.1 and 0.2.0-i4b.6, matching all three original SHA-256 values. These checks create no release or publication authority. |
| `git diff --check` | **Passed**, repeated after final report edits. |

Exact full and focused commands (with logging through `tee` and `pipefail`):

```bash
ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-phase4b4-clean-publication/test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q
ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-phase4b4-clean-publication/test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q tests/test_connector_draft_recovery.py tests/test_connector_publication.py tests/test_connector_release.py tests/test_connector_sigstore.py tests/test_publication_transport.py tests/test_publication_crypto.py tests/test_publication_packaging.py tests/test_documentation.py
```

The fresh collection was provisioned with:

```bash
.venv/bin/python tools/test_collection.py --archive /Users/Ben/Code/atlas/vendor/collections/community-proxmox-2.0.0.tar.gz --output /private/tmp/atlas-phase4b4-clean-publication/test-collections
```

The regressions prove Tag/Stage/Finalize equality rejection in preparation and
execution, including a fully reviewed pin-only model, existing drafts and published
identities. They also cover generic opaque draft URLs, final tagged URLs, exact
asset IDs/uploader/state/size/bytes, missing/conflicting/delayed digest, hostile
redirects, safe primary/secondary diagnostics, unchanged existing assets, all five
original uploads, separate Finalize approval and actual immutability. The real
`job_admission`/`admit`/`ConnectorSigstore` path rejects missing or unsigned evidence
before Publisher preparation/key use/mint; structural validation of the unsigned
subject succeeds so its signature remains the rejection boundary. Excessive
Workflows grants, historical signer mismatches and original packaging/security
regressions remain tested.

Local Python is **3.14.7**. Hosted required Python **3.12** `validate` CI has not
run for this uncommitted change and remains a later PR gate. No live signer
qualification, provider permission experiment, publication or activation was run.

## H. Preservation, compatibility and repository state

No database or migrations apply. No Atlas/SDK API, UI, package request schema,
success receipt contract, workflow route or catalogue authority changed. Failure
receipts retain the additive bounded `write_failure` record. The existing
repository/owner identity and scoped App authorization remain the security boundary;
no new tenancy model is introduced.

All seven active workflows, all four S3 bindings, current committed package trust,
catalogue policy/trust/registry/current/history, frozen catalogue publisher,
original historical fixtures, Connector source/release metadata, dependencies,
SDK wheel/hash and verifier roots/distribution remain byte-identical to base,
as confirmed by the preservation checks and pinned verifier regression suite.
No 0.2.2 release metadata is added. Atlas and SDK sibling worktrees receive no edits.

No commit, push, merge, rebase, tag, release, workflow dispatch/rerun, GitHub
variable/secret/App/permission/settings mutation or historical asset mutation was
performed. All work remains unstaged/uncommitted on the existing feature branch.

## I. Documentation and remaining gates

The README and publication runbook now lead with the clean-release decision and
mandatory equality for every operation. The runbook preserves historical S/S2/S3
qualification and evidence as labeled history, replaces the old recovery handoff,
and keeps the reusable normal request/recovery contract. ADR 0007 retains its
rejected proposal; accepted ADR 0006 and other historical records are unchanged.

Remaining gates are reviewed implementation merge/hosted CI, actual S4 assignment,
separate repinning, matching independent disabled trust, genuine S4 acceptance-only
evidence/isolation, separate activation approval, later reviewed 0.2.2 source and
qualification, exact digest reproduction/P-C equality, separately authorized
publication operations and independent immutable verification. They are rollout
gates, not an unresolved cross-repin implementation exception. None is claimed
completed here. No further inspection or recovery of the 0.2.1 draft is needed.

## J. Exact S4 handoff

1. **Review/merge implementation:** review this corrected implementation PR with
   required hosted `validate`, security tests and rejected ADR 0007 history. This
   task leaves changes unstaged/uncommitted and does not perform the merge.
2. **Record package S4:** record the actual immutable merged successor SHA. No
   valid S4 SHA exists for these uncommitted changes. Do not use an invented SHA,
   moving ref, S3 or frozen catalogue S4 as a substitute.
3. **Separate repinning PR:** independently pin reusable signer `uses`, executable
   checkout `ref`, `ATLAS_IMPLEMENTATION_REVISION` and package trust
   `signer_revision` to S4; update pin-regression expectations as appropriate.
   Keep the frozen catalogue publisher separate. Use disabled/unaccepted
   qualification trust and keep the effective publication gate disabled.
4. **Genuine disabled qualification:** after separate repinning review/merge and
   owner-authorized matching independent trust configuration, obtain a new original
   main acceptance-only run. Preserve and genuinely verify its original ZIP,
   preflight/bundle, exact S4/C certificate/claims/invocation, approved request,
   policy/trust and complete protections. Confirm Publisher skipped before key use
   or token mint. Local tests and old S3 signatures cannot establish S4 acceptance.
5. **Separate activation approval:** obtain owner approval after genuine evidence
   and live control review. Only a later owner action may activate matching trust
   and gate. Keep baseline permissions and Workflows No access.
6. **Later 0.2.2 source PR:** prepare Proxmox 0.2.2 metadata/source in a subsequent
   reviewed PR, after S4 merge/repinning. Preserve all historical 0.2.1 objects.
7. **Qualify/reproduce:** qualify 0.2.2 at exact reviewed source P with required
   CI/main ancestry; reproduce exact package digest D twice using trusted S4 tools
   reading P as data. Record current caller C separately; no P/D is assigned here.
8. **Require workflow equality:** confirm P’s entire workflow directory equals C’s
   before each operation. If caller evolution breaks equality, stop for separate
   reviewed source/release selection. No repin exception or permission elevation.
9. **Separate Tag, Stage and Finalize:** separately authorize Tag for P/T/D; inspect
   the original signed successful build/attempt/artifact and exact ZIP digest;
   separately authorize Stage’s five original files; stop for a new explicit
   Finalize approval of the successful Stage and complete numeric asset inventory.
10. **Independent immutable verification:** require final tagged URLs, exact
    original signed bytes/approved identities and actual immutable release state
    before any catalogue update. Catalogue sequence/consumer authority and remote
    installation remain separately reviewed boundaries.

Final `git status --short` (all changes unstaged):

```text
 M README.md
 M catalogue/publication/connector-packages.md
 M tests/test_connector_publication.py
 M tools/connector_publication_github.py
 M tools/publish_connector.py
 M tools/verify_connector_release.py
?? docs/decisions/0007-post-tag-staging-recovery.md
?? docs/phase-4b4-draft-staging-recovery.md
?? tests/fixtures/connector_draft_provider/
?? tests/test_connector_draft_recovery.py
```

**Conclusion: PASS for local implementation readiness.** The successor is not
live or activated; its actual S4 SHA, separate repinning/qualification and all
owner publication approvals remain future work. No 0.2.1 recovery is authorized.
