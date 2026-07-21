# Bootstrap-Unit Architecture — Spec v3 (EXECUTION)

> v3 = v2's verified substrate + the skill-setting review + both cross-harness verdicts,
> under the user's locked decisions. This is the coordination document for the
> maximum-scale parallel implementation. v2 remains at `architecture-spec.md`;
> investigation at `_internal/investigation/`; skill review at `_internal/skill-review/`.

## 0. Locked decisions (user, 2026-07-21)

1. **승격 (PROMOTE):** `capabilities/topologies.json` becomes the single compositional
   router. `rollout.route_compiler` migrates report-only → **enforced** as a planned
   migration (not a flag flip — rollout semantics are internally contradictory today:
   the pin is test-locked at `capability_topology.py:198-202` while
   `legacy_low_level_dispatch:true` has **no consumer**; both get reconciled).
2. **재홈 (RE-HOME):** the 9 runtime team agents (Claude `adapters/claude/agents/*-team.md`
   AND Codex `adapters/codex/agents/*-team.toml` AND OpenCode team agents — team
   reification is cross-harness, per the Codex verdict) are **deleted**; their behavior
   atoms re-home into a **portable unit catalog**. `fam`/`family` survives as a pure label.
3. **Scale:** maximum parallel division of labor, thorough. Commit partitioning per
   workstream preserves revertability; guards must be green before each commit.

## 1. Target model (final)

```
ENTRY (skill; routing lives here and ONLY here)
  request → case selection (WORKFLOW §0.2 stays core doctrine; entry skill is executor)
          → recipe = COMPOSE(units) from the catalog   ← curated fast paths
          → no recipe matches? COMPOSE-ON-DEMAND       ← the long-tail fallback
          → compile → validate → hash-seal → §0.4 card → DISPATCH
DISPATCH (harness-neutral, registered, tracked)
  depth-1 owner = thin conductor; every unit runs as a depth-2 sibling node.
  A depth-2 worker NEVER routes and NEVER invokes a team. In-stage review needs
  hoist to sibling nodes at the owner level (this replaces today's in-session
  team calls and keeps the depth-3 ban intact).
UNIT CATALOG (roles/units/ — the new SoT; THE core deliverable)
  unit = one dispatchable behavior atom (former team-mode). English canonical,
  portable. Frontmatter = machine contract; body = domain persona at its floor.
NATIVE (per-harness helper primitive)
  ephemeral, depth-free, unforeseen narrow sub-tasks only. Never a unit, never a
  team. memory-scout stays (kernel helper). Everything else in agents/ goes.
TEAM → label only (`family:` field). No runtime team agents on any harness.
```

**Long-tail fallback = composition itself.** Enumerated recipes are curated fast paths;
an un-enumerable request gets a compose-on-demand node graph from the same catalog,
passing the SAME validator + hash-seal + §0.4 human gate, recorded `composed: true`.
No spec/artifact-order gate (§0.1) is bypassed — composition changes route *shape*,
never gate *applicability*.

**Depth derivation:** owner(1) → unit nodes(2). Abolishing in-stage team invocation
removes the only pressure toward depth-3. Native helpers stay depth-free.

**Hash-seal preservation (load-bearing):** compose → expand to full node array →
`validate` (DAG, write-scope isolation, depth==2 max, unit refs) → seal `route_hash`
over the expanded blob exactly as today (`capability-route.py:304→:342→:352`). The
depth-2 no-routing guarantee survives because sealing still happens pre-spawn.

## 2. What survives from v2 (verified substrate — unchanged)

- Guard blind-spot fix: `/agents/` whole-file exemption → generated-region exemption
  (`check-model-config.py:27`); the agents dir shrinks to kernel helpers.
- Floor is a **unit** property (never (role,kind), never family): near-zero → highest,
  per the investigation gradient. Thick tool fragments (pdf DPI, figure-semantic-verify,
  spectrogram LAW, security FP-filter) are domain LAW → relocate into `tools:` refs,
  never minimize. figure-semantic-verify lands in BOTH material/figure-gen AND qa/test.
- Stance = ONE shared fragment (`roles/units/_shared/stance.md`); MODES.md stays doctrine
  pointing to it; ≥6 restatements become pointers. Security confidence bar resolved: **8**
  (the 7-vs-8 drift picks 8; silence = "no HIGH/MEDIUM found", never "proven safe").
- Role→tier by NAME only; models.conf stays the model resolver; per-adapter divergence
  (external-adversary LIGHT/claude vs DEEP/codex) lives in adapter config.
