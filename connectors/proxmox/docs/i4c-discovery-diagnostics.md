# I4C diagnostic successor — 0.2.0-i4b.3

The operator's `.2` live run of Proxmox VE 9.2.11 was COMPLETED/PARTIAL with
179 observations, 48 reconciliation items and `invalid_source_record`. The `.1`
run had 140 observations. Both remain failed qualification evidence; `.2`'s
exists:null fix succeeded but did not resolve the independent remaining condition.
**9.2.11 and candidate .3 remain UNQUALIFIED; qualified_versions is empty.**

The next candidate is **0.2.0-i4b.3**, archive digest
`sha256:05c8ccb44b3964b780d3ffcef9a71a89b80ed2a5b7f4de22806ea7b0f62cf626`.
It instruments existing validation paths; it does not relax validators or change
source calls, privileges, AIP observations, warnings or completeness semantics.
Production 0.1.0 remains probe-only. No live source is contacted by fixture checks.

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

## Stages and reason vocabulary

| Stage | Representative stable reasons |
| --- | --- |
| Source read | source_response_invalid, source_response_limit, source_total_bytes_limit, source_call_limit, source_json_invalid, source_boolean_invalid |
| Authorization | permission_response_invalid, permission_flag_invalid, acl_path_invalid, acl_path_limit, authorization_unproven, authorization_changed_during_discovery |
| Deployment/node | deployment_record_unknown, duplicate_source_record, node_membership_mismatch, node_status_invalid, node_not_visible |
| Storage | storage_definition_missing, storage_definition_mismatch, storage_node_unresolved, storage_status_invalid, storage_capacity_invalid, storage_inventory_mismatch |
| Network/bridge | network_changes_pending, bridge_duplicate, bridge_inactive, bridge_cidr_invalid, bridge_status_invalid |
| Guest/config | guest_identity_invalid, guest_node_unresolved, guest_power_state_invalid, guest_config_missing, guest_config_read_failed, guest_inventory_mismatch |
| Guest storage | guest_storage_reference_invalid, guest_storage_unresolved |
| Guest interface | guest_interface_invalid, guest_mac_invalid, guest_ip_invalid, vlan_tag_invalid, guest_bridge_invalid, guest_bridge_unresolved |
| Consistency/limits | inventory_changed_during_discovery, observation_limit, sensitive_material_rejected, duplicate_observation |

The existing outward warning invalid_source_record remains compatible. The trace
supplies the stage/object/rule that produced it. Debug types and expected grammar
are metadata, not source values. Explicit source-local identity stays separate
from human display names and accepted canonical knowledge.

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

## Local and live gates

Use the [active runbook](i4c-live-qualification.md) for exact clean-commit staging.
This work remains uncommitted until operator review. Detached source_commit on a
dirty checkout is contextual, not a publisher attestation. Rebuild and independently
verify from the reviewed committed source before staging a new exact authorization.

Tests exercise diagnostic visibility, secret/body/config exclusions, destination
tricks, bounded flush/overflow, actual Runner, and identical AIP/source calls for
debug off/on. They do not qualify an actual Proxmox deployment. Do not accept live
reconciliation automatically or promote 0.2.0. The next live run should collect
safe normal reasons first and use the one-shot debug metadata to identify the
remaining validator. Any source-shape change is a separate reviewed fix.
