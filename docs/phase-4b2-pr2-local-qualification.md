# Phase 4B.2 PR2 — trusted implementation pinning qualification

Date: 26 October 2026. Local implementation and qualification only.

Historical PR2 qualification record. Subsequent genuine acceptance run 40523236413
failed before checkout/signing because the reusable job reference was SHA-pinned,
while the guard required main. See the current
[identity correction qualification](phase-4b2-identity-qualification.md) and
[operator runbook](../catalogue/publication/connector-packages.md) for the correction,
unchanged production pins and required new S2 review/pinning cycle. The original
local results below do not establish genuine package signing acceptance.

## A. Executive result

**PR2 LOCAL PASS.** Exact reviewed S is pinned, publication remains disabled,
and local security, packaging, historical and complete Ansible-enabled regressions
pass. The branch is ready for human commit/PR and required Python 3.12 CI. Genuine
cloud acceptance, final owner security acceptance and activation are separate; none
is claimed or executed here.

## B. Repository baseline

Repository `benchristian88/atlas-connectors`, origin
`https://github.com/benchristian88/atlas-connectors.git`. Starting HEAD, local main
and safely fetched origin/main all identify reviewed implementation **S**:
`d6601ad97815a85da164e4329766ea17b62bddc9`.
GitHub's read-only PR #37 metadata independently reports merged status, base main,
head `c24a7c9ba4e12e464e05560780131ada2937e81d` and merge commit S. Local history
confirms S is reachable from current main and contains all 17 PR1 changed files.

`feature/connector-publication-pinning` already existed at exactly S with a clean
working tree when work began. It was preserved and reused; no branch recreation,
reset, stash or history edit was necessary. There are no commits in PR2.
No repository-local/nested or ancestor `AGENTS.md` was found in atlas-connectors;
the supplied repository safety/scope requirements were followed.

Read-only references began clean: Atlas `dev`
`808ee0f76f77c11e17a6c403806ce0666e30074e`, SDK `main`
`8b0518c462289cca4758c3b9bf362f1130928a1c`.

## C. Architecture and exact pinning

| Binding | Exact value |
| --- | --- |
| Reusable verifier | `benchristian88/atlas-connectors/.github/workflows/connector-verifier.yml@d6601ad97815a85da164e4329766ea17b62bddc9` |
| Publisher executable checkout | `d6601ad97815a85da164e4329766ea17b62bddc9` |
| `ATLAS_IMPLEMENTATION_REVISION` literal | `d6601ad97815a85da164e4329766ea17b62bddc9` |
| Package trust `signer_revision` | `d6601ad97815a85da164e4329766ea17b62bddc9` |

The advancing reviewed caller commit **C** and data-only package-source commit
**P** are separately bound identities. The executable root and isolated reusable
workflow remain S, never PR2, main, an input ref or catalogue S4. Checkouts for C
and P have explicit separate paths and never supply executed helpers/dependencies.
The complete reusable workflow and trusted helpers/dependency pins at S were
reviewed without editing them. Existing offline gh/Sigstore, source/package
builders, authority validators and immutable catalogue architecture were reused.

## D. Implementation and material files

| File | Rationale |
| --- | --- |
| `.github/workflows/connector-publish.yml` | Replace three inert references with S; explain caller/implementation separation |
| `catalogue/publication/connector-trust.json` | Set S only; preserve false flags and every other trust field |
| `tests/test_connector_publication.py` | Bind synthetic fixtures to reviewed S; exact four-binding and alternate-ref regressions; frozen inline guard, acceptance/disabled entrypoint isolation and Publisher permission denial cases |
| `tests/test_publication_packaging.py` | Replace only the package reusable-workflow allowlist entry with exact S; retain historical catalogue allowlist |
| `catalogue/publication/connector-packages.md` | Precise repository-variable location/timing, proposed permission boundary, symbolic acceptance request and genuine evidence/offline verification procedure |
| `docs/decisions/0006-connector-package-publication.md` | Record proposed split decision, exact S, enforced checks, rationale and residual risk; retain Proposed status |
| `README.md` | Current reviewed S and remaining CI/acceptance status |
| `catalogue/publication/README.md` | Remove obsolete pending-pin status from current overview; historical catalogue controls unchanged |
| `catalogue/publication/consumer-handoff.md` | Replace obsolete inert-pin status and clarify pending owner decision |
| `docs/phase-4b2-local-qualification.md` | Mark the original PR1 report historical and link current PR2 evidence; retain original record |
| This report | A–J qualification, validation limits and human handoff |

No database/schema/migrations, API/UI/routes, application authorization, customer/
site tenancy, SDK, qualified Connector source or package metadata changed. Existing
publication contracts, original workflows, App identities/scopes and catalogue trust
are unchanged. Workflow caller edits are pin/comment changes only. Documentation
outside the immediate runbook was touched only to remove materially obsolete
pending/all-zero pin claims and preserve PR1 history as history.

