# Memory — Unified Store (canonical)

> Split from `CONVENTIONS.md` on 2026-06-23. Memory is an independent subsystem. Preserve the §7 numbering. This is the single source; the spec is `<artifact-root>/spec/prd.md` (`.agent_reports` first, with legacy `.claude_reports` compatibility), and the implementation is `tools/memory/mem.py`.

## §7. Unified Memory System

> Three former memory surfaces—short-lived post-its, durable learned memory, and the global user profile—share **one portable store**. The store is infrastructure, not a semantic policy engine. **The agent decides contextually what is worth storing, retrieving, promoting, merging, or pruning.** Deterministic code owns only mechanical concerns such as schema validity, scope isolation, lifecycle execution, pending protection, bounded I/O, telemetry, and recovery. Behavioral rules belong in the runtime bootstrap, `CONVENTIONS`, `WORKFLOW`, or Skills rather than memory.

### §7.0. Store Architecture

- **Store:** `<agent-home>/memory/memory.db` is the SQLite WAL source of truth with built-in FTS5. `dump.jsonl` is its deterministic, git-tracked text mirror. Keep both in a dedicated private memory repository; `memory/` is gitignored in the configuration repository at `<agent-home>`. A record is `tier`—short-lived `working` or long-lived `durable`—times `scope`—`project` or `global`—times `type` and `delivery_state` (`ordinary`, `pending`, or `consumed`). The DB became the source of truth on 2026-06-15, replacing the old Markdown-source plus derived `.index.db` design. Restore with `mem import dump.jsonl`.
- **Tier and scope:** the DB is the sole source of truth; file surfaces are on-demand views.

  | Channel | Store tier/scope | Synchronization |
  |---|---|---|
  | `post-it`, a DB working-tier alias authored by the `/post-it` Skill | working/project | `/post-it` → `mem note` or `mem add` → SessionEnd `mem sync` |
  | `projects/<cwd>/memory/`, built-in file memory whose direct writes are hard-blocked by `builtin-memory-guard.sh` | durable/project | SessionEnd `mem sync` absorbs stray writes from another session or harness as a safety net; the normal durable-learning path is an external distiller calling `mem add` |
  | DB records with `type=profile`, the cross-project profile source of truth | durable/global | `analyze-user` → `mem add` → `mem sync`; `user_profile/*.md` is an on-demand `mem export` cache for human reading, not a source of truth |

- **Harness integration:** automatic memory lifecycle belongs only to the interactive, user-facing main session (D-42). `mem inject --hook` may expose a bounded working, durable, and profile summary at main SessionStart; adapters whose start event repeats on resume, clear, or compact may keep this opt-in. Main SessionEnd runs `mem sync` plus bounded `MEM_DUMP_PUSH=1` mirroring under D-31. Main SessionEnd and turn-counter triggers may launch a no-tools distiller agent through `mem-distill-dispatch.sh`; the agent makes semantic choices and the dispatcher validates and executes structured actions under D-12–D-14. Registered dispatches, loops, title workers, distillers/curators, and native subagents are worker sessions: they never inject memory automatically, advance distill counters, sync on exit, or launch a curator. Every automatic model-backed distill path must also have an operator kill switch, atomic cross-session concurrency slots, and a persistent rolling start budget; per-session locks alone do not bound multi-session storms (D-41). Prompt-submit hooks do **not** classify every prompt for recall. Retrieval is agent-initiated through `mem recall` or `recall.sh` under D-40. `builtin-memory-guard.sh` keeps DB writes on the unified `mem` path. Hook registration remains adapter-native.
- **Recall:** `tools/memory/recall.sh` is a thin `mem recall` wrapper over store FTS5. It supports `--full`, `--limit 1..100`, `--sessions` for raw conversation JSONL, and `--all` for all scopes. If the ID is already known, read the full record directly through `mem show <id> [--all]`. The agent decides when recall is useful under §7.4.
- **CLI:** `mem {add, note, recall, show, consume, restore, index, sync, inject, export, import, migrate, lifecycle, delete, project, stats, profile, distill, register-postit}` plus curator commands `{curate-snapshot, reinforce, merge, prune, graduate, reattribute}`. `show <id> [--all]` prints metadata and the original multiline body within the visibility fence. `consume <id>` explicitly transitions a pending handoff. `restore <id>` restores one graveyard record. `profile <stem>` reads the body of a DB profile record. `export --target dump|profile` creates the git mirror or a human-readable profile cache. `import <dump.jsonl>` restores the DB. `delete <id>` deterministically deletes from records and all three FTS5 tables but refuses pending data until consumption or explicit force. `register-postit` is deprecated, migration-only, and no longer called by Skills.
- **Curator commands under D-18:** `curate-snapshot` is read-only input for a deep curator and includes durable/working data plus signals; it exposes pending records under `PROTECTED PENDING` but excludes them from destructive `IDS:`. `reinforce` increments strength under E-1. `merge` atomically combines strength, preserves noncanonical records in the graveyard, then deletes them. `prune` deletes only after graveyard backup succeeds and fails closed under S1. `graduate` moves working to durable under E-6. `reattribute` reassigns an orphan through reverse gates. All commands enforce a current-project allowlist and reject profile, global, other-project, and nonexistent targets. The no-tools distiller emits action JSON only; scripts invoke validated argv with `shell=False`.
- **Invariant D-18, D-35, D-40:** the acting agent—main, distiller, or curator—makes semantic memory decisions from available context. Scripts may validate action shape, visibility, identity, transaction safety, pending protection, graveyard recovery, and bounded lifecycle mechanics. They must not decide relevance through keyword lists, content categories, confidence thresholds, or fixed phrases. Unconsumed pending handoffs fail closed against destructive operations until an explicit `consume` transition.

