# 05 — 우리 세팅 개선 roadmap (actionable)

> Inferred goal: adopt/build — Hermes 설계요소를 우리 Claude Code 세팅에 *안전하게* 이식. 불변식 = "루프 출구는 제안까지, 결정은 사용자" (loops/README). 메커니즘만 차용, 결정 게이트는 사용자에 남긴다.

---

## 1. 이식 후보 우선순위 표

| # | 후보 | Hermes 근거 | 우리 적용 위치 | 난이도 | 기대효과 | 리스크 |
|---|---|---|---|---|---|---|
| **T1** | auto-memory 에 **자동 cross-session/cross-cwd recall 층** + 인덱스 채우기 | axis3 §4 FTS5 `session_search` | `projects/<cwd>/memory/` + 세션 주입 경로 + (신규) recall helper | 중 | 과거 결정·교정 자동 회상, 반복 질문 감소 | 인덱스 noise·과주입 → context 낭비 |
| **T2** | skill self-improvement 를 **drill/study 의 *제안 자동초안* 단계**로 | axis2 §1.3 `skill_manage` self-edit | `loops/study.sh`(외부대조 후 초안) · `loops/drill/run.sh`(FAIL 시 수정안 초안 — 이미 backlog) | 중 | 개선 제안 작성 비용↓, 사용자는 승인만 | 초안 품질·환각 → 사용자 검토 부담 |
| **T3** | post-it sweep 에 **시간기반 stale→archive lifecycle (플래깅만)** | axis2 §2 Curator 30d/90d | `skills/post-it`(sweep 로직) + `loops/oncall.sh`(stale 후보 보고) | 하 | stale 항목 누적 방지, lean 유지 | 살아있는 항목 오판 prune → 플래깅만(삭제는 보고) |
| **T4** | **periodic self-review nudge** 를 oncall/note 루프에 | axis3 §3 턴 카운터 nudge + per-turn review | `loops/oncall.sh`·`note.sh` (야간 회고 항목 추가) | 하 | "persist 할 게 있나" 자동 환기 → 메모리 성숙 | 노이즈 보고 증가 → 임계 조건 부여 |
| **T5** | memory write **품질 휴리스틱** (promote/skip 기준 명문화) | axis3 §2 write_approval + promote/skip | auto-memory 저장 규칙(SKILL/instruction) | 하 | 메모리 품질·일관성↑ | 과한 게이트 → 저장 누락 |
| **T6** | **multi-pass user modeling** 개념을 analyze-user 에 | axis3 §5 Honcho dialectic multi-pass | `skills/analyze-user`(initial→self-audit→reconciliation 단계) | 중 | user_profile 정합성·모순 점검↑ | 외부 Honcho 직접 의존은 거부(개념만 차용) |

---

## 2. 후보별 안전 이식 설계 (불변식 준수)

### T1 — auto-memory 자동 recall 층 (최우선)
- **무엇**: 과거 세션·다른 cwd 메모리를 *읽기 전용* 으로 검색하는 helper. SQLite FTS5 가 정석이나, 우리 메모리는 `projects/<cwd>/memory/*.md` 파일이므로 1차 구현은 `ripgrep` 기반 키워드 검색 + MEMORY.md 인덱스 강화로 시작 가능(외부 의존 0).
- **불변식 준수**: 읽기 전용 recall 은 *결정*이 아니라 *정보 제공* — 무해. 자동 *write* 는 도입 X(기존 정책: 행동양식은 원칙 문서, 사실은 수동/제안 저장).
- **단계**: ① 인덱스 먼저 채우기(얇은 MEMORY.md 보강) ② cwd-국소 recall helper ③ (선택) cross-cwd 검색 — 단 cross-cwd 는 per-cwd 격리 정책과 충돌하니 *명시 요청 시만*.

### T2 — drill/study 제안 자동초안
- **무엇**: study 가 외부 동향 대조 후 *개선 제안서*를 쓸 때, drill FAIL 시 *수정안*을 쓸 때 — Hermes `skill_manage` 처럼 *초안*을 자동 생성. 단 적용은 사용자 서명 후.
- **불변식 준수**: 출구가 "초안 제안"에서 멈춤. 자동 적용·자동 커밋 없음. (study 는 이미 "제안서만", drill 은 backlog "FAIL 자동 진단·수정안 초안" — 이 후보는 그 backlog 의 구체화.)

