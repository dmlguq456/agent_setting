# Capability: autopilot-spec

This is the portable capability contract for `autopilot-spec`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `autopilot-spec` |
| Group | `entry` |
| Supported modes | `app, library, api, cli, research, update` |
| Portable meaning | 요구사항·청사진 작성·갱신. `prd.md`를 spec 변경의 단일 경로로 유지한다. |
| Argument shape | `<task description> [--mode auto|app|library|api|cli|research|update (콤마로 다중)] [--intensity direct|quick|standard|strong|thorough|adversarial] [--user-refine]` |

## Invocation Semantics

_요구사항·청사진 작성·갱신_ 의 일반화 entry — 신규 의도, 기존 코드 정돈·공개 준비, 그리고 기존 spec 의 update·iteration (prd.md 갱신) 자리 모두. mode 5종 (app / library / api / cli / research) + 다중 + auto + update mode (기존 prd.md 갱신 — 모든 spec 변경의 canonical 경로, 버전 snapshot 자동). PRD 구조 = 공통 + mode 별 독립 섹션. autopilot-research / analyze-project 결과 자동 인용. analyze-project 의 _신규 의도 → 청사진_ 대칭 자리. 실제 코드 작업은 autopilot-code 가 담당 (spec/ 컨텍스트 자동 감지).

Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.

## Artifact Ownership

Use the shared artifact root rule: prefer `.agent_reports/`; use legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not.

Spec work writes to `<artifact-root>/spec/`. The canonical current blueprint is always `<artifact-root>/spec/prd.md`.

Required public artifacts:

- `prd.md`: current product/project requirements and mode-specific contract;
- `pipeline_state.yaml`: current mode, phase status, timestamps, and resume metadata;
- `pipeline_summary.md`: concise decision log and update narrative;
- mode-dependent companion files such as `stack.md`, `ship.md`, `data_model.md`, `api_contract.md`, `ui_flow.md`, or `design/`.

Internal artifacts belong under `spec/_internal/`, including old PRD snapshots, drafts, raw notes, review records, and temporary scaffolding decisions.

For update mode, snapshot the previous `prd.md` to `spec/_internal/versions/v{N}/prd.md` before overwriting it, then update `pipeline_summary.md` in the same transaction.

## Role Requirements

Use portable role names from `roles/README.md` and `core/CONVENTIONS.md`. Concrete model names, subagent frontmatter, and runtime-specific tool lists belong in adapter files.

Minimum role mapping:

- requirements planning: planning role;
- stack/API/data modeling review: planning plus QA review roles;
- app visual decisions: design role for token, flow, and handoff contracts;
- research or reference import: research role;
- final consistency pass: QA role.

Pipeline intensity follows `core/CONVENTIONS.md §1`: `direct` has no plan stage or durable plan artifact; `quick` is a depth-1 one-shot worker with its inline micro-plan plus plan-check-lite; `standard+` uses the capability's durable work-cycle plan when applicable. `plan-check` is required for every non-`direct` graph, but independent QA is not repeated after every stage by default. Verification rigor for plan-check, selected independent reviews, and final verify is derived from intensity; it does not name a model or introduce a separate stage graph.

## Guard Requirements

Adapters must preserve the portable invariants relevant to this capability:

- resolve artifact root through `utilities/artifact-root.sh` or equivalent logic;
- enforce git/worktree safety before edits;
- enforce artifact ordering before new durable artifacts;
- enforce spec-read gating when this capability changes spec-backed code or specs;
- use DB memory paths, not runtime-native memory files.

Additional spec-entry gates:

- if user input lacks irreversible-decision coverage, ask one structured intake round before drafting;
- use `update` behavior whenever `spec/pipeline_state.yaml` already exists and the request changes the blueprint;
- do not hand-edit `prd.md` as an ad hoc side effect of code work;
- acquire the shared spec/pipeline lock before writing `prd.md`, `pipeline_state.yaml`, or `pipeline_summary.md`;
- when drift is clear, update the spec and report the drift route; when drift is ambiguous, ask the user before choosing semantics;
- keep deployment setup and environment/domain rollout work in `autopilot-ship` unless the task is only blueprint definition.

## Portable Procedure

1. Parse the task and resolve mode: `auto`, one or more of `app/library/api/cli/research`, or update of an existing spec.
2. Resolve artifact root and identify the target `spec/` directory. In monorepos, choose the component spec from cwd and user wording.
3. Run the intake gate when core irreversible choices are missing.
4. Import existing analysis and research artifacts when present: `analysis_project/code/`, `analysis_project/paper/`, and `research/<topic>/`.
5. Draft or update `prd.md` with a common section plus mode-specific sections.
6. Produce or update companion contracts for the active modes.
7. Run the configured QA/refine passes.
8. For update mode, snapshot the old `prd.md`, write the new `prd.md`, update `pipeline_state.yaml`, and append the narrative to `pipeline_summary.md`.

## Mode-Specific Semantics

| Mode | Required blueprint coverage |
|---|---|
| `app` | Feature scenarios, API contract, data model, UI flow, stack, scaffold/skeleton intent, design handoff hooks. |
| `library` | Public API, exports, examples, compatibility, versioning, module structure. |
| `api` | Endpoints, request/response bodies, errors, auth, rate limiting, data model. |
| `cli` | Commands, subcommands, options, input/output format, exit codes. |
| `research` | Train/eval entry points, configs, seeds, reproduction commands, expected metrics, baselines. |

Composite modes are valid. Keep shared decisions in the common PRD section and each mode's contract in its own section.

## Routing Boundary

`autopilot-spec` decides what should exist and records the blueprint. Actual implementation, refactoring, debugging, and test repair are `autopilot-code` work. Visual artifact production is `autopilot-design`; deployment execution is `autopilot-ship`.

## Adapter Realization

| Adapter | Realization |
|---|---|
| Claude Code | `adapters/claude/skills/autopilot-spec/SKILL.md` and `skills/autopilot-spec/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-spec/SKILL.md`, while `skills/autopilot-spec/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info autopilot-spec`. Use `adapters/codex/skills/autopilot-spec/SKILL.md` and `adapters/codex/plugins/agent-harness-codex/skills/autopilot-spec/SKILL.md` as native Codex Skill/plugin projections; do not consume `skills/autopilot-spec/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info autopilot-spec`. Use `adapters/opencode/skills/autopilot-spec/SKILL.md` and `adapters/opencode/commands/autopilot-spec.md` as native OpenCode projections; do not consume `skills/autopilot-spec/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/autopilot-spec/SKILL.md` and `adapters/claude/skills/autopilot-spec/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-spec/SKILL.md`, while `skills/autopilot-spec/SKILL.md` remains the compatibility reference kept for parity/drift checks.
