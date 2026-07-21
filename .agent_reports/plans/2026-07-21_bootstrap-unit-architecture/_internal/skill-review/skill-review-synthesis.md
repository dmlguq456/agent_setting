# Skill-Setting Review — synthesis


## skill_setting_map

## How the entry/skill layer is set up (verified across 3 harnesses: claude, codex, opencode)

**Two-tier skill layer + a separate native-agent layer.** Verified: `adapters/` holds exactly `claude/`, `codex/`, `opencode/`.

### Tier 1 — Skills (portable capabilities projected per harness)
- **Entry-group / `invocation_class: entry-router`**: 10 `autopilot-*` capabilities (code, research, lab, design, draft, refine, spec, note, ship, apply) + `audit` (ops/entry-router). Each SKILL.md body is deliberately a *thin router with "no execution procedure"* (`adapters/claude/skills/autopilot-code/SKILL.md:18-20`). Frontmatter carries `name` (Skill-tool invocation key), `metadata.modes`, and `family`/`fam` label.
- **Sub-group / `parent-invoked`**: 13 stage units (`code-plan`/`-execute`/`-test`/`-report`/`-refine`, `design-*`, `draft-*` …), each "only when autopilot-* dispatches; not for top-level routing". These carry the *real* procedure.
- **Pre / ops**: `analyze-project`, `analyze-user` (pre); `post-it` (ops/model-support).
- All SKILL.md are **generated** from `harness-manifest.json` (`SKILL.md:1-2`), which draws semantics from `core/` + `capabilities/topologies.json`. Claude's `skills/` is a compatibility mirror of `adapters/claude/skills/`, enforced byte-identical.

### Tier 2 — Native subagents (Claude-adapter-only)
Verified: `adapters/claude/agents/` = 9 files (plan-team/기획팀, qa-team/품질관리팀, dev-team, design-team, material-team, editorial-team, research-team, codex-review-team, memory-scout). Each is a **runtime named-persona Task subagent** with `name`/`tools`/`model`/`color` frontmatter (`plan-team.md` name:기획팀, model:fable; "Called from code-plan and code-refine skills — not directly by the user"). `qa-team.md` self-describes as a **"qa-team router"** with `metadata.modes:[code-review, plan-review, test, ml-debug, data-curate, security-review]` and a "Team Member Selection" table.

### The skill -> dispatch chain (routing decided at ENTRY, frozen before spawn)
1. **Case selection** (capability + mode + intensity) is a **main-agent judgment**, not a skill: main reads `core/WORKFLOW.md §0.2` semantic-precedence prose + request-shape tables from compact manifest metadata, presents the §0.4 five-field card, user confirms once.
2. On approval the Skill tool invokes the entry skill by frontmatter `name`; entry body directs the owner to load `capabilities/<name>.md` then `references/owner-execution.md` (its only post-approval edge).
3. `--intensity` selects topology: `direct`/`quick` stay inline (1 node); `standard+` compiles a route via `utilities/capability-route.py::compile_route` -> `resolve_recipe(capability, mode)` in `capabilities/topologies.json`, then **verbatim deep-copies** the recipe's pre-enumerated node array (`capability-route.py:304`: `nodes=json.loads(json.dumps(recipe["standard_plus"]["nodes"]))`) into an **immutable hash-sealed route** (`route_hash`/`route_id`, `:342`).
4. The depth-1 owner is a **thin conductor**: iterates already-pinned nodes and dispatches each stage as a dispatch-depth-2 registered headless session via `utilities/dispatch-node.py` -> `stage-dispatch-fallback.py` (v3 ordered transport fallback: same-harness-headless -> cross-harness-headless -> native-subagent -> inline). Depth-2 workers do **zero routing** (worker-route-guard + route immutability). The only dispatch-time decision is a transport hop, never a case/recipe choice.
5. **BUT** inside a standard+ Claude stage, the stage skill invokes native team subagents (`code-plan`->plan-team, qa-team; `code-execute`/`-test`->qa-team), and the team agent runs its **own depth-2 mode sub-router** ("Team Member Selection" in qa-team.md / research-team.md).

## fits

STRONG scaffolding already supports the converged direction on 4 of 5 axes:

1. **Routing-at-entry is real and enforced.** `invocation_class: entry-router` is a first-class frontmatter class on every entry skill; entry bodies are deliberately thin routers with "no execution procedure" (`autopilot-code/SKILL.md:18-20`). Case selection happens pre-approval at the main agent (WORKFLOW §0.2/§0.4).

2. **Never-route-at-depth-2 is architecturally guaranteed for the STAGE graph.** `capability-route.py` seals an immutable hash route BEFORE spawn (`:342`); the depth-1 owner is a thin conductor passing only paths/verdicts; depth-2 stage workers only execute their one pinned contract. Verified `resolve_recipe` is a pure lookup.

