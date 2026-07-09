# 하네스 3층 정합성 감사 — summary

> 상세·근거는 [`findings.md`](findings.md), 축별 심층은 [`cards/`](cards/). 본 문서는 상위 요약만.
> 총 21건(P0 0 · P1 8 · P2 13). 안전 hook·하드순서 게이트·런타임 wiring 은 정합 — 파손은 없으나 **공유층 물리 복제가 구조적 drift 원천**.

---

## (a) 기계적·명백 fix — 즉시 처리 가능 (설계 결정 불필요)

| # | 위치 | 고칠 것 | 근거 |
|---|---|---|---|
| a1 | `adapters/claude/CLAUDE.md:46` | `autopilot-code --qa quick` → `--intensity quick` | [1-1] |
| a2 | `adapters/claude/CLAUDE.md:54` | `CONVENTIONS.md §5.10`/bare `§5.9·§5.10` → `OPERATIONS.md §5.10/§5.9` | [4-2] |
| a3 | `adapters/claude/CLAUDE.md:120` | 함정 문구 quick/standard 를 `--intensity` 축으로 명확화 | [1-2] |
| a4 | `CLAUDE.md:67` ↔ `CONVENTIONS.md:604` | ScheduleWakeup 수치 10–30분/15–20분 통일 | [1-3] |
| a5 | `report-generation.md:290` | 죽은 앵커 `§1.4`→`§1.1`, "default thorough 통일"→intensity-derived | [4-1] |
| a6 | `loops/study.md:14` | `CONVENTIONS §3.6` → `§3(항목 8)` | [4-3] |
| a7 | `core/ADAPTATION_INVENTORY.md:33` | Codex hook location 을 실제 7-스크립트+`run-hook.sh` 로 | [2-1] |
| a8 | `core/ADAPTATION_INVENTORY.md:30` | Codex agent 행에 EXTRA_AGENTS(memory-scout,§7.4) 문구 추가 | [2-3] |
| a9 | `adapters/codex/ADAPTATION.md:50,397` | 요약표·매핑행을 7-스크립트로 통일 | [2-2] |
| a10 | `core/DESIGN_PRINCIPLES.md:97` | 로스터에 memory-scout 추가 또는 roles/README 포인터화 | [3-2] |
| a11 | `adapters/claude/CLAUDE.md:99` | recall 신호어 6→8(`지난번에·이전에`) 또는 "(전체 MEMORY §7.5)" | [5-1] |
| a12 | `utilities/agent-worklog-state.sh:41` (+claude 사본) | board probe 에 `.agent_reports` 추가 | [7-2] |
| a13 | `adapters/codex/ADAPTATION.md:184-432` | 모델 튜플 1곳 canonical + 나머지 포인터 | [3-1] |
| a14 | `loops/drill/cases/{g5,g4}` | `.agent_reports` fixture 1개 복제(신표준 회귀) | [7-1] |

> 모두 지침 파일 수정이라 **본 read-only 감사에선 미적용**. 반영은 소유 스킬(대개 core 먼저 → adapter) 경유. a7~a10·a13 은 core/adapter ledger, a1~a4·a11 은 CLAUDE.md → core-first 게이트 유의.

## (b) 구조적 개선 후보 — GSD 조사 결과와 종합 후 메인 오케스트레이터 결정

| # | 후보 | 왜 구조적인가 | 근거 |
|---|---|---|---|
| b1 | **공유층 물리 이중화 해소** — 최상위 `hooks/`·`tools/`·`utilities/` 와 `adapters/claude/` 복사본을 (i) content-parity 가드 추가 (ii) wrapper/symlink 전환 (iii) 단일 canonical 선언 중 택1 | 두 복사본을 묶는 바인딩이 없어 **fix 가 한쪽에만 반영**됨(이미 §S-1 spec-read-marker·§S-2 harness-status 발생). Claude=복사본 실행 / Codex·OpenCode=공유본 실행 / 가드=공유본만 검증 → acceptance test `INVENTORY:113`("projections, not independent sources")와 자기모순 | [S-1][S-2][S-3][S-4] |
| b2 | **포터블 행동 규율의 core 승격 범위 결정** — 말투·간결·pause·자율·후속동기화·"무조건 브랜치" 를 어디까지 core(또는 roles/)로 올릴지 | 현재 Claude bootstrap 에만 풍부, Codex/OpenCode 는 4줄. 런타임 전환 시 행동 계약이 조용히 빈약해짐. 단 core 가 "응답 메타원칙은 adapter single source" 로 명시 위임한 자리라 **어디까지 core 로 올릴지가 설계 판단** | [6-1][6-2] |
| b3 | **parity 가드의 검증 대상 정합** — `check-adaptation-boundary.sh` 가 공유본만 assert 하는 구조를 런타임 실행본까지 확장 | 가드 green ≠ 런타임 정합(§S-1 이 정확히 이 틈으로 통과). 어느 복사본이 런타임 진실인지 가드가 알아야 함 | [S-1][S-3] |
| b4 | **ADAPTATION_INVENTORY 를 "서술" 에서 "파일목록 파생" 으로** — hook/agent 파일집합을 가드 열거·생성기에서 파생 | ledger 가 실제 surface(7-스크립트, EXTRA_AGENTS)와 수동 동기라 반복적 UNDERCLAIM | [2-1][2-2][2-3] |

## (c) 축별 발견 수 통계

| Axis | P0 | P1 | P2 | 계 |
|---|---|---|---|---|
| §S 구조(공유층 복제) | 0 | 3 | 1 | 4 |
| 1 core↔adapter drift | 0 | 1 | 2 | 3 |
| 2 parity 신고 정확성 | 0 | 1 | 2 | 3 |
| 3 single-source | 0 | 0 | 2 | 2 |
| 4 죽은 참조 | 0 | 1 | 2 | 3 |
| 5 문서↔코드 | 0 | 0 | 1 | 1 |
| 6 계층 방향 | 0 | 2 | 0 | 2 |
| 7 project·runtime | 0 | 0 | 3 | 3 |
| **합계** | **0** | **8** | **13** | **21** |

**무게중심**: (1) 발견의 절반 이상이 **Claude bootstrap(`adapters/claude/CLAUDE.md`)** — Codex/OpenCode 가 이미 intensity-first·OPERATIONS 분리를 반영했는데 Claude 만 stale. (2) 진짜 구조적 원인은 **공유층 물리 복제(§S)** — 사용자가 느낀 "매번 어긋남" 의 메커니즘적 진원지. (3) OVERCLAIM("있다는데 없음")은 0 — 전부 UNDERCLAIM/stale 계열이라 방향은 명확하고 fix 는 저위험.
