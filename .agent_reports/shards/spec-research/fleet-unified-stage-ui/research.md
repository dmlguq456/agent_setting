# Fleet unified stage/progress UI — research handoff

Date: 2026-07-22  
Assignment: research support for the approved `agent-fleet-dashboard` PRD v16 update  
Repository state inspected: `e8938809d87e54474f5e7242a2552598c2636a0a` (`HEAD`, `main`, `origin/main`)  
Scope: read-only repository/spec analysis; no source or PRD edits

## Outcome

The v16 update should add one source-agnostic work projection used by both interactive `Session` rows and registered `DispatchJob` rows, make exact route/node evidence strictly outrank legacy artifact inference, and fail closed on an ambiguous identity or route match. The route side must treat node IDs and `depends_on` as opaque DAG data, including parallel nodes introduced by compose-on-demand routes.

For the UI, use one subordinate detail line in all three layouts, reserving the context indicator before the live subtitle. A child job may receive only its own context telemetry through the existing ambiguity-refusing child-session join; it must never inherit its parent's context. Context pressure is display/response-policy evidence only and remains orthogonal to intensity.

The conservative higher title-refresh allowance is:

- default concurrency `3`, hard maximum `4`;
- default and hard maximum `4` starts per rolling `60s`;
- main debounce remains `600s`; child debounce remains `150s`;
- one shared global pool for main sessions, children, default provider, and custom provider.

This lets a cold board fill three default slots and permits at most one replacement in the same minute. Even an environment override cannot exceed four live workers or four new starts per minute.

## Evidence

### Canonical PRD and current Fleet model

- The PRD currently specifies unit-aware stage rows and route-record-first conductor breadcrumbs for registered depth-2 work (`prd.md` §4.5, lines 160–168), but it does not define a common projection shared with interactive sessions.
- `Session` has context/title/summary fields but no route, node, attempt, assigned-contract, or common stage-projection fields (`tools/fleet/model.py:125-181`). `DispatchJob` alone carries `assigned_contract`, `unit`, `route_file`, `route_id`, `route_hash`, `route_node`, and `attempt_id` (`tools/fleet/model.py:203-270`). This is the concrete parity gap.
- `route.build_views()` currently groups only objects with `job.route_id`; a row without it contributes nothing (`tools/fleet/route.py:543-580`). Consequently an interactive session cannot consume the same route view directly.
- Exact route views already preserve `unit_catalog_digest`, `composed`, node `unit`, `unit_choices`, state, and progress (`tools/fleet/route.py:500-540`, `643-665`). Reusing this projection is lower risk than adding a second interactive-only stage classifier.
- Legacy artifact inference is still active: `live_stage()` searches a likely `plans/*_<slug>` directory and infers `plan/exec/test/done` (`tools/fleet/collectors/dispatch.py:675-744`), then registry-only working jobs are overwritten with this inferred stage after classification (`tools/fleet/collectors/dispatch.py:1449-1456`). This must become a marked, lower-confidence fallback and must never override exact route/node evidence.
- The group renderer still chooses the first active routed child and first available child route ID (`tools/fleet/render.py:2875-2910`). That is unsafe for conflicting matches and lossy for valid parallel branches.

### Compose-on-demand route evidence (`e8938809`)

- Commit `e8938809` added `utilities/compose-route.py`, accepting an arbitrary non-empty list of unit nodes. Every node preserves its caller-supplied `id`, `depends_on`, inputs/outputs, write scope, completion gate, and optional `unit_choices`/guard preconditions before the existing compiler validates and hash-seals the route (`utilities/compose-route.py:116-170`).
- The helper does not silently select a completion gate when a unit maps to zero or multiple candidates; it requires an explicit gate (`utilities/compose-route.py:103-113`). The regression suite explicitly pins the multiple-gate ambiguity refusal (`utilities/compose_route.test.py:142-147`) and proves a composed route round trip through the canonical compiler/verifier (`:107-120`).
- The Fleet route reader already topologically levels arbitrary node IDs using record order within a level (`tools/fleet/route.py:407-432`). The synthetic lab fixture exercises a fork/fan-in graph: `setup -> {eval-asr, eval-sep, eval-vad} -> aggregate -> report` (`tools/fleet/tests/test_f28_route.py:116-123`). Breadcrumb tests also prove non-code node labels such as `eval-sep` and `research` render (`tools/fleet/tests/test_f28_breadcrumb.py:81-117`).
- Therefore v16 must not narrow the new common projection back to the historic `plan/exec/test/report` vocabulary. Resolved route records are the topology source of truth.

