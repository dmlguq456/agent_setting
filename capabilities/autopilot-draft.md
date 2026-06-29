# Capability: autopilot-draft

This is the portable capability contract for `autopilot-draft`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `autopilot-draft` |
| Group | `entry` |
| Supported modes | `paper, presentation, doc` |
| Portable meaning | 문서 초안 파이프. 전략·초안·검증·편집을 거쳐 적용용 문서 artifact를 만든다. |
| Argument shape | `<task description> [--mode paper|presentation|doc] [--qa quick|light|standard|thorough|adversarial] [--user-refine] [--no-clarify] [--from analyze|strategy|strategy-refine|draft|draft-refine|finalize]` |

## Invocation Semantics

Document draft pipeline — analyze → strategy → strategy-refine → draft → draft-refine → finalize. NOTE: in `paper` mode 'draft' means a **paste-ready cheatsheet draft** — a set of LaTeX paste-ready cards (a mutation/edit plan the user pastes into the canonical main.tex via autopilot-apply), NOT blank-page body writing. 'draft' = the *cheatsheet draft*, regardless of whether the paper is new or already complete. 3 modes by output form: `paper` (LaTeX academic output, always produced as a paste-ready cheatsheet draft that autopilot-apply pastes into main.tex — new-body cheatsheet entries for an initial submission/thesis/book chapter, edit/mutation cheatsheet entries for camera-ready/major-revision of an existing body) / `presentation` (slide-by-slide markdown for PPT) / `doc` (prose for Word/HWP/markdown — reports·proposals·rebuttal responses·peer reviews·tech blogs·memos). Mode is form-first; purpose/genre is conveyed via natural-language task description (no subtype enum). All inputs implicitly discovered from `<artifact-root>/{analysis_project,research}/*` — pre-process external materials via `/analyze-project --mode {paper|doc}` first (cwd 자동 발견). Format specs auto-loaded from `analysis_project/doc/{matching}/formats/` — no explicit `--format-ref` flag. Mode-specific conventions live in `## Mode-Specific Conventions` (§Common + §paper / §presentation / §doc). `presentation` produces markdown only (PPTX export NOT supported — use PowerPoint directly).

Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.

## Artifact Ownership

Use the shared artifact root rule: prefer `.agent_reports/`; use legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not. Capability-specific output placement follows `core/CONVENTIONS.md` section 5 until this spec is expanded with a stricter per-capability artifact map.

## Role Requirements

Use portable role names from `roles/README.md` and `core/CONVENTIONS.md`. Concrete model names, subagent frontmatter, and runtime-specific tool lists belong in adapter files.

## Guard Requirements

Adapters must preserve the portable invariants relevant to this capability:

- resolve artifact root through `utilities/artifact-root.sh` or equivalent logic;
- enforce git/worktree safety before edits;
- enforce artifact ordering before new durable artifacts;
- enforce spec-read gating when this capability changes spec-backed code or specs;
- use DB memory paths, not runtime-native memory files.

## Adapter Realization

| Adapter | Realization |
|---|---|
| Claude Code | `adapters/claude/skills/autopilot-draft` currently projects compatibility source `skills/autopilot-draft/SKILL.md`. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info autopilot-draft`. Do not consume `skills/autopilot-draft/SKILL.md` as native Codex configuration. |

## Compatibility Reference

The historical Claude Skill source remains at `skills/autopilot-draft/SKILL.md` while this capability is being split into portable and adapter-native layers.
