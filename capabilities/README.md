# Portable Capability Catalog

This directory is the runtime-neutral capability layer. It describes what each
capability means, what artifacts it owns, and which portable roles it may use.
It is not a Claude Skill registry. Per-capability contracts live in
`capabilities/<capability>.md`; this README is the catalog index.

Claude Code realizes these capabilities through adapter-owned concrete Skill
files under `adapters/claude/skills/*/SKILL.md`. Historical
`skills/*/SKILL.md` files remain compatibility references while portable
contracts move into this directory.
Codex and OpenCode adapters start from this catalog, then consult
adapter-native instructions only for runtime mechanics. Codex realizes
capabilities through generated native Skill/plugin projections; OpenCode
realizes them through generated native Skill and command projections.

## Capability Contract

Each capability has:

- an identifier;
- a capability group;
- supported modes;
- invocation semantics in runtime-neutral terms;
- artifact ownership;
- required role families;
- adapter realization notes.

Autopilot entry capabilities additionally follow `core/CONVENTIONS.md §1`:

- `intensity` is the primary stage-graph selector;
- `direct` has no plan stage, no plan-check, and no durable plan artifact;
- `quick+` has at least a small `plan-check` gate;
- stage-local gates stay cheap and only check next-stage readiness;
- independent QA is not repeated after every stage by default;
- final `verify` remains capability-specific and concrete;
- Verification rigor for `plan-check`, selected independent reviews, and `verify` is derived from intensity; there is no separate user-facing `--qa` axis.

Runtime-specific details stay out of portable capability meaning:

- Claude Skill frontmatter and folder layout;
- slash command names;
- Claude hook names, `ScheduleWakeup`, statusline, or MCP registration details;
- concrete model names;
- CLI-specific external reviewer commands.

## Catalog

