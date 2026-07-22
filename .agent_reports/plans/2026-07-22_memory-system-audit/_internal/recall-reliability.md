# Stream 3 — Recall Reliability 실측 (relocation go/no-go)

Date: 2026-07-22. Method: READ-ONLY — live DB opened only via `mode=ro` URI for inspection;
all `recall` runs used `--no-touch`; no repo file edited; scratch work under session scratchpad.
Store shape at measurement time: `memory/memory.db` 3.6MB (dir total 602MB = own git repo +
backups), WAL journal, schema v5, 1378 records, 7 profile records, `records_fts` present,
`records_trig` ABSENT.

## Verdict table

| Path | Verdict | Condition |
|---|---|---|
| 1. `mem profile` read (correct home) | **RELIABLE** | — |
| 2a. Worker resolution, AGENT_HOME unset, any cwd | **RELIABLE** | falls back to `~/agent_setting` (primary) |
| 2b. AGENT_HOME pointed at a checkout without `memory/` (any worktree) | **BROKEN** | silently creates a NEW EMPTY memory.db there; reports "aspect not found" |
| 2c. Project-scoped `recall` from a non-git cwd | **CONDITIONAL** | needs `--all`, else project records invisible (20 hits → 2) |
| 2d. Project-scoped `recall` from a worktree cwd | **RELIABLE** | same `git:` project_key via remote/git-common-dir (contract-tested) |
| 3. Semantic recall (`recall.sh`) mechanics | **RELIABLE** | ~0.12s, stdlib-only, no services/embeddings |
| 3'. Semantic recall precision | **CONDITIONAL** | OR-token bm25 = noisy top-N; single-token overlap ranks junk high |
| 5. Profile read inside registered headless worker | **RELIABLE today** | Bash wholesale-allowed; env inherits; breaks only under 2b (drill-style AGENT_HOME export) |

## 1. Profile path — RELIABLE

`python3 tools/memory/mem.py profile <aspect>`, 3 runs each:

- `01_paper_figure_style`: 0.09 / 0.08 / 0.09 s, maxrss ~18MB, **byte-identical** (md5 c64b6d7a…)
- `05_domain_expertise`: 0.10 / 0.09 / 0.09 s, byte-identical
- `07_coding_convention`: 0.09 x3, byte-identical

Determinism is by construction: newest-wins dedup sorts `(created DESC, rowid DESC)`
(mem.py:1677), single SELECT, no randomness.

Failure modes (all clean, all exit 2 with actionable stderr):
- wrong name → full aspect list with aliases printed;
- ambiguous alias (`style`) → candidate stems listed (01/02/06);
- unique alias (`figure`, `coding`) and 2-digit prefix (`05`) resolve correctly;
- `--list` shows all 7 aspects with sizes.

Concurrent second reader (open read transaction held 6s on the live DB): profile reads
unaffected — 0.09-0.10s, exit 0, identical bytes. WAL + `busy_timeout=5000` (mem.py:579).
Writer-lock contention was NOT tested (would require taking a write lock on the live DB —
out of read-only bounds); busy_timeout gives a 5s grace, and the v14 suite's TOCTOU test
exercises reader-under-`BEGIN IMMEDIATE` successfully.

Caveat worth knowing: "read-only" `profile` is not read-only at the FS level. `get_con()`
(mem.py:571-582) does `STORE.mkdir()`, opens the DB **read-write**, sets WAL, and runs
schema migrations. Consequences: (a) needs write permission on `memory/` (same-user setup:
fine); (b) it is exactly why path 2b is destructive-ish (see below).

## 2. Worker-context resolution

Resolution chain (mem.py `default_agent_home`, utilities/agent-home.sh):
AGENT_HOME → CLAUDE_HOME → `$XDG_DATA_HOME/agent-harness/current` (absent on this host) →
`~/agent_setting` → `~/.claude`. Script location is IGNORED — running a worktree's copy of
mem.py still resolves by env/HOME only.

**2a (RELIABLE, measured):** from `/tmp` scratch cwd with AGENT_HOME/CLAUDE_HOME unset,
both `mem.py profile figure` and `recall.sh "figure style" --no-touch` resolved the primary
store and returned correct data.

**2b (BROKEN, measured):** `AGENT_HOME=<dir-without-memory/>` (which is EVERY worktree —
`memory/` is gitignored in the config repo and is its own private git repo, so no checkout
besides primary has it):

```
AGENT_HOME=$S/fake-worktree python3 …/mem.py profile figure
→ exit 2, "[migrate v3] …", "[profile] aspect 'figure' was not found. Available aspects:" (empty list)
→ side effect: $S/fake-worktree/memory/memory.db (36KB, empty, schema v5) CREATED
```

