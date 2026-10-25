# Phase 4B.2 — local package-publication qualification

Date: 26 October 2026. Local engineering only; no remote publication authority.

## A. Executive result

**PARTIAL — local mechanisms implemented and locally tested; production authority
and genuine acceptance remain blocked.** No LOCAL IMPLEMENTATION PASS is claimed
under the prompt's strict unresolved-prerequisite rule.

The reviewed future implementation SHA cannot exist before the human commits and
merges this work. All-zero pins are deliberately inert, package trust is disabled,
and a two-PR pinning/acceptance procedure is documented. Separately, the Verifier's
own credential cannot observe another App's effective installation grant. The
Publisher verifies its installation and issued token after signed admission and
before writes. That split requires explicit owner policy review if the request
requires independent effective permissions inside signed pre-token admission.
Neither policy gap is bypassed or represented as live verification.

## B. Repository and baseline

Repository: `benchristian88/atlas-connectors`. The existing clean local branch
`feature/connector-package-publication`, local main, fetched origin/main and HEAD
all began at merged PR #36:
`7bd6f42c668e90abdd4b692ab809edaa01446f98`. No branch switch or history edit was
necessary. Origin was fetched read-only; the branch remains uncommitted/unpushed.

Atlas `dev` was inspected read-only at
`808ee0f76f77c11e17a6c403806ce0666e30074e`; SDK `main` was inspected read-only at
`8b0518c462289cca4758c3b9bf362f1130928a1c`. Both began clean. No database/schema,
Manifest/compatibility, API/UI/route, qualified discovery or consumer code changes
are involved. Existing historical package/catalogue identities are preserved.

## C. Architecture alignment

Reviewed producer ADRs 0001–0005, Phase 4B.1 source/tests/report, publication policy
and trust, both existing publication workflows, deterministic builders and GET-only
release verifier. Atlas ADRs 0006/0011 preserve immutable verified supply-chain and
offline provenance boundaries; ADR 0013 approves exact original sequence one only.
Atlas ADR 0012 remains Proposed for stronger future publication evidence.

Reused existing qualified package selection/build/archive/SPDX/compatibility checks,
full ruleset validators, bounded GitHub transport, isolated Verifier JWT/token
authentication, gh 2.102.1/frozen roots, package attestation profile and final
anonymous verifier. A narrow adapter validates the new caller path then reuses
the frozen authority validator's common checks. No second generic publisher or
cryptographic trust service was introduced. Proposed producer ADR 0006 records
the new package-specific signer/admission boundary and unresolved owner decision;
it does not activate itself or modify an accepted historical ADR.

## D. Implementation and material files

| File | Purpose |
| --- | --- |
| `.github/workflows/connector-publish.yml` | Manual three-operation caller; default acceptance-only, fully skipped Publisher, inert S pins, shared non-canceling concurrency |
| `.github/workflows/connector-verifier.yml` | Separate isolated package signer, existing Verifier custody, public evidence only |
| `catalogue/publication/connector-trust.json` | New distinct disabled/unaccepted trust profile, exact existing ruleset/environment IDs, unset S |
| `tools/connector_publication_contract.py` | Bounded requests, complete inventory, separate admission and caller-path adapter |
| `tools/connector_publication_preflight.py` | Complete authenticated observations, signed-context validation, offline startup/same-job admission |
| `tools/connector_publication_sigstore.py` | Distinct package-admission certificate/subject/predicate profile using existing verifier/roots |
| `tools/connector_publication_github.py` | Exact original Actions artifact, bounded ZIP decoding, restricted redirect handling and local Publisher App/installation/token checks |
| `tools/publish_connector.py` | Data-only source checkout, pre-token preparation, separate tag/stage/finalize, safe failures/receipts |
| `tests/test_connector_publication.py` | Deterministic security, interruption, workflow isolation, provider and generic-Connector fixtures |
| `tests/test_historical_workflows.py` | Explicitly allow only the two requested disabled workflows alongside the existing five; preserve archived byte checks |
| `tests/test_publication_packaging.py` | Extend exact reusable-workflow allowlist to the inert package signer with the same restricted secret mapping |
| `docs/decisions/0006-connector-package-publication.md` | Proposed package authority decision; no activation |
| `catalogue/publication/connector-packages.md` | Exact configuration, request formats, pinning/acceptance, separate ceremony and recovery |
| `README.md` | Truthful current package-publication status/link |
| `catalogue/publication/README.md` | Current status and new procedure while retaining historical assessment |
| `catalogue/publication/consumer-handoff.md` | Package versus future catalogue/consumer authority boundary |
| This report | Qualification evidence, limitations and owner handoff |

No migrations are required. Existing APIs/UI/contracts/routes are unchanged; the
new workflow and package-admission profile are additive and disabled. Atlas's
feature ledger is outside this read-only task and was not changed.

## E. Identity and authorization

