---
status: done
created: 2026-07-22
---

# Plan — pending 기억 배수(drain) 정책: doctor 나이순 노출 + `maintenance --drain-pending`

## 1. 목표 (Goal)

`tools/memory/mem.py`에 정체 pending 레코드의 가시화(`mem doctor` 나이순 노출)와 명시적 배수 경로(`mem maintenance --drain-pending`)를 추가한다. consumed 레코드만 `--apply`로 정리(graveyard 백업 후 삭제)하고, N일 초과 정체 pending은 **보고 전용 폐기 후보**로 남긴다 — D5(gc만 사람 게이트)·D-35(파괴 경로 fail-closed) 원칙에 따라 pending 자동 삭제는 어떤 경로로도 도입하지 않는다. spec-significance: within-spec (PRD v14 Cluster I 연장, 판정 완료).

## 2. 현재 상태 분석 (Current State Analysis)

대상 파일: `/home/Uihyeop/agent_setting-wt/pending-drain/tools/memory/mem.py` (3,724줄)

| 구성요소 | 위치 | 현재 동작 |
|---|---|---|
| `DELIVERY_STATES` | `mem.py:62` | `("ordinary", "pending", "consumed")` |
| `WORKING_TTL_DAYS` | `mem.py:44` | `21` — doctor stale-pending 임계와 consume 후 TTL 재시작에 공용 |
| `maintenance()` | `mem.py:199-285` | **git squash 전용** (dump repo 이력 압축 + gc). dry-run 기본, `--apply` 실행. drain 기능 없음 |
| `consume()` | `mem.py:2287-2326` | 유일한 `pending→consumed` 전이. working이면 21일 TTL 재시작. `_append_write_event("consume", …)` 저널 |
| `lifecycle()` | `mem.py:2329-2376` | 만료 working 삭제(`--apply`). **pending은 `protected-expired`로 보호**. consumed는 TTL 만료 시 이 경로로만 정리됨 — durable consumed·미만료 working consumed는 정리 경로 부재 |
| `_delete_rows()` | `mem.py:2380-2392` | 열린 커넥션 위 3-table DELETE (records+fts+cjk); 호출자가 트랜잭션 소유 |
| `delete_record()` | `mem.py:2395-2425` | `BEGIN IMMEDIATE` → pending이면 `--force` 없이는 거부 → graveyard 실패 시 삭제 중단(fail-closed) |
| `_graveyard_append()` | `mem.py:2432` | `action` 문자열 자유 지정 가능 (`"lifecycle-expire"`, `"delete-force"` 등 기존 선례) |
| `_append_write_event()` | `mem.py:1260-1291` | fail-open 쓰기 저널. `action` 자유 문자열 — `mem log --action` 필터도 자유 문자열이라 신규 action 호환 |
| doctor `stale-pending` | `mem.py:3047-3058` | `created <= today-21d`인 pending의 **id만 최대 10건, 정렬 없음** — 나이·생성일 미노출. 실측: 30건 정체, 최고령 2026-06-26, 만료 없음(pending은 `expires=NULL` 불변식, `mem.py:727`) |
| CLI `maintenance` 파서 | `mem.py:3630-3636` | `--squash-days`, `--apply`만 존재 |
| CLI dispatch | `mem.py:3719-3720` | `maintenance(squash_days=…, apply=…)` 직결 |
| 접속 시 정규화 | `mem.py:710-727` | `ordinary`→`pending` backfill만 수행, `consumed`는 승격 안 됨(`normalized == "ordinary"` 가드) — drain이 지운 consumed가 재출현할 경로 없음 |

테스트 스위트 스타일 (`mem_cluster_j.test.sh` 기준): `set -u`, `mktemp -d` 격리(`MEM_STORE`/`MEM_PROJECTS`/`MEM_WRITE_EVENTS` export), `ok()`/`bad()` 카운터, `seed()` 직접 INSERT 헬퍼(id/tier/scope/type/cwd/strength/last_accessed/body/[expires]/[delivery_state]/[created]), `trap rm -rf EXIT`, `claude` 미스폰(ISO-2). 기존 테스트가 `grep -q '\[WARN\] stale-pending'`으로 doctor 출력을 검사하므로 **`[WARN] stale-pending:` prefix는 반드시 보존**해야 한다 (`mem_cluster_j.test.sh:267`).

## 3. 변경 계획 (Change Plan)

### Phase 1 — `mem doctor` stale-pending 나이순 노출

**Step 1.1** — `mem.py:3047-3058` stale-pending 체크 확장.

