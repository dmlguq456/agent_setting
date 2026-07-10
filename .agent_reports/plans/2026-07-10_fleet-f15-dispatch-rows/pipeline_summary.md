# pipeline_summary — F-15 분사 row 재설계 + F-16 표시명 짧게

- **사이클**: 2026-07-10 fleet-f15-dispatch-rows
- **커밋**: d3f5efb(spec minor #2) → 6f79a66(plan, 디자인팀 critic 반영) → e3bddfd(impl) → 060121b(verdict, GREEN-with-notes 88 tests)

## 사이클/스코프

fleet 대시보드 F-15(분사 row 재설계 — 탈가로화·옵션 1급 정렬·workflow-first done-folding·queued 오라벨 해소) + F-16(세션 표시명 짧게). spec §4.6 F-15·F-16 범위 내(within-spec). 표시층(render.py) + collector 매칭·liveness 유도(collectors/dispatch.py)만 — collector 공개 필드 계약 불변(additive only), `--json` additive only, jobs.log/statusline/registry write 0.

## 스테이지 타임라인

code-plan(opus·deep maker, 디자인팀 critic plan-review 반영 → SHIP-WITH-FIXES 판정 P0 3건 목업 개정) → code-execute(sonnet·fast implementer) → code-test(opus·deep reviewer) → code-report(본 스테이지). 각 depth-2 headless worker, file-only handoff(산출물만 경유, 대화 컨텍스트 미공유).

## 변경 파일 (git diff --stat d3f5efb..HEAD)

- `tools/fleet/collectors/dispatch.py` (+43/-) — dedup 키 정규화(`_slug_stem` + (cwd,stem) 매칭), working registry row 라이브 stage 재유도, queued liveness 상태 신설.
- `tools/fleet/render.py` (+188/-) — 옵션 컬럼 1급화, 레이아웃 컷오프 110→138, 자식 breadcrumb 복제 제거, done/queued row folding, F-16 title cap.
- `tools/fleet/tests/test_f15_rows.py` (신규, 244줄, 22건) — slug-stem·dedup-key·queued-liveness·folding·done-marker·title-cap·wide-row·layout-cutoff·live-stage-induction 커버.
- `tools/fleet/tests/test_dispatch.py` (+5/-) — 기존 dispatch collector 테스트에 dedup/queued 케이스 보강.

## 핵심 구현 결정

- **dedup 키 = (정규화 cwd, slug-stem)**: `_slug_stem`이 stage-role 접미(`-execute`/`-code-plan` 등) strip. cwd 포함으로 conductor와 depth-2 자식(서로 다른 worktree)은 병합되지 않고 보존, 같은 worktree 이중 카운트만 합침.
- **queued additive liveness**: registry `open` + 무-transcript + elapsed 소(startup grace) → `queued`, 무-transcript+elapsed 대 → `dead`, transcript 활동 有 → `working`. 3분기 유닛 테스트로 검증.
- **live_stage 재유도**: working한 registry-only row는 raw `open` 대신 실제 track(`live_stage`)을 breadcrumb에 그림 — queued 오라벨 해소.
- **done-folding**(`_SHOW_ALL` 복원 토글 유지): conductor 활성 스테이지 이전(done)·이후(queued) 자식 row는 접어 breadcrumb에 흡수, working·stale/dead 자식만 별도 row 유지 — 잡 다수 시 세로 폭증 억제.
- **`_TWO_LINE_CUTOFF` 110→138**: 옵션 컬럼 추가로 wide 1-line에 필요한 폭이 늘어 dead-zone(110–138) 제거, 2-line narrow가 주 레이아웃으로 이동.
- **옵션 컬럼 이설**: name-zone 괄호 옵션 태그 제거, model↔breadcrumb 사이 정렬 컬럼(wide)/L2 dim 라인(narrow)으로 이동 — 탈가로화.
- **`_TITLE_MAX≈24` tail-cut**(F-16): 세션 표시명 head 보존 tail-cut, 전체 제목은 `--json`에 보존.

## 검증 결과

**GREEN-with-notes** — 차단 결함 0.
- 유닛: `python3 -m unittest discover -s tools/fleet/tests -v` → 88 tests 전량 GREEN.
- live 실측: `fleet.py --once`(narrow) / `--json | python3 -m json.tool`(26필드 additive, valid) / `COLUMNS=160/100/60 --once`(wide/narrow/stack 3-layout 육안 확인) — 탈가로화·옵션 정렬·done-folding·queued 해소·title cap 전부 라이브 실증.
- no-curses import: bare curses 모듈 주입 시에도 module-level AttributeError 없음(회귀 0).
- drill g9/g10: full run은 dispatch cycle fixture 필요(독립 headless 환경서 재현 불가, depth-3 금지 계약상 워커 재분사도 불가) → 미실행. 대신 정적 계약 확인(DispatchJob 26필드 보존, `_scan_jobs_log` additive 시그니처, 6-field TSV 라인 불변) → GREEN 유지 판정, full run은 main orchestrator 몫.

## 문서화 편차 2건 (spec 요구 미달 아님, 둘 다 ACCEPTABLE)

1. **R8 `↳` arrow 재정의 scope-out**: plan은 top-level peer 무-arrow / depth-2 전용 재정의를 계획했으나 execute가 scope-out. 현재도 위계가 육안으로 명확히 읽혀 원 불평(가로 sprawl·중복)의 근본 원인은 아님.
2. **옵션 토큰 `_mq_tag`/`_dispatch_profile` 재사용**: plan의 신규 uniform 토큰(`mode·qa:<lvl>·int:<lvl>`) 대신 기존 포맷(`dev·std/owner/qa:~std`) 재사용 — role 정보까지 담아 오히려 정보 풍부, 정렬된 1급 자리 요구는 충족.

두 편차 모두 후속 토글 후보로만 기록(P2-13 uniform-token, ask-4 default-elision과 함께 재검토).

## 불변식 유지 확인

- collector 공개 필드/`--json` additive only — 필드 삭제·개명 0.
- jobs.log/statusline/registry write 0 — 검증 후 `git status --short` clean.
- render.py 모듈레벨 `curses.A_*` 직접참조 금지 — `_A_BOLD`/`_A_DIM` 폴백 유지.
- F-14 불변식(Session.slug/title/ai_title/alert) 무접촉 — test_f14_title 16건 회귀 없음.

## 후속 (오케스트레이터 몫)

- main으로 merge·push, worktree 정리.
- 편집 세션 마무리에 `~/.claude/loops/drill/run.sh` 1회 발사(g9/g10 full run 포함 지침 회귀 게이트 완결).
