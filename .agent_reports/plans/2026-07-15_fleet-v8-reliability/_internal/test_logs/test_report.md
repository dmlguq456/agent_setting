# code-test — fleet v8 관제 신뢰성 독립 검증

- **사이클**: 2026-07-15 fleet-v8-reliability
- **스테이지**: code-test (depth 2, 독립 검증) — intensity=standard, mode=dev, qa=standard
- **워크트리**: `/home/Uihyeop/agent_setting-wt/fleet-v8-reliability` (dirty/uncommitted — 예상됨)
- **소스 무수정**: 본 스테이지는 소스를 1바이트도 고치지 않았다. 커밋 없음.
- **베이스라인 기준점**: `git merge-base main HEAD` = `8dd0c062` (브랜치에 커밋된 diff 없음 — 전량 워킹트리 변경. 따라서 `git diff main...HEAD`는 **빈 출력**이고, 모든 비교는 워킹트리 ↔ merge-base로 수행했다.)
- **최종 판정**: **PASS (조건부 — 후속 obligation 3건, 블로커 0)**

---

## Level 1 — 전체 회귀

### Test 1.1: 전체 스위트

**Command:** `python3 -m unittest discover -s tools/fleet/tests -t . -q`

**Output:**
```
Ran 414 tests in 16.334s

OK
```

**Verdict:** PASS — execute 주장 414 OK와 **일치**. 실패 0.

> ResourceWarning 1건(`test_f27_control.py:493` unclosed file — grep 가드가 `open()` 결과를 닫지 않음). 테스트 실패 아님, 위생 문제.

### Test 1.2: 베이스라인 테스트 수 — execute의 "247" 주장 독립 검증

**Command:**
```bash
git archive $(git merge-base main HEAD) tools/fleet | tar -x -C /tmp/v8_base
cd /tmp/v8_base && python3 -m unittest discover -s tools/fleet/tests -t . -q
```

**Output:**
```
Ran 247 tests in 7.948s
FAILED (failures=2, errors=11, skipped=8)
```

**Verdict:** PASS — 베이스라인 **247 확인**(execute 주장과 일치). 247 → 414 = **+167**.

> 실패 13건은 **본 검증자의 추출 아티팩트**이지 베이스라인 회귀가 아니다. `/tmp/v8_base`에는 `tools/`만 추출했고, 실패한 테스트는 전부 `adapters/`·repo root를 요구하는 것들이다(`test_f17_title_refresh`·`test_token_budget`·`test_token_experiment`). 동일 테스트가 실제 워크트리에서 414 OK로 통과한다. **오보 방지를 위해 명시한다.**

### Test 1.3: 테스트 약화·삭제 0 — 파일별 test 메서드 수 대조

**Command:** 베이스라인 각 `test_*.py`의 `grep -c "def test_"` ↔ 현재

**Output:**
```
    test_dispatch.py: 59 -> 59          test_f19_memory.py: 17 -> 17
    test_f14_title.py: 16 -> 16         test_f21_cross_harness_titles.py: 10 -> 10
    test_f15_rows.py: 28 -> 28          test_mirror_parity.py: 1 -> 1
    test_f17_title_refresh.py: 49 -> 49 test_runtime_currentness.py: 5 -> 5
    test_f18_attribution.py: 31 -> 31   test_token_budget.py: 21 -> 21
                                        test_token_experiment.py: 10 -> 10
```

**Verdict:** PASS — **기존 테스트 삭제 0**. 11개 파일 전부 개수 보존.

### Test 1.4: 유일하게 수정된 기존 테스트 — 약화 여부 정밀 판정

**Command:** `git diff $(git merge-base main HEAD) -- tools/fleet/tests/`

수정된 기존 테스트는 `test_f18_attribution.py` **1개뿐**(+16/-3). 단언 3줄이 교체됐다:

```diff
-        self.assertEqual(jobs[0].liveness, "working")
+        self.assertEqual(jobs[0]._proc_liveness, "working")     # tier-2 증거로 흡수됨
+        self.assertEqual(dispatch._dispatch_liveness(jobs[0], now=0), "working")
+        self.assertEqual(jobs[0].state_evidence["tier"], 2)
```
```diff
-        self.assertEqual(registry.liveness, "working")
+        self.assertEqual(registry._proc_liveness, "working")
+        self.assertEqual(dispatch._dispatch_liveness(registry, now=0), "working")
```

**Verdict:** PASS — **약화 아님, 강화**.
- 교체가 **불가피**하다: F-25가 `dispatch.py:924`의 `r.liveness = p.liveness` 대입을 제거했으므로(재배치 가드 대상) `_reconcile_drill_rows` 직후의 `.liveness`는 더 이상 존재하지 않는다. 옛 단언은 사라진 코드를 겨눈다.
- 교체 후가 **더 강하다**: 옛 단언 1줄(`liveness == "working"`) → 새 단언 3줄(증거 흡수 + **분류기 종단 통과** + tier=2 고정). 같은 행동(live proc = ground truth)을 더 좁게 고정한다.
- **통과시키려 느슨하게 만든 단언은 발견되지 않았다.**

