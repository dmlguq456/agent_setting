# Stage: report (depth-2 headless, technology mode, intensity=thorough)

너는 autopilot-research 파이프의 **report stage** 담당 depth-2 세션이다. 이전 대화 컨텍스트 없음 — 아래 정보와 참조 파일만으로 작업. 이 세션 안에서 Agent(연구팀)/Agent(편집팀)/Agent(codex-review-team 불필요, thorough 는 adversarial 아님) 를 in-session 으로 직접 호출한다(별도 headless 재분사 금지 — depth 3+ 금지).

## Artifact 경로
- artifact_dir: `/home/Uihyeop/agent_setting-wt/research-token-self-regulation/.agent_reports/research/token-self-regulation`
- 원본 skill reference (Step 4 전문 — 반드시 Read):
  - `/home/Uihyeop/agent_setting/skills/autopilot-research/references/report-generation.md` (Step 4a technology mode 7개 보고서 템플릿 = 파일 188번째 줄 부근 `### Mode \`technology\` — 7 files`, Step 4a-Polish, Step 4b QA Loop, Step 4c Status Check)
  - `/home/Uihyeop/agent_setting/skills/autopilot-research/references/summary-and-briefing.md` (참고만 — Step 5/6 은 conductor 가 별도로 처리하니 이 세션은 안 함)
- 입력: `{artifact_dir}/analysis_summary.md` (필독 — 4개 분석축: 메커니즘분류/실측한계/self-regulation일반화/하네스시사점), `cards/*.md` (22개), `code_resources/`(caveman·ponytail·wilpel 소스 발췌 + EXCERPTS.md), `_internal/search_results.json`.
- 내부 보조 참조(재조사 아님, report 4번 파일 하네스 시사점 대조용): `{artifact_dir}/../token-ceremony-audit/2026-07-07_context-footprint.md`, `2026-07-07_reduction-plan.md` — 기존 하네스 context footprint 현황과 이번 조사의 token-budget 자기조절 시사점을 연결.

## Mode: technology — 7개 보고서 (템플릿 어댑테이션 필요)

표준 technology 템플릿은 codec/protocol/vendor 대상이라 이 주제(token-saving skill 생태계)엔 제목·내용을 아래처럼 어댑테이션한다. **구조(7파일, 각 파일 역할)는 유지**, 내용 초점만 바꾼다:

- `00_briefing.md` — Executive Briefing. Mermaid: 4계층 메커니즘 분류(A/B/C/D) landscape. Top-3 actionable insight (예: "output-compression 은 안전, input-context-reduction 은 default off 권장" 같은 axis 4 핵심 결론).
- `01_landscape.md` — Technology Landscape. "Category taxonomy" = 4계층 메커니즘 분류(output-compression/behavior-suppression/input-context-reduction/budget-directive-self-monitoring). "vendor" = caveman/ponytail/wilpel/headroom/RTK/TokenSave/token-optimizer/ContextBudget 등. Lineage diagram (caveman↔wilpel 이름은 같지만 계열 다름 — 명확히).
- `02_standards.md` — "Standards & Specs" 대신 **"측정·검증 방법론"**: 각 발견물이 절감을 어떻게 주장·측정했는지(광고 수치 vs 저자 자기검증 vs 독립 replay vs 학술 반증) 인벤토리. codepointer replay·CAVEWOMAN·SkillReducer 방법론 상세.
- `03_vendor_comparison.md` — Vendor/Solution Comparison → 발견물 매트릭스(도구 | 계층 | 절감claim | 실측치 | 재주입오버헤드 | 품질영향 | 검증신뢰도). **Takeaway**: 상황별 추천(예: output-heavy workload엔 A, terse workload엔 비권장 등).
- `04_technical_deep_dive.md` — Algorithm·Mechanism Details. caveman(system-prompt 지시문)·ponytail(7-rung decision ladder)·wilpel(결정론/LLM 하이브리드) 실제 메커니즘 상세(code_resources/EXCERPTS.md 기반). Performance trade-off(세션 희석·재주입 오버헤드·풍선효과).
- `05_deployment.md` — "Deployment Considerations" → **"하네스 적용 시 고려사항"**: intensity 축과 token-budget 축의 직교성/간섭 지점(analysis_summary §4b), safety rail 불가침 원칙, 레버 우선순위(A 우선·C default off), 재주입 오버헤드 회계.
- `06_implementation.md` — Goal-Adaptive Action Roadmap (기존 템플릿 형식 유지, build/adopt 우선). **`## Next Pipeline`** 섹션 필수 — 다운스트림 `autopilot-spec` 호출 권장 커맨드를 copy-paste-ready 로 명시 (예: token-budget 자기조절 축 spec 작성 목적).
- `07_resources.md` — Open-source Code/Tools. Tier 1(직접 참조 가능 — caveman/ponytail/wilpel repo, 각 Quick verify 방법) / Tier 2(참조용 — headroom/RTK/TokenSave/token-optimizer) / Tier 3(실험용 — ContextBudget RL 정책 등).

**공통 규칙** (report-generation.md 원문 참조): 한국어 산문 + 도메인 용어(리포명/저자/지표/모델명)는 영어 유지. 모든 비교표는 굵은 **Takeaway** 줄로 마무리. 수치·claim 은 analysis_summary/cards 출처만(fabrication 금지). 파일 간 `[text](filename.md)` cross-reference.

## Step 4a-Polish: 편집팀 모드 B (intensity thorough → 호출 필수)
7개 보고서 작성 완료 후 `Agent(subagent_type="편집팀")` 모드 B(다듬기) in-place 호출. 판교체·번역체 회피, 표기 일관성, 내용(claim/수치/citation)은 손대지 않음.

## Step 4b: QA Loop (intensity=thorough → 2× deep reviewer 병렬 + 1× fast fact-checker, max 2 rounds)
`report-generation.md` Step 4b 원문 그대로 따름 (rigor tier: thorough). round=0, review_dir={artifact_dir}/_internal/reviews/.
- Quality reviewer 2개 병렬 (completeness reviewer + accuracy reviewer, 둘 다 deep — Agent(subagent_type="연구팀") 로 role 명시)
- Fact-checker 1개 (fast, cards/ verbatim 대조)
- 🔴 있으면 round<2 조건에서 재작성 재호출, 없으면 exit. round>=2 잔존 🔴 → `_internal/reviews/unresolved.md` 기록.
- thorough 는 adversarial 아니므로 claim-verify·codex-review-team external adversary 는 **호출하지 않음**.

## Step 4c: Status Check
`{artifact_dir}/07_resources.md` 존재 + 7개 파일 전부 존재 확인. 부분 실패면 어느 파일이 빠졌는지 status 파일에 기록.

## Status 파일 (필수)
`{artifact_dir}/_internal/stage-report-status.json`:
```json
{"stage": "report", "status": "done", "reports_written": 7, "qa_rounds": <int>, "unresolved_flags": <int>, "notes": "<2-3줄 한국어 요약 — 핵심 결론 + QA 상태>"}
```
실패/부분 시 `"status": "partial"` 또는 `"failed"` + `"reason"` + 어느 파일 누락인지.

마지막 응답(반환 텍스트)은 파일 경로 + 3-5줄 한국어 요약만. 보고서 본문 전체를 반환하지 말 것.
