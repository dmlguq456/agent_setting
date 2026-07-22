# Memory Architecture Map — Stream 2 (매우 강하게)

조사일: 2026-07-22 · 조사 방식: 전부 read-only (DB는 `file:…?mode=ro` URI, 파일 편집 없음)

## 0. Headline — 가장 날카로운 구조적 약점 (심각도순)

| # | 약점 | 한 줄 요약 |
|---|---|---|
| W1 | **dump 미러 8일째 조용히 사망** | `memory/.git/index.lock` (2026-07-14 18:14 생성, 0바이트, 소유 프로세스 없음)이 남아 모든 `git add`가 rc=128로 실패. `_commit_dump()`(mem.py:147-172)는 실패를 전부 삼킴 → 마지막 커밋 7/14, HEAD ahead-1 미push, 이후 8일치 기억 변경이 재해복구 미러에 없음 |
| W2 | **"602MB DB"는 신화 — 실제 DB는 3.6MB** | 602MB = `.git` 406MB(전부 loose object 3,590개 314MiB + 살해된 git의 tmp_obj 쓰레기 325개 88.75MiB, pack 0개) + 고아 상태파일 39,167개의 4KB 블록 오버헤드 ~156MB + 실데이터 ~8MB |
| W3 | **회수 가시성 split-brain** | 네이티브 auto-memory 흡수(mem.py:1794-1816)가 `cwd_origin=디렉토리명`(예: `-home-Uihyeop-agent-setting`)으로 기록하는데, recall/inject의 가시성 울타리는 `project_key()`=`git:github.com/dmlguq456/agent_setting`(mem.py:907-913, 222-259)을 씀 → **최근 사용자 교정 기억 24건(7/15-7/21)이 agent_setting 기본 recall/inject에서 안 보임**. legacy 키 전체 118건+ |
| W4 | **한국어 회수 성능 저하 (구조적)** | 시스템 SQLite 3.31.1 < 3.34라 trigram tokenizer 없음(`records_trig` 테이블 자체가 미생성, 실측 확인). CJK 쿼리는 rank 없는 LIKE 부분일치로 폴백(mem.py:1077-1088, score=0.0). unicode61은 한국어 형태소 분리를 못 하므로 FTS bucket 0도 조사-제거 휴리스틱(mem.py:883-888)에 의존. 최근 기억 대부분이 한국어 |
| W5 | **turn-nudge 증류 경로가 7/15 이후 무동작 정황** | `.turn-state-*` 최신 파일이 7/15 (18건), 이후 0건 — 등록은 살아있음(~/.claude/settings.json UserPromptSubmit). herdr/teammate-mode 전환(7/15, herdr-not-tmux 메모리와 일치)과 시기 일치. mid-session 증류가 현 세션 토폴로지에서 안 도는 것으로 추정 (SessionEnd curate는 소량 지속: distill-state 7/20-21 일 6-7건, curator write-event 513건) |
| W6 | **상태파일 GC 소유자 부재** | `.distill-state-*` 18,656개(7/13 폭풍 16,408개 포함)는 **누구도 청소 안 함** — dispatcher GC(hooks/mem-distill-dispatch.sh:96-99)는 lock/slot/out/prompt/snapids/budget만, turn-nudge GC(hooks/mem-turn-nudge.sh:58)는 `.turn-state-*`만. 그리고 그 turn-nudge 자체가 W5로 안 돎 → `.turn-state-*` 20,511개도 잔존 |
| W7 | **guard 울타리에 구멍** | `builtin-memory-guard.sh`는 PreToolUse(Write\|Edit\|MultiEdit)의 `*/projects/*/memory/*.md`만 차단하는데, Claude 네이티브 auto-memory는 매일 그 경로에 계속 쓰고 있음(7/21까지 실측) → "DB가 유일한 진실원천" 불변식이 기계적으로 강제되지 않음. 실제로 메인 세션 컨텍스트에 도달하는 건 DB inject(15줄 요약)가 아니라 파일 MEMORY.md 전문 |
| W8 | **pending 배수 불량** | pending 30건, 최고령 6/26 (`hint_hint-25-17-트래커_e4bfd6`), 7/14 잔재 다수. consume 이벤트 전 기간 14회. 보호(fail-closed)는 작동하나 소비가 안 됨 — pending은 만료도 안 되므로(영구) 무한 적체 |
| W9 | **durable 용량·타입 파편화** | durable/project 1,090건 vs soft ceiling 80/cwd(mem.py:79). agent_setting만 462건. inject는 상위 4건만 노출(INJECT_DEFAULT_MAX_DURABLE=4). type이 자유문자열이라 **251종** 난립(fact/사실, lesson/교훈 이중언어 중복 포함) — 회수 필터로서의 type은 사실상 무력 |

