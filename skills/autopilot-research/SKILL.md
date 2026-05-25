---
name: autopilot-research
description: "Research survey pipeline — multi-mode investigation (academic / technology / market). Mode-specific search sources and report templates. Field intelligence only; no PPT/paper drafts. Hand off to autopilot-draft (writing/slides) or autopilot-code (build) for actual document/code creation."
argument-hint: "<query> [--mode academic|technology|market] [--depth shallow|medium|deep] [--qa quick|light|standard|thorough|adversarial] [--no-clarify] [--no-figures] [--from search|analyze|report]"
---

> **산출물 폴더 컨벤션**: [CONVENTIONS.md §5](../../CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier: T1 root / T2 named subdir / T3 `_internal/`). 본 skill의 raw metadata (`search_results.json`, `phase_a_*.json`, `chaining_results.md`, `code_search.md` 등) + reviews는 모두 `_internal/` 하위로 격리. T1/T2 chapter 파일과 `cards/`는 root.

## Default Invocation Rule (메인 Claude 자동 라우팅)

본 skill 은 글로벌 [`CLAUDE.md`](../../CLAUDE.md) §6 "autopilot-* 호출 패턴" 의 _컨펌 의무_ 적용 대상. 메인 Claude 가 사용자 발화에서 아래 trigger 신호를 인지하면, 옵션 자동 구성 + 자연어 요약 컨펌 거쳐 invoke.

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

### Default 옵션 권장값 (컨펌 시 메인 Claude 가 제안)

- `--mode`: 발화 신호로 academic/technology/market 자동 추론. 명확하지 않으면 academic.
- `--depth`: medium (default). "빠르게" / "간단히" → shallow, "체계적으로" / "deep dive" → deep.
- `--qa`: thorough (default — global §6 high-stakes 신호 시 adversarial 자동 상향)
- `--no-clarify`: off (default — Step 0 Scope Clarification 보존; query 가 모호하면 메인 Claude 가 직접 clarify 후 invoke 가능)

### Override 1순위 — autopilot 우회

- 단발 paper 1편 fetch / paywall 만 — `Agent(자료팀)` 직접 호출
- PDF figure 일괄 추출 — `Agent(자료팀, mode="pdf-extract")`
- 인터넷 reference 그림 검색 — `Agent(자료팀, mode="web-image-search")`
- 기존 research 폴더에 entry 추가만 — `/autopilot-refine`
- `/autopilot-research <args>` slash 직접 입력 — 컨펌 skip 하고 즉시 invoke

> 본 섹션은 `/sync-skills` 가 `~/.claude/README.md` 운영 룰 안내로 자동 반영.

## Language Rule
- When explaining something to the user, write in Korean.

## Argument Parsing
Parse `$ARGUMENTS` for optional flags:

- **query**: research topic, paper title, arXiv ID, or PDF path (remaining text after flags)
- **--mode**: `academic` (default) | `technology` | `market` — investigation type (see Modes below)
- **--depth**: `shallow` | `medium` (default) | `deep`
- (no `--refs` flag — local reference materials should be pre-processed via `/analyze-project --mode paper` first → output goes to `.claude_reports/analysis_project/paper/` which autopilot-research auto-detects)
- **--qa**: `quick` | `light` | `standard` | `thorough` (default) | `adversarial` — QA 5 단계 정의 + 모델·round 매트릭스는 [`CONVENTIONS.md §1`](../../CONVENTIONS.md#1-qa-levels-canonical) 단일 source. `quick` 은 1라운드 강제 종료 + refine skip + fact-checker 비활성. `standard`+ 는 fact-checker (sonnet, parallel) 가 cards verbatim 대조 (citation/venue/year/metric). `adversarial` 은 thorough + Codex external review (camera-ready / public report 같은 외부 strong scrutiny 자리).
- **--from**: `search` | `analyze` | `report` — resume the pipeline at a specific stage (see Resume below)
- **--no-clarify**: skip Step 0 Scope Clarification (force-run with current query as-is)
- **--no-figures**: skip Step 3.5 Web Figure Extraction (figure 자동 추출 단계 건너뜀; cards 본문은 그대로 생성, 단 `**Figures**:` 줄만 누락)

## Modes

The mode determines (a) search sources used in Step 2, (b) Phase A/B/C activation in Step 3, and (c) report templates in Step 4. The pipeline structure (search → analyze → report) is the same across modes.

### `--mode academic` (default)
**Use when**: 학술 논문 중심 조사 (deep learning method survey, 알고리즘 비교, 분야 trend).
- **Search sources**: arXiv, Semantic Scholar, OpenAlex, Hugging Face paper_search, Google Scholar
- **Phases**: A (skimming) + B (reference chaining) + C (code & model search) — 모두 활성
- **Reports**: 9개 (briefing → landscape → core_papers → baselines → technical_deep_dive → datasets → implementation → resources → reading_guide) — 현행 동일

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

## Resume (`--from`)

`--from <stage>` re-enters an existing artifact directory and runs from that stage onward. Stages:
- `search` — Step 2 (Paper Search)
- `analyze` — Step 3 (Phase A skimming + B chaining + C code search + analysis_summary)
- `report` — Step 4 (Report Generation + QA loop)

When `--from` is used, the positional argument should be either the artifact directory path or a fuzzy-matchable topic name. The orchestrator resolves it via `ls -d .claude_reports/research/*$ARG* 2>/dev/null`. Read `pipeline_state.yaml` to recover `query`, `mode`, `depth`, `qa_level`, `clarified_intent`. CLI flags override stored values. Step 0 Scope Clarification is always skipped on resume (already captured in first run).

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

## Pipeline

### Step 1: Input Parsing & Validation
- Detect query type: keyword, paper title, arXiv ID, PDF path, folder path
- Resolve `--mode`: explicit flag value, or infer from query keywords (academic / technology / market — see Modes section). Notify user of inferred mode in one line. Multi-match → defer resolution to Step 1.5 Scope Clarification.
- Auto-detect supplementary input: if `.claude_reports/analysis_project/paper/` exists in current dir, include as supplementary input for chaining. If user explicitly requested "use my local PDFs" but no `analysis_project/paper/` → suggest running `/analyze-project --mode paper` first.
- Construct topic name (sanitize: lowercase, hyphens, max 30 chars)
- Set artifact_dir: `.claude_reports/research/{topic}/`
- `mkdir -p {artifact_dir}` (only AFTER validation)

### Step 1.5: Scope Clarification (사전 조율) — skipped if `--no-clarify` or `--from`
**Purpose**: 모호한 query는 mode 선택과 검색 폭을 잘못 잡아 9/7/5개 보고서 출력이 무용지물이 됨. 모호 detection 시 사용자에게 2-4 sharp question을 던진다.

**Trigger conditions** (any one matches → run):
- Mode multi-match (≥2 modes 동시 매치)
- Query 길이 < 50 Korean chars 또는 < 12 English words AND no specific constraint (예: time range, specific platform, target metric)
- Query에 "조사/분석/survey" 같은 메타 키워드만 있고 구체적 deliverable·범위 없음

**Mode-specific question seed**:
- `academic`: 조사 깊이(--depth 명시 의도?), 필독 컷오프(citation > N or year ≥ Y), 분야 경계(예: speech only? including audio in general?)
- `technology`: 대상 표준 그룹/년도, 배포 환경(production/research), vendor 범위, 비교 축(performance/cost/license 우선순위)
- `market`: 지역/시간 범위, 경쟁자 명시 여부, 의사결정 목적(투자 판단? 진출 결정? competitive intel?)

**Skip 조건**:
- `--no-clarify` 명시
- `--from <stage>` 재개 (이미 캡처됨)
- Query 길이 ≥ 50 Korean chars 또는 ≥ 12 English words AND mode 명확

**Output**: 사용자 답변을 통합한 refined query를 Step 2로 전달 + `pipeline_state.yaml`의 `clarified_intent` 필드에 한 줄 요약 기록.

**§5 자율 진행**: 질문 던질 때 글로벌 [CLAUDE.md](../../CLAUDE.md) §5 적용 — ScheduleWakeup 15-20분 동시 호출, 답 없으면 mode 추론 결과 + depth medium + 가장 좁은 범위 default 로 자율 진행.

### Step 2: Source Search (direct Agent call) — mode-aware

> **Search source selection per mode**:
> - `academic`: arXiv + Semantic Scholar + OpenAlex + Hugging Face paper_search + Google Scholar (현행)
> - `technology`: WebSearch (industry blogs, vendor whitepapers) + WebFetch (3GPP/ITU-T/IEEE/W3C standards pages) + arXiv (보조) + Hugging Face (관련 모델)
> - `market`: WebSearch (analyst content, news, press releases) + WebFetch (company sites, investor pages). **arXiv·Semantic Scholar·OpenAlex 비활성**.

#### Step 2a: 초기 쿼리 확장 (LLM 지식 기반)
오케스트레이터가 사용자 쿼리로부터 **2~3개 동의어/대체 표현**을 생성한다.
목적: 같은 분야인데 다른 이름으로 불리는 연구를 첫 검색부터 포함.
(예: "user-defined keyword spotting" → + "query-by-example KWS", "personalized wake word detection")
`queries = [original_query, variant_1, variant_2]`

> Step 2e의 **논문 기반 확장**과 다름: 2a는 LLM 사전 지식으로 동의어 생성, 2e는 실제 발견된 논문에서 새 키워드 추출.

#### Step 2b: HF MCP Pre-Fetch
Before invoking the agent, attempt HF `paper_search` for all queries:
- For each query in `queries`: call `paper_search` and collect results
- If successful: store combined as `hf_results_json`
- If MCP unavailable or fails: `hf_results_json = null`, note in pipeline log

#### Step 2c: Invoke Agent
```
Agent(subagent_type="연구팀"):
  "Research survey mode: Paper search.
   Queries: {queries_list}
   Original query: {original_query}
   Query type: {detected_type}
   Output directory: {artifact_dir}
   **Routing**: All raw metadata files (search_results.json, phase_a_*.json, access_classification.json, browser_extracts/) → write to `{artifact_dir}/_internal/`. T1/T2 deliverables (cards/, chapter .md files, analysis_summary.md) → root `{artifact_dir}/`. mkdir -p `_internal` before first write if absent.
   Max results per source per query: 10
   {If analysis_project/paper/ available: 'Supplementary local paper analysis: {artifact_dir}/../analysis_project/paper/'}
   {If hf_results_json: 'HF paper_search results (pre-fetched): {hf_results_json}'}
   Timeout rule: If any single source takes >3 minutes, skip it and proceed to the next.

   ## search_results.json Schema
   {
     "query": "string", "date": "YYYY-MM-DD", "sources_used": ["string"],
     "total_papers": int,
     "papers": [{"title": "string (required)", "authors": ["string"],
       "year": int|null, "citation_count": int|null,
       "discovery_count": int (required, >=1), "sources": ["string"],
       "arxiv_id": string|null, "oa_url": string|null,
       "openalex_id": string|null, "referenced_works": ["string"]|null,
       "venue": string|null, "venue_tier": int|null (1-4), "raw_type": string|null,
       "url": string|null (landing page URL from any source — used by 자료팀 for paywall access)}]
   }

   ## Google Scholar HTML Parsing Patterns
   - Split blocks: <div class='gs_r gs_or gs_scl'>
   - Title: strip tags from <h3> content
   - Year: , (\d{4})\s*[-–] pattern (leading comma required)
   - Citation: >Cited by (\d+)< pattern

   Follow your Role 2a procedure. Return file paths + 3-5 line Korean summary."
```

#### Step 2d: Post-Search Validation
1. Read `{artifact_dir}/_internal/search_results.json`
2. Verify valid JSON — if parse fails, re-invoke Agent once: "Your search_results.json was invalid. Fix and rewrite."
3. Verify `papers` array non-empty, each paper has `title`
4. If still fails after retry: pipeline_summary(failed) → STOP
5. If `total_papers == 0`: pipeline_summary(failed, "검색 결과 0건") → STOP

**Error handling**: If Agent call fails or returns no output → pipeline_summary(failed) → STOP.

#### Step 2e: Query Expansion Rounds (depth-gated)
발견된 논문의 제목/키워드에서 새로운 검색어를 추출하여 추가 검색 라운드를 실행한다.

**라운드 제어** (depth 파라미터):
- `shallow`: 추가 라운드 없음 (Round 1만)
- `medium`: 최대 1회 추가 라운드 (Round 1 → keyword 추출 → Round 2)
- `deep`: 최대 2회 추가 라운드 (Round 1 → Round 2 → Round 3)

**각 라운드 절차**:
1. 오케스트레이터가 `search_results.json`의 논문 제목들을 읽고, 빈출 키워드/새로운 용어를 추출
   (예: Round 1에서 "query-by-example", "metric learning", "prototypical network"가 반복 등장)
2. 기존 쿼리에 없는 새 키워드로 2~3개 추가 쿼리 생성
3. 새 쿼리만으로 연구팀 재호출 (기존 쿼리 재검색 안 함):
   ```
   Agent(subagent_type="연구팀"):
     "Research survey mode: Paper search.
      Queries: {new_queries_only}
      Original query: {original_query} (for context, do NOT re-search)
      Output directory: {artifact_dir}
      **Routing**: raw metadata → `{artifact_dir}/_internal/` (search_results.json, etc.).
      Max results per source per query: 10
      MERGE mode: append to existing _internal/search_results.json — update discovery_count for duplicates, add new papers.
      ..."
   ```
4. 병합 후 Post-Search Validation 재실행
5. 새 논문이 3편 미만이면 → 라운드 종료 (수렴)

**수렴 조건** (일찍 끝나는 경우):
- 추가 라운드에서 새 논문 < 3편 → 더 이상 확장하지 않음
- 새 키워드를 추출할 수 없음 (기존 쿼리와 동일) → 종료

Auto-proceed after expansion rounds (no user gate).

### Step 3: Source Analysis (direct Agent calls) — mode-aware

> **Phase activation per mode**:
> - `academic`: Phase A (skim) + B (reference chaining) + C (code/model search) — 모두 활성
> - `technology`: Phase A (full skim of standards + whitepapers) — 활성. Phase B (reference chaining) — **비활성** (academic citation graph가 의미 약함). Phase C — 활성 (open-source 구현체 탐색)
> - `market`: Phase A (skim of market reports + news) — 활성. Phase B / C — **비활성**

#### Step 3a: Playwright Pre-Check + 자료팀 Pre-Fetch
```
Bash: python3 -c "from playwright.async_api import async_playwright; print('OK')"
Bash: ls ~/.cache/ms-playwright/chromium_headless_shell-*/ > /dev/null 2>&1 && echo 'BROWSER_OK'
```
Set `playwright_available = true/false`.

If `playwright_available == true`:
  Read `_internal/search_results.json` and identify paywall papers (no arXiv ID AND no oa_url → likely paywall).
  If paywall papers exist, invoke 자료팀 to pre-fetch their content:
  ```
  Agent(subagent_type="자료팀"):
    "Mode: browser-fetch
     URLs: {paywall_url_list}
     Output directory: {artifact_dir}
     Extract full text from each URL. Write to `_internal/browser_extracts/{filename}.txt` (T3 raw metadata).
     Return summary of successes and failures."
  ```
  The extracted texts will be available for 연구팀 to Read during Phase A skimming.
  If 자료팀 fails or playwright unavailable: proceed without — 연구팀 will fall through to abstract-only.

#### Step 3b: Phase A — Parallel Skimming Batches
Read `_internal/search_results.json`. Classify each paper's access type FIRST:
- **accessible**: has `arxiv_id` OR `oa_url` OR matching file in `_internal/browser_extracts/`
- **paywall-only**: no `arxiv_id`, no `oa_url`, no browser extract → abstract/metadata only

Construct batches (accessible papers only get full-read treatment):
- Full-read accessible (citations > 10 AND not null AND accessible): 1 paper per Agent call
- Abstract-only (citations <= 10 OR null OR paywall-only): up to 10 per Agent call
- **Exception**: `discovery_count >= 3` AND accessible → upgrade to full-read (1 per call)
- **Paywall-only papers**: always go in abstract-only batches regardless of citation count
  (attempting WebFetch on paywall sites causes timeout/hang — never do this)

For each batch:
```
Agent(subagent_type="연구팀"):
  "Research survey mode: Paper analysis.
   Papers: {batch_json}
   Output directory: {artifact_dir}
   Supplementary inputs (if any): `{artifact_dir}/../analysis_project/paper/` (use if exists, otherwise none)
   Browser extracts: {artifact_dir}/_internal/browser_extracts/ (pre-fetched by 자료팀, if available)

   Per-paper timeout: 60s. Batch budget: 10min. WebFetch 3xx loop / empty response → skip.
   Paywall / Access priority / browser_extracts handling: per your Role 2b 본문 (paywall fast-detect + 60s timeout + 5-tier access ladder + 자료팀 분리 원칙) — single source 거기.

   Follow your Role 2b procedure. Return file paths + Korean summary."
```
Launch batches in parallel. **Error handling**: Individual batch failure → log and continue. Total failure (0 batches succeed) → pipeline_summary(failed) → STOP.

#### Step 3c: Phase B — Reference Chaining (depth-gated)
If `depth == shallow`: SKIP Phase B entirely.
```
Agent(subagent_type="연구팀"):
  "Research survey mode: Reference chaining.
   Paper cards: {artifact_dir}/cards/
   Search results: {artifact_dir}/_internal/search_results.json
   Depth: {depth}
   Output: {artifact_dir}/_internal/chaining_results.md
   Follow your Role 2b reference chaining procedure. Return file paths + Korean summary."
```

**Loopback control** (orchestrator responsibility):
1. Parse `chaining_results.md` → extract papers with `reference_frequency >= 2`
2. If new papers exist AND loopback_count < limit (medium: 1, deep: 2):
   - Construct Phase A batches for new papers only (top 10)
   - Invoke additional skimming Agent calls
   - Increment loopback_count
   - Re-invoke Phase B for further chaining
3. When limit reached or no new papers → proceed to Phase C

#### Step 3d: Phase C — Code & Model Search
```
Agent(subagent_type="연구팀"):
  "Research survey mode: Code and model search.
   Paper cards: {artifact_dir}/cards/
   Output: {artifact_dir}/code_resources/
   Aggregate: {artifact_dir}/_internal/code_search.md
   Follow your Role 2c procedure. Return file paths + Korean summary."
```

#### Step 3e: Compile analysis_summary.md
```
Agent(subagent_type="연구팀"):
  "Research survey mode: Compile analysis summary.
   Compile from: cards/, _internal/chaining_results.md (if exists), _internal/code_search.md (if exists).
   Set phase flags: chaining_available, code_search_available.
   Output: {artifact_dir}/analysis_summary.md
   Return file path + Korean summary."
```

#### Step 3 Status Check
Read `{artifact_dir}/analysis_summary.md`.
- Not exists or 0 papers → pipeline_summary(failed) → STOP
- Depth-aware: `shallow` + `chaining_available == false` + `code_search_available == true` → **done** (intentional skip)
- Otherwise partial flags → **partial**, warn user, proceed

### Step 3.5: Web Figure Extraction (옵션, accessible paper 대상)

Phase A skimming 직후 cards/{paper}.md가 작성되면, _accessible 분류_ paper의 figure를 web에서 자동 추출.

**Scope**:
- 대상 = `accessible` 분류 paper (Step 3b 정의: `arxiv_id` OR `oa_url` OR `_internal/browser_extracts/{filename}.txt` 존재)
- paywall-only paper는 skip (figure도 마찬가지로 접근 불가)

**Procedure** (자료팀 호출):
```
Agent(subagent_type="자료팀"):
  Mode: web-image-search
  Paper list: [{arxiv_id, paper_id (cards filename without .md), title}, ...]
  Output dir: {artifact_dir}/figures/
  Workflow per paper:
    1. ar5iv URL 시도: https://ar5iv.labs.arxiv.org/html/{arxiv_id}
       → WebFetch 또는 Playwright로 HTML 페이지 fetch (5s timeout)
       → BeautifulSoup 또는 정규식으로 <img src="..."> 또는 <figure> 태그 파싱
       → 각 figure URL을 image binary 다운로드 (정상 figure만, 아이콘/로고 제외 — 200×200 minimum)
       → save as {paper_id}_fig{N}.png
    2. ar5iv 실패 시 (페이지 없음 또는 figure 0개) → arxiv-vanity fallback (https://www.arxiv-vanity.com/papers/{arxiv_id}/)
    3. 둘 다 실패 시 → arxiv PDF fallback: https://arxiv.org/pdf/{arxiv_id}
       → wget/curl로 PDF 다운로드 (_internal/raw_pdfs/ 임시 저장) → pdfimages -png 추출 → {paper_id}_fig{N}.png
       → PDF 임시 파일 삭제 (token/storage 절감)
    4. 모두 실패 시 → 해당 paper figure 0개로 기록
  Output:
    - {artifact_dir}/figures/{paper_id}_fig*.png (paper마다 N개)
    - {artifact_dir}/figures/figure_index.md (paper × figure path 매핑)
```

**cards 갱신**: 각 cards/{paper}.md 헤더 frontmatter 또는 `## Reference` 섹션 직후에 `**Figures**: ../figures/{paper_id}_fig1.png · ../figures/{paper_id}_fig2.png ...` 한 줄 추가. figure 0개면 `**Figures**: (none extracted)` 표시.

**Caveats**:
- ar5iv는 _대부분의 arxiv paper 지원_이지만 _최근 2024-26 paper 일부_는 지원 안 됨 — PDF fallback 자동 발동.
- Vector figure는 ar5iv에서 SVG/PNG로 자동 raster 변환되어 양호. PDF fallback은 raster figure만 (vector PDF figure는 미인식).
- _저작권_: 학술 paper figure 인용은 _발표·문서 fair use_ 영역. 본 추출 결과는 _연구 reference_로만 사용, 외부 배포 시 출처 명시 필요.
- 추출 figure 품질 변동 — 사용자 polish 또는 직접 캡처가 더 적합한 경우 다수.

**Skipping**:
- `--qa quick` mode에서는 Step 3.5 자동 skip (fastest path 우선).
- `--no-figures` flag 명시 시 skip.

### Step 4: Report Generation (direct Agent call + QA loop)

> **자료팀 위임 (옵션)** — 보고서에 _집계 통계 시각화_ 나 _cross-card metric 비교 plot_ 등 _custom 분석 figure_ 가 필요하면 본 Step 안에서 `Agent(자료팀, "<spec>")` 직접 호출 가능. paper figure 직접 추출 (자료팀 영역) 과 다른 자리 — 자료팀은 _카드 데이터로부터 새 시각화_ 만들 때. 일반 survey 자료 (taxonomy table / lineage ASCII / per-paper card) 는 연구팀 본 자리 처리. (2026-05-22 신설.)

#### Step 4a: Generate Reports
```
Agent(subagent_type="연구팀"):
  "Research survey mode: Report generation.
   Analysis directory: {artifact_dir}
   Topic: {topic}
   Output directory: {artifact_dir}
   **Routing**: T1/T2 chapter files (00_briefing.md ~ NN_*.md, analysis_summary.md) → root `{artifact_dir}/`. Reviews/raw metadata are written elsewhere by other steps — do not touch _internal/ here.
   Date: {YYYY-MM-DD}

   ## Source Files to Read
   - analysis_summary.md (MUST READ — taxonomy, core papers, themes, evolution, gaps)
   - _internal/chaining_results.md (foundational dependencies, if exists)
   - _internal/code_search.md (code/model resources)
   - _internal/search_results.json (paper metadata)
   - Read key card files from cards/ (at least top 15-20 by discovery_count)

   ## Report Structure (mode-specific)

   The report set differs per mode. Common rules across all modes:
   - **Korean prose** (default). autopilot-research 의 보고서는 _한국어 사용자가 직접 읽고 검토_ 하는 산출물이라 _주 언어 한국어 단일_ 이 자연. 사용자가 task description 에서 _영문 보고서_ 를 명시한 경우만 영문 산출.
   - Technical terms stay in English (논문 제목·저자·학회·모델·약자·지표 영어 그대로) — 한국어 본문 + 영문 도메인 용어 혼합 (판교체 와 다름: 판교체는 _한국어로 자연스럽게 쓸 수 있는_ 일반 명사를 굳이 영어로 박는 패턴).
   - Save each report file to root `{artifact_dir}/{filename}.md`. _internal/en/ 같은 분리 경로 안 씀 — 단일 산출.
   - Every comparison table ends with bold **Takeaway** line
   - Numbers/claims sourced only from analysis_summary / cards — NO fabrication
   - Cross-references via `[text](filename.md)` (same-directory link).

   ### Mode `academic` (default) — 9 files

   ### 00_briefing.md — Executive Briefing
   - **Level 0** (1 line): 한 문장 요약
   - **Level 1** (3-5 lines): 핵심 발견 요약
   - **Level 2** (1 page):
     - Mermaid paper relationship diagram (`graph TD`, styled key nodes, 4 subgraphs: Backbone/QbE/QbT/On-Device)
     - Research axes table: axis | description | key papers | paper count
     - Key findings (numbered, 5-7 items)
     - Recommended architecture stack (ASCII pipeline: input → feature → encoder → matching → output)
     - Model size spectrum (ASCII: MCU→Edge→GPU→Server with params and best metric per tier)
   - **Level 3**: 전체 보고서 가이드 table (file | content | key question answered)

   ### 01_landscape.md — Research Landscape
   - Problem definition (formal: few-shot, zero-shot, open-set variants)
   - 3D taxonomy: enrollment method (audio/text/multi-modal) × learning paradigm (metric/contrastive/classification/KD/meta) × architecture (CNN/Conformer/Hybrid/MLP)
   - Temporal evolution table: period | key transition | representative papers
   - Research axes detailed breakdown with paper counts
   - Enrollment method comparison (QbE vs QbT vs Multi-modal, with paper lists per category)

   ### 02_core_papers.md — Core Paper Analysis
   - Grade classification: **필독** (DC>=5 or CC>100), **정독** (DC>=3 or CC>30), **참조** (rest)
   - Paper lineage diagrams (ASCII: metric learning lineage, phoneme matching lineage, multi-modal lineage)
   - Per-paper detailed cards for 필독+정독:
     authors | venue/year | DC/CC | code link | core insight | architecture (diagram if possible) | key results table | limitations | connections
   - 참조 grade: compact table only (title | year | contribution | params)

   ### 03_baselines.md — Benchmark Comparison Tables
   Tables (each ending with bold **Takeaway** line):
   1. GSC closed-set (12-class): model/year/acc-v1/acc-v2/params/MACs/latency/code
   2. LibriPhrase text-enrollment: model/year/EER-Easy/EER-Hard/AUC-Easy/AUC-Hard/params/code
   3. splitGSC few-shot open-set: model/backbone/params/5-shot-acc/AUROC/code
   4. Zero-shot audio enrollment: model/size-quant/AUC/EER/training-data/code
   5. Continuous speech KWS: model/keywords/recall@2FA-clean/other/speed
   6. Multilingual UD-KWS: model/params/languages/metric/score/code
   7. On-device deployment: model/year/platform/params/power/accuracy/method
   8. Model size spectrum ASCII (MCU→Server with params and best metric at each tier)
   - Only include numbers directly from card files — NO fabrication

   ### 04_technical_deep_dive.md — Technical Deep Dive
   - 5-8 technology themes, each with: problem definition → approach comparison table → key insight
     Expected themes: phoneme-level supervision, audio-text modality gap, metric/contrastive losses, KD for lightweight, open-set rejection, streaming detection, data augmentation/synthesis
   - Loss function comparison table (MANDATORY): loss | papers | mechanism | pros | cons | best-for
   - Closing section: **미해결 과제와 연구 기회** (5-8 gaps with difficulty/impact ratings + solution directions)

   ### 05_datasets.md — Dataset Specifications
   - Primary benchmarks (detailed field/value tables): GSC v1/v2 (+ splitGSC split details), LibriPhrase (+ key eval numbers), Qualcomm KWSD, Hey-Snips
   - Training datasets: MSWC, LibriSpeech, VoxCeleb, WenetPhrase, Common Voice
   - Each dataset: year/size/speakers/keywords/language/access URL/license/usage count
   - Noise/augmentation datasets table
   - Dataset usage map (ASCII diagram: training datasets → evaluation benchmarks)
   - Recommended benchmark combination table: scenario → datasets → metrics

   ### 06_implementation.md — Goal-Adaptive Action Roadmap
   First **infer the user's primary goal** from the original query and select the matching template. Always state the inferred goal at the top of the file (`> Inferred goal: {goal} — {one-line rationale}`). If ambiguous, default to **build** but log the assumption.

   **Goal detection cues** (non-exhaustive, infer from `original_query`):
   - **build** — "구현", "implement", "develop", "build a system", "재현", "프로젝트" → code/system implementation
   - **seminar** — "세미나", "발표", "lecture", "presentation", "slides", "talk" → talk/slide preparation
   - **write** — "논문 작성", "survey 쓰기", "review writing", "thesis" → paper/survey writing
   - **research** — "연구 방향", "research direction", "open problem", "hypothesis", "what's next" → research direction scoping
   - **adopt** — "기술 도입", "선택", "어떤 모델 써야", "production 적용" → technology selection / adoption decision

   **Template by goal** (always end with a Cross-References section + 5-7 line Korean summary):

   #### Goal: build — Implementation Roadmap
   - Architecture decision matrix (5-8 decisions): each with Option A/B/C + Recommendation + reasoning. Decision keys depend on domain (e.g., backbone, loss, training paradigm, deployment target, data pipeline).
   - Phased implementation plan (typically 6-12 weeks): Phase 0 (Infrastructure: dataset pipeline, eval metrics, reference code) → Phase 1-N (incremental capability buildup, ending with optimization/deployment).
   - Key technical decisions with runnable Python code snippets (feature extraction, evaluation protocol, etc.)
   - Paper-to-code mapping table: technique → source paper → reference repo → status
   - Risk assessment table: risk | probability | impact | mitigation

   #### Goal: seminar — Seminar Preparation Roadmap
   - Slide structure outline organized by chapter (target audience-aware slide count, e.g., 30-50 for 60-min)
   - Per-chapter cheat sheet (key papers, takeaways, transitions, time budget)
   - Deep-dive slide candidates for expert audiences (5-10 backup slides)
   - Demo candidates with reproducible inference setup (link to repos)
   - Q&A anticipation table (5-10 likely questions with brief answers + supporting paper)

   #### Goal: write — Writing Roadmap
   - Section-by-section outline (Abstract → Intro → Related Work → Methods → Experiments → Conclusion, or domain-appropriate variant)
   - Argument scaffolding: thesis → supporting evidence per claim → counter-considerations / limitations
   - Figure/table candidates with caption drafts and source paper references
   - Citation map: which papers to cite where (with rationale linking to claim)
   - Writing-stage timeline (literature consolidation → outline → draft → revision → submission)

   #### Goal: research — Research Direction Roadmap
   - Open-problem identification: 5-8 gaps with severity (impact × tractability) ratings
   - Hypothesis candidates: testable hypotheses with expected outcomes
   - Experimental setup proposals: minimal viable experiment per hypothesis (data, baseline, metric, resource estimate)
   - Decision matrix: which direction first (impact × feasibility × novelty)
   - Risk register: scientific risks (negative results, scooping) + mitigation

   #### Goal: adopt — Technology Adoption Roadmap
   - Selection criteria matrix (cost, latency, accuracy, license, maintenance) weighted to user constraints
   - Candidate shortlist (3-5 options) with pros/cons aligned to criteria
   - Pilot evaluation plan: which to try first, measurement protocol, decision threshold
   - Integration considerations: data pipeline, monitoring, rollback path
   - Risk assessment: technical + organizational

   **Schema flexibility**: section names above are guides, not hard requirements. Adapt headings, decision keys, phase counts to the actual domain (e.g., "MCU optimization" only relevant if on-device is in scope). Numbers/examples in cards must drive the template, not the other way around.

   **CRITICAL — Output scope strictly limited to the 9 markdown reports** (00_briefing through 08_reading_guide). Specifically for goal=seminar:
   - Produce `06_implementation.md` with chapter outline + cheat sheet + Q&A + deep-dive candidates ONLY.
   - Do **NOT** produce `seminar_slides.md`, `notion_seminar_slides.md`, slide-by-slide markdown, PPTX, or any other slide-rendering artifact.
   - Slide-by-slide draft generation belongs to autopilot-draft presentation mode. Never overstep.

   Same restriction applies to other goals: do NOT generate paper drafts, code, PPTX, or any final-form document — only the 9 markdown analysis reports.

   **MANDATORY closing section — `## Next Pipeline`** (always include at end of `06_implementation.md`, regardless of goal):

   This file is a **high-level outline / sketch** based on field analysis. For the actual document creation or implementation, hand off to a downstream pipeline. Pick the recommendation by detected goal:

   | Inferred Goal | Recommended next command | Hand-off rationale |
   |---|---|---|
   | build | `/autopilot-code --mode dev "<task>"` | Code implementation needs code-plan → code-execute → code-test loop. autopilot-code reads `analysis_project/{code,paper}/` + `research/{topic}/` implicitly. |
   | seminar | `/autopilot-draft "<task>" --mode presentation` | Slide-by-slide markdown draft (PPTX export is NOT supported — user converts to PPT manually with their lab template). research artifact는 implicit 인지. |
   | write | `/autopilot-draft "<task>" --mode paper` | LaTeX paper draft (Abstract → Conclusion) generation. |
   | research | `/autopilot-draft "<task> grant proposal" --mode doc` (or stay in research-only mode) | doc mode + grant-proposal genre intent — hypothesis + experiment design framing. |
   | adopt | `/autopilot-draft "<task> tech adoption report" --mode doc` | doc mode + report/proposal intent — structured go/no-go decision document. |
   | review | `/autopilot-draft "<task> peer review" --mode doc` (REQUIRED: pre-process the venue's review form via `/analyze-project --mode doc <folder>` first — no built-in presets, venues differ year-to-year) | doc mode + peer-review intent — reviewer report draft following the venue's review form. |

   Include the recommended next command verbatim in this section so the user can copy-paste it. autopilot-draft은 `research/{topic}/` 산출물을 prompt 키워드 fuzzy match로 자동 인지하므로 별도 path 인자 불요.

   **Boundary disclaimer** (also include): "이 06_implementation.md는 분야 분석에서 도출된 high-level 계획입니다. 본격적인 문서 작성·코드 구현은 autopilot-draft / autopilot-code로 인계됩니다."

   ### 07_resources.md — Code, Data & Model Resources
   - Tier-based repos: Tier 1 (directly usable for UD-KWS) / Tier 2 (backbone/infra) / Tier 3 (supplementary)
     Columns: repo | paper | stars | language | last-update | reproducibility | notes
   - Code-not-available high-impact papers (institution/reason)
   - Pre-trained models table: model | architecture | params | framework | checkpoint | URL
   - Reproducibility assessment matrix: paper | code | data | checkpoint | overall rating

   ### 08_reading_guide.md — Recommended Reading Paths
   - 4-5 purpose-based tracks:
     Track A: UD-KWS 입문자 (what is this field)
     Track B: 경량 모델 설계 (small model, good performance)
     Track C: 실전 구현 (I want to build a system)
     Track D: 연구자 (where are the open problems)
     Track E (optional): On-device 배포 전문가
   - Each track: target audience, goal, ordered paper list (5-7), reading point per paper, estimated time
   - Per-paper markers: 필수/권장/선택 for each track

   ### Mode `technology` — 7 files

   ### 00_briefing.md — Executive Briefing
   - 1-line summary, 3-5 line key findings, 1-page overview
   - Mermaid: technology landscape (categories, vendors, standards) — `graph TD`
   - Top-3 actionable insights (e.g., "production 환경엔 X 코덱이 사실상 표준", "오픈소스 대안 Y가 부상")

   ### 01_landscape.md — Technology Landscape
   - Category taxonomy (codecs / protocols / processing / hardware 등)
   - Key technologies × categories matrix
   - Lineage diagram (어떤 기술이 어디서 파생됐는지)
   - Adoption stage per technology (emerging / mainstream / legacy)

   ### 02_standards.md — Standards & Specs
   - Standards inventory: org (3GPP / ITU-T / IEEE / W3C / IETF) | spec ID | scope | year | status
   - Per-standard detail: 핵심 sections, mandatory vs optional features, profile/level
   - Cross-references between specs (예: VoLTE는 3GPP 26.171 + IETF SDP + ITU-T G.722.2)
   - **Takeaway**: 어느 표준을 따라야 하는가 (production / research 별도)

   ### 03_vendor_comparison.md — Vendor / Solution Comparison
   - Vendor matrix: vendor | product/SDK | licensing | platform | strengths | weaknesses
   - Capability checklist: feature × vendor (Yes/No/Partial)
   - Cost·license model 비교 (proprietary / open-source / royalty)
   - **Takeaway**: 사용 시나리오별 추천 솔루션

   ### 04_technical_deep_dive.md — Algorithm·Protocol Details
   - 3-5 핵심 기술 테마, each: 문제 정의 → 알고리즘 비교 → key insight
   - Critical equations / pseudocode / state machines (필요 시)
   - Performance trade-off 분석 (latency / quality / complexity)

   ### 05_deployment.md — Deployment Considerations
   - Reference architectures (network topology / signal flow)
   - Latency budget breakdown
   - Integration paths (existing system → new tech 마이그레이션)
   - Failure modes + mitigation
   - Cost model (CapEx / OpEx / per-call cost 등 해당 시)

   ### 06_implementation.md — Goal-Adaptive Action Roadmap (academic mode와 동일 템플릿; build / adopt 우선)

   ### 07_resources.md — Open-source Code, Models, Tools
   - Tier-based resources: Tier 1 (직접 사용 가능) / Tier 2 (참조용) / Tier 3 (실험용)
   - Pre-trained checkpoints (있다면) | platform support | license
   - Evaluation tools, test datasets, benchmarking suites

   ### Mode `market` — 5 files

   ### 00_briefing.md — Executive Briefing
   - 1-line summary, 3-5 line key findings, 1-page overview
   - Top-3 strategic implications

   ### 01_market_overview.md — Market Sizing & Segmentation
   - Total Addressable Market (TAM) / Serviceable (SAM) / Obtainable (SOM)
   - Segment breakdown: by region / customer type / use case
   - Growth rate (CAGR) + projection 3-5년
   - Source attribution table (출처 / 발행일 / 신뢰도)
   - **Takeaway**: 시장 규모 + 어디서 성장 동인이 나오는가

   ### 02_key_players.md — Competitor Profiles
   - Top 5-10 players: name | revenue / market share | products | strategy | recent moves
   - Positioning map (2D, 예: price vs feature)
   - Recent M&A / partnership / funding 동향
   - **Takeaway**: 경쟁 구도 1줄 요약

   ### 03_trends.md — Market Trends & Drivers
   - Driver factors (technology / regulation / customer need)
   - Inhibitor factors (cost / risk / inertia)
   - Disruptor candidates (incumbent를 위협할 수 있는 신기술·플레이어)
   - Timeline (단기 / 중기 / 장기 trend 분리)

   ### 04_opportunities.md — Opportunity Assessment
   - Whitespace identification (충족되지 않는 needs)
   - Entry strategy options (organic / partnership / acquisition)
   - Risk register
   - **Recommended actions** (prioritized)

   ## Quality Directives
   - Cross-reference other reports: [text](filename.md)
   - Every comparison table MUST end with bold **Takeaway** line
   - Mermaid: use graph TD with style directives for key nodes
   - Code snippets in 06_implementation.md must be runnable Python
   - Numbers only from card files / analysis_summary — NO fabrication
   - Do NOT return report content in response — write files only
   Return file paths (under `{artifact_dir}/`) + 3-5 line Korean summary."
```

#### Step 4a-Polish: Editorial polish (편집팀 모드 B — optional)

연구팀이 한국어로 직접 작성한 보고서 세트에 편집팀 모드 B (다듬기) 호출 — 판교체·번역체 회피, 표기 일관성, 줄바꿈·호흡 마무리. _수정만_ (mirror 생성 아님).

호출 조건 (single source — `agents/editorial-team.md` 모드 B 호출 조건):
- **기본**: `--qa standard / thorough / adversarial` 일 때만 호출
- **skip**: `--qa quick` / `--qa light` 또는 사용자 명시 skip

```
모드 B — 다듬기 (다중 파일, in-place).
대상 디렉토리: {artifact_dir}/
대상 파일: 연구팀이 작성한 mode-specific report 세트 전체 (academic 9 개, technology 7 개, market 5 개)

~/.claude/agents/editorial-team.md 의 모드 B 절차를 적용한다.
판교체·번역체 회피 + 표기 일관성 (한 문서 안 같은 개념은 같은 표기) + 줄바꿈·bullet·공백 호흡.
영어로 그대로 둘 어휘: 논문 제목·저자·학회·약자·모델·데이터셋·지표 등 도메인 용어. 그 외 일반 표현은 한국어로.
파일 간 표기 일관성도 강제 — 첫 파일에서 결정한 표기를 이후 파일에도 동일 적용.
내용 (claim / 수치 / citation) 은 손대지 않음 — 표현·표기·가독성만.

완료 시 변경 요약 + 의도적으로 한 표기 결정 두세 개만 돌려준다.
```

> 연구팀이 자연 산출 언어 (한국어) 로 직접 작성하고, 편집팀이 _수정만_ — 두 번 쓰는 노동 회피.

#### Step 4b: QA Loop (max 2 rounds; quick = 1 round; adversarial = 2 + Codex 1)
QA level: `--qa` flag if provided, else default `thorough` (모든 autopilot-* 통일 — [CONVENTIONS.md §1.4](../../CONVENTIONS.md#14-skill별-사용-매트릭스)).

**Two reviewer roles run in parallel** at standard+:
- **Quality reviewer(s)**: coverage / no-fabrication / progressive disclosure / actionable roadmap
- **Fact-checker** (연구팀 subrole): cards/ verbatim 대조 — reports에 인용된 venue/year/metric/lineage가 source cards와 일치하는지 narrow 검증. classification 8-row table 의 canonical 정의는 [`research-team.md`](../../agents/research-team.md) L258-300 single source.

| Level | Quality reviewer | Fact-checker (parallel) | Max rounds |
|---|---|---|---|
| **quick** | 1× 품질관리팀 (sonnet), spot-check만 | _skip_ | **1 (no re-invoke even on 🔴)** |
| **light** | 1× 품질관리팀 (sonnet) | _skip_ (quality reviewer covers basic spot-checks) | 2 |
| **standard** | 1× 품질관리팀 (opus) | **1× 연구팀 fact-checker (sonnet)** | 2 |
| **thorough** | 2× 품질관리팀 parallel (opus, completeness + accuracy) | **1× 연구팀 fact-checker (sonnet)** | 2 |
| **adversarial** | 2× 품질관리팀 parallel (opus) + 1× `Agent(codex-review-team)` (Codex CLI external review) | **1× 연구팀 fact-checker (sonnet)** | 2 + Codex 1 |

**Why Sonnet for fact-checker**: cards verbatim 대조는 _창의적 판단_이 아닌 _단순 매칭 작업_이라 Sonnet으로 충분. 비용 효율적.

```
round = 0, review_dir = {artifact_dir}/_internal/reviews/
Loop:
  round += 1

  # Parallel reviewer invocation (single message with multiple Agent calls per QA Scaling)

  Quality reviewer prompt (opus or sonnet per level):
    "Review research survey report — _coverage / no-fabrication / disclosure / roadmap_ focus.
     Topic: {topic}. Reports dir: {artifact_dir}.
     Verify: coverage, no fabrication, progressive disclosure, actionable roadmap.
     Do NOT individually verify each citation (model venue/year/metric) — that's the fact-checker's role at standard+.
     Write to: {review_dir}/round_{round}_quality.md (or round_{round}.md at light level).
     Return ONLY path + one-line verdict."

  Fact-checker prompt (sonnet, parallel — standard/thorough only):
    "You are a fact-check focused reviewer — NOT report quality.
     Topic: {topic}. Reports dir: {artifact_dir}. Cards: {artifact_dir}/cards/.

     For every domain claim in the reports (model name / venue / year / metric / dataset /
     lineage / classification mentioned in 00_briefing through last report), open the
     corresponding card and verbatim compare:
     - Single source of truth: {artifact_dir}/cards/*.md
     - If a report claim has no matching card → flag as 🔴 (fabrication risk)

     Do NOT comment on coverage, narrative, or roadmap quality — that's the quality reviewer's job.
     Cost-aware mode (sonnet): table-only output. Limit to ~30 most material claims (prioritize Tier 1 papers + key models in user-prompt).

     Output table:
     | Report | Section | Claim | Source card (file:line) | Match (✅/❌) | Severity (🔴/🟡) |

     Write to: {review_dir}/round_{round}_factcheck.md.
     Return ONLY path + one-line verdict."

  No 🔴 from any reviewer → exit.
  qa_level == quick → after round 1, write unresolved.md if any 🔴 remain (tag fact-check residuals as [FACT-RESIDUAL]), exit. NEVER re-invoke 연구팀.
  🔴 from quality + round < 2 → re-invoke 연구팀 with quality findings.
  🔴 from fact-checker + round < 2 → re-invoke 연구팀 with mandatory ref-grounding (re-read named cards).
  🔴 from both + round < 2 → re-invoke 연구팀 with combined findings.
  round >= 2 + 🔴 remain → write unresolved.md (tag fact-check residuals as [FACT-RESIDUAL]), exit.
```

#### Step 4c: Status Check
Verify `{artifact_dir}/00_briefing.md` exists. Not exists → pipeline_summary(failed) → STOP.

### Step 5: Pipeline Summary
Write `{artifact_dir}/pipeline_summary.md` BEFORE reporting:
```markdown
# Research Survey Pipeline Summary: {topic}
- **Date**: {YYYY-MM-DD}
- **Query**: {query}
- **Depth**: {depth}
- **Status**: done / partial / failed
- **From-Stage**: {stage if resumed via --from, else "N/A"}

## Process Log
| Step | Action | Result | Notes |
|---|---|---|---|
| 1 | Input parsing | {type} | topic: {topic} |
| 2a | Query Expansion | {N} queries | original + {N-1} variants |
| 2b-c | Paper Search (Agent) | {N} papers | sources: {list} |
| 2e | Query Expansion Rounds | {N} rounds | new papers per round: {list} |
| 3 | Paper Analysis (Agent x N) | {N} analyzed | depth: {depth}, loopbacks: {N} |
| 4 | Report Generation (Agent + QA) | {N} files (mode={mode}: academic=9 / technology=7 / market=5) | QA: {level}, rounds: {N} |

## Artifacts
- Search: {artifact_dir}/_internal/search_results.json
- Analysis: {artifact_dir}/analysis_summary.md
- Reports: {artifact_dir}/00_briefing.md ~ {last_report.md} (mode-aware: academic→08_reading_guide / technology→07_resources / market→04_opportunities)

## Decision Points
| Step | Decision | Response | Action |
|---|---|---|---|
| (from in-memory log) |
```

### Step 6: Briefing
Read `00_briefing.md` and `06_implementation.md` (for the inferred goal + Next Pipeline) and present:
1. Level 0 summary (one line)
2. Level 1 overview (3-5 lines)
3. Key stats: total papers, core papers, code availability
4. File paths for all reports (mode-aware: academic→00~08 / technology→00~07 / market→00~04)
5. **Next pipeline recommendation**: read the `## Next Pipeline` section from `06_implementation.md` and present the inferred goal + recommended next command verbatim. Make it copy-paste-ready.
6. "질문이 있으시면 물어보세요. 보고서를 기반으로 답변드리겠습니다."

> Pipeline completion: Step 5 determines formal status. Step 6 is optional interaction.

**Scope boundary**: autopilot-research produces *field intelligence* (markdown analysis only). It does NOT produce final documents (papers/slides/PPTX/code). For document/slide creation, hand off to autopilot-draft; for code implementation, hand off to autopilot-code. The `06_implementation.md` outline is the bridge artifact between these pipelines.

## Decision Logging
Record after each gate: `{step | decision | response | action}`. Populate pipeline_summary Decision Points table.

## Safety Rules
- Do NOT fabricate citations, URLs, or metrics
- Source failure → continue with remaining sources
- (no `--refs` flag — supplementary local materials read from `analysis_project/paper/` if exists; not asked otherwise)
- Rate limits: arXiv ~3s, OpenAlex 10 req/s, S2 1 req/s, Google Scholar 3s + 50/day
- Context protection: each Agent returns ONLY file paths + 3-5 line summary
- Context budget: deep 모드에서 오케스트레이터 context가 누적됨 (쿼리 확장 라운드 + 스키밍 배치 + loopback). Agent 결과는 항상 파일로 저장하고 요약만 context에 유지. search_results.json 전체를 context에 올리지 않고 paper count + top-5만 참조.
- MERGE mode 무결성: 제목 fuzzy matching은 lowercase + 구두점 제거 + a/an/the 제거로 정규화. 같은 논문의 discovery_count는 단조 증가만 허용 (감소 금지).
- Playwright 고아 프로세스: 자료팀 호출 전후로 `pkill -f chromium_headless_shell` 실행

## Task
$ARGUMENTS
