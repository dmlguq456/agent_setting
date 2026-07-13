---
name: autopilot-ship
description: "Use for autopilot-ship: 앱 배포·출시 준비. build/deploy setup과 ship checklist를 만든다."
metadata:
  portable_source: capabilities/autopilot-ship.md
  adapter: opencode
---

# autopilot-ship

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-ship.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-ship`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-ship.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-ship`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-ship`
- Supported modes: `none`
- Argument shape: `<task description (선택)> [--intensity direct|quick|standard|strong|thorough|adversarial]`
- Portable meaning: 앱 배포·출시 준비. build/deploy setup과 ship checklist를 만든다.

## Portable Contract

- Invocation semantics: _앱 배포 셋업_ entry — 이미 `spec/` 가 잡혀 있고 기능 어느 정도 완성된 자리에서 첫 ship setup·env·domain·migration deploy 안내. 호스팅 선정 (Vercel / Fly / Railway / Cloudflare / EAS) + CI/CD 파일 + `.env.example` + 도메인 가이드 + deploy_record. 실제 배포 명령은 사용자 직접 실행 — 본 skill 은 _안내만_. autopilot-spec 의 _초기 spec·skeleton_ 자리와 작업 본질 분리. 재호출 가능 (env 변경·domain 추가·migration 운영 배포 자리). Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-ship [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
