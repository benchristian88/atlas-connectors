# Phase 4B.5 — S4 repinning and disabled qualification preparation

Date: 31 October 2026 (Pacific/Auckland). Local engineering only.

## A. Scope, identities and result

**PASS — S4 repinning and disabled qualification preparation validated locally.**
This change prepares independent S4 qualification; it grants no publication or
activation authority.

| Identity | Immutable revision |
| --- | --- |
| Approved package S4 / base / HEAD | `dc79af8e3115e263c267989dfa9ba72599c25463` |
| Previous package S3 | `be24042c4e7446c7d88d2f08608ab7f058bb24b6` |
| Frozen catalogue S4, separate implementation | `2dd1ffcd2f5677dc35bdbc8f68ea28275c91c285` |

Repository: `/Users/Ben/Code/atlas-connectors`. Requested branch
`feature/connector-publication-s4-pinning` already existed, clean at approved S4;
no branch recreation or history change was needed. Read-only
`git ls-remote origin refs/heads/main` independently returned exact S4, matching
local `origin/main` and HEAD. The initial sandboxed request could not resolve
github.com; the approved read-only network retry succeeded. No remote ref was
changed. There is no repository, ancestor or nested AGENTS.md in this checkout.

## B. Four exact bindings

Each binding replaces exact S3 above with exact S4 above:

| Binding | Location |
| --- | --- |
| Preflight reusable workflow `uses` | `.github/workflows/connector-publish.yml`, `jobs.preflight.uses` |
| Publisher executable checkout `ref` | Same workflow, first Publisher checkout |
| `ATLAS_IMPLEMENTATION_REVISION` | Same workflow, Publisher environment literal |
| `signer_revision` | `catalogue/publication/connector-trust.json` |

The workflow bytes equal the base file with exactly its three literal S3 SHAs
replaced by S4. Its existing PR41/S3 comment is preserved as required by the
byte-exact replacement boundary; this report records the current S4 binding.
No logic, conditions, job permissions, routes, actions, secret mappings,
environments or other workflow content changed.

## C. Disabled trust and live configuration boundary

Committed package trust is deliberately disabled and unaccepted:

```json
{
  "enabled": false,
  "live_signer_accepted": false,
  "max_observation_age_seconds": 900,
  "ruleset_ids": {
    "atlas-bootstrap-lock": 25628137,
    "atlas-catalogue-current": 25618684,
    "atlas-history-lock": 25618809,
    "atlas-main": 25618213,
    "atlas-publication-tags": 25618901
  },
  "schema": "atlas-connector-package-trust/v1",
  "signer_revision": "dc79af8e3115e263c267989dfa9ba72599c25463",
  "verification_environment_id": 25016263801
}
```

Schema, all five exact ruleset IDs, 900-second observation age and verification
environment ID are unchanged. Acceptance-only trust validation permits these
false flags; publication configuration rejects them before Publisher credentials.
This uses existing production validation without changing any security rule.

The owner reports `CONNECTOR_PUBLICATION_ENABLED` disabled. It was left untouched;
no live settings were read or changed to reconcile it. Live repository
`CONNECTOR_VERIFICATION_POLICY` may still contain the accepted S3 profile, including
true/true flags. That potential mismatch is intentionally unresolved and not
reported as updated or independently verified. Effective repository/environment
values and inheritance must be checked by the owner before any future run.

## D. Material files and compatibility

| File | Change |
| --- | --- |
| `.github/workflows/connector-publish.yml` | Three byte-exact S4 SHA replacements only |
| `catalogue/publication/connector-trust.json` | Fourth S4 pin and both false flags only |
| `tests/test_connector_publication.py` | Active S4 bindings, S3/mutable-pin negatives, disabled trust and actual entrypoint rejection |
| `tests/test_connector_sigstore.py` | Prospective synthetic S4 expectations; genuine historical claims unchanged |
| `tests/test_publication_packaging.py` | Exact active S4 reusable-workflow allowlist entry |
| `README.md` | Current S4 and disabled qualification status |
| `catalogue/publication/connector-packages.md` | Current S4 handoff and separate owner gates; historical evidence retained |
| This report | A–J evidence and human handoff |

