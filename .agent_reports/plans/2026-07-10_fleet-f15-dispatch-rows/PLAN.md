# F-15 · F-16 구현 계획 — 분사 row 재설계(탈가로화·옵션 1급·workflow-first) + 세션 표시명 짧게

- **사이클**: 2026-07-10 fleet-f15-dispatch-rows
- **스코프**: 표시층(render.py) + collector 매칭·liveness 유도(collectors/dispatch.py). collector **공개 필드 계약 불변**(추가만 additive), `--json` additive only, jobs.log/statusline/registry write 0.
- **근거 문서**: `.agent_reports/spec/agent-fleet-dashboard/prd.md` §4.6 **F-15·F-16**(prd.md:178–185), §4.5 SD-F1~F4, §7 liveness. within-spec 구현.
- **선행 사이클**: F-14(세션 title), fleet-ui-v2(v2 UI). F-14 불변식(title additive·slug 무접촉·alert=slug) 유지.

---

## 0. 목표와 스코프

사용자 F-14 출하 후 최대 불만 = "분사 세션 행이 옵션과 함께 **가로로 쭉 늘어짐**". 단 옵션(capability·mode·qa·intensity·model·effort)은 **숨기지 말고 더 잘 설계**하라가 명시 요구.

네 갈래(전부 spec §4.6):
1. **F-15a 탈가로화 + 옵션 1급**: 분사 row 1차 라인 = 정체성(단계 라벨·slug·glyph·경과)만. 옵션은 **정렬된 자리**로 — wide=고정 컬럼, narrow/stack=2줄 카드 L2 dim 옵션 라인.
2. **F-15b workflow-first done-folding**: depth-1 conductor 의 **done·queued 스테이지 자식 row 는 접어** conductor breadcrumb 하이라이트로 흡수. **working·실패(stale/dead) 자식만** 별도 row 유지 → 잡 다수 시 세로 폭증 억제.
3. **F-15c queued 오라벨 해소**: registry-only row 가 실작업 중이면 breadcrumb 을 라이브로(working), queued 는 _진짜 미기동_(등록 후 transcript 무활동)만. proc-job ↔ registry row **dedup 키 정합**(slug-stem × cwd) 개선.
4. **F-16 세션 표시명 짧게**: name zone title 예산 타이트(≈24 display cols, tail-cut·head 보존). 전체 제목은 `--json`. (영어화는 하네스 title 설정 몫 — 본 스코프 밖.)

---

## 1. 디자인팀 critic plan-review — verdict 요약(embed)

**Verdict: SHIP-WITH-FIXES**. 네 축(컬럼 정렬화·L2 강등·done-folding·registry 라이브 breadcrumb) 모두 원인을 정면으로 겨눔. 근본 재설계 불요. 아래 P0 3건을 반영해 목업을 개정했다(§2 는 post-critic 최종본).

**반영한 P0(코드 전 필수)**
- **P0-1 자식 breadcrumb 복제 제거**: depth-2 자식 row 는 부모 전체 파이프 breadcrumb 을 반복하지 않는다 — 자식 정체성은 **name-zone 단계 라벨**(`exec fleet-ui-v2`)이 전담, breadcrumb 슬롯은 자기 micro-status(`running`)/blank. 원 불평(중복·가로 sprawl) 재발 + 다색 noise 증폭 방지. (기존 코드가 자식에 `exec: <token>` 을 그려 단계 라벨이 name·breadcrumb 두 곳 중복 → 라벨을 name-zone 으로 단일화.)
- **P0-2 queued 자식도 folding**: queued 스테이지는 이미 conductor breadcrumb 의 future-dim 세그먼트로 존재 → 별도 row 불필요. row 유지 = **working + stale/dead** 만. stack 에서 절감 큼(9줄→6줄).
- **P0-3 110–138 dead-zone 제거**: wide 1-line 은 옵션 컬럼 탓 ≈138 cols 필요 → **2-line(narrow) 을 138 까지 확장**, single-line wide 는 ≥138 한정. 실터미널 ≤120 이 흔하므로 **2-line 카드가 주 레이아웃**, 138-wide 는 rare case.

