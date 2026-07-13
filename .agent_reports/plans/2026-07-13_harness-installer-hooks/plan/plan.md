---
status: draft
created: 2026-07-13
cycle: 3
carryover_from: .agent_reports/plans/2026-07-13_harness-installer-impl2/
spec: .agent_reports/spec/harness-installer/prd.md
prd_open_touched: "INST-OPEN-1 defer 하위집합(spec 파이프 3종)을 채택으로 전환 — plugin hooks.json 이 ${CLAUDE_PLUGIN_DATA} 재기준으로 3종을 탑재. 이 스테이지는 prd.md 를 편집하지 않음 — code-report 가 main orchestrator 의 autopilot-spec update 로 INST-OPEN-1 문구를 '채택 5 / 제외 나머지'로 갱신할지 기록만 남긴다."
phases:
  - "Phase 1: hook 3종 재확인 + wrapper 방식 판정 (env-prefix 채택, --agent-home 기각, utilities 번들 필요) — 결정 기록, 코드 무변경 (P0 선행)"
  - "Phase 2: sync-native-plugin.py 확장 — HOOK_ADOPT+3, event/matcher/shell/DATA 메타, hooks_json 다중이벤트 + AGENT_HOME=${CLAUDE_PLUGIN_DATA} env-prefix, sync() utilities/agent-home.sh 동반 복사, check() 확장, docstring/comment 동기화 (P0)"
  - "Phase 3: 대응 동기화 — _internal/hooks_inventory.md defer→adopt, PRD OPEN 갱신 필요 기록 (P1)"
  - "Phase 4: code-test 시나리오 명세 — marker 재기준·이중발화·fail-open·real-home 결정론 가드 (실행은 code-test 몫)"
---

# harness-installer — Implementation Cycle 3 (spec 파이프 hook PLUGIN_DATA 재기준)

## Goal

사이클 2 가 INST-OPEN-1 에서 **defer** 한 spec 파이프 hook 3종(`spec-skill-gate.sh`·
`spec-read-marker.sh`·`spec-sync-nudge.sh`)을 Claude plugin 채널에 탑재한다. defer 사유는
"grounding 상태를 `$AGENT_HOME/.spec-grounding` 에 write → `${CLAUDE_PLUGIN_DATA}` 재기준 배선
필요, cycle 2 self-contained 원칙을 흐림"(사이클 2 `final_report.md` §4)이었다. 이번 사이클이
그 재기준 배선을 완결한다.

**핵심 발견(코드 재확인 결과) — canonical 스크립트 무수정으로 재기준 가능**: 세 hook 모두 이미
`AGENT_HOME="${AGENT_HOME:-$(.../utilities/agent-home.sh)}"` 로 `AGENT_HOME` env 를 최우선
override 로 존중한다. 따라서 plugin `hooks/hooks.json` 의 command 문자열에
`AGENT_HOME="${CLAUDE_PLUGIN_DATA}"` env-prefix 를 얹으면 세션 마커가 `${CLAUDE_PLUGIN_DATA}/.spec-grounding/`
에 떨어진다 — **canonical `hooks/*.sh` 본체를 한 줄도 고치지 않는다.** 유일한 물리 산출물은
`sync-native-plugin.py`(생성기)의 확장 + 생성되는 plugin 트리다.

**In-scope**: (1) `sync-native-plugin.py` 에 spec 파이프 3종 + `utilities/agent-home.sh` 번들
추가, (2) `hooks_json()` 이 PreToolUse+PostToolUse 두 이벤트 그룹을 생성하고 spec 3종 command 에
`${CLAUDE_PLUGIN_DATA}` env-prefix 를 얹도록 확장, (3) `sync()`/`check()` 가 새 파일·번들을
커버, (4) `_internal/hooks_inventory.md` defer→adopt 동기화, (5) code-test 시나리오 명세.

**Out of scope (명시)**:
- canonical `hooks/*.sh` 본체 의미 변경 — **불가**(무수정이 목표이자 달성 가능). 만약
  code-execute 가 무수정으로 불가능한 벽을 만나면 STOP+보고, 즉흥 편집 금지.
