# Spec Pipeline Summary: memory-store

- **Date**: 2026-06-15
- **Mode**: library + cli
- **Status**: spec in_progress (PRD 초안, open 결정 대기)

## Process Log
| Step | Action | Result |
|---|---|---|
| 1 | 정보 수집 | 입력 5종 확인, 이주 대상 59파일/22dir |
| 2 | mode 확정 | library + cli (메모리 저장소 모듈) |
| 3 | PRD 작성 | prd.md — D1~D7 locked + D-open 1~3 |

## 핵심 결정 (locked)
- D1 markdown 원본(추적) + SQLite FTS5 색인(파생) + projection(파생)
- D2 저장 위치 ↔ 스코프 분리 (통합 저장소 + cwd_origin 태그)
- D3 자동 write (기억 한정, 사람 게이트 없음, 품질필터만) — 불변식 의식적 전환
- D4 59파일 이주 / D5 하네스 projection / D6 recall 진화 / D7 injection 가드

## Open (사용자 확인)
- D-open-1 삭제 정책 / D-open-2 projection 갱신 시점 / D-open-3 이주 후 기존 폴더

## Update Log

### v1 → v2 (2026-06-15, update mode — drift 정정, snapshot `_internal/versions/v1/`)
구현이 spec 보다 앞서 만든 drift 정정 (코드가 진실, spec 후행):
- **D5** "주입은 Claude Code 가 projects/ 에서, 우리가 못 바꿈" (outdated) → **자체 하네스**로 정정: SessionStart `mem inject --hook`(store→additionalContext 직접 주입) + SessionEnd `mem sync`(projects/ auto-memory→store mirror+색인). store 가 세션 주입의 source.
- **Architecture mermaid**: PROJ→CC projection 주입 흐름(old) → `SRC ==mem inject==> CC`(주입) + `projects/ ==mem sync==> SRC`(회수) + 하네스 write→projects/ 로 교체.
- **D-4** projection 갱신 → inject(세션시작)+sync(세션종료) hook 자동.
- **cli 표·[library] API**: `mem inject`·`mem sync` 행 추가, `mem project` 는 "보조(주입은 inject)" 주석.
- 근거(검증): `settings.json` SessionStart=`mem.py inject --hook`·SessionEnd=`mem.py sync` 확인, 이번 세션 상단 inject 블록 실측.
- 스코프 한정: D1~D4·D6·D7·통합모델·데이터모델 불변.

### v2 → v3 (2026-06-15, update mode — Hermes DB화 강화, snapshot `_internal/versions/v2/`)
사용자 방향 전환 (4턴 설계 동기화 후 lock): "sqlite 기반 DB화 + 메모리 git 이력 제거 + 별도 저장소". Hermes `state.db`(로컬 SQLite WAL) 정렬.
- **D1 반전 (SoT 전환)**: markdown 원본(추적) → **로컬 SQLite `memory.db`(WAL)가 SoT**. git 은 `dump.jsonl`(레코드당 1줄·id 정렬, deterministic 텍스트) mirror 만 추적, 바이너리 `.db`·`.index.db`·WAL 은 gitignore. 복원 = 덤프 replay. FTS5 색인은 파생물 아니라 DB 본체 내장으로 승격.
  - 근거(사용자 합의): 자주 갱신되는 DB 를 git 바이너리로 올리면 delta 안 먹고 bloat. 텍스트 덤프는 변경 줄만 diff + audit 가시성은 덤. 사람이 메모리를 routine 으로 읽을 필요는 없음(읽기=inject/recall).