**반영한 P1/P2**
- P1-4 `↳` 는 stage 자식(depth-2) 전용. top-level registry-only/orphan(docs-sync·old-migrate)은 conductor peer → 무-arrow indent2.
- P1-5 breadcrumb done 세그먼트에 `✓` 마커(`plan✓ › exec › test`) — folding "흡수·가시" 약속 노출(past-done vs future-pending 판독).
- P2-9 registry-only breadcrumb 진정성: docs-sync 는 **실제 track**(`live_stage`)을 그림, 템플릿 `code: plan›exec›test` 페인팅 금지(새 mislabel 방지).
- P2-11 dead row = `dead @<last-stage>`(time 컬럼 `2h` 와 중복인 "last seen 2h" 대체).
- P2-13 옵션 토큰 **통일**: conductor·자식 공히 `mode·qa:<lvl>·int:<lvl>`(intensity 비대칭 제거).

**보류(사용자 확인 자리 — 본 사이클 미적용, 커밋 전 노출)**
- ask-4 **옵션 default-elision**(qa:std·int:std 접고 비기본만): 폭 절감·sparse 스캔 이점 있으나 "옵션 숨기지 말라"와 상충 소지 → **본 사이클은 전량 표시(요구 존중)**, elision 은 후속 토글 후보로 기록.
- P2-12 group header `🚧` emoji 셀폭 불안정: F-15 스코프 밖(그룹 헤더, 별도 사이클).

---

## 2. 텍스트 목업 (post-critic 최종)

시나리오: conductor A `fleet-ui-v2`(working — plan 자식 done·folded, exec 자식 working, test 자식 queued·folded) / conductor B `auth-refactor`(working — plan·exec done·folded, test 자식 working) / registry-only working row `docs-sync`(과거 queued 오라벨) / dead worker `old-migrate` / loop `drill`.

### 2.1 WIDE (≥138 cols) — 옵션 = model↔breadcrumb 사이 고정 컬럼, 1-line
```
    harness       session             branch      model             options              context / stage           time
● agent_setting/  🚧 2  tracked
  ⠹ claude        fleet-ui-v2         ⎇ f15-rows  Fable 5           dev·qa:std·int:std   plan✓ › exec › test        1h20m
    ↳ ⠹ claude    exec fleet-ui-v2    ⎇ f15-rows  Opus 4.8 (xhigh)  dev·qa:std·int:std   running                    18m
  ⠹ claude        auth-refactor       ⎇ auth      Fable 5           dev·qa:thr·int:std   plan✓ › exec✓ › test       3h05m
    ↳ ⠹ claude    test auth-refactor  ⎇ auth      Sonnet 5 (high)   dev·qa:thr·int:std   running                    7m
  ⠹ claude        docs-sync           ⎇ main      Opus 4.8          note·qa:light        search › analyze › report  44m
  ✕ claude        old-migrate         —           —                 —                    dead @exec                 2h
loops/
  ⠹ claude        drill               —           Haiku 4.5         —                    g14                        9h
```
- A: `plan✓`(자식 done → folded, breadcrumb 에 흡수) · `exec`(active → 자식 row 유지, micro-status `running`) · `test`(queued → folded, breadcrumb future-dim). 자식 3개 중 **1개만** row.
- B: `plan✓ exec✓`(folded) · `test`(active → 자식 row).
- docs-sync: registry-only 이나 transcript 활동 → **working + 자기 실제 track**(note/search›analyze›report), queued 아님. top-level peer → 무-arrow.
- old-migrate: dead → `dead @exec`(마지막 관측 stage), telemetry 셀 생략.
- 자식 breadcrumb 슬롯 = `running`(자기 micro-status) — 부모 파이프 복제 금지.

### 2.2 NARROW (70–138 cols) — 주 레이아웃, 2-line 카드, 옵션 L2 dim
```
● agent_setting/  🚧 2  tracked
  ⠹ claude      fleet-ui-v2                       ⎇ f15-rows
       1h20m    Fable 5           dev·qa:std·int:std   plan✓ › exec › test
    ↳ ⠹ claude  exec fleet-ui-v2                  ⎇ f15-rows
         18m    Opus 4.8 (xhigh)  dev·qa:std·int:std   running
  ⠹ claude      auth-refactor                     ⎇ auth
       3h05m    Fable 5           dev·qa:thr·int:std   plan✓ › exec✓ › test
    ↳ ⠹ claude  test auth-refactor                ⎇ auth
          7m    Sonnet 5 (high)   dev·qa:thr·int:std   running
```
- **L1 = 정체성만**(glyph · harness · [단계라벨] slug · branch). 기존 L1 `(mode·qa)` 괄호 태그 → L2 로 이동.
- **L2 = 경과 · model+effort · 옵션(dim mode·qa·int) · breadcrumb/micro-status**. 컬럼은 conductor·자식 공통 정렬(위계는 L1 indent+`↳` 로만; L2 무-nest).

