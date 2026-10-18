# I4C — Proxmox live qualification

Updated **18 October 2026** for the subsequent bridge Asset product scope decision.

The active successor is **0.2.0-i4b.6**, still **UNQUALIFIED**, unpublished and with
`qualified_versions: []`. Proxmox VE **9.2.11 remains UNQUALIFIED**. The candidate
archive digest is `sha256:dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97`. `.6` has no live results yet.
Production/default **0.1.0** remains probe-only and byte-identical.

## Operator-reported `.5` live baseline

Connector `.5` was committed at `a153d8804c89f5184e151cef51b5f9a961f20705`, with
bundle `sha256:bff4a3c9c4b824ed46622153b52c433c3bf03d926bc47d8249ae8831f68fa69b`.
Against Proxmox **9.2.11**, cluster **pve1/pve2/pve3**, Test Connection succeeded,
source version was 9.2.11 and inventory capability was Ready. The first live
manual discovery completed with **Coverage Complete, 136 observations, one batch,
zero warnings/errors**. Diagnostics classified **75 processed, 66 accepted,
9 skipped, zero warning/error**; its debug trace contained no storage operations.
A second unchanged run with **Debug Off** again completed COMPLETE with **136
observations, one batch and zero warnings/errors**. These are operator-reported
positive-path results, not execution performed by this implementation pass.

This is a repeatable COMPLETE baseline for `.5`'s declared contract. `.5` and
9.2.11 remain UNQUALIFIED, with no production promotion. `.3` diagnosed the storage
mismatch; `.4` correctly handled legitimate node-scoped disabled/inactive status;
`.5` deliberately removed storage definitions/pools from the MVP Asset model.
Those historical artifacts and explanations remain intact.

## Current `.6` product boundary

Proxmox bridges are host networking constructs used to describe Interface and
Network topology. Atlas MVP does not model them as standalone Assets. Guest bridge
attachment remains bounded topology context on the guest Interface, and explicit
VLAN/static-network evidence is retained.

Only `proxmox.cluster`, `proxmox.node`, `proxmox.qemu` and `proxmox.lxc` remain
Asset classes. Only `proxmox.member_of` and `proxmox.runs_on` remain relationship
classes. There are no `proxmox.bridge` Assets or `proxmox.connected_to` Asset links,
no replacement pseudo-Assets/resources, no storage Assets and no storage dependencies.
Qualification requires **four Asset / two relationship mappings**. With current
Atlas taxonomy, the only deliberate override remains cluster→proxmox_cluster;
node/QEMU/LXC and member_of/runs_on exact-auto-map. No bridge/network_bridge or
connected_to/connected_via choice is required or accepted.

An active `vmbr0` becomes canonical host Interface
`node/{node}/interface/vmbr0`, owned by `node/{node}`, with source name, VLAN-aware
boolean fact and explicit CIDR-derived current IP/Network link where available.
Guest Interface `guest/{kind}/{vmid}/interface/net0` retains configured name/MAC,
explicit static IP and validated attachment as single string configuration fact
`proxmox.bridge_name=vmbr0`. `proxmox.vlan_tag=99` remains an integer configuration
fact when explicitly configured. `proxmox.vlan_trunks` safely retains at most 128
unique VLANs as a sorted semicolon-separated string, with the same 1–4094 bounds.
No coercion, default VLAN 0, inferred DHCP address or guest-agent call is allowed.
Tagged/trunk Interfaces cannot inherit the bridge subnet; untagged membership
requires the unchanged explicit static-subnet match.

`/nodes/{node}/network` remains required for host topology, bridge-reference
validation, subnet evidence, pending/current safety and completeness. The source
sequence/count is unchanged from `.5`: **46 three-node / 40 two-node requests**.
All ACL, malformed-record, placement, offline, pending, limits and before/after
consistency checks remain fail-closed. Missing/unresolved attachment still warns
and prevents COMPLETE. PARTIAL/failed still prohibits absence processing.

Atlas's existing generic scope identity includes the selected object classes;
removing `proxmox.bridge` changes the coverage key. Its baseline selector requires
an equal key plus the same DataSource/Customer/Site. Thus a `.5` COMPLETE run cannot
cause absence/deletion of historical bridge knowledge under `.6`. No Atlas or SDK
change, migration, new taxonomy, source endpoint/privilege or licensing change is
required. The existing normal/debug sidecar architecture is unchanged; host network
diagnostics now identify Interfaces rather than bridge Assets.

Candidate-specific [README](../candidate/README.md),
[discovery/source calls](../candidate/docs/discovery.md),
[capabilities](../candidate/docs/capability-matrix.md),
[permissions](../candidate/docs/permissions.md),
[qualification](../candidate/docs/qualification.md) and
[packaged completion report](../candidate/docs/i4b-completion-report.md) describe `.6`.
The [local implementation/validation report](i4c-network-scope-report.md) records
actual commands, fixture counts, exact digest and immutable-byte proof.
Shared production documents and prior archives remain frozen.

Next live action after separate review and a clean committed-source checkpoint:
rebuild twice and verify this exact `.6` identity, preview only the four/two mapping
plan, stage/activate in the isolated qualification instance, run Test Connection,
then one manual Debug On discovery. Inspect vmbr0 host topology, guest bridge/MAC/
VLAN 99/static IP and conservative membership, explain count changes from `.5`,
then repeat unchanged with Debug Off. No commit/push/staging/activation/live source
call or production promotion occurs in this implementation pass.

