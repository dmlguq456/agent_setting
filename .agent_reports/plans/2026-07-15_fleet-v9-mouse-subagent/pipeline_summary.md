# Pipeline summary (locked) — fleet v9 mouse-subagent cycle

- date: 2026-07-15
- capability: autopilot-code · intensity: standard · route: 4-node dispatch (plan → execute → test → report), all same-harness headless via ancestor-broker fallback (SD-50), 0 inline stages except 1 recorded exception
- scope: F-27 mouse-first select/kill, F-29 subagent observation (OpenCode child-session + Claude sidechain), D3 stage-zone width cap follow-up, scroll regression test
- tests: baseline 416 → 468 OK (52 new: 21 mouse + 15 subagents + 6 width-cap + 10 scroll). Mirror byte-identical.
- independent verification: test_review.md — PASS (conditional on glyph divergence), 22/22 acceptance items PASS, 0 blocking defects, 4 findings (1 yellow spec-divergence now resolved, 1 yellow OpenCode-honesty carry-forward, 2 green informational)
- inline exception: glyph `🔬`→`⚡` revert in render.py (2 lines), reason recorded in _internal/metrics.md, reproduced by conductor, re-verified 468 OK + mirror parity
- safety: 0 real claude/codex/opencode sessions spawned or signaled across the entire cycle; mouse events mocked via curses getmouse
- out of scope: F-28/F-30 (awaiting stage-dispatch v9 topology registry), D4 60-col truncation, 2 cosmetic critic suggestions
- carry-forward defects: OpenCode subagents permanently active=True (no completion signal in source); mirror-tree direct-run 3 pre-existing test failures (identical at HEAD, not a v9 regression)
- final report: final_report.md (Korean, user-facing)

This summary is locked — do not edit after write; supersede with a new cycle's summary file instead.
