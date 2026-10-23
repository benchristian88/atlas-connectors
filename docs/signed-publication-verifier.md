# Lean V2 signed publication preflight

Status: **S4 signer accepted; independent environment trust must be synchronized; bootstrap staging and activation incomplete.**
[ADR 0005](decisions/0005-lean-run-preflight.md) supersedes the V1 transition-grant
architecture. The [operator runbook](../catalogue/publication/README.md) is the active
procedure; [V1 documentation](signed-publication-verifier-v1.md) is historical.

The checked-in publication policy is unchanged: enabled, bootstrap `stage`, with
both root approval pins unset. Verifier trust is now
`live_signer_accepted: true` for S4, with ruleset/environment pins preserved in
[verifier-trust.json](../catalogue/publication/verifier-trust.json). The operator
must synchronize `catalogue-verification`'s `VERIFICATION_POLICY` after this
approval merges, before granting and approving temporary Publisher Workflows Write.
S4 passed genuine signing acceptance in run **39893809663** with baseline Publisher
App permissions and Publisher skipped. Workflows Write has not yet been granted.
This approval changes no executable code or permission behavior. No live workflow,
GitHub variable/settings mutation, release or ref write was performed by this task.

## One preflight, two Apps, one maintainer

A fresh manual main dispatch selects `bootstrap`, `publish` or `recover` and
`acceptance_only` (default true). The verifier is a separate SHA-pinned reusable
job in `catalogue-verification`. Its exact App/installation remains **5424851 /
174088125** with Administration Write, Contents Read, Actions Read, Checks Read and
Metadata Read, scoped to repository **1414494920**, owner **93822871**. Its only POST
mints that restricted installation token. Every repository evidence operation is
an allowlisted, bounded GET. Redirects, pagination and incomplete evidence fail.
No release/draft/ref observation or mutation endpoints remain in this transport.

The issuer independently reads the exact publication policy bytes at C, repository,
protected main, run and attempt one, exact caller workflow, human maintainer/user,
required successful CI, Publisher App metadata, publication and verification
environments, release immutability and all five exact ruleset IDs/details with
complete bypass arrays. It reuses P1 authority/protection validators. There is no
per-asset target, transition challenge, per-ref grant or challenge-consumption API.

The Publisher App remains **5422372 / 174027755**, with baseline Contents Write,
Actions Read, Administration Read and Metadata Read. The frozen S4 implementation
requires exactly that baseline for acceptance-only signing and normal publish/recover;
live bootstrap stage/activate require exactly baseline plus Workflows Write. Any
other permission or missing field is rejected by both the signed security checks
and Publisher checks. No policy mechanism or bypass is added. Its key exists only
in the Publisher job's
pinned token action; the Verifier key exists only in the isolated issuer step.
The jobs never inherit each other's secrets. Only two public signed files cross
jobs: `preflight.json` and `preflight.sigstore.json`, selected by artifact ID.
The caller explicitly maps only `VERIFICATION_APP_PRIVATE_KEY` to the reusable
workflow's one required secret. The key remains stored in `catalogue-verification`,
which the called job explicitly uses; do not copy it to repository secrets or
`catalogue-publication`. Local workflow tests do not prove real secret delivery.

The Publisher job depends on preflight success and is skipped unconditionally for
acceptance-only dispatches. Before its App token action, trusted code independently
verifies canonical bytes, Sigstore signature and transparency evidence, signer S,
source C, exact run/attempt/operation, exact local policy digest, complete signed
security observations and startup freshness. Missing, stale, substituted or
unaccepted evidence stops before token creation. Each later CLI phase verifies
the same signature/context again against its local startup receipt; it requests
no new signed authorization.

The pinned token action requests Workflows Write only when the signed dispatch
operation is `bootstrap`; publish/recover retain their original explicit token
permissions. Its empty-input parser omits Workflows Write in those ordinary
operations rather than inheriting all App permissions. Registration elevation
alone cannot authorize writes: GitHub must grant the requested permission on the
existing single-repository installation or token minting fails and the job stops,
without a lower-permission fallback. Automatic token revocation and `GITHUB_TOKEN`
job permissions are unchanged. Acceptance-only skips the entire Publisher job,
so S4 can be genuinely verified before elevating the Publisher App. Normal
publication also rejects an elevated App registration until mandatory rollback.

