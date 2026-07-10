# Adaptation Contract

This document defines how the neutral harness becomes a runtime-specific setting.
It is the boundary contract for `claude_setting/`, `codex_setting/`,
`opencode_setting/`, and future runtime projections.

## 1. Source Categories

Every file in this repo must fall into one category.

| Category | Meaning | Examples | Runtime projection rule |
|---|---|---|---|
| Portable source | Runtime-neutral semantics. Describes what must happen, not how a vendor runtime invokes it. | `core/`, portable parts of `tools/`, portable guard algorithms | May be symlinked into adapters if the runtime can read plain files |
| Adapter source | Runtime-specific representation of portable semantics. | `adapters/claude/CLAUDE.md`, `adapters/claude/settings.json`, `adapters/claude/commands/` | Projected into that runtime home |
| Adapter projection | Versioned mirror that exposes adapter source under runtime-expected names. | `claude_setting/`, `codex_setting/`, `opencode_setting/` | Symlink or generated output only; no independent semantics |
| Compatibility reference | Historical source kept for parity/drift checks after an adapter-owned realization exists. | `skills/` byte-equivalent to `adapters/claude/skills/` except sync state | Not projected as portable source; guarded against drift |
| Compatibility passthrough | Legacy file still consumed directly by a runtime before a true portable/adapted split exists. | Mixed shared hooks or utilities not yet split into invariant + adapter wrapper | Allowed only with an explicit debt note in the adapter |
| Runtime state | Tool-owned mutable local state. | `<runtime-home>/projects`, credentials, session logs, caches, DB files | Never committed to this repo |
| Continuity state | Cross-project agent worklog/notes data that survives sessions but is not harness source. | `<agent-notes-root>/cards`, `_layer2`, `_triage`, `digests`, `oncall`, `study` | Never committed to this repo; may be versioned in a separate notes/data repo |
| Local board app state | Worklog-board local app workspace, generated output, DB/cache, dispatch logs, and worktrees. | `<worklog-board-app>/.cache`, `.next`, `.dispatch`, `.env*`, `node_modules`, `<worklog-board-app>-wt/` | Never committed to this repo |

## 2. Adapter Rule

An adapter must not claim support for a surface unless it provides one of:

1. A native adapter file.
2. A generated file with a documented source.
3. An explicit compatibility reference or passthrough entry and the reason it is safe.

Plain symlinks are acceptable only as a projection mechanism. They are not proof
that adaptation is complete.

## 2.1 Runtime Distribution Seam

Installing or exposing the harness in a runtime is its own adaptation seam. A
runtime surface is supported only when the adapter can name the runtime-native
entrypoint and prove that the runtime will discover it.

Use this order when adding a runtime surface:

1. Define the portable invariant in `core/`, `capabilities/`, or `roles/`.
2. Describe the runtime surface as data: kind, destination, invocation syntax,
   conversion rule, hook/config surface, and unsupported fallback.
3. Generate or maintain adapter-owned concrete output from the portable source.
4. Verify runtime discoverability or explicitly mark the surface unsupported.

An adapter must fail closed for unknown or undocumented runtime features. Do not
assume a Claude Code surface exists elsewhere because the purpose is similar.
For example, a runtime with native status, command, skill, hook, or plugin
support should use that native surface first; harness-specific gaps should be
bridged by adapter wrappers.

External reference: GSD Core
(`https://github.com/open-gsd/gsd-core`) uses the same seam shape: canonical
workflow files are transformed into runtime-specific artifacts, while Claude
plugin manifests and Codex skills are concrete runtime projections rather than
portable source. This repo should follow the pattern, not the exact file layout.

## 2.2 Runtime Currentness and Parity Claims

Before answering, planning, or editing adapter projection behavior for modern
runtime surfaces, verify the current runtime documentation and recent practice
instead of inferring from another adapter or from local harness state.

- **Claude Code / Codex surface questions require fresh external research**:
  read the current official documentation first, then inspect local adapter
  realization. Use community posts, issues, or examples only as secondary
  evidence for real-world gaps or practices, and label them as such.
