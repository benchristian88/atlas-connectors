# Phase 4B.3 — Publication activation preparation

Date: 30 October 2026 (Pacific/Auckland). Local preparation; no live activation.

## A. Result and authority boundary

**PASS — local preparation, owner architecture acceptance and original-byte evidence qualification recorded.**
Prepared for human review on `feature/connector-publication-activation`,
based on exact current main `d3f66b039e2027832be932cacd006d86442821ec`.
The branch was clean at that SHA when activation preparation began. This
owner-decision follow-up preserved all existing uncommitted preparation changes.
The combined proposal changes only
the two checked-in package-trust flags to true and the necessary tests/docs.
Trusted implementation S3 remains `be24042c4e7446c7d88d2f08608ab7f058bb24b6`.
All six frozen executable files remain byte-for-byte S3.

**Owner security architecture approval is recorded; live publication is not authorized.**
Live trust remains false/false and the separate enable gate is absent. No GitHub
configuration, credential, workflow execution, ref, release or asset was changed.
No commit, push, merge, PR, tag or remote build was performed. Changes are unstaged
and uncommitted. The owner explicitly accepted
[ADR 0006](decisions/0006-connector-package-publication.md) on **30 October 2026**,
subject to remaining evidence verification and live security checks. The decision
accepts Publisher effective-permission verification after authenticated admission,
acknowledges existing residual risks and forbids Verifier permission expansion or
Publisher credential sharing. Activation, tag, stage and finalize retain separate
explicit owner approval gates. Proposed true/true trust stays only in this unmerged
branch. Original-byte evidence qualification passed as detailed below; fresh live
security checks and separate activation/operation approvals remain required.

## B. Independent genuine S3 acceptance evidence

