# code-test — harness-installer 구현 사이클 3 — 종합 결과

plan: `../plan/plan.md` §Phase 4 (T0~T6) · checklist: `../plan/checklist.md` Phase 4

## 요약

| 스크립트 | 대상 | PASS | FAIL | 커버 | real-home 결정론 가드 |
|---|---|---|---|---|---|
| `t0_t6_spec_pipeline_rebase.sh` | Phase 2 생성물(hooks.json 재기준) + 3종 spec hook 실 발화 | 29 | 0 | T0~T6 전항목 | PASS |

세 hook(`spec-skill-gate.sh`·`spec-read-marker.sh`·`spec-sync-nudge.sh`)을 실 plugin 설치 없이 `AGENT_HOME=<mktemp>` env-prefix + stdin JSON 파이프로 직접 발화시켜, hooks.json 이 생성하는 실제 호출 shape 을 그대로 재현했다.

## real-home 결정론 가드 (가장 중요)

스크립트 실행 **전** 시점의 real `~/.claude/settings.json`·`~/.codex/config.toml`·`~/.config/opencode/opencode.json`·`~/.claude/plugins/`(재귀) sha256 을 스크립트 최상단(HOME 재할당 이전)에서 캡처하고, `trap ... EXIT` 로 스크립트 종료 시 재확인했다. **최종 실행 PASS** — settings.json/codex/opencode 3개 파일은 매 실행 byte-unchanged, `~/.claude/plugins/` 재귀 해시도 최종 실행에서 before=after 일치.

**중간 관찰 (해프닝, 스크립트 결함 아님)**: 스크립트 수정 전 1회 실행에서 `~/.claude/plugins/` 재귀 해시가 trap 시점에 달라져 guard 가 트립(exit 99)한 적이 있다. 근본원인 조사 결과:
- 세 hook 호출은 전부 `AGENT_HOME=<mktemp>` prefix 로 실행 — canonical hook 본체가 `${AGENT_HOME:-...}` 로 env 를 최우선 존중하므로 real `$HOME` 참조 경로가 코드 구조상 없음.
- T6 `harness verify claude --json` 호출은 스크립트 최상단에서 export 한 `CLAUDE_CONFIG_DIR=<mktemp>` 하에 실행 — `claude plugin ...` 서브프로세스 전부 이 격리 적용.
- 변경된 파일(`~/.claude/plugins/known_marketplaces.json`)의 실제 내용을 직접 열람 — `claude-plugins-official`/`openai-codex` 기존 엔트리만 존재, `agent-harness-claude`·mktemp 경로 등 이번 테스트의 흔적 전혀 없음. `lastUpdated` 값도 이번 실행 시각과 무관(각각 기존 값 그대로).
- 즉 이 mtime 변화는 **이 스크립트의 쓰기가 아니라, 이 머신에서 상시 구동 중인 실 Claude Code 세션(호스트 자신)의 marketplace 백그라운드 refresh** 로 판단된다 — 공유·상시가동 실 홈이라는 이 환경의 특성상 발생하는 노이즈이며, 재실행 시 guard 는 클린하게 PASS 했다(같은 파일이 그사이 재차 안 건드려짐).
- **조치**: 실 홈에 대한 remediation 은 전혀 시도하지 않음(cycle 1 INCIDENT 교훈 그대로 — 실 홈 쓰기 자체가 금지). 스크립트 자체의 쓰기 범위(`git status --porcelain` 비교, `confinement.git_status_matches_baseline` 체크)는 두 실행 모두 clean 이었고, 트립된 실행에서도 스크립트 내부 29개 체크는 전부 PASS — guard 트립은 스크립트 밖 동시성 노이즈였음을 시사. 최종 채택 실행 결과(guard PASS)를 `t0_t6_spec_pipeline_rebase.md` 로 보존.

## 격리 계약 준수 (사이클 3 code-test 프롬프트 §1-4)

