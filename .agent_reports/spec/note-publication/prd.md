# DB-gated note follow-up topology
<!-- BLUEPRINT-SUMMARY:BEGIN -->
- Vision: durable result-producing pipelines publish one Layer 2 note only when the user's remote note DB is live.
- Current shape: `autopilot-note --from <artifact>` remains secondary and last; disconnected or unconfigured DB state is an explicit non-error skip.
- Active decisions: source identity is the upsert key; report refinement updates the same note and preserves user/DB-owned routing fields.
- In-flight cycle: topology registry v6, route sealing, adapter readiness command, portable/adapter contract parity, and deterministic tests.
<!-- BLUEPRINT-SUMMARY:END -->

> Version: 1 · 2026-07-30
>
> Owner: `autopilot-spec`
>
> Scope: note follow-up activation and update semantics. This does not change the user's DB schema, credentials, scheduler, or runtime configuration.

## 1. Problem

The workflow prose calls `autopilot-note` a final secondary step, but the executable
topology does not seal that follow-up. It also treats lab note routing as mandatory
even when the user's note DB is unavailable, while an explicit-source rerun only
implicitly promises update/idempotency. This creates three gaps:

1. result pipelines can finish without a machine-visible note handoff;
2. disconnected users receive a mandatory step that cannot produce the intended DB result;
3. refining the same report can be interpreted as creating a second note or replacing
   user-owned routing state.

## 2. Goals and non-goals

### Goals

- Seal a conditional `autopilot-note` follow-up after the durable terminal of each
  note-eligible entry recipe.
- Require that follow-up only when a read-only live probe confirms the configured
  remote DB server is reachable in the current execution environment.
- Treat missing configuration, local-file fallback, probe timeout, authentication
  failure, or network failure as a typed `unavailable` state that skips the follow-up
  without invalidating the primary result.
- Define same-source update behavior for feedback-driven report revisions.
- Preserve parity across Claude, Codex, and OpenCode without using hooks.

### Non-goals

- No DB migration, credential rewrite, scheduler change, or production deployment.
- No note follow-up for recipes whose primary product is not a supported note source
  (`autopilot-apply`, `autopilot-design`, `autopilot-ship`, `autopilot-spec`). A later
  recipe may opt in only by declaring a concrete source output.
- No nested `autopilot-note` follow-up from `autopilot-note` itself.
- No new dispatch depth. The primary capability owner executes the sealed follow-up
  after its graph; it is not an additional depth-2 worker node.

## 3. Locked decisions

### NP-1 — Readiness is a live remote-DB predicate

The portable predicate is `agent-note-db-connected`. Its command is
`utilities/note-db-readiness.sh --check`. Codex and OpenCode also expose the
same command through `preflight.sh note-readiness --check`; Claude calls the
shared utility directly.

The check:

1. resolves the board app only from `WORKLOG_BOARD_APP`;
2. safely parses only the required DB keys from the board's documented `.env.local`
   and `ops/cron/.agent.env` sources without executing dotenv content;
3. rejects absent `DATABASE_URL` and `file:`/local database URLs;
4. imports the board app's installed libSQL client and executes read-only `SELECT 1`
   with a bounded timeout;
5. prints only a state and closed reason enum, never a URL, token, or exception body.

Exit `0` means `connected`. Exit `69` means `unavailable`. `unavailable` is normal
for conditional topology activation and never changes primary capability success.

### NP-2 — Conditional follow-up is topology metadata

Topology registry schema v6 adds:

- a global `activation_conditions` contract for `agent-note-db-connected`;
- per-recipe `conditional_follow_ups` with exact capability, condition, terminal
  anchors, source-output references, and unavailable behavior;
- route records that realize `after` against the effective direct, quick, or
  standard+ terminal nodes and seal the metadata into `route_hash`.

The initial note-eligible set is:

| Primary | Modes | Note source | Runs after |
|---|---|---|---|
| `autopilot-code` | audit/debug/dev | `report:final_report.md` | `report` |
| `autopilot-draft` | doc/paper/presentation | `finalize:final-artifact` | `finalize` |
| `autopilot-lab` | setup | `full-run:experiment-artifact` | `full-run` |
| `autopilot-lab` | eval | `report:experiment-artifact` | `sync` |
| `autopilot-refine` | default | `transaction:revised-artifact` | `transaction` |
| `autopilot-research` | academic/market/technology | `report:research-artifact` | `claim-verify` |

For direct and quick routes the compiler maps `after` to `inline` and `one-shot`
respectively while preserving the declared standard+ source contract. At execution,
the owner resolves the actual durable artifact path. A missing declared source is
reported as `failed/note-source-unavailable`; it is not disguised as a DB skip and
the owner never invents a path.

### NP-3 — Connected means required; unavailable means skipped

For a note-eligible recipe:

- `connected` + source exists: run `autopilot-note --from <source>` as the last
  owner postcondition and record `created`, `updated`, or `unchanged`;
- `unavailable`: record `skipped/db-unavailable` and finish the primary normally;
- connected probe followed by publication failure: preserve the primary result but
  report `failed/note-publication` explicitly; never claim full note completion;
- user-requested omission does not override the connected-state requirement. The
  connection predicate is the single activation policy.

Standalone user-invoked `autopilot-note` keeps its own capability behavior. NP-3
governs only automatic follow-up cycles.

### NP-4 — Same-source refinement is an upsert, not a second note

`--from` canonicalizes the source path before identity calculation. Reprocessing the
same canonical source:

- preserves note `id`, `source`, and `created_at`;
- preserves DB/user-owned routing and workflow fields unless the user explicitly
  changes them through their owning surface;
- refreshes agent-derived summary, results, decisions, metrics, next steps, source
  revision evidence, `run_id`, and `run_at`;
- returns `unchanged` when the source revision and derived body are unchanged;
- creates a new note only for a different canonical source artifact, not merely a
  new refinement run, snapshot, or temporary path.

`autopilot-refine` must hand off the canonical revised artifact path. Snapshot and
diff-preview outputs are never note identities.

### NP-5 — No hook dependency

Readiness is an explicit preflight/tool contract and the follow-up is route metadata.
Hooks may display reminders but are neither the activation authority nor a correctness
requirement.

## 4. Acceptance criteria

1. Registry validation rejects unknown conditions, self-follow-ups, non-terminal
   anchors, missing source-output references, and any unavailable action other than
   `skip`.
2. Every route intensity seals realized follow-up anchors; tampering is rejected by
   route verification/hash checks.
3. The six note-eligible recipe rows above contain exactly one conditional note
   follow-up; other recipes and `autopilot-note` contain none.
4. Readiness tests cover unset app, absent remote URL, `file:` fallback, dependency
   failure, successful `SELECT 1`, timeout, and secret-safe output.
5. Portable workflow/note/refine/lab contracts and all adapter projections agree
   on the DB gate and same-source update behavior.
6. Generated projection, topology, route, adaptation-boundary, and focused readiness
   tests pass.

## 5. Rollout and rollback

Rollout is additive but route-registry breaking: bump topology schema to v6 and
regenerate projections in one commit. Existing immutable routes remain historical
read-only records. Rollback removes v6 follow-up metadata and restores the v5
validator/compiler together; it must not touch DB or note data.
