# plan-check round 2 — 처분 기록 (code-plan 스테이지 소유)

- **사이클**: 2026-07-15 fleet-v8-reliability
- **rigor**: standard (CONVENTIONS §1.1) → 독립 리뷰 1회 + **교정 최대 1회**
- **round 1**: `round_1.md` — verdict **BLOCK**, blocking 2건 / non-blocking 5건
- **round 2**: 교정 1회 소진(예산 종료). 재-독립리뷰는 standard 예산에 없으므로 **스테이지 소유자가 직접 검증**했다.

## 교정 지시 시 스테이지 소유자가 해소한 계약 모호성 (B2)

리뷰가 제시한 두 선택지 중 **①(비교 재정의)**을 채택하고 ②(adapter 파라미터화)를 기각했다. 근거:

- prd.md:255의 "SD-15 `close_job_row` **동형 경로** 재사용"에서 **"동형"의 규범 범위는 동시성·정합성 규율**이지 note 토큰 문자열이 아니다.
- `note=dead-<reason>`("dispatch가 스스로 죽었다")와 `note=fleet-kill`("외부 관제 도구가 사용자 승인 하에 종료시켰다")은 **서로 다른 행위축**이다. 파라미터화로 두 축을 합치면 사후 감사에서 구분이 불가능해지고, 이는 prd.md:255가 `fleet-kill`을 굳이 명시한 이유와 정면 충돌한다.
- 따라서 spec의 `note=fleet-kill`이 우선하고, 성립 불가능했던 "byte-identical" 단언을 철회한다. 드리프트 방어는 **note 토큰만 정규화 후 나머지 전 바이트 일치**로 재설계 — 면제는 계약상 달라야 하는 단 한 토큰뿐이므로 방어력은 유지된다(약화 아님).

## 직접 검증 결과 (스테이지 소유자, 도구 실측)

| 항목 | 방법 | 결과 |
|---|---|---|
| B1 heredoc 안티패턴 제거 | `grep -c "json \| python3 - <<" plan.md` | 잔존 1건 = **경고 주석 자체**(plan.md:382). 실제 명령(plan.md:383-384)은 Step 1 #3 패턴(`--json > /tmp/...` → `json.load(open(...))`)으로 교정됨 ✅ |
| B2 "byte-identical" 철회 | `grep -n "byte-identical" plan.md` | 잔존 2건(plan.md:574, 738) = **철회 서술·변경 이력**뿐. 살아있는 단언 0 ✅ |
| spec note 보존 | `grep -c "note=fleet-kill" plan.md` | 7건 — prd.md:255 문구 유지 ✅ |
| N1 hysteresis tier 게이트 | `grep -n "HYST_APPLIES_TO_TIER" plan.md` | plan.md:188 `HYST_APPLIES_TO_TIER = (3,)` — dwell을 tier-3 유도 전이로 한정, §2.1 "하위가 상위를 못 이긴다" 불변식과 정합 ✅ |
| 소스 무수정 | `git status --porcelain` (worktree) | **empty (clean)** — 계획 스테이지가 소스를 건드리지 않음 ✅ |
| 기준선 회귀 | `python3 -m unittest discover -s tools/fleet/tests -t . -q` | **Ran 247 tests — OK** (13.7s) ✅ |

## 잔존 우려 (code-execute가 인지하고 소유할 것)

1. **N2 `unused` 글리프 `◌`는 잠정** — 최종 확정은 Step 2의 디자인팀 critic(read-only)에 위임됨. 기존 `_DETACHED_GLYPH`와의 비충돌 및 "readable without color" 계약을 critic이 확인해야 한다.
2. **F-27 `↑↓` 키 계약 양보** — spec F-27(prd.md:252)은 "`↑↓` 선택 모드 **진입**/이동"이라 하나, `render.py:2071-2073`에서 `↑↓`는 이미 스크롤에 바인딩돼 있다. 계획은 스크롤 회귀 0을 우선해 **모드 있는 커서**(`s`/`x` 진입 → `↑↓` 이동 → `Esc` 해제)를 택했다. "진입"만 별도 키로 양보한 것이며, 이 양보는 **사용자 확인 자리**로 계획에 표시돼 있다. 사용자가 spec 문구 그대로를 원하면 스크롤 키 재배치가 별도로 필요하다.
3. **hysteresis dwell 수치(90/300s)는 제안값** — 실측 튜닝 대상. Step 1 픽스처가 경계를 고정하나, 라이브 체감은 execute 단계에서 재평가될 수 있다.

## Verdict

**PASS with concerns** — round 1의 blocking 2건은 실측으로 해소 확인, non-blocking 5건 전량 반영. 잔존 우려 3건은 모두 execute 단계가 안전하게 소유 가능한 범위(글리프 확정은 critic 게이트, 키 양보는 표시된 사용자 확인 자리, dwell은 픽스처로 고정된 튜닝값)이므로 사이클을 진행한다.
