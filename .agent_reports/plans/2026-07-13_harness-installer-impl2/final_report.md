# harness-installer — 구현 사이클 2 최종 보고

> plan: `plan/plan.md` · checklist: `plan/checklist.md` · INST-OPEN-1 근거: `_internal/hooks_inventory.md`
> 브랜치 `harness-installer-impl2` (worktree `/home/Uihyeop/agent_setting-wt/harness-installer-impl2`, main 미머지)
> 이월 출처: `.agent_reports/plans/2026-07-13_harness-installer-impl/final_report.md` (사이클 1, main 머지 완료)

## 1. 한 줄 요약

사이클 1이 남긴 Phase 7 Claude 축 이월분을 완결했다 — Claude plugin content generator(`adapters/claude/bin/sync-native-plugin.py`) 신설, `install --plugin` claude 경로 wrapping(`tools/install/drivers/claude.py`), verify 3종(`claude.sync-native-plugin`·`claude.plugin-marketplace-source`·`claude.plugin-registered`) 추가, `INSTALL_LAYOUT.md` 514→250줄 축소까지 **Phase 1~5 전부 완료**. 부산물로 INST-OPEN-1(plugin 탑재 hook 파일별 목록)을 채택 2 / defer 3 / 제외 나머지로 확정했다. **verdict: 사이클 2 목표 전량 달성**. code-test 는 로컬 `claude` CLI(2.1.207) 존재 하에 CLI-gated integration(실제 marketplace add + plugin install)까지 포함해 53/53 PASS, real-home 결정론 가드 3/3 PASS로 확인했다 — 사이클 1 인시던트(실제 `~/.claude/settings.json` 오염)와 같은 실제 홈 오염은 재발하지 않았다.

## 2. 목표 대비 결과

PRD §0.5 설계 원칙 1(2-채널 하이브리드) 항목 기준. 사이클 1에서 이 항목은 "부분"(Codex만 plugin 채널 완결, Claude는 스켈레톤)이었다:

| 원칙 | 사이클 1 | 사이클 2 (이번) | 비고 |
|---|---|---|---|
| 1. 2-채널 하이브리드 | 부분 | **달성** | Claude plugin content generator + `install --plugin` claude 경로 + verify 3종 전부 완결. **3-런타임(Claude·Codex·OpenCode) 중 plugin 채널이 구조적으로 가능한 2개(Claude·Codex)가 모두 완결**되었다. OpenCode는 PRD상 plugin 채널 자체가 부재로 확인된 설계 — **해당 없음(미해당이지 결함이 아님)**, installer CLI가 유일 경로다. |

installer CLI 경로(dev 머신 사용성)는 사이클 1에서 이미 3-런타임 전부 완결됐고, 이번 사이클로 **소비자 경로(plugin 채널)의 나머지 절반(Claude)** 이 채워졌다. 이로써 plugin 채널이 존재할 수 있는 모든 런타임에서 2-채널 하이브리드가 성립한다.

## 3. Phase별 완료 현황

| Phase | 내용 | 상태 | 근거 |
|---|---|---|---|
| 1 | `adapters/claude/bin/sync-native-plugin.py` — Claude plugin content generator + `--check` | ✅ done | checklist 1.1~1.5, `dev_logs/step_01_plugin_generator_claude.md`, test `01_*` 15/15 |
| 2 | `drivers/claude.py` — `install --plugin` wrapping (marketplace add + plugin install) | ✅ done | checklist 2.1~2.2, `dev_logs/step_02_driver_claude_plugin.md`, test `02_*` |
| 3 | `drivers/claude.py checks()` + verifier — verify 3종 | ✅ done | checklist 3.1~3.3, `dev_logs/step_03_verifier_claude_plugin.md`, test `02_*` 24/24 |
| 4 | `INSTALL_LAYOUT.md` 축소 (INST-OPEN-3) | ✅ done | checklist 4.1~4.3, `dev_logs/step_04_install_layout_reduction.md`, test `03_*` 14/14 |
| 5 | code-test — 격리 계약(단일 self-contained 스크립트·mktemp target·결정론 trap·mktemp `CLAUDE_CONFIG_DIR`) | ✅ done | checklist 5.1~5.5, `test_logs/test_report.md` 53/53 |

**설계 인사이트 (구현 중 확정)**:
- **Claude 첫 sync-native 생성기**: Claude는 native 런타임이라 Codex와 달리 sync-native 계열이 원래 없었다. 이 생성기는 plugin 채널이 self-contained(설치본이 version-ephemeral `~/.claude/plugins/cache`로 복사되어 `../` 참조 불가)이기 때문에 **오직 plugin을 물리적으로 materialize하기 위해서만** 존재한다 — Claude의 다른 표면은 repo-root SoT 자체라 생성기가 불필요하다.
- **Codex 대비 확장**: Codex 생성기는 skills만 담지만 Claude 생성기는 skills(28) + agents(9) + hooks(2 채택) + hooks.json을 담는다. `check()`의 excess-file 탐지도 세 콘텐츠 트리 전부를 커버한다(맹목 미러링이었다면 agents/hooks를 누락했을 지점).
- **INST-D-5 parity 유지**: `plugin=True`여도 symlink + copy_once projection을 **항상 병행**한다. plugin은 `agent`/`subagentStatusLine` 키만 인정하므로 settings.json 복사·statusline·mem 복원·CLAUDE.md·PATH launcher를 담을 수 없다 → "plugin이면 symlink 생략"은 명시적 anti-pattern이다.

