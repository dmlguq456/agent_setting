# stage-dispatch — Spec Pipeline Summary

- **Date**: 2026-07-10
- **Mode**: library + cli (autopilot 파이프 디스패치 토폴로지 개정 인프라)
- **Status**: spec v10 (tracked×dispatch 축 분리 — SD-44~47 spec-only) · v9 구현 완료(26497cd0), v10 구현은 capability-routing-topology plan Phase 1~2 + core §5.8 개정으로 이월
- **Placement**: 독립 컴포넌트 `spec/stage-dispatch/` — 기존 `spec/prd.md`(Unified Memory System)·`spec/harness-layer-sync/`·`spec/dispatch-profiles/`·`spec/agent-fleet-dashboard/` 무수정.

## 배경

사용자 결정(2026-07-10): "스킬 단위의 처리가 분사해서 할 것을 기본 지침으로. 어차피 산출물 기반 소통." → `standard+` 에서 각 sub-skill 스테이지를 별개 headless 세션으로 분사. 사용자 결정(2026-07-13): `direct` 는 depth-0 inline 유지, `quick` 은 단일 depth-1 one-shot capability worker 로 이동, `standard+` 는 기존 depth-1 conductor -> 순차 depth-2 stage-worker topology 유지. v7에서는 standard+ conductor를 high-reasoning/deep orchestration 기본으로 고정하고, planning 계열은 GPT family via Codex + deep maker affinity(비-hard-pin), plan review는 다른 family를 선호하도록 정했다. Codex 공식 manual 근거는 subagent가 main-thread context pollution을 줄이지만 token 비용이 늘고 parallel write-heavy workflow는 충돌·조정비용 주의가 필요하다는 점이다. OpenAI Models의 현재 권장은 GPT-5.6 Sol(`gpt-5.6-sol`)이지만 API alias와 Codex ChatGPT runtime 허용 ID는 같다고 가정하지 않으며 adapter exact-ID probe를 요구한다.

v8은 2026-07-14 사용자 확정사항인 "agent 산출물은 task worktree에 넣지 않는다"를 구현 계약으로 승격한다. linked worktree의 tracked `.agent_reports` snapshot은 write target이 아니며, 모든 worker는 main checkout의 canonical artifact root를 사용한다. 정리는 runtime 종료 이벤트가 아니라 main/orchestrator가 merge·통합 검증·push를 증명한 직후 실행하는 fail-closed state machine이다.

v9은 2026-07-15 사용자 결정을 고정한다. substantive tracked work의 depth-0 main은 orchestration/integration만 수행하고, direct는 atomic inline, quick은 depth-1 one-shot/no-depth2, standard+는 capability별 recipe다. intensity, execution topology, worker kind, transport를 분리하고 `capabilities/topologies.json` + validator + immutable route record를 machine SoT로 정한다. spec/refine/note/ship의 single-writer transaction을 보존하며 detached jobs, global spawn governor, hash-bound smoke, single-manifest report completion, absolute cwd, spec-nudge structured-token matching, on-demand/lightweight sibling parity를 같은 acceptance contract에 묶었다.

