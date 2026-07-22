# Change Report: pending 기억 배수(drain) 정책 — doctor 나이순 노출 + `maintenance --drain-pending`
- **Date**: 2026-07-22 | **Plan**: `.agent_reports/plans/2026-07-22_pending-drain/plan.md` | **Status**: ✅

## 1. Change Overview

`tools/memory/mem.py`에 정체 pending 레코드를 가시화하는 두 가지 기능을 추가했다.

1. `mem doctor`의 `stale-pending` 체크를 나이순(oldest-first)으로 확장해, 어떤 레코드가 얼마나 오래 정체됐는지 한눈에 드러낸다.
2. `mem maintenance --drain-pending` 명령을 신설해 `consumed` 레코드만 graveyard 백업 후 삭제(dry-run 기본, `--apply` 명시)하고, N일 초과 정체 `pending` 레코드는 **보고 전용 폐기 후보**로만 나열한다.

핵심 제약은 PRD D5(gc만 사람 게이트)·D-35(파괴 경로 fail-closed) 원칙에 따라 **pending 자동 삭제 경로를 어떤 형태로도 도입하지 않는 것**이며, plan·구현·테스트·양쪽 리뷰 모두 이 제약이 지켜졌음을 확인했다. spec-significance: within-spec(PRD v14 Cluster I 연장).

커밋: `eae36aad` — `tools/memory/mem.py` (+105/-6), `tools/memory/pending_drain.test.sh` (신규, +195, 23케이스).

## 2. Key Changes

### 2.1 doctor `stale-pending` 나이순 노출 — `tools/memory/mem.py`

- **Change**: stale-pending 쿼리를 `SELECT id, created FROM records WHERE delivery_state='pending' AND created<=? ORDER BY created ASC, id ASC`로 교체하고, WARN 메시지를 `N records (oldest <date>, no auto-expiry): id(Nd),... [+K more]` 형식으로 확장했다(최대 10건 표시, 초과분은 `+N more`).
- **Reason**: 기존 체크는 id만 최대 10건, 정렬 없이 노출해 어떤 레코드가 가장 오래됐는지 운영자가 알 수 없었다.
- **Principle**: `[WARN] stale-pending:` prefix와 `0 records` OK 분기, exit-code 계약은 메시지 본문만 확장하고 그대로 보존했다 — 기존 `mem_cluster_j.test.sh:267`의 grep 계약을 깨지 않기 위한 설계 제약.
- **Impact**: 회귀 없이 운영 가시성만 개선. 실제 운영 스토어 대상 dry-run 확인에서 `[WARN] stale-pending: 1 records (oldest 2026-06-26, no auto-expiry): hint_hint-25-17-트래커_e4bfd6(26d)` 형식으로 정상 렌더링됨을 검증했다.

### 2.2 `drain_pending()` 신설 + CLI 배선 — `tools/memory/mem.py:2979` 부근

- **Change**: D-39 doctor 섹션 직전에 `drain_pending(stale_days=WORKING_TTL_DAYS, apply=False)`를 신설했다. `--apply`일 때만 `BEGIN IMMEDIATE` 트랜잭션 안에서 `consumed` 행을 재조회 → `_graveyard_append(action="drain-consumed")` fail-closed → `_delete_rows` → `con.commit()` → 커밋 성공 건에 한해 `_append_write_event("drain-consumed", …)` 순으로 삭제한다. `pending` 행은 apply 여부와 무관하게 오래된 순으로 `SELECT`만 하여 출력하며, 어떤 UPDATE/DELETE도 발행하지 않는다. `maintenance` 서브파서에 `--drain-pending`, `--pending-stale-days`(기본 `WORKING_TTL_DAYS`)를 추가하고, dispatch가 `--drain-pending` 지정 시 기존 squash 경로(`maintenance(squash_days=, apply=)`)를 건너뛰도록 배선했다.
- **Reason**: `consumed` 레코드를 정리할 명시적 경로가 없었고(기존 `lifecycle()`은 TTL 만료 working consumed만 정리), 정체 pending을 폐기할지 판단할 근거도 없었다.
- **Principle**: 파괴 대상(`consumed`)과 보고 전용 대상(`pending`)의 코드 경로를 완전히 분리하고, 커밋-후-저널·fail-closed graveyard 등 `lifecycle()`/`delete_record()` 선례를 그대로 재사용해 새 불변식을 만들지 않았다.
- **Impact**: 운영자가 `mem maintenance --drain-pending`(dry-run) → `--apply`로 consumed 잔여물을 명시적으로 정리할 수 있게 됐다. pending은 이 경로를 포함한 어떤 자동화로도 삭제되지 않는다 — D5/D-35 게이트가 실행 단계와 두 리뷰(plan-review, dev-review)에서 모두 CLEAN으로 확인됨.

### 2.3 회귀 테스트 신설 — `tools/memory/pending_drain.test.sh`

- **Change**: `mem_cluster_j.test.sh` 격리 골격(mktemp `MEM_STORE`/`MEM_PROJECTS`/`MEM_WRITE_EVENTS`, `seed()`, `ok`/`bad`, `trap rm -rf EXIT`)을 복제해 8개 케이스군, 23개 assert로 신규 스위트를 작성했다: doctor 나이순, doctor 0건 OK 회귀, drain dry-run 비파괴, `--apply` consumed 삭제(DB+FTS+graveyard+write-event), `--apply` pending 인간 게이트 생존, `--pending-stale-days` 경계, squash 경로 무회귀, consumed 접속 정규화 비재출현.
- **Reason**: plan §3 Phase 3이 요구한 8개 케이스를 신규 기능의 유일한 자동 회귀 방어선으로 명시.
- **Impact**: 신규 스위트 PASS=23 FAIL=0. 기존 3개 관련 스위트(`mem_cluster_j`, `mem_cluster_e_gamma`, `mem_retrieval_v14`)도 무회귀.

