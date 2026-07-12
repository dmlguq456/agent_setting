# Research Survey Pipeline Summary: skill-design-principles
- **Date**: 2026-07-13
- **Query**: "Matt Pocock 'Skills for Real Engineers' — AI 에이전트 skill 설계 원칙 심층 조사 (trigger·structure·guidance·pruning) — 스킬셋 진단·개선 설계 입력"
- **Mode**: technology · **Depth**: deep · **Intensity**: thorough
- **Status**: done
- **From-Stage**: N/A

## Process Log
| Step | Action | Result | Notes |
|---|---|---|---|
| 1 | Input parsing | technology-mode survey | topic: skill-design-principles |
| 2 | Source search | 21 cards + mattpocock/skills git clone verbatim | Phase A skim + Phase C code (B 비활성) |
| 3 | Source analysis | analysis_summary.md | 4축 확정 Invocation/Information Hierarchy/Steering/Pruning; Guidance↔Steering CONFIRMED |
| 4 | Report Generation (연구팀) | 8 files (00_briefing~07_resources, technology mode) | 편집팀 polish 완료 |
| 4b | QA loop (thorough) | 2 rounds | R1: 2× deep quality + 1× fast fact-check → 🔴1(accuracy)+🟡 다수; R2: 연구팀 수정 + verify → 🔴0 |

## Artifacts
- Search/meta: _internal/search_results.json, _internal/code_search.md, _internal/pocock-verbatim-comparison.md
- Analysis: analysis_summary.md
- Reports: 00_briefing.md ~ 07_resources.md (technology mode, 8 files)
- QA reviews: _internal/reviews/round_1_{quality_coverage,quality_accuracy,factcheck}.md, round_2_verify.md
- Code resources: code_resources/ (mattpocock/skills SKILL.md 예시 9개 verbatim)

## QA 결과
- Round 1: 🔴 1건(accuracy — scottspence ~50%를 hook 적용 후가 아닌 bare 신뢰도로 재배치한 왜곡) + 🟡 다수(failure-mode 종 수 드리프트, post-it invocation 판정, gerund 오귀속, 06 로드맵 step 누락 등). fact-check verbatim 전수 ✅.
- Round 2: 연구팀 재호출로 🔴 + material 🟡 전부 수정 → verify 결과 배포 보고서 🔴 0, 새 왜곡 없음.
- **잔여 residual (보고서 아님)**: analysis_summary.md(analyze-stage 산출물)에 3개 미세 drift 잔존 — §2c ~50% bare 프레이밍, §7.2 "6종" 라벨 vs 4개 이름 열거, §4a paraphrase-as-quote. 배포 보고서(00~07)는 이 3건 모두 정정 반영됨. analysis_summary는 analyze-stage 소유 산출물이라 report-stage에서 미수정(cross-stage 편집 회피) — 다음 analyze 재진입 또는 audit 시 동기화 권장.

## Downstream (06_implementation ## Next Pipeline)
- Inferred goal: adopt/build 혼합 (최종 소비자 = 우리 harness 자체 28스킬 audit+개선).
- 권장 순서: `/audit` (스킬셋·산출물 사후 점검·drift 진단) → 필요 시 `/autopilot-spec "28-skill 4-axis audit 개선 청사진"` → `/autopilot-code --mode refactor "28-skill 4-axis audit 반영"`.
- Boundary: 28스킬 전수 audit은 본 보고서 범위 밖 별도 사이클.