## Historical `.5` product boundary and preparation

The following records `.5`'s original local preparation before the operator
reported the positive live runs above. Its original digest and validation evidence
are retained; the current live procedure below targets `.6`.


Proxmox storage definitions are configuration/resources exposed by the
virtualisation platform. Atlas MVP does not model them as standalone Assets.
Backing storage infrastructure should be discovered by the integration responsible
for that infrastructure where available.

`.5` removes `proxmox.storage` Assets and `proxmox.uses_storage` relationships,
storage-only facts and storage-specific diagnostics/completeness. No storage
capacity telemetry, storage-pool Assets, workload storage facts or storage
dependencies are represented. Atlas may introduce a richer resource/dependency
model later. No backing NAS/backup server is inferred from a pool name.

The five Asset classes are `proxmox.cluster`, `proxmox.node`, `proxmox.qemu`,
`proxmox.lxc`, `proxmox.bridge`. The three relationships are `proxmox.member_of`,
`proxmox.runs_on`, `proxmox.connected_to`. Networks/Interfaces remain canonical
AIP domains. Qualification requires only those five Asset and three relationship
mappings. Do not include old storage mappings in `.5` mapping-choice input.
Atlas global taxonomy/reference data is unchanged; no historical knowledge is deleted.

Neither `/storage` nor `/nodes/{node}/storage` is called or allowlisted.
Storage-specific targeted ACL reads/Datastore.Audit requirements are removed.
Guest current config reads and network-interface parsing remain required;
disk/rootfs/mount values are ignored without storage resolution warnings.
Every remaining capability retains its existing fail-closed ACL, malformed-record,
placement, topology, offline/pending, source limit and before/after proof rules.
PARTIAL/failed still prohibits absence processing. The existing generic Atlas
scope encoding includes declared classes, so `.5` has a different coverage key
from `.4`; an old broader-scope COMPLETE run is not an absence baseline for `.5`.

The representative three-node fixture now uses **46 source requests** (previously
52), and the ordinary two-node fixture uses **40** (previously 45). Removed reads
are one storage definition list, one storage status list per node and two storage
ACL-root checks. Debug off/on produces identical AIP, relationships, warnings,
completeness and ordered source calls. Only safe diagnostic detail differs.

Candidate-specific [README](../candidate/README.md),
[discovery specification/source call matrix](../candidate/docs/discovery.md),
[capability matrix](../candidate/docs/capability-matrix.md),
[permissions](../candidate/docs/permissions.md),
[qualification](../candidate/docs/qualification.md) and
[change record](../candidate/docs/i4b-completion-report.md) are packaged in `.5`.
Shared production package documents remain frozen to preserve 0.1.0 bytes.
The builder uses explicit overrides and version-specific candidate output directories.
The generic diagnostics architecture, licences, SDK/AIP and Atlas code are unchanged.

`.4` remains valid historical qualification work for pve3's local-zfs row with
`active=0/enabled=0` and no applicable node definition. `.5` is a later product
scope decision, not a replacement explanation for that `.4` defect. The `.4`
normalizer and every prior artifact remain byte-identical. The following records
that history; the current live procedure later in this document now targets `.6`.

## Historical local `.5` validation — fixtures, not live qualification

The pinned Python 3.14.7 / SDK 1.1.0 / Ansible 2.19.7 / Runner 2.4.3 /
proxmoxer 2.3.0 / requests 2.34.2 environment and reviewed collection were reused.
Commands actually executed from `atlas-connectors`:

```bash
ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-i4c-diagnostics/collections /private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python -m pytest tests/test_proxmox_normalization.py tests/test_proxmox_discovery.py tests/test_discovery_diagnostics.py tests/test_i4c_checkpoint.py tests/test_proxmox_capabilities.py tests/test_proxmox_transport.py -q --tb=short
ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-i4c-diagnostics/collections ATLAS_TEST_RUN_ANSIBLE=1 /private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python -m pytest tests/test_proxmox_ansible.py -q --tb=short
ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-i4c-diagnostics/collections ATLAS_TEST_RUN_ANSIBLE=1 /private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python -m pytest -q --tb=short
/private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python tools/build_bundle.py --candidate --output /private/tmp/atlas-i4c-mvp-scope/candidate-a
/private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python tools/build_bundle.py --candidate --output /private/tmp/atlas-i4c-mvp-scope/candidate-b
for name in proxmox-0.2.0-i4b.5.tar.gz manifest.json SHA256SUMS index.json; do cmp "/private/tmp/atlas-i4c-mvp-scope/candidate-a/$name" "/private/tmp/atlas-i4c-mvp-scope/candidate-b/$name" || exit; done
/private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python tools/verify_candidate.py --directory /private/tmp/atlas-i4c-mvp-scope/candidate-a --expected-digest sha256:bff4a3c9c4b824ed46622153b52c433c3bf03d926bc47d8249ae8831f68fa69b
/private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python tools/build_bundle.py --output /private/tmp/atlas-i4c-mvp-scope/production
cmp /private/tmp/atlas-i4c-mvp-scope/production/proxmox-0.1.0.tar.gz dist/proxmox/proxmox-0.1.0.tar.gz
/private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python tools/build_bundle.py --candidate
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/Ben/Code/atlas/apps/api DATABASE_URL=sqlite:// /Users/Ben/Code/atlas/apps/api/.venv/bin/python -m pytest /private/tmp/atlas-i4c-mvp-scope/test_atlas_reference.py -q -p no:cacheprovider --tb=short
/private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python -m pytest tests/test_documentation.py -q --tb=short
git diff --check
```

