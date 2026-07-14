# CLAUDE.md — Claude Code Adapter Bootstrap

> Loaded automatically at session start. This is the Claude Code adapter for the shared agent harness, not a standalone or portable source of truth. `core/CORE.md` owns model- and tool-neutral behavior; this file and `adapters/claude/settings.json` own Claude Code realization. Edit core first, then derive this adapter.

The harness is not limited to Claude Code, Codex, or any one runtime.

## Source Order

1. Read `core/CORE.md` for the portable contract.
2. Read `core/WORKFLOW.md` on demand for routing and tracked work.
3. Read `core/CONVENTIONS.md` for intensity, roles, artifacts, and invariants.
4. Read `core/OPERATIONS.md` for git, worktree, dispatch, merge, and push.
5. Read `core/MEMORY.md` for agent-owned memory judgment and guarded mechanics.
6. Read capabilities and roles relevant to the task. Treat this adapter's Skills, Agents, modes, hooks, and commands as Claude-specific realizations.

## Workflow Map

- Documents: `analyze-project` / `autopilot-research` → `autopilot-draft` → `autopilot-refine` ↻ → `autopilot-apply`
- Research and experiments: `analyze-project` / `autopilot-research` → `autopilot-spec` ↻ → `autopilot-code` ↻ → `autopilot-lab` ↻
- Applications: `autopilot-spec` ↻ → `autopilot-design` → `autopilot-code` ↻ → `autopilot-ship` ↻
- Libraries and CLIs: `analyze-project` → `autopilot-spec` ↻ → `autopilot-code` ↻
- Post-work: read-only `audit` and corrective `autopilot-refine`; cross-project `analyze-user` and `post-it --scope user`

Read `~/.claude/core/WORKFLOW.md` when making a routing decision. The mode signal from `workflow-guard-hook` is the anchor: tracked follows the contract, explicit untracked is exempt. The hook provides runtime state, not the routing body. Do not load the user-facing README as agent instructions.

## Runtime Currentness

For questions or edits concerning Claude Code or another runtime's agents, subagents, hooks, Skills, settings, model/reasoning, permissions, headless dispatch, or adapter parity, verify current official documentation before asserting behavior. Use community evidence only as secondary material. Separate what the product supports, what this adapter projects, and what parity gaps remain.

## Response and Routing Policy

`roles/response-policy.md` is the single source for portable response clauses. This section realizes them for Claude Code without imposing a locale.

### 0. Route Through the Tracked Contract

Every tracked task first passes through `WORKFLOW §2`. Direct tools, plugins, and built-in Skills are used only where that router places them.

Artifact order is one-way:

```text
research / analyze-project → autopilot-spec → autopilot-code
research / analyze-project → autopilot-draft → autopilot-refine
```

Code requires spec; spec requires research or analysis. A one-off throwaway is the narrow exception, and repeated work graduates. `artifact-guard.sh` hard-enforces creation order only; it does not distinguish direct edits from an owning capability. Explicit `/track` untracked mode is user-owned and must not be enabled by the agent merely to escape a gate.

The capability that created an artifact owns its revisions:

| Artifact | Update path | Version record |
|---|---|---|
| `spec/` | `autopilot-spec` update | `_internal/versions/v{N}/` |
| `plans/` and code work | `autopilot-code` | Repeated `plans/<date>_<slug>/` cycles |
| `documents/` | `autopilot-draft` / `autopilot-refine` | `_internal/versions/v{N}/` |
| `experiments/` | `autopilot-lab` | `_RUNLOG.md` |
| Profile DB records | `analyze-user` / `post-it --scope user` | Record changelog |

Primary capability selection is semantic (`WORKFLOW §0.2`): new empirical work — checkpoint reevaluation, new metrics, figure/media generation — keeps `autopilot-lab` primary even when the request is phrased as a document update; refine, spec, draft, and note attach as secondaries and never replace the execution primary. Before long-running, GPU-bound, or bulk-generation execution, answer the `WORKFLOW §0.3` pre-execution gate.

In a spec-backed cwd, read `prd.md`, pipeline state, and recent plans before work; then check spec drift and route through the appropriate intensity. Spec read markers and capability gates enforce this path.

When a user invokes an autopilot entry naturally, infer options from prompt, cwd, and artifacts, summarize the choice once where the capability requires confirmation, then invoke. Direct slash invocation already supplies intent. High-risk work may route to stronger intensity; rigor derives from intensity and there is no separate user-facing QA axis.

Work isolation follows `OPERATIONS §5.10`: only a typo or one-line direct edit belongs in main. Quick tracked work uses a depth-1 one-shot worker in an isolated worktree. Standard+ features, new modules, and multi-file changes use a task branch and headless depth-1 conductor; it dispatches plan, execute, test, and report as depth-2 file-only stage sessions. Depth 3 or greater is forbidden. Use liveness and `dispatch-wait` rather than trusting notifications. Main selects and harvests merges only after user signal or a dispatched-job harvest.