---

## Level 2 — 렌더 실측 (실제 출력 관찰)

### Test 2.1: F-22 name zone 폭 독립 측정

**Command:**
```bash
python3 -c "import sys; sys.path.insert(0,'tools'); from fleet import render; \
print({w: render._wide_name_width(w) for w in (60,120,168,200)})"
```

**Output:**
```
현재      : {60: 28, 120: 29, 168: 40, 200: 40}
베이스라인: {60: 28, 120: 29, 168: 77, 200: 109}
_wide_name_width(None) == 28 | _NW_S = 28 | _NAME_WIDE_MAX = 40 | _TITLE_MAX = 24
```

**Verdict:** PASS — execute 주장 `{60:28,120:29,168:40,200:40}`와 **완전 일치**. execute의 "was `168:77, 200:109`" 주장도 **베이스라인 실측으로 독립 확인**. 60/120 불변, 168·200만 상한 적용. `None` → `_NW_S` 레거시 경로 보존.

### Test 2.2: 실제 렌더 출력 — 60 / 120 / 168 (관찰함)

**Command:** `for w in 60 120 168; do COLUMNS=$w python3 tools/fleet/fleet.py --once; done`

**Output (COLUMNS=168, 발췌):**
```
  usage claude code   5h [━━──────────  16%]   7d [━━━━────────  32%]
        codex         7d [━━──────────  13%] ↻ 6d16h
  fleet ⠙ 2 working   ● 7 idle   ↳ 2 jobs (2 working)
  🧠 mem  +54 added(21w·33d) · 24 expired · 5 pruned · last distill 0m
  alert ⚠ 2 ctx-high jobs: agent_setting·personal_homepage
─────

    harness         session                                 branch        model                      context / stage   time

● agent-note/  tracked
▍ ⠙ codex           방금 논의사항 바로 파악해서 작… tracked main          gpt-5.6-sol (xhigh)        ━━━━━───────────  33%       4m
▍ ● claude code     Connection indicator semantic … tracked main          Fable 5 (xhigh)            ━━━━━━━━────────  52%    7h21m

● agent_setting/ 🚧 4  tracked
▍ ⠙ codex           Codex wrapper PID and liveness tracked  main          gpt-5.6-sol (xhigh)        ━━━━━━━━━━━━━━──  85%    1h19m
▍ ● claude code     Fleet spec F-29: sub-agent … ▾2 tracked main          Fable 5 (xhigh)            ━━━━━───────────  30%    4h03m
▍ ↳ ⠙ claude code   fleet-v8-reliability                    fleet-v8-reli opus (high)                dev·std/conductor/qa:~std  code: plan✓ › exec✓ › test        —
▍     ⠙ claude code test fleet-v8-test                      fleet-v8-reli opus (high)                dev·std/test/qa:~std  running        —
▍ ● claude code     Fix codex dispatch liveness de… tracked main          Fable 5 (xhigh)            ━━━━━───────────  29%    2h24m
▍ ● codex           방금 논의사항 바로 파악해서 작… tracked main          gpt-5.6-sol (xhigh)        ────────────────   2%    1h29m

● personal_homepage/ 🚧 1  ✓ 14m  tracked
▍ ● codex           Homepage deployment and profil… tracked main          gpt-5.6-sol (xhigh)        ━━━━━━━━━━━━━━──  90%    1h03m

● SR_CorrNet_DSC/ 🚧 1  ✓ 22m  tracked
▍ ● claude code     M3_3 M4_1 SNR robustness epoch… tracked main          Fable 5 (xhigh)            ━━━━━━━━────────  53%    7h26m
▍ ● codex           Polish report text with correc… tracked main          gpt-5.6-sol (xhigh)        ━━━━━━━━━━━─────  71%    6h47m

  +2 malformed jobs.log rows skipped

  ⠹ working   ● idle   ▾N child jobs   ↳ dispatch   🚧 N worktrees   🧠 0 mem   ~ derived/inherited value
```

**Output (COLUMNS=120, 발췌):**
```
  SESSIONS   narrow · press w to cycle

● agent-note/  tracked
▍ ⠋ codex           방금 논의사항 바로 파악해서 작업 착수해줘. tracked  main
▍   4m              gpt-5.6-sol (xhigh)    [━━━━────────  33%]
▍ ● claude code     Connection indicator semantic decomposition tracked  main
▍   7h21m           Fable 5 (xhigh)        [━━━━━━──────  52%]
```

**Output (COLUMNS=60, 발췌):**
```
  SESSIONS   stack · press w to cycle

● agent-note/  tracked
▍ ⠹ codex           방금 논의사항 바로 … tracked  main
▍   4m              gpt-5.6-sol (xhigh)
▍                   [━━━━────────  33%]
```