- INST-OPEN-4(OpenCode 복수형 migration) — OPEN 유지.
- `spec/prd.md` 편집 — INST-OPEN-1 문구 갱신은 main orchestrator 의 `autopilot-spec update` 몫;
  이 plan 은 **갱신 필요 여부만** 기록.
- Codex/OpenCode plugin 채널 — 이번 사이클은 Claude plugin 전용.

---

## Current State Analysis (이 worktree, 브랜치 `harness-installer-hooks`, 코드로 검증)

### 재기준 대상 3종 — 상태 파일 read/write 실측

| hook | 이벤트 | matcher (settings.json 실측) | shell | `.spec-grounding` 상호작용 | AGENT_HOME 용도 |
|---|---|---|---|---|---|
| `spec-skill-gate.sh` | PreToolUse | `Skill` (L73-77) | `sh` | 마커 **읽기**(stat+cat, `$AGENT_HOME/.spec-grounding/${sid}__${key}`) | 마커 base dir |
| `spec-read-marker.sh` | PostToolUse | `Read` (L140-149) | `sh` | 마커 **쓰기**(`mkdir -p`+`printf > $AGENT_HOME/.spec-grounding/...`) | 마커 base dir |
| `spec-sync-nudge.sh` | PostToolUse | `Edit\|Write\|MultiEdit` (L125-134) | `bash` | **없음** — read-only, 파일 write 0 | (설정·export 되나 로직 미사용 — 아래) |

- **spec-skill-gate.sh**(L34-63): `check_gate()` 가 `$AGENT_HOME/.spec-grounding/${sid}__${key}`
  를 `stat`/`cat` 으로 **읽기만** 한다. spec-backed cwd + prd 재-Read drift 를 게이트. side-effect
  0(순수 read-only 검사). → **DATA 재기준 필요**(마커를 어디서 읽느냐가 판정을 좌우).
- **spec-read-marker.sh**(L18-40): `mark_read()` 가 `mkdir -p "$AGENT_HOME/.spec-grounding"` 후
  마커에 mtime 을 **쓴다**. → **DATA 재기준 필요**(마커를 어디에 쓰느냐가 게이트 통과 증거).
- **spec-sync-nudge.sh**: `AGENT_HOME` 을 L29 에서 설정하고 L30 에서 export 하지만, **로직
  본체(inline `NUDGE_PY`)는 AGENT_HOME 을 전혀 읽지 않는다**(spec-backed 판정은 `find_spec_dir`
  가 cwd 기준 `.agent_reports|.claude_reports/spec/pipeline_state.yaml` 를 상향 탐색; 파일
  write 0, additionalContext 만 emit — 자체 주석 "Read-only 불변식: DB·파일 write 0"). 태스크
  요약("AGENT_HOME 은 python 헬퍼 실행 경로 해석에 쓴다")은 **부정확** — python 은 inline
  문자열(`python3 -c "$NUDGE_PY"`)이라 외부 헬퍼 경로 해석에 AGENT_HOME 을 안 쓴다. →
  **기능상 DATA 재기준 불필요.** 단 (a) plugin 탑재 대상 3종에는 포함(태스크 계약), (b)
  `set -euo pipefail` 하에서 AGENT_HOME 미설정 시 `$("$HOOK_DIR/../utilities/agent-home.sh")`
  subshell 이 실행되므로, env-prefix 를 얹으면 이 subshell 호출을 회피해 더 견고 → **uniformity+
  robustness 목적으로 3종 모두 env-prefix 적용**(spec-sync-nudge 는 defensive-only 로 명시).

### 외부 헬퍼 의존 — `utilities/agent-home.sh` 단 하나 (grep 검증)

세 hook 이 참조하는 유일 외부 파일 = `$SCRIPT_DIR/../utilities/agent-home.sh`(각 L8~L29). inline
python 외 다른 헬퍼 파일 참조 없음. plugin 트리에서 `$SCRIPT_DIR = ${CLAUDE_PLUGIN_ROOT}/hooks/`
이므로 `../utilities/agent-home.sh = ${CLAUDE_PLUGIN_ROOT}/utilities/agent-home.sh` — **PLUGIN_ROOT
안**(루트 밖 `../` escape 아님). env-prefix 로 AGENT_HOME 을 항상 설정하면 이 fallback 은
런타임에 실행되지 않지만, self-contained 방어(subshell 이 살아있는 경로가 resolve 가능하도록) +
spec-sync-nudge 의 `set -e` 안전을 위해 **`utilities/agent-home.sh` 를 plugin 에 번들**한다.

