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

The helper fetches all five details, prints only validated diagnostic fields,
then requires the exact bypass lists. The three lock/main rules require `[]`;
the other two require exactly App **5422372**, type **Integration**, mode **always**,
matching the existing publication contract. Empty, absent and malformed bypass
evidence are distinct: an absent field produces `bypass_actors_present:false`
and null count/actors, then fails. Well-formed unexpected actors can be printed
as safe IDs/types/modes before failing. Unrecognized actor strings, raw API bodies,
exception messages, authorization headers, JWTs, tokens and keys are never printed.
Malformed evidence or transport/authentication failures exit 1 without raw errors.

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
safe diagnostics, main-only dispatch context and workflow contract. No live App
credentials or network requests are needed. YAML syntax is also parsed locally.
