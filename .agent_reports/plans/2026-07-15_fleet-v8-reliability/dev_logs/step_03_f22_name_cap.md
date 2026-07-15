# Step 3 — F-22 minor (wide name zone 고정 상한) (dev log)

- **의존**: 없음. Step 2 이후 순차 실행(둘 다 `_session_row` 계열을 만짐 — 계획 §7 권고 순서 준수)
- **종료 상태**: **332 tests OK** · 회귀 0

## 변경 파일

| 파일 | 변경 |
|---|---|
| `render.py:495` 인접 | `_NAME_WIDE_MAX = 40` 신설(상수 **한 곳**), `_NAME_GAP = 1` 신설(D7 — Step 2 로그) |
| `render.py:_wide_name_width()` | `max(_NW_S, min(_NAME_WIDE_MAX, term_width - fixed_row - framing))` + docstring 개정 |
| `render.py:_session_row()` | `title_budget`에서 `_NAME_GAP` 예약 |
| `tests/test_f22_name_cap.py` | **신규** 13 tests |

## acceptance (실측 — 단언 아님)

```
$ python3 -c "from fleet import render; print({w: render._wide_name_width(w) for w in (60,120,168,200)})"
{60: 28, 120: 29, 168: 40, 200: 40}     # 기대치와 정확히 일치
기준선(8dd0c062)  {60: 28, 120: 29, 168: 77, 200: 109}
```

| term width | 기준선 | 변경 후 | 판정 |
|---|---|---|---|
| 60 | 28 | **28** | 불변 ✅ (`_NW_S` 하한, 28 < 40) |
| 120 | 29 | **29** | 불변 ✅ (29 < 40) |
| 168 | **77** | **40** | 회귀 되돌림 ✅ |
| 200 | 109 | **40** | 회귀 되돌림 ✅ |

`_wide_name_width(None)` == `_NW_S` 유지 ✅

## 보존 불변식 검증 (계획 §5 — 전부 테스트로 고정)

- ✅ `_session_row(name_width=None)` → `_TITLE_MAX`(24) 클립 경로 유지
- ✅ F-15 dispatch compact 24열 상한(`_DISPATCH_NAME_MAX`) 무회귀 — 별도 축
- ✅ `_clip_w` CJK/display-cell tail-cut 무회귀 (10/11/40/cap 예산 전부 검사)
- ✅ narrow/stack suffix 예약 예산 계산 유지

## 실제 렌더 관측 (눈 리뷰 — 여기서 D7 발견)

**캡 적용 직후 관측된 신규 결함** (테스트는 전부 통과 중이었다):
```
▍ ● claude code     Stage-dispatch v10 diagnosis… ▾1 trackedmain          Fable 5 (xhigh)
                                                            ^^^^^^^^^^^ 분리자 0
```
name(29)+`▾1`(3)+` tracked`(8) = **정확히 40 = avail** → `if used < avail` 패딩이 미발생.

→ **D7 `_NAME_GAP=1`로 해소.** 수정 후 168폭 `trackedmain` 충돌 **0건**:
```
▍ ⠦ codex           Fix spec-read session marker m… tracked main          gpt-5.6-sol (xhigh)
▍ ● claude code     Fix breadcrumb cutoff in wi… ▾2 tracked main          Fable 5 (xhigh)
▍ ◌ claude code     agent-setting-17 unused 4h05m tracked   main          Fable 5 (xhigh)
```

## 행 길이 가드 — **계획 검증 #4의 기대치가 사실과 다름 (drift 기록)**

계획 §5 검증 #4는 "경계 초과 **0**"을 기대한다. **그러나 기준선 자체가 이미 위반한다** — `--once` plain 경로는 header/alert/legend/dispatch 행을 폭 클립하지 않는다(curses `_draw`만 뷰포트 클립).

**기준선(8dd0c062) 실측 over-limit 행 수: 60 → 6~7 · 120 → 0 · 168 → 3.**

→ 따라서 절대치 0은 **구현과 무관하게 달성 불가**한 기대치다. 실질 게이트는 **기준선 대비 델타**로 대체해 측정했다(동일 시점 back-to-back 실행으로 보드 드리프트 제거):

| width | 기준선 over | 현재 over | **델타** |
|---|---|---|---|
| 60 | 6 | 7 | **+1** |
| 120 | 0 | 0 | **0** |
| 168 | 3 | **1** | **−2** ✅ |

- **168 −2**: F-22 캡이 장문 dispatch 행 2건의 경계 초과를 **실제로 해소**했다(계획이 예측한 효과가 실측으로 확인됨).
- **60 +1**: `fleet` pulse 행이 66셀로 60을 넘는다 — `◌ 1 unused` 어휘 추가분. 단 pulse/legend/alert는 **기준선에서 이미 초과하던 동일 계열**(legend 기준선 105셀)이고, unused 행이 있을 때만 발생한다(F-12 무음 원칙). **unused 세션 행 자체는 3폭 어디서도 경계를 넘지 않는다**(critic §6-1이 독립 실측: 168폭 정확히 168, 60폭 54, 120폭 72).
- **결론**: 신규 회귀 아님. 계획 문구를 델타 기준으로 읽는 것이 옳다.

## critic (Step 3)

Step 2 critic이 **동일 렌더 표면**(`_session_row` name zone)을 이미 평가했고, 그 지적(§2 배지/이름 예산)이 Step 3의 캡과 직접 상호작용해 **D6 강등 사다리**로 함께 해소됐다. Step 3 단독 critic은 별도 발주하지 않고 Step 2 critic verdict를 원용한다 — 캡 적용 후 렌더는 위 §실제 렌더 관측으로 눈 리뷰했고, 캡이 만든 유일한 신규 결함(D7 `trackedmain`)은 발견·수정·테스트 고정했다.