- 쿼리를 `SELECT id, created FROM records WHERE delivery_state='pending' AND created<=? ORDER BY created ASC, id ASC`로 교체 (결정론적 나이순 — 최고령 우선).
- age 계산: `created`는 `today()`(`YYYY-MM-DD`) 저장이므로 `datetime.date.fromisoformat(created[:10])`로 파싱해 `(today - created).days`.
- WARN 메시지 형식(체크명·상태 불변, 메시지만 확장):
  `f"{n} records (oldest {oldest_created}, no auto-expiry): " + ",".join(f"{rid}({age}d)" for … 상위 10건) + (f" +{n-10} more" if n > 10)`
- OK 분기(`0 records`)와 exit-code 규약(WARN=1)은 불변.

의존성: 없음(독립). Phase 2와 병렬 실행 가능.

### Phase 2 — `drain_pending()` 신설 + CLI 배선

**Step 2.1** — `mem.py` D-39 doctor 섹션 직전(≈`mem.py:2978` 위)에 새 섹션 `# ---------- pending drain (maintenance --drain-pending) ----------`과 `drain_pending(stale_days=WORKING_TTL_DAYS, apply=False)` 함수 추가.

동작 계약:

1. 헤더 출력: `# maintenance --drain-pending  ({'APPLY' if apply else 'dry-run'}, stale-days={stale_days})`. `DB.exists()` 아니면 안내 후 `return 0`.
2. **consumed 정리** (유일한 파괴 대상):
   - `apply`일 때 `BEGIN IMMEDIATE` 선행 후 같은 write 트랜잭션 안에서 `delivery_state='consumed'` 재조회 (D-35 이중 가드 패턴 — `delete_record`/`lifecycle --apply`와 동일).
   - 각 건 `[consumed] {id} (tier={tier}, updated {updated}) — {'deleting' if apply else 'would delete'}` 출력.
   - `apply`: `_graveyard_append(con, rid, action="drain-consumed")` 실패 시 그 레코드 삭제 중단(fail-closed, stderr 경고) → 성공 시 `_delete_rows(con, rid)`. 전체 `con.commit()` 후 커밋 성공 건에 한해 `_append_write_event("drain-consumed", rid, tier=…, scope=…, rtype=…, snippet=_first_line(body))` — `lifecycle()`의 커밋-후-저널 순서(`mem.py:2361-2367`)를 그대로 따른다. actor는 기본 해석(`_write_actor()` → 운영자 수동 실행이므로 `manual`).
3. **정체 pending 보고** (보고 전용 — apply와 무관하게 절대 비파괴):
   - `created <= today - stale_days` pending을 `ORDER BY created ASC, id ASC`로 조회.
   - 각 건 `[stale-pending] {id} (created {created}, {age}d, type={type}) — discard candidate; consume then delete, or delete --force (human gate)` 출력.
   - `--apply`여도 pending 행에는 어떤 UPDATE/DELETE도 발행하지 않는다.
4. 요약: `→ consumed {n_consumed}{f' (deleted {n_deleted})' if apply else ''} · stale-pending {n_stale} (report-only, never auto-deleted)`.
5. dry-run이면 `dry-run; use --apply to drain consumed records` 안내, apply로 1건 이상 삭제 시 `run 'mem sync' to refresh dump.jsonl` 힌트 1줄 (doctor dump-freshness WARN 예방).
6. 반환 0 (진단성 명령 — 실패는 개별 stderr, 치명 실패 없으면 exit 0).

**Step 2.2** — CLI 배선 (`mem.py:3630-3636` 파서, `mem.py:3719-3720` dispatch).

- `mt` 파서에 추가:
  - `mt.add_argument("--drain-pending", action="store_true", help="Drain consumed delivery records and report stale pending discard candidates (dry-run by default)")`
  - `mt.add_argument("--pending-stale-days", type=int, default=WORKING_TTL_DAYS, help="Report pending records older than this many days as discard candidates (default 21)")`
- dispatch 분기:
  ```python
  elif args.cmd == "maintenance":
      if args.drain_pending:
          sys.exit(drain_pending(stale_days=args.pending_stale_days, apply=args.apply))
      sys.exit(maintenance(squash_days=args.squash_days, apply=args.apply))
  ```
  `--drain-pending` 지정 시 git squash 경로에 진입하지 않으므로 store가 git repo가 아니어도 동작한다. 기존 `maintenance` 시그니처·동작은 무변경.
- `maintenance` help 문자열을 두 모드가 드러나게 갱신 (`help="Squash auto-sync dump history (default) or drain delivery-state records (--drain-pending); dry-run by default"`).

의존성: Step 2.2는 Step 2.1 이후. Phase 1과는 독립.

### Phase 3 — 회귀 테스트 `tools/memory/pending_drain.test.sh` 신설

