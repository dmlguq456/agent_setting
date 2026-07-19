# fleet 제목+부제 통합 요약 — 한 호출 두 출력 (quick evidence)

worktree: /home/Uihyeop/agent_setting-wt/fleet-title-subtitle (branch fleet-title-subtitle, base main 8871b11d)

## 변경 파일

- tools/fleet/refresh_title.py — PROMPT_TEMPLATE 두 줄(TITLE:/NOW:) 출력, TITLE_MAXLEN 64→40·TITLE_MAX_WORDS 8→6,
  `_labeled_line`/`_TITLE_LINE_RE`/`_NOW_LINE_RE` 파서, `validate_summary` 신규(1줄·printable·≤120자 클립·메타 거부·비ASCII 허용),
  `main()`에서 summary 파싱→titles.write 전달(빈 증분 경로는 이전 summary 보존, NOW 파싱 실패는 summary=None으로 정직 강등),
  `CHILD_DEBOUNCE_SEC=150`·`schedule_sessions`가 is_child 세션에 짧은 디바운스 전달(폭주 상한은 공유 불변).
- tools/fleet/titles.py — `write()`/`read()` dict에 `summary` 키 additive(None이면 생략), `fresh_summary()` 신규
  (max_age 기본 `_FRESH_SUMMARY_SEC=15*60`, 제목의 `_FRESH_SEC=24h`와 별도 상수).
- tools/fleet/model.py — `Session.summary`/`DispatchJob.summary: Optional[str] = None` additive(asdict 자동 포함).
- tools/fleet/collectors/claude.py, codex.py — enrich()에서 `titles.fresh_summary()` 읽어 `sess.summary` 세팅.
- tools/fleet/collectors/__init__.py — `_adopt_child_titles`가 title과 summary를 같은 pid→cwd 조인으로 함께 입양
  (모호 cwd는 둘 다 거부, F-26 유지).
- tools/fleet/render.py — `_summary_row()` 신규(순수 인셋, `_SUBAGENT_IND` + depth*2, 전부 dim). 세션 행/디스패치 잡 행 직후·
  `⚡` 서브에이전트 스트립 이전에 삽입, wide 레이아웃 전용(`_srow`/`_jrow is None` 분기), summary 있고 dead/stale 아닐 때만
  표시(F-13 healthy-silent), 없으면 완전 무음.
- tools/fleet/demo.py — 부제 행 시각 확인용 데모 픽스처 2건에 `summary=` 추가(세션 1건 + 디스패치 잡 1건).
- 테스트: tools/fleet/tests/test_f17_title_refresh.py 갱신(64자/8단어 가정 3건 교체, 두-줄 파싱/디바운스/summary
  라운드트립 등 다수 추가) + tools/fleet/tests/test_f16_f17_subtitle.py 신규(모델 additive, 입양 조인, 렌더 부제 행
  전용 16건).
- adapters/claude/tools/fleet/ 미러 rsync 완료(demo.py 포함).

## 스펙 게이트

.agent_reports/spec/agent-fleet-dashboard/prd.md §4.7 F-16/F-17 어휘만 확인(수정 없음) — F-16 "짧은 영어 기준선",
F-17 "라이브 제목 refresher — cross-harness fleet sidecar + no-tools 경량 LLM 워커"와 부제 확장이 상충하지 않음을 확인.
PRD 본문은 수정하지 않음(개정 등재는 별도 minor).

## 테스트

```
cd tools/fleet && python3 -m unittest discover -s tests -p "test_*.py"
```
- 미러 rsync 전: 659 pass / 1 fail(test_mirror_parity — 예상된 드리프트, rsync 전이라 당연).
- `rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/` 실행 후: **660 passed, exit code 0**.
- 관련 스위트 개별 재확인: test_f17_title_refresh(69) / test_f16_f17_subtitle(16, 신규) / test_dispatch_child_titles /
  test_f29_subagents / test_harness_model_merge / test_f21_cross_harness_titles / test_f14_title — 전부 pass.

## `--once --demo` 캡처 (60/120/168열)

```
COLUMNS=60  python3 fleet.py --once --demo --section both
COLUMNS=120 python3 fleet.py --once --demo --section both
COLUMNS=168 python3 fleet.py --once --demo --section both
```
- 60열(stack)·120열(narrow): 부제 행 없음 — 스코프대로 wide 전용, 회귀 없음.
- 168열(wide)에서만 부제 행 확인:
  ```
  ▍ ⠸ claude code (Opus 4.8·xhigh)    demo-app-a7 ▾4 tracked   ...  45%    1h35m
  ▍     지금 render.py 그룹 루프의 틴트 적용 경로를 분석 중
  ▍   ↳ ⠸ claude code (Opus 4.·xhigh) demo-feat-x   ...  22m
  ▍       지금 feat-x 브랜치의 테스트 실패를 재현하는 중
  ```
  세션 부제는 세션 행 직후·`⚡` 스트립 이전, 잡 부제는 잡 행 직후·그 잡의 스트립 이전(순서 확인). 인셋은 `_SUBAGENT_IND`
  기준(세션 depth 0, 잡 depth+2), 전부 dim.
- 회귀 diff: `git stash`로 변경 전 상태를 만들어 동일 3폭 before/after 캡처 후 diff — 168열에서 구조적 차이는 위 2줄
  신규 삽입뿐(그 외 diff는 실제 라이브 세션의 스피너 프레임·경과 분·정렬 변화 등 캡처 시점 노이즈로, 코드 변경과 무관).
  60/120열은 스피너/시간 노이즈 외 구조적 차이 0.

## 최종 계약

```text
artifact: /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_fleet-title-subtitle/quick_evidence.md
verdict: PASS
blocker: none
```
