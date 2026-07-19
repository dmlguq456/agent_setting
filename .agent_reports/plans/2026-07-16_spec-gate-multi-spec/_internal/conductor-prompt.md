# Assignment — autopilot-code dev/standard conductor: spec-read 게이트 멀티-스펙 인지화

You are the depth-1 capability owner (thin conductor) for one approved autopilot-code cycle.
Load `capabilities/autopilot-code.md` and the owner-execution reference, then run the
`plan → execute → test → report` stage graph. Do not re-select capability, intensity,
or topology (SD-45): they are fixed by the immutable route record below.

## Immutable route binding

- route file: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_spec-gate-multi-spec/_internal/route.json`
- route_id: `rt-603bfc57313d9266`
- route_hash: `sha256:603bfc57313d9266205b20b37dc14d6d001220c26a005276d197e2056bd9913b`
- nodes: `plan → execute → test → report` (all depth 2)
- worktree (cwd, source writes): `/home/Uihyeop/agent_setting-wt/spec-gate-multi-spec` (branch `spec-gate-multi-spec`, base `origin/main`)
- canonical plan root (artifact writes): `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_spec-gate-multi-spec/`
- tracked gate evidence rides in the route record; `spec-significance: within-spec`
  (gate-contract change in `core/`, no `spec/**` PRD mutation; record this line in the plan).

## Task — what to build

Multi-spec awareness for the spec-read gate. Today `hooks/spec-skill-gate.sh` demands only
the root `<artifact-root>/spec/prd.md` and `hooks/spec-read-marker.sh` records markers only
for that path, so in a multi-spec repo (root PRD + `spec/<slug>/prd.md` sub-specs) a session
that read the *governing* sub-spec is still denied and is pushed to read an unrelated root
PRD for formal compliance (observed 2026-07-16, fleet work vs Unified Memory root PRD).

Scope, five surfaces:

1. `hooks/spec-read-marker.sh` — also record markers for one-level sub-spec reads
   `*/.agent_reports/spec/<slug>/prd.md` (and legacy `*/.claude_reports/...`).
   Exclude any path with an `_internal` segment (`spec/<slug>/_internal/versions/...` never counts).
   Marker filenames: root spec keeps the exact existing name `${sid}__${key}` (backward
   compatibility with live markers and the plugin mirror); sub-spec uses `${sid}__${key}__${slug}`.
   Keep the existing canonicalization through `utilities/artifact-root.sh` (worktree → primary
   canonical root) and keep storing prd mtime at read time.
2. `hooks/spec-skill-gate.sh` — candidate set = root `spec/prd.md` plus each existing
   `spec/<slug>/prd.md` (one level, `_internal` excluded). Gate passes when ANY candidate has a
   session marker whose recorded mtime is >= that candidate's current mtime (per-spec drift
   check). Fail-closed is preserved: no fresh marker for any candidate → deny. The deny message
   must list the concrete candidate prd.md paths ("read the one governing the declared work
   scope") and keep the existing "a quotation does not satisfy the gate" and drift-retry wording.
   Single-spec repos must behave byte-for-byte like today from the caller's perspective.
   Which candidate *governs* stays agent judgment + route-record `spec_read.source` (SD-45);
   the deterministic gate only enforces "actually read a current spec of this project".
3. Core-first contract sync — update `core/HOOKS.md` (spec read gate row) and
   `core/WORKFLOW.md` §7.0 ("Reading `prd.md` is a hard gate…") so the portable contract says
   the gate keys on the governing spec candidates (root or sub-spec) with same-session
   freshness. Minimal wording deltas, English, edit core before hooks in the commit narrative.
4. `hooks/portable-guards.test.sh` — add multi-spec scenarios: sub-spec read → gate passes;
   `_internal/versions/**/prd.md` read → no marker, gate still denies; no read → deny and the
   message lists all candidates; sub-spec drift (prd touched after read) → deny until re-read;
   root-only repo → behavior identical to current expectations (no regression);
   legacy `.claude_reports` variant for the sub-spec path.
5. Claude plugin mirror — resync
   `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/hooks/{spec-read-marker.sh,spec-skill-gate.sh}`
   through the repo's generator (`adapters/claude/bin/sync-native-plugin.py`) so mirror stays
   byte-consistent; `hooks.json` command strings (env-prefix) stay unchanged.

Explicitly OUT of scope (do not touch): gate firing-point relocation (Skill entry → mutation
surface), codex/opencode preflight *write*-gate sub-spec patterns, SD-45 route-record schema,
any `spec/**` PRD edit, and `.dispatch/` broker internals.

Adjacent surfaces to keep green (verify, don't redesign): `tools/build-manifest.py`,
`tools/check-adaptation-boundary.sh`, codex/opencode `preflight.sh read|route|gate` paths that
invoke the same canonical hooks via CLI — they must keep passing with the new behavior.

## Hard operational constraints

- Run `hooks/portable-guards.test.sh` and any guard suites ONLY inside the task worktree.
  Never run them against the primary checkout `/home/Uihyeop/agent_setting` — a guard run on
  primary rotates the live dispatch broker (실측 2026-07-15).
- Source edits happen only in the task worktree; plan/dev/test/report artifacts go only to the
  canonical plan root above (`AGENT_ARTIFACT_ROOT`), never to the worktree's `.agent_reports/` snapshot.
- Do not merge or push to `main`; depth-0 main harvests and integrates. Committing on the task
  branch inside the worktree is expected (safety commit + implementation commits).

## Stage dispatch mechanics

For each node, in order, dispatch a depth-2 headless stage with:

```bash
python3 /home/Uihyeop/agent_setting/utilities/dispatch-node.py \
  --route /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_spec-gate-multi-spec/_internal/route.json \
  --node <plan|execute|test|report> --adapter <claude|codex> --action start \
  --slug spec-gate-multi-spec-<stage> --parent spec-gate-multi-spec --qa standard \
  --prompt-text "<stage contract: sub-skill name + absolute input paths + output contract + intensity standard + slug>" \
  -- --model-role "<node role from route>"
```

- Model roles: plan=`deep maker`, execute=`fast implementer`, test=`deep reviewer`, report=`fast writer`.
- Harness: default claude children; prefer `--adapter codex` for the `test` node when
  `utilities/usage-check.sh` reports codex ok (checker from a different model family).
- After each dispatch, poll in the same turn with
  `sh /home/Uihyeop/agent_setting/utilities/dispatch-wait.sh --parent spec-gate-multi-spec`
  until exit 0 (exit 2 → poll again; exit 3 → diagnose via transcript/log tails, then redispatch
  from existing artifacts). Then flip the harvested row `open → done` in jobs.log, and write the
  completion marker before the next stage:
  `python3 /home/Uihyeop/agent_setting/utilities/capability-route.py complete --route <route.json> --node <id> --evidence <stage terminal artifact>`.
- Stage prompts carry absolute paths only — no plan bodies, no prior-stage conversation.
- Concurrency: this pipeline is sequential; conductor + one active stage.
- code-test verdict FAIL → one bounded retry per dev-pipeline Step 4 (safety-commit restore,
  memo, one code-refine, redispatch execute+test). Second failure → rollback, failed
  pipeline_summary, stop before report.

## Completion

Write `pipeline_summary.md` (§5.8 lock for shared singletons) at the plan root before finishing.
Final output exactly three lines:

```
artifact: /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_spec-gate-multi-spec/final_report.md
verdict: PASS | FAIL | BLOCKED
blocker: none | <one line>
```
