# Capability: autopilot-ship

This is the portable capability contract for `autopilot-ship`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `autopilot-ship` |
| Group | `entry` |
| Supported modes | `none` |
| Portable meaning | 앱 배포·출시 준비. build/deploy setup과 ship checklist를 만든다. |
| Argument shape | `<task description (선택)> [--qa quick|light|standard|thorough]` |

## Invocation Semantics

_앱 배포 셋업_ entry — 이미 `spec/` 가 잡혀 있고 기능 어느 정도 완성된 자리에서 첫 ship setup·env·domain·migration deploy 안내. 호스팅 선정 (Vercel / Fly / Railway / Cloudflare / EAS) + CI/CD 파일 + `.env.example` + 도메인 가이드 + deploy_record. 실제 배포 명령은 사용자 직접 실행 — 본 skill 은 _안내만_. autopilot-spec 의 _초기 spec·skeleton_ 자리와 작업 본질 분리. 재호출 가능 (env 변경·domain 추가·migration 운영 배포 자리).

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
| Claude Code | `adapters/claude/skills/autopilot-ship/SKILL.md` and `skills/autopilot-ship/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-ship/SKILL.md`, while `skills/autopilot-ship/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info autopilot-ship`. Use `adapters/codex/skills/autopilot-ship/SKILL.md` and `adapters/codex/plugins/agent-harness-codex/skills/autopilot-ship/SKILL.md` as native Codex Skill/plugin projections; do not consume `skills/autopilot-ship/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info autopilot-ship`. Use `adapters/opencode/skills/autopilot-ship/SKILL.md` and `adapters/opencode/commands/autopilot-ship.md` as native OpenCode projections; do not consume `skills/autopilot-ship/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/autopilot-ship/SKILL.md` and `adapters/claude/skills/autopilot-ship/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-ship/SKILL.md`, while `skills/autopilot-ship/SKILL.md` remains the compatibility reference kept for parity/drift checks.