---

## 1. 계약 (Contract)

### core/MEMORY.md (§7, 전문 판독)
- **저장소**: `<agent-home>/memory/memory.db` SQLite WAL + FTS5가 SoT (2026-06-15부터). `dump.jsonl`은 git-tracked 결정론적 텍스트 미러, `mem import`로 복원 (§7.0, MEMORY.md:11).
- **레코드 모델**: `tier`(working/durable) × `scope`(project/global) × `type`(자유) × `delivery_state`(ordinary/pending/consumed) (MEMORY.md:11).
- **3채널 통합**: post-it → working/project, 내장 파일 메모리(projects/<cwd>/memory/) → durable/project ("SessionEnd `mem sync`가 타 세션/하네스의 stray write를 안전망으로 흡수"), profile → durable/global type=profile (MEMORY.md:14-18).
- **D-42**: 자동 lifecycle은 대화형 메인 세션 전용. 워커(등록 dispatch, loop, title, distiller, native subagent)는 inject/counter/sync/curator 전부 금지 (MEMORY.md:20).
- **D-40**: prompt별 자동 recall 분류 금지 — 회수는 에이전트 주도(`mem recall`/`recall.sh`)만. `mem recall --auto` 폐기, `mem-recall-inject.sh`는 fail-open 호환 no-op (MEMORY.md:90-95).
- **D-18/D-35**: 의미 판단은 에이전트(main/distiller/curator), 스크립트는 기계적 계약만(형태 검증, 가시성, pending fail-closed, graveyard 복구). 미소비 pending은 파괴 연산에 fail-closed (MEMORY.md:24, 99-103).
- **§7.6 프로필 매트릭스**: 7개 aspect × 소비자 역할 매핑. 05_domain_expertise가 "speech, TF DNN, signal processing 도메인 배경+용어" 담당 — **스펙트로그램 상수류의 계약상 귀속처**. 소비 패턴: "관련 작업 시작 시 `mem profile <stem>` 읽고 기본값으로 취급"(MEMORY.md:122) — **문서 지시일 뿐 기계적 게이트 없음**.

### roles/units/_shared/memory-flow.md (전문 9줄)
"Authorized memory flow" = **저장(closing) 규범만** 정의: "acting surface의 인가된 기억 흐름으로만 기억을 남겨라, 다른 채널로 쓰지 마라, artifact가 이미 기록한 일회성 detail은 저장하지 마라". 28개 유닛이 참조. **회수(recall) 지시는 유닛 카탈로그에 0건** — recall 안내는 어댑터 bootstrap(CLAUDE.md "Context and Memory")과 capabilities(analyze-project.md:28,65)에만 있음. → 유닛 상수를 메모리로 이설하면, 유닛 파일 자체에는 "그걸 어떻게 되찾는지"에 대한 지시가 현재 전무하다는 뜻.

### builtin-memory-guard.sh (전문 68줄)
차단 대상: file_path가 `*/projects/*/memory/*.md` 패턴인 Write|Edit|MultiEdit 툴 호출만 (라인 21). deny 사유 문자열로 mem CLI 사용 안내. **차단하지 않는 것**: Bash 경유 파일쓰기, mem CLI 자체(의도된 경로), 그리고 Claude 네이티브 auto-memory 내부 쓰기(실측: 7/20-21에도 파일 갱신 지속 → 훅을 우회하는 네이티브 경로 존재). MEMORY.md도 패턴에 포함되나 실제로는 갱신되고 있음.

## 2. 엔진 (tools/memory/)

