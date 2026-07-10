# stage-dispatch — Spec Pipeline Summary

- **Date**: 2026-07-10
- **Mode**: library + cli (autopilot 파이프 디스패치 토폴로지 개정 인프라)
- **Status**: spec done (v1)
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
