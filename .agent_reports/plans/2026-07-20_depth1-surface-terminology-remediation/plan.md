# Depth-1 surface terminology remediation — implementation plan

Final disposition: **REJECTED / NOT MERGED** (2026-07-20). The one permitted
fix round did not clear the independent final gate. The authoritative blocker
and reproductions are in `test_logs/final-independent-review.md`; no additional
fix round is authorized by this plan.

Date: 2026-07-20  
Route: `rt-4ddceb3e346c0941` / node `plan`  
Capability / mode / intensity: `autopilot-code` / `dev/refactor` / `strong`  
Starting worktree / HEAD: `/home/Uihyeop/agent_setting-wt/depth1-surface-terminology-remediated` / `d7e5ad35865b77cfa5c05ddf4b3c4dccd87e9c72` (`origin/main`)  
Spec significance: `within-spec` — implement PRD v20 §13.12, SD-73–75; do not edit the PRD.

## Outcome and non-negotiable boundaries

Implement the v20 dispatch contract so portable dispatch topology, wrapper transport,
attempt execution surface, registration status, and fallback position cannot be
confused. Quick routes become registered-headless-only and fail before emitting any
route, registry row, or child process when that requirement is not met. Direct stays
main-inline, and standard+ keeps its existing checked four-hop fallback order.

The execute stage must apply, without committing, only the two approved source
candidates:

1. `7094c92b` — canonical and adapter terminology seed.
2. `c95ed391` — portable and generated-layer propagation seed.

Use `git cherry-pick --no-commit 7094c92b c95ed391`, then resolve their intent against
current `origin/main` and extend it to the v20 machine contract. Do not cherry-pick,
copy, or recreate `6b3a34bc`; co-primary routing, multi-capability composition, and a
cross-capability DAG/envelope are explicitly out of scope. Do not alter either source
branch. Create one task commit only after implementation, deterministic verification,
and the independent risk-focused review all pass.

Authoritative inputs are the immutable route in `_internal/code-route.json`, PRD v20
§13.12 / SD-73–75, and the depth-1 terminology audit. The current route has the old
schema and is self-hosting bootstrap evidence, not a model for newly emitted records.

## Contract decisions for the execute stage

### 1. Qualified topology and attempt fields

Use these names on every new/current machine-readable surface:

| Concern | v20 field | Meaning |
|---|---|---|
| route owner topology | `owner_dispatch_depth` | logical capability-owner level |
| route maximum | `max_dispatch_depth` | logical portable topology bound |
| node topology | `dispatch_depth` | logical route-node level (`0`, `1`, or `2`) |
| attempt location | `execution_surface` | runtime surface from the closed vocabulary below |
| attempt registration | `registered_worker` | boolean backed by a repo-owned wrapper claim |
| fallback position | `fallback_hop` | one entry from the closed fallback vocabulary |

Rename public CLI/output/registry/Fleet fields such as `--depth`, `depth=`, route
`depth`, `owner_depth`, and `max_depth` to their qualified forms. Internal display
indentation variables may retain a generic local name only when they are not serialized
or described as dispatch topology; current normative prose and generated projections
must say “dispatch depth” or use `dispatch_depth`. `AGENT_DISPATCH_DEPTH` is already
qualified by its namespace, but new code and evidence should prefer
`AGENT_DISPATCH_DEPTH` -> `dispatch_depth` mapping explicitly and never compare it to
Codex `agents.max_depth`.

Direct routes emit a logical inline node at `dispatch_depth=0`, with
`execution_surface=inline`, `registered_worker=false`, and no worker registry row.
Quick routes emit one owner node at `dispatch_depth=1`,
`owner_dispatch_depth=max_dispatch_depth=1`; they have no child nodes. Standard+ keeps
an owner at dispatch depth 1 and its existing recipe nodes at dispatch depth 2.

### 2. Closed namespaces

Define and validate one canonical vocabulary for each namespace before applying a
recipe-specific allowlist:

- wrapper `transport`: `headless`, `interactive`;
- attempt `execution_surface`: `registered-headless`, `codex-native-subagent`,
  `claude-subagent`, `claude-agent-team-teammate`, `inline`;
- `fallback_hop`: `same-harness-headless`, `cross-harness-headless`,
  `native-subagent`, `inline`.

`detached-process` remains a separately named resource-job lifecycle value; it is not
a transport or execution surface. Remove `native-subagent` and `inline-fallback` from
the transport vocabulary. In the topology registry, describe standard+ fallback
allowlists as fallback hops/execution surfaces rather than overloading `transport`.
For new route records, use `fallback_hops` entries with a `fallback_hop` field; do not
write the legacy `dispatch_fallback[].hop` shape.