3. **UNIT = composable dispatchable atom is embodied.** Each `standard_plus` node carries a full unit contract (kind, inputs, outputs, write_scope, completion_gate, dispatch_depth:2, fallback_hops) and is the dispatch grain. `code-plan/-execute/-test/-report` exist as first-class sub-capability contracts resolved as each worker's `assigned_contract`. Shared vocabularies (worker_kinds, fallback_hops, roles, execution_topologies, resource classes) referenced by-value form a real compositional substrate — the atoms already speak a common language.

4. **TEAM = family-label has an existing non-runtime home.** `metadata.fam` / `manifest.family` (fam:code, family:code) is a pure grouping label already distinct from runtime.

5. **A judgment step partially exists at entry**: §0.2 semantic precedence + mode inference + one-round human-gated ambiguity ask.

Also fits: topologies.json is compositional AT THE STAGE LEVEL (a case = capability+mode expands into a DAG of dispatchable units), and a `route_compiler` scaffold already exists (schema_version:2) pointing toward a compiled-route future.

## breaks

Five concrete breaks, all cross-confirmed by ≥2 streams and verified in-file:

**(A) TEAM = runtime agent, NOT label — the sharpest contradiction.** The direction wants team=family-label and native=ephemeral helper. But the 9 `*-team` files ARE load-bearing runtime named-persona subagents doing the real work: `plan-team.md` (name:기획팀, model:fable) authors the plan; `qa-team.md` is a router owning code-review/plan-review/test. The label sense the direction wants is carried by the SEPARATE `fam`/`family` field, so today "team" is overloaded onto the exact runtime concept the direction rejects.

**(B) Skills DISPATCH-BY-INVOKING native teams, not by dispatching units.** The real behavior atom (code-review, plan-review, test, research-survey, fact-check, ml-debug) exists ONLY as a **mode inside a native team agent**, not as an independently dispatchable unit. 40+ `Agent(subagent_type=...)` call sites across ≥12 stage skills/references (code-plan:36/68, code-execute:99, code-test:26, research/lab/design references). These atoms have NO topologies.json unit row and NO sub-capability home.

**(C) Routing-at-depth-2 IS violated inside stages.** qa-team/research-team run "Team Member Selection" mode routers at depth-2. Worse, classification judgment is explicitly delegated DOWNWARD: `analyze-project/references/mode-doc.md:23` — "If classification remains ambiguous, delegate the judgment to the research-team." This directly contradicts judgment-at-entry.

**(D) NO single entry-skill router; the router is core-doc prose.** "THE entry skill is the router" is realized as 10 sibling entry-router skills PLUS main-agent prose in WORKFLOW §0.2. Each entry skill only routes WITHIN its own family; the cross-family case selector lives in core docs, not a composing skill.

**(E) NO long-tail fallback for un-enumerable requests.** `resolve_recipe` HARD-ERRORS on unknown (capability,mode) (`capability_topology.py:211`), and `validate_registry` demands EXACT coverage against the manifest entry group (`:179-202`). The only escape is a DOWNGRADE to inline direct editing (WORKFLOW.md:271) — a bypass, not a catch-all route. `fallback_hops` is a TRANSPORT fallback, never a request-classification fallback.

## combinatorial_verdict

**VERDICT: The registry is an ENUMERATED-BLOB structure, not compositional — but the target IS achievable because the compositional substrate already exists one layer down.**

Decisive artifact = `capabilities/topologies.json` (schema_version 2). Verified: a flat `recipes[]` of 11 objects (autopilot-lab appears TWICE — setup:689 and eval:818 — proving modes that need different graphs become separate enumerated blobs). Each recipe is a **fully-inlined static blob**: `direct_predicates` + `quick` + a `standard_plus.nodes` array that hand-authors every node inline. There is **NO $ref / include / node-library / template mechanism** anywhere. The compiler does ZERO composition: `capability-route.py:304` verbatim deep-copies `recipe["standard_plus"]["nodes"]`; quick/direct are hardcoded single-node shapes.

**Measured duplication (from combinatorial-recipe-structure, consistent across streams):**
- `direct_predicates`: byte-identical across all 11 recipes (1 distinct).
- `quick` block (minus write_scope): identical across all 11.
- `fallback_hops`: only 2 distinct arrays copy-pasted across 36 nodes.
- 38 nodes collapse to 13 shape signatures — same handful of unit shapes re-inlined.
- **DECISIVE:** only 8 of 38 completion_gates map to a sub-unit skill name; the other 30 are recipe-LOCAL gate strings with no unit skill. The "unit" is re-described per case, not referenced.

