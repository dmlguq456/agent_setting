# stage-dispatch — Spec (PRD)

> mode: **library + cli** (하네스 인프라 — 스테이지 분사 계약 문서 + dispatch wrapper·jobs.log·fleet 관제) · 작성 2026-07-10 · v1 · **v2 2026-07-10** (Phase 2 결정 등재 — SD-10~13·SD-OPEN-2. Phase 1 main 머지 5b7cf33 반영: 계약 12표면 개정 + wrapper depth-aware + pilot 계측 plan 218s/execute 255s/test 46s/report 28s·conductor 프롬프트 ~2KB 일정) · **v6 2026-07-13** (사용자 승인 topology 변경: `quick` = depth-1 one-shot capability worker, depth-2 금지, headless 우선/Fleet 표시) · **v7 2026-07-13** (standard+ conductor deep orchestration 기본·family/role 기반 route-dispatch 계약·Fleet hotfix 수용 기준) · **v8 2026-07-14** (source-only worker worktree·canonical artifact root·merge/push 후 fail-closed cleanup) · **v9 2026-07-15** (capability-specific topology registry·route record·promotion signals·detached/governor/smoke/report/parity 계약) · **v10 2026-07-15** (tracked×dispatch 축 분리 — Tracking 다섯째 독립 축·worker manifest-consumer 계약·guard↔topology 정합성 validator·공유 tracked 표면 병렬 계약) · **v11 2026-07-15** (중첩 stage-dispatch 복원력 — nested child-spawn hard eligibility·canonical global attempt registry·cross-harness stage fallback 사슬) · **v12 2026-07-15** (하네스 중립 depth-0 launch broker — 공통 요청·lifecycle·4조합 배치 계약) · **v13 2026-07-16** (broker 접수·실행 동시성 분리 — HOL blocking 해소·route record broker-identity 결합 해제(contract v2)·completion gate 통과 marker 의무화) · **v14 2026-07-16** (운영 병목 해소 1차 — broker 생존증거 위계·sandbox-독립 도달성(SD-57), worker 진행 감시(SD-58, O5 흡수), capacity failover(SD-59), registry reconciliation(SD-60))
> · **v15 2026-07-16** (broker retirement — 신규 route의 direct headless 기본화·Codex network-enabled conductor profile·단일 attempt identity·v1/v2 read-only migration)
> · **v16 2026-07-16** (사용자 하네스 기본값 config — SD-66 `profiles/dispatch-defaults.yaml` 신설, SD-OPEN-3 가중 정책의 사용자-선언 해소, SD-22 stage-affinity의 데이터 외부화, depth-1 owner 허용집합 [claude,codex], OpenCode relief-only)
> · **v17 2026-07-19** (재시도 계보·config 봉인 — mutation 노드 재시도의 first-parent 계보 검증(SD-67), dispatch-defaults의 route record 봉인 배선(SD-68 — SD-66 2단계 유보 해제))
> · **v18 2026-07-19** (conductor 생존·Codex linked-worktree mutation 경계·completion marker↔attempt row 결합 — SD-69~71)
> · **v19 2026-07-20** (transient PID namespace lifecycle — foreground-scoped wrapper·outer-sandbox 경계·exact parent·unmatched depth-2 visibility, SD-72) · **v19 reliability minor 2026-07-20** (sandbox-init terminal handoff·canonical transport·same-route fallback·exact-attempt liveness)
> · **v20 2026-07-20** (`quick` registered-headless-only fail-closed·portable `dispatch_depth` namespace·Codex/Claude execution-surface terminology, SD-73~75; SD-19 superseded)
> 컴포넌트: `agent_setting` repo 의 **autopilot 파이프 디스패치 토폴로지 개정** — 각 sub-skill 스테이지(code-plan / code-execute / code-test / code-report)를 `standard+` 에서 **기본으로 별개 headless 세션**으로 분사하는 계약. 기존 `spec/prd.md`(Unified Memory System)·`spec/harness-layer-sync/`·`spec/dispatch-profiles/`·`spec/agent-fleet-dashboard/` 와 무관한 독립 청사진. 이 폴더(`spec/stage-dispatch/`)가 자체 SoT.
> 입력(1순위 근거):
> - **사용자 승인 결정 (2026-07-20 v20)**: `effective_intensity=quick` 인 모든 route는 registered headless worker session만 사용한다. `native-subagent`, `inline-fallback`, interactive/empty, unknown/arbitrary surface는 compile 단계에서 fail-closed이며 dispatch depth로 이름 붙이지 않는다. `direct` inline과 `standard+` fallback은 유지한다. portable nesting은 `dispatch_depth`/`max_dispatch_depth`로 한정하고 Codex `agents.max_depth`와 분리한다. Claude subagent, Claude agent-team teammate session, registered headless worker session을 구별하며 multi-capability composition은 추가하지 않는다.
> - **v20 근거**: `documents/2026-07-20_depth1-surface-terminology-audit.md` + registered depth-2 research `shards/spec-research/depth1-surface-terminology.md` + independent review `reviews/spec/spec-verdict.json`. Review의 V20-R1~R6을 본 transaction에서 모두 해소한다.
> - **사용자 결정 (2026-07-10 확정)**: "스킬 단위의 처리가 분사해서 할 것을 기본 지침으로 했으면 한다. 어차피 산출물 기반 소통인데." — 입도 = sub-skill 스테이지 단위, 적용 = `standard+`, 이는 2026-07-06 depth 재설계 기본값의 명시적 반전.
> - **사용자 결정 (2026-07-13 확정)**: `direct` 는 depth-0 inline 유지, `quick` 은 depth-0 실행에서 **단일 depth-1 one-shot capability worker** 로 이동한다. quick worker 는 micro-plan·plan-check-lite·implementation·focused verification·concise report 를 한 세션에서 끝내며, **depth-2 를 열지 않는다**. `standard+` 는 기존 depth-0 main → depth-1 conductor → 순차 depth-2 stage-worker topology 유지.
> - **사용자 결정 (2026-07-13 v7 확정)**: depth-1 `standard+` conductor 는 high-reasoning/deep orchestration 을 기본으로 하고 fast orchestration 은 mechanical-only 로 한정한다. planning/architecture/decomposition 은 Codex의 GPT family + `deep maker` affinity 를 우선하되 hard pin 하지 않으며, plan review 는 maker 와 다른 family 를 선호한다. 라우팅 우선순위·read-only helper 계약과 Fleet 오탐 hotfix 수용 기준을 본 v7에 고정한다.
> - **사용자 결정 (2026-07-14 v8 확정)**: agent 산출물은 task worktree에 쓰지 않는다. worker는 main checkout의 canonical artifact root만 읽고 쓰며, main/orchestrator는 merge·통합 검증·push를 증명한 뒤 안전 조건을 모두 통과한 worktree를 자동 정리한다. runtime 종료 hook은 정리 권위자가 아니다.
> - **공식 Codex 근거 (2026-07-13 확인 시도)**: OpenAI Codex manual `https://developers.openai.com/codex/codex-manual.md#execution-model-and-workflows` / Subagents 섹션은 subagent workflow 가 noisy work 를 main thread 밖으로 옮겨 context pollution 을 줄이고, 병렬 read-heavy 작업에 유용하지만 write-heavy 병렬은 충돌·조정비용 주의가 필요하며 각 subagent 가 자체 model/tool work 를 하므로 single-agent 대비 token 을 더 쓴다고 설명한다. skill helper 는 `x-content-sha256` 헤더 누락으로 실패했으나 `/tmp/openai-docs-cache/codex-manual.md` 에서 해당 공식 manual 섹션을 확인했다.
> - **공식 모델 currentness 근거 (2026-07-13 확인)**: OpenAI Models 문서는 최신 권장 시작점으로 GPT-5.6 Sol을 복잡한 reasoning/coding에 안내하고 exact model ID=`gpt-5.6-sol`, API alias=`gpt-5.6`으로 게시한다. 단 API alias 게시와 Codex ChatGPT runtime 허용 ID는 별도 표면이다. parent 실측에서 Codex ChatGPT surface는 `gpt-5.6` alias를 거부했고 이 환경은 exact `gpt-5.6-sol`을 지원했다. 따라서 adapter는 현재 runtime에 exact ID를 probe한 뒤 성공한 ID만 선택하고, 실패 시 다음 eligible 후보로 깨끗하게 fallback해야 한다.
> - **로컬 runtime 근거 (parent 검증 완료, 2026-07-13)**: Codex native subagent check ok, strict headless projection restored/check ok, quick depth-1 dispatch dry-run accepted, quick depth-2 remains forbidden.
> - research `.agent_reports/research/cross-platform-agent-frameworks/` — `analysis_summary.md` §4-(8)(fresh-context-per-agent + file-state 지배 관용구), `cards/gsd.md`(fresh-context subagent per stage·`.planning/` file-state·two-stage routing·size-budget), `06_implementation.md`(파일-복제 회피·parity 정직성).
> - 운영 실증 (2026-07-10, 이 결정의 직접 계기): ① in-session Task 서브에이전트 = jobs.log 미등록 → fleet 관제에 스테이지 진행 불가시 ② in-session 서브에이전트는 hook ceremony(가드·spec 게이트) 미수령 ③ owner 단일 세션 = 스테이지 누적 컨텍스트 비대.
> - 현행 계약 실측 (2026-07-10, 본 워크트리): `core/OPERATIONS.md §5.10`·`§5.8`, `core/CONVENTIONS.md §1`·`§2`, `core/WORKFLOW.md §1.1`·`§5`, `core/DESIGN_PRINCIPLES.md §8`, `skills/autopilot-code/references/{dev-pipeline,context-and-guards}.md` + sub-skills, `adapters/claude/bin/dispatch-headless.py`, `adapters/{claude,codex,opencode}` bootstrap §0(C)/AGENTS.md.
> - **진단 입력 (2026-07-15, v10)**: `../../plans/2026-07-15_capability-routing-topology/_internal/tracked-dispatch-conflict-diagnosis.md` — main 세션 분석 + Codex 교차 진단 통합(인용 근거는 현행 소스 실측 검증). tracked(산출물 차원 불변식)와 분사(실행 차원 토폴로지)는 직교 계약이나, ① tracked→intensity/dispatch 축 결합(`WORKFLOW.md:165`·`CONVENTIONS.md:26-33`) ② tracked 집행 장치(hook·read marker·routing reminder)의 세션 지역성이 충돌 원천. 마찰면 F1~F7 중 D1~D4가 미반영 delta.
> - **사용자 결정 (2026-07-15 v10 확정)**: Tracking 축 분리는 채택하되 quick 경계는 **현행 유지(옵션 (a))** — 애매한 작업은 inline이 아니라 quick depth-1로 기운다(메인 컨텍스트 보호 우선). Codex inline 권고(옵션 (b) — 명확한 독립 작업 패키지 없으면 inline)는 기각. 2026-07-13 SD-18 결정의 재확정.
> - **운영 진단 (2026-07-15 v11)**: `../../plans/2026-07-15_stage-dispatch-v10/_internal/codex-nested-dispatch-diagnosis.md` + `.dispatch/logs/stage-dispatch-v10.codex.jsonl` + cycle/global jobs registry 대조. Codex depth-1 conductor 안의 depth-2 `codex exec` 6회가 network `Operation not permitted`로 실패했고, 모든 시도는 최초 dry-run부터 cycle-local `--jobs`를 명시해 전역 Fleet registry를 우회했으며, same-harness 실패 뒤 cross-harness child를 시도하지 않고 inline으로 내려갔다.
> - **공식 Codex currentness (2026-07-15 v11 확인)**: 공식 Codex manual은 native subagent의 `agents.max_depth`(기본 1), subagent sandbox 상속, `codex exec` 비대화형 실행, `workspace-write`의 기본 network-off와 subprocess까지 적용되는 network policy를 문서화한다. 그러나 sandboxed `codex exec` 안에서 다시 `codex exec`를 실행하는 nested headless 지원은 보장하지 않는다. 따라서 native subagent eligibility와 registered nested-headless eligibility를 별도 runtime surface로 취급한다.
> - **사용자 결정 (2026-07-15 v12 확정)**: depth-1과 depth-2에 Claude Code·Codex를 자유롭게 배치할 수 있어야 하며, 한 runtime의 재귀 호출 가능 여부가 topology 의미를 바꾸면 안 된다. `Claude→Claude`, `Claude→Codex`, `Codex→Claude`, `Codex→Codex`를 동일한 논리 계약으로 지원한다.
> - **공식 runtime currentness (2026-07-15 v12 확인)**: Codex native subagent depth는 `agents.max_depth` 설정과 sandbox/permission 상속에 묶이고 `codex exec`는 별도 non-interactive surface다. Claude Code 공식 subagent 문서도 subagent가 다른 subagent를 직접 spawn할 수 없다고 명시하며, agent teams와 `claude -p`는 다시 별도 surface다. 어느 runtime도 recursive native spawn을 portable 전제로 제공하지 않으므로 공통 계약은 depth-0 외부 broker를 표준 launch authority로 삼는다.
> - **v11 구현 갭 실측 (2026-07-15 v12)**: `utilities/stage-dispatch-fallback.py`는 `launch_authority=ancestor-broker` row를 선택해도 target adapter wrapper를 conductor process에서 `subprocess.run`한다. `utilities/nested-dispatch-eligibility.py`의 ancestor-broker 검사는 root headless readiness만 확인하며 request handoff·broker process·ack/lease/fencing가 없다. 따라서 v11의 broker는 metadata/readiness 계약만 구현됐고 실제 launch authority 분리는 미완이다.
> - **v12 운영 실측 (2026-07-15~16, v13 계기)**: fleet v10 사이클(`../../plans/2026-07-15_fleet-v10-process-view/`) 수행 중 ① broker 전역 락 하 동기 실행으로 타 프로젝트 worker 1개가 전 fabric dispatch를 약 12분 차단(대기 6), ② broker rollover로 record 고정 `broker_instance`가 사멸해 해당 사이클의 execute/test/report가 ordinal-3 native-subagent로 열화, ③ completion marker 호출 0건으로 gate "통과"의 on-disk 증거 부재(fleet 정직 결손 처리)가 실측됐다.
> - **사용자 결정 (2026-07-16 v13 확정)**: 위 3건 전부 계약 확정 + 구현 착수 ("전부다 작업 해줘").
> - **운영 진단 (2026-07-16 v14)**: 사용자 보고 — v94-reading-face standard+ 사이클(D3~D5)에서 ① root에서 정상 기동된 broker가 depth-1 owner에서 `broker-unavailable`로 재현되고 local conductor fallback도 `network-operation-not-permitted`로 막혀 등록형 plan→execute→test→report 연결을 포기(native/inline 하강), ② plan·execute·report worker가 "분석 완료/편집 시작" 발화 후 수분간 파일 변경·실행 0(재촉/follow-up 후에도 동일 — 최대 운영 시간 손실원), ③ test worker 2개가 "Selected model is at capacity"로 연속 즉사 + 재분사도 동일 모델 재선택, ④ preflight에 현재 작업과 무관한 open row 다수 잔존. 개선 순서 사용자 확정: 1 broker 도달성 → 2 progress watchdog → 3 capacity failover → 4 shell 이식성(core 규약 소관) → 5 worktree build isolation(core 규약 소관) → 6 browser harness(별도 spec 소관) → 7 registry 위생.
> - **코드 원인 실측 (2026-07-16 v14, 본 repo)**: ①의 뿌리 = `dispatch-broker.py broker_status()`의 `/proc/<pid>/stat` 단일 하드 게이트 — PID 네임스페이스 격리 sandbox에서 항상 실패하며 socket ping은 그 뒤에 배치되어 실행되지 않는다. `ensure`도 같은 오판(산 broker를 사망 판정) 후 flock을 획득하지 못하는 serve를 반복 spawn해 `broker-start-timeout`. fleet-depth2-retry-liveness 준비 실측(pid 1057841/12701276 — heartbeat·socket 갱신 중에도 caller `/proc` 검증 불가)과 일치.
> - **사용자 결정 (2026-07-16 v15 확정)**: native subagent와 별도 `codex exec` 재귀 headless를 구분한다. `codex exec`는 subprocess이므로 parent sandbox가 network/auth/file 경계를 허용하면 중첩 실행 가능하고, 2026-07-15 실패는 `workspace-write + network-off` tuple의 실패이지 Codex headless의 보편적 금지가 아니다. broker가 만든 Fleet 중복·stale·fencing·retry 상태면이 효익보다 크므로 기본 경로에서 폐기한다.
> - **공식 Codex currentness (2026-07-16 v15 재확인)**: 공식 Non-interactive mode는 `codex exec`를 자동화용 독립 CLI로, Sandboxing 문서는 spawned command/subprocess가 parent의 OS sandbox 경계를 상속하며 `workspace-write` network가 기본 off임을 명시한다. 따라서 nested Codex headless는 `agents.max_depth`와 무관한 subprocess surface이고, parent conductor profile이 network를 명시적으로 열어야 한다.
> - **운영 실측 (2026-07-16~17, v17 계기)**: dispatch-defaults-config·evidence-autobind 두 standard 사이클에서 execute FAIL 후 재시도가 worker-route-guard의 source_commit 정확 일치 pin에 구조적으로 차단됐다 — 1차는 `route-source-commit-mismatch` launch 사망 실측(`plans/2026-07-16_dispatch-defaults-config/pipeline_summary.md` blocker 절), 2차는 같은 구조를 알기에 conductor 지침으로 재시도를 사전 봉쇄(`plans/2026-07-17_evidence-autobind/final_report.md`). 승인된 탈출구(safety-commit restore = `git reset --hard`)는 권한 분류기가 파괴적 복원으로 차단해 fix-forward가 매번 depth-0로 승격됐다.
> - **사용자 결정 (2026-07-19 확정)**: 재시도 계보 검증 등재(SD-67)와 SD-66 2단계(route compile 봉인 배선) 유보 해제(SD-68)를 승인 — "execute 재시도 vs source_commit 고정 갭 해소 … PRD에 해법 결정 등재 후 구현", "하네스 기본값 config 2단계 … PRD에 결정 등재 후 구현".
> - **운영 실측·사용자 지시 (2026-07-19, v18)**: 경고 문구가 있는 Claude `-p` conductor가 세 번째로 비동기 Monitor/wakeup 대기를 예약하고 턴을 끝내 사망했다. plan worker는 PASS했으나 depth-0가 수동으로 고아 표기·marker·대체 conductor를 복구했다. 같은 사이클에서 Codex execute는 linked worktree의 primary checkout `.git/worktrees/.../index.lock`을 쓸 수 없어 BLOCKED, Claude execute 재시도는 PASS했다. 이후 marker가 있는 두 execute attempt row가 open으로 남아 test와 동시 실행처럼 보였고 depth-0가 수동 마감했다. 사용자는 이 진단 전체의 즉시 구현을 지시했다.
> - **공식 runtime currentness (2026-07-19, v18)**: Claude Code 2.1.215 CLI는 `--disallowedTools`를 제공하지만 실제 치명적 비동기 도구 이름은 runtime probe로 확인해야 한다. Codex 0.144.6 문서는 `--add-dir`를 제공하나 workspace-write의 `.git` 및 resolved gitdir은 writable root 안에서도 보호된다고 명시한다. 따라서 Git common dir을 `--add-dir`에 넣어 commit 가능하다고 주장하지 않는다.
> 본 문서는 청사진(PRD). 구현은 autopilot-code (산출물 `plans/`). 지침 파일(core/adapters/skills) 자체는 본 spec 이 수정하지 않는다 — 방향만 확정.

## 0. 한 줄

**autopilot 파이프의 각 sub-skill 스테이지(code-plan·code-execute·code-test·code-report)를 `standard+` 에서 기본으로 별개 registered headless session에 분사하고, 세션 간 소통은 오직 산출물 파일로 한다.** `dispatch_depth=1` owner는 스테이지 산출물 경로를 계약으로 넘기고 게이트 판단만 자기 컨텍스트에서 쥔 **얇지만 deep-orchestration conductor**다. `direct`는 main-inline(`dispatch_depth=0`)이고, `quick`은 registered headless capability-owner node 하나(`owner_dispatch_depth=1`, `max_dispatch_depth=1`)가 micro-plan부터 concise report까지 한 세션에서 끝내며 child node를 열지 않는다. `quick`은 native-subagent·inline fallback을 갖지 않고 checked headless가 없으면 fail-closed한다. 이는 2026-07-06 "owner 단일 세션 + in-session 팀" 재설계의 **기본값을 반전**하고, 2026-07-13 quick topology를 Fleet-visible one-shot worker로 승격하며 standard+ 라우팅 판단 품질을 high-reasoning 기본으로 고정하는 결정이다.

> **v20 현재 규범 우선순위**: 이 문서의 v1~v19 구간에 남은 bare `depth`/`max_depth`/`owner_depth`와 SD-19 fallback 문언은 당시 schema·결정의 **명시적 historical/legacy 기록**이다. 신규 route, schema, generated projection과 현재 규범은 오직 SD-73~75의 qualified vocabulary를 사용한다. legacy record는 version-tagged read-only로만 읽고 v20 recompilation 전 resume/re-emit하지 않는다.

## 0.5 설계 원칙 — 산출물 기반 소통 (file-only handoff) ★ cross-cutting

**스테이지 세션은 대화 컨텍스트를 주고받지 않는다. 입력은 앞 스테이지 산출물 파일 경로 + 자기 sub-skill 계약뿐이고, 출력도 산출물 파일뿐이다. 스테이지의 진실은 파일에만 있다.**

- **왜 (사용자 결정)**: "어차피 산출물 기반 소통인데" — 파이프는 이미 `plan/plan.md`·`checklist.md`·`dev_logs/`·`test_logs/`·`final_report.md` 로 스테이지 상태를 파일에 적재한다(§2.1). 대화 컨텍스트로 상태를 추가 운반하는 것은 이 파일 계약과 중복이고, 그 중복이 owner 컨텍스트 비대(운영 실증 ③)의 원천이다.
- **왜 (research §4-(8))**: "fresh context per agent + file 로 복원" 이 context rot 방지의 **지배적 관용구** — "대부분 DB 없이 git-committable Markdown/JSON 파일(GSD `.planning/`, spec-kit `specs/`, BMAD `_bmad/`, Agent OS `.agent-os/`)로 세션·`/clear` 경계를 넘는다"(`analysis_summary.md` §4-(8)). GSD 는 이를 설계원칙으로 명문화: "모든 heavy work(research/plan/execute)를 fresh 200K subagent 에서 실행, main 세션은 lean(30–40%) 유지 → context rot 방지"(`cards/gsd.md` §4), 상태는 "`.planning/` 의 `STATE.md`·`CONTEXT.md` 등 구조화 산출물이 세션·`/clear` 경계를 넘어 컨텍스트를 복원"(§4). 우리가 새로 만드는 게 아니라 **이미 검증된 관용구를 스테이지 입도로 채택**한다.
- **왜 (core 원칙 §8)**: `DESIGN_PRINCIPLES.md §8`(Performance Preservation)은 이미 "결과 흐름: file 통해 (verdict 만 token)" 를 명문화했다. 본 spec 은 이 원칙의 적용 범위를 _in-session agent→orchestrator_ 에서 _headless 스테이지 세션→conductor_ 로 확장할 뿐이다 — 원칙 신설이 아니라 승격.
- **결정론-first 연결**(§0.5 DESIGN_PRINCIPLES): 산출물 = 유일 인터페이스이면 "무엇이 넘어갔나"가 파일로 결정론적으로 재현·감사 가능하다. 대화 컨텍스트 전달은 재현 불가·drift 원천이므로 금지.
- **제약 (계약의 완결성 의무)**: 산출물이 다음 스테이지에 필요한 컨텍스트를 **완전히** 담아야 한다. 담지 못하면 그것은 스테이지 경계가 잘못됐거나 산출물 스키마가 빈약하다는 신호 — 대화 컨텍스트로 때우지 말고 산출물 계약을 보강한다(§4). 이 의무가 현행 금지 조항의 우려(§2.2 "상태 재발굴")를 규칙으로 흡수한다.

## 1. 배경 — 사용자 결정 + 운영 실증 + research 종합

사용자 문제의식: **파이프의 스킬 단위 처리를 분사하는 것을 기본 지침으로.** 근거는 "어차피 산출물 기반 소통"이라는 관찰 — 스테이지가 이미 파일로 상태를 넘기므로 세션을 쪼개도 잃을 게 없고, 오히려 관제·격리·컨텍스트에서 이득이라는 판단.

이 결정의 직접 계기 = 2026-07-10 운영에서 드러난 세 실증:

| # | 현행 in-session 팀 모델의 실측 문제 | 근거 |
|---|---|---|
| ① | **fleet 관제 불가시** — in-session Task 서브에이전트(기획팀/개발팀/품질관리팀)는 `.dispatch/jobs.log` 에 등록되지 않아, fleet 대시보드에 스테이지별 진행·liveness 가 뜨지 않는다. owner 세션 한 줄만 보인다. | OPERATIONS §5.10 job 레지스트리 계약(분사만 등록) + 운영 실측 |
| ② | **hook ceremony 미수령** — in-session nested subagent 는 "hook 발화·skill·worktree·jobs.log·statusline 풀 ceremony 격리를 못 받음"(adapter bootstrap §0(C) 명문). 즉 스테이지가 artifact-guard·spec-read 게이트·mode 신호를 온전히 통과하지 않는다. | `adapters/claude/CLAUDE.md §0(C)` |
| ③ | **owner 컨텍스트 비대** — owner 단일 세션이 plan→execute→test→report 를 통째로 들고 가면 각 스테이지 산출물 본문이 대화에 누적되어 컨텍스트가 부풀고, 2026-07-06 재설계가 막으려던 바로 그 팽창이 스테이지 누적으로 재발한다. | OPERATIONS §5.10 재설계 narrative + DESIGN_PRINCIPLES §8 |