### Ambiguity and child joins

- The existing title/summary adoption path is a useful precedent: PID equality is the strong join, `(harness, realpath(cwd))` is a fallback, and two child sessions sharing the same key cause refusal instead of first-match attribution (`tools/fleet/collectors/__init__.py:63-94`). Existing tests assert title and summary are both withheld on an ambiguous cwd (`tools/fleet/tests/test_f16_f17_subtitle.py:72-88`).
- That join currently copies only title and summary. `DispatchJob` has no child context field, so dispatched rows cannot honestly show their own context even though the hidden child `Session` may already have `ctx_pct`.
- Process scanning already reads each process environment but discards `AGENT_ROUTE_FILE`, `AGENT_ROUTE_ID`, and `AGENT_ROUTE_NODE` when constructing a `Session` (`tools/fleet/collectors/procscan.py:287-333`). Capturing these as optional evidence is additive and avoids cwd/artifact guesses when the runtime exports them.

### Rendering and context contracts

- The live subtitle is currently emitted only in the wide path because it is inside the `_srow is None` / wide dispatch branch (`tools/fleet/render.py:2848-2854`, `2953-2958`). Narrow and stack cards omit it.
- Session context is already normalized as `ctx_pct` and rendered in the wide row and narrow/stack card telemetry (`tools/fleet/render.py:919-1004`, `1368-1462`). Dispatch rows have no equivalent child context source.
- The portable invariant is explicit: token/context pressure is orthogonal to intensity and cannot change graph, depth, dispatch, model role, effort, review, verification, retry, guards, or definition of done (`core/CONVENTIONS.md:78-84`). The existing portable bands are `normal`, `tight >= 70%`, and `critical >= 85%`; invalid/missing input is `unknown` (`tools/fleet/token_budget.py:20-23`, `84-98`).

### Title-provider bounds and provider contract

- Current constants are verified at `tools/fleet/refresh_title.py:45-51`: concurrency `2` / max `4`; starts `3` / max `3` per `60s`; main debounce `600s`; child debounce `150s`. Commit `41e99239` changed the former `16 per 600s` allowance to `3 per 60s`.
- Concurrency and rolling starts are cross-process leases guarded by a non-blocking global lock and fail closed on contention (`tools/fleet/refresh_title.py:325-449`). A direct `run_worker()` call cannot bypass these guards (`:452-466`).
- The default provider invokes Claude with every tool disallowed; `FLEET_TITLE_COMMAND` remains a shell-free argv template with `{model}` and `{prompt}` substitution (`tools/fleet/refresh_title.py:259-283`). The custom wrapper is responsible for preserving the no-tools execution property.
- Title scheduling remains live-TUI-only; `--json` and `--once` do not schedule providers (`tools/fleet/fleet.py:152-193`). Main and child sessions already share one scheduler pool, with the shorter child debounce selected per session (`tools/fleet/refresh_title.py:592-616`).

## Recommended exact PRD language

Recommended insertion after §4.11, retaining the PRD's Korean normative style:

### `## 4.12 [v16 신설] 공통 work projection·context detail row·title budget — F-36~F-39`