## Process Log
| Step | Action | Result | Notes |
|---|---|---|---|
| 입력 Read | 사용자 결정 + research 3종(summary §4-(8)·gsd·06_impl) + 현행 계약 실측(OPERATIONS §5.10·§5.8·CONVENTIONS §1·§2·WORKFLOW §1.1·§5·DESIGN_PRINCIPLES §8·autopilot-code refs+sub-skills·dispatch-headless.py·3어댑터 §0(C)) | — | 모든 결정 근거를 사용자 결정·research 카드(§/줄)·운영 실증으로 인라인 소급 |
| 현행 실측 | 스테이지 산출물 파일 계약 census(plan/plan.md·checklist·dev_logs·test_logs·final_report) | — | 스테이지 인터페이스가 **이미 파일** — 분사 전제 성립(§2.1) |
| 현행 실측 | context-and-guards.md:51 "스테이지 헤드리스 분리 = worst of both, 금지" 발견 | — | 본 spec 이 **반전하는 정확한 조항** — §2.2·§9-7 |
| 현행 실측 | dispatch-headless.py depth=2/parent/worker_role/게이트 census | — | wrapper 가 **이미 스테이지 분사 골격 지원** → 재작성 불요(§2.4·SD-9) |
| spec | PRD 작성 (lean) | `prd.md` v1 | SD-1~9 채택 + SD-OPEN-1 open(inline 임계 pilot 계측). 영향 표면 14곳. 구현 2-phase |
| v7 update | root/component PRD full read + current v6↔`_internal/versions/v6/prd.md` byte compare + official model currentness 확인 | `prd.md` v7 | v6 snapshot cmp=0, 재생성 안 함. SD-21~24 및 pipeline state/summary만 갱신. |
| v8 update | memory full-body + existing reports/spec + current code + official Codex/Claude/OpenCode runtime surface 대조 | `prd.md` v8 | v7 snapshot. SD-25~30: canonical artifact routing, local-write deny, guarded cleanup. |
| v9 update | current v8 PRD/state/summary + capability-routing-topology plan/checklist/metrics/plan-check + current core/capability/mode contracts read | `prd.md` v9 | v8 snapshot once. SD-31~43 and 10 acceptance groups; no source edits. Codex root/core read-marker persistence was unavailable under worker sandbox, so instruction-only fallback used. |
| v9 implementation | topology registry/compiler, route-bound dispatch/completion, governor/resource lifecycle, smoke/report gates, cwd/nudge fixes, sibling projections | source commit `26497cd0` | portable guard 357/357, generated projections, routing, adaptation, context and focused unit suites passed. |
| v10 update | tracked-dispatch-conflict-diagnosis.md + plan.md + current v9 PRD 대조, D1 옵션 2개 사용자 제시 → (a) 확정 | `prd.md` v10 | v9 snapshot cmp=0. SD-44~47 + acceptance 6항. spec artifact only — 소스 무변. |

## 채택 결정 (locked)
- **SD-1~2 (토폴로지·인터페이스)**: depth-1 owner = 얇은 conductor(verdict/게이트만), 스테이지 = depth-2 headless 세션. 인터페이스 = 산출물 파일만, 대화 컨텍스트 전달 금지(산출물 기반 소통). 근거 = 사용자 결정 + research §4-(8) + DESIGN_PRINCIPLES §8 "결과 흐름 file 통해".
- **SD-3 (관제)**: 스테이지 세션 jobs.log 등록(depth=2,parent,worker_role,owner) → fleet 스테이지 row. stealth-death 가드 conductor 책임. 운영 실증 ①② 해소.
- **SD-4 (depth-2 write 개정)**: read-only 기본을 스테이지-워커 클래스별 write 소유로 재정의(plan/execute소스/test/report). depth 3+ 금지 유지.
- **SD-5~6 (모델·가드레일)**: model role conductor 명시(§5.10 ⑦). 동시상한5=Σ(conductor+활성스테이지)·마이크로 inline·실패=스테이지만 재분사·lock=report의 pipeline_summary만.
- **SD-7 (영향 표면)**: 14곳(core·bootstrap 3어댑터·SKILL·wrapper·fleet·drill) 현행문구→개정방향 표. 문구 편집은 core-first 별도.
- **SD-8 / SD-18 (적용 범위)**: standard+ stage-dispatch 기본, direct depth-0 inline 유지, quick depth-1 one-shot capability worker 로 승격(depth-2 금지).
- **SD-9 (wrapper)**: 재작성 불요. stage-dispatch helper 신설은 pilot 후 판정.
- **SD-21 (conductor tier)**: standard+ depth-1 conductor는 `orchestrator` + high-reasoning/deep orchestration 기본. fast orchestration은 mechanical-only.
- **SD-22 (route policy)**: explicit > hard eligibility/tool/runtime/account/limit > stage affinity > maker-checker family diversity > capacity/cost/latency. planning 계열은 deep maker + GPT/Codex affinity(비-hard-pin), plan review는 다른 family 선호. core는 family/role, adapter는 runtime-probed exact model/reasoning 소유.
- **SD-23 (helper)**: read-only `route-dispatch` 계약. Claude+Codex부터 지원하고 OpenCode는 probe 계약 확정 전 honest unknown. 실제 dispatch/registry/file mutation은 하지 않음.
- **SD-24 (Fleet acceptance)**: env-marked Codex headless child-hidden, non-code fuzzy `plans`/거짓 `spec:test` 0건, 정상 code stage 표시 유지.
- **SD-25~27 (artifact ownership)**: worker worktree는 source-only. explicit env 또는 Git primary worktree의 canonical artifact root를 사용하고, dispatch 3종이 최소 외부-write 권한과 함께 전달하며 worker-local artifact 쓰기는 차단한다.
- **SD-28~30 (cleanup ownership)**: cleanup은 dry-run 기본의 fail-closed state machine이다. merge·integrated verification·push·clean·inactive·unlocked를 모두 증명한 main/orchestrator만 apply하며 branch를 보존한다. runtime lifecycle hook은 destructive trigger가 아니다.
- **SD-31~35 (routing semantics)**: main orchestration-only 경계, atomic direct, one-shot quick, capability-specific standard+, four independent axes, `capabilities/topologies.json`, immutable route record, bounded-work promotion signals.
- **SD-36~38 (capability/parity ownership)**: apply/code/design/draft/lab setup+eval/note/refine/research/ship/spec mapping. transactional single writer 유지. portable meaning은 core/capabilities, runtime mechanics는 각 sibling adapter가 독립 소유·검증.
- **SD-39~43 (operability/completion/lightweight)**: detached run identity+reattach, atomic global spawn governor, mandatory hash-bound smoke, one report manifest, absolute cwd/spec-nudge matching, topology on-demand+strict footprint budget.
- **SD-44~47 (tracked×dispatch orthogonality, v10)**: Tracking 다섯째 독립 축(tracked=산출물 계약만, 분사=promotion/separability 신호, quick 경계 현행 유지 — 사용자 (a)), worker manifest-consumer 계약(재라우팅 금지 + tracked gate 증거 4종 record 운반 + bootstrap 축소), guard↔write_scope 정합성 validator(fail-closed + runtime structured failure), 공유 tracked 표면 병렬 계약(spec-transaction lock 원자 시퀀스 + 버전 경합 대기 규칙).

