> **SUPERSEDED (2026-07-22) → `architecture-spec-v3.md`가 실행 정본.**
> 이 v2의 핵심 모델 중 "team = native 집계(1모델)" 축은 사용자 결정(재홈: team 해체,
> unit은 dispatch로, native는 helper 전용)으로 대체되었다. v2의 나머지 검증된 결정
> (unit별 floor·write_scope=node 소유·hot-path 무생성·guard 쌍)은 v3에 승계됨.

# Bootstrap-Unit Architecture — Spec & Migration Plan (v2)

> Blueprint for consolidating bespoke sub-agent personas into composable **units**
> projected onto two distinct-lifecycle surfaces. Investigation basis:
> `_internal/investigation/current-state-map.md` (7-stream parallel audit, file:line grounded).
> **v2**: revised after 2-way cross-harness adversarial verification (Claude-side + Codex);
> both legs independently converged on a core granularity flaw in v1 — now fixed (§1).
> Verification log: `_internal/verification/`.

## 0. The reframe — this is consolidation, not a rewrite

- **Codex + OpenCode native agents are ALREADY the target** — generated from
  `harness-manifest.json` roles + `models.conf` (`ownership.generated`).
- **The dispatch worker is ALREADY reduced** to `kernel + one worker-type overlay`
  (`worker_bootstrap.py`, stdlib-only: `re`+`pathlib`), single-sourced across 3 adapters.
- **Only CLAUDE native agents are the outlier**: hand-authored, `model:` hardcoded,
  **guard-exempt** (`check-model-config.py:26` whole-file `/agents/` exemption), actively
  drifted (primary `qa-team.md=sonnet` vs plugin mirror `=opus`, though `models.conf` declares
  opus *failover-only, never primary*).

## 1. Core model (v2 — granularity fixed)

v1 fatally conflated two different things under "unit". Verification proved
`topologies.json` has 38 nodes collapsing to **11 distinct `(role,kind)` pairs**, and the
highest-floor personas (`ml-debug`, `plan-review`, `maker`, `critic`, `code-review`) **are
not topology nodes at all**. So `(role,kind)` cannot key a 25-mode floor table, and "a unit
projects onto a node" is false for most personas. v2 separates three entities:

| Entity | Granularity | What it is | Count |
|---|---|---|---|
| **UNIT** | fine (mode-persona) | The **behavior SoT** for one mode: role(→tier), stance-ref, io-SEMANTICS, read-only *nature*, domain-body path, tool_contract, shared-fragments, **floor-class**, surface_aliases, native_extras, lifecycle_class, branches | ~31 |
| **TEAM** | native agent | A router **aggregating many units** of a family under ONE model tier (native surface bundles modes; per-unit model differentiation exists ONLY on dispatch) | 9 |
| **NODE** | capability-graph slot | Carries `role`+`kind`+**`write_scope`**(node-owned)+edges; **binds to a unit by mode-aware route resolution** `(capability, capability_mode, node) → unit` — NOT `(role,kind)` | 38 |

```
UNIT (behavior SoT, per mode)  +  per-adapter tier projection
   │ role→tier (name only), stance-ref, io-SEMANTICS, read-only-nature,
   │ domain_body path, tool_contract, shared_fragments, FLOOR-CLASS, aliases, lifecycle_class
   ├─▶ NATIVE: generated into a TEAM agent (aggregate units of a family, ONE model tier)
   └─▶ DISPATCH: the resolved node's worker reads the unit's domain_body .md directly
                 (kernel + worker-type overlay + unit body — all hand/authored .md, stdlib-only)
NODE → UNIT resolution is route-compile-time, mode-carrying (Phase 4).
FLOOR is a property of the UNIT, never of (role,kind).
```

**Invariant preserved:** the two projections keep distinct lifecycles. The unit unifies
*behavior authoring*; it never collapses *surface lifecycle*. `write_scope` stays
node/route-owned; the unit declares only a read-only *nature*. Dispatch's 3-line
machine-readable handoff (consumed by `completion_marker_gate`) is dispatch-only.

## 2. The architecture decisions (v2)

