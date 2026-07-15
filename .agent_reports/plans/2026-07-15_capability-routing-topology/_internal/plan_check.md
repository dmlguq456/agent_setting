# Plan check — capability routing topology

## Verdict

**PASS WITH IMPLEMENTATION PREREQUISITES.** The plan is executable after the active parity branch lands and the component spec is updated. It does not force every entry capability into depth=2 and directly addresses the code-centric realization gap.

`qa-policy thorough code` requests a selected independent pass with up to two deep and two fast reviewers. No independent-review claim is made here: registered headless dispatch is currently unavailable, and this planning cycle used the documented inline fallback. The four explicit fallback lenses were architecture/topology, enforcement/runtime, capability granularity, and rollout/operability.

## Checks

### Scope coherence — PASS

- Main orchestration goal is scoped to substantial/tracked work.
- Atomic direct work remains inline.
- Quick remains a single depth-1 worker.
- Standard+ topology is capability-specific.

### Depth semantics — PASS

- Pipeline stages and reviewers are separated.
- Resource runners are not misrepresented as model depth.
- Depth 3+ remains forbidden.
- Spec/refine/note/ship asymmetry is preserved.

### Deterministic enforcement — PASS WITH LIMIT

- Registry, route hash, wrapper gates, write scopes, smoke hashes, report contracts, and leases are mechanically testable.
- Semantic scope/separability judgment remains explicit evidence rather than a fake deterministic classifier.
- Codex arbitrary tool denial is not overclaimed; enforcement is limited to repo-owned wrapper surfaces plus audit.

### Runtime currentness — PASS

- Plan distinguishes native subagents from `codex exec` headless dispatch.
- Current hook limitation is treated as a design constraint.
- Installed projection source and task worktree target are separated.

### Concurrency — PASS

- Existing distill/title fixes are reused as evidence.
- Plan replaces script-local caps with a class-aware shared governor.
- Native subagent runtime caps remain a separate user-owned configuration surface.

### Capability granularity — PASS

- Design phases are grouped by ownership instead of one worker per named phase.
- Draft and research retain meaningful file handoffs.
- Transactional capabilities retain a single writer.
- Lab separates model orchestration from detached resource execution.

### Rollout safety — PASS

- Report-only first, capability flags, compatibility window, and per-capability pilots are included.
- Active parity session overlaps are explicitly gated.
- Generated projections are updated only through sources and generators.

## Required refinements during spec update

1. Decide whether the execution registry filename is `capabilities/topologies.json` or a schema-v2 extension of `harness-manifest.json`; do not implement both.
2. Assign exact capability/mode recipes and completion gate identifiers.
3. Define lease backend and native subagent disclosure without editing runtime config automatically.
4. Confirm whether user-systemd is an optional detached backend or keep `setsid+nohup` only.
5. Define report manifest schema ownership between lab and draft.

## Rejected approaches

- all entry skills use a symmetric four-stage pipeline
- every named phase becomes a separate depth-2 session
- free-text inline exception as the only audit surface
- Codex `PreToolUse` `decision=block` as a hard gate
- process PID alone as detached liveness identity
- separate Markdown and HTML report assembly paths
- per-script spawn caps with copied implementations
