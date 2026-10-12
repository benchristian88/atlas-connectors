# Proxmox VE connection probe 0.1.0

This Manifest 1.1 package implements **Test Connection only**. It advertises
`discover: false`, has no executable discovery entry point, no inventory classes,
no AIP output, no scheduling and no source versions claimed as qualified.

Use a dedicated API token with Privilege Separation. The token ID and secret
are both write-only credentials. Password, SSH and root/admin login workflows
are unsupported. The probe reads only `GET /api2/json/access/permissions` for
its own token and `GET /api2/json/version`. It returns authentication category,
a bounded source version and limited-permission indication; it does not
enumerate nodes, guests, storage, networks or other inventory.

The current [Proxmox access-control API source](https://github.com/proxmox/pve-access-control/blob/master/src/PVE/API2/AccessControl.pm)
allows users/tokens to query their own effective permissions. This was checked
on 12 October 2026 for the two-call probe, not the I4 discovery qualification.
Least-privilege inventory ACLs and the full external-reference/edge-case review
remain I4 work. No live Proxmox environment has been qualified here.

I4A dependency groundwork and its dated exact-artefact review are documented in
the [capability matrix](docs/capability-matrix.md), proposed
[permissions](docs/permissions.md) and [qualification status](docs/qualification.md).
This does not enable discovery or qualify Proxmox 9.2.11.

The separate [I4B candidate](docs/discovery.md), **0.2.0-i4b.1**, now implements
fixture-proven secured discovery under `candidate/manifest.json`. It remains
unqualified, unpublished and rejected by normal Atlas activation. The production
0.1.0 manifest/probe and Atlas bootstrap are retained. See the
[candidate report](docs/i4b-completion-report.md) for validation and live gates.

HTTPS verifies certificates by default. Fingerprint mode checks a trusted
SHA-256 leaf-certificate pin **before sending credentials**. Advanced insecure
mode is explicit and warned by Atlas. Redirects are never followed. DNS results
are vetted then pinned to the socket peer, while retaining hostname/SNI checking.
Private LAN/ULA sources are supported; loopback, link-local, multicast,
unspecified/reserved and known cloud-metadata addresses are blocked.
The runtime's total deadline also bounds DNS resolution; connection/read timeouts
and a 128 KiB response ceiling bound individual calls.

The verified playbook passes only private runtime input/output paths to an
Atlas-authored local Ansible module. Credential data bypasses Ansible templating
and events. The runtime removes that workspace and terminates its child process
group on every terminal outcome. Ansible remains a separately licensed runtime
dependency; its licences/notices live with the runtime distribution.
