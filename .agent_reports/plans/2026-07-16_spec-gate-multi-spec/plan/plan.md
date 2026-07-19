---
status: done
created: 2026-07-16
spec-significance: within-spec (gate-contract change in core/, no spec/** PRD mutation)
---

# Multi-spec awareness for the spec-read gate

## Goal

Make the deterministic spec-read gate accept a read of the **governing** spec — the root `spec/prd.md` **or** any one-level `spec/<slug>/prd.md` sub-spec — instead of demanding the root PRD only, while preserving fail-closed behavior, per-spec drift detection, and byte-for-byte identical messages for single-spec repos.

**Scope line:** spec-significance: within-spec (gate-contract change in core/, no spec/** PRD mutation)

Worktree (read + write target for source steps): `/home/Uihyeop/agent_setting-wt/spec-gate-multi-spec`

---

## 1. Current State Analysis

### 1.1 `hooks/spec-read-marker.sh` (99 lines)

`mark_read()` (L19-52) is single-path by construction:

- L23-26 — relative→absolute canonicalization: `*) fp="$PWD/$fp" ;;`
- L28-32 — accepts **only** `*/.agent_reports/spec/prd.md` and `*/.claude_reports/spec/prd.md`; everything else `return 0`
- L35 — `file_root` via 3× `dirname`
- L36-44 — resolve canonical artifact root through `utilities/artifact-root.sh`, then physically compare `fp` against `$canonical/spec/prd.md` (this is what makes a worktree-local shadow read not satisfy the canonical gate)
- L46-47 — `root=$(dirname "$canonical")`; `key=$(printf '%s' "$root" | sed 's#[/ ]#_#g')`
- L48 — `mtime=$(stat -c %Y "$fp")` stored at read time
- L50-51 — marker written to `$AGENT_HOME/.spec-grounding/${sid}__${key}`

### 1.2 `hooks/spec-skill-gate.sh` (142 lines)

- `find_prd()` (L22-37) — walks `$cwd` up to an existing dir, resolves artifact root, and sets globals `prd`/`root` **only if** `$artifact_root/spec/prd.md` exists.
- `check_gate()` (L39-72) — gates `autopilot-code|autopilot-spec` only (L48-51); `[ -z "$prd" ] && return 0` (L54) means "not a spec-backed project" = PASS; builds `key` from `root` (L56); reads marker (L57); `cur=$(stat -c %Y "$prd")` (L58); no-marker → `reason=...` + `return 2` (L60-63); drift `cur > read_mtime` → `return 2` (L66-69).
- `deny_json()` (L74-77) — **`printf '...%s...'` interpolates `$1` raw into JSON**. The reason must stay a single line with no `"`, no `\`, no newline.
- CLI path (L117-124) prints `$reason` to stderr and exits 2; stdin/hook path (L134-141) calls `deny_json`.

### 1.3 Contract docs

- `core/HOOKS.md` L46 — invariant row `spec read gate`, portable meaning currently: *"Spec-changing capability calls in spec-backed projects require a current `prd.md` read marker."*
- `core/WORKFLOW.md` L332 — §7 step 0: *"Reading `prd.md` is a hard gate in a spec-backed cwd. Adapter-native markers and gates deny entry to spec-changing capabilities when it has not been read in the current session or changed since the read."*

### 1.4 Test + mirror + boundary

- `hooks/portable-guards.test.sh` — bash, `set -u`, ~4010 lines. `ROOT`=repo root, `MARK="$ROOT/hooks/spec-read-marker.sh"`, `SPEC="$ROOT/hooks/spec-skill-gate.sh"`, `CODEX` wrapper, hermetic `export AGENT_HOME="$TMP/agent_home"`. The `== spec read gate CLI ==` block runs L294-357 with fixture `$TMP/specproj` (no-marker exit 2, non-gated pass, marker→pass, `sleep 1` drift→exit 2, codex wrapper, relative path L326-331, canonical-vs-worktree-shadow L333-357). `$TMP` is not a git repo → artifact-root.sh uses the non-git upward-discovery branch (same as existing specproj tests).
- `tools/check-adaptation-boundary.sh` L961-964 asserts two **verbatim** strings must exist: `*) fp="$PWD/$fp" ;;` in `hooks/spec-read-marker.sh`, and the test name `codex read wrapper resolves relative prd paths for spec gate` in `hooks/portable-guards.test.sh`.
- `adapters/claude/bin/sync-native-plugin.py` — `HOOKS_SOURCE = ROOT / "hooks"`; both hooks are in the adopted set; `sync()` uses `shutil.copy2`; `main()` takes `--check` (verify) and no-arg (sync).
- `tools/build-manifest.py` `main()` L656+ — confirmed flags: `--check`, `--adaptation-surface <kind>`, `--sync-baselines`. Hook entries carry slug/name/mono/event/hard_block only — **no body hash → no manifest regen needed** for hook body edits.

---

## 2. Change Plan

Phases are strictly ordered (core-first; `hooks/core-first-guard.sh` enforces it at runtime). Steps within a phase are sequential unless noted.

### Phase 1 — Core contract wording (MUST land before any hook edit)

**Step 1.1 — `core/HOOKS.md` L46, `spec read gate` row, "Portable meaning" cell.**
Replace the single-PRD phrasing with candidate-set phrasing. Minimal delta, English, keep the row's table shape and the existing "Non-Claude adapter requirement" cell (the CLI signatures do not change). Target meaning:

> Spec-changing capability calls in spec-backed projects require a current same-session read marker for at least one governing spec candidate — the root `spec/prd.md` or a one-level `spec/<slug>/prd.md` sub-spec (`_internal` snapshots excluded). Freshness is per candidate: the marker's recorded mtime must be at least that candidate's current mtime.

*Verify:* `grep -n 'spec read gate' core/HOOKS.md` shows the new cell; table renders as one line (no embedded newline in the cell).

**Step 1.2 — `core/WORKFLOW.md` L332, §7 step 0.**
Amend the hard-gate sentence so it names candidates rather than the root PRD only. Keep the surrounding orientation-order sentence untouched. Target meaning: reading the spec that governs the declared work scope — root `prd.md` or the relevant `spec/<slug>/prd.md` — is the hard gate; which candidate governs remains agent judgment recorded via route-record `spec_read.source`, while the deterministic gate only enforces that a current spec of this project was actually read this session.

*Verify:* `grep -n 'hard gate' core/WORKFLOW.md`; the paragraph stays a single numbered item.

### Phase 2 — `hooks/spec-read-marker.sh` (after Phase 1)

**Step 2.1 — Generalize `mark_read()` path acceptance (L28-44) to root + one-level sub-spec.**

Keep L23-26 **verbatim** (boundary-asserted). Then:

Do **not** add an early `*/_internal/*` guard: a path segment *above* the artifact root (e.g. `/srv/_internal/proj/.agent_reports/spec/prd.md`) would false-deny a legitimate root read. The structural depth check below already rejects every `_internal` shape at or below `spec/`, which is the only region that matters. *(plan-review round_1, non-blocking finding — accepted.)*

1. Keep the existing exact root branch (`*/.agent_reports/spec/prd.md`, `*/.claude_reports/spec/prd.md`) → `slug=""`.
2. Otherwise, run the **structural depth check** (do *not* glob `*/.agent_reports/spec/*/prd.md` — a shell `case` `*` matches `/`, so that pattern would also swallow `spec/<slug>/_internal/versions/v1/prd.md`):
   ```
   [ "$(basename "$fp")" = prd.md ] || return 0
   d1=$(dirname "$fp")   # .../spec/<slug>
   d2=$(dirname "$d1")   # .../spec
   d3=$(dirname "$d2")   # .../.agent_reports
   [ "$(basename "$d2")" = spec ] || return 0
   case "$(basename "$d3")" in .agent_reports|.claude_reports) ;; *) return 0 ;; esac
   slug=$(basename "$d1")
   [ "$slug" = "_internal" ] && return 0
   ```
   The depth check rejects `_internal/versions/v1/prd.md` naturally (`basename $d2` = `versions`), and the explicit `_internal` test covers the direct `spec/_internal/prd.md` case. Relative input is already absolute by here (L23-26 runs first), so `dirname` chains are well-defined.
3. `[ -f "$fp" ] || return 0` stays.

**Step 2.2 — Root derivation + canonical comparison for both shapes.**

**Do not reuse `d1/d2/d3` across branches.** The root branch (Step 2.1 item 1) returns before any `dirname` runs, so those variables are unset there; the hook has no `set -u`, and `dirname "$d3"` would silently evaluate to `dirname ""` → `.`, corrupting `file_root` without any error. *(plan-review round_1 B2.)* Derive `file_root` **inside each branch**:

- Root shape: `file_root=$(dirname "$(dirname "$(dirname "$fp")")")` — the existing L35 expression, unchanged.
- Sub-spec shape: `file_root=$(dirname "$d3")` — valid only in the branch that computed `d1/d2/d3`.
- Canonical target: `canonical_prd="$canonical/spec/prd.md"` for root, `"$canonical/spec/$slug/prd.md"` for sub-spec. Keep the existing physical `cd … && pwd -P` comparison unchanged so linked-worktree shadow reads still fail to satisfy the canonical gate.

**Step 2.3 — Marker filename.**

- `root=$(dirname "$canonical")`; `key=$(printf '%s' "$root" | sed 's#[/ ]#_#g')` — unchanged.
- Root spec: marker name stays **EXACTLY** `${sid}__${key}` (backward compat with live markers and the plugin mirror; frozen).
- Sub-spec: `slug_key=$(printf '%s' "$slug" | sed 's#[/ ]#_#g')` (slugs are dir names and may contain spaces), marker name `${sid}__${key}__${slug_key}`.
- Keep `mtime=$(stat -c %Y "$fp")` stored at read time and the same `mkdir -p`/`printf` write.

*Verify:* Phase 4 test run; plus manual `sh -n hooks/spec-read-marker.sh`.

### Phase 3 — `hooks/spec-skill-gate.sh` (after Phase 2)

**Step 3.1 — Build the candidate set in `find_prd()` (L22-37).**

Keep the upward walk and artifact-root resolution. Replace the single `prd`/`root` assignment with a newline-separated `specs` list of `<slug>\t<path>`-equivalent data (or two parallel accumulations), built as:

- root candidate: `[ -f "$artifact_root/spec/prd.md" ]` → candidate slug `""`.
- sub-spec candidates: glob loop `for d in "$artifact_root"/spec/*/` — a trailing-slash glob yields directories only; guard the literal-no-match case (`[ -d "$d" ] || continue`), skip `_internal`, and require `[ -f "$d/prd.md" ]`.
- Set `root=$(dirname "$artifact_root")` whenever at least one candidate exists.
- Empty candidate set → unchanged PASS ("not a spec-backed project").

Avoid `while read` in a pipeline (subshell loses variables). Use the glob `for` loop, or a newline-separated string iterated with saved `IFS`/`set -f` restore.

**Step 3.2 — Per-candidate marker + drift evaluation in `check_gate()` (L39-72).**

For each candidate: marker = `${sid}__${key}` (root) or `${sid}__${key}__${slug_key}` (sub-spec); `cur=$(stat -c %Y "$candidate_prd")`; candidate is **satisfied** iff the marker exists and `[ "$cur" -le "$read_mtime" ]`.

- ANY candidate satisfied → `return 0`.
- No candidate satisfied → `return 2` with a built `reason` (fail-closed preserved).
- Track whether *any* candidate had a marker at all, to choose between the "not read" and the "drift" message family.

**Step 3.3 — Message builder, branched on candidate count.**

`deny_json` interpolates raw → the reason MUST be a **single line**, no newlines, no double quotes, no backslashes. Build the candidate list as a comma-space-joined single-line string.

- **Exactly one candidate → emit today's strings verbatim** (byte-for-byte single-spec parity):
  - no marker: `This cwd is spec-backed, but prd.md was not read in this session. Read $prd directly with the Read tool, then retry. A code comment or brief quotation does not satisfy the gate.`
  - drift: `prd.md changed after the most recent Read marker. Read $prd again, then retry.`
- **N > 1 → enumerated variant**, listing concrete candidate `prd.md` paths comma-space-joined, containing the phrase **"read the one governing the declared work scope"**, and preserving the existing **"a quotation does not satisfy the gate"** and drift-retry wording.

**Step 3.4 — Leave the CLI/stdin plumbing (L79-141) untouched**; `reason`/`return 2`/exit-code contract is unchanged, so codex/opencode `preflight.sh read|route|gate` callers stay green with no edit.

*Verify:* `sh -n hooks/spec-skill-gate.sh`; Phase 4 tests.

### Phase 4 — `hooks/portable-guards.test.sh` (after Phase 3)

**Step 4.1 — Do not touch the existing `$TMP/specproj` block (L294-357).** Its untouched, still-passing assertions **are** the root-only no-regression evidence.

**Step 4.2 — Add a new `$TMP/multispec` fixture block** after L357, with root `spec/prd.md` + `spec/alpha/prd.md` + `spec/beta/prd.md` + `spec/alpha/_internal/versions/v1/prd.md`.

**Every scenario MUST use its own distinct session id.** The gate passes when ANY candidate is satisfied, so a shared sid makes the deny assertions unfalsifiable: 4.2.b's `_internal` deny would be satisfied by 4.2.a's alpha marker, and 4.2.d's alpha-drift deny would be satisfied by any surviving root marker. This block is the plan's entire multi-spec evidence — a shared sid would make it pass vacuously. *(plan-review round_1 B1.)* Assign ids explicitly, e.g. `msubsid` (a), `msinternalsid` (b), `msnoreadsid` (c), `msdriftsid` (d), `msparitysid` (e), `mslegacysid` (f). Scenarios are then independent and may be written in one pass.

- a. `msubsid`: sub-spec read (`$MARK --file …/spec/alpha/prd.md`) → `$SPEC --skill autopilot-code` **passes**.
- b. `msinternalsid`: `_internal/versions/v1/prd.md` read → **no marker written** (assert absence of any `msinternalsid__*` under `$AGENT_HOME/.spec-grounding/`) and gate still **denies** (exit 2).
- c. `msnoreadsid`: no read at all → exit 2 **and** stderr lists all candidate paths (grep for each concrete `prd.md` path and for the phrase `read the one governing the declared work scope`).
- d. `msdriftsid`: read `spec/alpha/prd.md` → pass; `sleep 1`; touch `spec/alpha/prd.md` → deny (exit 2; this sid holds no root marker, so the deny is real); re-read → pass.
- e. `msparitysid`: root-only deny-message parity — assert `$TMP/specproj` (single candidate, fresh sid ⇒ no marker) stderr still matches today's exact text (`This cwd is spec-backed, but prd.md was not read in this session.` … `A code comment or brief quotation does not satisfy the gate.`).
- f. `mslegacysid`: legacy `.claude_reports` sub-spec variant in a **separate** fixture dir (the resolver prefers `.agent_reports` when both exist, so it must not share `$TMP/multispec`).

**Step 4.3 — Preserve the verbatim boundary string.** The test name `codex read wrapper resolves relative prd paths for spec gate` (L328) must remain literally present.

*Verify:* `cd <worktree> && bash hooks/portable-guards.test.sh` — all new + all pre-existing assertions pass.

### Phase 5 — Claude plugin mirror resync (after Phase 4 is green)

**Step 5.1 — Run the repo generator** `python3 adapters/claude/bin/sync-native-plugin.py` (no-arg = sync) so `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/hooks/{spec-read-marker.sh,spec-skill-gate.sh}` are byte-consistent with `hooks/`. Do **not** hand-edit the mirror. `hooks.json` command strings (AGENT_HOME env-prefix) stay unchanged.

*Verify:* `python3 adapters/claude/bin/sync-native-plugin.py --check` exits 0.

**Step 5.2 — Adjacent-surface confirmation (verify only, do not redesign):** `tools/check-adaptation-boundary.sh`, `python3 tools/build-manifest.py --check` (expected: no manifest edit needed — hook entries carry no body hash), and the codex/opencode `preflight.sh read|route|gate` paths that invoke the same canonical hooks via CLI (covered by the existing suite).

---

## 3. Constraints

1. **Worktree-only guard runs.** `hooks/portable-guards.test.sh` and any guard suite run ONLY inside `/home/Uihyeop/agent_setting-wt/spec-gate-multi-spec`, NEVER against the primary checkout `/home/Uihyeop/agent_setting` — a guard run on primary rotates the live dispatch broker (measured 2026-07-15).
2. **Verbatim-string preservation** (`tools/check-adaptation-boundary.sh` L961-964): `*) fp="$PWD/$fp" ;;` must remain literally present in `hooks/spec-read-marker.sh`; the test name `codex read wrapper resolves relative prd paths for spec gate` must remain literally present in `hooks/portable-guards.test.sh`.
3. **Deny JSON single-line.** `deny_json()` interpolates the reason raw into JSON — no newlines, no double quotes, no backslashes in any candidate list.
4. **Root marker name frozen.** Root-spec markers keep the EXACT name `${sid}__${key}` (live markers + plugin mirror depend on it). Only sub-specs get the `__${slug_key}` suffix.
5. **Core-first order.** `core/` wording lands before hook edits in both the commit narrative and execution order (`hooks/core-first-guard.sh` enforces at runtime).
6. **POSIX sh, no jq**, in both hooks. No `while read` in a pipeline for candidate iteration.
7. **Single-spec byte-for-byte parity** from the caller's perspective.

---

## 4. Risks / Notes

- **Sub-spec-only repo behavior delta (real, deliberate).** Today a repo with sub-specs but NO root `spec/prd.md` resolves `prd=""` → "not spec-backed" → PASS. Under the new candidate set it becomes **gated**. This follows from the stated intent but is a genuine behavior change; surface it in the execution report.
- **Marker-name collision — checked, none.** Root key for `/home/x/y` → `_home_x_y` → `sid___home_x_y`; sub-spec of `/home/x` with slug `y` → `sid___home_x__y`. Distinct (single vs double underscore before the tail).
- **`_internal` exclusion depth trap.** A `case` glob `*` matches `/`, so `*/.agent_reports/spec/*/prd.md` would also match `spec/<slug>/_internal/versions/v1/prd.md`. The structural depth check (Step 2.1) is the mitigation; the early `*/_internal/*` guard and the explicit `[ "$slug" = "_internal" ]` test are belt-and-braces.
- **Slug sanitization.** Slugs are directory names and can contain spaces — apply `sed 's#[/ ]#_#g'` before the slug enters a marker filename.
- **Message-length growth.** This repo has 11 sub-specs today; plan-review measured the enumerated deny list at **893 bytes**, uncapped. It must still be one line — verify no wrapping is introduced by the builder. No truncation is planned: a silently clipped candidate list would hide the very path the agent needs. If the executor finds a runtime limit on `permissionDecisionReason`, report it rather than truncating unannounced.
- **Governance stays judgment.** The deterministic gate only enforces "actually read a current spec of this project"; which candidate GOVERNS remains agent judgment plus route-record `spec_read.source`.

---

## 5. Verification

All commands `cd`-scoped to the worktree; never run against the primary checkout.

```sh
cd /home/Uihyeop/agent_setting-wt/spec-gate-multi-spec

# syntax
sh -n hooks/spec-read-marker.sh
sh -n hooks/spec-skill-gate.sh

# primary regression + new multi-spec scenarios
bash hooks/portable-guards.test.sh

# Claude plugin mirror byte-consistency
python3 adapters/claude/bin/sync-native-plugin.py --check

# adaptation boundary (incl. the two verbatim-string assertions at L961-964)
bash tools/check-adaptation-boundary.sh

# manifest drift (flag confirmed by reading tools/build-manifest.py main() L656+;
# expected clean — hook entries carry no body hash, so no manifest edit is planned)
python3 tools/build-manifest.py --check
```

---

## 6. Plan-Check Record

Standard rigor: one independent review, correction budget 1 (spent).

- Review: `_internal/plan_reviews/round_1.md` — verdict **NEEDS-CORRECTION** (2 blocking).
- **B1** (test session ids collide with the ANY-candidate rule → deny assertions vacuous) — **fixed** in Step 4.2.
- **B2** (`d1/d2/d3` reused where the root branch never computes them; no `set -u` ⇒ silent `dirname ""` → `.`) — **fixed** in Step 2.2.
- Non-blocking accepted: early `*/_internal/*` guard dropped as redundant and false-deny-prone (Step 2.1); 893-byte deny-list measurement recorded (§4).
- Verified against source by the review and left unchanged: deny strings match L61/L67 character-for-character including `$prd`; the depth check rejects every `_internal` shape and accepts legacy `.claude_reports` + relative input; the `spec/*/` no-match literal is guarded; no existing assertion is perturbed (every gate-reaching fixture is root-only ⇒ single candidate ⇒ verbatim branch); all five verification flags exist.

No residual blocking concerns.

## 7. Out of Scope

Do not plan or implement:

1. Gate firing-point relocation (Skill entry → mutation surface).
2. codex/opencode preflight WRITE-gate sub-spec patterns.
3. SD-45 route-record schema.
4. Any `spec/**` PRD edit.
5. `.dispatch/` broker internals.
