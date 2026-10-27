# Original S2 Sigstore evidence

Public evidence from run `40534608937`, attempt 1, job `122296352579`, attestation
`60446602`, preserved on 28 October 2026. See the
[qualification report](../../../docs/phase-4b2-sigstore-qualification.md) for
authentication, provenance, limitations, commands and human handoff.

| File | Evidence |
| --- | --- |
| `job-log.json` | Original GitHub job log encoded losslessly as a JSON string, including signing PEM and failed seal; provider-masked credentials remain masked |
| `certificate.pem` | Exact PEM extracted from that successful signing step |
| `bundle.sigstore.json` | Original signed bundle extracted from GitHub's public attestation API response; outer JSON serialization only is normalized |
| `attestations.json` | API response with only the temporary storage URL query removed; bundle content unchanged |
| `run.json` | Selected original run metadata, caller SHA and referenced immutable signer |
| `jobs.json` | Original run's job/step summaries, including skipped Publisher and evidence upload |
| `artifacts.json` | Empty original run artifact list |

The bundle certificate matches the logged certificate in DER. Official Sigstore
4.3.0 independently authenticated the DSSE envelope against the repository's
frozen public-good root and exact S2 identity. This authenticates the certificate
and signed statement, not the unavailable preflight contents. The pinned hosted
gh output and original subject bytes were not exported; no reconstructed subject
or mocked CLI output is claimed to be genuine. Test models use the decoded PEM
with explicitly synthetic subject/output and do not grant admission authority.

Historical S, catalogue and package signature fixtures are preserved separately
and unchanged. These new fixtures do not establish successful hosted acceptance.

To repeat archival authentication, run this from the repository root using an
isolated interpreter with official `sigstore==4.3.0` installed. It uses the frozen
root offline. The returned payload contains a subject digest; this procedure
does not verify the unavailable subject file and does not replace pinned gh.

```python
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from sigstore.models import Bundle, TrustedRoot
from sigstore.verify import Verifier, policy

roots = Path("tools/publication_trust/trusted-root.jsonl").read_bytes()
assert hashlib.sha256(roots).hexdigest() == "3c2cc7f357dc064ec527fdcd78da6e9245c21a381e1abaa0f2b62b186bcac1a1"
raw = Path("tests/fixtures/connector_sigstore_s2/bundle.sigstore.json").read_bytes()
assert hashlib.sha256(raw).hexdigest() == "f85c122df49f2c49c0117830dc81c00a52670e982368407ba9b406c74c96eb80"
identity = "https://github.com/benchristian88/atlas-connectors/.github/workflows/connector-verifier.yml@c2b4ecb493160f0226b1724aa688d0f436d51489"
with TemporaryDirectory() as work:
    root = Path(work) / "public-good-root.json"
    root.write_bytes(roots.splitlines()[0])
    verifier = Verifier(trusted_root=TrustedRoot.from_file(str(root)))
    kind, payload = verifier.verify_dsse(Bundle.from_json(raw), policy.Identity(
        identity=identity, issuer="https://token.actions.githubusercontent.com"))
    assert kind == "application/vnd.in-toto+json"
    print(payload.decode())
```
