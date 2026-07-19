# Plan review — round 1

Plan: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_spec-gate-multi-spec/plan/plan.md`
Mode: plan-review, standard rigor, read-only. No guard suite executed (per hard constraint); findings are from reading source only.

## Verified as correct (not defects)

Recorded so the executor does not re-litigate these:

- **Deny-string parity is exact.** Plan L135/L137 quote strings that match `hooks/spec-skill-gate.sh` L61 and L67 character-for-character, including the raw `$prd` interpolation. Confirmed by direct comparison.
- **Structural depth check (Step 2.1) is sound.** Traced against every shape: `spec/alpha/prd.md` accepted (d2=`spec`, d3=`.agent_reports`); `spec/alpha/_internal/versions/v1/prd.md` rejected (d2=`versions`); `spec/_internal/prd.md` rejected (slug test); `spec/_internal/versions/v1/prd.md` rejected (d2=`versions`); two-level `spec/a/b/prd.md` rejected (d2=`alpha`). The legacy `.claude_reports` arm is handled by the `case` at Step 2.1(3). Relative input works: `*) fp="$PWD/$fp" ;;` runs first, and an interior `./` segment does not disturb `basename`.
- **The `for d in "$artifact_root"/spec/*/` no-match literal case is handled.** `[ -d "$d" ] || continue` (plan L116) correctly discards the unexpanded literal. Trailing slash is harmless: `[ -f "$d/prd.md" ]` yields a benign `//`, and `basename` strips it.
- **No existing spec-gate assertion is perturbed.** `$SPEC`/`$MARK` appear only at `hooks/portable-guards.test.sh` L17-18 and are used only in the L294-357 block. Every fixture that reaches the gate — `specproj`, `canonical-spec`/`canonical-spec-wt` (L333-357), `$TMP/repo` (L2094), `$TMP/bridgeproj` (L2772) — is root-`prd.md`-only, i.e. exactly one candidate, so all of them take the verbatim-parity branch and keep the frozen `${sid}__${key}` marker name. The canonical-vs-worktree-shadow cases are untouched because Step 2.2 preserves the physical `cd … && pwd -P` comparison.
- **All verification flags are real.** `tools/build-manifest.py` `--check` (L670), `--adaptation-surface` (L658), `--sync-baselines` (L665); `adapters/claude/bin/sync-native-plugin.py` `--check` (L278), no-arg sync (`def sync()` L152, `shutil.copy2` L179). Boundary assertions confirmed at `tools/check-adaptation-boundary.sh` L961-964.
- **Fixture-separation claim for legacy `.claude_reports` (Step 4.2.f) is justified.** `utilities/artifact-root.sh` L56-59 and L68-75 both prefer `.agent_reports` when both exist.

---

## BLOCKING

### B1. Step 4.2.b and 4.2.d cannot pass as written — no session-id isolation under ANY-candidate semantics

Evidence: plan L124-126 (`ANY candidate satisfied → return 0`) vs. plan L150 and L152.

Step 3.2 makes the gate pass if *any* candidate is satisfied. Steps 4.2.a–f are declared "independent and may be written in one pass" (plan L147), which implies a shared session id. Under that reading both assertions are contaminated:

- **4.2.b** asserts "no marker written" for the `_internal` read plus "gate still denies". If 4.2.a already ran under the same sid, a marker `${sid}__${key}__alpha` exists, so the absence assertion is ambiguous and the deny assertion fails outright (alpha is satisfied → PASS).
- **4.2.d** asserts sub-spec drift on `spec/alpha/prd.md` denies. If the same sid also holds a still-fresh **root** marker, ANY-satisfied makes the gate PASS and the assertion fails.

This is the plan's entire multi-spec verification evidence, so it must be executable as specified. Required correction: give each of 4.2.b, 4.2.c, 4.2.d, 4.2.e (4.2.e already says so at L153) its own fresh session id, and state explicitly that a drift assertion is only meaningful when the sid holds markers for the drifted candidate *alone*. The existing block models this correctly (`testsid`, `relsid`, `shadowread`, `canonicalread` at L297/L326/L344/L352).

### B2. Step 2.2 instructs the executor to reuse `d1/d2/d3` that the root branch never computes

Evidence: plan L80 (root branch = existing `case`, sets `slug=""` only), plan L81-91 (d1/d2/d3 computed **only** in the `Otherwise` branch), plan L97 ("Derive from the already-computed `d1/d2/d3` rather than re-globbing").

For the root shape the `case` at Step 2.1(2) matches and returns before any `dirname` runs, so `d3` is unset at Step 2.2. As written, `file_root=$(dirname "$d3")` for root would evaluate `dirname ""` → `.` → `artifact-root.sh .` resolves against the hook's `$PWD`, not the project — silently marking the wrong root or `return 0`-ing. `hooks/spec-read-marker.sh` has no `set -u`, so this fails silently rather than erroring.

Correction: compute `d1/d2/d3` unconditionally *after* the `_internal` guard and before the `case`, or keep the current 3×`dirname` (`hooks/spec-read-marker.sh` L35) verbatim in the root branch. Note the shapes are consistent — root `dirname³ fp` and sub-spec `dirname d3` both yield the project root — so either resolution works; the plan just must pick one.

---

## NON-BLOCKING

### N1. The early `*/_internal/*` guard is not free belt-and-braces — it can false-deny a legitimate root read

Evidence: plan L78-79, applied to `$fp` *after* absolutization by `hooks/spec-read-marker.sh` L23-26.

The guard matches the whole absolute path, including the segments **above** the artifact root. A project at `…/_internal/proj` reading its own legitimate `…/_internal/proj/.agent_reports/spec/prd.md` matches `*/_internal/*` → `return 0` → no marker → permanent deny, with no diagnostic. This is a regression against today's root-only behavior, which accepts that path. It stays fail-closed (a false deny, never a false allow), so it is not blocking, and no such path exists in this repo today. Recommend scoping the exclusion to the portion at/below `spec/` — which the structural check and the explicit `[ "$slug" = "_internal" ]` test already do completely, making the early guard redundant as well as harmful. Simplest fix: drop it.

### N2. Step 3.2's loop needs the same no-subshell warning Step 3.1 got

Evidence: plan L120 warns about subshells for `find_prd` only; plan L124-128 is silent.

`check_gate`'s per-candidate loop is the more dangerous of the two: a subshell (pipe or `$( )`) makes the satisfied-candidate `return 0` exit only the subshell, producing a **false deny even with a valid marker**, and loses `reason`, yielding `permissionDecisionReason":""` from `deny_json` (`hooks/spec-skill-gate.sh` L74-77). Extend the warning, and add an assertion that the deny reason is non-empty.

### N3. `<slug>\t<path>` accumulation has an empty-field parsing trap; prefer path-only

Evidence: plan L113 ("newline-separated `specs` list of `<slug>\t<path>`-equivalent data").

The root candidate's slug is `""`, so its entry is a leading-empty tab field — exactly the case where POSIX word-splitting behavior with non-whitespace `IFS` is easy to get wrong, and the plan forbids the `while read` idiom that would handle it. Simpler and fully equivalent: accumulate **paths only** and re-derive the shape structurally at use (`basename "$(dirname "$path")" = spec` → root, else that basename is the slug). This mirrors Step 2.1's own check and removes the parsing question.

### N4. Mixed no-marker / drift state has no specified message

Evidence: plan L128 ("Track whether *any* candidate had a marker at all") vs. plan L137 (N>1 enumerated variant).

With candidate A unread and candidate B stale, the rule selects the drift family, but the plan does not say whether the enumerated drift list names all candidates or only the drifted ones. Reduces to today's exact behavior for N=1, so parity is safe; the executor just needs a decision for N>1. Recommend listing all unsatisfied candidates in both families and letting the family choose only the verb.

### N5. Enumerated deny message is ~1 KB single-line in this repo, with no bound

Evidence: plan L188 flags length but sets no cap. Measured: the joined candidate list alone is **893 bytes** (root `prd.md` + 11 sub-specs, confirmed present under `.agent_reports/spec/`). Plus boilerplate this exceeds 1 KB on a single JSON line, on every ungrounded deny in this repo. Not a correctness issue — it is one line, no `"`/`\`/newline from these paths — but consider a cap (e.g. first N + "and K more") or listing slugs rather than full paths. Also note candidate order follows locale collation; Step 4.2.c greps per-path, so it is order-independent as designed.

### N6. Step 1.1's reworded portable invariant broadens a surface the Codex write-gate does not realize for sub-specs

Evidence: `adapters/codex/bin/preflight.sh` L243-250 — the autopilot-spec write gate matches `*/.agent_reports/spec/prd.md` etc. A `case` glob cannot match `…/spec/alpha/prd.md` against that literal tail, so sub-spec PRD writes are ungated on Codex before *and* after this change. Plan §6 item 2 puts this out of scope, which is a legitimate call, and HOOKS.md's "Non-Claude adapter requirement" cell is CLI-signature-only (confirmed at `core/HOOKS.md` L46), so nothing becomes literally false. But once the portable-meaning cell names sub-specs, the gap becomes a documented-looking promise. Recommend one explicit deferral line in the plan's §4 Risks.

---

## NIT

- **N7. "Marker-name collision — checked, none" (plan L185) is overstated.** The `sed 's#[/ ]#_#g'` key is already aliasing today (`/home/x_y` and `/home/x/y` both → `_home_x_y`). The sub-spec suffix adds a second dimension: root spec of project `/home/x/_y` → `sid___home_x__y` collides with sub-spec `y` of project `/home/x`. Contrived, and the class is pre-existing rather than introduced. Accurate claim: "no new collision class beyond the pre-existing key aliasing."
- **N8. Corrupt/empty marker file.** `read_mtime=$(cat "$marker" 2>/dev/null || echo 0)` (`hooks/spec-skill-gate.sh` L65) — the `|| echo 0` fires only when `cat` *fails*, not when the file is empty, so `[ "$cur" -le "" ]` errors and denies. Pre-existing and fail-closed; just do not regress it into a fail-open while restructuring.
- **N9. Drill surface unmentioned.** `adapters/claude/loops/drill/cases/g4_spec_gate/` asserts `ls "$MARKER_HOME/.spec-grounding/"*"__${key}"` (assert.sh L10) and cleans with the same glob (fixture.sh L29). Both are unaffected — the fixture is root-`prd.md`-only, so the frozen root marker name still matches, and `*__${key}` correctly does not match a `__${slug}`-suffixed name. Per the standing "do not run drill automatically" rule, omitting it from §5 is right; the plan should just record the one-line analysis.

---

## Verdict

**NEEDS-CORRECTION** — two blocking items (B1 test session-id isolation, B2 unset `d1/d2/d3` in the root branch). Both are local edits to the plan; the core design — structural depth check, candidate set, frozen root marker, single-candidate verbatim parity — is sound and was verified against the actual source.
