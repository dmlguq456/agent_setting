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
