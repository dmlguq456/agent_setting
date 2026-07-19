# Checklist — Multi-spec awareness for the spec-read gate

Safety commit: 4272eba8a70bdf0413b2665168ede39c8d36b729

spec-significance: within-spec (gate-contract change in core/, no spec/** PRD mutation)

Plan: `plan/plan.md` · Review: `_internal/plan_reviews/round_1.md`
Worktree (all edits + all runs): `/home/Uihyeop/agent_setting-wt/spec-gate-multi-spec`

> **Hard constraint — never violate.** `hooks/portable-guards.test.sh` and any guard suite run ONLY inside the worktree above, NEVER against the primary checkout `/home/Uihyeop/agent_setting` (a guard run on primary rotates the live dispatch broker, measured 2026-07-15).

Phases are strictly ordered. Do not start a phase before the previous one verifies.

## Phase 1 — Core contract (must land before any hook edit)

- [x] 1.1 `core/HOOKS.md` L46 `spec read gate` row — portable meaning names the governing candidate set (root `spec/prd.md` or one-level `spec/<slug>/prd.md`, `_internal` excluded) with per-candidate same-session freshness. Minimal English delta; CLI signatures in the adapter cell unchanged; cell stays one line.
- [x] 1.2 `core/WORKFLOW.md` L332 §7 step 0 — hard-gate sentence names candidates, not the root PRD only; governance stays agent judgment + route-record `spec_read.source`. Paragraph stays a single numbered item.

## Phase 2 — `hooks/spec-read-marker.sh`

- [x] 2.1 Generalize `mark_read()` path acceptance to root + one-level sub-spec via the **structural depth check** (not a `case` glob — `*` matches `/`). Keep L23-26 verbatim. No early `*/_internal/*` guard. Exclude `slug = _internal`.
- [x] 2.2 Derive `file_root` **inside each branch** — root uses the existing 3× `dirname` expression; sub-spec uses `dirname "$d3"`. **Never** reference `d1/d2/d3` from the root branch (no `set -u` ⇒ silent `dirname ""` → `.`).
- [x] 2.3 Canonical target `"$canonical/spec/$slug/prd.md"` for sub-spec; physical `pwd -P` comparison unchanged.
- [x] 2.4 Marker names: root **exactly** `${sid}__${key}` (frozen); sub-spec `${sid}__${key}__${slug_key}` with `slug_key` sanitized by `sed 's#[/ ]#_#g'`. `mtime` still stored at read time.
- [x] 2.5 `sh -n hooks/spec-read-marker.sh` clean.

## Phase 3 — `hooks/spec-skill-gate.sh`

- [x] 3.1 `find_prd()` builds the candidate set: root `spec/prd.md` + `for d in "$artifact_root"/spec/*/` (guard the literal no-match with `[ -d "$d" ] || continue`, skip `_internal`, require `[ -f "$d/prd.md" ]`). `root=$(dirname "$artifact_root")` when any candidate exists. Empty set → unchanged PASS. No `while read` in a pipeline.
- [x] 3.2 `check_gate()` — candidate satisfied iff marker exists AND `cur <= read_mtime`; ANY satisfied → `return 0`; none → `return 2` with `reason` set on **every** deny path. Track "any marker at all" to pick the not-read vs drift message family.
- [x] 3.3 Message builder branched on candidate count. **Single candidate → today's strings verbatim** (byte-for-byte parity, incl. `$prd` interpolation). N>1 → comma-space-joined single-line candidate list + "Read the one governing the declared work scope", preserving "a quotation does not satisfy the gate" and the drift-retry wording. **No newline, no `"`, no `\`** — `deny_json` interpolates raw into JSON.
- [x] 3.4 CLI/stdin plumbing (L79-141) untouched — `reason`/`return 2`/exit-code contract unchanged so codex/opencode preflight callers stay green.
- [x] 3.5 `sh -n hooks/spec-skill-gate.sh` clean.

## Phase 4 — `hooks/portable-guards.test.sh`

- [x] 4.1 Existing `$TMP/specproj` block (L294-357) left **untouched** — it is the root-only no-regression evidence.
- [x] 4.2 New `$TMP/multispec` fixture (root + `alpha` + `beta` + `alpha/_internal/versions/v1/prd.md`), **one distinct session id per scenario** (`msubsid`/`msinternalsid`/`msnoreadsid`/`msdriftsid`/`msparitysid`/`mslegacysid`) — a shared sid makes every deny assertion vacuous under the ANY-candidate rule:
  - [x] a. sub-spec read → gate passes
  - [x] b. `_internal/versions/v1/prd.md` read → no `msinternalsid__*` marker written **and** gate still denies (exit 2)
  - [x] c. no read → exit 2 and stderr lists every candidate path + the governing-scope phrase
  - [x] d. sub-spec drift (`sleep 1`, touch) → deny until re-read, then pass
  - [x] e. root-only deny-message parity against today's exact text
  - [x] f. legacy `.claude_reports` sub-spec variant in a **separate** fixture dir (resolver prefers `.agent_reports` when both exist)
- [x] 4.3 Verbatim boundary string `codex read wrapper resolves relative prd paths for spec gate` (L328) still literally present.
- [x] 4.4 `cd <worktree> && bash hooks/portable-guards.test.sh` — new + pre-existing assertions all pass (FAIL=13 matches unmodified baseline; the 13 failures are pre-existing dispatch/harvest wrapper flakiness unrelated to this plan, confirmed via `git stash` A/B).

## Phase 5 — Claude plugin mirror (only after Phase 4 is green)

- [x] 5.1 `python3 adapters/claude/bin/sync-native-plugin.py` (no-arg = sync). Do **not** hand-edit the mirror. `hooks.json` command strings (AGENT_HOME env-prefix) unchanged.
- [x] 5.2 `python3 adapters/claude/bin/sync-native-plugin.py --check` exits 0.

## Verification gate (all from the worktree)

- [x] `sh -n hooks/spec-read-marker.sh` · `sh -n hooks/spec-skill-gate.sh`
- [x] `bash hooks/portable-guards.test.sh` — PASS=355 FAIL=13; the 13 failures are pre-existing (confirmed via `git stash` A/B against unmodified HEAD, same 13 names)
- [x] `python3 adapters/claude/bin/sync-native-plugin.py --check`
- [x] `bash tools/check-adaptation-boundary.sh` — incl. the two verbatim assertions at L961-964 (`*) fp="$PWD/$fp" ;;` in the marker hook; the codex-relative test name)
- [x] `python3 tools/build-manifest.py --check` — clean; no manifest edit was needed (hook entries carry no body hash)

## Report obligations

- [x] Surface the deliberate behavior delta: a repo with sub-specs but **no** root `spec/prd.md` is PASS today ("not spec-backed") and becomes **gated** under the new candidate set. (recorded in dev_logs/step_01_multispec_gate.md and plan §4)
- [x] Commit narrative order: `core/` before `hooks/` — `395a797c` (core) then `8496bf90` (hooks).

## Out of scope (do not touch)

Gate firing-point relocation (Skill entry → mutation surface) · codex/opencode preflight WRITE-gate sub-spec patterns · SD-45 route-record schema · any `spec/**` PRD edit · `.dispatch/` broker internals.
