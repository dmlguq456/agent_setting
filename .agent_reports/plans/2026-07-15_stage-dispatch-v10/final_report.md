# Stage-dispatch v10 implementation report

SD-44–47 are implemented with report-only rollout preserved.

The route schema now treats tracking as an independent fifth axis and records selection/escalation evidence without inferring dispatch strength from tracked state. Worker startup is route-consumer-only: it validates the immutable record, exact assigned scope, four tracked-gate evidence fields, canonical paths, safe git state, and route-bound source commit before registration or start. Claude, Codex, and OpenCode each have their own fixture, while legacy route-less low-level dispatch remains available.

Topology validation now rejects unauthorized `spec/**` write declarations unless the recipe is the sole owner or declares the conductor precondition. Runtime artifact-guard collisions emit structured route-addressed failures. Spec mutation is serialized across the three canonical files and version snapshots through one lock-held sequence; contenders report BLOCKED, wait, re-read latest state, and allocate the next version.

All six acceptance criteria passed. The separate SD-45 native Codex review initially found stale-source acceptance and legacy `--write-scope` regression; both were fixed and the re-review passed with no remaining high/medium finding.

Registered headless stage execution was unavailable because the sandbox blocked outbound Codex API access. The failure is recorded transparently; implementation, test, and report stages used the documented inline fallback, with the risk review performed by an independent native Codex agent.

The requested branch commit could not be created from this worker: the parent repository's linked-worktree Git administration directory is read-only and rejected `index.lock`. The source worktree is intact and unstaged. Main should commit the harvested diff with subject `feat(dispatch): implement stage-dispatch v10 guards` and trailer `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`; merge/push remain main-owned.
