# Capability: autopilot-research

This is the portable capability contract for `autopilot-research`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `autopilot-research` |
| Group | `entry` |
| Supported modes | `academic, technology, market` |
| Portable meaning | 공통 사전조사. 논문·기술·시장 survey 후 downstream capability로 분기한다. |
| Argument shape | `<query> [--mode academic|technology|market] [--depth shallow|medium|deep] [--qa quick|light|standard|thorough|adversarial] [--no-clarify] [--no-figures] [--from search|analyze|report]` |

## Invocation Semantics

Research survey pipeline — _세 family 의 공통 사전_ entry. academic (논문 survey·trend·필드 정리) / technology (라이브러리·프로젝트·스택·코드 baseline 비교) / market (시장·경쟁·reference 앱·UX 패턴) 3 mode. 다운스트림 매핑: academic → autopilot-draft (paper/presentation) + autopilot-code (academic baseline 코드) | technology → autopilot-code (라이브러리·연구 baseline 위) + autopilot-spec (스택·reference 패턴) | market → autopilot-draft (proposal/report) + autopilot-spec (reference 앱 UX). Field intelligence only — 실제 문서·코드·앱 생성은 다운스트림 skill 이 담당.

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
| Claude Code | `adapters/claude/skills/autopilot-research` currently projects compatibility source `skills/autopilot-research/SKILL.md`. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info autopilot-research`. Do not consume `skills/autopilot-research/SKILL.md` as native Codex configuration. |

## Compatibility Reference

The historical Claude Skill source remains at `skills/autopilot-research/SKILL.md` while this capability is being split into portable and adapter-native layers.
