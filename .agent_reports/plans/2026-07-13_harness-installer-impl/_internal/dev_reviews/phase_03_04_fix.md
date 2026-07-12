# Phase 3+4 review fix — HIGH data-loss + MEDIUM/LOW findings addressed

Applied all findings from `phase_03_04.md`:

- **HIGH (data loss)**: `claude.py`/`opencode.py` symlink guards narrowed from
  `dest.exists() and not dest.is_symlink() and dest.is_dir()` to
  `dest.exists() and not dest.is_symlink()` — now blocks on a real **file**
  in the way too, matching codex's already-correct guard. Re-verified with a
  temp-HOME fixture seeding a real `CLAUDE.md`/`agent-agents.md` with user
  content before install: content survives, `blocked=True` at both the
  action and top level.
- **MEDIUM (`blocked` aggregation)**: `claude.py` no longer hardcodes
  `"blocked": False` — now `any(a.get("status")=="blocked" for a in actions)`,
  and `manifest.record()` is gated on `not blocked`. `opencode.py`'s
  `blocked` now ORs the merge-conflict flag with any symlink-blocked action.
  Re-verified: a full clean install into a fresh temp HOME across all three
  drivers still reports `blocked=False` with the expected action counts
  (claude 17 created + 1 skipped-delegate, codex 54 created, opencode 50
  created + 1 merged) and non-null manifests.
- **LOW-MEDIUM (check-id shadowing)**: `opencode.py` `checks()` symlink check
  ids now use `parent.name.name` (matching codex's convention) instead of
  bare basename.
- **LOW (drift-watch false positive)**: removed `plugins` from the
  INST-OPEN-4 plural-dir candidate list in `opencode.py`'s drift-watch
  sentinel — it's a directory the harness itself always creates
  (`agent-harness-guards.js` dest), not a migration signal.

All three driver files re-compiled clean (`compile()` smoke) after the edits.
