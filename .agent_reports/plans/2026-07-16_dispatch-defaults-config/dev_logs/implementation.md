# dispatch-defaults-config — code-execute dev log

worktree: /home/Uihyeop/agent_setting-wt/dispatch-defaults-config
baseline: 3ebd1c77 (spec v16 §13.8 SD-66)
commits produced: efeab72e (core-first safety/contract), 7697c3b6 (implementation)

## What changed

### Commit 1 (efeab72e) — core-first safety/contract
- `core/OPERATIONS.md` §5.10 SD-16: added the sentence declaring
  `profiles/dispatch-defaults.yaml` the user-declared source for SD-22
  cascade step 3 (stage affinity) — explicit choice + hard eligibility
  always win, orchestrator deviation requires a recorded reason (soft
  default, never a pin), unspecified cells stay discretionary.
- `core/OPERATIONS.md` SD-48: added the required no-reconfirmation sentence
  for manual `--start` plus the HEAD-truth caveat that `dispatch-node.py
  --action start` does not yet forward `route.dispatch_evidence`.
- `loops/drill/cases_growing/g9_cross_harness_depth2_dispatch/assert.sh`
  (+ byte-identical `adapters/claude/...` mirror): relaxed the depth-1
  OWNER row's `parent_sid` assertion to a well-formed-SID check
  (`[A-Za-z0-9_.:-]+`, non-empty) instead of exact `drill-parent-session`
  equality, in both the wrapper-row `expect()` block and the fleet-collector
  `fleet_owner` filter. Both depth-2 CHILD rows still assert exact
  `drill-parent-session` equality, unchanged.
- `prompt.md` (+ mirror): added one line explaining the owner is
  intentionally rebound to the real Codex thread id at launch, so only the
  format is checked for that row.
- Did **not** run the g9 drill (out of scope this cycle); only `bash -n`,
  targeted Python-heredoc syntax checks (`ast.parse` on the extracted
  second heredoc), `cmp` for mirror byte-identity, and
  `git diff --check` were run.

### Commit 2 (7697c3b6) — implementation
- `profiles/dispatch-defaults.yaml` (new): narrow schema
  (`schema_version`, `depth1_owner`, `opencode.relief_only`,
  `capabilities.<cap>.<stage>`). Populated only `autopilot-code`:
  `execute: codex`, `test: diverse`, `report: claude`; `plan` intentionally
  omitted. `depth1_owner: [claude, codex]`. `opencode.relief_only: true`
  with a 1-2% relief-target comment. All other registered
  capability/stage coordinates from `capabilities/topologies.json` are
  present only as a commented scaffold (parse-neutral, not empty keys).
- `utilities/dispatch-defaults.py` (new): standard-library-only YAML-subset
  parser (comments, 2-space-indent mappings, inline lists, scalars — no
  PyYAML/yq) plus a CLI: `validate`, `affinity --capability --stage`,
  `owners`, `opencode-policy`. Validates against the canonical node ids
  unioned from every `capabilities/topologies.json` recipe; fails loud
  (nonzero + stderr) on unknown top-level/opencode keys, missing/non-int
  `schema_version`, non-concrete/duplicate `depth1_owner` entries,
  `opencode.relief_only != true`, unknown capability, unknown stage for a
  known capability, and any affinity value outside
  `{claude, codex, opencode, diverse}` (so model-like values such as
  `gpt-5.4-mini` are rejected). `DISPATCH_DEFAULTS_CONFIG` env var or
  `--config` overrides the production path for fixtures.
- `utilities/dispatch-route.sh`: wired the config in **without** changing
  the existing cascade order. New order: explicit `--adapter` >
  `--family` > validated config affinity > existing
  stage-heuristic/capacity-bias fallback > hard-eligibility
  reject/fallback (unchanged). The script now unconditionally runs
  `dispatch-defaults.py validate` before any routing decision, so a
  malformed config fails loud even when an explicit `--adapter` would
  otherwise fully decide the call. A config cell resolving to `opencode`
  is honored only when the caller left `--adapter`/`--family` unset (explicit
  choice still outranks config), and is routed through the existing
  `status=unknown`/opencode early-exit branch — opencode is never added to
  the automatic neutral/diverse candidate set. `--capability` (already an
  accepted but previously-unused flag) is now the capability key for the
  config lookup.
