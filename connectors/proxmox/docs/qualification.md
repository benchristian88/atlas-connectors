# Proxmox qualification status

As of **12 October 2026**, Connector **0.1.0** remains **probe-only**:
Test Connection enabled; discovery, scheduling and complete snapshots disabled;
no discovery entry point; no collection dependencies in the production manifest.
**Proxmox 9.2.11 remains UNQUALIFIED. I4 is not complete.**

I4A reviews and packages community.proxmox 2.0.0 in the Atlas-owned runtime,
baseline `atlas-ansible-i4a-v1` / 1.2.0, runtime 0.3.1, retaining Ansible core
2.19.7 and runner 2.4.3. The [matrix](capability-matrix.md) records the exact
archive digest, shipped module calls, ACL implications and capability gaps.
[Permissions](permissions.md) is a source-derived proposal awaiting live proof.

Package/unit tests, `pip check`, collection listing and offline source-call
inspection validate the dependency groundwork. They do not establish native
Debian/systemd LIVE acceptance, source transport safety or source-version
qualification. Python 3.12 Docker validation and a local native-style environment
must be reported separately from live product acceptance.

Remaining I4 gates include a contained discovery implementation using existing
I3 orchestration; preservation of probe transport protections through actual
collection calls; effective ACL/visibility proof; offline-node and per-domain
failure isolation; storage-status fallback review; optional guest-IP isolation;
identity/migration/storage collision fixtures; and dated source-version live
acceptance. No fallback client, production discover.yml, atlas_discover.py,
0.2.0 production bundle or release is introduced by I4A.

SDK 1.1.0 and AIP 1.0 remain unchanged. The current production manifest stays
dependency-free so existing 0.1.0 probes remain usable on I1–I3 baselines. Exact
collection compatibility is exercised with test manifests in Atlas until a
future discovery Connector genuinely requires that dependency.