## E. Security decision review

Before Publisher credentials, independent admission authenticates repository/owner,
original/triggering human, original attempt, reviewed C/S, C's CI, exact request,
policy/trust, App registration, environments and complete privileged ruleset/bypass
observations. It does not certify package-source/build qualification during
acceptance; those gates are in the skipped Publisher preparation path.

Review of S confirms `publish_connector.main` authenticates admission and committed
package/original artifact before `mint_publisher`. The mint authenticates exact App
5422372, owner 93822871, slug, installation 174027755, selected-repository and
unsuspended state; compares exact registered/installed permissions; requests only
repository 1414494920 and baseline permissions; checks issued permissions and the
token's sole official repository/owner. Only then is a write-capable client returned.
The authentication transport allows fixed App/installation GETs and one scoped
mint POST, never repository mutations. Write methods recheck admission/authority.
Negative cases cover missing, additional and contradictory grants/identities.
No material flaw requiring a new executable baseline was found in this review.

**Publisher installation permissions are independently validated by the admitted
Publisher before writes; they are not included as independently observed effective
permissions in the Verifier's signed pre-token admission.** The proposed owner
decision accepts this least-privilege split; final acceptance is separate. ADR 0006
remains Proposed. Correct stolen keys, compromised maintainer/admin/trusted code/
actions/runner/provider and changes between observations remain risks. Local tests
cannot establish live custody, scope, genuine certificate representation or
continuously enforced hidden protections. No permission expansion, credential
sharing, new secret store or changed executable masquerading as S was introduced.

## F. Isolation and activation safeguards

Package `enabled` and `live_signer_accepted` remain false. Job condition retains
`!inputs.acceptance_only`, successful preflight, effective repository variable
`CONNECTOR_PUBLICATION_ENABLED == 'true'`, fixed identities/main/attempt. Default
acceptance is Boolean true. Acceptance excludes the entire Publisher environment,
key injection, preparation, token mint and writes, even with a mistakenly true gate.
Missing/false enable configuration cannot start Publisher. Malformed acceptance
values fail strict request validation before successful authenticated preflight;
failed/skipped dependencies cannot satisfy the job condition.

Tests execute S's actual inline Python guard and Publisher CLI admission paths with
synthetic credentials. A constrained model covers the existing Actions AND/NOT/
equality condition, including case-insensitive string comparison and truthiness;
this is local regression evidence, not genuine hosted scheduling acceptance.
Only the Verifier secret is explicitly forwarded; no inherited/Publisher secret
enters its reusable job. All mutable/arbitrary/data-source executable fallback
references remain prohibited. Frozen catalogue S4 authority is unchanged.

## G. Testing and validation

Local interpreter is Python 3.14.7; Python 3.12 CI remains the human PR merge gate. Tests use the existing Ansible-enabled
virtual environment and approved community.proxmox 2.0.0 archive, SHA-256
`77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6`.
No test credential is live and no mock is represented as genuine cloud acceptance.