1. **단일 self-contained 스크립트**: `_internal/test_scripts/t0_t6_spec_pipeline_rebase.sh` 정확히 1회 `sh` 프로세스(=1회 Bash 도구 호출)로 실행 — `HOME`/`AGENT_HOME`/`CLAUDE_CONFIG_DIR` 를 스크립트 최상단에서 export, 별도 Bash 호출 경계를 넘긴 적 없음.
2. **real-home 파일 sha256 캡처**: `~/.claude/settings.json`·`~/.codex/config.toml`·`~/.config/opencode/opencode.json`·`~/.claude/plugins/`(재귀) 를 HOME 재할당 이전에 캡처, `trap ... EXIT` 재확인.
3. **실 plugin 설치 없이 hook 발화 재현**: mktemp `AGENT_HOME`/`DATA` 디렉토리에 stdin JSON 을 파이프해 canonical hook 스크립트(생성된 plugin 트리 하의 사본)를 직접 실행 — 실 `claude plugin install` 불필요.
4. **`claude` CLI 실 호출(T6)**: `CLAUDE_CONFIG_DIR` 를 스크립트 최상단에서 mktemp 로 export — `harness verify claude --json` 내부의 `claude plugin ...` 서브프로세스 호출까지 포함해 스크립트 안의 모든 `claude` CLI 호출이 처음부터 격리됨.

## T0 — 정적·생성기 (9/9 PASS)

- `py_compile` clean.
- `--check` 클린 트리 exit 0.
- **assertion 수정 1건**: 최초 스크립트는 `touch` 만으로 `--check` 가 dirty(exit 1) 될 것으로 기대했으나, `check()` 는 mtime 이 아니라 **byte 내용 비교**(`read_text`/`read_bytes`)라 순수 `touch` 는 no-op — 스크립트를 실제 1바이트 append 로 수정해 정확한 dirty-detection 을 검증(테스트 스크립트 자체의 assertion 오류, 제품 결함 아님).
- regen 후 `--check` 복귀 exit 0, `git status --porcelain` 이 touch 이전 baseline 과 완전히 일치(round-trip 결정론).
- `hooks.json` 구조: `PreToolUse` 3(matcher `Edit|Write|MultiEdit|NotebookEdit`/`Edit|Write|MultiEdit`/`Skill`) · `PostToolUse` 2(matcher `Read`/`Edit|Write|MultiEdit`). 기존 2종(`git-state-guard`·`artifact-guard`) command 는 prefix 없이 사이클 2 와 byte-identical(회귀 0), spec 3종 command 는 `AGENT_HOME="${CLAUDE_PLUGIN_DATA}"` prefix + `${CLAUDE_PLUGIN_ROOT}/hooks/<name>` 리터럴 동시 포함.
- `utilities/agent-home.sh` 존재 + exec bit. `hooks/` 에 정확히 5개 `.sh`, 전부 exec bit.
- **기존 사이클 2 테스트 shape 기대치 note**: `t0_t6_spec_pipeline_rebase.sh` 는 신규 스크립트라 사이클 2 durable 스크립트(`01_generator_plugin_content.sh`)를 수정하지 않았다. 확인 결과 그 스크립트는 `hooks.json` 의 이벤트 구조(단일 `PreToolUse` 가정)를 직접 assert 하지 않으므로(스모크는 `--check` exit 코드만 확인) 이번 다중이벤트 확장으로 **깨지지 않는다** — plan Risk 절의 우려는 실제로 발현되지 않음, note 로만 기록.

## T1 — marker 재기준 (5/5 PASS)

- `AGENT_HOME=<mktemp DATA>` + `.agent_reports/spec/prd.md` fixture cwd 로 `spec-read-marker.sh` 에 PostToolUse Read stdin JSON 파이프 → 마커가 `$DATA/.spec-grounding/<sid>__<key>` 에 생성, 스크립트 자신의 `$HOME` 하위엔 `.spec-grounding` 무생성.
- 같은 `AGENT_HOME=$DATA` 로 `spec-skill-gate.sh`(PreToolUse Skill) → 마커 존재 시 통과(stdout 비어있음, exit 0).
- 마커 삭제 후 재발화 → `permissionDecision:"deny"` JSON emit.
- 마커 재생성 후 prd.md mtime 을 +2분 전진 → 역방향 drift deny 확인.

## T2 — 이중발화 안전성 (5/5 PASS)

