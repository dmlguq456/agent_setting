# Test report — Multi-spec awareness for the spec-read gate

- Mode: qa-team `test` (native-subagent fallback hop for the `code-test` stage of cycle `2026-07-16_spec-gate-multi-spec`; registered headless dispatch is unavailable — route guard fail-closed, already documented).
- Source (read-only): worktree `/home/Uihyeop/agent_setting-wt/spec-gate-multi-spec` @ HEAD `8496bf90` (change commits `395a797c` core + `8496bf90` hooks; base `4272eba8`).
- All guard runs executed **inside the worktree**, never the primary checkout (hard constraint — primary run rotates the live dispatch broker).
- **Final verdict: PASS.**

---

## Level 1 — Syntax / static (POSIX sh)

| Check | Command | Result |
|---|---|---|
| marker hook parse | `sh -n hooks/spec-read-marker.sh` | OK |
| gate hook parse | `sh -n hooks/spec-skill-gate.sh` | OK |
| test file parse | `bash -n hooks/portable-guards.test.sh` | OK (bash script by shebang) |
| bashism review (both hooks) | manual read | Clean — only `case`, `[ ]`, `printf`, `dirname`/`basename`, `$(( ))` arithmetic, `tr`/`sed`, and IFS save/restore. No `[[ ]]`, `local`, arrays, or process-substitution. Newline-`IFS` candidate loop is POSIX. |

## Level 2 — Import / plumbing

Shell hooks, no import graph. CLI/stdin plumbing (`spec-skill-gate.sh` L136-198) is untouched by the diff; deny path exits `2` on CLI and emits `deny_json` (exit 0) on the stdin/hook path — the exit-code contract the codex/opencode `preflight.sh read|route|gate` callers depend on is preserved. Confirmed by reading the unchanged plumbing block.

## Level 3 — Smoke

Direct hook invocation against an isolated, hermetic fixture (`AGENT_HOME` redirected to a scratch dir, `AGENT_ARTIFACT_ROOT` unset so candidate resolution stays inside the fixture). Root-spec read → marker written → gate passes; empty candidate set → unchanged PASS. OK.

## Level 4 — Functional (multi-spec semantics, from plan §5 + verification requirements)

Two evidence paths, both green: (1) the suite's new `== spec read gate: multi-spec candidate set ==` block, and (2) an **independent** hermetic re-derivation of every required scenario (not just echoing the suite). Independent run used `AGENT_HOME=<scratch>`, `AGENT_ARTIFACT_ROOT` unset, distinct fixtures under `/tmp`.

| # | Scenario | Expected | Observed | Verdict |
|---|---|---|---|---|
| a | sub-spec `spec/alpha/prd.md` read → marker → gate | pass (exit 0); marker `${sid}__${key}__alpha` | exit 0; marker `A__<key>__alpha` present | PASS |
| b | `spec/alpha/_internal/versions/v1/prd.md` read | no `${sid}__*` marker written; gate still denies | 0 markers for sid; gate exit 2 | PASS |
| c | no read at all | exit 2; deny lists **every** candidate path + phrase "Read the one governing the declared work scope"; single line | exit 2; all 3 candidate paths + phrase present; `wc -l` = 1 | PASS |
| d | sub-spec drift (read → `sleep 1` → touch) | pass, then deny (exit 2), then pass after re-read | 0 → 2 → 0; drift message is the multi-candidate "One or more governing spec candidates changed…" variant | PASS |
| e | root single-spec repo, fresh sid | deny message **byte-for-byte** identical to pre-change single-candidate string | exact match (`[ "$msg" = "$expected" ]` true) | PASS |
| e' | root single-spec marker name | exactly `${sid}__${key}`, **no** slug suffix (backward compat) | `E__<key>` (no suffix); gate passes after read | PASS |
| f | legacy `.claude_reports` sub-spec | read → gate passes | exit 0; marker `F__<key>__gamma` | PASS |

Deny-message single-line contract (deny_json interpolates raw → no newline/quote/backslash): confirmed single physical line for both the no-read and drift enumerated variants.

