# 0003 — Two-dispatch sequence-one bootstrap with a consumed-authority fence

Status: **Proposed for owner review; implemented behind disabled policy**

Date: 2026-10-22

Extends [ADR 0001](0001-github-catalogue-publication.md) and
[ADR 0002](0002-single-maintainer-publication.md), without changing their signing
profiles, pointer schema, normal publication history or single-maintainer model.
No Atlas ADR or consumer trust profile is superseded.

## Decision and circularity

Normal publish/recover require authenticated current history. A distinct fixed
`bootstrap` operation is the only initializer. Its immutable inputs are the pinned
original sequence-one bytes, original build bundle, historical source and legacy
release/asset identities. It neither rebuilds nor qualifies a Connector package.

GitHub assigns the new release and asset IDs after draft creation. Therefore the
root pointer digest cannot be approved in advance. Use two separately reviewed
policy revisions and two fresh manual dispatches of catalogue-publish.yml:

1. `enabled: true`, `bootstrap_operation: stage`, sequence/digest pins null. Verify
   source and P1 authority; stage the exact original catalogue/bundle; construct
   canonical pointer using actual IDs; attest through the existing selection
   signer; verify and retain all four draft assets. Stop without publication.
2. Independently inspect/authenticate the staged files. Commit the actual pointer
   digest with sequence 1 and `bootstrap_operation: activate` through protected
   main. A fresh dispatch verifies the original signing run and the new dispatch,
   requires different authenticated source revisions/run identities, and only
   then finalises the release and establishes current. A receipt alone is not approval.

`enabled` remains false and both pins remain null in this implementation change.
Normal publication cannot use unconfigured history, and no missing-current fallback
is added to preparation, publish or recover. Subsequent selection still requires
P1's predecessor chain and all generic package eligibility checks.

## One-time authority and interrupted ref creation

Absence of current cannot distinguish initial bootstrap from deletion after
successful bootstrap. An immutable snapshot alone cannot distinguish those cases
either: it is deliberately published before current. To preserve a durable fence
without adding a service, database, fifth release asset or pointer field, create
`refs/tags/catalogue-bootstrap-root` pointing at the verified root commit **before**
creating current. The existing App-only publication-tag creation rule applies.
A new `atlas-bootstrap-lock` tag ruleset covers this exact ref, forbids update and
deletion, and has no bypass, including the App. This settings requirement is new
and needs operator review; this task does not configure it.

The root has no parent and exactly the pointer/bundle blobs. Both refs use
create-only POST; no forced update or ref deletion exists. If the fence is already
present, bootstrap stops even when current is absent. Thus success terminates
bootstrap authority, independently of consumer checkpoint loss. Marker creation
also conservatively consumes authority when interrupted before current creation.
That narrow interruption needs a separately reviewed recovery decision; this tool
intentionally has no marker-clearing or branch-recreation command.

A lost response to current creation is inspected within that invocation: exact
root SHA, root tree, current files, and fence must agree. No write is repeated.
If inspection is unavailable, a later dispatch stops on existing current/fence;
operators inspect and record evidence separately. A published immutable release
with neither ref remains recoverable by a fresh activation dispatch using the
approved digest. Every asset and both signatures are reverified without replacement.

## Provider semantics and bounds

[GitHub release listing](https://docs.github.com/en/rest/releases/releases#list-releases)
includes drafts for push-capable identities. Bootstrap uses that endpoint instead
of treating get-by-tag (documented for published releases) as proof of no draft.
It requires complete enumeration in at most four pages of 100 entries and a
bounded catalogue-tag ref listing. Overflow, duplicate drafts, extra history,
orphan root-snapshot tags and unavailable evidence stop before release creation.

[GitHub commit creation](https://docs.github.com/en/rest/git/commits#create-a-commit)
supports an empty parents array for a root;
[reference creation](https://docs.github.com/en/rest/git/refs#create-a-reference)
creates the branch without updating an existing one. Read-back verifies the exact
two blob identities/modes, no parents, and ref identity. Release immutability is
still an observed GitHub enforcement claim, separate from Sigstore verification.

## Limits

A repository administrator can remove settings and history. The fence is a
protected provider record, not a new cryptographic freshness oracle. Removing all
provider evidence and all consumer checkpoints defeats an in-repository historical
witness; recovery then requires independent audit. Current rules cannot prove that
protection was never temporarily disabled. Single-maintainer compromise retains
ADR 0002's limitations. No genuine new selection, configured protections, immutable
publication or live acceptance has been demonstrated by unit tests.

Historical Proxmox 0.2.0 stays exactly as signed, active in sequence one, but its
mutable executable release remains ineligible. There is no package exception.
A later reviewed catalogue can withdraw that old entry while retaining its full
identity and include a new qualified immutable version through normal P1 gates.