Initial focused checks: **153 passed**. Actual Runner checks: **18 passed**.
Full Connector suite after the remaining node/guest/bridge NoAccess regressions:
**199 passed, no skips**, with 162 existing Runner `codecs.open` deprecation
warnings. Documentation/link checks: **1 passed**. The read-only Atlas reference
checks: **5 passed**, using in-memory database doubles, no database connection,
no actual staging/activation and no Atlas edits. They execute the real plan and
mapping functions (only five Asset/three relationship requirements), reject both
removed mapping choices, prove changed scope hashes, and feed a real `.5`
config-failure PARTIAL seal into the unchanged absence gate with zero database access.
These checks do not substitute for live database/runtime qualification.

An independent archive-code audit exercised preserved `.4` and current `.5` on
**18 scenarios each with debug off/on**. Every retained observation and the ordered
request sequence matched after removing storage. Remaining capability failures
kept their warning/completeness outcomes. Only the three storage-only failure
cases changed from PARTIAL to COMPLETE. The preserved `.4` archive still correctly
skips the inactive/non-applicable pve3/local-zfs row and remains fail-closed for
active unknown storage and missing applicable storage status. No `.4` history or
normalization was rewritten. Audit scripts, results and logs are retained in
`/private/tmp/atlas-i4c-mvp-scope/`.

Both `.5` builds compare byte-for-byte for the archive, detached Manifest,
SHA256SUMS and index. The independent verifier accepts all **19** reviewed archive
files. The default candidate CLI writes the same digest into the new review copy
`dist/proxmox-candidate-0.2.0-i4b.5/`, without touching earlier output directories.
The detached source HEAD is contextual on this deliberately uncommitted tree,
not a claim that `.5` implementation is already present in a clean commit.

Before/after SHA-256 checks preserve all **20** existing artifact files (all five
archives and their existing manifests/checksums/indexes). A production rebuild
also compares exactly to the original 0.1.0 archive.

| Preserved archive | Unchanged SHA-256 |
| --- | --- |
| `0.1.0` | `b83ec2b3938b1747d12be5f0675dbc3e9da13c6259c2ab40f5daa994ee59ea60` |
| `0.2.0-i4b.1` | `d283441dfa70d8e589fd3da868075bdb795a8cda938a78931437432b572166c8` |
| `0.2.0-i4b.2` | `3dcf374e487a65a4398fe3ec2b3c0158c9fbdeaa5c8f885b85d8c3361904ffb5` |
| `0.2.0-i4b.3` | `05c8ccb44b3964b780d3ffcef9a71a89b80ed2a5b7f4de22806ea7b0f62cf626` |
| `0.2.0-i4b.4` | `62d25b92cf694dd7a8fde320961ccd887dc29b85497c084a44fab08fe1d7d645` |

All **804 tracked Atlas files** and **16 tracked SDK files**, HEADs and clean Git
statuses match the saved pre-edit state. No database migration, API/UI, tenancy,
secret-handling, SDK or licensing change is required. Existing authorization and
scope boundaries are retained; only storage-specific source privileges/reads are
removed. No architectural requirement for Atlas core changes was found.
Nothing is staged, committed, pushed, merged, tagged, released or live-qualified.

## Historical `.3` diagnosis and `.4` normalization

Updated **18 October 2026** after the operator-reported `.3` live diagnostic run.

The **0.2.0-i4b.3** run, digest
`sha256:05c8ccb44b3964b780d3ffcef9a71a89b80ed2a5b7f4de22806ea7b0f62cf626`,
remained **PARTIAL**. Test Connection authenticated, reported Proxmox VE **9.2.11**
and inventory capability **Ready**. Debug diagnostics successfully isolated the
only completeness warning: `storage_inventory_mismatch`, stage `storage_status`,
object `node/pve3`. This is operator-provided live evidence; `.3` remains failed,
unqualified evidence, with its immutable artifact unchanged.

The historical narrow compatibility successor was **0.2.0-i4b.4**, still **UNQUALIFIED** with
`qualified_versions: []`, archive digest
`sha256:62d25b92cf694dd7a8fde320961ccd887dc29b85497c084a44fab08fe1d7d645`.
No `.4` live qualification, production promotion or source qualification is claimed.

### Confirmed storage shape and contained normalization fix

The cluster has pve1, pve2 and pve3. pve1/pve2 use local-zfs on a ZFS SSD;
pve3 has only its system disk and uses LVM/LVM-thin. The applicable pve3 storage
configuration contains `local`, `synology-immich`, `synology-backup`,
`synology-vmdata`, `pbs-backup` and `local-lvm`. All six have node status rows.
Proxmox additionally returns `local-zfs`, type `zfspool`, `shared=0`, `enabled=0`,
`active=0` on pve3 despite there being no applicable pve3 definition or ZFS disk.

