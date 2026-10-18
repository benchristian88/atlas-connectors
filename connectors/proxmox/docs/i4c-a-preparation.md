# I4C-A — exact candidate preparation record

Prepared **13 October 2026**, for operator review/commit/push and later interactive
Docker/LXC qualification. **No live Proxmox qualification, commit, push, merge,
publication or production activation occurred.** I4 remains incomplete.

Starting/current branch: `feature/i4c-proxmox-qualification`.
Starting/current HEAD: `4f001b28df7a1618c7a87a5f8c911bafd4418fd8` (merged I4B, also
local main). Starting tree was clean. Atlas's branch is
`feature/integrations-i4c-proxmox-qualification`, unchanged HEAD
`7cc20b76662edbf94e929a5f17dda8f6cc56b494`; SDK main remains clean/read-only at
`8b0518c462289cca4758c3b9bf362f1130928a1c`.

## Immutable candidate

Version **0.2.0-i4b.1**, exact unchanged I4B manifest/SBOM/source, **unqualified**.
Archive SHA-256:

```text
d283441dfa70d8e589fd3da868075bdb795a8cda938a78931437432b572166c8
```

Two canonical builds and detached manifests compare equal. The archive also
equals the pre-change I4B candidate. The explicit reviewed 18-file package list
excludes this report/runbook, fixtures, test transport/tools, credentials, generated
caches and unrelated files. Independent inspection compares all source bytes,
manifest/SBOM, file identities and canonical metadata. Normal builds remain
**0.1.0 probe-only** and exclude all candidate executable/metadata additions.

SDK **1.1.0**, AIP **1.0**, runtime baseline **>=1.2.0,<2.0.0**, community.proxmox
**2.0.0**, reviewed archive SHA-256
`77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6`.
Actual baseline remains `atlas-ansible-i4a-v1` / **1.2.0**, runtime **0.3.1**,
ansible-core **2.19.7**, Runner **2.4.3**, proxmoxer **2.3.0**.

The Mac build's detached `source_commit` is the current merged HEAD, contextual
until the operator commits. After commit/push, rebuild from the exact clean LXC
checkout and use `tools/verify_candidate.py --source-commit <new-full-SHA>`.
The archive digest remains independent of Git provenance and preparation docs;
do not describe local metadata/release URLs as a remote publisher attestation.

## Staging and live handoff

Normal Atlas activation still rejects this unqualified candidate. The I4B harness
changes identity/qualification and is test-only. Atlas now supplies an explicit
generic local operator command, `python -m scripts.qualify_connector`, using a
separate opt-in test store and exact immutable 48-hour authorization for the
package/manifest/commits/store. The existing package validator, independent runtime
recheck, compatibility, global lifecycle, mappings/configuration/run locks and
scoped I3 orchestration stay authoritative. No source credential is passed to that
command; saved encrypted Atlas credentials can be retained.

The committed Atlas Docker override is used only by the operator on the isolated
test LXC; ordinary production installers/catalogues never select it. Evidence is
`operator-qualification`, never a source-qualified or officially attested release.
See Atlas `docs/deployment/connector-qualification.md` and ADR 0010 in the exact
Atlas task branch. [The interactive runbook](i4c-live-qualification.md) provides
explicit Mac commit/push commands, exact-LXC source retrieval/build/digest checks,
staging/preview/activation and planned live readiness/discovery/coverage/negative
checks. **Pause after Mac push for the interactive LXC checkpoint.**

## Files and validation

- `tools/build_bundle.py`: reviewed file list preserving candidate/default bytes.
- `tools/verify_candidate.py`: independent exact checkpoint inspector.
- `tests/test_i4c_checkpoint.py`: packaging exclusion and verifier regressions.
- `README.md`: link preparation/live workflow.
- `connectors/proxmox/docs/i4c-live-qualification.md`: planned interactive checks and Git/LXC handoff.
- `connectors/proxmox/docs/i4c-a-preparation.md`: this evidence/state record, excluded from packages.

Executed full suite with `ATLAS_TEST_RUN_ANSIBLE=1`, exact reviewed collection,
the existing pinned native-style runtime Python and separate pytest tooling:
**100 passed**, including four actual Runner cases, transport/normalization,
capability/completeness, candidate manifest, reproducible/default packaging and
documentation. Two explicit candidate builds, independent verification and
pre-change byte comparison passed. Actionlint of existing CI/release workflows
passed; workflows unchanged. Final full suite was rerun after documentation edits:
**100 passed**, no skips. `python -m compileall -q tools connectors tests` and
`git diff --check` passed. Candidate manifest/SBOM/source diff is empty. Existing
dependency deprecation warnings remain.

Atlas preparation/validation details are in its
`docs/architecture/integrations/i4c-a-preparation.md`. No migrations, SDK/AIP or
candidate transport/COMPLETE changes. After the operator started Docker Desktop,
the same full suite ran in the pinned Python **3.12** runtime image with network
disabled, read-only sources/test tools and the reviewed `/app/collections`:
**100 passed**, no skips, including actual Runner. Git-less image tests use explicit
test-only exported-source HEAD context; committed-source builds still happen in Git.
No live LXC/source or native systemd acceptance is claimed.

Production catalogue/bootstrap still use **0.1.0**, with discovery, scheduling
and complete snapshots disabled. **Candidate 0.2.0-i4b.1 and Proxmox 9.2.11 remain
UNQUALIFIED.** No release/promotion to 0.2.0 occurred. Node rename, retained-endpoint
source replacement, VMID reuse, absent classes and unsafe-to-produce live negative
scenarios retain the documented I4B limitations. Optional mutations require
explicit operator choice; no destructive infrastructure changes are required.

Atlas final automated evidence: **543 passed** release-critical, **97 passed**
I3/configuration/lifecycle regression, **95 passed** contracts/docs. Migration
head remains **20261012_0029**, release dry-run/independent verifier and parsed
qualification Compose configuration passed. No frontend change or migration.
All six packaged Docker images also built successfully. Actual packaged API
installer **UID/GID 10001:10001** staged the exact candidate into disposable
qualification volumes; the real pinned runtime independently verified its identity
and healthy baseline, denied store mutation and rejected disabled/revoked grants.
The original probe-only 0.1.0 stayed independently verified. Disposable volumes
were removed; no database activation, source call or live credential was used.
The operator procedure explicitly selects that installer UID/GID, preserving the
authority guard when the API image account's primary group differs.
Revocation retains history and blocks new execution; a prior probe-only version
may reject candidate scopes. No automatic scope conversion or previous-version
restore is supplied. Retain the disabled test state for a separately reviewed
compatible restore, preserving normal configuration guards and knowledge.

## Final repository state (`git status --short`)

```text
 M README.md
 M tools/build_bundle.py
?? connectors/proxmox/docs/i4c-a-preparation.md
?? connectors/proxmox/docs/i4c-live-qualification.md
?? tests/test_i4c_checkpoint.py
?? tools/verify_candidate.py
```

Atlas's full file inventory/status is in its preparation report. SDK status is
empty/clean. All branches/HEADs remain as recorded above. Stop for operator review
and the exact commit/push commands in the runbook; no preparation action qualifies
a source or authorizes I4C-B.
