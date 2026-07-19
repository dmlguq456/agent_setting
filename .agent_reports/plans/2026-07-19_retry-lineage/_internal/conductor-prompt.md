# Assignment — autopilot-code dev/standard conductor: SD-67 mutation 노드 재시도 계보 검증

You are the depth-1 capability owner (thin conductor) for one approved autopilot-code cycle.
Load `capabilities/autopilot-code.md` and the owner-execution reference, then run the
`plan → execute → test → report` stage graph. Do not re-select capability, intensity,
or topology (SD-45): they are fixed by the immutable route record below.

## Immutable route binding

- route file: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_retry-lineage/_internal/route.json`
- route_id: `rt-e6ed0326b81b2778`
- route_hash: `sha256:e6ed0326b81b27787cb00644071bdc99e2443fa79468722013f3a2a1fc916562`
- dispatch_contract_version: 3 (launch_authority=conductor)
- nodes: `plan → execute → test → report` (all depth 2)
- worktree (cwd, source writes): `/home/Uihyeop/agent_setting-wt/retry-lineage` (branch `retry-lineage`, base `main` @ `fb9a098f`)
- canonical plan root (artifact writes): `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_retry-lineage/`
- spec-significance: within-spec — governing item: `spec/stage-dispatch/prd.md` **§13.9.1 SD-67**
  (v17, 2026-07-19 등재). Read that section (canonical root spec path) before planning;
  record this line in the plan.

## Task — what to build

두 standard 사이클 연속으로 실측된 구조적 결함을 해소한다: execute(mutation 노드)가
커밋을 만든 뒤 재시도가 필요해지면 worker-route-guard의 `HEAD == source_commit` 정확
일치 pin이 launch를 거부하고(`route-source-commit-mismatch`), 승인된 탈출구(safety-commit
restore = `git reset --hard`)는 권한 분류기가 파괴적 복원으로 차단한다. SD-67은 SD-65의
계보 원칙을 결정론 재시도 증거로 게이트해 mutation 노드로 확장한다.

### (1) `utilities/worker-route-guard.py` — 재시도 계보 검증 (핵심)

`validate_route_contract`의 mutation 노드(worktree-mutating write_scope 보유, 현재
`HEAD ≠ source_commit`이면 무조건 거부) 검사를 다음으로 완화한다 — **세 조건 전부**일
때만 허용:

1. 해당 노드가 route record `resume_retry_boundaries`에 선언되어 있다.
2. **결정론 재시도 증거**: 바인딩된 전역 attempt registry(`AGENT_DISPATCH_JOBS` env)에
   동일 `route_id` + `route_node`의 **선행 attempt row**가 존재한다(현재 launch의
   attempt identity는 제외).
3. HEAD가 route cwd에서 `source_commit`의 first-parent 후손이다(기존
   `_is_first_parent_descendant` 재사용).

fail-closed 불변: registry 미설정·판독 불가·선행 row 부재 → 현행 정확 일치 요구.
발산·무관 HEAD·merge/rebase 진행 상태 차단 유지. post-mutation 노드의 SD-65 경로 불변.
route 재컴파일 우회 금지 불변.

### (2) wrapper 통합 — 현재 attempt 제외의 결정론화

가드는 `adapters/{claude,codex,opencode}/bin/dispatch-headless.py`의
`validate_route_record`가 subprocess로 호출한다. wrapper 흐름에서 route 검증과 attempt
row claim의 순서를 실측하고, **검증 시점에 현재 launch의 row가 이미 registry에 있으면**
가드가 그 row를 선행 증거로 오인하지 않도록 현재 attempt identity를 결정론적으로
제외하라(예: 가드에 `--current-attempt` 인자 추가 후 wrapper가 전달 — 검증이 claim보다
먼저면 인자는 optional로 두되 계약은 명시). wrapper 변경이 필요하면 3종 미러 동기.
가드의 registry 읽기는 read-only이며 registry 형식 파싱은 기존 dispatch 유틸을 재사용한다.

### (3) 소비 지침 현행화 (core-first 순서 준수)

- `core/OPERATIONS.md §5.10`: execute FAIL·부분 완료 후 conductor의 **in-place 재분사
  허용**(SD-67 3조건), `git reset --hard` 복원 금지 유지 명문화. **core 편집을
  스킬/어댑터 편집보다 먼저 커밋 순서에 배치하라(core-first gate).**
- autopilot-code dev-pipeline 레퍼런스의 Step 4 "safety-commit restore" 탈출구 서술을
  계보 완화 기반 재시도로 대체. `skills/`는 `adapters/claude/skills`의 미러 — 양쪽 동기.

### (4) 테스트

- `utilities/worker_route_guard.test.py` 확장 — spec acceptance 4건:
  ① 선행 execute attempt row(픽스처 registry) + execute 커밋의 first-parent 후손 HEAD
  → execute 재검증 통과 ② 선행 row 없는 첫 launch는 후손 HEAD여도 fail-closed
  ③ 발산 HEAD·registry 부재 fail-closed ④ SD-65 post-mutation 계보 기존 8 테스트 회귀 0.
- 현재 attempt 제외 케이스: registry에 현재 attempt row만 있을 때 → fail-closed.
- 기존 스위트 회귀 0: `worker_route_guard.test.py`, `dispatch_contract.test.py`,
  `dispatch_node.test.py`, sd15(sd15.test.sh)·sd45(sd45.test.py) 3종,
  `stage_dispatch_fallback.test.py`, `dispatch-route.test.sh`.

## Explicitly OUT of scope

SD-68(dispatch-defaults route compile 봉인 — 다음 사이클), 어댑터 투영 셀렉터 경로 수리,
권한 분류기 튜닝, `spec/**` 편집, capability-route.py compile 변경.

## Hard operational constraints

- guard/테스트 스위트는 **task worktree 안에서만** 실행. primary checkout에서 guard 금지.
- 소스 편집은 worktree만; 산출물은 canonical plan root에만.
- main 머지/push 금지. task 브랜치 커밋은 정상(safety commit + 구현 커밋).
- **주의**: 이 사이클이 구현하기 전까지 SD-67은 미적용이다 — 이 사이클 안에서 execute
  재시도가 필요해지면 여전히 구조적으로 차단된다. 그 경우 `git reset --hard`를 시도하지
  말고 남은 결함을 fix-forward 목록으로 정리해 정직하게 FAIL/BLOCKED 마감하라(depth-0가
  수확 시 fix-forward한다).
- evidence 자동 바인딩은 **구현 완료**(2026-07-17 머지) — dispatch-node가 record의
  checked tuple을 wrapper로 자동 전달하므로 스테이지 분사에 evidence 플래그를 수동으로
  넣지 마라.

## Stage dispatch mechanics

For each node, in order:

```bash
AGENT_DISPATCH_JOBS=/home/Uihyeop/agent_setting/.dispatch/jobs.log \
python3 /home/Uihyeop/agent_setting/utilities/dispatch-node.py \
  --route /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_retry-lineage/_internal/route.json \
  --node <plan|execute|test|report> --adapter <claude|codex> --action start \
  --slug retry-lineage-<stage> --parent retry-lineage --qa standard \
  --prompt-text "<stage contract: sub-skill name + absolute input paths + output contract + intensity standard + slug>" \
  -- --model-role "<node role>"
```

- Model roles: plan=`deep maker`, execute=`fast implementer`, test=`deep reviewer`, report=`fast writer`.
- Harness per node — **사용자 config(`profiles/dispatch-defaults.yaml`) 기본값 준수**:
  execute=`codex`(config), report=`claude`(config), test=diverse → maker와 다른 하네스,
  plan=미지정 → deep-maker affinity로 `codex` 권장. usage-check가 limited면 재조정하고
  사유를 기록하라(soft default).
- 분사 직전 `bash /home/Uihyeop/agent_setting/utilities/usage-check.sh` 확인.
- After each dispatch, poll in the same turn with
  `sh /home/Uihyeop/agent_setting/utilities/dispatch-wait.sh --parent retry-lineage`
  until exit 0 (exit 2 → poll again; exit 3 → diagnose then redispatch from artifacts).
  **One-shot 계약: 알림 대기로 turn을 끝내지 마라.** Then flip the harvested row, and write
  the completion marker before the next stage:
  `python3 /home/Uihyeop/agent_setting/utilities/capability-route.py complete --route <route.json> --node <id> --evidence <stage terminal artifact>`.
- Stage prompts carry absolute paths only. Sequential pipeline; conductor + one active stage.

## Completion

Write `pipeline_summary.md` (§5.8 lock) at the plan root before finishing.
Final output exactly three lines:

```
artifact: /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_retry-lineage/final_report.md
verdict: PASS | FAIL | BLOCKED
blocker: none | <one line>
```
