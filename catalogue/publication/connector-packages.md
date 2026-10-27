# Controlled Connector package publication

Phase 4B.2 prepares all four local bindings to reviewed implementation **S3**,
`be24042c4e7446c7d88d2f08608ab7f058bb24b6`. The certificate correction was
squash-merged through [PR #41](https://github.com/benchristian88/atlas-connectors/pull/41)
at this exact SHA; its required `validate` check passed. The separate S3 repinning
change is local and uncommitted, pending human review/CI/merge.
**Publication remains disabled.** Both package-trust flags remain false. The first
acceptance-only run failed before checkout/signing under original S. After S2
repinning merged through PR #40, original run `40534608937` completed observations
and signing, then failed local certificate authentication. Its genuine immutable
signer URI disagrees with S2's main-ref certificate expectation. S3 requires exact
`@trust["signer_revision"]` identities and matching signer digest. This repin
preserves the reviewed S3 executable files and makes no live setting changes.
Successful genuine S3 acceptance remains pending. No acceptance or publication
is authorized by this local work. See the
[genuine certificate correction report](../../docs/phase-4b2-sigstore-qualification.md)
for preserved evidence, independent authentication and unavailable subject bytes.
See [proposed ADR 0006](../../docs/decisions/0006-connector-package-publication.md),
the historical [PR2 qualification report](../../docs/phase-4b2-pr2-local-qualification.md)
and [identity correction qualification](../../docs/phase-4b2-identity-qualification.md),
the historical [S2 repinning report](../../docs/phase-4b2-s2-local-qualification.md)
and the current [S3 repinning report](../../docs/phase-4b2-s3-local-qualification.md).

This upgrades the trusted publication engine, not the Connector package version.
The proposed package remains Proxmox 0.2.1. Routine future releases select their
reviewed tag/version, source P and digest D as data; they do not require a new
implementation SHA pin unless the publication engine changes. Caller C, trusted
engine S and package source P remain independent identities.

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
disabled publication, acceptance-only Publisher exclusion and first-attempt/main/
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
original subject contents and unobserved hosted CLI exit status. Genuine acceptance
requires a future successful original run and independent signed-evidence review.

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

## S3 rollout — local preparation and future human gates

PR #41 established exact S3 `be24042c4e7446c7d88d2f08608ab7f058bb24b6`.
All four bindings are prepared locally: reusable Verifier `uses`, Publisher
trusted executable checkout, `ATLAS_IMPLEMENTATION_REVISION` and package trust
`signer_revision`. The six reviewed S3 executable files are frozen. Tests separate
the unchanged genuine S2 evidence from synthetic prospective S3 behavior.

After the human commits, pushes, reviews, completes required Python 3.12 CI and
merges this repinning PR, the following owner-only steps remain. They are
documented here and must not be performed as part of local pinning:

1. Update repository Actions variable `CONNECTOR_VERIFICATION_POLICY` from the
   new committed trust JSON, preserving `enabled: false` and
   `live_signer_accepted: false`.
2. Verify effective repository/environment configuration and absent or identical
   policy overrides; the effective publication enable gate must remain false.
3. Independently select and reproduce exact package source P and digest D.
4. Obtain separate authorization for a new original main acceptance-only run.
5. Preserve and independently authenticate its genuine certificate, statement,
   original preflight and complete security observations.
6. Confirm Publisher skipped, no Publisher credential operations and no tag or
   release created. Successful signing alone does not establish acceptance.

The remaining procedure uses **S** for exact reviewed **S3** above, after its
separate reviewed repin and owner configuration. Do not substitute a branch,
PR head or caller C for S3.
The PR2 baseline section below records the original S deployment, not authority
to dispatch its known failing workflow again.

## Administration prerequisites — owner verification required

Historical owner-reported observations from the earlier qualification: both `catalogue-verification` and
`catalogue-publication` exist with their original App secrets/variables, neither
has a conflicting environment-level `CONNECTOR_VERIFICATION_POLICY`, and the
repository variable contained previous S. `CONNECTOR_PUBLICATION_ENABLED`
was absent. Both environments reported **Protected branches only**, applying
to exactly `main`; the five Atlas rulesets remain, and a complementary classic
branch protection rule for `main` was added to make that environment restriction
effective. These observations are not independent privileged qualification, and
current effective values have not been inspected during this local S3 repin.
Before dispatch, the owner must verify the live branch restriction really selects
only main, complete protections/bypass visibility and effective variable values.
This local change does not modify settings, original catalogue `VERIFICATION_POLICY`,
secrets, App permissions, environments or rulesets.

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
permissions in the Verifier's signed pre-token admission.** The proposed owner
security decision is to accept this split as the least-privilege boundary. It does
not give the Verifier independent knowledge of the Publisher's effective grant.
ADR 0006 remains Proposed: final owner acceptance and activation are separate.
No Verifier permission expansion, Publisher credential sharing or secret move is
part of this design. Local tests do not verify live installed scope, key custody,
or uninterrupted hidden bypass configuration.

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

## Historical PR2 baseline and current independent configuration

PR #37 merged at original S `d6601ad97815a85da164e4329766ea17b62bddc9`;
PR2 bound all four identities to that S. The failed acceptance used that historical
deployment. PR #40 subsequently deployed S2; the current pinning change replaces
only those S2 bindings with S3.
`connector-verifier.yml`, its helpers, vendored SDK/hash lock, gh 2.102.1 and frozen
roots remain the reviewed executable distribution at S3. Code in a subsequent
pinning commit does not become executable authority merely because advancing
caller main **C** contains it.
The package-source commit **P** is a third identity, carried as request data; it is
not the caller C or the implementation S by definition. P may coincide with C
only when separately reviewed that way.

Before a future dispatch, the owner must independently confirm:

1. PR #41 and the separate S3 pinning PR above passed their required review
   and Python 3.12 `validate` CI and were merged into main. Record that exact
   dispatch caller C and its successful CI. C must contain
   all four S bindings and the complete disabled/unaccepted package trust JSON.
2. Review every field in [connector-trust.json](connector-trust.json), including
   the schema, S, both false flags, 900-second freshness limit, five ruleset IDs and
   Verifier environment ID. Independently inspect the configuration table above,
   complete privileged bypass visibility, App registrations, environment protection
   and existing secret availability. None of these live settings is certified by
   the local pinning work.
3. **After the S3 pinning PR is merged and before the next dispatch**, update the
   existing **repository Actions variable** `CONNECTOR_VERIFICATION_POLICY` at
   repository Settings → Secrets and variables → Actions → Variables to the exact
   complete JSON from the new committed `catalogue/publication/connector-trust.json`,
   including exact S3 and both false flags. This is
   public trust configuration, never a secret or downloaded authority. It must
   parse identically to C's checked-in package trust. The Publisher captures
   `${{ vars.CONNECTOR_VERIFICATION_POLICY }}` in its **job-level `env`**, whereas
   the reusable Verifier reads it in **step-level `env`** after entering
   `catalogue-verification`. Environment-only configuration is insufficient for
   this caller. Use the repository variable as the common source; prefer no
   same-name override in either `catalogue-verification` or `catalogue-publication`.
   If existing environment copies are retained, independently confirm their complete
   parsed JSON matches the repository value and C exactly before dispatch.
4. GitHub gives repository variables precedence over organization variables;
   environment values become available after the job starts. They cannot replace
   contexts already captured in job-level `env`; step evaluation after entering an
   environment can see that environment's variables. Thus same-name repository and
   environment variables are not interchangeable. Both workflows use the caller
   repository's variables. See GitHub's [variable precedence and timing](https://docs.github.com/en/actions/reference/workflows-and-actions/variables#configuration-variable-precedence)
   and [vars context](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#vars-context).
   A mismatch fails closed against C's trust and the actual reusable job SHA.
5. Repository `CONNECTOR_PUBLICATION_ENABLED` must be absent or the literal string
   `false`. Inspect organization inheritance too: no inherited effective `true`
   may be present. This job-level condition is evaluated before any Publisher
   environment is entered; an environment variable cannot serve as that gate.
   Leave original catalogue `VERIFICATION_POLICY`, `verifier-trust.json`, all App
   scopes, IDs, secrets, protection settings and catalogue state unchanged.
6. Confirm the existing Verifier key can be supplied through the explicit named
   secret mapping to the reusable job's `catalogue-verification` environment.
   GitHub's [reusable secret rules](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows#using-inputs-and-secrets-in-a-reusable-workflow)
   give that job's same-name environment secret precedence; `required: true`
   checks the mapping, not a nonempty secret value. Do not extract, copy or move
   either key. A custody/availability discrepancy is an operational prerequisite
   for the owner to resolve separately, never a reason to pass Publisher credentials
   to the Verifier. The Publisher environment/key is not entered or exercised by
   acceptance.

These are owner-operated prerequisites, not instructions for this local increment
to change settings. Missing live confirmation does not establish a local code
failure or confer remote authority.

## Future owner-operated acceptance-only request — do not dispatch here

Establish P and D before approving any request:

1. Select exact committed **P** independently of S3 and the pinning merge commit.
   Preserve authenticated main ancestry, the merged reviewed PR whose merge SHA
   is P, successful required Python 3.12 `validate` for P and qualified Proxmox
   0.2.1 metadata. Record the intended current main caller C separately. The later
   Publisher also requires P's entire workflow directory to match C's; a source
   predating repinning may not meet that conservative permission rule. Resolve
   source selection through review, never by changing S3 or App permissions.
2. Prepare separate clean detached local checkouts at exact S3 (trusted tools) and
   P (source data), using new directories. Verify both HEADs and clean inventories.
   Use S3's hash-pinned SDK and existing reviewed dependencies. Do not run P's
   helpers, requirements, workflows or playbooks. Store build output outside both
   checkouts. No tag is required for this source-only reproduction.
3. With `ATLAS_S3_TOOLS`, `ATLAS_PACKAGE_SOURCE_DIR`, `ATLAS_PACKAGE_SOURCE` and
   `ATLAS_PACKAGE_REVIEW_OUTPUT` set to those reviewed paths/P and a new empty output
   directory, run the following local preparation from outside P. It uses S3's
   existing source-data adapter and exact-source checks. Review the two equal
   archives, Manifest, SPDX/licence/qualification validation and resulting D.

```python
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

S3 = "be24042c4e7446c7d88d2f08608ab7f058bb24b6"
tools = Path(os.environ["ATLAS_S3_TOOLS"]).resolve()
source = Path(os.environ["ATLAS_PACKAGE_SOURCE_DIR"]).resolve()
P = os.environ["ATLAS_PACKAGE_SOURCE"]
output = Path(os.environ["ATLAS_PACKAGE_REVIEW_OUTPUT"]).resolve()
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tools, text=True).strip() == S3
assert not subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=tools)
sys.path.insert(0, str(tools / "tools"))
from publish_connector import package_source
import release_connector
from connector_publication_contract import check_input
from publication_contract import canonical_json

with package_source(source):
    first = release_connector.prepare("proxmox-v0.2.1", output / "first", commit=P)
    second = release_connector.prepare("proxmox-v0.2.1", output / "second", commit=P)
raw = (output / "first/proxmox-0.2.1.tar.gz").read_bytes()
assert raw == (output / "second/proxmox-0.2.1.tar.gz").read_bytes()
assert first == second
D = hashlib.sha256(raw).hexdigest()
assert first["distribution"]["bundle_digest"] == "sha256:" + D
assert first["distribution"]["provenance"]["source_commit"] == P
request = check_input({"operation": "tag", "acceptance_only": True,
    "package": {"tag": "proxmox-v0.2.1", "source_commit": P, "sha256": D}})
with (output / "request.json").open("xb") as stream:
    stream.write(canonical_json(request))
print(json.dumps(request["package"], sort_keys=True))
```

These outputs are local, unattested proposal data. Independently reproduce D from
the same exact P and retain both build records before owner approval. Neither an
earlier recorded digest nor equality with a prior candidate authorizes this request.
No actual P or D is selected by this runbook or the local S3 pinning increment.

After the prerequisites and separate owner authorization, use the reviewed
`connector-publish.yml` workflow from **main**, original attempt **1**, with original
and triggering ordinary user `benchristian88` (ID `93822871`). Do not rerun a failed
attempt as acceptance; investigate and obtain a separately approved new original
run. The exact future Proxmox 0.2.1 proposal has these inputs:

```text
operation: tag
acceptance_only: true
package: {"tag":"proxmox-v0.2.1","source_commit":"<REVIEWED_COMMITTED_SOURCE_P_40_LOWERCASE_HEX>","sha256":"<SOURCE_BUILT_PACKAGE_D_64_LOWERCASE_HEX>"}
```

This is a **non-executable example**, not an approved request. The tag is a proposed
future identity requiring owner approval; angle-bracket strings are invalid hash
placeholders. P must be an exact approved committed source with qualified metadata;
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

## Acceptance evidence — preserve before one-day expiry

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

The next human governance decision reviews this genuine evidence and the proposed
ADR 0006 split. **Neither trust flag nor the repository gate changes in this
correction, the separate S3 repin or acceptance.** Only separately authorized later reviewed activation may change them.
Actual tag/stage/finalize operations each need subsequent explicit publication
authority; catalogue sequence two remains separate.

## Request format and separate publication ceremony

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
