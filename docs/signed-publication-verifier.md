# Lean V2 signed publication preflight

Status: **Reviewed implementation frozen and acceptance trust configured; production activation BLOCKED pending genuine acceptance.**
[ADR 0005](decisions/0005-lean-run-preflight.md) supersedes the V1 transition-grant
architecture. The [operator runbook](../catalogue/publication/README.md) is the active
procedure; [V1 documentation](signed-publication-verifier-v1.md) is historical.

The checked-in publication policy is unchanged: enabled, bootstrap `stage`, with
both root approval pins unset. That does not activate V2. Verifier trust remains
`live_signer_accepted: false`, with signer/ruleset/environment pins configured in
[verifier-trust.json](../catalogue/publication/verifier-trust.json). The operator
must copy that exact JSON into `catalogue-verification`'s `VERIFICATION_POLICY`
environment variable before the first acceptance-only dispatch. No live workflow,
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

The Publisher App remains **5422372 / 174027755**, Contents Write, Actions Read,
Administration Read and Metadata Read. Its key exists only in the Publisher job's
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
`00c85f688a43fb6da44acb3fa713d938e30a6da9` (S2), the reviewed Lean V2 implementation
including the required verifier secret declaration, merged into protected main
with passing CI. All three executable workflow pins
and repository signer trust now identify S. The next protected-main merge of
these configuration changes becomes C; its actual SHA is not yet known, and
C must differ from S. The catalogue/source checkout stays `${{ github.sha }}`.
Never derive S from current main or replace it with a moving reference.

Repository trust pins verification environment **25016263801**, all five verified
ruleset IDs and a **900-second** startup age. Its acceptance flag remains false.
Configure the independent GitHub environment variable with JSON identical to that
file, then follow the [single bootstrap acceptance-only dispatch](../catalogue/publication/README.md#minimum-genuine-signingisolation-acceptance).
The Publisher job must remain skipped. No remote configuration or dispatch is
performed by this pinning task, and production activation remains blocked.

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
experiment. That establishes the mechanism; it does not accept this production
workflow, new schema, App isolation, environments or startup path. No new genuine
V2 fixture or live acceptance is claimed from synthetic verified-output tests.

## Controlled acceptance and staged bootstrap

Follow the [operator checklist](../catalogue/publication/README.md). The minimum
credential/signing acceptance is one fresh `bootstrap`, `acceptance_only: true`
main dispatch at the future C once `VERIFICATION_POLICY` matches the committed
trust JSON for frozen S. Keep both copies of trust unaccepted. Verify the exported
preflight offline, independently check
C/S and run/attempt/operation/policy, complete rulesets, environments and immutability,
and confirm the Publisher job was skipped and no publication credentials or writes
occurred. Preserve public artifacts before their one-day expiry and review the
actual isolation/configuration, not merely a green badge.

Only a separate reviewed trust change can admit publication. Then execute the
existing P2 two-dispatch bootstrap: stage/seal original bytes and stop; independently
approve the actual staged pointer digest through a policy PR; activate in a new
first-attempt dispatch. Each dispatch obtains its own startup preflight. Verify
immutable finalization, protected root marker, true current root and exact files.
Existing [bootstrap recovery rules](../catalogue/publication/bootstrap.md) remain
mandatory. No successful bootstrap or secure installation of legacy Proxmox 0.2.0
is claimed: that old mutable package remains ineligible.
