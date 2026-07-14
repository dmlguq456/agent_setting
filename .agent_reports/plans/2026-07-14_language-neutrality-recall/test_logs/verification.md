# Verification log

All commands ran through the Codex verification-runner contract unless noted.

- `python3 -m py_compile tools/memory/mem.py adapters/claude/bin/dispatch-headless.py adapters/codex/bin/dispatch-headless.py` — pass.
- `bash hooks/mem-recall-inject.test.sh` — PASS=18, FAIL=0.
- `bash tools/memory/mem_retrieval_v14.test.sh` — PASS=22, FAIL=0.
  The regressions prove semantic auto-recall is retired, Korean particle/CJK
  recall remains intact, and malformed UTF-8 telemetry cannot break explicit
  recall.
- `python3 tools/build-manifest.py --check` — pass; manifest and delta baselines
  are current.
- Claude plugin, Codex skills/plugin/agents/modes, and OpenCode
  skills/commands/agents generator `--check` commands — pass.
- `tools/skill-conformance/check.sh` — pass, 26 classifications.
- `tools/check-adaptation-boundary.sh` — pass. The existing informational warning
  about 52 documented concrete runtime/model references remains.
- `bash hooks/portable-guards.test.sh` — PASS=343, FAIL=0.
- `git diff --check` — pass.
- Ownership scan — no changes under `README.md`, `INSTALL_LAYOUT.md`, or
  `tools/install/**`.

The generic `skill-creator` `quick_validate.py` was also attempted. It rejects
this repository's established `argument-hint` frontmatter extension before
content validation, so it is not the applicable validator here. The repository
contract was validated instead by `tools/skill-conformance/check.sh`, byte-level
Claude compatibility comparison, all native generator checks, and the full
adaptation boundary/portable guard suites.

One initial adaptation-boundary run found only a Python bytecode cache generated
by the syntax check. The cache was removed and the clean rerun passed.
