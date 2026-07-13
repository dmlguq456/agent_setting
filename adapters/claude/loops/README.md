# loops/ — 상시 루프 카탈로그

세션 **밖**에서 독립 실행되는 것들의 집. (skills/agents/hooks 는 세션 _안_ 의 부품 — hooks 는 툴 호출 순간 강제, loops 는 세션 무관 실행.)

## autopilot 와의 관계 — 루프는 *파이프 일*을 대신하지 않는다

일은 전부 autopilot-* 파이프(+agents·skills·hooks)가 한다 — 루프는 파이프의 _앞(언제 돌릴지 발견·제안)_ 과 _뒤(산출물 정리·상태 감시·지침 검증)_ 만 담당. 어떤 루프도 라우팅·파이프 순서·산출물 컨벤션을 바꾸지 않는다. 미래 루프(학습 모니터·goal loop)도 동일 — 일손이 필요하면 _파이프를 호출_ 하지 직접 일하지 않는다. **autopilot = 동사(일하기), loop = 부사(언제·얼마나·끝났는지).** 단 "일을 안 한다"는 *파이프(구현·라우팅)를 대신 안 한다*는 뜻이지, 정리·감시까지 손 놓는다는 게 아니다 — *되돌릴 수 있고 명백한* 정리·처리(메모리 prune·죽은 산출물 정리)는 루프가 무인으로 하고 전수 보고한다 (D-25, 아래 공통 규약).

## 계층 — "loop engineering" 은 4개 층의 통칭 (혼동 주의)

같은 모양(행동→검증→조정)이 네 박자로 돈다. **초(도구) → 분(QA) → 일(작업) → 주(세팅)**:

| 층 | 주기 | 실체 | 우리 자리 |
|---|---|---|---|
| L1 에이전트 루프 | 초 | LLM→도구→반복 (런타임 영역) | 현재 adapter 런타임(Claude Code 등) — 소비만 |
| L2 과제 루프 | 분 | 한 작업 안 생성↔검증 (maker/verifier·QA 라운드) | skills/agents (기존) |
| L3 작업 루프 | 시간~일 | 세션 밖 발견·분사·기록 (cron+headless) | **본 폴더** — oncall·note |
| L4 메타 루프 | 주 | 시스템 자체 시험·개선 | **본 폴더** — drill (+후보 setting-audit) |

공통 규약:
- **루프 자율성 (Cluster F D-25, 2026-06-22 재정의)**: 루프는 *되돌릴 수 있고 명백한* 일은 **무인 직접 처리**하되 **한 일을 전수 보고**한다 (가드 2개: ① 되돌림 보장 — graveyard·git 등 복구 가능 경로로만 ② 전수 보고 — 무인 처리분은 빠짐없이 아침 브리핑에). *되돌리기 어렵거나 판단이 필요한* 것만 사용자 논의(아침 데스크 D-26)로 올린다. = "사전 승인"을 "되돌림 가능 + 사후 통보"로 교체. (옛 "출구는 보고·제안까지, 삭제·적용은 사용자" 원칙 폐기 — 큐레이터가 이미 무인 prune 중이었고 매 건 사전승인은 비효율. 브랜치 merge 는 여전히 메인 에이전트 선별 — OPERATIONS §5.10.)
- 실행 흔적은 `loops/*.log` (자체 로테이션, gitignore). 비용 = 구독 사용량 잠식 (별도 과금 아님).
- 트리거 3형: 시간형(cron) / 사건형(필요 시 발사) / 상태형(외부 신호 감시).

## 현역

> 파일명은 ASCII 유지, 표기는 `당직(oncall)` 처럼 병기.

