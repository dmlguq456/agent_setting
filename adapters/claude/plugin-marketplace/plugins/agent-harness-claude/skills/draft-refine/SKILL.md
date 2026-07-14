---
name: draft-refine
description: "초안 정련·다듬기 sub-skill — 편집팀 검수 경유"
argument-hint: "<strategy or draft name or path>"
metadata:
  group: sub
  fam: sub
  modes: []
  blurb: "초안 정련·다듬기 sub-skill — 편집팀 검수 경유"
---

> **산출물 폴더 컨벤션**: [CONVENTIONS.md §5](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier). 본 skill은 review 로그를 `_internal/strategy_reviews/` 또는 `_internal/draft_reviews/`에 기록. 버전 스냅샷은 modern artifact면 `_internal/versions/v{N}/`, legacy artifact면 `_v{N}.md` 형제 (자동 감지).

## Document Resolution
Resolve `$ARGUMENTS` to document file paths. Detect whether this is a **strategy** or **draft** refinement:

**Auto-detect document type**:
- If path contains `/draft/` → draft mode (resolve `draft.md` + `draft_ko.md`)
- If path contains `/strategy/` → strategy mode (resolve `strategy.md` + `strategy_ko.md`)
- If path is a directory → default to strategy mode

**Resolution rules** — always resolve BOTH English and Korean files:
1. If it ends with `.md` → use as-is; derive the other file by path swap (`draft.md` ↔ `draft_ko.md`, or `strategy.md` ↔ `strategy_ko.md`)
2. If it's a directory path → append `/strategy/strategy.md` (English) and `/strategy/strategy_ko.md` (Korean)
3. Otherwise, fuzzy search: `ls -d <artifact-root>/documents/*$ARGUMENTS* 2>/dev/null`
   - **1 match** → use `{match}/strategy/strategy.md` and `{match}/strategy/strategy_ko.md`
   - **Multiple matches** → ask user
   - **No match** → report error

## Language Rule
- User-facing artifacts follow the audience-language-first rule in
  `<agent-home>/roles/response-policy.md`. Preserve the target artifact's
  existing language unless the task explicitly changes it; this skill imposes
  no fixed chat locale.

## Pre-Refine: Versioning Setup

Before invoking 연구팀, the orchestrator establishes versioning. Snapshots go to `{artifact_root}/_internal/versions/v{N}/<relative-path>` (per [CONVENTIONS.md §5](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3)). The legacy `_v{N}.md` sibling pattern is **deprecated** for new artifacts.

1. **Determine next version number**:
   - **Modern** (`{artifact_root}/_internal/` exists): scan `_internal/versions/` for `v{N}` subdirs. Find max N. If none → `next_version = 2`.
   - **Legacy** (artifact has `*_v{N}.md` siblings AND no `_internal/`): scan for `{ko_path.stem}_v{N}.md` siblings. Find max N. If none → `next_version = 2`.
   - **New**: if neither exists, treat as modern, `next_version = 2`. mkdir -p `_internal/versions/`.

2. **Snapshot current state as previous version** (skip if a snapshot for `prev_version` already exists):
   - **Modern**:
     ```bash
     mkdir -p {artifact_root}/_internal/versions/v{prev_version}/{ko_relative_subdir}
     cp {ko_path} {artifact_root}/_internal/versions/v{prev_version}/{ko_relative_subdir}/{ko_filename}
     cp {en_path} {artifact_root}/_internal/versions/v{prev_version}/{en_relative_subdir}/{en_filename}
     ```
     where `{ko_relative_subdir}` is e.g. `strategy/` or `draft/`.
   - **Legacy**:
     ```bash
     cp {ko_path} {ko_path.parent}/{ko_path.stem}_v{prev_version}.md
     cp {en_path} {en_path.parent}/{en_path.stem}_v{prev_version}.md
     ```
3. **Pass `next_version`, `prev_version`, convention mode, and snapshot paths to 연구팀** in the prompt below.

## Delegate to 연구팀

전체 위임 프롬프트 템플릿(Memo Detection·MANDATORY Ref-Grounding·Output Versioning·Changelog YAML 계약·Other rules) = [references/delegate-prompt.md](references/delegate-prompt.md) — 로드해 `{...}` 변수 치환 후 **research-team(연구팀) subagent 에 verbatim 호출**. Changelog worked example(legacy→frontmatter 이전) = [references/changelog-example.md](references/changelog-example.md).

핵심 계약 요약(checkable): changelog 는 top-of-file HTML 주석이 아니라 frontmatter `changelog:` YAML 배열(newest-first, block scalar `|` entries) — 파일은 반드시 `---` 로 시작. 매 memo 는 ref-grounding(출처 재확인) 후 적용/override 판단, override 시 changelog 에 사유 기록.

