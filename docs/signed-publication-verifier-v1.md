# Historical V1 transition-authorization design

Superseded by [Lean V2](signed-publication-verifier.md) and [ADR 0005](decisions/0005-lean-run-preflight.md). The text below records the former foundation and its unresolved gates, not active operator instructions.

# Signed publication verifier — V1 foundation and V2 handoff

Status: **BLOCKED for production acceptance. Genuine experimental signer evidence
observed; no genuine production authorization acceptance or V2 integration.**
See [ADR 0004](decisions/0004-isolated-signed-publication-verifier.md).

The existing Publisher workflow is unchanged. Its Administration Read token still
fails closed when GitHub omits bypass evidence. The checked-in publication policy
has not been changed: it currently enables bootstrap staging with unset activation
pins. Older P1/P2 prose describing disabled policy is historical, not evidence of
the current file. V1 neither enables a new path nor makes that staging path work
with incomplete evidence.

## Files and independent trust

- `tools/publication_authorization.py`: canonical parser, discriminated schemas,
  shared ruleset validation, freshness/context checks and local challenge consumption.
- `tools/verification_github.py`: bounded fixed-host/endpoint GET evidence transport
  and the sole App-token mint POST.
- `tools/issue_publication_authorization.py`: independent privileged observations
  and issuance; no repository writes and no caller artifact execution.
- `tools/authorization_sigstore.py`: separate offline Sigstore authorization profile.
- `.github/workflows/catalogue-verifier.yml`: reusable isolated job, native signing,
  exact-profile self-verification and export of two public files only.
- `catalogue/publication/verifier-trust.json`: deliberately unconfigured trust template.

The trust object has exactly `schema`, `live_signer_accepted`, `signer_revision`,
`ruleset_ids`, `verification_environment_id` and `max_observation_age_seconds`.
Issuer jobs read its operator-managed counterpart from environment variable
`VERIFICATION_POLICY` (a GitHub environment variable, not a caller input). Future
consumers must load independently reviewed trust pins, never copy them out of a
grant or use the caller's unsigned request as trust policy. The publication policy
is separately fetched at the original caller commit; its exact bytes are hashed,
not a re-encoded dictionary. The consumer accepts those exact locally established
policy bytes.

The implementation is committed, but no production signer revision, five ruleset
IDs or verification environment numeric ID has been accepted in the trust template.
Those pins remain null and `live_signer_accepted` is false. The experimental commit
is not a production trust pin. Synthetic test IDs are not settings recommendations.
V1 provides no dispatch entry point and no production acceptance override.

## Canonical request and authorization contract

Canonicalization reuses Atlas's deterministic JSON writer: UTF-8, lexically sorted
object keys, two-space indentation, LF and one terminal newline. It is not a claim
of RFC 8785 canonicalization. Byte parsing explicitly decodes UTF-8 and rejects
noncanonical formatting, BOM/UTF-16/UTF-32, duplicate keys, nonfinite values and
oversized documents. Request and policy limits are 16 KiB, authorization 256 KiB,
bundle 1 MiB and combined verifier output 1 MiB. The offline process has a
30-second deadline and no ambient tokens, proxies, configuration or executable PATH.

The request has exactly these fields:

| Field | Binding |
| --- | --- |
| `source_commit` | Original publication dispatch commit, lowercase Git SHA |
| `policy_sha256` | SHA-256 of exact publication policy file bytes at that commit |
| `run_id`, `run_attempt` | Original caller run; attempt must be integer 1 |
| `operation` | Explicit `publish`, `bootstrap` or `recover` |
| `transition` | One supported mutation type from the table below |
| `challenge` | 64 lowercase hex characters; V2 must generate 256 unpredictable random bits |
| `target` | Exact variant for that one operation; no unassigned-ID placeholders |

The signed document has exactly `schema`, `authority`, `source`, `execution`,
`rulesets`, `target` and `freshness`:

