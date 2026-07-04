# Capability: analyze-user

This is the portable capability contract for `analyze-user`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `analyze-user` |
| Group | `pre` |
| Supported modes | `init, update` |
| Portable meaning | cross-project 사용자 성향 프로필 작성·갱신. 코드·작성·분석 패턴을 추출한다. |
| Argument shape | `<aspect> [--source <path>] [--mode init|update] [--from discover|analyze|verify|qa|output|summary] [--user-refine]` |

## Invocation Semantics

사용자의 cross-project 산출물 (paper / presentation / report / code / memory) 을 다단계로 스캔·분석해 DB `type=profile` 레코드 (`mem profile <stem>`) 의 _범용 작업 성향_ 을 누적·갱신. autopilot-* 와 동급 ceremony — 사용자 프로필은 _한 번 만들어지면 모든 sub-agent 가 default 로 따르는 자료_ 라 작은 오류도 propagating. 따라서 source discovery → aspect 별 분석 → cross-aspect 일관성 검증 → 다중 QA gate (adversarial 고정) → 산출 → pipeline summary 6 phase. QA level 은 _항상 adversarial_ — 사용자 협상 불가.

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
| Claude Code | `adapters/claude/skills/analyze-user/SKILL.md` and `skills/analyze-user/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/analyze-user/SKILL.md`, while `skills/analyze-user/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info analyze-user`. Use `adapters/codex/skills/analyze-user/SKILL.md` and `adapters/codex/plugins/agent-harness-codex/skills/analyze-user/SKILL.md` as native Codex Skill/plugin projections; do not consume `skills/analyze-user/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info analyze-user`. Use `adapters/opencode/skills/analyze-user/SKILL.md` and `adapters/opencode/commands/analyze-user.md` as native OpenCode projections; do not consume `skills/analyze-user/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/analyze-user/SKILL.md` and `adapters/claude/skills/analyze-user/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/analyze-user/SKILL.md`, while `skills/analyze-user/SKILL.md` remains the compatibility reference kept for parity/drift checks.
