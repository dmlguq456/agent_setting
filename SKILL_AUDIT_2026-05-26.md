# Skill·Agent·운영문서 무게 진단 리포트 (2026-05-26)

> read-only 진단. 4개 영역(SKILL.md / DEPRECATED / agents+modes / 자매 운영문서)을 병렬 분석한 통합본.
> **주의** — 본 리포트의 줄 번호 인용은 진단 시점 추정치. 실제 다듬기 단계에서 각 파일 재확인 후 편집.

---

## 0. 한 줄 진단

무게의 단일 근본 원인: **각 단위(skill/agent)가 자기 완결성을 추구하면서 global 정책(CLAUDE.md / CONVENTIONS.md / DESIGN_PRINCIPLES.md)에 이미 single-source로 정의된 내용을 각자 다시 풀어쓴다.** 완전성 100% + 간결성 40% 상태. 포인터로 위임하면 철학 손실 없이 ~40% 압축 가능.

현황 규모:
- SKILL.md 33개 = 9,347줄 (상위 8개가 절반 ~4,866줄)
- agents 8개 = 766줄 / agent-modes 22개 = 1,440줄
- 자매 운영문서 5개 = 1,735줄
- DEPRECATED 4개 = 632줄 (순수 noise)

---

## 1. SKILL.md (33개, 9,347줄)

### 무게 원인 분류 (상위 8개 기준)
| 원인 | 비중(추정) | 핵심 |
|---|---|---|
| (b) skill 간 중복 | ~40% | 같은 boilerplate가 여러 SKILL.md에 반복 |
| (a) 절차 과잉서술 | ~35% | mode 정의→추론→옵션→override 4회 재진술 |
| (c) 운영문서와 중복 | ~20% | CONVENTIONS/CLAUDE에 있는 걸 다시 풀이 |
| 핵심 로직 | ~5% | verification loop / mode 분기 / interface |

### 중복 패턴 종합 (제거 대상)
| 중복 항목 | 등장 | 권장 fix |
|---|---|---|
| **Language Rule** ("think English, write Korean") | 33개 전수 | CLAUDE.md §1로 단일화, 특수사항만 |
| **QA 5단계 boilerplate** | 11개 skill | CONVENTIONS.md §1 링크 1줄로 |
| **Default Invocation Rule** (trigger→옵션→override) | 6개 (draft/research/spec/code/lab/refine) | CLAUDE.md §6 canonical, trigger seed만 |
| **Scope Clarification** (Step 0/1.5 자율진행 흐름) | 4개 | CLAUDE.md §5 pattern, 질문 seed만 |
| **pipeline_state/summary 스키마** | 4개 | CONVENTIONS.md §5 공통 스키마 + 예시 |
| **artifact 3-tier 규칙** | 8개 | CONVENTIONS.md §5 링크 + 경로 2줄 |
| **resume (`--from`) 로직** | 4개 | CONVENTIONS.md 공통 정의 |
| **user-refine pause 동작** | 3개 | CLAUDE.md §4 standard behavior |

### 압축 시뮬레이션 (상위 8개)
draft 868→520 · research 855→510 · spec 624→370 · refine 507→380 · code 501→370 · lab 496→340 · analyze-project 482→320 · analyze-user 442→280. **합계 4,866 → ~2,800줄 (42%↓), 운영문서 ~+200줄, 순 -1,900줄.**

### 절대 보존 (줄이면 안 됨)
verification loop 구성 차이 · mode 분기 logic · interface contract(skill 간 데이터 인계) · 각 phase 구체 산출물 목록.

### 리스크
신규 reader의 context jump(CLAUDE.md 왕복) 인지부담 ↑. trade-off: 완전성 100/간결성 40 → 완전성 95/간결성 75.

---

## 2. DEPRECATED 4개 (app-qa/build/ship/iterate, 632줄) — **즉시 삭제 가능**

| skill | 대체 | 외부 참조 |
|---|---|---|
| app-qa | autopilot-code 앱 mode 검증 | 0건 |
| app-build | autopilot-code 앱 mode | design-handoff L97 1건 |
| app-ship | autopilot-ship (별도 skill) | 0건 |
| app-iterate | autopilot-code 호출 자체 | 0건 |

삭제 전 정리 체크리스트:
- [ ] README.md L251 — 4개 언급 제거
- [ ] AUTOPILOT_FLOWS.md L321-336 — DEPRECATED 표 제거 또는 archive로
- [ ] design-handoff/SKILL.md L97 — `/app-build` → `/autopilot-code`
- [ ] CONVENTIONS.md §6.6 — 현상 유지(정확), L465 "본 4개 파일" 명확화
- [ ] skills/.sync_state.json — 4개 entry 제거 (또는 sync-skills 재실행)
- [ ] 4개 디렉토리 삭제

