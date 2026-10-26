# 0006 — Separate Connector package publication admission

Status: **Proposed for owner security review; locally implemented, execution disabled**

Date: 2026-10-26

## Decision boundary

Extend the producer's existing single-maintainer and isolated run-preflight design
to package publication using three separate manual operations: tag, stage and
finalize. Reuse ADRs [0002](0002-single-maintainer-publication.md),
[0004](0004-isolated-signed-publication-verifier.md) and
[0005](0005-lean-run-preflight.md), existing Apps, environments, complete ruleset
validation, pinned offline verifier and package build/provenance contract.
Do not change the frozen S4 catalogue publisher or consumer bootstrap authority.

The new authority boundary is `atlas-connector-package-preflight/v1`, signed by
`connector-verifier.yml` at separately reviewed implementation S. Its caller is
`connector-publish.yml` from reviewed main C. Package request data includes exact
source/tag/digest, original build/artifact identity and, for finalization, explicit
approval of all five staged asset identities. Existing catalogue preflight,
package-build signatures and unsigned stage receipts cannot authorize these
operations. No new cryptography, App, secret, permission grant or trust service is
proposed. This ADR does not approve its own production activation.

## Pinning and credential boundary

PR1 merged as reviewed implementation S
`d6601ad97815a85da164e4329766ea17b62bddc9` (PR #37). PR2 replaces its deliberately
all-zero pins with S in the reusable call, executable checkout, implementation
literal and package trust file. It does not modify S's workflow/helpers or accept
the signer. The owner independently configures the complete matching package trust
as a repository Actions variable; environment overrides must be absent or match
exactly, as the [runbook](../../catalogue/publication/connector-packages.md) explains.
Both trust flags stay false and the repository publication gate stays absent/false.
Acceptance-only may sign under unaccepted package trust, but the Publisher job is
skipped at the job boundary. After inspecting genuine original signed evidence
and platform isolation, a further reviewed activation can enable package trust.
Never use current main or S4 as a substitute for S. Pinning is not activation.

Verifier App 5424851 retains Administration Write and Contents/Actions/Checks/
Metadata Read, with its key confined to the existing isolated environment. Its
restricted transport performs GET evidence reads and its existing single token
mint POST. Publisher App 5422372 retains Contents Write and Actions/Administration/
Metadata Read, without Workflows access. Its JWT/installation/token permissions
and one-repository token scope are checked after cryptographic admission, before
repository writes. Neither token nor private key is exported.

The Verifier cannot independently inspect another App's effective installation
grant using its own credential. Before any Publisher credential is supplied, it
authenticates official repository/owner, original/triggering human, original attempt,
caller C and signer S, caller source/CI, exact request/policy/trust, App registration,
environments and complete privileged ruleset/bypass observations. Package source
and original artifact authentication are additional Publisher preparation gates;
acceptance-only does not run them.

The proposed owner decision is to accept a split least-privilege boundary:
`publish_connector.main` reauthenticates admission and committed package bytes
before calling `mint_publisher`. That function JWT-authenticates the expected App
and installation, demands exact registered/installed baseline permissions, selected
repository installation and unsuspended state, requests only the approved repository
and permissions, checks exact issued token permissions, and verifies the token's
single official repository/owner before returning a write-capable client. Missing,
additional or contradictory authority rejects; the authentication transport cannot
write repository data. Mutation methods reauthenticate admission and visible controls.

**Publisher installation permissions are independently validated by the admitted
Publisher before writes; they are not included as independently observed effective
permissions in the Verifier's signed pre-token admission.** This proposed split
avoids expanding the Administration-Write Verifier's access or exposing Publisher
credentials before admission. It relies on reviewed S, trusted hosted execution,
GitHub's authenticated responses and the admitted Publisher's enforcement; it is
not a second independent credential witness in the signed evidence. A stolen valid
key, trusted code/action/runner compromise, administrator/sole-maintainer compromise
and protection changes between observations remain risks. The token-mint POST occurs
after App/installation checks and before token-permission/scope checks; no repository
mutation is reachable until all checks pass.

This ADR remains **Proposed**, pending the owner's final security decision. PR2
records the proposal and local checks, not acceptance or activation. A requirement
for independently observed effective permissions inside pre-token admission would
need a separately reviewed architecture/baseline. Do not pass Publisher credentials
to the Verifier, enlarge its permissions or move keys. Any defect requiring changes
to S's executable code blocks this pinning increment pending a new reviewed S and
re-pinning cycle.

## Publication and recovery

Tagging is create-only. Staging authenticates the exact original Actions ZIP and
package signature, then retains all five files without rebuilding their published
bytes. Only an explicitly approved partial draft identity can resume. A fresh
finalize dispatch approves C/T/D/R/L/A and the canonical complete inventory digest;
it cannot derive approval from the current provider. One PATCH may publish that
draft with `make_latest: "false"`. A separate anonymous GET-only verifier must
establish actual immutability and all approved identities before success.

The source must have successful required CI and a merged main PR identifying its
exact merge SHA. The workflow directory must equal current default main as a
conservative sufficient condition for baseline App permissions. Reject a mismatch;
do not request Workflows Write. This deliberately rejects some potentially valid
historical source choices rather than infer undocumented permission sufficiency.

There is no atomic provider transaction. Reauthenticate admission and reread
authority/protections/state at mutation boundaries. Omitted current bypass fields
remain unavailable; the signed full privileged snapshot supplies publication-time
evidence under ADR 0005, not proof of continuously unchanged protections. Ambiguous
writes cause fresh observation, never blind retry. An exact immutable publication
can be reverified without PATCH. Irreparable identities require a separately
reviewed version, never deletion, retagging or asset replacement.

## Consequences

Local tests establish modeled behavior, genuine historical signature regressions
and isolation guards. They do not establish live package signer representation,
key custody, installed permissions, continuous policy or actual immutable package
publication. Signed evidence currently has one-day Actions retention; receipts
have 90-day retention. Neither is a permanent public immutable evidence archive.
Future catalogue sequence two and consumer eligibility need their separate
approved archival/authorization work. Existing package and catalogue bytes,
Manifest/schema, Atlas, SDK, API/UI and qualified discovery remain unchanged.

See the [operator procedure](../../catalogue/publication/connector-packages.md)
and [PR2 local qualification report](../phase-4b2-pr2-local-qualification.md).