### mem.py (3,398줄, 전 구조 판독)
- **경로 해석** (19-39): `AGENT_HOME` env → `CLAUDE_HOME` → `~/agent_setting` → `~/.claude`. `STORE=$AGENT_HOME/memory`, 세션 원본은 `~/.claude/projects` (MEM_PROJECTS), codex는 `~/.codex/sessions`.
- **스키마 v5** (399-431): 단일 `records` 테이블 16컬럼(id/tier/scope/type/cwd_origin/created/updated/expires/source/tags/links/body/strength/last_accessed/injection_flag/delivery_state) + `records_fts`(fts5 unicode61) + 조건부 `records_trig`(trigram, **이 머신엔 미생성**). 마이그레이션 v2 strength → v3 cwd remap → v4 injection_flag → v5 delivery_state.
- **쓰기 게이트** (653-818): quality_ok(15자 미만 거부) → sanitize(INJECTION_PAT 플래그, SECRET_PAT 마스킹) → source-key upsert(기존 ID 보존) → body-hash dedup(재발 시 strength+1) → 신규 INSERT + FTS 미러, 전부 단일 트랜잭션. pending은 monotonic(ordinary로 강등 불가).
- **회수** (992-1172): bucket 0 = unicode61 토큰화 OR-MATCH + bm25 (한국어 조사 제거 _KO_PARTICLES, 883-888) → bucket 1 = CJK trigram (사용 불가) → bucket 2 = LIKE 부분일치 무순위. 기본 cwd fence, `--all`로 해제. 회수는 last_accessed만 갱신(비소비). telemetry는 `~/.local/state/agent-memory/recall-events.jsonl` (256KB 로테이션).
- **inject** (2989-3152): SessionStart 요약 — working 8 + durable 4 + profile 목록 1줄 + cleanup 2줄, 총 15 bullets/2,000자 cap. strength·updated 내림차순 상위만. → durable 462건인 프로젝트에서 4건 노출은 사실상 keyhole.
- **sync** (3156-3180): migrate(apply) → lifecycle(apply) → index rebuild → export_dump → _commit_dump. 각 단계 실패 무시하고 계속.
- **_commit_dump** (147-172): dump.jsonl만 stage, auto-sync HEAD가 미push면 **amend**(rolling single commit), `MEM_DUMP_PUSH=1`이면 push. `_git_out`은 실패 시 빈 문자열 반환·무예외(119-126, timeout 5s) → **W1의 침묵 실패 원인**. amend 루프는 매 sync마다 ~1.2MB blob+tree+commit을 loose로 고아화 — gc.auto 기본 임계(6,700개) 미달로 gc가 영원히 안 돌아 **W2의 406MB 축적 메커니즘**.
- **distill** (1489-1511): 세션 JSONL(claude/codex/opencode 3소스 클래스)에서 marker(`.distill-state-<sid>`) 이후 delta 출력, `--advance`로 marker 전진. marker 파일은 GC 없음(W6).
- **profile** (1653-1774): DB type=profile에서 newest-wins, stem/2자리번호/유일토큰 alias 해석. 읽기 전용, 견고함.
- **curator 명령군** (2205-2455): reinforce/prune/merge/graduate/reattribute — 전부 `_in_current_project` allowlist + pending fail-closed + graveyard(`deleted-records.jsonl`, 808KB) 선기록.
- **doctor** (2667-): 자가진단 명령 존재 (durable>80, working>150, worker 7일 정체 임계).

### recall.sh (13줄) — `mem recall` exec 박판 래퍼. index-check.sh (64줄) — legacy `projects/<cwd>/memory/MEMORY.md` 텍스트 인덱스 드리프트 검사, `--fix`는 append-only.

### apply-distill-actions.py (144줄)
증류 모델 출력(JSON-lines)의 유일한 실행 경로. shape 검증 → **increment 모드는 add-only 강제**(P-25 화이트리스트 우회 봉쇄, 77-79) → curate 모드만 snapshot 파일의 destructive ID allowlist 내 reinforce/prune/merge/graduate/reattribute 허용 → **delete는 어떤 모드에서도 불가**(66-68) → 전부 argv-only subprocess, shell=False. body 2,000자 상한. 견고한 설계.

## 3. DB 실측 (read-only)