**Verdict:** PASS — 3폭 전부 실제 관찰. 168에서 세션 제목이 **40열에서 멈추고** branch/model/context/time 정렬 유지. dispatch 이름은 24열 compact 유지. **`unused`(`◌`) 행은 3폭 어디에도 없다** — 유령 pid 1168514가 자연 종료해 현재 unused 행이 존재하지 않기 때문(Test 4.3 참조). 이 축은 캡처로 검증 불가.

### Test 2.3: 행 폭 하드 가드 — 베이스라인 대조 (★ 발견 있음)

**Command:** 플랜 §5 검증 #4의 가드를 현재/베이스라인 양쪽에 적용

**Output:**
```
현재      : width 60 → over-limit lines = 5 | width 120 → 0 | width 168 → 0
베이스라인: width 60 → over-limit lines = 5 | width 120 → 0 | width 168 → 2
```

초과 행(60폭):
```
OVER line=0  dw=61 (+1):  '  usage claude code   5h [━───────  16%]   7d [━━━─────  32%]'
OVER line=3  dw=70 (+10): '  🧠 mem  +54 added(21w·33d) · 24 expired · 5 pruned · last distill 1m'
OVER line=22 dw=74 (+14): '▍   —               opus (high)                dev·std/conductor/qa:~s'
OVER line=25 dw=69 (+9):  '▍   —               opus (high)                dev·std/test/qa:~std  '
OVER line=52 dw=105 (+45):'  ⠹ working   ● idle   ▾N child jobs   ↳ dispatch   🚧 N worktrees …'
```

**Verdict:** PASS (본 사이클 기준) — 60폭 초과 5건은 **베이스라인에 동일하게 존재하는 기존 결함**이며 본 변경과 무관하다. 오히려 168은 **2건 → 0건으로 개선**됐다(F-22 상한의 부수 효과).

> **다만 플랜 §9 완료 기준의 "60/120/168 경계 초과 0"은 60폭에서 미충족**이다. 원인은 F-22가 아니라 (a) legend/mem/usage 요약 행이 60폭에서 축약되지 않음, (b) dispatch stack 행의 `dev·std/…` 메타가 예산을 넘김. **기존 결함이므로 본 사이클의 블로커로 올리지 않되, 별도 이슈로 기록한다**(§ 발견 D3).

---

## Level 3 — `--json` 스키마 (additive 검증)

### Test 3.1: 베이스라인 스키마 대조 — 삭제·개명 0

**Command:** 현재/베이스라인 양쪽 `--json` 산출의 키 집합 대조

**Output:**
```
=== TOP-LEVEL keys ===   base: [jobs, memory, sessions, summary]   new: 동일
removed: NONE | added: NONE

=== sessions row schema ===
  removed from base: NONE
  added in new     : ['kind', 'proc_start', 'provenance', 'registry_name',
                      'registry_proc_start', 'started_at', 'state_evidence',
                      'updated_at']
=== jobs row schema ===
  removed from base: NONE
  added in new     : ['proc_start', 'state_evidence']

=== state_evidence presence ===
total rows: 13 | with state_evidence: 13 | missing key entirely: 0
```

**Verdict:** PASS — **additive only**. 기존 필드 삭제 0, 개명 0. 전 행에 `state_evidence` 존재.

### Test 3.2: ★ 주장된 tier가 분류기의 실제 판정과 맞는가 — 실 라이브 행 교차 검증

`state_evidence`가 자기 tier를 **스스로 주장**하는 것만으로는 검증이 아니다. 주장된 tier-1 행이 **진짜 registry 파일을 갖고 그 status를 갖는지**, tier-3 행이 **진짜 registry status가 없는지**를 파일시스템에서 직접 대조했다.

**Output:**
```
=== live rows: evidence vs rendered liveness ===
pid=113926   idle     tier=1 derived=False src=claude-registry   rule: registry status=idle
pid=133694   idle     tier=1 derived=False src=claude-registry   rule: registry status=idle
pid=1680590  idle     tier=1 derived=False src=claude-registry   rule: registry status=shell
pid=2166367  idle     tier=3 derived=True  src=mtime             rule: no activity within 60s
pid=2220685  idle     tier=3 derived=True  src=mtime             rule: no activity within 60s
pid=2297657  working  tier=3 derived=True  src=mtime             rule: activity within 60s
pid=2426760  idle     tier=3 derived=True  src=mtime             rule: no activity within 60s
pid=2582399  working  tier=3 derived=True  src=mtime             rule: activity within 60s
pid=2595285  working  tier=3 derived=True  src=mtime             rule: activity within 60s
pid=2639227  working  tier=3 derived=True  src=mtime             rule: activity within 60s
tier 분포: {1: 3, 2: 0, 3: 7}   invariant violations: 0

=== 파일시스템 교차 대조 ===
pid 113926 : ~/.claude/sessions/113926.json  status='idle'  name='sr-corrnet-dsc-3f'   → tier-1 주장 참
pid 133694 : ~/.claude/sessions/133694.json  status='idle'  name='agent-note-64'       → tier-1 주장 참
pid 1680590: ~/.claude/sessions/1680590.json status='shell' name='agent-setting-12'    → tier-1 주장 참
pid 2166367: registry 파일 존재하나 status=None(부재)  → 분류기가 tier-3으로 degrade   → 주장 참
pid 2297657: registry 파일 없음                        → tier-3(mtime)                  → 주장 참
pid 2582399: registry 파일 없음                        → tier-3(mtime)                  → 주장 참
```

