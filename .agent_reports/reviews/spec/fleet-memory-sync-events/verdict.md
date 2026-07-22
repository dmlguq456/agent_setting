# Review Verdict (r2) — sync/migrate 흡수의 write-event 저널 편입

- Date: 2026-07-22
- Route: `rt-4fb68fb6acaefc97` · node `review` (bounded, read-only) · parent `fleet-memory-sync-spec-owner-r2`
- Reviewed: `.agent_reports/shards/spec-research/fleet-memory-sync-events/research.md` (14:13, r1과 동일 판본)
- Prior round: r1 verdict(14:23) = FAIL 3건 — 그 요구(명시 actor 고정·전수 문장 상충 해소·no-backfill 봉인)는 이번 디스패치의 **승인 의미론으로 흡수·판정 완료** 상태. 본 r2는 그 승인 의미론을 기준으로 exact wording을 재판정한다.
- 코드 기준: worktree `fleet-memory-sync-events` @ `83870807` (shadow PRD = canonical PRD `diff -q` 무차이 실측)

## VERDICT: PASS — 필수 문구 수정 4건 반영 조건

research의 사실 주장은 전량 소스 실측으로 확정됐고, 제안 교정은 다섯 기준(최소성·내적 일관성·source-first·Fleet 호환·idempotency)을 모두 충족한다. 다만 §5 exact wording은 승인 의미론의 두 절("explicit sync actor", "no historical backfill")을 아직 완전히 봉인하지 못한다 — 아래 W1–W4를 PRD 트랜잭션에서 반영해야 하며, 반영 문구는 본 verdict에 확정본으로 제공한다. 추가 research 라운드는 불필요하다(모든 수정이 본 문서로 폐쇄 가능).

## 1. 반박 시도 결과 — 전 핵심 주장 소스 실측 확인

| # | Research 주장 | 실측 | 판정 |
|---|---|---|---|
| 1 | 흡수 경로 저널 0건 — migrate 4개 소스 루프 전부 `journal_action` 없는 `write_record(quiet=True)` | `mem.py:2119`(auto-memory) · `:2164`(post-it) · `:2186`(user_profile) · `:2215,2220`(md-file) 모두 미전달; `write_record`에 `journal_action=`을 넘기는 곳은 CLI `add`(`:3739`)·`note`(`:3743`)뿐. 기타 변이는 `_append_write_event` 직접 호출(consume `:2322` … drain-consumed `:3020`) | **확정** |
| 2 | 저널 게이트 3분기 | upsert `:1049` · dup-reinforce `:1075` · INSERT `:1113` 모두 `if journal_action:` 게이트 | **확정** (인용 라인 ±1~3 드리프트, 무영향) |
| 3 | cwd 폴백 오귀속 | `"cwd": os.environ.get("MEM_CWD") or os.getcwd()`(`:1279`); sync는 세션 cwd 실행(`adapters/codex/bin/preflight.sh:302`, `adapters/opencode/bin/preflight.sh:751` — `(cd "$cwd" && … sync)`); migrate는 전 프로젝트·전 registry post-it 순회 → 폴백 시 전 흡수 이벤트가 sync 실행 레포로 오귀속 | **확정** |
| 4 | `_canonical_cwd_key` 출력은 저널 `cwd`로 부적합 | `project_key`(`:335`)는 `git:`/`id:`/`root:`/enc 형식; 저널 cwd 계약(`:1275-1278` 주석 "consumers group it through project_of()")과 fleet `_repo_key`(`collectors/memory.py:106-121`)→`project_of`(`model.py:75`)는 파일시스템 절대경로 전제 → decode 절대경로 권고 타당 | **확정** |
| 5 | 원천별 논리 cwd 파생 | auto-memory 인코딩 디렉토리명→`_decode_enc_cwd`(`:375`, 실존 절대경로 or None) / post-it `pi.parent.parent`=레포 루트(`:2147`) / user-profile global 생략 / md-file `meta.cwd_origin` decode 시만 — 4행 전부 앵커 성립 | **확정** |
| 6 | `action=add`·`actor=sync` 기존 어휘, collector diff 0 | `WRITE_ACTORS`(`mem.py:80`)에 `"sync"` 예약·사용처 0(전역 grep); D-37 actor 집합에 `sync` 기등재; `ADDED_ACTIONS=("add","note")`(`collectors/memory.py:24`); `mem log --actor choices=WRITE_ACTORS`(`:3708`)·`--action` 자유 문자열(`:3706`); by_repo 정직 생략·recent/오늘 집계 포함은 기존 tolerant 계약(`:186-193` `if not rk: continue`) | **확정** |
| 7 | idempotency: create-only 방출이 유일 안전 실현 | `existing_src` 사전 스킵(`:2089-2098`; 사용처 `:2110,:2161,:2181/2186,:2203`); source는 INSERT 분기에서만 저장 — dup-reinforce 분기는 strength+1만·source 미기록이라 동일 body 신규 소스는 매 sync dup 재진입 → 무조건 방출이면 sync마다 재방출, create-only면 소스 키당 최대 1회 구조 보장. 동일 run 내 중복 src의 upsert 분기 도달도 create-only면 무방출 | **확정** |
| 8 | 리스크 3건 | rotation 256KB/500줄(`:1284-1288`) 최초 대량 흡수 시 recent 밀어내기 실재(관측 손실, fail-open) / `MEM_SID` setter 부재(전역 grep 0)→sid="" 정직 생략, F-19 `⟵` 규칙 정합 / `import_dump`(`:1845`) 직접 INSERT 무저널 — 범위 밖 기록 타당 | **확정** |
| 9 | 테스트 갭·앵커 | `mem_cluster_j.test.sh` migrate/sync 흡수 케이스 0건; `tools/fleet/tests/test_f19_memory.py` 실존 | **확정** |

