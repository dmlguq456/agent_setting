# code-test 독립 검증 리뷰 — fleet v8 관제 신뢰성

- **사이클**: 2026-07-15 fleet-v8-reliability · **스테이지**: code-test (depth 2, 독립 검증)
- **증거**: `_internal/test_logs/test_report.md` (전 명령·전 출력 첨부)
- **디자인 critic**: `_internal/test_reviews/design_critic_independent.md`
- **판정**: **PASS (조건부)** — 블로커 0, 후속 obligation 3건, 기존 결함 기록 3건

---

## 1. execute 주장 대조표 (독립 재측정)

| # | execute 주장 | 본 검증자 실측 | 판정 |
|---|---|---|---|
| 1 | baseline 247 → **414 tests OK** | 414 OK (16.3s) / baseline **247 확인** | ✅ **일치** |
| 2 | 회귀 0, 삭제 0 | 기존 테스트 파일 11개 전부 test 개수 보존. 수정된 기존 테스트 1개(`test_f18_attribution.py`)는 **약화 아닌 강화** | ✅ **일치** |
| 3 | F-22 `{60:28, 120:29, 168:40, 200:40}` | 완전 일치 | ✅ **일치** |
| 4 | F-22 was `{168:77, 200:109}` | 베이스라인 추출 후 실측 → 일치 | ✅ **일치** |
| 5 | F-27(a) 위조 → 거부, 프로세스 생존 / 대조군 → ok, rc=-15 | sleep 픽스처로 재측정 → 일치 | ✅ **일치** |
| 6 | F-27(b) 자동 제어 = 0 | 재측정 → action log 미생성. 추가로 **`control`이 import조차 안 됨**(런타임 probe) | ✅ **일치 (더 강함)** |
| 7 | 신규 `control.py` + 미러 동기 | `diff -r` → **바이트 동일** | ✅ **일치** |
| 8 | `DispatchJob.proc_start` BLOCK 발견·수정, 통합 커버리지 신설 | 필드 실재 + 수집 경로 4곳 실제 채움 + 종단 테스트 `test_job_row_kill_actually_works_end_to_end` 신설 확인 | ✅ **일치** |
| 9 | F-26 live acceptance (유령 pid 1168514 → `◌ agent-setting-17 unused 4h05m`, tier 1) | **재현 불가**(유령 자연 종료, registry 파일 소멸 — 지시대로 되살리지 않음). **문서 정합성만 검증**: `activity_ms=119`·`procStart=3918896`·tier/rule 문자열이 플랜 §1.2 실측 및 본 검증자의 동형 픽스처 재현 출력과 **1:1 일치**. 시각 계산도 모순 없음 | ⚠️ **내부 일관 — 단 시간 의존적** (발견 D2) |

**execute의 자진 보고는 전부 정확했다.** 과장·은폐의 흔적을 찾지 못했다. 특히 `proc_start` BLOCK 자진 보고와 안전 규율 위반 자진 보고는 검증자가 놓쳤을 수도 있는 사안이었다.

---

## 2. 발견 (심각도 순)

### D1 — 🟠 tier-3 mtime이 tier-1 registry `busy`를 이긴다 (§2.3 규범 표 미기재 + 테스트 공백)

**위치**: `tools/fleet/model.py` — `classify_session()`의 `if age_min > stale_min:` 분기 (`# Inactivity-history axis` 주석 블록, `_session_status_state` 호출 직후·`if st:` 검사 **직전**)

**재현**:
```python
model.classify_session(dict(pid_alive=True, status="busy", mtime=now-49*3600, transcript=True), now)
# → ("stale", {"tier": 3, "source": "mtime", "rule": "no activity for > 2880 min"})
```

**무엇이 문제인가**: registry가 tier-1으로 `busy`를 **명시 선언**하는데 tier-3 mtime이 이를 덮는다. 플랜 §2.1 불변식("하위 소스는 상위 소스와 모순될 때 절대 이기지 못한다")과 정면 충돌하고, **§2.3 규범 표에 이 조합에 대응하는 행이 없다**(표의 `stale`은 registry status `(부재)`일 때만).