**Step 3.1** — `mem_cluster_j.test.sh` 골격 복제(격리 env·`seed()`·`ok`/`bad`·`trap`), 새 파일 `tools/memory/pending_drain.test.sh` (실행권한 부여). 케이스:

1. **doctor 나이순**: pending 3건 seed(created 40d/30d/25d 전, 순서 뒤섞어 삽입) → `mem doctor` 출력에서 `[WARN] stale-pending` 존재 + 최고령 id가 목록 선두 + `oldest {날짜}` 문자열 + `({age}d)` 주석 확인.
2. **doctor 호환**: stale pending 0건 → `stale-pending` OK `0 records` 유지, exit 0.
3. **drain dry-run 비파괴**: consumed 2건 + stale pending 2건 + fresh pending 1건 seed → `maintenance --drain-pending` 실행 후 `records` 총계 불변, 출력에 `[consumed]` 2건·`[stale-pending]` 2건·fresh pending 미표시, `would delete`·`dry-run` 문구 확인.
4. **drain --apply consumed 삭제**: 3번 fixture에서 `--apply` → consumed 2건 DB에서 소멸 + FTS 행 소멸 + graveyard에 `_action":"drain-consumed"` 2줄 + write-events에 `"action": "drain-consumed"` 2줄.
5. **drain --apply pending 인간 게이트**: 같은 실행 후 stale/fresh pending 전건 생존 + `delivery_state='pending'` 불변 + 출력에 `never auto-deleted` 확인.
6. **--pending-stale-days 경계**: `--pending-stale-days 5`에서 created 6d 전 pending은 후보, 4d 전은 비후보.
7. **squash 경로 무회귀**: `--drain-pending` 없이 `mem maintenance` → 기존 `[maintenance] store is not a git repository` 메시지(격리 store는 비-git) + exit 0.
8. **consumed 비재출현**: type=handoff consumed 1건 seed → `mem doctor` 실행(접속 정규화 경유) 후 여전히 `consumed` — `mem.py:723` ordinary-only 승격 가드 회귀 확인.

### Phase 4 — 검증 실행

**Step 4.1** — §5 검증 명령 전부 실행, 신규+기존 스위트 green 확인. Phase 1–3 완료 후.

## 4. 리스크 (Risks)

- **기존 테스트 grep 계약**: `mem_cluster_j.test.sh:267`이 `\[WARN\] stale-pending`을 grep — 체크명·상태 문자열 보존 필수 (Step 1.1이 메시지 본문만 확장하므로 충족).
- **graveyard fail-closed 순서**: graveyard 실패 시 해당 건 삭제를 건너뛰되 나머지 진행 — `lifecycle --apply` 선례(`mem.py:2352-2360`)와 동일하게 처리해야 부분 실패에서 데이터 손실이 없다.
- **저널 시점**: write-event는 반드시 `con.commit()` 후 기록 (커밋 실패 시 유령 이벤트 방지 — `lifecycle()` 선례).
- **dump 신선도**: `--apply` 후 다음 `mem sync`까지 doctor `dump-freshness` WARN 가능 — 출력 힌트로 완화(설계 의도, 자동 sync 미도입).
- **created 파싱**: distill 경유 등으로 `created`가 timestamp일 가능성에 대비해 `[:10]` 슬라이스 후 파싱 (실패 시 해당 건 age를 `?d`로 표기하고 계속 — 진단 경로에서 예외로 중단 금지).
- **범위 준수**: pending에 대한 어떤 자동 전이(auto-consume·auto-expire 포함)도 추가하지 않는다 — PRD D-35 "consume만 일반 전이" 계약 위반이 되기 때문.

## 5. 검증 (Verification)

실행 스테이지 이후 test 스테이지가 소비할 명령 (worktree 루트 `/home/Uihyeop/agent_setting-wt/pending-drain`에서):

```bash
python3 -m py_compile tools/memory/mem.py
bash tools/memory/pending_drain.test.sh          # 신규 — FAIL=0 확인
bash tools/memory/mem_cluster_j.test.sh          # doctor/log/저널 무회귀
bash tools/memory/mem_cluster_e_gamma.test.sh    # graveyard·delete 경로 무회귀
bash tools/memory/mem_retrieval_v14.test.sh      # pending 보호(D-35) 무회귀
# 스모크 (격리 store, 실 runtime 비접촉):
MEM_STORE="$(mktemp -d)" MEM_PROJECTS="$(mktemp -d)" \
  python3 tools/memory/mem.py maintenance --drain-pending
```

수용 기준: 신규 스위트 8케이스 전부 ok, 기존 3개 스위트 기존 대비 FAIL 증가 0, `--apply` 없는 어떤 경로에서도 레코드 수 변화 0, `--apply`에서도 pending 행 변화 0.
