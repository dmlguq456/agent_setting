# harness-installer — 구현 사이클 3 최종 보고

> plan: `plan/plan.md` · checklist: `plan/checklist.md` · carryover: `.agent_reports/plans/2026-07-13_harness-installer-impl2/final_report.md` §4/§8 (INST-OPEN-1 defer 3)
> 브랜치 `harness-installer-hooks` (worktree `/home/Uihyeop/agent_setting-wt/harness-installer-hooks`, main 미머지)

## 1. 한 줄 요약

사이클 2가 INST-OPEN-1에서 **defer**한 spec 파이프 hook 3종(`spec-skill-gate.sh`·`spec-read-marker.sh`·`spec-sync-nudge.sh`)을 `${CLAUDE_PLUGIN_DATA}` 재기준으로 Claude plugin 채널에 탑재했다. canonical hook 본체가 이미 `AGENT_HOME` env 를 최우선 override 로 존중한다는 사실을 코드로 재확인해, `sync-native-plugin.py`(생성기)의 `hooks_json()` 이 spec 3종 command 에 `AGENT_HOME="${CLAUDE_PLUGIN_DATA}"` env-prefix 를 얹는 것만으로 재기준을 완결했다 — **canonical `hooks/*.sh` 본체는 한 줄도 고치지 않았다**. **verdict: 사이클 3 목표(spec 파이프 hook 3종 PLUGIN_DATA 재기준) 전량 달성**. code-test 는 실 plugin 설치 없이 env-prefix + stdin JSON 파이프로 세 hook 을 직접 발화시켜 29/29 PASS, real-home 결정론 가드도 최종 실행 PASS 로 확인했다.

## 2. 목표 대비 결과

| 항목 | 사이클 2 | 사이클 3 (이번) | 비고 |
|---|---|---|---|
| INST-OPEN-1 spec 파이프 3종 | defer(3) | **채택(3) — 완결** | `hooks.json` AGENT_HOME env-prefix 재기준. `HOOK_ADOPT` 채택 set 2→5 |
| canonical `hooks/*.sh` 불변식 | — | **무수정 유지** | `git diff --stat -- hooks/` 빈 출력(T3 확인) — 재기준은 생성기(plugin `hooks.json`)에서만 수행 |
| 이중발화 안전성 | — | **검증 완료** | settings.json 경로(non-prefix)와 plugin `hooks.json` 경로(DATA-prefix)가 물리적으로 분리된 마커 디렉토리에 각자 기록 — 상호 오염 0, deny-wins fail-safe |

사이클 2가 self-contained 원칙 유지를 위해 미룬 부분을 이번 사이클이 마무리해, **INST-OPEN-1 채택 set 이 2 → 5(전체 나머지는 여전히 제외)**로 확장됐다.

## 3. Phase별 완료 현황

| Phase | 내용 | 상태 | 근거 |
|---|---|---|---|
| 1 | hook 3종 재확인 + wrapper 방식 판정(env-prefix 채택, `--agent-home` 기각, utilities 번들 필요) — 코드 무변경, 결정 기록 | ✅ done | checklist 1.1~1.6, `dev_logs/step_01_hook_reconfirm.md` |
| 2 | `sync-native-plugin.py` 확장 — `HOOK_ADOPT`+3, `_HOOK_EVENTS`/`_HOOK_DATA_HOME`/`_HOOK_MATCHERS`/`_HOOK_SHELLS`, `hooks_json()` 다중이벤트+DATA env-prefix, `sync()` utilities 동반 복사, `check()` 확장, docstring 동기화 | ✅ done | checklist 2.1~2.12, `dev_logs/step_02_generator_extension.md` |
| 3 | 대응 동기화 — `_internal/hooks_inventory.md` defer→adopt, PRD OPEN 갱신 필요 기록 | ✅ done | checklist 3.1~3.2, 본 보고서 §6 |
| 4 | code-test — 실 plugin 설치 없이 env-prefix+stdin 재현, T0~T6 + real-home 결정론 가드 | ✅ done | checklist 4.1~4.7, `test_logs/test_report.md` 29/29 |