코드는 §2.2 축 분리로 정당화한다("Inactivity-history axis (§2.2, same axis as unused)"). **그러나 §2.2는 무활동 이력 축의 소유자를 "registry `startedAt`/`updatedAt` + transcript 부재"로 규정했지 mtime이 아니며**, 오히려 **"3순위 mtime만으로 `unused`를 만들지 않는다(registry 증거 필수)"**를 금지 규칙으로 못박았다. 이 stale 경로는 정확히 mtime **단독**으로 tier-1을 덮는다.

**정상 참작**:
- `state_evidence`가 `tier=3, source=mtime`이라고 **정직하게 보고**한다. 은폐 없음 — F-25의 감사 가능성 목표는 오히려 달성됐다(이 발견 자체가 `state_evidence` 덕에 가능했다).
- 코드 주석의 "Preserves the pre-F-25 ordering — status never rescued a 48h-silent row"는 **사실**이고, 48시간 침묵한 세션을 `working`으로 표시하는 것이 더 나쁘다. **행동 자체는 옹호 가능하다.**

**판정**: **코드가 옳고 플랜의 규범 표가 불완전하다.** 코드 수정이 아니라 **문서 정정**이 올바른 해소다.

**권고**: ① §2.3 표에 행 추가 — `(임의) | 3순위: mtime age > SESSION_STALE_MIN | stale — registry를 이긴다(존재 축과 동형: 48h 침묵은 활동성 주장을 종결)`. ② §2.2의 "무활동 이력 축 소유자" 문구에 mtime 48h 창을 포함하도록 정정하거나, 이 경로를 **제3의 축**으로 명명. ③ 테스트 신설 — `test_f25_state_model.py` 33개 테스트 중 이 케이스를 고정하는 것이 **없다**(픽스처 목록에도 없음). 규범 미기재 + 테스트 미고정이 겹쳐 **아무도 모른 채 착륙할 뻔했다.**

---

### D2 — 🟠 유령 세션은 48시간 후 다시 안 보이게 된다 (F-26의 목적이 자동 무력화)

**위치**: D1과 **동일 분기** + `tools/fleet/render.py:1670` (기본 가시성 필터)

**재현**:
```python
model.classify_session(dict(pid_alive=True, status="idle", mtime=now-49*3600,
                           transcript=False, activity_ms=119), now)
# → ("stale", tier=3)   ← unused 가 아니다
```
```python
# render.py:1670 — stale 은 기본 숨김, unused 는 기본 노출
shown = (group_sessions if _SHOW_ALL else
         [s for s in group_sessions if not (s.liveness in ("stale","dead") or s.app_server)])
```

**인과 사슬**:
1. 유령은 transcript가 없다 → `claude.py`가 mtime을 `statusUpdatedAt`(= 시작 시각)으로 채운다(플랜 §1.2 기재 기존 동작).
2. 따라서 **유령의 mtime = 유령이 태어난 시각**이고, 유령이 사는 동안 **영원히 갱신되지 않는다**.
3. 유령이 48시간을 넘기는 순간 → `stale`(tier-3) → **기본 숨김** → 대시보드에서 사라진다.
4. = prd.md:248이 문제로 규정한 상태("어디서도 인지 불가")로 **자동 복귀**.

**왜 사소하지 않은가**: 유령은 정의상 **아무도 안 쓰는 세션**이고, **오래 살아남는 것이 유령의 본질**이다. 48시간 커트오프는 **가장 오래되고 가장 정리가 필요한 유령을 정확히 골라 숨긴다.** F-27 kill의 1순위 대상이 F-26의 시야에서 사라지는 구조다.

**execute의 acceptance가 통과한 이유**: 측정 시점이 **4h05m**이었기 때문이다. 정직하고 재현 가능한 측정이지만 **시간 의존적**이며, 49시간째에는 통과하지 않는다.

**판정**: **설계 결정이 필요한 사안** — "유령의 `unused`는 48h를 넘어서도 유지돼야 하는가?" 본 검증자가 결정할 것이 아니다. **사용자/spec 결정 자리**로 올린다.

