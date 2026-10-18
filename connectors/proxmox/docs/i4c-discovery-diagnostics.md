# I4C discovery diagnostics — introduced in 0.2.0-i4b.3

The operator's `.2` live run of Proxmox VE 9.2.11 was COMPLETED/PARTIAL with
179 observations, 48 reconciliation items and `invalid_source_record`. The `.1`
run had 140 observations. Both remain failed qualification evidence; `.2`'s
exists:null fix succeeded but did not resolve the independent remaining condition.
**9.2.11 and candidate .3 remain UNQUALIFIED; qualified_versions is empty.**

Diagnostics were introduced in **0.2.0-i4b.3**, archive digest
`sha256:05c8ccb44b3964b780d3ffcef9a71a89b80ed2a5b7f4de22806ea7b0f62cf626`.
It instruments existing validation paths; it does not relax validators or change
source calls, privileges, AIP observations, warnings or completeness semantics.
Production 0.1.0 remains probe-only. No live source is contacted by fixture checks.

The operator's `.3` live debug trace then isolated the only PARTIAL cause to
`storage_inventory_mismatch` on `node/pve3`. Proxmox exposes an additional
disabled/inactive local-zfs status row there without an applicable configuration
definition. `.3` remains failed/unqualified evidence. The historical
**0.2.0-i4b.4** correctly fixed that precise condition; its artifact and
normalization remain immutable. It was valid qualification work under that scope.

The historical **0.2.0-i4b.5** made a subsequent storage MVP scope decision. Proxmox
storage definitions are configuration/resources exposed by the virtualisation
platform. Atlas MVP does not model them as standalone Assets. Backing storage
infrastructure should be discovered by the integration responsible for that
infrastructure where available. `.5` emits no storage-pool Assets, uses_storage
relationships, storage capacity telemetry, workload storage facts or storage
dependencies. Atlas may introduce a richer resource/dependency model later.

Neither storage inventory endpoint is called; storage normalization, resolution
and associated diagnostic stages/reasons are absent from `.5`. Guest disk/rootfs/
mount entries are ignored without storage warnings; bounded guest network parsing
is retained. All remaining validation and generic diagnostic behavior is unchanged.
See the [active live runbook](i4c-live-qualification.md) and
[current discovery specification/source call matrix](../candidate/docs/discovery.md).
The operator subsequently reported two `.5` COMPLETE runs: 136 observations,
one batch and zero warnings/errors each, with no storage operations. `.5` and
Proxmox 9.2.11 remain unqualified, with qualified_versions empty.

Candidate **0.2.0-i4b.6** is a separate product scope decision removing bridge
Assets and connected_to Asset relationships while retaining host bridge Interfaces,
validated guest `proxmox.bridge_name`, explicit `proxmox.vlan_tag` (99 in fixtures),
bounded trunk VLANs, canonical MAC/static IP and conservatively proven Networks.
Network enumeration, ACL, bridge/VLAN/reference and pending/current validation
remain mandatory. No DHCP IPs are inferred; no storage Assets/dependencies return.
Host network source/normalization contexts now use `proxmox.interface` with
`node/{node}/interface/{iface}`, never `proxmox.bridge` or bridge Asset IDs.
No generic diagnostic schema or UI is changed. Source-call order/count remains
identical to `.5`, and normal/debug still differ only in safe diagnostic detail.
Operator-reported `.6` live positive-path qualification against Proxmox VE
**9.2.11** passed repeatably on **18 October 2026**, with the diagnostic and
Debug On/Off evidence below. This accepted/passed live evidence does not change
published/global qualification: `.6` remains `source_versions.qualification=unqualified`
with `qualified_versions=[]`, unpublished and without production promotion.

## Structured trace

The fixed playbook receives a runtime-created private `diagnostics.ndjson` beside
its leased input. It cannot choose a destination through connection configuration
or runtime control. The writer opens only that precreated regular, private,
single-link file and appends unbuffered bounded JSON lines. The runtime separately
checks its retained descriptor/inode after stopping descendants. Validated evidence
survives PARTIAL, failure, Connector/Ansible exception, cancellation and timeout;
private workspaces/credentials are still removed.

Normal event fields are sequence, stage, result, reason_code, optional object_class,
external_id, parent_external_id, source_category, record_count. Tokens are bounded
to 64 characters and external identities to 192 characters. Debug only adds field,
encountered_type, validation_rule, expected and action. No offending value, arbitrary
body/config, comment/description, header, command, environment or mount content is
serialized. No XML, raw source logging or SDK/AIP extension is introduced.

Limits: 8,192 events, 768 bytes per line, 6 MiB sidecar. The same worst-case size
budget applies in both modes. Overflow emits diagnostic_limit; the runtime blocks
a contradictory COMPLETE or malformed/incomplete diagnostic trace before success
callbacks. Atlas permanently retains counts/reasons and up to 128 warning contexts.
Processed/accepted/skipped counts concern classified inventory rows/interface
subrecords, independently of the number of AIP observations.
Accepted counts describe normalization, not operator acceptance of Atlas knowledge.

## Active `.6` stages and reason vocabulary

