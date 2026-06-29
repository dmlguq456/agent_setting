# Capability: autopilot-design

This is the portable capability contract for `autopilot-design`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `autopilot-design` |
| Group | `entry` |
| Supported modes | `none` |
| Portable meaning | 시각 산출물 디자인 파이프. refs→tokens→components→review→handoff를 조율한다. |
| Argument shape | `<design task or app path> [--scope ui|webapp|slide|icon|diagram|mixed] [--artifact standalone|project] [--from <phase>] [--qa quick|standard|thorough]` |

## Invocation Semantics

Unified design pipeline — orchestrates design-init → design-refs → design-tokens → design-components → design-review → design-handoff. For visual artifacts across UI/UX, slides, diagrams, icons, logos. Can be invoked standalone or auto-delegated from autopilot-spec Phase 2. Distinct from autopilot-draft (text-only documents) — autopilot-design handles visual deliverables. **Claude-Design parity via a design harness** (claude-design-harness-spec.md): a Design MCP server (~/.claude/tools/design-mcp — preview/screenshot/console/eval_js/view_image) renders every output so it is visually self-verified (render → view_image → fix loop); a separate-context verifier subagent gates console/layout breakage; shared design rules (slop avoidance, scale, HTML conventions) and reusable scaffolds (deck_stage, tweaks_panel, device_frames) standardize craft; converters export PDF/PPTX/single-HTML bundle; a post-write hook auto-checks console on design HTML saves. Outputs can be a self-contained single-file HTML preview viewable without any project stack.

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
| Claude Code | `adapters/claude/skills/autopilot-design` currently projects compatibility source `skills/autopilot-design/SKILL.md`. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info autopilot-design`. Do not consume `skills/autopilot-design/SKILL.md` as native Codex configuration. |

## Compatibility Reference

The historical Claude Skill source remains at `skills/autopilot-design/SKILL.md` while this capability is being split into portable and adapter-native layers.
