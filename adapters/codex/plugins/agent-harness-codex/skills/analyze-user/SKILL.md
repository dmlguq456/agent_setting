---
name: analyze-user
description: "Use when the user requests analyze-user: cross-project 사용자 성향 프로필 작성·갱신. 코드·작성·분석 패턴을 추출한다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# analyze-user

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/analyze-user.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info analyze-user`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/analyze-user.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info analyze-user`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `analyze-user`
- Supported modes: `init, update`
- Argument shape: `<aspect> [--source <path>] [--mode init|update] [--from discover|analyze|verify|qa|output|summary] [--user-refine]`
- Portable meaning: cross-project 사용자 성향 프로필 작성·갱신. 코드·작성·분석 패턴을 추출한다.

## Portable Contract

- Invocation semantics: 사용자의 cross-project 산출물 (paper / presentation / report / code / memory) 을 다단계로 스캔·분석해 DB `type=profile` 레코드 (`mem profile <stem>`) 의 _범용 작업 성향_ 을 누적·갱신. autopilot-* 와 동급 ceremony — 사용자 프로필은 _한 번 만들어지면 모든 sub-agent 가 default 로 따르는 자료_ 라 작은 오류도 propagating. 따라서 source discovery → aspect 별 분석 → cross-aspect 일관성 검증 → 다중 QA gate (adversarial 고정) → 산출 → pipeline summary 6 phase. QA level 은 _항상 adversarial_ — 사용자 협상 불가. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.



## Projected Portable Details

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


## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before capability routing/spec-changing work: `adapters/codex/bin/preflight.sh route analyze-user [cwd] [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability analyze-user [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]` and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