- **D9 신규 (저장소 분리)**: `~/.claude/memory/` 를 전용 private repo(`claude-memory`)로. config repo(`claude_setting`)는 `git filter-repo --path memory/ --invert-paths` 로 전체 이력 제거 + force-push (git bundle 백업 선행), 이후 `memory/` gitignore. 중첩 ignore-repo (submodule 미사용).
- **통합 강화 (D-7)**: user_profile + post-it + **Claude 내장 auto-memory** 를 한 DB 로. tier/scope/type 컬럼으로 주입 행동 구분 유지 (Hermes MEMORY/USER/state 분리를 한 DB 컬럼으로 표현 → 더 통합적).
- **D3 정련**: user_profile raw=레코드 흡수, 구조화 aspect 문서는 DB→generated view (`mem export --profile`) — sub-agent 경로 Read 보존, 순수 DB 배선 대공사 회피.
- **API/CLI 추가**: `mem export`(dump/profile)·`mem import`(replay)·`mem migrate` 에 md-file source 추가. 데이터모델을 SQLite DDL + jsonl 덤프 스키마로 재기술.
- **non-goal 보강**: Turso/libSQL 원격 동기화 명시 비목표 (단일 사용자·외부 의존 0 근거).
- 스코프: D2(위치↔스코프 분리)·D4(자동write)·D5(lifecycle)·D6(inject/sync hook)·D8(보안)·통합모델 골격 불변.

### v3 → v4 (2026-06-15, update mode — profile 완전통합 + Hermes 잔여port + 결정론우선, snapshot `_internal/versions/v3/`)
v3 구현(DB화·이주·저장소분리) 완료 후, 사용자 지적("profile은 절반만 통합 — sub-agent는 여전히 md 원본을 권위로 읽음, 별론데")과 핵심 원칙("결정론·SW 가능한 건 코드로 → agent 생각 최소화") 반영.
- **§0.5 결정론-우선 (D-8, cross-cutting)**: SW 가능 요소는 hook/script/gate/DB로 대체, agent judgment는 fallback. DESIGN_PRINCIPLES 격상 예정.
- **Cluster A (D-9) profile 완전통합**: DB=profile SoT / `mem export --profile`을 sync·analyze-user에 wiring해 md를 generated view로(A2) / analyze-user DB-first(A3) / post-it·편집 DB 경유(A4). sub-agent 경로 Read는 보존(md=view, 파일명 결정론 도출).
- **Cluster B (D-10) Hermes 잔여port** (08_source_grounded 검증): B1 session_search 자율 turn-호출 강화 / B2 turn-counter 자기회고(UserPromptSubmit hook 결정론 카운터, nudge_interval=10 등가). 08 결론 = FTS5 cross-session 갭 닫힘, 남은 진짜 port 이 둘뿐.
- 유지: D1~D9 골격·데이터모델.

### v4 → v5 (2026-06-15, update mode — Option 2 파일 메커니즘 제거, snapshot `_internal/versions/v4/`)
사용자 결정: "그냥 sub-agent도 DB 읽게 하면 됨 + user_profile·post-it 별도 파일이 왜 있냐". v4의 Option 1(md를 generated view로 유지)을 **Option 2(파일 메커니즘 자체 제거)**로 전환.
- **Cluster A 재정의**: user_profile/·post-it.md **파일 제거**, DB가 유일 SoT·유일 읽기 소스. sub-agent는 `mem profile <aspect>`(신규)·`mem recall`로 DB 직접 읽기. analyze-user·/post-it는 DB authoring. projection wiring 불필요(파일 없음 → 동기 로직 소멸, §0.5 단순화). 매트릭스는 문서로 보존(소스=DB). register-postit·.postit-roots 폐기.
- 근거: Option 1의 유일 근거였던 'agent rewire 회피'를 사용자가 명시 waive("대공사 OK"). post-it은 세션 주입이 이미 mem inject(DB)라 파일이 이중 redundant.
- DESIGN_PRINCIPLES §0.5(결정론-우선) ✅ 이번에 격상 완료.