## QA Scaling
Auto-detect from sections changed. Two reviewer roles run **in parallel** at Standard+:
- **Quality reviewer** (품질관리팀): narrative arc / cohesion / audience fit / strategy alignment
- **Fact-checker** (연구팀 subrole): cards/PDFs verbatim 대조, venue/year/metric/lineage/classification 검증. classification 8-row table 의 canonical 정의는 [`research-team.md`](../../adapters/claude/agents/research-team.md) L258-300 single source.

| Level | Condition | Quality reviewer | Fact-checker (parallel) | Max rounds |
|---|---|---|---|---|
| **Quick** | (via `--intensity quick` — autopilot skips refine entirely in quick mode) | 1× fast reviewer, spot-check만 | _skip_ | **1 (no re-invoke even on 🔴)** |
| **Light** | ≤3 sections | 1× fast reviewer | _skip_ (quality reviewer covers basic spot-checks) | 2 |
| **Standard** | 4+ sections | 1× deep reviewer | **1× fast fact-checker** | 2 |
| **Thorough** | Major overhaul or new evidence | 2× deep reviewers in parallel | **1× fast fact-checker** | 2 |
| **Adversarial** | external-review-imminent (camera-ready / submission), or `--intensity adversarial` explicitly specified | 2× deep reviewers in parallel + 1× external adversary (`codex-review-team` in Claude adapter) | **1× fast fact-checker** | 2 + external 1 |

**Why fast fact-checker**: card verbatim 대조는 _창의적 판단_이 아닌 _단순 매칭 작업_이라 fast role 로 충분하고, 비용 효율적이다.

## Selected Post-Refine Review Pass (max 2 rounds; quick = 1 round)
After 연구팀 returns:
1. **Resolve log dir**: artifact root (e.g., `<artifact-root>/documents/2026-03-25_foo/`).
   - For strategy refinement: `mkdir -p {log_dir}/_internal/strategy_reviews`
   - For draft refinement: `mkdir -p {log_dir}/_internal/draft_reviews`
2. **Invoke selected quality/source-check reviewers** (parallel only when the selected QA budget calls for more than one reviewer):

   **Quality reviewer prompt** (deep or fast reviewer per level):
   ```
   Review changed sections — _quality / cohesion / audience fit_ focus.
   {Doc type}: [path]. Changed: [list]. For rebuttals, verify all reviewer points still addressed.
   Do NOT verify individual fact citations (model venue/year/metric) — that's the fact-checker's role.
   Write to: {log_dir}/{review_subdir}/refine_round_{N}_quality.md.
   Return ONLY path + one-line verdict.
   ```

   **Fact-checker prompt** (fast fact-checker, parallel — Standard/Thorough only):
   ```
   You are a fact-check focused reviewer — NOT narrative quality.
   {Doc type}: [path]. Changed sections: [list].

   For every domain claim in the changed sections (model name / venue / year /
   metric / lineage / classification), open the corresponding ground-truth source
   and verbatim compare against the deliverable:
   - Paper analyses: `<artifact-root>/analysis_project/paper/*.md` (single source of truth, produced by `/analyze-project --mode paper`)
   - Original PDFs: only if paper analyses lack the specific fact
   - Strategy/analysis: {artifact_root}/strategy|analysis/

   Output a single table (no narrative):
   | Slide/Section | Claim in deliverable | Source (file:line or section) | Match (✅/❌) | Severity (🔴/🟡) |

   Do NOT comment on writing quality, narrative arc, or audience appropriateness
   — that's the quality reviewer's job. Stay narrowly on fact verification.

   Fast fact-checker mode: table-only output, no extended discussion. Limit to
   ~30 most material claims if changed sections exceed 10.

   Write to: {log_dir}/{review_subdir}/refine_round_{N}_factcheck.md.
   Return ONLY path + one-line verdict (e.g., "factcheck.md — 🟢 28/28 claims verified" or
   "factcheck.md — 🔴 3/28 claims fail (Slide N PASE venue, ...)").
   ```

3. **Check verdict (both reviewers):**
   - **No 🔴 from either**: Report to user (both verdicts inline).
   - **qa_level == quick**: After round 1, exit regardless of 🔴. Add 🔴 issues to `## 미해결 이슈`. Report to user.
   - **🔴 from quality reviewer**: Re-invoke 연구팀 with quality findings. Max 2 rounds.
   - **🔴 from fact-checker**: Re-invoke 연구팀 with **mandatory ref-grounding** instruction (re-read the named cards/PDFs). Max 2 rounds.
   - **🔴 from both**: Re-invoke 연구팀 with combined findings. Max 2 rounds.
4. **If 🔴 remain after 2 rounds**: Add to `## 미해결 이슈`, report which sections changed, which issues resolved/unresolved and why. Tag fact-check residuals with `[FACT-RESIDUAL]` for downstream visibility.

## Task
Refine the document at: $ARGUMENTS
