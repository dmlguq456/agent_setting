# Final Report — stage-dispatch Phase 1

**status: done** · intensity strong · qa standard · 브랜치 `stage-dispatch-impl1` (push·merge 는 메인 오케스트레이터)

spec `.agent_reports/spec/stage-dispatch/prd.md` 의 §9 영향 표면 1-12 를 core-first 로 개정하고,
wrapper 최소 증분 + autopilot-code 스테이지-분사 pilot 1회를 완주했다.

## 개정한 표면 (12/12)

- **core** — OPERATIONS §5.10 ③④⑤(얇은 conductor + depth-2 스테이지-워커 클래스별 write + 동시상한 Σ), WORKFLOW §1.1·§5, CONVENTIONS §1·§2.3(SD-5 role 매핑), DESIGN_PRINCIPLES §8+부록(file-only handoff 승격·2026-07-06 반전 이력).
- **skills** — context-and-guards 스테이지 분사 금지→기본 권장 반전(우려 해소 근거 병기), dev-pipeline 스테이지 분사 오케스트레이션 블록, 4 sub-skill 독립 세션 진입점 계약(code-report 는 dispatched 세션의 orchestration-memory-없음 분기 포함).
- **adapters** — claude CLAUDE.md §0(C) 깊이1 전용→스테이지 depth-2, codex/opencode AGENTS.md 동형(parity), dispatch-headless.py depth-aware depth_note(재작성 X, SD-9).

## Deliverable
- 계약 개정 커밋 `cfbd098` (core 4 + skills 6×2 projection + adapters 3 + wrapper 1).
- wrapper 증분: `depth_note` depth/worker_role-aware 3분기. depth=2/parent/worker_role/owner/role_map 는 기존 그대로 (스테이지 분사에 이미 충분 — SD-9 확인).

## Pilot (SD-OPEN-1)
`/tmp` calc fixture 에 autopilot-code standard 사이클을 4 스테이지 depth-2 분사로 완주 —
fixture-local jobs.log 에 `depth=2,parent=<conductor>,worker_role=code-*,owner=autopilot-code` 4 row,
실 레지스트리 무오염, depth≤2 불변, 산출물(plan/checklist/test_report/final_report) 정상, 소스 VERIFY_OK.
계측·발견 상세 = `dev_logs/pilot_metrics.md`.

## 검증
boundary green(exit 0, 예고된 drill FAIL 미발생) · skills byte-equiv · footprint --strict exit 0 ·
py_compile · 앵커 grep 20/20 · pilot 10 체크 PASS (`test_logs/test_report.md`).

## 미결 (main+사용자 몫)
- SD-OPEN-1 마이크로-스테이지 inline 임계 *확정* (pilot 데이터만 수집 — report/test 급 경량 스테이지 부근 시사).
- Phase 2: fleet 스테이지 row 라벨(§9-13), drill 회귀 케이스(§9-14), 타 autopilot-* 확산.
- 부수 발견: (1) spec-less repo 분사 시 artifact-guard 가 sidecar 신규파일 차단 → conductor 가 spec 전제 선보장 필요. (2) 스테이지 세션 SessionEnd 가 mem curator 를 띄움(공유 store 오염은 없었음) — Phase 2 확산 시 masked-home/curation-suppress 검토 여지.
