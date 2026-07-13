# Phase 1 — hook 3종 재확인 + wrapper 방식 판정 (코드 무변경)

> code-execute 스테이지가 plan.md Phase 1 결정을 코드 재검증한 기록. 세 hook 모두 실측 결과
> plan 의 결정과 **일치** — 반증 없음, 코드 수정 없이 Phase 2 진입.

## 1.1 `spec-skill-gate.sh` — 마커 읽기 전용 + CLI/stdin 분기

- `check_gate()`(L34-63): `.spec-grounding/${sid}__${key}` 를 `stat`(L49, prd mtime)·`cat`(L56,
  마커 mtime)으로 **읽기만** — write 0. `AGENT_HOME`(L10)은 마커 base dir 산출에만 쓰인다.
- CLI/stdin 분기(L70 `if [ "$#" -gt 0 ]`): args 있으면 CLI 모드 진입 — `--skill`/`--capability`
  필수(L107 `[ -n "$skill" ] || { ... exit 64; }`). args 없으면(L118~) stdin 에서 hook JSON 을
  읽어 `skill`/`session_id` 를 grep 파싱.
- 실측 일치 — plan 인용 라인(L34-63 read-only, L70 분기, L107 필수)이 코드와 정확히 대응.

## 1.2 `spec-read-marker.sh` — 마커 쓰기 + `--file` 필수

- `mark_read()`(L18-40): `mkdir -p "$AGENT_HOME/.spec-grounding"`(L38) 후
  `printf '%s\n' "$mtime" > "$AGENT_HOME/.spec-grounding/${sid}__${key}"`(L39) — **쓰기**.
- CLI 모드 `--file` 필수(L73 `[ -n "$fp" ] || { ... exit 64; }`), stdin 모드는 `file_path` 를
  hook JSON 에서 grep 파싱(L81).
- 실측 일치 — plan 인용 라인(L38-39 write, L73 필수)이 코드와 정확히 대응.

## 1.3 `spec-sync-nudge.sh` — read-only·AGENT_HOME 로직 미사용

- `AGENT_HOME` 은 L29 에서 설정, L30 에서 `export` — 그러나 로직 본체(inline `NUDGE_PY`,
  L46-170)는 **`AGENT_HOME` 을 전혀 참조하지 않는다**(grep 결과 0건). spec-backed 판정은
  `find_spec_dir()`(L80-88)가 **cwd(`file_path`) 기준 상향 탐색**으로 `.agent_reports|
  .claude_reports/spec/pipeline_state.yaml` 을 찾는 방식 — env 미사용.
- 파일 write 0 — 스크립트 자체 주석(L17) "Read-only 불변식: DB·파일 write 0. additionalContext
  만 emit". 확인: 코드 전체에 `>` 리다이렉트(append/overwrite) 없음, `print()`/`json.dumps()` 만
  stdout 에 emit.
- 태스크 요약("AGENT_HOME 은 python 헬퍼 실행 경로 해석에 쓴다")은 **부정확** 확정 — python 은
  외부 파일이 아니라 `python3 -c "$NUDGE_PY"`(L188, L194) inline 문자열 실행이라 경로 해석
  자체가 발생하지 않는다.

## 1.4 `--agent-home` 기각 — env-prefix 채택

- `--agent-home` 플래그는 세 hook 모두 존재하나(gate L91-95, marker L57-61, nudge 는 미보유 —
  실측 정정: `spec-sync-nudge.sh` 는 CLI 모드에 `--agent-home` 옵션이 **없다**, `AGENT_HOME` env
  export 만 사용) **CLI-arg 모드 전용**이다. Claude 가 실제로 hook 을 부르는 경로는 항상
  args 0 + stdin JSON 파이프(hooks.json command 문자열은 고정, args 를 안 붙임) → gate/marker
  가 `--agent-home` 를 command 에 얹어도 args 가 생겨 CLI 분기(L70/L42)로 falling, 그런데
  `--skill`/`--file` 은 여전히 미제공 → `exit 64`.
- ∴ **`--agent-home` 는 실 stdin 호출 경로에서 비가용** — plan 반증 없음, env-prefix 채택 확정.
  `AGENT_HOME="${CLAUDE_PLUGIN_DATA}" <shell> "${CLAUDE_PLUGIN_ROOT}/hooks/<name>"` 는 args 0
  유지 → stdin 모드 정상 진입, `AGENT_HOME` env 만 override.
- **정정 사항 1건**: `spec-sync-nudge.sh` 는 애초 `--agent-home` CLI 플래그 자체가 없다(gate·
  marker 는 있음). plan 은 세 hook 모두 `--agent-home` 보유를 전제했으나, nudge 는 무관하게
  env-prefix 만으로 우회되므로 **Phase 2 결정에 영향 없음**(env-prefix 채택 결론 불변).

## 1.5 유일 외부참조 = `../utilities/agent-home.sh`

- `grep -rn "agent-home.sh\|SCRIPT_DIR\|HOOK_DIR" hooks/spec-skill-gate.sh hooks/spec-read-marker.sh hooks/spec-sync-nudge.sh`
  결과: 세 hook 모두 `$SCRIPT_DIR/../utilities/agent-home.sh`(gate L10, marker L8) 또는
  `$HOOK_DIR/../utilities/agent-home.sh`(nudge L29) 단 1회씩 참조. 다른 외부 스크립트 참조 없음
  (nudge 의 python 은 inline 문자열이라 파일 참조 아님).
- `utilities/agent-home.sh` 실존 확인(`ls utilities/agent-home.sh` → 존재). plugin 트리에서
  `$SCRIPT_DIR = ${CLAUDE_PLUGIN_ROOT}/hooks/` 이므로 `../utilities` = `${CLAUDE_PLUGIN_ROOT}/utilities`
  — PLUGIN_ROOT 내부, `../` 이스케이프 아님. **utilities 번들 필요 확정**.

## 1.6 `${CLAUDE_PLUGIN_DATA}` — 왜 DATA 인가

- plan §Runtime-currentness 검증(2026-07-13, `code.claude.com/docs/en/plugins-reference`)이 이미
  인용 확보: command 변수 치환에 `${CLAUDE_PLUGIN_DATA}` 포함, "persistent directory … survives
  updates … created automatically the first time this variable is referenced"; 대조군
  `${CLAUDE_PLUGIN_ROOT}` 는 "version-ephemeral … do not write state here".
- 한 줄 근거: 세션 grounding 마커는 설치 생존 상태이므로, 공식 문서가 상태 저장을 명시적으로
  금지한 ROOT(cache) 대신 상태 저장용으로 지정된 DATA 에 둔다.

## 종합 판정

세 결정(env-prefix 채택·`--agent-home` 기각 / utilities 번들 / spec-sync-nudge uniformity
defensive-only) 모두 코드로 **재확인 — 반증 없음**. 정정 1건(spec-sync-nudge 는 애초
`--agent-home` 플래그 미보유)은 결론에 영향 없어 Phase 2 진입.