## Independent implementation S and catalogue source C

The reusable job call uses a literal full SHA S. Before checkout or key injection,
the reusable job's exact repository/path and `job.workflow_sha` must match the
independent environment trust object. It checks out S, installs only the vendored
hash-pinned SDK offline, and never consumes caller code or artifacts.

The Publisher also checks out executable implementation S and installs dependencies
from S. A second checkout places caller commit C at `publication-source`; only
policy, public verifier trust, registry data and the read-only Git commit timestamp
are consumed there. No scripts, plugins or packages from C are executed. The
trusted builder creates the same catalogue bytes as preparation at C. Original
bootstrap fixtures come from S, never rebuilt C data. Existing catalogue, package
and pointer signing profiles and seven-field pointer bytes are unchanged.

Trust at C is reviewed public configuration. The Verifier environment carries its
independently administered counterpart; neither is copied from signed evidence.
The implementation SHA in the Publisher workflow must equal its consumer trust
pin. Advancing C alone does not accept a new S. New implementation code requires
an explicit reviewed pin change, including the call, Publisher checkout and
`ATLAS_IMPLEMENTATION_REVISION` literal, plus independent environment trust.

**Frozen implementation:** S is
`2dd1ffcd2f5677dc35bdbc8f68ea28275c91c285` (S4), the reviewed implementation merged
through [PR #30](https://github.com/benchristian88/atlas-connectors/pull/30). It adds
strictly scoped temporary bootstrap Workflows Write support, preserving S3's
sanitized diagnostics and the isolated Verifier configuration. This approval
changes neither executable code nor token-permission behavior. All three executable workflow pins
and repository signer trust identify S. Caller/source C advances independently
and must differ from S. The catalogue/source checkout stays `${{ github.sha }}`.
Never derive S from current main or replace it with a moving reference.

Repository trust pins verification environment **25016263801**, all five verified
ruleset IDs and a **900-second** startup age. Its acceptance flag is true.
S4's genuine acceptance approves its signer for live publication, subject to
matching independent environment trust. After this approval merges, copy the
complete accepted JSON to `VERIFICATION_POLICY` before owner permission elevation.
S3's acceptance remains historical evidence; S4's separate review is recorded below.
No remote configuration or dispatch is performed by this approval task.

## Canonical contract and verification

`atlas-publication-preflight/v2` has exactly these sections:

| Section | Content |
| --- | --- |
| `authority` | Exact repository, owner, human maintainer and both App/installation IDs |
| `source` | C, SHA-256 of exact policy bytes at C, S, reusable signer path |
| `execution` | Exact caller path, run ID, attempt 1, operation, acceptance-only boolean |
| `security` | Independently retrieved repository/main/run/attempt/workflow/user/CI, environments, Publisher metadata and immutability observations |
| `rulesets` | All five pinned IDs and complete observations, observation digest and approved bypass actors |
| `freshness` | Earliest observation, completion, issuance and startup expiry, whole UTC seconds |

Canonical UTF-8 uses the existing sorted two-space JSON writer, LF and one terminal
newline. Strict parsing rejects duplicate keys, BOM/UTF-16, nonfinite numbers,
noncanonical bytes, missing/extra contract fields and size overflows. Policies and
trust are bounded to 16 KiB, preflight to 256 KiB, Sigstore bundle/output to 1 MiB.
The pinned gh **2.102.1** and existing roots verify offline with no token, config,
proxy or executable PATH. Verification takes at most 30 seconds.

The distinct subject is `preflight.json`, with predicate
`https://atlas-impact.dev/attestations/publication-preflight/v2`; its predicate is
`atlas-publication-preflight-predicate/v2` plus the exact `preflight_sha256`.
CLI filters independently enforce source digest C, signer digest S, exact repository
and reusable workflow, GitHub OIDC issuer, main source ref and hosted runners.
Verified certificate fields additionally enforce numeric repository/owner IDs,
caller buildConfig URI/digest C, source C and original run/attempt. SAN and
buildSignerURI must agree on the exact reusable workflow path; textual ref spelling
is not substituted for signer digest S. Missing verified transparency evidence fails.

Acceptance-only mode can sign with configured pins while `live_signer_accepted`
is false, exclusively to gather real evidence. That boolean is itself signed.
The Publisher job never starts for this mode; its consumer always expects false
and separately requires reviewed `live_signer_accepted: true`. An acceptance-only
bundle cannot authorize publication even if that trust flag is later enabled.

## Freshness, later validation and explicit trade-offs

The default and maximum startup observation age is **900 seconds (15 minutes)**,
measured from before Verifier App authentication. Operators may narrow it. This
allows signing, artifact transport and runner scheduling without the former
unrealistic 60-second cross-job constraint. A new Publisher job must complete
verification strictly before expiry; verification crossing expiry fails. An API
outage or longer queue requires a fresh dispatch, not extended evidence.

Successful startup writes a canonical receipt only on that Publisher runner,
binding accepted time, exact preflight digest and exact run/source/policy/operation.
It is never a downloaded or exported grant. Later phases reverify the signature
and this local admission, allowing completion after the startup window only within
**30 minutes of admission**, also bounded by the job's 30-minute timeout. A missing
receipt, different run/source/operation/policy or modified preflight fails. There
is no global replay database or promise of cross-job exactly-once consumption.

P1/P2 still recheck current main, dispatch identity, CI, environments, App scope,
immutability, bytes, packages, historical selections, predecessor bindings and CAS.
After startup, the Publisher also compares visible ruleset IDs/protection fields
with the signed snapshot and rejects changed bypass arrays **when returned**.
Administration Read may omit bypass actors; that remains unavailable current
evidence. It is never treated as an empty array or represented as a complete fresh
observation. Complete bypass authority comes from the signed startup snapshot.
A hidden bypass change after preflight can therefore escape later read-scoped
checks. The single-preflight decision deliberately accepts that bounded race;
there is no claim of continuously attested protections or an atomic transaction.
An administrator, sole maintainer or correct stolen credential remains powerful.

Draft visibility is separate: Contents Read cannot certify draft absence. Only
the Publisher's authenticated Contents Write path enables a complete bounded
release inventory (at most four pages, overflow rejected). Normal staging uses
that inventory to detect duplicate/higher drafts rather than trusting get-by-tag
absence. Bootstrap preserves its original bounded inventory, recovery, exact-byte
resume and root-marker fencing. Unexpected or ambiguous writes never retry blindly.

Consumers retain existing signing identities, complete chain/high-water rollback
protections and approved bootstrap anchors. No consumer trust profile is changed.
One maintainer remains the human trust root; there is no second-person approval,
marketplace governance or proof of uninterrupted provider protections.

## Genuine identity evidence and corrected representations

The preserved genuine [same-commit probe](../tests/fixtures/verifier_signer_probe/README.md)
still verifies with real pinned gh and rejects tampering/substitution. The owner
reports successful genuine distinct C/S verification from the separate pinned
experiment. Those earlier experiments establish the mechanism. Separately, the
owner reviewed genuine production-profile [run 39878342565](https://github.com/benchristian88/atlas-connectors/actions/runs/39878342565),
which authenticated the Verifier App, repository authority, all five rulesets,
immutable-release protection, signed preflight and exact caller/signer identities.
Publisher was skipped. That review accepted S2
(`00c85f688a43fb6da44acb3fa713d938e30a6da9`), separately from S3's review below.
Synthetic verified-output tests remain local regression evidence, not proof of
live acceptance.

Owner-reviewed genuine [S3 acceptance run 39887360792](https://github.com/benchristian88/atlas-connectors/actions/runs/39887360792)
verified frozen signer `5c66a50f61d013204eada0234c3389323b4a3f71` and caller
`2e2ddb70a1da254c0adaa857deb121aa2b0f7dfa` on attempt **1**. Preflight, Verifier App
authentication, Sigstore attestation and offline cryptographic verification passed;
Publisher was **skipped**. This historical review accepted S3; it does not accept
S4, complete bootstrap staging or establish the cause of the original Publisher HTTP failure.

Owner-reviewed genuine [S4 acceptance run 39893809663](https://github.com/benchristian88/atlas-connectors/actions/runs/39893809663)
verified frozen signer `2dd1ffcd2f5677dc35bdbc8f68ea28275c91c285` and caller
`605553a556632ace6f21216bf6cd22fdc17ed528` on attempt **1**. Preflight, Verifier App
authentication, repository ruleset verification, Sigstore attestation and offline
cryptographic verification passed; Publisher was **skipped**. The Publisher App
still has baseline permissions, without Workflows Write. This genuine review
accepts S4's signer; it does not establish bootstrap staging or activation success.

The first live bootstrap staging [run 39880692187](https://github.com/benchristian88/atlas-connectors/actions/runs/39880692187)
passed signed authorization, offline historical verification and Publisher token
creation, but staging failed with `github_request_failed`; no new draft was observed.
The GET-only [diagnostic run 39883753194](https://github.com/benchristian88/atlas-connectors/actions/runs/39883753194)
passed all 35 API requests using the existing Publisher permissions. This does not
prove a release-creation failure or its cause. Subsequent controlled S3
[run 39888883962](https://github.com/benchristian88/atlas-connectors/actions/runs/39888883962)
confirmed `github_http_failure method=POST route=release_create status=403` for
`POST /repos/benchristian88/atlas-connectors/releases`. GitHub
[documents Workflows Write for release targets with workflow differences](https://docs.github.com/en/rest/releases/releases#create-a-release),
as applies to the fixed historical bootstrap target. This motivates the temporary
permission profile; successful bootstrap under it is not yet live evidence.
The HTTP 403 remains unresolved.

S3's reviewed transport reports terminal HTTP failures using only the method,
fixed endpoint label, numeric status and validated, bounded GitHub request ID.
Unknown endpoints use `other`; raw URLs, query strings, credentials, bodies and
arbitrary provider text are excluded. Recovered read retries and expected missing
404s stay silent. Exception categories, authentication, host/redirect restrictions
and write/retry behavior are unchanged. Run 39888883962 supplies actual route/status
evidence. This S4 approval does not change those diagnostics.

## Controlled acceptance and staged bootstrap

Follow the [S4 deployment and mandatory rollback sequence](../catalogue/publication/README.md#s4-deployment-and-mandatory-rollback--owner-actions-only):
S4's implementation merge, adoption and genuine baseline-permission signing
acceptance are complete. Merge this formal approval, then synchronize
`catalogue-verification`'s `VERIFICATION_POLICY` to the complete committed accepted
trust JSON before owner elevation and installation approval. The Publisher App
has not yet been granted Workflows Write. This task changes no GitHub setting or
workflow run.
Acceptance-only evidence continues to be ineligible to authorize publication.

Only after that sequence, perform a new controlled `bootstrap`,
`acceptance_only: false` dispatch from protected main to observe the Publisher HTTP
result using S4 and the preserved S3 diagnostics. It must obtain fresh signed authorization;
do not replay the failed run or reuse its evidence. Bootstrap staging and activation
remain incomplete. Follow the existing P2 two-dispatch
bootstrap: stage/seal original bytes and stop; independently
approve the actual staged pointer digest through a policy PR; activate in a new
first-attempt dispatch. Each dispatch obtains its own startup preflight. Verify
immutable finalization, protected root marker, true current root and exact files.
Existing [bootstrap recovery rules](../catalogue/publication/bootstrap.md) remain
mandatory. No successful bootstrap or secure installation of legacy Proxmox 0.2.0
is claimed: that old mutable package remains ineligible.

Immediately after successful activation, remove Workflows Write from the Publisher
App and verify the installation also returned to the exact baseline. Disable
bootstrap through reviewed policy while retaining approved root pins. Elevation
does not expire automatically. A staging failure requires investigation before a
fresh attempt, with partial drafts/evidence preserved and no automatic permission
changes that could prevent recovery. Remove the GET-only diagnostic workflow only
in a separate reviewed cleanup PR.