- write_scope stays **node-owned**; a unit declares only a read-only *nature*.
- Dispatch hot path stays stdlib-only: workers read the unit BODY as a plain .md
  (kernel + worker-type overlay + unit body). compose() logic is build/route-time only.
- Branches (direct/pipeline, auto/interactive) survive structurally; prune later with
  usage evidence.
- external-adversary: the Claude codex-review-team wrapper agent dies with the teams;
  cross-harness hostile review = dispatching the review unit to the codex harness via
  the existing transport (stage-dispatch-fallback). The build-manifest.py:577 alias retires.

## 3. Corrections carried from the cross-harness verdicts (honesty anchors)

- The **unit catalog is the actual hard work** — ~30/38 nodes have no matching
  sub-contract today; "80% scaffolded" was true of routing only.
- Team reification is **cross-harness** (Claude .md + Codex .toml + OpenCode), so
  re-homing touches all three adapters' generators.
- Call-site count: **~16-18 exact `subagent_type` literals** + pervasive team prose;
  the inventory workstream produces the exact list (no more guessed counts).
- 22 mode keys already collapse into 11 recipes — the explosion is real but milder;
  composition still wins (30/38 recipe-local gates → catalog refs).
- Entry coverage: exact-coverage applies to `group==entry` only; `analyze-project`,
  `analyze-user`, `audit` are entry-router class WITHOUT recipes — workstream B
  resolves (recipes or documented class exclusion), no silent gap.

## 4. Unit-def (authoring contract — full schema in `roles/units/_schema.md`)

Frontmatter (machine, parsed at build/route-time only):
`unit, family(label), role(portable name), worker_type(owner|stage|review|support),
floor(near-zero|low|moderate|high|highest), read_only(nature), stance(ref|none),
io{verdict semantics, return ref}, tools[](law/tool refs), branches[], aliases{}`.
Body = the irreducible domain persona at the declared floor. English canonical
(localization = projection concern). Sources to merge per unit: `roles/modes/<f>/<m>.md`
(EN, dispatch-flavored) + `adapters/claude/agent-modes/<f>/<m>.md` (KO, native-flavored,
_review_rules-extracted) + load-bearing blocks mined from the team agent files
(Knowledge Sources, MCP env checks, Automatic Entry Points, plan schema, …) — nothing
load-bearing may drop silently; unplaceable content goes to a NOTES file for review.

## 5. Workstreams (max-parallel) & commit partitioning

| WS | What | Writes | Commit |
|---|---|---|---|
| **A. Unit catalog** (7 parallel: qa, research, dev, design, material, editorial, plan) | author `roles/units/<family>/*` from the three sources; mine team files; shared fragments referenced not restated | `roles/units/<family>/` only (NEW files — zero behavior change; old paths untouched) | C1: spec+schema+fragments+catalog |
| **B. Topologies/compiler design→apply** | unit refs on 38 nodes; 30 local gates → catalog; rollout reconciliation (pin+test+legacy flag retire); entry-coverage fix; compose-on-demand mechanics; validator extensions (unit∈catalog ∧ kind↔worker_type ∧ role); in-stage team calls → sibling review nodes (concrete recipe deltas) | design draft to `_internal/design/`; apply after review | C2: topologies+validators+compiler |
| **C. Call-site inventory→rewiring** | exhaustive team-reference inventory (subagent_type literals + prose + generators + plugin mirrors, generated-vs-hand tagged) → exact per-file action list; then rewiring + team deletion + generator updates (build_agents, sync-native-agents ×3 → kernel-only) + manifest `requires.roles→requires.units` | inventory to `_internal/design/`; apply after review | C3: rewiring+deletion+generators+regen |
| **D. Guards & docs** | `check-unit-config.py` (fail-closed), exemption narrowing, `harness_manifest` schema, core docs (CONVENTIONS/WORKFLOW/OPERATIONS/MODES — main-session owned) | tools/, hooks/, core/ | C4: guards+docs |
| **V. Verification** | full regen + test suites (portable-guards in a clean worktree per standing rule) + 2-way cross-harness adversarial verify on the implemented state | — | fixes fold into C1–C4 |

Sequencing: A ∥ B-design ∥ C-inventory (round 1, disjoint paths) → review → B-apply,
C-apply (round 2) → D → V. Old files (`roles/modes/*`, agent-modes, team agents) are
deleted only in C3/C4 after all readers are rewired — compat window in between.

## 6. Definition of done

- All units authored; every node references a catalog unit; compiler enforced;
  validator green; guards green; full regen byte-stable; tests pass (worktree rule);
  no dangling team reference anywhere (grep-proof); depth ceiling and hash-seal
  provably intact; 2-way adversarial verify SHIP; committed per-partition and pushed.
