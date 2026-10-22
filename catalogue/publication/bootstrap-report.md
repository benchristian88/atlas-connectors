# P2 sequence-one bootstrap implementation and acceptance record

22 October 2026. Local implementation on `feature/catalogue-sequence1-bootstrap`,
base HEAD `4f99f8b82c63f87f69b3a514be7660d6ffbc9abe`; intended target `main`.
No migration, token minting, workflow trigger, Git mutation, release/tag/branch
creation, settings change or PR action was performed. All changes are uncommitted.
Atlas and atlas-connector-sdk were inspected/tested read-only and remain unchanged.

## A. Executive assessment

Implemented the distinct, disabled bootstrap transition on the existing P1
publisher. It preserves original bytes/provenance, stages and authenticates the
new selection, stops for separate actual-digest approval, verifies immutable
finalisation, and creates a fenced parentless current root with a sanitized receipt.

Ready for code/security review; **not live P2 production acceptance**. Real settings
validation, additional fence protection, approved staging/activation, new genuine
selection evidence, immutable release/root receipt and independent Atlas support
remain outstanding. No real new provider IDs or pointer digest were invented.

## B. Code and workflow changes

| Material file | Purpose |
| --- | --- |
| tools/bootstrap_catalogue.py | Fixed historical pins, read-only preflight, bounded draft inventory, exact-byte staging, separate activation, receipt |
| tools/publication_contract.py | Explicit operation-aware configuration using unchanged P1 authorization, bootstrap stage/activate checks and fence ruleset |
| tools/publication_github.py | Create-only root/fence transport; exact root/tree/blob verification; inspect lost branch-create response without replay |
| tools/publish_catalogue.py | Explicit bootstrap CLI routing, fixed workflow-operation/phase gates; ordinary stage/recover stay closed before history |
| .github/workflows/catalogue-publish.yml | Fixed bootstrap choice in existing manual signer, mutually exclusive policy-selected staging/activation, same scoped App/concurrency |
| catalogue/publication/policy.json | Add bootstrap_operation=disabled; preserve enabled=false, null bootstrap pins and all existing reviewed identities |
| tests/test_publication_bootstrap.py | Explicitly simulated provider/selection transitions, failure/security/lifecycle cases and workflow CLI routing |
| tests/test_publication_crypto.py | Genuine source preflight, catalogue-to-pointer rejection and tampered-signature regression |
| tests/fixtures/publication/README.md | Distinguish model evidence from unchanged genuine fixtures |
| docs/decisions/0003-sequence-one-bootstrap.md | New proposed decision for two-dispatch trust activation and protected one-time fence |
| catalogue/publication/bootstrap.md | Exact future operator steps, settings checklist and interrupted-publication table |
| catalogue/publication/bootstrap-report.md | This implementation/evidence record |
| catalogue/publication/README.md | Integrate bootstrap and remove superseded no-bootstrap claims |
| catalogue/publication/consumer-handoff.md | Exact consumer boundaries, root approval, history/legacy requirements |
| README.md; catalogue/README.md | Truthful feature status and links |

No database/schema/migration is required. No Atlas API, UI, SDK, Manifest, package
recipe, release registry, verifier implementation or cryptographic trust material
changed. Existing normal workflow choices retain their behavior. Direct workflow
CLI phases now explicitly require the matching PUBLICATION_OPERATION context.
The seven-field pointer and four-asset snapshot contracts are unchanged.

## C. Exact historical evidence

Frozen catalogue: **10,585 bytes**, schema 1.0, sequence 1, SHA-256
`55533ca67e7e9a14f82961e0a8c34ad78e2596049b3db02fde787494e3975afd`.
Source `91dfd86f18d0b59ff977bb1e8a5fef42c5329943`;
`.github/workflows/catalogue.yml@refs/heads/main`; attestation reference **57152061**.
Original bundle SHA-256
`0a404de77a6c47dc2f08e3acecf835a01313e924f6883a4b13d720c57610f72f`.

Legacy release **416561696**, tag `catalogue-v1`; original JSON assets
**653915685** (`catalogue.json`) and **653915743** (`catalogue-000001.json`).
Repository **1414494920**, owner **93822871**. These pins come from independently
captured source evidence, not downloaded catalogue trust claims.

Real pinned gh 2.102.1 and frozen roots verified original catalogue and package
provenance offline. No live legacy refresh was performed in this task. Tests
confirmed unchanged original package SHA-256
`a14fec5ab485c980688ff5907e8835ddd3e9cecd1a6989ef252cbcb1b1dc4ef8`.
The historical candidate remains
`dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97`.
Source fixtures, packages, Manifests, SDK wheel and trust data have no Git diff.

## D. State machine and transaction boundaries

- A: Offline genuine-source/configuration preflight; separate all-GET live
  authority/settings/legacy/empty-history inspection before any publication write.
