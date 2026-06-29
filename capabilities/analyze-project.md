# Capability: analyze-project

This is the portable capability contract for `analyze-project`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `analyze-project` |
| Group | `pre` |
| Supported modes | `code, paper, doc` |
| Portable meaning | 사전 분석. 코드·논문·문서 primary 자료를 구조화해 다운스트림 입력으로 만든다. |
| Argument shape | `[--mode code|paper|doc] [<scope/target/input-folder>] [--skip-qa]` |

## Invocation Semantics

Pre-work analysis skill — analyzes the project's primary materials and writes structured artifacts to <artifact-root>/analysis_project/. Three modes — code (codebase), paper (academic PDFs), doc (miscellaneous doc materials like reviewer comments, format templates, samples, internal notes). Mode auto-detects between code and doc when omitted; paper requires explicit --mode paper. Output is the persistent input source for downstream autopilot-{draft,code,research} skills.

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
| Claude Code | `adapters/claude/skills/analyze-project` currently projects compatibility source `skills/analyze-project/SKILL.md`. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info analyze-project`. Do not consume `skills/analyze-project/SKILL.md` as native Codex configuration. |

## Compatibility Reference

The historical Claude Skill source remains at `skills/analyze-project/SKILL.md` while this capability is being split into portable and adapter-native layers.