### v5 → v6 (2026-06-16, update mode — Cluster C 세션 자동 distillation, snapshot `_internal/versions/v5/`)
사용자 지적: "세션 끝낼 때마다 '기억해둬'를 수동으로 말하는 게 번거롭다 — 자동화하고 싶다." 현 시스템 분석으로 _자동 회수가 비어있는 유일한 자리 = 메인 에이전트 orchestration raw log_ 를 특정 (서브에이전트 작업은 산출물로, raw 대화는 jsonl로 이미 저장; turn-nudge+§2는 타이밍만 자동·쓰기는 에이전트 행동이라 cold-close 유실). 해법 = raw 아카이브(검색)가 아니라 **distillation**.
- **D-11 harness-agnostic source**: `ingest_session(source)` 추상화, Claude Code jsonl adapter 1개(미래 하네스는 adapter만 추가, 지금 미구현·자리만). "멀리 봐서 하네스에 안 묶이게."
- **D-12 SessionEnd distiller**: SessionEnd hook이 detached `claude -p`로 세션 jsonl → working/durable distill(fire-and-forget). 재귀가드 `MEM_DISTILL=1`. 증분 marker 스코프.
- **D-13 in-session 증분 consolidation**: turn-nudge 확장 — 메인 에이전트가 N턴마다 delta만 정리(요약 추가/해결분 prune), low-load. D-12와 상보(cold-close 구멍 차단).
- 데이터모델 영향: 신규 테이블 없음(기존 records로 흡수), raw 대화는 jsonl에 잔존·DB 복제 X(dump/claude-memory에 원문 비포함). 신규 상태파일 = distill/consolidation marker(gitignore, turn-state 패턴 동형).
- 범위 제외: raw FTS 아카이브(sessions/messages 테이블)는 durability를 jsonl이 이미 해결·현 규모 grep 충분이라 본 cluster 비범위, recall --sessions는 grep 유지.

### v6 → v7 (2026-06-16, update mode — D-13 외부 분사화 + sonnet + D-14 보안, snapshot `_internal/versions/v6/`)
v6 구현·머지(main `e491241`, distill 36 + turn-nudge 11 통과) 직후 사용자 피드백: ① "D-13 도 메인 클로드 말고 외부로 던져라 — 그 정리 일 하느라 메인 load 걸린다" ② "distiller 전부 sonnet 으로" ③ prompt-injection 신뢰경계 질의.
- **D-13 외부화**: in-session 정리를 메인 에이전트 → 외부 detached distiller 분사로(turn-counter hook 이 nudge 대신 분사). v6 의 '메인 context 보유라 쌈' 논리를 사용자가 waive(메인 turn 보존 우선). 두 트리거(①N턴·②종료)가 같은 distiller·marker 공유.
- **distiller 모델 sonnet** (`claude-sonnet-4-6`, haiku→sonnet).
- **D-14 권한 하드닝**: distiller 를 `mem.py` 명령만 허용(임의 bash·dangerously-skip 제거) → R1(대화=외부입력을 LLM+bash 로 읽는 신뢰경계) 근본 차단. 프롬프트 방어는 defense-in-depth. opt-in 게이트 유지.
- 동시성: 세션당 distiller lock(겹침 방지) + 재귀가드 turn-counter·SessionEnd 두 hook 다.

### v7 → v8 (2026-06-16, update mode — D-14 권한 allowlist 무력 실측 → no-tools 재설계, snapshot `_internal/versions/v7/`)
v7 머지(main `fab5b46`) 후 **enable 전 라이브 검증**에서 발견: v7 의 D-14 `--allowedTools 'Bash(python3 *mem.py*:*)'` 가 임의 명령을 **차단 못 함**. 원인 = `settings.json permissions.allow` 에 blanket `Bash` 가 있고 CLI `--allowedTools` 는 allow 에 _additive_(replace 아님) → `date>>file` 실측 실행됨. v7 빌드의 "비-mem.py 미실행" 주장은 모델 자체 거부의 오인.
- **D-14 재설계 (v8)**: distiller LLM 에서 도구 _전부 제거_(`--disallowedTools`), `mem distill` delta 를 프롬프트 데이터로 주입 → LLM 은 JSON-lines({tier,type,body}) 출력만 → **dispatch 스크립트가 검증 후 `mem add` 직접 실행**. LLM 판단·코드 실행(§0.5). injection 이 속여도 명령 실행 물리 불가(도구 없음) + mem add 마스킹 2차.
- **enable 전 검증 현황**: ✅ 재귀가드 env-상속(`claude -p` SessionEnd 발화 + `MEM_DISTILL=1` 상속 실측)·ghost-marker·hang-free. ⏳ 남은 gate = no-tools acceptance(`date>>file` 류 차단 실측).

