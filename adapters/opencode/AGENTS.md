# AGENTS.md — OpenCode Adapter Bootstrap

This file maps the shared agent harness onto OpenCode sessions. It is an
adapter bootstrap, not the portable source of truth. Load it through the
`instructions` array in `opencode.json` / `opencode.jsonc`.

This document is derived from core — edit core first; do not modify this adapter ahead of the core contract.

## Source Order

1. Read `core/CORE.md` for the model-neutral harness contract.
2. For routing and tracked work, read `core/WORKFLOW.md`.
3. For QA levels, model roles, artifact layout, and cross-doc invariants, read `core/CONVENTIONS.md`.
4. For git/worktree/dispatch rules, read `core/OPERATIONS.md`.
5. For memory behavior, read `core/MEMORY.md`.
6. For task-specific behavior, read `capabilities/README.md`, `roles/README.md`, and `roles/MODES.md` first. Use Claude Skill, Agent, or mode files only as compatibility references.

## Runtime Currentness

- For Claude Code or Codex runtime-surface questions or projection edits (agents/subagents, hooks, skills, settings/config, model/reasoning, permissions, headless/dispatch, or adapter parity), verify current official documentation first and then inspect local adapter realization.
- Use recent community posts, GitHub issues, and examples only as secondary evidence for real-world gaps or practices; label them as non-authoritative.
- Do not infer product capability from this harness projection alone. State separately: what the runtime supports, what this adapter currently projects, and what parity gaps remain versus the compared adapter.
- Any modification plan for those surfaces must include current-doc evidence, a local runtime/projection check, and a fallback for unsupported or buggy behavior.

## Runtime Mapping

