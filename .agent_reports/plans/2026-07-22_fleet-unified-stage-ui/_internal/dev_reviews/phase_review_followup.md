# Fleet v16 independent implementation review — follow-up (retry after prior process termination)

## Verdict

**FAIL.** Full regression/verification matrix is green, and six of the eight
prior review/repro findings are genuinely corrected. However, this follow-up
found one **new, reproducible major defect** in the shared `WorkProjection`
resolver's owner/conductor aggregation (a first-child selection that survived
the "retire first-child selection" mandate by moving from render.py into
projection.py), plus a **test-coverage gap** that let it pass every existing
gate, plus two **unresolved yellow obligations already named by the prior
review** (`demo.py` composed-DAG coverage, old-key-only JSON consumer test).
Per the assignment's PASS bar ("no major or yellow obligation remaining"),
this is FAIL. The route marker is not bound.

## Scope and method

Read completely: `spec/agent-fleet-dashboard/prd.md` (full v16, §4.12
F-36..F-39 + acceptance matrix), `plan/plan.md`, `plan/checklist.md`,
`dev_logs/execute.md`, `dev_logs/execute_fix2_stage.md`, `final_report.md`,
`_internal/dev_reviews/phase_review.md` (prior FAIL, 2 major + 4 yellow),
`_internal/dev_reviews/orchestrator_repro.md` (8 must-fix findings). Inspected
the current worktree diff (48 tracked files changed, 12 new — canonical +
byte-identical mirror), read `projection.py`, `route.py`, `model.py` in full
and the relevant sections of `render.py`, `collectors/__init__.py`, ran the
full required verification matrix, and independently reproduced/exercised
scenarios beyond what the existing test suite covers (per the assignment's
explicit instruction that JSON-only projection presence and green test counts
alone are not sufficient — must reproduce and inspect).

## Correction-group findings (1–9 from the assignment)

1. **Main Session row renders attached WorkProjection** — ✅ largely fixed,
   ⚠️ but incompletely (see Major Finding A below). `render.py:1030-1033` (wide)
   and `render.py:1471-1473` (narrow/stack, shared by `_session_row_2line`)
   now render `_projection_stage_text(s)`. Verified live via this worker's own
   process view (`impl-review` route node visible) and via
   `FLEET_DEMO=1 --once --view group` at 168/120/100/60, which shows
   `demo-app-a7 ... stage execute 1/4` — a single-active-node scenario. The
   *multi-active-sibling* owner scenario (the actual point of F-36c's
   "composed DAG" work) is broken — see Major Finding A. No CLI/demo fixture
   currently surfaces this because `demo.py`'s only owner→route link is a
   single-node chain (see Finding C).
2. **Unique exact `(pid,proc_start)` route candidate adopted; unique
   same-harness `realpath(cwd)` fallback only when identity evidence is
   absent** — ✅ confirmed correct in `projection.py:300-325`. Positive exact
   and unique-cwd adoption, PID-reuse refusal, and duplicate-cwd refusal are
   all implemented and covered by
   `test_unique_exact_and_unique_cwd_candidates_are_adopted` and
   `test_pid_reuse_and_duplicate_cwd_candidates_refuse_adoption`
   (`test_f36_work_projection.py`), both passing.
3. **`attempt_id` alone is not an explicit route tuple; Session
   `session_id/parent_sid` and DispatchJob `slug/parent_slug` traversal
   works** — ✅ confirmed. `projection.py:251-256` (`_explicit()`) excludes
   `attempt_id` by construction (only `route_file/route_id/route_hash/
   route_node` count). `_owner_children()` (`projection.py:259-269`) checks
   both link contracts. Covered by
   `test_attempt_only_and_both_owner_link_contracts_traverse_children`, passing.
4. **Direct owner-route vs child-route conflict → `owner-route-conflict`;
   same-route siblings remain visible** — ✅ conflict *detection* is fixed:
   `projection.py:327-355` now resolves the owner's own record, resolves every
   linked child's projection, and compares route keys before returning the
   owner's own route, emitting `owner-route-conflict` on disagreement instead
   of the previous silent early-return. Covered by
   `test_direct_owner_route_conflict_is_fail_closed`, passing. ⚠️ However,
   "same-route siblings remain visible" is only true in the *data* layer
   (`active_nodes[]`); it is false in the *owner row display* layer — see
   Major Finding A, which is exactly this correction group's other half.
