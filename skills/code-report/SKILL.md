---
name: code-report
description: Generate a detailed change report from plan + dev logs — focuses on key changes, principles, and insights for future reference
argument-hint: "<plan name or path>"
metadata:
  group: sub
  fam: sub
  modes: []
  blurb: "코드 작업 사이클 결과 요약·보고 sub-skill"
---

## Plan Resolution (canonical — keep in sync with code-execute, code-test, code-report, code-refine, autopilot-code)
Resolve `$ARG` to a plan file path:
1. If it ends with `.md` → use as-is
2. If it's a directory path → append `/plan/plan.md`
3. Otherwise, fuzzy search: `ls -d .claude_reports/plans/*$ARG* 2>/dev/null`
   - **1 match** → use `{match}/plan/plan.md`
   - **Multiple matches** → prefer folder without `_audit`/`_fix_` suffix; if still multiple, ask user
   - **No match** → report error

## Language Rule
- All user-facing output in natural Korean (no translationese — write Korean natively, don't translate from an English draft).

## Model & QA Policy

**Writer: always sonnet.** The final report is a synthesis over artifacts that were already verified by prior pipeline stages (plan reviews in code-plan/code-refine, code reviews in code-execute phase gates, test reviews in code-test). The code-report content itself does NOT require a QA/review pass — inaccuracies (line-number drift, outdated follow-ups) are user-facing and can be corrected on read, without affecting the committed code. Spending opus/codex budget here is wasted.

| Level | Auto-detect condition | Action |
|---|---|---|
| **Light** | ≤5 steps, single variant | 1× 품질관리팀 (`model: "sonnet"`) writes the report |
| **Standard** | 6-15 steps, moderate scope | 1× 품질관리팀 (`model: "sonnet"`) writes the report |
| **Thorough** | >15 steps, cross-variant, or architectural | 1× 품질관리팀 (`model: "sonnet"`) writes the report |
| **Adversarial** | Cross-variant / shared modules / >20 steps | 1× 품질관리팀 (`model: "sonnet"`) writes the report |

QA level from plan frontmatter `qa_level` or `--qa` flag still flows in (for context logging), but in code-report it affects **only the prompt's context**, not the model or any post-write review. No codex review of the report. No parallel writers. No review loop.

## Delegate to 품질관리팀
Invoke the **qa-team** (품질관리팀) agent with `model: "sonnet"` (all levels) as a subagent with the following prompt:

```
Generate a final change report.

Plan file: {$ARG} (resolved via Plan Resolution above)
Log directory: {task root folder — grandparent of plan/plan.md}
Korean plan: {same directory as plan.md}/plan_ko.md
Report output: {log_directory}/final_report.md
Date: {YYYY-MM-DD}

Follow these instructions:

## Inputs
1. **Plan file**: the English plan
2. **Log directory**: Contains plan/ (plan.md, plan_ko.md, checklist.md) [T1], dev_logs/ (step_*.md) [T2], test_logs/ [T2], _internal/{plan_reviews,dev_reviews,test_reviews}/ [T3]
3. **Korean plan** (_ko.md): for section titles and user-facing descriptions

## Procedure
1. Read the plan file to understand the goal, current state analysis, and change plan.
2. Read the checklist (plan/checklist.md) to identify which steps succeeded, failed, or were skipped.
3. Read all step log files (dev_logs/step_*.md) to extract every code change (old → new) with its Decision rationale, files modified, and what each change accomplished.
4. Read QA review files (`_internal/dev_reviews/phase_*.md`) to extract issues found and how they were resolved.
5. **Documentation Update**: Update `.claude_reports/analysis_project/code/` for successfully completed steps only (produced/maintained by `/analyze-project --mode code`). Topic-based file mapping is project-specific — pick the existing topic doc that best matches each changed file. Common patterns:
   - Model / module files → `model_modules.md` (or matching topic doc)
   - Network / backbone files → `network_modules.md`
   - Loss / objective files → `loss_functions.md`
   - Data pipeline files → `dataset_pipeline.md`
   - Training entry points → `engine_training.md`
   - Inference entry points → `engine_inference.md`
   - Utility files → `utilities.md`
   - Overall design, config, data flow, cross-variant → `architecture.md`
   - Project structure, doc table, file renames → `CLAUDE.md`
   Update Interface Reference tables (signatures, callers, line numbers). Skip if no steps succeeded. If the project does not yet have an `analysis_project/code/` directory, skip this step and recommend the user run `/analyze-project --mode code` once to bootstrap the topic docs.
   **Verification**: Verify every class/function line number in the Interface Reference table against the **post-edit** source (use Grep or a fresh Read of the file *after* your own Step 5 edits complete). Line numbers from pre-edit reads, the plan, or dev logs may be stale.
6. **Confirm doc changes are real**: After step 5, run `git diff --stat -- .claude_reports/analysis_project/code/ CLAUDE.md` to confirm that documentation files were actually modified. If the diff is empty but you expected changes, something went wrong — re-read and re-edit the files. Report a doc update only after `git diff` confirms it.
7. **Read pipeline_summary.md** (log_directory/pipeline_summary.md) if it exists. Extract the Decision Points table for section 4.5. If the file does not exist or the table is empty, write "자율 판단 이벤트 없음 (클린 실행)" for section 4.5.
8. Synthesize the information into a report. Do NOT just list changes — explain the reasoning and connect them to the bigger picture.

## Report Structure

```
# 변경 보고서: {task name}
- **일시**: {YYYY-MM-DD} | **플랜**: {plan path} | **상태**: ✅/⚠️/❌

## 1. 변경 개요          — what was done and why (3-5 sentences)
## 2. 핵심 변경 사항     — grouped by logical category (not step number)
   ### 2.N {category} — {file/module}
   - **변경 내용** / **변경 이유** / **핵심 원리** / **영향 범위**
## 3. 설계 인사이트      — key takeaways for future work
## 4. QA 리뷰 요약       — 발견된 이슈 / 해결 방법 / 미해결
## 4.5 자율 판단 기록    — pipeline_summary.md의 Decision Points 테이블을 서사적 요약으로 합성. 자율 판단 이벤트가 없으면 "자율 판단 이벤트 없음 (클린 실행)"
## 5. 실패/스킵된 단계   — explain why, or "전체 단계 성공 ✅"
## 6. 향후 참고사항      — watch-outs and potential follow-ups
```

## Quality Guidelines
- Do NOT just summarize — extract insights. Focus on "why" and "what to remember".
- Be specific about impact — mention exact callers, tensor shapes, or config keys.
- Connect to project design when relevant.
- Write the report in Korean. Code identifiers, file paths, and technical terms stay in English.
- Aim for 1-3 pages total. Length should scale with change count: small plans (≤5 steps) can be 1 page; large refactors (>20 steps) may need 3.

Return ONLY the file path and a one-line summary. Do NOT return the full report content.
```

## Post-Report — Memory × Report Reconciliation
After the 품질관리팀 agent returns:

1. **Read the produced `final_report.md` once.** The file is short (1-3 pages, ≲1500 tokens) — cheap.

2. **Reconcile with your orchestration memory.** You already carry rich context from running code-plan → code-refine → code-execute → code-test through subagent returns and your own Bash/Edit/Read calls. Compare the report against that memory:
   - **Numbers**: step counts, 🔴 resolution rounds, test pass/fail counts, commit hashes, file counts.
   - **Line numbers**: if the report cites `file.py:NNN`, verify you remember the same location (drift is common).
   - **Status of follow-ups**: report may claim an item is "pending" when memory says it was resolved in a later round.
   - **Deviations**: did any subagent flag a deviation from the plan that the report missed?

2.5. **Invoke 편집팀 with mode B** (polish, in-place — 사용자 영역 한국어 가독성):

   호출 조건 (single source — `agents/editorial-team.md` 모드 B 호출 조건):
   - plan frontmatter `qa_level` 가 **standard / thorough / adversarial** 중 하나일 때만 호출. `quick` / `light` 는 _fastest path_ 의도라 skip.
   - skip 시 곧장 step 3 (relay) 진행.

   ```
   Agent({
     subagent_type: "편집팀",
     prompt: `polish {log_directory}/final_report.md
   사용자가 직접 읽는 변경 보고서다. 편집팀 모드 B 다듬기 — 판교체 정리·표기 일관성·호흡.
   보존: 변경 내용·변경 이유·핵심 원리·QA 리뷰 요약·자율 판단 기록 본문 (수치·file:line·decision 본문). 다듬기 대상: 한국어 wording 만.`
   })
   ```

   편집팀이 in-place Edit 으로 마무리한 뒤 step 3 진행. (단발성 — single-pass, snapshot X.)

3. **Relay a concise Korean brief to the user** (2-3 paragraphs, NOT just the file path). The brief should:
   - State the final status (done/partial/failed) and final commit hash
   - Highlight 3-5 concrete deliverables / changes
   - Flag any discrepancies between memory and report explicitly (e.g., "리포트 본문엔 L1195로 기재됐는데 실제 HEAD 기준 L1207 — 리포트 오기")
   - Suggest obvious next steps

4. **The report gets reconciliation (step 2) only — no separate QA pass.** Inaccuracies are user-facing and can be corrected on read. The reconciliation step (2) is the lightweight safety net.

Rationale: the main Claude's memory is the richest orchestration-time record, and the report is the fact-checked persistent artifact. A cheap cross-check between the two gives the user a summary that benefits from both sources — without paying for a full QA/codex pass on the report itself.

## Task
Generate report for: $ARG
