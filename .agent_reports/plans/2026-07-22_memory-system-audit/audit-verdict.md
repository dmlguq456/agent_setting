# Memory System Audit — 통합 판정 (synthesis)


## audit_map
# 메모리 시스템 감사 — 통합 판정 (2026-07-22)

근거 파일 (전문 판독 완료):
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_memory-system-audit/_internal/legacy-content-sweep.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_memory-system-audit/_internal/memory-architecture.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_memory-system-audit/_internal/recall-reliability.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_memory-system-audit/_internal/oss-landscape.md`

## 1. 시스템 지도 (실태)

**두 개의 메모리 시스템이 병존한다.** (a) 하네스 DB계: `memory/memory.db` SQLite WAL+FTS5, 실측 3.6MB / 1,378건 — "602MB DB"는 신화(406MB는 memory/.git loose-object 축적, ~156MB는 고아 상태파일 39,167개의 블록 오버헤드). (b) Claude 네이티브 파일계: `~/.claude/projects/*/memory/*.md` — guard를 우회해 매일 쓰이고, 실제 메인 세션 컨텍스트에 전문 도달하는 쪽은 이쪽이다. DB는 SessionStart에 15줄 keyhole(durable 462건 중 4건)만 주입한다.

**생명주기 실태**: SessionStart inject 작동, SessionEnd curator(sonnet) 소량 지속, **Claude turn-nudge 증류는 7/15 herdr 전환 이후 무동작 정황**(codex 어댑터는 7/21까지 활동). **dump git 미러는 7/14 18:14부터 조용히 사망** — 0바이트 stale `index.lock`이 모든 `git add`를 rc=128로 죽이고 `_commit_dump`(mem.py:147-172)가 실패를 전부 삼킴 → 8일치 기억 변경이 재해복구 미러에 없다. pending 30건은 보호는 되나 배수가 안 됨(consume 전 기간 14회).

## 2. 화석화 총량 (전수 스윕)

35건: **KEEP 14 / 프로필 이설 10 / 메모리 아이템 이설 4 / 사용자 판단 필요 7.** 최악 사례:

- **활성 모순 2건** — 스테일 사본이 프로필 진실과 싸우는 중: (1) analyze-user 스킬의 예시가 프로필 01 §A7이 명시적으로 대체한 hex 추정치(#3F8C5C/#A0152A)를 화석화 — 프로필을 *쓰는* 스킬 안에서 (정답은 pptx 추출값 #548235/#C00000); (2) analyze-project 스킬이 사용자의 실제 speech 레포 TF_Restormer/SR_CorrNet을 **이미지 복원**(MDTA/GDFN/DIV2K/PSNR)으로 서술 — 프로필 05/07과 정면 충돌.
- **스펙트로그램 윈도우 삼조**(figure-gen 8k=256/16k=512/48k=1024, "domain LAW" 라벨): 도구 미강제(figure-semantic-verify.py는 윈도우를 검사 안 함), 값 자체가 EN/KO 원본 분기로 미확인 — 전사 추정을 LAW로 굳힐 위험.
- **날짜 박힌 사용자 결정의 삼중·이중 복제**: PPTX 출력 규칙(2026-05-09) 3회, DPI 지시(2026-05-12) 2회, camera-ready cohesion 사건+한국어 원문 인용 2회, figure-craft 정책(2026-05-28) 3회(프로필 01이 SoT).
- **data-script 메트릭 표**: 프로필 04와 대량 중복 + 표 강조 방식이 프로필 01(bold-only)·03(행 bold+열 underline)과 3파전 충돌.
- **메모리 안전 문서의 표류**: partial-body `mem add --source user-profile:*`가 **프로필 전체를 대체**하는 upsert footgun이 editorial/_NOTES에만 존재.
- 반면 9회 반복되는 프로필 preload 블록은 **올바른 패턴**(내용이 아닌 포인터) — `_shared` fragment로 표류만 잡으면 됨.

## 3. 경로별 신뢰성 판정

| 접근 경로 | 판정 | 근거 |
|---|---|---|
| `mem profile` 읽기 (올바른 home) | **신뢰 가능** | 0.09s, 3회 byte-identical, exit-2 실패모드 깨끗, 동시 reader 무영향 |
| 워커의 프로필 읽기 (오늘 기준) | **신뢰 가능 (조건부)** | Bash 전면 허용, wrapper가 AGENT_HOME 미설정 → primary로 해석. 단, 유닛 카탈로그에 recall 지시 0건 — 지시가 실려야만 회수 시도가 발생 |
| AGENT_HOME이 memory/ 없는 체크아웃을 가리킬 때 (= 모든 worktree, drill 스타일 export) | **파손** | mem.py가 조용히 빈 memory.db를 새로 만들고 "aspect not found" 보고 — relocation 킬러, 어떤 테스트도 미커버 |
| durable 레코드 의미 회수 (recall.sh) | **신뢰 불가 (런타임 의존으로는)** | 한국어 회수 구조적 저하(SQLite 3.31.1, trigram 부재, LIKE 무순위 폴백) + cwd 키 split-brain(7/15-21 최고가치 교정 기억 24건이 기본 recall에 불가시, legacy 키 118건+ 재생산 중) + OR-token 노이즈 + type 251종 파편화 |
| inject 경로 | **keyhole** | 15줄/4건 cap — 지식 전달 채널로 부적합 (설계상 요약일 뿐) |
| dump 재해복구 미러 | **사망 (7/14~)** | stale index.lock, 침묵 실패 |
| 비-git cwd에서 project recall | **조건부** | `--all` 없으면 20건→2건 (global만) |

## 4. 종합 판정

**프로필 경로로의 이설은 조건부 GO, 일반 durable-recall 의존 이설은 VETO.**

- 프로필 경로는 기계적으로 견고하나 소비가 문서 지시뿐(게이트 없음)이고, 유닛에 recall 지시가 전무하다. 이설 = 항상-존재하던 지시를 회수 의존으로 바꾸는 것이므로, **선행조건 3개**가 충족되기 전에는 어떤 이설도 금지: (P1) dump 미러 복구 — 미러가 죽은 DB로 콘텐츠를 옮기는 건 내구성 하향, (P2) 빈-스토어 생성 경로 가드 — 현재는 drill 환경에서 "지식이 존재하지 않는다"는 확신을 주는 형태로 실패, (P3) 소비 유닛/스킬에 명시적 `mem profile` 읽기 라인 추가 + 같은 변경에서 화석 원본 삭제(모순 2건이 증명하듯, 삭제 없는 이설은 둘 다보다 나쁘다).
- 일반 durable 레코드를 depth-2 워커의 런타임 의존으로 삼는 것은 cwd split-brain + 한국어 저하 + keyhole이 고쳐질 때까지 **거부**. 날짜 박힌 사용자 결정 4건의 메모리 아이템화는 허용하되, 유닛에 한 줄 운영 규칙을 남겨 회수 실패가 동작 파손이 되지 않는 형태로만.
- 모든 프로필 병합은 `/analyze-user` 또는 `/post-it promote` 경유 필수 — raw `mem add`는 source-keyed upsert로 대상 프로필을 파괴한다. 프로필 01/04는 ~7-10K 토큰 예산 근접, 병합 시 다이어트 필요.
- OSS 검증: Memobase가 우리의 compiled-profile+inject 설계를 독립 수렴으로 검증, claude-mem이 hooks+SQLite 기질을 검증. 2026 합의 스택 5요소 중 hybrid retrieval과 temporal supersession이 결여 — 풀 플랫폼/그래프DB/상주 데몬은 anti-fit(broker 금지 원칙과 충돌).

## relocation_policy
이설 판정 규칙 (신뢰성 실측에 근거):

**하네스에 남긴다** — (1) 결정론적 도구가 실제로 강제하는 무결성 게이트(figure-semantic-verify가 검사하는 항목만; "LAW" 라벨이 아니라 검사 코드가 기준), (2) 라우팅·I/O 계약·dispatch 메커니즘 등 하네스 동작, (3) 범용 엔지니어링 지식(ML 디버그 표, 디자인 doctrine, PDF 기하·Playwright 레시피), (4) 선언된 예시(단, 사용자 실물과 모순되는 예시는 예외 — 즉시 수정 대상).

**프로필(global scope)로 옮긴다** — 사용자 취향·스타일·도메인 관례(matplotlib 기본값, 메트릭 표 델타, 베뉴 선호, 한국어 행정 register). 단 4중 조건: (a) 선행조건 P1(dump 미러 복구)·P2(빈-스토어 가드) 완료 후에만, (b) 소비하는 유닛/스킬에 명시적 `mem profile <aspect>` 읽기 라인을 같은 변경에서 추가 — 프로필 읽기는 실측상 유일하게 신뢰 가능한 회수 경로이나 소비 지시가 없으면 워커는 도달 경로가 없다, (c) 화석 원본을 같은 변경에서 삭제/포인터화 — 남기면 스테일 사본이 프로필 진실과 싸운다(모순 2건 실증), (d) 병합은 반드시 /analyze-user 또는 /post-it promote 경유 — raw mem add partial-body는 프로필 전체를 대체 파괴.

**durable 메모리 아이템으로 옮긴다** — 날짜 박힌 사용자 결정·사건 provenance(PPTX 규칙, DPI 지시, cohesion 사건 인용). 단 아카이브 용도로만: 유닛/스킬에 한 줄 운영 규칙을 남겨, 회수 실패가 절대 런타임 파손이 되지 않는 형태로. 의미 recall을 런타임 의존으로 삼는 이설은 한국어 회수 저하(trigram 부재)·cwd 키 split-brain(legacy 키 재생산 중)·inject keyhole(4건 cap)이 고쳐질 때까지 **전면 거부(veto)**. depth-2 워커가 recall.sh 성공에 의존하는 어떤 설계도 현재 금지.

**우선순위 원칙**: 이설보다 모순 제거가 먼저다. 스테일 hex 예시와 image-도메인 레포 서술은 이설 여부와 무관하게 지금 프로필 진실을 오염시키고 있다.

## improvement_candidates
- 1. [차단급, ~1분, 메인 세션이 직접] memory/.git의 stale index.lock 삭제 + 밀린 dump commit/push — 8일째 죽은 재해복구 미러 복구. 모든 이설의 선행조건 P1. 매일 미룰수록 미미러 데이터 창이 넓어짐.
- 2. [차단급, ~1시간] mem.py 빈-스토어 생성 가드: 해석된 STORE에 기존 memory.db가 없으면 생성 대신 거부(또는 큰 경고)+해석된 DB 경로를 에러에 출력, 회귀 테스트 추가 — 현재 어떤 스위트도 미커버인 최고위험 경로(drill식 AGENT_HOME export가 이설된 지식을 '존재하지 않음'으로 보이게 함). 선행조건 P2.
- 3. [높음, ~반나절] mem.py:1807 migrate()의 cwd_origin을 project_key 정규화로 수정 + legacy 키 118건+ 일회성 v6 remap — 7/15-21의 최고가치 사용자 교정 기억 24건(no-broker-revival, incident-0046 등)이 기본 recall에서 불가시인 split-brain 해소. 수정 없이 remap만 하면 흡수 경로가 legacy 키를 재생산하므로 반드시 동시에.
- 4. [높음, ~반나절] memory/.git gc/repack(406MB→수MB) + amend-rolling-commit 설계 재검토(매 sync ~1.2MB blob 고아화가 근본 원인) + 고아 상태파일 39K개 삭제 + .distill-state-* GC 소유자 추가 — 단, amend vs plain-commit은 사용자 결정 사항.
- 5. [중간, ~1일, OSS 채택 1순위 실현] 워커 recall 도달 경로 공식화: 유닛 카탈로그에 recall 지시 0건인 현 상태 해소 — 이설 대상 유닛에 mem profile 읽기 라인 추가(_shared/profile-preload.md fragment로 9회 반복 블록 통합, 표류 동시 제거). 선행조건 P3이자 dev/_NOTES가 이미 후보로 지목.
- 6. [중간, ~1일, OSS 채택 2순위] 미니 retrieval eval 하네스(LongMemEval-V2 패턴 축소판): 이설 사실 1건당 고정 쿼리 1개, recall.sh/mem profile top-k 회수를 tests/에서 assert — 이설을 일회성 감사에서 회귀-테스트화. OR-token 노이즈·현실 규모 정밀도의 최초 측정 장치도 겸함.
- 7. [중간, ~15분 프로브 후 판단] turn-nudge 사망(7/15~) 실측 확인: herdr pane Claude 세션에서 MEM_NUDGE_INTERVAL=1로 1턴 검증 — UserPromptSubmit 미발화인지 D-42 가드 오발인지 판별 후 수리. 현재 mid-session 증류가 전멸 상태라 curator trickle만 남음.
- 8. [중간, ~1-2일] 한국어 회수 복구: pysqlite3-binary 등으로 SQLite 3.34+ 번들해 trigram 활성화, 또는 mem.py에 CJK bigram 토큰화 구현 — 최근 기억 대부분이 한국어인데 무순위 LIKE 폴백에 의존 중. 방식은 사용자 결정.
- 9. [중간, ~1-2일, OSS 채택 3순위] supersede-on-contradiction(Graphiti 의미론만 차용): records에 valid_from/superseded 컬럼 + apply-distill-actions.py에 모순 신규 저장 시 구버전 supersede 마킹 — 그래프DB 없이 SQLite로. 삭제 대신 시간적 무효화라 사용자-교정 기억에 안전.
- 10. [낮음, ~2시간, 사용자 결정 후] 활성 모순 2건 수정: analyze-user의 stale hex 예시(#3F8C5C→프로필 01 §A7 정확값 또는 genericize), analyze-project의 image-도메인 TF_Restormer 예시(speech 사실로 교정 또는 genericize).
- 11. [낮음, ~30분] mem-upsert footgun 문서를 editorial/_NOTES에서 core/MEMORY.md(또는 tools/memory 문서)로 승격 — 프로필 파괴급 데이터-손실 위험이 residue 파일에 표류 중.
- 12. [낮음, ~1시간] pending 배수 정책: 30건 적체(최고령 6/26)·만료 없음 — doctor 출력에 정체 pending 노출 + 소비/명시 폐기 절차. 아울러 폐기 no-op mem-recall-inject.sh의 live settings 등록 잔재 제거(프로젝션 표류 정리).

## oss_adoptions
- 워커용 memory-as-explicit-tool (Mem0/Hindsight/LangMem hot-path 패턴): recall.sh/mem profile을 dispatch 워커가 프롬프트 지시로 호출 — 도구는 이미 존재, 유닛 파일의 포인터만 결여. 도메인 상수 이설의 하드 선행조건. 실측(Stream 3)이 워커 도달 가능성을 이미 확인했으므로 순수 지시-플러밍 작업.
- 미니 LongMemEval-V2식 retrieval eval 하네스: 이설 사실별 고정 쿼리 세트 + top-k assert를 tests/에 — 이설을 회귀-테스트화하고 recall 정밀도의 최초 측정 기준선 확보.
- Graphiti식 temporal supersession의 의미론만 차용: SQLite 컬럼(valid_from/superseded) + applier 로직 — 그래프DB·데몬 없이. 사용자-교정 기억에 자동 decay 대신 명시적 무효화.
- Memobase 검증에 따른 프로필 강화: 자유문 프로필 문서 대신 typed slot + per-slot 갱신 규칙 — 이설 대상('speech 도메인 상수')이 프로필 05의 개별 회수 가능한 typed entry로 안착.
- claude-mem식 FTS5+vector hybrid recall: eval 하네스(#2)가 lexical 실패를 실측으로 보여줄 때만 채택 — 선제적 vector 도입은 보류.
- Anti-fit 확정: 풀 플랫폼(Letta/MemOS/Cognee/Zep 서버)·그래프DB 백엔드·auto-observation firehose·공격적 자동 decay·Mem0 의존(OSS graph 유료 게이트) — 상주 데몬 금지 원칙 및 큐레이션 계약과 충돌.

## user_decisions_needed
- 스펙트로그램 윈도우 삼조 값 확인: 8k=256/16k=512/48k=1024이 맞는가? (EN 원본 512/400/256과 분기, KO 기준으로 편집 해소된 미확인 값) — 맞다면 figure-semantic-verify.py에 결정론 검사로 승격(하네스 유지)할지, 프로필 04로 이설할지. no-resampling 규칙도 동일 선택.
- 표 강조 방식의 표면별 정본 확정: 논문 bold-only(프로필 01) vs data-script의 bold+underline-2위 vs 슬라이드 행-bold+열-underline(프로필 03) — 확정 전에는 data-script 메트릭 표의 프로필 04 병합 불가.
- 베뉴 4-tier 사다리(research-survey): 사용자 취향으로 프로필 05 §6에 이설(depth-2 검색 워커에 recall 의존 발생) vs 파이프라인 정렬 메커니즘으로 하네스 잔류+프로필 상호참조.
- fact-check의 speech 충돌쌍 사전: 프로필 05로 이설 vs 의도적으로 profile-free로 설계된 유닛의 현상 유지.
- 두 활성 모순의 처리 방향: 실제 값/사실로 교정 vs 가공 예시로 genericize. 연장선에서, 실제 프로젝트명(TF_Restormer 등)을 예시로 쓰는 스킬 참조 ~12곳의 일괄 genericization을 원하는가, 실물 예시 유지를 선호하는가.
- dump 미러 설계: amend-rolling-commit 유지+주기적 gc 훅 vs plain commit+주기적 squash — amend 루프가 406MB 축적의 근본 원인이므로 lock 제거(즉시 조치)와 별개로 설계 결정 필요.
- 한국어 회수 복구 방식: SQLite 3.34+ 번들(pysqlite3-binary, 향후 업그레이드 시 랭킹 동작이 조용히 바뀌는 점 포함) vs mem.py 자체 CJK bigram 토큰화.
- legacy cwd 키 118건+ v6 remap 승인: 라이브 DB를 건드리는 일회성 마이그레이션 — 24건이 최근 고가치 사용자 교정이라 가치는 높으나 실행 주체·시점 승인 필요. index.lock 삭제(라이브 memory repo 접촉)도 메인 세션 직접 실행 승인 대상.
- mem-upsert footgun 문서의 최종 거처: core/MEMORY.md vs tools/memory 문서.