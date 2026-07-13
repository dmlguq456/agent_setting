# harness-installer — pipeline summary

## v2 (2026-07-13) — spec update (구현 사이클 1·2 반영)

- snapshot: `_internal/versions/v1/prd.md`. 변경: INST-OPEN-1 확정(hook 채택 2·이월 3·제외 기록), INST-OPEN-3 완료(INSTALL_LAYOUT 514→250줄), INST-OPEN-4 만 잔존(drift-watch 상시 감시로 강등), [cli] verify 절에 채널-인지 계약 추가(실측 오탐 → quick fix 사이클 `harness-installer-fix-verify-gate` 와 동기).
- 구현 현황: 사이클 1(0e6b3fe — CLI 본체·3-런타임 driver·hash-manifest 3-way·Codex plugin wrap, 51/51 PASS) + 사이클 2(8311dcf — Claude plugin content generator·install --plugin·문서 축소, 53/53 PASS). 실환경 verify 로 opencode projection drift 1건 발견·복구 실적.

## v1 (2026-07-12) — 신규 spec 생성

- 계기: 사용자 발화 "claude code와 codex, opencode 등을 바로 플러그인 형태로 쓸 수 있는 installer" (2026-07-12). 라우팅 컨펌 — 새 spec 독립 생성(HLS v3 확장 아님).
- 하드 게이트 근거: `research/cross-platform-agent-frameworks/`(7/9) — GSD hash-manifest 채택 후보 1, Claude plugin 규격 카드, claude-flow 반면교사.
- runtime-currentness 검증(작성 중, 백그라운드 에이전트): Claude Code plugin 은 hooks·bin 까지 탑재 가능(cache self-contained·ephemeral), Codex plugin 은 skills/hooks/MCP/app 4종만(agents .toml 불가 → symlink 병행), OpenCode 는 번들 포맷 부재 + 기존 배선 drift 발견(복수형 디렉토리·`skills.paths` 문서 부재 → INST-OPEN-4).
- 사용자 결정 2건: 2-채널 하이브리드 구조(INST-D-1), CLI 명령 `harness`(INST-D-2).
- 의미↔규칙 경계 체크: 충돌 0 (config merge 충돌 판정도 규칙 처리).
- Step 4 scaffold: worktree `agent_setting-wt/harness-installer-scaffold` 에 headless 분사 (sonnet·fast implementer, ~25분 완주) — 브랜치 커밋 `9792fd3`(skeleton 13 files, 432 insertions) + `20c4f7e`(handoff 보고). 산출: `tools/install/{harness.sh,installer.py,projector,manifest,verifier,drivers/*}` + `adapters/claude/plugin-marketplace/` 대칭 skeleton + `.gitignore` 예외 2줄(Codex 선례 동형). 구문·JSON·CLI 스모크 전부 통과. hash-manifest 는 의도적 `NotImplementedError`(GSD 정독 게이트 준수). 상세 = `_internal/scaffold_v1.md`(브랜치).
- 다음: 사용자 merge 신호 → 브랜치 수확 / 구현 = `autopilot-code` (선행 게이트: GSD `bin/install.js` 정독 + INST-OPEN-4 OpenCode 실측).
