# Agent Harness

> **Portable workflows. Native runtimes. One local source of truth.**

Agent Harness is a local system for closing research, planning, implementation,
and verification work consistently across Claude Code, Codex, and OpenCode. It
is **not a setup for any single runtime**: shared contracts are defined once,
then projected only onto the native skill, agent, hook, and command surfaces
that each runtime actually discovers.

```text
"Implement and test the login API, then leave a change report."
                                  ↓
       plan → execute → test → report + durable evidence
```

## Quick start

You need Python 3.10+, Git, and the CLI for each runtime you plan to use.

```bash
git clone https://github.com/dmlguq456/agent_setting.git ~/agent_setting
cd ~/agent_setting

./tools/install/harness.sh runtime activate \
  --runtime all \
  --mode linked \
  --profile builder

./tools/install/harness.sh runtime doctor --runtime all --strict
```

After activation, manage the installation through the `harness` command on
your `PATH`.

```bash
harness runtime status --runtime all
harness runtime refresh --runtime all
harness runtime doctor --runtime all --strict
```

`builder` is the default profile, so omitting `--profile` activates the same
configuration. Use `--mode packaged` to deliver an immutable revision to
another machine. This path also avoids marketplaces and remote packages.

## Choose your profile

Profiles control how many capabilities and roles are exposed to a runtime.
Dependency closure is included automatically, while kernel surfaces such as
guards, bootstrap instructions, and `memory-scout` remain available in every
profile.

| Profile | Best for | Capabilities | Roles | Modes |
|---|---|---:|---:|---:|
| `starter` | A lightweight core code pipeline | 6 | 4 | 13 |
| `builder` **default** | Software development, analysis, operations, and memory | 14 | 7 | 26 |
| `full` | The complete research, documentation, and design harness | 27 | 8 | 26 |

```bash
harness runtime activate --runtime codex --mode linked --profile starter
harness runtime refresh --runtime all --profile full
```

Activation records the selected profile, capability/role/mode lists, and
manifest digest. You can therefore verify what is installed from runtime state
instead of trusting a README description.

## What makes it different

- **It closes the whole work cycle.** Research and code generation feed into
  specs, plans, execution, tests, reports, and durable evidence.
- **Contracts come before runtimes.** The portable core owns workflow, role,
  artifact, memory, intensity, and QA semantics; adapters translate them only
  into native runtime surfaces.
- **It exposes only what you need.** `starter`, `builder`, and `full` reduce
  skill metadata and agent discovery in practice, not just on paper.
- **Installation state is inspectable.** `status` and `doctor` report the
  absolute source path, revision, digest, profile, duplicates, freshness, and
  required session action.
- **Decisions survive sessions.** Project working memory, durable memory, and
  user profiles share one recall path.
- **Safety rules are executable.** Deterministic guards and tests verify spec
  grounding, artifact order, git state, and projection drift.

## Use it like this

You do not need to memorize command names. Describe the outcome and constraints
in your natural communication language; runtime-native skills select the
relevant pipeline, and user-facing output follows the conversation language
unless you specify a different audience or artifact language.

> “Analyze this repository and create a PRD for the next feature.”

> “Implement and test the login API, then leave a change report.”

> “Review these papers and experiment code, then build a reproduction plan.”

> “Render the current screen, refine the design, and produce a development handoff.”

> “Find the previous decision and apply this project's existing naming convention.”

See [capabilities/README.md](capabilities/README.md) for all entrypoints and
[roles/README.md](roles/README.md) for the portable role model.

## How it works

```text
                       harness-manifest.json
                    capability · role · profile
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
      Claude Code native   Codex native    OpenCode native
      skills / agents      skills / agents  skills / agents
      hooks / commands     hooks / modes    commands / plugins
             └─────────────────┼─────────────────┘
                               │
              activate · status · refresh · doctor
```

- `core/` — workflow, artifact, QA, memory, and git/worktree contracts
- `harness-manifest.json` — canonical machine contract for capabilities, roles,
  modes, packs, and profiles
- `capabilities/`, `roles/` — human-readable portable behavior sources
- `adapters/` — native projections and bridges for each runtime
- `tools/install/` — activation lifecycle that leaves runtime-owned state alone
- `.agent_reports/` — project artifact root for specs, plans, test evidence, and
  handoffs

`linked` is the maintainer default: repository changes appear immediately on
the discovery path. `packaged` creates an immutable local bundle and keeps its
active revision until `runtime refresh`. File visibility and instruction reload
are separate concerns, so `runtime status` reports whether each runtime needs a
re-invocation, new session, or restart through `session_action`.

## Native first, plugins optional

The default product path is a local native projection. Codex and Claude
marketplace bundles are optional distribution experiments, not prerequisites
for generation, activation, or a successful doctor run. OpenCode's local guard
plugin is a native hook bridge, not an external package.

As a result, the default installation does not require:

- marketplace registration
- plugin caches or registries
- npm package fetching
- external MCP servers, connectors, or APIs
- changes to Codex/Claude credentials, sessions, logs, or local databases

Duplicate native and plugin discovery for the same harness is forbidden and
causes strict doctor checks to fail.

## Runtime support

| Runtime | `linked` projection | `packaged` projection |
|---|---|---|
| Claude Code | skills, agents, commands, hooks | Immutable bundle of the same native surfaces |
| Codex | skills, custom agents, modes, hooks | Immutable bundle of the same native surfaces |
| OpenCode | skills, agents, commands, local guard plugin | Immutable bundle of the same native surfaces |

Runtime differences are reported, not hidden. The installer marks unsupported
surfaces as `SKIP` with a reason, while credentials, sessions, databases, logs,
and foreign caches remain outside its ownership. See
[INSTALL_LAYOUT.md](INSTALL_LAYOUT.md) for the detailed mapping.

## Develop the harness

After changing a shared definition, use the single generator to refresh every
core projection and check for drift.

```bash
python3 tools/generate.py
python3 tools/generate.py --check

./tools/generated-projections.test.sh
./tools/install/profile-activation.test.sh
./tools/install/runtime-activation.test.sh
./tools/skill-conformance/check.sh
./tools/check-adaptation-boundary.sh
adapters/codex/bin/preflight.sh doctor
```

Marketplace bundle generation is not part of this path. Humans own the root
README's value proposition and explanation; only machine contracts and runtime
projections are generated.

## Documentation

| Purpose | Document |
|---|---|
| Complete usage guide | [MANUAL.md](MANUAL.md) |
| Capabilities and roles | [capabilities/README.md](capabilities/README.md), [roles/README.md](roles/README.md), [roles/MODES.md](roles/MODES.md) |
| Routing and artifacts | [core/WORKFLOW.md](core/WORKFLOW.md), [core/CONVENTIONS.md](core/CONVENTIONS.md) |
| Git, worktrees, and dispatch | [core/OPERATIONS.md](core/OPERATIONS.md) |
| Memory and recall | [core/MEMORY.md](core/MEMORY.md) |
| Hooks and design principles | [core/HOOKS.md](core/HOOKS.md), [core/DESIGN_PRINCIPLES.md](core/DESIGN_PRINCIPLES.md) |
| Installation and runtime projections | [INSTALL_LAYOUT.md](INSTALL_LAYOUT.md) |
