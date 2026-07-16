# Entry Skill Layer Audit/Refactor — Implementation Plan

## Contract

- Date: 2026-07-16
- Capability/stage: `autopilot-code` / `code-plan`
- Mode/intensity/QA: `dev/refactor` / `thorough` / `thorough code`
- Route: `rt-598d435deeb0cb81`, node `plan`, source `23c86beaa613571a583f65e869da6b72013a2ad4`
- Worktree: `/home/Uihyeop/agent_setting-wt/entry-skill-layer-audit`
- Artifact root: `/home/Uihyeop/agent_setting/.agent_reports`
- spec-significance: within-spec

## Outcome

Refactor all 13 primary entry-router Skills into two deterministic layers:

1. a compact pre-approval router containing only manifest-owned routing
   metadata, the one-time route-confirmation boundary, and a post-approval
   contract pointer; and
2. a post-approval owner execution contract retaining the existing procedure,
   safety, artifact, role, and verification obligations.

The implementation must preserve behavior, keep worker-bootstrap v5
byte-for-byte intact, refresh Claude/Codex/OpenCode realizations, add
deterministic size/routing/projection/conformance gates, preserve concurrent
fleet-usage commits, commit only this task, and push the task branch.

The 13 routers are `analyze-project`, `analyze-user`, `audit`,
`autopilot-apply`, `autopilot-code`, `autopilot-design`,
`autopilot-draft`, `autopilot-lab`, `autopilot-note`,
`autopilot-refine`, `autopilot-research`, `autopilot-ship`, and
`autopilot-spec`.

## Audit Evidence and Design Decision

Read-only measurements at the route source commit:

| Surface | Count | Aggregate bytes | Largest |
|---|---:|---:|---:|
| `skills/` | 13 | 115,245 | 11,813 |
| `adapters/claude/skills/` | 13 | 115,245 | 11,813 |
| Claude plugin | 13 | 115,245 | 11,813 |
| `adapters/codex/skills/` | 13 | 35,173 | 2,843 |
| Codex plugin | 13 | 35,173 | 2,843 |
| `adapters/opencode/skills/` | 13 | 33,717 | 2,731 |

The manifest already owns all 13 `use_when`/`not_for` descriptions, and
Codex/OpenCode already omit projected procedure detail for entry routers. The
gap is the canonical/Claude body layer: owner procedure is exposed with the
entry Skill. Existing conformance checks line count, reference depth, and
invocation metadata, but not entry-body bytes or load phase.

Design:

- `harness-manifest.json` remains the compact routing-metadata source.
- `capabilities/<name>.md` remains the portable post-approval owner contract
  and topology/guard authority.
- Each canonical entry `SKILL.md` becomes a compact router. Its current
  procedure moves without semantic loss to the one-level
  `references/owner-execution.md`, which may point to existing references.
- Direct/quick acting sessions load selected owner detail only after approval.
  At standard+, depth 1 loads the capability/owner contract; depth-2 workers
  still load only their assigned stage contracts.
- Root `skills/` is the canonical Skill procedure/reference input for this
  refactor. Claude projects it; Codex/OpenCode remain sibling-native and must
  not receive copied Claude procedure text.
- Hard budget: 4,096 UTF-8 bytes per complete pre-approval `SKILL.md`
  (frontmatter included) and 53,248 bytes aggregate (13 × 4,096). This leaves
  headroom above the current native compact maximum of 2,843 bytes.
  Post-approval references are measured separately.
- Report static UTF-8 input only; make no total-token, billing, cost, savings,
  or ROI claim.

## Execution Plan

### 0. Safety, concurrent work, and baseline

1. Revalidate cwd, route node, task branch, clean source worktree, and canonical
   artifact root. Run write preflight before every source edit.
   The final planning check first found three unowned modified generators plus
   untracked `tools/sync-entry-skill-layer.py` after two earlier clean checks.
   That activity then expanded asynchronously across core, capabilities,
   canonical/Claude Skills, plugin projections, owner references, and a new
   test. It resembles the terminated r2 direction but was not created,
   adopted, or reviewed by this stage. Treat the entire dirty source tree as
   untrusted prior/concurrent-worker state. Before execution, the owner must
   establish provenance and restore a clean authorized base or explicitly
   adjudicate it; do not continue it as plan input.