5. **Render-local first-child/first-route selection retired** — ✅ the named
   helpers are gone: `grep -rn "_conductor_stage_override\|_conductor_route_seq"`
   returns nothing in `render.py`. Group tree walk
   (`render.py:2937-2942`, comment: "Row authority is the attached
   WorkProjection. No first-child or first-route selection is allowed in this
   render-local tree walk") and process view both consume only
   `entity.work_projection`. ⚠️ But Major Finding A shows first-child selection
   was not eliminated — it moved one layer down, from the renderer into the
   shared resolver's owner-aggregation branch, then leaks back out through the
   very `stage_label` field the renderer now trusts unconditionally.
6. **Process view emits job → context/NOW → exact-session sub-agent strip per
   chunk** — ✅ confirmed fixed. `_route_card()` (`render.py:2211-2223`) and
   `_degrade_card()` (`render.py:2294-2307`) both build
   `[job_row, ctx_row, *subagent_strip]` inline per node/job, and the caller
   (`render.py:2395-2422`) does a plain `lines.extend(card_lines)` with no
   post-hoc batching. Live-reproduced via
   `FLEET_DEMO=1 --once --view process`: each `└▸🚀 <job>` line is immediately
   followed by its own `ctx …` line before the next job. This resolves both
   the original review's 🔴 #1 and orchestrator_repro's #6.
7. **Public route JSON preserves old node keys/meanings
   (`model,harness,effort,elapsed_min,note`) and serializes from the attached
   backing view without reopening route files** — ✅ confirmed via live
   `--json` output: a real node dict from this run contains all five legacy
   keys with correct null/non-null values, and
   `route_summary_from_projections()` (`projection.py:427-467`) builds
   directly from `projection._route_view`, never calling `route.load()`
   again. `test_old_route_keys_and_private_evidence_remain_compatible`
   passes.
8. **Sealed arbitrary DAG `survey -> {claim-a, claim-b} -> synth`** — ⚠️
   partially proven, and the gap in proof directly correlates with Major
   Finding A going undetected. `test_f36_work_projection.py`'s
   `test_sealed_composed_dag_preserves_opaque_siblings_fanin_and_scope`
   correctly proves record-order topological levels
   (`[survey],[claim-a,claim-b],[synth]`), `write_scope` preservation, and
   `active_nodes` set membership — but **only at the pure-resolver layer**
   (imports only `fleet.projection`/`fleet.route`/`fleet.model`, never
   `fleet.render`). Plan step 5.2 explicitly named `test_f28_route.py`,
   `test_f28_breadcrumb.py`, and `test_f30_process_view.py` as the files to
   update so the composed fixture is proven through group/process/plain/route
   JSON; `grep -rln "synth_composed_survey\|claim-a" tools/fleet/tests/*.py`
   shows it appears in none of those three files — they still only exercise
   the pre-existing `synth_parallel_lab.json` fixture. I independently built
   the composed-DAG scenario through the real collector→projection→render
   path (see Major Finding A reproduction) and found the group-view owner row
   is wrong; process-view per-child rows are correct (each shows the full
   `survey › claim-a › claim-b › synth` breadcrumb via `_route_stage_segs`,
   which is a separate, already-correct code path from the owner's
   `stage_label`).
9. **Yellow obligations from the prior review** — mixed:
   - *Deterministic projection-aware demo*: ❌ still not resolved. `git diff
     -- tools/fleet/demo.py` shows exactly one line changed
     (`parent_sid="demo-claude-1"` added to the existing single-chain
     `demo-route-conductor` job) — this is what makes `stage execute 1/4`
     appear on the demo main session, but no composed/fork-fan-in route or
     multi-sibling-owner scenario was added to `demo.py`, so `--once --view
     group/process` smoke output still never exercises (and therefore never
     could have caught) Major Finding A.
   - *Old-key-only JSON consumer test*: ⚠️ not really resolved as a dedicated
     test. `test_t1_16_route_key_additive`/`test_t1_17_no_route_records_empty_array`
     (`test_f28_route.py`) only assert key *presence* against empty/near-empty
     data through `fleet._snapshot_json()`. `test_old_route_keys_and_private_evidence_remain_compatible`
     (`test_f36_work_projection.py`) checks value preservation but goes
     through `route_summary_from_projections()` directly, not the full
     `_snapshot_json()` pipeline, and is not framed as an "only reads old
     keys" consumer. No test combines populated legacy data + full snapshot
     pipeline + an assertion that a consumer touching only
     `sessions/jobs/summary/route` succeeds unchanged.
   - `WorkProjection.ambiguity` as `ambiguity[]`: ✅ resolved.
     `model.WorkProjection.to_dict()`/`route_summary_from_projections()` both
     serialize a list (`[]` or `["code"]`); live `--json` output confirmed
     `"ambiguity": []` on this worker's own session row.
   - Context sequence/head bound to same-sample per collector: unchanged
     (documented, not claimed fixed) — consistent with execute_fix2_stage.md's
     own disclosure.

## Major Finding A — owner/conductor `stage_label` silently drops agreeing
active siblings (first-child selection moved into the shared resolver)

**Location:** `tools/fleet/projection.py:376-385` (mirrored identically in
`adapters/claude/tools/fleet/projection.py`).

```python
    exact = [p for p in child_projections if p.source == "route-exact"]
    route_keys = {(p.route_id, p.route_hash) for p in exact}
    if len(route_keys) > 1:
        return WorkProjection(source="none", ambiguity=MULTIPLE_OWNER_ROUTES)
    if len(route_keys) == 1 and exact:
        p = exact[0]                              # <-- first child in `jobs` iteration order
        active = p.active_nodes
        return WorkProjection(source="route-exact", route_id=p.route_id, route_hash=p.route_hash,
                              active_nodes=active, progress=p.progress, stage_label=p.stage_label,
                              _route_view=p._route_view)
```

When two or more children agree on one validated route/hash (the exact
"parallel active siblings" scenario F-36c and this whole plan exist to
support), the owner's returned `WorkProjection.active_nodes` is correctly the
full multi-node list — but `stage_label` is copied from `p.stage_label`,
where `p = exact[0]`: whichever child happens to be first in
`_owner_children()`'s iteration order (i.e., the order jobs were appended to
the collector's `jobs` list — not record order, not a stable choice). Each
individual child's own `stage_label` is *that child's own single leaf node
id* (from `_projection_from_record`), so the owner ends up displaying one
arbitrary sibling's name as if it were the sole active stage.

**Why it matters / render-layer consequence:** `render.py`'s Session-row
stage text (`_projection_stage_text`, `render.py:907-921`) reads only
`projection.stage_label` — it has no analogue of the DispatchJob path's
`_projection_route_seq`/`_route_stage_segs` full-breadcrumb rendering
(`render.py:924-931`, `736-767`, wired in only for `DispatchJob` rows via
`_dispatch_stage_segs`, never for `Session` rows). So for a **Session** that
owns two or more parallel dispatch children on one validated route — the
literal "main Session with an attached route-exact WorkProjection" scenario
this assignment's correction group 1 asks to reproduce — the primary row's
stage/progress zone shows only one sibling's name and silently drops the
rest, in every layout (wide/narrow/stack), because they all route through the
same `_projection_stage_text`/`stage_label` value.

**Reproduction (direct API + live render, not merely a unit assertion):**

```python
owner = Session(harness="claude", pid=100, proc_start="s0", cwd="/home/proj",
                 slug="main-sess", session_id="sess-owner", liveness="working",
                 elapsed_min=12, branch="main")
jobs = [
    DispatchJob(key="claim", slug="claim-a", parent_sid="sess-owner", depth=2,
                route_id=rid, route_file=COMPOSED, route_node="claim-a",
                liveness="working", harness="claude", pid=101, proc_start="s1", elapsed_min=5),
    DispatchJob(key="claim", slug="claim-b", parent_sid="sess-owner", depth=2,
                route_id=rid, route_file=COMPOSED, route_node="claim-b",
                liveness="working", harness="claude", pid=102, proc_start="s2", elapsed_min=5),
]
sessions, jobs = projection.attach_projections([owner], jobs, now=100.0)
# owner.work_projection.stage_label == "claim-a"
# owner.work_projection.active_nodes == [claim-a, claim-b]   <- data is right
```

Rendered through the real `render._build_lines(sessions, jobs, "both", False,
None, layout="wide", term_width=168)` (using
`tests/fixtures/route/synth_composed_survey.json`, the sealed
`survey -> {claim-a, claim-b} -> synth` fixture this task added):

```
● proj/
▍ ⠼ claude code   main-sess   main   stage claim-a 0/4          12m
▍     ctx —
```

`claim-b` never appears anywhere on the owner's own row at any width. This is
reproducible deterministically (iteration order is insertion order of the
`jobs` list passed to `attach_projections`/`resolve_work_projection`, which
in real collection is proc-scan/jobs.log discovery order, not DAG record
order) — swapping the two `DispatchJob` construction calls changes which
label wins, which is itself further evidence this is an unintended ordering
artifact, not a deliberate "primary node" choice.

**Relation to prior findings:** This is a new manifestation of exactly the
defect class orchestrator_repro's finding #5 ("Group rendering still chooses
the first child/route... must render only `entity.work_projection`") and this
assignment's correction groups 1/5/8 were meant to close. The letter of "no
render-local first-child selection" is satisfied (the renderer really does
only read `entity.work_projection`), but the *spirit* — no first-child
selection anywhere in the owner/conductor path — is not, because the
selection now happens one layer down, inside the projection returned to the
renderer, and the field it corrupts (`stage_label`) is exactly the field the
renderer (correctly, per the new architecture) trusts unconditionally.

