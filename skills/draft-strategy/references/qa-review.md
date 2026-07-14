## QA Scaling

Infer the level from strategy scope. At Standard+, run the two reviewer roles in parallel:

- **Quality reviewer** (`품질관리팀`): completeness, logical soundness, venue norms, and reviewer coverage for rebuttals
- **Fact-checker** (`연구팀` subrole): verbatim comparison with in-artifact materials such as `analysis_project/paper/cards/*.md`, `analysis_project/doc/*/...`, and `research/{topic}/cards/*.md`; verify citation, venue, metric, year, and classification. [`research-team.md`](../../../adapters/claude/agents/research-team.md) lines 258–300 are the single source for the eight-row classification table.

| Level | Condition | Quality reviewer | Parallel fact-checker | Max rounds |
|---|---|---|---|---|
| **Quick** | `--intensity quick` | 1 fast reviewer, spot-check only | Skip | **1; do not reinvoke on 🔴** |
| **Light** | review/presentation, or report with ≤3 input paths | 1 fast reviewer | Skip | 2 |
| **Standard** | paper/report/proposal, or rebuttal with ≤3 reviewers | 1 deep reviewer | **1 fast fact-checker** | 2 |
| **Thorough** | rebuttal with ≥4 reviewers, or report/proposal with ≥10 inputs | 2 parallel deep reviewers | **1 fast fact-checker** | 2 |
| **Adversarial** | External review imminent—camera-ready, submission, public report—or explicit `--intensity adversarial` | 2 parallel deep reviewers + 1 external adversary (`codex-review-team` in the Claude adapter) | **1 fast fact-checker** | 2 + 1 external |

A fast fact-checker is sufficient because verbatim matching against artifact cards is narrow comparison work, not creative judgment.

## Selected Post-Strategy Review Pass

The log directory is the artifact root, parent of `strategy/`. Run `mkdir -p {log_dir}/_internal/strategy_reviews` before invoking QA.

After the `연구팀` agent returns:

1. **Invoke the selected quality/source-check reviewers.** Run them in parallel only when the QA budget selects more than one reviewer.

   **Quality reviewer prompt** using a deep or fast reviewer according to level:

   ```
   Review this document strategy for completeness and logical soundness.
   Strategy file: [path]. Mode: {mode}.
   For rebuttal mode, verify ALL reviewer points are addressed.
   Do NOT verify individual fact citations (model venue/year/metric) — that's the fact-checker's role.
   Write review to: {log_dir}/_internal/strategy_reviews/round_{N}_quality.md.
   Return ONLY the file path and a one-line verdict.
   ```

   **Fact-checker prompt** for a fast fact-checker, parallel at Standard/Thorough:

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

2. **Check both verdicts:**
   - No 🔴 → generate a language companion only when an explicit second-language, external-audience, or existing-workflow contract requires one.
   - `qa_level == quick` → exit after round 1 regardless of 🔴. Add findings under the functional compatibility heading `## 미해결 이슈`, then continue to companion generation only when that explicit contract exists.
   - Quality 🔴 → reinvoke `연구팀` with quality findings, up to two rounds.
   - Fact-check 🔴 → reinvoke `연구팀` with mandatory reference grounding and reread the named cards/PDFs, up to two rounds.
   - Both → reinvoke `연구팀` with combined findings.
3. If 🔴 remains after two rounds, add it under `## 미해결 이슈`, report it, and tag factual residuals `[FACT-RESIDUAL]`.
