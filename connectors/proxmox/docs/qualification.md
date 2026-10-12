# Proxmox qualification status

As of **12 October 2026**, production Connector **0.1.0** remains **probe-only**:
Test Connection enabled; discovery, scheduling and complete snapshots disabled;
no discovery entry point or collection dependency in its production manifest.
**Proxmox 9.2.11 remains UNQUALIFIED. I4 is not complete.**

I4A's runtime baseline remains `atlas-ansible-i4a-v1` / **1.2.0**, runtime **0.3.1**,
community.proxmox **2.0.0**, proxmoxer **2.3.0**, ansible-core **2.19.7** and
ansible-runner **2.4.3**. SDK **1.1.0** and AIP **1.0** remain unchanged.
The [capability matrix](capability-matrix.md) preserves its dated source review.

I4B now implements **0.2.0-i4b.1** as an explicit, unqualified candidate under
`candidate/manifest.json`, with fixed discovery, secured collection reuse,
normalization, bounded facts/topology, ACL proof and completeness rules. See
[implemented discovery](discovery.md) and the [completion report](i4b-completion-report.md).
`tools/build_bundle.py --candidate` builds it separately. Normal Atlas activation
rejects the unqualified candidate; no production catalogue/bootstrap is replaced.
No Connector release is published, activated, merged or source-qualified by I4B.

Fixtures exercise actual Ansible Runner and canonical SDK validation. Atlas's
separate `i4b-fixture` package uses candidate code with a test-only source adapter;
its synthetic `fixture-only` qualification is unrelated to Proxmox. The real
candidate manifest remains unqualified and production-rejected. Tests do not
qualify actual APIs, permissions, source topology or performance.

Remaining source qualification scenarios are listed in [discovery](discovery.md).
Native Debian/systemd LIVE acceptance remains outstanding. Python 3.12 Docker
fixture validation and local native-style validation are evidence for the candidate
implementation only. Production bootstrap stays 0.1.0 until live I4 acceptance
and a separately authorized qualified release.