**No test catches this.** `test_sealed_composed_dag_preserves_opaque_siblings_fanin_and_scope`
asserts only `{n.id for n in owner.work_projection.active_nodes} ==
{"claim-a", "claim-b"}` — it never inspects `stage_label`, and no test in the
suite calls `_projection_stage_text`/`_session_row`/`_build_lines` with a
multi-child-agreement Session or DispatchJob owner. This is the direct
consequence of Finding under group 8 above (the sealed fixture never reaches
`render.py` in any existing test).

## Test/verification matrix (all commands run fresh, in this worktree)

| Command | Result |
|---|---|
| `python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py'` | PASS, 773/773 (one pre-existing `ResourceWarning` in `test_f27_control.py:521`, not a failure) |
| `python3 utilities/compose_route.test.py` | PASS, 9/9 |
| `python3 utilities/capability_route.test.py` | PASS, 30/30 |
| `capability-route.py verify --route tools/fleet/tests/fixtures/route/synth_composed_survey.json --cwd "$PWD"` | PASS — `route_id=rt-63788ad671654b75`, sealed hash verified |
| `FLEET_TITLE_DISABLE=1 FLEET_DEMO=1 AGENT_DISPATCH_JOBS=/dev/null fleet.py --once --view group` | exit 0; renders `demo-app-a7 ... stage execute 1/4` (single-node case only — see Finding C) |
| `FLEET_TITLE_DISABLE=1 FLEET_DEMO=1 AGENT_DISPATCH_JOBS=/dev/null fleet.py --once --view process` | exit 0; job→ctx→subagent chunk order confirmed correct |
| `FLEET_TITLE_DISABLE=1 FLEET_DEMO=1 AGENT_DISPATCH_JOBS=/dev/null fleet.py --json \| python3 -m json.tool` | exit 0, parses; additive keys/`ambiguity` array/no private evidence confirmed by direct inspection |
| `python3 -m compileall -q tools/fleet adapters/claude/tools/fleet` | PASS |
| `python3 -m unittest tools.fleet.tests.test_mirror_parity` | PASS, 1/1 |
| `diff -rq tools/fleet/ adapters/claude/tools/fleet/ --exclude=__pycache__` | empty (byte parity) |
| `git diff --check` | exit 0, no whitespace errors |
| `bash tools/adaptation-guard.test.sh` | PASS, all 9 negative sentinel cases |
| `bash tools/check-adaptation-boundary.sh` | exit 0; `WARN: 127 concrete Claude/model references...` (documented adapter-mapping warning, matches prior report) |