No database or migration changes. No application API/UI, tenancy, package format,
release metadata, dependencies or publication request contract changed. There is
no feature ledger in this repository. Accepted ADRs and historical reports remain
unchanged; no architectural decision is revised. No Proxmox 0.2.2 is introduced.

## E. Security and permission invariants

Acceptance-only still defaults true and excludes the entire Publisher job,
including its protected environment and key/token steps. The separate repository
enable gate and successful preflight requirement remain. Verifier receives only
its explicit key mapping; no inherited secrets or Publisher key is added.
Main, official actor/repository/owner, original attempt, exact caller C and signer
S, request/trust/policy bindings, freshness and full ruleset checks are unchanged.
SAN, buildSignerURI and independent signer digest still require exact immutable S4.

Existing catalogue and package authority remain distinct. Publisher App baseline
stays Contents Write and Actions/Administration/Metadata Read, with Workflows
No access; registration/installation/token/single-repository scope checks remain.
No extra permission, workflow trigger or API route is added. The existing shared
non-canceling publication concurrency group is unchanged.

Tag, Stage and Finalize still reject unequal **entire source P / caller C workflow
directories**, including pin-only differences, existing drafts and published
identities. Original mismatch regressions run unchanged; no post-tag exception,
Workflows Write expansion, credential fallback or source retargeting is introduced.

## F. Tests and validation

Commands run from the Connector repository. WORK means
`/private/tmp/atlas-phase4b5-s4-review`, containing logs and preservation inventory.
Local interpreter is Python **3.14.7**; hosted Python **3.12** validation remains
the separate PR CI gate. Existing pinned development dependencies are installed.

| Executed command/check | Result |
| --- | --- |
| `.venv/bin/python tools/test_collection.py --archive /Users/Ben/Code/atlas/vendor/collections/community-proxmox-2.0.0.tar.gz --output WORK/test-collections` | Passed exact reviewed archive hash `77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6`; sibling input read only |
| `.venv/bin/python -m pytest -q tests/test_connector_publication.py tests/test_connector_sigstore.py tests/test_connector_draft_recovery.py tests/test_publication_packaging.py` | **712 passed**, 17.25 seconds; `focused-security-signing.log` |
| `ATLAS_TEST_COLLECTIONS_PATH=WORK/test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q` | **2,580 passed**, zero failures/skips, 69.64 seconds; 180 existing Python 3.14 `ansible_runner` deprecation warnings; `full-ansible.log` |
| `/private/tmp/atlas-phase4b2-tools/actionlint -shellcheck= -pyflakes= .github/workflows/*.yml` | Passed all seven workflows, actionlint **1.7.12**; optional shellcheck/pyflakes disabled; `actionlint.log` |
| `.venv/bin/python WORK/verify-preservation.py` | **PASS**, complete baseline inventory, exact caller/trust bytes, historical context/fixtures, refs/index/HEAD/siblings; `preservation.json` |
| `.venv/bin/python -m pytest -q tests/test_documentation.py` | **1 passed**; repository Markdown links, whitespace, newlines and fences; `documentation.log` |
| `git diff --check` | Clean tracked-file whitespace |
| `.venv/bin/python -m compileall -q tools tests` | Passed |
| `.venv/bin/python -m pip check` | No broken requirements; unwritable pip-cache warning only |

The initial focused run had **3 failed, 709 passed**: a new acceptance configuration
assertion incorrectly looked for `implementation_sha` in caller context. That
field belongs to the signed preflight; the test now checks returned trust's signer
revision and exact existing context contract. No production rule was modified.
All original signer-identity/malicious-pin cases are retained, with previous S3
and the mutable S4 branch added as negative active-pin authorities. Synthetic S4
models are not genuine signing evidence. Existing acceptance/input entrypoint tests
explicitly enable synthetic trust so disabled trust cannot mask their old checks.
New actual-entrypoint cases cover every Tag/Stage/Finalize and
authorize/prepare/execute combination with each disabled/unaccepted flag state,
asserting `connector_publication_disabled` before source/admission/preparation/mint.

## G. Byte preservation and historical fixture integrity

**PASS:** of **171** original tracked files, exactly the seven authorized files in
section D changed and **164** are byte-for-byte unchanged; this report is the only
new file. All **234** existing ignored `dist/` files and **26** historical fixture
files remain exact. HEAD, local refs/tags, index and sibling repository
HEAD/status/refs are unchanged. Every original tracked file was compared with
S4 Git bytes and its baseline SHA-256.