Centralize these constants in the portable dispatch contract and make topology,
compiler, wrapper, fallback, registry, completion, liveness, and Fleet validators use
or cross-check the same exact sets. Unknown values fail before route hashing/writing or
attempt claiming.

### 3. Quick registered-headless-only state machine

Change route compilation so an omitted quick transport derives to `headless`.
Explicit empty, `interactive`, `native-subagent`, `inline-fallback`, and arbitrary
values fail. Add structured, checked registered-headless eligibility input (for
example, a `--registered-headless-evidence <json>` fixture with harness, transport,
surface, status, probe source, and probe time); quick compilation requires at least one
eligible `supported` registered-headless candidate. Missing, `unknown`, or
`unsupported` evidence terminates with exactly `quick-headless-unavailable`.

All quick validation must occur before `write_once`, registry-directory creation,
attempt claim, or wrapper launch. Persist the permitted registered-headless candidates
and serial-attempt policy in the immutable route. At wrapper/registry time:

- allow at most one current/open attempt for the quick node under the route/node lock;
- accept only `execution_surface=registered-headless` and
  `registered_worker=true` attempts;
- preserve terminal retry rows and stable attempt identities;
- never create a depth-2 child row or native/inline degradation row;
- never mutate the route intensity, transport, or execution location;
- after the checked registered-headless candidates/retries are exhausted, fail with
  exactly `quick-registered-headless-exhausted`.

Any move to another intensity is a newly approved and newly compiled route, not a
runtime fallback. Add zero-emission tests that snapshot the output path, jobs registry,
claim callback, and spawn callback before every invalid quick case and assert all remain
absent/uninvoked.

### 4. Direct and standard+ preservation

Derive direct to the interactive/main-inline path without a wrapper registration,
keep one logical node at dispatch depth 0, and retain focused direct completion
behavior. Do not reuse the removed `inline-fallback` transport label.

For standard+, preserve checked ordering exactly:

1. `same-harness-headless`
2. `cross-harness-headless`
3. `native-subagent`
4. `inline`

Keep the route node's `dispatch_depth=2` through every attempt. Headless wrapper
attempts record `execution_surface=registered-headless` and
`registered_worker=true`; Codex native, Claude native, and inline fallback attempts
record the correct surface and `registered_worker=false`. A fallback must never erase
logical dispatch depth or acquire registered-worker status merely because it belongs to
a registered route.

### 5. Record versions and the self-hosting legacy boundary

Bump the current topology/route/attempt/completion schema versions as needed for the
qualified v20 shape. A legacy reader may parse old `schema_version=1` route files and
jobs rows lacking the new version field for diagnostics only, label their source
version, and show them in Fleet. New `node`, `complete`, start/resume, registry claim,
or re-emission operations must reject them until a fresh v20 route is compiled.
Completion markers, liveness heartbeats, and Fleet job models must carry or derive the
new node `dispatch_depth`, `execution_surface`, and `registered_worker` evidence without
collapsing the axes.

The current immutable route is the one bounded self-hosting exception. The depth-1
owner must create `_internal/metrics.md` with this exact substance before integration:

```text
self_hosting_legacy_bootstrap_route=rt-4ddceb3e346c0941
legacy_schema_version=1
classification=version-tagged-read-only-bootstrap
scope=current-remediation-cycle-only
reason=the owner and plan node were emitted before SD-73/74/75 existed
new_route_reemit=forbidden
post_change_acceptance=fresh-v20-direct-quick-standard-plus
```

Do not mutate `_internal/code-route.json`. The installed pre-change conductor may
finish this already-active pipeline; the changed worktree tools must not treat that
record as resumable v20 evidence. This exception is not permission for a new legacy
route or an inline/native quick fallback.

### 6. Four-surface terminology and generated propagation

Use the four exact runtime nouns in current prose and conformance fixtures:

1. Codex native subagent;
2. Claude subagent;
3. Claude agent-team teammate session;
4. registered headless worker session.

The cross-runtime category “runtime-native subagent” contains only the first two.
Claude agent-team teammates are separate full peer sessions, not Claude subagents.
Team membership never implies registered-worker status. Correct the candidate patch's
“team agent — a runtime-native subagent” wording when resolving the cherry-pick.

Edit canonical portable sources and generator templates first. Candidate `c95ed391`
touches generated Claude mirrors; after incorporating its intent, run the generators so
derived files are produced by their owners rather than maintained by hand:

- `tools/sync-entry-skill-layer.py` owns compact entry routers and Claude Skill mirrors;
- `adapters/codex/bin/sync-native-skills.py` and plugin generation own Codex Skills;
- `adapters/opencode/bin/sync-native-skills.py` and command generation own OpenCode
  projections;
- `tools/generate.py` is the aggregate projection entrypoint;
- `tools/fleet/` is canonical for Fleet and must be mechanically mirrored to
  `adapters/claude/tools/fleet/` as required by `test_mirror_parity.py`.

