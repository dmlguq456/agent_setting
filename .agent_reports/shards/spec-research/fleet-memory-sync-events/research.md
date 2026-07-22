# Research — sync/migrate 흡수의 write-event 저널 편입 (fleet-memory-sync-events)

> route rt-4fb68fb6acaefc97 · node research · 2026-07-22
> 대상: unified-memory PRD D-37 (§5.12.1) × agent-fleet-dashboard PRD F-19 (§4.7) / F-35f (§4.11)
> 코드 기준: worktree `fleet-memory-sync-events` @ `83870807`

## 1. 확정 사실 — 흡수 경로는 저널 이벤트 0

- `sync()` (`tools/memory/mem.py:3555`)는 `migrate(apply=True)`(:3560) → `lifecycle(apply=True)`(:3564) 순으로 실행한다. lifecycle은 `lifecycle-expire` 이벤트를 방출하지만(`mem.py:2365-2367`), **migrate 흡수는 4개 소스 루프 전부 `write_record(..., quiet=True)`를 `journal_action` 없이 호출**한다:
  - auto-memory (`projects/<enc-cwd>/memory/*.md`): `mem.py:2119`
  - post-it (registry + cwd): `mem.py:2165`
  - user_profile: `mem.py:2186`
  - legacy md-file: `mem.py:2215`, `mem.py:2220`
- `write_record()` (`mem.py:1000`)는 `journal_action`이 truthy일 때만 `_append_write_event()`를 부른다(:1048, :1074, :1112). 현재 이를 넘기는 호출자는 CLI `add`(:3739)와 `note`(:3743)뿐이다.
- 따라서 SessionEnd sync가 흡수하는 레코드는 **DB에는 생기되 write-events.jsonl에는 흔적이 없다**. D-37의 "모든 변이 경로" 열거(add/note/consume/reinforce/merge/prune/graduate/reattribute/delete/restore/lifecycle-expire)에 흡수가 빠져 있고 코드도 그 열거대로만 구현돼 있다 — spec·코드 동시 공백.
- 테스트 갭: `tools/memory/mem_cluster_j.test.sh`는 add/note/restore/lifecycle-expire/actor 결정론을 커버하나 migrate/sync 흡수 저널 케이스는 0건.

## 2. 논리 cwd 파생 — 프로세스 cwd 폴백은 흡수에 부적합

`_append_write_event()`의 현행 cwd는 `MEM_CWD` env 우선, `os.getcwd()` 폴백이다(`mem.py:1279`). sync는 세션 cwd에서 실행되지만(`adapters/codex/bin/preflight.sh:302`, `adapters/opencode/bin/preflight.sh:751` — 둘 다 `(cd "$cwd" && … mem.py sync)`), migrate는 **모든** 프로젝트의 auto-memory와 registry의 **모든** post-it을 훑는다. 프로세스 cwd 폴백을 그대로 쓰면 전 흡수 이벤트가 sync를 돌린 레포로 오귀속된다.

원천별 파생 가능 논리 cwd (fleet `_repo_key` → `project_of()`는 **절대경로**를 기대한다 — `tools/fleet/collectors/memory.py:103-118`, `tools/fleet/model.py:74`):

| 원천 | 파생 | 앵커 |
|---|---|---|
| auto-memory | `mp.parent.parent.name`(인코딩 cwd `-home-…`)을 `_decode_enc_cwd()`로 실존 절대경로 복원; 실패(사멸 경로) 시 생략 | `mem.py:2106,2109`, decode `mem.py:375` |
| post-it | `root_dir = pi.parent.parent` = 레포 루트 절대경로(post-it은 `<repo>/.agent_reports/post-it.md`, 존재 보장 :2138) | `mem.py:2147` |
| user_profile | global 스코프, 레포 귀속 없음 → 생략 | `mem.py:2186` |
| md-file | legacy `meta.cwd_origin`이 인코딩 cwd·절대경로로 decode될 때만; 아니면 생략 | `mem.py:2213` |

주의: migrate가 이미 쓰는 `_canonical_cwd_key()`(:2117) 출력은 `git:`/`id:` project_key 형식이라 `project_of()`와 **불일치** — 저널 `cwd`에는 decode된 절대경로를 써야 한다. cwd 부재 이벤트는 collector가 by_repo에서 정직 생략하되 recent/오늘 집계에는 포함한다(기존 tolerant 계약, `collectors/memory.py:190-193`). `project_of`의 `-wt`/`_worktrees` 접기로 worktree 경로도 부모 레포로 정상 귀속된다.

## 3. Fleet 호환 action/actor 어휘 — 신규 어휘 불요

collector 상수(`collectors/memory.py:23-26`): `ADDED_ACTIONS=("add","note")`, `EXPIRED=("lifecycle-expire",)`, `PRUNED=("prune","delete","merge")`, `DISTILL_ACTORS=("distiller","curator")`.

**권고: `action="add"` + `actor="sync"`.**

- `WRITE_ACTORS`(`mem.py:80`)에 `"sync"`가 이미 예약돼 있고 현재 사용처 0 — 이번이 예약의 이행.
- `today.added` 집계·`by_repo`·`recent`에 자연 편입, collector diff 0 → F-35f "기존 collector가 그대로 소비한다" 충족.
- `mem log --actor sync` 필터 즉시 동작(`--actor choices=WRITE_ACTORS` `mem.py:3708`; `--action`은 자유 문자열 :3706).
- actor 결정은 lifecycle 선례(`mem.py:2363`)대로 `_write_actor(default="sync")` — `MEM_ACTOR` 명시 오버라이드 보존. sync는 main SessionEnd 경로라 `MEM_DISTILL` 미설정이 정상이며 distiller 오판 여지는 실질 없음.
- 대안(기각 권고): 신규 action `migrate-absorb`는 recent/by_repo에는 뜨나 `today.added`에서 빠져 collector 개정(=양 spec 동기 의무 발동)이 필요 — F-35f 취지에 반함.

