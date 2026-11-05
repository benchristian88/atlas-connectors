# Catalogue 2 — Publisher successor contract approval

Date: 5 November 2026 (Pacific/Auckland).

## A. Executive result

**CONDITIONAL PASS — source contract approval only; operational acceptance remains
outstanding.** The producer now contains the owner's fixed, release-owned
`SuccessorApproval` and its independently reproduced canonical fingerprint. The
existing accessor, frozen dataclass, authorization flow and disabled-recovery
disposition are preserved. This does not identify or approve executable successor
revision S, adopt a workflow, authorize signing/publication, or approve remote
executable installation.

This report supersedes the approval-unset statements in the historical
[completion report](catalogue2-completion-engineering-report.md),
[remediation report](catalogue2-security-remediation-report.md) and
[Phase 1 contract](../catalogue/publication/durable-evidence.md) for this producer
record only. Their historical evidence and security controls are retained.
Atlas consumer approval records are outside this change.

## B. Baseline and decision authority

The pre-edit checkout was clean, on the existing
`feature/catalogue-v2-publisher-successor` branch. Both HEAD and the local
`origin/main` tracking ref were exactly
`078f4099c3fcf850557bf9148db207f696c0ecad`; their merge base was the same commit.
GitHub's read-only PR metadata independently confirmed this is the merged
[producer PR #48](https://github.com/benchristian88/atlas-connectors/pull/48),
containing the seven-asset driver, evidence verifier, candidate and workflow
generator. No branch, commit, ref, index or history was changed by this task.

Atlas remained read-only, clean on `dev` at
`76031dc6358a81c3babd15f74d407e22f0778dee`. Local `git show` and the commit-pinned
GitHub file both confirmed accepted ADR 0018, the 5 November owner acceptance and
the `Historical authorization`, `Selection binding` and `Recovery` sections.
Read-only metadata confirmed this exact commit merged
[Atlas PR #58](https://github.com/benchristian88/atlas/pull/58).
The authoritative reference is
[accepted ADR 0018](https://github.com/benchristian88/atlas/blob/76031dc6358a81c3babd15f74d407e22f0778dee/docs/decisions/0018-catalogue-durable-publication-evidence.md).
Its narrower acceptance leaves ADR 0012 **Proposed overall**.

The active Publisher remains the historical S4 workflow and four-asset driver,
pinned to `2dd1ffcd2f5677dc35bdbc8f68ea28275c91c285`. Its reusable signer,
executable checkout and environment implementation pin agree. The existing trust
file retains that S4 signer. The successor driver is absent from active workflows.
No future S has been invented or selected.

## C. Exact approved record

`tools/catalogue_evidence_driver.py` contains exactly the existing six dataclass
fields, populated as follows:

```json
{
  "historical_decision": "https://github.com/benchristian88/atlas/blob/76031dc6358a81c3babd15f74d407e22f0778dee/docs/decisions/0018-catalogue-durable-publication-evidence.md#historical-authorization",
  "policy_sha256": "c9a88eeb6c7e6d0a7f1a08eaa07eeed5ea251449db7104f7757626842cf1bbe9",
  "publication_seconds": 300,
  "recovery_decision": "disabled-pending-permanent-archive-decision",
  "selection_binding_decision": "https://github.com/benchristian88/atlas/blob/76031dc6358a81c3babd15f74d407e22f0778dee/docs/decisions/0018-catalogue-durable-publication-evidence.md#selection-binding",
  "selection_seconds": 900
}
```

The historical and selection fields use immutable commit-pinned section URLs.
Recovery retains its exact executable literal; no separate recovery approval is
created. Its authority and limitations are recorded in
[ADR 0018's recovery decision](https://github.com/benchristian88/atlas/blob/76031dc6358a81c3babd15f74d407e22f0778dee/docs/decisions/0018-catalogue-durable-publication-evidence.md#recovery).
Environment variables, downloaded policy, requests and GitHub responses cannot
populate or override this record. No CLI approval argument is introduced.

## D. Cryptographic identity and reproduction

The original `catalogue/publication/policy.json` bytes hash to:

```text
c9a88eeb6c7e6d0a7f1a08eaa07eeed5ea251449db7104f7757626842cf1bbe9
```

This was checked before editing and equals the independently supplied expected
digest. The file was never rewritten or canonicalized.

The fixed `APPROVED_SUCCESSOR_SHA256` is:

```text
8a1c69168ed22dc2f0bff385da182de9bae913e900df031d4b47aabccd7e9070
```

This is SHA-256 of `canonical_json(asdict(approved_record))`, using the actual
production helpers from `publication_contract` / `build_catalogue`: UTF-8, sorted
object keys, two-space indentation, `ensure_ascii=False`, `allow_nan=False` and
one terminating newline. It is distinct from the raw policy digest. The constant
is a literal; the accessor verifies it and cannot repair it at runtime.

Reproduce from the producer repository without credentials or provider calls:

```bash
shasum -a 256 catalogue/publication/policy.json
.venv/bin/python - <<'PY'
from dataclasses import asdict
import hashlib
import json
import sys
sys.path.insert(0, 'tools')
from catalogue_evidence_driver import approved_successor, APPROVED_SUCCESSOR_SHA256
from publication_contract import canonical_json, digest
record = asdict(approved_successor())
raw = canonical_json(record)
independent = (json.dumps(record, sort_keys=True, indent=2,
                         ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
assert raw == independent
assert digest(raw) == hashlib.sha256(independent).hexdigest() == APPROVED_SUCCESSOR_SHA256
print(raw.decode('utf-8'), end='')
print(APPROVED_SUCCESSOR_SHA256)
PY
```

The tests independently spell out all six approved values and the expected hash;
they do not derive expected decisions from the production constants.

## E. Security boundary preservation

The complete driver, inherited Publisher, evidence verifier, original
authorization code and generated workflow were inspected. Only the approval
literals and explanatory comments changed in production code; `main()`,
`approved_successor()` and all underlying security implementations are unchanged.

| Boundary | Preserved enforcement |
| --- | --- |
| Release-owned approval | Exact dataclass type, canonical fingerprint, policy identity, timing types/ranges, decision references and disabled recovery are validated before checkout or credentials. |
| Exact source policy | Raw bytes at C must match the approved policy hash; matching that hash alone cannot admit a job. Existing policy identities, enabled state and bootstrap pin are unchanged. |
| Reviewed implementation S and source C | `check_checkouts` checks both actual Git HEADs independently. Source trust must agree with the implementation revision; original preflight and signature profiles bind C and S. No future S is embedded in this record. |
| Original preflight | `job_preflight` requires the original dispatch, first attempt, fixed numeric repository/owner, hosted job, policy, trusted signer, authenticated artifact and fresh runner-local admission. An archived historical result is not live admission. |
| Isolated genuine signer | Existing reusable workflow, Verifier App, permissions, protected environment, subject/predicate, pinned gh 2.102.1 distribution and roots remain byte-exact. Existing offline fixture verification remains separate from successor signing acceptance. |
| Publisher credentials and gates | Generated workflow orders artifact download and authorization before App-token issuance. Driver requires `PUBLICATION_OPERATION=publish` and `ATLAS_CATALOGUE_EVIDENCE_ENABLED=true`. A token, approval JSON or environment identity cannot bypass these checks. |
| Seven-asset staging | `EvidencePublisher` preserves original preflight/bundle/policy bytes, catalogue/bundle and current pointer/bundle; numeric identities, original archive and durable same-job checkpoint must agree. |
| Authenticated selection | Original source/run/attempt correlation, build signature/tag/source agreement, exact retained selection bytes and one-selection-per-source enforcement remain. Preflight does not directly sign future pointer or asset IDs; this implementation reliance is the accepted ADR decision. |
| Historical validation | Original issuance/expiry, run creation and authenticated allowlisted Tlog witnesses remain required. Selection is bounded by 900 seconds and publication by 300 seconds. One through eight supported witnesses are accepted; no two-log quorum is claimed. |
| Finalization | Final authenticated-window check preserves the 30-second reserve after slow reads, immediately before irreversible PATCH. It extends no bound. Actual publication time must still validate afterward. |
| Immutable readback | Exact seven assets, IDs, sizes/digests, original bytes, by-ID/by-tag/source identity, immutability, signatures and publication time are rechecked before pointer selection. |
| Current-pointer CAS | Existing authority and unchanged channel are rechecked, then compare-and-swap is used. Ambiguous provider writes preserve evidence and do not automatically advance current. |

Publisher transport restrictions, repository isolation, numeric actor/App/environment
checks, permissions, bootstrap exception and historical ruleset controls are
unchanged. No database, migration, API/UI route, tenancy model, Connector Manifest,
SDK or native/systemd distribution contract changes were needed. No Atlas
installation eligibility or executable trust is approved here.

## F. Executed validation

Local evidence is under `/private/tmp/atlas-catalogue2-successor-approval`.
The established `.venv` uses Python **3.14.7** on macOS arm64, pytest 8.4.1,
jsonschema 4.25.1, ansible-core 2.19.7, ansible-runner 2.4.3, proxmoxer 2.3.0,
requests 2.34.2 and atlas-connector-sdk 1.1.0. No dependency or lock was changed.
The already provisioned reviewed community.proxmox 2.0.0 test collection was reused.

Executed focused command:

```bash
ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-catalogue2-evidence-review/test-collections \
ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q \
  tests/test_catalogue_evidence_driver.py tests/test_evidence_workflows.py \
  --junitxml=/private/tmp/atlas-catalogue2-successor-approval/driver-workflows-final.xml
```

Result: **102 passed, zero failed/errors/skipped**, 2.20 seconds. This comprises
83 driver/approval/checkpoint/candidate cases and 19 workflow-generation/security
cases. The initial development run was **95 passed, one failed, one setup error**:
the new manifest assertion omitted the catalogue's added distribution envelope,
and removal of an apparently unused `signed` import broke the imported `state`
fixture dependency. Both test mistakes were corrected without changing production
behavior, fixtures or historical expectations. No failure was suppressed.

Executed full-suite command:

```bash
ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-catalogue2-evidence-review/test-collections \
ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q \
  --junitxml=/private/tmp/atlas-catalogue2-successor-approval/full.xml
```

Full-suite result: **2,968 passed, zero failed/errors/skipped**, 93.76 seconds.
All 180 warnings are Python 3.14 `ansible_runner` deprecations of `codecs.open()`;
none represents a skipped or failed test. The following are subsets of that
single full run, not additional unique tests:

| Required validation area | Passing cases |
| --- | ---: |
| Successor approval / driver | 83 |
| Publication evidence, historical bounds and finalization reserve | 133 |
| Original Publisher authorization / preflight Sigstore | 131 / 61 |
| Original publication contract / cryptography | 180 / 4 |
| Generated workflows / retained historical workflows | 19 / 12 |
| Verifier workflow / publication packaging and permission isolation | 21 / 13 |
| Original bootstrap / ruleset visibility / Verifier App transport | 115 / 339 / 38 |
| Catalogue candidate/package/history contracts | 173 |
| Connector publication / Connector Sigstore regressions | 456 / 152 |
| Documentation links, whitespace and fences | 1 |

Additional executed checks:

```bash
/private/tmp/atlas-phase4b2-tools/actionlint -shellcheck= -pyflakes= .github/workflows/*.yml
git diff --check
git diff --cached --quiet
```

Actionlint **1.7.12 passed for all seven active workflows**; shellcheck and
pyflakes integrations were explicitly disabled. The Python tests cover generated
successor syntax/contracts and twelve hostile workflow mutations. Whitespace and
unstaged-only checks passed. Baseline/hash auditing and independent fingerprint
reproduction passed; the exact unchanged-file/control counts are in section H.

The final report was also checked with `.venv/bin/python -m pytest -q
tests/test_documentation.py`: **one passed**, zero failures/errors/skips. Its
embedded fingerprint reproduction command was extracted and executed verbatim;
its output matched the exact canonical record/hash. An AST comparison against
the baseline confirms all production definitions except the two approval
assignments and module docstring are unchanged.

Python 3.12 is used by hosted CI but no local 3.12 interpreter/environment was
available in PATH or the checked local Homebrew, framework, pyenv and uv locations.
Hosted CI was not dispatched. No Docker host or LXC was accessed for validation.
Python 3.12 hosted validation remains an explicit acceptance gate.

## G. Failure-mode and candidate coverage

| Requirement | Coverage and interpretation |
| --- | --- |
| H1: exact approved record | Exact type and six literal values, raw policy digest, immutable ADR URLs, frozen-field assignment rejection, independent stdlib serialization/hash and production accessor identity. |
| H2: absent approval | Isolated removal of record, fingerprint or both, with forged environment approvals present; exact fail-closed error precedes checkout/credentials/provider. The old missing-approval case remains explicit. |
| H3: tampering | Wrong/empty/non-string hashes, modified policy or decisions, mutable decision URL, changed bounds, wrong/empty identities, missing/oversized decisions, wrong type/subclass and forged recovery disposition reject. Test-only repinning also proves structural validators still reject malformed records; it is not a runtime approval mechanism. |
| H4: recovery | Real production approval plus forged recovery environment/request claims cannot admit `recover`. Credential reads, client construction, provider/publication effects and artifact creation are tripwires. Changed recovery disposition also rejects, even with a test-only matching fingerprint. |
| H5: gate-off | All three phases reject absent/false/malformed operational gates despite a token and forged identity/approval environment. Checkouts are isolated as admitted so these cases exercise the gate itself; source/preflight reads and credential/provider effects are forbidden. |
| H6: genuine identities | Driver denial tests retain checkout/policy/signer/original-preflight boundaries. Unchanged original authorization, cryptography and evidence tests cover exact C/S, original first attempt, actors/numeric identities, policy, signature profiles, original source/selection correlation and expiry. Approval-only synthetic authorization is not substituted. |
| H7: historical security | Original bootstrap, ruleset, permission, signer-isolation, active-control and archived S4 template tests are retained. The only successor workflow expectation changed was the obsolete `None` assertion; explicit accepted-record and disabled-recovery assertions replace it. No historical hash or trust fixture was rebaselined. |
| H8: candidate integrity | Candidate remains sequence 2, Proxmox 0.2.0 retains exact original identity with withdrawal, and the existing immutable 0.2.2 manifest/package remains selected. Active sequence remains 1. |

Checkpoint tests reject changed run, source, original preflight, policy or
implementation context without rewriting surviving state. Existing tests reject
orphan drafts, missing/substituted immutable evidence, expired live authority,
original preflight reuse across jobs/operations and ambiguous provider completion.
The inherited historical recovery evaluator tests are retained; the executable
successor driver still rejects recovery before reaching that evaluator.

The unchanged 0.2.2 candidate binds package release `429608780`, asset `693849044`,
tag `proxmox-v0.2.2`, source
`e58788a667c0c0006477ac149e8ad28aedda0745` and package SHA-256
`2d66fc69b9cf9c70d7df117fe41bff3e3e056299f1908cde965e9e3f75e59abf`.
No new Proxmox release, package, catalogue publication or signature was created.
Local test payloads and synthetic provider observations establish regressions,
not genuine successor signing, timing, publication or installation acceptance.

## H. Scope and source integrity

The complete changed-file inventory is:

| File | Purpose |
| --- | --- |
| `tools/catalogue_evidence_driver.py` | Populate the fixed accepted record and literal fingerprint; explain remaining activation gates. |
| `tests/test_catalogue_evidence_driver.py` | Exact approval/hash, explicit missing approval, tampering, recovery/gate denial, context isolation and strengthened unchanged package-identity assertions. |
| `tests/test_evidence_workflows.py` | Replace the successor-specific forever-unset expectation; retain all generation, isolation, pin, permission and mutation checks. |
| `docs/catalogue2-successor-approval-report.md` | This reproducible decision, validation and operator handoff. |

Before editing, SHA-256 values of all 199 tracked files were recorded in
`baseline.json`. After the source changes, only the three tracked files listed
above differed; all **196 other tracked files** were byte-identical. All **27
frozen preservation-control hashes** in
`tests/fixtures/publication_evidence/preserved.json` match unchanged. The report
is the sole new file. Historical S4 generation templates and archived workflows,
policy, trust, verifier distribution/roots, candidate registry, manifests, SDK,
original trust fixtures and all other production code remain unchanged.

No active workflow was edited or executed. No GitHub setting, ruleset,
environment protection, current pointer, release/asset, installed Connector,
production runtime or Atlas source was changed. Neither
`CATALOGUE_EVIDENCE_ENABLED` nor `CONNECTOR_PUBLICATION_ENABLED` was activated.
Positive/forged gate claims in tests are isolated in-memory dictionaries, not
operational configuration. No credentials were acquired; a dummy token is used
only to assert rejection/redaction. GitHub access was read-only decision/PR
verification. No commit, push, PR mutation, merge, tag, signing, publication,
deployment, LXC or Docker-host operation occurred.

No feature ledger or unrelated documentation was changed: this increment approves
one producer contract, not an end-to-end operational capability. The historical
producer reports are not rewritten to imply earlier approval.

## I. Outstanding acceptance gates

1. Owner source review and independently reviewed immutable producer S; no SHA is
   assigned by this report.
2. Successful hosted Python 3.12 CI and independent security review of the final
   exact source, fingerprint and preserved historical controls.
3. Separately reviewed workflow/build adoption pinned to frozen S, with independent
   signer/trust identity alignment. Existing active S4 remains unchanged here.
4. Separately authorized genuine acceptance-only signing: actual isolated signer,
   C/S/run/attempt identities, original evidence, permission isolation, Tlog
   witnesses and elapsed-time bounds.
5. Independent Atlas consumer-owned policy/signer/fingerprint acceptance and
   separate executable remote-installation approval. Producer acceptance cannot
   populate either consumer authority.
6. Explicit human publication-gate activation and one fresh authorized publication;
   anonymous seven-asset immutable readback, original signatures, complete history,
   actual publication timing and interrupted-provider acceptance remain unproven.

Disabled cross-job recovery is an accepted disposition, not a missing enable flag.
A failed/stranded release grants no new attempt or pointer advance. Any recovery
enablement requires a separately reviewed permanent recovery-archive contract and
implementation. Preserve original evidence after ambiguous writes.

## J. Human-controlled review, commit and freeze

**K1 — review now.** Inspect the complete diff and this report, independently
reproduce both hashes, verify the immutable decision sections, inspect the JUnit
evidence and unchanged-control results, and confirm all four changed files are
within scope:

```bash
git branch --show-current
git rev-parse HEAD
git status --short --branch
git diff --check
git diff -- tools/catalogue_evidence_driver.py tests/test_catalogue_evidence_driver.py tests/test_evidence_workflows.py
cat docs/catalogue2-successor-approval-report.md
```

**K2 — owner commit/push/PR after review.** These are operator instructions only;
the agent did not execute them:

```bash
git add tools/catalogue_evidence_driver.py tests/test_catalogue_evidence_driver.py tests/test_evidence_workflows.py docs/catalogue2-successor-approval-report.md
git commit -m "feat(catalogue): record approved successor publication contract"
git push -u origin feature/catalogue-v2-publisher-successor
gh pr create --base main --head feature/catalogue-v2-publisher-successor \
  --title "Approve release-owned Catalogue 2 successor contract" \
  --body-file docs/catalogue2-successor-approval-report.md
gh pr checks --watch
```

Require hosted validation; do not enable publication to obtain a green build.

**K3 — independent security acceptance.** Review the exact proposed commit,
canonical record/hash, full validation evidence, original authorization and signing
isolation, immutable staging/readback, deadlines and recovery denial.

**K4 — human-authorized merge and immutable S.** After review and CI, the owner
performs any merge. Retrieve the actual reviewed head and resulting producer
merge SHA. If the merge differs, verify its final merged source and all security
properties before designating that exact immutable commit S. A mutable branch,
synthetic test SHA or this pre-edit HEAD is not a frozen successor approval.

**K5 — separate workflow adoption.** In a new reviewed change only, prepare
Publisher/build workflows pinned to frozen S and coordinate independent signer/
trust identities. **K6 — separate genuine acceptance-only signing.** Only after
authorization, qualify actual evidence, isolation and timing. **K7 — later
publication.** Require independent security approval and explicit human gate
activation. K5–K7 are plans, not authorized actions in this task.

Final `git status --short --branch`; all changes remain unstaged and uncommitted:

```text
## feature/catalogue-v2-publisher-successor
 M tests/test_catalogue_evidence_driver.py
 M tests/test_evidence_workflows.py
 M tools/catalogue_evidence_driver.py
?? docs/catalogue2-successor-approval-report.md
```

HEAD remains `078f4099c3fcf850557bf9148db207f696c0ecad`. The accompanying Atlas
checkout remains clean and unchanged at its approval commit.
