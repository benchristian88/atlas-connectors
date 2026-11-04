# Durable evidence preservation fixture

`preserved.json` records SHA-256 values from clean baseline
`e58788a667c0c0006477ac149e8ad28aedda0745`. It protects the existing frozen
publication tools, workflow pins/gates, public policy/trust files, registry,
sequence, original catalogue/signature fixtures and historical release metadata
while the successor candidate is developed separately. It contains public file
digests, no production credentials and no genuine publication preflight.

The regression reads this fixture directly, so shallow CI checkouts and exported
source tests do not need historical Git objects. Updating a preserved control
requires deliberate review; changing the fixture cannot grant trust or publication
authority. The whole-tree before/after audit for this increment is recorded in
the [engineering report](../../../docs/catalogue2-phase1-engineering-report.md).

`s4-verifier-trust.json` preserves the exact historical S4 trust bytes as test
input. The byte-pinned historical Publisher/build workflows live under
`tools/templates`, outside active Actions paths. Historical security/bootstrap
assertions continue using those inputs while generated successor profiles are
tested separately. This creates no new accepted pin or production approval.