| 루프 | 형 | 트리거 | 대상 | 하는 일 | 산출 | 사용자 접점 |
|---|---|---|---|---|---|---|
| **당직** (`oncall`) | 시간 | cron 05:37 | 작업장 (repo·산출물·실험·루프 생존·모의훈련 미실행) | 야간 순찰 — 이상 **발견·보고만** | `notes/oncall/<date>.md` (당직 보고서) | 아침 "당직 보고 처리해줘" |
| **일지** (`note`) | 시간 | cron 05:03 | 전날 산출물 내용 | worklog-board L2 **노트화·라우팅** (idempotent) | `notes/_layer2/notes/` + digest | worklog-board `/triage` |
| **모의훈련** (`drill/`) | 사건 | 지침 _행동규칙_ 수정 후 `drill/run.sh` (정기 회귀 `--sample 2` 랜덤 2개 · 가드/라우팅 대폭 변경 시만 관련 케이스·전수 — 매번 전수는 과부하) | 메인 에이전트 행동 (지침 준수) | fixture 가상 상황에서 headless **시험·채점** + FAIL 시 **진단·수정안 초안** 자동 작성(적용 X) | `drill/results/<일시>/` (+ `<case>.diagnosis.md`) | FAIL 시 수정안 승인 |
| **연수** (`study`) | 시간 | cron 일요일 06:17 | 외부 동향 × 현 세팅 | agent engineering 신간·현재 주 adapter 변경 조사 → 세팅 대조 → **개선 제안서만** (🔴 한정 **자동 초안** 동반) (+ g0 세금 추세) | `notes/study/<date>.md` | 제안 채택 서명 → 적용 → 모의훈련 |
| **런타임 감시** (`runtime-watch`) | 상태 | 일 1회 이하 또는 runtime-currentness 사건 후 수동 | Codex·Claude Code 공식 정책/런타임 사실 × 로컬 adapter projection | 공식 primary source fingerprint + 로컬 CLI/projection/usage helper probe → **보고/제안만** (정책 auto-edit 금지, token 절약 위해 deterministic probe 우선) | `notes/runtime-watch/<date>.md` | 변경 감지 시 autopilot-spec/code 사이클 제안 |

새벽 시간표: 05:03 note → 05:37 oncall (충돌 방지 간격). runtime-watch 는 네트워크·정책 currentness 감시라 매일 강제하지 않고 oncall 이후 수동/상태형으로 둔다(2026-07-13 Codex window currentness 사고).

## 후보 (backlog)

| 후보 | 형 | 착수 조건 |
|---|---|---|
| **목표 루프 (goal loop)** | 목표 달성까지 반복 | 검증이 기계적인 첫 실전 자리 (테스트 전부 초록·ablation 표 빈칸 0 등). 부품: 기계적 목표 정의(루프가 수정 불가) + 회차별 새 세션·상태 파일 + 검증 게이트 + 무진전 N회 시 사람 호출 + 회차 상한 |
| 학습 모니터 | 상태 | 다음 autopilot-lab setup 때 실물(log 포맷·ckpt 경로)에 맞춰 |
| code discovery (깨진 테스트·TODO 스캔 → 수정 제안) | 시간 | oncall 운영 안정 후 |
| worklog-board 운영 패널 3종 — ①결재함(triage 확장: 당직 보고 미처리·연수 제안 채택) ②운영 현황 스트립(당직·drill 성적·디스패치 job·연수 D-day) ③매뉴얼 탭(`notes/manual/`) | — | worklog-board repo 의 spec update, 별도 세션. 데이터는 전부 기존 산출물(`notes/oncall`·`notes/study`·`drill/results`·`.dispatch/jobs.log`) — board 는 read+view 만 |

> _졸업_: `drill FAIL 자동 진단` 은 backlog 졸업 — `run.sh` 에 FAIL→`<case>.diagnosis.md`(진단+수정안 초안, 적용 X) 단계로 부착됨(현역 표 모의훈련 행). `study 🔴 자동 초안`(T2, 2026-06-15) 도 동반 — 둘 다 _초안까지, 적용은 사용자 서명_.

## 루프 러너 — core/adapter 분리 (2026-07-01)