## 4. INST-OPEN-1 확정 목록

`_internal/hooks_inventory.md` 전수 판정 표를 요약. 판정 기준 = **self-contained(AGENT_HOME 참조 0) + fail-open(하네스 상태 부재 시 조용히 `exit 0` no-op)**:

| 판정 | hook | 사유 |
|---|---|---|
| **채택 (2)** | `git-state-guard.sh` (PreToolUse) | git만 의존, AGENT_HOME 무. non-git dir → `exit 0`. 어떤 소비자에게도 유효한 순수 git 가드 |
| | `artifact-guard.sh` (PreToolUse) | cwd 상향 탐색만, 마커는 artifact root 내부. artifact root 부재 시 no-op. plugin이 싣는 skills와 짝 |
| **defer (3)** | `spec-skill-gate.sh` · `spec-read-marker.sh` · `spec-sync-nudge.sh` (spec 파이프 3종 묶음) | grounding 상태를 `$AGENT_HOME/.spec-grounding`에 write → `${CLAUDE_PLUGIN_DATA}` 재기준 배선 필요. cycle 2 self-contained 원칙을 흐리므로 별도 사이클. 소비자 spec 파이프 지원 요구 확인 시 재개 |
| **제외 (나머지)** | memory 계열(`builtin-memory-guard`·`mem-turn-nudge`·`mem-recall-inject`·`mem-briefing-inject`·`mem-distill-dispatch`·`mem.py`) · statusline 계열(`herdr-agent-state`·`workflow-guard-hook`) · dispatch 계열(`stage-dispatch-reminder`·`worktree-path-guard`) · core-first/marker(`core-first-guard`·`core-read-marker`) · `design-postwrite` | self-contained/fail-open 기준 미달 — mem DB·statusline env·dispatch 인프라·plugin root 밖 node 툴 실행을 전제하거나 CLI 부재 시 안내가 오도됨 |

plugin `hooks/hooks.json`은 채택 2개를 `PreToolUse`에 `${CLAUDE_PLUGIN_ROOT}/hooks/<name>` 경로로 등록한다.

## 4.5. QA·자율 판단 기록

- **QA (code-test)**: 53/53 PASS, FAIL 0. 발견된 제품 결함 없음. 유일하게 스크립트 03의 초기 assertion이 `${CLAUDE_PLUGIN_ROOT}` 리터럴을 과도하게 좁게 요구한 문제 1건을 발견해 **테스트 스크립트 자체를** 수정했다(제품 결함 아님).
- **자율 판단 이벤트 없음 (클린 실행)** — `pipeline_summary.md` 미생성. 파이프라인이 계획대로 진행됐고 중간에 방향을 바꾼 자율 판단 분기 기록이 없다.

## 5. 테스트 결과 요약

`test_logs/test_report.md` 기준:

- **PASS 53 / FAIL 0** (3개 durable 스크립트 합산)
  - `01_generator_plugin_content.sh` — Phase 1 생성기, **15/15** (syntax → import → smoke → functional; idempotent 재실행·touch→`--check` exit 1·stray excess-file 탐지·regen round-trip)
  - `02_driver_plugin_wiring_and_verify.sh` — Phase 2+3 driver 배선 + verify, **24/24** (syntax → import → smoke → functional → **CLI-gated integration**)
  - `03_install_layout_and_regression.sh` — Phase 4 문서 계약 + 회귀, **14/14**
- **CLI-gated integration 실제 실행**: 로컬에 `claude` CLI(2.1.207)가 존재해 SKIP 경로가 아니라 실제 `claude plugin marketplace add` / `plugin install`까지, **mktemp `CLAUDE_CONFIG_DIR`** 안에서 등록·조회·verify가 전부 실행됐다. 등록 전 `claude.plugin-registered`=`ok:False`(정직한 미등록 보고) → `install(plugin=True)` → `registered` → 등록 후 `ok:True`, `installPath`가 real `~/.claude/plugins` 하위가 아님을 assert, verify는 read-only(호출 전후 config 해시 동일).
- **real-home 결정론 가드 3/3 PASS**: 세 스크립트 모두 실행 전 시점의 real `~/.claude/settings.json`·`~/.codex/config.toml`·`~/.config/opencode/opencode.json`·`~/.claude/plugins/`(재귀) sha256을 스크립트 최상단(HOME 재할당 이전)에서 캡처하고 `trap ... EXIT`로 종료 시 재확인했다. **사이클 1 인시던트(`INCIDENT_real_home_touched.md` — 별도 Bash 호출 간 export 유실로 실제 `~/.claude/settings.json` 오염)와 동일한 실제 홈 오염은 재발하지 않았다.** 격리 계약(단일 self-contained 스크립트·명시적 mktemp target·결정론 trap·mktemp `CLAUDE_CONFIG_DIR`)이 구조적으로 재발을 차단했다.
- 회귀: 사이클 1의 51-test suite를 통째 재실행하지는 않고(diff 무관 표면 중복 비용 대비 이득 낮음), diff 표면 대표 스모크로 대체 확인(`py_compile` clean, `build-manifest --check` up-to-date, 전체 런타임 `install`/`verify --dry-run --json` 정상, codex plugin 채널 회귀 없음). 사이클 1 durable suite 원본은 `.agent_reports/plans/2026-07-13_harness-installer-impl/_internal/test_scripts/e2e_lifecycle.sh`에 보존.