- **크기 해부**: memory.db **3.6MB** / dump.jsonl 1.2MB / deleted-records.jsonl 808KB / 백업 2.6MB(pre-migrate-v4 2.5MB + pre-merge-old949 128KB) / WAL 0B·shm 32KB (checkpoint 건강) / **.git 406MB** / 상태파일 39,167개(apparent 733KB, 블록 ~156MB). du=602MB, apparent=441MB.
- **레코드**: 1,378건 (durable/project 1,090 · durable/global 25 · working/project 262 · working/global 1). 기간 2026-06-15 ~ 2026-07-22 (오늘도 쓰기 발생 — 쓰기 경로 정상).
- **FTS**: records_fts 1,378 정합. records_trig 부재 (W4).
- **cwd 분포**: agent_setting 637 · agent-note 281 · SR_CorrNet_DSC 99 · claude_setting(legacy) 65 · **legacy/비정규 키 118건+** (`-home-Uihyeop` 46, `-home-Uihyeop-agent-setting` 24, `-home-nas-user-Uihyeop*` 40+, raw 절대경로 키 8).
- **W3 상세**: `-home-Uihyeop-agent-setting` 24건 = 7/15-7/21의 auto-memory 흡수분 전부 — no-broker-revival, incident-0046-mass-sigterm, root-cause-codex-first, no-defer-to-user-initiative 등 **최고가치 사용자 교정 기억**. v3 remap은 일회성(user_version=5 도달 후 미실행)인데 migrate() 흡수 경로(1807: `cwd_origin = mp.parent.parent.name`)가 legacy 키를 계속 재생산 → 구조적 재발.
- **delivery**: ordinary 1,344 · pending 30 (최고령 6/26) · consumed 4.
- **strength**: 1이 1,079건(78%), 최고 58 — dedup-reinforce는 작동.
- **profile 7건**: 전부 6/15 생성, 06(7/14)·02(6/16) 외 **한 달간 무갱신**. 05_domain_expertise 4,138자.
- **type**: 251종 자유문자열 (W9).

## 4. Lifecycle — 4개 훅 + 등록 실태

| 훅 | 이벤트 | 동작 | 실태 |
|---|---|---|---|
| `mem-recall-inject.sh` | UserPromptSubmit | **폐기 no-op** (D-40) — 항상 exit 0 | 여전히 등록돼 있으나 무해. 소스 adapters/claude/settings.json에는 없고 설치본 ~/.claude/settings.json:325에만 잔존(주입 프로젝션 드리프트) |
| `mem-turn-nudge.sh` | UserPromptSubmit | 세션별 카운터, N=10턴마다 dispatcher argument-mode 호출(increment 증류), `.turn-state` 3일 GC | **7/15 이후 상태파일 0건 (W5)**. codex 어댑터의 `.codex-turn-state-*`는 7/21까지 지속 — Claude 경로만 침묵 |
| `mem-distill-dispatch.sh` | SessionEnd(+turn-nudge 내부호출) | delta 확인 → 세션lock+동시성slot(≤4)+10분 시작예산(≤8)+`.distill-disable` kill switch(7/14 폭풍 대응 D-41) → 무도구 워커 spawn → applier 검증 적용 → marker 전진 | 활동 중 (curator write-event 513건, distill-state 신규 생성 7/21까지). MEM_DISTILL_ENABLE=1 (settings env) |
| `mem-briefing-inject.sh` | UserPromptSubmit | morning desk(`~/.claude` cwd 한정) 온콜 브리핑 1일 1회 + promote-candidates(D-28 제도화 후보) | desk cwd에서만; `.briefing-*` 7일 GC 자체 보유 |
| (훅 아님) `mem inject --hook` | SessionStart | 15줄 요약 주입 | session-inject 이벤트 201건 — 작동 중 |
| (훅 아님) `mem sync` MEM_DUMP_PUSH=1 | SessionEnd | 흡수+lifecycle+export+commit+push | export까지 작동(dump mtime 7/22 00:13), **commit/push는 W1로 사망** |

