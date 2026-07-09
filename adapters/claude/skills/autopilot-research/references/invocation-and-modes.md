## Argument Parsing
Parse `$ARGUMENTS` for optional flags:

- **query**: research topic, paper title, arXiv ID, or PDF path (remaining text after flags)
- **--mode**: `academic` (default) | `technology` | `market` — investigation type (see Modes below)
- **--depth**: `shallow` | `medium` (default) | `deep`
- (no `--refs` flag — local reference materials should be pre-processed via `/analyze-project --mode paper` first → output goes to `<artifact-root>/analysis_project/paper/` which autopilot-research auto-detects)
- **--qa**: `quick` | `light` | `standard` | `thorough` | `adversarial` — assurance budget only. `intensity` selects the stage graph/depth; `--qa` scales selected report checks. `quick` keeps the selected gate small and disables fact-checker by default. source/fact-check runs only when claims/citations/cards are in scope and the selected graph/QA budget calls for it. `adversarial` adds external adversary / **claim-verify** where supported.
- **--from**: `search` | `analyze` | `report` — resume the pipeline at a specific stage (see Resume below)
- **--no-clarify**: skip Step 0 Scope Clarification (force-run with current query as-is)
- **--no-figures**: skip Step 3.5 Web Figure Extraction (figure 자동 추출 단계 건너뜀; cards 본문은 그대로 생성, 단 `**Figures**:` 줄만 누락)

## Modes

The mode determines (a) search sources used in Step 2, (b) Phase A/B/C activation in Step 3, and (c) report templates in Step 4. The pipeline structure (search → analyze → report) is the same across modes.

### `--mode academic` (default)
**Use when**: 학술 논문 중심 조사 (deep learning method survey, 알고리즘 비교, 분야 trend).
- **Search sources**: arXiv, Semantic Scholar, OpenAlex, Hugging Face paper_search, Google Scholar
- **Phases**: A (skimming) + B (reference chaining) + C (code & model search) — 모두 활성
- **Reports**: 9개 (briefing → landscape → core_papers → baselines → technical_deep_dive → datasets → implementation → resources → reading_guide)

### `--mode technology`
**Use when**: 산업 표준·기술 ecosystem 조사 (코덱/프로토콜, 표준 문서, vendor 솔루션 비교, 배포 고려사항).
- **Search sources**: WebSearch (industry blogs, technical whitepapers, vendor docs), WebFetch (standards orgs: 3GPP / ITU-T / IEEE / W3C), arXiv (보조), Hugging Face (관련 모델)
- **Phases**: A (full skim of standards + whitepapers) — 활성. B (reference chaining) — 약화 (academic citation 그래프가 의미 약함). C (code search) — 활성 (open-source 구현체).
- **Reports** (7개):
  - `00_briefing.md` — Executive briefing
  - `01_landscape.md` — Technology landscape (categories, players, lineage)
  - `02_standards.md` — Standards & specs (3GPP/ITU-T/IEEE/RFC numbers, key sections)
  - `03_vendor_comparison.md` — Vendor / solution comparison (Qualcomm vs Samsung vs Apple vs ...)
  - `04_technical_deep_dive.md` — Algorithm·protocol details
  - `05_deployment.md` — Deployment considerations (latency, cost, integration paths)
  - `06_implementation.md` — Goal-adaptive roadmap (existing template, build/adopt 우선)
  - `07_resources.md` — Open-source code, model weights, evaluation tools

### `--mode market`
**Use when**: 시장 동향·경쟁사·analyst report 조사 (제품/서비스 시장 사이즈, key players, 채택률).
- **Search sources**: WebSearch (analyst content, news, earnings reports, press releases), WebFetch (company sites, investor pages)
- **Phases**: A (skim of market reports + news) — 활성. B / C — 비활성 (학술 검색 X, 코드 검색 X).
- **Reports** (5개):
  - `00_briefing.md` — Executive briefing
  - `01_market_overview.md` — Market sizing, segmentation, growth rate
  - `02_key_players.md` — Competitor profiles, market share, positioning
  - `03_trends.md` — Trends, drivers, inhibitors, disruptors
  - `04_opportunities.md` — Opportunity assessment + actionable recommendations

> Mode 미지정 시 query 키워드로 추론 — "논문/algorithm/method/SOTA" → academic, "표준/codec/protocol/3GPP/ITU/chip/MCU" → technology, "market/시장/competitor/analyst" → market.
> **Fallback**: 어느 키워드도 매치되지 않으면 → `academic` (한 줄 통보: "키워드 매칭 실패 → academic으로 진행. 다른 모드는 --mode 명시").
> **Multi-match (>=2 modes 동시 매치)**: Step 0 Scope Clarification에서 사용자에게 확정 질문.

