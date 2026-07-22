# tools/memory — Unified Memory System (`mem`)

Portable storage and retrieval layer. The specification lives at
`<artifact-root>/spec/prd.md` (`.agent_reports` first, with legacy
`.claude_reports` compatibility).

## Boundary

Short-lived post-its, durable learned memory, and the global profile share one
SQLite store. The acting agent decides contextually what to store, retrieve,
promote, merge, or prune. Code owns mechanical integrity, scope isolation,
pending protection, lifecycle execution, bounded telemetry, and recovery.
`memory.db` is the source of truth; `dump.jsonl` is its text mirror.

## Storage layout

| Layer | Location | Git | Purpose |
|---|---|---|---|
| Source of truth | `<agent-home>/memory/memory.db` (SQLite WAL) | ignored binary | `records`, FTS5 `unicode61`, and the CJK bigram shadow index |
| Git mirror | `<agent-home>/memory/dump.jsonl` (one ID-sorted record per line) | tracked in the memory repository | deterministic text export and exact `mem import` recovery source |
| Harness projection | `<agent-home>/projects/<cwd>/memory/` | ignored | compatibility surface for stray auto-memory writes absorbed by `mem sync`; `mem project` can rebuild the projection |

A record combines `tier` (`working|durable`), `scope` (`project|global`),
`type`, and `delivery_state` (`ordinary|pending|consumed`). Working records have
a finite lifecycle; durable records persist until an agent chooses another
action. New `handoff` records and threads created with `--requires-consume`
start pending and remain protected from destructive operations until explicit
consumption. FTS5 and CJK bigram-shadow data live inside `memory.db`, not in a
separate `.index.db` file.

## Commands

Run commands as:

```text
python3 <agent-home>/tools/memory/mem.py <command>
```

| Command | Behavior |
|---|---|
| `add <tier> <type> "<body>" [--scope] [--tags] [--links] [--source] [--requires-consume]` | Add a record after mechanical validation, deduplication, and injection-safety checks. `handoff` or `--requires-consume` starts pending. |
| `note "<body>" [--type] [--requires-consume]` | Shorthand for a working record. Use `--requires-consume` for delivery-bearing threads. |
| `recall "<query>" [--tier] [--scope] [--all] [--sessions] [--full] [--limit 1..100] [--no-touch]` | Explicit retrieval with FTS5/BM25, ranked CJK bigram substring matching, LIKE last-resort fallback, and optional raw-session search. Default limit is 20; `--full` replaces snippets with complete bodies. |
| `show <id> [--all]` | Show one visible record with metadata and full body. The default fence is current project plus global; flagged or invisible IDs return a generic not-found result. |
| `consume <id>` | Move a pending handoff/thread to consumed. Retrieval and injection never consume records implicitly. |
| `restore <id>` | Restore one record from the graveyard while preserving action/canonical metadata. |
| `index [--rebuild]` | Rebuild the FTS5 tables embedded in `memory.db`. |
| `export [--target dump\|profile] [--apply]` | Export `dump.jsonl` or an on-demand human-readable profile cache. Profile export is dry-run unless `--apply` is supplied. |
| `import <dump.jsonl>` | Recreate the DB exactly from a dump: delete existing records, replay the mirror, and rebuild FTS in the same connection. |
| `project [--cwd]` | Build the compatibility projection. Session context uses `inject`, not this command. |
| `migrate [--apply]` | Idempotently migrate legacy auto-memory, post-it, and Markdown source files. Dry-run by default. |
| `lifecycle [--apply]` | Apply working expiry and expose durable duplicate/capacity candidates. Pending delivery records remain protected. |
| `stats` | Print a grouped store snapshot. |
| `log [--limit 20] [--action] [--tier] [--actor] [--json]` | Read the bounded write-event timeline (D-38), complementing the `stats` snapshot. |
| `doctor` | Run nine read-only checks covering integrity, FTS/schema invariants, working growth, stale pending, durable capacity, graveyard/dump consistency, and worker health. Exit 0 is clean, 1 is WARN, and 2 is FAIL. |
| `inject [--hook]` | Build bounded SessionStart context from working, durable, and profile records. Defaults to 2,000 characters and 15 bullets; `--hook` emits `additionalContext` JSON. |
| `sync` | Absorb stray projection writes, rebuild FTS5, re-export `dump.jsonl`, and append one PLAIN auto-sync commit at SessionEnd (git failures print a one-line stderr warning; sync stays non-fatal). |
| `maintenance [--squash-days 14] [--apply]` | Operator-run compaction for the plain-commit dump history: squash first-parent auto-sync commits older than N days into one root, then `git gc`. Dry-run by default; never pushes (a mirror needs an explicit force-push afterwards). |
| `distill <sid> [--advance]` | Print normalized transcript text after the shared session marker and optionally advance that marker. |
| `curate-snapshot` | Print a read-only current-project snapshot, mechanical signals, and destructive `IDS:` membership. Pending records appear under `PROTECTED PENDING` but never in destructive IDs. |
| `curate-artifacts` | Print read-only git, plan, and spec evidence for the curator agent. |
| `promote-candidates` | Print a bounded view of visible durable records for agent-owned institutionalization review. Type and strength are metadata, not semantic gates. |
| `reinforce <id>` | Increment strength and update access time within the current-project whitelist. |
| `merge --canonical <id> <ids…>` | Merge records into the canonical ID and graveyard the rest. Any pending member cancels the operation atomically. |
| `prune <id>` | Delete only after a successful `deleted-records.jsonl` backup. Pending records are rejected before consumption. |
| `delete <id> [--force]` | User-initiated single-record deletion. Pending records require prior consumption or explicit `--force`. |
| `graduate <id> [--to durable]` | Move a whitelisted working record to durable. |
| `reattribute <id>` | Reassign a true orphan to the current project without deleting it. Reverse gates reject live, global, profile, or self targets. |
| `register-postit <path>` | Deprecated legacy-migration-only registry command. Current post-its write DB working records directly. |

