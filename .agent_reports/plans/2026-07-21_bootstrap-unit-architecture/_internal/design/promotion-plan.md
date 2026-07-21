# Route-Compiler Promotion Plan — report-only → enforced (Workstream B design)

> Companion to `topologies-v3-draft.json` (same directory). Draft status: design round;
> apply happens after review, in commit C2 (topologies + validators + compiler, one commit,
> revertable as a unit). All line numbers refer to the current files at design time.
>
> Draft verification already performed: the v3 draft passes the CURRENT structural
> validator (DAG, write-scope isolation, depth ceiling, exact entry coverage 10/22,
> reviewer/map scope rules) when the two rollout pins are normalized, and a prototype of
> the new unit validator resolves all 43 node unit refs against the live
> `roles/units/` catalog with zero kind/role/read-only mismatches.

## 1. What changes, in one view

| Axis | Today | v3 draft |
|---|---|---|
| `schema_version` | 2 | **3** (forces atomic registry+validator landing; old validators fail closed) |
| `rollout.route_compiler` | `"report-only"` (validator-pinned) | `"enforced"` (validator-pinned to the new value) |
| `rollout.legacy_low_level_dispatch` | `true`, **zero consumers** | **removed**; validator forbids the key |
| Nodes | 38, no unit refs | **43**, every node has `"unit"`; 5 hoisted review siblings |
| Gates | 38 (30 recipe-local) | 43, all mapped in `completion_gate_contracts` (28 unit-io / 8 capability-doc / **10 custom kept**) |
| Team invocation | in-stage (`plan-team`, `qa-team`, …) | abolished; review atoms are sibling depth-2 nodes |

## 2. rollout reconciliation

### 2.1 `rollout.route_compiler`: `"report-only"` → `"enforced"`

The flag has **no runtime reader** — `grep -rn route_compiler` hits only
`capabilities/topologies.json:47`, the validator pin `tools/capability_topology.py:198-199`,
and the pin's test `tools/capability_topology.test.py:54-55`. "Enforced" is therefore
realized by three coordinated moves, not a flag flip:

1. Registry value flips to `"enforced"` (in the v3 draft).
2. The validator pin flips to require `"enforced"` (fail-closed in BOTH directions —
   a leftover `"report-only"` registry now fails validation).
3. Doctrine: `core/WORKFLOW.md:370` gains the enforcement sentence — a standard+ or quick
   dispatch without a compiled, verified route is a contract violation, and
   `stage-dispatch-fallback.py` / the dispatch wrappers treat a missing/unverifiable
   route file as a hard error (workstream D lands the doc text; the wrapper check is
   already the behavior of `capability-route.py verify` + the route guard).

### 2.2 `legacy_low_level_dispatch` retirement — verified

Evidence: repo-wide grep (`*.py, *.sh, *.md, *.json`, excluding `.agent_reports/`)
returns exactly one hit: the registry line itself (`capabilities/topologies.json:48`).
No tool, hook, wrapper, or doc consumes it. Action: key removed in v3; validator
addition rejects its presence (see §6) so it cannot silently return.

### 2.3 Pin + test edits (exact)

