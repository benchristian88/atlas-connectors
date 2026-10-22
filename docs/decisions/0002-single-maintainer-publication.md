# 0002 — Explicit single-maintainer publication authorization

Status: **Proposed for owner review; implemented behind disabled policy**

Date: 2026-10-22

Amends the authorization portion of the still-proposed
[ADR 0001](0001-github-catalogue-publication.md). Its immutable storage, signing,
selection, bootstrap and recovery decisions remain intact. Neither decision
changes Atlas's accepted trust policy automatically.

## Context

There is one human maintainer. ADR 0001's independent environment review and
last-push/PR approval requirements cannot be operated by one person. GitHub's
[prevent-self-review setting](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments#required-reviewers)
explicitly excludes the initiating user. Disabling that setting and calling the
result independent approval would misrepresent the trust model.

## Decision

Use the explicit mode `single-maintainer-v1`. A fresh manual workflow_dispatch of
catalogue-publish.yml from protected main is the authorization action. Its original
and triggering actors must both equal an independently configured numeric human
maintainer ID. Independently compare run, attempt-1, workflow, public user,
repository, source ref/SHA and successful required CI observations. The verified
selection attestation binds the exact pointer bytes and source/run invocation to
those observations. Missing, ambiguous, unsupported or rerun evidence fails closed.
This is **single-maintainer authorization**, not independent human approval.

Both environments keep ref restrictions and disable admin bypass, with no required
reviewers. Protected main retains required PRs, strict required validate CI from
GitHub Actions, no bypass, and force-push/deletion prevention. The necessary
compatibility change is zero required approvals and last-push approval false;
independent source review cannot be claimed. Runtime mode checks reject the old
reviewer configuration instead of silently switching assurance.

The dedicated App retains only Contents write, Actions read, Administration read
and Metadata read. Pin its App/installation/bot IDs and slug. The pinned token
action binds its key and token to GitHub's authenticated installation observation;
check its outputs, public App metadata/permissions and token repository scope.
Current/tag bypass stays App-only; a separate no-bypass current rule prevents
history rewrites. A correct stolen key cannot be identified as stolen by these
checks, but cannot supply the allowed human dispatch or forge workflow signatures.

Package signing stays on the exact release.yml tag profile. First-attempt package
run actors must match the configured App bot, with exact source/tag and protected
main ancestry plus source CI. Its tag build proves provenance, not human consent.
The maintainer's later catalogue dispatch authorizes inclusion of immutable,
qualified package bytes. Generic packaging and B1.2 verification are unchanged.

Policy remains disabled; real identities and approved bootstrap pins are mandatory
before startup. No settings, live publication, tags or bootstrap migration are
performed here. The [runbook](../../catalogue/publication/README.md) defines settings
and the [handoff](../../catalogue/publication/consumer-handoff.md) defines independent
consumer verification, including which evidence is public versus producer-only.

## Consequences and future dual control

One person can operate this policy after its configuration/bootstrap/consumer
prerequisites are satisfied. That person's compromised account has no second human
veto. Required CI, cryptographic provenance, immutable snapshots, exact selection,
predecessor chain, high-water/rollback rules and fail-closed evidence checks remain.
GitHub/API availability and actor-history retention are trust dependencies; current
settings do not cryptographically establish continuously enforced past settings.

A later independent-reviewer mode requires a new ADR and explicit policy identifier,
implemented distinct reviewer/initiator evidence, matching repository settings,
producer/consumer policy review, historical acceptance boundaries and genuine live
acceptance. Unknown modes are rejected. No environment toggle, new reviewer list
or fallback may silently upgrade or downgrade assurance. The seven-field pointer
need not change unless that future design establishes a concrete incompatibility.

## Validation boundary

Deterministic tests cover permitted/denied dispatch and App identities, incomplete
configuration, evidence inconsistency, reruns, source/workflow/repository errors,
disabled protections, existing immutable/history/recovery rules and future compatible
Connectors. These are simulated API responses, not real signatures. Existing genuine
B1.2 catalogue/package verification remains separate. Genuine new pointer acceptance
and configured GitHub enforcement remain prerequisites for live operation.
