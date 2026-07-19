---
status: done
date: 2026-07-20
intensity: thorough
task: 분사 워커 ↔ 네이티브 팀 부트스트랩 중복 해소 + native-bootstrap 측정 표면 추가
---

# Goal

depth-2 스테이지 워커가 네이티브 팀을 재소환할 때 두 부트스트랩 스택(스킬 계약 ↔ 에이전트 페르소나)이 같은 의미를 이중 로드하는 지점을 단일 원천+포인터로 정리하고(DESIGN_PRINCIPLES §0.5·§10.4), 네이티브 에이전트 부트스트랩 바이트를 context-footprint에 측정 표면으로 노출한다(예산 신설 없음, baseline 5% 회귀만 상속).

# Current State (검토 4종 종합)

- code-plan/refine/execute/test/report 모두 스테이지 세션 안에서 팀을 재소환하며, 위임 프롬프트가 팀 페르소나의 역할 콘텐츠를 재기술.
- 소유 기준: 스테이지 계약(경로·게이트·리졸브)=스킬, 역할 행동(절차·품질·포맷)=에이전트. plan-team만 직접 소환 불가 → 비대칭 무위험. dev/qa/editorial은 직접 소환 경로 존재 → 역할 콘텐츠는 에이전트에 잔존 필수, 스킬 사본만 축약.
- 정합성 결함 3건: ①plan return(1줄 vs 3-5줄) ②test report 템플릿 이중 정의(영/국문 분기) ③editorial polish 게이팅(단일원천 선언 vs code-report 재기술) — 각각 역할 쪽을 정본으로 정합화.
- Codex/OpenCode는 manifest 생성이라 영향 없음. code-* 본문은 skills/ ↔ adapters/claude/skills/ 실사본 수동 동기화, 프론트매터는 생성물이라 불가침. agent-modes는 플러그인 미투영.
- footprint: 측정 전용 선례 존재([largest-skill-bodies]), §6.1과 무충돌. agents 52,589B + agent-modes 119,338B 미측정 상태.

# Change Plan

1. footprint: [native-bootstrap] 블록(에이전트별·모드그룹별 노출 + 집계 2키 surfaces 등록), baseline 2키 추가, portable-guards.test.sh grep 1줄. (구현 완료, baseline 반영 단계)
2. code-plan: 위임 프롬프트에서 절차·return 재기술 제거(페르소나 소유), 3-5줄 요약 문구를 plan-team Return Format(1줄) 기준으로 정합.
3. code-refine: 메모 형식 5종 목록 제거 → plan-team refine 절차 참조.
4. code-execute: 시그니처 안전 규칙 전문 재기술을 dev 역할 참조로 축약, step log Decision 필드 상세를 refactor 모드 참조로 축약.
5. code-test: 인라인 리포트 템플릿 제거 → qa/test.md 리포트 구조 참조(경로 소유만 유지).
6. code-report: editorial 게이팅 조건·content boundary 재기술 → polish.md·editorial-team 참조로 축약.
7. qa 모드(plan-review·code-review): qa-team 라우터 공통 규칙(5-7 findings·uncertain-의도적·praise)의 문자 중복 제거 — 라우터가 항상 선로드되므로 무손실.
8. plan-team: Language Rule 15줄 전개를 핵심+단일원천 포인터로 축약.
9. CONVENTIONS 라우트 불변식: in-session 팀 소환이 depth를 증가시키지 않음을 한 절로 명확화(:37과의 잠재 모순 해소, 신규 규범 아님).

이연(후속 사이클): qa 리뷰 템플릿(🔴🟡🟢) 공유 include 승격, dev 모드 4중 confirm 규칙 승격, 라우터 공통 블록(R5) 승격, code-report 페르소나 갭(4.1).

# Verification

context-footprint status=ok(신규 키 포함) · sync-entry-skill-layer --check · sync-native-plugin 재생성+--check · build-manifest --check · skill-conformance check · skills/↔adapters 사본 diff 0 · 편집 파일 의미 보존 자체 대조(§10.4 포인터에 파일명·시점·의무 유지).

# Risks

- 위임 프롬프트 축약으로 팀이 받던 명시 지시가 페르소나 의존으로 바뀜 → 페르소나에 동일 의무 존재를 편집 시점마다 대조.
- return 계약 정합(1줄)은 스테이지 오케스트레이터가 받는 요약이 짧아지는 실동작 변화 → plan-team Return Format이 verdict 포함하므로 게이트 판단에는 무손실.
