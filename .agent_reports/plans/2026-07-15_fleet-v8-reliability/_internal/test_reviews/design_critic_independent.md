# 디자인팀 critic — 독립 렌더 비평 (code-test 스테이지)

- **성격**: execute 스테이지 critic(`_internal/dev_reviews/design_critic_step{2,4}.md`)의 재독이 **아니다**. 본 검증자가 직접 실측한 3폭 출력에 대한 **독립 패스**다.
- **입력**: `/tmp/v8_test_60.txt` · `/tmp/v8_test_120.txt` · `/tmp/v8_test_168.txt` (본 스테이지가 `COLUMNS=$w python3 tools/fleet/fleet.py --once`로 실측)
- **모드**: critic (read-only). **소스 수정 0건** — critic은 소스를 읽지도 않았고 렌더 캡처만 검사했다.
- **verdict**: **조건부 합격**

---

## critic verdict 요약

**F-22 40열 상한은 설계 판단으로 옳고 되돌릴 이유가 없다.** 168열에서 그리드가 헤더까지 정렬되고(branch@60 · model@74 · context/stage@101 전 행 일치), 세션 행 우측 edge가 131로 통일됐다.

**조건 1건**: **stage zone에도 대칭 상한을 걸어 131 edge에 맞출 것.**

## 축별 지적

### 🟢 확인된 강점
- 168열 그리드가 헤더까지 display-cell 단위로 정렬. dispatch 행도 동일 그리드에 앉는다.
- 세션 행 우측 끝 131로 완전 통일(8개 행 전부).
- `tracked` 배지가 name zone 끝(≈59)에 우측 정렬 — 제목 길이와 무관하게 배지 열이 안정.

### 🔴 조건 (blocking for the critic's pass)
- **stage zone이 무제한이라 168 무오버플로가 "운"이다.**

### 🟡 보완
- 우측 여백 131→168(37열)은 그 자체로 정당(제목 40열 제한은 시선 도약을 줄이는 올바른 판단 — 산문 max-width 65–75ch와 같은 논리). 문제는 세션 행이 131에서 끝나는데 dispatch 행만 139·163까지 뻗어 **ragged edge**가 된다는 것. F-22가 131에 선명한 edge를 만든 탓에 **기존 dispatch raggedness가 더 도드라졌다**(변경이 만든 문제가 아니라 드러낸 문제).
- **CJK 제목의 실효 예산은 40이 아니라 ~29열 = 한글 14–15자.** 40은 배지 포함 zone 폭이고 ` tracked`(8) + ` ▾2`(3)가 우측을 먹는다. 한국어는 SOV라 **동사가 항상 끝에 있고 항상 잘린다** — `방금 논의사항 바로 파악해서 작…`에서 사라진 것은 서술어 `작업 착수해줘`, 즉 **행위 그 자체**. 영어 제목은 명사구가 앞에 실려 head-truncation이 관대하다(`Fleet spec F-29: …`는 식별자가 살아 있어 충분). **단 이는 40이 좁아서가 아니라 잘림 방향 문제** — 77이어도 SOV 꼬리는 동일 위험이므로 **40 상한 자체는 유지 권고**.
- `time` 헤더 라벨만 좌측 정렬(@119)인데 데이터는 우측 정렬(끝 131) — 라벨이 자기 데이터보다 7열 왼쪽에 뜬다. 다른 5개 zone은 라벨/데이터 시작이 일치.

### ⚪ 비평 불가 (critic이 명시)
- **F-26 `◌` unused 배지는 3폭 캡처 전부에서 검증 불가.** `grep` 확인 결과 `◌` 0건, `unused` 0건. 유령 세션이 없어 글리프 렌더·배지 폭·name zone 예산 잠식 어느 것도 확인 못 했다. 특히 `unused <경과>` 배지가 `tracked`(8열)보다 길어질 때 제목 예산이 얼마나 남는지가 **미확인 리스크**.

---

## 본 검증자의 처분

### ✅ 채택 — critic의 🔴 조건은 **독립 실측으로 확인됨**