| Capability | Group | Modes | Portable spec | Portable meaning | Claude realization | Codex realization | OpenCode realization |
|---|---|---|---|---|---|---|---|
| `analyze-project` | pre | code, paper, doc | [`analyze-project.md`](analyze-project.md) | Pre-analysis that structures primary code, paper, and document sources into downstream-ready input. | `adapters/claude/skills/analyze-project/SKILL.md` | `adapters/codex/skills/analyze-project/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/analyze-project/SKILL.md` | `adapters/opencode/skills/analyze-project/SKILL.md`; `adapters/opencode/commands/analyze-project.md` |
| `analyze-user` | pre | init, update | [`analyze-user.md`](analyze-user.md) | Creates or updates a cross-project user preference profile from coding, writing, and analysis patterns. | `adapters/claude/skills/analyze-user/SKILL.md` | `adapters/codex/skills/analyze-user/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/analyze-user/SKILL.md` | `adapters/opencode/skills/analyze-user/SKILL.md`; `adapters/opencode/commands/analyze-user.md` |
| `audit` | ops | - | [`audit.md`](audit.md) | Read-oriented post-check of artifacts and pipelines for drift, inconsistency, and omissions. | `adapters/claude/skills/audit/SKILL.md` | `adapters/codex/skills/audit/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/audit/SKILL.md` | `adapters/opencode/skills/audit/SKILL.md`; `adapters/opencode/commands/audit.md` |
| `autopilot-apply` | entry | - | [`autopilot-apply.md`](autopilot-apply.md) | Applies a cheatsheet draft to the real source artifact and verifies the result. | `adapters/claude/skills/autopilot-apply/SKILL.md` | `adapters/codex/skills/autopilot-apply/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/autopilot-apply/SKILL.md` | `adapters/opencode/skills/autopilot-apply/SKILL.md`; `adapters/opencode/commands/autopilot-apply.md` |
| `autopilot-code` | entry | dev, debug, audit | [`autopilot-code.md`](autopilot-code.md) | Code-work entrypoint that closes the plan→execute→test→report loop; `direct` is inline and `quick` uses a depth-1 one-shot worker. | `adapters/claude/skills/autopilot-code/SKILL.md` | `adapters/codex/skills/autopilot-code/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/autopilot-code/SKILL.md` | `adapters/opencode/skills/autopilot-code/SKILL.md`; `adapters/opencode/commands/autopilot-code.md` |
| `autopilot-design` | entry | - | [`autopilot-design.md`](autopilot-design.md) | Visual-output design pipeline coordinating refs→tokens→components→review→handoff. | `adapters/claude/skills/autopilot-design/SKILL.md` | `adapters/codex/skills/autopilot-design/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/autopilot-design/SKILL.md` | `adapters/opencode/skills/autopilot-design/SKILL.md`; `adapters/opencode/commands/autopilot-design.md` |
| `autopilot-draft` | entry | paper, presentation, doc | [`autopilot-draft.md`](autopilot-draft.md) | Document-drafting pipeline producing an application-ready artifact through strategy, drafting, review, and editing. | `adapters/claude/skills/autopilot-draft/SKILL.md` | `adapters/codex/skills/autopilot-draft/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/autopilot-draft/SKILL.md` | `adapters/opencode/skills/autopilot-draft/SKILL.md`; `adapters/opencode/commands/autopilot-draft.md` |
| `autopilot-lab` | entry | setup, eval | [`autopilot-lab.md`](autopilot-lab.md) | Rapid experiment prototyping around training setup and checkpoint evaluation or analysis. | `adapters/claude/skills/autopilot-lab/SKILL.md` | `adapters/codex/skills/autopilot-lab/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/autopilot-lab/SKILL.md` | `adapters/opencode/skills/autopilot-lab/SKILL.md`; `adapters/opencode/commands/autopilot-lab.md` |
| `autopilot-note` | entry | - | [`autopilot-note.md`](autopilot-note.md) | Routes artifacts into notes and produces a digest with triage suggestions. | `adapters/claude/skills/autopilot-note/SKILL.md` | `adapters/codex/skills/autopilot-note/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/autopilot-note/SKILL.md` | `adapters/opencode/skills/autopilot-note/SKILL.md`; `adapters/opencode/commands/autopilot-note.md` |
| `autopilot-refine` | entry | - | [`autopilot-refine.md`](autopilot-refine.md) | Corrects and updates existing document or research artifacts while preserving snapshots and change history. | `adapters/claude/skills/autopilot-refine/SKILL.md` | `adapters/codex/skills/autopilot-refine/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/autopilot-refine/SKILL.md` | `adapters/opencode/skills/autopilot-refine/SKILL.md`; `adapters/opencode/commands/autopilot-refine.md` |
| `autopilot-research` | entry | academic, technology, market | [`autopilot-research.md`](autopilot-research.md) | Shared pre-research that surveys academic, technology, or market sources before routing downstream. | `adapters/claude/skills/autopilot-research/SKILL.md` | `adapters/codex/skills/autopilot-research/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/autopilot-research/SKILL.md` | `adapters/opencode/skills/autopilot-research/SKILL.md`; `adapters/opencode/commands/autopilot-research.md` |
| `autopilot-ship` | entry | - | [`autopilot-ship.md`](autopilot-ship.md) | Prepares application deployment and release with build/deploy setup and a shipping checklist. | `adapters/claude/skills/autopilot-ship/SKILL.md` | `adapters/codex/skills/autopilot-ship/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/autopilot-ship/SKILL.md` | `adapters/opencode/skills/autopilot-ship/SKILL.md`; `adapters/opencode/commands/autopilot-ship.md` |
| `autopilot-spec` | entry | app, library, api, cli, research, update | [`autopilot-spec.md`](autopilot-spec.md) | Creates or updates requirements and blueprints while keeping `prd.md` as the only spec-change path. | `adapters/claude/skills/autopilot-spec/SKILL.md` | `adapters/codex/skills/autopilot-spec/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/autopilot-spec/SKILL.md` | `adapters/opencode/skills/autopilot-spec/SKILL.md`; `adapters/opencode/commands/autopilot-spec.md` |
| `code-execute` | sub | - | [`code-execute.md`](code-execute.md) | Executes implementation step by step, delegates to development roles, and records an execution log. | `adapters/claude/skills/code-execute/SKILL.md` | `adapters/codex/skills/code-execute/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/code-execute/SKILL.md` | `adapters/opencode/skills/code-execute/SKILL.md`; `adapters/opencode/commands/code-execute.md` |
| `code-plan` | sub | - | [`code-plan.md`](code-plan.md) | Analyzes code, writes a detailed implementation plan, and runs the plan-check gate at the rigor derived from intensity. | `adapters/claude/skills/code-plan/SKILL.md` | `adapters/codex/skills/code-plan/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/code-plan/SKILL.md` | `adapters/opencode/skills/code-plan/SKILL.md`; `adapters/opencode/commands/code-plan.md` |
| `code-refine` | sub | - | [`code-refine.md`](code-refine.md) | Revises an existing plan using user notes, plan-check feedback, and verification-failure notes. | `adapters/claude/skills/code-refine/SKILL.md` | `adapters/codex/skills/code-refine/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/code-refine/SKILL.md` | `adapters/opencode/skills/code-refine/SKILL.md`; `adapters/opencode/commands/code-refine.md` |
| `code-report` | sub | - | [`code-report.md`](code-report.md) | Assembles code-work cycle results into a user-facing report. | `adapters/claude/skills/code-report/SKILL.md` | `adapters/codex/skills/code-report/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/code-report/SKILL.md` | `adapters/opencode/skills/code-report/SKILL.md`; `adapters/opencode/commands/code-report.md` |
| `code-test` | sub | - | [`code-test.md`](code-test.md) | Verifies implementation results step by step and records evidence. | `adapters/claude/skills/code-test/SKILL.md` | `adapters/codex/skills/code-test/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/code-test/SKILL.md` | `adapters/opencode/skills/code-test/SKILL.md`; `adapters/opencode/commands/code-test.md` |
| `design-components` | sub | - | [`design-components.md`](design-components.md) | Implements UI components or mockups and creates a preview artifact. | `adapters/claude/skills/design-components/SKILL.md` | `adapters/codex/skills/design-components/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/design-components/SKILL.md` | `adapters/opencode/skills/design-components/SKILL.md`; `adapters/opencode/commands/design-components.md` |
| `design-handoff` | sub | - | [`design-handoff.md`](design-handoff.md) | Packages design results as development-handoff assets and specifications. | `adapters/claude/skills/design-handoff/SKILL.md` | `adapters/codex/skills/design-handoff/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/design-handoff/SKILL.md` | `adapters/opencode/skills/design-handoff/SKILL.md`; `adapters/opencode/commands/design-handoff.md` |
| `design-init` | sub | - | [`design-init.md`](design-init.md) | Bootstraps the design environment and state. | `adapters/claude/skills/design-init/SKILL.md` | `adapters/codex/skills/design-init/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/design-init/SKILL.md` | `adapters/opencode/skills/design-init/SKILL.md`; `adapters/opencode/commands/design-init.md` |
| `design-refs` | sub | - | [`design-refs.md`](design-refs.md) | Collects external and user-provided visual references and creates a brief. | `adapters/claude/skills/design-refs/SKILL.md` | `adapters/codex/skills/design-refs/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/design-refs/SKILL.md` | `adapters/opencode/skills/design-refs/SKILL.md`; `adapters/opencode/commands/design-refs.md` |
| `design-review` | sub | - | [`design-review.md`](design-review.md) | Reviews design outputs for quality, token-contract compliance, and breakage. | `adapters/claude/skills/design-review/SKILL.md` | `adapters/codex/skills/design-review/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/design-review/SKILL.md` | `adapters/opencode/skills/design-review/SKILL.md`; `adapters/opencode/commands/design-review.md` |
| `design-tokens` | sub | - | [`design-tokens.md`](design-tokens.md) | Defines design tokens such as color, typography, and spacing. | `adapters/claude/skills/design-tokens/SKILL.md` | `adapters/codex/skills/design-tokens/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/design-tokens/SKILL.md` | `adapters/opencode/skills/design-tokens/SKILL.md`; `adapters/opencode/commands/design-tokens.md` |
| `draft-refine` | sub | - | [`draft-refine.md`](draft-refine.md) | Refines a draft by applying memo or review feedback to the document strategy or draft. | `adapters/claude/skills/draft-refine/SKILL.md` | `adapters/codex/skills/draft-refine/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/draft-refine/SKILL.md` | `adapters/opencode/skills/draft-refine/SKILL.md`; `adapters/opencode/commands/draft-refine.md` |
| `draft-strategy` | sub | rebuttal, paper, review, report, proposal, presentation | [`draft-strategy.md`](draft-strategy.md) | Creates a source-grounded writing plan for a document draft. | `adapters/claude/skills/draft-strategy/SKILL.md` | `adapters/codex/skills/draft-strategy/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/draft-strategy/SKILL.md` | `adapters/opencode/skills/draft-strategy/SKILL.md`; `adapters/opencode/commands/draft-strategy.md` |
| `post-it` | ops | - | [`post-it.md`](post-it.md) | Stores project and cross-project records or handoffs in working memory. | `adapters/claude/skills/post-it/SKILL.md` | `adapters/codex/skills/post-it/SKILL.md`; `adapters/codex/plugins/agent-harness-codex/skills/post-it/SKILL.md` | `adapters/opencode/skills/post-it/SKILL.md`; `adapters/opencode/commands/post-it.md` |

## Adapter Requirements

An adapter that supports capabilities must document:

- how a user invokes the capability;
- whether confirmation is automatic, required, or unsupported;
- how the adapter discovers artifact roots;
- how it loads the portable roles in `roles/`;
- which deterministic guards it can enforce;
- where durable output is written;
- how unsupported sub-capabilities are reported.

If an adapter cannot support a capability, it must say so explicitly and offer a
fallback path instead of silently treating a Claude Skill file as native.