| Section | Exact content |
| --- | --- |
| `schema` | `atlas-publication-authorization/v1` |
| `authority` | Numeric repository/owner/maintainer, Publisher App/installation and Verifier App/installation IDs |
| `source` | `commit`, `policy_sha256`, `verifier_revision`, `signer_workflow` |
| `execution` | `workflow`, `run_id`, `run_attempt`, `operation`, `transition`, `challenge` |
| `rulesets` | `ids`, `observations`, `sha256`, `approved_bypass_actors` |
| `target` | Same exact transition variant as the independently established request |
| `freshness` | Integer UTC seconds: `observation_started`, `observation_completed`, `issued_at`, `expires_at` |

All controlled objects reject extra/missing fields, including asset rows and prior
state. Ruleset observations retain the **complete provider JSON**, including API
metadata; provider metadata is not a closed Atlas schema. JSON parsing remains
strict for those objects. Five exact name/ID/source records are required, sorted
by name, with no inherited/unexpected/duplicate/missing rulesets. Explicit bypass
arrays must match the original policy exactly; the Verifier App is never approved.
Their digest covers canonical bytes of the full observation array. The original
protection validator remains the single authority for protection semantics.

Every target has `sequence`, `catalogue_sha256`, `snapshot_source_commit` and
`expected_prior`. Normal prior state has exactly `kind: selected`, `channel_sha`,
`pointer_sha256`, `sequence`, `release_id`, `catalogue_asset_id`, `catalogue_sha256`;
the target is its immediate successor. Bootstrap prior is exactly
`{kind: bootstrap-empty}`, except create-current requires
`{kind: marker-created, marker_sha: <next_channel_sha>}`. This describes provider
observations, not a substitute for authenticated history. Bootstrap source/digest
are pinned to the original frozen sequence-one evidence. Publish snapshot source
must equal publication source; recovery may select an independently authenticated
older snapshot source.

| Transition | Operations | Additional target fields |
| --- | --- | --- |
| `stage-create-draft` | publish, bootstrap | **Issuance blocked:** `draft_visibility_unproven`; schema reserved for V2, with no future release/asset IDs |
| `stage-upload-catalogue` | publish, bootstrap | `release_id`, `artifact_name`, `artifact_sha256`; the build-bundle variant also requires `catalogue_asset_id` |
| `seal-upload-selection` | publish, bootstrap | `release_id`, `catalogue_asset_id`, `catalogue_bundle_asset_id`, `catalogue_bundle_sha256`, `pointer_sha256`, `artifact_name`, `artifact_sha256`; the selection-bundle variant also requires `pointer_asset_id` |
| `finish-finalize-release` | publish | `release_id`, `assets`, `pointer_sha256` |
| `activate-finalize-release` | bootstrap | `release_id`, `assets`, `pointer_sha256` |
| `finish-advance-current` | publish | `release_id`, `assets`, `pointer_sha256`, `next_channel_sha` |
| `recover-advance-current` | recover | `release_id`, `assets`, `pointer_sha256`, `next_channel_sha` |
| `activate-create-marker` | bootstrap | `release_id`, `assets`, `pointer_sha256`, `next_channel_sha` |
| `activate-create-current` | bootstrap | `release_id`, `assets`, `pointer_sha256`, `next_channel_sha` |

Upload `artifact_name` is a strict additional discriminator: catalogue bytes or
`catalogue.sigstore.json` in stage, `current.json` or `current.sigstore.json` in seal.
Required predecessor assets must already exist with their exact IDs/digests, and
the upload destination must be absent. No grant authorizes replacing an asset.
`assets` is exactly four names, each with exactly `{id, sha256}`; IDs are unique.
Catalogue and pointer digests must agree with the target. Bootstrap build-bundle
digest and separately approved activation pointer are also checked. Draft creation
cannot preapprove GitHub's future IDs; each upload requires a newly observed grant.

## Implemented evidence and signature checks

Before credentials, the issuer requires the exact numeric repository/owner,
first-attempt main dispatch, original run/source, caller workflow, hosted runner,
explicit operation and accepted reusable revision. It then independently reads:

1. JWT-authenticated `/app` and repository installation: exact App/installation,
   account, selected repositories, permissions and unsuspended status.