| # | Question | Decision | Δ from v1 / risk closed |
|---|---|---|---|
| 1 | Canonical stance home | Stance = ONE surface-neutral fragment (`roles/units/_shared/stance.md`); `MODES.md` = doctrine that points to it; ≥6 restatements → 1-line pointer. Security-review's confidence bar is an **output-contract field of that unit** (NOTE: the two copies already disagree — `roles/modes/…:27` says 8-10, `agent-modes/…:56` says "7-10 채택 … ≥8"; unification MUST pick the bar, default 8) | + names the 7/8 drift to resolve |
| 2 | Claude agent ownership + **cardinality** | **A native agent = a TEAM = aggregation of a family's units under ONE model tier.** Flip Claude teams to `ownership.generated`; build Claude `sync-native-agents.py` + `CFG_PROFILE_*` in claude `models.conf`. **Per-unit model selection is a DISPATCH-surface property only** (one worker per node); native routers stay single-model. Hybrid first (generated frontmatter region), full-generate later | **FIX (both legs): defines unit→team aggregation + per-mode model contract** |
| 3 | Persona SoT location | NEW surface-neutral `roles/units/<family>/<unit>/`. To let capability/skill path refs defer to Phase 4, **land a `roles/modes/<f>/<m>.md` → `roles/units/…` compat-symlink** the moment a family moves | + compat-symlink so refs don't break in Phases 1-3 |
| 4 | Node↔unit binding + validator | `requires.roles`→**`requires.units`**. **Node binds to a unit by route resolution `(capability, capability_mode, node)→unit`**, NOT a static `(role,kind)` inference (non-unique: 11 pairs / 38 nodes) and NOT a bare `node.unit` (mode-varying: one node serves modes=[audit,debug,dev]). Cross-validator checks: unit∈`requires.units` **AND** `node.kind` compatible with unit.`worker_type` **AND** role consistency | **FIX (both legs): mode-carrying resolution; validator completeness** |
| 5 | Model tier ownership | Unit owns tier **by role NAME only**; concrete model via per-adapter `models.conf`. Unit SoT = portable-core + per-adapter tier projection (claude external-adversary LIGHT vs codex DEEP) | unchanged (verified clean) |
| 6 | Dual-mode branch survival | Do NOT drop branches structurally; per-unit `branches_both_surfaces` (default surface-picks-one); prune later with usage evidence | verified clean |
| 7 | Sub-capability + write_scope | Capability = stage *contract*; unit = *worker behavior*; node = *wiring* + **owns write_scope**. Unit declares read-only *nature* only, never a concrete write_scope (that would merge lifecycle policy) | **FIX (Codex): write_scope is node-owned, not unit-owned** |
| 8 | Stage taxonomy SoT | Move `STAGE_NODE_CONTRACT`/`REVIEW_MARKERS` into the manifest **only if** the dispatch hot path can read a generated constant WITHOUT new deps/staleness risk; else leave as inline Python constants. **Phase 4, conditional** | + honest: today they're zero-cost inline constants; moving adds hot-path load |
| 9 | Special-case agents | memory-scout=`lifecycle_class: kernel`; plan-team=single-unit family; external-adversary=`surface_aliases{claude: codex-review-team}` (replaces build-manifest.py:577) | verified clean |
| 10 | Guard scope | Replace `/agents/` blanket exemption with generated-region exemption (machinery `GEN_OPEN/GEN_CLOSE` already exists, `check-model-config.py:67`). New `check-unit-config.py`; scan `capabilities/` | verified feasible |
| 11 | Output contract | Semantically unified (unit `io_contract` = verdict SEMANTICS), syntactically per-surface (dispatch 3-line triple stays EXACT; native tokens separate) | verified clean |

## 3. Domain-graded minimization — floor is a UNIT property

