# P1 implementation completion report

Historical report of the original P1 implementation. Its separate-reviewer policy
is superseded by the [single-maintainer follow-up report](single-maintainer-report.md)
and [ADR 0002](../../docs/decisions/0002-single-maintainer-publication.md).

22 October 2026. Local implementation only; all source changes remain uncommitted.

## A. Executive assessment

Implemented fail-closed GitHub publication foundations: strict pointer protocol,
sequence/history protection, bounded authenticated transport, genuine offline
provenance verification, draft staging, immutable finalisation checks, atomic
current selection, safe retries/recovery and generic qualified package preparation.

**Ready for code and owner review, not live production publication.** Default
policy remains disabled. Actual GitHub inspection found unprotected main, no
rulesets, an unprotected connector-release environment and mutable legacy catalogue
and Proxmox 0.2.0 releases. Owner configuration, independently approved bootstrap
migration, legacy package handling and Atlas consumer/profile changes remain
required. No new signed pointer or immutable publication has been produced.

## B. Architecture decision

[ADR 0001](../../docs/decisions/0001-github-catalogue-publication.md) proposes one
immutable Release per sequence and a dedicated `catalogue-current` branch carrying
exact signed selection bytes/bundle. A single-parent non-force ref update gives
atomic advancement and race rejection. Signed predecessor digests bind history.

Rejected mutable catalogue-v1 replacement, freezing the advancing alias,
repository-wide `/releases/latest`, signed commits alone and external services.
The seven-field pointer is separate from the unchanged six-field catalogue.
Human approval is independently checked GitHub API/policy evidence; it is not
misrepresented as a human cryptographic signature.

## C. Repository state and material files

Repository: `atlas-connectors`.
Branch: `feature/immutable-catalogue-publication`.
Starting and ending HEAD: `83339e1747dc651ccdbdf4ab9ca8d4bc91d8c831`.
Starting worktree was clean; all changes below are uncommitted.

| Files | Purpose |
| --- | --- |
| `.github/workflows/catalogue.yml` | Main-only build provenance; separate publication authority |
| `.github/workflows/catalogue-publish.yml` | Protected publish/recover, scoped App credentials, signing and concurrency |
| `.github/workflows/release.yml` | Generic qualified tag selection; preserved package signer identity |
| `.github/workflows/ci.yml` | Provision pinned verifier for genuine offline tests |
| `.gitignore` | Exclude local verifier executable |
| `tools/publication_contract.py` | Pointer, sequence/history, environment/review/ruleset contracts |
| `tools/publication_github.py` | Bounded provider API, staging, pinned channel reads and CAS |
| `tools/publication_verify.py` | Pinned genuine Sigstore verification and exact profiles |
| `tools/publish_catalogue.py` | Staging, immutable finish, authority/package/history checks and recovery |
| `tools/prepare_publication_verifier.py` | Hash-verified upstream verifier provisioning |
| `tools/build_bundle.py` | Explicit generic recipe packaging with historical byte compatibility |
| `tools/release_connector.py` | Exact tag/qualified Manifest selection without an ID allowlist |
| `connectors/proxmox/package.json` | Existing reviewed file list and candidate overrides as data |
| `tools/publication_trust/distribution.json`, `trusted-root.jsonl`, `LICENSE.gh`, `README.md` | Public pinned upstream verification data and licence |
| `tests/test_publication_contract.py` | Schema, sequence, history, authorization/ruleset negatives |
| `tests/test_publication_state.py` | Explicitly mocked provider transitions, failure recovery and future Connector |
| `tests/test_publication_transport.py` | Controlled HTTP limits, credentials, redirects, retries and races |
| `tests/test_publication_packaging.py` | Frozen archive identity, generic recipes/qualification and workflow boundaries |
| `tests/test_publication_crypto.py` | Genuine original catalogue/package acceptance and negative profiles/bytes/source |
| `tests/fixtures/publication/catalogue.sigstore.json`, `package.sigstore.json`, `README.md` | Genuine frozen public evidence; no synthetic pointer proof |
| `tests/test_documentation.py` | Include new ADR/runbook/trust/fixture documentation in link/layout checks |
| `README.md`, `catalogue/README.md` | Current delivery status and correction of legacy immutability claims |
| `catalogue/publication/policy.json` | Disabled owner-reviewed authority/bootstrap configuration |
| `catalogue/publication/investigation.md` | Verified starting code, provider state and feasibility gate |
| `catalogue/publication/README.md` | Exact contract, operator settings, ordering, migration/recovery and limits |
| `catalogue/publication/consumer-handoff.md` | Exact Atlas profile/source/persistence/test work |
| `catalogue/publication/completion-report.md` | This A–N report |
| `docs/decisions/0001-github-catalogue-publication.md` | New proposed producer decision, no historical ADR rewrite |

