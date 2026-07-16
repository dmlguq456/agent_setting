# Overnight Patrol — Inspection, Evidence Promotion, and Reporting

The on-call report agent inspects and reports. Before it starts, the loop runner
may invoke the D-42 daily memory curator catch-up and write its XDG receipt. The
report agent does not rerun or bypass that curator. Its only mutation is bounded
evidence ingestion through `tools/improvement/proposals.py`; it must not edit,
commit, push, install, activate, or directly write proposal records, source,
generated projections, plugins, runtime config, or memory. Temporary context
and evidence files may be created only to call the guarded inbox CLI and must
be removed before exit. The morning discussion desk under D-26 handles human
decisions. Reversible, unambiguous work may then run unattended with full
disclosure; everything else requires user discussion under D-25 and
`loops/README.md`.

## Checks

1. **Git state:** find repositories with `.git` within depth 3 under `/home/nas/user/Uihyeop`, excluding backups, `node_modules`, and `_layer2*`. For each repository, inspect:
   - an active merge, rebase, or cherry-pick;
   - the dirty-file count;
   - DONE-BRANCH: the current branch is not the remote default branch but is zero commits ahead of it, which usually means the session remained on an already merged branch;
   - prunable worktrees from `git worktree list --porcelain`.
2. **Accumulated minor artifact findings:** if any `*/pipeline_summary.md` under an artifact root—`.agent_reports`, with legacy `.claude_reports` compatibility—contains at least five minor findings since the last audit, recommend `/audit`.
3. **Abandoned experiments:** list entries in `experiments/_RUNLOG.md` still marked ⏳ with no update for at least seven days.
4. **Missing regression drill:** if the newest `<agent-home>` commit is newer than the newest directory under `<agent-home>/loops/drill/results/`, recommend `run.sh --sample 2`. Periodic regression stays light with two random cases; run related cases or the full set only after major behavioral changes such as guard or routing changes. Do not run the drill from on-call. A prose-only wording or heading change may reasonably skip behavioral execution.
5. **Definition and projection drift:** under `<agent-home>`, run `python3 tools/build-manifest.py --check`, the active runtime adapter's `sync-native-* --check`, `tools/check-adaptation-boundary.sh`, and `tools/skill-conformance/check.sh`. Report the check name and first actionable error on failure. README prose requires human review and is not automatically freshness-scored.
6. **Note-loop health and success:** if the latest `=== note run` in `<agent-home>/loops/note.log` is more than 26 hours old, report a likely cron, authentication, or timeout failure. Also inspect its exit state: `=== exit N ===` with nonzero N, or a failure marker such as `401`, `invalid authentication`, `SyntaxError`, `=== FAILED after`, or `=== ABORT:`, is actionable even if the run is recent.
7. **Study-loop health and success:** if the latest `=== study run` in `<agent-home>/loops/study.log` is more than eight days old, report a likely failure for the weekly Sunday job. Apply the same nonzero-exit and failure-marker checks as the note loop. This prevents recurrence of the 2026-06-21 incident in which study failed immediately with 401 but a timestamp-only check missed it.
8. **Dispatch jobs:** list every open entry in `<agent-home>/.dispatch/jobs.log`, the registry defined by `core/OPERATIONS.md §5.10`. Flag a likely orphan when its worktree path no longer exists or the job is older than 24 hours. Flag likely lack of progress when the worktree exists but neither commits nor artifact-root `plans/*/dev_logs` changed in the last 24 hours. Report only; process termination and worktree cleanup require a separate decision.
9. **Daily memory curator receipt:** read
   `${MEM_DAILY_CURATOR_REPORT:-${XDG_STATE_HOME:-$HOME/.local/state}/agent-memory/daily-curator-last.json}`.
   The runner has already used the session-end curator's no-tools worker,
   snapshot/action validator, project gates, graveyard, and mirror sync as a
   catch-up over each project's `(last_success, run_start]` write-event window.
   Report every nonempty action receipt with project path, action, and target ID;
   report failed, overflow, journal-gap, validation, timeout, busy,
   worker-budget, or unsupported-worker phases because
   their project cursor remains unchanged for retry. Say nothing for successful
   no-change projects. Do not rerun the curator or take direct corrective action.
   Session-end remains primary; daily curation is only the D-42 backstop.