### v8 → v9 (2026-06-17, update mode — Cluster D 결정론-first lifecycle, snapshot `_internal/versions/v8/`)
v8 머지·enable·e2e(84줄→6레코드 정확) 완료 후, 사용자와 lifecycle 설계를 심화 — 원칙 정립: **추가(가역) 판단=외부 에이전트 offload / 삭제·정리(비가역) 판단=메인 직접**. distiller 가 "결정론 add" 가 아니라 "외부화된 salience 판단 + 결정론 scaffold" 임을 정정. Hermes consolidation 도 메인이 함(capacity-error 강제) — 같은 자리.
- **발견된 갭**: ① recall 이 instruction(메인 판단) — hook 으로 결정론화 가능(B1 미완분). ② lifecycle durable near-dup `[dup-flag]` 가 sync 출력으로 흘러 死(아무도 안 봄). ③ working "졸업"(working→durable)이 구현된 적 없음 — blind TTL delete 만. 외부화 때 prune 도 빠져(distiller add-only) 검토 삭제 부재.
- **D-15 recall hook** / **D-16 정리후보 mem inject 노출** / **D-17 distiller add-only 확정·삭제=메인·TTL backstop**.

### v9 → v10 (2026-06-17, update mode — Cluster E: 큐레이션 단순화 + audit P0 하드닝, snapshot `_internal/versions/v9/`)
Cluster B/C/D 머지·enable 후 사용자 "메모리=가장 중요한 시스템, 다각도 점검+강화" → 8각도 read-only audit(`analysis_project/memory-audit/findings.md`, 716줄, workflow 9 agent) 실측. + 설계 심화 대화로 두 축 확정:
- **(A) 큐레이션 단순화** (사용자 "구조 너무 복잡 → 세션끝 opus 가 메인 일까지"): 3자(distiller add→script flag→메인) → **세션끝 opus 풀 큐레이터** collapse. "새 메인이 해결 모름" 문제 소멸. D-12 sonnet→opus·add-only→full-curate, D-17 삭제=메인→세션끝 opus(dump 복구 안전망·worst=비효율). no-tools 유지·action JSON·script 실행.
- **(B) audit P0 하드닝**: strength reinforcement(재출현=중요도, dedup=reinforce)·폭증방지 4겹(durable snapshot·ceiling·budget·decay)·project_key robust(worktree/이동 오펀 해소)·recall 엔진(단일phrase→OR+bm25+top-K)·내구성(dump commit·import 멱등·user_version·INJECTION persist).
- **(C) E-7 프록시 폐기**(사용자 재검토): on-premise 로깅 프록시는 redundant — 다른 하네스도 자기 로그 남김 → D-11 adapter 만으로 model-agnostic 달성, 비용≫이득. graduate(working→durable)는 opus 가 수행.
- audit 발견 신규: 내구성 갭(dump push 0)·INJECTION_PAT 미persist(poisoning)·graduate/cold-decay 미구현.

## Next
**Cluster E 구현** → autopilot-code, worktree, **phase 분할**(한 사이클 X — schema·로직 큼): E-α(DB 하드닝: user_version+strength+project_key+마이그레이션) → E-β(recall 엔진+내구성) → E-γ(세션끝 opus 풀 큐레이터+폭증 4겹+graduate, no-tools 보안 재검증). 각 phase 머지 후 회귀. E-7 프록시 구현 없음.