### 2.3 STACK (<70 cols) — 3줄, 옵션은 L2 model 동행, breadcrumb L3
```
  ⠹ claude  fleet-ui-v2
       1h20m  Fable 5  dev·qa:std·int:std
              plan✓ › exec › test
    ↳ ⠹ claude  exec fleet-ui-v2
         18m  Opus 4.8 (xhigh)  dev·qa:std·int:std
              running
```
- L1 정체성 · L2 경과+model+옵션 · L3 breadcrumb(자식은 micro-status), model 아래 정렬.

---

## 3. 컬럼 예산 산정 (wide 옵션 정렬)

기존 상수(render.py): `_NAME_COL`=20(=4+`_HW`16) · `_BRANCH_COL`=48 · `_NW_S`=28(48−20) · `_BRW`=14(branch→col62) · `_MW`=23(model→col85). model 뒤 4-col gap→col89.

**신설 옵션 컬럼**(model↔breadcrumb):
```
col 89  옵션 컬럼(고정 _OPTW≈18, dim)   : "dev·qa:std·int:std"
col 107 2-col gap
col 109 breadcrumb "plan✓ › exec › test" (≈20; done 세그 ✓ 포함)
flush   경과 (~7)
→ conductor wide row 총폭 ≈ 136–138 cols
```
옵션 토큰 폭: mode(≤6 `design`) + `·` + `qa:`+lvl(short thr/adv/std/lt=3) + `·` + `int:`+lvl(3) ≈ `dev·qa:thr·int:std`=18. `_OPTW=18` 고정, 초과분은 컬럼 내 tail-cut(성분 드롭 아님 — 통일 포맷 유지).

**레이아웃 컷오프 변경(P0-3)**: `_TWO_LINE_CUTOFF` 110→**138**. `_layout_mode`: `<70` stack · `<138` narrow(2-line) · `else` wide(1-line). dead-zone 소멸, 2-line 이 주 레이아웃. 세션 row 도 같은 컷오프 공유 → <138 에서 2-line 카드(수용된 정책 이동, critic 권고).

---

## 4. dedup-키 정규화 (F-15c) — fleet-ui-v2 실측 mismatch

**증상**: proc job slug `fleet-ui-v2`(worktree basename 유도) vs registry slug `fleet-ui-v2-execute`(stage worker) 불일치 → 같은 세션이 **이중 표시** + registry row 가 static `queued` 노출.

**루트**: `collect()`(dispatch.py:799) 가 `seen = {j.slug for j in proc_jobs}`(순수 slug). `_scan_jobs_log`(dispatch.py:737) 는 `if slug in seen_slugs` 로만 skip → `fleet-ui-v2-execute` ∉ `{fleet-ui-v2}` → 미dedup.

**해소 — dedup 키 = (정규화 cwd, slug-stem)**:
- `_slug_stem(slug)` 헬퍼 신설: 말미 stage-role 접미 strip — `re.sub(r'-(?:code-)?(?:plan|exec|execute|test|report)$', '', slug)`. `fleet-ui-v2-execute`→`fleet-ui-v2`.
- `collect()`: `seen_keys = {(_norm_cwd(j.cwd), _slug_stem(j.slug)) for j in proc_jobs if j.cwd}` 추가(기존 slug set 은 fallback 유지 — 회귀 안전).
- `_scan_jobs_log`: skip 조건 = `slug in seen_slugs` **OR** `cwd and (_norm_cwd(cwd), _slug_stem(slug)) in seen_keys`.
- **핵심 안전판**: 키에 **cwd 포함** → conductor 와 그 depth-2 자식은 _서로 다른 worktree_ 에서 돌므로(OPERATIONS §5.10) cwd 불일치 → **dedup 되지 않고 둘 다 표시**(conductor + nested 자식 보존). 같은 worktree 에서 이중 카운트된 동일 워커만(위 실측 케이스) stem 일치+cwd 일치로 병합. proc row(live pid/model 보유)가 이김.