## 미결 (open — pilot 계측)
- **SD-OPEN-1**: 마이크로-스테이지 inline 의 손익 임계(어느 스테이지 크기부터 분사가 이득). research 가 per-stage dispatch cost 를 수치화하지 않음 → 추측 금지, Phase 1 pilot 토큰/시간 계측으로 확정.

## 반전의 정당성 (현행 금지 조항 대응)
현행 `context-and-guards.md:51` 은 스테이지 분사를 "상태 재발굴 + 연속성 상실 = worst of both"로 금지. 본 spec 은 이를 §0.5 계약 완결성 의무(산출물이 상태를 완전히 담으면 재발굴=파일로드·연속성=파일매체) + §8 마이크로-스테이지 inline 경계로 규칙화해 흡수. research §4-(8)이 "fresh-context+file-state가 context rot 방지 지배 관용구"임을 확증해 반전을 근거화.

## Next
운영 관찰에서 promotion signal, route fallback, governor start budget, capability별 DAG의 false-positive/false-negative를 수집한다. report-only rollout과 adapter별 runtime transport pilot을 거쳐 enforcement 승격 여부를 별도 판단한다. 자동 drill은 실행하지 않는다.

## Version History
- v10 (2026-07-15): tracked×dispatch 축 분리 — autopilot-spec update, v9 snapshot = `_internal/versions/v9/prd.md` (cmp=0 확인). 입력 = `plans/2026-07-15_capability-routing-topology/_internal/tracked-dispatch-conflict-diagnosis.md`(main+Codex 교차 진단 통합).
  - **SD-44 (진단 D1, 사용자 확정)**: Tracking을 SD-32 네 축에 더한 다섯째 독립 축으로 — tracked는 산출물 계약(필요·순서·소유·검증)만 결정하고 분사는 promotion(SD-35)/separability(SD-17) 신호가 결정. tracked→escalation 결합 문구(`WORKFLOW.md:165`·`OPERATIONS.md:109` 류) 제거. **quick 경계는 옵션 2개 제시 후 사용자 선택 (a) = 현행 유지** — 애매하면 quick depth-1(메인 컨텍스트 보호 우선, SD-18 재확정), Codex inline 권고 기각.
  - **SD-45 (진단 D2+F3)**: worker manifest-consumer 계약 — worker는 라우팅 재선택 금지, route record hash 검증+배정 node scope 실행+증거 반환만. tracked gate 증거 4종(spec-read·drift verdict·tracked/untracked mode·artifact-guard 전제)을 record 필수 필드로 운반(세션 지역 read marker의 분사-투영 실패 실측 대응). bootstrap `status/prompt-signal/mode/route` 재실행은 record 검증+안전 확인 전용으로 축소, 3어댑터 동형.
  - **SD-46 (진단 D3)**: guard↔topology 정합성 validator — `spec/**` write 선언 node는 sole-update-path 소유자 또는 conductor 선보장 gate 필요(fail-closed). runtime guard 차단은 structured failure + route record 참조.
  - **SD-47 (진단 D4)**: 공유 tracked 표면 병렬 계약 — spec 3-file transaction + `versions/v{N}` 체인은 §5.8 lock 보유 중 원자 시퀀스로만. 경합 = 대기 후 최신 재독·다음 버전 진입(동일 v{N} 이중 snapshot 차단). spec-touch route 선언 + §5.9 가드 선실행.
  - 진단 F6/F7은 v9 SD-36~38이 기존 답(추가 결정 없음), F2 일부·F3은 SD-45에 흡수. acceptance 6항 등재. spec artifact only — 소스 무변.