> **목표**: interactive 세션과 registered dispatch 잡을 서로 다른 stage 판정기로 그리지 않는다. 동일한 read-only evidence를 동일한 `WorkProjection`으로 정규화한 뒤 group/process/JSON 표면이 그 결과만 소비한다. route/node 귀속은 추정보다 부재가 낫고, context pressure는 intensity와 직교한다.

- **F-36a (공통 stage/progress projection)**: `Session`과 `DispatchJob`은 additive `work_projection`을 공유한다. 정규형은 `source`(`route-exact|registry-exact|artifact-inferred|none`), `route_id`, `route_hash`, `route_node`, `attempt_id`, `assigned_contract`, `unit`, `stage_label`, `node_state`(`active|done|failed|pending|unknown`), `active_nodes[]`, `progress{done,total}`, `ambiguity[]`를 운반한다. leaf 실행은 정확히 한 `route_node`를, owner/conductor는 같은 route의 0개 이상 `active_nodes`를 표현한다. group view, process view, `--once`, `--json`은 이 한 projection을 소비하며 별도 stage 판정을 만들지 않는다.
- **F-36b (evidence 우선순위·모호성 거부)**: 우선순위는 ① hash 검증된 immutable route record + 동일 entity의 명시 `route_id/route_node/attempt_id`, ② jobs.log 또는 process env의 명시 route/node evidence를 exact identity `(pid,proc_start)`로 결합, ③ 단 하나의 후보만 남는 `(harness,realpath(cwd))` registered-row 결합, ④ route evidence가 전혀 없는 legacy 행의 artifact stage 유도 순이다. 명시 route tuple이 record와 충돌·검증 실패하면 `unknown`/`ambiguity`로 남기고 artifact로 덮어 숨기지 않는다. 한 leaf에 서로 다른 route/node 후보가 2개 이상이거나 cwd fallback 후보가 2개 이상이면 첫 항목을 고르지 않는다. 같은 route의 병렬 active node 여러 개는 모호성이 아니라 `active_nodes[]`로 보존한다.
- **F-36c (임의 composed DAG)**: route record의 `nodes[].id`는 opaque label이고 `depends_on`이 유일한 순서/분기 근거다. `plan/execute/test/report` 하드코딩은 record가 없는 legacy fallback에만 허용한다. composed route의 병렬 branch·fan-in·임의 unit node를 record 순서의 topological level로 보존하며, 모든 active sibling을 동시에 표시한다. Fleet은 catalog를 재조합하거나 node 이름에서 capability/stage를 추론하지 않는다.
- **F-36d (artifact fallback 경계)**: artifact 유도는 route tuple이 완전히 부재하고 plan-dir 후보가 정확히 하나일 때만 `source=artifact-inferred`로 허용한다. 이 경로는 `stage_label`만 채우며 `route_id`, `route_node`, gate 통과, node 완료를 만들어 내지 않는다. 후보가 0개 또는 2개 이상이면 `source=none`이고 stage를 생략한다.
- **F-37a (context detail row)**: live session/dispatch identity card 직후, sub-agent strip보다 먼저 depth inset을 맞춘 detail row를 모든 레이아웃(wide/narrow/stack)에 표시한다. 문법은 `ctx <NN%|—> [normal|tight|critical][ · <fresh NOW>]`이다. context token을 먼저 예약하고 남는 폭에서 NOW를 display-cell 안전 tail-clip한다. NOW가 없으면 구분자 없이 context만, context가 없으면 `ctx —`, 둘 다 stale/dead이면 행 전체를 생략한다. dead/stale의 마지막 telemetry를 live처럼 표시하지 않는다.
- **F-37b (분사 자식 telemetry 결정)**: dispatch row의 context는 그 자식 runtime session 자신의 normalized context만 사용한다. `(pid,proc_start)` exact join을 우선하고, PID가 없는 jobs.log 행은 단 하나의 `(harness,realpath(cwd))` child 후보에만 fallback한다. ambiguity면 `ctx —`; 부모 context 상속은 금지한다. `DispatchJob`/JSON에는 child `context{used_pct,band,source}`를 additive로 노출하고 기존 키 의미를 바꾸지 않는다.
- **F-38 (context pressure ⊥ intensity)**: context band는 `unknown|normal|tight|critical`(`tight>=70`, `critical>=85`)의 관측·표시 신호다. band 변화는 title/NOW 표시, route/node state, intensity, stage graph, dispatch depth, model role/effort, QA/reviewer budget, test/verification, retry, completion gate, safety·permission guard를 변경하지 않는다. child와 parent는 각자 denominator를 사용하고 missing/stale/malformed 값은 `unknown`으로 정직 강등한다.
- **F-39 (보수적 title worker 상향)**: shared title/NOW scheduler의 기본 concurrency는 `3`, hard max는 `4`; rolling start budget은 기본·hard max 모두 `4 starts / 60s`; main debounce `600s`, child debounce `150s`는 유지한다. main/child와 default/custom provider는 같은 cross-process slot/start pool, per-session lock, stale-lease 회수, env/state kill switch를 공유한다. `FLEET_TITLE_COMMAND`의 shell-free argv template과 pluggable no-tools provider 계약을 유지하며, `--json`/`--once`/demo/test는 provider process를 시작하지 않는다.

