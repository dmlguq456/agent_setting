# Capability: autopilot-lab

This is the portable capability contract for `autopilot-lab`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract
<!-- GENERATED: harness-manifest.json -->

| Field | Value |
|---|---|
| Identifier | `autopilot-lab` |
| Group | `entry` |
| Supported modes | `setup, eval` |
| Portable meaning | 빠른 실험 prototype. 학습 세팅과 ckpt 평가·분석 앞뒤를 돕는다. |
| Argument shape | `<task description> [--mode setup\|eval\|auto] [--parent <slug>] [--ref <similar-model-path>] [--intensity direct\|quick\|standard\|strong\|thorough\|adversarial] [--report] [--from spec\|scaffold\|run\|eval\|summary]` |

## Invocation Semantics

_빠른 실험 prototype_ entry — 무거운 학습은 사용자가 돌리고, lab 은 그 앞뒤를 돕는다. 2 모드: **setup** (학습 실험 세팅 — spec → scaffold → 실행 명령 안내) / **eval** (학습 완료 ckpt 평가·분석 — metric·ablation·paper 비교·plot·(옵션) 정식 보고서 [prose→autopilot-draft / 음성·미디어는 재생 HTML]). 확장 케이스(기존 세팅에 새 데이터로 재평가·추가 fine-tuning)는 `--parent <slug>` 계보로 흡수 — 새 모드 없음 (fine-tune=setup --parent 로 새 config 갈래, 재평가=eval --parent). experiment 단위 폴더 강제 + STORY narrative + _RUNLOG timeline (⏳대기→✅완료 상태 + 부모 링크) 누적 → 덮어쓰기·휘발·즉흥 차단. analyze-project 의 experiment_conventions.md / similar_models.md 자동 read — 사용자 코드베이스 layer·prefix·config 패턴 1순위. 정련·라이브러리화 졸업은 autopilot-code.

Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.

## Artifact Ownership

Use the shared artifact root rule: prefer `.agent_reports/`; use legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not. Capability-specific output placement follows `core/CONVENTIONS.md` section 5 until this spec is expanded with a stricter per-capability artifact map.

## Role Requirements

Use portable role names from `roles/README.md` and `core/CONVENTIONS.md`. Concrete model names, subagent frontmatter, and runtime-specific tool lists belong in adapter files.

Pipeline intensity follows `core/CONVENTIONS.md §1`: `direct` has no plan stage or durable plan artifact; `quick` is a depth-1 one-shot worker with its inline micro-plan plus plan-check-lite; `standard+` uses the capability's durable work-cycle plan when applicable. `plan-check` is required for every non-`direct` graph, but independent QA is not repeated after every stage by default. Verification rigor for plan-check, selected independent reviews, and final verify is derived from intensity; it does not name a model or introduce a separate stage graph.

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
| Claude Code | `adapters/claude/skills/autopilot-lab/SKILL.md` and `skills/autopilot-lab/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-lab/SKILL.md`, while `skills/autopilot-lab/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info autopilot-lab`. Use `adapters/codex/skills/autopilot-lab/SKILL.md` as the native Codex Skill projection; do not consume `skills/autopilot-lab/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info autopilot-lab`. Use `adapters/opencode/skills/autopilot-lab/SKILL.md` and `adapters/opencode/commands/autopilot-lab.md` as native OpenCode projections; do not consume `skills/autopilot-lab/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/autopilot-lab/SKILL.md` and `adapters/claude/skills/autopilot-lab/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-lab/SKILL.md`, while `skills/autopilot-lab/SKILL.md` remains the compatibility reference kept for parity/drift checks.