### T3 — post-it 시간기반 stale lifecycle
- **무엇**: post-it 항목에 last-touched 타임스탬프, N일 미갱신 시 oncall 이 "stale 후보" 플래깅 보고. archive 폴더로 이동은 사용자 확인 후.
- **불변식 준수**: 자동 *삭제* 아님 — 플래깅+보고. 기존 "확실한 것만 자동 prune" 정책의 시간축 강화.

### T4 — periodic self-review nudge
- **무엇**: oncall(야간) 순찰 항목에 "어제 세션에서 persist 할 결정·교정이 있었나" 회고 1항. note 가 산출물 노트화할 때 메모리 승격 후보도 같이 제안.
- **불변식 준수**: 보고만. 저장은 사용자 흐름 안에서.

### T5 — write 품질 휴리스틱
- **무엇**: auto-memory promote/skip 기준을 Hermes 휴리스틱(§axis3 §2)에 맞춰 명문화 — preferences·conventions·corrections·lessons 는 promote, trivial·re-discoverable·ephemera 는 skip. 이미 우리 메모리 가이드에 유사 항목 있음 → 정합·보강.

### T6 — analyze-user multi-pass
- **무엇**: analyze-user 의 프로필 갱신을 initial → self-audit(gap) → reconciliation(모순) 3-pass 로. Honcho 개념 차용, 외부 서비스 의존 없음.

---

## 3. 이식 거부 / 보류 (정직)

| 항목 | 거부 사유 |
|---|---|
| persistent multi-channel gateway | 쓰임 불일치(논문·실험·코드 파이프, push 채널 불필요) |
| Honcho 외부 FastAPI 직접 통합 | 외부 의존·데이터 외부 전송 — 개념(T6)만 차용 |
| skill 자동 *적용*(승인 없는 self-edit) | 우리 불변식 정면 위반 — 초안(T2)까지만 |
| Atropos weight 학습 경로 | 우리는 모델 소비자, 제작자 아님 — N/A |
| memory 자동 write(무승인) | 행동양식=원칙 문서·사실=제안 저장 정책과 충돌 |

---

## Next Pipeline

> ⚠️ 본 이식 대상은 `~/.claude` *자체* (Claude 세팅) — 일반 프로젝트의 autopilot-draft/code 핸드오프와 다르다.

| 채택 유형 | 경로 |
|---|---|
| **지침 문서 수정** (CLAUDE.md/CONVENTIONS/WORKFLOW/SKILL/loops/README) — T5·T2(제안 단계 정의)·T4 | **직접 Edit** + 편집 후 `loops/drill/run.sh` 회귀테스트 (CLAUDE.md 도메인 트리거: 지침 수정 후 drill 발사). 변경이 사용자향 wording 이면 편집팀 다듬기. |
| **새 루프/스킬 신설** (T1 recall helper, T3 lifecycle 로직, T6 multi-pass) — 코드/스크립트 산출 | **autopilot-spec → autopilot-code** (spec-first 하드 게이트). T1 은 `loops/` backlog "학습 모니터/code discovery" 와 묶어 spec. |
| **backlog 구체화** (T2 = drill FAIL 자동진단, T1 = 학습 모니터) | 기존 `loops/README` backlog 행을 spec 입력으로 — 별도 세션 권장 |

**채택 우선순위**: T1(메모리 갭 최대) → T5/T4(저난이도·즉효, 직접 Edit) → T3 → T2 → T6. T1 은 단독 세션으로 autopilot-spec 부터 시작 권장.

**Takeaway**: 6개 후보 모두 *메커니즘은 Hermes, 결정 게이트는 우리* 구조로 설계 — 가장 큰 갭(FTS5 자동 recall)을 T1 으로 메우는 게 1순위이고, 저난이도 지침 보강(T4·T5)은 직접 Edit + drill 로 같은 turn 처리 가능하다.