**Verdict:** PASS — **주장된 소스 tier가 실제 분류 근거와 1:1로 일치**. 불변식 `ev.state == row.liveness`, `derived ⇔ tier==3` 위반 0.

> **부수 확인 (가치 있음)**: pid 2166367은 registry 파일이 **존재하지만 `status` 키가 없다**. 분류기가 크래시 없이 tier-3으로 degrade했다 — 픽스처 `registry_fresh_no_status.json`이 고정한 tolerate 경로가 **야생에서 실제로 작동 중**임을 우연히 실증했다.
>
> **부수 확인 2**: tier-1 `idle` 3행의 `activity_ms`는 각각 22,220,614ms / 23,924,255ms / 13,051,870ms — 전부 `UNUSED_ACTIVITY_MS`(2000)를 압도적으로 초과. `unused` 정제가 **과도하게 넓지 않음**을 실 데이터가 확인한다(오탐 0).

---

## Level 4 — F-25 우선순위 불변식 적대적 검증 (★ 발견 있음)

플랜 §2.1 불변식: **"하위 소스는 상위 소스와 모순될 때 절대 이기지 못한다."**
이 불변식을 **깨려고** 시도했다.

### Test 4.1: §2.2 축 분리 — 규범대로 동작하는가

**Output:**
```
ghost (idle, no transcript, 119ms)        -> unused  tier=1 src=claude-registry  ✅ MATCHES
    rule: idle refined to unused (no transcript, updatedAt≈startedAt)
busy + no transcript + 119ms              -> working tier=1 src=claude-registry  ✅ MATCHES (축 위반 가드 작동)
```

**Verdict:** PASS — registry가 `idle`을 주장하는데 행은 `unused`로 렌더되는 **§2.2 축 분리 케이스가 규범대로 성립**. `busy`는 `unused`로 좁혀지지 않는다(축 가드).

### Test 4.2: 하위 tier가 상위를 이기게 만들 수 있는가 — 공격 시도

**Output:**
```
=== tier-3 mtime만으로 unused를 주조하려는 시도 (반드시 실패해야) ===
no status, no transcript, activity_ms absent          -> idle tier=3  ✅ 방어됨
no status + activity_ms=1 (tier-3 forged unused)      -> idle tier=3  ✅ 방어됨
        → `_is_unused`가 `st == "idle"`을 요구하고 `st`는 registry status에서만 나온다. tier-3은 unused를 주조 못 함.

=== 존재 축이 registry를 이기는 케이스 (이건 이겨야 정상) ===
status=busy + pid dead              -> dead  tier=2 ✅  rule: pid not alive
status=busy + start-time mismatch   -> dead  tier=2 ✅  rule: start-time mismatch (pid reuse) — registry evidence discarded
status=busy + orphan cwd            -> stale tier=2 ✅  rule: orphan cwd (deleted worktree)
```

**Verdict:** PASS — 하위가 상위를 이기게 만드는 데 **실패했다**(= 불변식이 방어됨). 존재 축(tier-2)이 registry를 종결하는 것은 §2.3 표가 명시한 의도된 동작.

### Test 4.3: ★★ 공격 성공 — tier-3 mtime이 tier-1 registry `busy`를 이긴다

**Command:**
```python
model.classify_session(dict(pid_alive=True, status="busy", mtime=now-49*3600, transcript=True), now)
```

**Output:**
```
status=busy + mtime 49h old   -> stale  tier=3  src=mtime
    rule: no activity for > 2880 min
```

**Verdict:** **★ 발견 D1 — 플랜 §2.3 규범 표가 커버하지 않는 tier 역전.**