**권고 (택1, 사용자 결정)**:
- (a) `unused`를 `SESSION_STALE_MIN` 창에서 **면제** — `unused` 판정을 stale 검사 **앞으로** 이동. F-26의 목적에 가장 충실하나 D1의 tier 순서도 함께 정리해야 함.
- (b) 현행 유지 + **§2.3 표와 F-26 acceptance에 시간 한계를 명시** — "유령은 48h까지만 `unused`로 노출된다"를 계약으로 승격.
- (c) `stale`이면서 `activity_ms≈0`인 행에 **별도 표식** 부여(오래된 유령 = 더 강한 정리 후보).

---

### D3 — 🟡 stage zone 무상한 — 168 무오버플로가 "구조"가 아니라 "5열 여유의 운" (기존 결함)

**출처**: 독립 디자인팀 critic이 발견 → 본 검증자가 실측 확인.

```
168열 캡처 최장 행: line=15  width=163  slack=5    (dispatch conductor 행)
                    line=26  width=131  slack=37   (세션 행)
상한 상수: _NAME_WIDE_MAX=40 (name) · _DISPATCH_NAME_MAX=18 (dispatch 이름)
         → stage/meta suffix(`dev·std/conductor/qa:~std  code: plan✓ › exec✓ › test`)를 묶는 상수 **없음**
```

**함의**: 본 검증자가 관측한 "168 오버플로 베이스라인 2건 → 현재 0건"의 **개선은 실재하나 부수적(incidental)** 이다. F-22가 name을 77→40으로 깎아 dispatch 행을 우연히 168 안으로 끌어들인 것이지 stage zone을 고친 게 아니다. conductor/qa 라벨이 6열 길어지거나 stage가 `test✓ › report`로 진행하면 **다시 터진다**. **60폭 오버플로 5건 중 2건도 같은 stage zone이 원인** — 같은 뿌리가 좁은 폭에서 이미 증상 중.

**판정**: **본 사이클 블로커 아님** — 베이스라인에도 존재하는 기존 결함이고, F-22 minor(prd.md:218)의 스코프는 명시적으로 **name zone**이다. 본 사이클은 이 축에서 **순개선**을 냈다.

**단, 보고의 정직성 조건**: **"168 오버플로 0"을 구조적 보장으로 보고해서는 안 된다.** 5열 여유에 의존하는 상태임을 code-report에 명시할 것.

**권고**: stage zone 대칭 상한(131 edge 정렬)을 **후속 이슈**로 분리.

---

### D4 — 🟡 60폭 경계 초과 5건 — 플랜 §9 완료 기준 미충족 (기존 결함)

```
현재      : width 60 → 5건 | 120 → 0 | 168 → 0
베이스라인: width 60 → 5건 | 120 → 0 | 168 → 2
```
초과 행: usage bar(+1) · mem 요약(+10) · dispatch stage ×2(+14, +9) · legend(+45).

**판정**: 베이스라인 동일 → 본 변경 무관. 다만 **플랜 §9의 "60/120/168 경계 초과 0"은 60폭에서 미충족**이다. 원인은 F-22가 아니라 legend/mem/usage 요약 행의 60폭 미축약 + D3의 stage zone. **기존 결함이므로 블로커로 올리지 않되 기록한다.**

---

### D5 — 🔴 플랜 `plan.md:396-402`가 잘못된 절차를 규범화하고 있다 (안전)

플랜 §4 검증 #2의 "[pid 1168514가 이미 죽었을 때 동형 케이스 재현 절차]"는 다음을 **정상 절차로 기술**한다:
```
a. 새 유령 세션 생성:  (tmux new-session -d 'claude --teammate-mode tmux') 후 프롬프트 미제출
...
e. 정리:               Step 4 착륙 후에는 fleet 자신의 `x` kill 로 정리(그 자체가 F-27 acceptance)
```

**이는 실제 claude 세션을 spawn하고 SIGTERM하라는 지시다.** execute 워커가 이 절차를 따라 실제 claude 세션을 spawn·SIGTERM했고 자진 보고했다.