The old loop added every status ID to `seen` before checking configuration
applicability, so that extra row caused an unequal applicable-inventory set.
`.4` skips a status row only when **no configuration definition applies to that
node AND enabled and active are both explicitly false/0 AND both pass the existing
strict boolean validation**. Missing flags are not proof; strings, null, floats
and arbitrary values are not coerced. The skipped row enters neither the
applicable `seen` set nor Assets/storage lookup. Its normal diagnostic is
**Skipped / `storage_record_out_of_scope`**, with storage/node identity. Existing
debug fields explain the `inactive_disabled_without_applicable_definition` rule
and `action=skip`; no diagnostic schema, bounds or redaction change is required.

Applicable disabled/inactive storage remains inventory. Unknown/non-applicable
active or enabled storage still warns `storage_definition_missing` and prevents
COMPLETE. Missing applicable status still warns `storage_inventory_mismatch`;
malformed booleans, duplicate rows, type/shared inconsistencies, local capacity
validation and unresolved guest storage remain fail-closed. Local identity stays
node-scoped; shared identity stays source-level; guest relationship identity is
unchanged. No source call, privilege, Atlas/SDK code or global COMPLETE rule changes.

The original `.1`/`.2` findings and diagnostics introduced by `.3` follow.

The `.2` run, digest
`sha256:3dcf374e487a65a4398fe3ec2b3c0158c9fbdeaa5c8f885b85d8c3361904ffb5`,
was COMPLETED/PARTIAL: **179 observations**, **48 reconciliation items created**,
`invalid_source_record`. Its exists:null fix worked, but another independent
condition remained; `.3` subsequently isolated it as described above. Source flag
shapes and guest active bridge/storage references had already been checked by the
operator.

Structured diagnostics were introduced in **0.2.0-i4b.3** and are retained in `.4`.
Enable **debug for next discovery run** only as an administrator;
it is consumed when the run is created and expires within 48 hours. Normal safe
diagnostics are always enabled. Neither mode logs raw source bodies/config values
or changes calls, privileges, validation or completeness. See the
[diagnostic contract and checks](i4c-discovery-diagnostics.md).

The following preserves the original `.1` finding and the contained `.2` fix.
Proxmox **9.2.11 remains UNQUALIFIED**. Candidate **0.2.0-i4b.1** produced a
**PARTIAL** run (140 observations, `invalid_source_record`, no Bridge Assets).
No absence processing occurred. Source version was 9.2.11; runtime was
`atlas-ansible-i4a-v1` / 1.2.0, runtime 0.3.1. Guest interfaces still came from
current guest config. This is live operator evidence, not local test execution.

The legitimate separate VLAN row `vmbr0.99` contained `exists: null`. The raw
network validator incorrectly required that unused flag to be 0/1/bool, rejecting
the entire response before the valid `vmbr0` bridge could be normalized. The fix
removes only `exists` from that set; `active`, `autostart`, `bridge_vlan_aware`
remain strict. A regression preserves vmbr0 and adds the separate VLAN row.

The `.2` artifact remains failed live qualification evidence, still unqualified/unpublished. Version truth
is stored in the existing candidate Manifest/SPDX metadata, not a second build
configuration. The immutable `.1` artifact remains unchanged at
`sha256:d283441dfa70d8e589fd3da868075bdb795a8cda938a78931437432b572166c8`.
Production bootstrap/catalogue remain **0.1.0 probe-only**. I4/I4C are incomplete;
I4C-B, production activation, release and native/systemd LIVE acceptance remain
outstanding. No commit/push/merge/tag/publication is performed in this fix pass.

## Historical local `.4` validation — fixtures, not live qualification

The pinned native-style environment uses Python 3.14.7, SDK 1.1.0,
ansible-core 2.19.7, Runner 2.4.3, proxmoxer 2.3.0, requests 2.34.2 and the
reviewed community.proxmox 2.0.0 collection. Commands actually executed:

```bash
ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-i4c-diagnostics/collections ATLAS_TEST_RUN_ANSIBLE=1 /private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python -m pytest tests/test_proxmox_normalization.py tests/test_proxmox_discovery.py tests/test_discovery_diagnostics.py tests/test_i4c_checkpoint.py tests/test_proxmox_ansible.py -q --tb=short
ATLAS_TEST_COLLECTIONS_PATH=/private/tmp/atlas-i4c-diagnostics/collections ATLAS_TEST_RUN_ANSIBLE=1 /private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python -m pytest -q --tb=short
/private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python tools/build_bundle.py --candidate --output /private/tmp/atlas-i4c-storage-fix/candidate-a
/private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python tools/build_bundle.py --candidate --output /private/tmp/atlas-i4c-storage-fix/candidate-b
cmp /private/tmp/atlas-i4c-storage-fix/candidate-a/proxmox-0.2.0-i4b.4.tar.gz /private/tmp/atlas-i4c-storage-fix/candidate-b/proxmox-0.2.0-i4b.4.tar.gz
cmp /private/tmp/atlas-i4c-storage-fix/candidate-a/manifest.json /private/tmp/atlas-i4c-storage-fix/candidate-b/manifest.json
cmp /private/tmp/atlas-i4c-storage-fix/candidate-a/SHA256SUMS /private/tmp/atlas-i4c-storage-fix/candidate-b/SHA256SUMS
cmp /private/tmp/atlas-i4c-storage-fix/candidate-a/index.json /private/tmp/atlas-i4c-storage-fix/candidate-b/index.json
/private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python tools/verify_candidate.py --directory /private/tmp/atlas-i4c-storage-fix/candidate-a --expected-digest sha256:62d25b92cf694dd7a8fde320961ccd887dc29b85497c084a44fab08fe1d7d645
/private/tmp/atlas-i4c-diagnostics/runtime-venv/bin/python tools/build_bundle.py --output /private/tmp/atlas-i4c-storage-fix/final-production
cmp /private/tmp/atlas-i4c-storage-fix/original-production/proxmox-0.1.0.tar.gz /private/tmp/atlas-i4c-storage-fix/final-production/proxmox-0.1.0.tar.gz
git diff --check
```

