# Plan Check — Entry Skill Layer Audit/Refactor

## Review contract

- Reviewed: `plan.md`, `checklist.md`
- Route/node: `rt-598d435deeb0cb81` / `plan`
- Intensity/QA: thorough / thorough code
- Review form: inline fallback, not an independent agent pass
- spec-significance: within-spec

The thorough QA policy requests selected independent deep/fast review. This
depth-2 stage is prohibited from dispatching another worker, so the
`independent_delegation_policy` fallback applies. This record claims only an
inline plan review. The depth-1 owner may add an independent pass if an allowed
surface is available.

## Evidence checked

- Required task PRD, canonical tracked-project PRD, worker-bootstrap v5 final
  report, immutable route, stage Skill, and native mode were read.
- Route guard returned `status=ok` for node `plan` at `23c86bea`.
- Source worktree was clean during route/baseline checks on branch
  `entry-skill-layer-audit` tracking `origin/main`. Final checks then found
  late unowned changes that began in three generators and expanded
  asynchronously across core/capabilities/Skills/plugins/tools. This stage did
  not create or adopt them.
- All 13 manifest-classified entry routers were enumerated.
- Current complete-file UTF-8 totals were measured as 115,245 bytes for
  canonical/Claude, 35,173 for Codex, and 33,717 for OpenCode.
- Safe baseline: generation PASS, Skill conformance PASS, strict static
  footprint PASS, routing contract three pre-existing failures.
- Adaptation-boundary baseline remains unknown because the direct probe did not
  complete within 30 seconds; the plan requires a 180-second bounded baseline
  before edits.

## Review findings

### 1. Scope and source order — PASS

The plan begins with portable core/capability meaning, then canonical
Skills/references/generators, and only then Claude, Codex, and OpenCode
projections. It names every required source family and does not authorize
primary-checkout edits.

### 2. All-13 coverage — PASS

The router set is explicit in both artifacts. Per-router requirements cover
frontmatter preservation, compact body, post-approval owner reference,
one-level references, byte budget, and behavior preservation. High-risk
capability-specific contracts are called out.

### 3. Layer ownership — PASS with recorded constraint

The manifest owns pre-approval discovery/routing metadata; capabilities own the
portable post-approval contract; canonical owner references retain runtime
procedure detail; sibling adapters remain runtime-native. The generator step
must enforce canonical→Claude determinism without making Claude a reference
implementation for Codex/OpenCode. The plan states this boundary explicitly.

### 4. Quantitative gate — PASS

The 4,096-byte limit applies to each complete `SKILL.md`, including
frontmatter, and the 53,248 aggregate is its exact 13-file bound. Entry names
must be manifest-derived and exactly 13. References are measured separately.
This is deterministic and avoids token/cost inference.

### 5. Functional preservation — PASS

The work is a relocation/layering refactor, not a procedure rewrite. The plan
requires every removed obligation to land in `owner-execution.md`, preserves
existing references, forbids topology/intensity/worker changes, and names
critical boundaries for analysis, audit, apply, code, design, lab, refine,
ship, and spec.

### 6. Verification and baseline comparison — PASS

The matrix covers size, routing, generator freshness/idempotence, Skill
conformance, topology, generated restore cleanliness, adaptation boundary,
syntax, diff hygiene, and post-integration reruns. It distinguishes in-scope
fixed failures, unchanged unrelated failures, and new regressions. The
incomplete adaptation baseline is an explicit pre-edit requirement rather than
an unsupported PASS claim.

### 7. Worker-bootstrap v5 preservation — PASS

The plan rejects edits to the kernel/type files and gates the exact observed
static sizes (kernel 1,571; combinations 1,862–2,028). No dispatcher or worker
topology change is authorized.

### 8. Git/concurrency/delivery — PASS

The plan fetches and compares before edits and before delivery, integrates
concurrent fleet-usage commits without reset/amend/force, scopes changes to the
task worktree, reruns verification after integration, commits intentionally,
and pushes only `HEAD:entry-skill-layer-audit`.

### 9. Late unowned source state — PASS for plan; execute precondition

The final source status contains an asynchronously expanding implementation
diff that appeared after earlier clean checks and resembles the terminated r2
direction. The planning artifacts do not use it as evidence or continue it.
The plan now requires the owner to determine provenance and restore a clean
authorized base or explicitly adjudicate the entire dirty tree before execute.
This does not invalidate the completed read-only plan, but execute must not
treat any part of the late diff as approved.

## Residual risks for execution

- The Claude generator currently owns frontmatter only. Extending it to project
  body/reference trees must preserve all 27 Skills and reject extras/stale
  files without deleting non-generated content accidentally.
- Moving body text can break relative links or weaken a mandatory reference.
  The all-13 conformance/projection checks and manual generated diff review are
  required; file-size success alone is insufficient.
- `tools/generated-projections.test.sh` mutates/restores source by design. Run
  it only after implementation authorization and verify a clean restore.
- A new `origin/main` fleet commit may overlap core/tools. Reconcile rather
  than replacing either change, then rerun the entire matrix.
- Installed-harness core/spec read markers could not persist under the current
  sandbox. Record this runtime limitation; do not claim marker support.
- Late unowned source changes must be resolved by the owner before execute;
  this stage has no authority to revert another worker's or user's files.

## Verdict

PASS. The plan is implementable, ordered, bounded, deterministic, and
sufficient for handoff. No blocking plan defect remains. Execution has the
explicit precondition to resolve the late unowned source state. Independent QA
was not available at this depth and is not claimed.
