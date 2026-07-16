# SD-56 — completion 통과 marker 배선 실행 로그

## 무엇을 왜

`capability-route.py complete`가 쓰는 completion marker를 어떤 파이프라인도 호출하지 않아
repo 전역 marker 0건이었다(carryover §1 실측). 계획 §3대로 canonical marker 경로 +
재수확 이력 보존 + `--start` 선행 marker gate를 배선했다.

## 무엇을 어떻게 바꿨나

### `utilities/dispatch_contract.py`

- 신규 검증형 `resolve_agent_home()` — `adapters/claude/bin/dispatch-headless.py:546-558`의
  `core/CORE.md` 검증 선호 순서(`AGENT_HOME` → `CLAUDE_HOME` → `~/agent_setting` →
  `~/.claude` → 모듈 루트)를 그대로 옮겼다. **`os.environ.get("AGENT_HOME", ROOT)` 패턴을
  쓰지 않았다** — `ROOT`가 worktree라 registry가 갈리는 SD-14b② 패턴 재발 방지가 목적
  (plan-check B4).
- 신규 `completion_marker_gate(route_file, route_node, action, agent_home)` — `action != "start"`
  또는 `route_file` 없음 또는 `broker_contract_version != 2`면 미적용(v1/record-미결합
  소급 강제 금지). `depends_on` 전 노드의 canonical marker 존재 + `route_id`/`route_hash`
  일치를 검사, 부재 시 `DispatchContractError("completion-marker-missing", ...)`.
  **`agent_home`은 명시 인자** — 함수 내부에서 env를 재독하지 않는다(writer/reader가 같은
  루트를 쓴다는 보장이 시그니처에 드러나야 한다는 §3.2.1 요구).

### `utilities/capability-route.py`

- `from dispatch_contract import resolve_agent_home` (import를 위해 `sys.path.insert(0, ROOT/"utilities")`
  추가 — importlib.spec_from_file_location으로 로드되는 테스트 컨텍스트에서도 sibling
  모듈을 찾도록).
- 신규 `completion_dir(route_id)`, `atomic_write(path, payload)`(tmp+fsync+`os.replace`,
  `dispatch-broker.py`의 `atomic_json` 패턴과 동형), `write_completion_marker(route, node,
  node_id, evidence)`.
- 재수확 알고리즘: canonical(`<route_id>/<node_id>.json`, 원자적 교체) + 이력
  (`<node_id>.<seq>.json`, `write_once` 불변) 역할 분리. 동일 evidence sha256이면 no-op,
  변경 시에만 새 이력 파일 생성. `write_once` 충돌(타임스탬프 차이로 인한) 시 seq+1 재시도.
- `main`의 `complete` 분기를 `write_completion_marker` 호출로 교체. `--output`은 유지
  (override용), 기존 `<evidence>.completion.json` 기본 경로는 **제거**(carryover §1
  실측대로 소비자 0이므로 안전).

### 어댑터 3종 (`adapters/{claude,codex,opencode}/bin/dispatch-headless.py`)

- `dispatch_contract` import에 `completion_marker_gate` 추가.
- `action = ...` 계산 직후 `args.action = action` + `args.agent_home = resolve_agent_home()`
  세팅(gate가 `validate_route_record` 안, 기존 `agent_home` 계산 지점보다 앞이라 scope에
  없었던 문제 — plan §3.3 "gate 앞으로 끌어올려야" 반영). 이후 원래 `agent_home = resolve_agent_home()`
  호출부는 `args.agent_home` 재사용으로 정리(중복 호출 제거).
- `validate_route_record`의 `worker-route-guard.py validate` 성공 직후, 함수의 최종
  `return 0` 직전에 gate 호출 삽입:
  ```python
  try:
      completion_marker_gate(args.route_file, args.route_node, args.action, args.agent_home)
  except DispatchContractError as e:
      return fail(e.reason, 65, detail=e.detail, child_spawned="0")
  ```
  이 위치는 `shutil.which(...)`·registry row 기록·broker ensure **전부보다 앞**이라
  spawn 0건 + row 0건이 구조적으로 보장된다(§3.3 순서 근거, fixture ⑦에서 실측 확인).

### `utilities/dispatch-node.py`

- `resource-runner` 조기 return 앞에 `completion_marker=<canonical path>` 관측 라인 1줄
  추가(acceptance 요구 아님, §3.4 — 저위험이라 포함).