Official repository/owner IDs `1414494920`/`93822871`; maintainer `93822871`;
Publisher App/installation/bot `5422372`/`174027755`/`346232650`; Verifier
App/installation `5424851`/`174088125`. The original and triggering actors must
match; attempts other than one, wrong main/caller/signer, excessive permissions,
wrong environments, failed CI and incomplete bypass evidence reject.

Package admission has its own schema/predicate/subject and S; S4 is not accepted.
It binds the canonical full request, C, S, policy/trust hashes, original invocation
and complete privileged security observations. Freshness retains the existing
900-second startup and 1,800-second same-job limits. A local startup receipt is
never exported or treated as portable approval.

The Publisher job condition excludes acceptance-only before any key/token step.
The isolated Verifier receives only its existing key, never Publisher credentials.
The real Publisher mint is inside pinned code after admission and source/artifact
authentication, with exact baseline permissions and repository IDs. Key/JWT/token
remain process-local and never become outputs/logs/receipts. The actual live
installation/key-custody/hidden-settings state was not inspected with credentials.
The effective-permission pre-token evidence limitation in A remains unresolved.
Backend publication code is authoritative; no tenant/customer/site application
boundary is changed by this producer-only infrastructure work.

## F. Lifecycle and recovery

- **Tag:** exact reviewed merged main source, CI, compatible qualified metadata,
  deterministic D and equal workflow tree; private release absence and create-only
  ref. Stops after verifying T/C. Existing original App-triggered build is separate.
- **Stage:** successful original App build/attempt one; exact selected artifact
  ID/run/ZIP digest; genuine package-profile verification in production; all five
  original files retained unchanged. Creates only a non-prerelease draft, never
  latest. Rereads every uploader/ID/size/digest/byte and returns L/A/inventory.
- **Finalize:** new human dispatch explicitly approves complete C/T/D/R/L/A and
  five-asset inventory/digest. A distinct successful prior dispatch is checked.
  Revalidate immediately before one PATCH; then use the unchanged independent
  GET-only verifier to establish actual immutability and exact identities.

Ambiguous tag/create/upload failures are reread and stopped, without automatic
write retry. Partial drafts require new explicit approval of L and every existing
asset; only missing original files can be appended. A lost final response can
succeed only through exact independent immutable verification; a mutable,
conflicting, incomplete or unavailable observation fails. An already complete
immutable identity is reverified with zero PATCHes. No deletion, replacement,
retagging or historical rewrite is available. Expired original Actions artifacts
block this implementation; a retained local rebuild is not a fallback.

## G. Security testing and validation

Final validation passed as recorded below. Positive new-profile
signature-output tests and GitHub observations are explicitly synthetic. Genuine
historical package/catalogue/probe bundles are independently checked offline and
rejected as package-admission authority. No genuine package-preflight positive
signature or live workflow isolation acceptance is claimed.

The new tests cover wrong repository/owner/actors/App/installations/permissions,
environments, missing/changed bypass, CI, caller/S/profile, stale/replayed evidence,
existing tags/drafts, source review/ancestry/workflow mismatch, exact original
artifact selection, missing/substituted bundles/bytes, partial upload, changed
approved release/asset identities/inventories, mutable/contradictory publication,
failed rereads, lost responses, no retry and acceptance-only credential isolation.
Docker, UniFi and a future Connector fixture use the same stage/finalize logic.

The repository uses Python 3.12 in CI; the available local interpreter is Python
3.14.7. The inherited approved community.proxmox 2.0.0 collection is used with
Ansible enabled. Python 3.12 CI remains required after the human submits the PR.
Frontend, database and migration checks are inapplicable to this repository task.

