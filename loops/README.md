# loops/ — 상시 루프 카탈로그

세션 **밖**에서 독립 실행되는 것들의 집. (skills/agents/hooks 는 세션 _안_ 의 부품 — hooks 는 툴 호출 순간 강제, loops 는 세션 무관 실행.)

## autopilot 와의 관계 — 루프는 일을 하지 않는다

일은 전부 autopilot-* 파이프(+agents·skills·hooks)가 한다 — 루프는 파이프의 _앞(언제 돌릴지 발견·제안)_ 과 _뒤(산출물 정리·상태 감시·지침 검증)_ 만 담당. 어떤 루프도 라우팅·파이프 순서·산출물 컨벤션을 바꾸지 않는다. 미래 루프(학습 모니터·goal loop)도 동일 — 일손이 필요하면 _파이프를 호출_ 하지 직접 일하지 않는다. **autopilot = 동사(일하기), loop = 부사(언제·얼마나·끝났는지).**

## 계층 — "loop engineering" 은 4개 층의 통칭 (혼동 주의)

같은 모양(행동→검증→조정)이 네 박자로 돈다. **초(도구) → 분(QA) → 일(작업) → 주(세팅)**:

| 층 | 주기 | 실체 | 우리 자리 |
|---|---|---|---|
| L1 에이전트 루프 | 초 | LLM→도구→반복 (벤더 영역) | Claude Code 자체 — 소비만 |
| L2 과제 루프 | 분 | 한 작업 안 생성↔검증 (maker/verifier·QA 라운드) | skills/agents (기존) |
| L3 작업 루프 | 시간~일 | 세션 밖 발견·분사·기록 (cron+headless) | **본 폴더** — duty·note |
| L4 메타 루프 | 주 | 시스템 자체 시험·개선 | **본 폴더** — golden (+후보 setting-audit) |

공통 규약:
- **모든 루프의 출구는 보고·제안까지** — 삭제·지침 적용 같은 결정은 사용자. (브랜치 merge 는 Claude 선별 책임 — CONVENTIONS §5.10, 2026-06-11 위임.)
- 실행 흔적은 `loops/*.log` (자체 로테이션, gitignore). 비용 = 구독 사용량 잠식 (별도 과금 아님).
- 트리거 3형: 시간형(cron) / 사건형(필요 시 발사) / 상태형(외부 신호 감시).

## 현역

> 파일명은 ASCII 유지, 표기는 `당직(duty)` 처럼 병기.

| 루프 | 형 | 트리거 | 대상 | 하는 일 | 산출 | 사용자 접점 |
|---|---|---|---|---|---|---|
| **당직** (`duty`) | 시간 | cron 05:37 | 작업장 (repo·산출물·실험·루프 생존·모의훈련 미실행) | 야간 순찰 — 이상 **발견·보고만** | `notes/duty/<date>.md` (당직 보고서) | 아침 "당직 보고 처리해줘" |
| **일지** (`note`) | 시간 | cron 05:03 | 전날 산출물 내용 | worklog-board L2 **노트화·라우팅** (idempotent) | `notes/_layer2/notes/` + digest | worklog-board `/triage` |
| **모의훈련** (`golden/`) | 사건 | 지침 수정 후 `golden/run.sh` | Claude 행동 (지침 준수) | fixture 가상 상황에서 headless **시험·채점** | `golden/results/<일시>/` | FAIL 시 수정안 승인 |
| **연수** (`study`) | 시간 | cron 일요일 06:17 | 외부 동향 × 현 세팅 | agent engineering 신간·Claude Code 변경 조사 → 세팅 대조 → **개선 제안서만** (+ g0 세금 추세) | `notes/study/<date>.md` | 제안 채택 서명 → 적용 → 모의훈련 |

새벽 시간표: 05:03 note → 05:37 duty (충돌 방지 간격).

## 후보 (backlog)

| 후보 | 형 | 착수 조건 |
|---|---|---|
| **목표 루프 (goal loop)** | 목표 달성까지 반복 | 검증이 기계적인 첫 실전 자리 (테스트 전부 초록·ablation 표 빈칸 0 등). 부품: 기계적 목표 정의(루프가 수정 불가) + 회차별 새 세션·상태 파일 + 검증 게이트 + 무진전 N회 시 사람 호출 + 회차 상한 |
| 학습 모니터 | 상태 | 다음 autopilot-lab setup 때 실물(log 포맷·ckpt 경로)에 맞춰 |
| code discovery (깨진 테스트·TODO 스캔 → 수정 제안) | 시간 | duty 운영 안정 후 |
| worklog-board job 카드 (디스패치 현황 UI — `.dispatch/jobs.log` 를 board 가 read) | — | worklog-board repo 의 spec update, 별도 세션 (데이터 쪽은 §5.10 등록부 + 당직 7호로 가동 중) |
| golden FAIL 자동 진단 (run.sh 에 진단·수정안 초안 단계) | 사건 | baseline run 완료 후 부착 |

## 케이스 승격 (오답노트 → golden)

실사고 발생 → 그 상황을 fixture 로 재현해 `golden/cases/` 추가. 트리거 발화: "이거 golden 케이스로 박아".