Recommended locked-decision summary:

> **F-36~F-39 lock (v16)**: interactive/registered 공통 `work_projection`; exact route/node 우선·artifact inference 최후 fallback·ambiguity refusal; composed arbitrary DAG/parallel active-node 보존; 모든 폭의 `ctx … · NOW` detail row와 child-own telemetry(no parent inheritance); context pressure와 intensity 직교; title worker `3 concurrent (max 4)` + `4 starts/60s (max 4)`, main/child debounce `600/150s`, shared storm guards·pluggable no-tools provider·snapshot/test no-spawn.

## Acceptance-test matrix

| Area | Required fixture/assertion |
|---|---|
| Wide/narrow/stack | Render fixed `wide@168`, `narrow@100`, and `stack@60`; detail row follows the complete identity card, preserves `ctx` before NOW, precedes sub-agent strip, is display-cell safe, and never exceeds width. Assert NOW absent, context absent (`ctx —`), stale, and dead cases separately. |
| Child context | Exact `(pid,proc_start)` child join copies the child's context; parent and child with different percentages prove no inheritance. A unique harness+cwd fallback works; two children on one cwd yields `ctx —` and explicit ambiguity evidence. |
| Common projection parity | Feed equivalent exact route/node evidence once as an interactive `Session` observation and once as a jobs.log `DispatchJob`; normalized route/node/state/progress fields must match. Renderer group/process output must consume this result rather than call `live_stage()` independently. |
| Exact-over-artifact | Provide exact `route_node=research` while a conflicting code plan folder implies `test`; projection remains `research`, records the exact source, and never changes route/node from artifacts. Invalid/conflicting explicit route evidence becomes unknown/ambiguous, not artifact-derived. |
| Composed DAG | Use a sealed fork/fan-in route with opaque nodes `survey -> {claim-a,claim-b} -> synth`. Both siblings may be active simultaneously, record order is stable, progress counts are correct, and no `_PIPE_STAGES` labels appear. Also retain the existing lab fixture. |
| Ambiguity refusal | Two distinct route/node candidates for one leaf, two cwd fallback matches, and multiple gate candidates all fail closed. Separately prove that multiple active siblings inside one validated route are preserved, not mislabeled ambiguous. |
| Additive JSON | Existing `sessions`, `jobs`, `summary`, and `route` keys and all prior field meanings remain. Add `work_projection` and child `context`; absent evidence is null/unknown without deleting old fields. Snapshot consumers reading only old keys still pass. |
| Context orthogonality | Replay the same route and intensity at 69%, 70%, and 85%. Only context band/rendering changes; route graph, node state, intensity, model role/effort, QA, tests, and completion gates remain byte-equivalent. Missing/stale/decreasing telemetry becomes unknown. |
| Quota hermeticity | With a 200-session backlog, default starts are bounded by three live slots; after slots release, total starts in the same 60s never exceed four. Environment overrides clamp to concurrency four and starts four. The fifth start fails; a new start succeeds after the rolling window. Direct `run_worker()` cannot bypass either lease. |
| No live provider calls | Monkeypatch both `subprocess.Popen` and provider `subprocess.run` to fail if reached. Exercise `--json`, `--once`, demo, width fixtures, projection tests, and the 200-session storm fixture. No real/default/custom provider is invoked. Shell-free argv and default disallowed-tools assertions remain. |