- B: Approved stage dispatch creates/reuses the exact draft, uploads original
  bytes/bundle, obtains actual IDs, signs current.json and verifies all four files.
  Ends in staged_requires_separate_approval. No finalisation occurs here.
- Approval: Later protected-main policy revision pins the actual canonical pointer
  digest and sequence 1, selects activate, and receives successful exact-source CI.
- C: Fresh activation dispatch verifies both original selection and current human
  authority, finalises with make_latest=false, and rechecks immutable status,
  source/tag and all four asset IDs/bytes/signatures.
- D: Create and inspect a parentless two-file Git commit; create the protected
  root-intent fence; create current with POST only; reread exact root/ref/fence and
  immutable evidence. Every write is a separate provider transaction.
- E: Emit the sanitized observed-state receipt. It grants no consumer authority.

Deterministic operation identity:
`c61474c1d13629cb3c11bf70d9bdce0a52148b070a5a987066964157bdd1114f`.
It is a staging correlation value, not a pointer digest or signature.

## E. Authorization

Unchanged `single-maintainer-v1`: maintainer **93822871**, publication environment
**24999137498**, package environment **24617213627**, App **5422372** /
`atlas-catalogue-publisher`, installation **174027755**, bot **346232650**.
Both actors, independent user/run/attempt/workflow/repository records, main-only
manual dispatch, attempt 1, exact successful validate CI, protected source,
environment restrictions, exact App scope/permissions and historical no-bypass
rules remain mandatory. There is no independent second-human approval claim.

New bootstrap-only `atlas-bootstrap-lock` must protect exactly
`refs/tags/catalogue-bootstrap-root` from update/deletion with no bypass, including
the App. Existing App-only tag creation still applies. Actual enforcement has not
been configured or proven here. Publication remains disabled.

## F. New selection signature

Subject is the actual canonical `current.json`, exactly seven fields, sequence 1,
null predecessor, original catalogue digest and actual new release/snapshot IDs.
Its digest is over the pointer bytes, not over the catalogue. Signer remains
`.github/workflows/catalogue-publish.yml@refs/heads/main`; issuer, numeric identities,
hosted runner, SLSA/DSSE/profile, certificate/source and invocation checks reuse P1.
The original build bundle cannot authenticate this selection.

The signing invocation authorizes selection once the named release is immutable;
it does not claim draft immutability. Activation separately checks a later reviewed
policy/source and fresh run. **No new genuine signature exists from this task.**
Model fixtures never pass the production verifier and are not approval inputs.

## G. Immutable publication

Target is `catalogue-000001`. Exact assets: catalogue-000001.json,
catalogue.sigstore.json, current.json, current.sigstore.json. Provider release and
asset IDs are captured only during live staging, then bound by the canonical
pointer and its separately approved digest. All four asset IDs and bytes are
compared across finalisation. Draft=false, prerelease=false, immutable=true and
actual tag/source binding are mandatory before root creation.

Legacy releases/assets stay intact. No live release was created or selected.
Provider immutability remains an API enforcement claim, separate from original
build provenance and new cryptographic selection evidence.

## H. Recovery

Complete bounded release enumeration includes drafts and rejects duplicates,
conflicting history and overflow. Existing assets are only read/compared; missing
draft assets can be added on a fresh authorized stage dispatch. Signing interruptions
can resume without rebuilding, even after main advances. Incomplete drafts cannot
activate. A complete immutable snapshot with no current/fence can resume activation
using its original approved selection after a fresh dispatch.

Ambiguous writes are never replayed blindly. Lost current-create responses are
inspected against the exact root/ref/fence. Existing current ends bootstrap; the
protected fence prevents resurrection after branch loss. Fence-without-current,
including interruption between those writes, requires a **separately reviewed
recovery decision**. No automatic fence clearing or branch recreation is provided.
That conservative boundary also handles a lost successful response discovered only
by a later invocation. Ordinary publish/recover are never initialization fallbacks.

## I. Legacy package

The exact active Proxmox 0.2.0 catalogue entry is preserved as historical knowledge.
Its mutable package remains ineligible for B3 remote installation. Bootstrap neither
downloads nor executes packages and adds no vendor-specific qualification exception.
Normal P1 still checks every active package. A later reviewed sequence must retain
the old identity as withdrawn history if advancing alongside a new qualified
immutable package. No such withdrawal or release was made here.

## J. Tests and validation

Final results, with zero failed and zero skipped tests in each pytest command:

| Command / scope | Result |
| --- | --- |
| `ATLAS_TEST_COLLECTIONS_PATH=/tmp/atlas-catalogue-followup-test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q` | **822 passed**, 0 failed, 0 skipped; includes all 20 real Ansible fixture cases; 180 upstream Ansible Runner codecs.open deprecation warnings |
| `.venv/bin/python -m pytest --noconftest -q tests/test_publication_bootstrap.py tests/test_publication_contract.py tests/test_publication_state.py tests/test_publication_transport.py tests/test_publication_packaging.py tests/test_publication_crypto.py tests/test_catalogue.py tests/test_documentation.py` | **534 passed**, 0 failed, 0 skipped; includes genuine pinned verification and deterministic workflow dispatch routing |
| From atlas-connector-sdk: `PYTHONDONTWRITEBYTECODE=1 /Users/Ben/Code/atlas-connectors/.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_contracts.py` | **14 passed**, 0 failed, 0 skipped; sibling remains unchanged |
| `.venv/bin/python tools/publish_catalogue.py bootstrap-preflight` | Successful genuine offline original-source verification; enabled=false; remote_checks_performed=false |
| `/tmp/atlas-p1-actionlint .github/workflows/*.yml` | Exit 0; all four workflows pass |
| `.venv/bin/python -m compileall -q tools tests` | Exit 0 |
| `git diff --check` | Exit 0 |
| `git diff --exit-code -- tests/fixtures/official_catalogue tests/fixtures/publication/catalogue.sigstore.json tests/fixtures/publication/package.sigstore.json connectors catalogue/releases vendor/sdk tools/publication_verify.py tools/publication_trust` | Exit 0; frozen source/package/trust inputs unchanged |
| `shasum -a 256 tests/fixtures/official_catalogue/catalogue-000001.json tests/fixtures/publication/catalogue.sigstore.json tests/fixtures/publication/package.sigstore.json` | Exact pinned catalogue/bundle hashes; package evidence hash 2929b38721e31d48ca9ee8a51753c595880dca3c5fef9dea79c8bfdf0dca7db4 |

Earlier development runs also passed: 218 contract/state tests; 281 P1 publication
tests; 174 catalogue/documentation tests. Final aggregate commands above include
those cases; counts must not be added as unique tests.

Tests ran on the available Python 3.14 environment. The configured GitHub Python
3.12 workflow was linted/model-tested but not dispatched. Actual new selection,
provider settings, immutable release and root acceptance were not executed and
remain explicit live gates, not skipped unit tests.

## K. Operator runbook

Follow the exact ten-step [bootstrap procedure](bootstrap.md): offline source
validation; historical identity/settings/fence review; separately authorized
stage-only policy and main dispatch; genuine pointer evidence inspection; later
actual-digest policy approval and fresh dispatch; immutable finalisation; root
creation and evidence rechecks; independent Atlas bootstrap approval; disable
bootstrap and use normal contiguous publication; retain legacy ineligibility.
No commands for creating a release, ref or token were run during this task.

## L. Atlas consumer handoff

Atlas's existing B1.3 `publication_not_immutable` and
`current_channel_policy_unavailable` gates remain unchanged. The later independent
consumer implementation must add the selection profile/current-channel adapter,
approve actual root digest and identities, verify snapshot and both signatures,
persist pointer/history/high-water state, and demonstrate first trust, unchanged
confirmation, advancement, restart and last-known-good behavior. Producer policy,
API receipts and a successful unit suite cannot substitute for that trust decision.
See the [expanded handoff](consumer-handoff.md).

## M. Remaining blockers

Owner approval of this implementation/ADR and additional fence protection; live
identity/App/installation/security-setting evidence; staging authorization; actual
genuine signed pointer and verified IDs; separate exact-digest approval; immutable
finalisation/root receipt; consumer trust activation and live acceptance. The
marker-only interruption remains intentionally outside automatic recovery. A later
qualified immutable Proxmox package is still required for remote installation.
No current GitHub settings or account plan is inferred from historical observations.

## N. PR readiness and repository state

Implementation and local tests are reviewable. Policy stays disabled with null root
pins. No commits, PRs, branches, tags, releases, settings or workflows were created
or changed remotely. All material local changes are listed in section B. The human
operator controls any subsequent Git/PR actions. This is foundations readiness,
not P2 production acceptance.

Final `git status --short` in atlas-connectors:

```text
 M .github/workflows/catalogue-publish.yml
 M README.md
 M catalogue/README.md
 M catalogue/publication/README.md
 M catalogue/publication/consumer-handoff.md
 M catalogue/publication/policy.json
 M tests/fixtures/publication/README.md
 M tests/test_publication_crypto.py
 M tools/publication_contract.py
 M tools/publication_github.py
 M tools/publish_catalogue.py
?? catalogue/publication/bootstrap-report.md
?? catalogue/publication/bootstrap.md
?? docs/decisions/0003-sequence-one-bootstrap.md
?? tests/test_publication_bootstrap.py
?? tools/bootstrap_catalogue.py
```

`git status --short` in both Atlas and atlas-connector-sdk produced no output.