### `agent-home.sh` precedence (fail-open 근거, 코드로 검증)

`AGENT_HOME`(set·non-empty) → `CLAUDE_HOME` → `$HOME/agent_setting`(존재 시) → `$HOME/.claude`.
plugin hooks.json 의 env-prefix 가 `AGENT_HOME="${CLAUDE_PLUGIN_DATA}"` 를 넘기면 첫 분기에서
확정. hook 본체의 `${AGENT_HOME:-...}` 는 `:-` 형이라 **unset·empty 둘 다** fallback 을 트리거
→ 만약 `${CLAUDE_PLUGIN_DATA}` 가 비면(정상 경로에선 auto-create 되어 발생 안 함) agent-home.sh
fallback 으로 degrade(no crash). settings.json 배선은 env-prefix 를 안 실으므로 기존 fallback
그대로 — **회귀 0**.

### 현행 생성기 `sync-native-plugin.py` (사이클 2, 코드로 검증)

- `HOOK_ADOPT = ["git-state-guard.sh", "artifact-guard.sh"]`(L41), 주석 L38-40 "spec-pipeline
  trio deferred (would need ${CLAUDE_PLUGIN_DATA} rebasing)" — **갱신 대상**.
- `_HOOK_MATCHERS`/`_HOOK_SHELLS`(L44-51) — 2종만.
- `hooks_json()`(L85-109) — **`PreToolUse` 만 하드코딩**. 이벤트가 단일이라 다중이벤트 확장 필요.
- `sync()`(L117-142) — skills/agents/hooks copytree + `for name in HOOK_ADOPT: copy2`. utilities
  복사 없음.
- `check()`(L150-215) — plugin.json/marketplace.json/hooks.json byte-compare + skills/agents/hooks
  per-file + excess-file 탐지. utilities 커버 없음.
- 현행 생성물 hooks.json = `{"hooks":{"PreToolUse":[git-state, artifact]}}`(디스크 실측).
  plugin 트리 top = `agents/ hooks/ README.md skills/`(utilities 없음).

### 이중발화 표면 (settings.json vs plugin hooks.json)

- settings.json(비-plugin, dev symlink): `sh "$HOME/.claude/hooks/spec-skill-gate.sh"` 등,
  env-prefix 없음 → AGENT_HOME 은 agent-home.sh fallback(보통 `$HOME/agent_setting`) → 마커는
  `$HOME/agent_setting/.spec-grounding/`.
- plugin hooks.json: `AGENT_HOME="${CLAUDE_PLUGIN_DATA}" sh "${CLAUDE_PLUGIN_ROOT}/hooks/..."`
  → 마커는 `~/.claude/plugins/data/agent-harness-claude-agent-harness/.spec-grounding/`.
- **두 마커 디렉토리가 물리적으로 분리** → 파일 레벨 상호 오염 없음(§Phase 4 이중발화 분석).

---

## Runtime-currentness 검증 (2026-07-13, `code.claude.com/docs/en/plugins-reference` WebFetch)

사이클 2 가 `${CLAUDE_PLUGIN_ROOT}` 를 command 경로에 쓴 근거 문서를 재확인. 이번 사이클의 핵심
사실을 원문 인용으로 고정:

