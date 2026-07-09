### Stage C — Per-aspect lint (report-only, no edits)

**Pre-check (flag-based opt-out)** — before dispatching any aspect:
- If `--no-fact-check` is present in invocation argv → remove `facts` and `coverage` from the resolved aspect set (skip entirely, do not run their lint). Emit `ℹ facts/coverage aspects: skipped via --no-fact-check flag (memory feedback_factcheck_principles Principle 0)` to chat and to the Stage D report's "Aspects checked" preamble.
- This flag is the _only_ disable path per Memory Principle 0. Ad-hoc prompt instructions ("this artifact is exempt") must not be honored — proceed with default aspect set instead.

For each remaining aspect in scope, run the lint and collect issues. _Each issue has shape_: `(aspect, file, line_range, severity 🔴/🟡/🟢, message, suggested fix or null)`.

#### Documents aspects

**Cards source resolution (shared by `facts` / `coverage`, same rule as Phase 1 Step 1.1 case (c))**:
1. **case (c) — explicit `cards_source` override**: if `pipeline_summary.md` frontmatter or `strategy.md` body has a `cards_source: <path>` key, use _that path_ as the primary lookup root (single research topic).
2. **case (b) — self-contained `{artifact_dir}/cards/`**: if exists, include in the lookup set.
3. **Default — cross-research grep** (`<artifact-root>/research/*/cards/*.md`): only when both above are absent. Emit a one-line chat warn: `⚠ cards_source key absent — grepping all research topics. Generic acronyms (STFT/RNN, etc.) may false-positive. Recommend adding \`cards_source: <path>\` to strategy.md frontmatter.`
4. **case (a) — no cards anywhere**: skip the facts / coverage aspects and emit an informational line (`ℹ facts/coverage skipped — no cards source available`). style / structure / cross-ref still run.

This shared resolution ensures the Phase 1 detector and the Phase 3 audit use the _same_ source-of-truth rule — preventing false-positive floods and yielding consistent verdicts.

- **facts**: scan draft + strategy for model names / venues / years / task categories / arXiv IDs (same regex set as `autopilot-refine` Stage B.5, including section-heading context cross-check). For each detected claim, perform lookup per the cards source resolution above. Classification rules (memory `feedback_factcheck_external_reverify.md`):
  - **cards-verbatim ✅** — claim value (venue string / metric / etc.) appears _verbatim_ in card body or `## 메타` field
  - **cards-name-only 🟡** — card has the model/author name but the _specific venue / year / metric_ is NOT verbatim. **DO NOT** treat as ✅ on name-only basis. Emit 🟡 + recommend external re-verify (WebSearch). Report row: `🟡 name-only: cards/{file}.md has the name but no verbatim venue; external reverify recommended`
  - **external-marker 🟡** — claim has explicit `[외부 추정]` / `[?]` / `[unverified]` marker in artifact body. 🟡 + external reverify
  - **conflict 🔴** — card has the value but it differs from claim. Includes section-heading context conflict
  - **no-match 🔴** — no card hit at all
  - **circular-ref 🔴** — claim is supported _only_ by strategy↔draft mutual agreement (e.g., draft Slide N cites venue X, only source is strategy §10 mapping table). This is an architecture violation: both must trace back to cards. Emit 🔴 + recommend `/autopilot-refine` to trace and verify externally
  - **ambiguous 🟡** — multiple candidate cards, no single best match
