# Final verification

All commands below passed on the clean integrated feature tree unless noted.

- `utilities/artifact-root.test.sh`: 5 resolver cases passed.
- `python3 utilities/dispatch-artifact-root.test.py`: 3 adapter dispatch cases
  passed.
- `python3 utilities/worktree-cleanup.test.py`: 9 cleanup state-machine cases
  passed, including missing-upstream and push-pending vetoes.
- `bash tools/generated-projections.test.sh`: deterministic projections passed;
  the embedded report-figure semantic suite passed 29/29.
- `bash hooks/portable-guards.test.sh`: 348 passed, 0 failed after merging the
  current `origin/main` into the feature tree.
- `bash tools/check-adaptation-boundary.sh`: passed.
- `python3 tools/generate.py --check`: passed on the clean integrated tree.
- Codex and OpenCode adapter doctors: passed on the clean integrated tree.
- Installed Codex runtime projection: `status=ok`, plugin skill discovery,
  9/9 agent links, modes/hooks/bootstrap/plugin all verified.
- Main post-merge cleanup tests: resolver 5, dispatch 3, cleanup 9 all passed.
  Main's generator check was intentionally not used as final evidence because
  a separate active change to `hooks/mem-distill-dispatch.sh` causes its delta
  baseline drift; that unrelated work was preserved. The same merged commit
  passed the generator check in the clean feature worktree.
- Dogfood cleanup: check returned `status=eligible`; apply returned
  `status=removed`, `branch_deleted=0`, `artifact_harvest_required=0`.
