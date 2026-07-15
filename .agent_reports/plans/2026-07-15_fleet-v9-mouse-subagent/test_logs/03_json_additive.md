# test log 03 — `--json` additive 스모크

계약: prd.md:294 — *"`--json` additive(신규 `subagents` 키)"*, 기존 키 무변경.

## 방법 — HEAD 형상과의 구조 diff (워크트리 무변이)

작업 트리를 **변형하지 않고** HEAD 트리를 `/tmp`로 내보내 양쪽을 각각 실행:

```bash
git archive HEAD | tar -x -C /tmp/v9_head          # 워크트리 무변이 (git stash 미사용)
python3 tools/fleet/fleet.py --json > /tmp/v9_new.json
(cd /tmp/v9_head && python3 tools/fleet/fleet.py --json) > /tmp/v9_head.json
```

값이 아닌 **키 경로 + 타입**만 재귀 수집해 비교(라이브 데이터라 값은 필연적으로 다름):

```python
def shape(o, p=""):
    out = set()
    if isinstance(o, dict):
        for k, v in o.items():
            out.add(p + "/" + k + ":" + type(v).__name__)
            out |= shape(v, p + "/" + k)
    elif isinstance(o, list) and o:
        for v in o[:50]: out |= shape(v, p + "[]")
    return out
```

## 결과

```
=== TOP-LEVEL KEYS ===
  HEAD: ['jobs', 'memory', 'sessions', 'summary']
  NEW : ['jobs', 'memory', 'sessions', 'summary']

=== REMOVED (regression if non-empty) ===
   NONE — every pre-existing key/shape preserved

=== ADDED ===
   + /sessions[]/subagents:NoneType
   + /sessions[]/subagents:list
   + /sessions[]/rl_ms:list
   + /sessions[]/rl_rs:list

=== subagents key present on session rows? ===
  sessions with 'subagents' key: 9 / 9
```

## 판정

- **제거된 키/형상: 0** — 기존 계약 완전 보존. ✅
- **`subagents`**: 9/9 세션 행에 존재. `NoneType`(소스 부재/미확인 = 정직한 결손)과 `list`(확인됨) 두 형태 — model.py의 `Optional[list] = None` 계약과 정합. ✅
- **`rl_ms`/`rl_rs`**: 본 사이클과 **무관**함을 확증:

```bash
git show HEAD:tools/fleet/model.py | grep -c "rl_ms\|rl_rs"   # → 2
grep -c "rl_ms\|rl_rs" tools/fleet/model.py                    # → 2  (동일)
git diff -- tools/fleet/ | grep "rl_ms\|rl_rs"                 # → empty (diff에 없음)
```

HEAD에도 동일하게 존재하며 diff에 등장하지 않는다 → usage API가 그 순간 rate-limit 데이터를 반환했는지에 따라 조건부로 직렬화되는 **라이브 데이터 아티팩트**. 스키마 변경 아님.

**A3-4 (`--json` additive) 판정: PASS** — 신규 키는 `subagents` **단 하나**이며 기존 키/형상 제거 0.

> ※ plan §4.6 규범 준수: heredoc(`--json | python3 - <<'PY'`)은 stdin 점유로 항상 실패하므로 사용하지 않고 **파일 경유**로 실행함.
