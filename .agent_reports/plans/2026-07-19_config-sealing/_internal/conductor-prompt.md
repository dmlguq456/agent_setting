# Assignment — autopilot-code dev/standard conductor: SD-68 dispatch-defaults의 route record 봉인 배선

You are the depth-1 capability owner (thin conductor) for one approved autopilot-code cycle.
Load `capabilities/autopilot-code.md` and the owner-execution reference, then run the
`plan → execute → test → report` stage graph. Do not re-select capability, intensity,
or topology (SD-45): they are fixed by the immutable route record below.

## ⚠️ Liveness contract — read this before anything else

**You are a `claude -p` one-shot process. There is no next turn. The moment you end your
turn "to wait", you are dead and the pipeline is orphaned (measured twice on 2026-07-19).**
Never use Monitor, never schedule wakeups, never end a message saying "대기한다". To wait
for a stage: run `sh /home/Uihyeop/agent_setting/utilities/dispatch-wait.sh --parent config-sealing`
**synchronously in the same turn, repeatedly** until exit 0 (exit 2 → run again immediately;
exit 3 → diagnose from artifacts, then redispatch). Keep calling tools until
`pipeline_summary.md` is written and your three final lines are printed.

## ⚠️ Registry hygiene

After harvesting each stage: **flip the harvested row to done first, then write the
completion marker, then dispatch the next stage.** Do not leave harvested rows open.

## Immutable route binding

- route file: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_config-sealing/_internal/route.json`
- route_id: `rt-d57cbb149952fd3d`
- route_hash: `sha256:d57cbb149952fd3db6bc2f05da0890dd26e955fa6aad2c821c6784e63572938f`
- dispatch_contract_version: 3 (launch_authority=conductor)
- nodes: `plan → execute → test → report` (all depth 2)
- worktree (cwd, source writes): `/home/Uihyeop/agent_setting-wt/config-sealing` (branch `config-sealing`, base `main` @ `ecd3acd8`)
- canonical plan root (artifact writes): `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_config-sealing/`
- spec-significance: within-spec — governing item: `spec/stage-dispatch/prd.md` **§13.9.2 SD-68**
  (v17, 2026-07-19 등재 — SD-66 2단계 유보 해제). Read that section (canonical root spec
  path) before planning; record this line in the plan.

## Task — what to build

SD-66 1단계는 selector(dispatch-route.sh)만 config를 소비한다. 2단계(SD-68)는 config를
**route record에 컴파일 시점 스냅샷으로 봉인**해 conductor가 record에서 기본 하네스를
읽고, 실제 선택과의 이탈이 registry row 단위로 감사 가능해지는 것이다.

### (1) `utilities/capability-route.py` — compile 봉인 (핵심)

- `compile_route`가 검증된 dispatch-defaults config(`profiles/dispatch-defaults.yaml`,
  `DISPATCH_DEFAULTS_CONFIG` env 픽스처 오버라이드는 기존 loader 의미 유지)를 로드해:
  1. 각 **depth-2 stage 노드**에 `harness_affinity` 스탬프 — config 어휘 그대로
     `claude|codex|opencode|diverse`, 해당 capability×stage 칸 미지정·config 부재 =
     `unspecified`. 스탬프는 **route_hash 계산 전**에 노드에 들어가 hash로 봉인된다.
  2. record 상단에 `dispatch_defaults_digest` — 컴파일에 소비된 config의 결정론
     digest(sha256), config 부재 시 `null`. canonicalization 방식은 결정론적이고
     문서화되어야 한다(구현 선택은 plan 소관 — 원시 바이트 vs 정규화 파싱 결과 중
     택일하되 사유 기록).
- **`verify_route`는 config를 재로드하지 않는다** — hash 봉인 검증만. 사후 config 변경이
  기존 route를 무효화하면 안 된다. `harness_affinity` 필드가 있으면 어휘 유효성
  (`claude|codex|opencode|diverse|unspecified`)은 검증하되, 필드가 없는 **기존 route는
  하위호환으로 통과**해야 한다(구 route 회귀 0).
- 손상 config는 compile fail-loud(기존 validator 재사용), 부재는 전부 `unspecified`+digest null.
- `registry_digest`(topology pin)와 절대 섞지 마라 — 별도 필드다.
- loader 소비는 `utilities/dispatch-defaults.py`의 기존 API/CLI 재사용 — capability×stage
  전체 맵이 필요하면 최소한의 함수/서브커맨드 추가는 허용(스키마·어휘 변경 금지).

### (2) `utilities/dispatch-node.py` — row 계측

- record 노드에 `harness_affinity`가 있으면 registry row에 `harness_affinity=<값>`을
  기록해 실제 `harness=`와의 이탈이 행 단위로 감사 가능하게 하라. 구현 방식은 plan
  소관(예: wrapper 인자 전달 vs 시작 후 `dispatch_contract.annotate_attempt_row`) —
  단 **차단 장치 신설 금지**: affinity와 다른 explicit `--adapter`도 그대로 통과(soft
  default, SD-22 우선순위 explicit > hard eligibility > record affinity > heuristic 불변).
- 필드 없는 record(구 route)는 현행 동작 불변.

### (3) 테스트 — spec acceptance 5건

`utilities/capability_route.test.py`(+ 필요시 `dispatch_node.test.py`) 확장:
① compile 산출 route의 depth-2 노드 전부에 유효 어휘 `harness_affinity` 존재
② 픽스처 config 값 변경 → 신규 compile의 `route_hash` 변화(봉인 입증)
③ 스탬프된 기존 route는 config 사후 변경에도 `verify` 통과(재로드 없음 입증)
④ dispatch-node 경유 시 row에 `harness_affinity` 기록
⑤ explicit `--adapter`가 affinity와 달라도 launch 통과(soft)
+ 필드 없는 구 route verify 하위호환 + 기존 스위트 회귀 0:
`capability_route.test.py`, `dispatch_node.test.py`, `dispatch_contract.test.py`,
`worker_route_guard.test.py`, sd45 3종, sd15 3종(**bash로 실행**), `dispatch-route.test.sh`.

### (4) 소비 지침 (core-first 순서 준수)

`core/OPERATIONS.md §5.10`의 SD-16/SD-66 소비 규칙에 record affinity 소비를 한 문장
현행화: conductor는 record의 `harness_affinity`를 1차 후보로 소비하고 이탈 시 사유를
기록한다(soft, 차단 없음). **core 편집을 utilities 편집보다 먼저 커밋하라.**

## Explicitly OUT of scope

selector 캐스케이드 의미 변경(1단계 불변 존속), `profiles/dispatch-defaults.yaml` 값 변경,
worker-route-guard, wrapper 3종의 신규 검증 게이트, 권한 분류기, `spec/**` 편집.

## Hard operational constraints

- guard/테스트는 **task worktree 안에서만**. primary checkout에서 guard 금지.
- 소스 편집은 worktree만; 산출물은 canonical plan root에만. main 머지/push 금지.
- 테스트가 만든 `adapters/**/__pycache__`는 커밋 전 삭제(boundary guard가 잡는다).
- execute FAIL 후 재시도: **SD-67이 main에 있다** — 같은 route에서 새 attempt로
  in-place 재분사 가능. `git reset --hard` 금지.
- **주의**: 이 사이클의 route record 자체는 SD-68 구현 전에 컴파일됐으므로
  `harness_affinity` 필드가 없다 — 정상이며, 구 route 하위호환 경로로 소화된다.

## Stage dispatch mechanics

For each node, in order:

```bash
AGENT_DISPATCH_JOBS=/home/Uihyeop/agent_setting/.dispatch/jobs.log \
python3 /home/Uihyeop/agent_setting/utilities/dispatch-node.py \
  --route /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_config-sealing/_internal/route.json \
  --node <plan|execute|test|report> --adapter <claude|codex> --action start \
  --slug config-sealing-<stage> --parent config-sealing --qa standard \
  --prompt-text "<stage contract: sub-skill name + absolute input paths + output contract + intensity standard + slug>" \
  -- --model-role "<node role>"
