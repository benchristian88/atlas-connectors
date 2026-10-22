# Ruleset bypass visibility experiment

This isolated manual experiment checks whether verifier App **5424851**, installation
**174088125**, can retrieve explicit `bypass_actors` evidence for exactly five
repository rulesets. Local tests do not establish live GitHub visibility.

The workflow is `.github/workflows/ruleset-visibility-experiment.yml`. It accepts
only `workflow_dispatch`; its job runs only in `benchristian88/atlas-connectors`
from `refs/heads/main`, using environment `catalogue-verification`. Dispatching
another ref skips the job. A future live run requires both workflow and helper
on main. This implementation does not merge, commit, push or dispatch anything.

The environment must provide variables `VERIFICATION_APP_ID=5424851` and
`VERIFICATION_APP_INSTALLATION_ID=174088125`, and secret
`VERIFICATION_APP_PRIVATE_KEY`. The helper checks configuration and independently
checks the repository installation identity before minting a token.

## Permissions and HTTP boundary

The verifier token requests only **Administration write** and GitHub's mandatory
**Metadata read**, scoped to `atlas-connectors`. GitHub documents that
[`bypass_actors` requires write access to the ruleset](https://docs.github.com/en/rest/repos/rules#get-a-repository-ruleset).
Administration read alone must not be assumed to expose complete evidence.
No Contents, Actions, Workflows or publication permission is requested for this token.

The workflow's separate `GITHUB_TOKEN` has only Contents read, to fetch the helper
through the Contents API at the exact dispatched commit SHA. There is no checkout,
Git command, package installation, third-party action or reusable workflow call.
Python 3 and OpenSSL are supplied by the Ubuntu runner. The isolated helper uses
OpenSSL to sign the App JWT; private key bytes are held in a temporary mode-0600
file during signing and removed immediately afterward. Subprocess output is captured.

Every API request sets `X-GitHub-Api-Version: 2022-11-28`. The only non-GET request
is the explicitly authorized authentication exception:

```text
POST /app/installations/174088125/access_tokens
```

Its body specifies the single repository and exact permissions above. It is not
retried. The token stays in process memory and expires naturally; there is no
DELETE revocation. The remaining requests are:

```text
GET /repos/benchristian88/atlas-connectors/contents/tools/ruleset_visibility.py?ref=<dispatch SHA>
GET /repos/benchristian88/atlas-connectors/installation
GET /repos/benchristian88/atlas-connectors/rulesets?includes_parents=true&per_page=6&page=1
GET /repos/benchristian88/atlas-connectors/rulesets/<ID>?includes_parents=true
```

The final request runs once for each of the five listed IDs. Redirects are rejected.
There are no requests that change releases, tags, refs, branches or settings, and
no publication imports, credentials, policy access, artifacts or workflow calls.
The credential has write capability because GitHub requires it for visibility;
the implemented request paths do not exercise that capability. This is not a
claim that an Administration-write token is technically incapable of mutation.

## Fail-closed evidence and diagnostics

Exactly five unique expected names and unique positive integer IDs are required.
Both list and detail records must identify this repository; detail IDs/names must
match the list. Inherited or unexpected rulesets are not silently excluded.
The page size is six to detect overflow, but only five results are accepted.
Any Link header (including empty/malformed links) is rejected; no pagination is
followed. JSON bodies are bounded to 256 KiB, duplicate JSON keys and non-finite
constants are rejected, and status, encoding, length and evidence shape are checked.

The helper fetches all five details and requires the exact bypass lists before
printing any successful diagnostics. The three lock/main rules require `[]`;
the other two require exactly App **5422372**, type **Integration**, mode **always**,
matching the existing publication contract. Empty, absent and malformed bypass
evidence are distinct: absence fails with `ruleset_bypass_missing`; malformed or
unexpected actors fail with `ruleset_bypass_mismatch`. All existing identity,
permission, repository-selection, count, field-presence and exact-comparison checks
remain enforced.

On failure the helper exits 1 and writes exactly one allowlisted identifier plus
a newline to stderr. No ruleset JSON is printed on a validation failure. It never
prints remote response bodies, exception text, stack traces, authorization headers,
JWTs, tokens or private keys. Even unexpected exceptions use a fixed fallback code.
The failure identifiers distinguish stages without exposing remote data:

| Identifier | Failed stage |
| --- | --- |
| `verifier_context_failed` | Dispatch event, main ref or repository context |
| `verifier_configuration_failed` | Configured App/installation IDs or missing private key |
| `verifier_jwt_failed` | App JWT creation, including OpenSSL signing |
| `verifier_installation_failed` | Installation lookup, response parsing or identity/selection validation |
| `verifier_token_failed` | Token minting, response parsing or permission/repository/token validation |
| `ruleset_list_failed` | List retrieval, response parsing or exact count/name/ID/source validation |
| `ruleset_detail_failed` | Any individual detail retrieval, response parsing or detail identity/shape validation |
| `ruleset_bypass_missing` | A detail response lacks the explicit `bypass_actors` field |
| `ruleset_bypass_mismatch` | Malformed bypass actors or a list that differs from the exact expectation |
| `verifier_unexpected_failed` | An unexpected failure outside the named stages |

For example, a token HTTP error and an invalid token permission set both produce
only `verifier_token_failed`, without a status, response body or exception string.
The workflow's helper-download bootstrap is unchanged; these codes apply once
execution has reached the helper. This diagnostic change alone does not establish
which stage failed in an earlier live run.

A successful helper exits 0 and prints these five JSON lines in this order.
`<..._ID>` denotes the actual numeric ID returned by GitHub, not a literal output
value. IDs are intentionally not invented or pinned from an unperformed live run.
GitHub Actions also supplies its normal step/status logs.

```text
{"name":"atlas-main","id":<MAIN_ID>,"bypass_actors_present":true,"bypass_actor_count":0,"bypass_actors":[]}
{"name":"atlas-history-lock","id":<HISTORY_ID>,"bypass_actors_present":true,"bypass_actor_count":0,"bypass_actors":[]}
{"name":"atlas-bootstrap-lock","id":<BOOTSTRAP_ID>,"bypass_actors_present":true,"bypass_actor_count":0,"bypass_actors":[]}
{"name":"atlas-catalogue-current","id":<CURRENT_ID>,"bypass_actors_present":true,"bypass_actor_count":1,"bypass_actors":[{"actor_id":5422372,"actor_type":"Integration","bypass_mode":"always"}]}
{"name":"atlas-publication-tags","id":<TAGS_ID>,"bypass_actors_present":true,"bypass_actor_count":1,"bypass_actors":[{"actor_id":5422372,"actor_type":"Integration","bypass_mode":"always"}]}
```

This experiment validates bypass visibility and the specified actor expectations.
It does not certify every protection rule, historical enforcement or publication
readiness, and does not replace the existing publication verifier.

## Local validation

```bash
.venv/bin/python -m pytest -q tests/test_ruleset_visibility.py tests/test_publication_packaging.py::test_workflows_have_explicit_security_boundaries
actionlint .github/workflows/ruleset-visibility-experiment.yml
git diff --check
```

Tests use synthetic responses and an ephemeral generated RSA key. They exercise
the helper download, JWT signature, installation binding, narrowed mint request,
GET-only evidence client, exact expectations, unsafe/malformed/ambiguous responses,
safe stage-specific failures, unchanged successful output, main-only dispatch
context and workflow contract. Injected subprocess, HTTP, malformed-body and
unexpected errors prove sensitive error content does not reach diagnostics. No live App
credentials or network requests are needed. YAML syntax is also parsed locally.
