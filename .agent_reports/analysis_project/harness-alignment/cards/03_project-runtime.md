# card 03 — Axis 7(project 층) + 런타임 projection 현실 점검

> inspector(축 7+runtime). 대체로 정합 — legacy alias 잔재 위주.

## 확인됨 (finding 아님 — 계약·wiring 일치)
- **하드순서 게이트 3층 일치**: `research/analyze → spec → plans` 가 `CLAUDE.md:25-32`(§0(0)) · `WORKFLOW.md:9-18` · `hooks/artifact-guard.sh:92-101` 동일. 가드 폴더 spec/·plans/·documents/ 동일.
- **artifact-guard 서술↔구현 일치**: "신규 생성순서만 hard 강제, 기존편집·소스 비차단" = `artifact-guard.sh:88-106`(`[ -f "$fp" ] ||` 통과, 소스 `exit 0`). `_internal/`·`.untracked.<sid>` 우회 = `:51,76-79`.
- **Claude 런타임 hook = canonical**: live `~/.claude/settings.json` hook 집합 = worktree `adapters/claude/settings.json`(스크립트 단위 동일). `~/.claude/hooks → adapters/claude/hooks`(main tree) → worktree-vs-main 이슈 없음. 미열거 hook(herdr-agent-state·design-postwrite 등)은 CLAUDE.md "본 문서 확장 말 것" 정책상 의도된 비열거 → phantom 아님.
- **Codex hook 일치**: `~/.codex/hooks.json → adapters/codex/hooks/hooks.json`, 7이벤트(SessionStart·SessionEnd·Stop·UserPromptSubmit·PermissionRequest·PreToolUse·PostToolUse×2) = `codex/ADAPTATION.md:230-284`. `Stop→sessionend` alias 일치.
- **OpenCode 1:1:1**: skills 28 / commands 28 / agents 9 (source·runtime 일치). plugin 심링크 wire.

## 발견
- **[7-1] P2** — drill 회귀 fixture 가 `.claude_reports` 21개 vs `.agent_reports` 1개(`loops/drill/cases/g5_artifact_guard`·`g4_spec_gate`). 구현은 신표준 우선인데 회귀는 legacy 만 → 신표준 순서게이트 무방비. 제안: g5/g4 신표준 fixture 1개 복제.
- **[7-2] P2** — `agent-worklog-state.sh:41` board probe 가 `.claude_reports` 만(신표준 `path.missing` 오보고). 제안: `.agent_reports` 추가. (adapter 사본 동일 — card 00 §S-4.)
- **[7-3] P2(전제 정정)** — OpenCode projection 은 `~/.opencode`(바이너리만) 아니라 `~/.config/opencode`(agent-* 심링크+`opencode.jsonc`+native command/·agent/+plugin). `opencode/ADAPTATION.md:36` 도 그렇게 명시 → 문서 drift 아님, 과제 전제만 정정.

## 미확인
- OpenCode plugin guard throw 실발동 · Codex hooks.json 실 trust/fire — 정적 존재만 확인(런타임 실행 로그는 `check-runtime-projection.sh` 별도 검증 서술).
