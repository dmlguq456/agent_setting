## QA Scaling
Auto-detect from strategy scope. Two reviewer roles run **in parallel** at Standard+:
- **Quality reviewer** (품질관리팀): completeness / logical soundness / venue norms / reviewer-coverage (rebuttal)
- **Fact-checker** (연구팀 subrole): in-artifact materials verbatim 대조 (`analysis_project/paper/cards/*.md`, `analysis_project/doc/*/...`, `research/{topic}/cards/*.md`), citation/venue/metric/year 검증. classification 8-row table 의 canonical 정의는 [`research-team.md`](../../adapters/claude/agents/research-team.md) L258-300 single source.

| Level | Condition | Quality reviewer | Fact-checker (parallel) | Max rounds |
|---|---|---|---|---|
| **Quick** | (manual via `--qa quick` only) | 1× fast reviewer, spot-check만 | _skip_ | **1 (no re-invoke even on 🔴)** |
| **Light** | review/presentation mode, or report with ≤3 input paths | 1× fast reviewer | _skip_ | 2 |
| **Standard** | paper/report/proposal mode, or rebuttal with ≤3 reviewers | 1× deep reviewer | **1× fast fact-checker** | 2 |
| **Thorough** | rebuttal with ≥4 reviewers, or report/proposal with ≥10 input items (papers + doc materials) | 2× deep reviewers in parallel | **1× fast fact-checker** | 2 |
| **Adversarial** | external-review-imminent (camera-ready / submission / public report), or manual via `--qa adversarial` | 2× deep reviewers in parallel + 1× external adversary (`codex-review-team` in Claude adapter) | **1× fast fact-checker** | 2 + external 1 |

**Why fast fact-checker**: in-artifact cards verbatim 대조는 _창의적 판단_이 아닌 _단순 매칭 작업_이라 fast role 로 충분, 비용 효율적.

## Selected Post-Strategy Review Pass (max 2 revision rounds; quick = 1 round)
The log directory is the artifact root folder (parent of `strategy/`).
- `mkdir -p {log_dir}/_internal/strategy_reviews` before invoking QA.

After the 연구팀 agent returns:
1. **Invoke selected quality/source-check reviewers** (parallel only when the selected QA budget calls for more than one reviewer):

   **Quality reviewer prompt** (deep or fast reviewer per level):
   ```
   Review this document strategy for completeness and logical soundness.
   Strategy file: [path]. Mode: {mode}.
   For rebuttal mode, verify ALL reviewer points are addressed.
   Do NOT verify individual fact citations (model venue/year/metric) — that's the fact-checker's role.
   Write review to: {log_dir}/_internal/strategy_reviews/round_{N}_quality.md.
   Return ONLY the file path and a one-line verdict.
   ```

   **Fact-checker prompt** (fast fact-checker, parallel — Standard/Thorough only):
   ```
   You are a fact-check focused reviewer — NOT narrative quality.
   Strategy file: [path]. Mode: {mode}. Discovered inputs: {inputs_paths_list}.

   For every domain claim in the strategy (citation / model name / venue / year /
   metric / dataset / lineage / classification), open the corresponding ground-truth
   source and verbatim compare:
   - Paper analyses: `<artifact-root>/analysis_project/paper/*.md` (if exists — single source of truth, produced by `/analyze-project --mode paper`)
   - Original PDFs: only if listed in `--inputs` AND paper analyses lack the specific fact
   - Reviewer comments (rebuttal mode): {analysis_dir}/reviewer_analysis.md

   Output a single table (no narrative):
   | Section | Claim in strategy | Source (file:line or section) | Match (✅/❌) | Severity (🔴/🟡) |

   Do NOT comment on completeness, narrative arc, or strategic soundness
   — that's the quality reviewer's job. Stay narrowly on fact verification.

   Fast fact-checker mode: table-only output. Limit to ~30 most material claims.

   Write to: {log_dir}/_internal/strategy_reviews/round_{N}_factcheck.md.
   Return ONLY path + one-line verdict.
   ```

2. **Check verdict (both reviewers):**
   - **No 🔴 from either**: proceed to Korean Version Generation.
   - **qa_level == quick**: after round 1, exit regardless of 🔴. Add 🔴 issues to `## 미해결 이슈` section in the strategy. Proceed to Korean Version Generation.
   - **🔴 from quality reviewer**: re-invoke 연구팀 with quality findings (max 2 rounds).
   - **🔴 from fact-checker**: re-invoke 연구팀 with **mandatory ref-grounding** (re-read named cards/PDFs). Max 2 rounds.
   - **🔴 from both**: re-invoke 연구팀 with combined findings.
3. **If 🔴 issues remain after 2 rounds**: Add to `## 미해결 이슈` section in the strategy, report to user. Tag fact-check residuals with `[FACT-RESIDUAL]`.