Sections §7.1–§7.3 define the semantic/mechanical mutation boundary; §7.4 defines agent-initiated retrieval.

### §7.1. Semantic Decisions Belong to the Agent

There is no deterministic promote/skip classifier. The acting agent judges whether a memory operation is useful in context, including whether information is durable, non-obvious, recoverable elsewhere, stale, or merely ephemeral. Preferences, conventions, corrections, rationale, references, handoffs, and current code are considerations, not hard categories or scoring rules. The same boundary applies to retrieval and curation: scripts offer candidates and safe operations while the agent supplies meaning.

### §7.2. Write Mechanics and Deduplication

- After deciding to write, inspect visible memory and prefer updating the canonical record over creating an obvious duplicate. Fuzzy similarity is candidate evidence for the agent, not an automatic semantic verdict.
- After determining that memory is stale, use the guarded remove or merge path so recovery metadata is preserved.
- Related records may use `[[name]]` links in the DB `links` column. FTS5 indexing happens mechanically on insert; `MEMORY.md` remains a legacy projection view.
- Code may report capacity pressure and similarity candidates. The curator decides whether and how to consolidate them.

### §7.3. Agent-Backed Mutation Boundary

Purely deterministic monitors may surface candidates but cannot promote, skip, merge, or prune based on semantic rules. A user-directed post-it flow or an agent-backed distiller or curator may perform the mutation. The script then enforces only the mechanical action contract and recovery boundary.

#### D-43 — On-call incident-to-proposal bridge

An agent-backed on-call loop may use bounded recent memory mutation events only
as incident leads. It must read any selected record in full and corroborate the
claim against current source, tests, logs, artifacts, or runtime evidence
before sending it to the offline improvement proposal inbox. Memory remains
unchanged and is never sufficient evidence by itself.

The acting agent chooses one stable incident identity. Deterministic proposal
code may compare that identity exactly, append bounded recurrence evidence
under the inbox lock, and fail closed on ambiguous duplicates; it must not infer
semantic equivalence. A named automated collector may create `observed` and
advance only through `reproduced` to `proposed`. It cannot change a reviewed or
terminal decision, impersonate a human approver, edit source or runtime state,
or activate a realization. This bounded task operation is not automatic memory
lifecycle: the on-call worker does not inject, curate, sync, consume, or mutate
memory, preserving D-42.

### §7.4. Recall — On-Demand Retrieval

`mem inject` may provide a bounded SessionStart summary of working, durable, and profile records. The default cap remains 2,000 characters or 15 bullets. When more history could materially help, the agent chooses a query and invokes the read-only retrieval helper. Retrieval is information access, not handoff consumption: `show`, explicit recall/full, and SessionStart injection do not change `delivery_state`; only `mem consume <id>` does. Bounded telemetry distinguishes `explicit-recall`, `show`, `session-inject`, and `consume` without storing raw prompts.

