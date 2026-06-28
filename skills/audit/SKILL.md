---
name: audit
description: "Read-only multi-aspect audit / lint for `<artifact-root>/{plans,research,documents}/*` artifacts. Single global entry — auto-detects artifact type from path prefix (plans=code; research=field-survey; documents=doc deliverable). Per-type lint aspects: doc → facts / style / structure / cross-ref / coverage; research → cards 정합성 / Tier consistency / coverage / cross-card; plans → test results / lint / code review / TODO·미구현. Default `--scope auto` — artifact 특성 기반 자동 선택; 사용자 명시는 1순위 override. Report-only — never modifies the artifact. Complementary to autopilot-refine: refine = edit flow, audit = inspect flow."
argument-hint: "<artifact_path> [--scope auto|facts|style|structure|cross-ref|coverage|all] [--read-only] [--report-only] [--no-fact-check]"
metadata:
  group: ops
  fam: ops
  modes: []
  blurb: "산출물·파이프 사후 점검 — drift·일관성·누락 진단 보고"
---

> **산출물 폴더 컨벤션**: [CONVENTIONS.md §5](../../CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier). 본 skill은 입력 artifact를 _수정하지 않음_ — 점검 보고서만 생성. 보고서는 `{artifact_dir}/_internal/audit/audit_{YYYY-MM-DDTHHMM}.md`에 기록.
> `<artifact-root>` 해석: `.agent_reports` 우선, 없으면 legacy `.claude_reports`. 실제 쉘 명령에서는 `REPORTS_DIR=.agent_reports; [ -d "$REPORTS_DIR" ] || REPORTS_DIR=.claude_reports` 로 치환한다.

## Position in autopilot family

`audit` is the **read-only inspection** counterpart to `autopilot-refine`:
- `autopilot-refine` reads + writes (proposes diff, applies on confirm, versions).
- `audit` reads only (lints, reports issues, never edits).

Use `audit` when:
- 누적 minor drift batch 점검 — autopilot-refine의 Default Invocation Rule에 따라 minor는 직접 Edit + `pipeline_summary.md` 상세 log만 남기므로, 누적된 minor를 audit이 일괄 점검하는 게 정상 워크플로우.
- 새 산출물 인계 전 sanity check.
- 다른 사람이 만든 artifact 평가.

Use `autopilot-refine` when:
- 구체적 major-level 수정 의도가 있고 곧장 적용까지 가져갈 때 (3-criteria 충족 — 사용자 명시 / 구조적 대규모 / 외부 검토 직전).

## Dual-perspective audit (doc / research 전용)

doc / research artifact에 대한 audit은 **두 관점**으로 동시 점검한다:

| Perspective | 무엇을 보는가 | 산출물 섹션 |
|---|---|---|
| **P1 — vs last major baseline** | `pipeline_summary.md`의 `## 마이너 변경 로그 (v{N} → next major 누적)` 섹션 + `_internal/versions/v{N}/` 스냅샷 diff. 누적된 minor가 _집합적으로_ artifact를 어디로 drift시켰는지. | `## Perspective 1 — 누적 minor drift` |
| **P2 — vs universal principles** | 현재 artifact 상태를 Stage C aspect lint (facts / style / structure / cross-ref / coverage)로 점검. 시점 무관 정합성. | `## Perspective 2 — Universal principles` |

**왜 두 관점이 필요한가**:
- P1만 보면 — "변경된 것"만 보이고 "오래 전부터 누적된 미해결 issue"는 놓침.
- P2만 보면 — 현재 상태 평가는 정확하지만 "어느 minor가 issue를 introduce 했는지" 추적 불가 → revert 또는 major refine 시 baseline 설정이 어려움.
- 둘을 cross-correlate 하면: P2의 issue가 P1의 minor log audit-flag와 매칭되는지 확인 → "최근 도입된 issue (fix 우선순위 高)" vs "기존 잔존 issue (next cycle 처리 OK)" 분류 가능.