2. Fetch `origin`; compare `HEAD`, `origin/main`, and the task remote ref.
   Never reset, amend, force-push, or edit the primary checkout.
3. Preserve concurrent fleet-usage commits exactly. Merge an advanced
   `origin/main` into the task branch, reconcile overlaps file by file, and
   retain both contracts. Repeat immediately before commit/push.
4. Capture pre-change output under canonical logs. Planning baseline:
   - `python3 tools/generate.py --check`: PASS.
   - `tools/skill-conformance/check.sh`: PASS.
   - strict static `context-footprint.py`: PASS; worker kernel 1,571 bytes,
     typed combinations 1,862–2,028 bytes.
   - `tools/routing-contract.test.sh`: FAIL with three existing assertions:
     two demand Codex entry procedure preload and one expects a stale Claude
     bootstrap string.
   - adaptation-boundary baseline: unknown because the planning probe exceeded
     30 seconds; capture it with `verification-runner --timeout 180`.
5. Save exact commit, command, exit code, and first failure. The final result
   may eliminate the three in-scope routing failures but may add no unrelated
   regression.

### 1. Portable contract first

Edit in this order:

- `core/WORKFLOW.md`: make §0.4 explicit—manifest metadata before approval,
  selected owner contract after approval, no early references, and no repeated
  confirmation for an already approved route/scope.
- `core/CONVENTIONS.md`: add the phase split, 4,096/53,248 byte budgets,
  one-level post-approval references, and static-byte-only reporting.
- `core/DESIGN_PRINCIPLES.md`: align the compact-router → owner-contract →
  assigned-stage chain.
- `capabilities/README.md`: distinguish post-approval owner contracts from
  manifest discovery metadata and adapter-native Skill projections.
- `harness-manifest.json`, `tools/harness_manifest.py`, and
  `tools/build-manifest.py`: add or derive a validated entry load-phase and
  owner-contract declaration. Reject missing, invalid, non-capability, or
  non-entry declarations.
- Regenerate contract blocks in all 13 `capabilities/<name>.md` files so each
  identifies its post-approval owner status without duplicating generic prose.

Do not change topology, intensity selection, role names, worker inputs,
completion gates, or functional semantics.

### 2. Refactor all 13 canonical Skills/references

For every `skills/<entry>/SKILL.md`:

1. Preserve generated frontmatter, `use_when`, `not_for`, modes, and
   argument shape.
2. Use one compact body shape: identity/source pointer, pre-approval boundary,
   one-time confirmation, post-approval owner load, guard pointer, and one
   reference index.
3. Move all removed procedure, pipeline, modes, output schema, safety detail,
   return format, and examples to
   `skills/<entry>/references/owner-execution.md`. Preserve every current
   obligation and link existing references from that owner document.
4. Keep reference depth at one. Resolve contradictions in favor of portable
   core/capabilities and log each substantive reconciliation.
5. Enforce ≤4,096 bytes for each complete `SKILL.md`, including frontmatter,
   and ≤53,248 bytes aggregate. The owner document must exist and be reachable
   only through the post-approval section.

Preserve especially: analyze-project orientation/full-evidence order; audit
read-only semantics; apply isolation/compile/merge boundaries; code spec drift
and plan→execute→test→report; design visual-harness/token ownership; lab
empirical routing/lineage/`_RUNLOG`/long-run gates; refine's lab handoff;
ship's production/DNS/billing/secret restrictions; and spec's `prd.md`,
snapshot, and lock rules.

### 3. Generators and runtime projections

1. Extend `adapters/claude/bin/sync-native-metadata.py` (or a narrowly renamed
   registered successor) to project the canonical Skill body/reference layout
   plus manifest frontmatter into `adapters/claude/skills/`
   deterministically. Keep the Claude plugin downstream.
2. Update Codex/OpenCode Skill generators to emit the explicit phase boundary
   and validated owner pointer for every manifest entry router. Retain native
   frontmatter, guards, tool contracts, and fallbacks; preload no procedure.
3. Refresh catalogs, invocation policy, Claude native/plugin, Codex
   local/plugin, and OpenCode Skill/commands with `python3 tools/generate.py`.
4. Run `--check`, generate a second time, and compare hashes/status. Never
   hand-edit a generated projection after refresh.