Before invoking a generator or mirror sync, enumerate every file it will change and run
`preflight.sh write <file> codex-headless` for each. Do not hand-edit a generated output
after generation; update its canonical source/template and regenerate.

## Ordered implementation steps

### Step 0 — safety, candidate application, and scope fence

1. Confirm clean worktree, HEAD `d7e5ad35865b77cfa5c05ddf4b3c4dccd87e9c72`, and no merge/cherry-pick in progress.
2. Record the names changed by `7094c92b` and `c95ed391`; run the write preflight for
   each before applying them.
3. Apply both with `git cherry-pick --no-commit 7094c92b c95ed391` in that order.
4. Resolve against current main, retaining newer dispatch v3/v18 behavior. Confirm
   `git merge-base --is-ancestor 6b3a34bc HEAD` is false and grep the diff for
   `co-primary`, composition envelopes, and cross-capability DAG additions.
5. Keep the index/worktree uncommitted until the final gate.

### Step 1 — portable topology registry and compiler

Primary files: `capabilities/topologies.json`, `tools/capability_topology.py`,
`tools/capability_topology.test.py`, `utilities/capability-route.py`, and
`utilities/capability_route.test.py`.

Introduce the v20 schemas/vocabularies, rename all topology fields, make direct depth 0,
encode quick's strict allowlist/evidence/cardinality, and preserve standard+ fallback
semantics. Validate global vocabulary before recipe allowlists. Hash only the new
canonical representation. Keep a diagnostic-only legacy verifier with an explicit
version result; all mutating/resume CLI commands require the current version.

Add table-driven tests over every capability/mode recipe. For each recipe: quick default
with supported evidence produces exactly one registered-headless owner node; every
invalid quick transport/evidence case has zero emissions; direct has no registered row;
and standard+ retains the four fallback hops. Add negative tests for unknown values in
each of the three namespaces and for bare v20 depth fields.

### Step 2 — wrappers, registry, fallback, completion, and liveness

Primary files: `utilities/dispatch_contract.py`, `utilities/dispatch-node.py`,
`utilities/dispatch-registry.py`, `utilities/stage-dispatch-fallback.py`,
`utilities/worker-route-guard.py`, `utilities/worker_bootstrap.py`,
`utilities/dispatch-progress.py`, `utilities/dispatch-liveness.sh`,
`adapters/{claude,codex,opencode}/bin/dispatch-headless.py`, and their focused tests.

Rename public dispatch-depth arguments and row fields, stamp current record versions,
and attach exact execution-surface and registration evidence to claims and completion.
Enforce quick single-live-attempt and exhaustion while holding the canonical registry
lock. Ensure wrapper preflight rejects invalid quick state before registry creation.
Standard+ fallback code must translate each `fallback_hop` to the correct attempt
surface and registration flag. Node launch, completion, worker-route guard, orphan
classification, and liveness must reject legacy records for resume while retaining
read-only diagnostic parsing.

### Step 3 — Fleet and serialized fixtures

Primary files: `tools/fleet/model.py`, `tools/fleet/collectors/dispatch.py`, relevant
render/control code, route/jobs fixtures, and focused Fleet tests. Mirror the finished
canonical tree byte-for-byte to `adapters/claude/tools/fleet/`.

Expose `dispatch_depth`, `execution_surface`, and `registered_worker` as separate model
attributes. Parse v20 rows strictly; parse absent-version legacy rows only as labeled
read-only history. Add fixtures proving: one current/open quick attempt maximum;
terminal retry history remains visible; native/inline quick attempts and quick child
rows are contract violations; a standard+ native/inline fallback retains dispatch
depth 2 without registered status; and Codex native depth settings do not influence the
portable maximum.

### Step 4 — canonical prose and projections

Update `core/CONVENTIONS.md`, `core/OPERATIONS.md`, `core/WORKFLOW.md`, relevant role and
capability contracts, canonical `skills/` owner references, generator templates, and
the three adapter bootstraps. Qualify current dispatch-depth language and apply the
four-surface terminology. Preserve historical/version-tagged text as historical; do not
rewrite the PRD's v1–v19 record. Add a deterministic terminology conformance check that
rejects current bare route field names, conflated transport/surface/fallback values,
Claude teammate-as-subagent wording, and unqualified claims relating Codex
`agents.max_depth` to registered headless dispatch.

Run `python3 tools/generate.py` only after canonical/template edits, then mirror Fleet.
The resulting generated diff is expected; manual drift is not.

### Step 5 — focused test construction and fresh acceptance evidence

Extend existing focused suites rather than relying on generation/parity checks. The
test stage must create fresh artifacts under `test_logs/route-acceptance/` after the
implementation:

- `direct.json`: compile a direct route from complete direct predicates and assert
  dispatch depth 0, inline surface, unregistered status, and no jobs row;