Atlas remains clean at `41e615d8aaf90ecbd81456641a0968f0db1bd2b0`; SDK remains clean
at `8b0518c462289cca4758c3b9bf362f1130928a1c`. No database migrations, application API,
UI, tenancy, authorization or remote-installation behavior changed. No feature
ledger exists in this producer repository; relevant README/status documentation
was updated rather than modifying Atlas's ledger.

## D. Publication workflows

Preparation stays in catalogue.yml, with contents read, id-token write and
attestations write. Publication runs only by workflow_dispatch on main, first
attempt, with no caller-selected source, digest, signer or repository. Its only
input is publish/recover. An enforced catalogue-publication environment must
approve the run. Concurrency is `official-catalogue-publication`, cancellation off.

Publication's GITHUB_TOKEN has contents/Actions read plus attestation/OIDC writes.
An environment-gated, repository-only App installation token requests Contents
write, Actions read and Administration read; it cannot change settings. The
App bypass is constrained by rulesets, with an additional no-bypass current-branch
force-push/deletion lock. The private App key remains an owner-managed secret.

Same-byte re-runs resume verified assets without replacement. Ambiguous writes
stop for a fresh approved run. Existing immutable snapshots are never overwritten.
Recover selects only the authenticated immediate immutable successor, including
after main advances. Unfinished drafts after source changes require a separate
reviewed recovery decision. A stale worker cannot overwrite a newer pointer.

## E. Trust and signing

Catalogue signer: `.github/workflows/catalogue.yml@refs/heads/main`.
Package signer: `.github/workflows/release.yml@refs/tags/ID-vVERSION`.
New selection signer: `.github/workflows/catalogue-publish.yml@refs/heads/main`.

All bind GitHub Actions issuer, repository 1414494920, owner 93822871, exact
repository URI, signer/config/source ref and digest, hosted runner, original
artifact SHA-256, SLSA v1 and witnessed Sigstore v0.3 evidence. New selection
subject is `current.json`. gh 2.102.1 and roots are independently pinned.

The signed invocation connects selection to a public approval record with
externally configured environment/reviewer identities. First-attempt restriction
avoids unsupported review-to-rerun attribution. Current GitHub protection is
observed, not fabricated historical policy proof. App-triggered package actor
identity cannot prove which human initiated the App operation. Atlas must review
this authority model and add a separate selection profile; its existing profile
has not been widened.

## F. Release immutability

Draft assets are uploaded/read back/authenticated, then finalised with latest=false.
Publication rereads immutable=true, exact release/asset/tag/source identities and
bytes before touching current. The signed selection binds those release/asset IDs.
The separate automatically generated GitHub release-attestation predicate is not
claimed as cryptographically verified by this implementation.

Existing mutable releases are never changed, replaced or treated as locked.
Active package entries need actual immutable releases, exact authentic package
bytes, qualification and independent run approval. Proxmox 0.2.0 currently fails
these new eligibility gates. New package releases are still finalised by the
operator after generic preparation; no automatic executable-package publication
was added.

## G. Pointer protocol

Exact endpoint:
`https://api.github.com/repos/benchristian88/atlas-connectors/git/ref/heads/catalogue-current`.
Read both selection files at that resolved commit. Exact fields:
`schema_version`, `sequence`, `release_tag`, `release_id`, `asset_id`, `sha256`,
`previous_pointer_sha256`. Limit 1,024 bytes; strict canonical UTF-8 JSON; safe
literal integer IDs/sequence; exact lowercase hashes and derived numbered tag.

Authenticate current.json under the new selection profile. Require signed
predecessor plus transport parent binding, immutable snapshot identity, original
build provenance, approved run and ref reread. Persist consumer high-water state.
Equal-sequence substitutions, lower sequences, gaps and stale updates fail.
No credential is required for normal consumer reads. No current endpoint was
created by this task. Recovery retains the signed descriptor in the snapshot.

## H. Dynamic Connector support

The deterministic builder uses explicit reviewed recipes, canonical SDK manifests
and generic distribution identities. Tag selection is `ID-vVERSION` and requires
recorded qualification. Tests add `future-hypervisor` 12.3.4 without application or
publisher ID-specific changes, for both generic packaging and mocked active
package publication. Mock package evidence is explicitly not genuine acceptance.
Existing Proxmox production and candidate archive hashes remain exact.

## I. Tests and validation

Commands actually executed on the local Python 3.14.7 environment:

```bash
.venv/bin/python tools/prepare_publication_verifier.py --archive /private/tmp/atlas-b12-evidence/gh_2.102.1_macOS_arm64.zip
.venv/bin/python -m pytest --noconftest -q tests/test_catalogue.py tests/test_publication_contract.py tests/test_publication_state.py tests/test_publication_transport.py tests/test_publication_packaging.py tests/test_publication_crypto.py tests/test_documentation.py
ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-catalogue-followup-test-collections ATLAS_TEST_RUN_ANSIBLE=1 .venv/bin/python -m pytest -q
/private/tmp/atlas-p1-actionlint .github/workflows/ci.yml .github/workflows/release.yml .github/workflows/catalogue.yml .github/workflows/catalogue-publish.yml
.venv/bin/python -m compileall -q tools tests
.venv/bin/python tools/build_bundle.py
.venv/bin/python tools/build_bundle.py --candidate
.venv/bin/python tools/publish_catalogue.py stage
git diff --check
```