- `utilities/dispatch-route.test.sh`: converted to temporary
  `DISPATCH_DEFAULTS_CONFIG` fixtures. Preserved every original assertion
  (role-only cases, explicit adapter/family, explicit opencode, hard
  eligibility + fallback, exact trace/model-mapping strings, jobs-log
  non-mutation, read-only behavior) and added: configured-value-honored,
  omitted-cell-neutral, diverse-via-config resolved against maker family,
  config-beats-bias precedence, explicit-adapter/family-beats-config
  precedence, hard-eligibility-still-wins-over-config, explicit-opencode-
  config-cell routing (only when adapter/family unset), opencode-excluded-
  from-automatic-candidates, `depth1_owner`/`opencode-policy` queries, and
  one malformed-fixture case per failure class (model-like value, unknown
  capability, unknown stage, malformed owner set, invalid relief policy) —
  each asserted nonzero exit + non-empty stderr from both
  `dispatch-route.sh` and `dispatch-defaults.py validate` directly.

  Incidental fix noticed while rewriting: the original
  `HARNESS_CAPACITY_BIAS=codex route --stage report` line relied on a
  dash/POSIX-sh quirk where an env-var prefix on a *shell function* call is
  not exported to external commands the function invokes — that assertion
  was silently failing at baseline HEAD too (confirmed via `git stash`;
  baseline `sh utilities/dispatch-route.test.sh` also exits 1). The
  converted test now invokes `dispatch-route.sh` directly with the env
  prefix for that one assertion, which is genuinely exported. This is a
  pre-existing, unrelated portability bug incidentally fixed by the
  fixture-conversion rewrite, not a reimplementation of any tracked fix.

## Out of scope, not touched
- `capability-route.py` compile/topology wiring.
- Broker remnants / Fleet UI.
- `dispatch-node.py` route-evidence forwarding (documented as a follow-up
  in the SD-48 sentence added this cycle).
- Re-running the g9/g10 drills.
- The nested-dispatch-eligibility `auth_check` stderr fix (already merged;
  confirmed still present, not duplicated).

## Verification run in this stage (see dev_logs, all from this worktree)
- `sh -n utilities/dispatch-route.sh` — OK
- `sh -n utilities/dispatch-route.test.sh` — OK
- `bash -n loops/drill/.../g9_cross_harness_depth2_dispatch/assert.sh`
  (root + `adapters/claude` mirror) — OK
- `cmp` root vs. `adapters/claude` mirror for `assert.sh` and `prompt.md` —
  byte-identical, both before and after edits
- `python3 -m py_compile utilities/dispatch-defaults.py` — OK
- `python3 utilities/dispatch-defaults.py validate` (shipped config) —
  valid
- `python3 utilities/dispatch-defaults.py affinity --capability
  autopilot-code --stage {execute,test,report,plan}` →
  `codex`, `diverse`, `claude`, `neutral` respectively
- `python3 utilities/dispatch-defaults.py owners` → `claude,codex`
- `python3 utilities/dispatch-defaults.py opencode-policy` → `relief-only`
- 5 malformed fixtures (model-like affinity value, unknown capability,
  unknown stage/literal `exec`, malformed owner set [duplicate + `diverse`],
  invalid relief policy) — each fails with exit 65 and a specific stderr
  message, verified manually and re-asserted inside
  `dispatch-route.test.sh`
- `sh utilities/dispatch-route.test.sh` — `dispatch-route: PASS`, run 4x
  in a row for stability
- `python3 -B utilities/nested_dispatch_eligibility.test.py` — `OK`, 4
  tests, including `test_nested_auth_probe_runs_inside_checked_worktree`
  (confirmed present, not duplicated — this is the Test-stage gate's
  regression to own, not re-implemented here)
- `git diff --check` (all changed files, both commits) — clean
- `git status --short` — clean after each commit; no writes outside
  `source/**`, `checklist.md`, and this `dev_logs/**`/`_internal/**` scope
- No writes to `/home/Uihyeop/agent_setting` (primary checkout) or to the
  worktree's own `.agent_reports/**` snapshot at any point

## Note for the Test stage (not this stage's gate)
I ran the live nested-headless probe once, out of curiosity while
confirming the regression suite (`python3
utilities/nested-dispatch-eligibility.py --parent-harness claude
--parent-transport headless --parent-sandbox adapter-default
--child-harness codex --launch-authority conductor --worktree "$PWD"
--json`, using this session's actual `AGENT_DISPATCH_CURRENT_TRANSPORT`/
`AGENT_DISPATCH_CURRENT_SANDBOX`). It returned `status=unsupported`
because this task worktree's `codex_setting/*` runtime-projection symlinks
are not wired up (`agent-harness`, `AGENTS.md`, skill/agent links, etc. all
report `failed reason=expected-symlink-to:...`). Recording a fresh
`status=supported` probe per plan.md item 6 / checklist.md's "Test-stage
gate" section is that stage's completion gate, not code-execute's — this
log only preserves the raw evidence (`probe_time:
2026-07-16T13:00:19.404077Z`, `probe_source: direct-headless-check`) so
the test stage does not have to re-derive it blind. This stage's own gate
(preserving the existing regression test unduplicated) is met; the
symlink/runtime-projection state itself was not touched — out of scope
under "do not reimplement... already merged" / "do not wire config into
capability-route.py".

## Verdict
PASS — plan items 1, 3, 4, 5 fully implemented and verified from this
worktree; item 2 (g9 repair) fully implemented and verified without
running the drill (as instructed); item 6 correctly deferred to the Test
stage per plan.md's own stage assignment. No merge, no push, no g9/g10
drill run, no primary-checkout or worktree-report-snapshot writes.
