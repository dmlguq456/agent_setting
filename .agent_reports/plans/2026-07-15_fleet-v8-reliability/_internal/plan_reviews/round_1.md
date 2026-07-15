# plan-review round 1 — fleet v8 관제 신뢰성 (F-25 · F-26 · F-22 minor · F-27)

- **대상**: `plans/2026-07-15_fleet-v8-reliability/plan/plan.md`
- **계약**: `spec/agent-fleet-dashboard/prd.md` §4.8 (F-25/F-26/F-27), v8 minor(prd.md:217,218)
- **rigor**: standard — feasibility · 누락 단계 · 구체적 검증 명령
- **모드**: 독립 plan-check 게이트 (read-only, 소스 미수정)

## 요약

계획의 **실측 기반은 견고하다**. §1.1~§1.5의 인용 행·상수·측정값을 소스와 대조해 전부 일치를 확인했고, 반증된 항목은 없다. F-28 범위 침범 0, prd.md:410–413 잠긴 결정에 대한 이의 제기 0. 결함은 **검증 명령 층에 집중**돼 있으며 둘 다 국소 수정으로 해소 가능하다.

---

## Blocking

### B1. Step 2 F-26 live acceptance 명령이 구조적으로 실행 불가 (heredoc이 파이프 stdin을 대체)

plan.md:354 —

```bash
python3 tools/fleet/fleet.py --json | python3 - <<'PY'
import json, sys
d = json.load(sys.stdin)
```

`python3 - <<'PY'` 는 **heredoc을 stdin에 연결**하므로 앞단 파이프가 덮어써진다. python은 heredoc을 프로그램으로 소비하고, `sys.stdin`은 그 시점 EOF → `json.load(sys.stdin)`이 **구현 정합성과 무관하게 항상** 실패한다.

실증 (본 리뷰에서 직접 실행):

```
$ echo '{"a":1}' | python3 - <<'PY'
import json,sys
print(json.load(sys.stdin))
PY
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)   # exit=1
```

이 명령은 §9 완료 기준의 **"F-26 live acceptance"** 게이트 그 자체다. 현재 형태로는 게이트가 통과 불가 → 구현자가 임의 변형하게 되고, 계획이 고정하려던 acceptance가 사라진다.

**근거·수정**: Step 1 검증 #3(plan.md:277–291)은 **이미 올바른 패턴**(`--json > /tmp/... ` 후 `json.load(open(...))`)을 쓴다. Step 2 #2를 동일 패턴으로 통일하면 끝난다. (Step 4 #2·#5는 파이프가 없어 문제 없음.)

### B2. §6.5 "byte-identical 교차 구현 계약"이 성립 불가 — R3 드리프트 방어가 통과 불가능한 단언 위에 서 있다

계획(plan.md:541)은 `control.close_registry_row()`와 `close_job_row()`를 같은 픽스처에 돌려 **결과 파일이 byte-identical**임을 단언한다고 했다. 그러나 실제 원본(`adapters/claude/bin/dispatch-headless.py:358–388`)은 note 토큰을 **하드코딩**한다:

```python
def close_job_row(jobs: Path, slug: str, worktree: str, reason: str, reset: str) -> bool:
    ...
            pipe += f",note=dead-{reason}"
            if reset:
                pipe += f",reset={reset}"
            lines[i] = f"{ts}\tdone\t{repo}\t{wt}\t{row_slug}\t{pipe}\n"
```

- 원본은 **반드시 `note=dead-<reason>`** 을 쓴다. `reason="fleet-kill"`을 넣어도 산출은 `note=dead-fleet-kill`.
- 계획 §6.5(plan.md:538)와 prd.md:255는 **`done,note=fleet-kill`** 을 요구한다.
- → 두 출력은 **정의상 1바이트도 같아질 수 없다.** byte-identical 단언은 반드시 실패하거나, 통과시키려면 prd.md:255의 note 문구를 어겨야 한다.

이것이 blocking인 이유: `close_registry_row`는 F-18 **무write 불변식의 유일한 명시적 예외**(prd.md:255)이고, R2/R3(plan.md:639–640)가 그 예외를 정당화하는 **유일한 근거가 이 교차 검증**이다. 단언이 성립하지 않으면 구현자는 (a) 테스트를 조용히 약화(드리프트 방어 소멸) 또는 (b) spec note 문구 위반 중 하나를 고르게 된다. 어느 쪽도 계획이 승인한 경로가 아니다.

