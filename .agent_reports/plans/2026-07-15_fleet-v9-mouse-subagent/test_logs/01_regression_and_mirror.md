# test log 01 — 전체 회귀 + 미러 parity

- 스테이지: `code-test` (depth 2, 독립 검증자) · 2026-07-15
- 워크트리: `/home/Uihyeop/agent_setting-wt/fleet-v9-mouse-subagent` (dirty, uncommitted)
- 소스는 본 스테이지에 **read-only** — `tools/fleet/**`·`adapters/claude/tools/fleet/**` 무수정 확인

## 1. 정본 스위트 — `tools/fleet/tests`

```bash
python3 -m unittest discover -s tools/fleet/tests -q
```

```
Ran 468 tests in 16.956s

OK
```

**결과: PASS** — execute 주장(468 OK)과 정확히 일치. 베이스라인 416 → 468.

### 신규 4스위트 개별 실측

```bash
for m in test_f27_mouse test_f29_subagents test_d3_stage_zone test_scroll_regression \
         test_f27_control test_mirror_parity; do
  python3 -m unittest tools.fleet.tests.$m
done
```

| 스위트 | 테스트 수 | 결과 |
|---|---|---|
| `test_f27_mouse` | 21 | OK |
| `test_f29_subagents` | 15 | OK |
| `test_d3_stage_zone` | 6 | OK |
| `test_scroll_regression` | 10 | OK |
| `test_f27_control` (기존, 무변경) | 82 | OK |
| `test_mirror_parity` | 1 | OK |

**신규 합계 = 21+15+6+10 = 52.** 416 + 52 = **468** — 산술 일치, 주장 검증됨.

## 2. 미러 parity — 바이트 일치

```bash
diff -r --exclude='__pycache__' tools/fleet adapters/claude/tools/fleet
```

```
(출력 없음 — exit 0)
PARITY: byte-identical, no drift
```

**결과: PASS** — 변경 파일 전체(`render.py`·`model.py`·`collectors/{claude,opencode}.py`) + 신규 테스트 4종 모두 드리프트 0.

### 변경 표면 실측

```bash
git diff --stat -- tools/fleet/ adapters/claude/tools/fleet/
```

```
 adapters/claude/tools/fleet/collectors/claude.py   |  96 ++++++
 adapters/claude/tools/fleet/collectors/opencode.py |  35 ++
 adapters/claude/tools/fleet/model.py               |  20 ++
 adapters/claude/tools/fleet/render.py              | 370 ++++++++++++++++++---
 tools/fleet/collectors/claude.py                   |  96 ++++++
 tools/fleet/collectors/opencode.py                 |  35 ++
 tools/fleet/model.py                               |  20 ++
 tools/fleet/render.py                              | 370 ++++++++++++++++++---
 8 files changed, 954 insertions(+), 88 deletions(-)
```

execute가 보고한 변경 파일 집합과 일치 — 미보고 파일 변경 **없음**.

## 3. 미러 자체 스위트 실행 — 사전 존재 결함 3건 (회귀 아님)

```bash
python3 -m unittest discover -s adapters/claude/tools/fleet/tests -q
```

```
Ran 468 tests in 11.227s
FAILED (errors=3, skipped=15)
```

3건 전부 동일 원인:

```
ERROR: test_lifecycle_* (test_token_budget.AccountingTest)
FileNotFoundError: .../adapters/claude/adapters/codex/hooks/userprompt-lifecycle.py
```

### 사전 존재 여부 — HEAD에서 재현 검증

```bash
git archive HEAD | tar -x -C /tmp/v9_head
cd /tmp/v9_head && python3 -m unittest discover -s adapters/claude/tools/fleet/tests -q
```

```
Ran 416 tests in 10.503s
FAILED (errors=3, skipped=15)
```

```bash
git status --porcelain -- '*test_token_budget*'   # → empty
git diff -- tools/fleet/ | grep "rl_ms\|rl_rs"    # → empty
```

**판정: 회귀 아님 (사전 존재, 본 사이클 무관).** 근거 3중:
1. HEAD(416 테스트)에서 **동일한 3건**이 동일 원인으로 실패 — 본 사이클 이전부터 존재.
2. `test_token_budget.py`는 본 사이클이 건드리지 않은 파일(`git status` empty).
3. 원인은 테스트가 repo 루트를 자기 위치 기준으로 walk-up 하는 경로 해석 — 미러 사본(`adapters/claude/tools/fleet/tests/`)에서 실행하면 `adapters/claude/adapters/codex/...`로 잘못 착지. **미러 트리를 직접 실행할 때만 발생하는 아티팩트**이며, 정본(`tools/fleet/tests`)에서는 468 OK.

`test_mirror_parity`가 요구하는 것은 **바이트 일치**이고 그것은 통과했다. 미러 사본을 독립 실행하는 것은 parity 계약이 요구하는 바가 아니다.

> 🟢 **정보성 기록** — 본 사이클 스코프 밖의 기존 결함. 별도 이슈 분리 권고.
