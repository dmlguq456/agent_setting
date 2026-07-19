# Assignment — autopilot-code dev/standard conductor: 분사 하네스 기본값 config(SD-66) + 크로스 하네스 수리 2건

You are the depth-1 capability owner (thin conductor) for one approved autopilot-code cycle.
Load `capabilities/autopilot-code.md` and the owner-execution reference, then run the
`plan → execute → test → report` stage graph. Do not re-select capability, intensity,
or topology (SD-45): they are fixed by the immutable route record below.

## Immutable route binding

- route file: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_dispatch-defaults-config/_internal/route.json`
- route_id: `rt-20f4481665281810`
- route_hash: `sha256:20f44816652818107c3dcd8aa3120967202c12a21961c63aacc5be3372f87dde`
- dispatch_contract_version: 3 (launch_authority=conductor — 모든 depth-2는 adapter wrapper를 네 프로세스에서 직접 one-shot 실행; broker 없음)
- nodes: `plan → execute → test → report` (all depth 2)
- worktree (cwd, source writes): `/home/Uihyeop/agent_setting-wt/dispatch-defaults-config` (branch `dispatch-defaults-config`, base `origin/main` @ `3ebd1c77`)
- canonical plan root (artifact writes): `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_dispatch-defaults-config/`
- tracked gate evidence rides in the route record; `spec-significance: within-spec`
  (governing spec: `spec/stage-dispatch/prd.md` **v16 §13.8 SD-66** — 이 worktree HEAD에 포함됨. plan에 이 줄을 기록.)

## Task — what to build

크로스 하네스 자유 분사를 사용자 config로 통제 가능하게 만드는 SD-66 구현 + 검증에서 발견된 수리 2건.

### (A) `profiles/dispatch-defaults.yaml` 신설 + 로더/셀렉터 배선 (핵심)

PRD v16 §13.8.1 SD-66이 계약의 SoT다 — 구현 전에 worktree의
`.agent_reports/spec/stage-dispatch/prd.md` §13.8을 읽어라(주의: worktree는 source-only,
spec은 canonical root `/home/Uihyeop/agent_setting/.agent_reports/spec/stage-dispatch/prd.md`에서 읽는다).

1. **`profiles/dispatch-defaults.yaml`** — 사용자 편집용 단일 파일:
   - 값 어휘: `claude | codex | opencode | diverse` | 키 생략(=미지정, 오케스트레이터 재량).
   - `depth1_owner: [claude, codex]` 허용집합(단일값 아님).
   - capability×stage 키: `capabilities/topologies.json`의 entry capability들의 stage 노드를 열거해
     스캐폴드하되, 근거 없는 칸은 **생략**한다(빈 키를 채우지 말 것).
   - 초기값(PRD v16 고정): `autopilot-code: {exec: codex, test: diverse, review: diverse, report: claude}`
     (plan은 미지정 — 키 자체를 넣지 않음). 다른 capability는 전부 미지정으로 시작.
   - 전역 `opencode: relief-only` 정책 키(주석으로 1~2% 목표·자동승인 전제 명기).
   - concrete model/effort 금지 — 하네스 이름만. 스키마 주석으로 명문화.
2. **스키마 검증기** — 작은 파이썬 유틸(`utilities/dispatch-defaults.py` 또는 dispatch-route.sh 내
   로더와 함께, 설계는 plan 판단): 어휘 검증, capability/stage 키가 topologies.json에 실존하는지,
   모델명 금지, depth1_owner 집합 검증. 위반은 fail-loud.
3. **`utilities/dispatch-route.sh` 배선** — 하드코드 stage affinity case문(`plan|planning|...→codex`,
   `*review*|*test*→diverse`)을 이 파일 로딩으로 치환. 결정 캐스케이드 순서는 불변:
   explicit `--adapter` > `--family` > **config affinity(신규 소스)** > bias. config 미지정 칸은
   현행 `neutral`과 동일 동작. yq 의존 금지 — POSIX sh + python3 원라이너 수준 유지.
4. **`utilities/dispatch-route.test.sh` 갱신** — 기존 하드코드 기대값을 config 픽스처 기반으로 전환:
   config 값 반영, 미지정 칸 재량(neutral), diverse 해석(maker family와 다른 하네스),
   depth1_owner 집합, opencode relief-only(기본 후보에서 제외), 잘못된 config fail-loud.
   테스트는 임시 fixture config를 써서 repo 기본값 변경에 취약하지 않게.
5. **`core/OPERATIONS.md` §5.10 SD-16 항목에 컨덕터 소비 규칙 추가** (core-first: core 문서를
   adapter/유틸보다 먼저 커밋 서사에 배치): "dispatch-defaults.yaml은 SD-22 우선순위 3단계
   stage affinity의 사용자-선언 소스다. explicit choice와 hard eligibility(usage limit 포함)가
   항상 우선하고, 오케스트레이터는 더 적절한 하네스를 **사유 기록 후** 선택할 수 있다(soft default).
   미지정 칸은 재량이다." 간결한 영문 1~3문장.

### (B) 수리 1 — g9 드릴 케이스 owner parent_sid 단정 드리프트

`loops/drill/cases_growing/g9_cross_harness_depth2_dispatch/`:
codex 래퍼 `_bind_runtime_parent()`(adapters/codex/bin/dispatch-headless.py)는 depth-1 owner의
`--parent-session-id`를 **의도적으로** 실제 `CODEX_THREAD_ID`로 덮어쓴다(2026-07-16 드릴 FAIL 실측:
owner row parent_sid='019f...' vs 기대 'drill-parent-session'). 케이스를 이 계약에 맞춰 수정:
- assert.sh: **owner row**의 parent_sid는 리터럴 'drill-parent-session'이 아니라
  "비어있지 않고 [A-Za-z0-9_.:-]+이며, 가능하면 transcript의 실제 codex thread id와 일치"로 완화.
  **depth-2 children rows는 현행 'drill-parent-session' 정확 일치 유지**(래퍼가 depth-2 explicit
  envelope을 보존하는 계약의 검증이므로).
- prompt.md: owner 등록 지시에서 `--parent-session-id drill-parent-session`을 유지하되
  "codex 래퍼는 depth-1 owner를 실제 runtime thread에 바인딩하므로 owner row의 parent_sid가
  달라지는 것이 정상"이라는 한 줄 주석 추가(에이전트 혼란 방지).
- adapters/claude/loops/drill/ 미러가 있으면 동기화.

### (C) 수리 2 — SD-48 evidence 보충 지침 공백

2026-07-16 g10 드릴 실측: depth-1 owner가 `preflight.sh nested-headless`로 checked evidence
(`status=supported`)를 얻고도, 그 플래그를 `--start`에 보충하는 것을 "승인 필요한 변경"으로
오판해 정지 → child 미시작. `core/OPERATIONS.md` §5.10 SD-48 항목에 명시 한 줄 추가(영문):
"Supplementing a `--start` invocation with the checked evidence flags obtained from the
documented `nested-headless` probe is the required procedure, not a gate bypass; workers
proceed without re-confirmation even when a caller-provided argument list omitted those flags."
(단, dispatch-node.py가 record evidence를 자동 전달하는 v15 경로가 이미 있으므로, 이 지침은
record 밖 수동 wrapper 호출 경로에 적용됨을 문구로 한정.)

### (D) 검증-only — codex auth probe stderr 수용

`utilities/nested-dispatch-eligibility.py::auth_check`는 이미 stdout∨stderr 수용으로 수정돼
있다(직전 머지). 이번 사이클에서는 **재구현하지 말고**: ① 회귀 테스트가
`nested_dispatch_eligibility.test.py`에 있는지 확인, 없으면 "codex login status가 stderr로만
출력해도 supported" 케이스 추가. ② test 스테이지에서 `--child-harness codex` probe가 실제
`supported`를 반환함을 실측 기록.

## Explicitly OUT of scope

route hash 봉인 경로(`capability-route.py` compile/topology)에 config 배선(2단계로 유보),
`spec/**` PRD 편집(v16은 이미 등재됨), broker 잔재 정리, Fleet UI 변경,
`profiles/*.yaml` 기존 stage 프로파일의 harness 필드 의미 변경.

## Hard operational constraints

- guard/드릴/테스트 스위트는 **오직 task worktree 안에서만** 실행. primary checkout
  `/home/Uihyeop/agent_setting`에서 guard 실행 금지(라이브 상태 회전 실측 2026-07-15).
- 소스 편집은 worktree만; plan/dev/test/report 산출물은 canonical plan root
  (`AGENT_ARTIFACT_ROOT`)에만. worktree의 `.agent_reports/` 스냅샷 write는 fail-closed.
- main 머지/push 금지 — depth-0 main이 수확·통합한다. task 브랜치 커밋(safety commit +
  구현 커밋)은 정상. 커밋 서사는 core-first(§(A)5가 유틸 변경보다 앞).
- g9/g10 드릴 재실행은 이 사이클 범위 밖 — depth-0 main이 수확 후 통합 검증으로 실행한다.

## Stage dispatch mechanics

For each node, in order, dispatch a depth-2 headless stage with:

```bash
python3 /home/Uihyeop/agent_setting/utilities/dispatch-node.py \
  --route /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_dispatch-defaults-config/_internal/route.json \
  --node <plan|execute|test|report> --adapter <claude|codex> --action start \
  --slug dispatch-defaults-config-<stage> --parent dispatch-defaults-config --qa standard \
  --prompt-text "<stage contract: sub-skill name + absolute input paths + output contract + intensity standard + slug>" \
  -- --model-role "<node role from route>"
```

- Model roles: plan=`deep maker`, execute=`fast implementer`, test=`deep reviewer`, report=`fast writer`.
- **Harness per node (SD-22 affinity + diverse checker; usage-check가 limited면 재조정)**:
  plan=`codex`(GPT family deep-maker affinity), execute=`claude`(repo 관용구 밀착·멀티파일),
  test=`codex`(maker=claude와 다른 family), report=`claude`. 이 배치 자체가 이번 사이클이
  구현하는 크로스 하네스 기본값의 도그푸딩이다 — 하네스 선택 사유를 metrics.md에 한 줄씩 기록.
- 분사 직전 `bash /home/Uihyeop/agent_setting/utilities/usage-check.sh`로 양쪽 상태 확인;
  limited인 하네스는 회피하고 사유 기록.
- After each dispatch, poll in the same turn with
  `sh /home/Uihyeop/agent_setting/utilities/dispatch-wait.sh --parent dispatch-defaults-config`
  until exit 0 (exit 2 → poll again; exit 3 → diagnose via transcript/log tails, then redispatch
  from existing artifacts). **One-shot 계약(SD-14): 알림 대기로 turn을 끝내지 마라 — 같은 turn에서
  폴링 후 수확까지.** Then flip the harvested row `open → done` in jobs.log, and write the
  completion marker before the next stage:
  `python3 /home/Uihyeop/agent_setting/utilities/capability-route.py complete --route <route.json> --node <id> --evidence <stage terminal artifact>`.
- Stage prompts carry absolute paths only — no plan bodies, no prior-stage conversation.
- Concurrency: this pipeline is sequential; conductor + one active stage.
- code-test verdict FAIL → one bounded retry per dev-pipeline Step 4 (safety-commit restore,
  memo, one code-refine, redispatch execute+test). Second failure → rollback, failed
  pipeline_summary, stop before report.

## Completion

Write `pipeline_summary.md` (§5.8 lock for shared singletons) at the plan root before finishing.
Final output exactly three lines:

```
artifact: /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_dispatch-defaults-config/final_report.md
verdict: PASS | FAIL | BLOCKED
blocker: none | <one line>
```
