# P1 single-maintainer publication — implementation report

The original [P1 report](completion-report.md) is historical. This follow-up changes
only atlas-connectors on feature/immutable-catalogue-publication and leaves all
work uncommitted. No remote publication, tags, settings, branches or PRs were changed.

## Authorization model

`single-maintainer-v1` requires a fresh manual catalogue-publish.yml dispatch on
protected main. Both original and triggering API actors must match one explicitly
configured numeric human ID, independently corroborated by public user lookup.
Run and attempt-1 records, workflow identity, repository/owner identities, source
ref/SHA and successful validate CI must agree. The genuine selection signature
binds exact pointer bytes, workflow source and invocation to those observations.
A preflight checks dispatch identity before issuing App credentials; staging and
finalisation repeat authority/protection checks, including immediately before
advancing current after locking the snapshot. Recovery uses a fresh dispatch
and retains the original authenticated snapshot and selection bytes.

The assurance is **single-maintainer authorization**, not independent human approval.
Neither environment requires reviewers, and no self-approval workaround exists.
Main still requires PRs and strict CI with no bypass or force-push/deletion; its
necessary solo-maintainer adjustment is zero approvals and no last-push approval.
A compromised maintainer account has no second human veto. A correct stolen App
key cannot be detected as stolen, but cannot impersonate the configured human
actor or forge the selection signer; conflicts and denial of service remain risks.

The App remains dedicated/scoped with Contents write, Actions read, Administration
read and Metadata read. Its ID/slug/installation/bot-user identities are pinned;
JWT-authenticated pinned action outputs, public App permissions and token repository
scope are checked. CI reads are anonymous to avoid widening App permissions.
The tag-based B1.2 package signer remains unchanged: App build identity proves
provenance and the explicit catalogue dispatch authorizes package inclusion.
Unknown future modes fail closed; dual control requires a new reviewed policy,
producer/consumer implementation and deliberate historical acceptance boundary.

## Changed files in this follow-up

- `.github/workflows/catalogue-publish.yml`: identity preflight, explicit App output
  binding and accurate single-maintainer naming; existing minimal permissions kept.
- `.github/workflows/release.yml`: reject reruns early and clarify build/inclusion
  authority; original tag signer retained.
- `.github/workflows/catalogue.yml`: clarify the separate dispatch authority comment.
- `catalogue/publication/policy.json`: explicit mode and null maintainer/App identities;
  activation stays false and bootstrap pins stay null.
- `tools/publication_contract.py`: strict external policy, identity/API/CI checks,
  App binding and mode-specific protected-main/environment requirements.
- `tools/publish_catalogue.py`: independent evidence reads and preflight, source/context
  binding, package App/tag checks and sanitized authorization receipt context.
- `tools/publication_github.py`: bounded fixed-origin identity/scope reads and explicit
  anonymous read support; no broader write destination or credential forwarding.
- `tests/test_publication_contract.py`, `tests/test_publication_state.py`,
  `tests/test_publication_transport.py`, `tests/test_publication_packaging.py`:
  deterministic authorization, provider, transport, workflow and recovery regressions.
- `catalogue/publication/README.md`, `catalogue/publication/consumer-handoff.md`,
  `README.md`, `catalogue/README.md`: accurate authorization, settings, runbook and
  exact independent Atlas verification requirements.
- `docs/decisions/0002-single-maintainer-publication.md`: explicit new policy decision;
  `0001-github-catalogue-publication.md` links the amendment without erasing history.
- `catalogue/publication/completion-report.md`: marks the old policy report historical;
  this file records the follow-up scope, evidence and remaining blockers.

No database, application API, SDK or Atlas changes. Pointer fields, signing profiles,
original sequence-1 bytes/attestations, immutable snapshot scheme, predecessor chain,
rollback rules and generic packaging remain intact. Existing prior uncommitted P1
files are retained; the final git status includes that earlier work too.

## Required configuration and remaining blockers