| Helper | Purpose | Notes |
|---|---|---|
| `tools/memory/recall.sh "<query>" [--full] [--limit 1..100] [--all] [--sessions]` | Thin `mem recall` wrapper over FTS5 ranked with BM25, falling back to LIKE or `rg`. `--full` replaces snippets with full bodies for the same ranked IDs while retaining the normal output shape. `--sessions` also searches raw `*.jsonl` transcripts. | Default limit 20. Current cwd is the default scope; cross-cwd and raw retrieval require explicit flags. |
| `python3 <agent-home>/tools/memory/mem.py show <id> [--all]` | Print metadata and the exact multiline body for a known ID. | Default visibility is current project plus global; only `--all` permits other projects. `injection_flag` is always excluded, and invisible IDs return a generic not-found result. |
| `tools/memory/index-check.sh [dir] [--fix]` | Check drift in the legacy `MEMORY.md` text index under `projects/<cwd>/memory/`, including missing and orphaned pointers. `--fix` appends missing pointers only. | The built-in FTS5 index in `memory.db` is separately owned by `mem index`. Preserve existing curated lines. |

There are two retrieval surfaces. First, curated memory in durable and working tiers is searched by `mem recall` through SQLite FTS5 with BM25 ranking, falling back to LIKE or `rg`. A shortened or ellipsized snippet is never final evidence: if a hit is truncated or insufficient for the judgment, immediately read its full body by record ID with `show <id>` or use `recall --full --limit N`. Direct SQLite or `dump.jsonl` queries are not a normal retrieval path. Second, `--sessions` searches raw historical transcripts that have not been distilled into memory. Raw sessions are noisy and should supplement curated memory only when useful.

**Agent-initiated recall:** the agent decides whether prior context may materially improve the current judgment. No fixed signal words, mandatory topic list, prompt classifier, or category-to-recall rule substitutes for contextual judgment. Once the agent chooses to recall, search curated memory first, widen to `--all` or `--sessions` only when useful, and cross-check retrieved claims against current code or artifacts because memory can be stale.

- **Pointer follow-through:** when a recall result names a project file or
  artifact path relevant to the task, read that current target before using
  the memory claim to report project state. Memory supplies continuity and
  navigation; the referenced artifact and live code supply current facts. A
  missing or changed target is evidence that the memory pointer may be stale,
  not a reason to substitute the remembered summary for the file.
- **Inline recall:** for a simple agent-chosen search, run `tools/memory/recall.sh "<query>"` directly for one or two queries. If a hit needs context, follow with `mem show <id>` or `recall --full --limit N`.
- **Memory-scout capability:** use this read-only capability for deep searches across raw sessions, multiple query angles, many full bodies, or multiple working directories. Start with narrow recall and useful synonyms in any relevant language; inspect hit IDs through `show` or a few full results; widen to `--all` on a miss, then to raw sessions; finish with one line cross-checking live code. Do not bypass the interface through direct DB or `dump.jsonl` reads. Return at most 15 lines: verdict—present, absent, or ambiguous—up to three key quotations, record IDs, and one application instruction. All writes are forbidden, including `add`, `note`, `consume`, `restore`, `delete`, `reinforce`, `merge`, `prune`, or file edits.

Per-cwd isolation remains the default. Use `--all` only for an explicit cross-project need. A mass `--fix` touches gitignored live user data under `projects/` and therefore belongs in a user-directed flow; automated paths may report missing pointers but not repair them.

### §7.5. Mechanical Scaffold — Retrieval, Curation Candidates, and Pending Protection

Deterministic code may detect mechanical conditions and expose candidates around lifecycle operations; the deep curator decides semantic actions. Scripts execute only validated actions under D-18 and D-40.

**D-40 agent-owned semantic memory judgment, superseding the automatic portions of D-15 and D-34:**

- Prompt-submit bridges do not send every user prompt through a semantic classifier or inject threshold-qualified recall results.
- `mem recall` and `tools/memory/recall.sh` remain explicit retrieval tools. Ranking, tokenization, scope fences, limits, and access telemetry organize results only after the agent has chosen to search.
- `mem recall --auto` is retired. `hooks/mem-recall-inject.sh` remains only as a fail-open compatibility no-op for stale installed projections and is not registered by current adapters.
- `$XDG_STATE_HOME/agent-memory/recall-events.jsonl` remains bounded local telemetry for explicit retrieval and lifecycle access events. Raw prompts are not stored.

