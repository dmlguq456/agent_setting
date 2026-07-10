# dev_log — 구현 (inline, single step)

## SD-15b — 로그-패턴 DEAD 앵커링
- `dispatch-liveness.sh`: `scan_log_death()` 신설 — `tail -n 40 | awk NF | tail -n 3 | grep LIMIT_RE | awk length<=200`.
  루프에서 transcript 를 먼저 해결, `age<=STALE_MIN` 이면 로그 안 보고 ALIVE; transcript 부재/stale 일 때만 스캔.
- codex/opencode `.py`: `log_shows_limit` 을 `nonempty[-3:]` + `len<=200` 로 앵커. main 루프에서 fresh
  transcript/heartbeat 신호가 로그를 이기도록 재정렬(로그 스캔은 not-fresh 분기에서만).
- core OPERATIONS ⑨ 에 앵커링 계약 한 문장 추가.
- core-first-guard 로 adapters 편집이 막혀 core Read→core 편집→adapters 순서로 진행(정상 게이트).

## SD-16e — usage-check reset 의미론
- `reset_to_epoch()`: noon/midnight 정규화 후 `date -d`, 마커 이후 첫 도래(이르면 +1d).
- 결정 로직: reset 파싱되면 경과=ok / 미경과=limited(reset); reset 부재면 `UNKNOWN_WINDOW_MIN`(60m) 안
  limited(unknown-reset)·밖 ok. `--unknown-window-min` 플래그 + env 추가.
- core OPERATIONS jobs.log 하드 계약에 수동 마감 reset= 의무 한 문장.

## SD-11b — deny 상향
- `stage-dispatch-reminder.sh` 전면 재작성: `conductor_code_stage()` 판정 → intensity 분기
  (direct/quick=silent · standard+=opt-out?reminder:deny · unknown=reminder). `emit_deny`(hook JSON
  permissionDecision / CLI stderr+exit2, worktree-path-guard 선례), `emit_reminder`(기존 additionalContext).
- (a) env 주입은 3어댑터에 이미 존재 확인 — 추가 편집 없음.

## 함정·해결
- 테스트 Case F(prose 앵커링) 초기 실패: 요약 힌트 "→ SUSPECT/DEAD:" 를 grep DEAD 가 오매칭 →
  verdict 라인 `⚠️ DEAD`/`⚠️ SUSPECT` 로 좁혀 해결.
- usage-check 기존 3pm 케이스가 실행시각 의존이 됨 → reset 을 now 상대(±Nh)로 동적 산출하도록 테스트 갱신.
- baseline 대조: `git stash push -- <9파일>` → suite → `git stash pop`. baseline 311/12, 변경 313/12.