- registry가 tier-1으로 `busy`("지금 모델이 돌고 있다")를 **명시 선언**하는데, tier-3 mtime 휴리스틱이 이를 **덮고** `stale`을 emit한다. `state_evidence` 자신이 `tier=3, source=mtime`이라고 정직하게 보고하므로 **은폐는 없다**.
- 원인: `classify_session`의 `age_min > stale_min` 분기가 registry status 검사(`if st:`)보다 **앞에** 있다(`model.py`, `# Inactivity-history axis` 주석 블록).
- 코드는 이를 §2.2 축 분리로 정당화한다("Inactivity-history axis (§2.2, same axis as unused)"). **그러나 §2.2는 무활동 이력 축의 소유자를 "registry `startedAt`/`updatedAt` + transcript 부재"로 명시했지 mtime이 아니다.** 오히려 §2.2는 **"3순위 mtime만으로 `unused`를 만들지 않는다(registry 증거 필수)"**를 금지 규칙으로 못박았는데, 이 stale 경로는 정확히 **mtime 단독**으로 tier-1을 덮는다.
- **§2.3 표에 이 행이 없다**: 표의 `stale`은 registry status가 **`(부재)`**일 때만 나온다. `busy + mtime>48h` 조합에 대응하는 규범 행이 존재하지 않는다.
- **동기**는 정당하다: 코드 주석의 "Preserves the pre-F-25 ordering — status never rescued a 48h-silent row"는 사실이고, 48시간 침묵한 세션을 `working`으로 표시하는 것이 더 나쁘다. **행동 자체는 옹호 가능**하다.
- **성격**: 코드가 옳고 **플랜의 규범 표가 불완전**하다. 코드 수정이 아니라 **§2.3 표에 행 1개 추가 + §2.2 축 소유자 문구 정정**이 올바른 해소다.
- **테스트 공백**: `test_f25_state_model.py`의 33개 테스트 중 이 케이스를 고정하는 것이 **없다**(`grep "SESSION_STALE_MIN"` → 상수 이중화 검사 1건뿐). 픽스처 목록에도 없다. 규범 미기재 + 테스트 미고정이 겹쳐 **아무도 이 tier 역전을 알지 못한 채 착륙**하려던 상태였다.

### Test 4.4: ★★ 파생 발견 — 유령 세션은 48시간 후 다시 안 보이게 된다

**Command:**
```python
model.classify_session(dict(pid_alive=True, status="idle", mtime=now-49*3600,
                           transcript=False, activity_ms=119), now)
```

**Output:**
```
status=idle, no transcript, 119ms, mtime 49h old  -> stale  tier=3  src=mtime
```

기본 가시성 필터(`render.py:1670`):
```python
shown = (group_sessions if _SHOW_ALL else
         [s for s in group_sessions
          if not (s.liveness in ("stale", "dead") or s.app_server)])
```

**Verdict:** **★ 발견 D2 — F-26의 목적이 48시간 후 자동 무력화된다.**

- 유령 세션은 transcript가 없으므로 `claude.py`가 mtime을 `statusUpdatedAt`(= 시작 시각)으로 채운다(플랜 §1.2에 기재된 기존 동작). 따라서 **유령의 mtime = 유령이 태어난 시각**이며 유령이 존재하는 동안 **영원히 갱신되지 않는다**.
- 유령이 48시간을 넘기는 순간 `age_min > stale_min` → `stale`(tier-3). `unused`는 기본 노출이지만 **`stale`은 기본 숨김**이다.
- 결과: 유령은 처음 48시간만 `◌ unused`로 보이고, **그 후 대시보드에서 사라진다** — F-26이 해소하려던 상태(prd.md:248 "어디서도 인지 불가")로 **자동 복귀**한다.
- **이것이 사소하지 않은 이유**: 유령은 정의상 **아무도 안 쓰는 세션**이다. 오래 살아남는 것이 유령의 본질이다. 48시간 커트오프는 **가장 오래되고 가장 정리가 필요한 유령을 정확히 골라 숨긴다.** F-27 kill의 1순위 대상이 F-26의 시야에서 사라지는 구조다.
- **실측된 유령(pid 1168514)이 acceptance를 통과한 것은 4h05m 시점이었기 때문**이다. execute의 acceptance는 정직하고 재현 가능하지만, **시간 의존적**이며 49시간째에는 통과하지 않는다.
- **성격**: D1과 동일 코드 분기가 원인. 설계 판단이 필요한 사안이며(유령의 `unused`는 48h를 넘어서도 유지돼야 하는가?), **본 검증자가 결정할 것이 아니라 사용자/spec 결정 자리**다.

---

## Level 5 — F-27 안전 재측정 (★ 안전 규율 준수)

> **안전 (하드)**: 본 스테이지는 자가 생성한 `sleep` 픽스처 프로세스에만 시그널을 보냈다. **실제 claude/codex 세션은 단 하나도 spawn하지 않았고 signal하지 않았다.**
>
> execute 워커는 이 규율을 위반해 실제 claude 세션을 spawn하고 SIGTERM했다(자진 보고). `plan.md:396-402`가 그 절차("새 유령 세션 생성 → … → fleet 자신의 `x` kill로 정리")를 **정상 절차로 규범화**하고 있으며 **이는 잘못됐다** — 발견 D5 참조.

### Test 5.1: start-time 불일치 거부 — 직접 재측정

**Command:** (전문)
```python
p = subprocess.Popen(["sleep", "300"])          # ← 자가 생성 픽스처. 실제 세션 아님.
real = control.read_proc_start(p.pid)
control.verify_target(p.pid, real)              # 대조군
control.verify_target(p.pid, str(int(real)+1))  # 위조
control.kill_target(p.pid, proc_start=str(int(real)+1), sid=None, state="unused", approval="single")
```

