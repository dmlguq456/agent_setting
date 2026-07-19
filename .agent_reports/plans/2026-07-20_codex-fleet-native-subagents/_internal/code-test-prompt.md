# Code-test stage body

Independently verify the existing Codex native-subagent collector diff against
F-29 and the approved plan. Run focused Codex fixtures, Claude/OpenCode and
render/JSON regressions, the full Fleet suite, mirror byte parity, manifest and
adaptation-boundary checks, and a read-only live smoke. Record exact outcomes,
including any worker-environment limitation, in canonical `test_logs/` and an
independent review under `_internal/test_reviews/`. Do not modify runtime state.