### v10 → v11 (2026-06-22, update mode — Cluster F 추가, snapshot `_internal/versions/v10/`)
루프↔메모리 환류 + 적극 정리 (§5.8 신설, D-25~29). 계기 = 메모리 누적분의 시스템 구조 제도화·적극 정리 환류 부재 지적(사용자):
- **D-25** 루프 자율성 재정의 — "루프는 일 안 한다" 폐기 → 되돌림가능+명백=무인 직접처리+전수보고 / 그외=아침 논의. (가드: graveyard·git 복구경로 + 전수 보고)
- **D-26** 아침 논의 데스크 — cwd==~/.claude 당직후 그날 첫 발화 → UserPromptSubmit hook 브리핑 주입. SessionStart 아니라 '그날 첫 상호작용'(세션 유지 환경).
- **D-27** curator 산출물 대조 적극 prune — SessionEnd opus 입력에 ARTIFACTS(git/plans/spec) DATA 블록 + prune 적극화. 안전 3겹(화이트리스트·graveyard·DATA). /clear 도 SessionEnd reason=clear 발동(matcher '*') 확인 → 유실 구멍 없음.
- **D-28** 제도화 승격 채널 — durable 반복규칙·교훈(272 중 ~27건) → 아침 안건 → 종착지(문서/hook/drill) 분기 → 반영·drill 검증 후 prune. 정리(자동)와 승격(논의) 분리.
- **D-29** ✅ 선결 버그 복원력 (main b95b9a9) — lib.sh PATH(cron v20)·run_claude_retry(일시장애)·oncall exit code 생존체크.
- post-it 역할 재검토(§5.8.6, 열림): distiller 와 중복 — 별도 결정.

### v12 → v13 (2026-07-04, update mode — Cluster H 추가, snapshot `_internal/versions/v12/`)
memory 도메인 adapter-parity 불변식 (§5.10 신설, D-30~32). 계기 = codex-adapter-parity 전수 감사(`research/codex-adapter-parity/`)가 Codex adapter 의 memory lifecycle 비대칭을 확정 (P-12 overclaim 포함):
- **D-30** session-end distill 2-tier(increment+curate) 를 adapter-agnostic 계약으로 — 미실현 어댑터는 명시 신고 의무, "matches" 표현은 curate 축 성립 시만 (P-12).
- **D-31** SessionEnd sync 계약 = `mem.py sync` + `MEM_DUMP_PUSH=1` (원격 mirror drift 차단, P-10).
- **D-32** distill worker 는 portable `mem-distill-dispatch.sh` 계약 경유 — 재구현 시 mode/model routing·snapshot whitelist·lock·재귀가드 보존 의무 (P-13·P-25·P-36).
- 어댑터 전반 parity 계약(P-01 derived guard 등)은 본 PRD 범위 밖 — `core/ADAPTATION.md` 소관 명시.
- Next 8번 항목으로 Cluster H 구현 경로(autopilot-code, 감사 Phase 3 과 동일 사이클 가능) 추가.
- (이력 메모) v11→v12 update 때 `_internal/versions/v11/` snapshot 이 누락됐음을 확인 — v11 내용은 git 이력으로만 복원 가능. 본 v13 부터 snapshot 재준수.

- 2026-07-10 minor: memory mirror repo 개명 반영 (claude-memory → agent-memory, GitHub rename + remote/mem.py 주석/README 동기) — 사용자 지시, 하네스-중립 명명 정렬. 본문 4곳·state D-6 표기 갱신 (버전 스냅샷은 불변).

### v13 → v14 (2026-07-10, update mode — Cluster I 추가, snapshot `_internal/versions/v13/`)
Claude Code와 Codex의 동시 진단을 교차검증해 “저장은 되지만 꺼내 쓰기 어렵다”는 병목을 구조 문제로 확정했다. 실제 agent-memory 이력에서는 canonical handoff와 보강 2건이 함께 존재한 뒤 보강 2건 삭제+canonical strength `1→3`이 동시에 발생해, D-27 curator의 near-duplicate merge 오판으로 고유 인계 내용이 사라진 사고가 확인됐다.
- **D-33** full-body retrieval: `mem show <id>`와 `recall --full/--limit`, visibility fence, generic not-found. 읽기는 소비가 아니다.
- **D-34** prompt auto-recall: 모든 project 발화를 shared candidate engine으로 no-touch probe하고 identifier/CJK/coverage 기반 고신뢰 hit만 top3/1,200자로 주입. raw prompt 없는 bounded event telemetry로 hit-rate·정밀도·latency를 관측한다.
- **D-35** handoff delivery protection: schema v5 `delivery_state(ordinary|pending|consumed)`, 명시 `consume`, pending 대상 destructive operation의 실행시점 fail-closed, merge 원자 취소, lifecycle 보호, 단건 restore. 기존 handoff/HANDOFF 기록은 fail-safe pending backfill.
- **D-36** injection cap hold: cap 확대보다 recall 접근성을 먼저 고치고 `probe→qualified→injected→show/consume` 퍼널을 재관찰한다.