2. Scoped token mint and token-authenticated installation repository enumeration:
   exactly one numeric repository, with exact permissions. No token action output
   or caller-provided installation metadata substitutes for those observations.
3. Source policy and existing `check_authority` evidence: repository, protected main
   at source, publication environment, original run, attempt 1, workflow, public
   maintainer identity, original/triggering human actor and successful `validate`
   from GitHub Actions App 15368 for that exact source.
4. The run's single SHA-pinned reusable-workflow reference, unchanged Publisher App
   permissions, exact verification environment protections and immutable-release setting.
5. Complete five-ruleset list/details and the original exact protection checks.
6. Current/marker presence or exact prior channel/pointer, target draft/immutable
   release, release source, exact known asset identities/digests and next commit
   parents. `stage-create-draft` is unconditionally rejected before credentials or
   provider reads, signing or export, with fixed diagnostic `draft_visibility_unproven`.

GitHub's [release listing API](https://docs.github.com/en/rest/releases/releases#list-releases)
can omit drafts when the credential lacks push access. The Verifier App retains
Contents Read; an empty or apparently complete listing therefore cannot establish
draft absence. There is no enable toggle, and caller flags, inventory-completeness
claims or token metadata cannot bypass the rejection. Complete draft visibility
remains an unresolved **V2 acceptance gate** requiring an independently reviewed
evidence design and genuine provider evidence. Acceptance of the signer alone
cannot enable draft creation. Other transition types retain their existing checks;
failure to retrieve required draft/asset evidence still stops them.

Provider asset digests must be strings matching exactly `sha256:[0-9a-f]{64}`.
Only after this check is the hexadecimal portion extracted. Missing prefixes,
alternative algorithms, uppercase digests, non-string/missing/null values, invalid
lengths/characters and whitespace are rejected without normalization or coercion.

This is a security authorization foundation. Caller-provided artifact hashes are
data constraints, not proof of build provenance. The issuer does not download or
execute caller artifacts, authenticate package bytes, reconstruct full catalogue
history or verify a proposed Git tree's blobs. V2 must preserve P1/P2's existing
cryptographic artifact, history, tag, root-tree and package-eligibility checks in
the independently trusted transition consumer. A signed grant never replaces them.

Evidence transport uses a fixed GitHub host and endpoint allowlist, no proxy,
redirect, pagination following or retry. It rejects any Link header, unexpected
encoding/content type/status, ambiguous lengths, truncated/oversized bodies and
duplicate JSON keys. Requests use at most 20-second socket timeouts and a shared
50-second observation deadline; an already-blocked socket may take its remaining
timeout before returning. Scope/check enumeration and asset inventory fail on
overflow. Release listings are not used to infer draft absence; draft-creation
issuance remains blocked regardless of the listing response.

Signing uses the pinned `actions/attest` subject-path with a custom predicate,
then verifies the actual resulting bundle before export. The sole subject is
`authorization.json` with the actual SHA-256. The predicate is exactly
`{schema: atlas-publication-decision/v1, authorization_sha256: <actual_digest>}`.
It therefore signs the exact bytes through their authenticated subject digest;
it is not a raw detached signature directly over the JSON file.