research 종합: 거의 모든 multi-agent 프레임워크가 "fresh-context per agent + file-state" 로 세션 경계를 넘는다(§4-(8)). GSD 는 phase loop(Discuss→Plan→Execute→Verify→Ship)를 milestone 당 반복하며 각 heavy work 를 fresh subagent 로 돌리고 상태는 `.planning/` 파일이 복원한다(`cards/gsd.md` §4·§5). Superpowers 는 7단계 순차 gate 를 "design doc / plan / git worktree 로 분산"한다(`analysis_summary.md` §2). 즉 **"스테이지 = fresh 세션"과 "file 기반 handoff"는 각각 널리 실증**됐고, 이 둘의 결합이 §4-(8)이 말하는 지배 관용구다. 우리의 스테이지 입도 분사는 이 관용구를 우리 파이프에 이식하는 것.

## 2. 현행 계약 실측 (2026-07-10, 본 워크트리)

### 2.1 스테이지 파이프는 이미 파일로 상태를 넘긴다 (분사의 전제가 이미 성립)

`standard+` dev 파이프의 스테이지·산출물(전부 `<artifact-root>/plans/<date>_<slug>/` 하위):

| Stage(skill) | 읽는 입력 산출물 | 쓰는 출력 산출물 |
|---|---|---|
| **code-plan** | task 설명(args), 기존 `plans/` 조회 | `plan/plan.md`(영문 primary)·`plan/plan_ko.md`(한국어 mirror), `_internal/plan_reviews/round_{N}.md` |
| **code-execute** | `plan/plan.md` | `plan/checklist.md`(`Safety commit:` 헤더 + Phase/Step 상태), `dev_logs/step_*.md`, `_internal/dev_reviews/phase_{NN}.md`, plan frontmatter `status` |
| **code-test** | `plan/plan.md` verification 섹션 + `plan/checklist.md` | `test_logs/test_report.md`(Level N), `_internal/test_reviews/` |
| **code-report** | plan·checklist·dev_logs·test_logs·`_internal/*_reviews/`·`pipeline_summary.md` | `final_report.md`, `analysis_project/code/*.md` 보강 |

⇒ 스테이지 인터페이스는 **이미 파일**이다. 세션을 쪼개도 잃는 것은 대화 컨텍스트뿐이고, 그건 §0.5 대로 잃어도 되는(오히려 잃어야 하는) 것.

### 2.2 현행 dispatch 모델 = in-session 팀 + **스테이지 분사 명시 금지**

현행 autopilot-code 는 각 sub-skill 을 **owner 세션에서 Skill tool 로 인라인 호출**하고, 각 sub-skill 이 다시 **in-session Task subagent** 로 위임한다:

- `dev-pipeline.md:2`: "You (the main Claude) orchestrate by invoking each skill directly via the Skill tool."
- Step 1/3/4/5: "invoke Skill: `code-plan`/`code-execute`/`code-test`/`code-report` …"
- sub-skill 내부: code-plan→"Invoke the **plan-team** (기획팀) agent as a subagent", code-execute→"Delegate implementation to the dev-team (개발팀) agent", code-test→"Invoke the **품질관리팀** agent in **test mode**", code-report→"Invoke the **qa-team** (품질관리팀) agent as fast writer".

그리고 **스테이지 단위 headless 분사를 명시적으로 금지**한다 (drill 재발 방지 항목, `context-and-guards.md:51`):

> "worktree 확보 _즉시_ 그 안으로 `claude -p` 헤드리스 분사 — plan 호출부터 report 까지 **통째로 한 세션**. … 파이프 스테이지(code-plan·refine·execute)를 main 과 헤드리스로 **쪼개면 헤드리스가 상태 재발굴 + 연속성 상실 = worst of both — 금지.**"

adapter bootstrap §0(C) 도 동형: "풀 ceremony 가 필요하면 worktree 안 `claude -p` headless 분사, 이때 … **분사는 main 전용·깊이 1**".

**본 spec 이 반전하는 정확한 지점**: 위 금지 조항(전체 1세션 강제 + 스테이지 분리 금지)과 "스테이지 = 인라인 Skill" 계약. 반전의 정당성 = §0.5(산출물이 상태를 완전히 담으면 "상태 재발굴"은 파일 로드 비용으로 수렴, "연속성 상실"은 발생하지 않음 — 연속성의 매체가 대화가 아니라 파일이므로). 단 현행 우려는 실재하므로 §4 계약 완결성 의무 + §8 마이크로-스테이지 inline 경계로 규칙화해 흡수한다.

### 2.3 depth 모델 (현행) — 반전이 depth 예산 안에 든다

`OPERATIONS.md §5.10`·`CONVENTIONS.md §1`: depth 0 = 사용자-facing main, depth 1 = capability owner worker(autopilot-code 전체 파이프), depth 2 = `standard+` owner 가 여는 bounded sub-worker(planner/verifier/adversary). **depth 3+ 금지.** 현행 depth-2 는 _리뷰 보조 역할_ 이고 파이프 스테이지 자체는 depth-1 세션 안 in-session 팀이 실행.

⇒ 본 spec 은 **depth-2 의 용도를 리뷰 보조 → 파이프 스테이지 자체**로 확장한다. depth 예산은 그대로: main(0) → conductor(1) → 스테이지 세션(2). 스테이지 세션은 depth-3 headless 를 열지 않고 내부는 in-session 팀만 → depth ≤ 2 불변 유지.

### 2.4 dispatch wrapper 는 이미 스테이지 분사를 받을 수 있다 (증분 확인)

`adapters/claude/bin/dispatch-headless.py` 실측 — 현행 계약이 이미 스테이지 분사의 골격을 지원:

- 인자: `--depth {1,2}`, `--parent <slug>`, `--worker-role <자유문자열>`, `--owner <capability>`, `--capability/--mode/--qa/--intensity`, model 선택(`--model-role | --model+--effort | --inherit-model-settings` 셋 중 필수).
- 게이트: `depth==2` 인데 `--parent` 없으면 `missing-dispatch-parent`(64), `depth==2` + intensity ∈ {direct,quick} → `invalid-depth-two-intensity`(64), `depth 3+` 불가.
- jobs.log: launch _전_ append, `fcntl.flock` 로 `{jobs}.lock` 직렬화, pipe = `capability=…,mode=…,qa=…,intensity=…,depth=…,harness=claude` + 조건부 `parent=/worker_role=/owner=/model_*`.
- depth contract 를 자식 프롬프트에 주입: "depth 1 … should open bounded depth-2 sub-workers for separable standard+ work; … depth 3+ is forbidden."

⇒ **wrapper 는 스테이지 분사를 위해 재작성이 필요없다.** depth=2 + parent=owner-slug + worker_role=<sub-skill> 로 이미 호출 가능. 필요한 것은 (a) conductor 가 이 호출을 스테이지마다 도는 오케스트레이션 계약(문서) (b) 편의를 위한 stage-dispatch helper 판단(§9·§12) 뿐 — 신규 시스템 아님.

## 3. 기본 토폴로지 — 얇은 conductor + 스테이지 headless 세션 (채택)

> **SD-1**: depth-1 owner(autopilot-code)는 **얇은 conductor**. 실작업(plan 작성·구현·검증·보고)은 sub-skill 별 depth-2 headless 세션. conductor 는 스테이지 산출물 경로를 다음 스테이지에 계약으로 넘기고, **게이트 판단(plan-check verdict·CONFIRM 자리·retry 분기)만** 자기 컨텍스트에서 쥔다.

- **conductor 가 쥐는 것 (얇음의 정의)**: (a) 현재 사이클 slug·산출물 루트 경로 (b) 각 스테이지 verdict/status(plan frontmatter `status`, `test_report.md` Level 결과) (c) 게이트 분기 결정(진행/refine/back-jump/중단, retry). **스테이지 산출물 _본문_ 은 읽지 않는다** — verdict/status 만 파일에서 읽어 판단(DESIGN_PRINCIPLES §8 "verdict 만 token").
- **스테이지 세션이 쥐는 것**: 자기 sub-skill 계약 + 입력 산출물 경로. 내부는 현행 그대로 in-session 팀(기획팀/개발팀/품질관리팀)으로 실행 — 스테이지 세션 안에서는 아무것도 안 바뀐다.
- **왜 conductor 가 depth-1 인가**: 스테이지를 depth-2(parent=conductor)로 두려면 parent 가 depth-1 이어야 한다(§2.4 wrapper 게이트). 따라서 main(0)이 autopilot-code conductor 를 depth-1 로 분사(현행 "풀 ceremony" 자리)하고, conductor 가 스테이지를 depth-2 로 분사. main 은 정찰·conductor 분사·수확만(현행 §5.10 역할 불변).
- **conductor 도 얇으므로 main 부담 0 유지**: 재설계가 노린 "main lean"은 그대로 — 오히려 conductor 자신도 스테이지 본문을 안 읽어 lean 을 한 겹 더 얻는다.

## 4. 인터페이스 = 산출물 파일만 (채택)

> **SD-2**: 스테이지 세션은 (a) 입력 산출물 경로 (b) 자기 sub-skill 계약만 받고, 출력도 산출물 파일(§2.1 표). **세션 간 대화 컨텍스트 전달 금지** — §0.5 "산출물 기반 소통"의 명문화.

- **분사 프롬프트 계약**: conductor 가 스테이지를 분사할 때 프롬프트에 넣는 것 = {sub-skill 이름, 입력 산출물 절대경로, 출력 산출물 계약(어디에 무엇을 쓸지), qa/intensity, slug}. plan 본문·앞 스테이지 대화 요약을 프롬프트에 복사하지 않는다 — 스테이지가 파일을 직접 읽는다.
- **계약 완결성 의무(§0.5)**: 산출물이 다음 스테이지 입력으로 완전해야 한다. 예 — code-execute 는 `plan/plan.md` 만으로 구현 가능해야 하고(현행 이미 성립, §2.1), code-test 는 `plan.md` verification 섹션 + `checklist.md` 만으로 검증 가능해야 한다. 불완전하면 산출물 스키마를 보강(구현 phase 에서 sub-skill 계약 갱신), 대화로 때우지 않는다.
- **retry 의 파일 의미론**: 현행 test 실패 시 `plan/plan_ko.md` 에 `<!-- memo: [테스트 실패] … -->` 주입 + checklist 리셋 후 재진입. 이 memo-주입이 곧 파일 기반 handoff — conductor 는 test verdict(fail)만 보고 code-refine/code-plan 스테이지를 재분사하며, 실패 상세는 `test_logs/`·memo 가 운반. 스테이지 재분사는 **기존 산출물 재사용**(SD-6)으로 처음부터 다시 하지 않는다.

## 5. 레지스트리·관제 (채택)

> **SD-3**: 스테이지 세션은 `.dispatch/jobs.log` 에 `depth=2, parent=<conductor-slug>, worker_role=<sub-skill>, owner=autopilot-code` 로 등록 → fleet 에 **스테이지별 row**. stealth-death 가드는 conductor 책임.

- **row 형식**(OPERATIONS §5.10 하드 계약 준수): status 어휘 `open`/`running`→`done`, pipe metadata 쉼표 구분·공백 없음. 예: `capability=code-execute,mode=dev,qa=standard,intensity=standard,depth=2,harness=claude,parent=<conductor-slug>,parent_sid=<sid>,worker_role=code-execute,owner=autopilot-code`.
- **worker_role = sub-skill 이름**: `code-plan`/`code-execute`/`code-test`/`code-report`(+phase 분할 시 `code-execute:phase-A` 류 접미). wrapper 는 worker_role 을 자유문자열로 받으므로(§2.4) enum 확장 불요 — 다만 fleet collector 가 스테이지 row 를 사람이 읽는 라벨로 표시하도록 관제 표면(§9 fleet)에서 인지.
- **관제 이득(운영 실증 ① 해소)**: 이제 fleet 에 plan→execute→test→report 각 row 가 뜨고 liveness·stage 진행이 라이브로 보인다. 분사 직후 fleet 한 줄 안내(§5.10)는 conductor 가 첫 스테이지 분사 시 1회.
- **stealth-death 가드(§5.10 필수)**: conductor 는 각 스테이지 세션 대기 자리에서 완료 알림만 믿지 말고 `utilities/dispatch-liveness.sh` 로 transcript-mtime liveness 점검(SUSPECT/DEAD → 진단→수확/재분사). 스테이지 세션이 여럿이므로 이 가드가 더 중요.
- **hook ceremony 수령(운영 실증 ② 해소)**: 스테이지가 독립 headless 세션이므로 artifact-guard·spec-read·mode 신호 등 풀 ceremony 를 정상 통과(§0(C)가 in-session 에 불가라던 바로 그 격리를 획득).
- **v11 registry authority 보강**: 위 `.dispatch/jobs.log`는 관례가 아니라 canonical global registry다. cycle-local `_internal/jobs.log`는 선택적 audit mirror일 뿐이며 launch attempt의 유일한 registry가 될 수 없다(SD-49).

## 6. depth-2 계약 개정 — 스테이지-워커 클래스 (채택)

> **SD-4**: 현행 "depth-2 worker 기본 read-only, 구현 worker 만 제한 write"(§5.10 ④)를 **스테이지-워커 클래스별 write 소유**로 재정의. depth 3+ 금지 유지 — 스테이지 세션은 또 headless 를 열지 않고 내부는 in-session 팀만.

현행 depth-2 는 리뷰 보조라 read-only 기본이 맞았다. 스테이지 세션은 파이프의 실작업이므로 write 소유를 클래스로 정의:

| 스테이지-워커 클래스 | write 소유 범위 | 근거 |
|---|---|---|
| **code-plan** | `plans/<slug>/plan/` (plan.md·plan_ko.md) + `_internal/plan_reviews/` | plan 산출물만 |
| **code-execute** | **소스 코드 write 소유** + `plans/<slug>/{plan/checklist.md,dev_logs/,_internal/dev_reviews/}` + plan frontmatter status | 유일한 소스 mutation 스테이지 |
| **code-test** | `plans/<slug>/{test_logs/,_internal/test_reviews/}` (소스 read-only) | 검증은 관찰, 소스 불변 |
| **code-report** | `plans/<slug>/final_report.md` + `analysis_project/code/*.md` + `pipeline_summary.md`(lock 경유) | 보고·이력 |

- **read-only 기본의 예외로서 스테이지 write 를 명시**: depth-2 리뷰 워커(planner/verifier/adversary)는 여전히 read-only 기본. 스테이지-워커는 위 표의 클래스 write 만 소유 — 클래스 밖 write 는 계약 위반.
- **소스 mutation = code-execute 단일**: 여러 스테이지가 동시에 소스를 쓰지 않는다. execute 만 소스 소유이므로 스테이지 간 소스 경합 없음. plan/test/report 는 `plans/<slug>/` 하위 경로-분리라 상호 비경합(§8 lock 참조).
- **depth 3+ 금지 유지**: 스테이지 세션(depth 2)은 dispatch-headless.py 를 재호출하지 않는다(wrapper 가 depth 3 자체를 막음, §2.4). 내부 병렬(예: execute 의 독립 step 병렬 개발팀)은 in-session Task 팀으로 — depth 로 세지 않음.

## 7. 모델 라우팅 (채택)

> **SD-5**: 스테이지별 model role 은 CONVENTIONS §2 매핑을 conductor 가 스테이지 분사 시 **명시**(§5.10 ⑦ 그대로 — wrapper 는 기본 모델 암묵 선택 금지).

CONVENTIONS §2.3 role 매트릭스 → 스테이지 매핑:

| 스테이지 | portable model role | 근거 |
|---|---|---|
| code-plan | **deep maker** (기획팀) | §2.3 기획팀 = deep maker |
| code-execute | **fast implementer** default, 복잡 설계 시 deep maker 상향 | §2.3 개발팀 = fast implementer default |
| code-test | **variable reviewer/verifier** (품질관리팀) — qa/intensity 가 fast/deep 결정 | §2.3 품질관리팀 가변 |
| code-report | **fast writer** (품질관리팀 report) | §2.3 / §2.1 fast writer |

- conductor 는 스테이지마다 `--model-role <role>` 또는 concrete `--model+--effort` 를 명시. dispatch-headless.py `role_map`: deep maker→(opus,high), fast implementer→(sonnet,medium), fast writer→(sonnet,low) 등(§2.4 실측)이 재현.
- **작업 난이도별 상향은 conductor 판단**(§5.10 ⑦): 어려운 plan·복잡 API 는 conductor 가 deep maker/opus 로 상향, 단순 스테이지는 하향. wrapper 가 임의 기본 선택하거나 interactive session model 암묵 상속 금지.

### 7.1 v7 orchestration·family routing 계약 (SD-21~23)

> **SD-21 — conductor 기본**: depth-1 `standard+` conductor 는 portable `orchestrator` role + **high reasoning/deep orchestration** profile이 기본이다. "얇음"은 스테이지 본문을 들지 않는 context 책임이고, 라우팅·분해·게이트 판단을 가볍게 한다는 뜻이 아니다. fast orchestration 은 입력 정규화, 정해진 명령 조립, 상태/경로 전달, 결정된 결과 병합처럼 **선택지가 없고 의미 판단이 없는 mechanical-only** 작업에만 허용한다.

> **SD-22 — family affinity와 우선순위**: planning·architecture·decomposition은 portable `deep maker`이며 **GPT family via Codex affinity**를 우선한다. 이는 품질 affinity이지 hard pin이 아니므로 runtime/account/tool/limit 부적격이면 다른 eligible family/adapter로 fallback한다. plan review는 가능한 경우 maker와 **다른 model family**의 reviewer를 선호해 실패 모드 다양성을 확보한다.

라우팅 결정 순서는 다음 하나로 고정한다.

1. **explicit choice** — 사용자가 지정한 harness/family/role/model. 단 실행 불가능한 선택은 조용히 대체하지 않고 hard eligibility 실패를 reason trace에 남긴 뒤 fallback한다.
2. **hard eligibility** — 필요한 tool/runtime surface, account entitlement, 정확한 model ID 지원, active usage limit, 그리고 depth-2 recipe를 소유할 conductor의 **parent transport/sandbox별 nested child-spawn 가능성**. root/main에서의 headless check나 native subagent 지원으로 nested headless 지원을 추정하지 않으며 부적격·unknown 후보는 지원 후보에서 제거한다(SD-48).
3. **stage affinity** — planning/architecture/decomposition=`deep maker` + GPT/Codex 선호 등 stage별 family/role 적합성.
4. **maker-checker family diversity** — review/checker는 가능한 경우 maker와 다른 family.
5. **capacity/cost/latency** — 위 조건이 동률일 때만 잔여 용량, 비용, 지연으로 결정한다.

portable core/registry는 **family + role**만 canonical하게 기록한다. concrete model ID, reasoning flag, endpoint/CLI syntax은 adapter가 소유한다. Adapter는 dispatch 직전 current runtime을 probe해 실제 허용되는 **exact ID**를 확정해야 하며 cached alias·문서 alias를 가용성 증거로 쓰지 않는다. 2026-07-13 currentness 기준 공식 권장은 GPT-5.6 Sol이고 API alias는 `gpt-5.6`이지만, parent Codex ChatGPT 실측은 alias를 거부하고 exact `gpt-5.6-sol`을 허용했다. 그러므로 Codex 선택은 adapter-verified exact ID를 사용하고 probe 실패 시 다음 eligible exact ID/family로 clean fallback하며 선택 이유와 실패 ID를 기록한다.

> **SD-23 — `route-dispatch` helper**: 라우팅을 설명 가능하고 재현 가능하게 만드는 **read-only** helper를 둔다. 이는 SD-9의 stage 순서·경로 실행 helper와 별개인 후보 선택 helper다. 초기 지원 adapter는 Claude+Codex이며, OpenCode는 runtime model inventory/probe 계약이 확정되기 전까지 `unknown`을 정직하게 반환한다.

Helper 입력/출력 계약:

- 입력: stage/capability, intensity, QA, required tools/runtime surfaces, explicit choice(있으면), maker family(리뷰 시), adapter별 usage/account/runtime probe 결과.
- 출력: portable `{family, role}`, 선택 adapter, adapter-verified `{exact_model_id, reasoning}`, 우선순위별 reason trace, rejected candidates와 fallback chain, unknown/unsupported 필드.
- 금지: jobs.log 등록·프로세스 시작·worktree/file mutation·limit 상태 갱신. Helper는 후보를 **계산·보고만** 하고 실제 dispatch는 기존 adapter wrapper가 수행한다.
- OpenCode: family/model을 추측하거나 Claude/Codex mapping을 복사하지 않는다. probe surface가 없거나 불명확하면 `adapter=opencode,status=unknown`으로 반환하고 다른 eligible adapter로 fallback 가능하게 한다.

## 8. 비용·안전 가드레일 (채택)

> **SD-6**: 동시 상한 5 안 동시성 계산 / 마이크로-스테이지 inline 경계 / 스테이지 실패 재시도·재개 의미론 / §5.8 lock 범위를 명문화.

- **동시 상한 5 안 동시성**(§5.10 ⑤): 스테이지 파이프는 **순차**(plan→execute→test→report)라 한 conductor 는 보통 동시 1 스테이지만 점유 — conductor(1) + 활성 스테이지(1) = 2. 여러 요청을 병렬 처리하면 conductor 가 여럿이 되므로 상한 계산은 **`Σ(활성 conductor + 각 conductor 의 활성 스테이지)` ≤ 5**. code-execute 내부 병렬 개발팀은 in-session(depth 미증가)이라 상한에 안 셈. 초과 예상 시 conductor 는 스테이지 분사를 큐잉(다음 스테이지는 앞 스테이지 done 후이므로 자연 직렬).
- **마이크로-스테이지 inline 경계**(현행 우려 §2.2 흡수, v6 정정): 분사 오버헤드(세션 startup·산출물 로드)가 스테이지 실작업보다 크면 분사가 손해다. **경계 규칙**: 산출물을 새로 쓰지 않거나 한 줄 verdict 만 내는 스테이지(예: plan-check self-check, `direct` 파이프 전체, ≤3 step plan 의 통합 리뷰)는 **inline 유지**. `quick` 은 더 이상 depth-0 inline 실행이 아니라 **단일 depth-1 one-shot capability worker** 가 micro-plan·plan-check-lite·implementation·focused verification·concise report 를 한 세션에서 끝낸다. quick 내부 micro-stages 는 worker 세션 안에서 inline 이며, quick worker 는 depth-2 를 열지 않는다. 산출물을 실제로 생성·mutation 하는 `standard+` 스테이지(plan 작성·execute·test·report)만 depth-2 로 분사한다. 정확한 손익 임계(어느 크기부터 분사가 이득인가)는 **pilot 계측으로 캘리브레이트**(§12, SD-OPEN-1) — research 도 per-stage dispatch 비용을 수치화하지 않았으므로(digest 주의) 추측하지 말고 측정.
- **실패·재개 의미론(기존 산출물 재사용)**: 스테이지 실패 시 conductor 는 `--from <stage>` 로 **그 스테이지만 재분사**, 앞 스테이지 산출물은 재사용(재생성 금지). test 실패 retry 는 §4 memo-주입 경로(최대 1회 pipeline-level retry, `qa=quick` 은 retry 없음 — 현행 유지). 스테이지 세션이 hang/crash(§5 stealth-death)면 conductor 가 진단 후 동일 스테이지 재분사 — 부분 산출물이 있으면 이어쓰기, 없으면 처음부터 그 스테이지만. 동일 failure class에 eligibility 증거 변화가 없는 재시도는 금지하고, same-harness 실패 뒤에는 SD-50의 cross-harness 단계부터 평가한다.
- **§5.8 pipeline lock 범위**: lock 은 `spec/prd.md`·`spec/pipeline_state.yaml`·`spec/pipeline_summary.md` _공유 단일파일 쓰기_ 만 보호. 스테이지 산출물은 전부 `plans/<slug>/` 경로-분리라 **비경합 → lock 불요**. 예외 = **code-report 가 `pipeline_summary.md`(공유 단일파일)를 쓰는 자리만 lock acquire**(현행 code-report 계약과 동일). 즉 스테이지 분사가 lock 경합을 새로 만들지 않는다.

## 8.5 Phase 2 추가 결정 (v2, 2026-07-10 — Phase 1 pilot 실측 + 사용자 확인 발견)

> Phase 1 은 main 머지(5b7cf33; cfbd098 계약 개정 / 0cb216e pilot 계측). pilot 성공 기준(§12) 은 통과 — fleet 스테이지 row·산출물 정상·depth≤2·대화 전달 0. 아래는 pilot 과 사용자 후속 확인에서 나온 Phase 2 입력 결정.

### 8.5.1 SD-10 — autopilot-code 배선 완성: dev-pipeline 본문 dispatch-first 재작성 ★ Phase 2 최우선

**발견 (사용자 확인, 2026-07-10)**: Phase 1 의 §9-8 개정이 **반쪽** — `dev-pipeline.md` 는 앞머리(line 4)에 stage-dispatch 계약 블록을 얹었으나, 본문 Step 1~7 (Step 1 "invoke Skill: `code-plan`", Step 3/4/5 동형, retry loop 5~7항)이 여전히 in-session "Invoke Skill:" 명령형 그대로 = **이중 신호**. 또 계약 블록의 "When still orchestrating in-session (e.g. `--intensity` downgraded, or a runtime without headless dispatch)" 의 **e.g. 비한정 escape hatch** 가 in-session 우회를 정당화한다. 지시 문서에서 앞머리 계약과 본문 명령형이 갈리면 실행 주체는 본문을 따른다 — pilot 이 통과한 것은 conductor 프롬프트가 분사를 떠먹여줬기 때문이지 문서 자체의 효력이 아니다(§8.5.5 drill 연동).