Focused checks: **144 passed**. Full Connector suite: **209 passed, no skips**;
90 existing Runner `codecs.open` deprecation warnings. The ten actual Runner
cases include the three-node storage fixture with debug off and on. Coverage
proves the exact COMPLETE case; active/enabled unknown storage, malformed/missing
flags and missing applicable status remain PARTIAL; applicable disabled storage,
type/shared checks, capacity checks, duplicate detection and guest links retain
their required behavior. Debug modes produce identical AIP, relationships,
warnings, completeness and request sequences.

Both builds' archive, detached manifest, checksum file and index compare
byte-for-byte; the independent verifier accepts all 19 reviewed archive files.
The review copy is `dist/proxmox-candidate-0.2.0-i4b.4/`; previous output
directories were not overwritten. The builder already derives candidate identity
from Manifest/SPDX metadata; its checkpoint tests and the verifier now expect `.4`.

A separate compatibility audit ran the preserved `.3` archive code and `.4`
against the same sanitized three-node fixture: `.3` was PARTIAL with only
`storage_inventory_mismatch`; `.4` was COMPLETE. Both executed the same **52 source
requests in the same order**. Only the spurious pve3/local-zfs Asset was removed;
every remaining observation and relationship was identical. Atlas's unchanged
runtime/API diagnostic validators accepted the entire `.4` debug trace, with
one skipped row and zero warnings/errors.

Saved before/after SHA-256 audits confirm all **16 prior artifact files**
(archives, manifests, checksums and indexes) are unchanged. The default production
rebuild also matches all four pre-edit production output files byte-for-byte.

| Preserved archive | Unchanged SHA-256 |
| --- | --- |
| `0.2.0-i4b.1` | `d283441dfa70d8e589fd3da868075bdb795a8cda938a78931437432b572166c8` |
| `0.2.0-i4b.2` | `3dcf374e487a65a4398fe3ec2b3c0158c9fbdeaa5c8f885b85d8c3361904ffb5` |
| `0.2.0-i4b.3` | `05c8ccb44b3964b780d3ffcef9a71a89b80ed2a5b7f4de22806ea7b0f62cf626` |
| `0.1.0` probe-only | `b83ec2b3938b1747d12be5f0675dbc3e9da13c6259c2ab40f5daa994ee59ea60` |

All 804 tracked Atlas files and 16 tracked SDK files match their pre-edit hashes;
both worktrees remain clean at their starting HEADs. No database migration, API/UI
change, tenancy/authorization change, source privilege or secret handling change
was required. Shared packaged documentation remains frozen with production 0.1.0;
this runbook and the diagnostics document describe the current candidate.
Logs, compatibility evidence and hash audits are under
`/private/tmp/atlas-i4c-storage-fix/`. Nothing was committed, staged or pushed.
The only remaining step for this fix is operator review followed by a separate
clean-checkpoint `.4` live qualification. The later product decision now directs
the current procedure below to `.6` instead.

## Live review findings and qualification limits

- All Open silently truncated at 200; category queues could reveal items missing
  from that view. Atlas now uses bounded cursor pages with scoped totals and the
  Assets-style Previous / Page / Next footer. Reassess complete queue coverage.
- Initial namespaced facts appeared as independent Changed cards. They now group
  with their same-entity/source/run new Asset, with independent item actions.
  Prior claims, later facts and conflicts remain independent. The backend
  assertions, decisions, history and acceptance policy are preserved.
- Test Connection returned bounded capability diagnostics that the UI omitted.
  Atlas now renders the generic validated capability/state/path category and
  optional privilege, using shared status presentation. No raw ACL/body passthrough.
- Dynamic/DHCP/guest-agent/runtime IP enrichment remains deliberately omitted.
  Tagged/trunk attachments deliberately omit unsupported logical Network membership;
  guest-to-bridge connectivity must be reassessed after bridge discovery succeeds.
- The apparent five `uses_storage` relationships for roughly 30 LXCs are
  **unverified** historical `.1`–`.4` evidence because All Open was truncated.
  `.5` deliberately represents no storage dependencies and expects no uses_storage
  observations; it does not attempt to repair or erase those historical counts.
- Operator review changes `.2`'s recommended mapping for `proxmox.lxc` to the
  existing managed **LXC Container** key `lxc_container` (verified in Atlas's
  reference-data migration). `proxmox.qemu` still recommends `virtual_machine`.
  No taxonomy is created and no vendor-specific mapping moves into Atlas core.
  The `.2` Manifest supersedes the earlier `container` recommendation recorded
  in shared production discovery documentation. Current candidate docs now use
  `lxc_container`; the production docs stay frozen to preserve `0.1.0` bytes.
