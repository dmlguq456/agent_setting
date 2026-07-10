# Test Report — stage-dispatch Phase 1

Level 3-4: functional + integration (contract-doc + wrapper + pilot).

## Checks

| # | Check | Command | Result |
|---|---|---|---|
| 1 | adaptation boundary green | `bash tools/check-adaptation-boundary.sh` | **PASS** (`OK: adaptation boundary checks passed`, exit 0). 예고된 `loops/drill/run.sh` byte-equiv FAIL 은 baseline·post-edit 모두 **미발생**(타 세션 이미 랜딩한 듯). |
| 2 | skills byte-equiv | `diff -qr --exclude=.sync_state.json skills adapters/claude/skills` | **PASS** (편집 6파일 projection 동기화 후 동일) |
| 3 | context-footprint budget | `python3 tools/context-footprint.py --skip-hooks --strict` | **PASS** (exit 0, warning 0; claude skill-metadata 4290<10000, codex active 6301<8000; bootstrap chars: codex 21012·claude 14966·opencode 13645 — 소폭 증가, budget 게이트 대상 아님) |
| 4 | wrapper compile | `python3 -m py_compile adapters/claude/bin/dispatch-headless.py` | **PASS** |
| 5 | wrapper depth-aware note 3분기 | 함수 직접 호출 | **PASS** (depth2/code-* = stage-worker, depth2 기타 = review, depth1 = conductor) |
| 6 | 참조 앵커 grep (표면 1-12) | surface별 grep | **PASS** (20/20 앵커 존재) |
| 7 | pilot: 스테이지 depth=2 row | fixture jobs.log | **PASS** (4 row depth=2/parent/worker_role/owner) |
| 8 | pilot: 실 레지스트리 무오염 | `grep -c calc-subtract ~/.claude/.dispatch/jobs.log` | **PASS** (0건) |
| 9 | pilot: depth ≤ 2 불변 | fixture jobs.log | **PASS** (depth=2 4건, depth=3+ 0건) |
| 10 | pilot: 산출물 + 소스 검증 | `python3 -c "import calc; assert calc.subtract(5,3)==2"` | **PASS** (VERIFY_OK; plan→test→report 산출물 정상) |

## Verdict
PASS. 계약 개정·wrapper 증분·pilot 모두 성공 기준 충족. dev_logs sidecar 는 spec-less fixture 창에서
artifact-guard 에 막혀 미생성(내용은 커밋·checklist 반영) — 실패 아니라 hook-ceremony 수령 증거이자
conductor-책임 힌트로 `pilot_metrics.md` 에 문서화.
