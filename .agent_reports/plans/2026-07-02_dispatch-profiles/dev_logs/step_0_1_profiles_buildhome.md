# Step 0.1–0.5 + Step 1.1 — `profiles/` scaffolding + `build-home.py` generator

Plan ref: `.agent_reports/plans/2026-07-02_dispatch-profiles/plan/plan.md` Phase 0 (Steps 0.1–0.5), Phase 1 (Step 1.1).
Spec ref: `.agent_reports/spec/dispatch-profiles/prd.md` §2, §3, §4.1, §5.

All files in this step are **new files** (old = did not exist). Reported as full new content per file, with the Decision rationale for the choices made where the plan/spec left implementation freedom.

---

## File: `profiles/README.md` (NEW)

Old: (did not exist)
New: catalog/main index — (a) profile-name | one-line-description table starting with `lab-runner`; (b) L0/L1/L2 three-layer summary table (spec §2); (c) DP-3 exception section anchored by name to `core/ADAPTATION.md` ("Concrete model names belong in adapter documents or generated native files") rather than derived from `roles/README.md`; (d) term-disambiguation paragraph distinguishing dispatch **profile** (`profiles/`, `--profile`, `profile=` k=v — masked config home) from the family's **mem-profile** (`mem profile <stem>`, DB `type=profile`; `core/MEMORY.md` §7.6).

Decision: Read `roles/README.md` first to match its section-heading register (portable-vs-adapter framing) so the DP-3 "intended exception" reads as a contrast to that file's own final paragraph ("Concrete model names do not belong in this directory... let adapter documents define concrete mapping") rather than a contradiction of it. Confirmed the exact ADAPTATION.md wording by grep (`core/ADAPTATION.md:75`) before quoting it, since the plan's instruction requires citing the rule "by name" — quoting from memory would have risked citing `roles/README`'s paraphrase instead of the canonical line.

---

## File: `profiles/templates/bootstrap-claude.md` (NEW)

Old: (did not exist)
New: L0 reference stub for Claude dispatch workers — numbered list: (1) Read the four `core/` docs, (2) obey `artifact-guard` / `git-state-guard` / `spec-skill-gate` / `builtin-memory-guard`, (3) `.agent_reports/` artifact-convention pointer, (4) depth-1 no-re-dispatch rule. No L1 orchestration section. Closing note on `CLAUDE_CONFIG_DIR` attach.

Decision: Named the guard hooks by their actual filenames (`spec-skill-gate.sh`, verified via `ls hooks/`) rather than the prose label "spec-gate" used in the plan text, so a worker session grepping for the hook can find it. Deliberately did **not** add a `generated-from:` header inside the template — the task instructions state build-home.py prepends that header, so baking it into the template would double it up in the assembled bootstrap.

---

## File: `profiles/templates/bootstrap-codex.md` (NEW)

Old: (did not exist)
New: same L0 stub, Codex-flavored — same four-guard list, `CODEX_HOME` + `AGENTS.md` attach note, and an explicit statement that the codex preflight chain (`preflight.sh`/`check-runtime-projection`) still runs and is wrapper-owned, independent of this bootstrap. No L1 section.

Decision: Kept the guard list and depth-1 rule byte-for-byte parallel to `bootstrap-claude.md` (only the attach-mechanism closing paragraph differs) so the two templates stay easy to diff/audit as the same L0 contract expressed per harness.

---

## File: `profiles/lab-runner.yaml` (NEW)

Old: (did not exist)
New: copied verbatim from spec §3's example —
```yaml
name: lab-runner
description: "실험 실행 특화 — autopilot-lab 자율 구간 분사용"
harness: claude
model_role: fast implementer
effort: medium
fragments:
  - profiles/fragments/lab-runner.md
expose:
  skills: [autopilot-lab, analyze-project, post-it]
  agents: [dev-team, qa-team, material-team]
  triggers: []
```

Decision: No deviation from the spec example — this is the single reference declaration Phase 1 validates against, so literal fidelity (field order, values) matters for later `--check` smoke tests that assert specific paths (e.g. `skills/autopilot-lab`).

---

## File: `profiles/fragments/lab-runner.md` (NEW)