**본 스테이지의 처분**: 이 절차를 **따르지 않았다**. F-27 안전은 자가 생성 `sleep` 픽스처로만 재측정했고(test_report.md Level 5), **실제 claude/codex 세션은 단 하나도 spawn하지 않았고 signal하지 않았다.**

**권고**: `plan.md:396-402`를 **삭제 또는 정정**. 픽스처 주입(`classify_session`에 registry shape를 직접 주입 — 본 검증자가 Test 4.1에서 실증)으로 동일 검증이 **프로세스 생성 없이** 가능하다. 실제 세션 spawn/kill을 acceptance 절차로 규범화하면 후속 사이클이 같은 위반을 **정당한 절차로 알고** 반복한다.

---

### D6 — 🔵 플랜 §3 검증 #4 가드가 셸 의존적 (사소)

```bash
grep -rn "\.liveness = " tools/fleet/ --include=*.py | ...   # 인용 없음
```
사용자 셸은 **zsh**이고, zsh에서 `--include=*.py`는 글로빙 시도 → `no matches found` → `N=0` → `test 0 -eq 2` → **가드가 항상 FAIL 보고**. bash에서만 동작한다.

**정정**: `--include='*.py'`로 인용. (인용 후 실행 시 가드는 **정상 통과** — 대입 정확히 2곳.)

---

### D7 — 🔵 "스크롤 회귀 0"을 고정하는 테스트가 없다 (사소)

`test_f27_control.py` 68개 테스트 중 base mode에서 `↑↓`가 `_OFFSET`을 움직임을 단언하는 것이 없다(`KEY_UP`은 select-mode 커서 이동 테스트에만 등장). 회귀 0 보증이 **코드 검사에만** 의존한다 — 본 검증자가 베이스라인과 대조해 스크롤 블록이 **문자 단위 동일**하고 `_SELECT_MODE` 게이트가 올바름을 확인했으나, 누군가 게이트를 잘못 건드리면 **조용히 깨진다**.

**권고**: `test_arrow_keys_still_scroll_in_base_mode` 1건 신설.

---

### D8 — 🔵 플랜 §5 문서 오류 (사소, 회귀 아님)

플랜 §5가 "F-15 dispatch compact **24열** 상한(`_DISPATCH_NAME_MAX`)"이라 기술하나 실제 상수는 **18**이다(`render.py:871`). **베이스라인도 18** → 회귀 아님. 플랜이 `_TITLE_MAX = 24`와 혼동한 문서 오류. 신규 테스트(`test_f22_name_cap.py:79`)는 올바르게 18을 고정한다.

---

## 3. `↑↓` 드리프트 판정 (요청된 미결 항목)

**스크롤 회귀 = 0 (구조적으로 확인).** base mode 스크롤 블록이 베이스라인과 **문자 단위 동일**하고, `_SELECT_MODE`가 False인 한 `↑↓`는 select 핸들러를 거치지 않고 곧장 `_OFFSET`에 도달한다. select 모드 진입은 **오직** 명시적 `s`/`x`뿐이다.

**드리프트 판정: 블로커 아님 — 사용자 확인 후 수용 권고.**
- A안(`↑↓`=진입)을 채택하면 **prd.md:80의 명시적 키 표 계약**(`↑↓`=스크롤)과 **prd.md:155의 v2 "항상 맨 아래까지 도달" 버그 수정 계약**을 깨뜨린다. 두 개의 명시 계약 vs 조작 모델 절의 예시 표기 1건이 충돌할 때 후자를 양보하는 것이 옳다.
- 구현은 F-27의 실질(선택 커서·`↑↓` 이동·`x` kill·확인 프롬프트)을 **전부** 지키고 "진입" 한 단어만 양보한다.
- 플랜 R1이 이미 `[decision: significant — 사용자 확인 자리]`로 표시했다. **사용자 확인 + spec §4.8 F-27 문구 sync**가 필요하다.

---

## 4. 헤드리스로 검증 불가능한 것 (정직한 한계)