**plans type**: minor log 컨벤션 없음 → P1 skip, P2만 실행 (현 동작과 동일).

## Cadence (언제 audit 실행)

| 트리거 | 동작 |
|---|---|
| **사용자 명시 `/audit <artifact>`** (기본) | 즉시 실행 |
| **AUDIT_HINT_THRESHOLD 도달** (default 5 minors since last major) | 직전 작업 (minor Edit 또는 autopilot-refine) 종료 후 chat alert: `⚠ {N} minor edits accumulated since v{N} — recommend /audit {artifact_short_name}`. _자동 실행 X_ — 사용자가 invoke. |
| **자동 fix chain dispatch에서 spawned audit** | autopilot-refine 또는 autopilot-code의 fix routing에서 호출 시 |

threshold는 doc/research artifact의 `pipeline_summary.md` `## 마이너 변경 로그` 섹션의 entry 수 또는 `## 버전 히스토리` 표의 `v{N}_M` 형식 row 수로 계산.

## Language Rule

All user-facing output (chat report, audit log) in natural **Korean** (no translationese — write Korean natively, don't translate from an English draft).

## Argument Parsing

    /audit <artifact_path> [--scope auto|facts|style|structure|cross-ref|coverage|all] [--read-only] [--no-fact-check]

- `<artifact_path>` (REQUIRED): one of
  - Absolute path to a `<artifact-root>/{plans,research,documents}/*` directory
  - Fuzzy short name (e.g., `se-seminar-tfrestormer`) — resolved via `ls -d <artifact-root>/{plans,research,documents}/*$ARG* 2>/dev/null`. 1 match → use; multiple → ask user (글로벌 [CLAUDE.md](../../CLAUDE.md) §2 적용 — ScheduleWakeup 10분; 답 없으면 가장 최근 수정 artifact); 0 → error.
- `--scope` (default `auto`): which aspect set to check. **사용자 명시는 1순위 (override)**. 명시 없으면 audit이 artifact 특성 (mode / refine 횟수 / status / 구조)을 보고 _스스로 적절한 aspect set 선택_. 명시 값은 `facts | style | structure | cross-ref | coverage | all` 중 하나로 type-specific aspect group에 매핑 (Stage B 표 참조).
- `--read-only` (default for plans): if specified for `plans` type, skip any aspect that requires _executing_ tests / lints — only static inspection (file diff, TODO grep, code review heuristics). For `research` / `documents` types, `--read-only` is implicit and the flag is a no-op (warn: "audit는 research/documents에 대해 항상 read-only").
- `--report-only`: skip the auto-fix chain (Stage E). With this flag, `/audit` produces the report and stops — same as previous default behavior. Use when you want only inspection without follow-up edits.
- `--no-fact-check`: opt-out flag honored per `feedback_factcheck_principles.md` Principle 0. If present, the `facts` aspect (and the `coverage` aspect's cards-set diff) are **skipped** before Stage C aspect dispatch — i.e., the aspect skip happens at the _pre-check_ stage, not via filtering after lint runs. Other aspects (style / structure / cross-ref / Tier / cross-card / test / lint / code review / TODO) still run. Stage D report emits an informational line at the top of "Aspects checked": `ℹ facts/coverage aspects: skipped via --no-fact-check flag (memory feedback_factcheck_principles Principle 0)`. This is the _only_ allowed disable mechanism for fact verification; ad-hoc prompt evasion must not be honored.

## Process

### Stage A — Detect artifact type

1. Resolve `<artifact_path>` to an absolute directory path.
2. Inspect path prefix:
   - `<artifact-root>/plans/*` → **plans** type (autopilot-code dev/debug plan)
   - `<artifact-root>/research/*` → **research** type (field survey)
   - `<artifact-root>/documents/*` → **documents** type (doc strategy + draft)
   - Other → error: "audit은 <artifact-root>/{plans,research,documents}/* 산출물 전용. resolved path: {path}"
3. Print one-line to user (Korean): `Type 인식: {type} — {artifact short name}`.

### Stage B — Determine effective scope

**우선순위**:
1. **사용자가 `--scope <value>`를 명시한 경우 (1순위, override)** — 그 값을 그대로 사용. type-specific aspect group으로 매핑하여 적용 (아래 표 참조). 매핑이 N/A인 경우(예: `--scope coverage` on plans) 한 줄 warn 후 빈 aspect set 반환.
2. **명시 없음 (default = `auto`)** — Stage B.1 자동 판단 로직 실행.

#### Stage B.1 — Auto-scope detection (artifact 특성 기반)

artifact의 다음 단서를 _순차적으로_ 읽어 적절한 aspect set 결정:

**documents type:**
| 단서 | 우선 aspect | 이유 |
|---|---|---|
| `pipeline_summary.md` frontmatter `mode: presentation` | facts + cross-ref + coverage + **structure (§presentation-0 슬라이드 분량 자가 검사 — bullet 5~6 줄 / 키워드 ≤ 10 단어 / 그림·표 ≥ 60% / 표 6×5)** | slide claim 정확성 + cards 인용 완전성 + 16:9 분량 검증 (PPT 옮긴 시점 깨짐 사전 차단) |
| `mode: paper` | facts + style + cross-ref | 논문 citation 양식 + claim 검증 + paste-ready 의도면 §paper natural-integration rule 준수 |
| `mode: doc` (task description 안 _peer review_ / _rebuttal-response_ 의도) | structure + cross-ref | review form 양식 / reviewer point 대응 |
| `mode: doc` (그 외 — 보고서 / 제안서 / blog / memo) | style + structure | 양식 일관성 + 산출물 구조 |
| `pipeline_summary.md` 버전 히스토리 행 수 ≥ 10 (누적 drift 의심) | **all** | refine 다회 누적 → 종합 점검 |
| 위 단서 미발견 / 정보 부족 | **all** | 안전 default |

**research type:**
| 단서 | 우선 aspect | 이유 |
|---|---|---|
| chapters (`01_*.md ~ NN_*.md`) 존재 + `cards/` 존재 | **all** | 종합 (Tier + coverage + cards 정합성 + cross-card) |
| `cards/` only (chapters 없음) | cards 정합성 + cross-card | 카드 자체 점검 |
| chapters only (cards 없음) | Tier consistency + coverage | 인용 정합성 |

**plans type:**
| 단서 | 우선 aspect | 이유 |
|---|---|---|
| `status: done` + `test_logs/test_report.md` 존재 | test results + code review + semantic-deterministic consistency | 완료된 plan의 실행 정합성 — semantic-deterministic consistency 는 Step 3d 통과 후 코드 수정으로 spec 의미요구 ↔ 구현이 어긋났는지 _drift 재검출_ (중복비용 아님, 다른 시점) |
| `status: done` + test_logs 부재 | code review + TODO·미구현 + semantic-deterministic consistency | dev review 잔존 issue + 미완료 항목 |
| `status: partial` or `status: failed` | TODO·미구현 + code review + semantic-deterministic consistency | 실패 항목 + reviewer 의견 우선 |
| `status: active` | TODO·미구현 | 진행 중 — 다른 aspect는 미완료 상태 |

**Output to chat** (자동 판단 시):
```
Auto-scope: {aspect 1} + {aspect 2} + ... ({이유 한 줄})
```
사용자 명시 시:
```
Scope: {value} (사용자 지정, override)
```

#### Stage B.2 — Type-specific aspect mapping (when `--scope <value>` is given)

| `--scope` | documents | research | plans |
|---|---|---|---|
| `facts` | facts | cards 정합성 | test results + TODO·미구현 |
| `style` | style | Tier consistency | lint |
| `structure` | structure | coverage | code review |
| `cross-ref` | cross-ref | cross-card | N/A (warn) |
| `coverage` | coverage | coverage | N/A (warn) |
| `all` | facts + style + structure + cross-ref + coverage | cards 정합성 + Tier + coverage + cross-card | test results + lint + code review + TODO·미구현 + semantic-deterministic consistency |

**Why `coverage` is new for documents**: the Stage B.5 regex detector can only flag _present_ claims in `new_text` — it cannot, by construction, flag _absent_ claims (e.g., UniSE missing from a timeline). Omission requires a separate _set-diff_ mechanism. The `coverage` aspect fills this: reports the difference between the full cards source vs cards actually cited in the draft. Without it, UniSE-class omissions recur.

### Stage B.5 — Minor log baseline ingestion (doc / research 전용)

plans type은 본 단계 skip (minor log 컨벤션 없음).

**입력**:
- `pipeline_summary.md`의 `## 마이너 변경 로그 (v{N} → next major 누적)` 섹션 (있으면)
- `_internal/versions/v{N}/` 가장 최근 major snapshot 디렉토리 (있으면)

**동작**:

1. `## 마이너 변경 로그` 섹션 파싱 — 각 entry의 다음 정보 수집:
   - 버전 (`v{N}_M`)
   - 일시
   - Files touched (경로 list)
   - Audit-flag (`facts`/`style`/`structure`/`cross-ref`/`coverage` 중 표시된 것)
   - Trigger / Rationale (요약 인용)

2. 마지막 major snapshot vs 현재 artifact 디렉토리 diff:
   ```bash
   diff -ruN _internal/versions/v{N}/ {artifact_root} \
     --exclude=_internal --exclude=pipeline_summary.md \
     > /tmp/audit_p1_diff.txt
   ```
   (`_internal/`과 `pipeline_summary.md`는 audit log/version 메타라 diff에서 제외.)

3. 두 정보를 cross-correlate — 각 minor entry의 audit-flag를 현재 stage C aspect set에 _bias_로 전달:
   - audit-flag에 `facts`가 있는 minor가 N개 → Stage C `facts` lint에서 해당 file의 diff 영역을 우선 검사.
   - audit-flag가 `none`인 minor — Stage C는 default behavior로 점검 (특별 bias 없음).

4. 산출: `p1_findings` dict (minor entry별 변경 요지 + cross-correlate 결과)를 Stage D 보고용으로 보관.

**chat 출력 (1줄)**:
```
P1 baseline: v{N} snapshot 발견, 누적 minor {count}건 ingest (audit-flag 집계: facts={A} / style={B} / structure={C} / cross-ref={D} / coverage={E})
```

snapshot 또는 minor log 부재 시:
```
P1 baseline: skipped — last major snapshot 또는 minor log 부재. P2 only.
```

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
- **structure**: check artifact directory matches the [CONVENTIONS.md §5](../../CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) 3-tier convention. T1 should have `pipeline_summary.md`, `draft/`, `strategy/`. T3 should be `_internal/`. Extraneous files at root → 🟡. Missing required → 🔴.
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

### Stage D — Report

Write the audit report to `{artifact_dir}/_internal/audit/audit_{YYYY-MM-DDTHHMM}.md`:

~~~markdown
# Audit Report — {artifact name}

- **Date**: {YYYY-MM-DD HH:MM}
- **Type**: {plans | research | documents}
- **Scope**: {flag value or "all"}
- **Aspects checked**: {comma-separated}
- **P1 baseline**: v{N} snapshot ({YYYY-MM-DD}), 누적 minor {count}건 | _skipped (snapshot/minor log 부재)_

## Summary

| Aspect | 🔴 Critical | 🟡 Warning | 🟢 OK |
|---|---|---|---|
| {aspect 1} | {count} | {count} | {count} |
| ... | ... | ... | ... |

**Total**: 🔴 {N} / 🟡 {M} / 🟢 {K}

## Perspective 1 — 누적 minor drift (vs v{N} baseline)

> doc / research 전용. plans는 본 섹션 skip.

### 1.1 Accumulated minor entries (newest-first)

| 버전 | 일시 | Trigger 요약 | Audit-flag | Files |
|---|---|---|---|---|
| v{N}_M | ... | ... | facts/style/... | {count} |
| v{N}_M-1 | ... | ... | ... | ... |

### 1.2 Diff summary vs v{N} snapshot

- **Lines added/removed**: +{A} / -{B} (전체 누적 diff, excluding `_internal/` + `pipeline_summary.md`)
- **Files modified**: {list of relative paths}
- **Hot spots** (diff lines ≥20인 파일): {list}

### 1.3 Cross-correlation with Perspective 2 findings

| P2 finding | 매칭 minor entry | 도입 시점 |
|---|---|---|
| {aspect:🔴 issue title} | v{N}_M ({YYYY-MM-DD}) | 최근 도입 — fix 우선순위 高 |
| {aspect:🟡 issue title} | (매칭 없음) | 기존 잔존 — 정상 cycle 내 처리 |

(매칭 = P2 finding의 file:line이 minor entry의 Files touched에 포함되는 경우)

## Perspective 2 — Universal principles

> 현재 artifact 상태의 aspect-by-aspect 정합성 점검 (시점 무관).

### Aspect: {name}

#### 🔴 {issue title}
- **File**: `{relative path}:{line}`
- **Severity**: 🔴
- **Detail**: {1-3 line description}
- **Introduced**: v{N}_M ({YYYY-MM-DD}) | _기존 잔존 (v{N} baseline 이전 또는 추적 불가)_
- **Suggested fix**: {one-line — e.g., "/autopilot-refine '<artifact> {fix description}'"} | (또는 null)

#### 🟡 {issue title}
- ...

### Aspect: {name 2}
...

## Verdict

- **Status**: 🔴 issues require attention | 🟡 minor warnings only | 🟢 clean
- **Recommended next action**: {1-line — e.g., "Run /autopilot-refine 'X' to fix the 5 critical facts issues" or "No action required"}
- **Baseline reset 권장**: {if 누적 minor가 5건 이상 + P2 finding 모두 🟢 또는 fix 완료} `다음 작업을 major refine으로 묶어 v{N+1} snapshot + minor log 정리 권장` | (또는 omitted)

---

> Generated by `/audit` skill. Report-only — no edits applied.
~~~

#### Stage D.5 — 편집팀 polish (사용자 영역 한국어 가독성)

After writing the audit report file, **before chat output**, invoke 편집팀 with mode B (polish, in-place):

```
Agent({
  subagent_type: "편집팀",
  prompt: `polish {audit_log_path}
사용자가 직접 읽는 audit 보고서다. 편집팀 모드 B 다듬기 — 판교체 정리·표기 일관성·호흡.
보존: issue 식별 (severity 🔴/🟡/🟢, aspect 이름, file:line ref, suggested fix 본문). 다듬기 대상: 한국어 본문 wording 만.`
})
```

편집팀이 in-place Edit 으로 마무리한 뒤 chat 출력 단계로. (단발성 — single-pass, in-place. snapshot X.)

Then print to chat (Korean), in ≤8 lines:

    ✓ /audit 완료 — {artifact short name} ({type})
    • Aspects: {comma-separated}
    • Total: 🔴 {N} / 🟡 {M} / 🟢 {K}
    • Report: {audit log path}
    • Verdict: {one-line}
    {if 🔴 > 0:}
    권장 후속: /autopilot-refine "{artifact short name} {fix prompt suggestion}"

### Stage E — Auto-fix chain (default behavior)

After Stage D's report write + chat output, **automatically trigger a fix flow** for the issues found — _unless `--report-only` was specified_.

**Behavior**:
1. **Skip conditions**: if `--report-only` is set, OR if Stage D produced 0 🔴 issues AND 0 🟡 issues (clean), skip Stage E. Print: `✓ Audit clean — no auto-fix needed.` and exit.
2. **Generate fix prompt**: synthesize a single prompt text describing the 🔴 + significant 🟡 issues. Format:
   ~~~
   audit 결과 자동 fix:
   - {issue 1 short description} → {suggested fix from report}
   - {issue 2 short description} → {suggested fix from report}
   ...
   Source audit report: {audit log path}
   ~~~
   Each line of the prompt corresponds to one issue from Stage D's "Issues by aspect" section. Include the audit log path so downstream skill can read the full detail.
3. **Dispatch by artifact type**:
   - **plans (code)** → invoke `autopilot-code` skill with `--mode dev` and the generated prompt as the task description.
   - **research** / **documents** → invoke `autopilot-refine` skill with the artifact name + generated prompt.
4. **Chat alert before dispatch**: print `▶ Auto-fix chain 시작 — {dispatched skill} (🔴 N + 🟡 M issues 반영)`. If user wants to stop, they can interrupt before the next skill runs.
5. **Logging**: append a single line to the audit log's "## Verdict" section: `**Auto-fix dispatched**: yes (→ {skill name}) | no (--report-only or clean)`.

**Why default is auto-chain**: the user's stated incident (5 factual drifts unnoticed across 20+ refine cycles) shows that "report-only" reports get ignored. Auto-chain provides a _forcing function_ — the user must explicitly opt out via `--report-only` to skip the fix. This matches the "빈칸 > 잘못 채우기" Principle 0 spirit at the system level.

**Why `--report-only` opt-out exists**: occasionally the user wants only inspection (e.g., handoff review, exploratory check) without committing to immediate edits. The flag preserves that path.

## Constraints

- **Audit pass is read-only** — Stage A-D never modify the audited artifact (the audit log is written under `_internal/audit/`). Stage E _dispatches a separate skill_ (`autopilot-code` or `autopilot-refine`) which then makes edits per its own confirmation flow. With `--report-only`, Stage E is skipped entirely.
- **No web fetch** — all lookups are local (`<artifact-root>/*` files only). Cards grep, Style Guide read, regex scan. Cost is small.
- **No agent invocation** — `/audit` is a single-Claude task. No 연구팀 / 품질관리팀 subagent calls. (Future enhancement may add `--qa` levels with agent-backed lint; out of scope for v1.)
- **Type-specific aspects** — research aspects do not run on documents artifacts and vice versa. `--scope cross-ref` on plans warns and skips.
- **Suggestion only (Stage A-D)** — every 🔴 / 🟡 finding may include a "Suggested fix" line. Stage E dispatches these suggestions to the appropriate skill, which follows its own protocol (autopilot-refine: default 자동 apply + STRUCT halt + 사후 git diff 검토; autopilot-code: phase QA gates + safety commit + final report).

## Examples

    # Full audit of the SE seminar document artifact
    /audit 2026-05-06_se-seminar-tfrestormer

    # Facts-only check of the same artifact (after a 20-cycle refine session)
    /audit 2026-05-06_se-seminar-tfrestormer --scope facts

    # Audit a research artifact's cards consistency
    /audit speech-enhancement-trends --scope facts

    # Read-only static audit of a code plan (skip test execution)
    /audit 2026-05-11_audit-skill-infra --scope all --read-only

    # Inspection only (no auto-fix)
    /audit 2026-05-06_se-seminar-tfrestormer --report-only

## When NOT to use

- 산출물을 _수정_하고 싶은 경우 → `/autopilot-refine`.
- 단일 typo / cosmetic 점검 → 그냥 `grep` / `Read`.
- Full pipeline 재실행 필요 → `/autopilot-{research,doc,code}` 또는 `--from <stage>`.
- 산출물 자체가 존재하지 않음 (사전 분석부터 필요) → `/analyze-project` 또는 `/autopilot-research`.

## Post-Audit Checklist

After audit, the auto-fix chain (Stage E) dispatches automatically. If you used `--report-only`:
1. 🔴 이슈 존재 → `/autopilot-refine "<fix prompt suggested by audit log>"` 또는 `/autopilot-code --mode dev "<fix>"` 직접 호출
2. 🟡 only → 사용자 판단으로 deferred or batch-fix
3. clean → 추가 조치 불필요
