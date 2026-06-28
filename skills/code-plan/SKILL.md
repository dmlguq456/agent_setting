---
name: code-plan
description: Create a detailed implementation plan based on actual codebase
argument-hint: "<task description> [--qa quick|light|standard|thorough|adversarial]"
metadata:
  group: sub
  fam: sub
  modes: []
  blurb: "코드 분석 후 상세 구현 plan 작성 — 기획팀 경유 sub-skill"
---

> Caller note: planning benefits from `high` or `xhigh` effort; lower effort may miss call sites in cross-file analysis.

## Language Rule
- All user-facing output in natural Korean (no translationese — write Korean natively, don't translate from an English draft).

## Pre-Check
Check if a similar plan already exists in `<artifact-root>/plans/`. Behavior depends on plan status:

- `active`: Always ask the user — "기존에 진행 중인 plan이 있습니다. 이어서 진행할까요, 새로 만들까요?" Do NOT proceed until confirmed.
- `done`/`failed`: Note it for reference and auto-proceed with new plan creation (no prompt).
- `partial`: Auto-create a new plan covering only the failed steps (read `failed_steps` from plan frontmatter). No prompt.

> Record any user-facing pause for the pipeline_summary.md Decision Points table.

## Delegate to 기획팀
Invoke the **plan-team** (기획팀) agent as a subagent with the following prompt:

```
Plan mode. Create a new implementation plan.

Task: {$ARGUMENTS}
Save English plan to: <artifact-root>/plans/{YYYY-MM-DD}_{short-task-name}/plan/plan.md
Date: {YYYY-MM-DD}
{If a done/failed/partial plan exists: "Reference previous plan: [path], status: [status]"}
{If partial: "Failed steps from previous execution: [list from plan frontmatter failed_steps]"}

Read all relevant source files, analyze the current state, and create the plan.
Write the plan files directly. Return ONLY the file paths and a 3-5 line Korean summary. Do NOT return the plan content itself.
```

The agent writes the plan file directly; the orchestrator only receives paths and a summary.

## QA Scaling
If `$ARGUMENTS` contains `--qa quick|light|standard|thorough|adversarial`, use that level and strip the flag from the task description. Otherwise, auto-detect from the plan's scope. When `qa_level` is set in plan frontmatter, it overrides auto-detect.

| Level | Auto-detect condition | Action |
|---|---|---|
| **Quick** | (manual only — never auto-selected) | 1× fast reviewer (Claude adapter: 품질관리팀 `model: "sonnet"`), single pass, **max 1 review round** (no iteration even if 🔴 found — 🔴 are recorded as 미해결 이슈 and loop exits) |
| **Light** | ≤3 steps, mechanical, single-variant | 1× fast reviewer |
| **Standard** | 4-10 steps, logic changes, single module | 1× deep reviewer |
| **Thorough** | >10 steps, cross-module/variant, architectural | 2-3× reviewers in parallel: Agent A correctness (deep), B completeness (fast), C risk (deep, optional, >15 steps); each writes `round_{N}_{focus}.md`; all 🔴 issues must be resolved |
| **Adversarial** | Cross-variant (SE+SS+CSS), shared modules (utils/, network.py), or >20 steps with architectural impact — **AND external adversary available** | Thorough-level 품질관리팀 + 1× external adversary (`codex-review-team` in Claude adapter) in parallel; external review writes adapter-specific review log; all 🔴 from ANY agent must be resolved |

**External adversary availability check**: Before selecting Adversarial, run the adapter availability check (Claude adapter: `codex --version`, suppress stderr). If unavailable, fall back to Thorough silently. This check is skipped if `--qa adversarial` is explicitly specified (fail loudly instead).

## Post-Plan Review Loop (max 3 revision rounds; quick = 1 round)

The log directory is the task root folder (parent of `plan/`). Example: `<artifact-root>/plans/2026-03-18_task/plan/plan.md` → log dir is `<artifact-root>/plans/2026-03-18_task/`. Run `mkdir -p {log_dir}/_internal/plan_reviews` before invoking QA.

**Round counting:** Initialize `round = 0`. A round = one plan-team fix → QA review cycle; all parallel Thorough agents count as one round. Increment `round` only when QA is re-invoked after a revision. "max 3 rounds" means 기획팀 is invoked at most 3 times to fix issues. **`quick` mode**: max rounds = 1 — after the single review pass, exit regardless of 🔴 (record residuals as 미해결 이슈 and skip the fix-round).

**QA level lock:** QA level is determined once at loop start; only upward escalation allowed (no downgrade). If `--qa` was NOT specified, the orchestrator MAY upgrade once (starting round 2) when 🔴 count ≥3 in the one-line verdict (no review file reading needed); round counter does NOT reset. If `--qa` was manually specified, no change allowed. `quick` is never auto-upgraded (user opted in for fastest path).

After the 기획팀 agent returns:
1. **Assess QA level** from plan scope per the QA Scaling table above.
2. **Invoke 품질관리팀:** Prompt: "Review this plan in plan review mode for feasibility. Plan file: [plan_path]. Write review results to: [log_dir]/_internal/plan_reviews/round_{N}.md. Return ONLY the file path and a one-line verdict."
   - Light: use fast reviewer (Claude adapter: pass `model: 'sonnet'`). Thorough: 2-3 parallel agents with focus suffix and separate output files; use fast reviewer for the B (completeness) agent and deep reviewer for A (correctness) and C (risk). Do NOT read the review file unless relaying verdict to user.
3. **Check one-line verdict:**
   - **No 🔴**: Loop ends → proceed to Korean Version Generation.
   - **🔴 found AND qa_level == quick**: Loop ends (no fix-round). Invoke 기획팀: "Refine mode. Add 🔴 issues from {log_dir}/_internal/plan_reviews/round_1.md to the plan's 리스크 section under ## 미해결 이슈. Return brief Korean summary." Then proceed to Korean Version Generation.
   - **🔴 found**: Re-invoke 기획팀: "Refine mode. Plan file: {plan_path}. QA review: {log_dir}/_internal/plan_reviews/round_{N}.md. Fix 🔴 issues. Return only changed steps + brief Korean summary." Increment `round`, re-invoke 품질관리팀. Repeat until no 🔴 or `round >= 3`.
4. **If 🔴 remain after `round >= 3`**: Auto-proceed — invoke 기획팀: "Refine mode. Add remaining 🔴 issues to the plan's 리스크 section under ## 미해결 이슈. Return brief Korean summary." Then report to user: plan path, resolved issues, and unresolved issues with reasons.

> Record any user-facing pause (e.g., active-plan ambiguity) so the pipeline skill can surface it in pipeline_summary.md.

## Mirror Generation (편집팀 — conditional)

코드 plan 은 _코드 식별자 + 단계 설명_ 묶음 — primary language 는 English (코드 자체가 영문 자연). 한국어 사용자 검토용 mirror 가 보통 필요. 사용자가 영문 plan 만 본다고 명시한 경우 mirror 생성 skip.

**Skip condition**: 사용자가 영문 plan 만 검토한다고 명시 또는 영문 사용자.

**Trigger** (default for 한국어 사용자): plan.md 영문 + 한국어 mirror 필요.

```
모드 A — 영문에서 국문으로 옮기기.
영문 plan 경로: {plan_path}
국문 출력 경로: {same directory}/plan_ko.md
<agent-home>/agents/editorial-team.md 의 모드 A 절차를 따른다.
<agent-home>/agents/editorial-team.md 의 판교체 회피 절을 강제 적용. 사용자 표기 선호는 `mem profile 02_paper_writing_style` 보조 참조.
코드 식별자·파일 경로·라이브러리 이름은 영어 그대로, 그 외 일반 표현은 한국어로.
section 제목 매핑: Goals → 목표, Current State → 현황 분석, Change Plan → 변경 계획, Risks → 리스크, Verification → 검증 방법.
완료 시 파일 경로 + 한국어 요약 3-5 줄 + 의도적으로 한 표기 결정 한두 개만 돌려준다.
```

Then report to the user: plan path(s) + summary + QA verdict.

## Task
$ARGUMENTS