**The floor is graded per UNIT (mode-persona), NOT per family and NOT per `(role,kind)`**
(v1's mis-key, flagged by both legs). Full gradient in the investigation. Anchors:

| Pole | Units | Floor |
|---|---|---|
| A (mechanical) | material/{pdf-extract,browser-fetch,web-image-search,data-script,figure-gen}, qa/test, design/verifier, research/fact-check | near-ZERO persona; keep THICK **tool** fragments |
| Mid | dev/{backend,frontend,new-lib,refactor}, editorial/{review,polish,translate}, qa/{data-curate,code-review,plan-review,security-review} | LOW→MODERATE |
| B (judgment) | qa/ml-debug, research/{research-survey,claim-verify,plan-review}, design/{critic,maker} | HIGH→HIGHEST — irreducible domain core |

**Rule:** thick fragments that *look* like persona but encode domain law / dated user
feedback (pdf DPI, `figure-semantic-verify` [verified in BOTH `material/figure-gen.md:42`
AND `qa/test.md:18`], security FP-filter, spectrogram-integrity) → **RELOCATE to
`tool_contract`**, never minimize away.

## 4. Guards (pair + validator)

1. `generate.py --check` (byte round-trip) — extend to unit projections; **note: any new
   generated artifact on the dispatch hot path enlarges the `--check` baseline AND adds a
   stale-artifact→wrong-persona failure mode** (see §5 hot-path decision).
2. `check-model-config.py` — narrow `/agents/` whole-file exemption → generated-region.
3. NEW `check-unit-config.py` — fail-closed grep for behavior (persona/stance/model
   literal/tool grant) in `agents/*`/`worker-types/*` not derived from the unit SoT; scans
   `capabilities/`; keeps env-override + failover-literal exemptions.
4. NEW cross-validator (into `capability_topology.py`, which today validates `node.kind`
   only): unit∈`requires.units` ∧ `node.kind`↔unit.`worker_type` ∧ role consistency.

## 5. Migration plan — v2 (resequenced)

Each phase: **git-revertable** (hand file moves/ref edits are NOT regen-reversible — only
generated projections are; rollback of a relocation = atomic git revert of move+refs+regen),
**drilled**, guard-green before proceeding, committed separately.

### Phase 0 — Un-blind the guard + Claude parity (drift-resolving, NOT byte-neutral)
- Add GENERATED markers to Claude team agents; build Claude `sync-native-agents.py`;
  `CFG_PROFILE_*` block in claude `models.conf`; narrow the `/agents/` exemption.
- **Honest:** this is NOT byte-identical to today — single-sourcing **resolves** the
  sonnet/opus drift (→ sonnet, the non-failover tier). "Byte-identical" means regen
  idempotence, not parity with the drifted files.
- Drill: regen idempotent; `check-model-config` green; plugin mirror no longer pins opus.

### Phase 1 — Mechanical-UNIT pilot (NOT the whole qa family)
- Pilot = the near-ZERO-floor **units** (qa/test + material/*), NOT qa-as-family (qa is
  bimodal — ml-debug/security-review defer to Phase 3).
- Author the `unit-def` schema + `_shared/stance.md` + shared micro-fragments; migrate the
  pilot units to `roles/units/` **with compat-symlinks** so capability/skill path refs
  (e.g. `code-test.md:63,80,96`) keep resolving until Phase 4.
- **Compose model (hot-path safe):** dispatch reads the unit's domain-body `.md` DIRECTLY
  (kernel + worker-type overlay + unit body — all authored `.md`, stdlib-only, no generated
  overlay on the hot path). Native GENERATES its team agent from unit metadata at build.
  `compose()` is shared *logic in the build generator only*; the runtime path stays a plain
  `.md` read. (This is the ONLY way to keep worker_bootstrap dep-free — v1's "shared
  compose()" framing was wrong.)
- New `check-unit-config.py` scoped to the pilot.
- Drill: pilot units identical intent on both surfaces; **security silence≠proven-safe and
  the (resolved) confidence bar preserved.**

### Phase 2 — Remaining mechanical units (material done, dev-stage, editorial)
- RELOCATE thick tool fragments into `tool_contract` (figure-semantic-verify into material
  AND qa/test). Editorial shared voice+catch-net collapsed once.

### Phase 3 — Judgment units (qa/ml-debug, research, design) — keep THICK cores
- Preserve irreducible bodies: plan-review lens matrix + multi-axis dispatch, `_design_rules`
  taste law, maker generative judgment, ml-debug diagnosis, security FP-filter.

### Phase 4 — Capability wiring (LAST, riskiest)
- `requires.roles→requires.units`; build the **mode-aware node→unit resolver** and the
  cross-validator; retire compat-symlinks by moving capability/skill refs; conditionally move
  stage taxonomy; external-adversary `surface_aliases`. `topologies.json` is runtime-load-
  bearing (`capability-route.py`, contract-v3 atomic claim) → heaviest drill.

## 6. Risk register (v2 — granularity added as #1)

| Risk | Mitigation | Phase |
|---|---|---|
| **GRANULARITY: unit=mode-persona vs node-worker conflation** (both legs, SEVERE) | v2 §1 three-entity model; floor per-unit; node→unit by mode-aware resolution | design (§1) |
| Persona-relocation forces capability-ref edits in Phases 1-3 (runtime-load-bearing paths) | compat-symlinks; retire refs in Phase 4 | 1-4 |
| Hot-path: generated overlay on dispatch path = stale→wrong-persona | dispatch reads authored `.md` directly; NO generated overlay on hot path | 1 |
| Guard blind spot (/agents/ exempt, active drift) | generated-region exemption + Claude generator | 0 |
| Phase 0 not byte-neutral (resolves sonnet/opus) | reframed as drift-resolving; decide sonnet | 0 |
| Dual-copy persona diverged + stance fiction (≥6 files) + security 7/8 drift | surface-neutral body; one stance fragment; name+resolve the 7/8 bar | 1 |
| Mis-grading | floor per UNIT, keyed on the mode-persona not (role,kind) | all |
| Cross-validator incompleteness | validate requires.units membership + kind↔worker_type + role | 4 |
| Lifecycle collapse / write_scope | write_scope node-owned; unit = read-only nature only; dispatch handoff untouched | invariant |
| Thick tool fragments = domain law | RELOCATE to tool_contract | 2 |
| Reversibility of hand moves | git-revert-based (not regen); atomic phase commits | all |

## 7. Open items for the user
- **CORE MODEL v2 (§1) confirm** — the three-entity split (unit/team/node) is the load-bearing
  revision; worth a sanity read before Phase 0.
- **Phase 0 now?** Self-contained, high-value, drift-resolving (not behavior-neutral — it fixes
  the illegal opus pin). Recommend first regardless of the rest.
- **Persona SoT home** `roles/units/` + compat-symlinks — confirm.
- **Security confidence bar** — resolve the existing 7 vs 8 drift (default 8).
- **Appetite** — multi-phase, drilled, weeks; per-gate user review.

> Because the v2 core model changed materially, the **Phase 0 implementation gate should
> re-run a lightweight 2-way check on the revised §1 model** before code lands.