- v9 (2026-07-15): capability-specific routing topology. v8 snapshot = `_internal/versions/v8/prd.md`. SD-31~43: main/direct/quick/standard+ boundary, four axes, topology registry+validator+route record, 10 capability/11 mode mappings, transactional single writer, runtime boundary, detached/global governor/smoke/report/cwd/nudge/lightweight sibling parity. Source files unchanged.
- v8 (2026-07-14): source-only worker worktree + canonical artifact root + guarded automatic cleanup. v7 snapshot = `_internal/versions/v7/prd.md`.
- v1 (2026-07-10): 초기 PRD. 사용자 결정(스테이지 분사 기본화) + research cross-platform-agent-frameworks §4-(8) + 운영 실증 3종 종합. 2026-07-06 depth 재설계 기본값 반전 명시 기록.
- v2 (2026-07-10): Phase 2 결정 등재 — autopilot-spec update, v1 snapshot = `_internal/versions/v1/prd.md`.
  - **SD-10** (최우선, 사용자 확인 발견): Phase 1 의 dev-pipeline.md 개정이 반쪽 — 앞머리 계약 블록만 있고 Step 1~7 본문은 in-session "Invoke Skill" 잔존(이중 신호) + 비한정 e.g. escape hatch. 본문 dispatch-first 재작성 + fallback 조건 한정형(direct/quick·headless 불가 런타임) + SKILL.md Stage Graph dispatch 표기.
  - **SD-11**: conductor 의 code-* 직접 Skill 호출 reminder hook — soft 로 시작(deny 는 hook 이 intensity 를 몰라 false-positive 위험 → drill·계측 후 재판단).
  - **SD-12** (사용자 요구): 스테이지-워커별 dispatch-profiles 최소 fragment + conductor `--profile` 기본 배선 — full bootstrap 대신 스테이지 계약만. 토큰/시간 계측을 SD-OPEN-1 데이터와 병행 수집.
  - **SD-13** (pilot 부수발견 ①): conductor 의 스테이지 분사 전 spec 전제 선보장 — spec-less repo 에서 스테이지가 artifact-guard 에 차단된 실측.
  - **SD-14** (운영 실증 ④, 타 세션 발견): conductor 조기 종료 — one-shot `claude -p` 에서 turn 종료 = 프로세스 종료인데 sonnet conductor 가 Monitor 대기로 turn 을 끝냄. 3층 결정론화: (a) wrapper depth_note 에 one-shot 대기 계약 주입 (b) Stop hook 게이트 — open 자식 스테이지 row 남기고 종료 시 차단(전제: -p 모드 Stop hook 발화 실측 + worktree-local registry 갭 선수정) (c) dispatch-wait 동기 대기 헬퍼(dispatch-liveness 재사용). env 식별자(CLAUDE_CODE_CHILD_SESSION·AGENT_DISPATCH_DEPTH)는 wrapper 가 이미 주입함을 실측 확인.
  - **SD-OPEN-2** (관찰): 스테이지 SessionEnd mem curator 기동 — 개입 없이 계측 로그 관찰만.
  - **drill 확장**: 회귀 케이스에 "프롬프트 떠먹임 없이 스킬 문서만으로 분사 발생" 문서-효력 검증 추가 (SD-10 acceptance).
  - **범위 제외 명시**: `loops/**`·`tools/fleet/**` 타 세션 소유 — §9-13 fleet 표시 이관.

## Phase 2 완료 (code-report, 2026-07-10)

