## 📋 Plan Review Results

**Target:** `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/plan/plan.md` and `checklist.md`

**Plan summary:** The round-2 plan is safe and complete for execution. It translates v16 F-36–F-39 into a single projection/association authority, preserves opaque sealed DAGs, specifies all-layout context/NOW behavior, wires OpenCode refresh end to end, and provides concrete hermetic verification plus mirror gates.

**Verdict:** ✅ No issues

## 🔴 Must-fix before execution

None. The five round-1 major blockers were rechecked against the revised plan, checklist, canonical PRD, research handoff, and current source; each is now explicitly closed.

### Round-1 correction verification

- **Owner/conductor route discovery — plan step 1.3.5, checklist Gate A items 30–31 and Gate G item 121:** the resolver now uses `Session.session_id -> DispatchJob.parent_sid` and depth-1 `DispatchJob.slug -> child.parent_slug`, considers only current `route-exact` children, adopts one agreeing route/hash, preserves all same-route record-ordered siblings, and emits `multiple-owner-routes`/`owner-route-conflict`. This matches the current render-time joins in `tools/fleet/render.py:2875–2910` and the parent fields populated in `tools/fleet/collectors/dispatch.py:1025–1026,1083–1085,1165–1167`.
- **Deterministic route-exact stage labels — plan steps 1.3.4 and 3.2.2, checklist Gate A item 32 and Gate G item 122:** the selected exact nonempty `assigned_contract` is used only for the matching validated route/node/attempt evidence; otherwise the sealed opaque `route_node` is used. The plan forbids unit/role/capability/key and fixed-pipeline inference, and tests `research` versus opaque `claim-a` across group, process, plain, and JSON. This is faithful to PRD SD-F1 and F-36c.
- **Artifact root/cardinality and QA-only lookup — plan steps 1.3.7 and 2.2.2–2.2.3, checklist Gate A item 36, Gate B item 44, and Gate G item 128:** the resolver receives `artifact_root`, enumerates exact suffix matches across registry and cwd-local roots with realpath deduplication, fails closed on cardinality >1, and never uses mtime/token-overlap selection. QA is a separately named resolver after argv/jobs.log precedence and returns QA only. This corrects the current `_find_plan_dir()`/`_plan_qa()` behavior at `tools/fleet/collectors/dispatch.py:675–789` without coupling stage semantics into QA.
- **OpenCode refresh plumbing — plan steps 2.5 and 4.3, checklist Gate B items 54–56 and Gate F items 108–112:** the typed private source flows collector → scheduler → source-specific argv/CLI → exact-session SQLite delta reader → typed sidecar cursor. The plan fixes table precedence, integer rowid ordering, `mode=ro`, malformed/tool/internal filtering, cursor reset/advance behavior, mutually exclusive source arguments, and DB/WAL/SHM immutability tests. This addresses the current OpenCode enrichment/scheduler boundary at `tools/fleet/collectors/opencode.py:136–205` and `tools/fleet/refresh_title.py:507–516,619–645`.
- **Process-view subordinate ownership and identity — plan step 3.3.6, checklist Gate C item 68, Gate D items 82–86, and Gate G item 129:** process rendering receives attached projections and an exact `(pid, proc_start)` map, emits one detail row beneath each live active/degrade job before its exact-session strip, gives route headers none, and suppresses stale/dead rows. This replaces the current PID-only process map and current `_route_card()`/`_degrade_card()` call path (`tools/fleet/render.py:2324–2346`) with the required identity boundary.

## 🟡 Useful improvements

- **plan step 5.2:** the sealed `synth_composed_survey.json` fixture is required to be generated and checked in, but the plan does not name the exact fixture-generation/route-verification command. Add that command to the implementation handoff so a malformed hash or schema cannot first surface in the full Fleet suite.
- **plan step 1.1:** the public `active_nodes` element shape and `progress` object shape are named by the PRD but not restated as explicit type/serialization contracts. The implementation can proceed safely, but documenting those two shapes beside the dataclasses would make the additive JSON compatibility gate easier to audit.