**계약 불변**: `_slug_stem` 은 표시/매칭 헬퍼일 뿐 `DispatchJob.slug` 값·의미 무변경. collector 공개 API·필드명 무접촉(§6 불변식).

---

## 5. queued 오라벨 해소 (F-15c) — 라이브 stage 유도 + 진짜 queued 분리

**(a) working registry row → 라이브 breadcrumb.** `_scan_jobs_log` 은 `stage=status`(raw open/running, dispatch.py:753). `collect()` liveness 루프(dispatch.py:843–845) 직후 추가:
```python
for j in jobs:
    if j.source == "jobs" and j.cwd and j.liveness == "working":
        j.stage = live_stage(j.cwd, j.slug, j.key)   # 실작업 → 실 progress breadcrumb
```
docs-sync 처럼 transcript 활동 있는 registry row 는 raw `queued` 대신 자기 track 을 그린다. `live_stage` 는 `_find_plan_dir` token-overlap fallback 이 있어 slug-stem mismatch 도 plan 폴더를 찾음. **key 가 미지 track 이면**(`_PIPE_STAGES` 밖) `_stage_segs` 가 단일 토큰만 → 템플릿 페인팅 없음(P2-9).

**(b) 진짜 queued = 미기동만.** registry `open` row 로 아직 transcript 부재 = 등록 직후 미기동. 현행 `_job_liveness` 는 transcript 부재 시 `"dead"` 반환 → ✕ 오표시. **`queued` liveness 상태 신설**(render-model additive):
- `_dispatch_liveness`(dispatch.py:251): jobs-source + status=="open" + `_job_liveness`가 dead(무transcript) + `elapsed_min ≤ 15`(startup grace) → `"queued"` 반환. 그 외(오래된 무transcript)는 dead 유지.
- render: `_JOB_LIVE_RANK`(render.py:50)에 `queued` 추가(idle 인접 rank), `_LIVE_GLYPH`/`_GLYPH_KEY`(291·294)에 `queued`→`◦`(dim) 매핑, `_live_key`(283) 추가. `_stage_segs` 의 `open`→`queued` 라벨 매핑(617)은 유지(미기동 표시).
- **불변**: liveness 는 render-model 필드(값 집합 확장은 additive) — collector 공개 필드명·의미 무변경, drill g9/g10 은 jobs.log 포맷만 assert(liveness 값 무관).

---

## 6. 파일별 구현 단계 (함수·라인 앵커)

### 6.1 `tools/fleet/collectors/dispatch.py`
- **S1 `_slug_stem`**(신설, `_norm_cwd`(522) 부근): stage-role 접미 strip 정규식 헬퍼. 단위 테스트 대상.
- **S2 dedup 키**(`collect` 799): `seen_keys` 세트 구성 추가. `_scan_jobs_log` 시그니처에 `seen_keys` 전달(또는 `collect` 에서 skip 판정으로 흡수). skip 조건에 `(cwd,stem)` 매칭 OR-추가(737).
- **S3 라이브 stage 유도**(`collect` 843 liveness 루프 뒤): working+jobs-source row 에 `live_stage` 재유도(§5a).
- **S4 queued liveness**(`_dispatch_liveness` 251 / `_job_liveness` 375): open+무transcript+startup-grace → `"queued"`(§5b). `_job_liveness` 자체는 무변경, 분기는 `_dispatch_liveness` 에서.

