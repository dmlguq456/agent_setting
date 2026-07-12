# harness-installer — pipeline summary

## v1 (2026-07-12) — 신규 spec 생성

- 계기: 사용자 발화 "claude code와 codex, opencode 등을 바로 플러그인 형태로 쓸 수 있는 installer" (2026-07-12). 라우팅 컨펌 — 새 spec 독립 생성(HLS v3 확장 아님).
- 하드 게이트 근거: `research/cross-platform-agent-frameworks/`(7/9) — GSD hash-manifest 채택 후보 1, Claude plugin 규격 카드, claude-flow 반면교사.
- runtime-currentness 검증(작성 중, 백그라운드 에이전트): Claude Code plugin 은 hooks·bin 까지 탑재 가능(cache self-contained·ephemeral), Codex plugin 은 skills/hooks/MCP/app 4종만(agents .toml 불가 → symlink 병행), OpenCode 는 번들 포맷 부재 + 기존 배선 drift 발견(복수형 디렉토리·`skills.paths` 문서 부재 → INST-OPEN-4).
- 사용자 결정 2건: 2-채널 하이브리드 구조(INST-D-1), CLI 명령 `harness`(INST-D-2).
- 의미↔규칙 경계 체크: 충돌 0 (config merge 충돌 판정도 규칙 처리).
- Step 4 scaffold: worktree `agent_setting-wt/harness-installer-scaffold` 에 headless 분사 (skeleton — tools/install/ + Claude plugin-marketplace 대칭 skeleton).