부수 사실: 원본 시그니처는 `reset` 을 **필수 인자**로 받는다(`close_job_row(jobs, slug, worktree, reason, reset)`). 계획의 `close_registry_row(...)`(plan.md:511)에는 대응 논의가 없다. 또한 원본은 첫 매치에서 `break`하고, 6필드 초과 행은 재작성 시 초과 필드를 **버린다**(`parts[0..5]`만 재조립) — "동형"의 범위에 이 두 동작이 포함되는지 계획이 명시하지 않았다.

**수정 방향(택1, 계획이 결정할 문제)**: ① 비교를 note 토큰 정규화 후 등가로 재정의하고 "byte-identical" 문구를 철회 ② `close_job_row`의 note 생성만 파라미터화하도록 adapter를 최소 수정(단 계획이 §6.5에서 회피 사유로 든 "adapter 2개 + mirror 편집 표면 번짐"과 상충 — 재판단 필요).

---

## Non-blocking (권고)

### N1. hysteresis dwell가 tier를 무시한다 — §2.1 불변식과 §2.4의 어긋남

`HYST_DOWNGRADE_DWELL_SEC`(plan.md:176–183)의 키는 `(from_state, to_state)` **상태쌍뿐**이다. tier가 들어가지 않는다.

- `("working","idle"): 90` 의 정당화 근거는 plan.md:178 주석 그대로 **"mtime 60s 경계 진동 흡수"** — 즉 **tier-3 유도값** 문제다.
- 그러나 Claude 세션의 `working→idle`은 registry `status: busy→idle`, 즉 **tier-1 명시 선언**이다(실측: pid 1168514 행 `status='idle'`, tier-1).
- → tier-3 노이즈용 처방이 tier-1 진실에 무차별 적용돼, 런타임이 스스로 idle을 선언해도 90초 동안 `working`으로 표시된다. §2.1 불변식("상위 소스가 이긴다")의 정신과 정면으로 어긋나고, 사용자가 보고한 **"판정 기준 불안정"** 을 오히려 재생산할 수 있다(R6이 정확히 이 증상을 리스크로 적어두었다: plan.md:643).

prd.md:242가 hysteresis 자체를 요구하는 것은 맞으므로 **계약 위반은 아니다**. 다만 dwell을 **tier-3 유도 전이에만** 적용하고 tier-1 명시 전이는 dwell 0으로 두는 편이 두 계약을 동시에 만족한다. 최소한 §2.4에 "tier 무관 적용"이 의도임을 명시할 것.

### N2. `unused` 글리프 `○` 계열이 기존 `_DETACHED_GLYPH`와 충돌 — "readable without color" 계약 위반

plan.md:326은 unused 글리프를 **"`○`계열(무활동)" + 전용 dim-yellow 키**로 미리 확정했다. 그러나 render.py:296에 `○`가 이미 있다:

```
_DETACHED_GLYPH = "○"   # Ring means no attached client; idle uses a filled dim-green dot.
```

그리고 바로 위 render.py:291–292가 이 테이블의 계약을 명시한다 — **"Readable without color."** 색으로만 갈리는 `○`는 그 계약을 깬다. detached와 unused는 의미가 전혀 다르므로(전자는 attach 축, 후자는 활동 이력 축) 흑백에서 구분 불가는 F-26의 목적("idle과 구분되는 1급 신호", prd.md:248)도 약화시킨다.

**권고**: 미점유 글리프(예: `◌`/`⊘`)로 바꾸고, 최종 선택은 Step 2의 디자인팀 critic(plan.md:377–383)에 위임 — 계획이 critic 이전에 글리프를 확정할 이유가 없다.

### N3. §2.3 잡 어휘의 `killed`/`cancelled` 행이 live 경로에서 도달 불가 — 의도 미명시

dispatch.py:814–815가 분류 **이전에** 터미널 행을 버린다:

```python
if status not in ("open", "running"):
    continue                          # newest state is terminal (done/killed/…) → not live
```

