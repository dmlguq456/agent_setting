# Pipeline summary — Codex native subagents in Fleet

## Verdict

**PASS** — Codex native agent threads are projected under their exact parent in
Fleet, actual active→done behavior was observed, and all final gates pass.

## Delivered source changes

Fleet now passively enriches existing Codex sessions with native agent threads
through the shared `Session.subagents` model and existing horizontal strip:

- Reads the newest Codex state DB through SQLite URI `mode=ro` and
  `PRAGMA query_only=ON`.
- Joins `thread_spawn_edges` to child `threads` rows and requires exact,
  unambiguous parent linkage plus matching source JSON.
- Accepts only `thread_source=subagent`; missing/malformed/ambiguous data is
  omitted instead of inferred.
- Uses closed edge status plus validated physical-order child lifecycle.
  `task_started`, `task_complete`, and `turn_aborted` require matching
  `turn_id`; active also requires freshness within 60 seconds. Ambiguity is
  omitted rather than guessed.
- Uses `agent_role` first, then the final native `agent_path` component as the
  label. Nickname is never treated as type.
- Derives the owning runtime home from the already-attributed parent rollout,
  supporting nested/dispatched Codex homes without cross-home attachment.
- Attaches only after exact top-level session attribution; subagents never
  create or suppress `Session` rows.
- Caches by runtime home and DB/WAL/SHM stamp with a short TTL.

Canonical and required Claude mirror files are byte-identical. No Claude
runtime logic was used as a Codex implementation source, and no second subagent
schema or render path was introduced.

## Runtime support, local projection, and gaps

- **Runtime support observed:** Codex 0.144.6 persists exact spawn edges, child
  source metadata, role, rollout path, and task lifecycle. The official manual
  independently establishes agent threads, parent orchestration, `/agent`,
  Active/Done presentation, and custom agents.
- **Local passive projection:** the collector converts only exact persisted
  records into the existing Fleet subagent model. Live before/after snapshots
  show no changes to DB/WAL/SHM, config, or rollout metadata.
- **Remaining gap:** the state DB is an observed local runtime schema, not a
  public cross-version compatibility promise. Schema absence or drift returns
  no enrichment while preserving top-level sessions. A long-running turn with
  no persisted freshness for 60 seconds is omitted, not mislabeled done.

## Verification evidence

- Focused F-29: **43/43 PASS**.
- Codex/Claude/OpenCode attribution, subagent, nested-home, render/JSON, process
  view, and mirror regressions: **113/113 PASS**.
- Full Fleet: **681/681 PASS** in the integrating root environment.
- Canonical↔Claude changed-file byte parity: **PASS**.
- `git diff --check`: **PASS**.
- `python3 tools/build-manifest.py --check`: **PASS**.
- `tools/check-adaptation-boundary.sh`: **PASS** (existing 106-reference
  compatibility warning only).
- Actual native live smoke: **PASS**; `fleet_live_probe` projected active while
  running and done after completion; runtime metadata unchanged in both calls.
- Runtime-semantics reviewer `/root/codex_status_semantics_review`: **PASS**.
- Parser probe `/root/fleet_live_probe`: **PASS**.
- Final independent reviewer `/root/fleet_final_review`: **PASS**, no findings.

Exact commands, timings, outputs, and the residual gap are recorded in
`test_logs/verification.md`; implementation decisions are in
`dev_logs/implementation.md` and `_internal/test_reviews/code-test.md`.

## Pipeline and handoff

- Route `rt-095d82a8da1ac698` completed plan, execute, test, and report bodies
  through route-bound artifacts.
- Registered Codex plan worker returned BLOCKED on sandbox bootstrap; registered
  Claude fallback was synchronously polled and closed `dead-no-progress`.
  Checked dispatch-chain fallbacks selected inline for the durable stage bodies.
- Final synchronous `dispatch-wait.sh` reports no open owner children; harvest
  shows both depth-2 plan attempts and the depth-1 owner row closed.
- Source changes were committed in the isolated branch and integrated into
  `main`; this artifact cycle records the trusted-main verification. No
  runtime-owned file was mutated by the collector.