**설계 인사이트 (구현 중 확정)**:
- **wrapper 경로 = env-prefix, `--agent-home` 기각**: 세 hook 모두 `[ "$#" -gt 0 ]` 분기로 CLI-arg 모드에 진입하면 stdin JSON 을 읽지 않고 `--skill`/`--file` 필수 인자를 요구한다. Claude 는 hook 을 stdin JSON 으로 호출하므로 `--agent-home` 플래그만 얹으면 CLI 모드로 falling 해 `exit 64` — 실 호출 경로에서 비가용임을 코드로 확정했다. env-prefix(`AGENT_HOME="${CLAUDE_PLUGIN_DATA}" <shell> "<path>"`)는 args 0 → stdin 모드를 그대로 유지하며 env 만 override 해 canonical 무수정 목표를 더 깔끔히 달성.
- **`spec-sync-nudge.sh` 는 기능상 DATA 재기준 불요**: read-only 이고 `find_spec_dir` 가 cwd 기준으로 spec-backed 여부를 판정, `AGENT_HOME` 을 로직에서 전혀 읽지 않는다. 다만 (a) 태스크 계약상 3종 묶음에 포함, (b) `set -euo pipefail` 하에서 env-prefix 가 fallback subshell(`agent-home.sh`) 호출을 회피해 더 견고하므로 uniformity+robustness 목적으로 동일 env-prefix 를 적용했다(defensive-only, dev_logs 명시).
- **`utilities/agent-home.sh` 번들 필요**: 세 hook 의 유일 외부 참조(`../utilities/agent-home.sh`)가 plugin 트리에서 `${CLAUDE_PLUGIN_ROOT}/utilities/agent-home.sh` 로 resolve — PLUGIN_ROOT 밖 escape 아님. env-prefix 로 런타임엔 미실행되나 self-contained 방어 + `set -e` 안전을 위해 번들했다.

## 4. 이식 완료 hook 목록

| hook | 이벤트 | matcher | shell | DATA 재기준 |
|---|---|---|---|---|
| `spec-skill-gate.sh` | PreToolUse | `Skill` | `sh` | `AGENT_HOME="${CLAUDE_PLUGIN_DATA}"` env-prefix — 마커 **읽기**(stat+cat) |
| `spec-read-marker.sh` | PostToolUse | `Read` | `sh` | 〃 — 마커 **쓰기**(`mkdir -p`+`printf >`) |
| `spec-sync-nudge.sh` | PostToolUse | `Edit\|Write\|MultiEdit` | `bash` | 〃(defensive-only, 기능상 AGENT_HOME 미사용 — read-only) |

재기준 방식은 세 hook 동일: `AGENT_HOME="${CLAUDE_PLUGIN_DATA}" <shell> "${CLAUDE_PLUGIN_ROOT}/hooks/<name>"`. 기존 채택 2종(`git-state-guard.sh`·`artifact-guard.sh`)의 command 는 prefix 없이 사이클 2 와 byte-identical(회귀 0). `hooks.json` 은 `PreToolUse`(git-state-guard·artifact-guard·spec-skill-gate 3개) / `PostToolUse`(spec-read-marker·spec-sync-nudge 2개)로 확장됐다. **canonical `hooks/*.sh` 본체는 무수정**(재기준은 plugin `hooks.json` 의 command 문자열에서만 수행).

## 5. 이중-발화 안전성 결론

settings.json 경로(dev symlink, env-prefix 없음 → `agent-home.sh` fallback, 보통 `$HOME/agent_setting`)와 plugin `hooks.json` 경로(`AGENT_HOME="${CLAUDE_PLUGIN_DATA}"` → `~/.claude/plugins/data/agent-harness-claude-agent-harness/`)는 **물리적으로 분리된 `.spec-grounding` 디렉토리**를 쓴다. code-test T2 로 확인한 안전성:

- 두 경로가 각자의 마커 디렉토리에만 write — 상호 오염 0(`find … | wc -l` 대조).
- 각 경로는 자신의 마커로 독립적으로 통과 + **멱등**(gate 는 stat+cat 뿐인 read-only, 2회 실행에도 side-effect 0).
- **비대칭 케이스(deny-wins fail-safe)**: 한쪽 마커만 삭제되면 그 경로만 deny — Claude 의 다중 hook 병합 규칙상 어느 한 PreToolUse deny 가 tool 호출을 막으므로, plugin 을 세션 중간에 설치한 경우 1회 재-Read 가 강제되는 **정상적인 보수적 fail-safe** 다(검사가 read-only 라 부작용 없음, 재-Read 비용도 저렴).

## 6. 테스트 결과 요약

`test_logs/test_report.md`·`test_logs/t0_t6_spec_pipeline_rebase.md` 기준:

- **PASS 29 / FAIL 0** (`t0_t6_spec_pipeline_rebase.sh`, T0~T6 전항목 단일 self-contained 스크립트)
  - T0 정적·생성기(9/9): `py_compile` clean, `--check` clean→dirty→regen round-trip, `hooks.json` 구조(PreToolUse 3/PostToolUse 2) + spec 3종 `AGENT_HOME="${CLAUDE_PLUGIN_DATA}"` prefix 확인, `utilities/agent-home.sh` 존재+exec bit.
  - T1 marker 재기준(5/5): `AGENT_HOME=<mktemp>` stdin 호출 → 마커가 그 dir 하위에만 생성(real `$HOME` 무생성), 마커 부재 시 deny, prd.md mtime 역전 시 drift deny.
  - T2 이중발화(5/5): §5 참조.
  - T3 fail-open·회귀(3/3): env-prefix 없는 settings 경로 fallback 정상 degrade, `AGENT_HOME=""` empty degrade no-crash, canonical `hooks/*.sh` git-diff 무수정.
  - T4 self-contained(3/3): 생성 `hooks.json`·번들 스크립트 전부 `${CLAUDE_PLUGIN_ROOT}`/`${CLAUDE_PLUGIN_DATA}` 기준, PLUGIN_ROOT 밖 `../` escape 0.
  - T6 통합 스모크(2/2): `build-manifest.py --check` up-to-date, `harness verify claude --json` 의 `claude.sync-native-plugin` check `ok:true`.
  - 발견된 제품 결함 0건 — 발견된 2건은 전부 테스트 스크립트 자체의 assertion 오류(touch-only dirty-detection 오기대, `../` grep 범위 과다)로 이 스테이지에서 스크립트만 수정했다(canonical 코드·생성기 무편집).