**결정**:
- (a) Step 1~7 본문을 **dispatch-first 명령형**으로 재작성 — `standard+` 의 각 스테이지 Step = `dispatch-headless.py --depth 2 --parent <conductor-slug> --worker-role code-<stage>` 분사 명령이 1차 지시. in-session Skill 호출은 **[direct] 또는 [headless dispatch 불가 런타임]** fallback 으로 격하하고, v6 이후 `quick` 은 별도 depth-1 one-shot worker 경로로 분리한다. 비한정 "e.g." escape hatch 는 제거(조건 열거를 한정형으로).
- (b) `SKILL.md` Stage Graph 표에 **dispatch 모드 표기** 반영 — `standard+` 행이 "스테이지 = depth-2 headless 분사"임을 표에서 즉독 가능하게.

### 8.5.2 SD-11 — 결정론 신호: conductor 의 code-* 직접 Skill 호출 reminder hook

conductor(depth-1, `worker_role=capability-owner`) 세션이 `code-plan`/`code-execute`/`code-test`/`code-report` Skill 을 직접 부르면 reminder 를 주입하는 hook 신설 — `worktree-path-guard`(drill g3/g6) 선례의 stage-dispatch 판. **deny 가 아니라 reminder(soft)로 시작**: 당시에는 in-session fallback 이 direct/quick·headless-불가 런타임에서 정당했고, hook 이 그 자리의 intensity 를 결정론적으로 알기 어려워 deny 는 false-positive 위험이었다. v6 이후 quick 은 code-* stage 직접 호출 경로가 아니라 depth-1 one-shot worker 경로로 분리된다. deny 상향 여부는 drill·계측 누적 후 재판단(미결로 유지 — §14 의미↔규칙 경계).

### 8.5.3 SD-12 — 스테이지-워커별 bootstrap 최적화 (dispatch-profiles 연결)

**사용자 요구**: 분사 세션마다 하네스/부트스트랩 컨텍스트를 스테이지별로 최적화해 싣기. 기존 인프라 = **dispatch-profiles** (`spec/dispatch-profiles/` SoT; `profiles/fragments/<name>.md` + `tools/profile/build-home.py` 가 masked `CLAUDE_CONFIG_DIR` home 생성, `dispatch-headless.py --profile` 지원) — 신규 시스템이 아니라 기존 인프라의 스테이지 입도 연결.

- 스테이지-워커(code-plan/execute/test/report)별 **최소 프로필 fragment** 정의 — full bootstrap(CLAUDE.md 전체) 대신 그 스테이지 계약(해당 sub-skill + 필요한 core 절)만.
- conductor 의 스테이지 분사에 `--profile <stage-fragment>` **기본 배선**.
- **효과 계측(토큰/시간)을 SD-OPEN-1 데이터와 같이 수집** — full bootstrap vs 최소 프로필의 스테이지 세션 startup·총 토큰 비교.

### 8.5.4 SD-13 — conductor 의 spec 전제 선보장 (pilot 부수발견 ①)

pilot 실측: spec-less repo 에서 스테이지 세션이 `artifact-guard` 에 차단됨 — 스테이지는 풀 ceremony 를 받으므로(§5 의도된 획득) 생성-순서 게이트도 그대로 받는다. **결정**: conductor 는 스테이지 분사 _전_ 대상 repo 의 spec 전제(artifact root 존재 + `spec/` 존재 또는 untracked 모드)를 선확인·선보장한다 — 스테이지 세션 안에서 차단으로 발견하면 재분사 비용, conductor 게이트 판단 자리에서 잡으면 무료.

### 8.5.5 drill 회귀 확장 — 문서 자체의 효력 검증 (§9-14 개정)

스테이지 분사 회귀 drill 에 **"conductor 가 프롬프트 떠먹임 없이 스킬 문서만 보고 스테이지를 분사하는가"** 검증 포함 — pilot 처럼 분사 지시가 프롬프트에 명시된 통과가 아니라, `dev-pipeline.md`/`SKILL.md` 만 주어진 상태에서 분사가 일어나는지(SD-10 이중 신호 제거의 acceptance 이기도 함). 기존 검증(fleet row·산출물·depth≤2·lock 미경합)에 추가.

### 8.5.6 SD-OPEN-2 — 스테이지 SessionEnd mem curator 기동 (관찰 항목, 결정 아님)

pilot 부수발견 ②: 스테이지 세션도 SessionEnd 에 mem curator(distiller) 를 기동한다. Phase 1 에선 메모리 오염 없었으나, 다중 스테이지 세션이 순차로 curator 를 돌리는 구조의 영향(중복 add·불필요 curate 비용·동시성)은 미검증 — **Phase 2 에서 관찰만 지속**(계측 로그에 curator 기동 여부 기록), 개입 결정은 증거 후.

### 8.5.7b SD-15 — wrapper 의 limit-사망 즉시 감지 (운영 실증 ⑤, v3 2026-07-10)

**실증**: Phase 2 conductor 1차 분사가 launch 직후 session limit 로 즉사 — stdout 로그에 "You've hit your session limit · resets 3pm" 한 줄만 남기고 exit 했으나 jobs.log row 는 `open` 잔존, liveness SUSPECT(transcript-mtime 16분 정지)로만 간접 발견. 감지 지연 + "hang 인지 죽음인지" 오인 여지.

**결정**: (a) wrapper `--start` 가 child spawn 후 짧은 워치(수십 초)에서 조기 exit 를 감지하면 로그 tail 의 limit/auth 류 종료 패턴을 검사해 jobs.log row 를 `done,note=dead-<사유>` 로 즉시 마감하고 사유·reset 시각을 출력에 한 줄 표면화. (b) `dispatch-wait`/`dispatch-liveness` 도 로그의 limit 패턴을 DEAD 판정 근거에 추가(transcript-mtime 단독 의존 탈피). (c) codex/opencode wrapper 는 동형 검토(불가 시 ADAPTATION disclosure). loops 의 `run_claude_retry`(limit 시 ABORT) 선례와 동일 계열 — wrapper 는 재시도까지는 하지 않고 감지·마감·표면화만(재분사 판단은 orchestrator 의미 구간).

### 8.5.7c SD-16 — 사용량-인지 크로스 하네스 분사 (사용자 요구, v3 2026-07-10)

**사용자 요구**: "codex 와 claude code 의 사용량을 직접 체크하면서, 둘을 골고루 고려해 크로스 하네스로 분사를 구성하도록 강화." 배경 = 운영 실증 ⑤(limit 즉사)가 보여준 단일 하네스 의존 취약 — Claude 가 막히면 전체 파이프 정지. 기존 기반: codex/opencode `preflight.sh dispatch` 가 이미 동형 계약(depth/parent/worker_role/jobs.log `harness=` 표기, cross-harness `parent_sid` 연결 — OPERATIONS §5.10).

**결정**:
- (a) **사용량 직접 체크 헬퍼**: 분사 직전 orchestrator(main/conductor)가 Claude·Codex 양쪽의 사용량/limit 상태를 결정론적으로 조회하는 헬퍼 신설(`utilities/usage-check.sh` 류). 소스 = 각 CLI 의 공식 사용량 표면(**구현 시 runtime-currentness 조사 필수** — 최신 공식 문서 확인) + jobs.log `dead-session-limit` 마커·reset 시각 캐시(SD-15 연동). 출력 = harness 별 `{ok | limited(reset시각) | unknown}` 한 줄(파싱 가능).
- (b) **상호보완 라우팅 계약** (사용자 정제: "codex 와 claude 가 서로 상호보완적인 — 사용량이나 특성이나 — 동작"): 목표는 단순 부하 균형이 아니라 **보완성** —
  - **사용량 보완 (failover·분산)**: limit 상태인 하네스를 회피하고 여유 하네스로 우회(limited 면 타 하네스, 둘 다 여유면 분산). Claude 막힘 → codex preflight dispatch 동형 우회 명문화.
  - **특성 보완 (강점 배치)**: 작업 특성별 하네스/모델 적합성 배치 — CONVENTIONS §2 role 매핑의 하네스별 실현 + 검증·리뷰 자리는 **타 모델 계열 교차**(다른 실패 모드 = 리뷰 다양성 이득, codex-review-team 선례)를 우선 후보로. 같은 사이클 안에서 maker 하네스와 checker 하네스를 다르게 두는 조합을 정규 옵션화.
  - 계약 자리 = OPERATIONS §5.10 ⑦ 확장 + dev-pipeline 등 파이프 스테이지 분사 절.
- (c) **관제·계측**: cross-harness row 는 기존 `harness=`/`owner_harness=`/`parent_sid` 표기로 fleet 연속성 유지. harness 별 분사 분포·limit 회피 이벤트·교차 리뷰 조합을 계측에 기록.
- (d) **thorough+ 동시성 검증** (사용자 확인 요청): 현행 계약은 thorough/adversarial 에서 depth-1 owner 가 **다축 depth-2 perspective/verifier/adversary 워커**를 열도록 명시(WORKFLOW §1.1·OPERATIONS §5.10 ④)하고 동시 상한 ⑤ 가 "동시 분사"를 전제하나, **다축 워커의 병렬 실행이 실측 검증된 적은 없다**(Phase 1·2 사이클은 strong — 단일 리뷰). 검증 항목: thorough 사이클에서 다축 워커가 실제 동시 jobs.log row 로 뜨는지 + Σ 상한 계산 준수 + dispatch-wait 의 다중 자식 대기 의미론. 
- **한도 비대칭 기본값** (사용자 제공 2026-07-10, minor): 현행 가정 = **Claude Code 한도 > Codex 한도** → 기본 배분 = Claude 주력(주 파이프·대량 스테이지), Codex 보완(교차 리뷰·failover·특성 적합 자리에 우선 소비 — 낮은 한도를 고가치 자리에 아껴 씀). 단 **이 비대칭은 향후 바뀔 수 있는 가변 전제** — 코드에 하드코드 금지, 이름 있는 설정값(정책 파일/명시 상수, 예: `dispatch-policy` 의 `harness_capacity_bias`)으로 선언해 한 자리 수정으로 뒤집을 수 있게 한다.
- **SD-OPEN-3 (미결)**: 보완 정책의 정확한 가중("limit 회피 > 특성 적합 > 분산" 초기 보수 정책, 위 한도 비대칭 기본값 반영) — 편중·교차 리뷰 효과는 계측 누적 후 조정.

### 8.5.7 SD-14 — conductor 대기 계약 결정론화 (운영 실증 ④, 2026-07-10 타 세션 발견)

**실증**: 첫 conductor(sonnet)가 code-plan 분사 후 "Monitor 대기"로 turn 을 끝내 headless 프로세스가 조기 종료 — **one-shot `claude -p` 세션에선 turn 종료 = 프로세스 종료**이고 background 완료 알림은 영영 오지 않는다. 스테이지(code-plan)는 완주해 산출물은 남았으나 conductor 가 죽어 파이프가 고아화. 임시책(재개 conductor 프롬프트에 폴링 대기 명시)은 instruction 층이라 비결정론.

**결정 — 3층 (§0.5 결정론-first)**:
- (a) **wrapper 대기 계약 주입** (즉시, 최저비용): `dispatch_prompt()` 의 depth-1 `depth_note` 에 one-shot 계약 명문화 — "너는 one-shot 프로세스다 / background 완료 알림은 오지 않는다 / Monitor·알림 대기로 turn 을 끝내지 말라 / 같은 turn 안에서 폴링 대기 후 수확하라". 모든 conductor 분사에 자동 적용. (여전히 instruction 이지만 전달이 결정론 — 프롬프트 누락 불가.)
- (b) **Stop hook 하드 게이트** (가장 결정론적): headless 자식 세션(`CLAUDE_CODE_CHILD_SESSION=1` + `AGENT_DISPATCH_DEPTH=1` — wrapper 가 이미 주입, 실측 385-386행)이 turn 종료 시도 시, jobs.log 에 `parent=<자기 slug>` 인 `open` 스테이지 row 가 남아 있으면 Stop 차단 + 피드백. **피드백은 "대기하라"가 아니라 행동 지시**: liveness 점검(`dispatch-liveness.sh`) → ALIVE 면 폴링 계속 / SUSPECT·DEAD 면 진단→수확·재분사·row 정리 후 종료 — 죽은 스테이지 때문에 conductor 가 영구 hang 하는 역전 방지. 무한루프 가드(stop_hook_active 존중) 포함. **전제 2건 선해소**: ① `-p` 모드에서 Stop hook 발화 여부 실측 검증 ② worktree-local registry 갭(wrapper `AGENT_HOME` 폴백 시 parent/child 가 다른 jobs.log 를 보는 문제) 선수정 — hook 이 올바른 registry 를 봐야 성립.
- (c) **`dispatch-wait` 동기 대기 헬퍼** (실수 표면 제거): conductor 가 "알아서 폴링"하지 않도록 기존 `dispatch-liveness.sh` 를 재사용하는 헬퍼 신설 — 스테이지 종료·SUSPECT 시 exit, Bash 호출당 timeout(≤10분) 제약으로 반복 호출 형태. conductor 절차를 "분사 → `dispatch-wait` 반복 → 수확"으로 고정하고, 이 대기 계약을 **SD-10 의 dev-pipeline 본문 재작성에 포함**(스텝 명령형이 대기 방법까지 지정).

채택 = (a)+(b) 조합이 기본, (c) 는 절차 단순화 보강. 구현 자리 = Phase 2 wrapper 증분(SD-12 `--profile` 배선과 같은 묶음 — 같은 파일·같은 사이클). **타 세션 협조 노트**: 발견 세션이 registry 갭(AGENT_HOME)을 자체 수정할 수 있음 — 구현 전 wrapper 최신 상태 재실측으로 이중 수정 회피.

## 8.6 v4 정련 — 도그푸딩 발견 3건 (2026-07-10, SD-15/16 첫 실전 + 문서-효력 2연속 실측)

### 8.6.1 SD-15b — 로그-패턴 DEAD 판정 앵커링 (오탐 실측)

**실측**: sd15-adapter-parity conductor 가 **정상 완주**했는데 dispatch-liveness 가 로그 limit/auth 패턴으로 DEAD 오탐 — conductor 의 최종 보고문이 limit 감지를 _주제로_ 서술해 `LIMIT_RE` 가 본문에 걸림. **결정**: 로그-패턴 DEAD 판정을 앵커링 — (a) 패턴 매치를 CLI 의 실제 종료 에러 라인 형식(예: 로그 말미 N줄 + 짧은 단독 라인)에 한정 (b) 정상 완주 신호(구조화 최종 출력 존재·프로세스 exit 0)와 결합해 완주면 DEAD 배제. 회귀 케이스: "limit 를 논하는 보고문" fixture.

### 8.6.2 SD-16e — usage-check reset 의미론 (stale limited 오탐 실측)

**실측**: 아침 limit 사망 마커(수동 작성, `reset=` 필드 부재)가 300분 창 내내 `claude limited(-)` 로 읽힘 — 실제 리셋(15시)이 지나도 해제 안 됨. **결정**: (a) `reset=` 있는 마커는 reset 시각 경과 시 즉시 `ok(expired)` (b) `reset=` 없는 마커는 보수 창을 단축하거나 `limited(unknown-reset)` 로 구분 표기 — orchestrator 가 "확인 필요"로 읽게 (c) 수동 row 마감 시 reset 필드 기입을 OPERATIONS 계약에 명문화.

### 8.6.3 SD-11b — reminder → deny 상향 (문서-효력 2연속 실패 실증)

**실측 (2연속)**: 최소 프롬프트 conductor 가 ① Phase 3 — 자기수정 예외(성립: Claude 분사 경로 편집)로 inline ② sd15-adapter-parity — **Claude 분사 경로 무변인데도 동일 예외를 차용**(과잉 적용)해 inline. soft reminder(SD-11)는 두 번 다 행동을 바꾸지 못함. 한정형 2조건 fallback 문서도 자기 발명 예외를 막지 못함.

**결정**:
- (a) **결정론 조건 확보**: wrapper 가 자식 env 에 `AGENT_DISPATCH_INTENSITY`(+이미 있는 `AGENT_DISPATCH_DEPTH`) 주입 → hook 이 [depth==1 && intensity∈standard+ && code-* Skill 직접 호출] 을 결정론적으로 식별 가능 — SD-11 이 deny 를 보류했던 false-positive 근거(intensity 불가지) 해소.
- (b) **deny 상향**: 위 조건에서 code-* Skill 호출을 **hard deny** + "dispatch-headless 로 분사하라" 피드백. direct(env intensity 로 구분)·headless-불가 런타임(env 부재)은 자동 비대상. v6 quick 은 code-* depth-2 stage 호출을 열지 않는 별도 depth-1 one-shot worker 로 판정한다.
- (c) **자기수정 예외의 처리**: 예외를 문서 조항으로 남기지 않는다(2연속 실증 — 조항은 차용된다). 정당한 자기수정 자리(분사 launch 경로 자체 편집)는 사용자/main 이 분사 프롬프트에 명시 opt-out (`STAGE_DISPATCH_INLINE_OK` 류 env/문구)을 줄 때만 — 판단을 conductor 재량에서 orchestrator 명시로 이동.
- 문서-효력 재검증은 본 deny 착지 후 다음 일반 사이클에서.

## 8.7 SD-17 — 적용 조건 정련: separability 판정 (v5, 2026-07-10 사용자 결정 (a))

**근거 (conductor 3연속 실측)**: ① Phase 3 — 자기수정 예외 inline(정당) ② sd15-parity — 예외 차용 inline(위반 사례) ③ qa-intensity-unify — 경계-결합 문서 리팩터를 "비분리 편집은 inline + 분리 가능한 부분만 in-session 병렬 3워커"로 처리(계약의 "separable" 취지 인용, 조리 있는 판정). 증거 수렴: 스테이지 분사의 실익은 **separable 한 작업**에서 발생. SD-11b deny 는 code-* Skill 경로만 커버 — Skill 미사용 직접 오케스트레이션은 결정론 강제 불가.

**결정 (사용자 선택 (a))**:
- **기본값 불변**: `standard+` 파이프의 스테이지 = depth-2 headless 분사 기본.
- **conductor 는 분사 전 separability 판정**: [스테이지 산출물 계약이 완결적(파일만으로 다음 스테이지 가능) && 편집 표면이 경계-결합(공유 semantic anchor·boundary assertion 의 순차 결합)이 아님] → separable → **분사 의무**.
- **비분리 판정 시 inline 허용** — 단 3중 의무: (a) 판정 근거를 `plans/<slug>/_internal/metrics.md` 에 기록 (기록 없는 inline = 위반 — drill/audit 이 잡는 감사 표면) (b) 분리 가능한 부분(census·독립 파일군 편집)은 in-session 워커 병렬로 (qa-unify 선례) (c) 자기수정 자리는 SD-11b(c) orchestrator opt-out 경로 그대로.
- **SD-OPEN-1 과의 관계**: separability = inline 임계의 **질적 축** (기존 크기 축과 병행) — 계측 항목에 판정 결과 포함.
- **강제 계층**: 결정론(deny hook)은 code-* Skill 경로 유지, separability 는 기록-의무+감사(의미 판단 구간을 억지 규칙화하지 않음 — §14 경계 존중).

## 8.8 v6 topology 변경 — quick depth-1 one-shot capability worker (2026-07-13 사용자 승인)

### 8.8.1 SD-18 — intensity별 depth topology 재정의

**결정**: intensity topology 는 세 갈래로 고정한다.

| Intensity | Topology | Worker contract |
|---|---|---|
| `direct` | depth-0 main inline | plan stage 없음, durable plan 없음, final sanity/report 만 수행 |
| `quick` | depth-0 main → **depth-1 one-shot capability worker** | worker 한 세션이 `orient-lite -> micro-plan -> plan-check-lite -> produce -> focused verification -> concise report` 를 끝냄. quick 내부 micro-stages 는 모두 inline, **depth-2 금지** |
| `standard+` | depth-0 main → depth-1 conductor → 순차 depth-2 stage-workers | 기존 SD-1~17 유지: conductor 는 얇게 verdict/status 와 게이트만 쥐고 code-plan/execute/test/report 등 stage-worker 를 순차 headless 분사 |

**quick worker 의 범위**: quick 은 작은 tracked 변경의 ceremony 를 main thread 밖으로 옮기는 topology 변경이지, full stage-dispatch 로 승격하는 것이 아니다. quick worker 는 durable `plans/<slug>/` cycle 을 강제하지 않고, 필요한 경우 기존 capability 의 quick 산출물/summary 만 남긴다. quick worker 가 별도 planner/verifier/stage worker 를 열면 계약 위반이다.

**mutation quick 격리**: source mutation 이 가능한 quick job 은 isolated worktree 를 사용한다. mutation 없는 문서/검토 quick 은 main worktree 에서 depth-1 worker 를 열 수 있으나, file overlap·dirty state·merge state 가 있으면 기존 §5.9/§5.10 safety gate 를 우선한다.

### 8.8.2 SD-19 — Codex quick dispatch preference and fallback (historical; superseded by SD-73)

**선호 경로**: Codex quick job 은 `adapters/codex/bin/preflight.sh headless --check` 가 통과하면 headless dispatch 를 우선한다. 이유는 `.dispatch/jobs.log` row 로 Fleet 이 볼 수 있고, parent 가 liveness/harvest 계약을 공유하기 때문이다.

**fallback 순서**:

1. `headless --check` 실패, native subagent check ok → Codex native subagent 로 depth-1 quick worker 를 실행하되, **Fleet visibility degradation note** 를 남긴다. native subagent 는 main-thread context pollution 을 줄이는 runtime 지원이지만, headless jobs.log row/liveness 가 없거나 제한될 수 있음을 보고한다.
2. headless 와 native subagent 모두 불가 → depth-0 inline 으로 수행하고, concise fallback reason 을 pipeline summary/final report 에 남긴다.

**공식 Codex rationale**: OpenAI Codex manual 의 Subagents 섹션은 subagents 가 noisy exploration/test/log output 을 main thread 밖으로 옮겨 context pollution 을 줄인다고 설명한다. 동시에 각 subagent 가 자체 model/tool work 를 수행해 token 을 더 쓰며, parallel write-heavy workflow 는 충돌과 조정 비용을 늘릴 수 있으므로 주의하라고 한다. 따라서 quick 은 depth-1 **단일** worker 로 main context 오염을 줄이되, depth-2 fan-out 과 병렬 write 를 금지한다.

### 8.8.3 SD-20 — Fleet activity contract for quick

Fleet 는 quick depth-1 worker 를 하나의 live activity 로 보여야 한다. 표시 계약:

- stage label: `quick/exec`
- visual state: one blinking activity stage while the depth-1 quick worker is open/running
- metadata: `capability=<entry>,intensity=quick,depth=1,worker_role=capability-owner,owner=<entry>,harness=<runtime>`
- no child rows for quick depth-2; quick depth-2 row 가 생기면 contract violation

Headless dispatch 가 preferred 인 이유는 이 표시 계약을 jobs.log 로 자연스럽게 충족하기 때문이다. native subagent fallback 은 Fleet visibility degradation note 를 남기고, inline fallback 은 activity stage 를 만들 수 없음을 보고한다.

## 8.9 v7 Fleet hotfix acceptance (SD-24)

> **SD-24**: 라우팅 변경과 함께 드러난 Fleet process/stage 오탐은 아래 두 회귀가 모두 닫혀야 hotfix accepted다.

1. **Codex headless child 숨김**: dispatch wrapper가 부여한 환경 marker로 식별되는 Codex headless dispatch 프로세스는 Fleet의 top-level/local process 목록에서 child-hidden이어야 한다. command substring/부모 PID 추측이 아니라 env marker가 판정 근거이며, jobs.log의 정상 depth-1/2 row와 liveness는 계속 보인다.
2. **비-code job stage 오탐 금지**: non-code capability/spec/research/document job은 경로나 slug가 `plans`와 유사해도 code plan을 fuzzy-match하지 않는다. 명시적 capability/worker_role/stage metadata가 없으면 code stage를 합성하지 않으며, 특히 거짓 `spec:test` 표시가 없어야 한다.

수용 테스트는 (a) env-marked Codex headless child가 process 목록에서 숨고 registry row는 유지됨, (b) non-code fixture의 유사 경로/slug에서도 stage가 capability metadata대로 표시되고 `spec:test`가 0건임, (c) 정상 code-plan/code-test fixture는 기존 표시가 유지됨을 함께 단언한다.

## 9. 영향 표면 목록 (구현 phase 에서 갱신 — 현행 문구 → 개정 방향)

> **SD-7**: 아래 표가 구현(autopilot-code) 시 묶음 갱신할 자리. 각 surface = {현행 문구, 개정 방향}. 실제 문구 편집은 소유 스킬(core-first) 경유 별도 — 본 spec 은 방향만 확정.

