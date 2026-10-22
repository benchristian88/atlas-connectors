# 0001 — Separate immutable catalogue snapshots and authenticated selection

Status: **Proposed for owner review; implemented behind disabled policy**

Date: 2026-10-22

Authorization amendment: [ADR 0002](0002-single-maintainer-publication.md) replaces
this original proposal's separate-reviewer requirements with explicit
single-maintainer authorization. The original reasoning below is retained as
proposal history; use ADR 0002 and the current runbook for operating policy.

## Context

The [verified investigation](../../catalogue/publication/investigation.md) found
mutable legacy releases, unprotected main and an environment without reviewers.
Atlas ADR 0011 already separates build provenance from release authority. This
producer decision refines that boundary; it does not supersede an Atlas ADR or
claim that Atlas has accepted a new trust profile.

## Decision

Use one GitHub immutable Release `catalogue-NNNNNN` per contiguous sequence.
Retain original catalogue bytes, original build bundle, a distinct signed
`current.json` selection and its Sigstore bundle as release assets. Then atomically
advance the two selection files on `refs/heads/catalogue-current` through a
single-parent, non-force Git ref update. The signed predecessor digest binds
selection order; the transport commit must also have the corresponding parent.

Keep catalogue build identity in catalogue.yml and package build identity in
release.yml. Add catalogue-publish.yml as a distinct selection signer. Its SLSA
statement authenticates exact pointer bytes and workflow/source/invocation
identity. It does **not** contain a human's signature. Independently verify the
public GitHub review-history API, externally configured numeric reviewer and
environment IDs, protected main and enforced settings. First-attempt publication
only avoids the provider's missing per-attempt review binding. Recovery requires
a fresh approval, not replay of a workflow attempt.

Use a repository-scoped, short-lived GitHub App installation token for releases
and the current branch. No PAT. Contents write is necessary; Actions read reads
approval evidence; Administration read audits immutable-release settings and
rulesets. The App has no administration write. Its bypass is limited by rulesets
to publication tags/current updates. A second current-branch ruleset has **no**
bypass and blocks force-push/deletion, including for the App.

The fixed bootstrap pointer digest, environment IDs and reviewer identities are
owner-reviewed source policy, never data chosen by a downloaded pointer.
Activation defaults off. This task does not configure GitHub, create bootstrap
history or change Atlas. The production authority chain remains blocked until
owner configuration, migration approval, consumer review and genuine acceptance.

## Alternatives

- Mutable catalogue-v1 assets cannot give immutable history.
- Freezing catalogue-v1 also freezes its alias; it cannot advance.
- `/releases/latest` mixes independent package/catalogue release streams and has
  no compare-and-swap. Its latest marker is mutable even for immutable releases.
- A protected branch, signed Git commit or environment name alone is not an
  artifact attestation and does not authenticate a selection's human authority.
- Separate immutable selection releases need another discovery selector and add
  releases without eliminating the currentness/approval boundary.
- External storage, services and signing infrastructure violate GitHub-only scope.

## Consequences and limits

Consumers verify a new, narrowly scoped profile and public API authority evidence.
Unavailable/deleted approval records fail closed; neither a checksum nor an API
response substitutes for signature verification. GitHub administrator compromise,
policy removal and whole-history withholding remain trust limitations. After all
local state is lost, an old valid chain cannot cryptographically prove it is the
latest; live GitHub ref observation and an approved bootstrap are still required.

A bootstrap migration needs a separately approved implementation. Existing
Proxmox 0.2.0 cannot satisfy the new package gate: its release is mutable and its
original environment had no review protection. Do not rewrite its Manifest,
package digest, tag or asset ID to disguise a migration. New qualified package
versions or an explicit later legacy decision are needed.

The six-field catalogue, SDK, package runtime and Atlas remote-installation
boundary are unchanged. Generic recipes preserve existing archive bytes while
allowing future compatible Connector IDs without application source changes.
