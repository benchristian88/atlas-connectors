# Historical experimental workflows

These four workflows are retired historical test data. They were moved unchanged
from `.github/workflows/` at source branch commit
`632f5e5f9f297549b1d54c5b6fc1a5c8a086b38d`. They are no longer GitHub Actions
entry points. Do not restore them to the active workflow directory or invoke them
from a production workflow.

| Archived file | Original and relocated Git blob hash |
| --- | --- |
| diagnose-catalogue-publisher.yml | d847e02e236733e1869303c5b6539651dc581c3c |
| ruleset-visibility-experiment.yml | d1f32215f5f4dc0522652df807d70b255d2dcd25 |
| verifier-signer-experiment.yml | 9828853f7cc4ee1825df835edfe01fa521c52434 |
| verifier-signer-probe.yml | 9d23b3d2ec267c50b4b82340d11a08138d72b04f |

The original bytes, workflow identities, SHA pins and security assertions remain
intact. Tests read these fixtures while continuing to check historical signing
identities under `.github/workflows/`; fixture paths are never signer identities.
[Retirement regressions](../../test_historical_workflows.py) pin every fixture's
SHA-256 and enforce the five-workflow production inventory and separation.
The existing diagnostic, ruleset and signer tests continue to exercise the
archived inline programs and workflow security contracts offline.
