---
name: autopilot-research
description: "세 family 공통 사전조사 — 논문·기술·시장 survey 후 다운스트림으로 분기하는 entry"
argument-hint: "<query> [--mode academic|technology|market] [--depth shallow|medium|deep] [--intensity direct|quick|standard|strong|thorough|adversarial] [--no-clarify] [--no-figures] [--from search|analyze|report]"
metadata:
  group: entry
  fam: pre
  modes: [academic, technology, market]
  blurb: "세 family 공통 사전조사 — 논문·기술·시장 survey 후 다운스트림으로 분기하는 entry"
---

# autopilot-research

세 family(논문·기술·시장) 공통 사전조사 entry. `search → analyze → report` 파이프로 survey를 돌려 다운스트림(autopilot-draft / autopilot-code)으로 분기한다. 이 파일은 라우터와 stage 계약만 담고, 세부 orchestration·보고서 템플릿은 필요할 때 아래 reference를 Read 한다.

> **산출물 폴더 컨벤션**: [CONVENTIONS.md §5](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier: T1 root / T2 named subdir / T3 `_internal/`). 본 skill의 raw metadata (`search_results.json`, `phase_a_*.json`, `chaining_results.md`, `code_search.md` 등) + reviews는 모두 `_internal/` 하위로 격리. T1/T2 chapter 파일과 `cards/`는 root.

> `<artifact-root>` 해석: `.agent_reports` 우선, legacy `.claude_reports` 는 이미 존재하고 `.agent_reports` 가 없을 때만 사용. 실제 쉘 명령에서는 `REPORTS_DIR=.agent_reports; [ -d .claude_reports ] && [ ! -d .agent_reports ] && REPORTS_DIR=.claude_reports` 로 치환한다.

## Default Invocation Rule (메인 에이전트 자동 라우팅)

본 skill 은 runtime adapter bootstrap 의 "autopilot-* 호출 패턴" 컨펌 의무 적용 대상(Claude Code: [`CLAUDE.md`](../../adapters/claude/CLAUDE.md) §0). 메인 에이전트가 사용자 발화에서 아래 trigger 신호를 인지하면, 옵션 자동 구성 + 자연어 요약 컨펌 거쳐 invoke.

### Trigger 신호 (자연어 발화 예시)

**academic 모드** (default — 논문·학술 자료):
- "X 분야 조사해줘" / "Y 동향 알려줘"
- "최근 1년 paper 정리" / "literature review"
- "X 모델 / 데이터셋 비교"

**technology 모드** (기술 표준·라이브러리):
- "X 기술 표준" / "Y 라이브러리 비교"
- "벤더 솔루션 조사" / "SDK 비교"

**market 모드** (시장·비즈니스):
- "X 시장 동향" / "Y 경쟁사 분석"
- "비즈니스 모델 조사"

### Default 옵션 권장값 (컨펌 시 메인 에이전트가 제안)

- `--mode`: 발화 신호로 academic/technology/market 자동 추론. 명확하지 않으면 academic.
- `--depth`: medium (default). "빠르게" / "간단히" → shallow, "체계적으로" / "deep dive" → deep.
- `--intensity`: default 는 thorough-tier rigor 를 주는 수준 (검증 rigor 는 별도 `--qa` 축이 아니라 intensity 에서 파생 — CONVENTIONS §1.1). high-stakes 신호 시 intensity 를 adversarial 로 상향.
- `--no-clarify`: off (default — Step 0 Scope Clarification 보존; query 가 모호하면 메인 에이전트가 직접 clarify 후 invoke 가능)

### Override 1순위 — autopilot 우회

- 단발 paper 1편 fetch / paywall 만 — `Agent(자료팀)` 직접 호출
- PDF figure 일괄 추출 — `Agent(자료팀, mode="pdf-extract")`
- 인터넷 reference 그림 검색 — `Agent(자료팀, mode="web-image-search")`
- 기존 research 폴더에 entry 추가만 — `/autopilot-refine`
- `/autopilot-research <args>` slash 직접 입력 — 컨펌 skip 하고 즉시 invoke

> 본 섹션은 `/sync-skills` 가 `<agent-home>/README.md` 운영 룰 안내로 자동 반영.

## Language Rule
- When explaining something to the user, write in Korean.

## Mode Routing

Mode가 (a) Step 2 검색 소스, (b) Step 3 Phase A/B/C 활성, (c) Step 4 보고서 템플릿을 결정한다. 파이프 구조(search → analyze → report)는 세 mode 공통. 미지정 시 query 키워드로 추론(기본 academic), 2개 이상 동시 매치면 Step 1.5 Scope Clarification에서 확정.

- **academic** (default) — 학술 논문 survey. Phase A+B+C 전부. 보고서 9개(`00_briefing` → `08_reading_guide`).
- **technology** — 기술 표준·ecosystem. Phase A+C(B 비활성). 보고서 7개(`00_briefing` → `07_resources`).
- **market** — 시장·경쟁사. Phase A만. 보고서 5개(`00_briefing` → `04_opportunities`).

소스 목록·보고서 세부·키워드 추론/fallback 규칙 전체 → `references/invocation-and-modes.md`.

## Argument Shape

`<query> [--mode academic|technology|market] [--depth shallow|medium|deep] [--intensity direct|quick|standard|strong|thorough|adversarial] [--no-clarify] [--no-figures] [--from search|analyze|report]`