## 5.5. INSTALL_LAYOUT.md 축소

- **514줄 → 최종 250줄** (`git diff --stat`: 134 insertions, 398 deletions).
- **계약 사실 전부 보존 확인**(`dev_logs/step_04` 참조): copy-once 근거(settings.json은 runtime-owned, 한 번 복사·재link 금지), Windows 특기(symlink→copy + HOME-injection), Codex 특기(plugin이 agents .toml/prompts/config fragment를 못 담아 symlink projection 여전히 필요), OpenCode 특기(non-destructive merge + 복수형 디렉토리 drift = INST-OPEN-4 caveat), exit code 의미, fleet(`~/.local/bin` launcher) 계약. 대체된 것은 복사-붙여넣기 가능한 `ln -sfn` 런타임별 레시피 나열과 ~275줄 수동 Migration Order 검증 배터리 — 각각 `harness install [runtime]` / `harness verify [runtime]` 참조로 축약됐다.
- **편집팀 polish 모드 반영 완료**(이 스테이지가 호출): 상단 콜아웃을 실행 안내/설계 안내로 분리, 표 셀 과다 서술을 표 밖 sub-bullet으로 분리, "projection"/"merge" 표기 통일, "재-link"→"다시 링크" 등 code-switch 정리. 편집팀 산출물 diff는 이미 반영되어 커밋 대상이다(테스트 시점 225줄에서 polish 후 250줄로, 삭제분 398은 동일·삽입분이 109→134로 증가).

## 6. PRD OPEN 절 갱신 필요 여부

> **이 스테이지(code-report)는 `spec/prd.md`를 편집하지 않는다.** 아래는 main orchestrator가 바로 읽고 판단하도록 기록만 남기는 것이며, **실제 prd 편집은 main orchestrator의 `autopilot-spec update` 몫**이다.

- **INST-OPEN-1** → **closeable (확정)**. plugin 탑재 hook 파일별 목록이 확정됐다 — 채택 2(`git-state-guard.sh`, `artifact-guard.sh`) / defer 3(spec 파이프 3종) / 제외 나머지. PRD §INST-OPEN-1을 "확정(채택 2 / defer 3 / 제외 나머지)"으로 닫을 수 있다.
- **INST-OPEN-3** → **closeable**. `INSTALL_LAYOUT.md`가 계약 서술 + `harness install`/`verify` 참조로 축소 완료됐다. PRD §INST-OPEN-3을 닫을 수 있다.
- **INST-OPEN-4** (OpenCode 복수형 디렉토리 migration) → **OPEN 유지**. 이번 사이클 범위 밖, 미착수.

## 7. 커밋 목록 + 브랜치 상태

브랜치 `harness-installer-impl2` (main 미머지, 이 사이클 전용). **이 스테이지(code-report)가 report 작성 직후 사이클 전체를 일괄 커밋한다** — 커밋 대상은 uncommitted 상태인 `INSTALL_LAYOUT.md` 수정, `tools/install/drivers/claude.py` 수정, `adapters/claude/bin/sync-native-plugin.py` 신규, `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/{skills,agents,hooks}` 신규, `.agent_reports/plans/2026-07-13_harness-installer-impl2/` 산출물 전부다.

(커밋은 code-report 스테이지가 report 작성 직후 일괄 수행 — 최종 해시는 아래 갱신)

merge·push·worktree 정리는 미수행 — main orchestrator 몫.

## 8. Deferred / Open 항목

- **INST-OPEN-4** (OpenCode 복수형 디렉토리 migration): 이번 사이클 범위 밖, OPEN 유지.
- **INST-OPEN-1 defer 하위집합**: spec 파이프 3종 hook(`spec-skill-gate`·`spec-read-marker`·`spec-sync-nudge`)은 `${CLAUDE_PLUGIN_DATA}` 재기준 배선이 필요해 별도 사이클로 이월. 소비자가 plugin만으로 spec 파이프를 쓰려는 요구가 확인되면 재개.
- **PRD 편집**: INST-OPEN-1·INST-OPEN-3의 실제 `spec/prd.md` closeable 반영은 main orchestrator의 `autopilot-spec update` 대기.