During activation preparation, official GETs independently confirmed original
[run 40542954614](https://github.com/benchristian88/atlas-connectors/actions/runs/40542954614)
and `/attempts/1`: `workflow_dispatch`, main, attempt **1**, success, caller C
`d3f66b039e2027832be932cacd006d86442821ec`, original and triggering ordinary user
`benchristian88` / `93822871`. Repository/owner IDs are `1414494920` / `93822871`.
Both records reference exactly the SHA-pinned S3 reusable workflow. Original run
timing is 28 October 2026, 05:38:49–05:39:15 NZDT.

| Evidence | Independently observed result |
| --- | --- |
| [Preflight job 122325910928](https://github.com/benchristian88/atlas-connectors/actions/runs/40542954614/job/122325910928) | Successful guard, exact S3 checkout, complete-control observation, attestation, signer authentication and upload steps |
| Exact job context | `workflow_ref` ends in `@be24042c4e7446c7d88d2f08608ab7f058bb24b6`; `workflow_sha` equals S3; official repository and signer path |
| Original request in log | `tag`, `acceptance_only: true`, `proxmox-v0.2.1`, exact P/D in section F; disabled S3 trust |
| Hosted authentication | `Authenticate this package signer profile before exporting public evidence` succeeded after the pinned offline verifier and `seal` ran; upload was reached |
| Artifact production | `connector-preflight-40542954614`, ID `12751332224`, ZIP size **14,893** bytes; upload/finalization successful |
| Logged original ZIP SHA-256 | `3023e7abb9906a7cbdafabd8d31c83a261790c27f71f793aad696e99115dce47` |
| [Publisher job 122326141238](https://github.com/benchristian88/atlas-connectors/actions/runs/40542954614/job/122326141238) | **Skipped**, no steps; Publisher environment/credential/prepare/execute steps did not run |
| Corroborating inventory at preparation time | `GET /git/ref/tags/proxmox-v0.2.1` returned 404; visible release inventory had only the existing three releases |

The public [attestation 60469169](https://github.com/benchristian88/atlas-connectors/attestations/60469169)
was independently retrieved by a credential-free GET for subject SHA-256
`e78819ff12f28d6dd218f43e14c91dc6ad5095ad335a5fd467f3c338b656e88b`.
Offline `sigstore-python==4.3.0` verification succeeded against S3's frozen
public-good trusted root: DSSE signature, certificate chain, SCT and Rekor evidence.
Exact immutable signer identity passed; main, S2 and a wrong SHA each rejected.
All authenticated certificate fields were checked against independently known
C/S3/R: exact SAN/buildSignerURI and buildSignerDigest S3, issuer
`https://token.actions.githubusercontent.com`, official repository/owner URIs and
IDs, public visibility, hosted runner, main source ref, source/config digest C,
caller workflow, dispatch trigger and invocation `/actions/runs/40542954614/attempts/1`.
The sole subject and package predicate repeat the exact subject digest.

The locally saved API-serialized bundle has SHA-256
`0c87f063013972bbdb69c7990a4b84a7a611e3966fe8c2452a7bffaab671de1f`;
the frozen root distribution has SHA-256
`3c2cc7f357dc064ec527fdcd78da6e9245c21a381e1abaa0f2b62b186bcac1a1`.
The serialized bundle hash identifies this review's API representation, not the
original uploaded bundle/ZIP bytes authenticated below.

**Original-archive qualification — PASS:** on 30 October 2026 the owner
confirmed the original S3 ZIP was preserved independently of GitHub's expired
artifact retention, with ZIP SHA-256
`3023e7abb9906a7cbdafabd8d31c83a261790c27f71f793aad696e99115dce47`,
run **40542954614** and preflight SHA-256
`e78819ff12f28d6dd218f43e14c91dc6ad5095ad335a5fd467f3c338b656e88b`.
The original ZIP was located in the retained owner evidence folder through Finder
after shell access to Downloads/Desktop was denied. Only
`atlas-s3-acceptance-40542954614.zip` was copied into
`/private/tmp/atlas-adr0006-owner-approval`; the source was preserved. Both original
digests above were independently recomputed and matched. The ZIP is **14,893 bytes**
and contains exactly two bounded regular members: **64,192-byte**
`connector-preflight.json` and **10,917-byte** `connector-preflight.sigstore.json`.
The recomputed original bundle SHA-256 is
`ad40b88deaaac8ceaac1503903acbddd21205e444f611ff06d7c4146443b9b36`.

The owner-approval follow-up independently reverified the saved public API bundle
using `sigstore-python==4.3.0` and S3's frozen root, including signature,
certificate/SCT/Rekor, the exact C/S3/R profile and three wrong-identity rejections.
The root and distribution lock were compared byte-for-byte with S3. Subsequently,
a fresh local export of exact S3 supplied unmodified executable contracts, roots,
distribution lock and the hash-pinned SDK 1.1.0 wheel. The SDK was installed only
into a temporary target without network access. The copied darwin-arm64 gh binary
was authenticated against S3's lock: **2.102.1**, SHA-256
`b547134b94ff3139051f4cf96cf7081b368ce323450829c6e65d1f7c02833a92`.

Frozen S3 **`ConnectorSigstore.verify` passed on the original members**, verifying
cryptography offline and the full exact certificate, subject, predicate and
allowed transparency profile. A separate pinned-gh invocation retained its actual
verified JSON. Frozen S3 **`check_preflight` passed** against independently known
C/R/request, original false/false trust and exact raw policy bytes retrieved from
local Git at C. Canonical original preflight bytes, source/request/run/attempt,
implementation, policy/trust digests, all five complete signed ruleset/bypass
observations and the historical freshness interval passed. Policy SHA-256 is
`c9a88eeb6c7e6d0a7f1a08eaa07eeed5ea251449db7104f7757626842cf1bbe9`;
canonical original trust SHA-256 is
`20df0ce5560c6dfb5d34ee4e9df5665bd50937657d3dc6ade91900d87392bff0`.

The original bundle and API-serialized bundle are semantically identical but have
different byte hashes. No original preflight or bundle was reconstructed,
reserialized or substituted. Results and actual pinned-gh JSON are saved as
`original-s3-verification.json` and `original-pinned-gh-verification.json` in the
follow-up evidence directory. This closes the original-byte verification gap;
historical freshness validation is not current live `admit` or replay authority.
Anonymous release inventories still cannot establish private draft absence.
Fresh live security checks and separate activation authorization remain required.

## C. Owner security decision — 30 October 2026

**Accepted security architecture:** the repository owner explicitly approved
ADR 0006's split least-privilege permission model for controlled Proxmox 0.2.1
publication on **30 October 2026**, subject to remaining evidence verification
and live security checks. This records the owner's decision, not merely an
engineering recommendation. It does not authorize live activation or publication,
replace original-archive authentication, or establish current live permissions.

The accepted boundary checks Publisher effective permissions **after**
authenticated signed admission and before repository writes. The Verifier
authenticates registration and expected App permissions, but cannot use its own
credential to independently witness another App's effective installed/token grant.
Those effective permissions are **not** an independent witness in its signed
pre-token admission. Successful S3 acceptance did not exercise Publisher credentials.

Reviewed S3 authenticates admission and committed package bytes before
`mint_publisher`. The admitted Publisher JWT-authenticates App `5422372`, checks
installation `174027755`, exact registered/installed baseline permissions,
selected repository and unsuspended state, requests only repository `1414494920`
and those permissions, then checks issued permissions and one-repository scope.
Only after all checks return may a repository write client be used. The fixed
token-mint POST occurs before issued-token scope checks; it is not a repository
write. The authentication transport cannot write repository data. Mutation
boundaries reauthenticate admission and reread visible controls.

The owner accepts this split without expanding Verifier permissions, sharing
Publisher credentials or changing App grants. Any future requirement for an
independent effective-permission witness inside pre-token signed admission needs
a separate reviewed architecture and implementation; it must not be silently
reinterpreted within this increment.

Existing documented residual risks acknowledged by the owner remain:

* Compromise of the valid Publisher key, trusted S3/action/dependency/hosted runner,
  GitHub's authenticated responses, or the administrator/sole maintainer can defeat
  assumptions that modeled checks cannot independently guarantee.
* Protections and grants can change between observations. Fresh signed privileged
  bypass arrays and mutation-time checks reduce this risk without proving continuous
  protection. Missing fields do not establish empty bypass arrays.
* Token issuance precedes token-permission/scope verification; a mismatched token
  is rejected before repository writes, but issuance itself has occurred.
* GitHub publication is not atomic. Ambiguous writes require observation and human
  review. No deletion, asset replacement, retagging or blind retry is permitted.
* One-day preflight artifacts, retained logs and 90-day receipts are not a permanent
  immutable evidence archive. The owner reports independent original-ZIP retention;
  that archive has now been authenticated. Preserve the verification outputs with
  it under the owner's existing evidence practice; temporary outputs are not a
  permanent public immutable evidence archive.
* Actual Publisher key custody, current installed grant and real immutable package
  publication remain owner/live-operation gates. No live App token was minted here.

## D. Implementation and material files

| File | Change |
| --- | --- |
| `catalogue/publication/connector-trust.json` | Only `enabled` and `live_signer_accepted`: false → true |
| `tests/test_connector_publication.py` | Assert proposed activation state and exact separate execution gate; explicitly retain disabled-trust cases, including each flag independently false |
| `catalogue/publication/connector-packages.md` | Current genuine acceptance, precise owner-only configuration/activation and separate operation approvals; historical evidence remains identified |
| `README.md` | Current activation preparation and remaining owner gates |
| `docs/decisions/0006-connector-package-publication.md` | Owner architecture acceptance dated 30 October 2026, existing residual risks and separate activation/operation gates |
| This report | Independent original-byte evidence, explicit owner decision, remaining live checks, risks, preservation, validation and handoff |

No database/migration, application API/UI, SDK, Connector, package release format,
publishing permission, catalogue authority or tenancy boundary changed. There is
no feature ledger in this repository. Earlier ADRs and qualification reports, genuine S2 fixtures,
catalogue S4, sequence one, source metadata and vendor locks are preserved.

## E. Frozen controls and live gate

The full original 165-file inventory is checked against the starting tree. Frozen
files are independently compared to `git show S3:<path>` and SHA-256 inventoried:

* `.github/workflows/connector-verifier.yml`
* `tools/connector_publication_contract.py`
* `tools/connector_publication_preflight.py`
* `tools/connector_publication_sigstore.py`
* `tools/connector_publication_github.py`
* `tools/publish_connector.py`

The caller workflow is also unchanged. Its Publisher gate still requires
`!inputs.acceptance_only`, successful preflight and
`vars.CONNECTOR_PUBLICATION_ENABLED == 'true'`, plus official human/repository,
main and attempt-one checks. Acceptance-only still skips the entire Publisher job.
Identity disagreement, disabled trust, failed admission, unauthorized operations,
excessive/missing permissions and wrong token scope remain fail-closed regressions.

Read-only [Actions Variables](https://github.com/benchristian88/atlas-connectors/settings/variables/actions)
inspection on 30 October 2026 confirmed the **only repository variable** is complete
S3 `CONNECTOR_VERIFICATION_POLICY`, false/false and matching committed main.
`CONNECTOR_PUBLICATION_ENABLED` is absent. The complete environment-variable table
contains the existing Publisher App ID, Verifier App ID/install ID and original
catalogue `VERIFICATION_POLICY`; neither package trust nor enable-gate overrides
exist. This is a user-owned repository; organization inheritance does not apply.
No edit/create/delete control or secret page was used. This verifies the gate is
off at inspection time, not that future settings cannot change.

Trust comparison preserves all five ruleset IDs, Verifier environment `25016263801`,
schema, exact S3 and the 900-second limit. Unchanged policy preserves Publisher
environment `24999137498`, build environment `24617213627`, App/installation/bot
identities and original scopes. All four S3 bindings remain exact.

## F. Qualified Proxmox 0.2.1 source and deterministic bytes

Qualified proposal, independently rechecked without a remote tag or build:

* P: `d3f66b039e2027832be932cacd006d86442821ec`, current main and exact merged
  [PR #42](https://github.com/benchristian88/atlas-connectors/pull/42) commit.
* [Required validate](https://github.com/benchristian88/atlas-connectors/actions/runs/40541066706/job/122319261693):
  successful on P; original log confirms Python **3.12.15**, Ansible enabled and
  **2,417 passed**. This is baseline CI, not CI for the uncommitted activation.
* T: `proxmox-v0.2.1`; currently absent. P's seven workflow files equal current
  main and the unchanged activation working tree's workflows.
* D: `96eaa736c2919e56e09b9613dddd8648ad1f43b77679899ab706261b2a38e509`.

Trusted S3 helpers read a separate clean detached P checkout strictly as source
data. S3's real source-authority validator passed against freshly retrieved main,
comparison, PR, required-check and workflow inventories. Two new local builds
produced identical archive and all three detached metadata files. The archive is
32,145 bytes / 19 members, with nine executable files unchanged from qualified
0.2.0. Release Manifest/compatibility, qualified Proxmox **9.2.11**, Apache-2.0 and
SPDX 2.3 validation passed. Neither P's helper code nor playbooks were executed.
This reproduction is unattested and is not a tag/stage/finalize authorization.

## G. Tests and validation

The following activation-preparation commands were executed successfully before
the owner-approval documentation follow-up. Logs, fresh GET evidence,
offline verification scripts/results, inventory and build outputs are under
`/private/tmp/atlas-phase4b3-activation` (WORK). This local directory is not a
permanent archive. Local Python is 3.14.7; required Python 3.12 CI for this proposal
remains a human pre-merge gate.

| Executed command/check | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q tests/test_connector_publication.py tests/test_connector_sigstore.py` | **541 passed**, 12.49 seconds; `focused-security-final.log` |
| `.venv/bin/python tools/test_collection.py --archive /Users/Ben/Code/atlas/vendor/collections/community-proxmox-2.0.0.tar.gz --output /private/tmp/atlas-phase4b3-activation/test-collections` | Passed reviewed collection hash/install; sibling archive read only |
| `ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-phase4b3-activation/test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q` | **2,421 passed**, zero failures/skips, 65.92 seconds; `full-ansible.log`; 180 existing Python 3.14 `ansible_runner` deprecation warnings |
| `/private/tmp/atlas-phase4b2-tools/actionlint -shellcheck= -pyflakes= .github/workflows/*.yml` | Passed all seven active workflows with actionlint **1.7.12**; optional shellcheck/pyflakes unavailable and disabled |
| `.venv/bin/python -m json.tool catalogue/publication/connector-trust.json /private/tmp/atlas-phase4b3-activation/trust-validated.json` | Passed JSON parsing |
| `.venv/bin/python /private/tmp/atlas-phase4b3-activation/verify-preservation.py` | Passed real `check_trust`, canonical JSON, enabled state, all three disabled combinations, exact controls, all bindings, full inventory, frozen S3, refs/index/HEAD/siblings; `preservation.json` |
| `.venv/bin/python -m pytest -q tests/test_documentation.py` | **1 passed**; internal Markdown links, fences, final newlines and whitespace |
| `.venv/bin/python -m compileall -q tools tests` | Passed |
| `.venv/bin/python -m pip check` | No broken requirements; existing unwritable-cache warning only |
| `.venv/bin/python -B /private/tmp/atlas-phase4b3-activation/qualify-source.py` | Passed fresh source-authority checks, two equal S3/P builds, archive/qualification/licence/SPDX validation; `source-qualification.json` |
| `/private/tmp/atlas-sigstore-correction-verifier/bin/python /private/tmp/atlas-phase4b3-activation/verify-s3-archive.py` | Passed genuine S3 DSSE/certificate/SCT/Rekor, exact certificate profile and three wrong-identity rejections; `s3-archival-verification.json`; original subject was not yet available to preparation |
| `git diff --check` and `git diff --no-index --check -- /dev/null docs/phase-4b3-activation-preparation.md` | Clean tracked/new-file whitespace; no-index returns normal difference status 1 without whitespace diagnostics |

Owner-approval follow-up commands were rerun on 30 October 2026. Evidence is
under `/private/tmp/atlas-adr0006-owner-approval`; the prior preparation evidence
was preserved. No executable or test behavior was changed in this follow-up.

| Executed command/check | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q tests/test_connector_publication.py tests/test_connector_sigstore.py tests/test_documentation.py` | **542 passed**, 14.39 seconds; `focused-security-documentation.log` |
| `ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-phase4b3-activation/test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q` | **2,421 passed**, zero failures/skips, 68.43 seconds; `full-ansible.log`; 180 existing Python 3.14 `ansible_runner` deprecation warnings |
| `/private/tmp/atlas-sigstore-correction-verifier/bin/python /private/tmp/atlas-adr0006-owner-approval/verify-public-bundle.py` | Saved public API bundle DSSE/certificate/SCT/Rekor and exact C/S3/R profile passed; main/S2/wrong SHA rejected. Run before the original ZIP was located; `public-bundle-verification.log`, `s3-archival-verification.json` |
| `.venv/bin/python -B /private/tmp/atlas-adr0006-owner-approval/verify-original-s3.py` | **Passed** recomputed original ZIP/preflight hashes, exact original members, frozen S3 `ConnectorSigstore.verify`, canonical preflight and `check_preflight`, all five signed ruleset observations, original policy/disabled trust at C and pinned-gh offline verification with frozen roots; `original-s3-verification.log`, `original-s3-verification.json`, `original-pinned-gh-verification.json` |
| `.venv/bin/python -B /private/tmp/atlas-adr0006-owner-approval/verify-preservation.py` | **Passed** four-document-only follow-up, unchanged pre-existing trust/tests, all tracked files, six frozen S3 executables/roots, real trust validation and disabled combinations, four S3 bindings, separate execution gate, refs/HEAD/index and clean siblings; `preservation.json` |
| `.venv/bin/python -m pytest -q tests/test_documentation.py` | **1 passed** after the original-evidence documentation update |
| `git diff --check` and `git diff --no-index --check -- /dev/null docs/phase-4b3-activation-preparation.md` | Clean tracked/new-report whitespace; no-index has normal difference status 1 |

The first focused run exposed five tests whose disabled-trust fixture implicitly
read the old false/false file. That test now explicitly sets disabled trust, retaining
all five original negative cases; no assertion was removed. Three new cases check
each disabled flag combination, and the real inline guard additionally tests both
false. The corrected focused and full suites pass. No executable correction was
needed. Full suite coverage includes original signature/identity/authorization,
Publisher permission/scope, freshness, unauthorized-entrypoint and separate-operation
regressions. Required Python 3.12 CI for this uncommitted proposal has not been run;
no workflow was dispatched. Original-subject pinned-gh archival verification has
now passed; no live Publisher permission/custody/immutable-package test is claimed.

## H. Owner-only post-merge configuration

Follow the [complete owner sequence](../catalogue/publication/connector-packages.md#s3-rollout--completed-acceptance-pending-activation-review).
Retain the recorded 30 October 2026 ADR acceptance and completed original-archive
verification; complete and record current live security checks. Review the
local diff, obtain required CI/security review, then merge through the human
process. With no publication running/queued and the execution gate still off,
set repository `CONNECTOR_VERIFICATION_POLICY` from the exact merged trust file.
Independently verify both environments and repository/effective values, C/S3/CI,
complete protections, baseline grants and custody without extracting any key.

Only a separately authorized owner action may set repository
`CONNECTOR_PUBLICATION_ENABLED` to literal `true`, **last**, followed by independent
effective-value verification. A mismatch stops activation; keep/return the gate
to `false`. Environment-only settings cannot open the job-level gate. Disabling
does not cancel an already running Publisher or undo its writes. Catalogue trust,
permissions, keys, protections, S3 and release format must stay unchanged.

## I. Repository state and restrictions

The combined preparation and owner-decision update affects **five** of the
**165 original tracked files**, leaving **160 unchanged**, plus this new report.
The owner-decision follow-up changes only four documentation files and preserves
the existing trust/test changes. All six frozen executables,
all workflow files, SDK/vendor, Connector source, historical fixtures/earlier ADRs/reports,
catalogue S4 and sequence-one state remain unchanged. HEAD/main/origin-main still
identify the expected base; all original branches/tags are preserved.

`git status --short`:

```text
 M README.md
 M catalogue/publication/connector-packages.md
 M catalogue/publication/connector-trust.json
 M docs/decisions/0006-connector-package-publication.md
 M tests/test_connector_publication.py
?? docs/phase-4b3-activation-preparation.md
```

Nothing is staged or committed. Original refs/HEAD and both clean sibling repositories
remain unchanged; no SDK or Atlas work was performed. Original preparation used
GET-only GitHub access, including browser settings inspection and a credential-free public attestation
download. Restricted network DNS initially failed; the public GET succeeded with
network permission. No approval rejection occurred. No secrets, private keys or
Publisher installation tokens were accessed or minted. The owner-approval follow-up
used only local evidence and made no GitHub requests or settings changes. Shell
archive discovery encountered local OS access restrictions, resolved by copying
only the original ZIP through Finder. No automatic approval review rejection occurred.

## J. Precise human handoff and remaining decisions

ADR 0006's architecture decision is accepted on 30 October 2026, with existing
residual risks acknowledged. Independent original-ZIP digest/member verification,
archival `check_preflight` and original-bundle pinned-gh authentication have passed.
Preserve that evidence and its
verification record under the owner's evidence practice; neither this local
temporary directory nor expired Actions retention is a permanent archive.
Required activation review/Python 3.12 CI/merge, live effective-variable/protection/
grant/custody checks and separate live activation authorization are also
outstanding. Acceptance does not authorize any of those actions.

After explicit live activation authorization, each operation requires its own
approval and fresh original main run: **tag** exact P/T/D and stop; inspect original
build/signature/ZIP identity; **stage** those original five files and stop; inspect
L/A, every asset ID/digest/size and inventory digest; **finalize** only after explicit
approval of C/P/T/D/R/L/A, staging run and full inventory. Require the independent
anonymous GET-only verifier's exact immutable result. Never infer authorization
from a successful earlier run or receipt, rerun failed operations blindly, retag,
delete or replace assets. Consumer eligibility, catalogue sequence two, remote
installation and permanent archival design remain outside this increment.