1. **hook command 는 `${CLAUDE_PLUGIN_DATA}` 를 포함한 변수 치환을 지원**(doc §Environment variables,
   원문: *"The `command` value supports the same variable substitutions as MCP and LSP server
   configs: `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`, `${CLAUDE_PROJECT_DIR}`,
   `${user_config.*}`, and any `${ENV_VAR}` from the environment"*). → hooks.json command 문자열에
   `${CLAUDE_PLUGIN_DATA}` 를 env-prefix 로 실을 수 있음 **확정**.
2. **`${CLAUDE_PLUGIN_DATA}` = 업데이트 생존 영속 디렉토리**(원문: *"a persistent directory for
   plugin state that survives updates … created automatically the first time this variable is
   referenced"*), 경로 = `~/.claude/plugins/data/{id}/`(id = `agent-harness-claude-agent-harness`).
   → 마커가 auto-create 되는 DATA 에 안착, `mkdir -p` 로 하위 `.spec-grounding` 생성 가능.
3. **`${CLAUDE_PLUGIN_ROOT}` = 버전-ephemeral**(원문: *"This path changes when the plugin updates …
   treat it as ephemeral and **do not write state here**"*). → **왜 DATA 인가**(한 줄 근거):
   세션 grounding 마커는 "설치 생존 상태"이므로 공식 문서가 상태 저장 금지라고 명시한 ROOT(cache)가
   아니라, 상태 저장용으로 축복된 DATA 에 둔다. (마커가 날아가도 게이트는 fail-open 재-Read 강제라
   안전하지만, 의도가 영속 상태이므로 DATA 가 규범상 맞는 자리.)
4. **plugin hooks 는 user settings.json hooks 와 병합**되어 함께 발화(doc §hooks). → 이중발화
   시나리오(Phase 4) 실재 — 멱등성·마커 분리로 안전.
5. shell-form + double-quoted `${CLAUDE_PLUGIN_ROOT}` 는 공식 예시 패턴(원문 예시
   `"command": "\"${CLAUDE_PLUGIN_ROOT}\"/scripts/format-code.sh"`). env-prefix 는 shell-form 필수
   (exec form 은 env 접두 불가) → 사이클 2 shell-form 관례 유지.

---

## Change Plan

Phase 의존: **Phase 1(결정) → Phase 2(생성기 확장) → Phase 3(동기화)**. Phase 4 는 명세(코드
무변경) — code-test 로 넘기는 계약. 실제 코드 mutation 은 Phase 2·3 뿐.

---

### Phase 1 — hook 3종 재확인 + wrapper 방식 판정 (P0 선행, 코드 무변경 · 결정 기록)

이 Phase 는 산출물 코드가 없다 — code-execute 가 Phase 2 진입 전 아래 결정을 **재확인**하고
`dev_logs/` 에 기록만 한다(코드로 반증되면 STOP+보고).

**결정 1 — wrapper 경로 = env-prefix (canonical 무수정), `--agent-home` 기각.**
- `--agent-home` CLI 플래그는 존재하나 **CLI-arg 모드 전용**이다. 세 hook 모두 `if [ "$#" -gt 0 ]`
  분기(gate L70, marker L42)로 args 가 있으면 CLI 모드로 진입하는데, 이 모드는 (a) stdin JSON 을
  **읽지 않고**, (b) gate 는 `--skill` 필수(L107 `[ -n "$skill" ] || exit 64`), marker 는
  `--file` 필수(L73)다. Claude 는 hook 을 **stdin 에 JSON 을 파이프**해 호출하고 `--skill`/`--file`
  을 안 넘기므로, `--agent-home` 만 얹으면 CLI 모드로 falling → skill/file 미제공 → `exit 64`.
  **∴ `--agent-home` 는 실 호출(stdin) 경로에서 비가용.** (태스크가 예상한 벽 — 코드로 확정.)
- **채택 = env-prefix**: `AGENT_HOME="${CLAUDE_PLUGIN_DATA}" <shell> "${CLAUDE_PLUGIN_ROOT}/hooks/<name>"`.
  hook 본체는 args 0 → **stdin JSON 모드** 정상 진입(skill/file/session 을 JSON 에서 파싱),
  AGENT_HOME env 만 DATA 로 override. **canonical `hooks/*.sh` 무수정** 목표를 `--agent-home`
  보다 더 깔끔히 달성(플래그 파싱 경로 안 건드림).

**결정 2 — `utilities/agent-home.sh` 를 plugin 에 번들.**
- 세 hook 의 유일 외부 참조. env-prefix 로 런타임엔 미실행이나, PLUGIN_ROOT 안에 실존해야
  self-contained(subshell resolve 가능) + spec-sync-nudge 의 `set -e` 안전. `../utilities` 는
  PLUGIN_ROOT 내부라 cache `../` escape 위반 아님.

**결정 3 — spec-sync-nudge 는 DATA 재기준이 기능상 불요(read-only, AGENT_HOME 미사용)이나,
uniformity+`set -e` 회피 목적으로 env-prefix 를 동일 적용**(defensive-only 로 dev_logs 명시).

- **Done when**: dev_logs 에 세 결정이 코드 라인 인용과 함께 기록되고, 반증 없음 확인.

---

### Phase 2 — `sync-native-plugin.py` 확장 (P0, 유일 코드 mutation 핵심)

**Target**: `adapters/claude/bin/sync-native-plugin.py`. 아래는 최소·구조보존 확장(사이클 2 형태
유지, 새 shape 발명 금지).

**Step 2.1 — 상수·메타 확장.**
- `HOOK_ADOPT` 에 3종 추가 →
  `["git-state-guard.sh", "artifact-guard.sh", "spec-skill-gate.sh", "spec-read-marker.sh", "spec-sync-nudge.sh"]`.
- 새 상수:
  - `UTILITIES_SOURCE = ROOT / "utilities"`, `UTIL_BUNDLE = ["agent-home.sh"]`.
  - `_HOOK_EVENTS = {"git-state-guard.sh": "PreToolUse", "artifact-guard.sh": "PreToolUse",
    "spec-skill-gate.sh": "PreToolUse", "spec-read-marker.sh": "PostToolUse",
    "spec-sync-nudge.sh": "PostToolUse"}`.
  - `_HOOK_DATA_HOME = {"spec-skill-gate.sh", "spec-read-marker.sh", "spec-sync-nudge.sh"}`
    (env-prefix 대상).
- `_HOOK_MATCHERS` 추가: `"spec-skill-gate.sh": "Skill"`, `"spec-read-marker.sh": "Read"`,
  `"spec-sync-nudge.sh": "Edit|Write|MultiEdit"`(settings.json 실측 반영).
- `_HOOK_SHELLS` 추가: `"spec-skill-gate.sh": "sh"`, `"spec-read-marker.sh": "sh"`,
  `"spec-sync-nudge.sh": "bash"`(settings.json 실측 반영).

**Step 2.2 — `hooks_json()` 다중이벤트 + DATA env-prefix.**
- 현행 `PreToolUse` 하드코딩을 이벤트-그룹 빌드로 교체(결정론 순서 = `HOOK_ADOPT` 순회 →
  PreToolUse 3(git-state·artifact·spec-skill-gate) 먼저, PostToolUse 2(spec-read-marker·
  spec-sync-nudge) 뒤; dict 삽입 순서 결정론):
  ```python
  def hooks_json() -> dict:
      events: dict[str, list] = {}
      for name in HOOK_ADOPT:
          prefix = 'AGENT_HOME="${CLAUDE_PLUGIN_DATA}" ' if name in _HOOK_DATA_HOME else ''
          command = f'{prefix}{_HOOK_SHELLS[name]} "${{CLAUDE_PLUGIN_ROOT}}/hooks/{name}"'
          events.setdefault(_HOOK_EVENTS[name], []).append({
              "matcher": _HOOK_MATCHERS[name],
              "hooks": [{"type": "command", "command": command}],
          })
      return {"hooks": events}
  ```
- 결과 command 예: `AGENT_HOME="${CLAUDE_PLUGIN_DATA}" sh "${CLAUDE_PLUGIN_ROOT}/hooks/spec-skill-gate.sh"`.
  기존 2종은 prefix 없이 종전과 동일 문자열(회귀 없음). docstring(L85-91) 을 다중이벤트+DATA
  재기준으로 갱신.

**Step 2.3 — `sync()` 에 utilities 동반 복사.**
- 기존 hooks 복사 블록 뒤에 추가:
  ```python
  plugin_utils = PLUGIN_ROOT / "utilities"
  if plugin_utils.exists() or plugin_utils.is_symlink():
      shutil.rmtree(plugin_utils)
  plugin_utils.mkdir(parents=True)
  for name in UTIL_BUNDLE:
      shutil.copy2(UTILITIES_SOURCE / name, plugin_utils / name)
  ```
- `sync()` 진입 가드에 `UTILITIES_SOURCE / "agent-home.sh"` 존재 확인 추가(없으면 SystemExit).
- 3종 hook `.sh` 는 `for name in HOOK_ADOPT: copy2` 가 이미 커버(추가 코드 불요, `copy2` 로
  exec bit 보존).

**Step 2.4 — `check()` 에 utilities 커버.**
- hooks per-file 블록(L196-208) 다음에 utilities 미러 블록 추가: `UTIL_BUNDLE` 각 파일
  byte-compare(`read_bytes`) + `PLUGIN_ROOT/"utilities"` excess-file 탐지(예상집합 밖 파일 →
  stale). 3종 hook 은 기존 hooks per-file 루프(`for name in HOOK_ADOPT`)와 excess-file 탐지가
  자동 커버 — HOOK_ADOPT 확장만으로 반영됨(추가 코드 불요). hooks.json byte-compare(L163-167)는
  새 `hooks_json()` 산출을 자동 반영.

**Step 2.5 — 주석·docstring 동기화.**
- L38-40 `HOOK_ADOPT` 주석: "spec-pipeline trio deferred" → "spec-pipeline trio adopted (cycle 3,
  `${CLAUDE_PLUGIN_DATA}` rebasing via hooks.json AGENT_HOME env-prefix; see plan
  2026-07-13_harness-installer-hooks)".
- 모듈 docstring(L14-16): "skills + agents + hooks(2)" → "skills + agents + hooks(5: 2 self-
  contained + 3 spec-pipeline DATA-rebased) + utilities/agent-home.sh".

- **Done when**: `python3 adapters/claude/bin/sync-native-plugin.py` 가
  `hooks/{5 .sh + hooks.json}` + `utilities/agent-home.sh` 를 materialize; hooks.json 이
  `PreToolUse`(3) + `PostToolUse`(2)를 담고 spec 3종 command 에 `AGENT_HOME="${CLAUDE_PLUGIN_DATA}"`
  prefix + `${CLAUDE_PLUGIN_ROOT}/hooks/<name>` 포함; 재실행 byte-identical(idempotent);
  `--check` clean tree exit 0, 생성물 touch 후 exit 1; `adapters/claude/plugin-marketplace/`
  밖 write 0; **canonical `hooks/*.sh` 무수정**(git diff 에 hooks/ 소스 없음).

---

### Phase 3 — 대응 동기화 (P1)

**Step 3.1 — `_internal/hooks_inventory.md` defer→adopt.**
- 사이클 2 인벤토리의 spec 파이프 3종 판정을 defer→**채택(cycle 3)**으로 갱신, 재기준 방식
  (hooks.json AGENT_HOME env-prefix = `${CLAUDE_PLUGIN_DATA}`, canonical 무수정, utilities 번들)
  한 줄 근거 추가. 위치 = `.agent_reports/spec/harness-installer/_internal/hooks_inventory.md`
  (존재 확인 후 편집; 비-guard 경로).

**Step 3.2 — PRD OPEN 갱신 필요 기록(편집 X).**
- INST-OPEN-1 은 사이클 2 에서 이미 "확정(채택 2 / defer 3 / 제외)". 이번 사이클로 defer 3 이
  채택으로 이동 → 문구를 "채택 5 / 제외 나머지"로 좁힐 수 있음. **prd.md 편집은 이 스테이지
  금지** — code-report 가 main orchestrator 의 `autopilot-spec update` 로 갱신할지 기록만.
  pipeline_state.yaml 의 INST-D-6/dev 이월 항목도 동일(main 갱신 대기).

- **Done when**: hooks_inventory.md 가 채택 상태를 반영; code-report 핸드오프에 PRD/state 갱신
  포인터 기록.

---

### Phase 4 — code-test 시나리오 명세 (실행은 code-test 스테이지 몫 — 이 Phase 는 계획만)

아래는 code-test 가 **단일 self-contained 스크립트 + mktemp + real-home 결정론 trap**(사이클 2
격리 계약 계승) 하에 작성할 검증 항목. 이 스테이지에서 직접 실행하지 않는다.

**T0. 정적·생성기 기본(사이클 2 계약 계승).**
- `py_compile adapters/claude/bin/sync-native-plugin.py` clean.
- `sync-native-plugin.py --check`: clean tree exit 0 → 생성물 파일 touch 후 exit 1 → regen 후
  exit 0. idempotent 재실행 byte-identical.
- 생성 hooks.json 구조 assert: `hooks.PreToolUse` 에 git-state-guard·artifact-guard·spec-skill-gate
  3개(matcher Skill 포함), `hooks.PostToolUse` 에 spec-read-marker(Read)·spec-sync-nudge
  (Edit\|Write\|MultiEdit) 2개. spec 3종 command 에 리터럴 `AGENT_HOME="${CLAUDE_PLUGIN_DATA}"`
  와 `${CLAUDE_PLUGIN_ROOT}/hooks/<name>` 동시 포함. 기존 2종 command 는 prefix 없이 종전과 동일.
- plugin 트리에 `utilities/agent-home.sh` 존재 + exec bit; `hooks/` 에 5개 `.sh`.
- **⚠️ 기존 사이클 2 테스트가 hooks.json 을 `PreToolUse` 단일로 assert 한다면 갱신 필요**(shape
  이 superset 으로 확장 — 제품 회귀 아님, 테스트 기대치 갱신).

**T1. marker 재기준(핵심) — 실 plugin 설치 없이 env-prefix 경로 재현.**
- mktemp `DATA=$(mktemp -d)`. `printf '<PostToolUse Read JSON, file_path=<fixture>/.agent_reports/spec/prd.md, session_id=S>' | AGENT_HOME="$DATA" sh <plugin>/hooks/spec-read-marker.sh`
  → assert 마커가 `$DATA/.spec-grounding/S__<key>` 에 생성, **real `$HOME` 하위엔 무생성**.
- 이어 `printf '<PreToolUse Skill JSON, skill=autopilot-code, session_id=S>' | (cd <fixture> && AGENT_HOME="$DATA" sh <plugin>/hooks/spec-skill-gate.sh)` → exit 0 / deny JSON 없음(마커 존재 → 통과).
- 마커 삭제 후 재실행 → `permissionDecision:"deny"` JSON emit(마커 부재 → 게이트 작동).
- prd.md `touch`(mtime 상향) 후 재실행 → 역방향 drift deny(마커 mtime < prd mtime).

**T2. 이중발화 안전성(필수 섹션).**
- `A=$(mktemp -d)`(settings 경로 모사), `B=$(mktemp -d)`(plugin DATA 모사). 동일 세션 JSON 으로
  read-marker 를 `AGENT_HOME=$A` 와 `AGENT_HOME=$B` 로 각각 1회 → 마커가 `$A/.spec-grounding`
  와 `$B/.spec-grounding` 에 **각각** 생성(상호 write 없음, 디렉토리 분리 검증).
- gate 를 `AGENT_HOME=$A`·`AGENT_HOME=$B` 각각 → 둘 다 각자 마커로 통과(멱등).
- 비대칭 케이스: `$B` 마커만 삭제 후 `AGENT_HOME=$B` gate → deny(보수적 재-Read 강제).
  Claude 병합 규칙상 어느 한 PreToolUse deny 가 tool 을 막음 → mid-session plugin 설치 시
  1회 재-Read 강제되는 **정상 fail-safe** 임을 문서화(부작용 없음: 검사 read-only, 재-Read 저렴).
- gate 는 stat+cat 만 → **2회 실행 멱등**(side-effect 0) assert.

**T3. fail-open·회귀.**
- env-prefix 없이(settings.json 경로 모사) `AGENT_HOME` unset + `HOME=<tmp>` 로 hook 실행 →
  agent-home.sh precedence 대로 fallback resolve(`$HOME/agent_setting` 부재면 `$HOME/.claude`),
  마커가 fallback 하위에 생성 — **비-plugin 경로 회귀 0**.
- `AGENT_HOME=""`(빈 DATA degrade) → `:-` fallback 로 agent-home.sh(번들본) resolve, no crash.
- canonical `hooks/*.sh` git diff 비교 → **무수정** assert(이번 사이클 불변식).

**T4. self-contained.**
- 생성 hooks.json·번들 스크립트의 모든 경로가 `${CLAUDE_PLUGIN_ROOT}`/`${CLAUDE_PLUGIN_DATA}`
  기준 또는 PLUGIN_ROOT 내부(`../utilities` = 루트 내부)임을 assert — PLUGIN_ROOT 밖 `../` escape 0.

**T5. real-home 결정론 가드(사이클 2 인시던트 계승, 필수).**
- 스크립트 최상단(HOME 재할당 이전) real `~/.claude/settings.json`·`~/.claude/plugins`(재귀)·
  `~/.codex/config.toml`·`~/.config/opencode/opencode.json` sha256 캡처, `trap ... EXIT` 로
  종료 시 byte-unchanged 재확인. 모든 write 는 mktemp/`adapters/claude/plugin-marketplace/`
  하위로 한정.

**T6. 통합 스모크.**
- `build-manifest.py --check` up-to-date; `harness verify claude --json` 의 `claude.sync-native-plugin`
  check 가 새 생성물에 대해 exit 0(생성기-SoT 바인딩 유지).

- **Done when(code-test)**: T0~T6 전부 PASS, real-home trap 유지, mktemp/marketplace 서브트리
  밖 write 0.

---

## Risks

- **`--agent-home` 오적용**: `--agent-home` 는 CLI-arg 모드 전용(stdin 미독)이라 실 호출 경로에서
  비가용 — env-prefix 로 대체(Phase 1 결정 1). code-execute 가 실수로 `--agent-home` 를 hooks.json
  command 에 얹으면 stdin skill/file 미제공으로 `exit 64` → hook 오작동. **반드시 env-prefix**.
- **hooks.json shape 확장 → 기존 테스트 깨짐(제품 회귀 아님)**: 사이클 2 테스트가 `PreToolUse`
  단일을 기대하면 superset 확장으로 실패할 수 있음 — 테스트 기대치 갱신(T0 note).
- **canonical 무수정 불변식 위반 유혹**: 재기준을 "hook 본체에서 CLAUDE_PLUGIN_DATA 직접 읽게"
  고치고 싶을 수 있으나 **금지**(out-of-scope). env-prefix 가 무수정으로 충분. 무수정 불가 벽을
  만나면 STOP+보고.
- **`${CLAUDE_PLUGIN_DATA}` 미치환/empty**: 정상 plugin 실행에선 auto-create 로 항상 값 존재
  (doc 검증). 만약 empty 면 `:-` fallback → degrade(no crash) — fail-open 유지.
- **determinism 순서**: `hooks_json()` 이 dict 삽입 순서에 의존 → `HOOK_ADOPT` 리스트 순회로
  결정론 확보. `--check` byte-compare 가 순서 흔들림을 즉시 stale 로 잡음.
- **real-home 오염(사이클 1 인시던트 클래스)**: T5 격리 계약(단일 스크립트 env·mktemp·trap)으로
  구조적 차단 — 이번 사이클 최우선 안전 제약.

## PRD OPEN-section status (code-report 용 — 이 스테이지는 prd.md 편집 안 함)

- **INST-OPEN-1**: 사이클 2 "확정(채택 2 / defer 3 / 제외)". 이번 사이클로 defer 3 → 채택 이동
  → **"채택 5(git-state·artifact + spec 파이프 3종 DATA-rebased) / 제외 나머지"**로 좁힘 가능.
  실제 prd 편집은 main orchestrator `autopilot-spec update` 몫.
- **INST-D-6 / pipeline_state.yaml `dev:` 이월 항목**: "spec 파이프 hook 3종 PLUGIN_DATA 재기준"
  이 이번 사이클로 **완결** → decisions_locked/이월 문구 갱신 필요(main 갱신 대기).
- **INST-OPEN-4**(OpenCode 복수형): OPEN 유지 — 미착수.

## Verification (orientation only — code-test 가 실제 격리 스크립트 작성)

핵심 대표 검증(§Phase 4 상세):
- `sync-native-plugin.py --check` → clean exit 0, 생성물 편집 후 exit 1.
- 생성물: `hooks/{5 .sh + hooks.json(PreToolUse 3 / PostToolUse 2)}` + `utilities/agent-home.sh`;
  spec 3종 command 에 `AGENT_HOME="${CLAUDE_PLUGIN_DATA}"` prefix.
- marker 재기준: `AGENT_HOME=<mktemp>` stdin 호출 → 마커가 그 dir 하위, real HOME 무생성.
- 이중발화: `$A`/`$B` 마커 디렉토리 분리, 멱등, deny-wins fail-safe.
- fail-open: env-prefix 없는 settings 경로 회귀 0; canonical hooks git-diff 무수정.
- **안전 불변식(상시)**: real `~/.claude`·`~/.claude/plugins`·`~/.codex`·`~/.config/opencode`
  byte-unchanged.
