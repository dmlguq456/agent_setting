<h1 align="center">Agent Harness</h1>

<p align="center"><strong>One complete agent workflow across Claude Code, Codex, and OpenCode.</strong></p>

<p align="center">A local-first workflow layer for Claude Code, Codex, and OpenCode.</p>

<p align="center">
  <img alt="Claude Code: native" src="https://img.shields.io/badge/Claude_Code-native-D97757?style=flat-square">
  <img alt="Codex: native" src="https://img.shields.io/badge/Codex-native-111827?style=flat-square">
  <img alt="OpenCode: native" src="https://img.shields.io/badge/OpenCode-native-2563EB?style=flat-square">
  <img alt="Installation: managed release" src="https://img.shields.io/badge/installation-one--line_release-059669?style=flat-square">
</p>

<p align="center"><strong>English</strong> · <a href="README.ko.md">한국어</a></p>

Agent Harness closes research, planning, implementation, and verification work
consistently across supported coding-agent runtimes. It is **not a setup for a
single runtime**. Shared contracts are defined once, then projected only onto
the native skill, agent, hook, mode, and command surfaces that each runtime
actually discovers.

```text
"Implement and test the login API, then leave a change report."
                                  ↓
       plan → execute → test → report + durable evidence
```

## Why Agent Harness

- **Finish the whole cycle.** Research, specs, plans, implementation, tests,
  reports, and durable evidence stay connected.
- **Keep one contract across three runtimes.** Shared behavior is projected
  onto the surfaces Claude Code, Codex, and OpenCode actually discover.
- **Know what is running.** Inspect the active release or checkout, profile,
  revision, freshness, duplicates, and required session action.
- **Start small and grow.** Choose `starter`, `builder`, or `full` without
  forking capabilities or maintaining separate setups.
- **Carry decisions safely.** Durable memory and executable guards preserve
  conventions while checking spec, artifact, git, and projection boundaries.

## Quick start

### Requirements

- Python 3.10+
- `curl` or `wget`
- The CLI for each runtime you want to activate

### Install

```bash
curl -fsSL https://github.com/dmlguq456/agent_setting/releases/latest/download/install.sh | sh
~/.local/bin/harness runtime doctor --runtime all --strict
```

The installer and distribution logic come from the same immutable Release tag;
that exact tag's SHA-256 integrity-checked archive is then installed. It activates
the `builder` profile for all three runtimes as immutable packaged bundles and
registers a daily user-level update check where the OS supports it. It does not
touch runtime credentials, sessions, logs, or databases.

Once `~/.local/bin` is on your `PATH`, manage it with:

```bash
harness runtime status --runtime all
harness update
harness auto-update status
harness runtime doctor --runtime all --strict
```

`harness update` stages and verifies a new release before switching the active
pointer, and rolls back on failure. Existing agent sessions still follow their
runtime-specific re-invocation, new-session, or restart boundary; check
`runtime status` after an update.

The checksum sidecar detects transfer or asset corruption. Publisher
authenticity is anchored to the repository's GitHub Release and HTTPS account
boundary; it is not an independent signature.

To pin a version or disable scheduled checks:

```bash
curl -fsSL https://github.com/dmlguq456/agent_setting/releases/download/v1.0.1/install.sh | sh -s -- --no-auto-update
```

## Choose a profile

Profiles control how many capabilities and roles each runtime discovers.
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

Activation records the selected profile, capability, role, and mode lists plus
the manifest digest. You can verify what is installed from runtime state rather
than trusting a README description.

## Use natural language

You do not need to memorize command names. Describe the outcome and constraints
in your natural communication language. Runtime-native skills select the
relevant pipeline, and user-facing output follows the conversation, audience,
or artifact language instead of inheriting the language of this README.

> “Analyze this repository and create a PRD for the next feature.”

> “Implement and test the login API, then leave a change report.”

> “Review these papers and experiment code, then build a reproduction plan.”

> “Render the current screen, refine the design, and produce a development handoff.”

> “Find the previous decision and apply this project's existing naming convention.”

See [capabilities/README.md](capabilities/README.md) for every entrypoint and
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

| Layer | Responsibility |
|---|---|
| `core/` | Workflow, artifact, assurance, memory, and git/worktree contracts |
| `harness-manifest.json` | Canonical machine contract for capabilities, roles, modes, packs, and profiles |
| `capabilities/`, `roles/` | Human-readable portable behavior sources |
| `adapters/` | Native projections and bridges for each runtime |
| `tools/install/` | Activation lifecycle that leaves runtime-owned state alone |
| `.agent_reports/` | Project artifacts for specs, plans, test evidence, and handoffs |

Managed releases are the general-user default. `linked` remains the maintainer
mode: checkout changes appear immediately on the discovery path, and the
release updater never fetches, pulls, or repoints that checkout. File visibility
and instruction reload are separate concerns, so `runtime status` reports
whether each runtime needs a re-invocation, new session, or restart through
`session_action`.

## Runtime support

| Runtime | `linked` projection | `packaged` projection |
|---|---|---|
| Claude Code | Skills, agents, commands, and hooks | Immutable bundle of the same native surfaces |
| Codex | Skills, custom agents, modes, and hooks | Immutable bundle of the same native surfaces |
| OpenCode | Skills, agents, commands, and local guard plugin | Immutable bundle of the same native surfaces |

Runtime differences are reported rather than hidden. The installer marks
unsupported surfaces as `SKIP` with a reason, while credentials, sessions,
databases, logs, and foreign caches remain outside its ownership. See
[INSTALL_LAYOUT.md](INSTALL_LAYOUT.md) for the detailed mapping.

## Develop the harness

Maintainers can keep a live checkout instead of the managed release:

```bash
git clone https://github.com/dmlguq456/agent_setting.git ~/agent_setting
cd ~/agent_setting
./tools/install/harness.sh runtime activate --runtime all --mode linked --profile builder
```

After changing a shared definition, refresh every generated projection and
check for drift:

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
| Installation and runtime projections | [INSTALL_LAYOUT.md](INSTALL_LAYOUT.md) |
| Release criteria and SemVer automation | [RELEASE_POLICY.md](RELEASE_POLICY.md) |
| Capabilities and roles | [capabilities/README.md](capabilities/README.md), [roles/README.md](roles/README.md), [roles/MODES.md](roles/MODES.md) |
| Routing and artifacts | [core/WORKFLOW.md](core/WORKFLOW.md), [core/CONVENTIONS.md](core/CONVENTIONS.md) |
| Git, worktrees, and dispatch | [core/OPERATIONS.md](core/OPERATIONS.md) |
| Memory and recall | [core/MEMORY.md](core/MEMORY.md) |
| Hooks and design principles | [core/HOOKS.md](core/HOOKS.md), [core/DESIGN_PRINCIPLES.md](core/DESIGN_PRINCIPLES.md) |
