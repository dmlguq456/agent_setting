# Namespace-safe stage dispatch — implementation plan

## Route and constraints

- Capability: `autopilot-code`, mode `dev/refactor`, intensity `strong`, QA `standard`.
- Topology: depth-1 owner with depth-2 `code-plan -> code-execute -> code-test -> code-report` stages.
- Self-hosting fallback: `STAGE_DISPATCH_INLINE_OK=dispatch-infra-self-modification`.
- Source writes: assigned linked worktree only. Canonical artifacts: `/home/Uihyeop/agent_setting/.agent_reports`.
- No commit, push, merge, cleanup, runtime config mutation, native-subagent substitution, or primary-checkout mutation.

## Plan

1. Preserve the current wrapper guard as the fail-fast proof for unsafe detached launches.
2. Add portable lifecycle semantics to `core/OPERATIONS.md`: `dispatch-chain` selects `foreground-scoped` only in a transient PID namespace and otherwise remains `detached`.
3. Add a shared lifecycle selector to `utilities/stage-dispatch-fallback.py` and project its selection into both Codex and Claude wrapper invocations.
4. Add wrapper support for the selected lifecycle, exact machine-readable output, attempt-row metadata, terminal exit/signal classification, and signal forwarding while the launcher remains scoped.
5. Add deterministic conformance tests for namespace detection, detached compatibility, foreground completion, exact row closure, timeout/signal handling, and both Codex/Claude wrapper commands.
6. Run focused suites, then dispatch/route/liveness/Fleet/projection/boundary verification proportional to the changed surfaces.
7. Prepare the PRD change as an explicit transaction patch only; the immutable `autopilot-code` route has `spec_touch=false`, so the owning `autopilot-spec` transaction must apply it later.

## QA assurance

`qa-policy standard code` requires one selected independent pass when available (`1x-deep-reviewer+2x-fast-reviewers` upper bound), with final verification. The checked depth-2 path reached inline fallback before spawning a model. Independent stages/reviewers therefore did not run; inline review and deterministic tests are disclosed rather than misrepresented as independent delegation.