- **Status**: Phase 2 **implemented** — 스테이지 분사(code-plan→code-execute→code-test→code-execute-fix, 전부 depth-2 headless) 로 완주. 커밋 `5ae8c8a..cd9859b`(9개, `8596e25` 대비).
- **Decision Points 갱신**:
  - SD-10~13: 구현 완료(dev-pipeline dispatch-first, SD-11 reminder soft 등록, SD-12 프로필 4종, SD-13 spec 전제 문구).
  - **SD-14b (Stop gate)**: **held** — `claude -p` Stop hook 미발화 실측(probe 2026-07-10, `_internal/dev_reviews/phaseA_stop_probe.md`, CC #38651/#40506/#20063 교차확인) → 등록 보류, SD-14 는 depth_note 대기계약 + `dispatch-wait.sh` 로 커버.
  - **SD-OPEN-1**: pilot 계측 진행 중(마이크로-스테이지 inline 임계 미확정).
  - **SD-OPEN-2**: 관찰 지속(스테이지 SessionEnd mem curator, 개입 없음).
- **검증**: code-test Level 3 판정 시점 PASS 311/FAIL 12(신규 회귀 2건, baseline 기존 FAIL 10건). code-execute-fix 이후 conductor 재검증 = `check-adaptation-boundary.sh` PASS(FAIL 0)·`build-manifest.py --check` up-to-date → **최종 신규 회귀 0**.
- **잔여 handoff**: drill 케이스 정의만(러너 미설치, `loops/**` 타 세션 소유), `assert.sh` POSIX `sh -n` bashism 전달 필요.
- 상세: `.agent_reports/plans/2026-07-10_stage-dispatch-phase2/final_report.md`
- minor (2026-07-10, 머지 후 상태 동기): dev phase in_progress→done — Phase 2 main 머지 52f2f2c. 잔여(다음 사이클): 프로필 효과 계측·SD-14b(-p Stop hook 미발화로 held)·SD-11 deny 재판단·drill 러너 등록(loops 세션 handoff).
- v3 (2026-07-10): 사용량 복원력 + 크로스 하네스 등재 — autopilot-spec update quick, v2 snapshot = `_internal/versions/v2/prd.md`.
  - **SD-15** (운영 실증 ⑤): Phase 2 conductor 1차 분사가 launch 직후 session limit 즉사 — row open 잔존, liveness SUSPECT 로만 16분 지연 발견. wrapper 가 조기 exit + 로그 limit 패턴을 감지해 row 자동 마감 + reset 시각 표면화. dispatch-wait/liveness 도 로그 패턴을 DEAD 근거에 추가.
  - **SD-16** (사용자 요구): "codex·claude 사용량 직접 체크 + 상호보완(사용량·특성) 크로스 하네스 분사" — usage-check 헬퍼(runtime-currentness 조사 필수), 상호보완 라우팅(사용량 failover + 특성 강점 배치 + 검증 자리 타 모델 계열 교차 — codex-review-team 선례), fleet 연속성, thorough+ 다축 동시성 실측 검증(사용자 확인 요청 — 계약은 다축 워커 명시하나 병렬 실측 부재).
  - **SD-OPEN-3**: 보완 라우팅 가중 — 초기 보수 정책, 계측 후 조정.
- minor (2026-07-10): SD-16 한도 비대칭 기본값 추가 — Claude Code 한도 > Codex (사용자 제공, 가변 전제) → Claude 주력·Codex 보완(교차 리뷰·failover 고가치 자리 우선). 하드코드 금지, 이름 있는 설정값으로. (Phase 3 사이클 worktree spec 은 375207e 시점 → 수확 대조 결과 미반영 확인, 수확 후속으로 구현.)
- **Phase 3 구현 done** (2026-07-10, 브랜치 `stage-dispatch-phase3`, 미머지 — 수확은 메인): SD-15(wrapper `--early-exit-watch`+`scan_death`+`close_job_row` → limit-즉사 row 자동 마감·reset 표면화, liveness/wait 로그-limit DEAD 근거)·SD-16(a `usage-check.sh` 보수 조회 — 공식 스크립트 표면 부재 확정[Claude `/usage`·Codex `/status` 대화형뿐]로 jobs.log 마커+reset 캐시 기반, b 상호보완 라우팅 core §5.10 ⑧+dev-pipeline 파생, c row 연속성 실측)·SD-16(d) thorough+ 다축 동시성 실측 **PASS(병렬 성립, 계약 drift 없음)**. 검증: 신규 3+회귀 2 스위트 PASS, boundary check 신규 FAIL 0(잔존 1=fleet baseline). 상세: `.agent_reports/plans/2026-07-10_stage-dispatch-phase3/final_report.md`. 이월: SD-15 codex/opencode wrapper 동형(ADAPTATION disclosure)·프로필 A/B 계측. **수확 노트(메인)**: 이 사이클은 인프라 자기수정 예외로 inline 실행(drift 자진 공개, metrics.md) — 문서-효력 단독 검증은 미완, 다음 일반 사이클로 이월.
- v4 (2026-07-10): 도그푸딩 정련 3건 — SD-15/16 첫 실전 오탐 2건(SD-15b 로그-패턴 DEAD 앵커링 — 정상 완주한 conductor 의 "limit 논하는 보고문"에 LIMIT_RE 오탐 / SD-16e usage-check reset 의미론 — reset 부재 마커가 실제 리셋 후에도 limited(-)) + SD-11b deny 상향(최소 프롬프트 conductor 2연속 inline — Phase 3 는 자기수정 예외 성립, sd15-parity 는 Claude 분사 경로 무변인데 예외 차용 = soft reminder·한정형 fallback 문서 무효 실증 → wrapper env AGENT_DISPATCH_INTENSITY 주입으로 결정론 deny, 자기수정 예외는 orchestrator 명시 opt-out 만). v3 snapshot = _internal/versions/v3/.
- v5 (2026-07-10): SD-17 separability 판정 — 사용자 결정 (a). conductor 3연속 실측(자기수정 정당 1·차용 위반 1·경계-결합 정당 1)이 "분사 실익 = separable 작업" 수렴 → 분사 기본 불변 + 비분리 판정 시 inline 허용(metrics 기록 의무 — 기록 없는 inline 은 위반으로 감사 표면화, 분리 부분 in-session 병렬, 자기수정은 SD-11b(c) opt-out). deny 는 code-* Skill 경로 한정 유지(의미 판단 구간 억지 규칙화 회피). v4 snapshot = _internal/versions/v4/.

- v6 (2026-07-13): quick depth-1 topology — autopilot-spec update standard, v5 snapshot = `_internal/versions/v5/prd.md`.
  - **SD-18**: `direct` depth-0 inline, `quick` depth-1 one-shot capability worker, `standard+` depth-1 conductor -> 순차 depth-2 stage-workers. quick worker 는 micro-plan·plan-check-lite·implementation·focused verification·concise report 를 한 세션에서 끝내고 depth-2 를 열지 않음. mutation-capable quick 은 isolated worktree 사용.
  - **SD-19**: Codex quick 은 headless check 통과 시 headless dispatch 우선(Fleet-visible). headless 실패 시 native subagent fallback + Fleet visibility degradation note; 둘 다 불가 시 inline + concise fallback reason. parent local evidence: native subagent ok, strict headless projection ok, quick depth-1 dry-run accepted, quick depth-2 forbidden.
  - **SD-20**: Fleet 는 depth-1 quick worker 를 blinking `quick/exec` activity stage 하나로 표시. quick depth-2 child row 는 계약 위반.
  - **Official evidence**: OpenAI Codex manual Subagents section (`https://developers.openai.com/codex/codex-manual.md#execution-model-and-workflows`) — subagents move noisy work off the main thread, consume more tokens, and parallel write-heavy workflows require caution. Helper fetch ended with missing `x-content-sha256`; cached official manual was inspected.
- v7 (2026-07-13): orchestration/model-family routing + Fleet hotfix acceptance — autopilot-spec update standard. 기존 v6 snapshot `_internal/versions/v6/prd.md`가 update 직전 current v6와 byte-identical(`cmp` exit 0)임을 확인했고 재생성하지 않음.
  - **SD-21**: standard+ conductor high-reasoning/deep orchestration 기본, fast mechanical-only.
  - **SD-22**: planning/architecture/decomposition GPT family via Codex + deep maker affinity(비-hard-pin), plan review 다른 family 선호, 단일 route priority와 core/adapter 소유 경계 확정.
  - **Currentness**: 공식 Models는 GPT-5.6 Sol을 권장하고 exact ID=`gpt-5.6-sol`, API alias=`gpt-5.6`으로 게시. parent Codex ChatGPT surface는 alias를 거부하고 현 환경 exact ID를 지원했으므로 adapter probe 성공 exact ID만 선택하고 clean fallback.
  - **SD-23**: read-only `route-dispatch` helper(Claude+Codex, OpenCode honest unknown).
  - **SD-24**: Fleet env-child-hidden + non-code stage fuzzy-match 차단 수용 기준.
