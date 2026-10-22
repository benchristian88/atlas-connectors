# P1 verified starting state

Inspected 22 October 2026, before implementation. Scope: atlas-connectors only.
Branch: `feature/immutable-catalogue-publication`.
Starting HEAD: `83339e1747dc651ccdbdf4ab9ca8d4bc91d8c831`; clean worktree.
Adjacent Atlas HEAD: `41e615d8aaf90ecbd81456641a0968f0db1bd2b0` on `dev`, read only.

## Checked-in implementation

- `tools/build_catalogue.py` already validates the six-field v1 envelope,
  canonical SDK 1.1.0 combined Manifests, exact official identities, literal safe
  integers, duplicate keys, 200 entries, 256 KiB entries and 4 MiB aggregates.
  Sequence comes from `catalogue/sequence.txt`; no remote allocation/history gate.
- `catalogue.yml` prepares, attests and uploads; it does not publish.
  Its signer is `.github/workflows/catalogue.yml@refs/heads/main`.
- `release.yml` prepares tagged Proxmox releases only. The deterministic builder
  contains a Proxmox allowlist and hardcoded distribution filenames. Candidate
  packaging must preserve its historical bytes. Qualification is recorded in
  source-version metadata and reviewed connector documentation; fixture success
  does not qualify a connector.
- No repository AGENTS.md, ADR directory or publication authority policy existed.
  Tests cover catalogue structure/determinism/history fixtures, Markdown links,
  SDK contracts and Proxmox runtime/Ansible regressions.
- Atlas B1.1 validates declarations, not trust. B1.2 uses pinned gh 2.102.1 and
  frozen Sigstore roots. Catalogue and package certificate profiles differ.
  Numeric repository/owner IDs are 1414494920 / 93822871; issuer is GitHub Actions;
  hosted runner, SLSA v1, source ref/commit and original byte digests are checked.
- Atlas B1.3 reads legacy catalogue-v1 but rejects `publication_not_immutable`
  and then `current_channel_policy_unavailable`; no bypass exists. Persistence
  preserves highest sequence/digest, historical identities and withdrawal state.
  ADR 0011 distinguishes provenance from publication authority. No Atlas change
  is made here. Its publication prerequisite plan remains unsatisfied live.

## Read-only GitHub observations

Public REST GET observations (no credentials or mutations):

| Resource | Observation |
| --- | --- |
| Repository | Public, personal owner, default branch main; IDs match B1.2 |
| `/branches/main` | HEAD matches local starting HEAD; protected=false |
| `/rulesets` | Empty list |
| `/environments` | connector-release ID 24617213627; protection_rules=[]; deployment_branch_policy=null; can_admins_bypass=true |
| `/releases/tags/catalogue-v1` | Release 416561696, immutable=false |
| `/releases/tags/proxmox-v0.2.0` | Release 416290807, immutable=false |
| `/immutable-releases` | HTTP 401 anonymously; admin-read endpoint; setting not established |

The repository connector confirmed public visibility and IDs. It does not expose
all environment/settings operations, so bounded anonymous REST GETs were used.
The account billing plan is not public and was not inferred. Required reviewers,
self-review prevention and branch/tag rulesets are documented as available for
public repositories on current Free/Pro/Team plans. Legacy plans are excluded.
Availability is not configuration, nor proof of an approval event.

## Frozen historical evidence

Sequence 1: 10,585 bytes, SHA-256
`55533ca67e7e9a14f82961e0a8c34ad78e2596049b3db02fde787494e3975afd`;
source `91dfd86f18d0b59ff977bb1e8a5fef42c5329943`, attestation 57152061.
The two existing remote JSON assets and checked-in fixtures must remain unchanged.
Atlas has genuine catalogue/package Sigstore bundles and pinned roots available
for read-only compatibility verification. Neither legacy release is immutable.
Existing README descriptions of immutable tags/assets overstate provider state.

## Feasibility findings

A protected branch or Git commit signature is not B1.2 provenance. Use a distinct
Sigstore profile for exact current.json bytes, with independently configured
signer and approval policy. A non-force single-parent Git ref update provides a
compare-and-swap by ancestry; reread the ref before and after publication.

GitHub's public workflow review-history API exposes approval users/environments
but does not bind reviews to individual rerun attempts. Restrict publication to
first attempts; recovery uses a fresh approved run. Approval remains GitHub API /
policy evidence, not a human cryptographic signature. Anonymous live API
currentness plus persisted high-water marks cannot prove global freshness during
withholding or after loss of all local history. No expiry is added to v1.

The repository-wide `/releases/latest` selector lacks compare-and-swap, mixes
package and catalogue releases, and is mutable even for immutable releases.
Reject it as the authority/current channel. A dedicated branch requires an
owner-configured GitHub App with narrowly scoped bypass for that ref; ordinary
GITHUB_TOKEN is not assumed to bypass protection. No publication App identity or enforced publication policy was established by these reads.

References: [immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases),
[enable immutability](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes),
[environment API](https://docs.github.com/en/rest/deployments/environments),
[review history](https://docs.github.com/en/rest/actions/workflow-runs#get-the-review-history-for-a-workflow-run),
[rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository).

A further read-only check of the starting commit's check-runs identified the
successful `validate` check as GitHub Actions App **15368**. The supported ruleset
requires that integration identity, not an unbound check-context name.
