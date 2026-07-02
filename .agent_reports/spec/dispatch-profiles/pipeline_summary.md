# dispatch-profiles — pipeline summary

## 2026-07-02 · spec v1 (autopilot-spec, qa=standard)

**계기**: 사용자 설계 논의 (2026-07-02) — "모든 엔트리 스킬 분사?" → 하이브리드 결론, "분사 케이스별 다이어트+특화 마스킹 가능?" → 부분 투영 확정, "특화 지침을 더 구성하고 main 은 오히려 가리기" → 3층 대칭 모델. "ㅇㅇ 자율적으로 시작해" 로 spec 착수.

**사전 검증 (PRD 전 확정된 사실)**:
- CLAUDE_CONFIG_DIR 실측 통과 (haiku 1콜) — 마커 CLAUDE.md 로드 ✓ / credentials 심링크 auth ✓ / projects·sessions 상태가 override home 에 격리 ✓. 공식 env-vars 문서엔 미기재 (claude-code-guide 의 문서 기반 "부재" 답변을 실측이 반증).
- repo 현황: Claude dispatch wrapper 부재 (수기 §5.10 컨벤션), codex `dispatch-headless.py` 280줄 + `CODEX_HOME` 격리 기실증, jobs.log 6필드 (`pipe` = comma k=v bag), roles/=portable 카탈로그 + adapter 실현, projection = 2층 심링크 farm + `--check` 가드.

**산출**: `prd.md` (cli mode, §1 갭 3개 → §2 3층 모델 → §3 선언 스키마 → §4 CLI 2종 → §5 마스킹 규칙 → §6 하네스 attach → §7 관제 연동 → §8 하이브리드 라우팅[v1 범위 외] → §9 module → §10 diagram → §11 DP-1~12 → §12 의미↔규칙 경계).

**QA**: 품질관리팀 plan-review r1 — blocker 1 (bootstrap 조립 규칙 미정의) / major 4 (portable 경계 위반·opencode 채널 미정·home 수명주기·index.tsv 동시성) / minor 4. 전건 반영 — 핵심 재설계: 층 경계=소스 파일 분리(DP-10), per-dispatch ephemeral home(DP-4), index 파일 제거→결정론 유도(DP-11), v1=claude+codex(DP-12). 리뷰 원문+반영 내역 = `_internal/plan_review_r1.md`. 후방호환 주장(DP-5·7)은 리뷰가 3 reader 실코드 대조로 확인.

**다음**: autopilot-code 로 구현 (plans/ 사이클) — worktree 분사. 우선순위: templates+build-home.py → claude dispatch-headless.py → codex --profile → liveness/fleet 연동. §8 하이브리드 라우팅 문서 갱신은 별도 사이클.