- **query**: research topic / paper title / arXiv ID / PDF path (플래그 제거 후 남은 텍스트).
- **--mode**: 생략 시 academic. query 키워드로 추론 가능.
- **--depth**: `medium` 기본. Phase B loopback·query expansion 라운드 수를 gate.
- **--intensity**: stage graph 선택자이자 검증 rigor 의 유일한 파생원 (별도 `--qa` 축 없음 — CONVENTIONS §1.1). intensity `quick`/`light` 에서는 gate 축소 + fact-checker skip, `standard+` 에서 fact-check 실행, `adversarial` 은 external adversary·claim-verify 추가.
- **--no-clarify** / **--no-figures**: Step 1.5 / Step 3.5 skip.
- **--from**: `search` | `analyze` | `report` 재진입.

플래그별 정확한 의미·default → `references/invocation-and-modes.md`.

## Re-Entry & Resume

호출 자리에서 _발화 + cwd_ 를 검사해 **신규 vs 재진입**을 `--from` 없이 자동 분기한다. `<artifact-root>/research/<topic>/pipeline_state.yaml` 부재 → 신규(Step 1부터), 존재 → 재진입(발화 의도로 `search`/`analyze`/`report` stage 분류 후 재개). 명시적 `--from <stage>`는 그대로 따른다. 한두 줄 정정은 `autopilot-refine`의 영역.

자동 검사 표·발화→stage 분류·자동 컨펌 화면·`pipeline_state.yaml` 스키마 전체 → `references/invocation-and-modes.md`.

## Pipeline Overview (stage 목록)

`search → analyze → report` 3-stage. Decision Defaults(sane default 자동 진행)는 대부분 auto-proceed이며 pause는 mode multi-match·검색 0건 등에 한정.

| Stage | Steps | 내용 | Reference |
|---|---|---|---|
| (intake) | Step 1 · 1.5 | Input Parsing & Validation, Scope Clarification | `references/pipeline-search-analysis.md` |
| search | Step 2 (2a–2e) | Query 확장 → HF pre-fetch → 연구팀 검색 → 검증 → depth-gated expansion 라운드 | `references/pipeline-search-analysis.md` |
| analyze | Step 3 (3a–3e) · 3.5 | Playwright pre-check → Phase A skim / B chaining / C code search → analysis_summary → Web Figure Extraction | `references/pipeline-search-analysis.md` |
| report | Step 4 (4a–4c) | mode별 보고서 생성(academic 9 / technology 7 / market 5) → 편집팀 polish → QA loop | `references/report-generation.md` |
| (close) | Step 5 · 6 | pipeline_summary 작성 → Briefing | `references/summary-and-briefing.md` |

각 Step의 Agent 프롬프트·batch 규칙·QA 표·보고서 템플릿 전문은 위 reference에 verbatim 보존. Decision Logging(게이트별 기록)도 `references/summary-and-briefing.md`.

## Safety Rules
- Do NOT fabricate citations, URLs, or metrics
- Source failure → continue with remaining sources
- (no `--refs` flag — supplementary local materials read from `analysis_project/paper/` if exists; not asked otherwise)
- Rate limits: arXiv ~3s, OpenAlex 10 req/s, S2 1 req/s, Google Scholar 3s + 50/day
- Context protection: each Agent returns ONLY file paths + 3-5 line summary
- Context budget: deep 모드에서 오케스트레이터 context가 누적됨 (쿼리 확장 라운드 + 스키밍 배치 + loopback). Agent 결과는 항상 파일로 저장하고 요약만 context에 유지. search_results.json 전체를 context에 올리지 않고 paper count + top-5만 참조.
- MERGE mode 무결성: 제목 fuzzy matching은 lowercase + 구두점 제거 + a/an/the 제거로 정규화. 같은 논문의 discovery_count는 단조 증가만 허용 (감소 금지).
- Playwright 고아 프로세스: 자료팀 호출 전후로 `pkill -f chromium_headless_shell` 실행

## Required Reads

- 옵션 해석(argument/mode/depth/qa), mode별 소스·보고서 세트, Decision Defaults, 재진입·Resume·`pipeline_state.yaml`: `references/invocation-and-modes.md`.
- search·analyze 실행 (Step 1~3.5 — 검색 Agent 프롬프트, Phase A/B/C, Web Figure Extraction): `references/pipeline-search-analysis.md`.
- 보고서 생성 (Step 4 — mode별 보고서 템플릿 전문, 편집팀 polish, QA loop 표/프롬프트): `references/report-generation.md`.
- 종료 (Step 5·6 — pipeline_summary 템플릿, Briefing) 와 Decision Logging: `references/summary-and-briefing.md`.

## Reference Map

- `references/invocation-and-modes.md`: Argument Parsing, Modes(academic/technology/market 소스·Phase·보고서 세트), Decision Defaults, Context Auto-Detection(신규/재진입), Resume + `pipeline_state.yaml` 스키마.
- `references/pipeline-search-analysis.md`: Pipeline Step 1(Input Parsing)·1.5(Scope Clarification)·2(Source Search 2a–2e)·3(Source Analysis 3a–3e)·3.5(Web Figure Extraction).
- `references/report-generation.md`: Step 4 Report Generation — 4a mode별 보고서 템플릿 전문(9/7/5), 4a-Polish 편집팀 모드 B, 4b QA Loop(reviewer 표·프롬프트), 4c Status Check.
- `references/summary-and-briefing.md`: Step 5 Pipeline Summary 템플릿, Step 6 Briefing, Decision Logging.

## Task
$ARGUMENTS