**삭제 후 workflow 영향: 무.** autopilot-code/ship 이미 운영 중, 자동 감지.

---

## 3. agents (8) + agent-modes (22)

### 핵심 문제: 라우터 ↔ mode 파일 역할 혼재
라우터(agents/*.md)가 mode 파일에 있어야 할 **절차(Procedure)·Output Format**을 중복 보유.

| 파일 | 줄 | 문제 | 압축 가능 |
|---|---|---|---|
| codex-review-team | 174 | Output Format 2종 70줄(mode에 이미 존재) | ~95 (55%↓) |
| editorial-team | 138 | 편집 규칙 60줄(mode로 분산해야) | ~68 (51%↓) |
| plan-team | 121 | Procedure 74줄(mode와 90% 중복) | ~55 (55%↓) |
| material-team | 106 | 메모리 9줄 과잉 | ~85 (20%↓) |
| research-survey(mode) | 186 | 라우터/mode 경계 애매(구조적) | 분리 검토 |

### boilerplate 반복
| 항목 | 등장 | fix |
|---|---|---|
| **Return Format (CRITICAL)** | 11회 (mode 전반) | 공통 정의 + verdict 예시만 override |
| **Update agent memory** | 20회 (agent+mode 거의 전부) | 라우터 전용으로, mode는 권고만 |
| **Language Rule** | 7회 | CONVENTIONS/CLAUDE 전역 기본값 |

### 보존
Mode Selection 테이블 · tool 권한(손대는/안대는 영역) · team별 컨텍스트 · mode별 Procedure/sub-mode 분기.

### 통합 검토 후보
- design/critic — 호출 빈도 낮음, maker 내부 sub-step 검토
- editorial polish/review의 Catch-net signals 95% 동일 → 공용 섹션화

---

## 4. 자매 운영문서 (5개, 1,735줄)

single-source 원칙 ~95% 준수. 단 개념 중복 정의로 drift 위험인 곳:

| 중복 개념 | 위치 A | 위치 B | 일치도 |
|---|---|---|---|
| fact-checker 범위 | DESIGN_PRINCIPLES §5 | CONVENTIONS §1.1 | 95% |
| pause flag 정신 | DESIGN_PRINCIPLES §2 | CLAUDE.md §4 | 동일 |
| T1/T2/T3 Tier 정의 | DESIGN_PRINCIPLES §4 | CONVENTIONS §5.2 | 개념 분산 |
| 판교체/편집 원칙 | DESIGN_PRINCIPLES §6 | CLAUDE.md §1 | 95% |
| **워크플로우 map** | README §1 | AUTOPILOT_FLOWS §1 | **90% (형식만 다름)** |
| 산출물 폴더 구조 | CONVENTIONS §5.3-5.7 | AUTOPILOT_FLOWS §4 | 70% |

### 판정
- **README vs AUTOPILOT_FLOWS** = 가장 큰 중복(90%). 목적 분리 명확화: README=overview+entry, FLOWS=호출 자리 예시. 또는 통합.
- DESIGN_PRINCIPLES §5 fact-checker / §4 Tier / §6 판교체 → CONVENTIONS·CLAUDE 포인터로 축약(개념 재서술 금지, 아키텍처 차원만).
- CONVENTIONS §5.3-5.7 폴더 세부 → AUTOPILOT_FLOWS로 이동 검토. §6.2-6.4 호출 흐름 → README 요약.

---

## 5. 권장 실행 순서

| 단계 | 작업 | 리스크 | 효과 |
|---|---|---|---|
| **Phase 1** (quick win) | DEPRECATED 4개 삭제 + 참조 5곳 정리 | 무 | -632줄, noise 제거 |
| **Phase 2** | 자매 문서 중복 정리 (fact-checker/Tier/판교체 포인터화, README↔FLOWS 목적 분리) | 낮음 | single-source 강화 |
| **Phase 3** | agents 라우터 ↔ mode 역할 정리 (Procedure/Output Format mode로, boilerplate 공용화) | 중 | -300줄 |
| **Phase 4** | SKILL.md 8개 boilerplate 위임 압축 (Language/QA/Invocation/pipeline) | 중 | -1,900줄 |

Phase 1→2는 거의 무손실. Phase 3→4는 단위별 검토하며 진행 권장.