**D-16 cleanup signals in `mem inject`:** after the existing `mem inject --hook` block, add a `## 🧹 Cleanup signals` section only when nonempty. It may show cwd-scoped durable near-duplicate groups, capacity over `durable > soft_ceiling=80`, and working records within three days of expiration. The section remains inside the SessionStart cap and defaults to two lines. It is read-only and performs no deletes or flag writes. Under D-18 it is informational: main performs no housekeeping. The session-end deep curator reads `curate-snapshot` and its signals, emits action JSON, and `mem-distill-dispatch.sh` validates and executes it through an allowlist with `shell=False`. This moved deletion from main under D-17 to the session-end curator under D-18 because deep-role context plus graveyard/dump recovery makes the worst likely outcome inefficiency rather than loss.

**D-35 unconsumed handoff and thread protection:**

- `delivery_state` is `ordinary`, `pending`, or `consumed`. New `type=handoff` records and explicit `--requires-consume` threads are pending. Only `mem consume <id>` performs the normal pending-to-consumed transition. Source upsert and body dedup preserve pending monotonically rather than lowering it through an ordinary rewrite. `show`, recall/full, and inject are non-consuming. When retrieval exposes `[pending:<id>]`, read the full obligation, apply and verify it, then call `mem consume <id>`. A working pending record does not expire before consumption; its 21-day TTL starts over when consumed.
- `curate-snapshot` shows pending records under `PROTECTED PENDING` but excludes them from destructive `IDS:`. `prune`, `delete`, `merge`, and `lifecycle --apply` recheck DB state immediately before execution and fail closed on pending records. A merge containing any pending record aborts entirely without changing strength or deleting anything.
- Deleted records remain in the graveyard with action and canonical metadata and can be restored one at a time through `mem restore <id>`. Automatic consumption is allowed only in narrow pipeline or post-it paths that name the handoff ID and prove successful application through artifacts.

### §7.6. User Profiles — Aspect-to-Consumer Matrix

> Moved from `user_profile/README.md` on 2026-06-23 when the mapping document was removed. **Read profiles from the DB** through `mem profile <stem>` or `python3 <agent-home>/tools/memory/mem.py profile <stem>`. This matrix maps agents to aspects; the aspect body source of truth is the durable/global DB record with `type=profile`. This section is the single source for the matrix. `capabilities/analyze-user.md` and every adapter-native `analyze-user` projection must reference it; root `skills/analyze-user/SKILL.md` is only a compatibility reference.

| Stem | Domain | Consumers |
|---|---|---|
| `01_paper_figure_style` | Paper figures, tables, color, fonts, size, and metric grouping | material, design, research for figure citation style, and editorial roles |
| `02_paper_writing_style` | Paper tone, argumentation, and citation | research, editorial, and planning roles |
| `03_presentation_strategy` | Slide structure, narrative flow, visual decisions, and audience adaptation | material for presentations, design, and editorial roles |
| `04_analysis_methodology` | Data and experiment analysis approaches and verification patterns | material, research, planning, implementation for metrics and verification, editorial, and the main agent for analytical replies |
| `05_domain_expertise` | Domain background such as speech, TF DNN, and signal processing, plus terminology preferences | research, material, design, editorial, planning for abbreviations, implementation for identifiers, and the main agent for recognizing user terminology |
| `07_coding_convention` | Project layout, config, prefixes, preferred layers and frameworks, metric sets, logs and checkpoints, seeds and reproducibility, and naming | implementation, planning for code plans, and the main agent during `autopilot-lab` Step 0, `autopilot-spec` Phases 0 and 2, and the four `autopilot-code` principles |

Aspect 06, conversational meta rules, is excluded because the runtime adapter response discipline is its single source and applies only to the main agent; subagents do not speak directly to the user. The `06_collaboration_style` record remains the default collaboration target for `/post-it --scope user`. Aspect 07 applies only to implementation, planning, and main-agent code work, not editorial wording. Each agent normally consults three to five relevant aspects.

**Update protocol:** profile bodies live in durable/global DB records. Two flows may update them. `/analyze-user <aspect>` scans prior artifacts such as papers, presentations, code, and reports, extracts patterns, and accumulates them with `mem add durable profile --source user-profile:<stem>` during setup, new-material ingestion, or incremental `--mode update`. `/post-it --scope user <aspect>` adds a generally useful pattern discovered in conversation.

**Consumption pattern:** at the start of relevant work, an agent reads each aspect through `mem profile <stem>` and treats the body as a default unless the user says otherwise in the current turn. Per-project conventions in `analysis_project/code/experiment_conventions.md` take priority; profiles are the cross-project fallback. For example, a material figure task reads aspects 01, 03, 04, and 05, while a new-library implementation reads project conventions first and then aspects 07, 04, and 05.