- Treat `AGENT_HOME` as the installed harness root.
- Use `.agent_reports/` for new artifacts. Read legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not.
- Use portable model roles from `core/CONVENTIONS.md`; do not treat Claude model names such as `sonnet` or `opus` as portable semantics.
- Before treating a capability as supported, run `adapters/opencode/bin/preflight.sh capability-info <capability>` and follow the reported OpenCode realization.
- Treat OpenCode-native skills under `adapters/opencode/skills/` as generated adapter output from `capabilities/`; do not load Claude Skill, command, or agent files as native OpenCode surfaces.
- Treat OpenCode-native commands, agents, skills, and plugins as adapter-owned output from `capabilities/`, `roles/`, and portable hook invariants.
- Expose OpenCode skills, agents, commands, and plugin guards through `opencode_setting/opencode-skills`, `opencode_setting/opencode-agents`, `opencode_setting/opencode-commands`, and `opencode_setting/opencode-plugins`; do not copy Claude-native surfaces.
- When validating OpenCode-native discoverability, run with `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` so OpenCode's `~/.claude/skills/` compatibility autoload cannot mask missing adapter-owned output.
- Before using a `roles/modes/` fragment, run `adapters/opencode/bin/preflight.sh mode-info <family/mode>` and obey portable/tool-contract/unsupported status plus any named `tool_contract`, `tool_contract_check`, `runtime_surface`, and `fallback`.
- Run deterministic guard scripts directly when OpenCode plugins are unavailable or untrusted. The adapter provides a JS plugin for prompt lifecycle context, write/edit/patch guards, and design post-write checks; use explicit preflight wrappers when that plugin is not installed or trusted.
- Use `adapters/opencode/bin/preflight.sh permissions` to inspect the OpenCode native permission contract; do not port Claude `allowedTools`.
- Use `adapters/opencode/bin/preflight.sh mcp [--check]` to inspect OpenCode's native MCP surface; do not copy Claude `settings.json` MCP registrations or project `tools/design-mcp` wholesale.
- Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
- Before editing `adapters/**`, that write wrapper enforces the core-first gate; after actually reading `core/*.md`, run `adapters/opencode/bin/preflight.sh read <core-doc.md> [session-id]` so the marker exists.
- For `material/browser-fetch` URLs, run `adapters/opencode/bin/preflight.sh browser-fetch --check <url>` before treating rendered browser access as satisfying the mode tool contract. Exit 69 means the local Playwright browser stack is unavailable.
- For `material/data-script` outputs, run `adapters/opencode/bin/preflight.sh data-script --check <script.py>` before treating the generated analysis script as satisfying the mode tool contract.
- For `material/figure-gen` outputs, run `adapters/opencode/bin/preflight.sh figure-gen --check <script.py>` before treating a generated matplotlib figure script as satisfying the mode tool contract.
- For `material/pdf-extract` inputs, run `adapters/opencode/bin/preflight.sh pdf-extract --check <file.pdf>` before treating local PDF text extraction as satisfying the mode tool contract. Exit 69 means the local extractor is unavailable.
- For `material/web-image-search` queries, run `adapters/opencode/bin/preflight.sh web-image-search --check <query>` before treating image search as satisfying the mode tool contract. Exit 69 means no provider command is configured.
- For `qa/security-review`, use the portable read-only mode with OpenCode file and git diff tools; do not invoke or project Claude `/security-review`.
- For `qa/test` verification commands, run `adapters/opencode/bin/preflight.sh verification-runner --timeout <seconds> -- <command> [args...]` and report the captured exit status.
- For QA level routing, run `adapters/opencode/bin/preflight.sh qa-policy <level> [code|research|doc|general]` and obey `stage_graph_selector=intensity-not-qa`, `assurance_scope`, reviewer budgets, and fallback policy before claiming independent QA delegation.
- After design HTML writes, run `adapters/opencode/bin/preflight.sh design <file>`.
- Before claiming full design/autopilot-design support, run `adapters/opencode/bin/preflight.sh visual-harness <file.html>` and inspect the reported screenshot. Exit 69 means the local Playwright-backed checker is unavailable.
- After actually reading `<artifact-root>/spec/prd.md` or `core/*.md`, run `adapters/opencode/bin/preflight.sh read <file> [session-id]`; before spec-changing capability work, run `adapters/opencode/bin/preflight.sh capability <name> [cwd] [session-id]`.
- OpenCode plugin system transform runs `adapters/opencode/bin/preflight.sh start [cwd] [session-id]` and `adapters/opencode/bin/preflight.sh memory [cwd]` once per session; run them manually when plugins are unavailable.
- OpenCode plugin system transform runs `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`, tracked/project-only `adapters/opencode/bin/preflight.sh recall "<prompt>" [cwd] [session-id]` high-confidence auto recall, and `adapters/opencode/bin/preflight.sh briefing [cwd]`; run them manually when plugins are unavailable.
- For memory behavior, apply `core/MEMORY.md` §7.4 recall-first: before style, format, naming, figure/table/report-layout, or prior-convention decisions, run `adapters/opencode/bin/preflight.sh recall "<query>" [cwd]` or `tools/memory/recall.sh` directly. For deep memory-scout work, use the same read-only procedure and return the fixed <=15 line verdict; no memory or file writes. When recall or injection exposes `[pending:<id>]`, read the full obligation, apply and verify it, then run `python3 tools/memory/mem.py consume <id>`; retrieval alone never consumes it.
- Use `adapters/opencode/bin/preflight.sh status [cwd] [session-id]` when you need a read-only harness snapshot for workflow, artifact, notes, worktree, and git-risk signals. Keep OpenCode native UI/config responsible for model, context, and session fields.
- Use `adapters/opencode/bin/preflight.sh doctor` for a quick adapter readiness check covering manifest freshness, native projections, and boundary rules.
- Use `adapters/opencode/bin/preflight.sh loop-info <oncall|note|study|drill>` before following a loop guide; do not run Claude-coupled loop scripts as OpenCode-native executables.
- Use `adapters/opencode/bin/preflight.sh track [cwd] [session-id]` only when the user explicitly wants to toggle the tracked/untracked workflow escape hatch.
- Use `adapters/opencode/bin/preflight.sh worklog [cwd]` before worklog-board or agent-notes work to inspect configured notes/app paths without mutating data.
- Use `adapters/opencode/bin/preflight.sh headless [--check] <worktree>` before any OpenCode headless dispatch. Use `adapters/opencode/bin/preflight.sh dispatch --dry-run|--register|--start --worktree <path> --slug <slug> --capability <name> --mode <family/mode> --qa <level> [--intensity <direct|quick|standard|strong|thorough|adversarial>] [--depth 1|2] [--parent <slug>] [--parent-session-id <session>] [--worker-role <role>] [--owner <capability>] [--agent <agent>] (--model-role <portable-role>|--model <model> --variant <variant>|--inherit-model-settings)` to build/register/start the headless command; main/orchestrator must choose model settings per job. Do not launch headless work unless the job is main-dispatched depth 1, or depth 2 dispatched by a depth 1 capability owner under `standard+` intensity with `--parent`; every job must be registered in `.dispatch/jobs.log` and monitored with `adapters/opencode/bin/preflight.sh liveness [jobs.log]` while waiting. Depth-2 has two regular uses (2026-07-10 stage-dispatch, `core/OPERATIONS.md §5.10 ③④`): bounded review sub-workers, and — the `standard+` default — **pipeline stage-workers** where the depth-1 conductor dispatches each sub-skill stage (`--worker-role code-plan|code-execute|code-test|code-report`) as its own session with file-only handoff and class-scoped writes (only code-execute mutates source). `direct` stays inline; `quick` is a depth-1 one-shot worker; micro-stages stay inline; stage sessions never re-dispatch (depth 3+ forbidden). Exception to the stage-dispatch default = **separability judgment** (SD-17, `core/OPERATIONS.md §5.10 ③`): non-separable, boundary-coupled edits may run inline only with the reasoning recorded in `plans/<slug>/_internal/metrics.md` (an unrecorded inline run is a contract violation), separable parts still parallelized in-session, and dispatch-infra self-modification gated by the explicit orchestrator opt-out. The depth-1 conductor is a one-shot process — after dispatching a stage it must not end the turn on a notification wait; it polls the registered stage with `adapters/opencode/bin/preflight.sh liveness [jobs.log]` in the same turn and harvests, re-dispatching on SUSPECT/DEAD (SD-14 parity). After main-session harvest, use `adapters/opencode/bin/preflight.sh harvest --slug <slug> --mark-done` only to update the registry; merges and cleanup remain main/orchestrator responsibilities. For `autopilot-code`, follow the core stage graph: `direct` has no plan stage, `quick` is a depth-1 one-shot worker that uses micro-plan plus plan-check-lite, and `standard+` uses the durable plan/execute/test/report cycle.
- For `research/claim-verify`, run `adapters/opencode/bin/preflight.sh claim-verify --check <claim>` before treating adversarial external verification as satisfying the mode tool contract. Exit 69 means no external verification provider is configured.
- Use `adapters/opencode/bin/preflight.sh distill-delta <session-id>` to read transcript deltas through `opencode export`. Use `adapters/opencode/bin/preflight.sh distill-propose <session-id> [cwd]` only for explicit proposal attempts; it is disabled by default and reports the remaining OpenCode no-tools worker tool-contract instead of auto-applying memory distillation.
- Treat `opencode_setting/tools` as a selective memory/material/QA/design tool projection. Do not assume every shared tool is OpenCode-supported.
- Treat `opencode_setting/utilities` as a selective utility projection. Do not assume every shared utility is OpenCode-supported.
- Keep OpenCode-owned credentials, sessions, DB state, logs, caches, and local databases outside the harness repo.