| Executed command/check | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q tests/test_connector_publication.py tests/test_historical_workflows.py tests/test_publication_packaging.py tests/test_documentation.py --maxfail=2` | **172 passed**, including 147 new package-publication cases |
| `ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-phase4b1-test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q` | **2,027 passed**, no skips/failures, 180 inherited `ansible_runner` Python 3.14 deprecation warnings; final run 77.85 seconds |
| Genuine ephemeral RSA JWT test | Verifies actual local signature and Publisher issuer `5422372`; prevents accidentally reusing the Verifier helper's hardcoded issuer; no live App key/token |
| `/private/tmp/atlas-phase4b2-tools/actionlint -shellcheck= -pyflakes= .github/workflows/connector-publish.yml .github/workflows/connector-verifier.yml` | Passed workflow syntax/expression validation; optional shellcheck/pyflakes were not run |
| `.venv/bin/python -m compileall -q` with the five new helper paths | Passed |
| `tools/test_collection.py --archive /Users/Ben/Code/atlas/vendor/collections/community-proxmox-2.0.0.tar.gz --output /private/tmp/atlas-phase4b2-test-collections` | Approved archive SHA-256 `77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6`; all 189 fresh files byte-identical to the collection used in the full suite |
| `tools/release_connector.py --local --tag proxmox-v0.2.1 --output /private/tmp/atlas-phase4b2-review/candidate-first` and `tools/build_bundle.py --version 0.2.1 --output /private/tmp/atlas-phase4b2-review/candidate-second` | Both passed; all four output files byte-identical; local unattested archive `96eaa736c2919e56e09b9613dddd8648ad1f43b77679899ab706261b2a38e509` |
| Explicit original/candidate digest assertions using the existing builder | Historical 0.2.0 `a14fec5ab485c980688ff5907e8835ddd3e9cecd1a6989ef252cbcb1b1dc4ef8` and historical candidate `dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97` unchanged |
| `git diff --exit-code HEAD --` frozen workflows/helpers/policy/trust, catalogue releases and Connector source paths | Clean |
| `git diff --check` plus `git diff --no-index --check -- /dev/null FILE` for every untracked file | Clean |
| Documentation test in targeted/full suite | Markdown links, whitespace and fences passed |
| Atlas and SDK `git status --short` / exact HEAD | Both clean and unchanged at the read-only SHAs recorded in B |

The earlier full run exposed two exact workflow-inventory assertions that needed
the explicitly requested additions, and a report link written before its target
file existed. These were resolved; no historical byte test was removed. The final
full run includes all corrections. Actionlint 1.7.12 was downloaded only to `/tmp`
and matched published archive SHA-256
`aba9ced2dee8d27fecca3dc7feb1a7f9a52caefa1eb46f3271ea66b6e0e6953f`.
Logs and unattested reproducibility outputs are in
`/private/tmp/atlas-phase4b2-review`. The local digest is contextual evidence only;
the future reviewed/tagged committed-source build must establish its own D.

## H. Acceptance readiness

This is ready for review as **PR1 preparation**, not immediate dispatch. The exact
next controlled milestone is human PR1 review/commit/merge to establish S, then a
separate reviewed PR2 pins S and independent environment package trust while
publication stays disabled. Owner-run acceptance-only on C must authenticate the
new genuine signature, all complete observations, run/attempt and request, and
prove Publisher skipped/no write-token creation/no mutation. Preserve the original
public evidence before one-day expiry. Any unsupported live signer representation
requires reviewed correction and a new S, never a permissive fallback.

Only subsequent owner policy/security review and genuine acceptance can authorize
activation. The sole-maintainer model supplies no independent human veto. Same-
repository administrator, trusted code/action/provider/key compromise and changes
between observations remain risks. Signed snapshots do not prove continuous
protection or current hidden bypass. The original stage receipt is not human
approval or a permanent immutable evidence archive.

## I. Git and remote state

Final status/diff evidence follows. All work is scoped
to atlas-connectors on the existing feature branch. No commit, push, PR, merge,
rebase, tag, draft/release creation, workflow dispatch, live App-token mint, key
read/copy/change, permission/protection change or remote mutation was performed.
Network activity was read-only baseline fetch, official documentation and a
checksum-pinned temporary actionlint download. Test credentials are synthetic.

Frozen catalogue workflows/helpers/policy/trust, sequence-one files, historical
0.2.0 and 0.2.1 package inputs are unchanged. Atlas and SDK remain unchanged.

Branch remains `feature/connector-package-publication`, HEAD
`7bd6f42c668e90abdd4b692ab809edaa01446f98`. Five existing files are modified;
twelve files are new. Tracked diff: 42 insertions, 11 deletions. Untracked files
are listed explicitly because ordinary diff statistics omit them.

Final `git status --short`:

```text
 M README.md
 M catalogue/publication/README.md
 M catalogue/publication/consumer-handoff.md
 M tests/test_historical_workflows.py
 M tests/test_publication_packaging.py
?? .github/workflows/connector-publish.yml
?? .github/workflows/connector-verifier.yml
?? catalogue/publication/connector-packages.md
?? catalogue/publication/connector-trust.json
?? docs/decisions/0006-connector-package-publication.md
?? docs/phase-4b2-local-qualification.md
?? tests/test_connector_publication.py
?? tools/connector_publication_contract.py
?? tools/connector_publication_github.py
?? tools/connector_publication_preflight.py
?? tools/connector_publication_sigstore.py
?? tools/publish_connector.py
```

## J. Human handoff

Review every new/untracked file; ordinary tracked diff omits them. Human owner
performs all commits/push/PR/merge. Review proposed ADR 0006 and decide whether
the existing post-admission installation/token check satisfies the required
effective-permission boundary. If not, keep activation blocked for a separately
approved custody solution; do not widen permissions or move credentials here.

After pinning and genuine acceptance, request separate explicit authority for
each live tag/stage/finalize dispatch and inspect the exact staged identity before
finalization. Proxmox 0.2.1 remains unpublished. Final-artifact live qualification,
catalogue sequence-two immutable evidence/consumer authority and remote eligibility
remain later work. Preserve historical 0.2.0 and sequence one unchanged.