## Curator safety invariant (D-18/D-35/D-40)

The distiller model never invokes mutation commands directly. A no-tools worker
emits action JSON, and `tools/memory/apply-distill-actions.py` parses the shape,
checks snapshot membership, and calls `mem.py` with argv-only values. Each
command also enforces its own project whitelist. Pending records are protected
both in snapshot membership and through a transaction-time DB check. Prune,
merge, and delete retain recoverable graveyard data.

These safeguards validate operations; they do not decide meaning. Main agents,
distillers, and curators make contextual decisions about whether any action is
useful. Keyword lists, fixed phrases, content categories, record types, scores,
and confidence thresholds never substitute for that judgment.

## Retrieval boundary (D-40)

- `show`, explicit recall/full, and SessionStart injection do not consume a
  handoff. Explicit recall/show update `last_accessed` unless `--no-touch` is
  supplied. Source upsert/body dedup never lowers pending to ordinary.
- Prompt-submit hooks do not classify every prompt. An agent chooses when prior
  context may help and then invokes `recall.sh` or `mem recall`.
- FTS/BM25 ranking, CJK/identifier tokenization, scope fences, and limits
  organize results after an agent has chosen a query.
- Retrieval telemetry stores no raw prompt and distinguishes `explicit-recall`,
  `show`, `session-inject`, and `consume`.
- Telemetry defaults to
  `$XDG_STATE_HOME/agent-memory/recall-events.jsonl` (fallback:
  `~/.local/state/agent-memory/`) outside the memory Git mirror.
  `MEM_RECALL_EVENTS` overrides the path.

## Write telemetry and diagnostics (Cluster J)

- Every mutation appends one bounded `write-events.jsonl` entry with
  `ts/action/id/tier/scope/type/actor/sid/snippet`. Rotation keeps at most the
  recent 500 lines within a 256 KiB bound. This local telemetry is not mirrored.
- Journal precedence is `MEM_WRITE_EVENTS`, then a path beside an overridden
  `MEM_STORE`, then `$XDG_STATE_HOME/agent-memory/write-events.jsonl`.
- Telemetry is fail-open; a logging failure never blocks a mutation. Graveyard
  recovery remains fail-closed because it protects destructive actions.
- Actor precedence is explicit `MEM_ACTOR`, distiller context, operation-specific
  defaults, then `manual`. Curator application sets `MEM_ACTOR=curator`.
- `mem log` is a timeline and complements rather than replaces `stats`.
- `mem doctor` is read-only. Its findings are evidence for an agent; it does not
  automatically consolidate, merge, graduate, or delete records.

## Environment overrides

- `MEM_STORE` controls both `memory.db` and `dump.jsonl` location.
- `MEM_PROFILE` controls the human-readable profile export directory.
- `MEM_INJECT_MAX_CHARS`, `MEM_INJECT_MAX_BULLETS`,
  `MEM_INJECT_MAX_WORKING`, `MEM_INJECT_MAX_DURABLE`,
  `MEM_INJECT_CLEANUP_LINES`, and `MEM_INJECT_SNIPPET_CHARS` tune bounded
  injection budgets. Defaults are 2,000 characters, 15 bullets, 8 working,
  4 durable, 2 cleanup lines, and 100 characters per snippet.
- `MEM_DISTILL_ENABLE=1` enables background distillation. It is opt-in because
  it spends model capacity and sends potentially untrusted transcript data to
  a no-tools worker. Adapter-native settings own runtime enablement.
- `MEM_DISTILL=1` prevents recursive distillation lifecycle launches.
- `MEM_DISTILL_WORKER` selects an adapter-owned executable with contract
  `<worker> <mode> <model> <prompt-file>` and JSON-lines stdout.
- `MEM_DISTILL_MODEL` selects the portable model role; concrete defaults belong
  to adapter realization documents.
- `MEM_WRITE_EVENTS`, `MEM_ACTOR`, and `MEM_SID` override telemetry metadata.
- The retired `mem-recall-inject.sh` remains only as a silent compatibility
  no-op for stale installed projections.

## Operational contract

- Schema v6 stores 16 record columns, including `delivery_state`, plus embedded
  FTS5 and CJK bigram-shadow tables (v6 re-normalized legacy `cwd_origin` keys).
- `dump.jsonl` is ID-sorted with `sort_keys=True`, one record per line, and
  explicit JSON `null` values. `mem import dump.jsonl` performs exact recovery.
- SessionStart injection may remain adapter opt-in when start events repeat on
  resume or compact. SessionEnd uses `mem sync`; optional distillation exits
  early on empty delta and spawns detached so it does not block lifecycle hooks.
- `recall.sh` is a thin wrapper over explicit `mem recall`.
- `register-postit` and `.postit-roots` exist only for legacy Markdown migration.

`index-check.sh` remains a separate checker for the legacy
`projects/*/memory/MEMORY.md` text index. Store search indexes are owned by
`mem index` inside `memory.db`.
