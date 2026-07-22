verdict: CLEAN

## 📋 Plan Review Results

**Target**: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_pending-drain/plan.md`
**Plan summary**: `mem doctor`의 stale-pending 체크를 나이순(oldest-first)으로 확장하고, `mem maintenance --drain-pending`을 신설해 consumed 레코드만 graveyard 백업 후 삭제하며 정체 pending은 보고 전용 폐기 후보로만 남긴다 — pending 자동 삭제는 어떤 경로로도 도입하지 않는다.

### 🟢 잘 구성된 부분

- **소스 정합성**: plan이 인용한 모든 앵커(라인 번호, 함수 시그니처, 상수값)가 실제 `mem.py`(3,724줄)와 정확히 일치했다. `WORKING_TTL_DAYS=44`행, `consume()`(2287-2326), `lifecycle()`(2329-2376), `_delete_rows`/`delete_record`/`_graveyard_append`(2380-2432), `stale-pending` 체크(3047-3058), D-39 섹션 마커(2977), 파서(`mt`, 3629행대)·dispatch(3719-3720) 전부 실측과 일치. `mem_cluster_j.test.sh:267`의 `\[WARN\] stale-pending` grep 계약도 확인했고, plan은 이 prefix를 보존한 채 메시지 본문만 확장하도록 설계했다.
- **D5/D-35 인간 게이트 준수**: 설계 계약(§3 Step 2.1 항목 3)이 "`--apply`여도 pending 행에는 어떤 UPDATE/DELETE도 발행하지 않는다"를 명시하고, 리스크 섹션(§4 마지막 항목)에서 자동 전이 금지를 별도로 재확인한다. 실제 코드에서 pending 보호는 `lifecycle()`의 `protected-expired` 분기(2345-2348)와 `delete_record`의 force 게이트(2410-2413)로 이미 이중 방어되어 있고, 신규 `drain_pending`은 pending 테이블에 손대지 않는 순수 조회 경로이므로 설계가 이 불변식과 충돌하지 않는다.
- **dry-run/--apply 일관성**: `drain_pending`의 커밋-후-저널 순서(§3 Step 2.1 항목 2: `con.commit()` 이후 `_append_write_event`)가 `lifecycle()`의 기존 선례(2361-2367, 커밋 성공 후에만 `expired_ok`에 대해 이벤트 기록)를 그대로 재사용한다. graveyard fail-closed 처리(실패 시 해당 건만 skip, 나머지 진행)도 `delete_record`(2414-2417)·`lifecycle`(2352-2360) 패턴과 동형이다.
- **테스트 격리**: Phase 3 계획이 `mem_cluster_j.test.sh`의 `mktemp -d` + `MEM_STORE`/`MEM_PROJECTS`/`MEM_WRITE_EVENTS` export + `trap rm -rf EXIT` 격리를 그대로 복제하도록 명시했고, 케이스 8("consumed 비재출현")은 `mem.py:723`의 `normalized == "ordinary"` 승격 가드를 정확히 겨냥한다 — 이는 실제 정규화 로직(718-727)과 일치하는 회귀 지점이다.
- **plan-checklist 정합성**: checklist.md의 4개 Phase·세부 항목(특히 Phase 3의 8개 케이스)이 plan.md §3 Phase 3 목록과 1:1로 대응하며 순서·의존성 서술("Phase 1·2 독립, Phase 3은 완료 후, Phase 4는 마지막")도 동일하다.

### 🟡 참고할 만한 개선 여지 (blocking 아님)

- **consumed 삭제에 유예 기간(grace period)이 없음** — `drain_pending`은 `consumed` 상태이기만 하면 방금 consume된 레코드도 즉시(`--apply` 1회 실행으로) 삭제 대상이 된다(§3 Step 2.1 항목 2에 나이 필터가 없음). 이는 "정체된" 레코드만 정리한다는 명령 이름(`drain-pending`이 아니라 "consumed cleanup")의 직관과 약간 어긋날 수 있다. 의도적 설계(§1 목표가 "consumed 레코드만 --apply로 정리"라고 명시)로 보이지만, 실행 단계에서 실수로 최근 consume 레코드까지 쓸어가는 사고를 막으려면 checklist나 CLI help에 "consumed는 나이와 무관하게 즉시 삭제 대상"이라는 한 줄 경고를 남겨두는 편이 안전하다. 필수는 아니다.
- **라인 번호 드리프트**: Step 2.1(D-39 직전 삽입, ≈2978)이 Step 2.2가 참조하는 파서(3629행대)·dispatch(3719-3720) 라인보다 먼저 실행되므로, Step 2.2 시점에는 실제 라인 번호가 plan에 적힌 값보다 커진다. 실행 단계가 내용 기반(grep/anchor) 편집을 한다면 문제없지만, 라인 번호를 문자 그대로 따라가면 어긋난다 — plan 자체의 결함이라기보다 실행 시 유의사항이라 blocking으로 잡지 않았다.

### 검증 계획 평가

§5 검증 명령은 구체적이고 실행 가능하다(`py_compile`, 신규 스위트, 기존 3개 회귀 스위트, 격리 스모크). 수용 기준(신규 8케이스 all-ok, 기존 스위트 FAIL 증가 0, non-apply 경로 레코드 수 불변, apply에서도 pending 행 불변)도 명확하고 측정 가능하다.

### 결론

구축 품질 관점에서 blocking 이슈 없음. 소스 참조가 실측과 정확히 일치하고, D5 인간 게이트·dry-run 계약·기존 코드 패턴(commit-then-journal, fail-closed graveyard)을 일관되게 따른다. 위 🟡 두 건은 참고 사항으로, 실행을 막을 필요는 없다.
