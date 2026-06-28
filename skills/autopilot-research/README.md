# autopilot-research

> 본 README 는 `SKILL.md` 의 GitHub 표시용 mirror. 권위 있는 동작 명세는 `SKILL.md`.

## 개요
외부 분야 조사 파이프라인 — 학술/산업/시장 3개 mode별 보고서를 생성합니다. 논문 검색 + 분석 + 코드/모델/데이터셋 자원 발견 + 분야 implementation 가이드를 자동으로 산출.

> **Scope 경계**: markdown 분석 리포트만 산출. 슬라이드 본문 / paper draft / code / PPTX는 만들지 않음. 그것들은 autopilot-draft / autopilot-code에 인계.

## 호출 형식
```
/autopilot-research <topic> --mode academic|technology|market [--depth shallow|medium|deep] [--qa quick|light|standard|thorough] [--from search|analyze|report] [--no-clarify] [--no-figures]
```

## 3개 모드

| 모드 | 용도 | 산출 |
|---|---|---|
| academic | 분야의 핵심 논문 + 방법론 + 데이터셋 + 모델 자원 조사 | `research/{topic}/` — 9개 markdown (briefing, core_papers, baselines, code_resources, datasets, implementation, reading_guide, ...) |
| technology | 기술 표준 / 산업 동향 / 도구 비교 | `research/{topic}/` — 7개 markdown |
| market | 시장 분석 / 경쟁자 조사 / 채택 사례 | `research/{topic}/` — 5개 markdown |

## 산출물 위치
`<artifact-root>/research/{topic}/` 하위.

3-tier 컨벤션:
- **T1** (root): `00_briefing.md`, `01_core_papers.md`, ..., `06_reading_guide.md` (mode에 따라 5-9개)
- **T2**: `cards/` (논문별 카드 — academic), `code_resources/` (모델·레포 카드 — academic)
- **T3**: `_internal/search_results.json`, `_internal/browser_extracts/`, `_internal/reviews/` (QA 로그)

## --depth
- `shallow`: 상위 10-20 결과만, abstract only
- `medium` (default): 인용수·venue tier로 우선순위, citation > 10이면 full read
- `deep`: paywall 페이지까지 자료팀 위임, reference chaining

## --qa
- `quick` (1-pass 1 라운드)
- `light` (fast reviewer single-pass)
- `standard` (deep reviewer + fast fact-checker parallel)
- `thorough` (2× deep reviewers + fast fact-checker)
- `adversarial` (thorough + external adversary + claim-verify)

> concrete model mapping 은 runtime adapter 책임. Claude adapter 는 fast=sonnet, deep=opus, external adversary=Codex CLI 로 재현한다.

## --from
- `search`: Step 1 (paper search) — 검색·필터링·tier 분류
- `analyze`: Step 2 (paper analysis) — per-paper card 작성 + reference chaining
- `report`: Step 3 (report generation) — 7-9개 markdown 합성

## 파이프라인 (개요)
1. **Step 0 Scope Clarification** (모호 query 시 2-4개 질문)
2. **Step 1 Paper Search** — HF / OpenAlex / arXiv / Google Scholar / Semantic Scholar 6 sources 순차
3. **Step 2 Paper Analysis** — 인용수·venue tier 기반 reading depth 결정, paywall은 자료팀 위임
4. **Step 3 Report Generation** — mode별 5-9개 markdown 산출 + 06_implementation.md의 Next Pipeline 표로 autopilot-code / autopilot-draft / refine 인계

## Chaining (implicit)
- autopilot-research → autopilot-draft: `research/{topic}/`을 prompt 키워드 fuzzy match로 자동 발견
- autopilot-research → autopilot-code: code-plan이 implicit 인지

## Wiki database 안내

---
*원본: `<agent-home>/skills/autopilot-research/SKILL.md`*
