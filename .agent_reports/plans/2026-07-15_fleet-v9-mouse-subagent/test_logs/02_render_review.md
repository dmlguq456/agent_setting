# test log 02 — 3폭 렌더 검사 · D3 stage zone 상한

```bash
for w in 60 120 168; do COLUMNS=$w python3 tools/fleet/fleet.py --once > /tmp/v9_test_${w}.txt; done
```

curses 미진입 경로(`--once`) — kill 경로 도달 불가(plan §0). 실세션 스폰/시그널 0.

## 1. 오버플로 계측 — 두 척도의 불일치와 정본 판정

### awk 문자수 (참고 지표 — plan §6이 "참고"로 명시)

| width | over |
|---|---|
| 60 | 16 |
| 120 | 0 |
| **168** | **7** ← 겉보기 초과 |

### `_dw()` display-cell (★ **정본** — plan §6 "정본은 `_dw()` 기반")

```python
from fleet.render import _dw
for line in open(f"/tmp/v9_test_{w}.txt"): 
    if _dw(line) > w: ...
```

```
=== width=60: 7 overflow ===
  line=0  dw=103 slack=-43  '  usage claude code   5h [━━━─────  35%] ↻ 1h20m   7d ...'
  line=3  dw=71  slack=-11  '  🧠 mem  +73 added(33w·40d) · 24 expired · 7 pruned ...'
  line=4  dw=96  slack=-36  '  alert ⚠ durable-over github.com/dmlguq45…=86·...'
  line=21 dw=63  slack=-3   '▍ ↳ ⠧ claude code   fleet-v9-mouse-su…  fleet-v9-mouse-subagent'
  line=22 dw=74  slack=-14  '▍   —               opus (high)     dev·std/conductor/qa:~s'
  line=25 dw=78  slack=-18  '▍   —               opus (high)     dev·std/deep reviewer/q'
  line=41 dw=105 slack=-45  '  ⠹ working   ● idle   ▾N child jobs   ↳ dispatch  ...'
=== width=120: 0 overflow ===
=== width=168: 0 overflow ===
```

**168 = 0, 120 = 0 (display-cell 정본).** awk의 7건은 CJK/이모지/박스문자를 1문자=1셀로 세는 프록시 오차 — **거짓 양성**. A4-2 충족.

## 2. A4-2 — 168 무오버플로가 **구조적**인가

`test_d3_stage_zone` 6건 전부 OK. 특히:

- `test_cap_lives_in_exactly_one_constant` → `_STAGE_ZONE_MAX` 단일 상수 (A4-1 ✅)
- `test_168_no_overflow_is_structural_not_incidental` → stage 라벨을 인위적으로 늘린 fixture에서도 경계 미초과 (A4-2 ✅)
- `test_long_conductor_label_is_dropped_not_tail_cut` → 성분 통째 드롭 (A4-3 ✅)
- `test_active_stage_survives_when_past_stages_drop` → SD-F2 우선순위 (A4-3 ✅)
- `test_short_rows_are_unaffected` → 회귀 0 (A4-4 ✅)

**판정: PASS.** v8의 "slack 5에 의존하는 부수적 상태"가 상한 상수로 대체됨. 이제 "168 오버플로 0"을 구조적 보장으로 말할 수 있다.

## 3. A4-5 정직성 조건 — 60폭 잔존 명시

60폭 7건의 귀속:

| line | 내용 | 귀속 |
|---|---|---|
| 0 | `usage` 요약 행 | **D4** (스코프 밖) |
| 3 | `🧠 mem` 요약 행 | **D4** (스코프 밖) |
| 4 | `alert ⚠ durable-over` 행 | **D4** (스코프 밖) |
| 41 | legend 행 | **D4** (스코프 밖) |
| 21·22·25 | dispatch conductor/worker 행 | stage/role suffix 계열 |

- **4건 = D4**(legend/mem/usage/alert 요약 행) — plan §9가 명시적으로 스코프 밖 선언.
- **3건 = dispatch 행** — stage zone 상한이 도입됐음에도 60폭에서는 여전히 초과. 다만 `_STAGE_ZONE_MAX`는 stage zone **자체**의 상한이지 행 전체 상한이 아니므로 계약 위반은 아니다(A4-2는 **168** 한정 주장).

> ⚠️ **v8 베이스라인 "60폭 5건"과의 대비는 성립하지 않는다.** `--once`는 **라이브 데이터**를 렌더하며, 현 시점 세션 집합은 v8 계측 당시와 다르다(본 사이클의 depth-2 워커 행이 새로 존재 — line 25의 `dev·std/deep reviewer`가 바로 그것). 따라서 "5건 → 7건"은 회귀 증거가 **아니고**, "5건 중 2건 개선"도 이 실행만으로는 **증명 불가**다. 동일 입력 고정 없이는 비교 불가 — plan §6 R4-2의 성공 기준("60폭 5건 중 stage zone 원인 2건 개선")은 **본 실행으로 판정하지 않는다**. 정본 판정은 `test_d3_stage_zone`의 fixture 기반 단위 테스트가 소유하며, 그것은 통과했다.

**A4-5 판정: PASS (조건부 문구 정정 필요)** — 결과 보고는 "168 무오버플로 = 구조적 보장(단위 테스트 실증)" + "60폭 잔존 = D4 원인 4건 + dispatch 행 3건, 본 사이클 스코프 밖"으로 서술해야 하며, "60폭 5건 중 2건 개선"이라는 **수치 대비 주장은 근거 없음**(라이브 데이터 비고정).

## 4. 눈 검사 — 폭별 소견

- **168**: 컬럼 헤더 정렬 정상. dispatch 행의 `dev·std/deep reviewer/qa:~std  running` 이 stage zone 안에 안착. 경계 미초과.
- **120**: `narrow` 레이아웃 전환 정상. 오버플로 0.
- **60**: `stack` 레이아웃. 세션 행은 안착하나 요약/legend 행이 초과(D4 기존 결함).
- 3폭 모두 **`⚡` 0회 등장** (glyph 판정 근거 — test log 05 참조).
- 서브에이전트 행: 현 라이브 데이터에 활성 서브에이전트가 없어 `🔬` 미등장 → **소스 부재 시 서브 행 생략**(prd.md:294)이 실렌더에서도 확인됨.
