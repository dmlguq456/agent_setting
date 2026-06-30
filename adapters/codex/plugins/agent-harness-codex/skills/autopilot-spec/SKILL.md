---
name: autopilot-spec
description: "Use when the user requests autopilot-spec: 요구사항·청사진 작성·갱신. `prd.md`를 spec 변경의 단일 경로로 유지한다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# autopilot-spec

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-spec.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info autopilot-spec`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/autopilot-spec.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info autopilot-spec`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-spec`
- Supported modes: `app, library, api, cli, research, update`
- Argument shape: `<task description> [--mode auto|app|library|api|cli|research|update (콤마로 다중)] [--qa quick|light|standard|thorough] [--user-refine]`
- Portable meaning: 요구사항·청사진 작성·갱신. `prd.md`를 spec 변경의 단일 경로로 유지한다.

## Portable Contract

- Invocation semantics: _요구사항·청사진 작성·갱신_ 의 일반화 entry — 신규 의도, 기존 코드 정돈·공개 준비, 그리고 기존 spec 의 update·iteration (prd.md 갱신) 자리 모두. mode 5종 (app / library / api / cli / research) + 다중 + auto + update mode (기존 prd.md 갱신 — 모든 spec 변경의 canonical 경로, 버전 snapshot 자동). PRD 구조 = 공통 + mode 별 독립 섹션. autopilot-research / analyze-project 결과 자동 인용. analyze-project 의 _신규 의도 → 청사진_ 대칭 자리. 실제 코드 작업은 autopilot-code 가 담당 (spec/ 컨텍스트 자동 감지). Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.



## Projected Portable Details

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

QA level controls review breadth, number of refinement rounds, and how much external/independent validation is required; it does not name a model.

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

## Routing Boundary

`autopilot-spec` decides what should exist and records the blueprint. Actual implementation, refactoring, debugging, and test repair are `autopilot-code` work. Visual artifact production is `autopilot-design`; deployment execution is `autopilot-ship`.

## Mode-Specific Semantics

| Mode | Required blueprint coverage |
|---|---|
| `app` | Feature scenarios, API contract, data model, UI flow, stack, scaffold/skeleton intent, design handoff hooks. |
| `library` | Public API, exports, examples, compatibility, versioning, module structure. |
| `api` | Endpoints, request/response bodies, errors, auth, rate limiting, data model. |
| `cli` | Commands, subcommands, options, input/output format, exit codes. |
| `research` | Train/eval entry points, configs, seeds, reproduction commands, expected metrics, baselines. |

Composite modes are valid. Keep shared decisions in the common PRD section and each mode's contract in its own section.


## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before capability routing/spec-changing work: `adapters/codex/bin/preflight.sh route autopilot-spec [cwd] [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability autopilot-spec [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]` and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