- `quick.json`: compile quick with a fresh supported registered-headless evidence file
  and assert one node, depths 1/1/1, headless transport, registered-headless-only
  policy, no fallback chain, and at most one live attempt;
- `standard-plus.json`: compile strong standard+ with fresh checked nested evidence and
  assert owner dispatch depth 1, stage dispatch depth 2, and the unchanged four-hop
  order.

Write `test_logs/route-acceptance/summary.md` with commands, route IDs/hashes, source
HEAD, assertion results, and the negative zero-emission matrix. These files must be
newly compiled from the changed worktree, not copied from `_internal/code-route.json`.

The negative matrix must include quick + omitted eligibility, empty transport,
`interactive`, `native-subagent`, `inline-fallback`, arbitrary transport, unavailable
headless, exhausted headless, a requested child node, and a second simultaneous live
attempt. Assert exact error enums and zero route/row/spawn emissions. Preservation
fixtures must cover direct and standard+ separately.

### Step 6 — verification, independent review, bounded fix loop, commit

Run the focused tests first, then the complete relevant suite through the verification
runner. Required commands (adjust only test-runner syntax, not coverage):

```text
python3 tools/capability_topology.test.py
python3 utilities/capability_route.test.py
python3 utilities/dispatch_contract.test.py
python3 utilities/dispatch_node.test.py
python3 utilities/dispatch_registry.test.py
python3 utilities/dispatch_completion_marker.test.py
python3 utilities/dispatch_progress.test.py
python3 utilities/worker_route_guard.test.py
python3 utilities/stage_dispatch_fallback.test.py
python3 utilities/stage_dispatch_capacity.test.py
python3 utilities/worker_bootstrap.test.py
python3 utilities/worker_dispatch_prompt.test.py
python3 adapters/claude/bin/dispatch-headless.sd45.test.py
python3 adapters/codex/bin/dispatch-headless.sd45.test.py
python3 adapters/opencode/bin/dispatch-headless.sd45.test.py
sh adapters/claude/bin/dispatch-headless.sd15.test.sh
sh adapters/codex/bin/dispatch-headless.sd15.test.sh
sh adapters/opencode/bin/dispatch-headless.sd15.test.sh
python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py'
sh tools/routing-contract.test.sh
python3 tools/generate.py --check
python3 tools/sync-entry-skill-layer.py --check
sh tools/check-adaptation-boundary.sh
git diff --check
```

Also run the new v20 acceptance/conformance suite and the three fresh CLI route
compiles described above. Wrap the aggregate command with
`preflight.sh verification-runner --timeout <bounded-seconds> -- <command>` and retain
stdout/stderr and exit status in `test_logs/`.

After tests pass, a separate deep-review worker (the code-test stage is suitable) must
perform a read-only, risk-focused diff review of namespace closure, quick zero-emission
ordering, legacy migration fencing, direct/standard+ preservation, generated ownership,
and exclusion of `6b3a34bc`. Up to two separate fast reviewers may cover terminology
and fixture completeness. Record identities/artifacts of reviewers that actually ran;
do not write “independent pass” for inline self-review.

If the independent review or verification requests a fix, run at most one bounded
execute-fix round (`max_round=1`) against the exact findings, then rerun the complete
focused and final verification plus independent diff review. If the second result is
not PASS, stop with FAIL/BLOCKED and do not commit. When every gate passes, recheck
clean merge state and expected diff, then create the single task commit. No push,
integration, cleanup, or source-branch mutation belongs to the stage workers.

## QA assurance and plan-check

Policy: `standard/code`  
Assurance scope: `plan-check:selected-independent-pass:final-verify`  
Reviewer budget: one deep reviewer and up to two fast reviewers; the selected
independent pass is concentrated on the post-implementation risk-focused diff/final
verification rather than repeated after each sub-stage.

This plan stage performed a deep-maker self-check against all SD-73–75 acceptance
items, the audit's six findings, the current compiler/topology/wrapper/Fleet call sites,
and the two approved commit diffs. No separate reviewer process ran during plan
authorship, so no independent-delegation or independent-pass claim is made here. The
downstream gate requires a separate review artifact before commit.

The spec-read marker command was attempted after reading the PRD and failed because the
marker path under `/home/Uihyeop/agent_setting/.spec-grounding/` was reported read-only
inside this worker. The immutable route already records the upstream v20 spec-read gate
as satisfied. This is a recorded runtime warning, not permission to edit the spec or
skip execute-stage preflights.

## Completion gate for this plan

The plan is complete when `plan.md` and `checklist.md` are durable, name all v20
implementation areas and preservation tests, fence the rejected commit, specify the
self-hosting exception, enumerate QA/review/verification gates, and let execute/test
stages proceed without conversation history. Source remains unmodified by this stage.