10. **Memory-to-proposal promotion:** use recent memory mutations only as
   discovery leads for harness, instruction, loop, or runtime-adapter incidents.
   Run `python3 <agent-home>/tools/memory/mem.py log --limit 100 --json`, apply
   agent judgment to timestamps and content, and select at most one or two
   plausible incidents from roughly the previous 36 hours. For every selected
   ID, run `python3 <agent-home>/tools/memory/mem.py show <id>` and read the full
   body. Type, strength, keywords, and fixed thresholds are not promotion
   rules. Then cross-check the claim against current source, tests, loop logs,
   artifacts, or a local runtime probe. Memory alone is never evidence; omit
   the candidate when live corroboration is absent.

   For a corroborated incident, prepare bounded temporary `context.json` and
   `incident.md` files. Populate every strict context field from current local
   evidence. When official runtime documentation was not checked, say so
   honestly in `docs_fingerprint` (for example,
   `unverified:runtime-watch-required`) rather than inventing freshness. Choose
   one stable, semantic incident identity and run:

   ```text
   python3 <agent-home>/tools/improvement/proposals.py observe \
     --actor loop:oncall --incident-key <key> \
     --title <title> --summary <summary> \
     --context <context.json> --evidence <incident.md>
   ```

   The exact key either creates `observed` or appends recurrence evidence to
   the existing proposal without changing its state. If a bounded, local,
   no-network reproduction is possible without source/runtime mutation,
   transition with `--actor loop:oncall --context <context.json>` to
   `reproduced`; this explicit reproduction is what may rebase a stale
   pre-review proposal. If an inactive invariant, affected source surface,
   rollback, and fixture evidence are also complete, transition to `proposed`.
   Stop there. Do not run headless sessions, drills, network probes, or
   runtime/plugin changes, and never supply `human:*` actors or approval
   references. If recurrence lands on a reviewed or terminal proposal, append
   evidence only and report the unchanged state.
11. **Retired check:** do not scan post-it files with regex. The removed `post-it.md` model is obsolete. Session-end `mem sync` and `mem lifecycle --apply` own working-tier expiration, currently at `WORKING_TTL_DAYS=21`; durable consolidation candidates belong to memory lifecycle reporting rather than an on-call reimplementation.
12. **Complete memory-store diagnosis under D-39:** run `python3 <agent-home>/tools/memory/mem.py doctor`. It performs nine read-only deterministic checks: integrity, FTS consistency, schema invariants, working-tier size, stale pending records, durable soft ceiling, graveyard consistency, dump freshness, and worker health. Say nothing on exit 0. Copy `[WARN]` or `[FAIL]` items into the report on exits 1 or 2. Do not take corrective action; semantic deletion, consolidation, merge, and graduation remain owned by the D-18 curator, with D-42 only adding the guarded daily catch-up already run by the loop runner. This is distinct from the legacy file-index checker `tools/memory/index-check.sh`.
13. **Runtime-watch freshness:** check syntax for `<agent-home>/loops/runtime-watch.sh` and the newest report time under `/home/nas/user/Uihyeop/notes/runtime-watch/`. If no report exists within seven days or a recent runtime-policy change is plausible, recommend `runtime-watch --run`. On-call must not itself run network probes, drills, headless sessions, or policy edits. Route interpretation of official primary sources and policy changes into a separate `autopilot-spec`/`autopilot-code` cycle.

## Drill-Promotion Tags

Tag a reproducible runtime-behavior violation—such as a commit during merge, work on a dead branch, or an artifact without prerequisites—with `[drill promotion candidate]`. Collect tagged entries in a final report section. If the user approves promotion, reproduce the situation as a fixture skeleton under `loops/drill/cases_growing/` with `fixture.sh`, `prompt.md`, and `assert.sh`.

## Report

- Write a concise report to `/home/nas/user/Uihyeop/notes/oncall/<YYYY-MM-DD>.md` in the user's established communication language. Use one or two lines per item, include repository path and branch, and add one recommended action.
- Add an `Improvement proposals` section only when promotion occurred. For each
  item report proposal ID, state, `ingest_result` (`created` or
  `evidence-appended`), live corroboration, and the next human decision. Never
  copy a full memory body into the report.
- Add a `Memory curation` section only when the daily receipt contains applied
  actions or a failure. List every action by project/action/target ID and every
  failed phase; never copy full record bodies.
- Always write the heartbeat file, even when there are no findings. Use an equivalent of `# Overnight Patrol — <date>\nNo anomalies; all 13 checks passed.` in that communication language. A missing file indicates loop failure, not a clean patrol.
- Report facts only. Do not invent numbers or exaggerate; omission is better than a false entry.
