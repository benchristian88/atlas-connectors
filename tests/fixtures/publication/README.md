# Genuine public provenance fixtures

These two bundles are exact copies of public evidence independently captured for
Atlas B1.2 on 21 October 2026. No application code or executable Connector is copied.

| File | SHA-256 | Provenance subject |
| --- | --- | --- |
| catalogue.sigstore.json | 0a404de77a6c47dc2f08e3acecf835a01313e924f6883a4b13d720c57610f72f | Frozen catalogue.json and catalogue-000001.json |
| package.sigstore.json | 2929b38721e31d48ca9ee8a51753c595880dca3c5fef9dea79c8bfdf0dca7db4 | Original proxmox-0.2.0.tar.gz |

The original catalogue bytes remain in
[the unchanged fixture](../official_catalogue/catalogue-000001.json).
The catalogue attestation is 57152061, from catalogue.yml at refs/heads/main,
source `91dfd86f18d0b59ff977bb1e8a5fef42c5329943`. The package bundle is release.yml
at refs/tags/proxmox-v0.2.0, source `456a5bfdd1398c19da9ffef29216029027e24278`.

The real pinned verifier tests authenticate frozen catalogue bytes and the
exact reproducible original package archive, and reject
wrong bytes/profile/source/name and cross-profile package evidence. They do not
claim immutable release history, human approval or package installation eligibility.
No genuine pointer fixture exists: no pointer has been published or signed here.
State-machine tests use visibly marked TEST_ONLY_NO_SIGNATURE objects solely to
model transitions; those objects can never pass the production verifier.
