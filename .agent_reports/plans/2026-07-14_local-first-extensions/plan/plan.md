---
status: verified
created: 2026-07-14
spec: .agent_reports/spec/harness-productization/prd.md
spec_version: 5
intensity: strong
qa: standard
---

# Local-First Optional Extensions — Phase 3

## Goal

Add an offline, inspect-first lifecycle for one local instruction skill at a
time without making plugins, marketplaces, package managers, hooks, MCP, or
connectors part of the harness core. Preserve exact source provenance, isolate
external ownership, and report runtime parity loss instead of activating
runtime-specific execution surfaces.

## Runtime evidence

- Codex distinguishes local skills from installable plugins; plugins may bundle
  skills, hooks, MCP/apps, and other assets behind a separate install/cache
  lifecycle. The bridge therefore uses native skill discovery only.
- Claude Code watches standalone skill directories, while plugins have their
  own namespace, registry/cache, reload, hooks, agents, and MCP lifecycle. The
  bridge projects a standalone instruction skill and leaves plugin surfaces
  inactive.
- OpenCode discovers flat `skills/<name>/SKILL.md` entries and requires a
  lowercase hyphenated name matching the directory. Its JS/TS plugins and MCP
  config are separate executable surfaces. The bridge uses a hashed physical name
  and reports all other surfaces as losses.

## Design

### 1. Source inspection

Create `tools/install/extensions.py` with a strict stdlib-only `extension.json`
schema. Resolve one local directory, census every file without following
symlinks, validate the selected `skill_path`, parse minimal SKILL frontmatter,
and calculate a deterministic, versioned tree checksum. The mutation gate uses
`lstat` no-follow census, staging copy, a second inspection of staged bytes,
and a final source checksum comparison; unreadable or over-limit content blocks
instead of being skipped.

Inspection returns:

- canonical id `external/<publisher>/<skill>` and a collision-resistant,
  64-character-bounded physical id with canonical-id hash suffix;
- absolute local source plus Git root/ref/SHA/dirty evidence when present;
- declared license and LICENSE-file evidence;
- declared and detected scripts/hooks/MCP/connectors/packages/plugin surfaces;
- high-confidence secret findings with pattern id + relative path only;
- internal, escaping, broken, and cyclic symlink findings;
- per-runtime projection action, inactive surfaces, and parity status.

Blocking conditions are invalid schema/name/path/frontmatter, source escape,
symlink escape/cycle/broken target, high-confidence secret, or package
dependency. Other executable/runtime-specific surfaces remain inactive and
produce degraded parity.

### 2. Snapshot and registry

Use XDG state/data roots, never the repository or runtime-owned config:

- state: `.../agent-harness/extensions/registry.json`;
- data: `.../agent-harness/extensions/<publisher>/<skill>/<checksum>/`.

Materialize only Markdown files from the inspected skill path. Dereference
validated internal file symlinks into ordinary files and rewrite only SKILL
frontmatter `name` to the physical id. `source-digest-v1` binds relative path,
file type, link target, and source bytes; `projection-digest-v1` binds exact
staged paths and bytes. A composite digest keys the snapshot. Reused snapshots
must be symlink-free and rehash exactly to the lock.

Treat registry contents as untrusted. Recompute every destination and snapshot
path from validated canonical fields and trusted roots. Hold one XDG state file
lock across each mutation, validate registry generation/CAS, and reserve the
`external-` physical prefix against built-in manifest IDs.

### 3. Runtime projection

Project one harness-owned symlink per selected runtime:

- Codex: `<home>/.codex/skills/<native-id>`;
- Claude Code: `<home>/.claude/skills/<native-id>`;
- OpenCode: `<home>/.config/opencode/skills/<native-id>`.

Preflight all destinations and all parent paths. Add refuses an existing
unowned path. Update and remove require the current link target to match the
recomputed owned snapshot. Before the first mutation, persist registry bytes
and all link states in an XDG transaction journal. Multi-runtime link changes
roll back in reverse order on failure, and the next invocation recovers an
incomplete journal after a process crash. Built-in activation state and runtime
config are never mutation targets.

### 4. CLI

Extend the existing parser with:

- `extension inspect <source>`;
- `extension add <source> [--runtime ...]`;
- `extension update <canonical-id> [--source ...]`;
- `extension remove <canonical-id>`.

Keep the existing JSON emitter and exit meanings: 0 success, 2 verification or
parity inspection failure, 3 blocked mutation, 64 usage. Human output must name
the canonical id, checksum, runtime projection, inactive surfaces, and next
session action.

### 5. Acceptance fixtures and tests

Add two committed local fixtures:

- instruction-only: valid manifest/license/SKILL, full parity on three runtimes;
- runtime-specific: portable SKILL plus Claude plugin/hook evidence, skill
  projects but hook/plugin stays inactive and parity is degraded.

Add an isolated-HOME shell E2E covering inspect/add/no-op update/changed update/
remove, source immutability, Git provenance, namespace flattening, package
blocking, secret blocking, symlink escape, ownership conflict, injected
  multi-runtime rollback, crash-journal recovery, concurrent writer/CAS,
  registry/snapshot tampering, parity reporting, and coexistence with built-in
  profile activation/doctor. Include external-only+legacy-plugin and dangling
  extension cases to prove core duplicate detection remains exact.

## Implementation steps

1. Add XDG extension paths and `extensions.py` inspection/state/transaction code.
2. Wire the four CLI commands and stable JSON/human result shape.
3. Add fixtures and lifecycle/security/rollback E2E.
4. Run focused tests, Phase 1/2 regression, generator/adaptation/portable guards,
   compile checks, and diff hygiene.
5. Perform an independent risk review, close findings, update Phase 3 result
   artifacts, then commit and push the feature branch.

## Outcome

Implementation and final verification are complete. The lifecycle is local-only,
projects instruction Markdown into immutable snapshots, keeps runtime-specific
surfaces inactive, and fails closed on untrusted source/state/path transitions.
The independent implementation review closed all three HIGH and four MEDIUM
findings. The branch is ready for commit, upstream integration, and push.

## Risk gates

- Never shell-evaluate manifest/source data.
- Never print or persist matched secret values.
- Never follow an unvalidated symlink or write through a symlinked state/dest
  parent.
- Never remove a destination that no longer matches registry ownership.
- Never report full parity when non-instruction/runtime-specific surfaces exist.
- Never make extension health a precondition of kernel/runtime doctor success.
- Never derive a deletion path from an untrusted registry string.
- Never reuse a snapshot without recalculating its exact projection digest.

## Verification commands

- `python3 -m py_compile tools/install/*.py`
- `sh tools/install/extension-lifecycle.test.sh`
- `sh tools/install/profile-activation.test.sh`
- `sh tools/install/runtime-activation.test.sh`
- `python3 tools/generate.py --check`
- `sh tools/check-adaptation-boundary.sh`
- portable guard and skill-conformance suites selected by Codex doctor
- `git diff --check`