| # | Surface | 현행 문구(요지) | 개정 방향 |
|---|---|---|---|
| 1 | `OPERATIONS.md §5.10 ③`(depth 모델 narrative) | "depth 2 는 `standard+` owner-worker pipeline 의 기본 도구 … 단일 역할 worker(verifier/planner/…)" | depth-2 용도에 **파이프 스테이지 워커 클래스** 추가(리뷰 보조와 병기). 스테이지 = 기본 분사(`standard+`) 명문화. |
| 2 | `OPERATIONS.md §5.10 ④`(depth-2 write 계약) | "depth 2 worker 는 기본 read-only, 구현 worker 만 제한 write" | **스테이지-워커 클래스별 write 소유**(§6 표)로 재정의. 리뷰 워커 read-only 기본은 유지. |
| 3 | `WORKFLOW.md §1.1`(intensity routing 표) | `standard`: "depth-1 owner should open bounded depth-2 verifier/planner work" | `standard+` 행에 "**스테이지 분사 기본**(plan/execute/test/report 각 headless)" 추가. v6 기준 `direct` = depth-0 inline, `quick` = depth-1 one-shot capability worker 명시. |
| 4 | `WORKFLOW.md §5`(entry→서브에이전트 분기) | "autopilot-code: 기획팀(plan)+개발팀(execute)+품질관리팀 … (in-session)" | 각 스테이지가 **headless 세션(내부에 그 팀)** 임을 명시 — 팀은 스테이지 세션 _안_ 에서 실행. |
| 5 | `CONVENTIONS.md §1`(stage graph Dispatch policy 열) | `standard`: "depth-1 owner with bounded depth-2 sub-workers when useful" | Dispatch policy 에 **스테이지 = depth-2 headless 기본**(standard+) 반영. depth 계약(§1 line 46)에 스테이지-워커 클래스 추가. |
| 6 | `DESIGN_PRINCIPLES.md §8`(Performance Preservation) | "결과 흐름: file 통해 (verdict 만 token)" | 적용 범위를 **headless 스테이지 세션→conductor** 까지 확장 명시(원칙 승격, §0.5). 2026-07-06 재설계 기본값 반전을 이력에 기록. |
| 7 | `skills/autopilot-code/references/context-and-guards.md:51` | "파이프 스테이지를 헤드리스로 쪼개면 worst of both — **금지**" | **금지 해제 → 기본 권장**으로 반전. "산출물이 상태를 완전히 담으므로 재발굴=파일로드, 연속성=파일 매체"로 우려 해소 근거 병기(§2.2·§0.5). |
| 8 | `skills/autopilot-code/references/dev-pipeline.md`(Step 1/3/4/5) | ~~"invoke Skill: `code-plan/…` (인라인)"~~ → **Phase 1 반쪽**: 앞머리 계약 블록만 추가, Step 본문은 in-session 명령형 잔존(이중 신호) | **SD-10 + v6**: `standard+` Step 1~7 본문 dispatch-first 재작성 + fallback 조건 한정형(direct·headless 불가 런타임) + SD-14 대기 계약 포함. `quick` 은 depth-1 one-shot worker 경로로 분리. |
| 8b | `skills/autopilot-code/SKILL.md` Stage Graph 표 | `standard` 행에 dispatch 모드 표기 없음 | **SD-10(b)**: `standard+` 행 = "스테이지 depth-2 headless 분사" 즉독 표기. |
| 9 | sub-skills(code-plan/execute/test/report) SKILL.md | "orchestrator 가 Skill 로 호출 … in-session 팀 위임" | 스테이지가 **독립 세션 진입점**으로도 동작하도록 입력=산출물 경로 계약 명문화(§4 완결성). 팀 위임은 세션 _안_ 그대로. (Phase 1 완료분 유지) |
| 9b | 신규 hook (`hooks/`) — conductor 의 code-* 직접 Skill 호출 감지 | 없음 | **SD-11**: reminder(soft) hook 신설 — deny 는 미결(계측 후). |
| 9c | `profiles/fragments/` + conductor 분사 `--profile` 배선 | dispatch-profiles 인프라 존재하나 스테이지-워커 fragment 없음 | **SD-12**: code-plan/execute/test/report 별 최소 프로필 fragment + conductor 기본 배선 + 토큰/시간 계측. |
| 9d | wrapper `dispatch_prompt()` depth-1 `depth_note` + Stop hook + `utilities/dispatch-wait` | one-shot 대기 계약 없음 (운영 실증 ④ conductor 조기 종료) | **SD-14**: (a) depth_note 대기 계약 주입 (b) Stop hook 게이트(open 자식 row 시 차단, 전제 2건 선해소) (c) dispatch-wait 헬퍼. |
| 10 | `adapters/claude/CLAUDE.md §0(C)` | "분사는 main 전용·깊이 1" / "in-session nested 는 ceremony 격리 못 받음" | "**conductor(depth-1)가 스테이지를 depth-2 로 분사**" 추가 — 깊이 1 전용 문구를 깊이 2 스테이지까지 확장. ceremony 격리 문구는 유지(오히려 분사 정당화). |
| 11 | `adapters/codex/AGENTS.md` · `adapters/opencode/AGENTS.md`(동형) | headless dispatch 계약 "depth 1, or depth 2 by depth-1 owner under standard+" | 동일 개정 — 스테이지 분사를 depth-2 정규 용법으로 병기. 3어댑터 parity 유지(codex/opencode preflight dispatch 도 이미 depth=2/parent 지원). |
| 12 | `adapters/claude/bin/dispatch-headless.py`(+codex/opencode preflight dispatch) | depth=2/parent/worker_role 이미 지원(§2.4) | **재작성 불요**. 판단: (a) conductor 편의용 **stage-dispatch helper**(스테이지 순서·경로 계약을 캡슐화) 신설 여부 (b) worker_role 표준값 문서화. helper 는 pilot 후 필요성 판정. |
| 13 | fleet 관제(`tools/fleet`) | in-session 서브에이전트 미표시 | ~~스테이지 row 표시~~ → **Phase 2 범위 제외** (tools/fleet/** 타 세션 소유, 2026-07-10 handoff). |
| 14 | drill 케이스 | 스테이지 분사 회귀 없음 | **스테이지 분사 회귀 케이스 신설**(Phase 2): fleet row·산출물 정상·depth≤2 강제 + **문서-효력 검증**(§8.5.5 — 프롬프트 떠먹임 없이 스킬 문서만으로 분사 발생). ※ drill 러너(loops/**) 자체는 타 세션 소유 — 케이스 정의만 본 spec 범위. |
| 15 | portable route contract + adapter model resolution | family/role affinity, exact model currentness probe, 설명 가능한 우선순위 helper가 없음 | **SD-21~23**: core는 portable family/role과 우선순위만 소유. read-only `route-dispatch`는 Claude+Codex부터 시작하고 adapter가 exact model/reasoning을 runtime-probe; OpenCode는 unknown 정직 보고. |
| 16 | Fleet process/stage collector | Codex headless child가 top-level process로 중복 노출될 수 있고 non-code job이 fuzzy `plans` 매치로 `spec:test`를 합성할 수 있음 | **SD-24**: env-marked Codex child-hidden + metadata-exact stage 분류. non-code 유사경로 fixture와 정상 code fixture를 함께 회귀 테스트. |

## 10. 기각·비채택 (근거와 함께)

| 항목 | 판정 | 근거 |
|---|---|---|
| **owner 단일 세션 + in-session 팀 유지**(2026-07-06 기본값) | **반전(비채택)** | 운영 실증 ①②③(관제 불가시·ceremony 미수령·컨텍스트 비대). v6 기준 `direct` 만 depth-0 inline 유지, `quick` 은 depth-1 one-shot worker 로 이동. |
| **quick depth-0 inline 유지**(v5까지의 기본값) | **반전(비채택)** | 사용자 승인 topology 변경(2026-07-13). quick 은 main thread 오염을 줄이고 Fleet 에 보이도록 depth-1 one-shot worker 로 이동한다. 단 quick worker 내부 micro-stages 는 inline 이고 depth-2 fan-out 은 금지한다. |
| **스테이지 세션도 depth-3 headless 를 열기** | **기각** | depth 3+ 금지 불변(§2.3·§6). 스테이지 내부 병렬은 in-session 팀으로 충분. wrapper 가 depth 3 자체를 차단. |
| **대화 컨텍스트 요약을 프롬프트로 운반**(하이브리드) | **기각** | §0.5 산출물 기반 소통 위반 — 재현 불가·drift 원천. 산출물 불완전은 스키마 보강으로 해결(§4). |
| **모든 intensity 에서 스테이지 분사** | **범위 한정** | `direct` 는 inline, `quick` 은 depth-1 one-shot worker 이지만 내부 micro-stages 는 inline 이고 depth-2 stage 분사를 열지 않는다. stage-worker 분사는 `standard+` 만. |
| **per-stage dispatch 비용을 spec 에서 수치 단정** | **미결로 이관** | research 가 per-stage dispatch cost 를 수치화 안 함(digest 주의). 손익 임계는 pilot 계측(SD-OPEN-1) — 추측 금지. |

## 11. Module 구조 (확정 — 코드 생성은 autopilot-code)

```
adapters/claude/bin/dispatch-headless.py   # (증분/무변) depth=2·parent·worker_role 이미 지원 — helper 신설은 pilot 후 판정
adapters/{codex,opencode}/bin/preflight.sh # (증분/무변) dispatch 서브커맨드 동형 — parity 문구만 개정
skills/autopilot-code/references/
  dev-pipeline.md            # 스테이지 = standard+ 분사 / direct·quick 인라인 (§9-8)
  context-and-guards.md      # 스테이지 분사 금지 → 기본 권장 반전 (§9-7)
skills/{code-plan,code-execute,code-test,code-report}/SKILL.md
                             # 독립 세션 진입점 계약(입력=산출물 경로) 명문화 (§9-9)
core/OPERATIONS.md §5.10     # depth-2 스테이지-워커 클래스 + write 소유 (§9-1,2)
core/WORKFLOW.md §1.1·§5     # 스테이지 분사 기본 반영 (§9-3,4)
core/CONVENTIONS.md §1       # Dispatch policy·depth 계약 (§9-5)
core/DESIGN_PRINCIPLES.md §8 # 산출물 기반 소통 승격·재설계 반전 이력 (§9-6)
adapters/{claude,codex,opencode} bootstrap §0(C)   # 깊이 1 전용 → 스테이지 depth-2 확장 (§9-10,11)
tools/fleet                  # (범위 제외 — 타 세션 소유, §9-13)
loops/drill                  # 스테이지 분사 회귀 케이스 정의 (§9-14, Phase 2 — 러너는 타 세션 소유)

# --- v7 추가 (구현은 후속 autopilot-code) ---
core model-routing contract                   # portable family/role·우선순위만 기록 (SD-21·22)
utilities/route-dispatch                      # read-only 후보 계산·reason trace (SD-23)
adapters/{claude,codex}/model probe mapping   # current exact ID/reasoning resolution
adapters/opencode/model probe mapping         # 미확정 동안 honest unknown
tools/fleet collector + regression fixtures   # env child-hidden·metadata-exact stage (SD-24)

# --- v2 추가 (Phase 2) ---
skills/autopilot-code/references/dev-pipeline.md   # Step 1~7 본문 dispatch-first 재작성 + SD-14 대기 절차 (SD-10)
skills/autopilot-code/SKILL.md                     # Stage Graph 표 dispatch 표기 (SD-10b)
hooks/<stage-dispatch reminder>                    # conductor 의 code-* 직접 호출 reminder (SD-11, soft)
profiles/fragments/code-{plan,execute,test,report}.md  # 스테이지-워커 최소 프로필 (SD-12)
adapters/claude/bin/dispatch-headless.py           # depth_note 대기 계약 + --profile 스테이지 배선 (SD-12·14a)
hooks/<conductor Stop 게이트>                       # open 자식 row 시 Stop 차단 (SD-14b, 전제 2건 선해소)
utilities/dispatch-wait.sh                         # 동기 대기 헬퍼 — dispatch-liveness 재사용 (SD-14c)
skills/autopilot-{draft,research,spec,design,lab}  # 스테이지 분사 계약 확산 (§12-1)
```

- 신규 코드 최소화 — wrapper 재작성 없음(§2.4). 대부분 계약 문서(core·bootstrap·SKILL) 개정 + 얇은 conductor 오케스트레이션 문구 + (판정 시) stage-dispatch helper.
- 지침 파일 문구 변경은 소유 스킬(core-first) 경유 별도 — 본 spec 은 _구조_ 만 확정.

## 12. Next — 구현 phase 분할 (autopilot-code, 본 v1 입력)

`/autopilot-code --mode dev "stage-dispatch 구현"` (worktree 브랜치).

### Phase 1 — 계약 문서 + wrapper 증분 + autopilot-code pilot (저위험, 검증 우선)
1. **계약 문서 개정** — core(OPERATIONS §5.10 ③④·CONVENTIONS §1·WORKFLOW §1.1·§5·DESIGN_PRINCIPLES §8) + adapter bootstrap §0(C) 3어댑터 동형(§9-1~6,10,11). context-and-guards.md:51 금지 반전(§9-7).
2. **dev-pipeline.md + sub-skills 계약** — 스테이지 분사 오케스트레이션(§9-8,9): conductor 가 스테이지마다 dispatch-headless(depth=2,parent,worker_role) 호출, 입력=산출물 경로.
3. **wrapper 증분** — 재작성 불요 확인 + (필요 판정 시) stage-dispatch helper. worker_role 표준값 문서화(§9-12).
4. **autopilot-code pilot** — code track 한 실제 작업을 스테이지 분사로 1회 완주.

**pilot 성공 기준(계측)**:
- fleet 에 code-plan·code-execute·code-test·code-report **스테이지별 row** 가 뜨고 liveness 가 보인다(운영 실증 ① 해소 증명).
- 각 스테이지 산출물이 §2.1 표대로 정상 생성되고, 스테이지가 앞 산출물만으로(대화 전달 0) 완주(§0.5·§4 완결성 증명).
- depth ≤ 2 강제 확인(스테이지가 depth-3 안 염), §5.8 lock 경합 미발생.
- **토큰/시간 비교 계측** — 동일 작업 in-session(현행) vs 스테이지 분사의 conductor 컨텍스트 크기·총 토큰·wall-clock. 마이크로-스테이지 inline 경계 임계(SD-OPEN-1) 캘리브레이트 데이터.

### Phase 2 — 배선 완성 + 확산 + drill 회귀 (v2 재구성, 2026-07-10 — Phase 1 머지 5b7cf33 후)

우선순위 순 (0 = 최우선):

0. **SD-10 배선 완성** — dev-pipeline.md Step 1~7 본문 dispatch-first 재작성(이중 신호 제거, fallback 조건 한정형) + SD-14 대기 계약 포함 + SKILL.md Stage Graph 표 dispatch 표기(§8.5.1). SD-11 reminder hook 신설(§8.5.2). SD-14 wrapper 증분 — depth_note 대기 계약·Stop hook 게이트(전제 2건 선해소)·dispatch-wait 헬퍼(§8.5.7).
1. **확산** — autopilot-draft/research/spec/design/lab 파이프에 스테이지 분사 계약 적용. 각 파이프의 스테이지-워커 클래스·산출물 계약 매핑(§6 동형 표 신설).
2. **SD-12 프로필 배선** — 스테이지-워커별 최소 프로필 fragment + conductor `--profile` 기본 배선 + 토큰/시간 계측(§8.5.3).
3. **drill 케이스** — 스테이지 분사 회귀(§9-14): fleet row·산출물·depth≤2·lock 미경합 + **문서-효력 검증**(§8.5.5). 케이스 정의만 — drill 러너(loops/**)는 타 세션 소유.
4. **부수발견 반영** — SD-13 conductor spec 전제 선보장(§8.5.4) + SD-OPEN-2 curator 기동 관찰 로그(§8.5.6).
5. **SD-OPEN-1 계측 누적만** — 마이크로-스테이지 inline 임계는 확정하지 않음, 실운영 계측 수집만.

**제외 (타 세션 소유, 2026-07-10 handoff)**: `loops/**` · `tools/fleet/**` (§9-13 fleet 표시 이관, drill 러너 fix 3건 handoff 済).

## 13. 결정 목록

- **SD-1**: depth-1 owner = 얇은 conductor, 스테이지(plan/execute/test/report) = depth-2 headless 세션. conductor 는 verdict/게이트만, 스테이지 본문 미독. (§3, 사용자 결정·§5.10 depth)
- **SD-2**: 인터페이스 = 산출물 파일만. 세션 간 대화 컨텍스트 전달 금지. 계약 완결성 의무. (§4·§0.5, 사용자 결정·research §4-(8)·DESIGN_PRINCIPLES §8)
- **SD-3**: 스테이지 세션 = jobs.log `depth=2,parent=<conductor>,worker_role=<sub-skill>,owner=autopilot-code` 등록 → fleet 스테이지 row. stealth-death 가드는 conductor 책임. (§5, §5.10 레지스트리·운영 실증 ①②)
- **SD-4**: depth-2 write 계약을 스테이지-워커 클래스별 소유로 재정의(plan=plan폴더·execute=소스+dev로그·test=test로그·report=report+analysis). depth 3+ 금지 유지. (§6, §5.10 ④ 개정)
- **SD-5**: 스테이지 model role 은 conductor 가 CONVENTIONS §2 매핑으로 명시(wrapper 암묵 선택 금지). (§7, §5.10 ⑦·§2.3)
- **SD-6**: 동시 상한 5 = Σ(conductor+활성 스테이지). 마이크로-스테이지 inline. 실패=스테이지만 재분사(산출물 재사용). lock 은 report 의 pipeline_summary 쓰기만. (§8, §5.10 ⑤·§5.8)
- **SD-7**: 영향 표면 14곳(§9 표) — core·bootstrap·SKILL·wrapper·fleet·drill. 문구 편집은 소유 스킬(core-first) 별도. (§9·§11)
- **SD-8**: 적용 = `standard+` 기본. `direct` = depth-0 inline 유지, `quick` = v6에서 depth-1 one-shot capability worker 로 승격. 2026-07-06 "owner 단일 세션" 기본값의 명시적 반전. (§0·§10, 사용자 결정)
- **SD-9**: wrapper 재작성 불요 — depth=2/parent/worker_role 이미 지원. helper 신설은 pilot 후 판정. (§2.4·§11·§9-12)
- **SD-OPEN-1**(미결 — 계측 누적): 마이크로-스테이지 inline 의 정확한 손익 임계(어느 스테이지 크기부터 분사가 이득). research 가 per-stage cost 미수치화 → 추측 금지. Phase 1 pilot 1표본(plan 218s/execute 255s/test 46s/report 28s) 확보 — Phase 2 는 계측 누적만, 확정은 표본 축적 후. (§8·§12)

### v2 추가 (2026-07-10 — Phase 2 입력)

- **SD-10**: dev-pipeline.md Step 1~7 본문 dispatch-first 재작성(이중 신호 제거, in-session 은 direct·headless 불가 런타임 한정 fallback) + SKILL.md Stage Graph dispatch 표기. v6 이후 quick 은 depth-1 one-shot worker 경로로 분리. Phase 2 최우선. (§8.5.1, 사용자 확인 발견)
- **SD-11**: conductor 의 code-* 직접 Skill 호출 시 reminder hook(soft) — deny 는 drill·계측 후 재판단 미결. (§8.5.2, drill g3/g6 선례)
- **SD-12**: 스테이지-워커별 dispatch-profiles 최소 fragment + conductor `--profile` 기본 배선 + 토큰/시간 계측. (§8.5.3, 사용자 요구)
- **SD-13**: conductor 의 스테이지 분사 전 spec 전제 선보장. (§8.5.4, pilot 부수발견)
- **SD-14**: conductor 대기 계약 결정론화 — (a) wrapper depth_note one-shot 대기 계약 (b) Stop hook 게이트(open 자식 row 차단, -p Stop 발화 검증·registry 갭 선해소 전제) (c) dispatch-wait 헬퍼. dev-pipeline 본문(SD-10)에 대기 절차 포함. (§8.5.7, 운영 실증 ④)
- **SD-OPEN-2**(미결 — 관찰): 스테이지 SessionEnd mem curator 기동 영향 — 계측 로그로 관찰만, 개입은 증거 후. (§8.5.6)

### v3 추가 (2026-07-10 — 사용량 복원력 + 크로스 하네스)

- **SD-15**: wrapper limit-사망 즉시 감지 — launch 직후 조기 exit + 로그 limit 패턴 → jobs.log row 자동 마감(`dead-<사유>`) + reset 시각 표면화. dispatch-wait/liveness 도 로그 패턴을 DEAD 근거에 추가. 재시도는 안 함(orchestrator 판단). (§8.5.7b, 운영 실증 ⑤)
- **SD-16**: 사용량-인지 상호보완 크로스 하네스 분사 — (a) usage-check 헬퍼(양 하네스 limit 상태 결정론 조회, runtime-currentness 조사 필수) (b) 상호보완 라우팅(사용량 failover + 특성 강점 배치 + 검증 자리 타 모델 계열 교차) (c) fleet 연속성·계측 (d) thorough+ 다축 동시성 실측 검증. (§8.5.7c, 사용자 요구)
- **SD-OPEN-3**(미결): 보완 라우팅 가중 정책 — 초기 "limit 회피 > 특성 적합 > 분산" + 한도 비대칭 기본값(Claude>Codex 가변, `HARNESS_CAPACITY_BIAS`), 계측 후 조정. (§8.5.7c)

### v4 추가 (2026-07-10 — 도그푸딩 정련)

- **SD-15b**: 로그-패턴 DEAD 앵커링 — CLI 종료 에러 라인 형식 한정 + 정상 완주 신호 결합(완주면 배제). "limit 논하는 보고문" 오탐 실측 대응. (§8.6.1)
- **SD-16e**: usage-check reset 의미론 — reset 경과 시 ok(expired), reset 부재 마커는 창 단축/구분 표기, 수동 마감 reset 기입 계약화. stale limited 오탐 실측 대응. (§8.6.2)
### v5 추가 (2026-07-10 — 사용자 결정 (a))

- **SD-17**: 적용 조건 정련 — 분사 기본 불변 + conductor 의 separability 판정. 비분리 시 inline 허용(판정 기록 의무·분리 부분 병렬·자기수정은 opt-out 경로). 기록 없는 inline = 위반(감사 표면). SD-OPEN-1 의 질적 축. (§8.7, conductor 3연속 실측)

- **SD-11b**: reminder → **deny 상향** — wrapper 가 `AGENT_DISPATCH_INTENSITY` env 주입으로 결정론 조건 확보, [depth1·standard+·code-* Skill 직접 호출] hard deny. 자기수정 예외는 문서 조항이 아니라 orchestrator 명시 opt-out 으로만. 문서-효력 2연속 실패(soft reminder 무효) 실증. (§8.6.3)

### v6 추가 (2026-07-13 — quick depth-1 topology)

- **SD-18**: intensity topology 재정의 — `direct` depth-0 inline, `quick` depth-1 one-shot capability worker, `standard+` depth-1 conductor → 순차 depth-2 stage-workers. quick worker 는 micro-plan·plan-check-lite·implementation·focused verification·concise report 를 한 세션에서 끝내고 depth-2 를 열지 않는다. mutation quick 은 isolated worktree 를 사용한다. (§8.8.1)
- **SD-19**: Codex quick dispatch preference/fallback — headless check 통과 시 headless dispatch 우선(Fleet-visible). headless 실패 + native subagent ok 이면 native subagent fallback + Fleet visibility degradation note. 둘 다 불가하면 inline + concise fallback reason. parent 로컬 근거: native subagent ok, strict headless projection ok, quick depth-1 dry-run accepted, quick depth-2 forbidden. (§8.8.2)
- **SD-20**: Fleet quick 표시 계약 — depth-1 quick worker 는 하나의 blinking `quick/exec` activity stage 로 표시. quick depth-2 child row 는 contract violation. (§8.8.3)

### v7 추가 (2026-07-13 — orchestration/model routing + Fleet hotfix)

- **SD-21**: depth-1 `standard+` conductor는 `orchestrator` + high-reasoning/deep orchestration 기본. fast orchestration은 mechanical-only. 얇음은 context 소유 범위이지 판단 tier 하향이 아니다. (§7.1)
- **SD-22**: planning/architecture/decomposition=`deep maker` + GPT family via Codex affinity(비-hard-pin), plan review는 다른 family 선호. 우선순위=`explicit choice > hard eligibility/tool/runtime/account/limit > stage affinity > maker-checker family diversity > capacity/cost/latency`. core는 portable family/role, adapter는 runtime-probed exact model/reasoning을 소유. 공식 GPT-5.6 Sol 권장과 Codex alias/exact-ID 차이를 currentness 사례로 기록. (§7.1)
- **SD-23**: read-only `route-dispatch` helper — Claude+Codex 초기 지원, 입력 후보/상태에서 family·role·adapter exact ID·reason trace·fallback을 계산하되 dispatch/mutation 금지. OpenCode는 probe 계약 확정 전 honest `unknown`. (§7.1)
- **SD-24**: Fleet hotfix acceptance — env-marked Codex headless dispatch process child-hidden, non-code job은 fuzzy `plans` 매치 및 거짓 `spec:test` 0건, 정상 code stage 표시 유지. (§8.9)

### v8 추가 (2026-07-14 — canonical artifact root + worktree cleanup)

- **SD-25 — source-only worker worktree**: task worktree의 `.agent_reports/`·legacy `.claude_reports/`는 tracked snapshot일 수 있지만 worker의 쓰기 대상이 아니다. `AGENT_ARTIFACT_ROOT`가 있으면 그 절대경로가 우선이고, 없으면 Git primary worktree(`git worktree list --porcelain` 첫 entry)의 `.agent_reports/`를 canonical root로 자동 해석한다. canonical `.agent_reports/`가 없고 `.claude_reports/`만 있을 때에만 legacy fallback한다. non-Git은 현재 project root로 fallback한다.
- **SD-26 — runtime-scoped artifact access**: dispatch wrapper 3종은 canonical root를 계산해 child env와 jobs metadata/prompt에 전달한다. Claude/Codex는 `--add-dir <canonical-root>`로 그 경로만 추가 writable로 연다. OpenCode는 기존 설정을 보존하면서 canonical root에 한정한 `permission.external_directory=allow` 규칙만 합성한다. runtime 전체 외부경로 허용은 금지한다.
- **SD-27 — fail-closed local-artifact write guard**: linked task worktree에서 canonical root와 다른 `<worktree>/.agent_reports/**` 또는 legacy 경로 쓰기는 차단한다. canonical root 절대경로와 primary worktree의 정상 쓰기는 허용한다. status·spec read/write gate·pipeline lock은 동일 resolver를 사용하고 relative cwd를 물리 절대경로로 정규화한다.
- **SD-28 — cleanup eligibility state machine**: cleanup은 기본 dry-run/check이고 명시 `--apply`만 변경한다. primary worktree, dirty(untracked 포함), Git operation 중, locked, unmerged HEAD, integration ref 미push/원격보다 뒤처짐, exact registered PID 또는 process cwd가 살아 있는 대상은 fail-closed `blocked`다. 대상이 linked worktree이고 clean이며 HEAD가 integration ref의 ancestor이고 integration ref가 upstream과 동기화됐고 active process가 없을 때만 `git worktree remove`(force 금지)+`prune`한다.
- **SD-29 — registry reconciliation and audit**: merge 전 생성된 stale open row는 다른 안전 조건이 모두 성립할 때만 lock 아래 `done,note=cleanup-merged`로 화해한다. branch는 rollback point로 기본 보존하며 정리 결과는 bounded audit log에 남긴다. artifact harvest/copy는 cleanup 전제에서 제거한다. `git worktree lock`은 장기 보존 의도를 나타내는 deterministic veto다.
- **SD-30 — orchestration-owned trigger**: main/orchestrator는 자신이 수확한 작업을 merge하고 통합 검증과 push까지 끝낸 직후 guarded cleanup을 자동 호출한다. Claude `SessionEnd`/Codex `Stop`/OpenCode `session.idle` 같은 runtime lifecycle event는 merge·push 증거가 아니므로 destructive cleanup을 실행하지 않고 diagnostics/fallback 안내만 제공한다.

**v8 acceptance**:

1. linked worker에서 artifact resolver가 main canonical root를 반환하고, worker-local artifact 쓰기는 차단된다.
2. Claude·Codex·OpenCode dispatch가 동일 canonical root와 runtime별 최소 외부-write 권한을 전달한다.
3. eligible worktree는 `--apply`에서 제거되며 branch는 남는다. dirty·unmerged·locked·active·push-pending fixture는 모두 보존된다.
4. stale registry row는 cleanup 안전성이 이미 증명된 경우에만 done으로 화해되고, artifact recovery 여부는 eligibility에 영향을 주지 않는다.
5. portable/core-first, generated adapter, invariant/boundary 검증이 통과한다.

## 13.1 v9 — capability-specific routing topology (2026-07-15)

> 근거: 사용자 확정사항과 `../../plans/2026-07-15_capability-routing-topology/plan.md` 및 그 `checklist.md`, `_internal/metrics.md`, `_internal/plan_check.md`. 이 절은 v1~v8의 code-shaped 기본을 폐기하지 않고 **code에 한정**하며, 모든 entry capability에 같은 four-stage 그래프를 강제하던 해석 가능성을 제거한다.

### 13.1.1 SD-31 — depth-0 main 경계와 direct/quick 불변식

- substantive tracked work에서 depth-0 main은 context owner, semantic router, monitor, integrator만 맡는다. capability 산출물 생산·장기 실행·durable stage 수행은 하지 않는다.
- `direct`는 예외가 아니라 정상 inline route다. 결과가 원자적이고 대상/범위가 이미 알려졌으며 shared contract·spec·public API·resource run·artifact handoff·independent verification이 없고 focused verification 한 번으로 끝날 때만 depth-0 inline이다.
- 위 direct 조건 중 하나라도 불충족하지만 작업이 한 writer·한 세션·bounded outcome으로 명확히 닫히면 `quick`: depth-1 one-shot owner가 orient-lite → micro-plan → plan-check-lite → produce → focused verify → concise report를 수행하며 depth-2는 금지한다.
- `standard+`는 capability recipe를 사용한다. depth-1 owner만 있는 transaction, reviewer/map fan-out, durable staged graph, detached resource runner 결합을 모두 허용하며 **depth-2 존재 자체를 의무화하지 않는다**.

### 13.1.2 SD-32 — 네 축 분리

라우팅은 다음 네 축을 독립 필드로 기록한다. 한 축의 값으로 다른 축을 추정하지 않는다.

| Axis | 의미 | 예시 |
|---|---|---|
| `intensity` | effort, assurance, promotion level | direct, quick, standard, strong, thorough, adversarial |
| `execution_topology` | 실행 graph shape | inline, one-shot-owner, transactional-owner, map-reduce, staged, staged+resource |
| `worker_kind` | node 책임과 write 의미 | capability-owner, pipeline-stage, review-worker, map-worker, resource-runner |
| `transport` | runtime execution surface | headless, native-subagent, detached-process, inline-fallback |

사용자-facing 새 topology/transport 옵션은 만들지 않는다. 사용자는 capability와 intensity를 선택하고 registry/compiler가 나머지를 파생한다. `resource-runner`는 OS process이며 model recursion depth가 아니다.

### 13.1.3 SD-33 — topology registry SoT

portable 실행 graph의 단일 machine-readable SoT는 **`capabilities/topologies.json`**(`schema_version: 1`)이다. `harness-manifest.json`은 identifier/dependency/role catalog를 유지하고 topology 본문을 중복 저장하지 않는다. 생성 manifest에는 registry digest와 compact summary만 둔다.

각 `(capability, mode)` recipe는 최소 다음을 선언한다.

- `topology_class`, `direct_predicates`, `promotion_signals`, `quick.max_depth=1`
- standard+의 `owner_depth`, node `id/kind/depends_on/role/inputs/outputs/write_scope/resource_class/completion_gate`
- 허용 transport class와 checked fallback, pause/human gate, resume/retry boundary
- canonical single-writer scope와 read-only reviewer/map constraints

validator는 entry capability/mode exact coverage, schema/digest, depth≤2, quick depth-2 금지, DAG cycle, missing inputs/outputs/gates, concurrent write overlap, reviewer read-only, map canonical-merge 금지, resource-runner depth 오용을 fail-closed로 검사한다. topology summary는 `capability-info`와 route에서 on demand 생성한다.

### 13.1.4 SD-34 — immutable route record와 compiler

`utilities/capability-route.py`는 registry, intensity, observed/declared signals, runtime eligibility를 입력으로 immutable route record를 만든다. 일반 cycle은 owning artifact의 `_internal/route.json`에, durable cycle이 없는 direct/quick 진단은 dispatch registry의 route payload에 기록한다.

필수 필드: `route_id`, capability/mode/intensity, four-axis values, promotion signals와 source(`observed|declared|capability-default`), owner/node graph, role/write scope/resource class, selected transport와 eligibility/fallback evidence, model route trace, registry digest, source commit, absolute cwd, canonical artifact root, completion gates, route hash.

inline enum은 `atomic-direct`, `nonseparable-transaction`, `runtime-unavailable`, `dispatch-infra-self-modification`, `user-restricted`로 제한한다. `atomic-direct`는 정상 route이고 standard+ inline은 enum+evidence+metrics가 있어야 한다. `preflight route`와 `dispatch-route --route ... --node ...`가 동일 record/hash로 prompt, jobs row, liveness, completion marker를 연결한다.

### 13.1.5 SD-35 — bounded work promotion signals

명확히 scoped된 작업도 다음 중 하나면 standard+로 승격한다.

- `resource_class ∈ {gpu,long-running,bulk-generation}` 또는 parent session과 분리된 lifecycle
- 서로 다른 write scope의 durable output stage가 2개 이상
- metrics→media/figure→HTML/report처럼 동기화할 산출물이 3개 이상
- spec, public API, schema, shared contract 변경
- independent verifier/adversary가 completion condition
- partial failure의 stage-level resume/retry 필요
- multi-runtime parity 또는 external-facing irreversible gate가 completion condition

위 신호가 없고 direct all-predicate가 참이면 direct, direct는 아니지만 one writer/one session/bounded verify로 닫히면 quick이다. 파일 수·예상 시간 하나만으로 승격하지 않으며 semantic signal과 관찰 signal을 route record에 함께 남긴다.

### 13.1.6 SD-36 — capability/mode topology registry mapping

| Capability/mode | Standard+ recipe | Depth-2 / resource policy | Completion contract |
|---|---|---|---|
| `autopilot-apply` | owner → `apply` single writer → `verify` read-only → handback/human gate | 조건부 apply stage+reviewer | applied artifact hash, focused compile/test, explicit handback |
| `autopilot-code` | `plan → execute → test → report` | durable depth-2 stages 필수 | plan/checklist, source diff, tests, final report |
| `autopilot-design` | conductor init/confirm → `refs` → `build(tokens+components)` single writer → `visual-review` → `handoff` | staged; named phase마다 1세션 금지 | real-render evidence, token contract, review verdict, handoff |
| `autopilot-draft` | `material+strategy → draft-production → review/refine → finalize` | 조건부 staged; canonical draft writer는 한 시점에 하나 | evidence map, draft, review disposition, finalized artifact |
| `autopilot-lab setup` | owner contract → `scaffold` writer → `smoke` verifier; full run은 별도 human-gated resource runner | 조건부 stages + detached process | scaffold + passed hash-bound smoke; run authorization separate |
| `autopilot-lab eval` | `eval/metrics → media/playback → report → independent-verify → spec/note sync` | staged + detached GPU/long runner | run/metrics lineage, media/report manifest, independent verdict |
| `autopilot-note` | map workers may scan/analyze; depth-1 owner alone routes/applies canonical notes and digest | map/reviewer only, ordinary mutation stage 없음 | source coverage + single-writer digest/routing log |
| `autopilot-refine` | depth-1 transactional owner owns preview/snapshot/apply; fact/style reviewers read-only | reviewer only by default | snapshot, diff preview/disposition, verified revised artifact |
| `autopilot-research` | retrieval map workers → `analysis/synthesis` single writer → `report` → `claim-verify` | map + staged | source/card coverage, synthesis, report, claim verdict |
| `autopilot-ship` | depth-1 release-setup owner + security/release reviewers; deploy is external human gate | reviewer only by default | setup/checklist, review verdicts, explicit deploy authorization |
| `autopilot-spec` | depth-1 owner owns PRD transaction; research/review/scaffold만 선택적 workers | asymmetric; PRD 3-file transaction depth-2 writer 금지 | version snapshot + locked atomic PRD/state/summary consistency |

### 13.1.7 SD-37 — transactional single-writer preservation

`autopilot-spec`, `autopilot-refine`, `autopilot-note`, `autopilot-ship`의 canonical transaction은 depth-1 owner 한 명이 쓴다. reviewer/map worker는 read-only 또는 shard output만 쓰며 canonical merge/apply를 하지 않는다. `autopilot-apply`와 draft/design의 mutation도 registry가 지정한 단일 writer만 소유한다. validator는 동시에 runnable한 node의 write-scope overlap을 거부한다.

### 13.1.8 SD-38 — runtime/adapter boundary and recorded evidence

portable core/capability files는 graph meaning, roles, write scope, gates만 소유한다. exact model/reasoning, CLI argv, approval/sandbox, native subagent configuration, hook schema, projection discovery, detached backend는 각 `adapters/{claude,codex,opencode}`가 독립 구현·검증한다.

2026-07-15 plan에 기록된 current evidence를 구현 gate로 재사용한다: Codex `PreToolUse`는 conditional hard-deny 계약으로 간주할 수 없으므로 repo-owned wrappers에서 route/completion을 강제한다; native subagent의 `agents.max_threads/max_depth`는 registered `codex exec` headless와 별도 surface다; `codex exec`는 non-interactive transport다; local probe에서 pipeline/topology fields는 code에만 있었고 primary/linked headless check는 skill discovery/projection identity 문제로 실패했다. 근거와 URL은 `../../plans/2026-07-15_capability-routing-topology/plan.md` §3·§7.3~7.4에 고정하며 구현 전 currentness를 다시 확인한다.

### 13.1.9 SD-39 — detached resource job contract

GPU/long/bulk 작업은 model worker가 아니라 route-linked detached process로 실행한다. adapter는 검증된 backend를 선택하되 portable contract는 process group, PID, `/proc` start time, command hash, absolute cwd, canonical artifact/log path, start time, status, route id를 기록한다. `run-status`, `run-tail`, `run-stop`은 registry에 재부착하며 PID 단독 일치를 금지한다. parent/conductor 종료 뒤에도 job이 살아 있고 새 session이 동일 identity로 재부착할 수 있어야 한다. user-systemd는 adapter가 검증한 optional backend이고 portable fallback은 `setsid+nohup` 계열이다.

### 13.1.10 SD-40 — global model spawn governor

repo-owned headless/title/distill/loop model spawn은 canonical atomic lease pool 하나를 공유한다. total cap 기본 5, class cap, rolling start budget, kill switch, stale lease recovery를 제공한다. lease 획득 실패는 registry/model spawn을 0건으로 유지한다. 50개 동시 launch fixture에서 active lease가 cap을 넘지 않아야 한다. native runtime subagents는 별도 user-owned surface이므로 recommended limits와 preflight disclosure만 제공하며 runtime config를 자동 편집하지 않는다.

### 13.1.11 SD-41 — smoke and report completion contracts

- setup/eval의 smoke는 기본 mandatory다. attestation은 config hash, code hash, checkpoint/input signature, command, exit status를 기록하고 full run은 동일 hash의 passed attestation 없이는 시작하지 않는다. 1-batch가 불가능한 mode는 registry의 named minimal probe를 사용하며 자유로운 skip은 없다.
- report는 shared portable base schema `capabilities/report-manifest.schema.json`의 `report_manifest.json` 하나에서 Markdown과 user-facing HTML을 생성한다. capability별 extension은 동일 manifest의 namespaced section으로 추가하며 별도 assembler SoT를 만들지 않는다.
- lab extension은 audio↔waveform↔spectrogram↔playback 1:1, summary statistics의 Markdown/HTML 동시 존재, 48 kHz/full-band/house parameters, media hash/link binding, representative visual-review evidence, claim/range/figure-semantic evidence를 검사한다. HTML/media gate 실패 시 Markdown이 완전해도 completion은 fail이다.

### 13.1.12 SD-42 — absolute cwd and spec-nudge matching

route/dispatch/run registry는 physical absolute cwd와 canonical artifact root만 저장한다. guarded operation에서 current cwd와 route cwd가 다르면 structured failure이며 일반 read-only shell에는 전역 warning을 주입하지 않는다.

spec-sync nudge는 standalone 숫자를 identifier로 보지 않는다. `key=value`, prefix가 있는 requirement id, version/unit와 결합된 token만 비교한다. `«3»`, `«1»` 삭제는 nudge 0건이어야 하며 `SD-31`, `schema_version=1`, `48 kHz`, `v9` 같은 structured token은 해당 spec line을 정확히 찾는 fixture를 둔다.

### 13.1.13 SD-43 — lightweight parity and independent sibling verification

full topology graph는 on-demand registry data로 유지하고 always-loaded bootstrap, Skill frontmatter, generated adapter Skill/command에 복제하지 않는다. generated surface에는 portable source pointer와 digest/compact class summary만 둔다. checked footprint baseline과 strict 5% budget을 넘으면 fail한다.

Claude, Codex, OpenCode는 sibling realization이며 각 adapter의 capability-info, route, projection, dispatch, fallback을 독립 검증한다. 한 adapter의 PASS를 다른 adapter의 completion proxy로 사용하지 않는다. unsupported runtime mechanic은 checked fallback 또는 `unsupported/unverified`로 보고한다. source→generator→projection 경로만 허용하고 generated copy를 손으로 수정하지 않는다.

### 13.1.14 v9 acceptance criteria

1. registry가 모든 10개 entry capability와 lab setup/eval mode를 exact cover하고 quick-depth2/depth3/cycle/write-overlap/missing-gate/reviewer-write/resource-depth negative fixtures를 거부한다.
2. direct all-predicate, ambiguous→quick, promotion-any→standard+ property tests가 통과하고 spec/refine/note/ship의 not-all-depth2 비대칭이 snapshot으로 보존된다.
3. 하나의 route command가 route hash, prompt, jobs row, liveness/harvest, completion marker에 동일 node identity를 남긴다.
4. parent session 강제 종료 뒤 detached job이 계속 실행되고 `(pid,start_time,command_hash)`로 재부착되며 PID reuse fixture를 거부한다.
5. 50-way concurrent spawn에서 total/class/rolling cap, kill switch, stale recovery가 atomic하게 동작한다.
6. stale/missing smoke는 full run을 차단하고 동일 hash의 passed smoke만 허용한다.
7. HTML stats 누락, media 1:1 불일치, house parameter/hash/link 불일치가 각각 report completion을 fail-closed로 막는다.
8. route/job/run의 cwd는 absolute이고 mismatch가 structured failure다. standalone-number spec-nudge fixture는 0건, structured-token fixture는 exact match다.
9. normal linked worktree와 harness self-modification ephemeral projection 모두 Codex headless check를 통과하며 plugin-only/native-symlink discovery를 각각 검증한다.
10. portable guards, registry/manifest generator `--check`, context-footprint strict budget, Claude/Codex/OpenCode sibling projection/conformance, adaptation boundary, Fleet dispatch, doctor/runtime projection, `git diff --check`가 각각 통과한다.

### 13.1.15 rollout boundary

registry/compiler는 report-only로 시작하고 capability feature flag와 low-level compatibility window를 둔다. code pilot 뒤 lab eval, design/draft/research, transactional capabilities, apply/lab setup 순으로 one-shot+standard+ 실제 route를 검증한다. false positive 시 capability flag만 rollback하고 registry/route trace는 보존한다. source implementation, adapter projection, deployment는 후속 `autopilot-code`/`autopilot-ship` 작업이며 본 v9 transaction은 spec artifact만 변경한다.

## 13.2 v10 — tracked×dispatch 축 분리와 route-scope 집행 (2026-07-15)

> 근거: `../../plans/2026-07-15_capability-routing-topology/_internal/tracked-dispatch-conflict-diagnosis.md`. tracked 강제는 **산출물 차원의 불변식**(무엇이 존재해야 하고, 어떤 순서로, 누가 소유하는가)이고 분사는 **실행 차원의 토폴로지**(어느 세션이 어떤 write scope로 실행하는가)로, 본질적 상충이 없는 직교 계약이다. 현행 충돌의 뿌리는 ① tracked 여부가 intensity/dispatch escalation에 결합됨 ② tracked 집행 장치(hook·read marker·routing reminder)가 세션 단위라 분사가 실행을 여러 세션으로 쪼갤 때 투영 유실(marker) 또는 중복 발화(guard 재적용·재라우팅)함. v10은 tracked 약화가 아니라 (a) Tracking 축 분리 (b) tracked 집행의 세션 스코프→route 스코프 승격으로 닫는다. 진단 F6(depth-2 code 중심)·F7(transaction back-jump)은 v9 SD-36~38이 이미 답이므로 추가 결정 없음, F3(guard 뒤늦은 발화)은 SD-45에 흡수.

### 13.2.1 SD-44 — Tracking 다섯째 독립 축과 quick 경계 재확정 (진단 D1, 사용자 확정 2026-07-15)

- **Tracking = 다섯째 독립 축**: v9 SD-32의 네 축(intensity/execution_topology/worker_kind/transport)에 `tracking`을 다섯째 독립 필드로 추가한다. tracked 여부는 **산출물 계약**(산출물 필요 여부·생성 순서·소유 capability·검증 계약)만 결정하고, 분사 여부·규모는 route record의 promotion signals(SD-35)와 separability(SD-17)가 결정한다. 한 축의 값으로 다른 축을 추정하지 않는다는 SD-32 원칙이 tracking에도 적용된다.
- **tracked→escalation 결합 문구 제거**: `WORKFLOW.md:165` "Small localized *tracked* change → quick", `OPERATIONS.md:109` "Small tracked quick work → Depth-1 one-shot worker" 류 — "tracked라는 사실"을 dispatch 강도의 근거로 쓰는 문구를 promotion/separability 신호 기반 문구로 대체한다(구현 phase surface census 대상). tracked 사실 단독은 route record의 escalation 근거 필드에 올 수 없다.
- **quick 경계는 현행 유지 (사용자 선택 (a), 2026-07-15)**: direct all-predicate 미달이지만 명확한 독립 작업 패키지도 아닌 애매한 작업은 **quick depth-1 one-shot으로 기운다** — 메인 컨텍스트 보호 우선. SD-18(2026-07-13)·SD-31(v9)과 정합. Codex 권고(명확한 독립 작업 패키지가 있을 때만 depth-1, 아니면 inline — dispatch 오버헤드 절감 우선)는 **기각**: 기존 사용자 결정과 충돌하며, 오버헤드 절감보다 main context 보호가 우선한다는 판단의 재확정.
- **선택 근거 기록 의무**: direct/quick/standard+ 선택의 근거 신호(어느 축·어느 signal)를 route record에 남긴다.

### 13.2.2 SD-45 — worker manifest-consumer 계약 (진단 D2, F3 흡수)

- **worker는 라우팅을 재선택하지 않는다**: capability/intensity/topology 결정과 route record 발행(SD-34)은 main/conductor가 소유한다. worker의 계약 = ① route record hash 검증 ② 배정된 node scope만 실행 ③ 증거·결과 반환. worker가 record와 다른 capability/intensity로 재해석·재선택하면 계약 위반.
- **tracked gate 통과 증거의 record 운반**: route record 필수 필드에 tracked gate 증거 4종 — spec-read 여부, drift verdict, tracked/untracked mode, artifact-guard 전제 충족(SD-13 conductor 선보장 결과) — 을 추가한다. 세션 지역적 read marker 재취득의 기본 대체 경로이며, worker가 실제로 prd.md를 새로 읽은 경우의 marker 기록은 유지한다. (근거 실측: v9 process log "Codex root/core read-marker persistence was unavailable under worker sandbox, so instruction-only fallback used" — 세션 스코프 집행 장치가 분사에서 투영되지 않는 사례.)
- **worker 부트스트랩 축소**: required bootstrap의 `status → prompt-signal → mode → route` 재실행(`dispatch-headless.py` 및 codex/opencode preflight 동형)을 "재라우팅"에서 **"record 검증 + 안전 확인(absolute cwd·canonical artifact root·git state)" 전용**으로 축소한다. 3어댑터 동형 적용.
- **F3 구조 원인의 봉합**: 판단 시점(main)과 집행 시점(worker)의 분리로 artifact-guard가 worker 레벨에서 뒤늦게 발화하던 경로(SD-13 실측)는, gate 전제 충족 증거가 record에 실려 worker 시작 전에 검증되므로 구조적으로 닫힌다.

### 13.2.3 SD-46 — guard↔topology 정합성 validator (진단 D3)

- **validator 항목 추가**: SD-33 validator 검사 목록에 **artifact-guard 생성 순서 규칙 ↔ stage `write_scope` 정합성**을 fail-closed 항목으로 추가한다 — `spec/**` write를 선언한 node는 그 capability가 spec의 sole-update-path 소유자(`autopilot-spec`)이거나 conductor 선보장 gate(SD-13)를 선언해야 한다. registry가 허용한 write를 guard가 막는 조합이 validation 시점에 드러나야 하며 runtime까지 잠복하면 안 된다.
- **runtime 충돌의 structured failure**: 그럼에도 runtime에서 guard가 route-승인된 write를 차단하면 조용한 실패가 아니라 **structured failure + route record 참조**를 낸다(SD-42 cwd mismatch와 동형 의미론).

### 13.2.4 SD-47 — 공유 tracked 표면의 병렬 mutation 계약 (진단 D4)

- **직렬화 지점 명시**: `plans/<slug>/`는 경로 분리로 무경합이지만 `spec/` 3-file transaction(`prd.md`·`pipeline_state.yaml`·`pipeline_summary.md`)과 `_internal/versions/v{N}` 버전 체인은 **본질적 직렬화 지점**이다. §5.8 lock의 보호 범위를 spec-transaction 전체(snapshot→prd→state→summary 원자 시퀀스)로 명시하고, 버전 체인 갱신(snapshot 생성 포함)은 lock 보유 중에만 수행한다.
- **경합 규칙 = 대기, 재시도 아님**: 선점 실패(BLOCKED)면 동일 버전 번호 재선점을 시도하지 않는다 — 대기 후 최신 상태를 다시 읽고 **다음 버전 번호**로 진입한다. 두 세션이 같은 `v{N}` snapshot을 만드는 경로를 계약으로 차단한다.
- **lock 밖 위험의 선실행 가드**: §5.8 lock은 artifact write만 보호하고 merge/rebase·dirty·동일 branch를 감지하지 않는다(`OPERATIONS.md:57`, §5.9 별도 가드). 병렬 분사 사이클이 spec에 닿으면 route record에 spec-touch를 선언하고 conductor가 §5.9 git-state 가드를 spec-transaction 전에 선실행한다. "소스는 격리됐지만 추적 상태는 충돌"하는 경로(v8 source-only worktree가 소스 축에서 닫은 것의 tracked-표면 판)를 계약으로 닫는다. 현행의 사람-중재 직렬화(plan §10 "parity merge 후 rebase 전에는 수정하지 않는다")를 계약 규칙으로 승격.

### 13.2.5 v10 acceptance criteria

1. (SD-44) route record에 tracking이 독립 필드로 기록되고, escalation 근거 필드에 tracked 사실 단독이 올 수 없다. direct all-predicate/ambiguous→quick/promotion-any→standard+ property test는 v9 기준 그대로 통과한다(quick 경계 불변 증명).
2. (SD-44) tracked→escalation 결합 문구(`WORKFLOW.md:165`·`OPERATIONS.md:109` 류)가 promotion/separability 신호 기반 문구로 대체된다 — 구현 phase surface census에서 잔존 0건.
3. (SD-45) route record hash 불일치 또는 배정 node scope 밖 실행을 worker가 거부하고, tracked gate 증거 4종(spec-read·drift verdict·tracked/untracked mode·guard 전제)이 record에 없으면 tracked 대상 worker가 시작하지 않는다.
4. (SD-45) worker bootstrap이 capability/intensity/topology 재선택을 수행하지 않음을 3어댑터 fixture로 각각 독립 검증한다(SD-43 sibling 원칙 — 한 어댑터 PASS를 타 어댑터 proxy로 쓰지 않음).
5. (SD-46) `spec/**` write를 선언했으나 sole-update-path 소유자도 선보장 gate도 아닌 recipe negative fixture가 validator에서 fail-closed로 거부된다. runtime guard 차단은 structured failure + route id 참조를 낸다.
6. (SD-47) 두 세션 동시 spec-transaction fixture에서 후행 세션이 BLOCKED 후 대기→최신 재독→다음 버전 번호로 진입하고, 동일 `v{N}` snapshot 이중 생성이 0건이다. spec-touch 선언 없는 spec write는 structured failure다.

### 13.2.6 rollout boundary

v9 rollout boundary(§13.1.15)를 계승한다 — registry/compiler report-only 시작, capability feature flag, false positive 시 flag만 rollback. SD-44 문구 census와 SD-46 validator 항목은 Phase 1(registry/validator), SD-45 record 필드·worker 계약은 Phase 2(route compiler·transport) 범위에 흡수된다. SD-47은 core `OPERATIONS.md §5.8` 계약 개정이므로 core-first 순서를 따른다. source implementation은 후속 `autopilot-code` 작업이며 본 v10 transaction은 spec artifact만 변경한다.

## 13.3 v11 — nested stage-dispatch eligibility·registry·fallback (2026-07-15)

> 근거: `../../plans/2026-07-15_stage-dispatch-v10/_internal/codex-nested-dispatch-diagnosis.md`, `.dispatch/logs/stage-dispatch-v10.codex.jsonl`, cycle `_internal/jobs.log`, global `.dispatch/jobs.log`. v10 구현 conductor의 첫 code-plan에서 드러난 세 갭을 별도 spec cycle로 고정한다. 관측된 launch는 문서 초안의 5회가 아니라 **최초 1회 + 재시도 5회 = 총 6회**다.

### 13.3.1 SD-48 — nested child-spawn eligibility를 hard eligibility로 분리 (I1)

- **context-sensitive surface**: root/main에서의 `headless --check`와 conductor 안에서의 child spawn 가능성은 별도다. route evidence는 최소 `(parent_harness, parent_transport, parent_sandbox, child_harness, launch_authority)` tuple별 `supported|unsupported|unknown`, probe source/time, failure class를 기록한다. native subagent support도 registered headless support의 대리 증거가 아니다.
- **selection rule**: standard+ recipe가 depth-2 stage를 요구하면 main은 conductor 선택 전에 해당 tuple을 평가한다. `unsupported|unknown`은 “지원”으로 취급하지 않으며, 우선 (a) nested spawn 가능한 conductor 후보 선택 (b) 같은 route를 보존하는 eligible ancestor launch broker 사전 결합 (c) SD-50 fallback 사전 결합 순으로 route를 만든다. root headless PASS만으로 nested PASS를 합성하는 것을 금지한다.
- **launch authority와 logical depth 분리**: logical `depth=2,parent=<conductor>` ownership은 유지하되 OS child를 반드시 conductor process가 직접 spawn할 필요는 없다. conductor sandbox가 child network를 막으면 depth-0 main의 registered launch broker가 같은 route node/parent linkage로 stage를 시작할 수 있다. broker 사용은 route record에 미리 선언하고 ad-hoc 우회로 만들지 않는다.
- **현재 Codex evidence**: `parent_harness=codex,parent_transport=headless,parent_sandbox=workspace-write,child_harness=codex,launch_authority=conductor`는 2026-07-15 로컬 실측상 `unsupported(network-operation-not-permitted)`다. runtime/projection/sandbox 정책이 바뀌면 재probe하기 전까지 이 관측을 재사용하되 영구 vendor capability로 일반화하지 않는다.
- **official boundary**: 공식 Codex manual의 native `agents.max_depth`와 `codex exec` automation 지원은 서로 다른 surface다. manual은 `workspace-write` network가 기본 off이고 network policy가 spawned subprocess에도 적용된다고 설명하지만 nested `codex exec` 성공을 보장하지 않는다. 따라서 adapter는 공식 문서의 부재를 지원으로 추정하지 않고 로컬 checked evidence를 붙인다.

### 13.3.2 SD-49 — canonical global attempt registry (I2, 원인 확정 방향)

- **원인 판정**: sandbox가 global registry write를 거부한 뒤 우회한 것이 아니다. transcript는 최초 dry-run부터 여섯 start/wait/harvest 경로 모두 cycle `_internal/jobs.log`를 explicit `--jobs`로 지정한다. 전역 write attempt/permission error는 0건이고 global registry에는 depth-1 conductor row만 있다. 직접 원인은 **의도적 noncanonical `--jobs` 선택**이다.
- **SD-14b와 구분**: 이번 path는 linked-worktree artifact snapshot이 아니라 canonical artifact root 아래였고 parent/child wait·harvest도 같은 path를 봤다. 과거 `AGENT_HOME` fallback 불일치 재발이 아니라, explicit override가 Fleet authority를 우회할 수 있는 **registry authority 갭**이다.
- **global authority**: production registered model dispatch의 canonical registry는 depth-0에서 한 번 resolve한 `<agent-home>/.dispatch/jobs.log`이며 immutable `AGENT_DISPATCH_JOBS`로 모든 descendant와 launch broker에 전달한다. depth>0의 `--jobs`는 이 inherited canonical path와 같아야 한다. isolated fixture는 env와 argv를 함께 같은 임시 path로 바꿀 수 있지만 production child가 cycle-local path만 고르는 것은 fail-closed다.
- **attempt-first registration**: 실제 `--start` attempt마다 child spawn 전에 global row를 기록하고 stable `attempt_id`로 route id/node, parent, harness, launch authority, fallback ordinal을 묶는다. 즉시 runtime/network/auth/limit 실패도 같은 row를 `done,note=dead-<reason>`으로 닫아 Fleet가 실패 시도까지 본다. dry-run은 row를 만들지 않는다.
- **local mirror와 failure**: cycle-local registry는 선택적 audit mirror일 수 있으나 authoritative sink가 될 수 없다. global registry가 writable하지 않으면 child를 0개 유지한 채 `global-registry-unwritable` structured failure로 중단하며 local-only launch로 하강하지 않는다.
- **legacy reconciliation**: 기존 local-only row는 harvest가 `(route_id,route_node,parent,slug|attempt_id)`로 idempotent reconcile한다. 동일 attempt를 중복 생성하지 않고, 원래 timestamp/status/failure note를 보존하며 reconciliation 사실만 추가한다.

### 13.3.3 SD-50 — standard+ stage의 checked cross-harness fallback chain (I3)

standard+ stage launch의 fallback은 다음 순서로 고정한다. 각 hop은 동일 route node/write scope/completion gate를 유지하고 SD-49 global attempt row를 남긴다.

1. **same-harness headless** — SD-48 tuple이 `supported`일 때만 실행한다. 동일 failure class에 eligibility 증거 변화가 없으면 같은 hop을 반복하지 않는다.
2. **cross-harness headless** — SD-16 usage/role/runtime eligibility와 SD-48 launch tuple을 통과한 다른 harness를 선택한다. conductor sandbox가 직접 spawn할 수 없으면 prebound depth-0 launch broker가 `depth=2,parent=<conductor>`로 실행한다. parent sandbox 안에서 다른 CLI 이름만 바꾸는 것을 cross-harness 복원력으로 오인하지 않는다.
3. **native subagent** — 해당 runtime의 current native check와 logical depth/write/artifact contract가 모두 성립할 때만 사용한다. registered headless와 다른 surface이므로 Fleet visibility degradation과 ceremony 차이를 route evidence에 기록한다.
4. **inline fallback** — 앞 세 경로가 checked-ineligible 또는 실행 실패일 때만 허용한다. SD-34 enum(`runtime-unavailable` 또는 더 구체적인 기존 enum), 거부 후보·failure class·registry attempt ids·assurance 보완을 metrics/final report에 기록한다.

conductor는 same-harness 실패 후 cross-harness 평가를 건너뛰고 inline으로 내려갈 수 없다. 사용자/runtime 정책이 특정 harness나 native delegation을 금지한 경우 그 제한을 해당 hop의 checked-ineligible reason으로 기록하되, 한 surface의 제한을 다른 surface로 확장하지 않는다.

### 13.3.4 v11 acceptance criteria

1. root Codex headless PASS와 nested Codex-in-Codex FAIL을 동시에 주는 fixture에서 route가 두 surface를 구분하고 unsupported conductor-local spawn을 선택하지 않는다.
2. required depth-2 recipe에서 nested tuple이 `unknown`이면 지원으로 통과하지 않으며, eligible conductor 또는 prebound ancestor broker/cross-harness fallback이 없는 route는 compile 단계에서 fail-closed다.
3. observed Codex sandbox fixture에서 route는 동일 six-attempt retry를 만들지 않고, failure class 변화 없는 same-harness 재시도 0건과 다음 fallback hop 전이를 증명한다.
4. nested `--start`가 cycle-local `--jobs`를 제시해도 production fixture에서는 global registry가 authoritative다. 성공·network 즉사·auth/limit 즉사 각각이 spawn 전 global attempt row를 만들고 Fleet collector가 모두 읽는다.
5. global registry unwritable fixture는 child spawn 0건·local-only row 0건·`global-registry-unwritable` structured failure를 반환한다. legacy six local row reconciliation은 두 번 실행해도 global row가 정확히 6건이다.
6. same-harness headless 실패 + cross-harness eligible fixture는 inline 전에 cross-harness child를 실행하고, route id/node/write scope/completion gate/parent linkage가 보존된다. conductor-local network가 막힌 fixture는 depth-0 broker가 같은 logical depth-2 row를 시작한다.
7. cross-harness도 ineligible인 fixture는 native check 결과에 따라 native subagent로, 그것도 불가하면 inline enum+evidence로 내려간다. hop 생략·surface 제한의 무근거 확장·Fleet 가시성 overclaim은 각각 negative fixture로 거부한다.
8. Claude/Codex/OpenCode sibling adapter는 nested eligibility, global registry, fallback chain을 독립 fixture로 검증한다. 한 harness의 PASS를 다른 harness의 proxy로 쓰지 않으며 unsupported tuple은 정직하게 `unknown|unsupported`로 남긴다.

### 13.3.5 rollout boundary

- 본 v11 transaction은 **spec artifact와 I2 진단 보강만** 변경한다. source implementation, adapter projection, dispatch wrapper, preflight, test는 시작하지 않는다.
- 구현 선행조건은 진행 중인 `stage-dispatch-v10` cycle의 수확·main merge다. 그 branch/worktree가 `adapters/{claude,codex,opencode}/bin/dispatch-headless.py`와 Codex/OpenCode preflight를 편집 중이므로, v11 구현은 merge된 최신 main에서 **별도 autopilot-code cycle/branch/worktree**로 시작한다.
- 구현 시작 시 공식 Codex manual과 각 adapter local probe를 다시 확인한다. 2026-07-15 관측은 route evidence baseline이지 영구 runtime capability 선언이 아니다.

## 13.4 v12 — harness-neutral depth-0 launch broker (2026-07-15)

> 목표: runtime의 native recursion 가능 여부와 무관하게 logical depth-1 conductor와 logical depth-2 stage worker의 harness를 자유롭게 조합한다. **논리 소유권**(`depth=2,parent=<conductor>`)과 **OS launch authority**(depth-0 broker)를 분리하고, 모든 headless stage launch를 같은 broker protocol로 정규화한다.

### 13.4.1 SD-51 — depth-0 broker를 공통 launch authority로 표준화

- depth-0 main/orchestrator는 depth-1 conductor를 시작하기 전에 model이 아닌 deterministic broker sidecar를 준비하고 broker identity·endpoint를 route record와 conductor 환경에 결합한다. broker만 depth-2 target adapter process를 OS-level로 시작한다.
- conductor는 target harness가 자신과 같든 다르든 직접 `claude -p`, `codex exec`, OpenCode headless 또는 adapter wrapper를 실행하지 않는다. declarative broker request를 제출하고 같은 turn 안에서 ack→terminal 상태를 동기 대기·수확한다.
- logical `depth`, `parent`, route node, write scope, completion gate, owner와 worker role은 broker OS parentage와 독립이다. Fleet는 broker를 모델 worker로 세지 않고, 실제 target attempt row를 logical parent 아래 표시한다.
- runtime-native recursive spawn이나 conductor-local headless launch가 probe상 가능하더라도 portable 의미론의 전제가 아니다. 향후 직접 실행 최적화는 동일 request/state/registry 계약 뒤의 checked executor로만 허용하며, 기본 경로와 실패 의미를 바꾸지 않는다.

### 13.4.2 SD-52 — durable request·registry·lifecycle protocol

- request는 임의 shell/argv 전달이 아니라 versioned declarative envelope다. 최소 필드는 `request_id`, route id/hash/node, logical depth/parent, target harness, capability/mode/QA/intensity, portable/concrete model choice, worktree/canonical artifact root, write scope/completion gate, inherited global jobs path, fallback ordinal이다. broker는 adapter-owned allowlist와 schema를 검증하고 shell 없이 target wrapper를 구성한다.
- depth-0가 정한 broker root와 canonical jobs registry는 descendant가 바꿀 수 없다. conductor가 다른 endpoint·registry·worktree scope를 제시하면 target spawn 0건으로 fail-closed한다. request와 SD-49 `attempt_id`는 1:1로 연결되고 global row는 spawn 전에 기록된다.
- 상태는 `queued → claimed → launched|running → done|failed|cancelled`이며 terminal은 immutable하다. request publish와 state transition은 atomic write+lock으로 직렬화한다. broker identity는 PID+process start ticks+instance/fencing token+heartbeat/lease로 검증하고 stale broker나 이중 broker는 fail-closed 또는 fenced takeover만 허용한다.
- 동일 `request_id` 재제출은 기존 상태를 반환하며 새 target을 만들지 않는다. claim 뒤 broker crash는 global registry의 `attempt_id`와 exact PID/start ticks를 reconcile해 이미 launch된 target을 재실행하지 않는다. launch 전 claim만 남은 경우에만 lease 만료·fencing 뒤 재개한다.
- broker missing/dead, schema/route mismatch, timeout/cancel은 structured failure로 닫고 caller-local 실행으로 몰래 하강하지 않는다. conductor는 SD-14 same-turn wait 계약을 유지하며 detached completion promise를 남기지 않는다.

### 13.4.3 SD-53 — 4개 harness placement와 fallback 의미론 정규화

- 최소 호환 행렬은 `Claude→Claude`, `Claude→Codex`, `Codex→Claude`, `Codex→Codex`다. 네 조합 모두 동일 broker request/state machine을 사용하고 target adapter만 달라진다. parent harness와 child harness는 route compiler의 독립 축이며 OS process ancestry에 포함되지 않는다.
- SD-50의 후보 선택·순서·usage/role eligibility는 route compiler/conductor가 소유한다. broker는 선택된 한 target harness를 실행할 뿐 재라우팅하지 않는다. fallback hop마다 별도 request/attempt evidence를 만들고 동일 route node/write scope/completion gate를 보존한다.
- Claude native subagent, Codex native subagent, agent teams와 registered headless worker는 계속 별도 surface다. native fallback은 headless broker 후보가 exhausted/ineligible일 때만 SD-50 순서로 사용하며, native recursion 가정으로 broker readiness를 합성하지 않는다.
- OpenCode는 같은 envelope와 lifecycle을 소비할 수 있도록 protocol은 vendor-neutral로 두되, 본 v12 필수 placement matrix와 독립 acceptance는 Claude/Codex 4조합이다. OpenCode 미검증을 Claude/Codex 지원에 대한 proxy 또는 실패로 쓰지 않는다.

### 13.4.4 v12 acceptance criteria

1. 4개 placement fixture가 동일 broker endpoint를 사용해 성공하고, 각 target의 OS parent/launch authority는 conductor가 아닌 broker이며 global row의 logical `depth=2,parent=<conductor>`·route id/node·target harness는 정확하다.
2. conductor sandbox가 target CLI와 network operation을 직접 실행할 수 없는 fixture에서도 broker request는 성공한다. conductor-local wrapper 실행·subprocess spawn은 0건이다.
3. broker missing/dead/stale-heartbeat fixture는 target spawn 0건과 structured `broker-unavailable|broker-stale` failure를 반환하고 caller-local fallback으로 위장하지 않는다.
4. 동일 `request_id`를 동시·순차 재제출해도 `attempt_id`와 target process가 정확히 1개다. queue publish/claim/state file은 부분 JSON 없이 atomic하며 terminal 상태가 되돌아가지 않는다.
5. claim 직후와 target spawn 직후 broker crash fixture에서 fenced recovery가 registry/PID evidence를 reconcile하고 target 중복 launch 0건을 보장한다. 이미 시작된 attempt는 같은 identity로 wait/harvest한다.
6. 모든 실제 target start는 spawn 전에 canonical global registry row를 가지며 request id↔attempt id↔route node가 추적된다. inherited endpoint/jobs path 또는 worktree/artifact scope 변조는 spawn 0건으로 거부된다.
7. same-harness 실패 뒤 cross-harness fixture는 route layer가 다음 target을 선택해 별도 broker request를 제출한다. broker 자체 reroute 0건, fallback ordinal·failure class·보존 필드가 두 attempt에 모두 남는다.
8. conductor는 broker terminal 또는 bounded timeout/cancel까지 같은 turn에서 wait하고 harvest한다. turn 종료 뒤 background model completion을 약속하는 경로는 negative fixture로 거부된다.
9. direct recursive executor를 feature flag로 켜는 fixture가 추가될 경우에도 같은 envelope/schema/registry/lifecycle probe를 통과해야 한다. flag off 기본값에서는 네 조합의 결과·실패 enum이 runtime recursion 지원 여부에 따라 달라지지 않는다.

### 13.4.5 rollout boundary와 후속 관찰

- 구현은 v12 spec commit 뒤 최신 main에서 만든 별도 `stage-dispatch-v12-broker` worktree/cycle에서 수행한다. 우선 deterministic broker·client·fixture를 만들고, 다음으로 shared fallback helper와 3 adapter projection/preflight를 연결한 뒤 4조합 및 sibling 회귀를 검증한다.
- **O2는 본 v12에서 구현하지 않는다.** linked-worktree worker가 sandbox 밖 Git common-dir의 `index.lock`을 만들 수 없어 commit하지 못한 관찰이며, 후속 v13 후보로 `worker no-commit + prepared commit message/evidence → depth-0 main harvest/commit` 계약을 평가한다.
- **O3도 본 v12에서 구현하지 않는다.** dispatch 인프라 자기수정 중 route compiler 입력 digest가 바뀌어 completion이 stale-digest로 거부된 관찰이며, 후속 v13 후보로 evidence-bearing orchestrator override와 compile-time digest pin+drift record를 비교한다.

## 13.5 v13 — broker 동시성 분리·record-identity 결합 해제·completion 통과 증거 (2026-07-16)

> 근거: fleet v10 사이클 실측(`../../plans/2026-07-15_fleet-v10-process-view/final_report.md §5`, `_internal/carryover.md`) — ① 타 프로젝트 worker 1개가 broker 전역 락 아래 동기 실행되어 전 fabric dispatch를 약 12분 차단(대기 스레드 6, `dispatch-broker.py process_request`가 `request_guard`를 쥔 채 `subprocess.run` — 구조적 동시성 1). ② immutable route record가 mutable `broker_instance`를 고정해 broker rollover 후 해당 route의 ordinal-1 hop이 영구 불가 — fleet v10 conductor 자신이 plan 이후 ordinal-3 native-subagent(fleet_visibility=degraded)로 열화 수행. ③ `capability-route.py complete`가 쓰는 completion marker를 현행 파이프라인 어디서도 호출하지 않아 repo 전역 marker 0건 — gate "통과"의 on-disk 증거가 부재해 fleet가 정직 결손(`—`)으로 표시.
> 사용자 결정 (2026-07-16): 3건 모두 계약 확정 + 구현 착수 ("전부다 작업 해줘").

### 13.5.1 SD-54 — broker request 접수와 target 실행의 동시성 분리 (HOL blocking 해소)

- request 접수·schema/route 검증·dedup·claim·state transition은 **short critical section**으로 직렬화하되, target adapter process의 실행 생애는 어떤 전역 락도 쥐지 않는다. 서로 다른 request는 병렬로 launch·실행·terminal 전이된다.
- 동일 `request_id` 직렬화는 전역 뮤텍스가 아니라 per-request state(lease·status)로 보장한다: claimed/running 상태 재제출 = `broker-request-inflight` 거부, terminal 재제출 = 기존 상태 반환. SD-52 idempotency 의미는 불변.
- SD-52의 나머지 불변식(atomic transition, terminal immutability, PID/start-ticks+heartbeat/lease+fencing, spawn 전 canonical registry row)은 병렬 실행에서도 그대로 성립해야 한다. state file 갱신과 registry reconcile은 각자의 락/atomic write 범위로 보호하고, 실행 대기와는 분리한다.
- **동시성 상한은 broker가 소유하지 않는다** — 모델 워커 동시성·budget은 SD-40 governor가 계속 소유하며, broker는 OS launch authority만 담당한다. broker에 별도 cap을 넣어 governor와 이중 상한을 만들지 않는다.
- acceptance: ① 느린 target fixture(N초 sleep adapter) 실행 중 제출된 두 번째 request의 ack→terminal이 첫 target 생애와 독립적으로 완주한다. ② 동일 `request_id` 동시·순차 재제출은 여전히 attempt/target 정확히 1개(v12 AC4 유지). ③ claim 직후·spawn 직후 crash fixture의 fenced recovery(v12 AC5)가 병렬 상태에서도 중복 launch 0건.

### 13.5.2 SD-55 — immutable route record와 mutable broker identity의 결합 해제

- route record의 dispatch_evidence tuple은 **stable identity만** 고정한다: `broker_root`(+ `launch_authority=ancestor-broker`). `broker_instance`·PID·start ticks 같은 rollover마다 바뀌는 identity는 record에 넣지 않는다. 이 계약은 `broker_contract_version: 2`로 선언한다.
- hop 시점 instance 해석: client(stage-dispatch-fallback)는 request 제출 직전 record의 `broker_root`에 대해 `dispatch-broker.py status`(ping 검증 포함, 비생성 조회)를 실행해 **live instance**를 확보하고, envelope에는 그 시점의 live instance를 넣는다. broker 부재/사망이면 v12 계약대로 structured `broker-unavailable` fail-closed다 — 워커 컨텍스트는 `ensure`(생성)를 호출할 수 없고 broker 준비는 depth-0의 몫이므로, hop 해석은 조회만 수행한다(2026-07-16 구현 실측으로 문언 정정, v13 minor #1). broker의 envelope↔현재 instance 대조(SD-52)는 그대로다. 즉 identity 검증은 사라지지 않고 **record(불변)에서 hop(실시간)으로 이동**한다.
- 하위호환: `broker_contract_version: 1` record는 기존 검증 규칙(tuple에 instance 포함)과 기존 거동(rollover 시 fallback 열화)을 그대로 유지하며 소급 변환하지 않는다 — v1 record의 열화는 계약이 예비한 fallback의 정상 소비다. 신규 compile부터 v2를 생성한다.
- acceptance: ① broker rollover(restart) fixture에서 v2 record의 ordinal-1 hop이 새 instance로 성공하고 fallback 하강 0건, record hash는 rollover 전후 불변. ② v1 record fixture는 기존 verify/fallback 거동 그대로(회귀 0). ③ ensure가 broker를 못 세우는 fixture는 v12 계약대로 structured `broker-unavailable` fail-closed.

### 13.5.3 SD-56 — completion gate 통과 증거 marker 의무화

- **문제 축**: `completion_gate=`는 launch 시점 선언이라 시작 전·죽은 노드도 갖고, `status=done`은 fleet-kill도 포함해 성공 증거가 아니다. "통과"의 유일한 on-disk 증거는 `capability-route.py complete`가 쓰는 marker(route_id/route_hash/registry_digest/node_id/completion_gate/evidence sha256)인데 아무도 호출하지 않는다.
- **쓰기 의무**: conductor(또는 quick/inline의 capability owner)는 stage 노드의 산출물 계약 완결 판정(§14 의미 구간) 직후 `capability-route.py complete`를 호출해 marker를 남긴다. evidence = 그 스테이지의 계약상 종단 산출물(plan/plan.md, 최종 dev_log, test verdict, final_report.md 등). 판정 자체는 의미 판단으로 남되, 판정 **결과**는 marker로 결정론화한다.
- **canonical 위치**: `<agent-home>/.dispatch/completion/<route_id>/<node_id>.json` — jobs.log와 같은 canonical authority 규칙(SD-49)을 따르며 (route_id, node_id)만으로 외부 관찰자(fleet)가 결정론적으로 도출할 수 있어야 한다. 재수확(노드 재실행 후 재판정)은 이전 marker를 이력으로 보존하고 최신 marker가 authoritative다.
- **결정론 gate(강제 장치)**: route-file이 결합된 `--start`에서 dispatch wrapper는 해당 노드의 `depends_on` 전 노드 marker 존재를 검사하고, 부재 시 spawn 0건 + structured `completion-marker-missing` failure로 닫는다. 의무를 문서 vigilance로 남기지 않고 다음 노드 launch의 전제조건으로 규칙화한다 — 이것이 marker 0건 상태의 재발 방지 장치다. (기존 v1 record·record 없는 launch는 이 gate의 대상이 아니다 — 소급 강제 금지.)
- **소비 계약**: marker 존재 + route_id/route_hash 일치만 "통과"로 읽는다. marker 부재는 "실패"가 아니라 "무주장"이다(fleet의 정직 결손 원칙 유지). fleet 표시 연결은 별도 fleet spec cycle(F-28 재개 조건 충족)로 진행한다.
- acceptance: ① 성공 stage 수확 fixture에서 canonical path에 marker가 생기고 필드가 record와 일치. ② 후속 노드 `--start`가 선행 marker 부재 시 spawn 0건 + structured failure. ③ marker 부재를 실패로 읽는 소비자 0(negative fixture). ④ 재수확 fixture에서 이력 보존 + 최신 marker authoritative. ⑤ v1 record·record-미결합 launch는 gate 미적용(회귀 0).

### 13.5.4 rollout boundary

- 구현은 본 v13 spec commit 뒤 최신 main에서 별도 `stage-dispatch-v13` worktree/cycle로 수행한다: `utilities/dispatch-broker.py`(SD-54), `utilities/capability-route.py`+`utilities/stage-dispatch-fallback.py`(SD-55), wrapper 3종+`utilities/dispatch-node.py`+`skills/autopilot-code` 스테이지 문서(SD-56) + deterministic fixture.
- **live broker 롤오버 절차**: 구현 merge 후 기존 broker instance는 in-flight request가 0이 될 때를 기다려 shutdown→ensure로 교체한다. 교체 시점에 살아 있는 v1 record의 ordinal-1 열화는 SD-55 하위호환 계약이 흡수한다.
- O2(worker no-commit)·O3(digest pin)는 본 v13에 포함하지 않고 v14 후보로 유지한다. resource-runner canonical registry 경로(fleet F-28c 재개 조건)는 O4/v14 후보로 등재한다.

## 13.6 v14 — 운영 병목 해소 1차: 중첩 도달성·진행 감시·capacity failover·registry 위생 (2026-07-16)

> 근거: 2026-07-16 운영 진단(입력 목록 v14 항목) + 코드 원인 실측. 사용자 확정: 진단 7건 중 dispatch 도메인 4건(1·2·3·7)을 본 spec에 등재하고 개선 순서 1(도달성)부터 구현 착수("작업 개시"). 항목 4·5는 core 규약(CONVENTIONS/OPERATIONS), 항목 6은 별도 spec/도구 소관으로 명시 라우팅 — 본 spec 범위 밖.

### 13.6.1 SD-57 — broker 생존 판정의 증거 위계와 sandbox-독립 도달성

- broker 생존 판정은 단일 `/proc` 게이트가 아니라 **증거 위계**다: (1) exact PID+start-ticks `/proc` 일치 = 최강 양성(live); ticks **불일치 관측**(PID 가시·다른 프로세스) = 확정 사망(fail-closed 유지). (2) `/proc` 항목 부재는 사망 확정이 아니라 **unverifiable** — `broker.lock` 비블로킹 flock 프로브로 판별한다(획득 성공 = 보유 프로세스 없음 = 사망 / 거부 = 프로세스 생존; 파일 기반이라 PID 네임스페이스와 무관). (3) 생존 프로세스의 프로토콜 생존은 fenced socket ping(instance_id 에코 대조)과 fresh heartbeat로 확인한다. 어떤 경로도 양성 증거 없이 live를 합성하지 않는다.
- `status`/`request`/`stop`/`ensure` 전 클라이언트 경로가 같은 위계를 사용한다. `ensure`/`stop`의 교체·종료 대기는 `/proc` 관찰 대신 meta `state=stopped` 또는 lock 해제 관찰로 판정한다. 검증 불가 PID로의 signal 전송과 타 프로세스 보유 lock의 unlink는 계속 금지(기존 불변식).
- request 전송은 socket 우선에 **durable file-spool fallback**을 더한다: client가 `requests/inbox/`에 envelope를 원자 publish(tmp+rename, 대상 instance 명시)하고 기존 `req-*.json` state 파일을 poll로 수확한다. broker serve loop는 inbox를 결정론 주기로 소비해 동일 `process_request`(per-request lease·idempotency·fencing 그대로)로 처리한다. spool은 transport일 뿐 authority 변화가 아니다 — depth-0 준비 의무, 워커 `ensure` 금지, missing/stale broker fail-closed(SD-51~52) 불변. socket이 차단된 sandbox에서 liveness는 flock 프로브 + fresh heartbeat(전부 파일 기반)로 판정한다.
- acceptance: ① proc-invisible fixture(살아있는 broker, exact PID 비가시)에서 `status`/`request`/`stop` 성공 + `ensure` 중복 spawn 0. ② 사망 fixture(lock 해제 + 메타 잔존)는 기존대로 `broker-unavailable` fail-closed, 교체는 depth-0 `ensure`만. ③ socket-connect 거부 fixture에서 spool 경유 request가 성공하고 envelope/idempotency/terminal 의미가 socket 경로와 동일. ④ 실전 smoke: root에서 ensure된 broker를 depth-1 owner가 같은 jobs metadata로 `status` 조회하고 code-plan smoke job을 dispatch·수확. ⑤ 기존 v12/v13 fixture 전부 회귀 0.

### 13.6.2 SD-58 — worker 진행 감시: 발화는 liveness가 아니다 (구현 후속 사이클)

- liveness의 유일한 증거는 결정론 신호다 — 파일 write(mtime/새 산출물), tool-call/registry state 전이, 단계 heartbeat. "이제 구현을 시작합니다" 류 progress 발화는 liveness로 인정하지 않는다.
- 스테이지 worker는 analysis/file-write/test 단계 전이를 heartbeat로 남기고, conductor 감시는 실행 단계 진입 선언 후 결정론 deadline 내 첫 write/tool-call 부재 시 자동 경고, 두 번 연속 무진행 시 자동 interrupt + SD-50 fallback을 수행한다.
- O5 흡수: native-subagent fallback hop은 child 생성 실증(row/pid/산출물)이 없으면 그 hop을 실패로 닫는다 — "checked 폴백이 준비 상태를 합성하지 않는다"(SD-50/53)의 native surface 확장.
- acceptance(계약 수준): 무진행 fixture에서 경고→interrupt→fallback 자동 진행. 발화-만 progress는 ALIVE 판정 불가. 단계 heartbeat는 F-25 분류기와 단일 소스로 노출(이중 분류기 금지).

### 13.6.3 SD-59 — capacity failure class의 checked model failover (구현 후속 사이클)

- "Selected model is at capacity" 류 capacity 오류는 별도 failure class로 감지해 row를 `dead-capacity`로 즉시 마감하고(SD-15 확장), 동일 prompt/artifact ownership·route node를 유지한 채 **허용된 다른 모델 또는 명시 inheritance profile로 정확히 1회 자동 재시도**한다. 재실패 시 SD-50 순서로 하강(inline 포함).
- 직전 capacity 모델은 해당 route node에서 cooldown — 동일 failure class 무변경 재시도 금지(SD-50)의 model 축 적용. 모델 선택 주체는 orchestrator/route layer(SD-22 priority) 유지, wrapper는 감지·마감·증거 기록만.
- acceptance(계약 수준): capacity 즉사 fixture에서 대체 모델 1회 재시도→성공 경로와 재실패→하강 경로가 각각 route/attempt 증거로 남고, 동일 모델 재선택 0.

### 13.6.4 SD-60 — dispatch registry 자동 reconciliation과 현재-작업 필터 (구현 후속 사이클)

- 죽은 exact PID identity·병합 완료 branch·오래된(terminal-미갱신) job을 결정론적으로 구분해 자동 reconcile(`done,note=cleanup-merged|dead-*`)하는 preflight 경로를 제공한다. SD-29(안전 조건 통과 시만)·SD-49(attempt identity reconcile) 불변식을 재사용하며 별도 분류기를 만들지 않는다 — Fleet F-25 분류기와 단일 소스.
- 현재 session/route/job만 필터한 상태 출력을 preflight/liveness 표면에 제공해, 무관 open row가 liveness/cleanup 판단을 오염시키지 않게 한다.
- acceptance(계약 수준): 혼합 fixture(활성 job + 죽은 PID + 병합 branch + stale row)에서 필터 뷰가 현재 작업만 표시하고, reconcile은 안전 게이트를 전부 통과한 row만 마감.

### 13.6.5 rollout boundary

- 본 v14 spec commit 뒤: SD-57 = `broker-nested-reachability` 사이클(`utilities/dispatch-broker.py`+`utilities/stage-dispatch-fallback.py`+Claude adapter 미러+deterministic fixture) 즉시 착수(사용자 개선 순서 1). SD-58~60 = 후속 사이클(사용자 순서 2·3·7). SD-58은 `plans/2026-07-16_fleet-depth2-retry-liveness`의 registry attempt identity 보존(F-25 연계)과 결합해 진행하고, 그 플랜의 broker 복구 항목(fenced socket recovery)은 SD-57 사이클이 흡수한다.
- live broker 롤오버는 v13 절차 재사용: 구현 merge 후 in-flight 0 시점에 shutdown→ensure.

## 13.7 v15 — broker retirement와 direct nested headless (2026-07-16)

> v12~v14의 broker 계약은 특정 sandbox 실패를 모든 runtime placement에 일반화해 만든 우회였다. 실제 운영에서 broker 자체가 PID namespace, socket reachability, heartbeat, fencing, request lease, rollover, retry reconciliation이라는 별도 분산 상태를 만들었고 Fleet의 한 logical stage를 여러 상태면으로 증식시켰다. v15부터 broker는 신규 topology의 launch authority가 아니다.

### 13.7.1 SD-61 — 신규 route의 launch authority는 conductor direct

- 신규 route는 `dispatch_contract_version: 3`을 기록하고 headless 후보의 `launch_authority=conductor`만 허용한다. route compile은 broker tuple·root·instance를 요구하거나 기록하지 않는다.
- checked fallback은 `same-harness direct headless → cross-harness direct headless → native subagent → inline`이다. 첫 두 hop은 route node의 target adapter wrapper를 **호출자 프로세스에서 one-shot으로 실행**하며 daemon, socket, heartbeat, request state, lease, fencing을 만들지 않는다.
- wrapper는 기존 canonical registry·model governor·worktree·completion marker·early-death 계약을 그대로 소유한다. logical `depth=2,parent=<conductor>`는 OS ancestry와 별개라는 기존 의미를 유지하되, 실제 launch authority도 더 이상 가장하지 않는다.
- `dispatch_contract_version: 1|2` route는 hash verify와 historical Fleet read만 지원한다. 신규 compile 금지, broker auto-ensure/rollover 금지, 실행 재개 시 v3 route를 다시 compile한다.

### 13.7.2 SD-62 — Codex recursive headless profile

- native subagent와 nested `codex exec`는 별도 surface다. v15의 Codex depth-1 standard+ owner는 filesystem sandbox를 `workspace-write`로 유지하면서 `sandbox_workspace_write.network_access=true`를 명시한 **network-enabled conductor profile**로 시작한다. 이 권한은 child flag가 parent sandbox를 탈출하는 것이 아니라 depth-0 launcher가 parent 실행 경계를 사전에 선택하는 것이다.
- nested `codex exec`는 parent sandbox 안에서 자신의 runtime state를 쓸 수 있어야 한다. launcher는 owner worktree 아래 전용 `CODEX_HOME`을 만들고 runtime projection을 설치한 뒤, 현재 home의 `auth.json`과 `config.toml`은 복사·수정하지 않고 read-only source를 가리키는 symlink로만 제공한다. credential/session/cache를 worker-local home으로 복제하거나 shared runtime-owned 파일을 변경하는 것은 금지한다.
- network-enabled 표면은 owner/conductor에만 적용한다. depth-2 stage/review/support worker에는 자동 전파하지 않으며, 그 worker가 depth-3을 열 수 없다는 기존 gate를 유지한다. wrapper는 `AGENT_NESTED_HEADLESS_NETWORK=1`을 owner 환경에 기록하고 route eligibility probe는 이 checked evidence를 사용한다.
- Claude Code는 기존 direct `claude -p` 분사 경로를 유지한다. cross-harness direct는 child CLI·auth·parent network가 모두 checked일 때만 supported다. unknown/unsupported는 child 0으로 다음 hop에 내려간다.

### 13.7.3 SD-63 — 하나의 logical stage, 하나의 attempt identity

- direct chain은 `(route_id, route_node, slug, parent, target_harness, fallback_ordinal)`에서 안정적인 `attempt_id`를 도출해 dry-run/register/start가 같은 identity를 공유하게 한다. broker request id는 생성·기록하지 않는다.
- wrapper의 registry claim은 lock 아래 `attempt_id` exact match로 check+append를 원자화한다. 동일 attempt가 이미 claim되었으면 open row와 child를 추가하지 않고 기존 identity를 반환한다.
- Fleet current view는 exact `attempt_id + pid + process start`를 강한 identity로 사용한다. 종료된 retry는 default body에서 접고 `--all`/alert history로만 남긴다. cwd transcript mtime은 process identity가 없는 legacy row의 tier-3 fallback일 뿐이다.

### 13.7.4 migration과 제거 경계

- v15 구현에서 broker 신규 생성 경로(`ensure_launch_broker`, wrapper env projection, route broker requirement, dispatch-chain broker submit)를 제거한다. preflight의 broker lifecycle command와 `dispatch-broker.py`는 v1/v2 artifact 진단·명시적 stop을 위한 한 release compatibility surface로만 남기고 `retired=1`을 표시한다.
- live broker는 신규 request를 받지 않는다. in-flight 0을 확인한 뒤 stop하며 request state는 audit history로 보존한다. 삭제 작업이 새 daemon/supervisor/spool을 만들면 계약 위반이다.
- SD-57의 broker reachability/spool 구현은 취소한다. SD-58 progress watchdog, SD-59 capacity failover, SD-60 registry hygiene 중 broker-independent 부분은 direct wrapper/Fleet 후속으로 유지한다.

### 13.7.5 acceptance

1. broker process/socket/meta가 전혀 없는 fixture에서 v3 same-harness와 cross-harness direct dry-run/register/start가 wrapper를 정확히 한 번 호출한다.
2. Codex owner command는 standard+ depth-1일 때만 network-enabled marker/config를 가지며 depth-2에는 없다.
3. 동일 v3 start를 동시에 두 번 호출해 registry attempt와 child launch가 하나뿐이다.
4. v3 route JSON과 jobs row에 `broker_root`, `broker_instance`, `broker_request_id`, `ancestor-broker`가 없다.
5. v1/v2 route verify와 Fleet fixture parsing은 유지되지만 신규 compile과 wrapper start는 broker를 생성하지 않는다.
6. 기존 route/dispatch/wrapper/Fleet/adaptation suite에서 broker-only 기대를 제외한 회귀 0, live smoke에서 Fleet depth-2 row 중복 0.
### 13.7.6 v15 minor #1 — 운영 실측 3건: conductor 고아 파이프라인·route 증거 전달·source_commit pin (2026-07-16)

> 근거: `plans/2026-07-16_spec-gate-multi-spec` 사이클 실측 — ① r1 conductor(claude -p·opus)가 one-shot 폴링 지침에도 배경 대기 후 턴 종료로 사망, plan 워커만 고아 생존(depth-0 수동 복구·재분사) ② dispatch-node.py가 record의 eligibility 증거를 wrapper로 전달하지 않아 `nested-eligibility-evidence-missing` fail-closed ③ r2 conductor는 SD-14 완주했으나 worker-route-guard의 `head == source_commit` 정확 일치가 execute의 계약상 커밋과 모순 — test/report 분사가 구조적으로 거부(BLOCKED), same/cross-harness hop 동일 사유 실패.

- **SD-64 — conductor 고아 파이프라인의 결정론 감지·재개**: ① 감지 = conductor attempt identity 사망(exact pid+start) ∧ route 미완(completion marker 부재 노드 잔존) ∧ open/live 자식 또는 미기동 후속 노드 — F-25/SD-58과 단일 분류 소스로 판정하고, SD-60 reconcile 확장으로 고아 행 자동 표기(`note=dead-parent-orphaned`) + depth-0 표면(liveness/preflight/Fleet alert) 노출. ② 재개 = replacement conductor가 route record + completion marker에서 재개(SD-56이 재개 지점을 결정론화), marker 있는 노드 재실행 금지. 재개 여부·시점은 depth-0 의미 판단으로 남긴다(자동 재분사 금지). ③ SD-14(b) in-session Stop-hook 게이트는 `-p` 미발화 실측대로 held 유지 — 결정론 장치는 사후(post-exit) 감지로 이동한다. 지침 강화(r2)로 1회 완주했으나 지침만으로 재발 방지를 주장하지 않는다.
- **SD-65 — post-execute 노드의 source_commit 계보 검증**: worker-route-guard `route-source-commit-mismatch`의 정확 일치 검사를 노드 위상으로 분리한다 — 첫 mutation 노드(execute) 이전 노드는 현행 정확 일치 유지, 이후 노드는 `HEAD == source_commit ∨ HEAD가 source_commit의 후손(같은 route cwd, first-parent 계보)`을 허용한다. 발산·무관 HEAD·merge/rebase 진행 상태는 기존대로 fail-closed. route 위조·재컴파일 우회는 계속 금지 — 가드가 검증할 불변식은 "route가 결합한 작업 계보 위에 있는가"이지 "컴파일 순간에 멈춰 있는가"가 아니다.
- **v15 구현 흡수(신규 SD 없음)**: dispatch-node.py(node materializer)가 record `dispatch_evidence`의 checked tuple을 wrapper 인자로 결정론 전달한다 — 소비자가 증거를 수동 재전달하는 현행은 SD-45 manifest-consumer 취지 위반. SD-61 direct 전환 구현에서 함께 처리.
- acceptance(계약 수준): ① 고아 fixture(conductor 사망 + marker 미완 + 자식 잔존)에서 자동 표기·depth-0 표면 노출·재개 지점(marker 경계) 보고. ② execute 커밋 후손 HEAD에서 test/report 분사 통과, 발산 HEAD fail-closed 유지. ③ dispatch-node 경유 분사가 추가 인자 없이 eligibility 검증 통과.


## 13.8 v16 — 사용자 하네스 기본값 config (2026-07-16)

> 근거: 2026-07-16 크로스 하네스 depth-2 검증 사이클(사용자 세션)에서 확정된 사용자 결정. "cross 하네스가 자유로워도 결국 모델들은 정해진 방식대로만 분사한다 — 사용자의 기본값 config가 필요하다. config는 모델이 아니라 하네스만 고른다. 모델은 자의적 판단으로 더 적절한 하네스/모델을 고를 수 있다." + 2026-07-16 웹 취합 리서치(계획/코드베이스 적응=Claude 우위(침식 중), scoped 원샷·지시 준수·토큰 효율=Codex 우위, 검증은 maker와 다른 하네스가 커뮤니티 표준, OpenCode는 품질 평판이 모델 종속·headless ask-권한 데드락 이력).

### 13.8.1 SD-66 — `profiles/dispatch-defaults.yaml`: capability×stage×depth → 기본 하네스

- **표면**: `profiles/dispatch-defaults.yaml` 단일 파일. 값 어휘 = `claude | codex | opencode | diverse`(maker와 다른 하네스) | **미지정**(오케스트레이터 재량 = 현행 동작). depth-1 owner는 단일값이 아니라 **허용집합 `[claude, codex]`** — 메인 세션(depth-0)이 어느 하네스든 섞어 쓰고 owner도 자유 선택한다(2026-07-15 v12 결정의 config 실현). 값은 하네스만 — concrete model/effort 금지(SD-22 family/role 계약 불변).
- **적용 자리**: SD-22 라우팅 우선순위의 **3단계 stage affinity를 사용자-선언 데이터로 외부화**한다. 1단계 explicit choice와 2단계 hard eligibility(SD-48 tuple·usage limit)는 이 config에 항상 우선한다. soft default — 오케스트레이터는 더 적절한 하네스를 사유 기록 후 선택할 수 있다(hard pin 금지 유지).
- **전 capability 커버**: autopilot-code만이 아니라 `capabilities/topologies.json`의 모든 entry capability stage 노드를 열거해 키를 제공하며, 근거가 약한 칸은 미지정으로 남긴다. 초기값(2026-07 스냅샷, 모델 세대 교체 시 재평가): autopilot-code `exec=codex`(플랜 확정 후 scoped 스테이지 = Codex 강점 구간 + Claude 한도 분산), `test·review=diverse`, `report=claude`, `plan=미지정`(근거 상충 — Claude 다수설 우위 vs 사용자 부하 분산 선호).
- **OpenCode relief-only 정책**: 전역 `opencode: relief-only` — 기본 라우팅 테이블에 등장하지 않고, 양쪽 하네스 동시 limit/장애 시 저위험 벌크 작업의 릴리프 밸브(운용 비중 목표 1~2%)로만 선택한다. headless는 ask-권한 데드락 이력으로 자동 승인 구성이 전제다.
- **소비자 배선(1단계)**: `utilities/dispatch-route.sh`의 하드코드 stage affinity를 이 파일 로딩으로 치환(SD-23 read-only selector 유지), `core/OPERATIONS.md §5.10`에 컨덕터 소비 규칙 명문화. **route hash 봉인 경로(topology compile) 배선은 2단계로 유보** — record 불변식과 registry digest 파급을 분리 평가한다.
- **SD-OPEN-3 해소**: "limit 회피 > 특성 적합 > 분산" 보수 정책은 유지하되, '특성 적합'의 내용이 하드코드 heuristic이 아니라 이 파일의 사용자 선언이 된다. `HARNESS_CAPACITY_BIAS`는 별도 축(용량 편향)으로 존속.

## 13.9 v17 — mutation 노드 재시도 계보·dispatch-defaults 봉인 배선 (2026-07-19)

> 근거: ① 운영 실측 2건(입력 목록 v17 계기 항 — 두 standard 사이클 연속으로 execute 재시도가 구조적으로 차단되고 fix-forward가 depth-0로 승격) ② 사용자 승인(2026-07-19) — 재시도 계보 결정 등재 + SD-66 2단계 유보 해제.

### 13.9.1 SD-67 — mutation 노드 재시도의 first-parent 계보 검증

- **대안 비교**: (a) 재시도 전용 재개 경계 신설 — marker류 신규 상태면 + conductor 재-pin 권한이 SD-45 재선택 금지와 긴장. (b) SD-65가 확립한 계보 원칙("route가 결합한 작업 계보 위에 있는가")을 결정론 재시도 증거로 게이트해 mutation 노드로 확장 — 기존 가드·registry 표면 재사용, 신규 상태면 0. **(b) 채택**. route record는 이미 `resume_retry_boundaries`로 재시도 가능 노드를 선언하고 있어(autopilot-code는 4 스테이지 전부) 별도 선언 표면도 불필요하다.
- **계약**: worker-route-guard는 mutation 노드(worktree-mutating write_scope 보유)의 `HEAD ≠ source_commit`을 다음 세 조건 전부일 때만 허용한다 — ① 해당 노드가 route record `resume_retry_boundaries`에 선언됨 ② 결정론 재시도 증거: 바인딩된 전역 attempt registry에 동일 `route_id`+`route_node`의 선행 attempt row 존재(현재 launch의 attempt identity 제외) ③ HEAD가 route cwd에서 `source_commit`의 first-parent 후손.
- **fail-closed 불변**: registry 미설정·판독 불가·선행 row 부재 → 현행 정확 일치 요구. 발산·무관 HEAD·merge/rebase 진행 상태 차단 유지. route 재컴파일로 pin을 옮기는 우회 금지 유지(SD-45 재선택 금지).
- **첫 attempt 정확 일치 유지 이유**: conductor의 사전 변이(pre-mutation)로 스테이지 규율이 무너지는 것을 막고, 1차 diff 귀속(`source_commit..HEAD` = execute 산출)을 보존한다.
- **소비 규칙**: execute FAIL·부분 완료 후 conductor의 in-place 재분사를 허용한다. `git reset --hard` 복원은 계속 금지 — dev-pipeline Step 4의 "safety-commit restore" 탈출구 서술은 이 계보 완화로 대체하고, `core/OPERATIONS.md §5.10` 컨덕터 지침을 현행화한다.
- acceptance: ① 선행 execute attempt row + execute 커밋의 first-parent 후손 HEAD 픽스처에서 execute 재분사 통과 ② 선행 row 없는 첫 launch는 후손 HEAD여도 fail-closed(정확 일치 유지) ③ 발산 HEAD·registry 부재 fail-closed ④ SD-65 post-mutation 계보 동작·기존 스위트 회귀 0.

### 13.9.2 SD-68 — SD-66 2단계: dispatch-defaults의 route record 봉인 배선

- **계약**: `capability-route.py compile`이 검증된 dispatch-defaults config를 로드해 ① 각 depth-2 stage 노드에 `harness_affinity` 스탬프(config 어휘 그대로 `claude|codex|opencode|diverse`, 미지정 칸·config 부재 = `unspecified`) ② record 상단 `dispatch_defaults_digest`(canonical config sha256, 부재 시 null)를 기록한다. `route_hash`가 두 필드를 봉인한다 — 컴파일 시점 스냅샷이며, 사후 config 변경은 기존 route를 무효화하지 않는다(verify는 hash 봉인만 검증, config 재로드 금지). `registry_digest`(topology registry pin)와는 의도적으로 분리한다 — config 변경이 topology pin을 오염시키지 않는다.
- **우선순위 불변(SD-22)**: explicit choice > hard eligibility(SD-48 tuple·usage limit) > record affinity(config 스냅샷) > heuristic/bias. soft default 유지 — conductor는 사유 기록 후 이탈 가능, 차단 장치 신설 금지.
- **소비**: dispatch-node가 노드 `harness_affinity`를 registry row(`harness_affinity=`)에 기록해 실제 `harness=`와의 이탈을 행 단위로 감사 가능하게 한다. `opencode` affinity는 relief-only 전역 정책 하에서만 실효(1단계 selector와 동일 의미). 1단계 selector 배선(dispatch-route.sh)은 record 없는 depth-1·수동 경로의 소비자로 불변 존속. 손상 config는 compile fail-loud, 부재는 전부 `unspecified`.
- acceptance: ① compile 산출 route의 depth-2 노드 전부에 유효 어휘 `harness_affinity` 존재 ② config 값 변경 → 신규 compile의 `route_hash` 변화(봉인 입증) ③ 스탬프된 기존 route는 config 사후 변경에도 verify 통과 ④ dispatch-node 경유 row에 `harness_affinity` 기록 ⑤ explicit `--adapter`가 affinity와 달라도 launch 통과(soft) + 기존 스위트 회귀 0.

## 13.10 v18 — conductor 생존·Codex mutation 경계·marker↔row 결합 (2026-07-19)

> 근거: 위 v18 운영 실측. 지침만으로 같은 Claude one-shot 사망이 세 번 재현됐고, linked-worktree Codex mutation의 commit 불가와 marker가 있어도 open attempt row가 남는 registry 위생 결손이 같은 실전 사이클에서 확인됐다.

### 13.10.1 SD-69 — Codex linked-worktree mutation은 no-commit worker 계약

- **기각**: `git rev-parse --git-common-dir` 결과를 Codex `--add-dir`에 추가해 commit을 허용하는 안. 현재 Codex workspace-write는 `.git`과 resolved gitdir을 writable root 안에서도 보호하므로 이 안은 공식 runtime 계약과 모순이다. 보호 우회나 `danger-full-access` 승격도 표준 stage 계약으로 채택하지 않는다.
- **채택**: linked worktree의 Codex mutation stage는 source diff·tests·evidence를 만들되 Git commit은 하지 않는 `no-commit worker`다. route의 `source_commit`은 stage 종료까지 유지하고, PASS 산출물을 수확한 뒤 권한 있는 depth-0 또는 Claude 경계가 검증과 diff 귀속을 확인해 commit한다. dirty worktree를 후속 test/report가 읽는 것은 허용하되 commit을 했다는 허위 주장은 금지한다. runtime이 향후 protected gitdir write를 명시 지원할 때만 별도 checked capability로 재평가한다.
- **artifact write**: route-bound Codex worker에는 canonical artifact root 외에 primary checkout의 정확한 `$AGENT_HOME/.spec-grounding` 디렉터리만 좁은 writable root로 추가한다(사전 생성). 전체 agent home이나 Git metadata는 열지 않는다. 이로써 spec-read marker와 canonical evidence가 worker sandbox 밖 primary checkout에 영속한다.
- acceptance: ① disposable linked-worktree Codex fixture가 source edit와 `.spec-grounding` marker를 영속하고 no-commit 상태를 정직하게 보고 ② `.git/worktrees/...` write 허용·보호 우회 없음 ③ PASS 뒤 권한 경계 commit과 통합 검증 가능 ④ test/report가 dirty worktree를 소비해도 route hash/source pin 위조 없음.

### 13.10.2 SD-70 — completion marker와 exact attempt row의 결정론 결합

- `capability-route.py complete`는 canonical jobs path와 **현재 exact attempt id**를 입력받는다. completion marker를 원자적으로 쓴 직후 registry lock 아래 그 attempt 하나만 `done`으로 마감하고 `note=completed-marker`와 marker evidence를 기록한다. 같은 route/node의 이전 BLOCKED attempt나 새 live retry를 breadth-close하지 않는다.
- marker·row close는 idempotent다. 이미 동일 marker와 done row가 있으면 성공한다. marker는 썼지만 registry가 없거나 쓰기 실패하면 marker를 보존하고 구조화된 nonzero를 반환한다. `dispatch-registry.py reconcile`은 marker의 exact attempt evidence로 이 stale row만 수리한다.
- acceptance: ① 동일 node의 prior BLOCKED/current PASS/live retry 3행 fixture에서 current exact row만 닫힘 ② duplicate complete 성공 ③ marker-write 뒤 jobs unwritable failure가 marker를 훼손하지 않고 reconcile로 수리 ④ attempt 누락·불일치 fail-closed.

### 13.10.3 SD-71 — one-shot conductor hardening과 고아 자동 표면화

- **launch policy**: Claude wrapper는 현재 runtime에서 실제 비동기 wait/scheduling 도구 이름을 probe·열거한 경우에만 `--disallowedTools`로 차단한다. Bash나 동기 `dispatch-wait`를 포괄 차단하지 않는다. 이름을 확인할 수 없으면 unsupported evidence를 남기고 프롬프트 계약만 적용하되 deterministic support를 주장하지 않는다.
- **Stop 재검증**: Claude Code 2.1.215의 `-p`에서 Stop hook 발화·차단·stdout 무오염을 disposable fixture로 재검증한다. 세 조건이 모두 성립할 때만 conductor gate를 등록하며, 아니면 held를 유지한다.
- **post-exit reconcile**: SD-64를 구현한다. exact conductor attempt 사망 ∧ 미완 completion node ∧ open/live 자식 또는 미기동 후속이 성립하면 conductor row를 `dead-parent-orphaned`로 자동 마감하고 liveness/preflight/Fleet에 route·resume boundary를 경고한다. 자동 replacement/restart는 금지하고 depth-0 의미 판단으로 남긴다.
- **보조층**: standard conductor prompt 최상단에 “비동기 Monitor/wakeup 금지, 현재 턴에서 동기 `dispatch-wait` 반복”을 표준 문구로 둔다. 이는 runtime policy/post-exit reconcile의 대체가 아니다.
- acceptance: ① 현재 CLI tool-policy probe와 `-p` Stop fixture 결과를 증거로 기록 ② 고아 fixture 자동 표기·세 표면 노출·자동 재분사 0 ③ 정상 conductor/live child/완료 marker route 오탐 0 ④ 프롬프트에 동기 대기 계약 존재.

## 13.11 v19 — transient PID namespace lifecycle (2026-07-20)

> 근거: Codex depth-1 tool-call PID namespace에서 detached depth-2 worker가
> wrapper 반환과 동시에 2~4 JSONL event만 남기고 세 차례 사망했다. exit-77
> guard는 silent death를 차단했지만 checked Codex→Codex 및 Codex→Claude
> stage path를 완주시키지 못했다.

### 13.11.1 SD-72 — namespace-safe automatic lifecycle selection

- `dispatch-chain`은 실제 launcher scope에서 PID namespace를 판정한다.
  transient namespace이면 Codex/Claude child wrapper에
  `launch_lifecycle=foreground-scoped`를 자동 선택하고, wrapper call을 child
  terminal까지 유지한다. namespace 밖에서는 기존 `detached` launch를 보존한다.
- `AGENT_DISPATCH_ALLOW_NAMESPACED_SPAWN=1`은 namespace가 tool-call보다 오래
  산다는 명시적 checked assertion이며 이 경우 detached를 유지한다.
- foreground-scoped wrapper는 child process group에 SIGINT/SIGTERM을 전달하고,
  bounded timeout이면 group을 TERM→KILL 순으로 종료한다. nonzero exit, signal,
  timeout은 exact attempt row 하나만 typed `dead-*`로 마감한다. exit 0 자체는
  성공 증거가 아니다. exact completion marker가 있으면 성공으로 마감하고,
  exact attempt log의 최종 `turn.completed` handoff가 `BLOCKED`/`FAIL`이면 marker가
  없어도 typed failure로 즉시 마감한다. bwrap `.codex` bind-mount 실패는
  `dead-sandbox-init`이다. 둘 다 없을 때만 completion-marker harvest race를 위해
  open 상태를 보존한다.
- checked Codex `headless/workspace-write` parent 안의 foreground Codex child는
  unsupported nested mount setup을 피하려고 inner runtime sandbox만
  `danger-full-access`로 선택한다. outer workspace-write가 권한 경계로 유지되며
  wrapper output/attempt row에 effective runtime sandbox를 기록한다.
- dispatch tuple의 canonical transport는 `headless|interactive`이며
  `codex-exec-headless` 같은 adapter runtime-surface label은 route evidence가 아니다.
  inner sandbox가 활성인 worktree의 `.codex`가 파일 또는 symlink이면 wrapper는
  registry claim과 child spawn 전에 구조화 실패한다.
- standard+ Codex owner의 outer sandbox에는 기존 harness `.core-grounding`과
  Claude `session-env` scratch directory만 추가로 writable하게 투영한다. 따라서
  adapter write gate와 Codex→Claude Bash 초기화가 동작하되 두 runtime home의
  나머지 영역이나 depth-2 network 권한은 넓어지지 않는다.
- wrapper는 자신의 exact slug를 child 환경에 내보내고 `dispatch-chain`은 이를
  parent 기본값으로 사용한다. explicit parent 불일치는 등록 전에 거부한다.
  Fleet는 과거·malformed unmatched depth-2 row도 orphan으로 표시해 숨기지 않는다.
- wrapper machine output과 attempt row는 stable vocabulary
  `launch_lifecycle ∈ {detached,foreground-scoped}`를 기록한다. same-harness와
  cross-harness가 같은 selector를 소비하며 native subagent는 대체 경로가 아니다.
- registry attempt identity, heartbeat/watchdog, capacity failover,
  completion-marker binding, fallback order는 lifecycle 선택과 직교하며 불변이다.
  exact attempt의 terminal observation은 과거 heartbeat/PID보다 우선하고,
  canonical attempt identity가 있는 행은 cwd-wide transcript mtime으로 ALIVE를
  합성하지 않는다. inline fallback은 새 route를 만들지 않고 같은
  route/node/completion gate를 이어 쓴다.

**acceptance**: ① host/remounted-proc namespace fixture에서 lifecycle 판정이
결정론적이다 ② namespace 밖과 long-lived override는 detached를 유지한다
③ Codex/Claude wrapper foreground success가 child exit까지 반환하지 않고 output/row에
foreground-scoped를 기록한다 ④ timeout/signal/nonzero가 exact row만 typed closure한다
⑤ Codex depth-1→Codex depth-2 및 Codex depth-1→Claude depth-2 live attempt가 artifact,
typed handoff, exact marker, terminal row까지 완주한다 ⑥ parent mismatch가 등록 전
거부되고 unmatched depth-2 row가 Fleet orphan으로 표시된다 ⑦ 기존 dispatch/route/
liveness/Fleet/projection/boundary suite가 회귀 없이 통과한다.
⑧ `.codex` tracked-file 및 첫 command 전 bwrap 실패 fixture에서 child 0 또는
exact `dead-sandbox-init`, 최종 open row 0, liveness ALIVE 0이며 same-route fallback과
Fleet current view가 stale refs attempt를 현재 단계로 채택하지 않는다.

## 13.12 v20 — quick registered-headless invariant와 surface terminology (2026-07-20)

> 근거: 승인된 v20 결정, `documents/2026-07-20_depth1-surface-terminology-audit.md`,
> registered research shard와 independent review verdict. 이 절은 SD-19의 quick
> fallback을 명시적으로 뒤집되 `direct`와 `standard+`의 의미는 바꾸지 않는다.

### 13.12.1 SD-73 — quick는 registered-headless-only (SD-19 superseded)

- `effective_intensity=quick` route는 capability-owner route node를 **정확히 하나**
  가진다. node는 `dispatch_depth=1`, route는 `owner_dispatch_depth=1`,
  `max_dispatch_depth=1`이며 child node와 `dispatch_depth=2` fan-out이 없다.
- omitted transport는 compiler가 registered wrapper transport `headless`로 유도한다.
  explicit empty, `interactive`, `native-subagent`, `inline-fallback`, unknown/arbitrary
  값은 route emission·registry claim·child spawn 전에 실패한다. quick recipe의
  허용 execution surface는 `registered-headless` 하나뿐이며 machine wrapper
  transport 값은 기존 `headless`를 유지한다.
- checked registered-headless eligibility가 compile 시점에 없으면 정확한 error enum
  `quick-headless-unavailable`로 끝난다. route file, registry row, child process는 모두
  생성하지 않는다. compiler는 intensity, transport, execution location을 제자리에서
  바꾸거나 direct/native/inline으로 하강하지 않는다.
- quick cardinality는 **one route node + at most one live attempt/session**이다. SD-59의
  직렬 capacity/retry 규칙은 폐기하지 않는다. 허용된 재시도도 전부 registered
  headless이고 각자 canonical terminal attempt row를 가지며 동시에 둘 이상 live일
  수 없다. eligible registered-headless attempts가 소진되면
  `quick-registered-headless-exhausted`로 terminal failure한다. quick의 native-subagent와
  inline attempt count는 항상 0이다.
- 회복은 owner가 새 route를 다른 intensity로 **명시 재승인·재컴파일**하는 경계다.
  compile/runtime이 기존 quick route를 자동 변형하지 않는다.
- Fleet는 quick node당 current/open attempt row를 정확히 하나 이하로 표시하고 과거
  terminal retry rows는 보존한다. quick child row, native/inline degradation row는
  계약 위반이다.

**보존 경계**: `direct`는 main-inline(`dispatch_depth=0`)이고 registry worker row가
없다. `standard+`는 기존 capability recipe와 checked same-harness headless →
cross-harness headless → native-subagent → inline fallback 순서(SD-50/61/72)를
그대로 보존한다. 이 fallback은 quick에 적용되지 않는다.

### 13.12.2 SD-74 — portable dispatch topology와 attempt surface의 별도 namespace

- `dispatch_depth`는 portable route ownership/topology의 논리 수준이다. runtime
  transport, process ancestry, runtime-native nesting, registry 가입 여부와 독립이다.
  신규 schema/prose/projection은 bare `depth`, `max_depth`, `owner_depth` 대신
  `dispatch_depth`, `max_dispatch_depth`, `owner_dispatch_depth`를 사용한다.
- `dispatch_depth=0`은 user-facing main ownership, `dispatch_depth=1`은 capability-owner
  node, `dispatch_depth=2`는 bounded stage/support node다. 이 값은 route node의
  논리 위치이지 실제 attempt가 registered worker라는 주장이 아니다.
- attempt는 별도 `execution_surface`와 `registered_worker` evidence를 가진다. repo-owned
  registration contract로 launch된 `registered-headless` attempt만
  `registered_worker=true`다. direct inline과 standard+ native/inline fallback attempt는
  자기 route node의 `dispatch_depth` metadata를 유지하되 registered-worker status를
  얻지 않는다.
- route record, registry row, completion marker, liveness와 Fleet는 node
  `dispatch_depth`와 attempt `execution_surface`/registration evidence를 분리해 기록한다.
  fallback attempt가 logical depth를 지우거나 registered dispatch라고 오표기하면
  fail-closed한다.
- Codex `agents.max_depth`는 Codex native-subagent nesting 설정일 뿐이다. registered
  headless `max_dispatch_depth`를 검증·제한·광고하지 않으며 native-subagent probe는
  headless eligibility evidence가 될 수 없다.
- current normative prose, 신규 schema와 generated portable/adapter projection에는
  ambiguous bare depth field가 0개여야 한다. v1~v19 역사 구간과 version-tagged legacy
  record만 예외이며 legacy reader는 source schema version을 표시하고 v20 qualified
  recompilation 전 resume/re-emit을 거부한다.

### 13.12.3 SD-75 — transport, execution surface, fallback hop, runtime agent 용어

세 namespace는 서로 대입하지 않는다.

| Namespace | Closed vocabulary / meaning |
|---|---|
| registered wrapper `transport` | `headless`(non-interactive registered wrapper), `interactive`(명시적으로 허용한 non-quick wrapper 자리). `detached-process`는 execution surface가 아니라 route가 명시한 resource-job lifecycle에서만 유효한 historical/별도 값이다. |
| attempt `execution_surface` | `registered-headless`, `codex-native-subagent`, `claude-subagent`, `claude-agent-team-teammate`, `inline`. |
| `fallback_hop` | `same-harness-headless`, `cross-harness-headless`, `native-subagent`, `inline`; recipe가 허용한 intensity에서만 평가한다. |

compiler는 먼저 각 namespace의 global closed vocabulary를 검증하고 그 다음 recipe
allowlist를 적용한다. unknown string은 모든 intensity에서 실패한다. quick는
`execution_surface=registered-headless`와 wrapper `transport=headless`만 허용한다.

| Runtime surface | Normative meaning |
|---|---|
| **Codex native subagent** | Codex native agent child thread/session. `agents.max_depth` 같은 Codex-native 설정을 따르며 registered headless worker가 아니고 headless eligibility evidence를 충족하지 않는다. |
| **Claude subagent** | 한 Claude session 안에서 caller에게 결과를 돌려주는 Claude runtime-native child. registered headless worker가 아니다. |
| **Claude agent-team teammate session** | agent team의 peer communication에 참여하는 별도 full Claude Code session. Claude subagent가 아니며 team membership만으로 registered headless가 되지 않는다. |
| **registered headless worker session** | repo-owned wrapper를 통해 immutable route/node/attempt, canonical registry, liveness와 completion gate에 결합된 harness-neutral worker session. |

`runtime-native subagent`라는 cross-runtime 범주는 Codex native subagent와 Claude
subagent만 포함한다. Claude agent-team teammate를 포함하지 않는다. teammate가
registered wrapper를 호출한 경우에도 team membership과 그 wrapper child attempt의
registered-headless status는 별도 속성이다.

### 13.12.4 v20 acceptance / implementation handoff

1. every-capability quick default compile = one node, qualified depth fields, headless only;
   quick native/inline/interactive/empty/arbitrary negative fixtures는 route/row/spawn 0.
2. checked headless ineligibility는 `quick-headless-unavailable`; serial registered-headless
   exhaustion은 `quick-registered-headless-exhausted`; 자동 intensity mutation 0.
3. direct inline fixtures와 standard+ full fallback-order fixtures는 결과 불변이다.
4. quick는 one current/open attempt 이하, retry terminal history 보존, native/inline
   attempts 0, child node/row 0이다.
5. 신규 route/topology/registry/completion/Fleet schema와 generated projections에
   qualified depth + 분리된 execution-surface evidence가 있고 ambiguous bare fields 0.
6. Codex `agents.max_depth` probe 변화가 headless `max_dispatch_depth` 또는 eligibility를
   바꾸지 않는다.
7. terminology conformance는 Codex native subagent, Claude subagent, Claude agent-team
   teammate session, registered headless worker session을 서로 바꾸어 부르는 문구를
   거부한다.
8. legacy records는 version-tagged read-only이며 v20 recompilation 전 resume/re-emit 0.
9. Claude/Codex/OpenCode sibling compiler/projection이 동일 portable invariant를 독립
   검증한다. unsupported headless는 다른 surface로 대체하지 않고 정직하게 실패한다.
10. multi-capability composition, co-primary route, cross-capability DAG/envelope, source
    implementation, concrete model choice, user runtime config 변경은 본 v20 범위 밖이다.

## 14. 의미↔규칙 경계 체크 (DESIGN_PRINCIPLES §0.7)

- **규칙 구간(코드로 강제)**: depth ≤ 2(wrapper 게이트)·jobs.log row 형식·스테이지-워커 write 클래스·lock 범위·model role 명시 — 전부 결정론 가드/wrapper(§2.4). "산출물 기반 소통"의 완결성은 파일 존재로 결정론적 감사. **v2 추가**: SD-14(b) Stop hook(open 자식 row = 결정론적 차단 조건)·SD-14(c) dispatch-wait(대기 판단을 코드로)·SD-14(a) depth_note(계약 전달의 결정론화). **v6 추가**: quick depth-2 금지, quick jobs.log child-row 부재, mutation quick isolated worktree 는 결정론 gate 대상. **v7 추가**: hard eligibility 기반 후보 제거·adapter exact-ID probe·reason trace 필드·helper read-only·Fleet env child-hidden/metadata-exact 분류는 결정론 테스트 대상. **v8 추가**: canonical path 해석·worker-local artifact write 차단·cleanup eligibility·registry 직렬화는 모두 deterministic fail-closed 규칙이다. **v10 추가**: route record hash/scope 검증·tracked gate 증거 4종 필드 존재 검사·guard↔write_scope validator 항목·spec-transaction lock 시퀀스와 버전 경합 대기 규칙은 전부 결정론 검사 대상이다. **v11 추가**: nested eligibility tuple/status, immutable global registry path, attempt-first row identity, no-change retry 금지, fallback hop 순서·broker parent linkage는 결정론 validator/fixture 대상이다. **v12 추가**: broker endpoint/identity·request schema/idempotency·atomic state transition·fencing/lease·spawn 전 registry·4조합 logical parent 보존은 결정론 protocol/fixture 대상이다. **v13 추가**: per-request lease 직렬화·전역 락 비보유 실행·record v2 필드 규칙(stable identity만)·hop 시점 ensure 해석·completion marker 존재/필드/경로 검사·후속 노드 launch의 선행 marker gate는 전부 결정론 검사 대상이다. **v14 추가**: 생존증거 위계(exact-proc/flock 프로브/fenced ping+heartbeat) 판정 순서·spool publish/consume 원자성과 idempotency·발화-비인정 liveness 신호 집합·capacity failure class 감지와 모델 cooldown·registry reconcile 안전 게이트와 현재-작업 필터는 전부 결정론 검사 대상이다.
- **v15 규칙 전환**: v3 direct-only candidate 검증·stable attempt derivation·registry claim check+append·owner-only network marker·broker field 부재가 새 결정론 gate다. v12~v14의 broker reachability/spool 규칙은 historical이며 신규 route에 적용하지 않는다.
- **v16 추가**: dispatch-defaults 스키마 검증(어휘·capability/stage 키 유효성·모델 금지)·selector의 config 로딩·우선순위 적용 순서(explicit > eligibility > config affinity)는 결정론 검사 대상이다. 어느 칸에 어떤 기본값을 적을지, 미지정 칸에서 오케스트레이터가 어느 하네스를 고를지, soft default 이탈 사유의 타당성은 의미 판단 구간으로 남긴다.
- **v17 추가**: mutation 노드 재시도 계보 판정의 세 입력(route record `resume_retry_boundaries` 선언·바인딩된 전역 registry의 선행 attempt row·first-parent 계보)과 registry 부재 시 정확 일치 회귀, 그리고 `harness_affinity` 어휘 검증·`dispatch_defaults_digest` 봉인·registry row 기록은 결정론 검사 대상이다. 재시도를 할지·언제 할지의 판단과 record affinity 이탈 사유의 타당성은 conductor 의미 구간으로 남는다.
- **v18 추가**: exact attempt marker↔row 마감·marker 기반 reconcile, Codex linked-worktree no-commit 분류와 좁은 `.spec-grounding` writable root, verified Claude async-tool deny 목록, `dead-parent-orphaned` 사후 분류·표면화는 결정론 검사 대상이다. marker가 나타내는 stage 통과의 타당성, 고아 route를 실제 재개할지, no-commit diff를 최종 commit할지는 각각 conductor/depth-0 의미 판단으로 남는다.
- **v20 추가**: quick `registered-headless` 단일 surface allowlist, namespace별 closed vocabulary, exact compile/runtime failure enum, one-node/at-most-one-live-attempt cardinality, qualified dispatch-depth fields, node topology↔attempt surface 분리, four-surface terminology, legacy read-only migration은 전부 compiler/schema/conformance fixture로 강제한다. SD-19 quick fallback과 bare current terminology는 superseded다. direct/standard+ 보존과 multi-capability composition 비추가는 회귀 fixture 대상이다.
- **의미 판단 구간(사람/LLM)**: (1) 마이크로-스테이지 inline 경계 임계 — 계측 후 판정(SD-OPEN-1). (2) 스테이지 실패 시 재분사 vs 이어쓰기 판단 — conductor 의 부분 산출물 해석. (3) 산출물 계약이 "완전한가"의 판정 — 스테이지가 대화 없이 완주 가능한지. **v2 추가**: (4) SD-11 을 deny 가 아니라 reminder 로 시작 — hook 이 intensity(direct/quick 정당 fallback)를 결정론적으로 알 수 없어, 규칙화 불가 구간을 deny 로 억지 규칙화하지 않음(경계 존중). deny 상향은 계측 후. (5) SD-14(b) 피드백도 "대기 강제"가 아니라 liveness 진단→행동 분기 지시 — 죽은 스테이지 해석은 의미 판단으로 남김. **v6 추가**: headless 실패 시 native subagent 로 충분한지, 또는 inline fallback 으로 낮출지의 fallback reason 작성은 runtime 상태 해석이므로 의미 판단으로 남긴다. **v7 추가**: stage affinity와 family diversity의 품질 판단은 의미 구간이지만, 그 적용 순서와 후보 탈락 사유는 helper가 구조화한다. **v10 추가**: "산출물을 추적할 가치가 있는가"(tracking)와 "분사할 실익이 있는가"(promotion/separability)는 각각 의미 판단으로 남되, 두 판단을 하나로 동일시하지 않는 것이 SD-44의 축 분리다 — record는 판단 결과와 근거 신호만 구조화한다. **v11 추가**: eligible 후보가 여러 개일 때 role affinity·family diversity로 어느 cross-harness를 고를지와 새로운 failure class의 의미 해석은 판단 구간이지만, 지원 여부·hop 순서·row 기록은 규칙 구간이다. **v13 추가**: "스테이지 산출물이 계약상 완전한가"의 통과 판정은 conductor의 의미 판단으로 남긴다 — SD-56은 그 판단을 대체하지 않고 판단 결과를 marker로 결정론화하며, marker 부재를 실패로 해석하지 않는 것도 의미 구간의 존중이다. **v14 추가**: 무진행 worker에 대한 최종 interrupt vs 계속 대기, 그리고 재분사 시 이어쓰기/재시작 선택은 conductor 의미 판단으로 남긴다 — SD-58은 경고·차단의 발동 조건과 인정 가능한 liveness 신호 집합만 결정론화한다. capacity failover에서 "어느 대체 모델인가"의 품질 판단도 SD-22 affinity 의미 구간이며, SD-59는 재시도 횟수·cooldown·증거 기록만 규칙화한다.
- **충돌**: 없음 — 반전의 핵심 우려(현행 "상태 재발굴·연속성 상실")를 §0.5 계약 완결성 의무 + §8 inline 경계로 규칙화해 흡수했다. 우려를 사람 vigilance 로 남기지 않고 "산출물이 상태를 완전히 담는가"라는 검증 가능한 규칙으로 전환한 것이 이 경계 존중. per-stage cost 는 추측으로 규칙화하지 않고 계측(SD-OPEN-1)으로 미룬 것도 동일.
