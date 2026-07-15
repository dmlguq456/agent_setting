# Step 6 — 통합 검증 · 미러 동기 (마감)

## 실행 순서 (plan.md §8 그대로)
```
cd /home/Uihyeop/agent_setting-wt/fleet-v9-mouse-subagent

# 1) 전체 회귀
python3 -m unittest discover -s tools/fleet/tests -q
→ (rsync 전) Ran 468 tests. FAILED(failures=1) — 유일한 실패는 test_mirror_parity(미러 드리프트, 아래 4)에서 해소).
   베이스라인 416 + 신규 4스위트(test_f27_mouse 21 · test_f29_subagents 15 · test_d3_stage_zone 6 · test_scroll_regression 10 = 52) = 468. ≥416 충족, OK.

# 2) 3폭 렌더 눈 검사
for w in 60 120 168; do COLUMNS=$w python3 tools/fleet/fleet.py --once; done
→ 3폭 전부 정상 렌더(직접 확인 — 세션 목록, dispatch 트리, usage/mem/alert 라인, legend 전부 정상).

# 3) --json 스모크 (heredoc·파이프 금지 — 파일 경유)
python3 tools/fleet/fleet.py --json > /tmp/v9_final.json
python3 -c "import json;d=json.load(open('/tmp/v9_final.json'));print('sessions',len(d['sessions']),'jobs',len(d.get('jobs',[])))"
→ sessions 9 jobs 3

# 4) 미러 동기 (§2.1 — tests/ 신규 파일 포함 전체 트리)
rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/
python3 -m unittest tools.fleet.tests.test_mirror_parity -v
→ OK (1 test) — rsync 전 유일한 실패였던 parity가 해소됨.

# 5) 미러 동기 후 전체 재실행
python3 -m unittest discover -s tools/fleet/tests -q
→ Ran 468 tests, OK. rsync가 아무것도 깨지 않음.
```

## 완료 기준 판정 (전부 충족)

| # | 기준 | 판정 | 근거 |
|---|---|---|---|
| C1 | 전체 테스트 ≥416, OK, 신규 실패 0 | ✅ | 468 tests, OK (rsync 후 최종 재실행) |
| C2 | F-27 마우스 6동작 + 안전 5계약 전부 통과 | ✅ | `test_f27_mouse.py`(21) + 기존 `test_f27_control.py`(82) 전량 OK |
| C2b | §4.4.1 재그리기 불변식 + §4.2.1 클릭 맵 기준이 코드·테스트로 고정 | ✅ | `_handle_mouse` 호출이 `_PROMPT` 블록 내부에 배치(render.py), `test_confirm_to_confirm2_transition_repopulates_hits` · `test_click_map_costs_nothing_per_tick` · `test_first_click_works_from_base_mode`로 고정 |
| C3 | 키보드 폴백 회귀 0 · 스크롤 회귀 0(base 모드 한정) | ✅ | `test_f27_control.py` 82건 전량 통과 + `test_scroll_regression.py` 10건(A2-6 최종 판정) |
| C4 | F-29 백본 불가침 + pulse 혼입 0 + `--json` additive | ✅ | `test_f29_subagents.py::NoRegressionTest` 5건 |
| C5 | stage zone 상한 상수 1개, 168 무오버플로 구조적 | ✅ | `test_d3_stage_zone.py` 6건 |
| C6 | 3폭 `--once` 렌더 + `--json` 스모크 통과 | ✅ | 위 2)·3) |
| C7 | 디자인 critic 비평 2건 수령·기록 | ✅ | `_internal/dev_reviews/design_critic_step2.md`(Step 2) · `design_critic_step3.md`(Step 3, F-29는 critic 반영으로 `├/└` 커넥터 개선까지 완료) |
| C8 | 미러 parity 통과 | ✅ | 위 4) |
| C9 | 실세션 스폰·시그널 0 — dev log에 명시 | ✅ | 6개 dev log 전부 "안전 규칙 준수" 절에 명시. 모든 검증은 fixture(Session/DispatchJob/SubAgent/sqlite/jsonl) + mock(`curses.getmouse`/`doupdate`, `control.kill_target`, `render._do_kill`) + `--once`/`--json` 스냅샷뿐 |

## 잔존 사항 (명시 — 스코프 밖)
- **60폭 legend/mem/usage 요약 행 미축약(D4)**: Step 4 stage-zone과 원인이 다른 기존 결함, plan.md §9에 스코프 밖으로 명시됨. 60폭 char-length 오버플로 16건 중 stage-zone 기인 0건(D3로 해소된 부분은 이미 해소).
- **F-28/F-30**: plan.md §9 명시대로 스코프 밖(v9는 방향만 등재).
- **디자인 critic 권고 중 미반영분**: Step 2 §1(선택 하이라이트 반전 색-페어 전용화)·§3([KILL] 별도 강조색) — 시각 디자인 확장이며 §4 편집 표면 밖, 다음 사이클 후보로 남김(critic 문서에 명시).

## 안전 규칙 준수 (§0)
전 스텝에 걸쳐 실제 `claude`/`codex`/`opencode` 세션 스폰·시그널 0. `RealSignalTest` 계열(기존 `test_f27_control.py`)이 사용하는 `sleep` 프로세스 + monkeypatched `os.kill` 패턴 재사용 확인(무변경). 신규 코드는 전부 fixture 주입 + mock 스파이로만 검증됨.