5. Enforce canonical/Claude procedure/reference parity while keeping Codex and
   OpenCode sibling-native.

### 4. Deterministic gates

- `tools/context-footprint.py` and its baseline: derive exactly 13 entries
  from the manifest; emit max/aggregate bytes for canonical, Claude, Codex,
  OpenCode, and plugin surfaces; enforce hard budgets and baseline growth;
  retain worker-bootstrap v5 keys and exact values.
- Skill scan/check and generated invocation policy: expose body bytes and
  load-phase/owner-pointer observations; require compact routers and one-level
  post-approval refs across all four Skill trees; keep all 27 classifications.
- Generated-projections test: loop all 13; verify metadata/owner-pointer
  propagation, no procedure preload, stale-edit rejection, restore cleanliness,
  and second-run determinism.
- Routing-contract test: replace only the three stale assertions with all-13
  compact-router/owner-load checks; preserve semantic-primary and long-run
  coverage.
- Adaptation boundary: enforce exact coverage, canonical/Claude parity,
  sibling-native boundaries, freshness, size, and load phase.

The generated-projections test intentionally mutates/restores files. Run it
only in execute/test, never in this read-only planning stage.

### 5. Verification and baseline comparison

Record stdout/stderr/exit codes under canonical `test_logs/`:

1. all-13 static-size audit and unchanged worker-bootstrap v5 surfaces;
2. `PYTHONDONTWRITEBYTECODE=1 python3 tools/generate.py --check`;
3. `bash tools/skill-conformance/check.sh`;
4. `sh tools/routing-contract.test.sh`;
5. strict, no-runtime/no-hook `tools/context-footprint.py`;
6. `python3 tools/capability_topology.test.py`;
7. `sh tools/generated-projections.test.sh`, then clean restore check;
8. adaptation boundary through a 180-second verification wrapper;
9. syntax/targeted unit checks for changed shell/Python code, with bytecode
   outside the worktree;
10. `git diff --check`, generated diff review, and a final rerun after
    integrating any new `origin/main`.

Classify each failure as fixed in-scope baseline, unchanged unrelated baseline,
or new regression. A new regression blocks PASS and push. Do not weaken a test
to accept a missing contract.

### 6. Commit and task-branch push

1. Fetch/merge current `origin/main` again, preserve fleet-usage commits, and
   rerun verification.
2. Reject changes to `roles/worker-bootstrap.md`,
   `roles/worker-types/**`, dispatcher behavior, runtime state, primary
   checkout, or tracked artifact shadows.
3. Commit only intended source, generated outputs, tests, and approved cycle
   records; do not amend/squash another author's commit.
4. Push explicitly, e.g. `git push -u origin HEAD:entry-skill-layer-audit`.
   Never push `main` and never force-push.
5. Record commit SHA, remote ref, byte deltas, generated outputs, test matrix,
   baseline comparison, warnings, and unsupported runtime details.

## Completion Gate

This stage passes when the plan/checklist/review are durable, all 13 routers and
runtime surfaces are covered, no blocking plan defect remains, the QA fallback
is disclosed, and the stage itself made no source edit. Late unowned source
mutations are a mandatory owner precondition for execute, not implementation
evidence from this stage.

The later cycle passes only when exactly 13 routers satisfy the two-layer
contract on every surface; owner content remains complete; size, routing,
projection, conformance, topology, and adaptation gates pass (or only unchanged
unrelated baseline failures are documented); worker-bootstrap v5 remains
intact; concurrent fleet work is preserved; and the verified task commit is
pushed.

## Planning Warnings

- Thorough QA requested 2 deep + 2 fast selected independent reviewers. This
  depth-2 stage cannot dispatch, so it makes no independent-review claim. It
  records the mandated inline fallback in
  `_internal/plan_reviews/plan-check.md`; the owner may add an allowed pass.
- Core/spec read-marker commands emitted read-only-filesystem warnings while
  targeting the installed harness root. The files were read, but full marker
  support must not be claimed.
- The adaptation-boundary baseline remains incomplete until the executor runs
  the 180-second bounded check before edits.
- Final source status changed from clean to an asynchronously expanding,
  unowned implementation diff spanning core/capabilities/Skills/plugins/tools.
  This stage did not write or reuse those paths. The owner must resolve the
  whole dirty tree before execute.