**경미한 부정확 (비블로킹):** research §1 "cluster_j 테스트는 add/note/restore/lifecycle-expire/actor 결정론 커버"는 과소 서술 — 실제 11개 action 전부 + rotation + log 필터 커버. 핵심 주장(흡수 케이스 0건)은 유효.

## 2. 다섯 기준 판정 — 전부 충족

- **최소성**: D-37 개정 3점 + fleet PRD 2점 + additive create-only 전달(수동 add/note 3분기 방출 불변). 신규 action/필드/테이블/collector 변경 0.
- **내적 일관성**: dup-reinforce의 strength+1 영속은 "신규 흡수"가 아니므로 무방출 — 승인 의미론("무영속 반복 무방출")의 idempotent한 유일 실현이며 개정 #3이 명문화. W4 반영 시 "모든 변이 경로" 헤드라인과의 상충도 해소.
- **source-first**: 전 주장 코드 라인 앵커, 본 r2가 독립 재실측.
- **Fleet 호환**: add + 파일경로 cwd = 기존 소비 경로 그대로, F-19(§4.7)·F-35f(§4.11) 앵커 실존, "포맷 변경 시 양 spec 동기"(D-37 §5.12.4) 의무를 두 PRD 동시 개정으로 이행.
- **idempotency**: create-only + existing_src 이중 구조, no-backfill은 pre-existing source가 `existing_src`에 포함되어 구조적으로도 보장(W2로 명문 봉인).

## 3. 필수 문구 수정 (PRD 트랜잭션 반영 조건 — 본 문구로 확정)

- **W1 — 명시 actor 고정 (승인 의미론 "explicit sync actor" 이행, r1 지적 #1 유지)**: research §3의 `_write_actor(default="sync")` 실현 권고는 **기각** — `MEM_ACTOR`/`MEM_DISTILL` 선행 해석 때문에 standalone `migrate --apply`가 sync 아닌 actor를 낼 수 있어(`mem.py:1250-1257`) 승인 의미론과 모순. D-37 개정 #3에 다음을 명시: "흡수 이벤트의 actor는 ambient `MEM_ACTOR`/`MEM_DISTILL`과 무관하게 **literal `sync`** 다. 수동 add/note 및 기타 변이 경로의 기존 `_write_actor` 계약은 불변."
- **W2 — prospective-only/no-backfill 봉인 (승인 의미론 이행, r1 지적 #3 유지)**: D-37에 1문 추가: "이 계약은 prospective-only다 — 배포 전 저장된 레코드/source나 기존 journal에 대해 이벤트를 합성·backfill하지 않는다." 수용 기준에 1건 추가: "변경 전부터 동일 source가 DB에 존재하고 journal에 sentinel 행이 있는 fixture에서, 변경 후 최초 migrate가 신규 이벤트 0건(no backfill)."
- **W3 — 전수 문장 상충 해소 (r1 지적 #2 유지)**: 개정 #1의 열거 추가는 "…및 sync/migrate 흡수(신규 생성 시, **`action=add` 재사용** — 하단 idempotency 규정 참조)"로 쓰고, 개정 #3에 "existing-source skip·source-key upsert·body-dedup reinforcement 등 비-INSERT 흡수 경로는 흡수 `add` 이벤트를 방출하지 않는다(명시적 CLI 변이의 저널 계약과 별개)"를 명시해 "모든 변이 경로" 헤드라인의 예외 경계를 같은 절 안에서 폐쇄. cwd 예외 문구(개정 #2)는 기존 cwd 문장("`MEM_CWD` env 우선, 프로세스 cwd 폴백")과 같은 불릿에 인접 배치.
- **W4 — 수용 기준 정밀화**: ① 기준 1에 적대 환경을 결합 — 잘못된 프로세스 cwd + `MEM_CWD=/wrong/repo` + `MEM_DISTILL=1` + `MEM_ACTOR=curator` 상태에서도 이벤트가 정확히 `action=add`·`actor=sync`·`cwd=<decode된 원천 절대경로>` 1건. ② 기준 2의 "이벤트 증가 0"을 "**흡수(add·sync) 이벤트** 증가 0"으로 한정(sync()의 lifecycle이 만료 가능 픽스처에서 lifecycle-expire를 정당 방출할 수 있음).

위 반영 시 research §7의 기존 8개 기준은 전량 채택(기준 4의 사멸 경로 = `_decode_enc_cwd` None 실측 가능; 기준 7·8의 회귀 앵커 실존).

## 4. 불확실성·기록 사항

- Claude 어댑터 SessionEnd sync 실행 지점은 라인 실측하지 않음(codex/opencode 실측으로 오귀속 논증 성립, 결론 불변).
- `import_dump` 무저널·dup 분기 source 백필은 범위 밖 별도 결정 유지 — 이번 트랜잭션 포함 금지.
- 구현 단계 확인 항목: `_append_write_event`에 per-event cwd·actor 전달이 필요(현행 시그니처에 cwd 파라미터 없음) — additive 확장으로 기존 호출자 무영향이어야 함.
- r1의 기준선 실행 기록(test_f19_memory 26/26 · mem_cluster_j 33/33 PASS, spec-grounding read marker 미영속 경고)은 r1 아티팩트의 보고를 승계 기록만 하며 본 r2가 재실행하지 않았다.