- New Asset headings now use their bounded observed name, retaining stable source
  external IDs. Guest subtitles such as `LXC 1008 · pve3` remain deferred because
  the current response has no generic presentation contract for those fields.
- The Discovery summary table uses the friendly source name and structured scope
  label, with separate connector/trigger and status/completeness lines. Technical
  identities remain in existing API/detail/provenance contexts.
- Archived-run reconciliation suppression is **not implemented**. Identical claims
  coalesce by replacing the latest run/evidence pointers, without per-assertion
  contributing-run links. The latest run can be archived while an older active
  run observed the same claim. A run-pointer-only filter would incorrectly hide
  that current work. Follow the operator's stop condition; retain existing archive,
  queue, acceptance and history semantics pending a scoped provenance design.

Perform **one operator action at a time**, inspect the result and record evidence
before continuing. Stop on identity mismatch, unsafe credential handling or an
unexpected COMPLETE claim. Do not make destructive infrastructure changes merely
to satisfy qualification. Use saved Atlas Integration credentials; never provide
the token secret to chat, Git, docs, reports, shell arguments or screenshots.

Read the current [discovery](../candidate/docs/discovery.md),
[capability matrix](../candidate/docs/capability-matrix.md),
[permissions](../candidate/docs/permissions.md),
[qualification status](../candidate/docs/qualification.md), and
the [I4C-A preparation report](i4c-a-preparation.md).

## 1. Local review gate — stop before commit/push

Review the Connector feature-branch diff and the historical Atlas
`docs/architecture/integrations/i4c-live-qualification-fixes.md` acceptance report.
Clean starting checkpoints for this contained MVP scope change are Connector
`a153d8804c89f5184e151cef51b5f9a961f20705` and read-only Atlas
`85d750b626cdfe772706a92d1f9678f26c5f4e97`. Atlas and atlas-connector-sdk are
unchanged. No new committed Connector checkpoint exists until the operator
separately reviews/authorizes it. Local builds carry contextual HEAD only and are
not committed-source or remote-attestation evidence.

After a separately reviewed operator checkpoint, record both full SHAs and rebuild
from those exact clean checkouts using the procedure below. Do not stage a dirty
Mac artifact, reuse `.1`, or overwrite an immutable artifact. This pass stops
before any commit/push, LXC staging, activation, source call or promotion.

## 2. LXC committed-source reconstruction

Use the existing isolated Atlas Docker test LXC and deployment checkout. Preserve
its environment, project, overrides, private volumes and saved credentials. Make
an existing Atlas backup before changing the test instance. Never apply this
procedure to production.

1. Set the two public commit variables to the SHAs recorded after Mac review:

   ```bash
   read -r -p 'Reviewed Atlas commit SHA: ' ATLAS_COMMIT
   read -r -p 'Reviewed Connector commit SHA: ' CONNECTOR_COMMIT
   ```

2. In the LXC's existing Atlas checkout, require a clean tree, fetch/switch the
   feature branch and fast-forward only. Refuse a mismatched SHA:

   ```bash
   git status --short
   test -z "$(git status --porcelain)"
   git fetch origin feature/integrations-i4c-proxmox-qualification
   git switch feature/integrations-i4c-proxmox-qualification
   git pull --ff-only origin feature/integrations-i4c-proxmox-qualification
   test "$(git rev-parse HEAD)" = "$ATLAS_COMMIT"
   export ATLAS_BUILD_ID="$ATLAS_COMMIT"
   ```

3. Obtain the Connector checkout (clone once if absent):

   ```bash
   git clone --branch feature/i4c-proxmox-qualification https://github.com/benchristian88/atlas-connectors.git ~/atlas-connectors-qualification
   ```

   For an existing checkout instead use `git status --short`, the same clean-tree
   check, `git fetch`, `git switch` and `git pull --ff-only` for
   `feature/i4c-proxmox-qualification`. Never reset/discard local work. Then:

   ```bash
   cd ~/atlas-connectors-qualification
   test "$(git rev-parse HEAD)" = "$CONNECTOR_COMMIT"
   test -z "$(git status --porcelain)"
   ```

4. Use Python 3.12+ and the exact pinned SDK wheel from this committed checkout.
   Build-only tooling does not need a live collection or source credentials:

   ```bash
   python3 -m venv .venv
   .venv/bin/python -m pip install 'jsonschema[format-nongpl]==4.25.1'
   .venv/bin/python -m pip install --no-index --no-deps --require-hashes --find-links vendor/sdk -r vendor/sdk/requirements.txt
   .venv/bin/python tools/build_bundle.py --candidate --output /tmp/i4c-candidate-a
   .venv/bin/python tools/build_bundle.py --candidate --output /tmp/i4c-candidate-b
   cmp /tmp/i4c-candidate-a/proxmox-0.2.0-i4b.6.tar.gz /tmp/i4c-candidate-b/proxmox-0.2.0-i4b.6.tar.gz
   cmp /tmp/i4c-candidate-a/manifest.json /tmp/i4c-candidate-b/manifest.json
   cmp /tmp/i4c-candidate-a/SHA256SUMS /tmp/i4c-candidate-b/SHA256SUMS
   cmp /tmp/i4c-candidate-a/index.json /tmp/i4c-candidate-b/index.json
   ```