- Focused: **323 passed, 0 failed, 0 skipped**.
- Full suite including existing registry/SDK/qualification/Ansible regressions:
  **611 passed, 0 failed, 0 skipped**, 180 existing ansible-runner Python 3.14
  `codecs.open` deprecation warnings; 36.42 seconds.
- Genuine offline catalogue and exact original package verification passed;
  wrong bytes, source, subject and cross-profile evidence failed as expected.
- State/HTTP/approval outcomes are mocked; no genuine new pointer proof exists.
- Actionlint v1.7.7 passed all four workflows. YAML/security contract tests passed.
  Its initial sandboxed Go launcher could not resolve proxy.golang.org; a permitted
  read-only dependency download succeeded, then a cached offline binary was built
  and used. No workflow was triggered.
- Python compilation and both bundle builds passed. Production SHA-256 remains
  `a14fec5ab485c980688ff5907e8835ddd3e9cecd1a6989ef252cbcb1b1dc4ef8`;
  candidate remains `dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97`.
- The stage CLI was exercised only with checked-in disabled policy: it exited
  `publication_disabled` before creating an API client or performing any operation.
- Frozen sequence 1 remains 10,585 bytes and expected digest. Its publication.json
  and original registry files are unchanged. `git diff --check` is clean.
- Live publication, setting changes, new-pointer acceptance and real protected
  approval enforcement were deliberately not run. No frontend/database checks
  were applicable.

## J. Operator checklist

The [runbook](README.md) gives exact settings and read-only verification commands.
Enable future release immutability; configure four specified rulesets; bind
validate to GitHub Actions integration 15368; configure both environments with
required reviewers/self-review prevention/ref restrictions/no admin bypass;
provision the scoped App; keep Actions defaults read-only; approve/bootstrap
history and fill reviewed policy IDs; review the Atlas profile; then authorize
and capture a first live acceptance. Public-plan feature availability was checked,
but billing plan and actual enforcement were not assumed.

No setting changes were performed. A separate implementation/approval of the
one-time sequence-1 bootstrap migration is required; ordinary publisher commands
intentionally cannot create initial trusted history.

## K. Compatibility

Catalogue v1 still has six fields, unchanged SDK 1.1.0 validation and size limits;
no expiry. Sequence-1 JSON/registry identities and historical archive bytes remain
unchanged. Existing package/catalogue certificate profiles remain distinct and
compatible with genuine B1.2 fixtures. The new pointer is additive producer
infrastructure, not an enabled Atlas B1.3 source or remote installer.

## L. Security limitations

Production is disabled. Approval relies on GitHub's API/configuration, not an
independent human signature. API/approval retention failures block progress.
Protected-branch state observed now does not independently prove every historical
policy state. Repo administrator/source compromise and deliberate withholding
remain residual trust risks. Whole-database rollback/loss cannot establish absolute
freshness from an old valid signed chain alone. Reviewer/root/policy rotation needs
a separately reviewed compatibility transition. The v1 200-entry history bound is
preserved; no indefinite entry retention beyond that contract is claimed.

Both legacy releases remain mutable. Migrating exact catalogue bytes does not
repair package eligibility, and changing an old package's tag/asset ID would
violate its identity. Bootstrap migration and old-package decisions remain explicit
blockers. No unsupported deployment/App permission assumptions are treated as live
acceptance, and no unauthenticated pointer fallback exists.

## M. PR readiness

Local changes form a reviewable P1 foundation, with activation disabled and a
proposed ADR. Suggested human review order: contract/authority decision and
investigation; verifier/transport/state machine; tests/workflows; generic packaging;
operator/consumer handoff. One scoped PR can preserve their mutual dependencies;
owner settings/bootstrap and Atlas implementation should be separate work.

No branch was created/switched; no fetch/pull, commit/push, tag/merge/rebase/reset,
PR, release publication, workflow trigger or repository-setting mutation occurred.
All Git operations in this task were read-only inspection.

## N. Atlas consumer handoff

[consumer-handoff.md](consumer-handoff.md) specifies the exact pointer parser,
endpoint, separate certificate profile, approval API boundary, immutable snapshot
verification, parent/ref checks, history/persistence changes, bounded missed-sequence
catch-up and required genuine B1.3 tests. Keep existing publication failure gates
until that independently reviewed implementation and live acceptance pass.

## Final repository status

Read-only `git status --short`:

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
