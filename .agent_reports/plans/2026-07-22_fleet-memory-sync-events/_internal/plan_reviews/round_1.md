## 📋 Plan Review Results

**Target:** `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/plan.md` and `checklist.md`

**Plan summary:** The plan proposes additive journal plumbing in `tools/memory/mem.py`, then opts the four migration sources into literal-`sync`, `action=add`, INSERT-only events with source-derived cwd. It keeps the Fleet collector unchanged and provides strong focused coverage for actor precedence, cwd fallback/omission, idempotency, no-backfill, and an auto-memory-to-Fleet acceptance path.

**Evidence checked:** D-37 v22 / Fleet F-19/F-35f v15 wording, the spec-owner transaction report, the research artifact, the r2 review verdict (W1-W4), sealed worktree HEAD `e8938809d87e54474f5e7242a2552598c2636a0a` (clean, verified), and direct reads of every `mem.py` line range the plan cites (`write_record` 1000-1117, `_write_actor` 1250-1257, `_append_write_event` 1260-1291, `migrate()` 2084-2230, `sync()` 3555-3579, CLI call sites 3731-3743), plus `tools/fleet/collectors/memory.py` and `tools/fleet/model.py:project_of`.

### 🔴 must-fix before execution

**plan step "Scope and governing contracts" (plan.md:12-19) — governing spec citations do not resolve in this worktree, and the underlying text is uncommitted WIP in a different checkout (major)**

- **Current code state:** `spec/prd.md` and `spec/agent-fleet-dashboard/prd.md` do not exist at those paths in this worktree (`ls spec/` fails). The real tracked location is `.agent_reports/spec/prd.md` / `.agent_reports/spec/agent-fleet-dashboard/prd.md`, and this worktree's committed copy at HEAD (clean, no diff) is still **v21** — it has none of the create-only / literal-`sync`-actor-immune-to-`MEM_ACTOR`/`MEM_DISTILL` / prospective-only-no-backfill wording the plan depends on (verified by reading `.agent_reports/spec/prd.md:285-303` directly). The v22/v15 wording the plan quotes almost verbatim (matching the r2 review's W1-W4) exists only as **unstaged, uncommitted working-tree edits in the separate primary checkout** `/home/Uihyeop/agent_setting` (`git status` there shows `M .agent_reports/spec/prd.md` and 3 sibling files, nothing staged, no commit). The spec-owner-report's "PASS"/"atomic transaction" language describes writing these files under a lock, not committing them.
- **Plan's assumption:** "Normative requirements: root PRD v22 D-37 (`spec/prd.md:286-293`)... The PRDs and r2 review already fix the actor, action, create-only boundary..." — i.e., that this is settled, committed, re-derivable ground truth.
- **Proposed correction:** Either land the primary checkout's `.agent_reports/spec/*` edits as a real commit before code-execute starts (the diff is already produced and independently re-verified — this is a completion step, not new work), or add an explicit checklist scope-lock item that re-validates the cited spec text is present at a committed hash immediately before code-execute begins and fails closed if not. Also correct the plan's path citations to the real tracked location.

**plan step 4.1 (plan.md:134-141) — the verification command list omits every other canonical memory suite that shares the touched primitives (major)**

- **Current code state:** `write_record()` and `_append_write_event()` are shared by many mutation paths beyond add/note/migrate. The repository has additional canonical suites the plan never runs: `tools/memory/mem_cluster_e_gamma.test.sh`, `mem_retrieval_v14.test.sh`, `pending_drain.test.sh`, `distill.test.sh`, `inject.test.sh`, `empty-store-guard.test.sh`, `retrieval-eval.test.sh` (all confirmed present in `tools/memory/`). Phase 4.1 lists only Cluster J, repairs v15, Cluster E, and the Fleet F-19 unittest.
- **Plan's assumption:** Phase 4.1 calls this "the focused and adjacent memory suites" and checklist "Verification commands" treats the same short list as the completion gate, without naming or excluding the other suites.
- **Proposed correction:** Add the remaining suites to the verification command block (or a named full-suite runner), or explicitly name any suite excluded and why. A signature-additive change to a primitive this widely shared needs the full regression net run once, not just the suites the plan happened to touch.

**plan step 3.4 / checklist scope locks — `sync()`'s dump-commit/push side effect is not explicitly fenced in the fixtures (major)**

