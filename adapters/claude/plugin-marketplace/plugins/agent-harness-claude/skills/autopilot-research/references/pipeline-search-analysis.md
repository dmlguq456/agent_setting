## Pipeline

> **Stage-dispatch 계약** (`standard+`, OPERATIONS §5.10 ③④·SD-1·SD-2): `standard+` 에서 아래 각 durable stage 는 독립된 **depth-2 headless session** 으로 dispatch 되고, 각 step 에 명시된 in-session team 은 그 stage session _안에서_ 실행된다. depth-1 conductor 는 artifact path 만 넘기고 verdict/status 만 읽는다 — stage 본문이나 이전 stage 의 대화는 넘기지 않는다 (**file-only handoff**: 각 stage 는 입력을 파일에서 읽는다). `direct/quick` 과 micro-stage 는 inline 유지, stage session 은 재분사하지 않는다 (depth 3+ 금지). depth-gated step (2e/3c) 은 conditional stage — depth 조건 만족 시에만 별도 dispatch. 아래 stage-worker 매핑은 _계약 + 매핑 추가_ 만 — 각 파이프 본문을 imperative dispatch 로 재작성하는 건 후속 작업.

#### Stage-worker 매핑 (§6-homolog)

| stage | in-session team | input artifacts | output artifacts | write class |
|---|---|---|---|---|
| Step 2 (Source Search, 2a-2d) | 연구팀 | `queries`(오케스트레이터 생성), HF `paper_search` 결과(optional) | `_internal/search_results.json` | _internal (raw, T3) |
| Step 2e (Query Expansion Rounds — **conditional**, depth-gated) | 연구팀 | `_internal/search_results.json`(read) + 새 keyword 기반 `new_queries` | `_internal/search_results.json`(merge 갱신) | _internal (raw, T3, append/merge) |
| Step 3b (Phase A — Parallel Skimming Batches) | 연구팀 (batch, parallel) | `_internal/search_results.json`, `_internal/browser_extracts/`(자료팀 사전 fetch) | `cards/{paper}.md` | root (deliverable, T1/T2) |
| Step 3c (Phase B — Reference Chaining — **conditional**, depth-gated) | 연구팀 | `cards/`, `_internal/search_results.json` | `_internal/chaining_results.md` | _internal (raw, T3) |
| Step 3e (Compile analysis_summary.md) | 연구팀 | `cards/`, `_internal/chaining_results.md`(있으면), `_internal/code_search.md`(있으면) | `analysis_summary.md` | root (deliverable, T1/T2) |
| Step 4a (Report Generation — [report-generation.md](report-generation.md)) | 연구팀 | `analysis_summary.md`, `_internal/*`, `cards/` | `{00-08}_*.md`(mode-specific report set) | root (deliverable, T1/T2) |
| Step 4b (QA Loop — [report-generation.md](report-generation.md)) | 연구팀 (quality/fact-check/claim-verify subroles) / codex-review-team (adversarial external) | report set + `cards/` | `_internal/reviews/round_{n}_*.md`, `unresolved.md`(있으면) | _internal (raw, T3) |

> 자료팀 (browser-fetch / web-image-search, Step 3a·3.5) 은 위 stage 들 _안에서_ 일어나는 sub-delegation — 별도 dispatch stage 가 아니다. 두 stage 가 lock 없이 동일 파일에 동시 write 하지 않는다: Step 2e 는 매 라운드 순차 재호출로 `_internal/search_results.json` 을 merge 하고(동시 write 없음), Step 3b 병렬 batch 는 batch 마다 서로 다른 `cards/{paper}.md` 에만 써서 충돌하지 않는다.

### Step 1: Input Parsing & Validation
- Detect query type: keyword, paper title, arXiv ID, PDF path, folder path
- Resolve `--mode`: explicit flag value, or infer from query keywords (academic / technology / market — see Modes section). Notify user of inferred mode in one line. Multi-match → defer resolution to Step 1.5 Scope Clarification.
- Auto-detect supplementary input: if `<artifact-root>/analysis_project/paper/` exists in current dir, include as supplementary input for chaining. If user explicitly requested "use my local PDFs" but no `analysis_project/paper/` → suggest running `/analyze-project --mode paper` first.
- Construct topic name (sanitize: lowercase, hyphens, max 30 chars)
- Set artifact_dir: `<artifact-root>/research/{topic}/`
- `mkdir -p {artifact_dir}` (only AFTER validation)

### Step 1.5: Scope Clarification (사전 조율) — skipped if `--no-clarify` or `--from`
> 이 Step 1.5 는 [CONVENTIONS.md §6.6](../../core/CONVENTIONS.md#66-autopilot-intake-gate) Autopilot Intake Gate 의 연구 트랙 인스턴스 — 4속성 공유, 질문 뱅크는 §6.6 연구 행.

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

**§5 자율 진행**: 질문 던질 때 adapter pause/autonomy rule 적용(Claude Code: [CLAUDE.md](../../adapters/claude/CLAUDE.md) §2) — ScheduleWakeup 15-20분 동시 호출, 답 없으면 mode 추론 결과 + depth medium + 가장 좁은 범위 default 로 자율 진행.

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
- intensity `quick` 에서는 Step 3.5 자동 skip (fastest path 우선).
- `--no-figures` flag 명시 시 skip.