No hint that the wrong store was opened; an agent reading only "not found" would conclude
the profile doesn't exist. This is the memory-system twin of the known drill trap
("worktree validation silently validates primary" — here inverted: worktree home silently
reads an empty store). Trigger in real flows: drill/worktree validation exports
AGENT_HOME+DRILL_HOME; a worker inheriting that env loses ALL memory reads.

**2c (CONDITIONAL, measured):** `recall` defaults to cwd-scoped visibility
(`scope='global' OR cwd_origin=<project_key(cwd)>`). Query "dispatch", limit 20:
primary cwd → 20 hits; non-git scratch cwd → **2 hits** (globals only); `--all` → 20.
Profiles are `global` scope, so `profile`/global recall is immune; project-scoped facts,
contracts, and postits silently vanish.

**2d (RELIABLE by contract):** `project_key` prefers `git remote origin` normalized
(`git:github.com/dmlguq456/agent_setting`, verified) and falls to git-common-dir, so any
worktree of this repo maps to the SAME key. mem_cluster_e ③b/③d/⑦ explicitly test
inject+recall from a worktree retrieving project records. Registered workers run
`cd <worktree> && claude -p` (dispatch-headless.py:414), so their recalls keep project scope.

## 3. Semantic recall path — mechanics RELIABLE, precision moderate

`recall.sh` = thin exec wrapper → `mem.py recall`. No embeddings, no daemon, no network,
no non-stdlib Python; only optional `rg` for `--sessions`. A headless worker lacks nothing.

5 queries, primary cwd, `--no-touch --limit 5`:

| Query | latency | hits | quality |
|---|---|---|---|
| "spectrogram window size" | 0.12s | 5 | relevant fact (RMS 100ms window/20ms hop sample spec) top-1, then OR-noise ("rate-window", "context-window") |
| "figure style" | 0.12s | 5 | figure QA contract + profile records surfaced |
| "코딩 컨벤션" | 0.12s | 2 | coding-convention profile record found (unicode61 handles Korean tokens) |
| "zxqv flurble kumquat" (nonsense) | 0.11s | 0 | clean `(no store matches)`, exit 0 |
| "STFT window 크기 설정" (mixed KR/EN) | 0.12s | 5 | relevant matplotlib-size feedback top-1, then "window" OR-noise |
| "컨벤" (CJK substring, extra probe) | ~0.1s | 3 | LIKE fallback works |

Findings:
- Latency uniformly ~0.11-0.12s at 1378 records. No SLA is stated anywhere; this is
  comfortably interactive.
- **Trigram tokenizer is MISSING on this host** (system SQLite 3.31.1 < 3.34; docstring
  advertises "CJK trigram support", `records_trig` absent). The coded LIKE fallback
  (bucket 2, mem.py:1077-1088) covers CJK substrings correctly — but unranked (score 0.0)
  and full-scan. Works at current scale; a silent capability downgrade vs design intent.
- **OR-token semantics** (`_tokenize_query` → `t1 OR t2 …`) means any record sharing one
  token competes; bm25 mostly ranks well but top-5 contains obvious noise for multi-word
  queries. For relocation this matters: a speech constant stored as one durable record is
  findable if it shares a distinctive token ("spectrogram", "STFT"), but generic-token
  queries ("window size 설정") will bury it.
- Default `recall` (without `--no-touch`) WRITES `last_accessed` — worker recalls mutate
  access metadata by design (cold-decay signal, fail-open). Telemetry appends to
  `~/.local/state/agent-memory/recall-events.jsonl` regardless; contract-tested to exclude
  raw query text and to fail open on corrupt telemetry files.

## 4. Intended contract (test suites) vs measurement

Read: mem_retrieval_v14.test.sh (258 l), mem_cluster_e (668 l), e_gamma, cluster_j,
inject.test.sh.

Contract the suites pin (and my measurements confirm where overlapping):
- v14: hyphen≡space split-OR (silent-miss fix), Korean particle strip ("스테이지분사에서" →
  stem hit), FTS operator injection neutralized, `--no-touch` preserves `last_accessed`,
  telemetry events without raw query, pending records visible-but-protected, `--auto`
  semantic recall retired (agent-initiated only, D-40).
- cluster_e: migration idempotency, project_key taxonomy (git:/id:/root:/enc_cwd),
  **worktree ≡ main repo key** (③b/③d), inject+recall from worktree (⑦), live-DB
  preservation with sha256 body check (⑥).
- inject.test: SessionStart injection bounded (≤2000 chars/≤15 bullets), read-only, cleanup
  signals project-scoped.
- cluster_j: full write-actor journal coverage.