**Output:**
```
fixture pid: 2637902 | real proc_start: 5741667
verify_target(exact)  -> True   (expect True)   ✅
verify_target(forged) -> False  (expect False)  ✅
verify_reason(forged) -> start_time_mismatch                    ✅
kill_target(forged)   -> refused | fixture still alive: True    ✅ 거부된 대상이 실제로 살아남음
kill_target(no proc_start)            -> refused                ✅ (reason=no_proc_start — 위조와 구분됨)
kill_target(working session, single)  -> refused                ✅ 이중 확인 게이트
   fixture still alive: True                                    ✅
kill_target(exact, unused, single)    -> ok | exit rc: -15      ✅ 대조군 정상 종료(SIGTERM)

--- action log ---
{"ts":…, "action":"refused","pid":2637902,"state":"unused","approval":"single","result":"refused","reason":"start_time_mismatch"}
{"ts":…, "action":"refused","pid":2637902,"state":"unused","approval":"single","result":"refused","reason":"no_proc_start"}
{"ts":…, "action":"refused","pid":2637902,"state":"working","approval":"single","result":"refused","reason":"live_target_needs_double_confirm"}
{"ts":…, "action":"sigterm","pid":2637902,"state":"unused","approval":"single","result":"ok","reason":null}
```

**Verdict:** PASS — execute의 F-27(a) 주장(**위조 → 거부, 프로세스 생존 / 대조군 → ok, rc=-15**)을 **독립 재측정으로 확인**. 추가로 `no_proc_start`가 `start_time_mismatch`와 **구분되어 로깅**됨을 확인(감사 추적의 정직성 — 증거가 없었던 것을 PID 재사용 탐지로 위장하지 않는다).

### Test 5.2: 자동 제어 = 0 — 직접 재측정

**Command:**
```bash
FLEET_ACTION_STATE_DIR=/tmp/v8_auto_verify python3 tools/fleet/fleet.py --json > /dev/null
FLEET_ACTION_STATE_DIR=/tmp/v8_auto_verify COLUMNS=120 python3 tools/fleet/fleet.py --once > /dev/null
FLEET_ACTION_STATE_DIR=/tmp/v8_auto_verify COLUMNS=168 python3 tools/fleet/fleet.py --once > /dev/null
```

**Output:**
```
contents of /tmp/v8_auto_verify:  (비어 있음 — actions.jsonl 없음)
PASS: no action log created — automatic control count = 0

=== sys.modules probe after a --json render ===
modules matching 'control': (none)
```

**Verdict:** PASS — execute의 F-27(b) 주장 확인. 더 강하게: **`control` 모듈이 스냅샷 경로에서 import조차 되지 않는다**(런타임 probe로 실증). 정적 가드도 통과:
```
=== control importers OUTSIDE render.py and tests ===  (none — OK)
=== control importers (all) === render.py 6곳(전부 함수 내부 lazy import) + tests 1곳
```

### Test 5.3: 사용자 확인 없이 시그널 가능한 코드 경로 탐색

`control.kill_target`에 도달하는 **모든** 경로를 추적했다:
```
render.py:2406  _handle_prompt_key()  ← _PROMPT 활성 상태에서만, 그리고 ch == ord("Y") 요구(escalate)
render.py:2419  _do_kill()            ← _handle_prompt_key()에서만 호출
```
`_PROMPT`는 `_handle_select_key`의 `x` 키에서만 설정되고, `_SELECT_MODE`는 base mode의 `s`/`x` 키에서만 켜진다.

**Verdict:** PASS — **사용자 키 입력 없이 시그널에 도달하는 경로를 찾지 못했다.** `kill_target` 자신도 UI를 신뢰하지 않고 게이트를 독립 재검사한다(`is_excluded` → `single_confirm_allowed` → `verify_reason` 순, 전부 fail-closed). 방어가 2중이다.

> **부수**: `control.py`의 `is_excluded`는 **fleet 자신 + 전체 조상 계보 + 현재 구동 세션 + init + 해석 불가 입력**을 전부 배제하며 기본값이 **deny**다. `single_confirm_allowed`도 whitelist(미지 상태 → deny)다. 설계가 일관되게 fail-closed다.

### Test 5.4: `DispatchJob.proc_start` — execute가 발견·수정했다는 BLOCK의 실재 검증

execute 주장: `DispatchJob.proc_start`가 없어서 **모든 잡 kill이 거부**됐고 → prd.md:255 registry 마감이 **죽은 코드**였으며, 14개 parity 테스트는 함수를 직접 호출해 **통합 경로 커버리지가 0**이라 green이었다.