No live/default/custom title provider was invoked by any command above or by
this review; this worker did not spawn a provider and the hermetic suites'
own fail-if-reached provider guards are part of the 773-test PASS count.

## Other observations (not blocking, recorded for completeness)

- An untracked `Fleet title work/.runtime/model-worker-governor/{lock,state.json}`
  directory exists at the worktree root (created by some earlier test/run
  using a relative `FLEET_TITLE_STATE_DIR`-style path instead of an isolated
  temp dir). Not part of this review's write scope to remove; flagging so the
  owner can decide whether a hermetic test needs its isolation tightened.
- Layout-cutoff terminology check: PRD §3's historical "70/110 컷오프" text is
  superseded by the actual `_NARROW_CUTOFF=70` / `_TWO_LINE_CUTOFF=138`
  constants in `render.py` (F-15a). This is a pre-existing doc/code drift, not
  introduced by this task, and the acceptance matrix's "wide@168, forced
  wide@120" wording already anticipates it (120 is below the real wide
  cutoff, hence "forced").

## Required assurance

Not claimed. Standard code QA assurance
(`plan-check:selected-independent-pass:final-verify`) requires this gate to
be green; it is not. The registered route marker is intentionally **not**
bound by this review (`impl-review` completion command was not run).

## Resume boundary

Resume at `impl-review`/`execute`: fix the owner-aggregation branch in
`resolve_work_projection` (`projection.py:376-385`) so a multi-sibling
owner's `stage_label` (or the render layer's use of it) reflects every
agreeing active sibling in record order — the same guarantee `active_nodes[]`
already provides and the same guarantee `_route_stage_segs` already gives
DispatchJob rows — rather than an arbitrary first child. Add a regression
that renders a multi-child-agreement **Session** owner (not just a
`DispatchJob` owner) through `_build_lines`/`_session_row` and asserts every
sibling id is visible, not just presence in `active_nodes`. Then wire the
sealed `synth_composed_survey.json` fixture into `test_f28_route.py`,
`test_f28_breadcrumb.py`, and `test_f30_process_view.py` as plan step 5.2
specified, and add a `demo.py` composed/multi-sibling-owner entity so
`--once --view group/process` smoke actually exercises this path. Add a
dedicated old-key-only `_snapshot_json()` consumer test with populated route
node data.
