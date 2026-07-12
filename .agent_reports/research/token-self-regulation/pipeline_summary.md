# Research Survey Pipeline Summary: token-self-regulation

- **Date**: 2026-07-13
- **Query**: caveman·ponytail 심층 분석 — 에이전트 토큰 사용 자기조절(self-regulation) 메커니즘 설계 입력 (intensity 축과 독립)
- **Depth**: deep
- **Status**: done
- **From-Stage**: N/A (신규, --no-clarify)

## Process Log

| Step | Action | Result | Notes |
|---|---|---|---|
| 1 | Input parsing | technology mode | topic: token-self-regulation |
| 2 | Source Search (depth-2 stage: tsr-search, fast implementer) | 25 발견물 | sources: WebSearch/WebFetch(GitHub·블로그·카탈로그) + arXiv 보조. 필수 6대상(caveman/ponytail/wilpel/headroom-RTK-TokenSave/Hackenberger stack/skillsllm 카탈로그) 전부 확보 |
| 3 | Source Analysis (depth-2 stage: tsr-analyze, deep maker; Phase A+C, B 비활성) | 22 cards + code_resources(caveman/ponytail/wilpel 실 clone) | analysis_summary.md 4개 분석축(메커니즘분류/실측한계/self-regulation일반화/하네스시사점)으로 종합 |
| 4 | Report Generation + QA (depth-2 stage: tsr-report, deep maker) | 8 files (00_briefing~07_resources, technology 7-template 어댑테이션) | QA: thorough(2 deep reviewer 병렬 + 1 fact-checker), round 1 에서 🔴 0·🟡 5(전부 정정) → exit. 편집팀 모드 B 다듬기 적용 |

## Artifacts

- Search (raw): `_internal/search_results.json`
- Analysis: `analysis_summary.md`, `cards/` (22개), `code_resources/`(caveman·ponytail·wilpel 소스 발췌 + EXCERPTS.md)
- Reports: `00_briefing.md` ~ `07_resources.md` (technology mode 7-file, 주제 특성상 02/05 제목 의미 어댑테이션 — 02=측정·검증 방법론, 05=하네스 적용 고려사항)
- QA: `_internal/reviews/round_1_quality_completeness.md`, `round_1_quality_accuracy.md`, `round_1_factcheck.md`

## Decision Points

| Step | Decision | Response | Action |
|---|---|---|---|
| 0 | Scope clarification | `--no-clarify` (depth-0 세션에서 이미 합의) | clarified_intent 를 pipeline_state.yaml 에 기록 후 진행 |
| 3 (Phase B) | technology mode citation graph 의미 약함 | 자동 비활성 | chaining_results.md 미생성 (의도적) |
| 4b (QA) | round 1 🟡 5건 잔존 | thorough tier round<2 조건 충족 → 세션 내 surgical 정정 | round 2 재호출 불필요(즉시 정정 가능한 건들), unresolved.md 미생성 |
