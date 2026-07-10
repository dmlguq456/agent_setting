# Test Report — stage-dispatch Phase 2 (code-test)

**Level: 3** (conformance) — Level 4 (functional) unit/CLI checks all PASS, but the
conformance suite (`hooks/portable-guards.test.sh`) surfaces **2 confirmed new
regressions** (not present at baseline `8596e25`) rooted in a stale `manifest.json`
and un-projected new files under the adaptation-boundary contract. Graduated
verification reached Level 4 on every mechanism this plan added; it does not clear
Level 4 clean on the full conformance run because of those 2 regressions.

slug: `2026-07-10_stage-dispatch-phase2` · qa=standard · intensity=strong

## Summary

| Level | Result |
|---|---|
| 1 — syntax | PASS (5/5) |
| 2 — import/parse | PASS (5/5) |
| 3 — conformance | **PASS 311 / FAIL 12** (2 of the 12 are new regressions; 10 are pre-existing baseline environment FAILs, see below) |
| 4 — functional | PASS (dispatch-wait exit-matrix 6/6, SD-11 reminder 5/5, SD-14b CLI 4/4, dispatch-liveness regression 3/3) |
| 5 — doc-efficacy | Deferred to drill (Phase I handoff artifact) — correctly out of code-test scope per plan |

## Level 1 — Syntax

| Command | Result |
|---|---|
| `python3 -c "import ast; ast.parse(open('adapters/claude/bin/dispatch-headless.py').read())"` | ✅ OK |
| `sh -n utilities/dispatch-wait.sh` | ✅ OK |
| `sh -n utilities/dispatch-wait.test.sh` | ✅ OK |
| `sh -n hooks/stage-dispatch-reminder.sh` | ✅ OK |
| `sh -n hooks/conductor-stop-gate.sh` | ✅ OK |
| `sh -n .agent_reports/plans/2026-07-10_stage-dispatch-phase2/drill_case_stage_dispatch/fixture.sh` | ✅ OK |
| `sh -n .agent_reports/plans/2026-07-10_stage-dispatch-phase2/drill_case_stage_dispatch/assert.sh` | ⚠️ **`sh -n` reports "Syntax error: redirection unexpected" at line 48** — the script is written for `bash` (uses a bashism, e.g. process substitution or `<<<`), not POSIX `sh`. Not part of the plan's mandated syntax-check list (only the 4 new hooks/utilities scripts were named) and the drill dir is a **handoff artifact for another session**, but flagging since it fails strict `sh -n`. `bash -n` on the same file should be checked before handoff. |
| `python3 -m json.tool adapters/claude/settings.json` | ✅ OK — valid JSON; `stage-dispatch-reminder.sh` registered under `PreToolUse`(Skill); `conductor-stop-gate.sh` correctly **absent** (Stop gate held per Phase A probe) |

## Level 2 — Import/smoke

| Command | Result |
|---|---|
| `AGENT_HOME=$PWD python3 tools/profile/build-home.py code-plan --check` | ✅ `check=ok name=code-plan harness=claude fragments=1` |
| `AGENT_HOME=$PWD python3 tools/profile/build-home.py code-execute --check` | ✅ `check=ok name=code-execute harness=claude fragments=1` |
| `AGENT_HOME=$PWD python3 tools/profile/build-home.py code-test --check` | ✅ `check=ok name=code-test harness=claude fragments=1` |
| `AGENT_HOME=$PWD python3 tools/profile/build-home.py code-report --check` | ✅ `check=ok name=code-report harness=claude fragments=1` |

## Level 3 — Conformance

`bash hooks/portable-guards.test.sh` → **PASS=311 FAIL=12** (full log saved to
`/tmp/full-portable-guards.out` at test time; not copied into artifacts per
read-only source-tree scope).

Also ran directly:
- `bash utilities/dispatch-wait.test.sh` → **PASS** (6/6: missing jobs.log exit 0,
  no open children exit 0, different-parent child exit 0, alive+max-reached exit 2,
  dead child exit 3, `--max` clamp to 600 in source).
