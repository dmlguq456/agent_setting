# harness-installer 사이클 3 — 구현 체크리스트

> plan: `plan.md` · spec: `.agent_reports/spec/harness-installer/prd.md` · carryover: INST-D-6 (사이클 2 defer 3)
> 불변식: **canonical `hooks/*.sh` 무수정** · plugin write 는 `adapters/claude/plugin-marketplace/` 하위만 · real-home byte-unchanged

## Phase 1 — hook 3종 재확인 + wrapper 판정 (P0 선행, 코드 무변경)

- [x] 1.1 `spec-skill-gate.sh` 마커 **읽기 전용**(stat+cat, side-effect 0) + CLI/stdin 분기(L70) 코드 재확인 → dev_logs 기록
- [x] 1.2 `spec-read-marker.sh` 마커 **쓰기**(`mkdir -p`+`printf >`, L38-39) + `--file` 필수(L73) 재확인
- [x] 1.3 `spec-sync-nudge.sh` **read-only·AGENT_HOME 로직 미사용**(inline NUDGE_PY, find_spec_dir=cwd 기준) 재확인 — 태스크 요약("python 헬퍼 경로 해석") 부정확 확정
- [x] 1.4 `--agent-home` = CLI-arg 모드 전용(stdin 미독 → 실 호출서 `exit 64`) → **env-prefix 채택**·`--agent-home` 기각 근거 라인 인용 기록
- [x] 1.5 세 hook 유일 외부참조 = `../utilities/agent-home.sh`(grep 확인) → **utilities 번들 필요** 확정
- [x] 1.6 `${CLAUDE_PLUGIN_DATA}` = 영속·hook command 치환 지원·auto-create (plugins-reference 재확인) → "왜 ROOT 아닌 DATA" 한 줄 근거 기록

## Phase 2 — `sync-native-plugin.py` 확장 (P0, 유일 코드 mutation)

- [x] 2.1 `HOOK_ADOPT` 에 3종 추가(spec-skill-gate·spec-read-marker·spec-sync-nudge)
- [x] 2.2 `UTILITIES_SOURCE`·`UTIL_BUNDLE=["agent-home.sh"]`·`_HOOK_EVENTS`·`_HOOK_DATA_HOME`(spec 3종) 상수 추가
- [x] 2.3 `_HOOK_MATCHERS` 추가 — spec-skill-gate=`Skill`, spec-read-marker=`Read`, spec-sync-nudge=`Edit|Write|MultiEdit` (settings.json 실측)
- [x] 2.4 `_HOOK_SHELLS` 추가 — spec-skill-gate=`sh`, spec-read-marker=`sh`, spec-sync-nudge=`bash`
- [x] 2.5 `hooks_json()` 다중이벤트화 — `HOOK_ADOPT` 순회로 event-그룹 빌드(PreToolUse 3 / PostToolUse 2), 결정론 순서
- [x] 2.6 `hooks_json()` — `_HOOK_DATA_HOME` 멤버 command 에 `AGENT_HOME="${CLAUDE_PLUGIN_DATA}" ` prefix; 기존 2종은 prefix 없이 종전 문자열 유지
- [x] 2.7 `sync()` — utilities 복사 블록 추가(rmtree→mkdir→copy2) + 진입 가드에 `agent-home.sh` 존재 확인
- [x] 2.8 `check()` — utilities byte-compare + excess-file 탐지 블록 추가(hooks 블록 미러)
- [x] 2.9 `HOOK_ADOPT` 주석(L38-40) "deferred"→"adopted (cycle 3, DATA rebasing via env-prefix)" 갱신
- [x] 2.10 모듈 docstring(L14-16)·`hooks_json()` docstring(L85-91) 다중이벤트+DATA 재기준 반영
- [x] 2.11 `python3 sync-native-plugin.py` 실행 → 생성물 materialize, idempotent 재실행 byte-identical
- [x] 2.12 `git diff` 로 canonical `hooks/*.sh` **무수정** 확인 (변경은 생성기 + `plugin-marketplace/` 산출물뿐)

## Phase 3 — 대응 동기화 (P1)

- [x] 3.1 `_internal/hooks_inventory.md` spec 3종 판정 defer→**채택(cycle 3)** + 재기준 방식 한 줄 근거 (실제 경로 정정: plan 기재 `.agent_reports/spec/harness-installer/_internal/hooks_inventory.md` 는 부재 — 실물은 `.agent_reports/plans/2026-07-13_harness-installer-impl2/_internal/hooks_inventory.md`, 해당 파일 갱신)
- [x] 3.2 code-report 핸드오프에 PRD INST-OPEN-1(채택 5로 좁힘)·INST-D-6/pipeline_state `dev:` 이월 완결 갱신 포인터 기록 (prd.md·state 직접 편집 X)

## Phase 4 — code-test 시나리오 명세 (실행은 code-test 몫 — 계획만)

- [x] 4.1 T0 정적·생성기: py_compile / `--check` clean→dirty→regen / hooks.json 구조 assert(PreToolUse 3·PostToolUse 2, spec 3종 DATA prefix) / utilities 존재 / **기존 테스트 shape 기대치 갱신 필요 note** (기존 사이클 2 durable 스크립트는 아직 `PreToolUse` 단일 shape 을 assert 하지 않음 — hooks_json 구조 검사가 없어 실제로는 깨지지 않음, note 만 기록)
- [x] 4.2 T1 marker 재기준: `AGENT_HOME=<mktemp>` stdin 호출 → 마커 그 dir 하위·real HOME 무생성 / 마커 부재 deny / prd touch 역방향 drift deny
- [x] 4.3 T2 이중발화: `$A`/`$B` 마커 디렉토리 분리·상호 write 0 / 둘 다 멱등 통과 / 비대칭 deny-wins fail-safe / gate 2회 멱등(side-effect 0)
- [x] 4.4 T3 fail-open·회귀: env-prefix 없는 settings 경로 fallback resolve·회귀 0 / `AGENT_HOME=""` degrade no-crash / canonical git-diff 무수정
- [x] 4.5 T4 self-contained: 모든 경로 PLUGIN_ROOT/`${CLAUDE_PLUGIN_*}` 기준, `../` escape 0
- [x] 4.6 T5 real-home 결정론 가드: sha256 캡처+`trap EXIT` 재확인(`~/.claude`·`~/.claude/plugins`·`~/.codex`·`~/.config/opencode`), mktemp/marketplace 밖 write 0
- [x] 4.7 T6 통합 스모크: `build-manifest --check` up-to-date / `harness verify claude --json` `claude.sync-native-plugin` exit 0

## 완료 게이트

- [x] G1 생성물: `hooks/{5 .sh + hooks.json}` + `utilities/agent-home.sh`, `--check` clean exit 0
- [x] G2 canonical `hooks/*.sh` 무수정 (env-prefix wrapper 로 재기준 달성)
- [x] G3 이중발화·fail-open 시나리오 code-test PASS, real-home byte-unchanged
- [x] G4 code-report 가 PRD/state 갱신 포인터 기록 (main orchestrator autopilot-spec update 대기 — 이 스테이지 소관 아님) — `final_report.md` §6 참조