- **real-home 결정론 가드**: 스크립트 최상단(HOME 재할당 이전)에서 real `~/.claude/settings.json`·`~/.codex/config.toml`·`~/.config/opencode/opencode.json`·`~/.claude/plugins/`(재귀) sha256 캡처 후 `trap ... EXIT` 로 재확인 — **최종 채택 실행 PASS**(byte-unchanged).
  - **중간 해프닝(스크립트 결함 아님)**: 수정 전 1회 실행에서 `~/.claude/plugins/` 재귀 해시가 트립한 적이 있으나, 원인 조사 결과 세 hook 호출·T6 `claude` CLI 서브프로세스 전부 `AGENT_HOME=<mktemp>`/`CLAUDE_CONFIG_DIR=<mktemp>` 로 격리돼 있었고, 변경 파일(`known_marketplaces.json`) 내용에 이번 테스트 흔적이 전혀 없어 **이 머신에서 상시 구동 중인 별도 실 Claude Code 세션의 marketplace 백그라운드 refresh**로 판정 — 실 홈에 대한 remediation 은 시도하지 않았고(cycle 1 INCIDENT 교훈 유지), 재실행에서 guard 는 클린 PASS 했다.

## 7. PRD/INST-D-6 갱신 필요 사항 (이 스테이지는 `spec/prd.md`·`pipeline_state.yaml` 편집 안 함)

main orchestrator 의 `autopilot-spec update` 로 반영할 항목:

- **INST-OPEN-1**: "확정(채택 2 / defer 3 / 제외 나머지)" → **"확정(채택 5 — `git-state-guard.sh`·`artifact-guard.sh`·`spec-skill-gate.sh`·`spec-read-marker.sh`·`spec-sync-nudge.sh` / 제외 나머지)"**로 좁힐 것.
- **INST-D-6 / `pipeline_state.yaml` `dev:` 이월 항목**: "spec 파이프 hook 3종 PLUGIN_DATA 재기준"이 이번 사이클(cycle 3)로 **완결** — decisions_locked·이월 문구를 완결 반영으로 갱신할 것.
- **INST-OPEN-4**(OpenCode 복수형 migration): 이번 사이클 범위 밖, **OPEN 유지**(변경 없음).

## 8. 커밋 목록 + 브랜치 상태

브랜치 `harness-installer-hooks` (main 미머지, 이 사이클 전용). 사이클 2와 동형인 phase 별 커밋 컨벤션으로 이 스테이지(code-report)가 일괄 커밋했다:

```
67d7402 test+report: harness-installer cycle 3 — code-test (29/29 PASS) + final_report
af94367 docs: harness-installer Phase 3 — hooks_inventory.md defer→adopt
82c394e feat: harness-installer Phase 2 — spec 파이프 3종 hook PLUGIN_DATA 재기준
```

(base = `b4e303a`, 이 worktree 의 branch-tip 커밋. **주의**: 이 worktree 에는 본 사이클과 무관한 `skill-design-refactor` 작업(다수 `SKILL.md`/`README.md` 수정, 신규 `references/*` 디렉토리)이 **미커밋 상태로 함께 존재**한다 — 이 스테이지는 그 변경분을 건드리지 않았다(범위 밖). main orchestrator 가 머지/정리 시 두 작업 계열을 혼동하지 않도록 주의 필요.)

merge·push·worktree 정리는 미수행 — main orchestrator 몫.

## 9. Deferred / Open 항목

- **INST-OPEN-4**(OpenCode 복수형 디렉토리 migration): 이번 사이클 범위 밖, OPEN 유지.
- **PRD/state 편집**: §7 의 실제 `spec/prd.md`·`pipeline_state.yaml` 반영은 main orchestrator 의 `autopilot-spec update` 대기.
- **worktree 내 비관련 미커밋 변경**: `skill-design-refactor` 계열 `SKILL.md`/`README.md`/`references/*` 수정이 이 worktree 에 미커밋 상태로 남아 있음 — 이 사이클 소관 아니므로 그대로 두었다. main orchestrator 가 처리 방침(별도 브랜치 분리 등)을 결정해야 함.
