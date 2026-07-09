# Research Survey Pipeline Summary: cross-platform-agent-frameworks
- **Date**: 2026-07-09
- **Query**: 크로스 플랫폼 에이전트 세팅 프레임워크 구조 조사 — GSD(최우선) + spec-kit/BMAD-METHOD/SuperClaude/Superpowers/agent-os/claude-flow + Claude Code 공식 plugin/marketplace + 멀티하네스 projection 사례. 핵심 관심: core/adapter/proj 3층 drift 방지 메커니즘.
- **Mode**: technology
- **Depth**: medium (single-pass targeted survey; no query-expansion rounds — 대상이 사전 지정된 9개 framework/topic)
- **Status**: done
- **From-Stage**: N/A (신규)

## Process Log
| Step | Action | Result | Notes |
|---|---|---|---|
| 1 | Input parsing | technology mode, topic=cross-platform-agent-frameworks | 사용자가 mode·조사 대상·산출물 경로를 명시해 Step 1.5 Scope Clarification 생략 |
| 2 | Source Search | N/A (전통 paper search 미적용) | technology mode 중에서도 조사 대상이 사전 지정된 리스트라 WebSearch/WebFetch 직접 수행으로 대체 |
| 3 | Source Analysis (Agent x 8, parallel) | 9개 카드 생성 (GSD/spec-kit/BMAD-METHOD/SuperClaude/Superpowers/agent-os/claude-flow/Claude Code 공식/멀티하네스 projection) | Phase A만 해당(technology mode B/C 비활성), 각 카드 `## Sources` 절 필수 포함 |
| 3e | analysis_summary.md 컴파일 | 완료 | 축 A(single vs multi-runtime) × 축 B(convention-only ↔ machine-enforced gate) 분류 + drift 방지 패턴 5종 도출 |
| 4a | Report Generation (Agent) | 8개 파일 (00_briefing ~ 07_resources) | technology mode 템플릿, goal=adopt 로 06_implementation 작성 |
| 4a-Polish | 편집팀 모드 B 다듬기 | 8개 파일 전체 in-place 수정 | 판교체 어휘 통일(prior art→선행 사례 등), Takeaway→요점 라벨 통일 |
| 4b | QA Loop round 1 | quality: PASS(강함) / fact-check: ✅ 0건 fabrication, 🟡 2건 표현 뉘앙스만 | qa=standard → 1× deep quality reviewer + 1× fast fact-checker 병렬, 🔴 없어 1라운드 종료 |
| 4c | Status Check | `00_briefing.md` 존재 확인 | 통과 |

## Artifacts
- Cards: `.agent_reports/research/cross-platform-agent-frameworks/cards/*.md` (9개)
- Analysis: `.agent_reports/research/cross-platform-agent-frameworks/analysis_summary.md`
- Reports: `00_briefing.md` ~ `07_resources.md` (technology mode, 8개 — 00~07)
- QA reviews: `_internal/reviews/round_1_quality.md`, `_internal/reviews/round_1_factcheck.md`

## Decision Points
| Step | Decision | Response | Action |
|---|---|---|---|
| 1 | Mode 확정 | 사용자가 `tech mode` 명시 | Scope Clarification 생략, technology 템플릿(7 report set, 실제로는 00~07 8개 파일) 적용 |
| 3 | 대상 조사 순서 | GSD "필수·최우선" 명시 | GSD 카드를 가장 깊게(17 tool-use, 최대 토큰) 조사, 다른 8개 대상과 병렬 dispatch |
| 4a | 06_implementation goal 추론 | 원 query 가 "우리 세팅과의 대비 → drift 방지 메커니즘 차용" 지향 | goal=adopt 로 판정, adopt 템플릿(선택 기준 매트릭스+후보 shortlist+pilot 계획) 적용 |
| 4b | QA round 종료 | 🔴 없음 (quality PASS, fact-check 🟡 2건만) | 재호출 없이 1라운드로 종료 |
