# Phase 1+2 code-review — projector.py / manifest.py

**Scope**: `tools/install/projector.py` (Phase 1), `tools/install/manifest.py` (Phase 2), `tools/install/paths.py` (Phase 0, spot-check). code-review mode. All checks run under `mktemp -d` HOME + `AGENT_HOME=<worktree>`; real `~/.claude`/`~/.codex`/`~/.config/opencode` never touched.

**Verdict**: PASS — no blocking correctness bugs. All three named invariants (path-safety, anti-clobber pristine, non-corrupting reapply across conflict/degrade/verify_failed) hold under execution. A handful of medium/low hardening items below.

---

## Verified by execution (not just read)

- **projector.plan() zero skips** — `claude total=18 skips=0`, `codex total=54 skips=0`, `opencode total=51 skips=0`. Every source relpath resolves to a real file (spot-checked `claude_setting/`, `codex_setting/{codex-skills,codex-agents,codex-hooks,codex-modes}`, `opencode_setting/{opencode-agents,opencode-plugins}` — all present). Matches step-log claim.
- **codex project-scope agents override** — `plan(["codex"], scope="project")` correctly rewrites agents glob dest to `<cwd>/.codex/agents/design-team.toml` (not `~/.codex/`). `_dest_dir_for` special-case works.
- **plan() / check_drift() read-only** — temp HOME left empty (`os.listdir(HOME)==[]`) after `plan()`; `check_drift` only sha256+load. Confirmed no writes outside the `<runtime_home>/.harness` subtree during record/reapply.
- **`_safe_relpath`** — rejects `/etc/passwd`, `../escape`, `a/../../b`, `foo\x00bar`; accepts `settings.json`, `sub/dir/file.json`. Enforced in all three public functions before disk touch.
- **Anti-clobber pristine** — verified on three axes: (1) `record()` never overwrites an existing pristine even when re-run (SENTINEL survived a second `record`); (2) pristine refreshed **only** after a successful merge+verify (clean-merge case advanced it, `user_added` absent from pristine); (3) conflict / no-git-merge-file / verify_failed all leave pristine untouched at the old base.
- **3-way merge, all four buckets exercised**:
  - clean merge (non-adjacent edits): `reapplied`, dest holds both `new_top` + `user_added`, `check_drift` clean afterward, manifest hash re-synced.
  - conflict (overlapping edits): reported `status: conflict`, **dest left as the user's version (untouched)**, backup preserved, pristine not advanced, drift still flagged (unresolved). Correct.
  - git-absent degrade (monkeypatched `FileNotFoundError`): `status: no-git-merge-file`, dest not corrupted, backup made pre-attempt, pristine not advanced. This is the path the step log admits it only reviewed statically — confirmed working here.
  - dest is never overwritten on any non-`reapplied` branch. The "must NOT corrupt dest / must NOT discard a user edit" invariant holds in every edge case tested.
- **Atomic manifest write** — `_write_manifest` uses temp+`os.replace` (also used for `backup-meta.json`). Good.

Note: the step log's "정상 merge" fixture placed both edits non-adjacently, which is why it merged clean; an adjacent-edit fixture conflicts instead. Both outcomes are correct — the code is not over-eager to merge.

---

## Findings

### 1. [medium] `reapply` writes dest / pristine / backup with non-atomic `write_bytes`
`manifest.py:268` (backup), `:321` (dest), `:322` (pristine) use direct `Path.write_bytes`, which truncates-then-writes. The plan explicitly called out atomic writes and a "NEVER corrupt dest" invariant; a crash mid-write to `dest_abs` leaves a partial/truncated live file. Data loss is bounded (the pre-wipe backup at `local-patches/` is written first, so recovery is possible), but the guarantee is weaker than for the manifest, which *does* use temp+rename. Recommend routing the dest write (at minimum) through the same temp+`os.replace` pattern as `_write_manifest`. Cheap, closes the one remaining corruption window.

### 2. [low] `_safe_relpath` docstring overstates "symlink-escape" rejection
`manifest.py:81-104` — the resolve step joins against a **non-existent** sentinel base (`/__manifest_safe_base__`), so it normalizes `..` lexically but never follows a real symlink. It cannot catch a relpath that escapes via a symlink already present inside `<runtime_home>`. That's acceptable here (relpaths are manifest-controlled, not attacker-controlled, and `..`/absolute are already rejected lexically), but the docstring claim "symlink-escape 를 거부한다" is stronger than what's enforced. Either soften the comment or resolve against the actual `runtime_home` if you want the real guarantee.

### 3. [low] post-merge verifier substring check can false-pass
`manifest.py:312` `all(line in merged_bytes for line in backup_lines)` — an order-independent substring test. If a user's edit line were dropped by the merge but its exact bytes happen to appear elsewhere in the merged output (e.g. a bare `}` or a line duplicated from base), the verifier would wrongly pass. Real multi-token edit lines make this near-impossible, so it's a known-limitation note, not a bug — the check only ever *relaxes*, never falsely blocks, so it can't corrupt/discard on its own. Worth a one-line comment acknowledging it's a heuristic backstop, not a proof.

### 4. [low] crash window between pristine-refresh and manifest rewrite
In `reapply` Step 4 the order is: write dest → refresh pristine (`:322`) → stage in-memory manifest hash → (after the per-runtime loop) write manifest (`:331`). A crash between pristine-refresh and the manifest write leaves pristine advanced while the manifest hash is stale. Self-heals on the next `reapply` (base==theirs → user edit preserved), so low severity, but staging the pristine refresh to happen *with* the manifest write (or writing manifest per-file) would tighten it.

### 5. [nit] step-log narration miscounts claude symlinks (14 vs 15)
`step_01_projector.md` says "symlink (14개)" and "17 테이블 항목"; `_CLAUDE_SYMLINK_NAMES` actually has 15 entries (matching plan.md's listed 15 names) → 15+2+1 = 18 concrete, which is what the code and the verified `breakdown={'symlink':15,'copy_once':2,'delegate':1}` produce. Code is correct; only the log prose is off by one. Harmless but fix the note so a future reader doesn't chase a phantom missing entry.

---

## Praise / good calls

- **`sources` kwarg on `reapply` (step-log Decision #1)** — correctly refuses to hardcode the relpath→source-tree mapping inside `manifest.py`, keeping the projector table as the single owner. This avoids a real dual-ownership drift trap and is the right seam.
- **Anti-clobber timing is precisely right** — pristine touched at exactly two moments (absent-at-record, and post-verified-reapply) and nowhere else; the `#3407` trap the plan flagged is genuinely closed, verified three ways.
- **Degrade path is graceful, not silent** — `no-git-merge-file` surfaces as a reported bucket with the backup already on disk; no crash, no data loss, other files continue.
- **`check_drift` "no manifest = skip, not drift"** distinction (Decision #5) avoids the false-drift-on-uninstalled-runtime footgun that would have made `update` perpetually exit 4.

---

## Not reviewed (out of Phase 1/2 scope)
- Driver wiring that *assembles* the `files`/`sources` dicts and actually applies symlinks (Phase 3) — the projector emits intent only; symlink creation and the opencode.json merge are unverified here.
- `install-windows.sh` delegate branch (fires only on `os.name=='nt'`).
- Whether callers pass `scope` consistently through installer.py (Phase 5).
