# I4C — Proxmox live qualification

Updated **13 October 2026** after the operator-reported first live run.
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

The next artifact is **0.2.0-i4b.2**, still unqualified/unpublished. Version truth
is stored in the existing candidate Manifest/SPDX metadata, not a second build
configuration. The immutable `.1` artifact remains unchanged at
`sha256:d283441dfa70d8e589fd3da868075bdb795a8cda938a78931437432b572166c8`.
Production bootstrap/catalogue remain **0.1.0 probe-only**. I4/I4C are incomplete;
I4C-B, production activation, release and native/systemd LIVE acceptance remain
outstanding. No commit/push/merge/tag/publication is performed in this fix pass.

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
  **unverified**, because All Open was truncated. Storage discovery is unchanged.
  Reassess source coverage after paging and a COMPLETE `.2` run.
- Operator review changes `.2`'s recommended mapping for `proxmox.lxc` to the
  existing managed **LXC Container** key `lxc_container` (verified in Atlas's
  reference-data migration). `proxmox.qemu` still recommends `virtual_machine`.
  No taxonomy is created and no vendor-specific mapping moves into Atlas core.
  The `.2` Manifest supersedes the earlier `container` recommendation recorded
  in shared packaged discovery documentation; those shared files remain frozen
  to preserve production `0.1.0` bytes.
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

Read [discovery](discovery.md), [capability matrix](capability-matrix.md),
[permissions](permissions.md), [qualification status](qualification.md), and
the [I4C-A preparation report](i4c-a-preparation.md).

## 1. Local review gate — stop before commit/push

Review both feature-branch diffs and the Atlas
`docs/architecture/integrations/i4c-live-qualification-fixes.md` acceptance report.
Starting accepted checkpoints are Connector
`76af2507bd29934192d1d89428a618d081e4f4a0` and Atlas
`efde1d7b7a6bbb4f9098b1f7d228e4b834d096b4`. No new committed checkpoint exists
until the operator separately reviews/authorizes it. Local builds carry contextual
HEAD only and are not committed-source or remote-attestation evidence.

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
   cmp /tmp/i4c-candidate-a/proxmox-0.2.0-i4b.2.tar.gz /tmp/i4c-candidate-b/proxmox-0.2.0-i4b.2.tar.gz
   cmp /tmp/i4c-candidate-a/manifest.json /tmp/i4c-candidate-b/manifest.json
   ```

5. Independently inspect the candidate, including clean committed-source identity:

   ```bash
   export CONNECTOR_ID=proxmox
   export CANDIDATE_VERSION=0.2.0-i4b.2
   export CANDIDATE_FILE=proxmox-0.2.0-i4b.2.tar.gz
   export CANDIDATE_DIGEST=sha256:3dcf374e487a65a4398fe3ec2b3c0158c9fbdeaa5c8f885b85d8c3361904ffb5
   export CANDIDATE_DIR=/tmp/i4c-candidate-a
   .venv/bin/python tools/verify_candidate.py --directory "$CANDIDATE_DIR" --expected-digest "$CANDIDATE_DIGEST" --source-commit "$CONNECTOR_COMMIT"
   cd "$CANDIDATE_DIR"
   sha256sum -c SHA256SUMS
   ```

   Require all comparisons/checks to pass. This is the new `.2` archive digest;
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
Seed labels are not stable semantics: inspect actual active target keys and
relationship directions/allowed types. In particular cluster/bridge recommended
keys may need deliberate selection of existing local taxonomy. Never ignore a
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
| Candidate | `0.2.0-i4b.2`, exact SHA-256 above, still unqualified |
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
4. Review observations/evidence/reconciliation in the correct Customer/Site before
   accepting any new knowledge. Acceptance remains an explicit operator action.
   Confirm no cross-tenant observations and no silent overwrite of curated values.

## 5. Inventory and topology where present

Compare with the operator's read-only source view and record present/absent/not
applicable/untested for each class. An environment lacking a class does not qualify
that class. Check cluster versus standalone (no fake standalone cluster), nodes,
QEMU, LXC, templates, shared/local storage, bridges and supported Networks/Interfaces.
Check node→cluster `member_of`, guest→node `runs_on`, guest→storage `uses_storage`,
node/guest→bridge `connected_to`, direction and target identity. Review VLAN/trunk
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

Repeat unchanged discovery. Compare retained object/link IDs, relationship
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
