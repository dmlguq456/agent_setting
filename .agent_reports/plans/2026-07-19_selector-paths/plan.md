# Plan — selector-paths: adapter-projection selector path resolution

slug: `selector-paths-plan` · intensity: standard · capability: autopilot-code (dev/refactor) · qa: standard

## 1. Problem (verified)

`utilities/dispatch-route.sh` is a read-only selector projected onto each adapter
surface as a **symlink**:

```
adapters/{claude,codex,opencode}/utilities/dispatch-route.sh -> ../../../utilities/dispatch-route.sh
```

The script resolves its internal helpers with `$(dirname -- "$0")`, which does
**not** follow the symlink. When invoked through a projected path
(`adapters/<h>/utilities/dispatch-route.sh`):

- `dirname "$0"` → `adapters/<h>/utilities` (the projected dir, a real dir of symlinks)
- `dirname "$0"/..` → `adapters/<h>` (adapter root, **not** repo root)

Empirically reproduced (worktree, projected `adapters/claude` surface):

```
$ adapters/claude/utilities/dispatch-route.sh --stage plan
.../adapters/claude/adapters/codex/bin/model-map.sh: not found      # L106 climb wrong
$ adapters/claude/utilities/dispatch-route.sh --stage test --capability autopilot-code --maker-family gpt
.../adapters/claude/adapters/claude/bin/model-map.sh: not found
```

**Root cause split:**
- L103–104 (`model-map.sh`) **hard-breaks**: the `../` repo-root climb lands in
  `adapters/<h>/` so `.../adapters/<h>/adapters/<fam>/bin/model-map.sh` never exists.
  Output is silently corrupted (`exact_model_id=`/`reasoning=` empty) — the
  command substitution fails but `set -e` does not abort the assignment.
- L28 (`dispatch-defaults.py`) and L38 (`usage-check.sh`) currently *happen* to
  resolve because the whole `utilities/` tree is mirror-symlinked into
  `adapters/<h>/utilities/`, but this only works by accident of full projection
  and must be made robust by the same real-path resolution.

`utilities/dispatch-defaults.py` already self-resolves via
`os.path.realpath(__file__)` (see its `_repo_root()`) — **do not touch it** (out of scope).

## 2. Fix — path resolution only (SD-23 read-only preserved)

Resolve `$0`'s real path once, near the top of `utilities/dispatch-route.sh`,
immediately after the arg-validation block (after current L21, before the SD-66
comment at L23). No logic/cascade/output-format change.

Insert:

```sh
# selector-paths: resolve this script's real location so internal helper
# lookups work when it is invoked through the adapters/<harness>/utilities/
# symlink projection. readlink -f canonicalizes the symlink to the true
# utilities/ dir; if readlink lacks -f (non-GNU) it fails and we keep the
# prior $0-based dirname path.
real_self=$(readlink -f "$0" 2>/dev/null) || real_self=$0
self_dir=$(CDPATH= cd -- "$(dirname -- "$real_self")" && pwd)
repo_root=$(CDPATH= cd -- "$self_dir/.." && pwd)
```

Then replace the four inline resolutions with the precomputed vars:

| Line | Before | After |
|------|--------|-------|
| L28 | `defaults_script="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/dispatch-defaults.py"` | `defaults_script="$self_dir/dispatch-defaults.py"` |
| L38 | `usage_script="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/usage-check.sh"` | `usage_script="$self_dir/usage-check.sh"` |
| L103 | `map="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)/adapters/codex/bin/model-map.sh"` | `map="$repo_root/adapters/codex/bin/model-map.sh"` |
| L104 | `map="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)/adapters/claude/bin/model-map.sh"` | `map="$repo_root/adapters/claude/bin/model-map.sh"` |

Notes / constraints honored:
- **POSIX sh only.** `readlink -f`, `CDPATH= cd -- "$(dirname -- ...)"`, `pwd`,
  command substitution, `||` fallback are all dash-clean. No bashisms.
- **Fallback is one line** (`|| real_self=$0`): on a shell whose `readlink` lacks
  `-f`, the substitution fails → `real_self=$0` → `dirname "$0"` reproduces the
  *prior* behavior exactly. Real invocation via the true `utilities/` path is
  unaffected (readlink -f returns the same path).
- **Read-only unchanged (SD-23):** only path resolution changes; no cascade,
  branch, exit code, or emitted-line change.
- **Do not touch** `utilities/dispatch-defaults.py` (self-resolves already).

## 3. Regression test — `utilities/dispatch-route.test.sh`

Add a projection-surface block **before** the final `echo 'dispatch-route: PASS'`
(after the existing jobs-log non-mutation block, ~L164). Keep ALL existing
assertions and the `DISPATCH_DEFAULTS_CONFIG="$cfg"` fixture isolation.