| Executed command/check | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q tests/test_connector_publication.py tests/test_publication_packaging.py tests/test_historical_workflows.py tests/test_documentation.py` | **286 passed**, 7.22 seconds; 114 more cases than PR1's focused baseline; no previous security coverage removed |
| `ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-phase4b2-pr2-review/test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q` | **2,141 passed**, zero failures/skips, 58.81 seconds; 180 inherited `ansible_runner` Python 3.14 deprecation warnings |
| `.venv/bin/python tools/test_collection.py --archive /Users/Ben/Code/atlas/vendor/collections/community-proxmox-2.0.0.tar.gz --output /private/tmp/atlas-phase4b2-pr2-review/test-collections` | Passed approved archive verification; 189 installed source files match the existing approved Ansible test collection byte for byte |
| `.venv/bin/python -m pip check` | No broken requirements; only an unwritable pip-cache warning |
| `/private/tmp/atlas-phase4b2-tools/actionlint -shellcheck= -pyflakes= .github/workflows/connector-publish.yml .github/workflows/connector-verifier.yml` | Passed with existing actionlint 1.7.12; optional shellcheck/pyflakes were not run |
| `.venv/bin/python -m compileall -q tools/connector_publication_contract.py tools/connector_publication_preflight.py tools/connector_publication_sigstore.py tools/connector_publication_github.py tools/publish_connector.py tests/test_connector_publication.py tests/test_publication_packaging.py` | Passed |
| `.venv/bin/python -m json.tool catalogue/publication/connector-trust.json /private/tmp/atlas-phase4b2-pr2-review/trust-validated.json` | Passed |
| Repository Markdown test in focused/full suites | Links, whitespace, newline and fence checks passed |
| `git diff --check` and `git diff --no-index --check -- /dev/null docs/phase-4b2-pr2-local-qualification.md` | Clean tracked/new-file whitespace; no-index returns expected difference status 1 for a new file, with no whitespace diagnostics |
| Complete tracked SHA-256 inventory against starting S, `git for-each-ref`, `git rev-parse HEAD`, trust comparison and deterministic bundle assertions | Exactly 10 allowed tracked files changed, 141 unchanged; all Git refs and HEAD unchanged; new report is the only untracked file; trust differs only in S |
| Atlas/SDK `git status --short`, branch and HEAD checks | Both clean, at the read-only branches/SHAs in B |

Full-suite output is retained locally at
`/private/tmp/atlas-phase4b2-pr2-review/full-pytest.log`. Baseline hashes, complete
tracked/untracked inventories and local unattested archive comparisons are in that
same temporary review directory. No new gh/actionlint download was needed.

Preserved archive SHA-256 values:

- Historical Proxmox 0.2.0: `a14fec5ab485c980688ff5907e8835ddd3e9cecd1a6989ef252cbcb1b1dc4ef8`.
- Historical candidate: `dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97`.
- Local unattested 0.2.1: `96eaa736c2919e56e09b9613dddd8648ad1f43b77679899ab706261b2a38e509`.

The last value establishes unchanged local archive bytes only; it is **not** approval
of the future committed-source digest D. All tracked Connector/0.2.1 metadata,
sequence-one fixtures/registry, original release workflow, frozen S4 code/policy/
trust and SDK wheel/hash lock remain byte-identical to the starting S inventory.
No genuine package-preflight positive signature was fabricated or claimed.

## H. Genuine acceptance readiness

The [owner runbook](../catalogue/publication/connector-packages.md) specifies exact
prerequisites, locations, inputs, evidence endpoints, one-day artifact retention,
profile/certificate claims and offline verification using S. Configure the complete
reviewed `CONNECTOR_VERIFICATION_POLICY` as a **repository Actions variable**;
environment-only copies do not supply this caller's job-level env. Environment
overrides should be absent or match exactly for both jobs. GitHub's documented
variable timing/precedence and reusable secret rules are linked in the runbook.
Keep the effective repository publication gate absent/false; do not change the
original catalogue `VERIFICATION_POLICY` or secrets.

After review, Python 3.12 CI and merge, separate owner authority may approve an
original-main `operation=tag`, `acceptance_only=true` proposal for future
`proxmox-v0.2.1`. Source P and digest D are explicit invalid placeholders until
independently reviewed and reproduced from committed source; no earlier candidate
digest is approved here. Collect exact R/C/S, attempt/actors, signed subject/bundle,
certificate/predicate, complete observations, independent policy/trust/request bytes,
offline result and Publisher-skipped/no-mutation evidence within one day. Successful
Actions execution alone is insufficient. A profile discrepancy fails closed; a
helper correction requires new reviewed S and re-pinning, never relaxed checks.

Live variable/secret availability, protection state and effective installed scopes
were not independently confirmed. They remain owner operational acceptance
prerequisites, not local implementation failures. No genuine dispatch or signing
acceptance was attempted; acceptance does not qualify a build, authorize finalization
or make the package remotely installable.

## I. Git and remote state

Final inventory: 10 modified tracked files and one untracked report, all listed
below. All edits remain local and uncommitted on
`feature/connector-publication-pinning`, HEAD S. Original 151 tracked paths and all
local/remote-tracking refs are unchanged apart from the allowed file edits.
No commit, push, PR, merge, rebase, tag/release creation, workflow dispatch, settings/
secret/protection change, live App credential mint or publication was performed.
Remote activity was a safe no-tags fetch, read-only PR metadata and official GitHub
documentation reads. Python tests use synthetic provider responses/ephemeral test
keys and offline historical bundles. Proxmox 0.2.1 and catalogue sequence two remain
unpublished by this increment.

Final `git status --short`:

```text
 M .github/workflows/connector-publish.yml
 M README.md
 M catalogue/publication/README.md
 M catalogue/publication/connector-packages.md
 M catalogue/publication/connector-trust.json
 M catalogue/publication/consumer-handoff.md
 M docs/decisions/0006-connector-package-publication.md
 M docs/phase-4b2-local-qualification.md
 M tests/test_connector_publication.py
 M tests/test_publication_packaging.py
?? docs/phase-4b2-pr2-local-qualification.md
```

## J. Human handoff

The locally qualified branch is ready for human review of the complete tracked/
untracked diff, followed by the owner's manual commit/push/PR. Required Python 3.12 CI and review precede
merge. The exact next step after green CI **and merge** is owner verification of
the runbook's independent configuration and evidence-retention prerequisites,
followed only under separate owner authority by a genuine acceptance-only original
main dispatch. Preserve evidence and review the Proposed ADR split before any
separate activation decision. PR2 authorizes no privileged package operation.