**Why the case (not stage) axis explodes:** composition happens at the STAGE level but the design ENUMERATES at the case = capability×mode level. Adding a new case = author a whole new blob + a manifest entry to keep exact coverage — combinatorial authoring.

**Why it IS avoidable:** raw material for a flat unit catalog already exists (13 sub-skills; node contracts already carry kind/inputs/outputs/write_scope/gate/depth/fallback_hops; shared vocabularies referenced by-value). Recipes CAN become `compose(units)`. The blocker is not structural impossibility — it is that (i) 30/38 gates don't reference the catalog, (ii) the finer atoms live as native-team modes with no unit home, and (iii) the composing compiler is deliberately non-authoritative: `rollout.route_compiler` is pinned to **"report-only"** and `capability_topology.py:198-199` HARD-FAILS any other value (test-pinned), with `legacy_low_level_dispatch:true`. Composition is scaffolded but architecturally locked off; the sanctioned de-facto path is still hand-wired dispatch.

## cross_harness_deltas

**The routing LOGIC is identical across all 3 harnesses; only terminal execution surface and one vocabulary differ.**

- `capabilities/topologies.json` + `utilities/*.py` + `capabilities/*.md` are the **portable, harness-neutral core** (CLAUDE.md hierarchy: core -> capabilities -> {Claude, Codex, OpenCode} as siblings). This is where the combinatorial-vs-compositional question is decided ONCE for every harness. `resolve_recipe`/`compile_route` name no vendor.
- **Only place harness identity appears** = the enumerated `execution_surfaces` (verified `topologies.json:1679-1684`): `registered-headless`, `codex-native-subagent`, `claude-subagent`, `claude-agent-team-teammate`, `inline` — and nodes' `fallback_hops` map onto these. `stage-dispatch-fallback.py` fans out to `adapters/<harness>/bin/dispatch-headless.py` for codex/claude/opencode; model/effort mapping is per-adapter.
- **The "team" reification is Claude-adapter-ONLY.** Native `*-team` subagents live only under `adapters/claude/agents/`. The portable layer has NO team concept — it carries portable ROLE families (CONVENTIONS §2: deep-reviewer/maker/orchestrator). So the portable layer ALREADY treats team-like things as labels/roles; the Claude adapter is the one that reifies them into runtime agents. The direction's "team = label" is already true portably and breaks only in the Claude projection.
- **Path delta between streams (not a real divergence):** `claude-skill-setting` cites `adapters/claude/skills/…`; `skill-to-dispatch-chain` cites `skills/…` — these are the enforced byte-identical mirror. Codex/OpenCode consume the same portable spec via their own preflight capability-info projections and were not directly inspected.
- **Net implication:** the fix for (A)/(B)/(C) is a CLAUDE-ADAPTER problem (route real tracked work through registered-dispatch, not the claude-subagent/agent-team surfaces), whereas the compositional-vs-enumerated fix (E + combinatorial verdict) is a PORTABLE-CORE problem in topologies.json touching all three harnesses at once. NOTE: the 6th expected stream (`entry-layer-generation`) arrived as a test placeholder with no findings; this synthesis rests on the 4 substantive streams, which are mutually consistent.

## direction_adjustments

Where the skill-setting reality forces the converged direction to adjust:

1. **"team = label" cannot be a rename — it is a re-homing.** The direction must split the overloaded "team" into (a) the existing `fam`/`family` label field (keep) and (b) the 9 runtime `*-team` agents, whose LOAD-BEARING work must be relocated before demotion to ephemeral helpers. The atoms currently living as team-modes (code-review, plan-review, test, research-survey, fact-check, ml-debug, security-review) need an explicit unit home — none exists today.

2. **"routing at entry" must absorb the depth-2 mode-router.** Demoting native teams strands the "Team Member Selection" judgment and the explicit downward delegation (`analyze-project mode-doc.md:23`). The direction must relocate atom-selection into the entry composition step (or a first-class entry-time judgment unit), not leave it homeless.

3. **"entry skill is the router" must reconcile with the split router.** Today classification lives in core-doc prose (WORKFLOW §0.2) + 10 per-family thin skills, with the §0.4 human gate and the manifest-metadata-only pre-approval load boundary bound to that location. Converging to one composing entry skill MOVES the confirmation gate and load boundary — the direction must state whether §0.2 collapses into a skill or stays in core with the skill as executor.