```sh
# ---- selector-paths: adapter-projection surface resolves helpers ----
# Invoking through each adapters/<h>/utilities/ symlink must resolve the
# internal helpers (dispatch-defaults.py, usage-check.sh, model-map.sh) the
# same as the real utilities/ path. 'adapter=' is only emitted after model-map
# resolves, so asserting it proves the repo-root climb (L103-104) is fixed.
# Fixture isolation preserved via an explicit DISPATCH_DEFAULTS_CONFIG.
: > "$jobs"
for h in claude codex opencode; do
  proj="$root/adapters/$h/utilities/dispatch-route.sh"
  out=$(DISPATCH_DEFAULTS_CONFIG="$cfg" AGENT_HOME="$tmp" "$proj" --jobs "$jobs" \
        --stage test --capability autopilot-code --maker-family gpt)
  assert "$out" 'status=eligible'
  printf '%s\n' "$out" | grep -q '^adapter=' \
    || { echo "projection $h did not reach adapter= output" >&2; exit 1; }
done
# plan stage once through a projection exercises the codex model-map branch.
out=$(DISPATCH_DEFAULTS_CONFIG="$cfg" AGENT_HOME="$tmp" \
      "$root/adapters/claude/utilities/dispatch-route.sh" --jobs "$jobs" --stage plan)
assert "$out" 'adapter=codex'; assert "$out" 'role=deep maker'
```

Why this covers the fix:
- `--stage test --capability autopilot-code --maker-family gpt` → fixture
  `test: diverse` + maker gpt → claude → resolves `claude` model-map via
  `repo_root` (L104). Empty jobs → eligible.
- `--stage plan` → default affinity codex → resolves `codex` model-map via
  `repo_root` (L103).
- Both exercise `self_dir` (L28/L38) and `repo_root` (L103/L104) from a
  projected surface. Pre-fix these emit empty `exact_model_id`/`adapter=` path
  fails; post-fix `status=eligible`/`adapter=` present.

## 4. Verification plan

Run all from the worktree `/home/Uihyeop/agent_setting-wt/selector-paths`.

1. **Syntax (dash-clean):**
   `sh -n utilities/dispatch-route.sh && dash -n utilities/dispatch-route.sh`
   `sh -n utilities/dispatch-route.test.sh && dash -n utilities/dispatch-route.test.sh`
2. **Suite:** `sh utilities/dispatch-route.test.sh` → `dispatch-route: PASS`.
3. **Manual 3-adapter projection** (each must show `status=eligible` + `adapter=`):
   `for h in claude codex opencode; do adapters/$h/utilities/dispatch-route.sh --stage test --capability autopilot-code --maker-family gpt; done`
   plus once: `adapters/claude/utilities/dispatch-route.sh --stage plan` → `adapter=codex`.
4. **Cleanup before boundary guard:** `find adapters -name __pycache__ -type d -prune -exec rm -rf {} +`
5. **Boundary guard (worktree only):** `bash tools/check-adaptation-boundary.sh` → exit 0.
6. **Zero regression** (run with bash):
   - `python3 utilities/dispatch_contract.test.py`
   - `python3 utilities/dispatch_node.test.py`
   - `python3 adapters/{claude,codex,opencode}/bin/dispatch-headless.sd45.test.py` (3)
   - `bash adapters/{claude,codex,opencode}/bin/dispatch-headless.sd15.test.sh` (3)

Gate: all of the above pass; no new output lines, exit codes, or cascade
branches changed vs. baseline.

## 5. Scope boundaries

**In scope:** path resolution in `utilities/dispatch-route.sh` (L28, L38, L103–104
+ one resolution block); projection regression test in
`utilities/dispatch-route.test.sh`.

**Out of scope (do NOT touch):** `utilities/dispatch-defaults.py` (self-resolves);
SD-68 route compile sealing; `usage-check.sh`/`model-map.sh` internal logic;
selector cascade semantics; permission classifier; `spec/**`; worker-route-guard.

## 6. Inputs

- source: `utilities/dispatch-route.sh`
- test: `utilities/dispatch-route.test.sh`
- spec: `.agent_reports/spec/stage-dispatch/prd.md` §13.8.1 (SD-66)
- route: `.agent_reports/plans/2026-07-19_selector-paths/_internal/route.json`

## 7. Files changed (execute stage)

1. `utilities/dispatch-route.sh` — add resolution block; rewrite 4 helper paths.
2. `utilities/dispatch-route.test.sh` — add projection-surface block.

Both are real repo files; the `adapters/**/utilities/*` symlinks pick up the
change automatically (no separate edit). Two files, ~10 changed lines total.
