# loops/ — 상시 루프 카탈로그

세션 **밖**에서 독립 실행되는 것들의 집. (skills/agents/hooks 는 세션 _안_ 의 부품 — hooks 는 툴 호출 순간의 문지기, loops 는 세션 무관 일꾼.)

## 계층 — "loop engineering" 은 4개 층의 통칭 (혼동 주의)

같은 모양(행동→검증→조정)이 네 박자로 돈다. **초(도구) → 분(QA) → 일(작업) → 주(세팅)**:

| 층 | 주기 | 실체 | 우리 자리 |
|---|---|---|---|
| L1 에이전트 루프 | 초 | LLM→도구→반복 (벤더 영역) | Claude Code 자체 — 소비만 |
| L2 과제 루프 | 분 | 한 작업 안 생성↔검증 (maker/verifier·QA 라운드) | skills/agents (기존) |
| L3 작업 루프 | 시간~일 | 세션 밖 발견·분사·기록 (cron+headless) | **본 폴더** — scout·note |
| L4 메타 루프 | 주 | 시스템 자체 시험·개선 | **본 폴더** — golden (+후보 setting-audit) |

공통 규약:
- **모든 루프의 출구는 보고·제안까지** — 삭제·지침 적용 같은 결정은 사용자. (브랜치 merge 는 Claude 선별 책임 — CONVENTIONS §5.10, 2026-06-11 위임.)
- 실행 흔적은 `loops/*.log` (자체 로테이션, gitignore). 비용 = 구독 사용량 잠식 (별도 과금 아님).
- 트리거 3형: 시간형(cron) / 사건형(필요 시 발사) / 상태형(외부 신호 감시).

## 현역

| 루프 | 형 | 트리거 | 대상 | 하는 일 | 산출 | 사용자 접점 |
|---|---|---|---|---|---|---|
| **scout** (경비원) | 시간 | cron 05:37 | 작업장 (repo·산출물·실험·golden 미실행) | 이상 **발견·보고만** | `notes/scout/<date>.md` | 아침 "scout 처리해줘" |
| **note** (사서) | 시간 | cron 05:03 | 전날 산출물 내용 | worklog-board L2 **노트화·라우팅** (idempotent) | `notes/_layer2/notes/` + digest | worklog-board `/triage` |
| **golden** (감사관) | 사건 | 지침 수정 후 `golden/run.sh` | Claude 행동 (지침 준수) | fixture 무대에서 headless **시험·채점** | `golden/results/<일시>/` | FAIL 시 수정안 승인 |

새벽 시간표: 05:03 note → 05:37 scout (충돌 방지 간격).

## 후보 (backlog)

| 후보 | 형 | 착수 조건 |
|---|---|---|
| 학습 모니터 | 상태 | 다음 autopilot-lab setup 때 실물(log 포맷·ckpt 경로)에 맞춰 |
| setting-audit (지침 다이어트 제안) | 사건/월간 | 세팅 복잡도 체감 시 — 중복·모순·죽은 참조 스캔 → 제안서만 |
| code discovery (깨진 테스트·TODO 스캔 → 수정 제안) | 시간 | scout 운영 안정 후 |
| golden FAIL 자동 진단 (run.sh 에 진단·수정안 초안 단계) | 사건 | baseline run 완료 후 부착 |

## 케이스 승격 (오답노트 → golden)

실사고 발생 → 그 상황을 fixture 로 재현해 `golden/cases/` 추가. 트리거 발화: "이거 golden 케이스로 박아".
