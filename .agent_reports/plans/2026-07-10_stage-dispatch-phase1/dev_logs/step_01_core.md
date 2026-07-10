# Step 1 — core 계약 문서 개정 (surfaces 1-6, 5b)

core-first 게이트 준수: core 6개 파일 Read 후 편집.

| Surface | 파일 | 변경 |
|---|---|---|
| 1,2 | `core/OPERATIONS.md §5.10 ③④` | ③ = `standard+` depth-1 owner 를 얇은 conductor 로 재정의(스테이지마다 depth-2 분사, verdict/status 만, file-only). ④ = depth-2 두 용법 (a)리뷰 워커 read-only (b)스테이지-워커 클래스별 write 소유(plan/execute=소스/test/report) 명문화. depth 3+ 금지 유지. |
| SD-6 | `core/OPERATIONS.md §5.10 ⑤` | 동시 상한 = `Σ(conductor+활성 스테이지) ≤ 5`, 순차라 conductor 당 ~2, execute 내부 병렬 미포함, 초과 시 큐잉. |
| 3 | `core/WORKFLOW.md §1.1` | standard/strong 행 Routing note 에 스테이지 depth-2 분사 기본 반영. direct/quick 는 기존 "no depth dispatch" 로 inline 이미 명시. |
| 4 | `core/WORKFLOW.md §5` | autopilot-code 팀이 스테이지 세션 _안_ 에서 실행, conductor 는 경로만 전달, direct/quick inline. |
| 5 | `core/CONVENTIONS.md §1` | Dispatch policy 열(standard/strong) + depth 계약 문단에 스테이지-워커 용법 (b) 추가, depth 3+ 금지 재확인. |
| 5b | `core/CONVENTIONS.md §2.3` | 표 뒤 스테이지↔model role 매핑 (SD-5): plan=deep maker, execute=fast implementer, test=variable, report=fast writer. conductor `--model-role` 명시. |
| 6 | `core/DESIGN_PRINCIPLES.md §8` + 부록 | §8 에 file-only handoff 를 headless 스테이지→conductor 로 승격 + 2026-07-06 반전 이력. 부록에 §8 행 신설. |

Decision: 문구는 최소 증분으로 유지(byte-budget) — 기존 문장 확장 형태, 새 절 신설 없음. spec SD-1~6 참조 앵커를 각 자리에 박아 추적성 확보.
