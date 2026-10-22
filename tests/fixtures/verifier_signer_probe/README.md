# Genuine reusable-workflow probe evidence

Exact public subject and bundle from successful experiment
[run 39846232008, attempt 1](https://github.com/benchristian88/atlas-connectors/actions/runs/39846232008),
source `e5287c3229f5b9a1dc4c3dbcda0f4193fe221c3c` on `refs/heads/main`.
Captured for the signer-identity correction on 23 October 2026. These are new
fixtures; the historical catalogue/package/bootstrap fixtures are unchanged.

| File | Bytes | SHA-256 |
| --- | --- | --- |
| probe.json | 650 | 75052edaed33fda77502ed2ecac49515f9e22f96f7a009ef6cb4ad3f9041e08a |
| probe.sigstore.json | 10439 | 02fa47cde8e739dad47dfe8e902b2759f9eb2f1488cd60bebd8865ef5730d199 |

The downloaded probe artifact ZIP (ID `12455755905`) matched provider digest
`531aec6ea4a397a3039914d5813d9da196f7f606bffcd7ad61759a0d4a192e7a`.
The evidence ZIP (ID `12456020174`) matched
`5d7f9742cfbc46b6956bbfedffd703542bb2d9da87401c033a8aaec6c22a2e14`.
ZIP integrity is not signature verification: the unchanged pinned CLI and roots
independently authenticated this bundle offline and rejected changed/substituted
subject bytes. Tests repeat those real cryptographic checks without a network.

The authenticated certificate SAN and buildSignerURI identify
`.github/workflows/verifier-signer-probe.yml@refs/heads/main`; its buildSignerDigest
is the exact source SHA. buildConfigURI identifies the experimental caller at
`refs/heads/main`, and buildConfigDigest is its source SHA. The signed subject
reports the reusable job's branch-ref workflow_ref and exact workflow_sha.
The independently retrieved caller run API reports `referenced_workflows.path`
with `@e5287c3229f5b9a1dc4c3dbcda0f4193fe221c3c`, `sha` equal to that SHA, and
`ref: refs/heads/main`. Job diagnostics and API metadata are distinct from
certificate extensions; API metadata is not embedded in this signed subject.

The predicate is the experiment-only
`https://atlas-impact.dev/attestations/verifier-signer-experiment/v1`.
The sole subject is `probe.json`, never `authorization.json`. This bundle is
**not production authorization evidence**, does not accept the production signer,
and cannot enable publication. Production tests must continue to reject it even
when supplied with matching test-only source/signer SHA pins. No production trust
configuration is changed. This correction downloaded the existing run's artifacts;
it did not dispatch or rerun a workflow.