### v14 → v15 (2026-07-11, update mode — Cluster J 추가, snapshot `_internal/versions/v14/`)
계기 = fleet 메모리 가시화(agent-fleet-dashboard F-19) 방향 확정(사용자 2026-07-11). 설계 탐색 실측: 읽기측 telemetry(D-34 recall-events)는 있는데 쓰기측은 삭제만 graveyard 에 남고 add/note/consume/reinforce/merge/graduate 는 per-event 흔적 0(간접 이력 = dump.jsonl git diff 뿐), `mem` 에 log/recent 류 명령 없음, store 전수 건강 진단 부재(index-check 는 legacy 파일 인덱스용, oncall 메모리 항목은 승격 nudge 뿐).
- **D-37** 쓰기 이벤트 저널: 전 변이 경로 → write-events.jsonl(XDG state, bounded 256KB/500줄, fail-open — graveyard fail-closed 불변). recall-events 와 읽기/쓰기 대칭.
- **D-38** `mem log`: 저널 tail 1급 조회(--limit/--action/--tier/--actor/--json). stats(스냅샷)는 불변, log 가 흐름 보완.
- **D-39** `mem doctor` + oncall 편입: read-only 전수 진단 9항목 + exit code. 새 loop 신설 없음(oncall 항목 1개, D-25 계약). 조치 권한 = D-18 세션끝 opus 큐레이터 불변 — doctor 는 진단·보고까지만.
- 소비자 연결: fleet `collectors/memory.py`(F-19, read-only 관찰 — fleet F-1 정합) — 저널 포맷 변경 시 양 spec 동기 의무. 구현 = Next 10(autopilot-code, worktree; fleet F-19 는 별도 사이클, 파일 표면 비겹침 병렬 가능).

### v15 → v16 (2026-07-14, update mode — language-neutral recall, snapshot `_internal/versions/v15/`)
- 고정 자연어 회상 신호어와 signal-dependent `explicit/implicit` confidence 경로를 폐기한다.
- 모든 eligible project prompt는 동일한 content-based auto-recall threshold를 사용한다.
- 명시적 회상 의도는 문장 속 phrase가 아니라 `mem recall` CLI/API 호출로만 구분한다.
- document-frequency·coverage·rare exact term 기반 relevance, raw-prompt-free telemetry, top3/1,200자 cap은 유지한다.

### v17 → v18 (2026-07-14, update mode — on-call proposal promotion, snapshot `_internal/versions/v17/`)

- D-40의 agent-owned semantic judgment를 on-call에 적용한다: 최근 memory mutation은 후보 신호이며 full body와 현재 source/log/test/runtime evidence를 함께 읽는다.
- Live corroboration이 있는 harness incident만 offline improvement inbox로 승격한다.
- Agent가 incident key를 선택하고 deterministic CLI는 exact match만 deduplicate한다; recurrence는 evidence만 append하고 proposal state를 바꾸지 않는다.
- On-call 자동 범위는 `proposed`까지이며 review/adoption/activation과 source/runtime mutation은 계속 금지한다.
- 구현 완료: exact-key 동시 ingest는 하나의 proposal에 직렬화되고, stale recurrence는 current-context-bound reproduction 뒤에만 freshness를 회복한다. 19개 proposal 회귀와 adapter/release 회귀를 통과했다.