### 6.2 `tools/fleet/render.py`
- **R1 레이아웃 컷오프**(`_TWO_LINE_CUTOFF` 57): 110→138. `_layout_mode`(68) 주석 갱신(3-tier 폭 서술 동기화).
- **R2 옵션 컬럼 상수·헬퍼**(신설, `_MW`(490) 부근): `_OPTW≈18`. 통일 옵션 토큰 빌더 `_opts_segs(j)` → `mode·qa:<short>·int:<short>`(전량 dim). 기존 `_dispatch_role_suffix`(779)/`_dispatch_profile`(805)/`_mq_tag`(687) 의 name-zone 괄호 태그 경로를 **name-zone 에서 제거**하고 옵션 컬럼/L2 로 이설. (`_mq_tag` 는 잔여 호출부 없으면 제거 후보 — 실측 후 판단.)
- **R3 wide `_dispatch_row`**(813): name-zone = `[단계라벨] slug`(자식만 라벨; conductor 는 slug), 괄호 태그 제거. model cell 뒤 `_opts_segs` 고정 컬럼(89), 이어 breadcrumb. **자식 breadcrumb 복제 제거**(P0-1): depth≥2 는 `_stage_segs` 대신 micro-status(`running`/blank). `key: ` prefix(875) 제거(라벨은 name-zone 로 이동). dead row(853) → `dead @<last-stage>`(P2-11).
- **R4 conductor breadcrumb done 마커**(`_stage_segs` 582): 현재 stage 이전(done) 세그먼트에 `✓` 접미(P1-5). `_cur_key`/done 구분 로직 확장. per-stage 다색 유지(선존).
- **R5 narrow `_dispatch_row_2line`**(957): L1=정체성만(name-zone 라벨+slug, 괄호 태그 제거 973). L2 에 `_opts_segs` 추가(model↔breadcrumb 사이). 자식 L2 breadcrumb → micro-status. `_stack_split`(932) 분기점이 옵션/micro-status 를 올바로 가르는지 확인.
- **R6 stack `_dispatch_row_stack`**(950): R5 파생 자동 반영. L2=model+옵션, L3=breadcrumb/micro-status 정렬 검증.
- **R7 done/queued folding**(`_emit_dispatch_tree` 1367 / `job_children` 방출 1385): depth-2 자식 방출 필터 신설 — **stage-index < conductor active-stage-index(=이미 완료, breadcrumb 흡수) → fold(skip)**, **liveness=working → 유지**, **liveness∈{stale,dead} → 유지(실패 가시)**, **queued → fold**(breadcrumb future 흡수). `_SHOW_ALL`(1046) 토글로 접힌 자식 복원. `_conductor_stage_override`(1390) 는 active 자식 유도 유지(SD-F2).
- **R8 `↳` 의미 정리**(P1-4, `_dispatch_prefix` 724 / 방출부): top-level(orphan·loops·registry peer)은 무-arrow indent2, `↳` 는 depth-2 nested 전용. depth-1 top-level 의 현행 `↳`(726) 를 peer 표기로 조정. **주의**: loops row 표기 회귀 없는지 확인.
- **R9 queued glyph**(§5b R2): `_LIVE_GLYPH`/`_GLYPH_KEY`/`_JOB_LIVE_RANK`/`_live_key` 에 queued 추가. `curses.A_*` 직접참조 금지 — `_A_DIM`/색키만.
- **R10 F-16 세션 title cap**(신설 `_TITLE_MAX≈24`): `_session_row` name-zone(647 `_clip_w(name_txt, _NW_S-1)`) → `min(_NW_S-1, _TITLE_MAX)`; `_session_row_2line`(900 `_NAME2_MAX`) → `_TITLE_MAX`. tail-cut·head 보존(기존 `_clip_w` 재사용). 분사 name-zone 라벨+slug 는 composed cap(P2-6): slug budget = `zone − len(label) − 1`.
- **불변**: 모듈레벨 `curses.A_*` 직접 참조 금지(`_A_BOLD`/`_A_DIM` 폴백 유지, 33·43). 색 규율(status=녹/황/적, identity=시안/마젠타/청, dim=메타) — 새 hue 축 금지.

### 6.3 `tools/fleet/model.py`
- 신규 필드 **불요**(liveness·stage 기존 필드; queued 는 liveness 값 확장). `DispatchJob`/`Session` 스키마 무변경 → `--json` 회귀 없음.

---

## 7. 테스트 계획

### 7.1 신규/갱신 (`tools/fleet/tests/`)
- **`test_dispatch.py`(collector)**
  - `_slug_stem`: `fleet-ui-v2-execute`→`fleet-ui-v2`, `x-code-plan`→`x`, `already`→`already`(무변경), 다중 접미 무-과잉strip.
  - dedup (cwd,stem): (i) proc `fleet-ui-v2`@wtA + registry `fleet-ui-v2-execute`@wtA → **1 row**(병합). (ii) 동 stem 이나 wtA vs wtB → **2 rows**(conductor+자식 보존, 회귀 가드).
  - queued liveness: open+무transcript+elapsed 소 → `queued`; open+무transcript+elapsed 대 → `dead`; open+transcript활동 → `working`.
  - working registry stage 유도: transcript 활동 mock → `j.stage`가 `live_stage` 결과(raw `open` 아님).