- **Current code state:** `sync()` calls `export_dump()` then `_commit_dump()` (`mem.py:3576`). `_commit_dump()` no-ops when `MEM_DUMP_COMMIT=0` or when the store isn't a git working tree (`mem.py:169,178-179`), but otherwise stages and commits `dump.jsonl`, and pushes when `MEM_DUMP_PUSH=1` (`mem.py:193-196`). Today the fixture's `mktemp -d` `MEM_STORE` is never `git init`-ed, so this currently no-ops — but neither the plan nor the checklist requires `MEM_DUMP_COMMIT=0`/keeping `MEM_DUMP_PUSH` unset as an explicit fixture invariant.
- **Plan's assumption:** The repeat-`sync` test (3.4) is treated as safe purely because it uses temporary roots; the checklist's "Never invoke migrate/sync against the real memory store" doesn't cover the dump-commit git side channel specifically.
- **Proposed correction:** In every `sync()` acceptance invocation, explicitly set `MEM_DUMP_COMMIT=0` (belt-and-suspenders over the non-git-store no-op) and never set `MEM_DUMP_PUSH=1`. Given this route's explicit no-commit/no-push boundary, an explicit fence costs one env var and removes a latent footgun if a fixture ever accidentally reuses/initializes a git dir.

### 🟡 useful improvements

**plan steps 3.3-3.5 — broaden the Fleet repo-card proof beyond auto-memory**

- **Missing content:** The real producer-to-`collect()` proof (3.3) only exercises the auto-memory path. Checklist line 56 separately requires the registered post-it event cwd to be the repo root, but no Phase 3 step asserts that field lands correctly in `by_repo`.
- **Reinforcement suggestion:** Add a post-it producer assertion (`cwd=root_dir.resolve()`, `action=add`, `actor=sync`, and the resulting `by_repo["<repo>"]` card), or state explicitly why the auto-memory card alone is sufficient consumer proof for both source shapes.

**plan steps 3.2, 3.5, 4.1 — name the research artifact's `mem log --actor sync` acceptance criterion explicitly**

- **Missing content:** Research §7 criterion 6 (`mem log --actor sync` returns only absorption events) isn't named anywhere in the plan or checklist as an explicit assertion, though `--actor` is a closed enum choice (`mem.py:3708`) so this is a one-line check.
- **Reinforcement suggestion:** Add an explicit `mem log --json --actor sync` assertion alongside the existing event-shape checks.

### 🟢 well-constructed portions

- Steps 1.1-1.3 correctly separate the event-cwd sentinel from the existing default, preserve `MEM_CWD`/process fallback for ordinary callers, and require explicit `None` to omit the JSON key — I traced this through `_append_write_event`'s current `cwd` line (`mem.py:1279`) and confirmed no existing caller passes `cwd` today, so the extension is purely additive.
- Steps 2.1-2.5 accurately map auto-memory, post-it, global-profile, and legacy-Markdown sources to logical cwd values while preserving DB `cwd_origin`, source namespaces, and `existing_src` behavior; I independently re-derived the within-one-run duplicate-post-it-bullet scenario (`existing_src` is a pre-run DB snapshot, so both duplicates skip that gate, but the second `write_record()` call's `find_by_source()` hits the just-committed first INSERT and correctly lands in the source-upsert branch that `journal_insert_only` suppresses) and it matches the plan's edge-case expectation exactly.
- The literal `journal_actor="sync"` design is correct and necessary: `_write_actor(default="sync")` would still let `MEM_ACTOR`/`MEM_DISTILL` override it (`mem.py:1252-1256`), so the plan's explicit rejection of that helper for absorption events is the only construction that satisfies the "immune to ambient env" requirement.
- The new source-cwd decoder is genuinely needed, not redundant: `_decode_enc_cwd()` alone only accepts the encoded (`-`-prefixed) form and returns `None` for a raw absolute path (`mem.py:377-378`), so a decoder that additionally accepts absolute-path metadata (mirroring but not reusing `_canonical_cwd_key`'s dual branch) is required for the legacy-Markdown source.
- The Fleet-consumer analysis is precise: `collectors/memory.py:23-26,103-118,142-222` and `model.py:74-122` (`project_of`) match the plan's claims exactly, including honest `by_repo` omission when `cwd`/`project` is absent and that a plain repo name like `agent-note` groups correctly with no `-wt`/`_worktrees` false collapse.
- Signature-safety check: every existing `write_record(`/`_append_write_event(` call site (CLI `add`/`note`, all four migrate loops, and all direct mutation callers) uses keyword arguments only, so trailing additive kwargs are safe against positional-call breakage.
- Rollback and scope boundaries are clear and consistent with the route contract: only future prospective events are added, already-emitted rows remain valid on revert, and integration/commit/push/cleanup stay with the depth-1 owner.

## Verdict: `🔴 3 issues (3 major)`