## Level 5 — Integration (full guard suite, in worktree)

`bash hooks/portable-guards.test.sh` — run twice:

| Run | PASS | FAIL | Multi-spec block | Spec-gate failures |
|---|---|---|---|---|
| 1 | 358 | 10 | 9/9 ok | none |
| 2 | 357 | 11 | 9/9 ok | none |

All FAILs in both runs are in the **codex/opencode/claude dispatch-wrapper, harvest-wrapper, and doctor-runtime-strict** subsystem. The failing set is **non-deterministic** — count 10→11 and membership shifts across runs (run 2 adds `codex doctor --runtime-strict should require and accept complete hook trust`). This diff edits no dispatch/harvest/doctor code (changed files: `hooks/spec-read-marker.sh`, `hooks/spec-skill-gate.sh`, the `+88`-line multispec block appended after L356 of the test file, `core/HOOKS.md`, `core/WORKFLOW.md`, and the two byte-identical plugin mirrors). Conclusion: pre-existing flaky failures, unrelated to the spec-read gate. (Note: the dev-log's fixed "FAIL=13, same 13 names" characterization was not reproduced exactly — the failures are actually flaky in both count and membership — but the kind and the "unrelated to this plan" conclusion hold and are corroborated.)

## Adjacent verification (mirror parity, boundary, manifest, core wording)

| Check | Command | Result |
|---|---|---|
| mirror byte-diff (marker) | `diff hooks/… adapters/…/plugins/agent-harness-claude/hooks/spec-read-marker.sh` | identical (0 bytes) |
| mirror byte-diff (gate) | `diff … spec-skill-gate.sh` | identical (0 bytes) |
| mirror generator | `sync-native-plugin.py --check` | exit 0 |
| adaptation boundary | `check-adaptation-boundary.sh` | `OK: adaptation boundary checks passed` |
| verbatim string 1 | `grep -F '*) fp="$PWD/$fp" ;;' hooks/spec-read-marker.sh` | present |
| verbatim string 2 | `grep -F 'codex read wrapper resolves relative prd paths for spec gate' …test.sh` | present |
| manifest drift | `build-manifest.py --check` | `manifest up-to-date; delta baselines bound` |

**Core wording ↔ implementation:** consistent.
- `core/HOOKS.md` "governing spec candidate — root `spec/prd.md` or a one-level `spec/<slug>/prd.md` sub-spec (`_internal` excluded); per-candidate freshness, marker mtime ≥ candidate mtime" matches: `find_prd` builds root + one-level `spec/*/` candidates (skips `_internal`); satisfaction is `cur <= read_mtime`.
- `core/WORKFLOW.md` §7 step 0 "reading the spec that governs the declared work scope … is a hard gate; which candidate governs remains agent judgment via `spec_read.source`" matches the ANY-satisfied gate semantics (deterministic gate only enforces that a current project spec was read; governance stays judgment).

## Observations (non-blocking)

1. **Deliberate behavior delta confirmed (informational).** A repo with sub-specs but **no** root `spec/prd.md` was previously "not spec-backed" → unconditional PASS; it is now **gated**. Follows the plan's stated intent (plan §4); flagged for release notes, not a defect. No such repo shape exists here today.
2. **Raw JSON interpolation of candidate paths (pre-existing, low severity).** `deny_json` interpolates the enumerated path list raw into JSON; a spec slug/path containing `"` or `\` would break the JSON reason. This is the same raw-interpolation property the pre-change code already had for `$prd` (no regression) and is acknowledged in plan constraint 3 / §4. Out of this task's scope; noted for awareness.

## Verdict

**PASS.** Syntax clean and POSIX; all six required multi-spec semantics verified both independently and via the suite; root single-spec byte-for-byte parity and frozen `${sid}__${key}` marker name preserved; mirror byte-identical; boundary/manifest/core-wording all consistent. The only suite failures are pre-existing, non-deterministic dispatch/harvest/doctor flakiness untouched by this diff.