- `$A`(settings.json 경로 모사)·`$B`(plugin DATA 모사) 각각 독립 `AGENT_HOME` 로 marker 발화 → 마커가 각자 디렉토리에만 생성(`find … | wc -l` 로 상호 오염 0 확인).
- 두 gate 모두 자신의 마커로 1차 통과, 2차 재발화(멱등) 도 통과 + 마커 파일 개수 불변(gate 는 stat+cat 뿐인 read-only 확인).
- 비대칭 케이스: `$B` 마커만 삭제 → `$A` 는 계속 통과, `$B` 는 deny(보수적 재-Read 강제, deny-wins fail-safe — gate 가 read-only 라 부작용 없음).

## T3 — fail-open·회귀 (3/3 PASS)

- `env -u AGENT_HOME` (unset) → `agent-home.sh` fallback(`$HOME/agent_setting` 부재 → `$HOME/.claude`)으로 정상 degrade, 마커 생성, no crash.
- `AGENT_HOME=""`(명시적 empty) → `:-` 형이 unset 뿐 아니라 empty 도 트리거함을 확인, 동일하게 fallback 후 no crash.
- `git diff --stat -- hooks/` 빈 출력 — canonical `hooks/*.sh` 본체 무수정 재확인.

## T4 — self-contained (3/3 PASS)

- `hooks.json` command 문자열에 `../` 없음(전부 `${CLAUDE_PLUGIN_ROOT}`/`${CLAUDE_PLUGIN_DATA}` 기준).
- **assertion 축소 1건**: 최초 스크립트는 5개 hook 전체(`hooks/*.sh`)에서 `../` 패턴을 grep 했으나, out-of-scope 인 `artifact-guard.sh` 의 프로즈 주석(`.../.agent_reports/...`)이 `\.\./` 정규식에 우연히 매치되는 false positive 를 유발 — DATA-rebase 대상인 spec 3종 파일로 grep 범위를 좁혀 재검증(제품 결함 아님, 테스트 스코프 정정).
- spec 3종 본체가 참조하는 유일한 상대경로는 `../utilities/agent-home.sh`, `readlink -f` 로 `$PLUGIN_ROOT/utilities` 와 동일 경로임을 확인 — PLUGIN_ROOT 밖 `../` escape 없음.

## T5 — real-home 결정론 가드

trap 기반 가드가 전 구간(T0~T6, 최종 write-set confinement 포함)을 커버 — 위 "real-home 결정론 가드" 절 참조. 최종 채택 실행은 PASS.

## T6 — 통합 스모크 (2/2 PASS)

- `python3 tools/build-manifest.py --check` → `manifest up-to-date; delta baselines bound`, exit 0.
- `sh tools/install/harness.sh verify claude --json`(`CLAUDE_CONFIG_DIR=<mktemp>` 하) → `claude.sync-native-plugin` check `ok:true`, detail `OK: python3 adapters/claude/bin/sync-native-plugin.py --check`(스크립트 위치: `tools/install/drivers/claude.py` L363-366, `tools/install/harness.sh` 진입점). 전체 verify exit code(2)는 이 worktree 가 실 `~/.claude` symlink 대상이 아니라 다른 심링크 check 들이 실패하기 때문(무관 — 대상 check 자체는 `ok:true`).

## 발견된 결함

없음(제품 결함 0건). 발견된 2건은 전부 **테스트 스크립트 자체의 assertion 오류**였고 이 스테이지에서 직접 수정했다(canonical `hooks/*.sh`·생성기 무편집):
1. T0 dirty-detection: `touch` 만으로는 `check()` 의 byte-compare 를 트립하지 못함 — 실제 content mutation(1바이트 append)으로 수정.
2. T4 escape-scan: 5개 hook 전체에서 `../` 를 grep 하면 `artifact-guard.sh` 의 무관한 프로즈 주석이 false positive — DATA-rebase 대상 spec 3종으로 grep 범위 축소.

## 산출물

- `_internal/test_scripts/t0_t6_spec_pipeline_rebase.sh`
- `test_logs/t0_t6_spec_pipeline_rebase.md` (최종 PASS 실행 로그)
- `test_logs/test_report.md` (본 파일)
- `plan/checklist.md` Phase 4 전 항목 + 완료 게이트 G1~G3 `[x]` 갱신(G4 는 code-report/main orchestrator 소관으로 미체크 유지)