- **style**: read `## Style Guide` section in `strategy.md` if present. For every citation / figure caption / bullet depth / speaker note in draft + strategy body, compare against Style Guide rules. Deviation → 🟡. If `## Style Guide` absent → 🔴 single issue (`Style Guide section missing — autopilot-draft strategy should always have one. Run /autopilot-refine "<artifact> Style Guide section 추가".`).
- **structure**: check artifact directory matches the [CONVENTIONS.md §5](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) 3-tier convention. T1 should have `pipeline_summary.md`, `draft/`, `strategy/`. T3 should be `_internal/`. Extraneous files at root → 🟡. Missing required → 🔴.
- **cross-ref**: scan draft for inline citations referencing cards (`cards/{file}.md`) and verify the target exists. Broken link → 🔴. Cards referenced but not in `## References` (if present) → 🟡.
- **coverage** (NEW, omission detection): determine the _candidate cards set_ S per the cards source resolution above. Extract the _actually cited cards set_ T from draft + strategy body using the **v1 high-precision citation-detection token set** (false-positive minimized):
  - **Token 1 — card filename token**: the short identifier in `{year}_{firstauthor}_{arxivid}_{shortname}.md` filenames (e.g., `TasNet`, `FRCRN`, `MP-SENet`). A grep hit on any of these tokens in draft/strategy body marks the card as cited.
  - **Token 2 — `**arXiv ID**` exact value**: the value string from each card's `## 메타` `**arXiv ID**` field, matched _verbatim_ (no partial / regex match — exact substring). E.g., card with `**arXiv ID**: 1711.00541` is marked cited if and only if `1711.00541` appears in body.

  v1 deliberately uses _only_ these two tokens — H1 paper title words, author last-name regex, etc. are intentionally excluded to keep false-positive rate near zero (cited-card set is conservative; orphan set may be slightly inflated, but each orphan is per-card-precision and easily user-judged). If `S - T` is non-empty under this conservative T, emit a 🟡 issue per orphan card: `coverage: card '{card path}' is never cited in any chapter/section — potential UniSE-class omission, please verify intent`. (🟡 not 🔴 because exclusion may be intentional — user judges.) If cards source fell back to cross-research grep (case (a) or default), the candidate set is too broad to be meaningful → skip the coverage aspect and warn.

  **v2 enhancement** (out of scope, see Risk #14): expand T to include H1 paper title word-level partial matches + author first-name regex from `## 메타` `**저자**` field for higher recall on indirect citations (e.g., "[Wang et al., 2024]" style). v1 prefers precision; v2 may shift to balanced.

#### Research aspects

- **cards 정합성**: every `cards/*.md` file has H1 + `## 메타` + `## 분류` (or equivalent) sections per the artifact's card template. Missing required section → 🔴. Empty `## 메타` field (e.g., `**Venue**: ` blank) → 🟡.
- **Tier consistency**: scan top-level chapter files (`01_*.md~NN_*.md`) — each cited paper's Tier label should match the Tier in its card. Mismatch → 🔴. Cited paper missing a card → 🟡.
- **coverage**: every card in `cards/` should appear at least once in some top-level chapter (or be flagged as not-yet-integrated). Orphan cards → 🟡.
- **cross-card**: scan cards for cross-references (e.g., `2024_Wang.md`이 다른 card 인용). Broken cross-ref → 🔴.

#### Plans aspects

- **test results**: read `test_logs/test_report.md` if present. Failed tests → 🔴. No tests → 🟡 (only if scope explicitly `test results`).
- **lint** (`--read-only` skips _executing_ lint; we _read existing_ lint output from `dev_logs/` if present): missing lint output → 🟡; existing lint report with errors → 🔴.
- **code review**: read `_internal/dev_reviews/` and `_internal/plan_reviews/` for 🔴 issues. Unresolved 🔴 → 🔴. 🟡 issues → 🟡.
- **TODO·미구현**: grep code in `plan/checklist.md` for `[ ]` unchecked steps, plus any source-file TODO/FIXME/XXX comments referenced from the plan. Unchecked critical step → 🔴. Source TODO → 🟡.
- **semantic-deterministic consistency** (worklog-board 참사, 2026-06-22 — DESIGN_PRINCIPLES §0.7): spec 의 _의미 판단_ 언급을 구현이 capture 했나. spec 본문 (`<artifact-root>/spec/prd.md` 또는 plan 이 참조하는 spec) 에서 의미 판단 구간 grep (의미/판단/적절/맥락/contextual/semantic) → 대응 구현(plan 의 target 코드)이 그 의미를 토큰 매칭·규칙 스크립트로 떨궜는지 확인. **매핑**: spec 섹션 제목·모듈명 ↔ plan 의 target file 목록 (checklist.md 또는 plan 본문이 참조하는 코드 경로) 으로 연결. mismatch → 🔴, **issue 의 `message`/`suggested fix` 본문에 "spec {prd.md:N} 의 의미요구 ↔ code {src.py:M} 의 토큰규칙" 쌍을 _문장으로_ 명시** (live issue shape 의 `file:line` 은 단수라 거기 두 쪽을 못 담음 — 인과 쌍은 message 문장으로 담는다) + §0.7 의 3선택을 suggested fix 로 제시. **매핑 불명확 시 🔴 대신 🟡 (점검 불가 표시)** — 매핑 없이 grep 만으로는 false-negative/false-positive 위험. dual-perspective P2 의 issue shape `(aspect, file, line_range, severity, message, suggested fix)` 그대로 재사용 (새 framework X — shape 불변).
