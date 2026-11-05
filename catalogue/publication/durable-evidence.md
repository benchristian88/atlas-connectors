# Catalogue 2 durable publication evidence contract

Current source status: the owner accepted the contract under Atlas ADR 0018,
PR #49 recorded its release-owned fingerprint, and the two existing workflows
now select exact successor S `4be90c5292f931497473595a0958cc5e0f9d1beb`.
The [workflow adoption report](../../docs/catalogue2-workflow-adoption-report.md)
records the active publish-only caller and candidate builder. Following genuine
qualification [run 42006297079](https://github.com/benchristian88/atlas-connectors/actions/runs/42006297079),
the owner accepted S and checked-in signer trust now records
`live_signer_accepted: true`. Hosted `VERIFICATION_POLICY` still requires a separately
authorized false-to-true acceptance change after merge. Actual Catalogue 2
publication remains disabled; keep `CATALOGUE_EVIDENCE_ENABLED` absent/false. See the
[current runbook](README.md). No bootstrap exception or cross-job recovery was added.
Seven assets, original policy bytes, independent
verification, 900/300-second limits and the thirty-second reserve remain enforced.

## Historical Phase 1 implementation boundary

The remainder records the earlier inactive-candidate increment. Its statements
about unset contract approvals, active S4 or unchanged workflow/trust bytes are
historical; the current source status above supersedes them. Historical design
and security evidence is retained without rewriting the original decisions.

The [successor engineering report](../../docs/catalogue2-completion-engineering-report.md)
adds a gated driver, durable checkpoints, candidate registry and inactive workflow
preparation. Historical/selection approvals remain unset; production recovery is
disabled. The Phase 1 implementation boundary below records that earlier increment.

The [security remediation report](../../docs/catalogue2-security-remediation-report.md)
records the later pre-finalization deadline guard, stable historical workflow
templates and anonymous consumer request-budget correction. All approvals remain
unset; the Phase 1 historical boundary below is not an activation procedure.

Status: **Implemented and locally tested as an inactive successor candidate.**
Option A is the owner-approved development direction. No sequence-two publication,
consumer trust activation, production acceptance or installation is authorized.
See the [A–J engineering report](../../docs/catalogue2-phase1-engineering-report.md)
for validation and the proposed Atlas ADR 0012 amendment. Atlas ADR 0012 is not
edited or accepted here; accepted ADR 0013 remains restricted to original sequence one.

## Implementation and deployment boundary

The new `tools/publication_evidence.py` provides bounded original-byte archival,
offline authentication, historical checks and an exclusively local preparation CLI.
`tools/publish_catalogue_evidence.py` subclasses the existing Publisher, preserving
its authority, packages, history, source-tag and recovery checks. Only stage and
finish are successor implementations because frozen S4 hard-codes four assets.
Both candidates are reviewable source, without a workflow entry point or active pins.

All pre-existing tools, seven workflows, trust/policy files, registry and sequence
remain byte exact. Catalogue S4 stays
`2dd1ffcd2f5677dc35bdbc8f68ea28275c91c285`; package S4 remains separate and unchanged.
No production configuration or credential is accessed. The independent live
`CONNECTOR_PUBLICATION_ENABLED` gate must remain disabled; it was neither queried
nor modified. The checked-in historical catalogue policy's `enabled: true` is
preserved; it is a different control, not evidence of a new activation.

A future caller must persist the candidate's same-job checkpoint between phases,
obtain admission through the existing trusted runner-local startup receipt, and
pass that receipt's actual accepted time. A downloaded receipt or arbitrary past
timestamp must never select admission. There is no candidate production driver in
this increment. Freeze/review a successor executable revision and separately
approve workflow wiring and independent implementation/trust pins before any use.
Do not invoke the frozen four-asset CLI against seven-asset candidate releases.

## Exact immutable release inventory

For future ordinary sequence N >= 2, `catalogue-NNNNNN` must contain exactly seven
distinct regular assets. Names use the existing sequence padding convention.

| Canonical filename | Exact bytes retained | Inclusive maximum |
| --- | --- | ---: |
| `catalogue-NNNNNN.json` | Original existing canonical catalogue document | 4 MiB |
| `catalogue.sigstore.json` | Original catalogue build Sigstore bundle | 1 MiB |
| `current.json` | Existing canonical seven-field selection document | 1,024 bytes |
| `current.sigstore.json` | Original selection Sigstore bundle | 1 MiB |
| `preflight.json` | Original canonical `atlas-publication-preflight/v2` document | 256 KiB |
| `preflight.sigstore.json` | Original preflight Sigstore bundle | 1 MiB |
| `policy.json` | Exact `catalogue/publication/policy.json` bytes at caller source C | 16 KiB |

The last three names reuse the existing preflight names and policy basename.
The maximum combined inventory is 7,619,584 bytes. No fourth archive manifest,
portable startup receipt, replacement signature, zip wrapper or second signing
format is introduced. The local archive directory contains exactly the last
three files. Signature bundles and policy bytes are copied without JSON
reserialization. Policy whitespace is significant to its digest. Preflight and
catalogue canonical serialization remain the existing sorted, two-space UTF-8,
LF, one-terminal-newline format. Duplicate JSON keys and malformed encodings reject.

Preparation checks file sizes and regular-file/no-symlink reads. Authentication
recomputes all three SHA-256 values from original bytes. Every release download
must also match its numeric REST asset ID, declared digest, exact size and uploaded
state. Duplicate names, duplicate IDs, unexpected files, wrong repository URLs,
wrong App author/uploader and missing or oversized assets reject. Complete listing
uses the existing bounded provider inventory; overflow does not imply completeness.

## Authentication and selection binding

Consumer authority must come from independently approved consumer-owned inputs:
repository/owner/maintainer, environments, App identities, signer S, verifier binary
and roots, exact policy digests and historical limits. An archive cannot nominate
its own acceptable policy or signer. `ArchiveVerifier` accepts at most 16 explicit
policy digests, with no production defaults. The existing signed authority and
policy validators check both actors, user, run/latest attempt, workflow, source,
required CI, environments, complete five-ruleset bypass observations, and App IDs.

The original `AuthorizationSigstore` runs genuine offline verification using
hash-pinned gh 2.102.1 and unchanged roots. Its existing distinct subject is
`preflight.json`, predicate
`https://atlas-impact.dev/attestations/publication-preflight/v2`. Source digest C,
independent signer digest S, reusable workflow path, issuer, hosted runner,
numeric repository/owner, caller workflow/configuration and original invocation
remain required. Predicate and subject repeat the exact preflight SHA-256.
Parsing or decoding DSSE never authenticates evidence.

Frozen S4 returns the authenticated digest but discards verified timestamp values.
The companion `verified_times` performs a second bounded offline verification of
the identical bytes using that same binary, roots and profile constraints. It
reads only gh's verified statement/timestamps, cross-checks the exact subject/digest,
and requires 1–8 supported Tlog witnesses. Each subprocess retains the existing
30-second/1-MiB output limits and credential-free environment. This deliberate
extra verification preserves frozen implementation files rather than changing
their behavior. Positive new-profile tests mock verified output and are explicitly
distinct from genuine cryptographic acceptance.

The preflight signs C, exact policy digest, original run/attempt, operation and
acceptance-only mode. It does **not** sign a later pointer digest or release/asset
IDs. The original selection signature authenticates those pointer bytes and its
own C/run/attempt. Candidate finalization requires matching preflight/selection
C, run and attempt one, `publish`, acceptance-only false, and independently
verified original dispatch/actors/workflow/CI. It independently retrieves the
selected numeric release and catalogue asset, verifies exact catalogue bytes and
build signature at C, resolves its tag to C, checks published immutability and
rechecks complete inventory after downloads. By-tag and by-ID release identities
must agree. The identical selection and bundle remain in that immutable release.

Supported publication code builds the one declared catalogue sequence from C.
The candidate additionally rejects another numbered N >= 2 release using that
same source C. Together with contiguous history, original-run checks and complete
bounded release enumeration, this prevents supported calls from producing a
second selection from the same source. This is a reviewed-code/co-location
binding proposal, not a new direct cryptographic pointer claim in the preflight.
Atlas must independently approve whether it provides sufficient selection binding.

## Historical time: facts, candidate rules and limits

Live admission is unchanged: completion strictly before expiry within at most
900 seconds from the earliest privileged observation; subsequent same-job work
requires the original runner-local admission and a maximum 1,800-second lifetime.
The candidate rechecks that deadline after its additional verification. Historical
authentication does not feed a past clock or admission into this API and never
extends expiry.

Implemented archival facts/checks:

1. Signed observation start <= completion <= issuance < expiry, with the original
   approved maximum observation age and whole positive Unix seconds.
2. Signed original run/attempt `created_at` <= observation start. Missing or
   unsupported timestamps fail closed. Public run/attempt rereads must agree with
   those signed creation timestamps; all existing original-run checks also apply.
3. All cryptographically verified preflight Tlog times must be >= issuance and
   strictly < original expiry. Invalid, missing, unsupported or unordered evidence
   cannot be interpreted as historical admission.
4. All selection Tlog times must be >= the latest preflight Tlog time. Selection
   must fit an explicitly supplied bound measured from signed issuance.
5. Independently retrieved `published_at` must be >= the latest selection Tlog
   time and within a separately supplied publication-delay bound. Published
   snapshots must supply it; drafts are checked before locking and again afterward.

`HistoricalLimits` has no default values. Each proposed bound must be an explicit
integer from 1 through 1,800 seconds. Test values (900 selection / 300 publication)
are synthetic test policy only. Preparation can authenticate the original
preflight without choosing these limits; binding a selection cannot. These bounds
and the Tlog-within-expiry rule are **candidate restrictions needing owner security
review**, not an accepted historical-time policy. They may reject previously
valid same-job work; no compatibility fallback broadens them. Timestamps accept
timezone-qualified provider/verifier formats and normalize to UTC.

Signed times authenticate producer claims, while Tlog times independently witness
the signature's log integration. They do not prove when every API response was
observed, when live startup was admitted, continuous protection, absence of later
hidden bypass changes, historical installed App/token permissions or freedom from
credential/provider compromise. `published_at` is authenticated GitHub transport
metadata, not a signed publication timestamp. Delayed publication, timestamp
semantics, accepted transparency witnesses, maximum delays and whether a separate
signed final-selection authorization is necessary remain owner decisions.
Historical results explicitly carry `current_authorization: false` and
`consumer_acceptance: false`. Present-day state/currentness still require separate
live public rereads and consumer trust/history enforcement.

## Preparation, immutability and interrupted operations

After existing live admission, stage creates the draft and first uploads the exact
original preflight, bundle and policy, followed by existing catalogue/selection
assets. It never generates a signature. The trusted same-job checkpoint records
release ID and every successfully observed asset name/ID/size/digest, updated after
each upload. A retry compares that checkpoint and all surviving original bytes
before writes; it only fills genuinely missing uploads. Signature bundle equality
is exact even when another bundle could validly sign the same document.

An existing empty draft or one without its original preflight is an orphan and
fails closed. Lost checkpoint, response ambiguity, changed ID, contradictory bytes
or different run/source/policy requires inspection and a separate reviewed recovery
decision. Do not download an unsigned receipt to reconstruct same-job authority.
The local preparation CLI exclusively creates a new directory; an interrupted
partial directory is inspectable and cannot be overwritten on retry.

Finish authenticates the actual surviving selection bundle and original archive
before locking, requires all seven assets, records staged numeric identities,
rechecks live authority and channel, and finalizes. Immediately before its immutable
PATCH, after the last potentially slow read, it requires at least thirty seconds
remaining in the original selection-witness/publication window. The reserve covers
the existing twenty-second provider timeout plus ten seconds of headroom; neither
the proposed 900/300-second historical limits nor original admission is extended.
Already-late or insufficient-budget writes reject while still drafts. Afterward it independently
requires actual `immutable: true`, original catalogue/selection/archive bytes,
all seven unchanged asset IDs/sizes/digests, historical time rules and the original
run. Only then can the existing non-force compare-and-swap advance current.
Failure leaves current untouched. An immutable snapshot is never amended to add
missing evidence. An incomplete already-immutable snapshot is unrecoverable through
these APIs; neither reupload nor replacement signatures are a repair path.

The margin cannot force provider completion time. A provider delay or ambiguous
finalization may still leave an immutable release outside the historical window.
Actual publication metadata must reject it without advancing current. Preserve
original evidence and stop for a separately reviewed disposition; never reinterpret
the timestamp, replace signatures or enable cross-job recovery to make it pass.

If finalization succeeded but current did not advance, existing recovery reads only
the immutable immediate successor, authenticates its original archive/selection
under the original C/run/policy, validates packages/history, and separately requires
a fresh recovery dispatch/preflight. New recovery source/run/evidence never replace
the originals. Recovery performs no immutable asset writes. Durable archival of
the later recovery run's own authorization is **not implemented** here: attaching
it to the original immutable release is prohibited. An owner must decide whether
it needs a separate immutable archive and independent acceptance contract before
operational recovery activation. Candidate tests demonstrate original-evidence
preservation, not approval of that unresolved audit policy.

Bootstrap is unsupported by this candidate. Original sequence one remains exactly
four assets and the unchanged bootstrap pointer pin. Its two historical dispatches
and missing original preflight are not reconstructed. No future sequence can use
its narrowly approved consumer exception. Neither original sequence one nor
Proxmox 0.2.2 is accessed or changed by this local implementation.

## Anonymous consumer retrieval and local review

Atlas can retrieve the selected release with bounded anonymous GETs to the fixed
official `/releases/ID` and `/releases/ID/assets` endpoints, authenticate the by-tag
identity, then download each exact numeric `/releases/assets/ID`. Existing transport
allows only the fixed GitHub release distribution redirect without forwarding
credentials. No Actions artifact, administrative credential, producer receipt,
`/releases/latest` lookup or privileged settings endpoint is needed to recover the
archive. Missing public evidence must reject, without an administrative-token
fallback. This is a consumer implementation handoff, not new Atlas runtime code.

The remediated Atlas future adapter retains numeric REST release/asset binding but
uses application-constructed official `github.com/REPOSITORY/releases/download/TAG/NAME`
URLs for byte transfer, avoiding a redundant REST redirect request per asset.
It never routes through a provider-supplied URL. Exact size/digest, original
signatures, immutable by-ID/by-tag identity, checked public DNS/redirects and final
uncached current confirmation remain required. Its private bounded per-operation
observation set shares no failed responses, refs or releases across operations.
The PostgreSQL fresh 1→2 plus genuine-package activation regression measures forty
combined REST requests and separately counts fourteen release/fourteen CDN GETs.

An exclusively local preparation command is available:

```bash
.venv/bin/python tools/publication_evidence.py \
  --preflight-directory /path/to/original-two-file-preflight \
  --policy /path/to/original-policy-at-C.json \
  --trust /path/to/independently-reviewed-trust.json \
  --policy-sha256 REVIEWED_POLICY_SHA256 \
  --source-commit REVIEWED_SOURCE_C --run-id ORIGINAL_RUN_ID \
  --operation publish --output /path/to/new-local-archive
```

Placeholders are not valid authority. The CLI verifies original preflight validity
and cryptography before creating the three-file directory; stdout contains a
digest/size report explicitly labeled non-authority. It neither publishes nor
selects historical delay limits. A real future fixture, successor workflow wiring,
independent security acceptance, consumer-owned trust approval, matching live pins
and explicit live publication authorization remain separate gates.