Old: (did not exist)
New: L2 specialization text in three sections — autonomous experiment-run discipline (low-confirmation autonomy, but stop-and-report on destructive/ambiguous cases), RUNLOG convention pointer (`<artifact-root>/experiments/{date}_{slug}/_RUNLOG.md`, append-only), and a stay-in-lane rule scoped to the profile's exposed skill/agent subset plus the depth-1 no-re-dispatch reminder.

Decision: Kept this fragment self-contained (no cross-reference assumed beyond `core/WORKFLOW.md`'s workflow map and the RUNLOG path already documented in CLAUDE.md's Drift-Free Essentials table) since L2 fragments are meant to be readable in isolation inside a masked home that does not carry the main CLAUDE.md body.

---

## File: `tools/profile/build-home.py` (NEW, `chmod +x`)

Old: (did not exist)
New: CLI generator per spec §4.1 / plan Step 1.1. Key pieces:

- `resolve_agent_home()` — env-first (`AGENT_HOME` env var, accepted only if `<it>/core/CORE.md` exists), else walks `Path(__file__).resolve().parents` upward for the first dir containing `core/CORE.md`. Does **not** use the forbidden `Path(os.environ.get("AGENT_HOME", os.getcwd()))` anti-pattern (verified by grep post-write).
- `load_declaration()` / `validate_declaration()` — `import yaml` with the graceful `"PyYAML required: pip install pyyaml\n"` + `sys.exit(2)` fallback (ported verbatim in spirit from `tools/build-manifest.py`). Validates: required `name`/`description`/`harness`; `harness ∈ {claude, codex, opencode}`; `model_role` XOR `model` (both or neither → error); `fragments` is a list of paths that must exist under `agent_home`; `expose` is a dict restricted to `skills`/`agents`/`triggers` keys, each a list. All validation failures print to stderr and `sys.exit(1)`.
- `assemble_bootstrap()` — reads `profiles/templates/bootstrap-<harness>.md`, fails loud with `sys.exit(1)` if missing (this is the path an undeclared `harness: opencode` template hits in v1 — schema-valid, template-missing, fail-loud, never silently skipped). Prepends `<!-- generated-from: profiles/<name>.yaml — do not edit -->`, then appends each fragment file's content in declared order. Plain concat: each piece is `rstrip("\n")`-ed and joined with a single `"\n"`, so template/fragment boundaries are separated by exactly one newline, with one trailing newline at end of file — deterministic on every call.
- `link()` — Python port of `install-runtime-projection.sh`'s `link()` primitive (`adapters/codex/bin/install-runtime-projection.sh:49-67`): skip when `target` doesn't exist (`skip=... reason=projection-target-missing`), refuse to clobber a real non-symlink (`skip=... reason=non-symlink-exists`), else unlink a prior symlink and `os.symlink(target, linkpath)`. Creates `linkpath.parent` as needed (the codex shell version relies on pre-existing `mkdir -p` calls; the Python port folds that into `link()` itself since it also has to create nested `skills/<name>` and `agents/<name>.md` parents).
- `build_instance()` — assembles the bootstrap **first** (fail-fast before any filesystem writes), then creates `<home-root>/<slug>.<name>/` and links, in order: L0 hard include (`core/`, `hooks/` — always); harness=claude → dual-path `settings.json` (first existing of `<HOME>/settings.json`, `<HOME>/adapters/claude/settings.json`); harness=codex → dual-path `hooks.json` (first existing of `<HOME>/codex-hooks/hooks.json`, `<HOME>/adapters/codex/hooks/hooks.json`) and explicitly never links claude `settings.json`; `expose.skills`/`expose.agents` dual-path (repo-root then `adapters/claude/...`, per the task instruction literally — not harness-branched); `triggers` no-op; `.credentials.json` shared via symlink if present. Session-state dirs (`projects/`, `sessions/`, `.statusline/`) are never linked (isolation by omission — no code path touches them). Writes the assembled bootstrap to `CLAUDE.md` (claude) or `AGENTS.md` (codex). Prints `instance=<dir> harness=<h> links=<n>` and `sys.exit(0)`.
- `do_check()` — parses + validates (declaration errors → exit 1 inside `validate_declaration`), assembles the bootstrap twice and requires byte-identical output; mismatch → `sys.exit(2)` (drift). Since v1 has no persisted instance to diff against, this double-assembly is the concrete realization of "reassembly is deterministic" from spec §4.1. Success → `check=ok name=... harness=... fragments=<n>` + `sys.exit(0)`.
- Bare invocation (no `--instance`, no `--check`) — declaration-only validation (parse + validate + one assembly, no double-check, no instance writes), `sys.exit(0)` on success. Not required by the plan/spec but added so the CLI does not silently no-op when called without an action flag.
- Exit codes strictly: `0` ok, `1` declaration/template error, `2` `--check` drift. `3` is never used (reserved for the dispatch wrapper's own preflight gate per spec §4.1/§4.2).

Decision: Ordered `build_instance()` to call `assemble_bootstrap()` **before** creating the instance directory or any symlinks, even though the plan's prose lists "assemble bootstrap" as the last sub-step. Rationale: this avoids leaving a partially-populated instance directory (core/hooks/settings linked, but no bootstrap file) when a template or fragment is missing — the most likely failure mode is `harness: opencode` (no `bootstrap-opencode.md` in v1), and failing before touching the filesystem keeps `--instance` failures side-effect-free, consistent with the plan's "gate-first, then create" anti-leak principle used for the dispatch wrapper (Phase 2/3), applied here at generator granularity.

Decision: For `expose.skills`/`expose.agents` dual-path resolution, followed the task instruction literally (`<HOME>/skills/<name>`, `<HOME>/adapters/claude/skills/<name>` — and the agents equivalent) rather than branching the fallback path by the declaration's own `harness:` field. This matches both the plan text (Step 1.1 bullet) and the spec (`profiles/` is a repo-context-only build input read from the source tree, where `skills/` and `adapters/claude/skills/` are the only two locations skills live at today) — a codex-harness profile's `expose.skills` would still resolve against these same two paths in v1, since no `adapters/codex/skills/<name>` equivalent exists as a per-skill directory to expose from.

Decision: Did not add an `opencode`-specific L0 branch (no settings.json/hooks.json linked) inside `build_instance()`, since `assemble_bootstrap()` already exits 1 for `harness: opencode` before that code is reached — adding dead branches for an unreachable harness would be speculative code the plan explicitly scopes out (v1 = claude + codex only, DP-12).

### Verification performed (informal smoke, not the full gate suite — orchestrator owns gate execution)

```
python3 -c "import ast; ast.parse(open('tools/profile/build-home.py').read())"   # syntax OK
AGENT_HOME="$PWD" python3 tools/profile/build-home.py lab-runner --instance smoke --home-root "$TMP/homes"
  → instance=<tmp>/homes/smoke.lab-runner harness=claude links=9
  → verified: core/, hooks/, settings.json, CLAUDE.md, skills/autopilot-lab all present
AGENT_HOME="$PWD" python3 tools/profile/build-home.py lab-runner --check   → check=ok ... exit=0
AGENT_HOME="$PWD" python3 tools/profile/build-home.py <harness:opencode decl> --check   → missing template, exit=1
AGENT_HOME="$PWD" python3 tools/profile/build-home.py <model_role+model both-set decl> --check   → mutually-exclusive error, exit=1
grep 'os.environ.get("AGENT_HOME", os.getcwd())' tools/profile/build-home.py   → no match (anti-pattern absent)
```

No mirror file (`adapters/claude/tools/profile/build-home.py`) was created — Phase 1.2 (byte-identical mirror) is explicitly out of scope for this step per the task instructions ("미러는 만들지 마라"). No boundary/portable-guard gates were run — gate execution is orchestrator-owned per the task instructions ("게이트 실행하지 마라").

## Files touched (all new)

- `profiles/README.md`
- `profiles/templates/bootstrap-claude.md`
- `profiles/templates/bootstrap-codex.md`
- `profiles/lab-runner.yaml`
- `profiles/fragments/lab-runner.md`
- `tools/profile/build-home.py` (chmod +x)
