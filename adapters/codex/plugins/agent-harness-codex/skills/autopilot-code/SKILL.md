---
name: autopilot-code
description: "Use for autopilot-code: 코드 작업 entry. spec 컨텍스트를 감지하고 plan→execute→test→report 흐름을 닫는다."
---

# autopilot-code

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-code.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info autopilot-code`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/autopilot-code.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info autopilot-code`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-code`
- Supported modes: `dev, debug, audit`
- Argument shape: `--mode dev|debug <task/plan/error description> [--from <step>] [--intensity direct|quick|standard|strong|thorough|adversarial] [--qa quick|light|standard|thorough|adversarial] [--user-refine]`
- Portable meaning: 코드 작업 entry. spec 컨텍스트를 감지하고 plan→execute→test→report 흐름을 닫는다.

## Portable Contract

- Invocation semantics: _코드 작업 일반_ entry — 라이브러리·연구 코드·앱 모두 커버. 신규·기존 코드 무관 (cwd 자동 감지). dev (기능 추가·신규) / debug (진단·수정) 두 mode. spec/ 컨텍스트 발견 시 spec 자동 Read + spec mode 별 분기: app mode → 디자인팀 critic + DB migration 안전 + push 자동 deploy. library mode → 공개 API 일관성 점검. cli mode → 명령·옵션 일관성. research mode → 재현성·configs·metric 검증. 코드 외 결정 (PRD·스택·skeleton·ship setup) 은 autopilot-spec 영역. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.



## Projected Portable Details

## Artifact Ownership

Use the shared artifact root rule: prefer `.agent_reports/`; use legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not.

Code work normally writes to `<artifact-root>/plans/<date>_<slug>/`, even when a `spec/` directory exists. `spec/` is the blueprint bucket; `plans/` is the work-cycle bucket.

Artifact intensity policy:

- `direct`: no new plan root, no `plan.md`, and no durable pipeline artifact unless the adapter or current repo policy explicitly requires one;
- `quick`: no durable `plan.md` by default; record a short summary/evidence only when a work-cycle artifact is already required;
- `standard+`: create or resume `<artifact-root>/plans/<date>_<slug>/`.

Required public artifacts for `standard+` work cycles:

- `plan.md` at the plan root;
- `checklist.md` at the plan root when the plan is multi-step;
- `pipeline_summary.md` at the plan root before completion;
- `dev_logs/` and `test_logs/` for implementation and verification evidence.

Internal artifacts belong under `_internal/`, including plan reviews, dev reviews, test reviews, retry notes, raw command logs, and model/team deliberation notes.

## Role Requirements

Use portable role names from `roles/README.md` and `core/CONVENTIONS.md`. Concrete model names, subagent frontmatter, and runtime-specific tool lists belong in adapter files.

Minimum role mapping:

- planning: planning role for `code-plan`;
- implementation: development role for `code-execute`;
- verification: QA role for `code-test`;
- review: QA/reviewer role for plan, code, and test review;
- app UI changes: design role as critic or handoff verifier when design artifacts exist.

Pipeline intensity is the primary ceremony selector for this entrypoint. Use `direct` for inline fixes with no plan stage, `quick` for micro-plan plus plan-check-lite, `standard` for the normal closed loop, `strong` for the normal loop plus one risk-focused independent review, and `standard+` for owner-worker orchestration that should open bounded depth-2 verifier/planner work when separable, with `thorough|adversarial` expanding to multi-perspective or adversary workers. QA level remains an assurance override or compatibility input; it changes `plan-check`, selected independent reviews, and `code-test` rigor, but must not force a monolithic full pipeline by itself. Concrete models remain adapter-specific.

## Guard Requirements

Adapters must preserve the portable invariants relevant to this capability:

- resolve artifact root through `utilities/artifact-root.sh` or equivalent logic;
- enforce git/worktree safety before edits;
- enforce artifact ordering before new durable artifacts;
- enforce spec-read gating when this capability changes spec-backed code or specs;
- use DB memory paths, not runtime-native memory files.

Additional code-entry gates:

- before any code edit, classify the request against existing `spec/prd.md` when present and emit a one-line `spec-significance` verdict;
- route `spec-significant` changes through `autopilot-spec` update before implementation unless the user explicitly defers;
- detect whether `spec/pipeline_state.yaml` has changed since the last relevant plan and re-read newer spec/design artifacts before editing;
- for app mode, treat design tokens and handoff artifacts as source contracts, not suggestions;
- for destructive DB/schema/migration work, explain the command and risk, but do not auto-run destructive operations without explicit user approval;
- for non-trivial feature, multi-file, or module work, use the runtime's isolated-worktree or equivalent dispatch policy from `core/OPERATIONS.md`.

## Portable Procedure

1. Parse arguments and infer `dev`, `debug`, or `audit` when the adapter allows natural-language entry.
2. Resolve artifact root and create or resume a `plans/<date>_<slug>/` work cycle.
3. Run git/worktree preflight and remember the starting `HEAD`.
4. If `spec/` exists, read `spec/prd.md` plus relevant mode contracts before planning.
5. Emit `spec-significance: within-spec` or `spec-significance: SPEC-SIGNIFICANT (...)`.
6. Select the stage graph from pipeline intensity, then map common stages to code sub-capabilities. `direct` skips `code-plan`; `quick` runs as a depth-1 one-shot worker with an inline micro-plan and plan-check-lite; `standard+` uses `code-plan`, optional `code-refine`, `code-execute`, `code-test`, and `code-report` according to the selected graph, QA override, and resume point. For `standard+`, a depth-1 capability owner may dispatch bounded depth-2 planner/verifier/adversary workers when the task is separable and must synthesize their short reports before final write-back. `direct` stays inline; `quick` is a depth-1 one-shot worker unless explicitly escalated.
7. Before each durable write-back or commit, re-run git/worktree safety and stop if `HEAD` or merge state changed unexpectedly.
8. Record implementation evidence and verification results in `pipeline_summary.md`.

## Mode-Specific Semantics

| Spec mode | Extra requirement |
|---|---|
| `app` | Use design handoff and token artifacts when present; UI changes get design review; destructive migration work requires explicit approval. |
| `library` | Check public API, exports, semver impact, compatibility notes, and examples. |
| `api` | Check endpoint/body/error/auth/rate-limit contracts and security implications. |
| `cli` | Check command names, options, input/output formats, and exit codes. |
| `research` | Check train/eval entry points, configs, seeds, reproducibility commands, and metrics. |

When no spec exists, infer mode lightly from project files, report the inference, and keep the stricter spec-only gates disabled.


## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before capability routing/spec-changing work: `adapters/codex/bin/preflight.sh route autopilot-code [cwd] [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability autopilot-code [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh status [cwd] [session-id]`, `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]`, and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
