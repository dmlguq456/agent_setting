# Integration Verification

Final post-hardening matrix:

- AST parse, 8 files: PASS
- Phase 2 focused, 21 tests: PASS
- Phase 3 focused, 10 tests: PASS
- Fleet discovery, 221 tests: PASS
- portable guards: `PASS=344 FAIL=0`
- adaptation negative guard: PASS, baseline restored
- adaptation boundary: PASS, 56 documented warnings
- manifest check: PASS
- repository doctor: PASS
- git diff check: PASS
- production dynamic absence, 4 paths x 3 needles: PASS
- canonical/Claude parity, 9 pairs: PASS
- Codex utility symlink and OpenCode defer: PASS
- adapter pycache pollution: absent

Candidate SHA-256:
`11288b737241598dcf585eb762cfc033f3cbcca70eee6ff583cb6065f6de3606`.

The portable suite was run in an isolated `/tmp` because unrelated active
worktrees overwrite legacy fixed capture files. The final run also bound the
normal main `.dispatch/logs` fallback writable and passed 344/344.

Fixtures are synthetic/non-evidentiary. This verification does not satisfy the
real paired `n>=30` adoption gate.