**Output:**
```
=== 필드 실재 ===
model.py:180  proc_start: Optional[str] = None    # /proc/<pid>/stat field 22 — the other half of the pid's identity

=== 실제 채워지는가 (통합 경로) ===
dispatch.py:760   proc_start=procscan.read_proc_start(pid_s) if pid_s.isdigit() else None
dispatch.py:796   proc_start=procscan.read_proc_start(pid_s) if pid_s.isdigit() else None
dispatch.py:956   r.proc_start = p.proc_start      # pid and its start-time travel together, always
dispatch.py:1021  j.proc_start = procscan.read_proc_start(pid)   # identity, not just a number

=== 통합 커버리지 신설 확인 ===
test_f27_control.py:744  def test_job_row_kill_actually_works_end_to_end(self)
test_f27_control.py:765  def test_dispatchjob_carries_proc_start(self)
test_f27_control.py:768  def test_proc_start_defaults_to_none(self)
test_f27_control.py:771  def test_reconcile_absorbs_proc_start_with_the_pid(self)
```

**Verdict:** PASS — **수정은 실재한다.** 필드가 존재하고, 수집 경로 **4곳**에서 실제로 채워지며(생성 2곳 + drill 병합 흡수 1곳 + 잡 enrich 1곳), 함수 직접 호출이 아닌 **종단 통합 테스트**(`test_job_row_kill_actually_works_end_to_end`)가 신설됐다. execute의 자진 보고가 정확하다.

### Test 5.5: F-25 재배치 가드

**Command:** `grep -rn "\.liveness = " tools/fleet/ --include='*.py' | grep -v tests/`

**Output:**
```
tools/fleet/collectors/__init__.py:149:            s.liveness = liveness.classify(s, now)
tools/fleet/collectors/dispatch.py:1030:        j.liveness = _dispatch_liveness(j, now)
count = 2 (expected 2)
```

**Verdict:** PASS — 대입 정확히 2곳, 둘 다 `classify_*` 위임. `dispatch.py:924`의 F-18a 흡수 대입이 예정대로 소멸했다. **독립 패치층 신설 0.**

> **★ 발견 D4 (사소)**: 플랜 §3 검증 #4의 가드 스크립트는 `--include=*.py`를 **인용하지 않는다**. 사용자의 셸은 **zsh**이고, zsh에서 이 스크립트는 `no matches found: --include=*.py`로 실패해 `N=0` → `test 0 -eq 2` → **가드가 항상 FAIL을 보고**한다. bash에서만 동작한다. 플랜의 자동 단언이 셸 의존적이다 — `--include='*.py'`로 인용 필요.

### Test 5.6: 미러 패리티

**Command:** `diff -r --exclude=__pycache__ tools/fleet/ adapters/claude/tools/fleet/`

**Output:** `(빈 출력)` → `IDENTICAL — mirror parity OK`

**Verdict:** PASS — canonical ↔ mirror **바이트 수준 완전 동일**. 변경 파일 전부 동기됨(신규 `control.py` + 픽스처 디렉토리 + 신규 테스트 4개 포함).

---

## Level 6 — F-27 `↑↓` 드리프트 판정 (알려진 미결 항목)

### Test 6.1: 스크롤 회귀가 진짜 0인가

**Command:** 현재/베이스라인 `_loop` 키 분기 대조

**Output (현재, `render.py:2591-2614`):**
```python
        if _SELECT_MODE:
            if _handle_select_key(ch):
                ...
                continue
        elif ch in (ord("s"), ord("S"), ord("x"), ord("X")):
            # Enter selection mode. `x` doubles as the enter shortcut …
            ...
            continue

        # --- base mode: scroll keys UNCHANGED (F-27 regression budget = 0) ---
        if ch in (curses.KEY_UP, ord("k")):
            _OFFSET -= 1
        elif ch in (curses.KEY_DOWN, ord("j")):
            _OFFSET += 1
        elif ch == curses.KEY_PPAGE:   _OFFSET -= body_h
        elif ch == curses.KEY_NPAGE:   _OFFSET += body_h
        elif ch in (curses.KEY_HOME, ord("g")):  _OFFSET = 0
        elif ch in (curses.KEY_END, ord("G")):   _OFFSET = 1 << 30
```

**Output (베이스라인, `render.py:2071-2080`):** 스크롤 블록이 **문자 단위로 동일**.

**Verdict:** PASS — **스크롤 회귀 = 0 (구조적으로 확인)**. `_SELECT_MODE`가 False인 한 `↑↓`는 select 핸들러를 거치지 않고 곧장 `_OFFSET`에 도달한다. select 모드 진입은 **오직** 명시적 `s`/`x` 키뿐이다.

**드리프트 판정: 블로커 아님 — 사용자 확인 후 수용 권고.**
- spec prd.md:252는 "`↑↓` 선택 모드 진입/이동"을 요구하나 구현은 `s`/`x` 진입 + `↑↓` 이동이다.
- **A안(`↑↓`=진입)을 채택하면 prd.md:80의 명시적 키 표 계약(`↑↓`=스크롤)과 prd.md:155의 v2 "항상 맨 아래까지 도달" 버그 수정 계약을 깨뜨린다.** 두 명시 계약 vs 조작 모델 절의 예시 표기 1건이 충돌할 때, 후자를 양보하는 것이 옳다.
- 구현은 spec F-27의 실질(선택 커서·`↑↓` 이동·`x` kill·확인 프롬프트)을 **전부** 지키고 "진입" 한 단어만 양보한다.
- **필요 조치**: 플랜 R1이 이미 `[decision: significant — 사용자 확인 자리]`로 표시했다. **spec §4.8 F-27 문구 sync가 후속 obligation으로 남는다**(prd.md:252 → "`s`/`x` 진입, `↑↓`/`jk` 이동").