## Risks and mitigation

- **Plain interactive sessions may have no exact route tuple.** Do not guess one from cwd or artifacts. Show the legacy inferred stage only when its plan directory is unique, with `source=artifact-inferred`; otherwise omit stage. This is an honest support boundary, not a parity failure.
- **Current first-match code hides both conflict and parallelism.** Replace `active_routed[0]` / first route-ID selection with the common resolver. A validated route with parallel nodes is a set; conflicting route IDs for one leaf are ambiguity.
- **Vertical density increases in narrow/stack.** Use one compact detail row, reserve the context token, clip only NOW, and omit the entire row for dead/stale. Do not duplicate a second gauge line.
- **PRD v15 contains stale title-budget numbers.** F-17 still mentions `16` starts in a `600s` window and the locked F-23 paragraph mentions older `4/16/600s` values, while current code is `3/3/60s`. v16 should replace those historical-current claims or label them explicitly superseded; F-39 becomes the current source of truth.
- **Custom providers cannot be made no-tools merely by `shell=False`.** Preserve the existing shell-free interface, keep the default provider's explicit tool denial, and require a custom wrapper to attest/enforce no-tools behavior. Do not claim runtime enforcement beyond that boundary.

## QA and command results

- `preflight.sh qa-policy standard general`: selected assurance is plan-check + independent selected pass + final verify; external adversary skipped. This bounded support worker is prohibited from dispatching another worker, so the reported fallback (`report-inline-review-if-independent-agent-unavailable`) was used. The inline review actively checked exact-evidence conflicts, parallel-DAG behavior, child misattribution, JSON compatibility, quota bypass, and live-provider leakage.
- `preflight.sh verification-runner --timeout 120 -- python3 utilities/compose_route.test.py`: **9/9 PASS**.
- `preflight.sh verification-runner --timeout 180 -- python3 -m unittest tools.fleet.tests.test_f28_route tools.fleet.tests.test_f28_breadcrumb tools.fleet.tests.test_f30_process_view tools.fleet.tests.test_f16_f17_subtitle tools.fleet.tests.test_f17_title_refresh tools.fleet.tests.test_f21_cross_harness_titles tools.fleet.tests.test_wide_ctx_gauge`: **157/157 PASS**.
- Total selected baseline checks: **166 PASS, 0 FAIL**. These validate the current contracts and fixtures; they do not implement or prove the proposed v16 behavior.
- `git status --short`: clean at evidence collection time.
- `preflight.sh read <canonical-prd> codex-headless`: the marker hook could not write `/home/Uihyeop/agent_setting/.spec-grounding/...` because that worker-visible location is read-only. The PRD itself was read successfully; this is recorded as an unsupported runtime guard detail, not silently claimed as satisfied.

## Changed files

- Project/source files: none.
- Spec files: none.
- Durable worker output only: `/home/Uihyeop/agent_setting/.agent_reports/shards/spec-research/fleet-unified-stage-ui/research.md`.

## Unsupported runtime-contract details

- The spec-read marker side effect was unavailable in this worker due the read-only `.spec-grounding` location.
- No independent reviewer process ran because the support-worker kernel forbids dispatch; QA used the policy's explicit inline-review fallback and records that limitation.
- No live title provider was called. Provider quota/cost behavior beyond the repository's hermetic lease logic was not empirically measured.