- **Separate existence from parity**: if a runtime supports a feature in some
  form, still state whether it is equivalent to the other adapter's feature.
  Include concrete parity gaps such as model pinning, tool restriction,
  permission inheritance, session/worktree isolation, hook lifecycle, discovery,
  UI visibility, and noninteractive/headless behavior.
- **Plan with verification**: when a projection change depends on a runtime
  capability, the implementation plan must include a current-doc citation or
  note, a local runtime/projection check, and a fallback if the feature is
  unavailable, buggy, or unsupported in this adapter.

## 3. Portable Role Model

Portable docs use role names, not vendor model names:

| Portable role | Meaning |
|---|---|
| `fast reviewer` | Broad, low-latency review: coverage, style, cross-reference, formatting, simple consistency |
| `fast fact-checker` | Narrow source comparison: citations, years, metrics, verbatim matching |
| `fast writer` | Assembly from verified artifacts |
| `fast implementer` | Routine implementation and refactoring |
| `deep reviewer` | Architecture, methodology, safety, domain correctness, high-risk review |
| `deep maker` | High-judgment creation: planning, synthesis, visual/editorial craft |
| `external adversary` | Independent reviewer with different model/runtime/process assumptions |
| `orchestrator` | Tooling, merge, dispatch, and report assembly; should not be the sole judge |

Adapters map these roles to concrete models, reasoning profiles, or tools. Concrete model names belong in adapter documents or generated native files. For dispatch/headless jobs, the main/orchestrator must choose a portable role or concrete model/reasoning setting per job; adapter wrappers must not silently choose a default model or inherit the interactive session model unless the caller explicitly asks for inheritance.

## 4. Capability Model

A portable capability describes:

- trigger semantics;
- required inputs and artifact roots;
- output contract;
- Verification rigor (intensity-derived) semantics;
- delegation roles using the portable role model;
- deterministic guards and side effects;
- recovery and audit requirements.

A runtime skill/slash command/native instruction describes:

- how that runtime invokes the capability;
- which tools are available;
- how subagents or reviewers are spawned;
- how confirmation, pause, and user input work;
- how hook events are attached;
- runtime-specific file formats and frontmatter.

Current `skills/*/SKILL.md` files are compatibility references. Claude Code
consumes adapter-owned concrete files under
`adapters/claude/skills/*/SKILL.md`. Portable capability meaning belongs in
`capabilities/`.

## 5. Hook Model

Portable hook semantics are named by invariant:

| Invariant | Portable meaning |
|---|---|
| artifact order | New artifacts must be created in the allowed dependency order |
| git state safety | Do not edit during merge/rebase/cherry-pick/detached unsafe states |
| spec read gate | Spec-backed work must read the current blueprint before changing code/spec |
| core first gate | Adapter edits must be grounded in an actual current-session read of the relevant core contract |
| memory write guard | Runtime-native memory files must not bypass the unified memory store |
| workflow signal | Surface tracked/untracked mode to the active agent |
| memory recall/inject/distill | Inject relevant memory and optionally distill session deltas |
| worklog state signal | Surface the configured notes root and board app status without moving or mutating data |

Adapters decide whether each invariant is enforced by native hook, wrapper,
manual preflight, or unsupported fallback.

## 6. Projection Invariant

Runtime homes keep their expected names. Common docs describe this generically;
adapter docs own the concrete runtime-home paths and bootstrap filenames:

```text
<runtime-home>/<adapter-bootstrap>
<runtime-home>/<runtime-settings>
<runtime-home>/<runtime-command-or-skill-surface>/
```

Those paths may symlink into versioned projection directories such as
`claude_setting/`, `codex_setting/`, or `opencode_setting/`. The projection
directory must make it clear whether each entry is native adapter output,
portable passthrough, or compatibility debt.

**Projection completeness**: a cross-adapter guard that checks whether every
portable source item has a corresponding adapter-side projection must
**enumerate the source domain** (iterate the actual current entries) rather
than assert a hardcoded list fixed at authoring time — a hardcoded list stops
catching new entries the moment the source domain grows, silently reopening
the exact gap the guard exists to close. This applies at minimum to agents,
hook events, tools, utilities, and scaffolds. Any intentional exclusion from
projection belongs in an explicit exemption or name-mapping list next to the
guard, never as a silent omission, so every excluded entry is a declared
decision rather than an accidental leak.