## 🟢 Well-constructed portions

- The dependency order and exclusive ownership are coherent: model/route/projection → evidence/association → surfaces → scheduler → tests → canonical-to-Claude mirror. Phase 6 is correctly gated on canonical tests.
- The plan faithfully distinguishes the canonical PRD v16 from the immutable pre-correction snapshot and keeps development pending; it does not treat the 179 baseline checks as implementation evidence.
- Evidence precedence is fail-closed: explicit route tuple members block artifact fallback; registry-only evidence cannot fabricate topology/progress/gate/completion; exact artifact inference is stage-only and cardinality constrained.
- DAG construction is opaque and lossless: `depends_on` is the ordering primitive, record-order topological levels and fan-in/fork siblings are preserved, `write_scope`/unit/gate metadata are covered, and `_PIPE_STAGES` is prohibited for validated or explicit-invalid routes.
- F-37/F-38 coverage is concrete: all four required widths, CJK-safe clipping, the context/NOW truth table, stale/dead suppression, parent/child non-inheritance, sequence/freshness handling, compaction decreases, and byte-equivalent non-context fields are named.
- F-39 coverage includes the exact 3/4 concurrency and 4/60 rolling-start limits, 600/150 debounces, shared leases/kill switches, direct-worker guard coverage, OpenCode ordinary-child eligibility, source-specific cursor tests, and fail-if-reached provider/spawn guards.
- The checklist carries every v16 acceptance row into named test work, explicitly migrates superseded `live_stage`/artifact/heuristic/PID-only tests, preserves old-key JSON consumers, and records the required assurance string `plan-check:selected-independent-pass:final-verify`.

## Review evidence and checks

- Read completely: the round-2 plan, checklist, round-1 review, canonical v16 PRD snapshot, current canonical Fleet PRD, assigned Fleet research handoff, v16 pipeline state, and owner finalization/specification verdict artifacts.
- Rechecked current code read-only: `tools/fleet/model.py` (Session/DispatchJob identity and parent fields), `collectors/procscan.py`, `collectors/__init__.py`, `collectors/dispatch.py`, `collectors/opencode.py`, `route.py`, `render.py`, `fleet.py`, `refresh_title.py`, `titles.py`, token-budget helpers, and affected Fleet tests/fixtures.
- Confirmed `DispatchJob.proc_start` already exists at `tools/fleet/model.py:210–213`; the process-view exact identity requirement is therefore implementable without inventing an unavailable source field.
- Confirmed the current renderer still has the superseded independent route resolution, first-child selection, PID-only process mapping, inline context gauges, and wide-only summary placement described by the plan; the plan assigns each replacement to the correct phase and owner.
- Confirmed canonical PRD v16 §4.12 lines 356–400 covers the same projection, route/artifact authority, arbitrary DAG, all-layout detail row, context orthogonality, quota, no-live-provider, and mirror requirements. The current canonical PRD’s OpenCode clause also makes ordinary registered OpenCode children eligible; the immutable pre-correction snapshot’s contrary historical clause is not active input.
- `adapters/codex/bin/preflight.sh qa-policy standard code` passed with assurance `plan-check:selected-independent-pass:final-verify`.
- `python3 /home/Uihyeop/agent_setting/utilities/worker-route-guard.py validate ...` passed for route `rt-dfec3aabe921b37f`, node `plan-check`, canonical artifact root, assigned capability/intensity/unit, and the narrow review write scope.
- No source, plan, checklist, commit, push, integration, cleanup, monitor, or live-provider action was performed by this worker. The worktree remained clean at `340359eb5a12e175dc2b1f28212763df5f96b791`.
- Known unsupported runtime detail remains correctly recorded for later reporting: the owner-side `.spec-grounding` PRD-read marker is read-only/unavailable; the plan does not overclaim it.

The two 🟡 items are execution-handoff reinforcements only; they do not reduce the PASS verdict or block the plan-check completion gate.
