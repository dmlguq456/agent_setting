# depth-2 stage worker — code-test (harness-installer 사이클 3)

당신은 depth-2 stage worker 입니다. worktree `/home/Uihyeop/agent_setting-wt/harness-installer-hooks` (브랜치 `harness-installer-hooks`) 에서 **code-test** 스테이지만 수행하고 산출물 파일만 남긴 뒤 종료합니다. depth-3 분사 금지.

## 입력 (반드시 Read)

- `.agent_reports/plans/2026-07-13_harness-installer-hooks/plan/plan.md` §Phase 4 (code-test 시나리오 명세 — T0~T6)
- `.agent_reports/plans/2026-07-13_harness-installer-hooks/plan/checklist.md` Phase 4 항목(4.1~4.7)
- `.agent_reports/plans/2026-07-13_harness-installer-hooks/dev_logs/step_01_hook_reconfirm.md`, `step_02_generator_extension.md` (code-execute 가 실제로 무엇을 구현했는지)
- `git diff` (이 브랜치의 실제 변경분 — `adapters/claude/bin/sync-native-plugin.py`, `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/hooks/hooks.json` 등)
- `.agent_reports/plans/2026-07-13_harness-installer-impl2/_internal/hooks_inventory.md` (사이클 2 격리 테스트 스크립트 선례 — `test_logs/` 폴더의 사이클 2 스크립트를 형식 참고용으로 Read 해도 됨, 단 이번 사이클 산출물은 새로 작성)
- `.agent_reports/plans/2026-07-13_harness-installer-impl2/test_logs/` 아래 사이클 2 durable 테스트 스크립트 (형식 선례 — 이번 사이클 스크립트가 참고할 구조)

## ⚠️ 테스트 격리 계약 (반드시 준수 — 사이클 1 실 홈 오염 인시던트 이력, 위반 시 재발)

1. temp 환경 테스트는 **HOME/CLAUDE_CONFIG_DIR 를 스크립트 내부 최상단에서 설정하는 단일 self-contained 스크립트 1회 Bash 호출**로만 실행하세요. `export`를 여러 Bash 호출 경계 너머로 유지하려 하지 마세요(각 Bash 호출은 독립 셸입니다 — 이전 호출의 export 는 다음 호출에 안 남습니다. 이게 사이클 1 인시던트의 원인이었습니다).
2. 스크립트 **최상단**(HOME 재할당 이전)에서 실 런타임 홈 파일 sha256 을 캡처하세요: `~/.claude/settings.json`, `~/.codex/config.toml`, `~/.config/opencode/opencode.json`, 그리고 `~/.claude/plugins/`(재귀 — 이번 사이클은 plugin 설치를 다루므로 특히 중요). `trap ... EXIT` 로 스크립트 종료 시 재확인해 byte-unchanged 를 assert 하세요.
3. `claude` CLI 실 통합 테스트(marketplace add/plugin install)를 한다면 **mktemp `CLAUDE_CONFIG_DIR`** 안에서만 하세요. 실 `~/.claude/plugins` 를 대상으로 하는 명령은 절대 실행하지 마세요.
4. hook 발화 검증은 plan Phase 4 T1~T4 대로: mktemp `AGENT_HOME`/`DATA` 디렉토리에 stdin JSON 을 파이프해 hook 스크립트를 직접 실행하는 방식(실 plugin 설치 없이도 env-prefix 경로를 재현 가능 — plan 참조). tracked/untracked 각 1개 temp 프로젝트로 (a) spec-backed cwd 정상 발화 (b) 비spec cwd no-op (c) 하네스 상태 부재 fail-open 을 실측하세요.

## 작업

plan.md §Phase 4 (T0~T6) 을 격리 테스트 스크립트로 작성·실행하세요. 사이클 2 선례(`01_generator_plugin_content.sh` 류 — syntax→import→smoke→functional 단계 구조)를 형식으로 따르되, 이번 사이클 대상(spec 3종 marker 재기준·이중발화·fail-open)에 맞게 새로 작성합니다. 특히:

- **T0**: 생성기 정적 검증 + hooks.json 구조(PreToolUse 3 / PostToolUse 2, spec 3종 command 에 `AGENT_HOME="${CLAUDE_PLUGIN_DATA}"` + `${CLAUDE_PLUGIN_ROOT}/hooks/<name>` 포함) assert.
- **T1**: marker 재기준 — `AGENT_HOME=<mktemp>` 로 hook 에 stdin JSON 파이프 → 마커가 그 mktemp 디렉토리 하위에 생성되고 real `$HOME` 에는 생성되지 않음을 확인. 마커 부재 시 deny, prd.md touch 후 역방향 drift deny 도 확인.
- **T2**: 이중발화 — `$A`(settings.json 경로 모사)와 `$B`(plugin DATA 모사) 두 mktemp 디렉토리로 marker/gate 를 각각 실행해 상호 오염 없음(각자 디렉토리에만 마커 생성) + 멱등성(2회 실행 안전) + 비대칭 케이스(한쪽만 마커 없을 때 그쪽만 deny) 확인.
- **T3**: fail-open — env-prefix 없이(AGENT_HOME unset, `HOME=<tmp>`) hook 실행 시 `agent-home.sh` fallback 으로 정상 degrade(crash 없음), canonical `hooks/*.sh` git diff 무수정 재확인.
- **T4**: self-contained — 생성물의 모든 경로가 `${CLAUDE_PLUGIN_ROOT}`/`${CLAUDE_PLUGIN_DATA}` 기준이거나 PLUGIN_ROOT 내부(`../utilities`)임을 확인, PLUGIN_ROOT 밖 `../` escape 없음.
- **T5**: real-home 결정론 가드 (위 격리 계약 §2 그대로).
- **T6**: 통합 스모크 — `build-manifest.py --check` up-to-date, `harness verify claude --json` 의 `claude.sync-native-plugin` check 가 exit 0(스크립트 위치는 `tools/install/` 또는 `tools/harness.sh` — 직접 찾아서 확인).

발견된 제품 결함은 즉시 code-execute 스코프로 되돌리지 말고(별도 스테이지 소유), **여기서 직접 최소 수정**해도 됩니다 — 단, canonical `hooks/*.sh` 본체 수정은 여전히 금지(불변식). 생성기(`sync-native-plugin.py`)나 생성물 버그라면 고치고 fix 를 기록하세요.

## 산출물

- `.agent_reports/plans/2026-07-13_harness-installer-hooks/test_logs/` 아래 격리 테스트 스크립트(들) + 실행 로그/리포트
- `.agent_reports/plans/2026-07-13_harness-installer-hooks/test_logs/test_report.md` — PASS/FAIL 요약, T0~T6 각각 결과
- `.agent_reports/plans/2026-07-13_harness-installer-hooks/plan/checklist.md` Phase 4 항목 + 완료 게이트(G1~G4 중 검증 가능한 것) `[x]` 갱신

완료 후 PASS/FAIL 카운트 + real-home 가드 결과를 짧게 보고하고 종료하세요. 코드 커밋은 하지 마세요(code-report 가 일괄 커밋합니다).
