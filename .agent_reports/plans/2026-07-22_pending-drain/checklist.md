# Checklist — pending drain (2026-07-22)

plan.md의 실행용 체크리스트. Phase 1과 Phase 2는 독립 — 병렬 가능. Phase 3은 Phase 1·2 완료 후, Phase 4는 마지막.

## Phase 1 — doctor 나이순 노출
- [ ] 1.1 `mem.py:3047-3058` stale-pending 쿼리에 `created` 컬럼·`ORDER BY created ASC, id ASC` 추가
- [ ] 1.1 age 계산(`created[:10]` → `date.fromisoformat`, 실패 시 `?d`) 및 WARN 메시지 확장 (`oldest {날짜}`, `{id}({age}d)`, 10건 초과 시 `+N more`)
- [ ] 1.1 `[WARN] stale-pending:` prefix·OK 분기·exit code 불변 확인

## Phase 2 — drain_pending + CLI
- [ ] 2.1 `drain_pending(stale_days=WORKING_TTL_DAYS, apply=False)` 신설 (D-39 doctor 섹션 직전)
- [ ] 2.1 consumed 정리: apply 시 `BEGIN IMMEDIATE` 내 재조회 → `_graveyard_append(action="drain-consumed")` fail-closed → `_delete_rows` → commit 후 `_append_write_event("drain-consumed", …)`
- [ ] 2.1 stale pending 보고 전용 출력(나이순, human-gate 안내) — apply여도 pending 무변이
- [ ] 2.1 요약 라인 + dry-run/`mem sync` 힌트, return 0
- [ ] 2.2 파서에 `--drain-pending`, `--pending-stale-days`(기본 21) 추가, help 갱신
- [ ] 2.2 dispatch 분기: `--drain-pending`이면 squash 미진입, 기존 시그니처 무변경

## Phase 3 — 회귀 테스트
- [ ] 3.1 `tools/memory/pending_drain.test.sh` 신설 (cluster J 골격: mktemp 격리 MEM_STORE/MEM_PROJECTS/MEM_WRITE_EVENTS, seed, ok/bad, trap, +x)
- [ ] 케이스 1: doctor 나이순(최고령 선두·oldest·(Nd) 주석)
- [ ] 케이스 2: stale 0건 → OK `0 records`, exit 0
- [ ] 케이스 3: dry-run 비파괴 (총계 불변, would delete/dry-run 문구, fresh pending 미표시)
- [ ] 케이스 4: --apply consumed 삭제 (DB·FTS 소멸, graveyard `drain-consumed`, write-events `drain-consumed`)
- [ ] 케이스 5: --apply pending 생존 (human gate, `never auto-deleted`)
- [ ] 케이스 6: --pending-stale-days 경계 (5일 기준 6d=후보 / 4d=비후보)
- [ ] 케이스 7: 옵션 없는 maintenance → 기존 squash 경로 무회귀 (비-git 메시지, exit 0)
- [ ] 케이스 8: consumed handoff가 접속 정규화 후에도 consumed 유지

## Phase 4 — 검증
- [ ] `python3 -m py_compile tools/memory/mem.py`
- [ ] `bash tools/memory/pending_drain.test.sh` — FAIL=0
- [ ] `bash tools/memory/mem_cluster_j.test.sh` — 무회귀
- [ ] `bash tools/memory/mem_cluster_e_gamma.test.sh` — 무회귀
- [ ] `bash tools/memory/mem_retrieval_v14.test.sh` — 무회귀
- [ ] 격리 store 스모크: `maintenance --drain-pending` dry-run 정상 출력