- **`test_f14_title.py`(또는 신규 `test_f15_rows.py`)**
  - wide `_dispatch_row`: name-zone 에 괄호 옵션 태그 부재, 자식 name-zone 에 단계라벨 존재, 옵션 컬럼 세그 존재, 자식 breadcrumb 미복제.
  - narrow L2: 옵션 세그가 L2 에(L1 부재), conductor·자식 L2 컬럼 정렬(offset 동일).
  - folding: conductor+[plan done·exec working·test queued] 자식 → exec 자식만 row(plan·test fold); stale/dead 자식은 유지. `_SHOW_ALL` 로 복원.
  - done 마커: `_stage_segs` done 세그에 `✓`.
  - F-16: 세션 title display-width ≤ `_TITLE_MAX`(한글 2셀 tail-cut), 분사 composed(label+slug) ≤ zone.
  - 컷오프: `_layout_mode(120)`→narrow, `_layout_mode(140)`→wide, `_layout_mode(60)`→stack.

### 7.2 라이브 스모크
- `python3 tools/fleet/fleet.py --once`(plain) · `--json | python3 -m json.tool`(필드 계약·additive 확인). 3-layout: `--once` 폭 강제 없으면 `_LAYOUT` 강제 헬퍼/좁은 터미널로 wide/narrow/stack 각 렌더 육안.
- curses import 폴백: no-curses 경로에서 `--once`/`--json` 무크래시(`_A_*` 폴백).

### 7.3 drill 회귀 (지침 게이트)
- **g9/g10**(`~/.claude/loops/drill/cases_growing/`): `fleet.collectors.dispatch` 파이썬 API import + jobs.log 6필드·status(open/running)·comma-separated key=value 계약 assert. **본 변경은 표시/매칭·liveness 값만 — 공개 필드명·의미·jobs.log 포맷 무접촉** → g9/g10 GREEN 유지 확인. 편집 세션 마무리에 `~/.claude/loops/drill/run.sh` 1회 발사 권장.

---

## 8. 불변식 체크리스트 (실행 스테이지 필수 준수)

- [ ] collector 공개 필드명·의미 무변경(추가만 additive). `fleet.collectors.dispatch` import 표면·jobs.log 포맷 불변(g9/g10).
- [ ] `--json` additive only(`to_dict`=`asdict` — 신규 필드 없음 → 회귀 0).
- [ ] jobs.log·statusline·registry write 0(표시층+매칭+liveness 유도만).
- [ ] render.py 모듈레벨 `curses.A_*` 직접참조 금지(`_A_BOLD`/`_A_DIM` 폴백, Windows no-curses import).
- [ ] F-14 불변식: `Session.slug/title` 무접촉(title additive·매칭 무접촉·alert=slug).
- [ ] dedup 키 정규화 = 표시/매칭 로직, 필드 계약 변경 아님.
- [ ] 색 규율·새 hue 축 금지(옵션 전량 dim, queued glyph 는 dim).

---

## 9. 실행 스테이지가 따라야 할 핵심 결정

1. **자식은 부모 breadcrumb 을 복제하지 않는다** — 정체성=name-zone 단계 라벨, breadcrumb 슬롯=micro-status/blank(P0-1). conductor 만 full breadcrumb(done=✓·active=bold·pending=dim).
2. **folding: working+stale/dead 자식만 row** — done·queued 는 conductor breadcrumb 로 흡수(P0-2). `_SHOW_ALL` 복원.
3. **컷오프 138** — 2-line 이 주 레이아웃, wide 1-line 은 ≥138(P0-3). 세션 row 도 공유.
4. **dedup 키 = (정규화 cwd, slug-stem)** — 다른 worktree 면 병합 안 함(conductor↔자식 보존), 같은 worktree 동일 워커만 병합(F-15c).
5. **working registry row 는 live_stage 재유도, 진짜 미기동만 queued** — queued liveness 신설(additive), 미지 track 은 템플릿 페인팅 금지.
6. **옵션 토큰 통일** `mode·qa:<lvl>·int:<lvl>` 전량 표시(default-elision 미적용 — 사용자 요구 존중, 후속 토글 후보).
7. **F-16 title cap ≈24 tail-cut**, 분사는 composed(label+slug) 기준.