## 3. Design Insights

- 삭제 가능 상태(`consumed`)와 보호 상태(`pending`)를 하나의 함수 안에서도 물리적으로 분리된 쿼리·분기로 유지한 것이 D5 게이트를 코드 리뷰 수준에서 기계적으로 검증 가능하게 만들었다 — dev-review는 "pending 행에 대한 UPDATE/DELETE 문이 어디에도 없다"를 코드 전수 검사로 직접 확인했다.
- 기존 `lifecycle()`의 커밋-후-저널·fail-closed graveyard 패턴을 재사용함으로써 신규 불변식을 추가하지 않고 기존 테스트·리뷰 관례가 그대로 적용 가능했다(plan-review가 "동형 패턴"으로 지적).
- `created` 컬럼이 스키마상 nullable이지만 `created<=?` WHERE 절이 SQLite NULL 비교 시맨틱상 NULL 값을 결과 집합에서 자연히 배제해, plan이 우려했던 "age 파싱 실패 시 `?d` 표기" 방어 코드가 실질적으로 도달 불가능한 경로임을 dev-review가 확인했다 — 방어 코드 자체는 유지하되 실행 경로상 리스크는 없다는 결론.

## 4. QA Summary

| 레벨 | 대상 | 결과 |
|---|---|---|
| 1 Syntax | `python3 -m py_compile tools/memory/mem.py` | ✅ PASS |
| 4 Functional | `pending_drain.test.sh`(신규) | ✅ PASS 23/23 |
| 4 Functional | `mem_cluster_j.test.sh` | ✅ PASS 33/33 |
| 4 Functional | `mem_cluster_e_gamma.test.sh` | ✅ PASS 40/40 |
| 4 Functional | `mem_retrieval_v14.test.sh` | ✅ PASS 22/22 |
| 4 Functional | 격리 스토어 `maintenance --drain-pending` dry-run 스모크 | ✅ PASS |
| 4 Functional | 실 스토어 `doctor`/`maintenance --drain-pending` dry-run(`--apply` 미실행) | ✅ PASS, 비파괴 확인 |
| Code review | D5/D-35 인간 게이트(pending 미삭제) | ✅ CONFIRMED — 위반 없음 |

합계 4개 스위트 118 ok / 0 fail, 전부 exit 0 — plan §5 수용 기준(신규 8케이스 all-ok, 기존 스위트 FAIL 증가 0, non-apply 경로 레코드 수 불변, apply에서도 pending 행 불변)과 정확히 일치.

두 단계 리뷰 모두 **verdict: CLEAN**:
- **plan-review(round 1)**: 소스 인용(라인 번호·상수·시그니처) 전부 실측과 일치, D5/D-35 준수, dry-run/--apply 일관성, 테스트 격리 확인. blocking 이슈 없음.
- **dev-review(phase_review)**: plan 대비 구현 정합성, D5 인간 게이트 위반 여부, dry-run/--apply 계약, 기존 테스트 회귀 4개 관점 모두 확인, 3개 기존 스위트 + 신규 스위트 재실행으로 dev log 주장과 결과 일치 확인. blocking 이슈 없음.

문서 업데이트: `<artifact-root>/analysis_project/code/`에는 `tools/memory/mem.py`(memory 엔진)와 대응하는 기존 토픽 문서가 없다(현재 디렉터리는 harness-installer, skill-design 감사 문서만 보유) — 대상 문서가 없어 이번 변경에서는 문서 갱신을 건너뛰었다.

## 4.5 Decision Record

`pipeline_summary.md`가 이 작업 디렉터리에 존재하지 않는다 — 자율 결정 이벤트 없음(clean run).

## 5. Failed or Skipped Steps

없음. plan.md·checklist.md의 Phase 1~4 전 항목이 완료 상태([x])로 기록되어 있고, dev log·test report·양쪽 리뷰가 일치된 근거로 이를 뒷받침한다.

## 6. Follow-Ups

- (참고, non-blocking) plan-review가 지적한 사항: `drain_pending`의 `consumed` 삭제는 나이 필터가 없어 방금 consume된 레코드도 `--apply` 1회로 즉시 삭제 대상이 된다. 의도된 설계(§1 목표에 "consumed 레코드만 --apply로 정리"로 명시)이지만, 운영 실수 방지를 위해 CLI help나 운영 문서에 "consumed는 나이와 무관하게 즉시 삭제 대상"이라는 경고 한 줄을 추후 추가하는 것을 고려할 수 있다.
- (참고, non-blocking) dev-review가 지적한 사항: 신규 스위트 케이스 1은 pending 3건만 시딩해 WARN 메시지의 `+K more`(10건 초과 truncation) 분기를 직접 커버하지 않는다. 코드 검토로 로직 정확성은 확인했으나, plan 범위에도 명시적으로 요구되지 않아 이번 이탈은 아니다. 향후 회귀 스위트를 두텁게 하고 싶다면 11건 이상 시딩 케이스를 추가할 수 있다.