The [CLI documentation](https://cli.github.com/manual/gh_attestation_verify) identifies
verified certificate fields and transparency timestamps as authenticated evidence.
The profile checks exact SAN/buildSigner URI at the production reusable workflow's
`refs/heads/main` ref, an independently pinned buildSignerDigest, caller buildConfig
URI/digest, OIDC issuer, source URI/numeric
IDs/owner URI/ref/commit, public visibility, hosted runner, dispatch trigger and
original invocation URI. It rejects missing/extra subjects, wrong predicate or
digest, missing transparency witnesses and malformed/bounded results. The existing
hash-pinned roots and gh authenticate certificate/signature/log evidence before
any of these fields are read. No custom trust root or binary can come from the grant.

`AuthorizationVerifier(trust, policy_raw).verify_and_consume(raw, bundle, expected)`
then requires exact locally established request equality, exact policy-byte hash,
all schemas/protections and freshness before and after real verification. Its
challenge set lives only in that object. The consumer must run sequentially and
must recheck freshness/provider state immediately before mutation. Recreating
the object, restarting the process or another job loses that local set.

## Credential isolation and platform acceptance blockers

The reusable job uses a separate hosted runner. Only the issuer step receives
`VERIFICATION_APP_PRIVATE_KEY`; it removes it from its environment before signing
the JWT with a mode-0600 temporary key file. No token is written to outputs,
artifacts, caches or logs. The installation token expires naturally; no revocation
DELETE is performed. Python strings are not claimed to be securely zeroized.
Attestation and artifact actions use their separate job token after the issuer
process exits. Only the two explicitly named public files are uploaded on success.

GitHub's [current job context documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#job-context)
provides `job.workflow_sha`, `workflow_ref`, `workflow_repository` and
`workflow_file_path` for the defining reusable workflow, unlike caller-associated
`github` context. The workflow reads these through `toJSON(job)`, checks them
against the exact production path/main ref and independent SHA pin before checkout
or the credential-bearing step, then checks out that pinned revision. Missing
fields, wrong SHA, wrong branch/path/repository and disabled acceptance fail closed.
These fields are documented for GitHub.com, not GHES.

### Genuine identity evidence and corrected representations

Successful experiment
[39846232008, attempt 1](https://github.com/benchristian88/atlas-connectors/actions/runs/39846232008)
at `e5287c3229f5b9a1dc4c3dbcda0f4193fe221c3c` supplied a genuine bundle from the
credential-free reusable probe. The exact [public subject and bundle](../tests/fixtures/verifier_signer_probe/README.md)
are preserved separately from historical P1/P2 fixtures, independently verified
with unchanged pinned gh/roots, and covered by real tampering/substitution tests.
The original run API was independently read as well.

| Surface | Genuine probe observation | Production validation after correction |
| --- | --- | --- |
| Certificate subjectAlternativeName / buildSignerURI | `https://github.com/benchristian88/atlas-connectors/.github/workflows/verifier-signer-probe.yml@refs/heads/main` | Same origin, exact `catalogue-verifier.yml@refs/heads/main`; old SHA URI and other paths/branches rejected |
| Certificate buildSignerDigest | `e5287c3229f5b9a1dc4c3dbcda0f4193fe221c3c` | Exact independently configured `trust["signer_revision"]`, also passed to CLI `--signer-digest` |
| Job workflow_ref / workflow_sha | Probe workflow at `@refs/heads/main` / exact source SHA | Exact production main-ref workflow and independent trusted SHA before checkout/credentials |
| Caller API referenced_workflows.path / sha | Probe path at `@e5287c3229f5b9a1dc4c3dbcda0f4193fe221c3c` / that same SHA | Exact production path at `@<trusted signer SHA>` and exact matching sha; unchanged |

The signed subject's job fields are workflow-reported diagnostics bound by its
signature, not certificate extensions. API metadata is separate provider evidence.
In particular, do **not** replace the issuer's SHA-suffixed API check with the
job's branch-ref representation. The issuer's internal `VERIFIER_WORKFLOW_REF`
is still constructed from the trusted revision as a SHA-suffixed identity; it is
not a copy of `job.workflow_ref`, and its existing validation remains unchanged.

The genuine certificate's buildConfigURI identifies the experimental caller at
`refs/heads/main`, and buildConfigDigest/sourceRepositoryDigest identify the caller
source SHA. Production continues to require the original `catalogue-publish.yml`
caller, exact source/ref, run/attempt, issuer, numeric repository/owner IDs and
hosted runner. The only implementation changes are the two main-ref comparisons;
all digest, production predicate/subject and transparency checks remain strict.
This probe uses a different workflow, predicate and `probe.json` subject and cannot
authorize production publication. No genuine production authorization is claimed.

GitHub's [reuse guide](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)
describes called-job environment secrets. This is not a repository-wide ACL:
another main workflow can request that environment. Same-repository administrator
or trusted-source compromise can leak an Administration Write key and mutate
protections. The isolated runner and exact reusable signer prevent access from
the existing publisher job under the reviewed workflow; they do not eliminate
that administrative trust. One maintainer still has no independent human veto.
GitHub does not validate the signed grant before honoring a Publisher App API
request. V2's reviewed consumer code enforces it; a stolen Publisher token can
still exercise its existing Contents Write/bypass powers. Consumer provenance,
selection, history and rollback verification remain separate necessary defenses.

Before production acceptance, **separately authorized** controlled acceptance
must obtain a genuine production verifier bundle, verify it with pinned gh, confirm all
certificate/run/job identities, retain a reviewed positive fixture, and measure
end-to-end latency. Do not set `live_signer_accepted: true` based on unit tests.
The production workflow intentionally cannot be used to bypass that acceptance
gate; an experiment needs its own reviewed scope. Nothing in this change triggers
or authorizes that experiment.

### Verifier pin lifecycle remains a V2 gate

The successful experiment called the probe through a local same-commit reference.
[GitHub's local-call semantics](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows#calling-a-reusable-workflow)
mean that `uses: ./.github/workflows/catalogue-verifier.yml` would execute at the
publication caller commit C. With trusted signer S, advancing main to C different
from S changes job.workflow_sha and buildSignerDigest to C even if verifier file
contents are unchanged. The exact S pin must reject that run before credentials;
the consumer would reject its certificate too. Checking out S afterward cannot
pin the already selected workflow implementation.

V2 must independently pin verifier workflow execution at S while allowing normal
catalogue source C to advance. Prefer a literal full-SHA job reference
`benchristian88/atlas-connectors/.github/workflows/catalogue-verifier.yml@<S>`,
with the same independently reviewed S in verifier environment policy and consumer
trust. Verify caller/source/buildConfig against C and signer digest/job SHA/checkout/
API path and SHA against S. Only an explicit security-reviewed pin change approves
new verifier code. Never accept any signer SHA, trust current main automatically,
or substitute a post-start checkout for an execution pin.

The observed local call had C = S. A further harmless experiment must use an
explicit SHA reference and a later caller commit to establish exact certificate
and job URI representations and independent C/S claims. A SHA-pinned call may
produce SHA-suffixed signer/job refs; this has not been demonstrated by the local
probe. Today's corrected exact main-ref checks must reject any other spelling.
Any narrowly specified change for an explicit call requires fresh genuine evidence
and separate security review; no dual-ref fallback is added here. V2 must also
demonstrate production environment credential delivery/isolation and exact provider
permission responses. This correction neither integrates V2 nor changes those gates.

## Exact V2 transition/job requirements

Every verifier call must use a literal reviewed 40-character `uses:` SHA, from the
same fresh main publication dispatch, in a separate job without `secrets: inherit`.
Only the verifier job selects `catalogue-verification`; only fixed publisher jobs
select `catalogue-publication`. Never colocate the keys, use a composite action
as an isolation substitute, or execute downloaded packages in either credential job.
Both caller and called jobs need GitHub's native attestation permissions.

1. **Stage:** independently establish policy/source, candidate provenance,
   qualified package provenance and immutable IDs, accepted current history and
   contiguous sequence. Establish a random challenge in trusted consumer context,
   resolve the unproven draft-visibility gate before implementing or enabling
   `stage-create-draft`; V1 currently rejects this transition unconditionally.
   After that separate review, verify/consume a grant for exactly one create. Use draft,
   non-prerelease, `make_latest: false`, derived snapshot tag and exact
   `snapshot_source_commit`; bootstrap also retains its frozen operation body.
   Read assigned release ID; separately authorize each catalogue/build-bundle
   upload, reading and binding assigned predecessor IDs. Never pass the first
   grant to later writes. Read-only resume skips exact already-authenticated
   assets; conflicting assets stop.
2. **Seal:** construct the unchanged seven-field pointer from actual IDs and
   predecessor bytes. Separately authorize pointer upload and selection-bundle
   upload. Keep selection signing on the existing `catalogue-publish.yml` profile,
   verify its original maintainer/source invocation, and retain genuine bundles
   on resume. Bootstrap stage stops with four exact draft assets; a separately
   reviewed activation policy/source and fresh dispatch remain mandatory.
3. **Activate:** authenticate original frozen evidence, legacy release/asset/tag,
   inventory and all four staged assets/signatures, approved pointer hash and
   distinct staging/activation source/run. Request `activate-finalize-release`
   immediately before finalization; read back immutable flag and identical IDs/
   bytes. Construct/verify the root with exactly two ordinary blobs and no parents.
   Separately authorize `activate-create-marker`, then `activate-create-current`
   against the observed marker SHA. Never delete/reset the marker, automatically
   recreate a missing current branch or replay a lost marker response.
4. **Finish:** reauthenticate source/policy/dispatch, packages and full history,
   exact staged pointer/signature and all asset identities. Separately authorize
   `finish-finalize-release`, verify actual immutable release and exact bytes,
   prepare a commit with exactly the selection files and the accepted parent,
   then obtain `finish-advance-current` for its **already known** SHA. Recheck
   predecessor/freshness and use a non-force update. Verify exact ref/tree/bytes
   afterward. Object/tree creation is inert preparation, not permission to advance
   refs; V2 must narrowly constrain those preparatory API writes too.
5. **Recover:** fresh original-run authority, authenticated current high-water and
   immutable immediate successor only; preserve original selection invocation,
   catalogue history and package eligibility. Never rebuild old bytes or finalize
   a draft through recovery. Prepare/verify the single-parent commit, then request
   `recover-advance-current` for exact predecessor, immutable IDs and next SHA.
   No successor is a read-only no-op, not an authorization to initialize history.

V2 must retain concurrency serialization and local challenge consumption, but
cannot claim cross-process exactly once. After ambiguous mutation, inspect state
without automatic retry. A new job/process needs a fresh challenge/observation;
provider create-only identities, immutable records, non-force parent constraints
and the protected bootstrap fence provide the durable state bounds. GitHub does
not atomically bind settings observations to later writes. Rechecking narrows the
race; a signature and 60-second budget cannot eliminate it.

## Operator prerequisites and local validation

No settings are changed here. After independent experiment/review, operators must
pin the actual implementation SHA, all five ruleset IDs and verification environment
ID in independently reviewed consumer trust and the environment's `VERIFICATION_POLICY`.
Retain the existing App permissions, environment key/ID variables, protected-branch
restriction and disabled admin bypass. Keep the Verifier App absent from **every**
bypass list. Protect changes to workflow/source/trust/environment configuration.
Review latency before choosing an operational freshness budget; this implementation
does not accept a value greater than 60 seconds. Integrate/review V2 separately,
then perform genuine acceptance before any publication-readiness claim.

Local tests distinguish synthetic API/verified-output tests from real pinned-gh
verification. Existing genuine catalogue/package fixtures still verify under their
old profiles and are rejected under the authorization profile. The genuine probe
fixture verifies only under its experimental profile and is also rejected as a
production grant, even with matching test-only source/signer digest pins. A genuine old fixture also checks
the CLI's supported separate signer/source flag combination. Synthetic output tests
do not establish production signer acceptance. The probe provides genuine evidence
only for the documented local-call identity semantics. Ansible tests continue to exercise
the pinned reviewed collection without a live Proxmox source.

```bash
.venv/bin/python -m pytest -q tests/test_publication_authorization.py tests/test_authorization_sigstore.py tests/test_verification_github.py tests/test_verifier_workflow.py
.venv/bin/python -m pytest -q tests/test_publication_contract.py tests/test_publication_state.py tests/test_publication_bootstrap.py tests/test_publication_transport.py tests/test_publication_crypto.py tests/test_publication_packaging.py tests/test_ruleset_visibility.py
ATLAS_TEST_COLLECTIONS_PATH=/tmp/atlas-v1-verifier-test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q
actionlint .github/workflows/*.yml
.venv/bin/python -m compileall -q tools tests
git diff --check
```

No live credentials, Git mutations, workflow dispatches, releases, refs, settings
changes, Atlas/SDK changes or remote publication are part of this task.