| Stage | Representative stable reasons |
| --- | --- |
| Source read | source_response_invalid, source_response_limit, source_total_bytes_limit, source_call_limit, source_json_invalid, source_boolean_invalid |
| Authorization | permission_response_invalid, permission_flag_invalid, acl_path_invalid, acl_path_limit, authorization_unproven, authorization_changed_during_discovery |
| Deployment/node | deployment_record_unknown, duplicate_source_record, node_membership_mismatch, node_status_invalid, node_not_visible |
| Network/bridge | network_changes_pending, bridge_identity_invalid, bridge_duplicate, bridge_inactive, bridge_cidr_invalid, bridge_status_invalid |
| Guest/config | guest_identity_invalid, guest_node_unresolved, guest_power_state_invalid, guest_config_missing, guest_config_read_failed, guest_inventory_mismatch |
| Guest interface | guest_interface_invalid, guest_mac_invalid, guest_ip_invalid, vlan_tag_invalid, vlan_trunks_invalid, guest_bridge_invalid, guest_bridge_unresolved |
| Consistency/limits | inventory_changed_during_discovery, observation_limit, sensitive_material_rejected, duplicate_observation |

The existing outward warning invalid_source_record remains compatible. The trace
supplies the stage/object/rule that produced it. Debug types and expected grammar
are metadata, not source values. Explicit source-local identity stays separate
from human display names and accepted canonical knowledge.

Historical `.4` traces can still contain Skipped / `storage_record_out_of_scope`
for the proven inactive/disabled non-applicable row, and storage-specific warnings
for real uncertainty under `.4`'s broader scope. Those records are not rewritten.
`.6`, like `.5`, has no storage stage, storage source category or guest-storage resolution;
normal/debug tests require none to appear. The generic sidecar format and reason
validation do not change, so historical traces remain interpretable.

## One next run, administrator access and retention

With the matching Atlas migration/API/worker/runtime deployed, a global runtime
administrator with scoped Integration view selects **Enable debug for next
discovery run**. **Debug next run: Armed** becomes **Off** as soon as the next run
is created, including a scheduled run. Transactional creation failure preserves
arming; a created run consumes it regardless of outcome. Run intent is immutable.

Ordinary users see safe normal diagnostics only. Authorized administrators expand
**Debug trace**, inspect its expiry and may select **Delete debug data**. Debug
expires within 48 hours of creation; Atlas's existing worker purges expired rows,
and reads purge expired rows immediately. Portable backups exclude debug data.
Deletion retains normal diagnostics, run, evidence, reconciliation and audit.

## Local validation and completed live evidence

The [live qualification record](i4c-live-qualification.md) records the completed
operator checkpoint at Connector `73f539883fe1663c332b7e6cd1cb4c054e0eae75` and
Atlas `85d750b626cdfe772706a92d1f9678f26c5f4e97`, clean LXC dual rebuilds, independent
verification of exact archive
`sha256:dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97`,
isolated staging and final revocation. Pre-live dirty-checkout provenance remains
contextual, not a publisher attestation. Packaged documents preserve that pre-live
snapshot; this repository record adds the later operator evidence.

Tests exercise diagnostic visibility, secret/body/config exclusions, destination
tricks, bounded flush/overflow, actual Runner, and identical AIP/source calls for
debug off/on. Those tests establish fixture evidence independently of the following
operator-supplied live results; this documentation update did not repeat live execution.

The first manual `.6` discovery in a fresh Customer/Site and fresh Integration
completed with **Coverage Complete / Full scope, 100 observations, one batch and
zero warnings/errors**. Normal diagnostics reported **75 processed, 66 accepted,
9 skipped, 0 warning, 0 error**. These counts concern normalization, not operator
acceptance of knowledge. **Debug next run** was armed before discovery and returned
automatically to **Off** after run creation/completion. Debug did not alter coverage
or outcome.

Live reconciliation showed host **vmbr0** as `proxmox.interface`, guest
`proxmox.bridge_name=vmbr0`, and real VLAN tags **3, 5 and 6**. No bridge Asset was
observed; searches found no `connected_to`, `uses_storage` or `proxmox.storage`.
**VLAN 99 remains fixture/test evidence only.** MAC/static IP/trunk and conservative
Network membership behavior retains its pre-live test evidence; no additional live
field values are supplied.

The second manual run with **Debug Off** again completed **Complete / Full scope**,
with **100 observations, one batch and zero warnings/errors**. The first had
`baseline_run_id=null`; the second used the first `.6` run,
`af5bf74c-4d81-40e0-b163-e6fc6f38e73a`, as baseline. It created **100 evidence records**,
**0 reconciliation items**, **0 assertions**, **0 reobservations** and **0 no-longer-observed
results**. No duplicate reconciliation work or unsafe absence was generated. No
reconciliation decisions were accepted/rejected during qualification, so the zero
assertion/reobservation counts were expected.

An incorrect SHA-256 certificate fingerprint then caused Test Connection to fail;
restoring the correct fingerprint restored **9.2.11 / Inventory Ready**. This is
live fail-closed TLS evidence. No fingerprint value is recorded. Authentication-secret
negative testing was **not performed** because the stored secret is hidden/non-readable
and Integration fields become immutable after successful discovery.

The temporary `.6` qualification permission was revoked after collection, retaining
run/evidence history. There was no release, published/global qualification or
production/default 0.1.0 promotion. One-shot debug detail remains optional outside
this completed comparison; any further source-shape change is a separate reviewed fix.