§2.3 표(plan.md:159–161)는 `done`에만 **"터미널 — 현행처럼 live 목록에서 제외"** 를 달았고 `killed`/`cancelled`에는 달지 않았다. 문자대로 읽으면 killed/cancelled 행이 **새로 live 목록에 노출된다**는 해석이 가능하다 — spec이 승인하지 않은 동작 변경이고, `_LIVE_GLYPH`에 `killed` 엔트리가 없어(render.py:294) `_glyph`의 `.get(state, "·")` 폴백으로 **stale과 동일한 `·`/dim** 으로 찍힌다(크래시는 없음).

픽스처 `job_cancelled.json`(plan.md:258)은 `classify_job()` 직접 호출로만 통과 가능하다. **권고**: §2.3에 "dispatch.py:815 필터 불변 — killed/cancelled 매핑은 분류기 수준 계약이며 live 행을 신설하지 않는다"를 1줄 명시.

### N4. §6.3 control.py 함수 표면과 §6.6 검증 명령이 불일치 — 복사-실행 시 AttributeError

§6.3(plan.md:511)이 선언한 control.py 표면 = `verify_target` · `kill_target` · `log_action` · `close_registry_row` · `actions_root`. 그런데 검증이 호출하는 것:

- plan.md:559 `control.read_proc_start(p.pid)` — 계획 §Step 2 편집표(plan.md:323)는 이 헬퍼를 **`procscan.py`** 에 둔다.
- plan.md:592–593 `control.is_excluded(...)` — §6.3 목록에 없음(§6.4-3의 제외 규칙에 대응하는 함수명 미선언).

기능 누락이 아니라 **표면 선언 누락**이다. §6.3에 두 함수를 등재하거나(재수출 포함), 검증 명령의 호출 경로를 `procscan`으로 교정할 것.

### N5. Step 1 검증 #4 grep 가드가 자동 단언이 아니라 주석 기대값

plan.md:293–295는 기대값을 `#` 주석으로만 적었다 — 사람이 눈으로 세어야 하고, 게이트로 기능하지 않는다.

기대값 자체는 **정확하다**(실측 확인). 현재 `.liveness = ` 대입 지점은 3곳:

- `tools/fleet/collectors/__init__.py:149` — `s.liveness = liveness.classify(s, now)`
- `tools/fleet/collectors/dispatch.py:924` — `r.liveness = p.liveness` (F-18a 흡수 → 계획대로면 증거 병합으로 재배치되며 **소멸**)
- `tools/fleet/collectors/dispatch.py:982` — `j.liveness = _dispatch_liveness(j, now)`

즉 3 → 2 로 줄어야 재배치 성공. 이 전이는 실제로 의미 있는 신호이므로 **count 단언(`test $(... | wc -l) -eq 2`)으로 승격**해 게이트화할 것.

---

## 정보 (확인된 강점 — 반증 시도 후 유지)

