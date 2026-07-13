## Proactive nudge (context-aware — 메인 에이전트가 먼저 제안)

post-it 의 목적 = 에이전트가 _사용자 흐름을 이어가고_(연속성) + _사용자가 놓친 것을 상기_(nudge). **working 기억 저장은 _자동_** (통합 기억 §7 자동 write 불변식 — confirm 없음), 세션 단절을 막기 위해 메인 에이전트 는 다음 신호에서 working 맥락을 **자동 기록(store working tier)** 한다:

- **context 사용량 ~50%+** — statusline context 막대·긴 대화·compaction 임박. → working 맥락 자동 기록 + 한 줄 보고.
- **wind-down 발화** — "오늘 여기까지" / "내일 이어서" / `/clear` 직전 류. → 세션 working 맥락(진행중·결정·다음 hint) 자동 handoff 기록.
- **작업 한 덩어리 완료** — 재사용 가치 있는 thread/decision 자동 `mem note`.

> **자동 기록 모델 (사용자는 post-it 을 안 본다)**: working 맥락은 _자동 기록_ (저장 confirm 없음 — §7 기억 저장 자동). 자동 handoff 는 sweep 을 _자동 포함_ — 확실한 졸업·stale 만 자동 prune (애매하면 keep), 결과는 _한 줄 보고_. **confirm 은 _prune/삭제_ 같은 비가역 자리만** (저장 자체는 자동). 줄 단위 검토는 사용자가 `/post-it sweep` 를 직접 칠 때만.

> 이 nudge 의 _트리거 규칙_ 은 runtime adapter bootstrap 에도 한 줄 있다 (SKILL.md 는 호출 시만 로드되므로, 자발적 제안은 adapter bootstrap 이 발화시킴). hard backstop 으로 PreCompact hook 을 둘 수 있으나(옵션, 미설정 시 nudge 만), hook 은 셸 스크립트라 _고정 리마인드_ 만 — 똑똑한 요약 handoff 는 대화 안의 에이전트만 가능.

## What this skill is NOT

- **자동 메모리 시스템 대체 X** — post-it 은 DB store 의 _working tier 사람-편집 자리_ 이고(`mem recall` 한 면에서 검색), 하네스 auto-memory(`projects/*/memory/` → store durable mirror)와 역할이 다르다.
- **영구 기록 X** — post-it 은 포스트잇. 영구 진실은 산출물·코드·git·구조화 프로필(DB type=profile 레코드). 엔트리는 졸업하면 떼어낸다 (sweep/promote).
- **코드/문서 변경 기록 X** — `autopilot-code` 의 `plans/`, `autopilot-draft` 의 `documents/`.
- **세션 활동 로그 X** — `pipeline_summary.md` 등에 이미 누적.

post-it 은 "매 세션 시작 시 알아야 할, 아직 산출물로 졸업하지 않은 한정된 working 맥락"만 담는다.

## Auto-memory와의 경계

store 단일소스 모델에서 두 경로는 같은 `memory.db` 의 다른 면이다.

| 경로 | store 위치 | 갱신 |
|---|---|---|
| `<agent-home>/projects/*/memory/` (하네스 auto-memory write 면) | SessionEnd `mem sync` → `memory.db` **durable**(project/global scope) 행으로 mirror; git 미러 `dump.jsonl` | 하네스 자동 write → sync |
| DB working tier (본 skill — `mem note`/`mem add`) | `memory.db` **working**(project scope) 레코드 직접 write; git 미러 `dump.jsonl` | 사용자 `/post-it` 로만 |

구분:
- **이 레포에만 적용되는 사실** (노션 위치, 데이터셋 경로, 진행 중 작업) → `--scope project` (DB working)
- **사용자 자신 / 일반 작업 선호** (Korean output, 코드 스타일) → durable auto-memory 또는 `--scope user`
겹치면 project working 레코드가 더 정확한 local context 라 우선. `mem recall` 이 양쪽을 한 면에서 검색한다.

## Writing Style (간결성 원칙 — 반드시 준수)

working 레코드는 세션 주입 시 항상 읽히는 컨텍스트. **짧고 dense 하게.**

- **한 bullet = 한 줄** (정 길면 최대 2줄).
- **명사구 / 사실 문장**. 형용사·부연·존댓말·이유 설명 최소화.
  - ❌ `Overleaf 는 X 폴더 아래 정리하는 게 좋습니다. 이유는...`
  - ✅ `Overleaf 정리 위치: <Overleaf URL>/TF-Restormer`
- **핵심 어휘만**. 한·영 혼용 OK, 약어·기호(`→`, `&`, `vs`) 적극.
- **카테고리 중복 금지** — 같은 정보는 한 곳에만.
- **시간성**: convention/reference → 날짜 X. decision → `YYYY-MM-DD:` 필수. thread → `[in-progress YYYY-MM-DD]` / `[blocked YYYY-MM-DD]` 필수.
- **메타 코멘트 금지** — "TODO 추후 확인" 류 X. thread 로.
- `handoff` 요약·`sweep` pointer 도 이 원칙 (1줄).
