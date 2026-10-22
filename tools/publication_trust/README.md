# Public verifier distribution data

These are public upstream trust/distribution artifacts, matching the reviewed
Atlas B1.2 acceptance on 21 October 2026. No Atlas application source is included.

- `distribution.json`: gh 2.102.1 upstream archive and extracted-binary SHA-256
  locks for Linux/macOS amd64/arm64; frozen root digest and identifier.
- `trusted-root.jsonl`: Sigstore Public Good trust data, SHA-256
  `3c2cc7f357dc064ec527fdcd78da6e9245c21a381e1abaa0f2b62b186bcac1a1`.
- `LICENSE.gh`: upstream GitHub CLI licence.
- `bin/gh`: ignored, prepared locally/CI only after archive and binary hash checks.

Upstream: [GitHub CLI release](https://github.com/cli/cli/releases/tag/v2.102.1).
The independent original B1.2 verification record is available in adjacent Atlas
`docs/deployment/attestation-verification.md`; that repository is not a runtime,
packaging or CI dependency of this producer.

Install with `python tools/prepare_publication_verifier.py`, or supply a local
pinned archive with `--archive PATH`. Tests never download roots during verification.
Updates require reviewed data/hash changes and genuine offline verification;
never obtain a replacement trust root from a pointer or catalogue.