- **I1. §1.2가 spec 서술을 실측으로 정정했다.** prd.md:236은 유령 세션을 "`title None`의 **익명** idle 행"으로 기술하지만, 실측 `--json`은 `{'pid':1168514, 'slug':'agent-setting-17', 'title':None, 'status':'idle', 'liveness':'idle', 'mtime':1784083189.601}` — claude.py:207이 `name`을 `slug`에 덮어써서 **이름은 이미 표시되고 title만 None**이다. 계획 §1.2(plan.md:68)가 이 차이를 정확히 포착했다. spec 문구를 그대로 베끼지 않고 소스를 읽은 결과다.
- **I2. F-27 안전 계약의 핵심 전제를 실증 확인했다.** 레지스트리 `procStart:"3918896"` 과 `/proc/1168514/stat` field 22 = **3918896** 이 정확히 일치(`SC_CLK_TCK=100`). §6.4-1의 "시그널 직전 start-time 재대조" 설계와 `pid_reuse.json` 픽스처는 실재하는 사실 위에 서 있다. 유령 pid 1168514는 리뷰 시점에도 생존.
- **I3. §2.2의 "transcript 부재" 입력이 aliasing으로 오염되지 않는다.** `claude.py:35–60 _newest_transcript_path()`는 **known sid의 transcript가 없으면 이웃 `.jsonl`로 폴백하지 않고 None을 반환**한다(2026-07-15 도난 title 사고 이후 명시 계약). 레지스트리가 있으면 sessionId도 있으므로 `unused` 판정 경로는 항상 sid-정확 경로를 탄다. 계획이 이를 명시하진 않았으나 전제는 성립한다.
- **I4. 검증 명령의 폭 주입은 실제로 작동한다.** `COLUMNS=168 python3 -c "import shutil; print(shutil.get_terminal_size().columns)"` → **168**. `render_once`(render.py:1806–1816)가 그 값을 `_build_lines(term_width=tw)`로 넘겨 `_wide_name_width`에 도달하는 경로도 확인(render.py:1279). Step 3 검증 #1도 그대로 실행 가능(`from fleet import render` 헤드리스 임포트 성공, `_wide_name_width(None)` → 28).
- **I5. §1.3 실측표 재현 확인.** `{60: 28, 120: 29, 168: 77, 200: 109}`, `_NW_S=28`, `_TITLE_MAX=24`. "40 상한은 168+만 영향" 판단과 acceptance 교체표(plan.md:413–418) 정확.
- **I6. F-25 재배치 누락 없음.** prd.md:244가 지목한 3건(F-15 queued 유도 · F-18 상관 dedup · F-24 fd 소유권)과 `liveness.classify()`가 §3 재배치 매핑표(plan.md:235–241)에 **전부** 입력 계층으로 등재됐고, F-18b env 마커까지 포함한다. "독립 패치 층으로 남기지 않는다"(plan.md:243)가 N5의 grep 가드로 뒷받침된다.
- **I7. `state_evidence` additive-only 확인.** `Session`(model.py:117–160)·`DispatchJob`(model.py:162–194) 모두 `to_dict() = asdict(self)`이므로 Optional 신규 필드는 자동으로 `--json`에 실린다. 계획의 신규 필드 전부 `Optional`/default `None`, **삭제·개명 0**. `sess._has_transcript` 같은 언더스코어 임시 속성도 `_transcript_path`(claude.py:223) 선례가 있고 `asdict()`에 새지 않는다.
- **I8. `StateTracker` 싱글턴 ↔ `--once`/`--json` no-op 주장 정합.** `--json`(fleet.py:108)·`--once`(fleet.py:128–129) 모두 프로세스당 `collect_all()` 1회 → 트래커가 빈 상태 → dwell 미충족 → 즉시 확정. 라이브만 `_loop`에서 반복 호출한다. 주장 성립.
- **I9. 상수 흡수 정합.** `STALE_MIN = 48*60`(liveness.py:14) → `SESSION_STALE_MIN`, `_QUEUED_GRACE_MIN = 15`(dispatch.py:299) → `JOB_QUEUED_GRACE_MIN`, `_job_liveness(stale_min=15)`(dispatch.py:378) → `JOB_STALE_MIN` — 인용 위치·값 전부 일치. 48h 창에 300s dwell을 얹는 것은 무해하고, dispatch 15분 창에 300s가 붙어 hung 잡 표시가 15→20분으로 늘어나는 것은 수용 범위(단 N1의 tier 논점과 함께 재확인 권장).
- **I10. 범위 준수.** F-28(route record 소비 · resource-runner · governor lease)을 건드리는 Step 0건, §0 스코프 밖 명시(plan.md:33). prd.md:410–413 잠긴 결정에 대한 이의 제기 0 — 계획은 그것을 코드로 실현하는 데만 집중한다(plan.md:15).
- **I11. python 3.8.10 확인**, 계획의 `ast.parse` 가드·`typing.Optional` 유지 방침 타당. mirror parity 부담이 **매 Step 끝**에 배치된 것(plan.md:630, R4)도 2026-07-11 실사고에 비춰 옳다. 디자인 critic·3폭 눈 리뷰·247+ 회귀가 **Step 2/3/4 각각에** 배치돼 있어 "끝에 한 번" 결함 없음(Step 1은 모델 계층이라 critic 생략이 합리적).

---

## Verdict

**BLOCK** — blocking 2건(B1: F-26 live acceptance 명령이 실행 불가 / B2: byte-identical 교차 구현 계약이 성립 불가). 둘 다 국소 수정 대상이며, 계획의 실측 기반·재배치 설계·범위 준수는 유지된다. B1은 기계적 교정, B2는 `close_job_row`의 하드코딩된 `note=dead-` 와 prd.md:255의 `note=fleet-kill` 사이 계약 충돌 해소 결정이 필요하다.