4. **Composition needs an authoritative compiler = a planned migration, not a flip.** "Compose units" is only possible once `route_compiler` leaves report-only — but that value is hard-pinned and test-locked (`capability_topology.py:198-199`), and `legacy_low_level_dispatch:true` is the real path. The direction must own the report-only -> enforced migration AND preserve the per-route hash-seal (`route_hash` over the full node blob) that guarantees the depth-2 no-routing property; a composition layer must expand-then-validate so existing invariants (write-scope isolation, DAG acyclicity, max_dispatch_depth==actual) still hold on the expanded graph.

5. **The long-tail fallback is a genuinely NEW element to design, not reuse.** No routing-classification fallback exists; the exact-coverage gate actively forbids un-enumerated cases. A catch-all must be added WITHOUT conflating it with the existing transport fallback and WITHOUT becoming a spec/gate bypass (interacts with WORKFLOW §0.1 no-code-without-spec).

6. **Depth budget must be re-derived.** If units become independently dispatched from inside what is currently a depth-2 stage calling in-session native teams, the depth-3 ban (OPERATIONS §5.10) is at risk; the direction must re-place launch authority, not silently deepen.

## top_risks

- Team reclassification is not mechanical: demoting the 9 native *-team agents to labels/helpers touches 40+ Agent(subagent_type=...) call sites across ≥12 stage skills/references, and a naive rename silently DROPS the depth-2 mode-router + downward classification delegation (analyze-project mode-doc.md:23) that currently lives only inside those agent files.
- The behavior atoms (code-review, plan-review, test, research-survey, fact-check, ml-debug, security-review) have NO unit/capability/topologies home — promoting them to dispatchable units requires net-new sub-capability contracts AND new topologies.json node references; until then 'compose units' has nothing to compose at that grain.
- Flipping to a compositional compiler requires leaving route_compiler='report-only', but capability_topology.py:198-199 HARD-FAILS any other value and a test pins it, and legacy_low_level_dispatch:true is the real path — assuming composition is already runtime-driven is wrong; a report-only->enforced migration must be planned, not flipped.
- The immutable route_hash (sealed over the full node blob, capability-route.py:342) is load-bearing for the depth-2 no-routing guarantee, worker-route-guard, and completion markers; moving from enumerated blobs to composed graphs must expand-then-seal-then-validate or the depth-2 no-routing property and the validator invariants (write-scope isolation, DAG acyclicity, max_dispatch_depth==actual) weaken.
- No long-tail/catch-all route exists and validate_registry actively forbids un-enumerated (capability,mode); adding one interacts with the hard WORKFLOW §0.1 no-code-without-spec/artifact-order gates — a catch-all must not become a spec/gate bypass.
- If units become independently dispatched from inside a stage that today only calls in-session native teams, the OPERATIONS §5.10 depth-3 ban is at risk; the depth budget / launch authority must be re-derived, not silently deepened.
- code-plan/execute/test/report are only PARTIALLY first-class: their graph wiring (depends_on, write_scope, fallback_hops) is duplicated inside each recipe blob, so a compositional refactor risks contract/scope drift between the unit contract and its per-recipe node.

## open_design_questions

- Is capabilities/topologies.json intended to become the SINGLE compositional router (route_compiler promoted from report-only, entry SKILLs collapsing into one composing entry), or does the design keep 10 per-family entry skills with composition inside each? schema_version:2 + report-only compiler signals a migration underway but the current surface does not own it.
- Should the 9 native *-team agents be DELETED and their modes re-homed as dispatchable sub-capability units, or KEPT as thin ephemeral helpers while the atoms become new topologies.json unit rows? A cross-cutting decision beyond the skill layer.
- Should the code-* stage capabilities (and the finer team-mode atoms) become the canonical flat UNIT catalog that recipes compose, and should the 30/38 recipe-local gates collapse onto that catalog — or is the gate-vs-sub-skill divergence intentional as a separate completion vocabulary?
- Where does the entry-level unit composition + the relocated depth-2 mode-selection judgment live: a single composing entry SKILL body, WORKFLOW §0.2, or a new first-class dispatchable judgment unit? Today ambiguity is human-gated at entry AND partly delegated downward.
- Where should the long-tail / un-enumerable-request fallback live, and how does it coexist with the exact-coverage gate (validate_registry) and the hard spec/artifact-order gates without becoming a bypass?
- If route_compiler stays architecturally report-only, is the plan a SEPARATE enforcing composer, or retiring the capability_topology.py:198-199 pin + legacy_low_level_dispatch to make the compiled route authoritative? And does 'entry composes units' permit per-request dynamic node graphs (dynamic depends_on) or only selection among fixed recipe variants as today?
- Are modes intended to remain a curated closed enumeration (mirrored in 3 generated places: SKILL frontmatter, manifest, recipe) or dissolve into free unit composition — a change that touches the harness-manifest.json generator contract, not one file?