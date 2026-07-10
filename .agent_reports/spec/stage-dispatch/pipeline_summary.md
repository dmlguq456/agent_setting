# stage-dispatch — Spec Pipeline Summary

- **Date**: 2026-07-10
- **Mode**: library + cli (autopilot 파이프 디스패치 토폴로지 개정 인프라)
- **Status**: spec done (v2) · dev Phase 1 done (main 5b7cf33) · Phase 2 in progress
- **Placement**: 독립 컴포넌트 `spec/stage-dispatch/` — 기존 `spec/prd.md`(Unified Memory System)·`spec/harness-layer-sync/`·`spec/dispatch-profiles/`·`spec/agent-fleet-dashboard/` 무수정.

## 배경

사용자 결정(2026-07-10): "스킬 단위의 처리가 분사해서 할 것을 기본 지침으로. 어차피 산출물 기반 소통." → autopilot 파이프의 각 sub-skill 스테이지(code-plan·execute·test·report)를 `standard+` 에서 **기본으로 별개 headless 세션** 분사. 이는 2026-07-06 "owner 단일 세션 + in-session 팀" 재설계 기본값의 **명시적 반전**. 직접 계기 = 2026-07-10 운영 실증 3종(① in-session 서브에이전트 fleet 미표시 ② hook ceremony 미수령 ③ owner 컨텍스트 비대). research(cross-platform-agent-frameworks) 가 "fresh-context per agent + file-state"를 지배 관용구로 확증(§4-(8))해 근거 보강.

## Process Log
| Step | Action | Result | Notes |
|---|---|---|---|
| 입력 Read | 사용자 결정 + research 3종(summary §4-(8)·gsd·06_impl) + 현행 계약 실측(OPERATIONS §5.10·§5.8·CONVENTIONS §1·§2·WORKFLOW §1.1·§5·DESIGN_PRINCIPLES §8·autopilot-code refs+sub-skills·dispatch-headless.py·3어댑터 §0(C)) | — | 모든 결정 근거를 사용자 결정·research 카드(§/줄)·운영 실증으로 인라인 소급 |
| 현행 실측 | 스테이지 산출물 파일 계약 census(plan/plan.md·checklist·dev_logs·test_logs·final_report) | — | 스테이지 인터페이스가 **이미 파일** — 분사 전제 성립(§2.1) |
| 현행 실측 | context-and-guards.md:51 "스테이지 헤드리스 분리 = worst of both, 금지" 발견 | — | 본 spec 이 **반전하는 정확한 조항** — §2.2·§9-7 |
| 현행 실측 | dispatch-headless.py depth=2/parent/worker_role/게이트 census | — | wrapper 가 **이미 스테이지 분사 골격 지원** → 재작성 불요(§2.4·SD-9) |
| spec | PRD 작성 (lean) | `prd.md` v1 | SD-1~9 채택 + SD-OPEN-1 open(inline 임계 pilot 계측). 영향 표면 14곳. 구현 2-phase |

## 채택 결정 (locked)
- **SD-1~2 (토폴로지·인터페이스)**: depth-1 owner = 얇은 conductor(verdict/게이트만), 스테이지 = depth-2 headless 세션. 인터페이스 = 산출물 파일만, 대화 컨텍스트 전달 금지(산출물 기반 소통). 근거 = 사용자 결정 + research §4-(8) + DESIGN_PRINCIPLES §8 "결과 흐름 file 통해".
- **SD-3 (관제)**: 스테이지 세션 jobs.log 등록(depth=2,parent,worker_role,owner) → fleet 스테이지 row. stealth-death 가드 conductor 책임. 운영 실증 ①② 해소.
- **SD-4 (depth-2 write 개정)**: read-only 기본을 스테이지-워커 클래스별 write 소유로 재정의(plan/execute소스/test/report). depth 3+ 금지 유지.
- **SD-5~6 (모델·가드레일)**: model role conductor 명시(§5.10 ⑦). 동시상한5=Σ(conductor+활성스테이지)·마이크로 inline·실패=스테이지만 재분사·lock=report의 pipeline_summary만.
- **SD-7 (영향 표면)**: 14곳(core·bootstrap 3어댑터·SKILL·wrapper·fleet·drill) 현행문구→개정방향 표. 문구 편집은 core-first 별도.
- **SD-8 (적용 범위)**: standard+ 기본, direct/quick inline 유지 — 2026-07-06 기본값 명시 반전.
- **SD-9 (wrapper)**: 재작성 불요. stage-dispatch helper 신설은 pilot 후 판정.

## 미결 (open — pilot 계측)
- **SD-OPEN-1**: 마이크로-스테이지 inline 의 손익 임계(어느 스테이지 크기부터 분사가 이득). research 가 per-stage dispatch cost 를 수치화하지 않음 → 추측 금지, Phase 1 pilot 토큰/시간 계측으로 확정.

## 반전의 정당성 (현행 금지 조항 대응)
현행 `context-and-guards.md:51` 은 스테이지 분사를 "상태 재발굴 + 연속성 상실 = worst of both"로 금지. 본 spec 은 이를 §0.5 계약 완결성 의무(산출물이 상태를 완전히 담으면 재발굴=파일로드·연속성=파일매체) + §8 마이크로-스테이지 inline 경계로 규칙화해 흡수. research §4-(8)이 "fresh-context+file-state가 context rot 방지 지배 관용구"임을 확증해 반전을 근거화.

## Next
Phase 1(계약문서+wrapper증분+autopilot-code pilot) · Phase 2(autopilot-* 확산+drill 회귀) = 별도 브랜치 구현. pilot 성공 기준 = fleet 스테이지 row·산출물 정상·depth≤2·토큰/시간 계측(SD-OPEN-1 캘리브레이트). 상세 = PRD §12.

## Version History
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
- **Phase 3 구현 done** (2026-07-10, 브랜치 `stage-dispatch-phase3`, 미머지 — 수확은 메인): SD-15(wrapper `--early-exit-watch`+`scan_death`+`close_job_row` → limit-즉사 row 자동 마감·reset 표면화, liveness/wait 로그-limit DEAD 근거)·SD-16(a `usage-check.sh` 보수 조회 — 공식 스크립트 표면 부재 확정[Claude `/usage`·Codex `/status` 대화형뿐]로 jobs.log 마커+reset 캐시 기반, b 상호보완 라우팅 core §5.10 ⑧+dev-pipeline 파생, c row 연속성 실측)·SD-16(d) thorough+ 다축 동시성 실측 **PASS(병렬 성립, 계약 drift 없음)**. 검증: 신규 3+회귀 2 스위트 PASS, boundary check 신규 FAIL 0(잔존 1=fleet baseline). 상세: `.agent_reports/plans/2026-07-10_stage-dispatch-phase3/final_report.md`. 이월: SD-15 codex/opencode wrapper 동형(ADAPTATION disclosure)·프로필 A/B 계측.
