# Atlas official Connectors

Apache-2.0 by default for Atlas-authored code. Connector source lives here;
Atlas application/domain/runtime source remains in the AGPL Atlas project.
Third-party dependencies retain their licences and are inventoried by their
own distribution. No AGPL application/plugin implementation was copied here.

Each `connectors/<id>/` package owns its independent SemVer Manifest, fixed
entry-point playbooks, `library/`, README, NOTICE and SPDX SBOM. Repository-level
LICENSE is included in every bundle. Fixtures/unit tests live in `tests/`.
Production [Proxmox 0.1.0](connectors/proxmox/README.md) is Test Connection-only.
The separate [I4B candidate](connectors/proxmox/docs/discovery.md),
0.2.0-i4b.1, implements fixture-proven discovery. The first operator-reported
9.2.11 runs of .1 and .2 were PARTIAL (140 and 179 observations). The next
qualification candidate is **0.2.0-i4b.3**, adding structured discovery diagnostics.
All remain unqualified and unpublished. Docker/UniFi implementations remain absent.

[I4C-A preparation](connectors/proxmox/docs/i4c-a-preparation.md) preserves the exact
original candidate bytes. The [active live runbook](connectors/proxmox/docs/i4c-live-qualification.md)
records both PARTIAL results and the next candidate checkpoint.
[Discovery diagnostics](connectors/proxmox/docs/i4c-discovery-diagnostics.md) describes
always-on safe reasons and administrator-only next-run debug, with 48-hour retention,
no raw source logging and unchanged source/COMPLETE semantics.
Qualification documents/checkpoints and incidental files are excluded by the
reviewed bundle file list. Neither local preparation nor fixture tests qualify a source.

Python 3.12+ development:

```bash
python -m pip install --no-index --no-deps --require-hashes --find-links vendor/sdk -r vendor/sdk/requirements.txt
python -m pip install -r requirements-dev.txt
python tools/test_collection.py --archive ../atlas/vendor/collections/community-proxmox-2.0.0.tar.gz --output /tmp/atlas-connector-test-collections
export ATLAS_TEST_COLLECTIONS_PATH=/tmp/atlas-connector-test-collections
export ATLAS_TEST_RUN_ANSIBLE=1
python -m pytest -q
python tools/build_bundle.py
python tools/build_bundle.py --candidate
```

The same SDK **1.1.0 wheel/hash** is staged in Atlas and here. Canonical schemas
remain exclusively in atlas-connector-sdk; the wheel is a pinned distribution
artifact. Update that artifact in both consumers together after reproducibility
and package-data checks, never via mutable source URLs or copied schemas.

The USTAR/gzip builder sorts paths and fixes modes, owners and timestamps.
`dist/proxmox/` contains the exact bundle, SHA256SUMS, detached combined Manifest
and an index. The archive contains the domain Manifest without its own digest.
Build twice and compare bytes. A local dirty-tree candidate has no authenticated
remote provenance; its recorded source HEAD is contextual, not a claim that the
uncommitted implementation exists at that commit.

The test collection archive above is the exact I4A artefact from a sibling Atlas
checkout. CI downloads the same archive and verifies its reviewed SHA-256 before
test installation. This tooling never installs dependencies into a production
Connector bundle. Candidate metadata and executable helpers are excluded from the
normal 0.1.0 build. Candidate output goes to `dist/proxmox-candidate/`.
`tools/build_acceptance_fixture.py --output <test-directory>` creates a separate
deterministic `i4b-fixture` harness for Atlas tests. Its source adapter and embedded
sanitized fixtures exist only in that test bundle; its `fixture-only` qualification
does not qualify Proxmox or allow candidate activation.

CI validates contracts, fixtures and build. The protected `proxmox-v<SemVer>`
release workflow verifies tag/Manifest identity, builds and attests the exact
bundle with the pinned GitHub `actions/attest` action, then retains a release
candidate artifact. The operator publishes those unchanged files as immutable
GitHub Release assets only after qualification. No release has been published
by this work. Repository identity is **benchristian88/atlas-connectors** and
signer workflow is **.github/workflows/release.yml**; Atlas must bind both, the
exact digest/source commit and authenticated Sigstore issuer/predicate evidence.

Remote acceptance remains blocked on an actual reviewed pushed workflow,
immutable release, attestation/trust-root verification and operator
qualification. Atlas's remote verifier remains fail-closed. Local acceptance
uses the existing Atlas bootstrap trust path with an exact packaged allowlist;
it is not a substitute claim of remote attestation verification.
