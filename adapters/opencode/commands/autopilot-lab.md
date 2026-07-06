---
description: "Run the portable autopilot-lab capability through the OpenCode adapter. Meaning: 빠른 실험 prototype. 학습 세팅과 ckpt 평가·분석 앞뒤를 돕는다."
---

Use the OpenCode adapter realization of portable capability `autopilot-lab`.
This is adapter-owned output generated from `capabilities/autopilot-lab.md`, not a runtime-specific command copy.

1. Read `capabilities/autopilot-lab.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-lab` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract`, run any
   `tool_contract_check`, and obey `runtime_surface` / `fallback` before
   claiming full support. For `unsupported`, stop or use the reported
   `fallback`.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability autopilot-lab [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<task description> [--mode setup|eval|auto] [--parent <slug>] [--ref <similar-model-path>] [--intensity direct|quick|standard|strong|thorough|adversarial] [--qa quick|light|standard|thorough|adversarial] [--report] [--from spec|scaffold|run|eval|summary]`.

Portable contract excerpt:

- Invocation semantics: _빠른 실험 prototype_ entry — 무거운 학습은 사용자가 돌리고, lab 은 그 앞뒤를 돕는다. 2 모드: **setup** (학습 실험 세팅 — spec → scaffold → 실행 명령 안내) / **eval** (학습 완료 ckpt 평가·분석 — metric·ablation·paper 비교·plot·(옵션) 정식 보고서 [prose→autopilot-draft / 음성·미디어는 재생 HTML]). 확장 케이스(기존 세팅에 새 데이터로 재평가·추가 fine-tuning)는 `--parent <slug>` 계보로 흡수 — 새 모드 없음 (fine-tune=setup --parent 로 새 config 갈래, 재평가=eval --parent). experiment 단위 폴더 강제 + STORY narrative + _RUNLOG timeline (⏳대기→✅완료 상태 + 부모 링크) 누적 → 덮어쓰기·휘발·즉흥 차단. analyze-project 의 experiment_conventions.md / similar_models.md 자동 read — 사용자 코드베이스 layer·prefix·config 패턴 1순위. 정련·라이브러리화 졸업은 autopilot-code. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


User arguments from OpenCode: `$ARGUMENTS`

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