## Response Policy

Portable behavior contract = `roles/response-policy.md` (single source for the clauses below). This section is the OpenCode realization: the portable clauses plus OpenCode-specific tone and runtime notes. Do not redefine a portable clause here.

Portable clauses (from `roles/response-policy.md`):
- **Concise · promise–action match** — say only what is needed, no self-narration; if you use a commitment verb the matching action is in the same turn.
- **Verify before asserting · convention adherence** — state tool/code facts only after checking; follow an existing convention rather than improvising, and expose changes before committing.
- **Pause is not automatic · autonomous on no answer** — a pause/review applies only on an explicit user signal; when a question is unanswered, proceed in the recommended direction with a one-line report and do not re-ask.
- **Do not ask what is certain · sync then execute** — reserve questions for genuinely non-obvious design/format/destructive decisions; align intent upfront, then run without mid-stream confirms.
- **Auto-continue in-flow follow-ups · corresponding sync is part of the change** — inside a "do X" flow do not re-confirm each step (commit/push/cleanup); the records/docs the change implies follow automatically. Confirm separately only for new design decisions, destructive ops, or touching another system.

OpenCode realization notes:
- Answer the user in Korean unless they explicitly request another language.
- Keep implementation work grounded in the repo's current files and existing conventions.
- When modifying this harness repo, commit and push after validation.
- Do not run drill automatically; it can invoke headless runtime sessions and spend tokens. Run `adapters/opencode/bin/preflight.sh loop-info drill` and report when drill would be useful.

## Compatibility Boundary

Claude Code files are implementation references, not OpenCode bootstrap files:

- `adapters/claude/CLAUDE.md`
- `adapters/claude/settings.json`
- `adapters/claude/commands/`
- `adapters/claude/statusline.sh`
- `adapters/claude/hooks/*.sh` (Claude hook event schema)

OpenCode has native surfaces for commands (`.opencode/command/`), skills
(`.opencode/skill/`), agents (`.opencode/agent/`), and plugin hooks (JS/TS).
When porting behavior, copy the invariant from `core/` first, then map it to
OpenCode tools, permission behavior, agent mode, and session lifecycle. Do not
copy Claude frontmatter or hook payloads into OpenCode-native files.