The passed checks cover all six other GitHub workflows, all tools including the existing S4
implementation, frozen catalogue engine/trust/policy, SDK wheel/hash locks,
dependencies, trusted roots, Connector/package source and release metadata.
Historical reports, all fixtures and genuine attestations remain byte exact.
The original failed-run job context, historical certificate decoder/assertions
and runbook's historical 0.2.1 identity table also match the baseline.

Genuine S2 bundle SHA-256 remains
`f85c122df49f2c49c0117830dc81c00a52670e982368407ba9b406c74c96eb80`;
certificate PEM SHA-256 remains
`f4fa1cc084858a52e94e54adfc4a0a6852e14fee3c45fba26119ad524bf99d90`.
Historical genuine S3 acceptance and activation reports are retained, without
relabelling their evidence as S4. S3 acceptance run `40542954614` remains historical.

Protected `proxmox-v0.2.1`, source `d3f66b039e2027832be932cacd006d86442821ec`,
original build `41017538114`, artifact `12960302111`, incomplete draft `428740362`
and checksum asset `691270692` retain their historical references. No request,
inspection, download or mutation of that draft occurred. No Connector release,
tag, package bytes or release metadata changed, and no 0.2.2 artifact was created.

## H. Required PR and hosted CI review

Human review must confirm the exact four S4 bindings, disabled trust and preserved
workflow bytes, review the security/test changes and complete required hosted
Python 3.12 `validate` CI before merge. Local Python 3.14 results do not claim that
hosted gate passed. No PR was opened, committed, pushed or merged by this task.
The owner must separately review live policy mismatch and effective overrides;
do not automatically copy the committed JSON into repository settings.

## I. Genuine acceptance-only qualification requirements

After reviewed repinning is merged, separately authorize matching independent
S4 repository trust configuration with **both flags false**, verify effective
environment/organization overrides, complete live protections and the disabled
publication enable gate. Preserve the accepted split least-privilege boundary
from ADR 0006; do not use Publisher credentials to inspect configuration.

Obtain distinct authority for a **new original main acceptance-only run** at
advancing caller C, signer exact S4, first attempt and reviewed bounded request.
Do not rerun historical S3 evidence as S4 acceptance or select the abandoned
0.2.1 draft for recovery. Retain original subject bytes, artifact ZIP, original
Sigstore bundle/certificate/statement, run/job/invocation evidence, request,
policy/trust bytes and complete signed security observations. Authenticate the
original subject digest/signature offline with pinned gh and frozen roots, checking
exact S4 signer SAN/URI/digest, caller C and all existing constraints. Synthetic
certificates or decoded historical claims alone cannot qualify S4.

Require genuine Publisher-skipped evidence before its environment/key/token steps,
no Publisher credential access or write operations, and no tag/release creation.
Acceptance-only does not validate package source/build, effective Publisher
installation permissions or any publication operation, and grants no activation
authority. Unavailable or mismatched evidence stops qualification.

## J. Human-controlled activation boundary and repository state

Activation requires later explicit owner approval after genuine S4 acceptance and
fresh effective-control review. Any live trust flag or publication-enable change
is a separately authorized owner action. Future clean release source, exact
package digest and full P/C workflow equality require their own reviewed evidence;
Tag, Stage and Finalize each require distinct human authorization. Catalogue
publication remains separately controlled by its frozen implementation.

No commit, staging, push, merge, tag, release, dispatch/rerun, variable/settings/
permission change, Publisher credential access or App token mint occurred. Changes
remain local, unstaged and uncommitted. Final `git status --short`:

```text
 M .github/workflows/connector-publish.yml
 M README.md
 M catalogue/publication/connector-packages.md
 M catalogue/publication/connector-trust.json
 M tests/test_connector_publication.py
 M tests/test_connector_sigstore.py
 M tests/test_publication_packaging.py
?? docs/phase-4b5-s4-repinning.md
```

Conclusion: **PASS** for local repinning and disabled qualification preparation.
Hosted PR CI/security review, genuine S4 acceptance and human activation gates
remain outstanding by design. Publication and activation are not authorized.
