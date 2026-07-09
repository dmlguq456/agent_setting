## 피드백 간단 처리 모드 (`--feedback` — worklog-board prd §16 검토함 양방향 루프)

worklog-board 검토함은 v48 까지 _에이전트 제안 → 사람 결재_ 단방향이었다. v49~v50 은 **사람→에이전트 의견 채널**을 더해 루프를 닫는다 (상세 = worklog-board prd §16). 사용자가 앱 검토함에서 보낸 의견은 `<target>/_feedback/<id>.md` 큐(앱 write·fs 곁가지, `_triage` 동형 — DB 이전 대상)에 쌓이고, 본 모드가 그 큐를 집어 갈래별로 처리한 결과를 **다시 검토함에 surface → 사용자 승인 경유**한다.

> **불변식 = 모든 적용은 검토함 승인 경유 (자동 적용 0).** 사용자 피드백 = _의도_, 검토함 승인 = _확정_. 본 모드는 _제안 재생성·코드 변경 준비_ 까지만 — DB write·머지는 승인/수확 자리.

본 모드는 풀 Stage A-F 가 아니라 _항목당 가볍게_ 도는 경량 자리 (default `--qa light`, 즉시·저비용). 트리거 = 앱 submit 직후(즉시 — prd §16.5 Q1) 또는 짧은 폴링.

### 입력
`<target>/_feedback/` 의 `status: pending` 항목. frontmatter `kind`(proposal/ui-code)·`screen`·`proposal_id`(proposal 만)·본문(사용자 의견). worklog-board `lib/feedback.ts` 의 `listPendingFeedback()` 가 진입점.

### 라우팅 (피드백 갈래 + Q4 위험도 분기)

**A. proposal 피드백** (`kind: proposal`·`proposal_id` 있음) — 그 `_triage/<proposal_id>.md` 제안을 _피드백 반영해 재생성_:
- 의견을 읽고 제안 payload 를 고쳐 **revised payload** 를 만든다 (예: 제목 교정·프로젝트 재배정·연결 노트 조정).
- worklog-board `scripts/process-feedback.ts` 의 `reviseProposal({ proposalId, revisedPayload, feedbackId })` 로 `_triage` 파일만 갱신 — **DB write 0**. 원본 제안은 `revised_from` 스냅샷으로 보존(overlay 의 원본↔수정 토글용), `payload` 는 revised 로 교체(승인 시 기존 approve 경로가 그대로 revised 사용).
- idempotent — 재실행해도 `revised_from` 은 최초 원본 유지. 검토함 계층 면 제안 행에 `수정됨` 배지로 surface.
- 가볍고 즉시 (데이터 재생성이라 안전 — verify 게이트 불요).

**B. ui-code 피드백** (`kind: ui-code`·화면 일반 의견) — 위험도(prd §16.5 Q4)로 3분기:
- **시각 폴리시 (낮은 위험)** — worktree 작업 브랜치에서 직접 fix → `Agent(디자인팀 verifier)` 로 실화면(light/dark/mobile) 회귀 검수 PASS → worklog-board `lib/change-review.ts` 큐(`_change_review/<id>.md`, `risk: visual`)에 **"변경 검토" 항목** 생성(diff/스크린샷). 승인=`approved-for-merge` 마킹(머지는 에이전트 수확 자리 — prd §16.5 Q2), 거절=worktree 폐기 마킹.
- **컴포넌트 구조 (중위험)** — **자동 수정 안 함**. `_change_review` 항목을 `risk: structure`·확인 필요 표시로만 올린다(제안 — 사용자 확인 후 `autopilot-code` 로 착수). verify 게이트(디자인팀 render)는 _시각 회귀_ 만 잡고 _구조·데이터 의도_ 는 못 잡으므로 자동 fix 금지.
- **DB/enum/API spec (고위험)** — 본 spec 의 v45~v48 불변식(DB 0)과 충돌하므로 **반드시 spec 경유**. 코드 손대지 말고 _`autopilot-spec` update → `autopilot-code` 로 escalate_ 한다고 `_change_review` 항목(`risk: db`·확인 필요)에 기록 + 본 모드 보고에 escalate 명시.

### 처리 후
각 처리한 `_feedback` 항목은 `lib/feedback.ts` 의 status 전이로 `status: processed` 마킹 (재실행 시 중복 처리 안 함 — idempotent). A 재생성·B 변경검토 항목 생성 자체는 모두 _제안/검토 staging_ 일 뿐, 확정은 검토함 승인.

### 경계
- **머지 안 함** — B 승인의 `approved-for-merge` 마킹은 _신호_ 일 뿐, 실제 worktree 머지는 §5.10 따라 머지 신호 자리 Claude 세션이 수확(prd §16.5 Q2).
- **DB write 0** — A 는 제안 재생성(`_triage` 파일만), B 는 코드/큐 파일만. 신규 컬럼·enum·마이그레이션은 spec 경유.
- worklog-board cwd 에서 `scripts/process-feedback.ts`·`lib/feedback.ts`·`lib/change-review.ts` 호출 (CARDS_DIR 부모의 `_feedback`/`_triage`/`_change_review`).
