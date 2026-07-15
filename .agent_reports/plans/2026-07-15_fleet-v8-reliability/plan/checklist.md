Safety commit: 8dd0c062a58fd61827cc9c3f1d7c7be63b8a7aa8

Baseline: 247 tests OK (14.4s) · python 3.8.10 · worktree clean at entry
Live fixture: pid 1168514 ALIVE (verified 2026-07-15, name=agent-setting-17, activity 119ms)

Phase A: F-25 단일 상태 분류기 (기반)
  [x] Step 1: tools/fleet/model.py — 상수 블록 + StateTracker + classify_session/classify_job/reset_state_tracker/tracker_sweep + Session/DispatchJob 필드 additive
  [x] Step 1b: collectors/liveness.py — classify() 를 증거 수집기로 강등, model 위임, _proc_evidence(start-time 재검증)
  [x] Step 1c: collectors/dispatch.py — _dispatch_liveness 위임, _reconcile_drill_rows 증거 병합(:924 대입 소멸)
  [x] Step 1d: collectors/{__init__,procscan}.py — tracker_sweep GC, read_proc_start
  [x] Step 1e: tests/test_f25_state_model.py + fixtures/state_model/ 신규

Phase B: F-26 레지스트리 1급화
  [x] Step 2: collectors/claude.py — read_registry() 1급 계약, registry_name/started_at/updated_at/proc_start/kind 적재
  [x] Step 2b: collectors/procscan.py — read_proc_start / provenance
  [x] Step 2c: render.py — unused 글리프·배지·name 사슬·pulse·legend·필터
  [x] Step 2d: tests/test_f26_registry.py + 디자인팀 critic + live acceptance pid 1168514

Phase C: F-22 minor name zone cap
  [x] Step 3: render.py — _NAME_WIDE_MAX=40 + _wide_name_width 상한
  [x] Step 3b: tests/test_f22_name_cap.py + 3폭 렌더 + critic

Phase D: F-27 세션 제어
  [x] Step 4: tools/fleet/control.py 신규 — verify_target/is_excluded/kill_target/log_action/close_registry_row
  [x] Step 4b: render.py — 모드 있는 커서(s/x 진입, ↑↓ 이동, Esc 해제) + 확인 프롬프트
  [x] Step 4c: tests/test_f27_control.py + safety acceptance A/B + critic

결과: 394 tests OK (기준선 247 + 147 신규) · 회귀 0 · mirror parity OK
미수행(RED 아님): 계획 §6.6-6 라이브 TUI 수동 검증 — 헤드리스 워커에 대화형 TTY 부재. 헬퍼 분리 + 62 tests + UI 캡처로 대체, 잔여 갭은 code-test/사용자에게 인계.