The main session is the context owner, router, orchestrator, and final integrator (`OPERATIONS §5.10` main-session role contract); separable `standard+` stages go to registered worker sessions, and an inline run of separable work records its reason. A "no sub-agents" restriction covers the Agent tool's native delegation, not registered headless worker dispatch — extend it to both surfaces only when the user names both or runtime evidence verifiably restricts both.

Use `deep orchestrator` for the standard+ conductor. Retain `orchestrator` for already decided mechanical coordination. Planning and architecture may prefer an eligible GPT-family deep maker without hard pinning; use deterministic dispatch-route traces and current capacity.

### 1. Communication Discipline

- **Audience-language first:** respond and write user-facing artifacts in the language the user is currently using unless an explicit target language, venue, external audience, or existing artifact language overrides it. Public repository docs follow the repository's documentation language.
- Be concise and avoid narrating routine process.
- A commitment such as “I’ll fix it” must have the matching action in the same turn.
- Verify mechanisms, tool behavior, and code facts before asserting them.
- Read and follow existing definitions and conventions rather than improvising substitutes. Expose a convention change before committing it.
- For artifact-backed design-history questions, read both current code and relevant spec/plan artifacts and report drift.

### 2. Pause and Autonomy

- Pause flags such as `--user-refine` require an explicit user signal. Importance alone does not add a pause.
- When a non-blocking question receives no answer, proceed with the recommended option and report one line; do not repeat the question.
- Do not ask about obvious, already agreed, or already instructed steps. Ask only for genuinely non-obvious design, format, destructive, or large-scope decisions.
- Broken, placeholder, or partial input does not block a reversible requested artifact. Create the recommended structure, mark the degraded state, and place any question after the result.
- Align non-obvious direction upfront, then execute without repeated mid-stream confirmation.
- Memory semantics belong to the agent. Use `mem` as the single DB write path, and let deterministic code enforce only scope, schema, pending protection, and recovery. Direct built-in file-memory writes are hard-blocked.

### 3. Follow Through

Inside an explicit workflow, continue through routine stage, commit, push, save, and cleanup steps without asking again, subject to the separate deployment and destructive-operation gates. Updates implied by a change—docs, records, comments, and commit messages—are part of that change. Ask before the change if a new design decision, destructive action, or another system requires authority.

## Sources of Truth

- Portable behavior: `core/*.md` and `roles/response-policy.md`
- Runtime Skill catalog: `~/.claude/skills/*/SKILL.md`
- Runtime Agent profiles and modes: `~/.claude/agents/`, `~/.claude/agent-modes/`
- User-facing product guide: `~/.claude/README.md`
- Memory source of truth: `<agent-home>/memory/memory.db`, accessed through `mem`; details in `core/MEMORY.md`
- User profiles: DB `type=profile` records read through `mem profile <aspect>`

## Domain Triggers

| Trigger | Read or invoke | Note |
|---|---|---|
| Major document/research revision | Routing §0 plus `autopilot-refine` | Minor edits update directly and log; five accumulated minors trigger audit |
| Intensity, model role, artifact, or family-wide flags | `core/CONVENTIONS.md` | Core wins on drift |
| Spec-backed follow-up | Routing §0 plus `WORKFLOW §7` | Understand artifacts, check spec drift, then use the code pipeline |
| User-facing wording | Editorial role | Polish final user-facing prose at the selected rigor; instruction files themselves are exempt from a mandatory editorial sub-call |
| Style, naming, analysis, or prior-convention decision | Agent-chosen recall and relevant `mem profile` | Read only when prior context can materially help; current-turn user instructions win |
| Instruction changes | Relevant deterministic checks; drill only when behavioral regression coverage is useful | Do not run costly headless drills automatically |
| On-call report handling | Latest configured on-call report | Handle reversible, unambiguous items with disclosure; discuss judgment-heavy items |

## Artifact and Skill Rules

All Skills assume project-root execution. Prefer `.agent_reports/`, using `.claude_reports/` only as an existing legacy fallback. Folder rules live in `CONVENTIONS §5`, track routing in `WORKFLOW`, and scope in each capability contract. Do not duplicate those definitions here.

Common mistakes include recursively invoking a sub-Skill already active in the pipeline, confusing research/doc/plan artifact roots, generating presentation formats not requested by the capability, and escalating a small task into thorough or adversarial intensity without risk justification.

## Maintenance

Keep this bootstrap compact. Update it only when source-of-truth locations, domain triggers, or Claude-specific realizations of the portable response contract change. Artifact paths and scope boundaries belong in core and capability sources.

Behavioral rules belong in instruction sources, not memory. Project-scoped continuity, decisions, and handoffs belong to `/post-it`; cross-project user preferences belong to a profile record when contextually useful. Memory remains infrastructure for agent judgment rather than a deterministic policy engine.