**★ 발견 D6 (사소)**: "스크롤 회귀 예산 = 0"이라는 계약을 **고정하는 테스트가 없다**. `test_f27_control.py` 68개 테스트 중 base mode에서 `↑↓`가 `_OFFSET`을 움직임을 단언하는 것이 없다(`KEY_UP`은 select-mode 커서 이동 테스트에서만 등장). 회귀 0 보증이 **코드 검사에만** 의존한다 — 누군가 `_SELECT_MODE` 게이트를 잘못 건드리면 조용히 깨진다.

### Test 6.2: 새 키 바인딩의 부수 효과

베이스라인에서 `s`/`x`는 **미바인딩**(무시)이었다. 이제 select 모드로 진입한다. 스크롤 회귀는 아니나 **기존 무동작 키에 동작이 생긴** 변화다. `x`가 첫 입력에서 kill하지 않고 선택만 하는 것은 확인됨(`test_x_from_base_mode_selects_and_does_not_kill`).

**Verdict:** PASS — 안전 측면 문제 없음.

---

## Level 7 — 디자인팀 critic (독립 패스)

execute의 critic 재독이 아니라, **본 검증자가 실측한 3폭 출력**(`/tmp/v8_test_{60,120,168}.txt`)에 대해 `디자인팀` critic 모드를 **read-only**로 새로 dispatch했다.

**verdict 및 처분**: `_internal/test_reviews/design_critic_independent.md` 참조.

---

## 헤드리스로 검증 불가능한 것 (정직한 한계)

1. **라이브 TUI 눈 검사** — TTY가 없어 `curses` 루프를 실제로 구동하지 못했다. 검증된 것은 **헬퍼 수준**(`_handle_select_key`/`_handle_prompt_key`/`_prompt_segs`/`_footer_segs`를 직접 호출하는 68개 테스트)과 **비-curses 스냅샷 출력**(`--once`)뿐이다.
   - **테스트가 실제로 덮는 것**: 키 분기 로직, 커서 identity 앵커링·클램프·재앵커, 프롬프트 문구가 60/120/168에서 잘리지 않음, 이중 확인 키 요구, grace 만료 시 재프롬프트.
   - **오직 실제 터미널의 사람만 잡을 수 있는 것**:
     - 커서 하이라이트(`reverse` 속성)가 실제 터미널 테마에서 **읽히는가** — 특히 dim yellow `◌` 행 위에 reverse가 겹칠 때 대비가 무너지지 않는가.
     - 확인 프롬프트가 뜬 순간의 **깜빡임/재그리기 아티팩트**.
     - 커서 뷰포트 추종이 **체감상** 자연스러운가(클램프 로직은 테스트됐으나 스크롤 점프의 어지러움은 아님).
     - `◌` 글리프가 **실제 폰트**에서 `○`/`●`와 구분되는가 — 폰트에 U+25CC가 없으면 tofu(`□`)로 렌더된다. 이건 **실제 위험**이며 캡처로도 잡히지 않는다.
     - SIGTERM 후 행이 사라지는 **타이밍**이 사용자에게 "먹혔다"고 읽히는가.
2. **`unused` 행의 실제 렌더** — 유령 pid 1168514가 자연 종료했고 registry 파일도 사라졌다(`ls ~/.claude/sessions/1168514.json` → No such file, `ps -p 1168514` → 없음). **재측정 불가**이며, 지시대로 되살리지 않았다. 분류기 축은 픽스처/`--json`으로 검증했고 dev log의 증거 일관성은 확인했다(아래).
3. **execute의 F-26 live acceptance 내부 일관성** — 재현 불가하므로 **문서 정합성만** 검증:
   - dev log의 `activity_ms=119` ↔ 플랜 §1.2 실측 `updatedAt - startedAt = 119ms` **일치**.
   - dev log의 `procStart:"3918896"` ↔ 플랜 §1.2 registry 덤프 `"procStart":"3918896"` **일치**.
   - dev log의 `tier=1, derived=false, source=claude-registry, rule="idle refined to unused…"` ↔ 본 검증자가 **동형 픽스처로 재현한 분류기 출력과 문자열까지 일치**(Test 4.1).
   - 시각: 유령 시작 `Wed Jul 15 11:39:47`, 배지 `4h05m` → 측정 시각 ≈ 15:44:47. step_02 dev log 파일 mtime 15:52. **모순 없음.**
   - → **내부적으로 일관되며 조작의 흔적이 없다.** 다만 이 acceptance는 **시간 의존적**이다(발견 D2).
</content>
</invoke>
