# Proxmox VE 0.2.0 qualification

As of **18 October 2026**, production Connector **0.2.0** declares
`source_versions.qualification=qualified`, `qualified_versions=["9.2.11"]`,
`known_incompatible=[]` and `newer_untested_policy=allow_with_warning`.
**Proxmox VE 9.2.11 is the qualified source version.** SDK semantics report
supported only for that exact version; other versions, including other 9.x
versions, remain untested unless later qualified. No incompatible versions are
asserted by this release.

This is promotion of the exact discovery implementation in **0.2.0-i4b.6**,
qualified live at source commit `73f539883fe1663c332b7e6cd1cb4c054e0eae75`.
The historical candidate Manifest remains unqualified, version 0.2.0-i4b.6,
with qualified_versions empty. Its accepted archive SHA-256 remains
`dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97`.
The production metadata/docs and normal packaging are promoted separately;
shared discovery, readiness, transport, normalization and diagnostics source
remain unchanged.

## Accepted operator live evidence

The operator supplied repeatable positive-path results from an isolated Atlas
qualification instance against Proxmox VE **9.2.11**:

| Check | Accepted result |
| --- | --- |
| Test Connection | Authenticated successfully; source version 9.2.11; Inventory Ready. |
| First manual run, Debug On | COMPLETE / Full scope; 100 observations; one batch; zero warnings/errors. |
| Repeat unchanged, Debug Off | COMPLETE / Full scope; 100 observations; one batch; zero warnings/errors. |
| Reconciliation repeat | No duplicate reconciliation work; zero new reconciliation items. |
| Absence safety | No unsafe absence/no-longer-observed result; repeat no-longer-observed count zero. |
| Deliberately incorrect SHA-256 certificate fingerprint | Test Connection failed closed. |
| Correct fingerprint restored | Test Connection succeeded again with 9.2.11 / Inventory Ready. |

Live topology evidence showed node-owned host vmbr0 Interfaces, guest
`proxmox.bridge_name=vmbr0` and VLAN tags 3, 5 and 6. No bridge/storage Assets
or connected_to/uses_storage relationships were found. VLAN 99 is fixture/test
evidence only. Broader static IP/MAC/trunk behavior remains implementation/fixture
evidence unless explicitly recorded live. No reconciliation items were accepted
or rejected during qualification; repeat evidence does not imply automatic
knowledge acceptance. The original temporary candidate qualification authority was revoked after the
qualification evidence was collected, then later restored for post-qualification
regression verification. That restored authority remains time-bounded pending
replacement by the released Connector or automatic expiry.

## Limits of qualification

Authentication-secret negative testing was not performed. The fingerprint
mismatch was the supplied live negative test. Positive-path qualification does
not claim live testing of all ACL/NoAccess mutations, source outages, offline nodes,
migrations, VMID reuse, node renames, deployment replacement, malformed inputs,
limits, cancellation, certificate rotation or other safe-negative scenarios.
Those scenarios remain fixture/regression evidence or future live work as
applicable. The historical `.1`/`.2` runs were PARTIAL, and the `.3` diagnostic /
`.4` inactive-storage fix / `.5` storage scope decision retain their original
outcomes. This promotion does not rewrite them as successful `.6` runs.

Native Debian/systemd LIVE acceptance remains outstanding. The current Atlas
I3/I4A architecture records that deployment acceptance separately from Docker/LXC
and native-style local fixture validation. No native live deployment or new source
call was performed by this promotion.

## Package and publication boundary

0.2.0 is the first actual production Connector release being prepared. 0.1.0 was
an internal development/probe baseline, never tagged or published as a GitHub
Release; Git history preserves it without a retroactive release. Candidate `.6`
packaged docs preserve their pre-live snapshot and are not rewritten as release
evidence. The full dated candidate/live history remains in the repository's I4C
operator records outside the reviewed package contents.

The normal deterministic bundle contains both fixed entry points and all qualified
discovery helpers, while excluding tests, fixtures, candidate paths and incidental
files. The combined detached Manifest uses the canonical SDK schema, exact archive
digest, source HEAD and existing GitHub attestation identity. A local dirty-tree
build records contextual HEAD; it does not attest that uncommitted changes exist
at that revision. Publication still requires the reviewed committed source and
unchanged assets through the protected release workflow. This preparation performs
no commit, push, tag, merge or GitHub Release publication. Atlas catalogue/download
integration is separate work; no remote provenance acceptance is claimed here.