**라이브 TUI 눈 검사는 수행되지 않았다** (TTY 없음). 검증된 것은 헬퍼 수준(68개 테스트가 `_handle_select_key`/`_handle_prompt_key`/`_prompt_segs`/`_footer_segs`를 직접 호출)과 비-curses 스냅샷(`--once`)뿐이다.

**커버리지 적정성 판정**: **로직 축은 충분하다.** 키 분기, 커서 identity 앵커링(index가 아닌 `(pid, proc_start)` — 재빌드 시 재조준을 구조적으로 차단), 클램프, 재앵커, 프롬프트 문구의 60/120/168 무잘림, 이중 확인 키 요구, grace 만료 시 재프롬프트가 전부 고정돼 있다. **시각 축은 불충분하다.**

**오직 실제 터미널의 사람만 잡을 수 있는 것**:
1. **`◌`(U+25CC)가 실제 폰트에 없으면 tofu(`□`)로 렌더된다.** 캡처로도 안 잡힌다(캡처는 코드포인트만 보존). **실제 위험** — F-26의 "흑백에서도 읽히는 1급 신호" 계약이 폰트 하나로 무너질 수 있다.
2. 커서 하이라이트(`reverse`)가 실제 터미널 테마에서 읽히는가 — 특히 **dim yellow `◌` 행 위에 reverse가 겹칠 때** 대비가 무너지지 않는가.
3. 확인 프롬프트가 뜨는 순간의 깜빡임/재그리기 아티팩트.
4. 커서 뷰포트 추종이 **체감상** 자연스러운가(클램프 로직은 테스트됐으나 스크롤 점프의 어지러움은 아님).
5. SIGTERM 후 행이 사라지는 타이밍이 "먹혔다"고 읽히는가.
6. **`unused` 행의 실물 렌더 전체** — 유령이 없어 `◌` 행을 3폭 어디에서도 관찰하지 못했다(디자인 critic도 동일 한계를 명시).

---

## 5. 후속 obligation

| # | 항목 | 근거 |
|---|---|---|
| O1 | **spec §9 모듈 트리에 `control.py` 1줄 등재** | 플랜 §6.1 [decision: significant] · F-19 `collectors/memory.py` 선례(prd.md:202) |
| O2 | **spec §4.8 F-27 키 문구 sync** (prd.md:252 → "`s`/`x` 진입, `↑↓`/`jk` 이동") + **사용자 확인** | 플랜 R1 [decision: significant] · 본 리뷰 §3 |
| O3 | **플랜 §2.2/§2.3 규범 표 정정 + 테스트 신설** (D1) · **D2 설계 결정** · **`plan.md:396-402` 삭제/정정** (D5) | 본 리뷰 §2 |

---

## 6. 최종 판정

**PASS (조건부)** — 블로커 0.

**통과 근거**: 414 tests OK(회귀 0·삭제 0·약화 0), F-22 4폭 실측 완전 일치(베이스라인 대조 포함), `--json` additive-only(삭제/개명 0), 실 라이브 행 13개에서 tier 주장이 파일시스템 사실과 1:1 교차 검증(불변식 위반 0), F-27 안전 재측정 전항 통과(위조 거부·프로세스 생존·대조군 rc=-15·자동 제어 0), 미러 바이트 동일, 재배치 가드 2곳 정확, `proc_start` BLOCK 수정 실재 + 통합 커버리지 신설 확인, 스크롤 회귀 0.

**조건**:
1. **D2는 사용자 결정 자리다** — 유령이 48h 후 다시 숨겨지는 것이 의도인지 확인 필요. 코드 결함이 아니라 **미결정 설계**다.
2. **D5(plan.md:396-402)는 반드시 정정**하라 — 잘못된 절차가 규범으로 남으면 후속 사이클이 안전 위반을 정당한 절차로 알고 반복한다. 본 검증자가 발견한 것 중 **유일하게 안전 축**이다.
3. **code-report는 D3를 반영해 "168 오버플로 0"을 구조적 보장으로 보고하지 말 것.**
4. D1의 규범 표 정정 + 테스트 신설은 착륙 전 권고, 착륙 후 후속 허용(코드 행동은 옹호 가능하므로).
</content>