루프의 **케이스(prompt/fixture/assert)는 런타임 중립**, **러너만 어댑터별**이다 — 하네스 전체의 core/adapter 분리를 루프 축에도 적용. `loops/lib-runner.sh` 의 `run_case_on_adapter <adapter> …` 가 `claude`(`claude -p --output-format json`) · `codex`(`codex exec --json`) · `opencode`(`opencode run --format json`) 를 같은 계약(transcript + `turns|in_tok|out_tok|cost`)으로 정규화한다. `drill/run.sh --adapter <a>` (또는 `DRILL_ADAPTER`) 로 선택하며 기본은 `auto`다.

- **케이스 포터블화**: 마커 경로는 `$DRILL_MARKER_HOME/.spec-grounding`(러너가 어댑터 agent-home 으로 export), 산출물은 `.agent_reports`(+legacy `.claude_reports`). g4_spec_gate 가 포터블 기준 케이스. design(g8*)·mem_builtin 은 claude 고유(design-MCP·claude 내장 memory)라 잔존.
- **공통 usage-aware 선택**: `DRILL_ADAPTER=auto`와 `LOOP_ADAPTER=auto`가 기본이다. `utilities/usage-check.sh --select <routing-key>`가 한 canonical jobs.log의 known-limit을 먼저 회피하고, 한쪽만 `ok`면 그쪽, 둘 다 `ok|unknown`이면 `HARNESS_CAPACITY_BIAS=claude|codex` 또는 날짜+loop key 중립 분산으로 고른다. 둘 다 limited면 실행하지 않는다. 정확한 잔여 quota API가 없으므로 `auto`는 잔여 퍼센트 추정이 아니다. "거의 소진"처럼 limit 전 사람이 아는 상태는 `HARNESS_CAPACITY_BIAS`로 전달한다.
- **명시 선택**: `DRILL_ADAPTER`/`--adapter` 또는 `LOOP_ADAPTER`를 `claude|codex|opencode`로 주면 강제 선택이며 auto failover하지 않는다. OpenCode는 사용량 상태원이 없어 명시 선택만 지원한다.
- **Fleet·실행 중 failover**: drill case와 oncall/study runtime attempt는 모두 physical harness repo의 한 canonical jobs.log에 `open→done`으로 보여 중복 Fleet tree를 만들지 않는다. auto로 고른 런타임이 새 session/usage limit을 반환하면 그 row에 `note=dead-*-limit,reset=`을 남긴다. oncall/study는 같은 실행에서 반대 하네스로 한 번 즉시 넘기고, drill은 같은 case를 한 번 넘긴 뒤 다음 case 전 상태를 다시 읽는다.
- **oncall/study 러너**: `loops/lib.sh` 의 기존 `run_claude_retry` 이름은 호출 호환을 위해 유지하지만 실제로는 Claude/Codex/OpenCode dispatch를 담당한다. Codex/OpenCode는 자체 sandbox/permission으로 프롬프트(oncall.md/study.md)를 돌리고 Claude 전용 인자(`--model`/`--allowedTools`)는 무시한다. note는 이미 포터블한 `autopilot-note` capability라 스케줄 shim만 남음.
- **behavioral 검증 게이트 (선결)**: codex/opencode 로 케이스를 _실제_ 돌리려면 (1) 해당 어댑터의 runtime projection 설치(bootstrap+hooks/plugin 로드), (2) 마커 등 하네스 상태쓰기가 sandbox 안에 떨어지게 agent-home 배치가 필요. 러너·케이스 배선은 완료, 이 게이트가 다음 단계.
- 진단·judge 메타 층도 그 실행에서 선택된 adapter를 재사용해 다른 runtime 토큰을 암묵 소비하지 않는다.

## 케이스 승격 (오답노트 → drill)

실사고 발생 → 그 상황을 fixture 로 재현해 `drill/cases/` 추가. 트리거 발화: "이거 drill 케이스로 박아".