Supply the actual maintainer ID, environment IDs, dedicated App ID/slug/installation/
bot ID, App key/variable and reviewed bootstrap sequence/digest. Configure all four
exact rulesets, both environments without required reviewers/admin bypass, default
read-only Actions permissions and future release immutability as in the
[runbook](README.md). Verify these settings and the anonymous evidence API paths.
The policy deliberately stays disabled until those inputs and reviews exist.

The legacy bootstrap migration has **not** been implemented or approved. Legacy
sequence 1 and Proxmox 0.2.0 remain untouched; the mutable old package cannot become
eligible by changing authorization policy. Decide its retained non-installable
history and publish a new qualified immutable version through the scoped App.
Package tag creation/staging/finalisation remains an operator procedure, not newly
automated infrastructure; one person can perform it without a second reviewer.

Atlas still needs the distinct selection profile and independently configured
single-maintainer trust policy, full API actor/run/attempt/workflow/CI/protection
checks, immutable selection/history/bootstrap/high-water handling and acceptance
tests described in the [handoff](consumer-handoff.md). It must not adopt IDs from
a pointer or producer policy file. No Atlas code was modified.

No genuine new signed selection, immutable snapshot or enforced live publication
has been produced. Those remain explicit acceptance prerequisites. Current GitHub
settings cannot prove past uninterrupted enforcement, historical reruns/account
renames/deleted evidence can block verification, and API rate limits/availability
fail closed. These are availability/trust limitations, not independent approval.

## Validation

Commands actually executed on Python 3.14.7:

- `ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-catalogue-followup-test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q`
  — **743 passed**, zero skipped, 37.85 seconds. There were 180 existing
  ansible_runner `codecs.open` deprecation warnings under Python 3.14.
- `/private/tmp/atlas-p1-actionlint .github/workflows/ci.yml .github/workflows/release.yml .github/workflows/catalogue.yml .github/workflows/catalogue-publish.yml`
  — passed, actionlint 1.7.7, no diagnostics.
- `.venv/bin/python -m compileall -q tools tests` — passed.
- `git diff --check` — clean.
- `.venv/bin/python tools/publish_catalogue.py authorize` — expected exit 1,
  `publication_disabled`; startup stopped before GitHub access or credential issuance.
- `shasum -a 256` on the frozen catalogue, legacy publication metadata and both
  original attestation fixtures — all four hashes match their original values.
  Sequence-1 catalogue remains 10,585 bytes with SHA-256
  `55533ca67e7e9a14f82961e0a8c34ad78e2596049b3db02fde787494e3975afd`.
  Full-suite archive regressions also preserved both normal/candidate bundle hashes.

Simulated GitHub API and structural selection evidence tests do not constitute
genuine signature acceptance. The full suite separately executed all three genuine
B1.2 cryptographic tests with the pinned verifier and frozen public catalogue/package
evidence. No genuine new pointer proof or live GitHub enforcement was tested.
No frontend/database checks apply. Atlas and SDK `git status --short` were empty.

## Repository state

Branch remains `feature/immutable-catalogue-publication`; HEAD remains
`83339e1747dc651ccdbdf4ab9ca8d4bc91d8c831`. No commit, push, branch, merge, reset or PR
was performed. This status includes the preceding uncommitted P1 implementation.

`git status --short`:

```text
 M .github/workflows/catalogue.yml
 M .github/workflows/ci.yml
 M .github/workflows/release.yml
 M .gitignore
 M README.md
 M catalogue/README.md
 M tests/test_documentation.py
 M tools/build_bundle.py
?? .github/workflows/catalogue-publish.yml
?? catalogue/publication/
?? connectors/proxmox/package.json
?? docs/
?? tests/fixtures/publication/
?? tests/test_publication_contract.py
?? tests/test_publication_crypto.py
?? tests/test_publication_packaging.py
?? tests/test_publication_state.py
?? tests/test_publication_transport.py
?? tools/prepare_publication_verifier.py
?? tools/publication_contract.py
?? tools/publication_github.py
?? tools/publication_trust/
?? tools/publication_verify.py
?? tools/publish_catalogue.py
?? tools/release_connector.py
```