Contract GAPS exposed by measurement:
1. **No test covers path 2b** (AGENT_HOME → memoryless checkout ⇒ silent empty-store
   creation + "not found"). This is the highest-risk untested path and it is the exact
   shape of relocation failure: an agent told "run mem profile" concludes the knowledge
   does not exist.
2. No test asserts trigram presence or flags its absence; CJK depends on the fallback
   branch whose selection is environment-dependent (`_TRIG_OK`).
3. No ranking/precision assertions at realistic corpus scale (tests use 2-3 planted
   records); OR-noise is untested territory.
4. No latency bound anywhere (currently moot at 3.6MB).

## 5. Dispatch-worker reality — profile reads WORK today

Trace (stage-dispatch-fallback.py → adapters/claude/bin/dispatch-headless.py):
- Child = `cd <worktree> && claude -p --add-dir <artifact_root> [--disallowedTools <7 async tools>]`
  (dispatch-headless.py:398-417). **No permission bypass flag** — but live
  `~/.claude/settings.json` allows `"Bash"` wholesale (defaultMode "auto"), so
  `python3 <agent-home>/tools/memory/mem.py profile …` faces no permission gate. Only
  proven-async tools are denied; Bash is explicitly never denied (SD-71 comment).
- Env: parent env minus `AGENT_DISPATCH_BROKER_*`, plus `AGENT_DISPATCH_*`/role vars
  (dispatch-headless.py:992-1027). **AGENT_HOME is not set by the wrapper** — it passes
  through only if the launcher had it. Launcher sessions on this host run with AGENT_HOME
  unset (verified) → workers resolve primary store correctly (path 2a). `resolve_agent_home()`
  in the wrapper is used for the jobs registry only, not exported.
- cwd = worktree → project_key preserved (path 2d), so unit instructions like
  figure-gen.md:70 (`python3 <agent-home>/tools/memory/mem.py profile 01_paper_figure_style`),
  backend.md:45 (07), editorial/_voice.md:71/126 (05, 02), research-survey.md:42 would
  execute successfully — PROVIDED the worker expands `<agent-home>` sanely. Even the lazy
  expansion "my checkout root" is harmless for mem.py (env-based resolution ignores script
  path); only `export AGENT_HOME=<worktree>` breaks it (path 2b).
- Lifecycle hygiene confirmed: mem-briefing-inject, mem-turn-nudge, mem-distill-dispatch
  all early-exit on `AGENT_SESSION_ROLE=worker` / `AGENT_DISPATCH_CHILD=1`; workers get no
  auto-injection and never distill (MEMORY.md D-42), while agent-initiated `recall`/`profile`
  remain available — matching the D-40 contract. `mem-recall-inject.sh` is a deprecated
  no-op shim (still registered in live settings; harmless, worth cleaning).
- Residual conditional: quick/one-shot workers running in NON-git scratch dirs lose
  project-scoped recall without `--all` (path 2c). Profile reads (global) unaffected.

## Go/no-go implication for relocating domain constants into memory

- **Go, with two fixes.** The mechanical substrate is strong: profile reads are fast,
  deterministic, permission-clear, concurrency-safe, and worker-reachable; semantic recall
  needs no services a worker lacks.
- Fix 1 (blocker-class): guard path 2b — `mem.py` should refuse (or loudly warn) when the
  resolved STORE has no existing `memory.db` instead of creating an empty store and
  reporting "not found"; at minimum print the resolved DB path in the error. Otherwise any
  drill-style AGENT_HOME export turns relocated knowledge into a convincing "does not
  exist". Add a regression test (the suites currently never cover it).
- Fix 2 (quality-class): relocated constants should live in profile records (global scope,
  alias-resolvable, deterministic reads) rather than rely on semantic `recall`, whose
  OR-token ranking is the weakest measured link; if recall-ability matters, give records
  distinctive domain tokens (e.g. "spectrogram", "STFT") and document `--all` for non-git
  cwds.

## Raw evidence

Scratch outputs: `/tmp/claude-1003/-home-Uihyeop-agent-setting/1fef26b4-de7a-4605-a171-e3fe1716e227/scratchpad/`
(prof01_r*.out/.time, 05/07 runs, lock_r*, q1-q5.out/.time, fakewt.out, workercwd tests).
Key code lines: mem.py:19-39 (home/store resolution), 571-582 (get_con RW+migrate),
1652-1774 (profile), 992-1172 (recall), 222-259 (project_key);
recall.sh:10-13; utilities/agent-home.sh; dispatch-headless.py:398-417, 684-703, 992-1052;
stage-dispatch-fallback.py:390, 455-464; hooks/mem-*.sh worker guards; core/MEMORY.md §Harness integration.
