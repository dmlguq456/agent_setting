# AGENTS.md — OpenCode Adapter Bootstrap

This is an OpenCode adapter router, loaded through the `instructions` array in
`opencode.json(c)`. The semantic hierarchy is
`core/capabilities/roles -> {Claude, Codex, OpenCode}`; adapters are siblings.
Edit portable sources first.

## Source Order

Read `core/CORE.md` first; load the remaining documents only when the task
touches the named domain.

1. `core/CORE.md`
2. `core/WORKFLOW.md` for routing and tracked work
3. `core/CONVENTIONS.md` for intensity, QA, roles, artifacts, and Skill rules
4. `core/OPERATIONS.md` for git, worktrees, locks, and dispatch
5. `core/MEMORY.md`
6. `capabilities/README.md`, `roles/README.md`, and `roles/MODES.md`

For runtime-surface or parity changes, verify current official documentation,
then inspect local projection and fallback. Never infer support from another
adapter.

## Runtime Mapping

- `AGENT_HOME` is the installed harness root. Resolve the canonical artifact root with `utilities/artifact-root.sh`; linked worktrees write the primary checkout's `.agent_reports/`.
- Capabilities come from `capabilities/`. OpenCode-native generated Skills, commands, agents, and plugins live under `adapters/opencode/` and project through `opencode_setting/opencode-skills`, `opencode_setting/opencode-commands`, `opencode_setting/opencode-agents`, and `opencode_setting/opencode-plugins`.
- Validate native discovery with `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1`; Claude compatibility autoload must not mask missing OpenCode output.
- Run `preflight.sh capability-info <capability>` and `preflight.sh mode-info <family/mode>`; obey named `tool_contract`, `tool_contract_check`, `runtime_surface`, and `fallback`.
- Before edits run `preflight.sh write <file> [session-id]`. Read portable core first for `adapters/**`; mark core/spec reads with `preflight.sh read <file> [session-id]`; run `preflight.sh capability <name> [cwd] [session-id]` for spec changes.
- Use explicit guards when the OpenCode plugin is unavailable or untrusted. Never port Claude allowedTools, settings MCP, command, agent, or hook formats.

Detailed lifecycle and edge-case contracts live in
`adapters/opencode/README.md` and `ADAPTATION.md`.

## Command Surface

| Need | Command |
|---|---|
| lifecycle/workflow | `preflight.sh start`, `preflight.sh mode`, `preflight.sh track`, `preflight.sh briefing`, `preflight.sh worklog` |
| memory | `preflight.sh memory`, `preflight.sh recall`, `preflight.sh distill-delta`, `preflight.sh distill-propose` |
| readiness/loops | `preflight.sh status`, `preflight.sh doctor`, `preflight.sh loop-info <oncall|note|study|drill|runtime-watch>` |
| QA | `preflight.sh qa-policy <level> [code|research|doc|general]` |
| runtime | `preflight.sh permissions`, `preflight.sh mcp [--check]` |

Main lifecycle does not run for workers. Runtime-owned credentials, sessions,
logs, caches, databases, and config stay outside this repo.

## Tool Contracts

Before claiming support, run:

- `preflight.sh visual-harness <file.html>`
- `preflight.sh browser-fetch --check <url>`
- `preflight.sh data-script --check <script.py>`
- `preflight.sh figure-gen --check <script.py>`
- `figure-gen --verify-report <manifest.json> <report.md>`
- `preflight.sh pdf-extract --check <file.pdf>`
- `preflight.sh web-image-search --check <query>`
- `preflight.sh verification-runner --timeout <seconds> -- <command>`
- `preflight.sh claim-verify --check <claim>`

Exit 69 means unavailable; use the reported fallback or keep the adapter row
partial. OpenCode native UI/config owns model and context fields.

## Dispatch

Select the primary capability semantically per `core/WORKFLOW.md §0.2` and use
its §0.3 pre-execution gate when applicable.

Check `preflight.sh headless [--check] <worktree>`. Launch only registered jobs
through `preflight.sh dispatch --dry-run|--register|--start` with explicit
worktree, slug, capability, mode, QA, intensity, depth, parent, worker role,
owner, agent, and model/variant choice or inheritance. Monitor
`preflight.sh liveness [jobs.log]`; harvest via `preflight.sh harvest`.
Before a standard+ conductor starts, depth 0 prepares the shared non-model
broker through `preflight.sh broker ensure --jobs <canonical-jobs>`; the wrapper
does this idempotently on `--start`. Conductors use `dispatch-chain`, which sends
all same/cross-harness depth-2 targets through that broker rather than recursively
starting adapter CLIs.

`standard+` uses a depth-1 capability owner and separable depth-2
`code-plan -> code-execute -> code-test -> code-report` workers. `direct` is
inline; `quick` is one depth-1 one-shot worker; depth 3 is forbidden. Record
inline exceptions in plan metrics. After merge, integrated verification, and
push, use `preflight.sh worktree-cleanup --check` before `--apply`.

Keep native agent delegation distinct from registered headless work. The
main/orchestrator chooses portable roles and concrete model settings per job.

## Memory and Context

Memory semantics belong to the acting agent. Use a targeted `preflight.sh recall
"<query>" [cwd]`; retrieve a full pending obligation before applying and
consuming it.

OpenCode token self-regulation remains explicitly deferred: Phase 2 automatic accounting and the isolated experiment CLI are not projected; it does not copy
Codex token-budget hooks or mutate runtime config. Ordinary lifecycle context
should be silent. Static bytes, lines, and directive counters are footprint
measures, not token or billing savings. Context pressure never lowers intensity,
dispatch/depth, model role, required input, tools/tests, safety, or validation.

Do not run drill automatically.

## Response Policy

Portable behavior contract = `roles/response-policy.md`.

- **Audience-language first** — user artifacts default to the user's current communication language unless a stronger audience/repository contract applies.
- Keep responses concise, match promises with same-turn action, verify before asserting, and follow current conventions.
- Ask only for non-obvious or destructive choices. Continue reversible in-flow work and its implied validation, records, commit, and push.

## Compatibility Boundary

Claude/Codex files are sibling references, not OpenCode bootstrap input. Map
portable meaning from `core/`, `capabilities/`, and `roles/` to OpenCode
permissions, tools, lifecycle, agents, commands, Skills, and plugins.