5. Independently inspect the candidate, including clean committed-source identity:

   ```bash
   export CONNECTOR_ID=proxmox
   export CANDIDATE_VERSION=0.2.0-i4b.6
   export CANDIDATE_FILE=proxmox-0.2.0-i4b.6.tar.gz
   export CANDIDATE_DIGEST=sha256:dd3b7fa5ebc7e47dd3c4607d631d87f50ef3eef3f6add7fff63e10fe721bea97
   export CANDIDATE_DIR=/tmp/i4c-candidate-a
   .venv/bin/python tools/verify_candidate.py --directory "$CANDIDATE_DIR" --expected-digest "$CANDIDATE_DIGEST" --source-commit "$CONNECTOR_COMMIT"
   cd "$CANDIDATE_DIR"
   sha256sum -c SHA256SUMS
   ```

   Require all comparisons/checks to pass. This is the new `.6` archive digest;
   detached provenance must identify the separately reviewed new Connector SHA.
   Its release URLs are schema descriptors, not published assets/attestations.
   Do not use an uncommitted Mac bundle or overwrite a mismatch with a new digest.

## 3. Exact staging and runtime identity

Return to the Atlas checkout. Follow
`docs/deployment/connector-qualification.md` **one action at a time**, using the
reviewed variables above. Its canonical command is
`python -m scripts.qualify_connector` with `stage`, `plan`, `activate`, `revoke`.
Append the committed `infra/docker/docker-compose.qualification.yml` override;
no production bootstrap/catalogue file is edited. Use the separate test store.

Before activation, preview with `--scope inventory`. Resolve required mappings
through explicit managed reference choices and `--mappings` as described there.
Require exactly four Asset and two relationship mappings from the current
Manifest; no bridge/network_bridge, connected_to/connected_via or storage choices. Do not alter global taxonomy.
Seed labels are not stable semantics: inspect actual active target keys and
relationship directions/allowed types. With current unchanged taxonomy, only
`proxmox.cluster → proxmox_cluster` needs an explicit override; node/QEMU/LXC and
member_of/runs_on exact-auto-map. Inspect the actual preview before activation. Never ignore a
required class or change relationship meaning to force activation. Repeat the
read-only plan until all required mappings resolve and configuration is ready.
Then activate using those same reviewed scope/mapping arguments. Retain saved
credentials/DataSource; activation resets Test Connection status and source version.

For this candidate, keep the selections in a public argument array and use the
explicit existing installer UID/GID, even if the API account's primary group differs:

```bash
qualification_options=(--scope inventory)
"${dcq[@]}" exec -T --user 10001:10001 api python -m scripts.qualify_connector plan "${checkpoint[@]}" "${qualification_options[@]}"
```

If the preview needs explicit mapping choices, prepare the reviewed local JSON
file as described by the Atlas procedure, copy it to the temporary input directory
and make that non-secret file readable by the installer. Append it to the same
options and repeat the preview:

```bash
qualification_options+=(--mappings /tmp/qualification-input/mappings.json)
"${dcq[@]}" exec -T --user 10001:10001 api python -m scripts.qualify_connector plan "${checkpoint[@]}" "${qualification_options[@]}"
```

Only after all required mappings resolve and dependent configuration is ready:

```bash
"${dcq[@]}" exec -T --user 10001:10001 api python -m scripts.qualify_connector activate "${checkpoint[@]}" "${qualification_options[@]}"
```

Record (no source credentials/raw ACLs):

| Identity | Required value/evidence |
| --- | --- |
| Atlas commit | Full reviewed Mac/pushed/LXC SHA; API build identity matches |
| Connector commit | Full reviewed Mac/pushed/LXC SHA; detached manifest agrees |
| Candidate | `0.2.0-i4b.6`, exact SHA-256 above, still unqualified |
| Runtime | healthy `atlas-ansible-i4a-v1` / `1.2.0`, runtime `0.3.1` |
| Ansible | core `2.19.7`, Runner `2.4.3` |
| Client | proxmoxer `2.3.0` |
| Collection | compatible `community.proxmox` `2.0.0`, archive digest `77e02e0d1e341c6b064900fe58484ad8880cee4832f5fd65d09834ed068216f6` |
| Contracts | SDK `1.1.0`, AIP `1.0` |
| Authority | `operator-qualification`, exact grant/expiry, runtime independent verification |
| Production | catalogue/bootstrap still `0.1.0`; original store retained |

Require runtime `verify_connector` to accept the exact candidate; the activation
command invokes this existing authenticated private path before database activation.
Inspect installed identity through the normal global runtime-view UI/API. Do not
print runtime-control credentials or call source APIs from Atlas core.

## 4. Readiness and first real discovery

1. In the saved authorized Integration, run **Test Connection**. Record sanitized
   category, source version and capability diagnostics. Require source still reports
   **9.2.11**; if it differs, stop and establish actual package/API identity with the
   operator. Authentication/version success alone does not prove readiness.
2. Check discovery readiness diagnostics. Missing privilege reports are bounded
   identifiers and generic path categories (maximum 16); no raw ACL/source bodies.
   Review backing-user **and** privilege-separated token grants/intersection. Check
   `Sys.Audit` on `/access` for an **unfiltered** `/access/acl` proof. Do not grant
   root, allocation or write privileges to bypass readiness. A restricted token can
   legitimately yield PARTIAL. Record its bounded reason and retain qualification
   status as unqualified.