critic의 핵심 주장("5열 여유의 운")을 본 검증자가 직접 재측정했다:

```
=== 168열 캡처의 최장 행 ===
  line=15  width=163  slack=5    '▍ ↳ ⠏ claude code   fleet-v8-reliability …'   ← dispatch conductor 행
  line=16  width=139  slack=29   '▍     ⠏ claude code test fleet-v8-test …'     ← dispatch 하위 행
  line=26  width=131  slack=37   '▍ ● codex           Polish report text …'     ← 세션 행
  line=25  width=131  slack=37
  line=22  width=131  slack=37

=== 상한 상수 존재 여부 ===
render.py:523  _NAME_WIDE_MAX = 40        ← name zone 상한 (F-22 minor, 신설)
render.py:871  _DISPATCH_NAME_MAX = 18    ← dispatch **이름** 상한
→ stage/meta suffix(`dev·std/conductor/qa:~std  code: plan✓ › exec✓ › test`)를 묶는 상수는 **없다**.
```

**critic이 옳다.** 168 무오버플로는 구조적 보장이 아니라 **5열 여유의 우연**이다. stage zone은 상한이 없으므로 conductor/qa 라벨이 6열 길어지거나 stage가 `test✓ › report`로 진행하면 **168에서 다시 터진다**.

이는 본 검증자가 Level 2.3에서 관측한 사실들을 **하나의 원인으로 통합한다**:
- 168 오버플로 베이스라인 2건 → 현재 0건의 **개선은 실재하나 부수적(incidental)** 이다. F-22가 name을 77→40으로 깎아 dispatch 행을 우연히 168 안으로 끌어들인 것이지, stage zone을 고친 게 아니다.
- **60폭 오버플로 5건 중 2건(line 23 +14, line 26 +9)이 정확히 같은 stage zone**이 원인이다. 같은 뿌리가 좁은 폭에서 이미 증상을 내고 있다.

### 처분: **본 사이클의 블로커 아님 — 후속 이슈로 분리**

- stage zone 무상한은 **베이스라인에도 존재하는 기존 결함**이며 F-22 minor(prd.md:218)의 스코프는 명시적으로 **name zone**이다. 본 사이클이 도입한 회귀가 아니다.
- 오히려 본 사이클은 이 축에서 **순개선**(168: 2건 → 0건)을 냈다.
- 다만 **개선의 성격을 정직하게 기록해야 한다**: "168 오버플로 0"을 **구조적 보장으로 보고해서는 안 된다**. 5열 여유에 의존하는 상태다.
- → **발견 D3에 통합**하여 후속 이슈로 기록(§ test_review).

### 🟡 처분
- **CJK 중간 생략 제안**: 채택하지 않음(본 사이클 스코프 밖 — 제목 생성/클립 정책 변경은 F-22 minor가 아니다). 단 critic의 **"40 상한 자체는 유지"** 결론에 동의하며, 이는 F-22 acceptance를 지지한다. 후속 검토 대상으로 기록.
- **`time` 헤더 라벨 정렬**: 기존 결함(베이스라인 동일), 본 사이클 무관. 사소하여 기록만.

### ⚪ 처분 — critic의 "F-26 비평 불가"는 **본 검증자의 한계와 정확히 일치**
유령 pid 1168514가 자연 종료해 `unused` 행이 존재하지 않는다. critic도 본 검증자도 `◌` 렌더를 **캡처로 검증하지 못했다**. execute의 step_02 dev log는 유령 생존 시점(4h05m)에 실측한 `◌ claude code  agent-setting-17 unused 4h05m tracked` 출력을 담고 있고 그 증거는 내부적으로 일관되나(test_report.md § 한계 3), **본 스테이지가 독립 재현하지는 못했다.**

critic이 지적한 미확인 리스크(`unused <경과>` 배지가 `tracked`보다 길어 name 예산을 더 잠식)는 execute의 step_02 dev log D6 항목이 "이름이 굶을 때만 축약하는 규칙"으로 다뤘다고 기록하고 있으나, **본 검증자는 이를 실물 렌더로 확인하지 못했다.** → 미검증 항목으로 명시.
</content>