- `tools/capability_topology.py:180` — `!= 2` → `!= 3` (message: "legacy topology
  registry is read-only" stays accurate).
- `tools/capability_topology.py:198-199` — replace with:
  - `route_compiler != "enforced"` → raise `"route compiler rollout must be enforced"`.
  - `"legacy_low_level_dispatch" in registry.get("rollout", {})` → raise
    `"legacy_low_level_dispatch is retired"`.
- `tools/capability_topology.test.py:54-55` (`test_tracking_and_rollout_schema_fail_closed`) —
  invert: set `route_compiler="report-only"` and assert regex `"enforced"`; add a case
  reinserting `legacy_low_level_dispatch: true` and assert regex `"retired"`.
- `tools/capability_topology.test.py:11` — `(10, 22)` is unchanged (no new recipes; new
  nodes only). Digest-stability assertion unchanged.

## 3. Entry-coverage resolution: analyze-project / analyze-user / audit

`expected_recipe_keys` (`capability_topology.py:36-40`) filters `group == "entry"`.
Manifest facts: `analyze-project` and `analyze-user` are group **`pre`**; `audit` is group
**`ops`**. They are NOT in the entry-coverage domain today, and adding recipes for them
would *break* exact coverage (extra keys). Decision, with evidence:

**Documented class exclusion + compose-on-demand, no new recipes.**

- `audit` — explicitly declares "**No delegated role invocation** — run `/audit` in the
  current agent session without `research-team` or `qa-team` workers"
  (`adapters/claude/skills/audit/references/owner-execution.md:84`). Its only team touch
  is a single in-session `editorial-team` polish of the report
  (`references/report-and-autofix.md:71-77`), which re-homes as the `editorial/polish`
  unit invoked inline by the owner (direct intensity) or as a one-node composed route.
  → class exclusion is already the file's own contract; document it, done.
- `analyze-project` — DOES delegate (`research-team` in paper/doc modes, `qa-team` Phase 5
  in code mode; `references/owner-execution.md:81-92`). Post re-home these become
  dispatches of `research/research-survey` and `qa/test`/`qa/code-review` units. Because
  the capability is `pre`-group (persistent-analysis producer, not an entry pipeline), it
  routes via **compose-on-demand** (§5): the owner composes a small map/review graph from
  the catalog, passes the same validator + hash-seal + §0.4 card. No recipe, no silent gap.
- `analyze-user` — same shape (3 parallel `research-team` extraction passes,
  `references/owner-execution.md:65`, `pipeline-phases.md:52`) → composed map-reduce
  (3× `research/research-survey` shards + owner consensus synthesis).

Coverage rule stays exact for `group == "entry"`; the exclusion and its rationale are
recorded in the registry consumer docs (workstream D: CONVENTIONS/WORKFLOW) and in this
plan. Revisit-with-evidence path: if composed analyze-* routes recur with a stable shape,
promote that shape to a curated recipe then (recipes are the fast path, composition is
the fallback — spec v3 §1).

## 4. Node→unit mapping (all 43; documents every collapse)

Legend: `←` = role updated to the unit's portable role (role consistency rule, §6).
`_kernel/owner` = depth-1 conductor identity (bootstrap owner overlay + entry capability
is the contract; a catalog persona here would create a second persona source).
`_kernel/resource` = detached process, not an agent.

| Recipe / node | kind | unit | Notes |
|---|---|---|---|
| apply/apply | pipeline-stage | dev/refactor | generic artifact application ≈ mechanical edit atom |
| apply/verify | review-worker | qa/code-review | gate `apply-verify` collapses to unit io |
| apply/handback | capability-owner | _kernel/owner | gate stays custom |
| code/plan | pipeline-stage | plan/plan-author | write_scope narrowed to `plan/**` (review scope hoisted out) |
| **code/plan-check (NEW)** | review-worker | qa/plan-review | hoisted from `code-plan/SKILL.md:68` (`qa-team` plan-review mode) |
| code/execute | pipeline-stage | dev/backend (+`unit_choices` dev/*) | task-resolved member sealed at compile; deps now `[plan-check]` |
| **code/impl-review (NEW)** | review-worker | qa/code-review | hoisted from `code-execute/SKILL.md:99-108` (per-phase `qa-team` loop → single post-execute review + retry boundary) |
| code/test | pipeline-stage | qa/test ← fast reviewer | stage-kind with review-natured unit: writes `test_logs/**` (stage artifact), so review-worker scope rule doesn't fit; compat table §6 allows it |
| code/report | pipeline-stage | editorial/polish ← deep editor | absorbs BOTH `code-report/SKILL.md:37` (fast-writer assembly) and `:105` (editorial polish) — same-family, no sibling needed; **gap G1** below |
| design/refs | map-worker | material/web-image-search ← fast tool worker | hoist of `design-refs/SKILL.md:51`; brief synthesis folds into build |
| design/build | pipeline-stage | design/maker | `design-components/SKILL.md:46,69,89,104` maker calls become the node's own unit |
| **design/visual-verify (replaces visual-review)** | review-worker | design/verifier | from `design-review/SKILL.md:35`; scope `reviews/visual/verify/**` |
| **design/critic-review (NEW)** | review-worker | design/critic | from `design-review/SKILL.md:92`; scope `reviews/visual/critic/**`, concurrent with visual-verify (disjoint) |
| design/handoff | pipeline-stage | editorial/polish ← deep editor | deps `[visual-verify, critic-review]`; gap G1 |
| draft/material-strategy | pipeline-stage | research/research-survey | `draft-strategy/SKILL.md:62` research-team delegation = the node's unit |
| **draft/strategy-review (NEW)** | review-worker | research/fact-check | hoisted from `draft-strategy/references/qa-review.md` (fact-checker subrole) |
| draft/draft-production | pipeline-stage | research/research-survey | deps `[strategy-review]` |
| **draft/quality-review (replaces review-refine)** | review-worker | editorial/review | quality half of the old combined review |
| **draft/fact-verify (NEW)** | review-worker | research/claim-verify | classification-table half (`draft-refine/SKILL.md:86`; 8-row table re-homes into research/claim-verify body) |
| draft/finalize | pipeline-stage | editorial/polish ← deep editor | deps `[quality-review, fact-verify]` |
| lab-setup/scaffold | pipeline-stage | dev/new-lib (+choices) | |
| lab-setup/smoke | review-worker | qa/ml-debug | gate `hash-bound-smoke` stays custom (hash binding is infrastructure, not persona) |
| lab-setup/full-run | resource-runner | _kernel/resource | |
| lab-eval/eval-run | resource-runner | _kernel/resource | |
| lab-eval/metrics | pipeline-stage | material/data-script ← deep maker | |
| lab-eval/media | pipeline-stage | material/figure-gen | |
| lab-eval/report | pipeline-stage | editorial/polish ← deep editor | gap G1 |
| lab-eval/independent-verify | review-worker | qa/test ← fast reviewer | figure-semantic-verify LAW rides in the unit's `tools:` (dual placement per spec §2) |
| lab-eval/sync | capability-owner | _kernel/owner | |
| note/scan | map-worker | qa/data-curate | coverage triage = curation atom |
| note/route-apply | capability-owner | _kernel/owner | single-writer gate stays custom |
| refine/review | review-worker | editorial/review (+choices claim-verify, code-review) | artifact-type-resolved at compile, sealed |
| refine/transaction | capability-owner | _kernel/owner | snapshot/diff transaction is conductor work |
| research/retrieval | map-worker | research/research-survey (branch `search`) ← deep maker | **open choice O2**: material/browser-fetch would be the cheap fan-out alternative; kept survey for source-policy judgment |
| research/synthesis | pipeline-stage | research/research-survey | |
| research/report | pipeline-stage | research/research-survey (branch `report`) ← deep maker | survey unit owns the report templates |
| research/claim-verify | review-worker | research/claim-verify ← fast fact-checker | |
| ship/release-setup | capability-owner | _kernel/owner | |
| ship/security-review | review-worker | qa/security-review | confidence bar 8 lives in the unit |
| ship/release-review | review-worker | qa/code-review | |
| spec/research | map-worker | research/research-survey | |
| spec/review | review-worker | research/plan-review | floor `highest` — intent review is the value core |
| spec/prd-transaction | capability-owner | _kernel/owner | |

**Conditional companions are NOT recipe nodes.** `code-plan/SKILL.md:78` (plan companion
translation) and `draft-strategy/references/mirror.md:5` (draft mirror) are conditional
`editorial/translate` invocations: they become compose-on-demand extension nodes appended
at compile when the companion contract is present — a static optional node would either
always dispatch or need runtime routing at depth 2, both worse. `code-refine`
(out-of-recipe stage; `code-refine/SKILL.md:24,46`) maps to re-entering the `plan` →
`plan-check` boundary pair (`resume_retry_boundaries` already carries both).

**Gate collapse summary** (machine copy in `completion_gate_contracts`): 28 gates → unit-io
(the gate's checkable contract = the referenced unit's `io.verdict` + node outputs);
8 gates → existing capability docs (`capabilities/{code-plan,code-execute,code-test,code-report,design-refs,design-handoff,draft-strategy}.md` + design-refs);
**10 stay custom, each with a recorded reason**: apply-hash, apply-handback,
hash-bound-smoke, authorized-full-run, hash-bound-eval, lab-sync, note-single-writer,
refine-transaction, ship-setup, spec-atomic-transaction — all are owner-transaction,
human-gate, or hash-binding gates where the contract is infrastructure, not persona.

**Catalog gaps flagged to workstream A** (nothing dropped silently):
- **G1 — no fast-writer/assembly unit.** code/report, design/handoff, lab-eval/report,
  draft/finalize map to `editorial/polish` (deep editor), a tier RAISE from "fast
  writer". Either accept (polish body already covers assembly boundaries) or author
  `editorial/report` at floor `low` with role `fast writer`; the draft carries
  editorial/polish so the registry is valid either way — swapping the ref later is a
  one-line node edit + reseal.
- **O2 — retrieval tier** (see table row research/retrieval).

## 5. Compose-on-demand mechanics (long-tail fallback)

Principle (spec v3 §1): composition changes route *shape*, never gate *applicability*.
Implementation is a **pre-compile recipe synthesis**, so everything downstream is
byte-identical to the curated path:

1. **Expand**: new `capability-route.py compose` entry point takes
   `--capability <manifest capability> --mode <mode> --node <spec>...` (or `--graph
   <json>`), where each node spec names a catalog unit; it synthesizes a recipe-shaped
   dict: `direct_predicates` = the common 7-predicate block, `promotion_signals` from the
   caller's card, `standard_plus.nodes` from the unit specs with node-owned write scopes,
   `owner_dispatch_depth: 1`, `max_dispatch_depth: 2`.
2. **Validate**: run the SAME `_validate_recipe(recipe, registry)` (refactored public) +
   the §6 unit validator — DAG, write-scope isolation, reviewer/map scope rules, depth==2
   ceiling, unit refs. A composed graph cannot express anything a recipe couldn't.
3. **Hash-seal**: `compile_route` is refactored to `_compile_from_recipe(recipe, ...)`
   (the body from `utilities/capability-route.py:264` onward, after `resolve_recipe`);
   both the curated path (`resolve_recipe` result) and the composed path feed it. The
   payload additionally records `"composed": true` and `"composed_recipe"` (the full
   synthesized recipe embedded), then the ordinary seal runs — nodes deep-copied
   (`:304`), dispatch evidence checked and fallback chains stamped (`:315-319`),
   `route_hash` computed and pinned (`:342`).
4. **Verify**: `verify_route` gains one branch — when `route["composed"]` is true,
   re-run `_validate_recipe(route["composed_recipe"], registry)` and check the route's
   nodes equal the composed recipe's nodes (both are inside the hashed payload, so this
   is a determinism re-check, same spirit as the fallback-chain recheck at `:450-456`).
   Everything else (hash `:352`, registry digest `:356`, depth checks `:357-390`,
   dispatch-evidence recheck) applies unchanged.
5. **Gates preserved**: the §0.4 five-field card is presented for composed routes exactly
   as for recipes (`composed: true` is displayed on the card); `spec_touch` is computed
   from the composed scopes (`:321`), so the §0.1 spec/artifact-order gate applies by
   construction — **no bypass is representable**, because gate applicability derives from
   write scopes and tracking evidence, not from recipe membership.
6. **Record**: `composed: true` rides inside the sealed payload → Fleet and completion
   markers see it via the route file; no separate registry mutation.

## 6. Validator extensions (fail-closed, stdlib-only)

New in `tools/capability_topology.py` (called from `_validate_recipe` per node, after the
kind check at `:119`):

- **unit exists** — `unit` matches `^[a-z-]+/[a-z-]+$` or is reserved
  (`_kernel/owner`, `_kernel/resource`); catalog refs must resolve to
  `roles/units/<unit>.md`; frontmatter scalars read with the same regex technique as
  `worker_bootstrap.profile_worker_type` (no YAML dependency).
- **kind ↔ worker_type** — per the registry's own `unit_kind_compatibility` table:
  `capability-owner` → `_kernel/owner` only; `resource-runner` → `_kernel/resource` only;
  `review-worker` → `review` only, AND the unit must declare `read_only: true`;
  `pipeline-stage` → `{stage, review, support}` (review allowed because stage-positioned
  verification writing stage artifacts — code/test — cannot satisfy the reviewer scope
  rule and is a pipeline stage by write class); `map-worker` → `{support, stage, review}`.
- **role consistency** — `node.role == unit frontmatter role` (a node never overrides the
  unit's portable role; the model still resolves per-adapter via models.conf).
- **unit_choices** — when present, every member passes the same checks and
  `node.unit ∈ node.unit_choices`.
- **gate contracts** — every gate in every recipe's `completion_gates` has a
  `completion_gate_contracts` entry; `unit-io` entries must name the unit of the node
  carrying that gate; `capability-doc` contracts must exist on disk.
- **rollout** — `route_compiler == "enforced"`; `legacy_low_level_dispatch` forbidden
  (§2.3).
- **catalog digest (recommended)** — compile stamps `unit_catalog_digest` (sha256 over
  sorted `roles/units/**/*.md` frontmatter blocks) into the payload so unit-contract
  drift after sealing is detectable at verify, mirroring `registry_digest`. Unit BODY
  prose stays un-hashed by design (persona wording may evolve; the machine contract may
  not).

## 7. PROOF SKETCH — hash-seal and depth-2 no-routing survive

**Claim 1: route_hash sealing is unchanged in mechanism and strengthened in scope.**
- Curated path: `compile_route` copies recipe nodes verbatim —
  `nodes=json.loads(json.dumps(recipe["standard_plus"]["nodes"]))`
  (`utilities/capability-route.py:304`). The new `unit`/`unit_choices` fields are inert
  JSON data on those nodes, so they flow into the payload untouched. The payload is
  hashed over its canonical bytes minus `route_hash`/`route_id` (`route_hash()`,
  `:90-92`) and pinned at `:342`; `verify_route` recomputes at `:352` and rejects any
  drift. Therefore a worker (or anyone) editing a node's `unit` after compile breaks the
  hash — unit assignment is sealed exactly as write scopes are.
- The registry that DEFINES the units' machine contracts is itself pinned:
  `registry_digest` is in the hashed payload (`:330`) and rechecked against the live
  registry at `:356`. With §6's `unit_catalog_digest` the unit frontmatter is pinned the
  same way. Composed routes embed their synthesized recipe inside the hashed payload, so
  they are *more* sealed than today's recipes (which live outside the route file but are
  digest-pinned).
- Consequence to schedule around: flipping the registry invalidates all in-flight
  standard+ routes ("stale registry digest") — land C2 in a quiet window; in-flight
  cycles recompile.

**Claim 2: depth-2 workers still cannot route, and the last depth-3 pressure is gone.**
- A depth-2 worker receives kernel + worker-type overlay + unit BODY as plain markdown
  (`worker_bootstrap.render_worker_bootstrap`, stdlib file reads); no compile authority,
  no registry write, and `worker_route_guard` continues to bar route mutation. The unit
  ref adds only persona text to what the worker reads — zero new capabilities.
- Routing decisions exist at exactly two moments, both pre-spawn and both sealed: recipe
  resolution/composition (owner, §0.4-gated) and fallback-chain stamping from checked
  dispatch evidence (`:315-319`), which `verify_route` re-derives and compares
  (`:450-456`). Nothing a worker does at runtime can change which units run where.
- The only mechanism that ever pushed toward depth-3 was in-stage team invocation
  (a depth-2 stage spawning a persona). Section 4 hoists every such call (grep-complete
  inventory: code-plan:68, code-execute:99-108, code-report:37/105, code-refine:24/46,
  code-test:26 [self-unit], design-refs:51, design-components:46-104 [self-unit],
  design-review:35/92, draft-strategy:62/qa-review/mirror, draft-refine:37-137) into
  sibling depth-2 nodes or the node's own unit. The validator's ceiling
  (`max_dispatch_depth == max(node depths)`, `capability_topology.py:103-115`; node depth
  ∈ {1,2}, `:136-137`) and verify's realized-depth check (`capability-route.py:389-390`)
  are unchanged and now have no workload that wants to exceed them. Native helpers stay
  ephemeral and outside the route graph entirely.

## 8. Exact file:line edit list for the apply round (commit C2)

1. `capabilities/topologies.json` — replace with `topologies-v3-draft.json` content
   (43 nodes, schema 3, rollout enforced, unit refs, gate contracts, compat table).
2. `tools/capability_topology.py`
   - `:180` schema pin 2→3.
   - `:198-199` rollout pin → enforced + legacy-key rejection (§2.3).
   - after `:119` (inside node loop) → call new `_validate_unit_ref(recipe, node, registry)`;
     new helpers `_unit_frontmatter(unit)` (cached), `_validate_unit_ref`; new module
     constant `UNITS = ROOT / "roles" / "units"`.
   - after `:145` (gate membership) → gate-contract cross-check (§6).
3. `tools/capability_topology.test.py`
   - `:54-55` invert rollout expectations; add legacy-key case.
   - new tests: unknown unit ref, kind/worker_type mismatch, node role ≠ unit role,
     review-worker with `read_only: false` unit, gate-contract missing entry,
     `unit_choices` non-membership. (`:11` counts stay `(10, 22)`.)
4. `utilities/capability-route.py`
   - refactor `compile_route` → thin wrapper over `_compile_from_recipe`
     (split point after `:263` `resolve_recipe`).
   - new `compose` subcommand (§5) + `composed`/`composed_recipe` payload fields +
     `unit_catalog_digest` stamping next to `dispatch_defaults_digest` (`:320`).
   - `verify_route` — composed branch (§5.4) + `unit_catalog_digest` recheck.
5. `utilities/capability_route.test.py`
   - `:123` expected node ids →
     `["plan","plan-check","execute","impl-review","test","report"]`.
   - new tests: composed route round-trip (compose → verify → tamper unit → reject),
     composed spec-touch gate, catalog-digest staleness.
6. `utilities/worker_bootstrap.py` — no code change required. Verified: every new node id
   hits `REVIEW_MARKERS` on the legacy fallback path (`plan-check`, `impl-review`,
   `visual-verify`, `critic-review`, `quality-review`, `fact-verify`, `strategy-review`)
   and canonical writers pass `explicit` from node kind anyway. `STAGE_NODE_CONTRACT`
   unchanged.
7. Dispatch-defaults config — no edit required; new node ids resolve
   `harness_affinity: "unspecified"` by default. Optional per-stage affinity rows may be
   added later with usage evidence.
8. `core/WORKFLOW.md:370` region — enforcement + compose-on-demand doctrine
   (**workstream D owns the wording**; listed here for sequencing only).
9. Run order for the apply round: edit 2+3 and 1 in the SAME commit (schema 3 makes a
   mixed state fail closed); then 4+5; regen + full test suites in a clean worktree per
   the standing portable-guards rule.

## 9. Deferred (documented follow-ups)

- **F1 — direct_predicates/quick dedup.** All 11 recipe rows carry a byte-identical
  7-predicate `direct_predicates` block (and near-identical `quick` blocks differing only
  in `write_scope`). Schema 2/3 has no reference mechanism, and introducing loader-side
  `$ref` expansion would change the bytes that `registry_digest`/`route_hash` are
  computed over and surprise raw-JSON consumers (jq, other harnesses) — it breaks the
  "verbatim-copy compiler" guarantee that `compile_route:304` depends on being able to
  treat nodes/predicates as plain data. Follow-up: schema_version 4 with expansion INSIDE
  `load_registry` and the digest defined over the expanded canonical form, landed with a
  paired digest-migration note. Not done now; the duplication is inert data.
- **G1 / O2** unit-tier choices (§4) — one-line node edits once workstream A rules.
- Recipe promotion path for recurring composed analyze-* shapes (§3).
