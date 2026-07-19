# Assignment — autopilot-code dev/standard REPLACEMENT conductor (SD-64 재개): SD-67 재시도 계보 검증

You are the **replacement** depth-1 capability owner for an in-flight autopilot-code cycle.
The original conductor died after dispatching `plan` (it ended its turn to "wait for a
Monitor event" — in `claude -p` one-shot mode that is process death). Per SD-64 you resume
from the route record + completion markers. Load `capabilities/autopilot-code.md` and the
owner-execution reference first.

## ⚠️ Liveness contract — read this before anything else

**You are a `claude -p` one-shot process. There is no next turn. The moment you end your
turn "to wait", you are dead and the pipeline is orphaned (this already happened once
this cycle).** Never use Monitor, never schedule wakeups, never end a message saying
"대기한다/기다린다". To wait for a stage: run
`sh /home/Uihyeop/agent_setting/utilities/dispatch-wait.sh --parent retry-lineage`
**synchronously in the same turn, repeatedly**, until it exits 0 (exit 2 → run it again
immediately; exit 3 → diagnose from artifacts and redispatch). Keep calling tools until
`pipeline_summary.md` is written and your three final lines are printed.

## Immutable route binding (unchanged)

- route file: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_retry-lineage/_internal/route.json`
- route_id: `rt-e6ed0326b81b2778`
- route_hash: `sha256:e6ed0326b81b27787cb00644071bdc99e2443fa79468722013f3a2a1fc916562`
- dispatch_contract_version: 3 (launch_authority=conductor)
- nodes: `plan → execute → test → report` (all depth 2)
- worktree (cwd, source writes): `/home/Uihyeop/agent_setting-wt/retry-lineage` (branch `retry-lineage`, base `main` @ `fb9a098f`)
- canonical plan root (artifact writes): `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_retry-lineage/`
- spec-significance: within-spec — governing item: `spec/stage-dispatch/prd.md` **§13.9.1 SD-67**.
  Read that section before orchestrating; record it in your gate notes.

## Resume state (verified by depth-0 at relaunch)

- `plan` (codex, att-11f2218c…): worker **finished; artifacts are in
  `<plan root>/plan/`**. Its registry row was closed and its completion marker written by
  depth-0 during recovery — verify the marker exists
  (`.dispatch/completion/rt-e6ed0326b81b2778/plan.json`) and **do not re-run plan** (SD-64:
  marker 있는 노드 재실행 금지). Read `plan/plan.md` + `plan/checklist.md` as your input.
- `execute`, `test`, `report`: not started. Run them in order, per the mechanics below.
- Original conductor's dead row is already reconciled; ignore it.

## Task being built (context for stage prompts)

SD-67: worker-route-guard의 mutation 노드 재시도 계보 검증. 상세 계약은 route-bound spec
§13.9.1과 plan 산출물에 있다. 요약: (1) `utilities/worker-route-guard.py` — mutation 노드
`HEAD ≠ source_commit` 허용 조건 = resume_retry_boundaries 선언 ∧ 전역 registry 선행
attempt row(현재 attempt 제외) ∧ first-parent 후손; registry 부재·선행 row 부재 → 정확
일치; 발산·merge/rebase fail-closed 불변. (2) wrapper 3종의 현재-attempt 제외 결정론화
(validate와 claim 순서 실측 후 필요시 `--current-attempt` 전달, 미러 동기).
(3) `core/OPERATIONS.md §5.10` 재시도 지침 현행화(**core-first 커밋 순서**) +
dev-pipeline Step 4 "safety-commit restore" 서술 대체(`skills/`↔`adapters/claude/skills`
미러 동기). (4) `worker_route_guard.test.py` acceptance 4건 + 현재-attempt-only 케이스 +
기존 스위트 회귀 0.

## Explicitly OUT of scope

SD-68(config compile 봉인), 셀렉터 경로 수리, 권한 분류기, `spec/**` 편집,
capability-route.py compile 변경.

## Hard operational constraints

- guard/테스트는 **task worktree 안에서만**. primary checkout에서 guard 금지.
- 소스 편집은 worktree만; 산출물은 canonical plan root에만. main 머지/push 금지.
- 이 사이클 안에서 execute 재시도가 필요해지면(SD-67은 아직 미적용) `git reset --hard`
  금지 — fix-forward 목록으로 정직하게 FAIL/BLOCKED 마감.
- evidence 자동 바인딩 구현 완료 — 스테이지 분사에 evidence 플래그를 수동으로 넣지 마라.

## Stage dispatch mechanics

For each remaining node (`execute` → `test` → `report`), in order:

```bash
AGENT_DISPATCH_JOBS=/home/Uihyeop/agent_setting/.dispatch/jobs.log \
python3 /home/Uihyeop/agent_setting/utilities/dispatch-node.py \
  --route /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_retry-lineage/_internal/route.json \
  --node <execute|test|report> --adapter <claude|codex> --action start \
  --slug retry-lineage-<stage> --parent retry-lineage --qa standard \
  --prompt-text "<stage contract: sub-skill name + absolute input paths + output contract + intensity standard + slug>" \
  -- --model-role "<node role>"
```

- Model roles: execute=`fast implementer`, test=`deep reviewer`, report=`fast writer`.
- Harness per node — 사용자 config 기본값: execute=`codex`(config), test=diverse →
  maker(plan=codex)와 실행 스테이지 관점에서 **execute 하네스와 다른 것**을 골라라
  (execute=codex면 test=claude), report=`claude`(config). usage-check limited면 재조정
  후 사유 기록.
- 분사 직전 `bash /home/Uihyeop/agent_setting/utilities/usage-check.sh`.
- 각 스테이지 수확 후: row flip → completion marker:
  `python3 /home/Uihyeop/agent_setting/utilities/capability-route.py complete --route <route.json> --node <id> --evidence <stage terminal artifact>`.
- Stage prompts carry absolute paths only. Sequential; conductor + one active stage.

## Completion

Write `pipeline_summary.md` (§5.8 lock) at the plan root before finishing — include the
SD-64 orphan/replacement history honestly. Final output exactly three lines:

```
artifact: /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_retry-lineage/final_report.md
verdict: PASS | FAIL | BLOCKED
blocker: none | <one line>
```
