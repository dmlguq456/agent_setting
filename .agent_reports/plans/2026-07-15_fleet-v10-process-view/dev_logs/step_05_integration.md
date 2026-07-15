# Step 5 — integration verification · mirror sync

## V1 — full regression
`python3 -m unittest discover -s tools/fleet/tests -t .` → **515 tests, OK** (baseline 468 + 47
new: 20 route + 6 breadcrumb + 15 process-view + 6 governor). **0 regressions** among the
pre-existing 468.

## V2 — 3-width × 2-view `--once` captures
Raw captures: `dev_logs/step_05_v2_captures.txt` (moved here from a `test_logs/` draft location
— that path is the **test** node's write_scope per the real route record, not execute's;
relocated to stay inside `source/**`/`dev_logs/**`, the execute node's actual write_scope).

Overflow check (`east_asian_width`-based `_dw` reimplementation, independent of render.py's own
`_dw` to cross-check): **0 overflow in any F-30 process-view CARD line**, all 3 widths. The only
overflowing lines at 60 columns are in the **group view's pre-existing shared header** (usage
gauges, pulse row, legend) — confirmed present and unchanged in the group-view capture too, so
this is inherited baseline behavior, not a v10 regression (see Step 3 dev_log for the original
finding).

## V3 — design critic
**Deferred to code-test**, per the plan's own assignment (plan.md §7 V3: "산출: … ← code-test
스테이지가 수행/수확"). The V2 captures above are the critic's required input; they are ready.

## V4 — `--json` additive
```
keys: ['governor', 'jobs', 'memory', 'route', 'sessions', 'summary']
route entries: 6   (all real, live route records currently in this environment's jobs.log)
governor: {'active': 1, 'cap': 5, 'classes': {'dispatch': 1}}
jobs[0] additive keys present: route_file / route_id / route_hash / route_node
gate_passed key: ABSENT (verified via full-payload string search — I11)
```
Existing top-level keys (`sessions`/`jobs`/`summary`/`memory`) unchanged in shape; `route`/
`governor` are new top-level keys; `jobs[]` elements gained 4 new `Optional` keys. No existing
key removed, renamed, or reshaped.

## V5 — mirror sync
`rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/` run twice
(once mid-cycle, once final after the I2 fix below) — `test_mirror_parity` passes: canonical and
mirror trees are byte-identical, including all new `.py` files and every `tests/fixtures/route/*`
fixture.

## G3 — read-only static gate
```
grep -nE "open\(.*['"]w|write_text|os\.replace|\.write\(" tools/fleet/route.py tools/fleet/collectors/governor.py
grep -nE "open\(.*['"]w|write_text|os\.replace|\.write\(" adapters/claude/tools/fleet/route.py adapters/claude/tools/fleet/collectors/governor.py
```
Both → **0 lines of output** (canonical and mirror). The docstring in `route.py` was reworded
mid-cycle because its OWN prose (quoting the banned patterns as English text, e.g. `` `open(...,
"w")` ``) tripped this exact grep — a false positive from the gate matching its own
documentation, fixed by describing the patterns in words instead of literal code snippets.

## Bug found during this sweep: `route.load()` raised on a non-path-like input (I2 violation)
`os.path.abspath(123)` raises `TypeError` — `route.load()` had no guard against a caller passing
a non-str/bytes/PathLike value. This can only be reached today via a defensive/malformed caller
(every real pipe field is text), but I2 ("load()는 어떤 입력에도 raise하지 않는다") is
unconditional, not "raise-free for realistic inputs only." Fixed: `load()` now checks
`isinstance(path, (str, bytes, os.PathLike))` up front and wraps the `abspath`/`stat` call in
`except (OSError, TypeError, ValueError)`. Added `test_t1_3b_non_path_like_input_never_raises`
(fuzzes `int`/`float`/`dict`/`list`/`object()`/`bytes`/`tuple`) to `test_f28_route.py` — the full
suite was rerun and mirror resynced after this fix (515 tests, still 0 regressions).

## Invariant sweep (plan §8, I1–I11)
| # | Invariant | Verified how |
|---|---|---|
| I1 | record 없는 환경 = v9와 동일 | T2-1 (breadcrumb byte-match against the old code path directly) + T3-1 (process-view-off = group view unaffected) + 0 regressions across the 468-test baseline |
| I2 | `route.load()` never raises | T1-3/T1-3b/T1-5/T1-6/T1-7 (missing file, non-path types, broken hash, bad schema, pipe mismatch) — **1 real bug found + fixed this step** |
| I3 | route record write 0 | G3 grep, 0 lines, both trees |
| I4 | 노드 점등 = 자식 실측 | T1-14 (`●` beats a `done` registry row), T2-4 (record with 0 live children stays unlit) |
| I5 | `--json` 기존 키 불변 | V4 above + `test_t1_16`/`test_t1_17` |
| I6 | kill 경로 = `_handle_prompt_key` 하나 | `control.py` diff = **empty** (git status confirms 0 changes); process view's job rows reuse `_SELECTABLE`/`_CLICK_ROWS` unmodified |
| I7 | `_FOLD_ROWS ∩ (_CLICK_ROWS ∪ _TOGGLE_ROWS) = ∅` | Structural (fold-row check runs FIRST and exclusively in `_draw`'s row loop, before the toggle-text check) + T3-9/T3-9b |
| I8 | governor lease 카운트 미혼입 | `_governor_segs()` is a separate line/function; never touches `n_wk`/`n_id`/job counts — code-level inspection + `test_f28c_governor.py` (collector-only, no pulse coupling) |
| I9 | 실세션 스폰·signal 0 | No `subprocess`/`Popen`/`os.system`/`os.spawn*` call anywhere in `route.py`/`governor.py`/`demo.py` (grep-verified); every route/governor test uses `tempfile.TemporaryDirectory` + `mock`, never a real `claude`/`codex`/`opencode` process |
| I10 | spec 미변경 | `git diff --stat spec/` → empty |
| I11 | gate 통과 추측 금지 | No `gate_passed` key anywhere in `--json` output (V4) or in any card glyph; `route.py`'s node view carries `gate` (name only) — see `_internal/carryover.md` §1 |

All 11 hold.

## Final numbers
- Tests: **468 → 515** (+47), 0 regressions.
- New files: `tools/fleet/route.py`, `tools/fleet/collectors/governor.py`,
  `tools/fleet/tests/test_f28_route.py`, `tools/fleet/tests/test_f28_breadcrumb.py`,
  `tools/fleet/tests/test_f30_process_view.py`, `tools/fleet/tests/test_f28c_governor.py`,
  `tools/fleet/tests/fixtures/route/*` (8 files) — all mirrored byte-identically.
- Modified files: `tools/fleet/{model.py,fleet.py,demo.py,render.py,collectors/dispatch.py}` —
  all mirrored byte-identically.