```

- Model roles: plan=`deep maker`, execute=`fast implementer`, test=`deep reviewer`, report=`fast writer`.
- Harness per node — config 소비 + 실측 이탈 사유:
  - plan=`codex`(deep-maker affinity). 알려진 제약: codex 워커가 primary
    `.spec-grounding`에 못 써 BLOCKED될 수 있다 — 그 경우 fallback으로 claude 재분사
    (직전 사이클과 동일 대응).
  - execute: config는 `codex`지만 **이탈하여 `claude`** — 사유: "2026-07-19 실측 —
    codex workspace-write 샌드박스는 linked worktree git metadata read-only로 커밋 불가".
  - test: diverse → `codex`(execute=claude와 다름). 아티팩트 영속화 실패 시 로그에서
    salvage해 `test_logs/`에 영속화.
  - report=`claude`(config).
- 분사 직전 `bash /home/Uihyeop/agent_setting/utilities/usage-check.sh` 확인.
- 각 스테이지: dispatch-wait 동기 반복 → row flip → completion marker
  (`python3 /home/Uihyeop/agent_setting/utilities/capability-route.py complete --route <route.json> --node <id> --evidence <terminal artifact>`)
  → 다음 스테이지.
- Stage prompts carry absolute paths only. Sequential; conductor + one active stage.

## Completion

Write `pipeline_summary.md` (§5.8 lock) at the plan root before finishing.
Final output exactly three lines:

```
artifact: /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_config-sealing/final_report.md
verdict: PASS | FAIL | BLOCKED
blocker: none | <one line>
```
