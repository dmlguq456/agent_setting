# test log 05 — F-29 불변식 + 스크롤 회귀 (독립 프로브)

## 1. 스크롤 회귀 = 0 (A2-6 / A5-1·A5-2)

```bash
python3 -m unittest tools.fleet.tests.test_scroll_regression.BaseModeScrollTest.test_arrow_keys_still_scroll_in_base_mode -v
```

```
Ran 1 test — OK
```

태스크가 명시 요구한 테스트명이 **실재하고 통과**. 스위트 전체 10건 OK (`BaseModeScrollTest` 6 + `ScrollIsolationTest` 4).

**판정: PASS.** 범위는 plan §7.1이 못박은 대로 **base 모드 한정** — 아무것도 선택하지 않은 사용자(=kill을 쓰지 않는 전 사용자)의 스크롤 100% 불변. 선택 모드에서 방향키가 커서로 가는 것은 prd.md:279("선택 모드 진입과 동일 상태")가 **요구한** 동작이며 회귀가 아니다.

## 2. F-29 불변식 — 독립 프로브 (`/tmp/v9_f29_probe.py`)

```
BackboneInviolable.test_subagent_read_failure_does_not_drop_the_session ... ok
BackboneInviolable.test_missing_agent_column_degrades_to_none_not_crash .. ok
BackboneInviolable.test_no_children_yields_empty_list_not_none ........... ok
PulsePurity.test_adding_subagents_does_not_change_any_pulse_count ........ ok
RowOmission.test_subagents_none_emits_no_subrow .......................... ok
RowOmission.test_subagents_empty_emits_no_subrow ......................... ok

Ran 6 tests — OK
```

### (a) enrichment 전용 — 세션 존재 판정 불가침 (prd.md:291)

`_child_sessions`가 예외를 던지도록 강제 주입해도 `enrich`가 raise하지 않고 세션 행이 생존:

```python
with mock.patch.object(oc, "_child_sessions", side_effect=Exception("boom")):
    oc.enrich(s)        # 예외 전파 없음
assert s is not None    # 세션은 프로세스 백본이 소유 — enrichment 실패와 무관
```

**PASS (A3-1).** 서브에이전트는 `Session`의 **속성**일 뿐이며 세션 목록 구성에 관여하지 않는다.

### (b) 결손 어휘의 정직성 — `None` vs `[]`

| 상황 | 반환 | 의미 |
|---|---|---|
| `agent` 컬럼 부재 (구버전 DB) | `None` | 정직한 결손 — 확인 불가 |
| 쿼리 성공, 자식 없음 | `[]` | 확인됨 — 없음 |

**PASS** — tolerant degrade(F-3 동형). 구버전 스키마가 크래시를 내지 않고 조용히 결손 처리.

### (c) pulse 카운트 혼입 0 (prd.md:293) ★★

동일 세션 집합에 서브에이전트만 10개 주입 후 pulse 재측정:

```
pulse with 0 subagents: ('1', '1')  |  with 10 subagents: ('1', '1')
```

**PASS (A3-3).** 구조적 근거 — `render.py:1814`:

```python
n_work = sum(1 for s in live_sessions if s.liveness == "working") + \
         sum(1 for j in group_jobs if j.liveness == "working")
```

카운트는 `live_sessions`/`group_jobs`만 순회한다. 서브에이전트는 어느 쪽 컬렉션에도 들어가지 않으므로 혼입이 **구조적으로 불가능**(우연한 상태가 아님).

### (d) 소스 부재/파싱 실패 → 서브 행 생략 (prd.md:294)

`subagents=None`과 `subagents=[]` 양쪽에서 렌더 출력에 `_ICON_SUBAGENT` 미등장 → **회귀 없음 원칙** 충족. 라이브 `--once` 렌더에서도 동일 확인(test log 02 §4).

**PASS (A3-4).**

### (e) zero-injection (read-only) 유지 (prd.md:294)

신규 코드의 I/O 전수 검사:

```bash
git diff -- tools/fleet/collectors/claude.py   | grep '^+' | grep -E "open\(|write|execute\("
# → with open(path, "rb") as f:          ← 읽기 전용 바이너리
git diff -- tools/fleet/collectors/opencode.py | grep '^+' | grep -E "open\(|write|execute\("
# → rows = con.execute("SELECT id, agent, time_updated FROM session WHERE parent_id=? ...")
```

- Claude: `open(path, "rb")` — 읽기 전용, 기존 tail 경로 재사용.
- OpenCode: `SELECT`만. 커넥션은 `sqlite3.connect("file:%s?mode=ro" % db, uri=True)` (opencode.py:144) — **URI 레벨 read-only**.
- `INSERT`/`UPDATE`/`DELETE`/`commit` **0건**.

**PASS (A3-4).** 하네스 원본 transcript·DB 무주입 불변.

## 3. 🟡 관찰 — OpenCode 서브에이전트는 영구 `active=True`

`collectors/opencode.py::_child_sessions`:

```python
out.append(SubAgent(agent_type=agent or None, active=True, ...))
```

독스트링이 이유를 밝힌다:

> *"No completion signal exists in this schema (unlike claude's tool_use/tool_result pairing) — every row found here is reported active=True; that is not a guess, it is the absence of evidence to the contrary."*

**평가**: `done`을 날조하지 않는다는 점에서 prd.md:292의 "추측 표시 금지"에 정합하며, 방향은 정직하다. 다만 **반대 방향의 단언은 남는다** — 증거 부재를 `active=True`로 표현하는 것은 "활성"이라는 적극적 주장이다. 실질 결과:

- prd.md:293의 *"완료분은 기본 숨김, 활성만 표시"* 가 OpenCode 소스에 대해서는 **달성 불가** — 종료된 서브에이전트가 무기한 활성으로 표시된다.
- `⚡N`(현 `🔬N`) 배지가 OpenCode 세션에서 단조 증가할 수 있다.

**심각도: 🟡 낮음 (설계상 인지됨, 문서화됨).** Claude 경로는 `tool_use`↔`tool_result` 짝짓기로 완료를 정확히 유도하므로 영향은 OpenCode 한정. 스키마에 완료 신호가 없다는 것이 사실이라면 이는 소스의 한계이지 구현 결함이 아니다. 다만 **`time_updated` 기반 staleness 유도**(예: N분 무갱신 → 비활성)가 가능한 후속 개선 여지로 남으며, 현재 `time_updated`를 SELECT하고도 `started_at`으로만 쓰고 활성 판정에 쓰지 않는다. **후속 사이클 권고 사항**으로 기록.
