# Stage: analyze (depth-2 headless, technology mode)

너는 autopilot-research 파이프의 **analyze stage** 담당 depth-2 세션이다. 이전 대화 컨텍스트 없음 — 아래 정보만으로 작업.

## Artifact 경로
- artifact_dir: `/home/Uihyeop/agent_setting-wt/research-token-self-regulation/.agent_reports/research/token-self-regulation`
- 원본 skill reference: `/home/Uihyeop/agent_setting/skills/autopilot-research/references/pipeline-search-analysis.md` (Step 3, technology mode: Phase A 활성 / Phase B 비활성 / Phase C 활성)
- 입력: `{artifact_dir}/_internal/search_results.json` (25개 발견물 — GitHub 리포 9, 블로그/카탈로그 11, arXiv 논문 5). 이 파일을 먼저 Read 할 것.

## Clarified intent (분석 관점 — 반드시 반영)
```
핵심 대상: github.com/JuliusBrussee/caveman (출력 산문 압축, ~65% 출력 토큰 절감,
세션 전체 효과 4-5% 비판 존재) 및 github.com/DietrichGebert/ponytail (lazy senior dev
decision ladder 로 코드 작성량 자체 억제). 보조 생태계: wilpel/caveman-compression,
Headroom(RTK)/TokenSave, Hackenberger Ultimate Token-Saving Stack, openagentskill/skillsllm
카탈로그 유사 skill.

분석축 (4개, 각 카드/요약에서 명시적으로 다룰 것):
1. 메커니즘 분류 — 출력 표면 압축 vs 행동 억제(작업량 축소) vs 입력/컨텍스트 절감 vs
   budget 지시·self-monitoring. 각 발견물을 이 4분류 중 하나 이상으로 태깅.
2. 실측 절감 수치와 한계 — output-only 절감의 세션 전체 효과, 재주입 오버헤드(skill 자체
   input 토큰 비용), 품질 회귀(adversarial safety 주장 검증). search stage 가 발견한
   codepointer.substack 반증 분석(실사용 3.7% vs 광고 60-90%, 3중 gap)과 arXiv
   CAVEWOMAN(2606.24083, input 압축 순손실 ~1.15x) 을 반드시 핵심 비판 근거로 활용.
3. self-regulation 일반화 — 어떤 신호(잔여 budget·작업 가치·컨텍스트 압박)로 어떤
   레버(출력 스타일·작업 범위·도구 호출·분사 깊이)를 조절하는가. 각 발견물에서 이
   신호->레버 매핑을 추출 가능하면 명시.
4. 하네스 시사점 — intensity 축(난이도·중요도 파생)과 독립인 token-budget 자기조절 축
   설계 입력. 두 축의 직교성/간섭 지점.
```

## Phase 활성 (technology mode)
- **Phase A (skimming)**: 활성 — 25개 발견물 전부 카드화. GitHub 리포는 README 전문(이미 search stage 에서 browser_extracts 나 URL 확보됐으면 재활용, 없으면 WebFetch 재시도) 기반으로 카드 작성.
- **Phase B (reference chaining)**: **비활성** — technology mode 는 academic citation graph 의미 약함. `_internal/chaining_results.md` 생성하지 않음.
- **Phase C (code & model search)**: 활성 — caveman/ponytail/wilpel-caveman-compression 등 실제 소스 코드(스킬 정의 파일, decision ladder 텍스트, compress 알고리즘)를 가능한 한 실제로 열람해 메커니즘 상세를 카드에 반영. `code_resources/`, `_internal/code_search.md` 에 정리.

## Card 작성 (`cards/{slug}.md`)
각 발견물마다 카드 1개. 표준 필드 + 아래 커스텀 필드 추가:
```markdown
# {title}

**Type**: repo|blog|catalog|paper
**URL**: ...
**분류축1 (메커니즘)**: output-compression | behavior-suppression | input-context-reduction | budget-directive-self-monitoring (복수 가능)
**절감 claim**: <광고/저자 주장 수치>
**실측/검증**: <독립 검증 수치나 비판이 있으면, 없으면 "미검증">
**신호->레버 매핑**: <있으면 기술, 없으면 "명시 없음">
**하네스 시사점**: <1-2줄>

## Summary
...
```

## Output
- `cards/{slug}.md` × 25 (또는 확인 결과 병합 가능한 것은 병합, 최소 20개 이상 개별 카드)
- `code_resources/` — 실제 코드/ruleset 발췌 (caveman skill 정의, ponytail decision ladder 원문 등)
- `_internal/code_search.md` — Phase C 요약
- `analysis_summary.md` — 4개 분석축 기준으로 종합. phase flags: `chaining_available: false`, `code_search_available: true`.
  - **analysis_summary.md 는 report stage 의 핵심 입력이므로 4개 분석축 섹션을 명확히 분리해서 작성**: `## 1. 메커니즘 분류`, `## 2. 실측 절감과 한계`, `## 3. Self-Regulation 일반화`, `## 4. 하네스 시사점(초안)`.

## Status 파일
`{artifact_dir}/_internal/stage-analyze-status.json`:
```json
{"stage": "analyze", "status": "done", "cards_written": <int>, "notes": "<1-2줄 한국어 요약>"}
```
실패 시 `"status": "failed"` + `"reason"`.

마지막 응답(반환 텍스트)은 파일 경로 + 3-5줄 한국어 요약만.