### 문서 3부

- `adapters/claude/skills/autopilot-code/references/dev-pipeline.md`(원본)에 "After
  harvest..." 문단 뒤 conductor `complete` 의무 문단 추가.
- `cp`로 `skills/autopilot-code/references/dev-pipeline.md`와
  `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-code/references/dev-pipeline.md`에
  동기화. `diff -r skills/autopilot-code adapters/claude/skills/autopilot-code` → 차이 없음
  확인.

## 신규 `utilities/dispatch_completion_marker.test.py`

fixture ⑥⑦⑧⑨ 전부 구현. v2 record는 이 시점(SD-55 배선 전)엔 compile_route가 항상 v1을
생성했으므로 손수 `as_v2()`(broker_instance strip + `broker_contract_version=2` + rehash)로
구성 — SD-55가 나중에 compile_route 기본값을 v2로 바꾼 뒤에도 이 헬퍼는 그대로 유효했다
(gate는 필드 값만 읽으므로).

- ⑥ `test_complete_writes_canonical_marker` — canonical 경로 존재 + 6필드
  (route_id/route_hash/registry_digest/node_id/completion_gate/evidence.sha256) 일치.
- ⑦ `test_start_without_dependency_marker_fails_closed` — 3어댑터 parametrize.
  **eligibility 인자(`--parent-harness/--parent-transport/--parent-sandbox/--nested-eligibility
  supported/--eligibility-source/--launch-authority conductor`) 포함 필수**(plan-check M3
  — 없으면 `validate_nested_eligibility`가 먼저 exit 69로 막아 `completion-marker-missing`에
  도달 못 함). marker 없을 때 `reason=completion-marker-missing`+`child_spawned=0`+jobs.log
  row 0건 단언 → `plan` marker 작성 → 재실행 시 그 reason이 **아님**만 단언(다른 사유로
  실패해도 무방 — 실제 `claude`/`codex`/`opencode` 바이너리가 없어 이후 다른 gate에서 막힘).
- ⑧ `test_marker_absence_is_not_a_failure` — (a) v1 record(손수 `as_v1()`로 고정) --start,
  marker 없어도 gate 미적용. (b) record 미결합 --start, gate 미적용. (c) 정적 스캔:
  `utilities/`·`adapters/*/bin/`·`tools/fleet/`에서 `completion_marker_gate` 헬퍼 자체와
  어댑터의 `fail(e.reason, ...)` 중계 지점 외에는 `"completion-marker-missing"` 문자열이
  등장하지 않음을 확인 — "marker 부재는 무주장" 원칙의 정적 수호자.
- ⑨ `test_reharvest_preserves_history_and_latest_is_authoritative` — 동일 evidence 재실행
  no-op(이력 파일 안 늘어남), evidence 변경 시 새 이력 + 기존 이력 파일 내용 불변 + canonical
  이 최신을 가리킴 + sequence 증가.

## 실행 커맨드 및 결과

```
$ unset AGENT_SESSION_ROLE AGENT_DISPATCH_CHILD AGENT_DISPATCH_BROKER_INSTANCE AGENT_DISPATCH_BROKER_ROOT AGENT_DISPATCH_JOBS
$ python3 utilities/dispatch_completion_marker.test.py -v
# Ran 4 tests ... OK
$ python3 utilities/capability_route.test.py -v
# Ran 10 tests ... OK (SD-56 시점, SD-55 이전)
$ python3 utilities/dispatch_contract.test.py -v
# Ran 5 tests ... OK
```

## 투영 census 후속 (§7 리스크 실현 — v12와 동일 패턴)

`tools/check-adaptation-boundary.sh`의 `check_claude_utility_projection`이 `utilities/*`의
모든 파일이 `adapters/claude/utilities/`에 대응 엔트리(symlink)를 가질 것을 요구한다.
신규 `dispatch_completion_marker.test.py`를 빠뜨려 최초 실행에서 FAIL — 다른
`dispatch_*.test.py`와 동일하게 `adapters/claude/utilities/dispatch_completion_marker.test.py
-> ../../../utilities/dispatch_completion_marker.test.py` symlink를 만들고, `tools/check-adaptation-boundary.sh`의
`UTILITY_DEFERRED` 목록(2곳, OpenCode/Claude 섹션 각각) 옆에 파일명을 추가해 해소했다
(03 로그의 전체 회귀 절에서 최종 확인).
