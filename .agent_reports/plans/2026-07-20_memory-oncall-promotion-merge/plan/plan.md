# Memory on-call proposal promotion — selective integration plan

> capability: `autopilot-code` (`autopilot-spec` secondary) · mode:
> `dev/refactor` + `update` · intensity: `strong` · QA: `standard`
> · source: `f9aba3969bca3de6b668972f3819d36cfc614165`
> · target: `origin/oncall-proposal-promotion`

## Outcome

Strictly review the two target commits as independent change sets. Integrate only
the incident-to-proposal bridge from `8ceb3cbd`, rebased onto the current memory
and self-improvement contracts. Reject `35a0c75d` as an archive-only experiment.
Finish with a merge commit on `main`, push, and consume the pending handoff only
after all contract and regression checks pass.

## Review verdict by commit

### `8ceb3cbd` — select and adapt

The useful invariant is narrow: on-call may turn a live-corroborated incident
into a proposal-inbox record keyed by one exact stable `incident_key`.
Recurrence appends bounded evidence under the inbox lock instead of multiplying
records. The loop's highest autonomous state remains `proposed`; it never edits
source, generated projections, runtime config, or activation state.

Do not cherry-pick the commit mechanically. Its root memory PRD was based on an
older snapshot and reused D-41, which now names the global distill cost boundary.
Port the behavior onto current `main` as D-43 and update the dedicated
self-improvement-governance PRD from v1 to v2.

Implementation corrections required while porting:

1. Require a single-line, bounded incident key for every named automated
   collector (`actor` beginning with `loop:`).
2. Keep exact-key lookup and create/append under the same store lock; reject
   ambiguous duplicate keys rather than choosing a record.
3. Limit automatic collector transitions to `observed`, `reproduced`, and
   `proposed`. Human approval requirements and all later states remain unchanged.
4. Require a current context when a named collector records `reproduced`, and
   rebase only that collector path. Preserve the pre-existing manual transition
   semantics for other actors.
5. Append bounded evidence/history and preserve the proposal state, approval
   provenance, and stored base on recurrence unless the explicit reproduced
   transition performs the allowed pre-review rebase.
6. Keep the on-call prompt read-only with respect to memory and source:
   `mem log` is candidate telemetry only; inspect full bodies with `mem show`,
   corroborate against live artifacts, then call the offline proposal CLI.

### `35a0c75d` — reject

Do not integrate any source or spec from this commit.

- It renames D-42 to an automatic daily curator even though current D-42 is the
  main-session-only lifecycle boundary.
- It launches memory curation from an on-call worker, directly violating the
  rule that loops/workers never run automatic memory lifecycle.
- Its defaults allow eight workers, exceeding the current D-41 hard maximum.
- It can run full mirror sync for up to 200 repositories, creating the exact
  multi-session amplification D-41 exists to prevent.
- Journal read errors and missing/truncated watermarks can advance cursors and
  lose events; validation and apply are not transactional, so a failed action
  can leave partial mutations that are retried inconsistently.
- It hard-codes a user-specific path and Claude worker surface into portable
  behavior.

The archive commit remains reachable on its remote branch as historical
evidence; no content from it is needed for this merge.

## Spec transaction

Use the shared pipeline lock and update both governing specs in one transaction:

1. Snapshot root memory `prd.md` v19 to `_internal/versions/v19/prd.md`, then
   add v20 / D-43 without changing D-40, D-41, or D-42.
2. Snapshot self-improvement-governance v1 to its
   `_internal/versions/v1/prd.md`, then publish v2 with the exact-key on-call
   bridge, live-corroboration rule, recurrence semantics, and `proposed` ceiling.
3. Keep both pipeline states `phase: implemented`, `status: complete`; update
   timestamps, resume guidance, and summaries consistently.

## Source integration

Port the selected diff into:

- `tools/improvement/proposals.py`
- `tools/improvement/tests/test_proposals.py`
- `loops/oncall.md`
- `loops/README.md`
- `core/MEMORY.md`
- `core/DESIGN_PRINCIPLES.md`
- `harness-manifest.json`
- generated Claude/Codex/OpenCode projections only through the repository's
  canonical projection/generation path

Before each edit, run the applicable write/core/spec preflight. Avoid the target
branch's stale root-spec snapshots and all daily-curator files.

## Verification

Run, through `preflight.sh verification-runner`, at minimum:

1. proposal unit/regression tests, including concurrent recurrence, duplicate-key
   ambiguity, bounded history/evidence, terminal-state recurrence, missing
   context, and manual-actor compatibility;
2. loop/on-call contract tests;
3. memory contract and core/adaptation boundary tests;
4. manifest/generated projection checks;
5. runtime projection/activation checks that are read-only with respect to
   runtime-owned config;
6. full relevant repository regression selected by the existing test scripts.

Also inspect the final diff against `origin/main` and assert that no
daily-curator source, hard-coded runtime path, credential/session/cache/database,
or unrelated Fleet change is present.

## Integration and delivery

Commit the selected implementation on the task branch. Re-fetch `origin/main`;
if it moved, rebase or fast-forward safely and rerun affected tests. Merge with
`--no-ff` into `main`, verify the merge result, push `origin/main`, and run
`preflight.sh worktree-cleanup --check` before cleanup. Consume
`handoff_handoff-oncall-proposal-promotion_c634cc` only after the pushed merge
contains the verified result.

## Failure policy

Stop before merge/push on any ambiguous semantics, stale spec transaction,
projection drift, runtime-owned mutation, failing regression, or target-branch
content outside the selected `8ceb3cbd` behavior. Preserve evidence in this
cycle directory and leave the pending handoff unconsumed.