## Decision Defaults (no autonomy gating)

The pipeline auto-proceeds with sane defaults. There is no autonomy-level dial. Pause points are limited to:

| Decision Point | Default Behavior |
|---|---|
| Search results review | Auto-proceed. |
| Query expansion rounds | Auto-proceed. |
| Phase B loopback | Auto-proceed up to the depth-gated limit. |
| External material discovery | If `analysis_project/paper/` exists in current dir, auto-include as supplementary input. If user expects external materials but none found → suggest `/analyze-project --mode paper` first. |
| Search returned 0 papers | Auto-stop with `pipeline_summary(failed)` (no useful continuation possible). |
| Report generation | Auto-proceed. |

## Context Auto-Detection (신규 vs 재진입 자동 분기)

본 skill 은 호출 자리에서 _발화 + cwd_ 검사로 자동 분기 — `--from` 명시 없이도 동작:

### 1단계 — research/<topic>/ 자동 검사

| 감지 조건 | 처리 |
|---|---|
| `<artifact-root>/research/<topic>/pipeline_state.yaml` 부재 (또는 fuzzy match 0) | **신규** — Step 1 (Input Parsing) 부터 처음 |
| `<artifact-root>/research/<topic>/pipeline_state.yaml` 존재 (fuzzy match 1+) | **재진입** — `last_completed_stage:` read + 발화 의도 분류 후 해당 stage 부터 |

`<topic>` 추출 — 발화 키워드 fuzzy match (예: `"speech enhancement 분야 재조사"` → topic=speech-enhancement). 다중 매치 시 사용자 컨펌.

### 2단계 — 발화 → stage 자동 분류 (재진입 자리)

| 발화 신호 | 추론 stage | 흐름 |
|---|---|---|
| "X 재조사" / "최근 paper 추가" / "search 다시" | `--from search` (Step 2 부터) | 새 쿼리·확장 라운드 + 기존 cards 병합 |
| "분석 다시" / "Phase B reference chaining 다시" / "card 보강" | `--from analyze` (Step 3 부터) | 기존 search 결과 위 Phase A/B/C 재실행 |
| "보고서 갱신" / "report 다시" / "06_implementation 자리 수정" | `--from report` (Step 4 부터) | 기존 cards / analysis_summary 위 보고서 재작성 |

### 3단계 — 자동 컨펌 한 화면

```
=== autopilot-research 호출 자리 ===
topic: <name>
산출물: research/<name>/ (발견 — last_completed_stage: <stage>) 또는 (부재 — 신규)
발화: "<사용자 한 줄>"
→ 추론: <신규 / --from <stage>> 자리

진행? (진행 / 다른 stage 로 / 새 topic 으로 / 중단)
```

신규 vs 재진입 분류는 _명시 옵션 없이도_ 동작 — 발화 + cwd 자동 판단. 사용자가 명시적 `--from <stage>` 입력하면 그대로.

> **cross-artifact 정정 자리 (research 산출물의 자잘한 정정)** 는 `autopilot-refine` 의 영역 — 본 skill 의 _재진입_ 은 _stage 단위 재실행_ 자리. 한 두 줄 정정은 autopilot-refine.

## Resume (`--from`)

`--from <stage>` re-enters an existing artifact directory and runs from that stage onward. Stages:
- `search` — Step 2 (Paper Search)
- `analyze` — Step 3 (Phase A skimming + B chaining + C code search + analysis_summary)
- `report` — Step 4 (Report Generation + selected report-check gate)

When `--from` is used, the positional argument should be either the artifact directory path or a fuzzy-matchable topic name. The orchestrator resolves it via `ls -d <artifact-root>/research/*$ARG* 2>/dev/null`. Read `pipeline_state.yaml` to recover `query`, `mode`, `depth`, `qa_level`, `clarified_intent`. CLI flags override stored values. Step 0 Scope Clarification is always skipped on resume (already captured in first run).

### pipeline_state.yaml

Written/updated at `{artifact_dir}/pipeline_state.yaml` after each completed stage:

```yaml
pipeline: autopilot-research
query: <original query>
mode: academic                   # academic | technology | market (resolved at Step 1)
depth: medium
qa_level: standard
clarified_intent: <string or null>    # Step 0 output (if Clarification ran)
last_completed_stage: analyze    # one of: clarify, search, analyze, report
artifact_dir: <abs path>
```