3. Leave scheduling **Manual**. Select `inventory`, then **Run Now** through normal
   I3 UI/orchestration. Record Integration/DataSource/run IDs, trigger, package
   version/digest, runtime baseline, source version, status, counts, warnings and
   COMPLETE/PARTIAL/failed seal. Confirm actual isolated Ansible Runner and AIP
   ingestion using run provenance and sanitized orchestration evidence. Never enable
   raw source/ACL/Ansible event logging or expose tokens to prove execution.
   Confirm no storage-pool Assets, uses_storage relationships, storage capacity
   facts or storage diagnostics are emitted on any node, and no storage inventory
   calls execute. Host bridge Interfaces and guest Interfaces must remain. Verify guest bridge_name,
   MAC and explicit VLAN 99/static IP evidence; require no bridge Assets or connected_to
   Asset relationships. Tagged/trunk Interfaces must not inherit a bridge Network.
   Compare against `.5`'s 136 only by counting removed bridge Assets/connected_to
   links or recording genuine live source changes; never hard-code 136 for `.6`.
   COMPLETE requires every remaining declared capability/proof; retain real warnings.
4. Review observations/evidence/reconciliation in the correct Customer/Site before
   accepting any new knowledge. Acceptance remains an explicit operator action.
   Confirm no cross-tenant observations and no silent overwrite of curated values.

## 5. Inventory and topology where present

Compare with the operator's read-only source view and record present/absent/not
applicable/untested for each class. An environment lacking a class does not qualify
that class. Check cluster versus standalone (no fake standalone cluster), nodes,
QEMU, LXC, templates, host bridge Interfaces and explicit Networks.
Check node→cluster `member_of`, guest→node `runs_on`, direction and target identity.
Check guest `proxmox.bridge_name` against an active bridge on its own node,
`proxmox.vlan_tag` against configured VLAN (including 99), and canonical MAC/static IP.
There must be no bridge Assets or connected_to Asset relationships. Review VLAN/trunk
and subnet exclusions; do not infer unsupported logical membership or unknown IPs.
Record node-renaming, source-replacement and VMID-reuse identity limitations.

## 6. COMPLETE / PARTIAL hard gate

COMPLETE requires **all** of: mandatory source calls succeeded; selected required
scope/classes executed; positively proven ACL visibility; unfiltered `/access/acl`;
hidden relevant NoAccess overrides ruled out; stable source membership/placement;
no mandatory node/source failure, offline node uncertainty, staging/pending-config
ambiguity, malformed required records, limit breach or unresolved topology.
Compare before/after inventory and ACL proof. HTTP 200 plus an empty inventory is
never completeness evidence. Any uncertainty must be **PARTIAL** (or failed for a
mandatory top-level failure); PARTIAL must never invoke unsafe absence.

Plan observations for missing user/token grants, hidden NoAccess, denied mandatory
calls, naturally offline nodes, existing pending/staged configuration, malformed
responses and limits. Do not shut down nodes, alter production configuration or
inject malformed source data just to fill this checklist. Cases that cannot be
safely produced remain **untested**, with fixture evidence clearly distinguished.
After an explicitly accepted COMPLETE baseline, run a safely restricted PARTIAL
case where feasible and confirm accepted Assets/source links are preserved and
there are no absence-based reconciliation conclusions. No actual removal required.

## 7. Repeatability and safe negatives

Repeat unchanged discovery with **Debug Off** after the first Debug On run. Compare retained object/link IDs, relationship
identities/endpoints, stable membership/topology and duplicate counts; volatile
metrics may change. Review evidence/history continuity. No automatic acceptance.

Use a **separate disposable test Integration** and dedicated test token for
invalid-credential/missing-permission cases, entered only in the normal protected
UI. Never damage or print the saved valid credentials. Test fingerprint mismatch
using a separate non-secret trust configuration; require failure before credentials
are transmitted and no insecure fallback. For source unavailability use a safe
unreachable test endpoint **before** successful history; do not repoint an established
DataSource. Test a hidden NoAccess override only on a disposable token/user where
the operator can safely grant and revoke it. Confirm bounded redacted failures.
No redirect/proxy/DNS/ACL mutation of production infrastructure is required.

## 8. Optional mutations — explicit operator choice only

Guest rename, migration, disposable-object removal and re-observation require
separate explicit operator choice. Use a disposable object and preserve evidence
of identities/history/placement; do not delete accepted Atlas knowledge. Do not make
destructive infrastructure changes merely to satisfy qualification. If declined,
mark these live scenarios untested, retaining the existing fixture evidence.

## 9. Evidence and stopping gate

For each action record date, exact checkpoint, safe expected/actual result and
pass/fail/untested/not-applicable. Keep local inventories private as appropriate.
Never retain source secrets/raw ACLs/source bodies. Separate actual live evidence
from fixture expectations. Stop on mismatches; fixes require a new reviewed Git
checkpoint and rebuilt digest. Do not weaken I4B COMPLETE/security behavior.

Disable/settle test jobs and revoke permission using the Atlas procedure when
finished; its 48-hour expiry independently prevents new execution. This fix pass ends at
local review readiness, before commit/push. Even successful individual live checks do
not themselves change metadata or authorize I4C-B promotion, merge, release,
bootstrap replacement or production discovery/scheduling/complete snapshots.
