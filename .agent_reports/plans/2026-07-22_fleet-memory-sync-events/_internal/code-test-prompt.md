This is only the independent `test` node (`code-test` / `qa/test`) of route `rt-d7392fcfbc9ce241`. Do not edit source/tests/specs, dispatch, commit, or push.

Verify the actual diff after an impl-review PASS against the plan, checklist, D-37 v22, Fleet F-19/F-35f v15, execute evidence, and code-review artifact. Run at minimum:

- the new focused sync/migrate journal regression(s);
- `bash tools/memory/mem_cluster_j.test.sh`;
- `python3 -m unittest tools.fleet.tests.test_f19_memory -v`;
- relevant memory unit/integration tests discovered from the diff;
- Python syntax/import checks for edited modules;
- `python3 tools/generate.py --check` and `sh tools/check-adaptation-boundary.sh` when projection ownership is touched;
- `git diff --check` and a source-scope/status audit.

Independently prove: hostile env still yields literal sync + source cwd; first INSERT emits one; repeat/upsert/dedup/no-backfill emit zero; unknown cwd is omitted; an `agent-note`-like source is grouped under `by_repo["agent-note"]`; existing manual event behavior is unchanged. Record exact commands, counts, failures, and residual risks in `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/test_logs/verification.md`. Complete the exact marker/attempt only on PASS, then return the kernel's exact three-line handoff.
