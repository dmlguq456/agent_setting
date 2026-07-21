# Call-Site Inventory — team-agent references to rewire/delete (v3 re-homing)

> Workstream C round 1 deliverable. Spec: `architecture-spec-v3.md` §5 WS-C.
> Scope: `grep -rn` over adapters/ skills/ capabilities/ core/ roles/ hooks/ tools/ utilities/
> for `subagent_type`, the 9 script team names, and the 8 Korean display names
> (테스트팀 included — it appears at call sites although no such team agent exists).
> Hits are per matched line; one line may match several terms (deduped by line).

## Summary

| Action | Files | Hit lines |
|---|---:|---:|
| A. [rewire→dispatch unit as sibling node] (incl. prose rewrites to unit semantics) | 74 | 273 |
| B. [delete with team agent] | 39 | 160 |
| C. [generator change: emit kernel-only] | 17 | 69 |
| D. [regen-covered, no hand edit] | 133 | 477 |
| E. [keep: memory-scout kernel helper / unchanged mechanism] | 4 | 7 |
| F. AMBIGUOUS — flagged for explicit decision | 16 | 65 |
| **Total** | **283** | **1051** |

**[rewire→ephemeral native helper] is EMPTY by design:** every surveyed call site invokes an
*enumerated* behavior (an `Agent(subagent_type=…, mode=…)` with a named mode, or prose naming a
team mode) — all of these are unit-shaped and rewire to catalog units. No existing call site
qualifies as an "unforeseen narrow sub-task"; the ephemeral-native lane starts unused, which is
consistent with v3's "native = ephemeral helper only, never a unit, never a team".

### Structural facts the rewiring depends on

