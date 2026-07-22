verdict: CLEAN

# Code Review — pending drain 정책 (doctor 나이순 노출 + `maintenance --drain-pending`)

**Reviewed**: `git show eae36aad` (base `fec5350a`), worktree `/home/Uihyeop/agent_setting-wt/pending-drain`
**Files**: `tools/memory/mem.py` (+105/-6), `tools/memory/pending_drain.test.sh` (new, +195, 23 cases)

## (a) Plan 대비 구현 정합성

일치. Phase 1(doctor stale-pending 나이순 확장), Phase 2(`drain_pending()` + CLI 배선), Phase 3(회귀 테스트) 모두 plan.md §3 계약대로 구현됨:

- doctor 쿼리가 정확히 plan대로 `SELECT id, created FROM records WHERE delivery_state='pending' AND created<=? ORDER BY created ASC, id ASC`로 교체됨 (mem.py:3117-3120). 메시지 포맷(`N records (oldest <date>, no auto-expiry): id(Nd),... [+K more]`)도 명세와 일치.
- `[WARN] stale-pending:` 접두사·`OK`/`0 records` 분기 보존 — `mem_cluster_j.test.sh:267` grep 계약 무회귀 확인(재실행, PASS=33 FAIL=0).
- `drain_pending()`이 plan §3 Phase2 동작 계약(헤더 출력 → consumed 조회/삭제 → stale pending 보고 전용 → 요약 → 힌트)을 순서대로 구현. graveyard-fail-closed → `_delete_rows` → commit → 커밋-후-저널(`_append_write_event`) 순서가 `lifecycle()`(mem.py:2329-2372)의 선례와 동일 패턴.
- CLI 배선(`--drain-pending`, `--pending-stale-days`, dispatch 분기)이 plan Step 2.2와 정확히 일치, 기존 `maintenance(squash_days=, apply=)` 시그니처 무변경.

## (b) D5 사람-게이트 위반 여부

위반 없음. `drain_pending()` 전체를 검사한 결과 `pending` 행에 대한 UPDATE/DELETE 문은 어디에도 없다 — stale pending 조회는 순수 `SELECT`이며 apply 플래그와 무관하게 출력만 한다(mem.py:3033-3043). 유일한 파괴 대상은 `delivery_state='consumed'` 행뿐이고, 이 경로도 `_graveyard_append` 성공 후에만 `_delete_rows`를 호출하는 fail-closed 구조(mem.py:3005-3016)로 `delete_record()`/`lifecycle()` 선례와 동형이다. `pending_drain.test.sh` 케이스 5("pending 인간 게이트")로 3건 전건 생존 + `delivery_state` 불변을 직접 검증하며, 재실행 결과도 일치.

## (c) dry-run/--apply 계약

정확. `apply=False`(기본)는 `BEGIN IMMEDIATE` 없이 읽기만 하고 어떤 write도 발행하지 않음 — dry-run 케이스 재실행 결과 레코드 총계 불변(5→5) 확인. `--apply`만 `BEGIN IMMEDIATE`로 트랜잭션을 열고, consumed 삭제 후 `con.commit()` → 커밋 성공 건에 한해 저널 기록(고스트 이벤트 방지, plan §4 리스크 항목 충족). 개별 건 graveyard 실패 시 해당 건만 skip하고 나머지 진행(`lifecycle --apply`와 동일 패턴).

## (d) 기존 관례·기존 테스트 계약 회귀 위험

회귀 없음 — 3개 기존 스위트 재실행 결과 전부 dev log 주장과 일치:

```
tools/memory/mem_cluster_j.test.sh        PASS=33 FAIL=0
tools/memory/mem_cluster_e_gamma.test.sh  PASS=40 FAIL=0
tools/memory/mem_retrieval_v14.test.sh    PASS=22 FAIL=0
tools/memory/pending_drain.test.sh        PASS=23 FAIL=0  (신규)
python3 -m py_compile tools/memory/mem.py OK
```

- `created` 컬럼은 스키마상 nullable(`created TEXT`, NOT NULL 아님)이지만, doctor·drain_pending 양쪽 모두 `created<=?` WHERE 절을 먼저 거치므로 SQLite NULL 비교 시맨틱(`NULL<=X`→NULL/false)에 의해 NULL 값은애초에 결과 집합에서 배제된다 — `_age_days`/age 계산의 `created[:10]` 호출이 None을 받을 경로가 없어 plan §4의 "created 파싱 실패시 `?d` 표기, 예외로 중단 금지" 요구를 실질적으로 만족한다 (ValueError만 잡지만 도달 불가능한 케이스이므로 안전).
- consumed 레코드 비재출현: `_migrate_v5`의 ordinary-only 승격 가드가 그대로 유지되어 drain 이후 재출현 경로 없음(케이스 8로 확인).
- 신규 액션 문자열 `"drain-consumed"`는 `_graveyard_append`/`_append_write_event`의 자유 문자열 `action` 계약과 호환 — `mem log --action` 필터 등 기존 소비자 영향 없음.

## 참고 (blocking 아님)

- doctor stale-pending 메시지의 `+K more`(10건 초과 truncation) 분기는 코드 검토로 로직 정확성을 확인했으나 신규 스위트(케이스 1)는 3건만 시딩해 이 분기를 직접 커버하지 않는다 — plan §3 Phase 3에도 명시적으로 요구되지 않은 범위이므로 plan 이탈은 아니다.

## 결론

plan 정합성, D5/D-35 게이트 준수, dry-run/--apply 계약, 기존 테스트 회귀 4개 관점 모두 확인 완료. 소스 미수정. **verdict: CLEAN**
