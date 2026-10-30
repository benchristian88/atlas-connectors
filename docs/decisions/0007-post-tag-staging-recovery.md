# 0007 — Narrow post-tag draft staging recovery

Status: **Rejected; superseded by the owner’s clean 0.2.2 publication direction**

Date: 2026-10-31 (Pacific/Auckland)

## Owner decision — 31 October 2026

The proposed workflow-mismatch relaxation is **not accepted**. The owner abandoned
automated recovery of incomplete Proxmox 0.2.1 and selected a clean 0.2.2 publication
from later reviewed source, after the corrected engine is merged and repinned.
No 0.2.2 metadata or identity is created by this implementation task.

[ADR 0006](0006-connector-package-publication.md) remains authoritative and is not
superseded: package source P and current caller C must have identical workflow
directories for **Tag, Stage and Finalize**, including existing-draft recovery.
Source review, main ancestry, required CI, original-build authentication, signed
admission and separate human approvals remain mandatory. Workflows Write remains
unavailable; no App permission expansion or provider permission bypass is authorized.

Protected tag `proxmox-v0.2.1`, original successful signed build `41017538114`,
artifact `12960302111`, incomplete draft `428740362` and checksum asset `691270692`
remain unpublished and untouched historical evidence. They are not valid catalogue
publication authority and must not be resumed through the rejected exception.

The general draft URL/asset verification correction and partial-draft recovery
with matching P/C workflows remain in the successor. The post-tag repin exception
and its redundant source module have been removed. Publication stays disabled.
See the [current report and S4 handoff](../phase-4b4-draft-staging-recovery.md).

The following proposal is retained as **rejected design history**, not executable
policy or current operator instructions. It would have relaxed only existing-draft
uploads; it could not safely support Finalize without a permission expansion.

## Historical context

The existing signed Proxmox 0.2.1 package at P predates a required implementation
correction. A later independent SHA repin changes `connector-publish.yml` in C,
although the protected original tag, source and signed build remain unchanged.
Using Tag's workflow equality rule for every later operation prevents recovery.
An unrestricted workflow mismatch exception would be too broad.

## Historical proposed decision — rejected

For Stage/Finalize preparation and authority, retain exact reviewed source P,
merged main ancestry and successful required CI. For a mismatch require an
explicit positive existing release ID, separately reviewed/merged/CI-passing
successor S and caller C, and the following exact workflow constraints:

1. S's whole workflow directory equals P's, including the original release build,
   verifier and all unrelated workflows.
2. C's workflow directory has exactly the same paths as P. All files except
   `connector-publish.yml` have identical blob identities.
3. Authenticate both versions of that caller file against their Git blob hashes.
   Its only byte changes are the existing three occurrences of one immutable
   implementation SHA, replaced by trusted S: reusable signer call, executable
   checkout, and implementation environment literal. No comment, action,
   permission, gate, script, branch reference or extra workflow change is allowed.

The original protected tag, successful first attempt, official Publisher actor,
signed provenance, approved P/D and original artifact ID/ZIP digest remain
mandatory before credentials or writes. Trusted S reconstructs package/metadata
and compares them byte for byte to the original artifact. It verifies the original
Sigstore bundle; it never executes P's code or creates replacement signatures.
Stage authenticates the approved existing draft and exact partial inventory,
then uploads only missing original files. No release metadata write is permitted
by the exception. The signed admission format and explicit request are unchanged.

Draft download web URLs may use only the expected tag or a bounded lowercase-hex
`untagged-…` selector independently supplied by that exact authenticated release's
official `html_url`. Numeric REST IDs, repository/asset URLs, release author,
uploader, state, size, digest and exact bytes are still required. Missing metadata
fails closed. Published-release verification accepts only final tagged URLs.

## Historical permission blocker

GitHub's [current release-update documentation](https://docs.github.com/en/rest/releases/releases#update-a-release)
says the resolved existing target is subject to the workflow permission check,
even when `target_commitish` is not changed. Its
[2023 announcement](https://github.blog/changelog/2023-11-02-github-actions-enforcing-workflow-scope-when-creating-a-release/)
describes an existing-ref exception for creation; this is insufficient authority
to override the current update contract. Asset
[uploads](https://docs.github.com/en/rest/releases/assets#upload-a-release-asset)
require Contents Write and do not change the target or workflows.

The rejected implementation rechecked whole-workflow equality immediately before
PATCH and rejected a mismatch with `connector_finalize_workflows_write_required`. Already
published exact identities can still undergo the independent read-only verifier.
That implementation modeled original-build recovery, but an end-to-end
no-escalation Finalize after repinning was **BLOCKED**. No Workflows Write grant,
alternate credential, retargeting, tag recreation, workflow rollback or substituted
build was proposed. The owner instead rejected this relaxation and selected a
clean release.
Successful local models never established that permission sufficiency.

See the [engineering report and owner handoff](../phase-4b4-draft-staging-recovery.md).