- 워커 모델 티어: increment=`fast-distiller`→CFG_LIFECYCLE_NUDGE=**mini(haiku)**, curate=`deep-curator`→CFG_LIFECYCLE_CURATE=**light(sonnet)** (adapters/claude/config/models.conf:31-32, bin/mem-distill-worker.sh:36-42). 워커는 `claude -p --disallowedTools 'Bash Read Write …'` + timeout(increment 120s/curate 600s) + setsid + governor class distill=동시 1.
- D-42 워커 판별 env: `AGENT_SESSION_ROLE=worker | AGENT_DISPATCH_CHILD=1 | AGENT_DISPATCH_DEPTH | CLAUDE_CODE_CHILD_SESSION=1 | OPENCODE_DISPATCH_SLUG | FLEET_TITLE_REFRESH=1 | MEM_DISTILL=1` — 4개 훅 + settings 인라인 sync/inject 가드에 동일 복제 (7곳 중복, 드리프트 리스크).

### 접근 매트릭스 (surface × 연산)

| Surface | profile-read | recall-query | memory-write | distill/lifecycle | 강제 메커니즘 | 신뢰도 |
|---|---|---|---|---|---|---|
| **메인 대화 세션** | ○ `mem profile` (Bash) | ○ recall.sh / mem show | ○ mem add/note (Bash); 파일 직접쓰기는 guard가 차단 | inject(SessionStart)·nudge(10턴)·curate(SessionEnd)·sync 자동 | 훅 등록 + guard | inject ○ / **nudge 의문(W5)** / curate ○ / dump 미러 ×(W1) |
| **등록 headless 워커 (depth-1/2)** | ○ (CLI 차단 없음) | ○ (CLI 차단 없음) | **△ mem add가 기계적으로는 열려 있음** — D-42는 자동 lifecycle만 금지, 명시적 CLI 쓰기는 미차단 | × 전부 env 가드로 skip | env marker 7종 | 회수는 워커 프롬프트에 지시가 있을 때만 — 계약(문서) 수준 |
| **native subagent (memory-scout 등)** | ○ | ○ (scout의 본업) | **프롬프트 계약상 금지, 기계적 강제 없음** (Bash 보유 → mem add 실행 가능) | × (자기 세션 훅 이벤트 없음) | 지시문만 | scout 절차는 우수 (좁은 쿼리→show→--all→--sessions→live-code 교차검증, 15줄 출력) |
| **distiller/curator 워커** | – | – (무도구) | stdout JSON → applier만 | 그 자체가 lifecycle | disallowedTools + applier 검증 + allowlist + delete 불가 | 높음 (S2a/S2b/P-25 봉쇄 확인) |
| **Codex/OpenCode 세션** | ○ | ○ (telemetry: codex 72 · opencode 34 이벤트) | ○ | 자체 어댑터 훅 (`.codex-turn-state-*` 7/21까지 활동) | 어댑터별 복제본 | Codex 경로가 현재 Claude nudge보다 활발 |
| **Claude 네이티브 auto-memory** | – | (시스템이 MEMORY.md 전문 주입) | **guard 우회로 매일 쓰기 중** | sync가 DB로 흡수하나 **legacy cwd 키(W3)** | 없음 | 파일 표면은 높음, DB 사본은 기본 recall에서 불가시 |

## 5. 이중 시스템: Claude auto-memory vs 하네스 DB

**완전히 별개의 두 시스템이 맞고, 겹침이 실재한다.**
1. **파일계** `~/.claude/projects/<enc-cwd>/memory/*.md` + MEMORY.md 인덱스 — Claude Code 내장 기능이 소유, 세션 컨텍스트에 **전문 주입**(이번 세션 system-reminder로 실증). 7/21까지 활발. 5개 프로젝트에 존재.
2. **DB계** `~/agent_setting/memory/memory.db` — 하네스 계약상 SoT. SessionStart에 15줄 요약만.
- 계약상 관계: 파일계는 "타 하네스 stray write를 sync가 흡수하는 안전망"(MEMORY.md:17). 흡수는 실제 작동(auto-memory:* source 29건, 7/21분까지).
- **혼동 리스크 (실증)**: (a) 같은 지식이 두 곳에 다른 신선도로 존재 — 파일이 사후 수정되면 source-key upsert로 DB에 재흡수되지만 cwd 키가 어긋나 기본 recall에선 영영 안 보임(W3); (b) 파일 삭제 시 DB 사본은 잔존(고아); (c) 에이전트가 "기억했다"고 믿는 채널(파일)과 하네스가 회수하는 채널(DB)이 불일치 → **relocation(유닛 상수→메모리) 시 어느 계로 넣을지에 따라 회수 가시성이 완전히 달라짐**. 참고: 구 store는 `~/.claude/memory.archived-2026-07-03`에 보존(memory/README.md:8).

