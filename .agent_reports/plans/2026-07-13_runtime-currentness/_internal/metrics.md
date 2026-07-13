# runtime-currentness metrics

## SD-17 Separability Judgment

Decision: inline standard pipeline, no depth-2 stage dispatch.

Reason: this is a boundary-coupled harness update. The same semantic change crosses fleet rendering, dispatch usage policy, core operations wording, loop catalog/projection, adapter preflight loop-info, manifest generation, and PRD update semantics. Splitting code-plan/code-execute/code-test/code-report into independent stage sessions would force each worker to reinterpret shared runtime-currentness evidence and could produce inconsistent labels or policy wording.

Mitigation: keep durable standard artifacts; keep edits scoped by surface; run focused deterministic tests and projection/boundary checks; report that no independent Codex QA delegation was claimed.

## Unsupported/Fallback Notes

- Independent QA delegation: not used. QA policy permits inline fallback when no separate Codex agent/headless pass ran.
- Original `preflight.sh route autopilot-code . codex-headless` failed because the current wrapper passed relative cwd `.` into spec-skill-gate while the read marker was keyed by absolute project root. The absolute-cwd route passed and the failure is recorded as a local preflight edge case, not a task blocker.
- Runtime projection probe: `loops/runtime-watch.sh --probe` completed successfully, but recorded that the installed `$CODEX_HOME` projection currently points at a different harness root than this worktree. That is reported as local projection state, not auto-fixed by this loop.
- External source fetch: after adding a browser-compatible user agent and visible-text normalization, Codex pricing/changelog and Claude plan/changelog probes succeed. The two OpenAI Help Center article endpoints remain unavailable to shell curl and are explicitly reported as such; normative claims were also checked through official-source browsing.
- Change detector: a hermetic two-run test proves the timestamp and script/hydration noise do not trigger report rewrites; a real two-run probe also returned `report-written` then `unchanged`.
- Commit/push: the headless worker could not create the parent worktree `index.lock`; the main orchestrator owns and completes the final git operation.