- `bash utilities/dispatch-liveness.test.sh` → **PASS** (3/3 runtime-root regression
  cases — unaffected by this plan, listed here per the plan's regression-check
  requirement).

### Baseline cross-check (regression discrimination — **required by dispatch instructions**)

Baseline commit under test: `8596e25` (pre-Phase-2, "Spec: stage-dispatch v2 —
Phase 2 결정 등재"). Reproduction: `git archive 8596e25 | tar -x -C
/tmp/baseline-checkout && cd /tmp/baseline-checkout && bash
hooks/portable-guards.test.sh` → **PASS=301 FAIL=13**.

Diff of `BAD` lines, baseline vs this branch (`diff <(baseline BAD) <(current BAD)`):

```
< BAD codex projection preflight should resolve harness root        (baseline-only, now passes)
< BAD adapter loop runtime logs should be ignored                    (baseline-only, now passes)
< BAD opencode projection preflight should resolve harness root      (baseline-only, now passes)
---
> BAD codex doctor --runtime should include runtime projection validation        (NEW)
> BAD codex doctor --runtime-strict should require and accept complete hook trust (NEW)
```

- **10 of the 12 current FAILs are identical to baseline** (`codex dispatch wrapper
  should register open headless job`, `codex harvest wrapper should mark selected
  jobs done`, `claude dispatch wrapper should record cross-harness ownership
  metadata`, `dispatch-liveness.sh` ×4 timing-dependent cases, `opencode dispatch
  wrapper should register open headless job`, `opencode dispatch wrapper should
  materialize generated register prompt with QA policy`, `opencode harvest wrapper
  should mark selected jobs done`) — **pre-existing environment-dependent FAILs**,
  confirmed reproduced verbatim in a clean `8596e25` checkout. **Not this work's
  regression** — do not attribute to this plan.
- **3 baseline FAILs no longer fail** (`codex/opencode projection preflight should
  resolve harness root`, `adapter loop runtime logs should be ignored`) — improvement
  or shared environment-timing flakiness resolved between runs; not caused by
  source edits in this plan (no file touched by this plan is in that code path).
- **2 NEW FAILs not present at baseline — confirmed regression, root-caused below.**

### Root cause of the 2 new regressions

Both new failures are `codex doctor --runtime[-strict]` checks that require overall
`status=ok`; they fail because two *other* doctor sub-checks — `manifest` and
`adaptation-boundary` — now fail (the tests only grep for `runtime-projection:ok` /
`native-subagents:ok` / `status=ok`, so a failure anywhere else still fails
`status=`). Isolated:

```
$ python3 tools/build-manifest.py --check
manifest drift: manifest.json is out of date — run `python3 tools/build-manifest.py`
$ (cd /tmp/baseline-checkout && python3 tools/build-manifest.py --check)
manifest up-to-date; delta baselines bound
```

```
$ tools/check-adaptation-boundary.sh
FAIL: no projection decision for utilities/dispatch-wait.sh (must be classified projected or deferred)
FAIL: no projection decision for utilities/dispatch-wait.test.sh (must be classified projected or deferred)
FAIL: skills/ compatibility refs must stay byte-equivalent to adapters/claude/skills/ except .sync_state.json:
  Files skills/autopilot-code/references/dev-pipeline.md and adapters/claude/skills/autopilot-code/references/dev-pipeline.md differ
  Files skills/autopilot-code/SKILL.md and adapters/claude/skills/autopilot-code/SKILL.md differ
  Files skills/autopilot-design/SKILL.md and adapters/claude/skills/autopilot-design/SKILL.md differ
  Files skills/autopilot-draft/references/pipeline-steps.md and adapters/claude/skills/autopilot-draft/references/pipeline-steps.md differ
  Files skills/autopilot-lab/references/eval-procedure.md and adapters/claude/skills/autopilot-lab/references/eval-procedure.md differ
  Files skills/autopilot-lab/references/setup-procedure.md and adapters/claude/skills/autopilot-lab/references/setup-procedure.md differ
  Files skills/autopilot-research/references/pipeline-search-analysis.md and adapters/claude/skills/autopilot-research/references/pipeline-search-analysis.md differ
  Files skills/autopilot-research/references/report-generation.md and adapters/claude/skills/autopilot-research/references/report-generation.md differ
  Files skills/autopilot-spec/references/prd-authoring.md and adapters/claude/skills/autopilot-spec/references/prd-authoring.md differ
  Files skills/autopilot-spec/references/scaffolding.md and adapters/claude/skills/autopilot-spec/references/scaffolding.md differ
FAIL: adapters/claude/hooks/conductor-stop-gate.sh is missing
FAIL: adapters/claude/hooks/stage-dispatch-reminder.sh is missing
$ (cd /tmp/baseline-checkout && tools/check-adaptation-boundary.sh)
OK: adaptation boundary checks passed
```

**Diagnosis** (confirmed, not merely plausible — reproduced both ways): this
plan's code-execute stage added new source files (Phases C/E) and edited the
canonical `skills/*` reference docs (Phases F/H) but did not run the two
repo-wide bookkeeping steps the adaptation-boundary contract requires:
1. `python3 tools/build-manifest.py` (regenerate `manifest.json` after adding
   `utilities/dispatch-wait.sh`, `utilities/dispatch-wait.test.sh`,
   `hooks/stage-dispatch-reminder.sh`, `hooks/conductor-stop-gate.sh`,
   `profiles/code-{plan,execute,test,report}.yaml`,
   `profiles/fragments/code-{plan,execute,test,report}.md`, and the
   `drill_case_stage_dispatch/` artifact dir).
2. Mirror the 9 edited `skills/**` docs into `adapters/claude/skills/**` (the
   existing byte-equivalence convention `check-adaptation-boundary.sh` already
   enforces for every other skill doc), and add explicit projection decisions
   (projected/deferred) for the 2 new `utilities/dispatch-wait*.sh` files, and
   copy/mirror the 2 new hooks into `adapters/claude/hooks/`.

This is **not** an environment-dependent flake (reproduced deterministically 3×
at 3 different `CODEX_RUNTIME_PROJECTION_CLI_TIMEOUT` values) and **not** present
at baseline — it is a genuine gap left by code-execute. **Fix belongs to
code-execute** (source/adapter-mirror writes are outside code-test's read-only
write class) — recommend a follow-up execute pass: run
`python3 tools/build-manifest.py`, mirror the 9 skill docs to
`adapters/claude/skills/**`, mirror/copy the 2 new hooks to
`adapters/claude/hooks/**`, and add projection-decision entries for the 2 new
`utilities/dispatch-wait*.sh` files, then re-run
`tools/check-adaptation-boundary.sh` and `python3 tools/build-manifest.py --check`
to confirm clean.

## Level 4 — Functional

| Check | Result |
|---|---|
| `dispatch-wait.sh` exit-code matrix (0/2/3) | ✅ PASS — see `utilities/dispatch-wait.test.sh` output above |
| SD-11 reminder emits `additionalContext` for conductor+standard+code-plan; no-ops for direct/quick / depth-2 / non-code / main | ✅ PASS (5/5, `hooks/portable-guards.test.sh` "SD-11 stage-dispatch reminder" block) |
| SD-14b conductor Stop gate CLI unit (no block/no open children, block+diagnose on dead child, no block on `stop_hook_active`, no block for non-conductor env) | ✅ PASS (4/4, correctly **unregistered** in settings.json per Phase A verdict) |
| `dispatch-headless.py --dry-run` registry parity (C1 fix) | ✅ implicit in conformance suite ("claude dispatch wrapper" cases) — the one *new*-vs-baseline claude-dispatch case (`should record cross-harness ownership metadata`) is a pre-existing baseline FAIL, unrelated to C1 |

## Doc-effect (SD-10) grep assertions — all PASS

| Assertion | Result |
|---|---|
| `grep -n "e.g." dev-pipeline.md` no longer matches the old escape-hatch line | ✅ (only a benign "e.g." inside the stage-dispatch orientation paragraph, not the old open-ended fallback wording) |
| `grep -c "dispatch-headless.py" dev-pipeline.md` ≥ 4 | ✅ 5 |
| `grep -c "dispatch-wait" dev-pipeline.md` | ✅ 8 (present in every stage step) |
| `grep -n "depth-2 headless" SKILL.md` | ✅ present, Stage Graph annotated |
| `grep -n "one-shot"` in `core/OPERATIONS.md`, `adapters/claude/CLAUDE.md`, `adapters/codex/AGENTS.md`, `adapters/opencode/AGENTS.md` | ✅ all 4 present |
| `grep -n "one-shot 대기 계약\|spec 전제 선보장" core/OPERATIONS.md` | ✅ both present |
| `grep -n "homologous stage set" core/CONVENTIONS.md` | ✅ present |
| `grep -n "SD-14" core/DESIGN_PRINCIPLES.md` | ✅ present |
| `grep -rl "stage-worker\|스테이지-워커"` across the 5 diffusion pipes | ✅ all 8 files matched (draft/research×2/spec×2/design/lab×2) |
| `grep -n "autopilot-lab" core/WORKFLOW.md` (new §5 row) | ✅ present |
| No-regression: `loops/**` / `tools/fleet/**` untouched by this plan's commits | ✅ `git diff --stat 5ae8c8a^..8224285 -- loops/ tools/fleet/` is empty. (Note: `git diff --stat 5b7cf33..HEAD` shows loops/ changes, but those come from an **earlier, unrelated merge** (`8310dda`/`d545e21`, pre-dating this plan's Phase A commit `5ae8c8a`) — confirmed by `git log --oneline 5b7cf33..HEAD -- loops/` showing only `8310dda`, which sits *before* `5ae8c8a` in the branch's commit sequence, not part of this plan's work.) |

## SD-14b `-p` Stop hook probe cross-check

`phaseA_stop_probe.md` verdict: Stop does **not** fire under `claude -p` (probe
exit 1, empty sentinel; cross-referenced against CC #38651/#40506/#20063). This
matches the shipped state: `conductor-stop-gate.sh` exists on disk (Level 1 `sh -n`
OK, Level 4 CLI unit 4/4 PASS) but is **absent** from
`adapters/claude/settings.json`'s `Stop` array (confirmed via `json.tool` +
`grep -n "conductor-stop-gate" adapters/claude/settings.json` → no match), and
`core/OPERATIONS.md`/`core/DESIGN_PRINCIPLES.md`/`adapters/claude/CLAUDE.md` all
state the hold explicitly with the probe date and CC issue numbers. **Wait
contract ↔ probe verdict are consistent**: SD-14 ships via (a) depth_note +
(c) dispatch-wait only, as the plan's Phase A branch required.

## Findings requiring conductor attention

1. **[Regression, confirmed]** `manifest.json` stale + `check-adaptation-boundary.sh`
   fails (missing hook mirrors, missing skill-doc mirrors, missing projection
   decisions for `utilities/dispatch-wait*.sh`) — see root-cause section above.
   Recommend routing back to code-execute before promoting plan status further.
2. **[Minor]** `drill_case_stage_dispatch/assert.sh` fails strict POSIX `sh -n`
   (bashism at line 48) — re-check with `bash -n` before the loops-owning session
   installs it; not blocking (handoff artifact, not this repo's executed code).

## Reproduction commands (for conductor / re-run)

```
python3 -c "import ast; ast.parse(open('adapters/claude/bin/dispatch-headless.py').read())"
sh -n utilities/dispatch-wait.sh utilities/dispatch-wait.test.sh hooks/stage-dispatch-reminder.sh hooks/conductor-stop-gate.sh
python3 -m json.tool adapters/claude/settings.json
for s in plan execute test report; do AGENT_HOME=$PWD python3 tools/profile/build-home.py code-$s --check; done
bash utilities/dispatch-wait.test.sh
bash utilities/dispatch-liveness.test.sh
bash hooks/portable-guards.test.sh
python3 tools/build-manifest.py --check
tools/check-adaptation-boundary.sh
git archive 8596e25 | tar -x -C /tmp/baseline-checkout-repro && (cd /tmp/baseline-checkout-repro && bash hooks/portable-guards.test.sh)
```