- **Skill-copy triplication:** repo-root `skills/` is the canonical tree (`tools/sync-entry-skill-layer.py` projects `skills/<entry>` → `adapters/claude/skills/<entry>`; trees are byte-identical today, `diff -rq` clean), and `adapters/claude/bin/sync-native-plugin.py` copies `adapters/claude/skills` + `adapters/claude/agents` → `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/`. **One hand edit in `skills/`, two projections.** NOTE: `~/.claude/CLAUDE.md` calls `skills/` the "compatibility mirror" — the sync tool's direction says otherwise for entry skills; flagged in §F.
- **Claude team agents are HAND-authored SoT** (`adapters/claude/agents/*-team.md`, no GENERATED marker; there is **no** `adapters/claude/bin/sync-native-agents.py` — the spec's "sync-native-agents ×3" is ×2: codex + opencode). Deleting them = plain `git rm` + plugin regen.
- **Codex/OpenCode team agents are GENERATED** from `harness-manifest.json` by `adapters/{codex,opencode}/bin/sync-native-agents.py` ("adapter-owned output generated from harness-manifest.json" header). Never hand-delete: make `tools/build-manifest.py` `build_agents()` (:189) emit kernel-only, fix both sync scripts' team-specific overrides, regen.
- **`tools/build-manifest.py:577`**: `claude_name = "codex-review-team" if profile == "external-adversary" else profile` — the alias the spec retires (§2 last bullet).
- `tools/fleet/` and `adapters/claude/tools/fleet/` are a duplicated pair — edits (if any) land in both.

## A. [rewire→dispatch unit as sibling node] (incl. prose rewrites to unit semantics)

### `adapters/claude/ADAPTATION.md`
- provenance: HAND (doc)
- action detail: Doctrine/registry prose: team tables and mentions become unit-catalog/family-label prose (WS-D owns core docs).
- rewire target unit family(ies): (cross-harness review unit → codex transport), design/*, dev/*, editorial/*, material/*, plan/*, qa/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (9 lines): 218, 231, 232, 233, 234, 235, 236, 237, 238
  - `codex-review-team` @ 218, 238
  - `design-team` @ 236
  - `dev-team` @ 235
  - `editorial-team` @ 237
  - `material-team` @ 234
  - `plan-team` @ 231
  - `qa-team` @ 232
  - `research-team` @ 233

### `adapters/claude/README.md`
- provenance: HAND (doc)
- action detail: Doctrine/registry prose: team tables and mentions become unit-catalog/family-label prose (WS-D owns core docs).
- rewire target unit family(ies): (cross-harness review unit → codex transport), qa/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (2 lines): 87, 92
  - `codex-review-team` @ 87
  - `codex-review-team,품질관리팀` @ 92

### `adapters/codex/ADAPTATION.md`
- provenance: HAND (doc)
- action detail: Doctrine/registry prose: team tables and mentions become unit-catalog/family-label prose (WS-D owns core docs).
- rewire target unit family(ies): editorial/*, plan/*, qa/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (5 lines): 212, 229, 234, 238, 239
  - `editorial-team,plan-team` @ 229, 234
  - `memory-scout` @ 212
  - `qa-team` @ 238, 239

### `adapters/codex/README.md`
- provenance: HAND (doc)
- action detail: Doctrine/registry prose: team tables and mentions become unit-catalog/family-label prose (WS-D owns core docs).
- rewire target unit family(ies): dev/*, editorial/*, plan/*, qa/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (3 lines): 210, 351, 352
  - `dev-team,plan-team,qa-team` @ 351
  - `editorial-team` @ 352
  - `memory-scout` @ 210

### `adapters/codex/bin/capability-map.sh`
- provenance: HAND
- action detail: role_contract strings (planning=plan-team,…) → unit ids from the catalog.
- rewire target unit family(ies): dev/*, editorial/*, plan/*, qa/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (2 lines): 74, 84
  - `dev-team,editorial-team,plan-team,qa-team` @ 74
  - `qa-team` @ 84

### `adapters/codex/bin/preflight.sh`
- provenance: HAND
- action detail: Preflight asserts native team agent files exist — assert kernel-only (memory-scout) instead; qa-team existence checks are deleted.
- hits (1 lines): 738
  - `memory-scout` @ 738

### `adapters/codex/bin/role-map.sh`
- provenance: HAND
- action detail: Portable-role→team-profile mapping becomes role→unit/family-label mapping; external-adversary alias rows retire.
- rewire target unit family(ies): design/*, dev/*, editorial/*, material/*, plan/*, qa/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (7 lines): 38, 44, 50, 56, 62, 67, 72
  - `design-team` @ 72
  - `dev-team` @ 44
  - `editorial-team` @ 56
  - `material-team` @ 67
  - `plan-team` @ 38
  - `qa-team` @ 50
  - `research-team` @ 62

### `adapters/opencode/ADAPTATION.md`
- provenance: HAND (doc)
- action detail: Doctrine/registry prose: team tables and mentions become unit-catalog/family-label prose (WS-D owns core docs).
- hits (1 lines): 60
  - `memory-scout` @ 60

### `adapters/opencode/bin/capability-map.sh`
- provenance: HAND
- action detail: role_contract strings (planning=plan-team,…) → unit ids from the catalog.
- rewire target unit family(ies): dev/*, editorial/*, plan/*, qa/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (1 lines): 59
  - `dev-team,editorial-team,plan-team,qa-team` @ 59

### `adapters/opencode/bin/preflight.sh`
- provenance: HAND
- action detail: Preflight asserts native team agent files exist — assert kernel-only (memory-scout) instead; qa-team existence checks are deleted.
- rewire target unit family(ies): qa/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (3 lines): 185, 186, 188
  - `qa-team` @ 185, 186, 188

### `core/CONVENTIONS.md`
- provenance: HAND (doc)
- action detail: Doctrine/registry prose: team tables and mentions become unit-catalog/family-label prose (WS-D owns core docs).
- rewire target unit family(ies): design/*, dev/*, editorial/*, material/*, plan/*, qa/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (7 lines): 115, 116, 117, 118, 119, 120, 121
  - `design-team` @ 120
  - `dev-team` @ 119
  - `editorial-team` @ 121
  - `material-team` @ 118
  - `plan-team` @ 115
  - `qa-team` @ 116
  - `research-team` @ 117

### `roles/README.md`
- provenance: HAND (doc)
- action detail: Doctrine/registry prose: team tables and mentions become unit-catalog/family-label prose (WS-D owns core docs).
- rewire target unit family(ies): (cross-harness review unit → codex transport), design/*, dev/*, editorial/*, material/*, plan/*, qa/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (8 lines): 16, 17, 18, 19, 20, 21, 22, 23
  - `codex-review-team` @ 19
  - `design-team` @ 16
  - `dev-team` @ 17
  - `editorial-team` @ 18
  - `material-team` @ 20
  - `plan-team` @ 21
  - `qa-team` @ 22
  - `research-team` @ 23

### `skills/analyze-project/references/mode-code.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): dev/*, plan/*, qa/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (3 lines): 72, 84, 192
  - `dev-team` @ 84
  - `plan-team` @ 72
  - `qa-team` @ 192

### `skills/analyze-project/references/mode-doc.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (2 lines): 23, 27
  - `research-team` @ 23, 27

### `skills/analyze-project/references/mode-paper.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (5 lines): 7, 28, 39, 54, 78
  - `research-team` @ 7, 28, 39, 54, 78

### `skills/analyze-project/references/owner-execution.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): qa/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (5 lines): 81, 83, 84, 85, 92
  - `qa-team` @ 83
  - `research-team` @ 81, 84, 85, 92

### `skills/analyze-user/references/integration-and-usage.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): design/*, dev/*, editorial/*, material/*, plan/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (6 lines): 7, 8, 9, 10, 11, 12
  - `design-team` @ 8
  - `dev-team` @ 12
  - `editorial-team` @ 10
  - `material-team` @ 7
  - `plan-team` @ 11
  - `research-team` @ 9

### `skills/analyze-user/references/owner-execution.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (1 lines): 65
  - `research-team` @ 65

### `skills/analyze-user/references/pipeline-phases.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (2 lines): 52, 57
  - `research-team` @ 52
  - `연구팀` @ 57

### `skills/audit/references/owner-execution.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): editorial/*, qa/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (3 lines): 77, 84, 101
  - `editorial-team` @ 77, 101
  - `qa-team,research-team` @ 84

### `skills/audit/references/report-and-autofix.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): editorial/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (3 lines): 71, 75, 77
  - `editorial-team` @ 71, 77
  - `subagent_type,편집팀` @ 75

### `skills/autopilot-code/references/context-and-guards.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): design/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (1 lines): 30
  - `design-team` @ 30

### `skills/autopilot-code/references/debug-audit.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): design/*, qa/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (4 lines): 32, 70, 71, 92
  - `research-team` @ 32
  - `디자인팀` @ 70, 92
  - `품질관리팀` @ 71

### `skills/autopilot-code/references/dev-pipeline.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): design/*, material/*, qa/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (2 lines): 5, 79
  - `material-team,자료팀` @ 79
  - `디자인팀,연구팀,품질관리팀` @ 5

### `skills/autopilot-design/references/harness.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): design/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (1 lines): 8
  - `디자인팀` @ 8

### `skills/autopilot-design/references/owner-execution.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): design/*, material/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (7 lines): 30, 31, 32, 69, 99, 101, 102
  - `design-team` @ 30, 31, 69, 101, 102
  - `material-team` @ 32, 99

### `skills/autopilot-design/references/paper-figure-policy.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): design/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (1 lines): 5
  - `design-team` @ 5

### `skills/autopilot-design/references/pipeline-execution.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): design/*, material/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (4 lines): 20, 39, 57, 58
  - `디자인팀` @ 39, 57, 58
  - `자료팀` @ 20

### `skills/autopilot-draft/references/convention-common.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): editorial/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (1 lines): 9
  - `editorial-team` @ 9

### `skills/autopilot-draft/references/convention-paper.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): material/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (3 lines): 171, 175, 177
  - `자료팀` @ 171, 175, 177

### `skills/autopilot-draft/references/invocation-and-args.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (1 lines): 67
  - `연구팀` @ 67

### `skills/autopilot-draft/references/owner-execution.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): editorial/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (5 lines): 28, 64, 65, 67, 68
  - `editorial-team` @ 28, 68
  - `research-team` @ 64, 65, 67

### `skills/autopilot-draft/references/pipeline-steps.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): editorial/*, material/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (11 lines): 9, 10, 11, 166, 173, 205, 207, 277, 283, 332, 336
  - `editorial-team` @ 283
  - `subagent_type,자료팀` @ 173
  - `subagent_type,편집팀` @ 336
  - `연구팀` @ 10, 205, 207
  - `자료팀` @ 9, 166
  - `편집팀` @ 11, 277, 332

### `skills/autopilot-draft/references/review-and-qa.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (2 lines): 13, 14
  - `연구팀` @ 13, 14

### `skills/autopilot-draft/references/summary-and-safety.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): editorial/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (3 lines): 18, 21, 23
  - `연구팀` @ 18, 21
  - `편집팀` @ 23

### `skills/autopilot-lab/references/eval-procedure.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): editorial/*, material/*, qa/*, qa/test, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (8 lines): 11, 12, 13, 14, 15, 51, 57, 61
  - `subagent_type,연구팀` @ 61
  - `subagent_type,자료팀` @ 57
  - `subagent_type,테스트팀` @ 51
  - `연구팀` @ 13
  - `자료팀` @ 12
  - `테스트팀` @ 11
  - `편집팀` @ 14
  - `품질관리팀` @ 15

### `skills/autopilot-lab/references/owner-execution.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): dev/*, material/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (2 lines): 94, 131
  - `dev-team` @ 131
  - `material-team` @ 94

### `skills/autopilot-lab/references/setup-procedure.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): dev/*, qa/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (5 lines): 11, 12, 50, 69, 110
  - `subagent_type,개발팀` @ 69
  - `subagent_type,연구팀` @ 50
  - `subagent_type,품질관리팀` @ 110
  - `개발팀` @ 12
  - `연구팀` @ 11

### `skills/autopilot-note/references/feedback-mode.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): design/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (2 lines): 24, 25
  - `design-team` @ 25
  - `디자인팀` @ 24

### `skills/autopilot-note/references/owner-execution.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): editorial/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (1 lines): 68
  - `editorial-team` @ 68

### `skills/autopilot-note/references/process.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): editorial/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (1 lines): 62
  - `편집팀` @ 62

### `skills/autopilot-note/references/scope-qa-usage.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): (cross-harness review unit → codex transport) (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (1 lines): 50
  - `codex-review-team` @ 50

### `skills/autopilot-refine/references/process-stages.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (1 lines): 72
  - `research-team` @ 72

### `skills/autopilot-refine/references/versioning-and-modes.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): (cross-harness review unit → codex transport) (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (1 lines): 64
  - `codex-review-team` @ 64

### `skills/autopilot-research/references/owner-execution.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): editorial/*, material/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (5 lines): 13, 14, 15, 61, 63
  - `editorial-team` @ 63
  - `material-team` @ 13, 14, 15
  - `research-team` @ 61

### `skills/autopilot-research/references/pipeline-search-analysis.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): material/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (20 lines): 7, 8, 9, 10, 11, 12, 13, 15, 66, 68, 71, 130, 133, 157, 160, 185, 203, 216, 226, 242
  - `subagent_type,연구팀` @ 71, 133, 185, 203, 216, 226
  - `subagent_type,자료팀` @ 160, 242
  - `연구팀` @ 7, 8, 9, 10, 11, 12, 13, 66, 68, 130
  - `자료팀` @ 15, 157

### `skills/autopilot-research/references/report-generation.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): editorial/*, material/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (7 lines): 7, 8, 10, 15, 209, 216, 267
  - `editorial-team` @ 216
  - `subagent_type,연구팀` @ 15
  - `연구팀` @ 7, 8, 267
  - `연구팀,자료팀` @ 10
  - `편집팀` @ 209

### `skills/autopilot-ship/references/owner-execution.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): qa/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (2 lines): 61, 62
  - `qa-team` @ 61, 62

### `skills/autopilot-spec/references/invocation-and-modes.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): dev/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (1 lines): 80
  - `개발팀` @ 80

### `skills/autopilot-spec/references/operations-and-examples.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): dev/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (1 lines): 123
  - `개발팀` @ 123

### `skills/autopilot-spec/references/owner-execution.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): dev/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (2 lines): 43, 66
  - `dev-team` @ 43, 66

### `skills/autopilot-spec/references/prd-authoring.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): dev/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (1 lines): 50
  - `개발팀` @ 50

### `skills/autopilot-spec/references/scaffolding.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): dev/*, qa/test (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (6 lines): 3, 10, 24, 56, 81, 84
  - `개발팀` @ 3, 10, 24, 81, 84
  - `테스트팀` @ 56

### `skills/code-execute/README.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): dev/*, qa/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (6 lines): 7, 43, 62, 66, 69, 72
  - `개발팀` @ 43, 62, 69, 72
  - `개발팀,품질관리팀` @ 7
  - `품질관리팀` @ 66

### `skills/code-execute/SKILL.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): dev/*, plan/*, qa/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (7 lines): 18, 70, 94, 99, 106, 108, 125
  - `dev-team` @ 18, 70, 94, 106, 108
  - `dev-team,plan-team` @ 125
  - `qa-team` @ 99

### `skills/code-plan/README.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): plan/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (3 lines): 7, 32, 44
  - `기획팀` @ 7, 32, 44

### `skills/code-plan/SKILL.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): editorial/*, plan/*, qa/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (7 lines): 20, 36, 49, 65, 68, 69, 78
  - `editorial-team` @ 78
  - `plan-team` @ 20, 36, 49, 65, 69
  - `qa-team` @ 68

### `skills/code-refine/README.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): plan/*, qa/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (3 lines): 19, 49, 63
  - `qa-team` @ 49
  - `기획팀` @ 19, 63

### `skills/code-refine/SKILL.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): plan/*, qa/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (4 lines): 24, 36, 46, 50
  - `plan-team` @ 24, 36, 50
  - `qa-team` @ 46

### `skills/code-report/README.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): qa/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (2 lines): 23, 67
  - `품질관리팀` @ 23, 67

### `skills/code-report/SKILL.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): editorial/*, qa/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (4 lines): 18, 37, 105, 114
  - `editorial-team` @ 105, 114
  - `editorial-team,qa-team` @ 18
  - `qa-team` @ 37

### `skills/code-test/README.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): qa/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (1 lines): 19
  - `품질관리팀` @ 19

### `skills/code-test/SKILL.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): qa/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (4 lines): 18, 26, 55, 85
  - `qa-team` @ 18, 26, 55, 85

### `skills/design-components/SKILL.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): design/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (4 lines): 46, 69, 89, 104
  - `design-team` @ 46, 69, 89, 104

### `skills/design-refs/SKILL.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): material/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (1 lines): 51
  - `material-team` @ 51

### `skills/design-review/SKILL.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): design/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (2 lines): 35, 92
  - `design-team` @ 35, 92

### `skills/draft-refine/README.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (3 lines): 22, 106, 118
  - `연구팀` @ 22, 106, 118

### `skills/draft-refine/SKILL.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (7 lines): 37, 46, 65, 86, 90, 136, 137
  - `research-team` @ 37, 46, 65, 86, 90, 136, 137

### `skills/draft-refine/references/delegate-prompt.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (2 lines): 1, 3
  - `research-team,연구팀` @ 3
  - `연구팀` @ 1

### `skills/draft-strategy/README.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (6 lines): 7, 40, 63, 86, 87, 88
  - `연구팀` @ 7, 40, 63, 86, 87, 88

### `skills/draft-strategy/SKILL.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): editorial/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (4 lines): 62, 64, 71, 73
  - `editorial-team` @ 64, 73
  - `research-team` @ 62, 71

### `skills/draft-strategy/references/delegate-prompt.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (2 lines): 1, 2
  - `research-team,연구팀` @ 2
  - `연구팀` @ 1

### `skills/draft-strategy/references/mirror.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): editorial/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (2 lines): 1, 5
  - `editorial-team` @ 5
  - `editorial-team,편집팀` @ 1

### `skills/draft-strategy/references/qa-review.md`
- provenance: HAND (repo-root skills/ = canonical SoT per tools/sync-entry-skill-layer.py)
- action detail: SoT edit point for all three skill copies; rewire team invocations/prose to unit dispatch, then re-project mirrors.
- rewire target unit family(ies): (cross-harness review unit → codex transport), qa/*, research/* (exact unit id = the mode named at each call site, e.g. `mode="figure-gen"` → `material/figure-gen`)
- hits (7 lines): 5, 6, 14, 22, 65, 66, 67
  - `codex-review-team` @ 14
  - `research-team,연구팀` @ 6
  - `연구팀` @ 22, 65, 66, 67
  - `품질관리팀` @ 5

## B. [delete with team agent]

### `adapters/claude/agent-modes/design/_design_rules.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (1 lines): 3
  - `디자인팀` @ 3

### `adapters/claude/agent-modes/design/critic.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (1 lines): 2
  - `디자인팀` @ 2

### `adapters/claude/agent-modes/design/maker.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (5 lines): 2, 15, 21, 60, 61
  - `개발팀` @ 60
  - `디자인팀` @ 2, 21
  - `자료팀` @ 15, 61

### `adapters/claude/agent-modes/design/verifier.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (1 lines): 2
  - `디자인팀` @ 2

### `adapters/claude/agent-modes/dev/backend.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (2 lines): 2, 19
  - `개발팀` @ 2
  - `디자인팀` @ 19

### `adapters/claude/agent-modes/dev/frontend.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (4 lines): 2, 20, 28, 32
  - `개발팀` @ 2
  - `디자인팀` @ 20, 28, 32

### `adapters/claude/agent-modes/dev/new-lib.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (1 lines): 2
  - `개발팀` @ 2

### `adapters/claude/agent-modes/dev/refactor.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (1 lines): 2
  - `개발팀` @ 2

### `adapters/claude/agent-modes/editorial/polish.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (3 lines): 2, 19, 38
  - `편집팀` @ 2, 19, 38

### `adapters/claude/agent-modes/editorial/review.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (1 lines): 2
  - `편집팀` @ 2

### `adapters/claude/agent-modes/editorial/translate.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (1 lines): 2
  - `편집팀` @ 2

### `adapters/claude/agent-modes/material/browser-fetch.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (1 lines): 2
  - `자료팀` @ 2

### `adapters/claude/agent-modes/material/data-script.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (1 lines): 2
  - `자료팀` @ 2

### `adapters/claude/agent-modes/material/figure-gen.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (1 lines): 2
  - `자료팀` @ 2

### `adapters/claude/agent-modes/material/pdf-extract.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (1 lines): 2
  - `자료팀` @ 2

### `adapters/claude/agent-modes/material/web-image-search.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (1 lines): 2
  - `자료팀` @ 2

### `adapters/claude/agent-modes/qa/_review_rules.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (1 lines): 3
  - `품질관리팀` @ 3

### `adapters/claude/agent-modes/qa/code-review.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (2 lines): 2, 52
  - `qa-team` @ 52
  - `품질관리팀` @ 2

### `adapters/claude/agent-modes/qa/data-curate.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (5 lines): 2, 23, 51, 56, 58
  - `개발팀` @ 23, 51, 56
  - `개발팀,품질관리팀` @ 2
  - `자료팀` @ 58

### `adapters/claude/agent-modes/qa/ml-debug.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (6 lines): 2, 24, 39, 45, 50, 52
  - `개발팀` @ 24, 39, 45, 50
  - `개발팀,품질관리팀` @ 2
  - `자료팀` @ 52

### `adapters/claude/agent-modes/qa/plan-review.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (4 lines): 2, 4, 6, 42
  - `qa-team` @ 42
  - `연구팀` @ 4, 6
  - `품질관리팀` @ 2

### `adapters/claude/agent-modes/qa/security-review.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (3 lines): 3, 64, 66
  - `qa-team` @ 64
  - `개발팀` @ 66
  - `품질관리팀` @ 3

### `adapters/claude/agent-modes/qa/test.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (1 lines): 2
  - `품질관리팀` @ 2

### `adapters/claude/agent-modes/research/claim-verify.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (1 lines): 3
  - `연구팀` @ 3

### `adapters/claude/agent-modes/research/fact-check.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (1 lines): 2
  - `연구팀` @ 2

### `adapters/claude/agent-modes/research/plan-review.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (5 lines): 2, 6, 35, 47, 49
  - `연구팀` @ 2, 35, 47, 49
  - `품질관리팀` @ 6

### `adapters/claude/agent-modes/research/research-survey.md`
- provenance: HAND-authored (KO divergent persona copies; unit-catalog source material)
- action detail: File retires wholesale in C3/C4 after its content is merged into roles/units/ (WS-A); team-name hits die with the file.
- hits (3 lines): 2, 81, 82
  - `연구팀` @ 2
  - `자료팀` @ 81, 82

### `adapters/claude/agents/codex-review-team.md`
- provenance: HAND-authored (no GENERATED marker; Claude-native SoT)
- action detail: Runtime team agent file — delete outright in C3 after all readers rewired.
- hits (1 lines): 2
  - `codex-review-team` @ 2

### `adapters/claude/agents/design-team.md`
- provenance: HAND-authored (no GENERATED marker; Claude-native SoT)
- action detail: Runtime team agent file — delete outright in C3 after all readers rewired.
- hits (3 lines): 2, 13, 24
  - `design-team` @ 13
  - `design-team,dev-team,material-team` @ 24
  - `디자인팀` @ 2

### `adapters/claude/agents/dev-team.md`
- provenance: HAND-authored (no GENERATED marker; Claude-native SoT)
- action detail: Runtime team agent file — delete outright in C3 after all readers rewired.
- hits (2 lines): 2, 13
  - `dev-team` @ 13
  - `개발팀` @ 2

### `adapters/claude/agents/editorial-team.md`
- provenance: HAND-authored (no GENERATED marker; Claude-native SoT)
- action detail: Runtime team agent file — delete outright in C3 after all readers rewired.
- hits (1 lines): 2
  - `편집팀` @ 2

### `adapters/claude/agents/material-team.md`
- provenance: HAND-authored (no GENERATED marker; Claude-native SoT)
- action detail: Runtime team agent file — delete outright in C3 after all readers rewired.
- hits (12 lines): 2, 46, 47, 48, 49, 50, 51, 52, 93, 97, 101, 105
  - `design-team,material-team` @ 50
  - `dev-team` @ 46, 47, 48
  - `editorial-team` @ 49
  - `qa-team` @ 51, 52
  - `자료팀` @ 2, 93, 97, 101, 105

### `adapters/claude/agents/plan-team.md`
- provenance: HAND-authored (no GENERATED marker; Claude-native SoT)
- action detail: Runtime team agent file — delete outright in C3 after all readers rewired.
- hits (1 lines): 2
  - `기획팀` @ 2

### `adapters/claude/agents/qa-team.md`
- provenance: HAND-authored (no GENERATED marker; Claude-native SoT)
- action detail: Runtime team agent file — delete outright in C3 after all readers rewired.
- hits (4 lines): 2, 13, 25, 44
  - `dev-team` @ 44
  - `qa-team` @ 13
  - `research-team` @ 25
  - `품질관리팀` @ 2

### `adapters/claude/agents/research-team.md`
- provenance: HAND-authored (no GENERATED marker; Claude-native SoT)
- action detail: Runtime team agent file — delete outright in C3 after all readers rewired.
- hits (3 lines): 2, 13, 39
  - `qa-team` @ 39
  - `research-team` @ 13
  - `연구팀` @ 2

### `hooks/portable-guards.test.sh`
- provenance: HAND (guard + guard tests)
- action detail: Team-agent-shaped checks/fixtures die with the teams; replaced by check-unit-config.py and unit-shaped fixtures (WS-D). memory-scout checks stay.
- hits (32 lines): 1376, 1378, 1381, 1384, 1386, 1487, 1502, 1804, 1805, 1806, 1807, 1809, 1814, 1815, 1816, 1817, 1818, 1823, 1824, 1825, 1826, 1827, 1829, 2601, 2628, 2631, 2932, 2938, 2949, 3296, 3297, 3305
  - `dev-team` @ 1381, 1809
  - `dev-team,editorial-team,plan-team,qa-team` @ 1487
  - `editorial-team` @ 1386, 1817
  - `material-team` @ 1816
  - `memory-scout` @ 1823, 1824, 1825, 1826, 1827, 1829
  - `plan-team` @ 1376, 1378, 2601, 2628, 2631, 3296, 3297
  - `qa-team` @ 1384, 1502, 1804, 1805, 1806, 1807, 1814, 1818, 2932, 2938, 2949, 3305
  - `research-team` @ 1815

### `tools/check-adaptation-boundary.sh`
- provenance: HAND (guard + guard tests)
- action detail: Team-agent-shaped checks/fixtures die with the teams; replaced by check-unit-config.py and unit-shaped fixtures (WS-D). memory-scout checks stay.
- hits (40 lines): 849, 851, 854, 856, 858, 1077, 1098, 1648, 1676, 1683, 1687, 1699, 1705, 1706, 1707, 1708, 1709, 1717, 1729, 1735, 1736, 1737, 1755, 1758, 1764, 1769, 2531, 2534, 2540, 2547, 2551, 2568, 2575, 2576, 3040, 3059, 3083, 3086, 3764, 3765
  - `codex-review-team` @ 3086
  - `design-team,dev-team,editorial-team,material-team,memory-scout,plan-team,qa-team,research-team` @ 1648, 1699, 2534, 2568
  - `design-team,dev-team,editorial-team,material-team,plan-team,qa-team,research-team` @ 1769, 3040
  - `dev-team` @ 854, 1729
  - `dev-team,editorial-team,plan-team,qa-team` @ 1098
  - `editorial-team` @ 858, 1737, 3764, 3765
  - `material-team` @ 1736, 1758, 1764
  - `memory-scout` @ 1676, 1683, 1687, 1705, 1706, 1707, 1708, 1709, 1755, 2531, 2540, 2547, 2551, 2575, 2576, 3059, 3083
  - `plan-team` @ 849, 851
  - `qa-team` @ 856, 1077, 1717
  - `research-team` @ 1735

### `tools/install/profile-activation.test.sh`
- provenance: HAND
- action detail: codex-review-team activation entries retire with the alias; memory-scout entries stay.
- hits (1 lines): 79
  - `codex-review-team` @ 79

### `tools/install/runtime_activation.py`
- provenance: HAND
- action detail: codex-review-team activation entries retire with the alias; memory-scout entries stay.
- hits (2 lines): 350, 460
  - `codex-review-team` @ 460
  - `memory-scout` @ 350

## C. [generator change: emit kernel-only]

### `adapters/codex/agents/design-team.toml`
- provenance: GENERATED (adapters/<h>/bin/sync-native-agents.py from harness-manifest.json)
- action detail: Do NOT hand-delete: change the generator to emit kernel-only (memory-scout), then regen removes these.
- hits (4 lines): 1, 2, 7, 23
  - `design-team` @ 1, 2, 7, 23

### `adapters/codex/agents/dev-team.toml`
- provenance: GENERATED (adapters/<h>/bin/sync-native-agents.py from harness-manifest.json)
- action detail: Do NOT hand-delete: change the generator to emit kernel-only (memory-scout), then regen removes these.
- hits (4 lines): 1, 2, 7, 23
  - `dev-team` @ 1, 2, 7, 23

### `adapters/codex/agents/editorial-team.toml`
- provenance: GENERATED (adapters/<h>/bin/sync-native-agents.py from harness-manifest.json)
- action detail: Do NOT hand-delete: change the generator to emit kernel-only (memory-scout), then regen removes these.
- hits (4 lines): 1, 2, 7, 23
  - `editorial-team` @ 1, 2, 7, 23

### `adapters/codex/agents/material-team.toml`
- provenance: GENERATED (adapters/<h>/bin/sync-native-agents.py from harness-manifest.json)
- action detail: Do NOT hand-delete: change the generator to emit kernel-only (memory-scout), then regen removes these.
- hits (4 lines): 1, 2, 7, 23
  - `material-team` @ 1, 2, 7, 23

### `adapters/codex/agents/plan-team.toml`
- provenance: GENERATED (adapters/<h>/bin/sync-native-agents.py from harness-manifest.json)
- action detail: Do NOT hand-delete: change the generator to emit kernel-only (memory-scout), then regen removes these.
- hits (4 lines): 1, 2, 7, 23
  - `plan-team` @ 1, 2, 7, 23

### `adapters/codex/agents/qa-team.toml`
- provenance: GENERATED (adapters/<h>/bin/sync-native-agents.py from harness-manifest.json)
- action detail: Do NOT hand-delete: change the generator to emit kernel-only (memory-scout), then regen removes these.
- hits (4 lines): 1, 2, 7, 23
  - `qa-team` @ 1, 2, 7, 23

### `adapters/codex/agents/research-team.toml`
- provenance: GENERATED (adapters/<h>/bin/sync-native-agents.py from harness-manifest.json)
- action detail: Do NOT hand-delete: change the generator to emit kernel-only (memory-scout), then regen removes these.
- hits (4 lines): 1, 2, 7, 23
  - `research-team` @ 1, 2, 7, 23

### `adapters/codex/bin/sync-native-agents.py`
- provenance: HAND (the generator itself)
- action detail: Generator change: emit kernel-only (memory-scout); drop team-profile emission + team-specific overrides.
- hits (13 lines): 47, 49, 87, 106, 107, 108, 161, 165, 169, 174, 178, 182, 186
  - `design-team` @ 182
  - `dev-team` @ 165
  - `editorial-team` @ 87, 108, 186
  - `material-team` @ 178
  - `memory-scout` @ 47, 49
  - `plan-team` @ 161
  - `qa-team` @ 106, 169
  - `research-team` @ 107, 174

### `adapters/opencode/agents/design-team/design-team.md`
- provenance: GENERATED (adapters/<h>/bin/sync-native-agents.py from harness-manifest.json)
- action detail: Do NOT hand-delete: change the generator to emit kernel-only (memory-scout), then regen removes these.
- hits (3 lines): 2, 10, 24
  - `design-team` @ 2, 10, 24

### `adapters/opencode/agents/dev-team/dev-team.md`
- provenance: GENERATED (adapters/<h>/bin/sync-native-agents.py from harness-manifest.json)
- action detail: Do NOT hand-delete: change the generator to emit kernel-only (memory-scout), then regen removes these.
- hits (3 lines): 2, 10, 24
  - `dev-team` @ 2, 10, 24

### `adapters/opencode/agents/editorial-team/editorial-team.md`
- provenance: GENERATED (adapters/<h>/bin/sync-native-agents.py from harness-manifest.json)
- action detail: Do NOT hand-delete: change the generator to emit kernel-only (memory-scout), then regen removes these.
- hits (3 lines): 2, 10, 24
  - `editorial-team` @ 2, 10, 24

### `adapters/opencode/agents/material-team/material-team.md`
- provenance: GENERATED (adapters/<h>/bin/sync-native-agents.py from harness-manifest.json)
- action detail: Do NOT hand-delete: change the generator to emit kernel-only (memory-scout), then regen removes these.
- hits (3 lines): 2, 10, 24
  - `material-team` @ 2, 10, 24

### `adapters/opencode/agents/plan-team/plan-team.md`
- provenance: GENERATED (adapters/<h>/bin/sync-native-agents.py from harness-manifest.json)
- action detail: Do NOT hand-delete: change the generator to emit kernel-only (memory-scout), then regen removes these.
- hits (3 lines): 2, 10, 24
  - `plan-team` @ 2, 10, 24

### `adapters/opencode/agents/qa-team/qa-team.md`
- provenance: GENERATED (adapters/<h>/bin/sync-native-agents.py from harness-manifest.json)
- action detail: Do NOT hand-delete: change the generator to emit kernel-only (memory-scout), then regen removes these.
- hits (3 lines): 2, 13, 27
  - `qa-team` @ 2, 13, 27

### `adapters/opencode/agents/research-team/research-team.md`
- provenance: GENERATED (adapters/<h>/bin/sync-native-agents.py from harness-manifest.json)
- action detail: Do NOT hand-delete: change the generator to emit kernel-only (memory-scout), then regen removes these.
- hits (3 lines): 2, 10, 24
  - `research-team` @ 2, 10, 24

### `adapters/opencode/bin/sync-native-agents.py`
- provenance: HAND (the generator itself)
- action detail: Generator change: emit kernel-only (memory-scout); drop team-profile emission + team-specific overrides.
- hits (6 lines): 20, 22, 78, 79, 80, 101
  - `editorial-team` @ 80
  - `memory-scout` @ 20, 22
  - `qa-team` @ 78, 101
  - `research-team` @ 79

### `tools/build-manifest.py`
- provenance: HAND (the manifest generator)
- action detail: build_agents() (:189) emits one agent row per role profile; switch to kernel-only + retire the :577 codex-review-team alias for external-adversary.
- hits (1 lines): 577
  - `codex-review-team` @ 577

## D. [regen-covered, no hand edit]

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/agents/codex-review-team.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 2
  - `codex-review-team` @ 2

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/agents/design-team.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (3 lines): 2, 13, 24
  - `design-team` @ 13
  - `design-team,dev-team,material-team` @ 24
  - `디자인팀` @ 2

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/agents/dev-team.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (2 lines): 2, 13
  - `dev-team` @ 13
  - `개발팀` @ 2

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/agents/editorial-team.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 2
  - `편집팀` @ 2

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/agents/material-team.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (12 lines): 2, 46, 47, 48, 49, 50, 51, 52, 93, 97, 101, 105
  - `design-team,material-team` @ 50
  - `dev-team` @ 46, 47, 48
  - `editorial-team` @ 49
  - `qa-team` @ 51, 52
  - `자료팀` @ 2, 93, 97, 101, 105

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/agents/memory-scout.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (2 lines): 2, 13
  - `memory-scout` @ 2, 13

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/agents/plan-team.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 2
  - `기획팀` @ 2

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/agents/qa-team.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (4 lines): 2, 13, 25, 44
  - `dev-team` @ 44
  - `qa-team` @ 13
  - `research-team` @ 25
  - `품질관리팀` @ 2

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/agents/research-team.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (3 lines): 2, 13, 39
  - `qa-team` @ 39
  - `research-team` @ 13
  - `연구팀` @ 2

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/analyze-project/references/mode-code.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (3 lines): 72, 84, 192
  - `dev-team` @ 84
  - `plan-team` @ 72
  - `qa-team` @ 192

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/analyze-project/references/mode-doc.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (2 lines): 23, 27
  - `research-team` @ 23, 27

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/analyze-project/references/mode-paper.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (5 lines): 7, 28, 39, 54, 78
  - `research-team` @ 7, 28, 39, 54, 78

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/analyze-project/references/owner-execution.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (5 lines): 81, 83, 84, 85, 92
  - `qa-team` @ 83
  - `research-team` @ 81, 84, 85, 92

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/analyze-user/references/integration-and-usage.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (6 lines): 7, 8, 9, 10, 11, 12
  - `design-team` @ 8
  - `dev-team` @ 12
  - `editorial-team` @ 10
  - `material-team` @ 7
  - `plan-team` @ 11
  - `research-team` @ 9

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/analyze-user/references/owner-execution.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 65
  - `research-team` @ 65

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/analyze-user/references/pipeline-phases.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (2 lines): 52, 57
  - `research-team` @ 52
  - `연구팀` @ 57

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/audit/references/owner-execution.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (3 lines): 77, 84, 101
  - `editorial-team` @ 77, 101
  - `qa-team,research-team` @ 84

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/audit/references/report-and-autofix.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (3 lines): 71, 75, 77
  - `editorial-team` @ 71, 77
  - `subagent_type,편집팀` @ 75

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-code/references/context-and-guards.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 30
  - `design-team` @ 30

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-code/references/debug-audit.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (4 lines): 32, 70, 71, 92
  - `research-team` @ 32
  - `디자인팀` @ 70, 92
  - `품질관리팀` @ 71

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-code/references/dev-pipeline.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (2 lines): 5, 79
  - `material-team,자료팀` @ 79
  - `디자인팀,연구팀,품질관리팀` @ 5

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-design/references/harness.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 8
  - `디자인팀` @ 8

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-design/references/owner-execution.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (7 lines): 30, 31, 32, 69, 99, 101, 102
  - `design-team` @ 30, 31, 69, 101, 102
  - `material-team` @ 32, 99

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-design/references/paper-figure-policy.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 5
  - `design-team` @ 5

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-design/references/pipeline-execution.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (4 lines): 20, 39, 57, 58
  - `디자인팀` @ 39, 57, 58
  - `자료팀` @ 20

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-draft/references/convention-common.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 9
  - `editorial-team` @ 9

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-draft/references/convention-paper.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (3 lines): 171, 175, 177
  - `자료팀` @ 171, 175, 177

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-draft/references/invocation-and-args.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 67
  - `연구팀` @ 67

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-draft/references/owner-execution.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (5 lines): 28, 64, 65, 67, 68
  - `editorial-team` @ 28, 68
  - `research-team` @ 64, 65, 67

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-draft/references/pipeline-steps.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (11 lines): 9, 10, 11, 166, 173, 205, 207, 277, 283, 332, 336
  - `editorial-team` @ 283
  - `subagent_type,자료팀` @ 173
  - `subagent_type,편집팀` @ 336
  - `연구팀` @ 10, 205, 207
  - `자료팀` @ 9, 166
  - `편집팀` @ 11, 277, 332

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-draft/references/review-and-qa.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (2 lines): 13, 14
  - `연구팀` @ 13, 14

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-draft/references/summary-and-safety.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (3 lines): 18, 21, 23
  - `연구팀` @ 18, 21
  - `편집팀` @ 23

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-lab/references/eval-procedure.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (8 lines): 11, 12, 13, 14, 15, 51, 57, 61
  - `subagent_type,연구팀` @ 61
  - `subagent_type,자료팀` @ 57
  - `subagent_type,테스트팀` @ 51
  - `연구팀` @ 13
  - `자료팀` @ 12
  - `테스트팀` @ 11
  - `편집팀` @ 14
  - `품질관리팀` @ 15

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-lab/references/owner-execution.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (2 lines): 94, 131
  - `dev-team` @ 131
  - `material-team` @ 94

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-lab/references/setup-procedure.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (5 lines): 11, 12, 50, 69, 110
  - `subagent_type,개발팀` @ 69
  - `subagent_type,연구팀` @ 50
  - `subagent_type,품질관리팀` @ 110
  - `개발팀` @ 12
  - `연구팀` @ 11

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-note/references/feedback-mode.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (2 lines): 24, 25
  - `design-team` @ 25
  - `디자인팀` @ 24

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-note/references/owner-execution.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 68
  - `editorial-team` @ 68

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-note/references/process.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 62
  - `편집팀` @ 62

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-note/references/scope-qa-usage.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 50
  - `codex-review-team` @ 50

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-refine/references/process-stages.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 72
  - `research-team` @ 72

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-refine/references/versioning-and-modes.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 64
  - `codex-review-team` @ 64

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-research/references/owner-execution.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (5 lines): 13, 14, 15, 61, 63
  - `editorial-team` @ 63
  - `material-team` @ 13, 14, 15
  - `research-team` @ 61

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-research/references/pipeline-search-analysis.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (20 lines): 7, 8, 9, 10, 11, 12, 13, 15, 66, 68, 71, 130, 133, 157, 160, 185, 203, 216, 226, 242
  - `subagent_type,연구팀` @ 71, 133, 185, 203, 216, 226
  - `subagent_type,자료팀` @ 160, 242
  - `연구팀` @ 7, 8, 9, 10, 11, 12, 13, 66, 68, 130
  - `자료팀` @ 15, 157

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-research/references/report-generation.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (7 lines): 7, 8, 10, 15, 209, 216, 267
  - `editorial-team` @ 216
  - `subagent_type,연구팀` @ 15
  - `연구팀` @ 7, 8, 267
  - `연구팀,자료팀` @ 10
  - `편집팀` @ 209

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-ship/references/owner-execution.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (2 lines): 61, 62
  - `qa-team` @ 61, 62

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-spec/references/invocation-and-modes.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 80
  - `개발팀` @ 80

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-spec/references/operations-and-examples.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 123
  - `개발팀` @ 123

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-spec/references/owner-execution.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (2 lines): 43, 66
  - `dev-team` @ 43, 66

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-spec/references/prd-authoring.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 50
  - `개발팀` @ 50

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-spec/references/scaffolding.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (6 lines): 3, 10, 24, 56, 81, 84
  - `개발팀` @ 3, 10, 24, 81, 84
  - `테스트팀` @ 56

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-execute/README.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (6 lines): 7, 43, 62, 66, 69, 72
  - `개발팀` @ 43, 62, 69, 72
  - `개발팀,품질관리팀` @ 7
  - `품질관리팀` @ 66

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-execute/SKILL.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (7 lines): 18, 70, 94, 99, 106, 108, 125
  - `dev-team` @ 18, 70, 94, 106, 108
  - `dev-team,plan-team` @ 125
  - `qa-team` @ 99

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-plan/README.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (3 lines): 7, 32, 44
  - `기획팀` @ 7, 32, 44

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-plan/SKILL.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (7 lines): 20, 36, 49, 65, 68, 69, 78
  - `editorial-team` @ 78
  - `plan-team` @ 20, 36, 49, 65, 69
  - `qa-team` @ 68

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-refine/README.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (3 lines): 19, 49, 63
  - `qa-team` @ 49
  - `기획팀` @ 19, 63

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-refine/SKILL.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (4 lines): 24, 36, 46, 50
  - `plan-team` @ 24, 36, 50
  - `qa-team` @ 46

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-report/README.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (2 lines): 23, 67
  - `품질관리팀` @ 23, 67

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-report/SKILL.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (4 lines): 18, 37, 105, 114
  - `editorial-team` @ 105, 114
  - `editorial-team,qa-team` @ 18
  - `qa-team` @ 37

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-test/README.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 19
  - `품질관리팀` @ 19

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-test/SKILL.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (4 lines): 18, 26, 55, 85
  - `qa-team` @ 18, 26, 55, 85

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/design-components/SKILL.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (4 lines): 46, 69, 89, 104
  - `design-team` @ 46, 69, 89, 104

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/design-refs/SKILL.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (1 lines): 51
  - `material-team` @ 51

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/design-review/SKILL.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (2 lines): 35, 92
  - `design-team` @ 35, 92

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/draft-refine/README.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (3 lines): 22, 106, 118
  - `연구팀` @ 22, 106, 118

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/draft-refine/SKILL.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (7 lines): 37, 46, 65, 86, 90, 136, 137
  - `research-team` @ 37, 46, 65, 86, 90, 136, 137

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/draft-refine/references/delegate-prompt.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (2 lines): 1, 3
  - `research-team,연구팀` @ 3
  - `연구팀` @ 1

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/draft-strategy/README.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (6 lines): 7, 40, 63, 86, 87, 88
  - `연구팀` @ 7, 40, 63, 86, 87, 88

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/draft-strategy/SKILL.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (4 lines): 62, 64, 71, 73
  - `editorial-team` @ 64, 73
  - `research-team` @ 62, 71

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/draft-strategy/references/delegate-prompt.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (2 lines): 1, 2
  - `research-team,연구팀` @ 2
  - `연구팀` @ 1

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/draft-strategy/references/mirror.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (2 lines): 1, 5
  - `editorial-team` @ 5
  - `editorial-team,편집팀` @ 1

### `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/draft-strategy/references/qa-review.md`
- provenance: GENERATED (sync-native-plugin.py copies adapters/claude/{skills,agents})
- action detail: Regenerate after SoT edit/regen upstream; team agent copies disappear on regen once the SoT agents are deleted.
- hits (7 lines): 5, 6, 14, 22, 65, 66, 67
  - `codex-review-team` @ 14
  - `research-team,연구팀` @ 6
  - `연구팀` @ 22, 65, 66, 67
  - `품질관리팀` @ 5

### `adapters/claude/skills/analyze-project/references/mode-code.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (3 lines): 72, 84, 192
  - `dev-team` @ 84
  - `plan-team` @ 72
  - `qa-team` @ 192

### `adapters/claude/skills/analyze-project/references/mode-doc.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (2 lines): 23, 27
  - `research-team` @ 23, 27

### `adapters/claude/skills/analyze-project/references/mode-paper.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (5 lines): 7, 28, 39, 54, 78
  - `research-team` @ 7, 28, 39, 54, 78

### `adapters/claude/skills/analyze-project/references/owner-execution.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (5 lines): 81, 83, 84, 85, 92
  - `qa-team` @ 83
  - `research-team` @ 81, 84, 85, 92

### `adapters/claude/skills/analyze-user/references/integration-and-usage.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (6 lines): 7, 8, 9, 10, 11, 12
  - `design-team` @ 8
  - `dev-team` @ 12
  - `editorial-team` @ 10
  - `material-team` @ 7
  - `plan-team` @ 11
  - `research-team` @ 9

### `adapters/claude/skills/analyze-user/references/owner-execution.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (1 lines): 65
  - `research-team` @ 65

### `adapters/claude/skills/analyze-user/references/pipeline-phases.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (2 lines): 52, 57
  - `research-team` @ 52
  - `연구팀` @ 57

### `adapters/claude/skills/audit/references/owner-execution.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (3 lines): 77, 84, 101
  - `editorial-team` @ 77, 101
  - `qa-team,research-team` @ 84

### `adapters/claude/skills/audit/references/report-and-autofix.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (3 lines): 71, 75, 77
  - `editorial-team` @ 71, 77
  - `subagent_type,편집팀` @ 75

### `adapters/claude/skills/autopilot-code/references/context-and-guards.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (1 lines): 30
  - `design-team` @ 30

### `adapters/claude/skills/autopilot-code/references/debug-audit.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (4 lines): 32, 70, 71, 92
  - `research-team` @ 32
  - `디자인팀` @ 70, 92
  - `품질관리팀` @ 71

### `adapters/claude/skills/autopilot-code/references/dev-pipeline.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (2 lines): 5, 79
  - `material-team,자료팀` @ 79
  - `디자인팀,연구팀,품질관리팀` @ 5

### `adapters/claude/skills/autopilot-design/references/harness.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (1 lines): 8
  - `디자인팀` @ 8

### `adapters/claude/skills/autopilot-design/references/owner-execution.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (7 lines): 30, 31, 32, 69, 99, 101, 102
  - `design-team` @ 30, 31, 69, 101, 102
  - `material-team` @ 32, 99

### `adapters/claude/skills/autopilot-design/references/paper-figure-policy.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (1 lines): 5
  - `design-team` @ 5

### `adapters/claude/skills/autopilot-design/references/pipeline-execution.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (4 lines): 20, 39, 57, 58
  - `디자인팀` @ 39, 57, 58
  - `자료팀` @ 20

### `adapters/claude/skills/autopilot-draft/references/convention-common.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (1 lines): 9
  - `editorial-team` @ 9

### `adapters/claude/skills/autopilot-draft/references/convention-paper.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (3 lines): 171, 175, 177
  - `자료팀` @ 171, 175, 177

### `adapters/claude/skills/autopilot-draft/references/invocation-and-args.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (1 lines): 67
  - `연구팀` @ 67

### `adapters/claude/skills/autopilot-draft/references/owner-execution.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (5 lines): 28, 64, 65, 67, 68
  - `editorial-team` @ 28, 68
  - `research-team` @ 64, 65, 67

### `adapters/claude/skills/autopilot-draft/references/pipeline-steps.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (11 lines): 9, 10, 11, 166, 173, 205, 207, 277, 283, 332, 336
  - `editorial-team` @ 283
  - `subagent_type,자료팀` @ 173
  - `subagent_type,편집팀` @ 336
  - `연구팀` @ 10, 205, 207
  - `자료팀` @ 9, 166
  - `편집팀` @ 11, 277, 332

### `adapters/claude/skills/autopilot-draft/references/review-and-qa.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (2 lines): 13, 14
  - `연구팀` @ 13, 14

### `adapters/claude/skills/autopilot-draft/references/summary-and-safety.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (3 lines): 18, 21, 23
  - `연구팀` @ 18, 21
  - `편집팀` @ 23

### `adapters/claude/skills/autopilot-lab/references/eval-procedure.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (8 lines): 11, 12, 13, 14, 15, 51, 57, 61
  - `subagent_type,연구팀` @ 61
  - `subagent_type,자료팀` @ 57
  - `subagent_type,테스트팀` @ 51
  - `연구팀` @ 13
  - `자료팀` @ 12
  - `테스트팀` @ 11
  - `편집팀` @ 14
  - `품질관리팀` @ 15

### `adapters/claude/skills/autopilot-lab/references/owner-execution.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (2 lines): 94, 131
  - `dev-team` @ 131
  - `material-team` @ 94

### `adapters/claude/skills/autopilot-lab/references/setup-procedure.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (5 lines): 11, 12, 50, 69, 110
  - `subagent_type,개발팀` @ 69
  - `subagent_type,연구팀` @ 50
  - `subagent_type,품질관리팀` @ 110
  - `개발팀` @ 12
  - `연구팀` @ 11

### `adapters/claude/skills/autopilot-note/references/feedback-mode.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (2 lines): 24, 25
  - `design-team` @ 25
  - `디자인팀` @ 24

### `adapters/claude/skills/autopilot-note/references/owner-execution.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (1 lines): 68
  - `editorial-team` @ 68

### `adapters/claude/skills/autopilot-note/references/process.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (1 lines): 62
  - `편집팀` @ 62

### `adapters/claude/skills/autopilot-note/references/scope-qa-usage.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (1 lines): 50
  - `codex-review-team` @ 50

### `adapters/claude/skills/autopilot-refine/references/process-stages.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (1 lines): 72
  - `research-team` @ 72

### `adapters/claude/skills/autopilot-refine/references/versioning-and-modes.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (1 lines): 64
  - `codex-review-team` @ 64

### `adapters/claude/skills/autopilot-research/references/owner-execution.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (5 lines): 13, 14, 15, 61, 63
  - `editorial-team` @ 63
  - `material-team` @ 13, 14, 15
  - `research-team` @ 61

### `adapters/claude/skills/autopilot-research/references/pipeline-search-analysis.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (20 lines): 7, 8, 9, 10, 11, 12, 13, 15, 66, 68, 71, 130, 133, 157, 160, 185, 203, 216, 226, 242
  - `subagent_type,연구팀` @ 71, 133, 185, 203, 216, 226
  - `subagent_type,자료팀` @ 160, 242
  - `연구팀` @ 7, 8, 9, 10, 11, 12, 13, 66, 68, 130
  - `자료팀` @ 15, 157

### `adapters/claude/skills/autopilot-research/references/report-generation.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (7 lines): 7, 8, 10, 15, 209, 216, 267
  - `editorial-team` @ 216
  - `subagent_type,연구팀` @ 15
  - `연구팀` @ 7, 8, 267
  - `연구팀,자료팀` @ 10
  - `편집팀` @ 209

### `adapters/claude/skills/autopilot-ship/references/owner-execution.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (2 lines): 61, 62
  - `qa-team` @ 61, 62

### `adapters/claude/skills/autopilot-spec/references/invocation-and-modes.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (1 lines): 80
  - `개발팀` @ 80

### `adapters/claude/skills/autopilot-spec/references/operations-and-examples.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (1 lines): 123
  - `개발팀` @ 123

### `adapters/claude/skills/autopilot-spec/references/owner-execution.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (2 lines): 43, 66
  - `dev-team` @ 43, 66

### `adapters/claude/skills/autopilot-spec/references/prd-authoring.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (1 lines): 50
  - `개발팀` @ 50

### `adapters/claude/skills/autopilot-spec/references/scaffolding.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (6 lines): 3, 10, 24, 56, 81, 84
  - `개발팀` @ 3, 10, 24, 81, 84
  - `테스트팀` @ 56

### `adapters/claude/skills/code-execute/README.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (6 lines): 7, 43, 62, 66, 69, 72
  - `개발팀` @ 43, 62, 69, 72
  - `개발팀,품질관리팀` @ 7
  - `품질관리팀` @ 66

### `adapters/claude/skills/code-execute/SKILL.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (7 lines): 18, 70, 94, 99, 106, 108, 125
  - `dev-team` @ 18, 70, 94, 106, 108
  - `dev-team,plan-team` @ 125
  - `qa-team` @ 99

### `adapters/claude/skills/code-plan/README.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (3 lines): 7, 32, 44
  - `기획팀` @ 7, 32, 44

### `adapters/claude/skills/code-plan/SKILL.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (7 lines): 20, 36, 49, 65, 68, 69, 78
  - `editorial-team` @ 78
  - `plan-team` @ 20, 36, 49, 65, 69
  - `qa-team` @ 68

### `adapters/claude/skills/code-refine/README.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (3 lines): 19, 49, 63
  - `qa-team` @ 49
  - `기획팀` @ 19, 63

### `adapters/claude/skills/code-refine/SKILL.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (4 lines): 24, 36, 46, 50
  - `plan-team` @ 24, 36, 50
  - `qa-team` @ 46

### `adapters/claude/skills/code-report/README.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (2 lines): 23, 67
  - `품질관리팀` @ 23, 67

### `adapters/claude/skills/code-report/SKILL.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (4 lines): 18, 37, 105, 114
  - `editorial-team` @ 105, 114
  - `editorial-team,qa-team` @ 18
  - `qa-team` @ 37

### `adapters/claude/skills/code-test/README.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (1 lines): 19
  - `품질관리팀` @ 19

### `adapters/claude/skills/code-test/SKILL.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (4 lines): 18, 26, 55, 85
  - `qa-team` @ 18, 26, 55, 85

### `adapters/claude/skills/design-components/SKILL.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (4 lines): 46, 69, 89, 104
  - `design-team` @ 46, 69, 89, 104

### `adapters/claude/skills/design-refs/SKILL.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (1 lines): 51
  - `material-team` @ 51

### `adapters/claude/skills/design-review/SKILL.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (2 lines): 35, 92
  - `design-team` @ 35, 92

### `adapters/claude/skills/draft-refine/README.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (3 lines): 22, 106, 118
  - `연구팀` @ 22, 106, 118

### `adapters/claude/skills/draft-refine/SKILL.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (7 lines): 37, 46, 65, 86, 90, 136, 137
  - `research-team` @ 37, 46, 65, 86, 90, 136, 137

### `adapters/claude/skills/draft-refine/references/delegate-prompt.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (2 lines): 1, 3
  - `research-team,연구팀` @ 3
  - `연구팀` @ 1

### `adapters/claude/skills/draft-strategy/README.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (6 lines): 7, 40, 63, 86, 87, 88
  - `연구팀` @ 7, 40, 63, 86, 87, 88

### `adapters/claude/skills/draft-strategy/SKILL.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (4 lines): 62, 64, 71, 73
  - `editorial-team` @ 64, 73
  - `research-team` @ 62, 71

### `adapters/claude/skills/draft-strategy/references/delegate-prompt.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (2 lines): 1, 2
  - `research-team,연구팀` @ 2
  - `연구팀` @ 1

### `adapters/claude/skills/draft-strategy/references/mirror.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (2 lines): 1, 5
  - `editorial-team` @ 5
  - `editorial-team,편집팀` @ 1

### `adapters/claude/skills/draft-strategy/references/qa-review.md`
- provenance: MIRROR (projection of repo-root skills/ via tools/sync-entry-skill-layer.py; byte-identical today)
- action detail: Edit repo-root skills/ SoT, then re-project; do not hand-edit here independently.
- hits (7 lines): 5, 6, 14, 22, 65, 66, 67
  - `codex-review-team` @ 14
  - `research-team,연구팀` @ 6
  - `연구팀` @ 22, 65, 66, 67
  - `품질관리팀` @ 5

## E. [keep: memory-scout kernel helper / unchanged mechanism]

### `adapters/claude/agents/memory-scout.md`
- provenance: hand (claude) / GENERATED (codex+opencode via sync-native-agents.py)
- action detail: memory-scout is the kernel helper; survives on every harness.
- hits (2 lines): 2, 13
  - `memory-scout` @ 2, 13

### `adapters/codex/agents/memory-scout.toml`
- provenance: hand (claude) / GENERATED (codex+opencode via sync-native-agents.py)
- action detail: memory-scout is the kernel helper; survives on every harness.
- hits (2 lines): 1, 7
  - `memory-scout` @ 1, 7

### `adapters/opencode/agents/memory-scout/memory-scout.md`
- provenance: hand (claude) / GENERATED (codex+opencode via sync-native-agents.py)
- action detail: memory-scout is the kernel helper; survives on every harness.
- hits (1 lines): 13
  - `memory-scout` @ 13

### `core/ADAPTATION_INVENTORY.md`
- provenance: HAND (doc)
- action detail: memory-scout inventory rows — kernel helper stays; verify wording still true post-re-homing.
- hits (2 lines): 30, 41
  - `memory-scout` @ 30, 41

## F. AMBIGUOUS — flagged for explicit decision

### `adapters/claude/statusline.sh`
- provenance: HAND
- action detail: KO comment mentions 디자인팀 as an example of direct-edit flows; cosmetic comment rewrite only.
- hits (1 lines): 254
  - `디자인팀` @ 254

### `adapters/claude/tools/fleet/collectors/claude.py`
- provenance: HAND (fleet observability; tools/fleet ↔ adapters/claude/tools/fleet duplicated pair)
- action detail: subagent_type parsing is a generic mechanism (keep); team names appear only as test fixtures/comments. Rename fixtures only if the grep-proof DoD is enforced literally over tests.
- hits (1 lines): 222
  - `subagent_type` @ 222

### `adapters/claude/tools/fleet/render.py`
- provenance: HAND (fleet observability; tools/fleet ↔ adapters/claude/tools/fleet duplicated pair)
- action detail: subagent_type parsing is a generic mechanism (keep); team names appear only as test fixtures/comments. Rename fixtures only if the grep-proof DoD is enforced literally over tests.
- hits (1 lines): 1155
  - `plan-team` @ 1155

### `adapters/claude/tools/fleet/tests/test_f15_rows.py`
- provenance: HAND (fleet observability; tools/fleet ↔ adapters/claude/tools/fleet duplicated pair)
- action detail: subagent_type parsing is a generic mechanism (keep); team names appear only as test fixtures/comments. Rename fixtures only if the grep-proof DoD is enforced literally over tests.
- hits (2 lines): 437, 440
  - `plan-team` @ 437, 440

### `adapters/claude/tools/fleet/tests/test_f29_subagents.py`
- provenance: HAND (fleet observability; tools/fleet ↔ adapters/claude/tools/fleet duplicated pair)
- action detail: subagent_type parsing is a generic mechanism (keep); team names appear only as test fixtures/comments. Rename fixtures only if the grep-proof DoD is enforced literally over tests.
- hits (3 lines): 390, 401, 409
  - `qa-team` @ 390, 401
  - `subagent_type` @ 409

### `roles/units/design/_NOTES.md`
- provenance: HAND (NEW WS-A authoring residue)
- action detail: Provenance references to legacy team files. Conflicts with DoD 'grep-proof no dangling team reference' — decide: allow as historical provenance or rephrase.
- hits (6 lines): 5, 33, 43, 49, 56, 62
  - `design-team` @ 5, 33, 43, 49, 56, 62

### `roles/units/dev/_NOTES.md`
- provenance: HAND (NEW WS-A authoring residue)
- action detail: Provenance references to legacy team files. Conflicts with DoD 'grep-proof no dangling team reference' — decide: allow as historical provenance or rephrase.
- hits (8 lines): 3, 5, 7, 9, 11, 17, 21, 25
  - `dev-team` @ 3, 5, 7, 9, 11, 17, 21, 25

### `roles/units/editorial/_NOTES.md`
- provenance: HAND (NEW WS-A authoring residue)
- action detail: Provenance references to legacy team files. Conflicts with DoD 'grep-proof no dangling team reference' — decide: allow as historical provenance or rephrase.
- hits (6 lines): 5, 9, 15, 21, 27, 63
  - `editorial-team` @ 5, 9, 15, 21, 27, 63

### `roles/units/material/_NOTES.md`
- provenance: HAND (NEW WS-A authoring residue)
- action detail: Provenance references to legacy team files. Conflicts with DoD 'grep-proof no dangling team reference' — decide: allow as historical provenance or rephrase.
- hits (11 lines): 5, 33, 37, 43, 49, 55, 60, 61, 62, 64, 66
  - `material-team` @ 5, 33, 37, 43, 49, 55, 60, 61, 64, 66
  - `자료팀` @ 62

### `roles/units/plan/_NOTES.md`
- provenance: HAND (NEW WS-A authoring residue)
- action detail: Provenance references to legacy team files. Conflicts with DoD 'grep-proof no dangling team reference' — decide: allow as historical provenance or rephrase.
- hits (6 lines): 6, 9, 17, 24, 30, 38
  - `plan-team` @ 6, 9, 24, 30, 38
  - `기획팀` @ 17

### `roles/units/qa/_NOTES.md`
- provenance: HAND (NEW WS-A authoring residue)
- action detail: Provenance references to legacy team files. Conflicts with DoD 'grep-proof no dangling team reference' — decide: allow as historical provenance or rephrase.
- hits (7 lines): 5, 14, 20, 25, 26, 30, 55
  - `qa-team` @ 5, 14, 20, 25, 30, 55
  - `품질관리팀` @ 26

### `roles/units/research/_NOTES.md`
- provenance: HAND (NEW WS-A authoring residue)
- action detail: Provenance references to legacy team files. Conflicts with DoD 'grep-proof no dangling team reference' — decide: allow as historical provenance or rephrase.
- hits (6 lines): 5, 13, 24, 28, 32, 45
  - `research-team` @ 5, 13, 24, 28, 32, 45

### `tools/fleet/collectors/claude.py`
- provenance: HAND (fleet observability; tools/fleet ↔ adapters/claude/tools/fleet duplicated pair)
- action detail: subagent_type parsing is a generic mechanism (keep); team names appear only as test fixtures/comments. Rename fixtures only if the grep-proof DoD is enforced literally over tests.
- hits (1 lines): 222
  - `subagent_type` @ 222

### `tools/fleet/render.py`
- provenance: HAND (fleet observability; tools/fleet ↔ adapters/claude/tools/fleet duplicated pair)
- action detail: subagent_type parsing is a generic mechanism (keep); team names appear only as test fixtures/comments. Rename fixtures only if the grep-proof DoD is enforced literally over tests.
- hits (1 lines): 1155
  - `plan-team` @ 1155

### `tools/fleet/tests/test_f15_rows.py`
- provenance: HAND (fleet observability; tools/fleet ↔ adapters/claude/tools/fleet duplicated pair)
- action detail: subagent_type parsing is a generic mechanism (keep); team names appear only as test fixtures/comments. Rename fixtures only if the grep-proof DoD is enforced literally over tests.
- hits (2 lines): 437, 440
  - `plan-team` @ 437, 440

### `tools/fleet/tests/test_f29_subagents.py`
- provenance: HAND (fleet observability; tools/fleet ↔ adapters/claude/tools/fleet duplicated pair)
- action detail: subagent_type parsing is a generic mechanism (keep); team names appear only as test fixtures/comments. Rename fixtures only if the grep-proof DoD is enforced literally over tests.
- hits (3 lines): 390, 401, 409
  - `qa-team` @ 390, 401
  - `subagent_type` @ 409

## Appendix — team-adjacent references OUTSIDE the term grep (manually added, all flagged)

These do not match any of the 9 team names or KO display names but contain "team" and must be
explicitly dispositioned so the DoD grep-proof is defined precisely.

### 1. `claude-agent-team-teammate` execution-surface id — DIFFERENT CONCEPT, presumed KEEP
This names Claude Code's native **agent-teams peer-session** surface (peer lifecycle, not dispatch
depth — `utilities/dispatch_contract.py:207`), not one of the 9 runtime team agents. Presumed
**keep unchanged**; confirm at review that the word collision is acceptable under the "teams become
labels" language, or rename the surface id in a separate, self-contained change (it is a wire-level
enum consumed by dispatch contract + fleet collectors + tests).

- `capabilities/topologies.json:1683` (execution_surfaces registry — WS-B owns this file)
- `utilities/dispatch_contract.py:29, 204, 207`
- `utilities/dispatch_contract.test.py:72`
- `utilities/capability_route.test.py:156`
- `tools/fleet/collectors/dispatch.py:133, 215` and `adapters/claude/tools/fleet/collectors/dispatch.py:133, 215` (duplicated pair)
- `tools/fleet/tests/test_v20_dispatch_contract.py:141` and `adapters/claude/tools/fleet/tests/test_v20_dispatch_contract.py:141`
- prose: `core/CONVENTIONS.md:45, 516`, `core/OPERATIONS.md:108` ("Claude agent-team teammate sessions")

### 2. `capabilities/autopilot-code.md:50` — generic-word false positive
"model/team deliberation notes" uses "team" as an ordinary English word. No rewiring needed;
optionally rephrase so a naive `grep team` stays clean.

### 3. DoD grep-proof definition (recommendation)
Define the §6 "no dangling team reference" check as: the 9 exact team-agent names + the 8 KO
display names + `subagent_type=` team literals, excluding (a) `claude-agent-team-teammate` (native
peer-session surface), (b) `roles/units/*/_NOTES.md` provenance IF the review keeps them, (c) git
history. A bare `grep -r team` is not the contract.