## 6. Relocation 판단에 주는 함의 (stream 1 연동)

1. **프로필 경로(05_domain_expertise 등)는 기계적으로 견고**하나(전역 scope, cwd fence 무관, newest-wins), 소비가 문서 지시("작업 시작 시 읽어라")에만 의존 — 게이트/훅 없음. 스펙트로그램 상수 이설의 최소 조건은 "해당 유닛/스킬이 mem profile 읽기를 명시"하는 것.
2. **일반 durable 레코드 경로는 현재 신뢰 불가**: 한국어 회수 저하(W4) + cwd 키 분열(W3) + inject keyhole(4건) + type 파편화(W9). "필요할 때 반드시 회수됨"을 보장하지 못한다.
3. 워커/서브에이전트로 내려가는 작업은 recall 지시가 프롬프트에 실려야만 회수 시도 자체가 발생 — 유닛 카탈로그에 recall 언급 0건인 현 상태에서 상수를 빼면 워커는 그 지식에 도달할 경로가 없다.

## 7. 즉시 조치 후보 (본 스트림 권고, 실행은 별도 승인)

1. `memory/.git/index.lock` 제거(소유 프로세스 없음 확인 완료) + 밀린 dump commit/push — W1 해소 (1분).
2. `git gc`(또는 `git repack -ad && git prune`) — 406MB→수 MB 예상. amend-루프 유지 시 주기적 gc 훅 필요, 또는 amend 대신 일반 commit+주기 squash.
3. `.distill-state-*`/`.turn-state-*` 고아 39K개 일괄 삭제 + dispatcher entry-GC에 `.distill-state-*`(mtime 기준, 단 active 세션 marker 보호) 추가.
4. migrate() 1807행 `cwd_origin`을 `project_key(_decode_enc_cwd(name))`로 정규화 + 기존 legacy 키 일회 remap(v6) — W3 해소.
5. W5 재현 조사: herdr pane의 Claude 세션에서 UserPromptSubmit 훅 발화 여부 실측 (`MEM_NUDGE_INTERVAL=1`로 1턴 검증).
6. 한국어 회수: sqlite 3.34+ 번들(파이썬 pysqlite3-binary 등)로 trigram 활성화, 또는 CJK bigram 수동 토큰화를 records_fts에 인덱싱.

## 부록: 근거 좌표
- 계약: core/MEMORY.md:11-24,63-84,90-123 · roles/units/_shared/memory-flow.md:1-9 (참조 유닛 28개)
- 엔진: tools/memory/mem.py:19-107(경로·상수), 147-172(commit), 222-259(project_key), 304-319(marker), 399-431(스키마), 653-818(쓰기), 867-913(토큰화·CJK·fence), 992-1172(recall 3-bucket), 1489-1511(distill), 1653-1774(profile), 1778-1816(migrate/auto-memory 흡수), 2014-2061(lifecycle), 2989-3180(inject/sync) · apply-distill-actions.py:66-79(delete 금지·add-only) · recall.sh:13 · index-check.sh
- 훅: hooks/{builtin-memory-guard.sh:21, mem-turn-nudge.sh:14-23·36-68, mem-distill-dispatch.sh:58-99·131-163·269-288, mem-briefing-inject.sh:34-43·90-116, mem-recall-inject.sh} · 등록: ~/.claude/settings.json(hooks 6건, env MEM_DISTILL_ENABLE=1) · 모델: adapters/claude/config/models.conf:31-32 · 워커: adapters/claude/bin/mem-distill-worker.sh:36-66
- 실측: memory.db ro-query(레코드 1,378·trig 부재·legacy 키 118·pending 30) · memory/.git(commit 311·loose 3,590/314MiB·garbage 325/88.75MiB·index.lock 7/14 18:14) · 상태파일 날짜분포(turn-state 7/13 16,403·이후 0) · telemetry ~/.local/state/agent-memory/{recall,write}-events.jsonl(recall 257·inject 201·consume 14·curator 513) · ~/.claude/projects/*/memory/ 최신 쓰기 7/21
