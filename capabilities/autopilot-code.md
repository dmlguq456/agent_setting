# Capability: autopilot-code

This is the portable capability contract for `autopilot-code`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `autopilot-code` |
| Group | `entry` |
| Supported modes | `dev, debug, audit` |
| Portable meaning | 코드 작업 entry. spec 컨텍스트를 감지하고 plan→execute→test→report 흐름을 닫는다. |
| Argument shape | `--mode dev|debug <task/plan/error description> [--from <step>] [--qa quick|light|standard|thorough|adversarial] [--user-refine]` |

## Invocation Semantics

_코드 작업 일반_ entry — 라이브러리·연구 코드·앱 모두 커버. 신규·기존 코드 무관 (cwd 자동 감지). dev (기능 추가·신규) / debug (진단·수정) 두 mode. spec/ 컨텍스트 발견 시 spec 자동 Read + spec mode 별 분기: app mode → 디자인팀 critic + DB migration 안전 + push 자동 deploy. library mode → 공개 API 일관성 점검. cli mode → 명령·옵션 일관성. research mode → 재현성·configs·metric 검증. 코드 외 결정 (PRD·스택·skeleton·ship setup) 은 autopilot-spec 영역.

Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.

## Artifact Ownership

Use the shared artifact root rule: prefer `.agent_reports/`; use legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not.

Code work always writes to `<artifact-root>/plans/<date>_<slug>/`, even when a `spec/` directory exists. `spec/` is the blueprint bucket; `plans/` is the work-cycle bucket.

Required public artifacts:

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

QA level controls review depth and number of independent passes; it does not name a model. Adapters map fast/balanced/deep/adversarial review semantics to runtime-specific models or workers.

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
6. Run `code-plan`, optionally `code-refine`, then `code-execute`, `code-test`, and `code-report` according to QA level and resume point.
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

## Adapter Realization

| Adapter | Realization |
|---|---|
| Claude Code | `adapters/claude/skills/autopilot-code` currently projects compatibility source `skills/autopilot-code/SKILL.md`. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info autopilot-code`. Do not consume `skills/autopilot-code/SKILL.md` as native Codex configuration. |

## Compatibility Reference

The historical Claude Skill source remains at `skills/autopilot-code/SKILL.md` while this capability is being split into portable and adapter-native layers.
