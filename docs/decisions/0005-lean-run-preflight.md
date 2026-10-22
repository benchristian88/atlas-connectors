# 0005 — Lean run-level publication preflight

Status: **Implemented for review; production activation blocked pending genuine acceptance**

Date: 2026-10-23

Supersedes [ADR 0004](0004-isolated-signed-publication-verifier.md)'s transition-specific
authorization and 60-second cross-job freshness decision. The historical ADR is
retained. [ADR 0001](0001-github-catalogue-publication.md)'s immutable storage,
[ADR 0002](0002-single-maintainer-publication.md)'s single-human trust model and
[ADR 0003](0003-sequence-one-bootstrap.md)'s separate bootstrap approval/fence remain.

## Decision

Issue one canonical signed security preflight for a fresh manual main publication
run, bound to exact source C, policy-byte digest, run ID, attempt one, operation
and acceptance-only mode. Independently authenticate the configured human,
repository/owner, required CI, protected main, publication/verification environments,
release immutability and all five complete rulesets/bypass lists. Reuse the two
existing Apps, bounded transport, protection/authority validators and pinned
GitHub/Sigstore verifier. Remove transition variants, per-asset/ref grants, target
observation and challenge-consumption code rather than retaining an alternate mode.

The reusable signer and executable Publisher code are pinned to reviewed full SHA
S, independent of advancing catalogue data C. The isolated Verifier receives no
caller code, artifacts or inherited secrets. Publisher code reads C as data only.
Before minting a Publisher token, verify the signature, exact run/source/operation,
actual policy bytes, S and complete signed observations. P1/P2 continue performing
all normal state, provenance, package, history, immutable-release and CAS checks.
Existing catalogue/package/pointer signatures and consumer contracts are unchanged.
The public policy's `single-maintainer-v1` identifier continues describing the
unchanged human authorization model; it is not the retired signed V1 grant schema.

Preflight freshness is a maximum 15-minute startup window from earliest privileged
observation. Verification must finish inside it. A local, nonexported startup
receipt permits later phases only in the same job/run for at most 30 minutes;
each phase reauthenticates the same bundle and context. Provider checks continue
at mutation boundaries; there is no new signature for individual writes.

The Verifier's Contents Read capability cannot establish draft absence. Its API
surface excludes draft/release/ref observations. Keep complete bounded draft
inventory and bootstrap-stage recovery in the authenticated Publisher Contents
Write path. Normal staging also enumerates drafts, never inferring absence from
the published-release-by-tag endpoint.

## Security and operational trade-offs

One preflight reduces job/artifact/signature orchestration and avoids expiring
legitimate work during cross-job scheduling. It authorizes startup, not every
individual provider mutation. Administration Read later rechecks visible ruleset
configuration and returned bypass arrays against the signed snapshot; omitted
bypass actors remain unavailable current evidence, never empty arrays. A hidden
bypass change after observation cannot be excluded. Main/environment/CI/state
rechecks, immutable releases, exact bytes, bounded inventories, CAS and fail-closed
ambiguous writes reduce races but cannot make GitHub operations atomic.

Both Apps retain their permissions and independent identities. Administration
Write remains a powerful Verifier credential, confined to the isolated job; a
compromise can mutate protections despite this client's GET-only evidence API.
GitHub environments are not workflow-file secret ACLs. A compromised administrator,
sole maintainer, trusted implementation, pinned action or correct App key remains
a risk. Source C contains no executed privileged code; accepted S is a deliberate
implementation trust boundary. There is no independent human reviewer or marketplace.

The startup receipt relies on the trusted ephemeral runner, not portable signature
semantics or a global replay store. Bindings prohibit cross-run/operation/source
reuse. The run-level preflight deliberately does not certify mutable draft absence,
continuous protection, package eligibility, recovery success or safe future writes.

## Deployment and acceptance boundary

Local implementation cannot know its future reviewed commit SHA without creating
a commit, which this task forbids. Existing literal pins therefore remain the
explicitly inert pre-V2 `da5562eeb21d5c1cc653cfea7ae8d025d2a9174a`, not a falsely accepted
V2 implementation. Freeze reviewed V2 as S, then review a separate caller C updating
the reusable call, executable checkout, implementation literal and real trust pins.
Never automatically follow main or invent a pin. Current trust is unaccepted and
active publication policy bytes are unchanged.

An acceptance-only dispatch signs configured real evidence with an explicit signed
acceptance-only boolean while trust remains unaccepted. It skips the Publisher job
entirely; its bundle is rejected by the publication consumer even after acceptance.
Review one genuine production-profile signing/isolation run before separately
enabling trust. Experimental C/S evidence and synthetic tests are not production
acceptance. Then use the unchanged staged P2 bootstrap and independent approval of
the actual pointer digest; no one-dispatch activation or legacy package exemption.
See the [implementation/security contract](../signed-publication-verifier.md) and
[operator checklist](../../catalogue/publication/README.md).