## 4. 중복 이벤트 방지 — idempotency 조건

- 1차 키: migrate의 `existing_src` 사전 스킵(`mem.py:2088-2098`; 사용처 :2110, :2161, :2181, :2203) — source가 DB에 있으면 `write_record` 자체를 부르지 않으므로 재sync는 무이벤트. 단 **source는 신규 INSERT 분기에서만 저장**된다.
- 구멍: `find_dup` body-dedup 분기(`mem.py:1052-1077`)는 strength+1만 하고 **source를 기록하지 않는다** → 기존 레코드와 body가 같은 신규 소스는 매 sync마다 dup 분기에 재진입한다(현행 재강화 반복 동작). 여기서 journal_action을 무조건 넘기면 sync마다 이벤트가 재방출된다.
- **권고 조건: 흡수 이벤트는 신규 레코드 생성(INSERT 분기, `mem.py:1096-1114`)에서만 방출** — 소스 키당 최대 1회, source-idempotent 재실행 0회가 구조적으로 보장된다. dup-reinforce·source-upsert 분기는 흡수 맥락에서 무방출. 수동 `add`/`note`의 현행 3분기 방출 동작은 불변(additive kwarg — 예: `journal_on_create_only` — 또는 동등한 create-only 전달 방식).
- dup 분기에 source를 백필하는 대안은 기존 레코드 변이라 이번 범위(역사 데이터 무변이) 밖 — 별도 결정 사항으로만 기록.

## 5. PRD 규범 문구 권고

**unified-memory PRD §5.12.1 D-37** (개정 3점):

1. 변이 경로 열거에 흡수 명시: "… lifecycle-expire, **및 sync/migrate 흡수(신규 레코드 생성 시)**".
2. cwd 규정 보강: "흡수 이벤트의 `cwd`는 흡수 **원천의 논리 cwd**다 — auto-memory는 인코딩 프로젝트 디렉토리의 decode 절대경로, post-it은 해당 레포 루트, global(user-profile)·decode 불가 원천은 정직 생략. 프로세스 cwd·`MEM_CWD` 폴백은 흡수 이벤트에 적용하지 않는다(오귀속 방지)."
3. idempotency·어휘 규정: "흡수 이벤트는 `action=add`·`actor=sync`(기존 어휘, collector 무변경)로 소스 키당 신규 생성 시 1회만 방출한다. source-idempotent 재실행과 body-dedup 재강화 분기는 방출하지 않는다."

**agent-fleet-dashboard PRD** (동기 2점):

1. **F-19** 소스 절에 1줄: "sync/migrate 흡수 이벤트도 D-37 저널로 편입된다(`action=add`·`actor=sync`) — collector 어휘·집계 로직 불변, `by_repo` 귀속은 흡수 원천 레포(저널 `cwd`)."
2. **F-35f**: "현행 journal에 `cwd`가 없다는 오래된 주석만 정정한다"에 이어 "흡수 이벤트의 `cwd`는 원천 논리 cwd이며 프로세스 cwd가 아니다"를 명시(포맷 양 spec 동기 조항 이행).

## 6. 리스크

- **첫 대량 흡수의 rotation 밀어내기**: 최초 apply에서 수백 이벤트가 256KB/500줄 rotation을 돌려 기존 recent 관측을 밀어낼 수 있다(관측 손실, 데이터 손실 아님 — fail-open 계약 그대로).
- **`sid` 공백**: sync 프로세스에 `MEM_SID` setter가 없어 흡수 이벤트 sid=""가 기본 — F-19 "`sid`가 화면 세션으로 해석될 때만 ⟵ 태그" 규칙과 정합(정직 생략)이므로 결함 아님. 명시 기록만.
- **인접 무저널 경로 잔존**: `import_dump()`(`mem.py:1845`)는 `write_record`를 거치지 않고 직접 INSERT — 저널 무방출. 복구/부트스트랩 경로라 이번 계약 범위 밖, D-37 해석 결정 필요 사항으로 기록.
- **dup 분기 반복 재강화**: §4의 source 미기록 동작은 이벤트와 무관한 기존 동작 — 이번 변경이 악화시키지 않으나, 향후 백필 결정 시 저널 계약 재확인 필요.

## 7. 수용 기준 (testable)

1. 격리 스토어에서 auto-memory 파일 1개를 `migrate(apply=True)`로 흡수 → write-events.jsonl에 `action=add`·`actor=sync`·`cwd=<decode된 절대경로>` 이벤트 정확히 1건.
2. 직후 `sync()`(또는 migrate 재실행) → 이벤트 증가 0.
3. 기존 레코드와 body 동일한 신규 post-it bullet 흡수(dup 분기) → 이벤트 0, strength만 +1(현행 유지).
4. 사멸 경로(decode 불가 인코딩 디렉토리) 원천 흡수 → 이벤트는 남되 `cwd` 부재, collector `by_repo` 제외·`recent` 포함.
5. user-profile 흡수 → `cwd` 생략, `today.added` 집계 포함.
6. `mem log --actor sync`가 흡수 이벤트만 반환.
7. fleet `collectors/memory.py` diff 0으로 `today.added`/`by_repo`/`recent` 반영 — `tools/fleet/tests/test_f19_memory.py` 무수정 통과.
8. `tools/memory/mem_cluster_j.test.sh` 전 케이스 통과(수동 add/note 3분기 방출 동작 회귀 0) + 흡수 저널 신규 케이스 추가.
