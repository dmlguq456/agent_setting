---
name: code-plan
description: "코드 분석 후 상세 구현 plan 작성 — 기획팀 경유 sub-skill"
argument-hint: "<task description> [--qa quick|light|standard|thorough|adversarial]"
metadata:
  group: sub
  fam: sub
  modes: []
  blurb: "코드 분석 후 상세 구현 plan 작성 — 기획팀 경유 sub-skill"
---

> Caller note: planning benefits from `high` or `xhigh` effort; lower effort may miss call sites in cross-file analysis.

> **Stage-session entry (`standard+` dispatch, spec/stage-dispatch SD-2)**: this stage runs either in-session (Skill tool) or as its own depth-2 headless session dispatched by the autopilot-code conductor. Its only inputs are the task description (args) and the artifact tree (`<artifact-root>/plans/`) — never prior-stage conversation context. Write class: `plan/plan.md`·`plan/plan_ko.md`·`_internal/plan_reviews/`. 기획팀 delegation below stays **inside** this session.

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

## Plan-Check Assurance
If `$ARGUMENTS` contains `--qa quick|light|standard|thorough|adversarial`, use that level and strip the flag from the task description. Otherwise infer the assurance level from the caller's selected intensity and plan risk. `--qa` is not a stage graph selector; `code-plan` only runs when the caller already selected a durable `standard+` plan graph. `direct` skips this skill, and `quick` uses inline micro-plan plus plan-check-lite in the caller.

The log directory is the task root folder (parent of `plan/`). Example: `<artifact-root>/plans/2026-03-18_task/plan/plan.md` → log dir is `<artifact-root>/plans/2026-03-18_task/`. Run `mkdir -p {log_dir}/_internal/plan_reviews` before invoking an independent review.

| QA level | Plan-check action | Fix behavior |
|---|---|---|
| `quick` | Should normally not reach `code-plan`. If invoked directly, run a single fast sanity review or self-check. | Record residual concerns in the plan; no repeated fix loop. |
| `light` | One focused fast reviewer or equivalent self-check. | One correction pass only if the issue blocks execution. |
| `standard` | Lightweight independent plan review focused on feasibility, missing steps, and concrete verification commands. | At most one correction pass. |
| `thorough` | Deeper or multi-axis plan review only when `intensity=thorough` selected it. | Up to two correction passes; synthesize review outputs before refining. |
| `adversarial` | Thorough plan review plus explicit adversary/failure-mode/security critique when the adapter can prove it ran. | Explicit `--qa adversarial` fails loudly if unavailable; auto escalation falls back to thorough. |

After the 기획팀 agent returns:
1. Decide whether the selected graph actually calls for independent plan review. If not, run an inline plan-check and proceed to mirror generation.
2. If independent review is selected, invoke 품질관리팀 plan-review with the selected focus and write to `{log_dir}/_internal/plan_reviews/round_{N}.md`. Use separate reviewers when the selected standard+ owner-worker graph opens bounded depth2 review; thorough/adversarial expands that to multi-axis review.
3. If review finds blocking issues, re-invoke 기획팀 for one bounded correction pass (`standard`) or up to the selected budget (`thorough|adversarial`). Do not loop merely because a QA level exists.
4. If unresolved issues remain after the selected budget, add them to the plan's risk/unresolved section and proceed only when the caller can safely handle the risk.

> Record any user-facing pause (e.g., active-plan ambiguity) so the pipeline skill can surface it in pipeline_summary.md.

## Mirror Generation (편집팀 — conditional)

코드 plan 은 _코드 식별자 + 단계 설명_ 묶음 — primary language 는 English (코드 자체가 영문 자연). 한국어 사용자 검토용 mirror 가 보통 필요. 사용자가 영문 plan 만 본다고 명시한 경우 mirror 생성 skip.

**Skip condition**: 사용자가 영문 plan 만 검토한다고 명시 또는 영문 사용자.

**Trigger** (default for 한국어 사용자): plan.md 영문 + 한국어 mirror 필요.

```
모드 A — 영문에서 국문으로 옮기기.
영문 plan 경로: {plan_path}
국문 출력 경로: {same directory}/plan_ko.md
<agent-home>/adapters/claude/agents/editorial-team.md 의 모드 A 절차를 따른다.
<agent-home>/adapters/claude/agents/editorial-team.md 의 판교체 회피 절을 강제 적용. 사용자 표기 선호는 `mem profile 02_paper_writing_style` 보조 참조.
코드 식별자·파일 경로·라이브러리 이름은 영어 그대로, 그 외 일반 표현은 한국어로.
section 제목 매핑: Goals → 목표, Current State → 현황 분석, Change Plan → 변경 계획, Risks → 리스크, Verification → 검증 방법.
완료 시 파일 경로 + 한국어 요약 3-5 줄 + 의도적으로 한 표기 결정 한두 개만 돌려준다.
```

Then report to the user: plan path(s) + summary + QA verdict.

## Task
$ARGUMENTS
