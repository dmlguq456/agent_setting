# Step log — Multi-spec awareness for the spec-read gate

Plan: `plan/plan.md` · Checklist: `checklist.md`
Worktree: `/home/Uihyeop/agent_setting-wt/spec-gate-multi-spec` (branch `spec-gate-multi-spec`)
Safety commit: `4272eba8a70bdf0413b2665168ede39c8d36b729` (working tree was clean at entry — no checkpoint commit needed, nothing to snapshot)

All five plan phases were executed in order, in-session (no `dev-team` delegation — the edits are precise POSIX-sh structural changes with byte-for-byte parity requirements that benefit from direct, single-pass control rather than a second agent hop).

## Phase 1 — Core contract wording

- `core/HOOKS.md` L46 `spec read gate` row: portable-meaning cell reworded to name the governing candidate set (root `spec/prd.md` or a one-level `spec/<slug>/prd.md`, `_internal` excluded) with per-candidate same-session freshness. Adapter cell (CLI signatures) untouched.
- `core/WORKFLOW.md` L332 §7 step 0: hard-gate sentence reworded to name candidates rather than the root PRD only; governance (which candidate governs) stays agent judgment, recorded via route-record `spec_read.source`. Stayed a single numbered item.

Commit: `395a797c docs(core): widen spec read gate to a governing candidate set`

## Phase 2 — `hooks/spec-read-marker.sh`

`mark_read()` now branches on two shapes:
- Exact root path (`*/.agent_reports/spec/prd.md`, `*/.claude_reports/spec/prd.md`, kept verbatim) → `slug=""`.
- Otherwise, a structural depth check (`dirname` chain, not a `case` glob — `*` matches `/`, so a literal glob would also swallow `spec/<slug>/_internal/versions/v1/prd.md`): requires `basename == prd.md`, `basename(dirname(dirname(fp))) == spec`, `basename(dirname(dirname(dirname(fp))))` in `{.agent_reports,.claude_reports}`, and `slug != _internal`.

`file_root` is derived per-branch (`[ -z "$slug" ]` guard) rather than by reusing `d1/d2/d3` from the root branch, per plan-review B2 — the root branch never computes those variables and the script has no `set -u`, so a shared reference would have silently corrupted `file_root` to `.`.

Canonical comparison target is `$canonical/spec/prd.md` (root) or `$canonical/spec/$slug/prd.md` (sub-spec); the physical `cd … && pwd -P` comparison is unchanged, so the canonical-vs-worktree-shadow behavior is untouched.

Marker filenames: root keeps the frozen `${sid}__${key}` exactly; sub-specs get `${sid}__${key}__${slug_key}` with `slug_key` sanitized via the same `sed 's#[/ ]#_#g'`.

Verify: `sh -n hooks/spec-read-marker.sh` clean; `*) fp="$PWD/$fp" ;;` (boundary-asserted string) still present verbatim.

## Phase 3 — `hooks/spec-skill-gate.sh`

