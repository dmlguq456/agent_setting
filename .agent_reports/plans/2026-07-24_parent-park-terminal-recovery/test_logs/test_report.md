# Test report

## Focused behavior

- `utilities/codex-parent-park.test.py`: **10/10 PASS**
  - ordinary open/running remains parked
  - ordinary terminal live and terminal-unverifiable release the global tool park
  - explicit poll terminal live/unverifiable remains parked
  - supervised terminal-unverifiable remains strict
  - quiescent terminal, foreign parent, and no-registered-child/native-only cases release
  - hook leaves the registry byte-identical and does not signal the live process
- `utilities/dispatch_completion_join.test.py`: **8/8 PASS**
- `utilities/dispatch-wait.test.sh`: **17 conformance checks PASS**
- `utilities/worktree-cleanup.test.py`: **11/11 PASS**
- `utilities/registered_parent_park.test.py`: **4/4 PASS**

## Boundaries

- `tools/check-adaptation-boundary.sh`: **PASS** (documented 129-reference warning only)
- `tools/build-manifest.py --check`: **PASS**, manifest up to date
- `preflight.sh subagent-info --check`: **PASS**, Codex native `multi_agent` surface available
- Python syntax/AST and `git diff --check`: **PASS**

## Portable baseline comparison

`hooks/portable-guards.test.sh` is not green on the pre-change main tree:
`PASS=327 FAIL=29`. The source branch produced the same counts, and a direct diff of
all 29 `BAD` descriptions was empty. The failures are existing governor-root/context
fixture drift across Codex/Claude/OpenCode dispatch tests; this change adds **0** new
portable guard failures.

## Verdict

## Integrated main smoke

- source commit `a9462fc1` fast-forwarded to main
- installed runtime projection: **status=ok**
- strict hook trust requirement: **check=hook-trust:ok**
- current-session hook invocation with `AGENT_PARENT_PARK_BYPASS` removed and the
  canonical jobs registry selected: **exit 0, stdout empty, stderr empty**
- the 50 focused checks were rerun on integrated main: **all PASS**

Verdict: **PASS**. Main push and guarded worktree cleanup remain.
