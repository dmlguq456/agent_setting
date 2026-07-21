# Current-State Architecture Map (investigation synthesis)


## current_state_map

## CURRENT-STATE ARCHITECTURE MAP — persona/unit consolidation

### Layer inventory (top = composition root, bottom = runtime projection)

**L0 — Concrete-value SoTs (already single-source + guarded).**
- `adapters/{claude,codex,opencode}/config/models.conf` — the ONLY legal home for concrete model IDs/efforts/variants. Declares tiers (`CFG_TIER_{DEEP,LIGHT,MINI}_MODEL`), role→tier groupings (`CFG_ROLES_DEEP/LIGHT`), failover cascade (`CFG_TIER_DEEP_FAILOVER_CASCADE`), lifecycle helper tiers, and — codex only — native-agent profile rows (`CFG_PROFILE_*_TEAM=tier:effort:sandbox`).
- Guard: `tools/check-model-config.py` (VERIFIED present; the native-bootstrap stream's claim that only a `.sh` exists is WRONG). Fail-closed grep over `SCAN_DIRS=["adapters","core","roles"]` (line 19); whole-file-exempts `/agents/` (line 27) and generated projections.

**L1 — Portable metadata SoT.**
- `harness-manifest.json` (root, schema_version 2) — declares 27–30 capabilities, 8 roles (`{portable_role, responsibility}`), modes (`{role, status:portable-persona}` — no persona text), packs, profiles, `kernel.agents=['memory-scout']`, and an `ownership.{generated,adapter_owned}` ledger. The single place a capability binds to a bespoke agent: `capabilities[].requires.roles` (VERIFIED — 8 role-teams). Loaded/validated by `tools/harness_manifest.py`.

**L2 — Portable behavior prose + declarative graph.**
- `capabilities/*.md` (30 files) + `capabilities/README.md` — GENERATED from harness-manifest.json (`<!-- GENERATED: harness-manifest.json -->`); already AGENT-NEUTRAL (grep for bespoke team names returns nothing).
- `capabilities/topologies.json` (1692 lines) — the actual DAG. `recipes[]` keyed by (capability, mode); each node carries `role` (PORTABLE MODEL ROLE string), `kind` (worker_kinds enum), `depends_on`, `write_scope`, `dispatch_depth`, `fallback_hops`, `completion_gate`. Validated (not generated) by `tools/capability_topology.py`: checks `node.kind ∈ worker_kinds` (:118) but does NOT validate `node.role` (VERIFIED — grep found no role validation). Consumed at runtime by `utilities/capability-route.py` (immutable route compilation, dispatch contract v3).
- `roles/README.md` Role Catalog (GENERATED) + `roles/MODES.md` (Universal Review Stance, :10-27) + `roles/modes/<family>/<mode>.md` (31 mode personas — the portable domain bodies).

**L3 — Two DISTINCT-lifecycle projection surfaces.**
- NATIVE subagent (Task tool): `adapters/claude/agents/*.md` (9 hand-authored routers, `ownership.adapter_owned`) → read `adapters/claude/agent-modes/<family>/<mode>.md` (a SECOND, drifted copy of the personas). Codex `agents/*.toml` and OpenCode `agents/**/*.md` are GENERATED from manifest roles + models.conf.
- REGISTERED DISPATCH worker: assembled at LAUNCH by `utilities/worker_bootstrap.py::render_worker_bootstrap` (:95-103) = `roles/worker-bootstrap.md` kernel + one `roles/worker-types/{owner,stage,review,support}.md` overlay, then points at `roles/modes/<f>/<m>.md`. Wrapped by `adapters/claude/bin/dispatch-headless.py` / `utilities/stage-dispatch-fallback.py` (liveness, contract-v3 claim, depth accounting, kill/orphan reconcile).

### Where behavior lives (the core finding)
The SAME conceptual "role/mode behavior" is reached through THREE independent declaration paths that are only partially single-sourced:
1. **role → model tier**: single-sourced via models.conf for DISPATCH (through `model-map.sh`) and for CODEX/OPENCODE generated agents; but Claude native agents HARDCODE `model:` in frontmatter (VERIFIED: qa/dev/material=sonnet, research/design/plan/editorial=fable, memory-scout=haiku, codex-review-team=sonnet) with NO generator and NO guard (the `/agents/` exemption).
2. **refute-by-default stance**: asserted "single source" in MODES.md:10-27 but PHYSICALLY restated in ≥6 files (qa/code-review, plan-review, test, research/claim-verify, agent-modes/qa/_review_rules.md [Korean], README.md:92).
3. **domain persona body**: duplicated as `roles/modes/*` (dispatch/capabilities read) vs `adapters/claude/agent-modes/*` (native routers read) — a copy relationship that has ALREADY DIVERGED (English/inline-stance vs Korean/_review_rules-extracted).

### Composition seams already present
- `topologies.json` nodes already carry the two fields a unit needs: `node.role` (→ tier via models.conf) + `node.kind` (→ worker-type/lifecycle). Units project ONTO nodes; nodes own the graph.
- `worker_bootstrap.py` already reduces dispatch persona to kernel + one overlay (single-source, symlinked across 3 adapters).
- Codex `sync-native-agents.py` is a WORKING prototype of "project a role profile + models.conf → generated agent."

## domain_gradient_table

| # | Mode / family | Pole | Mechanical ⟷ Judgment | Extractable shared scaffolding | Irreducible domain core | Persona-min floor |
|---|---|---|---|---|---|---|
| 1 | material/pdf-extract | A | ●○○○○ most mechanical | kernel + support-type + 1-line return (:45-49) | PyMuPDF DPI/two-column/bbox crop tool recipe (dated user feedback :12,:39) | near-ZERO persona; THICK tool fragment |
| 2 | material/browser-fetch | A | ●○○○○ | kernel + support + return (:88-93) | Playwright stealth config, sub-mode procedures | near-ZERO |
| 3 | material/web-image-search | A | ●○○○○ | kernel + support + return | ar5iv→vanity→pdfimages fallback ladder | near-ZERO |
| 4 | qa/test | A | ●○○○○ (QA but a runner) | kernel + review/support + refute stance + PASS/FAIL/SKIP/BLOCKED I/O | level 1→5 ladder + `figure-semantic-verify` tool contract (:17-21) | near-ZERO; THIN fragment |
| 5 | design/verifier | A | ●○○○○ SURPRISE mechanical anchor of design | kernel + review + refute + YAML schema I/O | check-ID set + thresholds 1.0/0.85/0.6; references _design_rules | near-ZERO ("model does not invent a score" :38) |
| 6 | material/data-script | A | ●●○○○ | kernel + support + `<path> -- <verdict>` | speech/TF-DNN metric-table preference (:14-33) | near-ZERO; preference doc |
| 7 | material/figure-gen | A | ●●○○○ | kernel + support + return | spectrogram-integrity LAW + fail-closed manifest verify (:25-53) | near-ZERO; THICK rule fragment |
| 8 | research/fact-check | A | ●○○○○ mechanical anchor of research | kernel + review + refute + table I/O | source-class taxonomy + [FACT] memo | near-ZERO; THIN |
| 9 | editorial/translate | A | ●●○○○ | kernel + support/maker + mirror-path return | thin editorial voice + terminology rule | LOW |
| 10 | dev/refactor | Mid | ●●●○○ safety-checklist | kernel + stage-type + step-log I/O + forbidden-zone guard | thin refactoring-safety core; auto/interactive branch | LOW |
| 11 | qa/data-curate | Mid | ●●○○○ audit checklist | kernel + review + 🔴🟡🟢 I/O + refute | dataset-hygiene axes | LOW |
| 12 | dev/backend | Mid | ●●●○○ | kernel + stage + dual direct/pipeline I/O | thin backend-boundary core | LOW |
| 13 | dev/new-lib | Mid | ●●●○○ | kernel + stage + dual I/O | thin library-design core | LOW |
| 14 | dev/frontend | Mid | ●●●○○ | kernel + stage + dual I/O | frontend core + adapter VISUAL-verify tool coupling | LOW+ |
| 15-16 | editorial/review + polish | Mid | ●●●○○ | kernel + support/review + audience-lang I/O + SHARED catch-net | editorial voice + catch-net (shared across all 3 editorial → strong dedup) | LOW |
| 17 | qa/code-review | Mid | ●●●●○ checklist-framed | kernel + review + refute (verbatim MODES doctrine) + verdict I/O | criteria list + pedagogical voice | MODERATE |
| 18 | qa/plan-review | Mid | ●●●●○ | kernel + review + refute + 🔴🟡🟢 I/O | construction-logic core (bounded vs research plan-review) | MODERATE |
| 19 | qa/security-review | Mid | ●●●●○ judgment bounded by FP-filter | kernel + review + refute + HIGH/MED I/O | threat categories + FP-filter (thick) + confidence-8-10 contract | MODERATE+ |
| 20 | qa/ml-debug | B | ●●●●○ | kernel + review + hypothesis-report I/O | ML-failure diagnosis expertise (thick) | HIGH |
| 21 | research/research-survey | Mid | ●●●○○ mixed | kernel + owner/stage + completion-verdict I/O | venue/access/reading rules + card-synthesis judgment (thick) | HIGH |
| 22 | research/claim-verify | B | ●●●●○ | kernel + review + refute + table I/O + external-verify tool contract | falsification tradecraft; N-vote/quorum aggregation (thick) | HIGH |
| 23 | research/plan-review | B | ●●●●● HIGHEST structural+domain | kernel + review + 1-line return | task-type LENS MATRIX + multi-axis dispatch + meta-skill grep — largest core in inventory | HIGHEST |
| 24 | design/critic | B | ●●●●● aesthetic taste | kernel + review + 5-7 finding I/O + refute | design-taste core + _design_rules substrate | HIGH |
| 25 | design/maker | B | ●●●●● MOST judgment overall | kernel + owner/stage + artifact-path + rationale I/O | _design_rules.md (66 lines taste law) + generative judgment | HIGHEST |

**FAMILY FLOORS (grade WITHIN family, never per-family):** material = uniformly near-ZERO (keep thick TOOL fragments). qa = BIMODAL (test/data-curate mechanical → code/plan/security/ml-debug judgment). dev = LOW + shared step-log/dual-I/O. editorial = LOW, ONE shared voice+catch-net. research = WIDEST spread (fact-check → plan-review). design = split (verifier mechanical outlier vs maker/critic irreducible taste). A per-family minimization policy would over-flatten planning/design capabilities — the UNIT is the correct granularity, keyed on `node.role + node.kind`, NOT capability group.

## duplication_matrix

## Behavior duplicated across surfaces (with file evidence)

| Behavior fact | Physical homes today | Single-source? | Guard? | Drift status |
|---|---|---|---|---|
| **Concrete model ID per role** | (a) models.conf `CFG_ROLES_*`+`CFG_TIER_*` [SoT]; (b) Claude `agents/*.md` frontmatter `model:` literal (VERIFIED 9 files); (c) "Recommended Portable Model Roles" prose in each Claude router; (d) codex `agents/*.toml` (generated); (e) plugin mirror `plugin-marketplace/.../agents/*.md` | Only for dispatch + codex/opencode | NO for Claude native (`/agents/` whole-file exempt, check-model-config.py:27) | LIVE: qa-team.md=`sonnet` vs plugin mirror=`opus` (sync-native-plugin.py shutil-copy stale). Native agents have ZERO GENERATED markers (VERIFIED) |
| **Refute-by-default stance** | MODES.md:10-27 [asserted SoT]; roles/modes/qa/{code-review:8,plan-review:11,test:7}; research/claim-verify:9-10; agent-modes/qa/_review_rules.md:5-7 (Korean, ALSO claims "단일 원천"); README.md:92 | Asserted, NOT realized (≥6 physical copies) | none | Restatements can diverge/be dropped; MODES.md:20 forbids LOWERING but nothing enforces |
| **Domain persona body** | `roles/modes/<f>/<m>.md` (dispatch/capabilities read) vs `adapters/claude/agent-modes/<f>/<m>.md` (native read) — ADAPTATION.md:166-168 calls latter "copied from roles/modes" | NO — copy relationship | none | ALREADY DIVERGED: code-review English+inline-stance+inline-template vs Korean+_review_rules-delegated |
| **🔴🟡🟢 triage output shape** | qa/code-review:52-76, plan-review:23-27, data-curate:26 | NO (verbatim recurrence) | none | extractable I/O contract |
| **"authorized memory flow" closing** | ~20 mode files (code-review:96-98, ml-debug:28, maker:27, verifier:81, …) | NO | none | near-identical wrapper, per-mode retention target differs |
| **Dual direct/pipeline I/O switch** | dev/{backend:31,frontend:30,new-lib:30}, refactor:57-64, code-review:79-86, research/plan-review:55-61, all material modes | NO (one pattern repeated) | none | — |
| **role_note → runtime-role mapper** | codex sync-native-agents.py:85-110 + mapper_roles:113-129 (editorial special-case) vs opencode sync-native-agents.py:59-82 (LACKS mapper_roles) | NO | generate.py --check (byte) | ALREADY DRIFTED (opencode missing codex's extension) |
| **memory-scout kernel-agent instructions** | codex EXTRA_AGENTS:46-67 vs opencode EXTRA_AGENTS:19-41 | NO (inline duplicated) | generate.py --check | near-identical separate copies |
| **read-only/independence stance** | codex ROLE_BOUNDARIES tables:160-194 vs opencode `read_only={qa-team,external-adversary}`:101 vs Claude hand-prose | NO — one fact, three encodings | none | — |
| **node.role ↔ requires.roles ↔ roles/README portable_role** | topologies.json node.role strings; harness-manifest requires.roles; roles/README portable_role | NO cross-validator | capability_topology.py checks node.KIND only (:118), NOT node.role (VERIFIED) | can drift independently TODAY |
| **stage taxonomy (plan/execute/test/report + review markers)** | capabilities/*.md; topology node.kind; worker_bootstrap.py `STAGE_NODE_CONTRACT`:26-35 + `REVIEW_MARKERS`:16-25 | NO (3+ encodings) | none | must stay reconciled |
| **worker_bootstrap.py module** | utilities/ + 3 adapter mirrors | YES (symlinks, VERIFIED) | — | not drifted |

**Note:** GENERATED boilerplate across the 30 `capabilities/*.md` (Guard Requirements 5-bullet block byte-identical; "Concrete model names…belong in adapter files" in ~28 files) is single-SoT (harness-manifest.json) → low risk; hand-editing those files is a no-op that regen overwrites.

## shared_vs_specific

## Synthesized unit-def candidate (SHARED) vs surface-specific split

### GENUINELY SHARED — belongs in the unit-def (one declaration, projected to both surfaces)
1. **role identity → model tier** — declared as a PORTABLE ROLE NAME only; concrete model resolves through each adapter's models.conf (`model-map.sh`/`role-map.sh`/codex `sync-native-agents.py`). The unit MUST NOT name a tier directly (that reintroduces native frontmatter drift).
2. **worker-type semantics** — owner/stage/review/support bounded-worker stance (already near-zero persona in `roles/worker-types/*.md`).
3. **refute-by-default stance** — one composed fragment replacing the ≥6 restatements (canonical home = MODES.md:10-27 or a new kernel fragment; per-mode copies become a pointer, NOT re-authored prose).
4. **I/O contract (semantic)** — "observed-correct vs not-observed-wrong → PASS/FAIL/BLOCKED/unproven" verdict SEMANTICS, plus named inputs.
5. **read-only / write-scope discipline** — one semantic property (currently encoded 3 incompatible ways).
6. **thin domain fragment (path reference)** — the mode persona body, unified from the roles/modes vs agent-modes double-copy into ONE source.
7. **shared micro-fragments** — 🔴🟡🟢 triage shape, editorial catch-net (already de-duped: polish.md:28-34 ← review.md:14 — the model to generalize), dual direct/pipeline I/O switch, "authorized memory flow" wrapper.

### GENUINELY SURFACE / LIFECYCLE-SPECIFIC — stays per-projection
**NATIVE-subagent only:** Task-tool frontmatter (name/tools/color/memory/metadata.modes); intra-agent "Team Member Selection" router table (native bundles many modes under one subagent; dispatch spawns one worker per node → no in-agent router); native return TOKENS tuned for router harvest (✅/🔴 one-line, design `breakage/vision_passrate`); "Agent Memory" project note; dense hand-tuned blocks with NO manifest representation today (design-team MCP Environment Check table, material-team Automatic Entry Points, research-team Knowledge Sources hierarchy, editorial-team allow/deny surface list, plan-team inline plan schema).

**DISPATCH-registered only (MUST NOT collapse into a shared unit):** the 3-line handoff triple as MACHINE-READABLE terminal proof (worker-bootstrap.md:20-31, consumed by completion_marker_gate); contract-v3 atomic attempt-row claim + jobs.log schema; DEPTH accounting (1|2, parent-required, direct/quick forbidden, namespace-local pid); LIVENESS (SD-15 death-patterns, SD-58 heartbeat, SD-71 async-deny, DETACHED vs FOREGROUND_SCOPED); KILL/orphan reconcile (killpg, SIGTERM→SIGKILL cascade); capacity failover cascade; native-subagent as a DEGRADED fallback hop (registered_worker=0, fleet_visibility=degraded).

**CAPABILITY-level (owns the graph, NOT a unit concern):** topology DAG edges, resume boundaries, completion/human gates, per-node write_scope, fallback_hops, resource-runner detached lifecycle. A unit is projected ONTO a node; it does not own edges.

### Structural asymmetry to close FIRST
Codex + OpenCode native agents ARE ALREADY the target (fully generated from manifest + models.conf, `ownership.generated`). CLAUDE is the outlier: `adapters/claude/agents/*.md` is `ownership.adapter_owned`, hand-authored, guard-exempt, with the richest un-represented persona. The migration's first structural act is bringing Claude to parity: add a Claude `sync-native-agents` generator + a `CFG_PROFILE_*` block in `adapters/claude/config/models.conf` (which today has NONE, unlike codex).

## generation_hook_points

## Where a composition step hooks in (per surface, today's exact call sites)

**NATIVE agents.**
- Codex: `adapters/codex/bin/sync-native-agents.py::render` (L209-253), driven by `manifest["roles"].items()`; resolves `CFG_PROFILE_*→tier→CFG_TIER_*_MODEL` via `load_models_conf` (L22-43). WORKING prototype — replace the ad-hoc `mapper_role` free-text substring matching (L85-110) + hardcoded `ROLE_BOUNDARIES` (L160-194) + inline `EXTRA_AGENTS` (L46-67) with ONE unit-def read.
- OpenCode: `adapters/opencode/bin/sync-native-agents.py::render` (L98-150) — same shape; DEFERS model to runtime `preflight.sh role` (embeds no model).
- Claude: **MISSING HOOK.** `sync-native-metadata.py` generates only SKILL frontmatter (its docstring + `manifest['capabilities']` loop), never AGENT frontmatter. A new Claude `sync-native-agents` generator must be added to the `generate.py` GENERATORS list, emitting a GENERATED `model:` region (agents have none today). Plus a `CFG_PROFILE_*` block must be added to `adapters/claude/config/models.conf`.

**DISPATCH worker.**
- `utilities/worker_bootstrap.py::render_worker_bootstrap` (L95-103) — the single string-composition point (kernel + one overlay), invoked from `dispatch-headless.py::dispatch_prompt` (L298). A unit-projection call replaces the two hard-coded `roles/` paths here. Companion hooks: `resolve_worker_type` (L51-84) and `assigned_contract` (L106-128) already take structured route metadata and would instead read the unit-def; `worker_type_for_kind` (L87-92) maps topology kind→unit (the migration's LAST step). Model already flows through `resolve_model_settings`/`role_map`→`model-map.sh` (dispatch-headless.py:220-255) — UNCHANGED, already SoT-backed.

**Shared-compose constraint.** The composition step must be a single `compose()` consumed at BOTH the build-time `render()` functions AND the runtime `worker_bootstrap` module. Today worker_bootstrap.py reads plain `.md` with NO manifest dependency across 4 file copies — a unit-def parser there changes the dispatch hot-path dependency surface (must NOT pull build-only deps like yaml/capability_topology into the dispatch path).

**Catalog/manifest projection.** `tools/build-manifest.py::build_agents` (L189-210) projects roles+kernel.agents into manifest rows; `generated_document_outputs` (L596-617) rewrites roles/README#role-catalog and capabilities#contract sections. The `external-adversary → Claude codex-review-team` alias is special-cased at build-manifest.py:L577 — the unit-def must model per-surface name aliasing.

**Guard round-trip.** `generate.py` runs 13 generators, forwards `--check`, aggregates exit codes only. Any composition refactor that changes whitespace/ordering REDS every generated-projections test until baselines re-derive.

## sot_guard_template

## Replicating the models.conf SoT+guard for a unit-def SoT

The models.conf pattern (the stated precedent) has 5 transferable parts:
1. **Single declaration file of atomic facts** — concrete ID/effort/variant live in exactly one file.
2. **Semantic indirection layer** — consumers reference tier/role/bucket, never literals.
3. **Generated-projection derivation** + `generate.py --check` byte-for-byte round-trip.
4. **Fail-closed grep guard** (`check-model-config.py`) forbidding the declared literal outside the SoT.
5. **Env-override precedence** (`${VAR:-$CFG_...}`) — SoT is a DEFAULT, not a hard pin.

### Applied to units
- **Unit SoT** (e.g. `roles/units/*` or manifest `capabilities[].requires.units` + a unit table): each unit declares role→tier (BY ROLE NAME, resolving one level down through models.conf), refute stance, I/O contract, worker-type, read-only flag, and a domain-fragment PATH. Because role→tier groupings deliberately differ per adapter (claude conf:34-36: external-adversary LIGHT in Claude, DEEP in codex), the unit SoT should be portable-core + a per-adapter projection layer, NOT one flat file.
- **Generators** project each unit onto BOTH surfaces exactly as codex `sync-native-agents.py` projects `CFG_PROFILE_*` into `agents/*.toml`: (a) native agent md/toml frontmatter+body, (b) the dispatch worker overlay — added to the `generate.py` GENERATORS list.
- **New guard `check-unit-config.py`**, analogous to check-model-config.py, greps `agents/*.md` and `worker-types/*.md` for behavior declarations (persona text, refute stance, model/tier literals, tool grants) NOT derived from the unit SoT, fail-closed.

### Two gaps the guard template MUST fix before it can work
1. **Replace the blanket `/agents/` whole-file exemption** (check-model-config.py:27, VERIFIED) **with a GENERATED-REGION exemption** (like codex tomls). Today the entire Claude native-agent surface is a guard blind spot — this is exactly why the sonnet(primary)/opus(plugin) drift went unnoticed. Agent files must become PROJECTIONS with a GENERATED marker (they have none today, VERIFIED).
2. **Widen `SCAN_DIRS`** (currently `["adapters","core","roles"]`, VERIFIED — excludes `capabilities/`) if unit behavior can leak into capabilities/.

### Second guard still required (both, not one)
Keep the PAIR: `generate.py --check` catches un-regenerated projections; the grep guard catches literals outside any projection. A unit migration needs the analogous pair or drift slips the seam. Preserve the env-override escape hatch, and note the failover cascade still needs concrete model literals INSIDE models.conf (opus is "failover-only, never a primary tier") — the unit SoT references by role and must not flag that.

### Missing cross-validator (net-new, no precedent)
There is NO validator tying `topologies.json node.role` ↔ `harness-manifest requires.roles` ↔ `roles/README portable_role` (capability_topology.py validates node.KIND only, VERIFIED). A units migration rewiring requires.roles→units could leave topology node.role dangling. This validator must be BUILT, keyed on node.role+node.kind.

## top_migration_risks

- GUARD BLIND SPOT (must fix first): check-model-config.py:27 whole-file-exempts /agents/ and Claude agents carry hand-written model: literals with ZERO generated markers (VERIFIED). The native-agent surface is currently UNGUARDED bespoke persona — the live sonnet(primary qa-team.md)/opus(plugin mirror) drift proves the gap is active. The composition guard MUST narrow this to a generated-region exemption or it keeps sanctioning drift.
- DUAL-COPY PERSONA ALREADY DIVERGED: roles/modes/* (English, inline stance+template) vs adapters/claude/agent-modes/* (Korean, delegates to _review_rules.md). A naive merge to one source loses EITHER the Korean localization OR the _review_rules severity/return extraction — they encode different structural decisions, not just translation. Migration must decide which survives before unifying.
- STANCE SINGLE-SOURCE IS FICTION: refute-by-default is asserted single-source in MODES.md but physically lives in ≥6 files, two of which (_review_rules.md:5-7, MODES.md) BOTH claim to be THE source. Composition must not silently drop a restatement a downstream reader depends on, nor lower it (MODES.md:20 forbids lowering); security-review's silence-means-no-finding contract is subtle and easily mis-composed as 'proven safe'.
- MIS-GRADING BY FAMILY: qa spans test(mechanical)→ml-debug(judgment); research spans fact-check→plan-review; design spans verifier(mechanical rubric, 'model does not invent a score')→maker(pure taste). A per-family persona-minimization policy would over-thin maker/plan-review or under-thin verifier. Grade WITHIN families, keyed on node.role+node.kind, never capability group.
- NO node.role CROSS-VALIDATOR EXISTS: capability_topology.py validates node.kind (:118) but NOT node.role (VERIFIED); node.role strings, harness-manifest requires.roles, and roles/README portable_role can drift independently today. Rewiring requires.roles→units could leave topology node.role dangling — a net-new validator is required.
- LIFECYCLE COLLAPSE BREAKS DISPATCH: native subagents never register, heartbeat, claim attempt-rows, depth-account, or get orphan-reconciled. A shared 'lifecycle' or 'output contract' field would over-constrain native or silently drop SD-15/SD-58/SD-71 + the 3-line machine-readable handoff for dispatch. The two projections' KEEP-SEPARATE lifecycles are the CLAUDE.md invariant (native distinct from registered dispatch).
- THICK TOOL FRAGMENTS LOOK LIKE PERSONA BUT ARE IRREDUCIBLE DOMAIN LAW encoding DATED USER FEEDBACK: pdf-extract DPI/two-column, figure-gen spectrogram-integrity + figure-semantic-verify fail-closed (shared by qa/test), security FP-filter, data-script speech tables. Aggressive persona-minimization must RELOCATE, not delete, these; the figure-semantic-verify tool contract must be carried into BOTH the material unit AND the qa/test unit or the 48k-full-band gate silently degrades.
- CAPABILITY CONTRACTS ARE GENERATED: hand-editing capabilities/*.md is a no-op that regen overwrites; migration MUST route through harness-manifest.json + tools/harness_manifest.py + sync-entry-skill-layer.py. topologies.json is runtime-load-bearing for capability-route.py (immutable route compilation, contract v3 atomic claim) — the reason the capability layer is sequenced LAST.
- SPECIAL-CASE AGENTS DON'T FIT THE ROUTER+MODE SHAPE: plan-team (modes:[]), memory-scout (kernel agent, recall-only, injected via EXTRA_AGENTS not manifest roles), and codex-review-team (Claude-only, maps to external-adversary via a hand-coded name alias at build-manifest.py:577) each break a naive 1:1 unit projection.
- RUNTIME vs BUILD-TIME COMPOSE + 4 FILE COPIES: dispatch composes at runtime (worker_bootstrap.py, 4 copies), native at build time. A single unit-def must be parseable by both WITHOUT pulling build-only deps (yaml, capability_topology) into the dispatch hot path; and --check enforces byte-identical output, so any whitespace/ordering change reds all generated-projection tests until baselines re-derive.

## open_design_questions

- CANONICAL STANCE HOME: does the refute-by-default stance live in MODES.md, a new kernel fragment, or worker-bootstrap.md — and do the ≥6 per-mode restatements get deleted or reduced to a one-line pointer? Does any restatement carry per-mode nuance beyond MODES.md (e.g. security-review's confidence-8-10 output contract) that must survive?
- CLAUDE AGENT OWNERSHIP: flip adapters/claude/agents/*.md from ownership.adapter_owned to ownership.generated (parity with codex/opencode), or keep hand-authored with only a unit-def-derived frontmatter region (like sync-native-metadata does for skills today)? This decides whether a Claude sync-native-agents generator + a CFG_PROFILE_* block in claude models.conf are built.
- PERSONA SoT LOCATION: unify onto roles/modes/* (dispatch-flavored — but its headers wrongly say 'the router reads this file'), onto adapters/claude/agent-modes/* (native-flavored, Korean, _review_rules-extracted), or a NEW surface-neutral location? And how are the ~15 direct path references in capabilities/*.md (code-test.md:63,80,96) and skills/*.md (inconsistently citing both stores) updated in lockstep?
- UNIT SoT SHAPE: does capabilities[].requires.roles become requires.units, and do topology nodes gain an explicit `unit` field, or is the unit INFERRED from (node.role, node.kind)? Nodes today carry role+kind but no unit id.
- MODEL TIER OWNERSHIP: does the unit-def own the tier as a ROLE NAME (letting model-map.sh/models.conf remain resolver — avoids native-frontmatter drift), and given claude/codex role→tier groupings deliberately diverge (external-adversary LIGHT vs DEEP), is the unit SoT portable-core + per-adapter projection rather than one flat file?
- DUAL-MODE BRANCH SURVIVAL: for refactor(auto/interactive), dev(direct/pipeline), research plan-review(default/Focus-axis), does each execution SURFACE always use one branch (so the split can drop the other per projection), or must both branches survive in both projections — a risk plan-review.md:30 itself flags for meta-skill callers?
- SUB-CAPABILITY DOUBLE-REPRESENTATION: do code-execute/test/report collapse into units, given they exist BOTH as capabilities/*.md contracts AND as nodes inside autopilot-code standard_plus? Does the sub-capability contract or the node reference become authoritative?
- STAGE TAXONOMY SoT: do STAGE_NODE_CONTRACT + REVIEW_MARKERS (worker_bootstrap.py:16-35) move into the unit-def/capability catalog so the plan/execute/test/report vocabulary has ONE home, or stay in the assembly module (a 3rd encoding beside capabilities and node.kind)?
- SPECIAL-CASE AGENTS AS UNITS: how are memory-scout (kernel agent, EXTRA_AGENTS), plan-team (modes:[], inlined schema), and external-adversary/codex-review-team (cross-runtime, per-surface name alias) modeled — do kernel agents become units or stay a generator-local concept, and how is per-surface name aliasing declared in one unit-def?
- GUARD SCOPE: does check-model-config.py's SCAN_DIRS widen to include capabilities/ if unit behavior can leak there, and does the new check-unit-config guard replace the /agents/ blanket exemption with a generated-region exemption while preserving the env-override escape hatch and the failover-cascade literals inside models.conf?
- OUTPUT-CONTRACT UNIFICATION: do the dispatch 3-line verdict triple and the bespoke native return tokens (✅/🔴 one-line, design breakage/vision_passrate) both project from ONE 'verdict semantics' unit field, or remain fully independent per-surface output contracts since dispatch parses its handoff as machine-readable terminal state consumed by completion_marker_gate?