`find_prd()` now builds a newline-separated `candidates` path list instead of a single `prd`/`root` pair: the root `spec/prd.md` if present, plus every `spec/<slug>/prd.md` from `for d in "$artifact_root"/spec/*/` (guarding the literal no-match with `[ -d "$d" ] || continue`, skipping `_internal`). Accumulated as paths only (plan-review N3: avoids the `<slug>\t<path>` empty-field parsing trap for the root candidate's empty slug). `root` is set from `dirname "$artifact_root"` only when at least one candidate exists; an empty candidate set is the unchanged "not spec-backed" PASS.

`check_gate()` iterates the candidate list with a plain `for candidate in $candidates` loop under a temporarily newline-only `$IFS` (restored on every iteration and after the loop) — deliberately not a `while read` pipeline or any subshell, since a subshell there would make a satisfied candidate's `return 0` exit only the subshell (plan-review N2), producing a false deny. Each candidate's marker name is re-derived from its own path shape (root vs `<slug>` parent dir), matching Phase 2. A candidate is satisfied iff its marker file exists and `cur <= read_mtime`; the first satisfied candidate returns 0 immediately (ANY-satisfied semantics). If none are satisfied, the loop tracks `any_marker` (whether any candidate had a marker at all, fresh or stale) to select the message family, and `unsatisfied` (all unsatisfied candidate paths) for the enumerated list.

Message builder: exactly one total candidate reproduces today's two deny strings verbatim, including the raw `$prd` interpolation — confirmed byte-for-byte via a dedicated parity test (scenario e below). More than one candidate emits a single-line, comma-space-joined enumeration of every unsatisfied candidate path plus the phrase "Read the one governing the declared work scope" (capital R, sentence-initial), preserving "A code comment or brief quotation does not satisfy the gate." and the drift-retry wording. `deny_json`'s raw-interpolation contract (no newline/quote/backslash) holds since paths and boilerplate contain none.

CLI/stdin plumbing (argument parsing, `reason`/`return 2`/exit-code contract) is untouched, so the codex/opencode `preflight.sh read|route|gate` callers are unaffected.

Verify: `sh -n hooks/spec-skill-gate.sh` clean; manual smoke test against an isolated `$TMP`/`$AGENT_HOME` (with `AGENT_ARTIFACT_ROOT` explicitly unset — it is preset in this worker's environment and would otherwise silently redirect candidate resolution to the primary checkout's real artifact root) covering sub-spec pass, `_internal` exclusion, no-read enumeration, drift, and root-only parity — all passed before touching the test suite.

## Phase 4 — `hooks/portable-guards.test.sh`

Added a new `== spec read gate: multi-spec candidate set ==` block immediately after the existing `$TMP/specproj`/`$TMP/canonical-spec` block (left byte-for-byte untouched as the root-only regression baseline). New `$TMP/multispec` fixture: root + `alpha` + `beta` + `alpha/_internal/versions/v1/prd.md`. Each scenario uses its own session id (`msubsid`, `msinternalsid`, `msnoreadsid`, `msdriftsid`, `msparitysid`, `mslegacysid`) per plan-review B1 — a shared id would make every deny assertion vacuous under the ANY-candidate rule.

- a. sub-spec read → gate passes.
- b. `_internal/versions/v1/prd.md` read → asserted absence of any `msinternalsid__*` marker file, and the gate still denies (exit 2).
- c. no read at all → exit 2, and stderr is grepped for all three concrete candidate paths plus the phrase "Read the one governing the declared work scope".
- d. sub-spec drift → fresh read passes, `sleep 1` + touch denies, re-read passes again.
- e. root-only parity → a **fresh** session id (`msparitysid`, distinct from `testsid` which already holds a marker) against the existing `$TMP/specproj` fixture, asserting the deny stderr matches today's exact single-candidate string.
- f. legacy `.claude_reports` sub-spec, in its own `$TMP/legacyspec` fixture directory (not reusing `$TMP/multispec`, since the resolver prefers `.agent_reports` when both exist in the same tree).

One bug found and fixed during this phase: scenario c's grep initially checked for lowercase "read the one governing the declared work scope", but the actual message is sentence-initial ("Read the one governing…"), so the grep never matched. Fixed the test's grep string, not the hook — the hook's capitalization is correct English for a sentence start.

Verify: `sh -n hooks/portable-guards.test.sh` clean; the boundary-asserted test name `codex read wrapper resolves relative prd paths for spec gate` is still literally present (untouched, upstream of the new block).

Full-suite run from inside the worktree (never the primary checkout, per the hard constraint): `PASS=355 FAIL=13`. Confirmed via `git stash` / `git stash pop` A-B that all 13 failures (codex/opencode dispatch-wrapper and harvest-wrapper tests) are **pre-existing** on unmodified `HEAD` — same 13 names fail with none of this plan's changes applied. They are unrelated to the spec-read gate. Every new multispec assertion and every pre-existing spec-gate assertion passes.

## Phase 5 — Claude plugin mirror + adjacent verification

- `python3 adapters/claude/bin/sync-native-plugin.py` (no-arg sync) — regenerated the mirror; `--check` exits 0.
- `bash tools/check-adaptation-boundary.sh` — `OK: adaptation boundary checks passed` (both verbatim-string assertions hold).
- `python3 tools/build-manifest.py --check` — `manifest up-to-date; delta baselines bound` (no manifest edit needed, as predicted — hook entries carry no body hash).

## Commits (core-first order, per `hooks/core-first-guard.sh`)

1. `395a797c docs(core): widen spec read gate to a governing candidate set` — `core/HOOKS.md`, `core/WORKFLOW.md`.
2. `8496bf90 feat(hooks): accept root or one-level sub-spec reads in the spec gate` — `hooks/spec-read-marker.sh`, `hooks/spec-skill-gate.sh`, `hooks/portable-guards.test.sh`, and the resynced Claude plugin mirror.

## Behavior delta (deliberate, per plan §4 Risks)

A repo with one or more sub-specs but **no** root `spec/prd.md` previously resolved to "not spec-backed" (PASS, unconditionally). Under the new candidate set it is now **gated**: the sub-spec candidates make the set non-empty, so a session must read at least one governing sub-spec before an `autopilot-code`/`autopilot-spec` call proceeds. This follows directly from the plan's stated intent (any sub-spec is a valid governing candidate) but is a real behavior change worth flagging — no such repo shape exists in this repo today (a root `spec/prd.md` is always present alongside sub-specs), so it did not surface in the existing suite.

## Deviations from the plan

None. All phases, verification commands, and constraints (worktree-only guard runs, verbatim-string preservation, deny-JSON single-line reasons, frozen root marker name, core-first commit order) were followed as specified. The plan-review's two blocking corrections (B1 session-id isolation, B2 unset-variable reuse) were already folded into the plan text and implemented as specified; no further correction was needed during execution.
