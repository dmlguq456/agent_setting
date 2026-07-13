# Skill-Design Audit — 28스킬 4축 전수 진단 (Pocock rubric)

> mode: code · date: 2026-07-13 · intensity: thorough · owner: analyze-project (depth-1)
> **rubric SoT**: `.agent_reports/research/skill-design-principles/` — 06_implementation §3 8-Step(Step 0~7), 02_standards(정량 규범·failure 6종), 04_technical_deep_dive(메커니즘), analysis_summary §7(감사 체크리스트).
> 4축 canonical = **Invocation / Information Hierarchy / Steering / Pruning**, root virtue = **Predictability**(같은 *출력*이 아니라 같은 *과정*).
> 절차: Step 1-2 결정론 스크립트 전수(`_internal/skill_design_audit/scan.sh`) + Step 0·3-6 in-session 연구팀 5-그룹 병렬 판정 + 메인 spot-verify. 상세 근거(file:line) = T2 [`skill_design_audit_per_skill.md`](skill_design_audit_per_skill.md).
> **범위 한정**: 본 run은 **진단 전용**(read-only) — `skills/`·`core/`·`CLAUDE.md` 무수정. mode-code의 "CLAUDE.md 갱신"·"lab 사전 자료 4종" 단계는 이 scoped audit run에 **해당 없음(skip)** — 수정은 다운스트림(autopilot-spec → autopilot-code refactor) 소관.

---

## 0. Executive — verdict 분포

**28스킬 × 5 판정 항목**(Step0 + 4축) verdict 분포:

| 항목 | 🟢 정합 | 🟡 minor gap | 🔴 material gap |
|---|---|---|---|
| **Step 0 · Predictability** | **28** | 0 | 0 |
| **① Invocation** | 0 | 23 | 5† |
| **② Information Hierarchy** | 18 | 9 | 1 |
| **③ Steering** | 19 | 9 | 0 |
| **④ Pruning** | 3 | 24 | 1 |

† Invocation 🔴×5 = 연구팀 그룹 C(code-* subs)의 dissent 판정. 종합에서는 동일 근거로 그룹 D/E가 🟡로 판정한 순수 sub-skill과 **severity harmonize → per-skill 🟡**로 정규화하되, aggregate 영향(순수 sub-skill 13개 × resident description)을 Step 7 상위로 승격(§4 P1). harmonize 후: Invocation 🟡×28.

**한 줄 결론**: 하네스는 **Predictability(같은 과정 재현)를 전 스킬에서 🟢 달성** — 불변식·stage 계약·checkable completion이 촘촘하다. classic failure 중 **no-op·sediment·premature-completion·variance-bug는 0건**. 실질 gap은 두 갈래로 수렴 — (a) **Invocation 축 systemic**(전 스킬 model-invoked·"Use when" trigger 부재 + 순수 sub-skill 13개 오분류), (b) **Pruning 축 중복**(Required Reads↔Reference Map 이중 서술 + cross-skill SoT 물리 복제). 구조 도입이 아니라 **정합성 튜닝** 단계다.

---

## 1. Step 1-2 결정론 스캔 결과 (정량 규범)

전수 스크립트(`_internal/skill_design_audit/scan.sh` → `scan_raw.tsv`) 결과:

| 정량 규범 | 기준 | 결과 |
|---|---|---|
| **SKILL.md body <500줄** | Anthropic best-practices | **28/28 통과** (최장: autopilot-design 315 · draft-refine 278 · autopilot-ship 241 · design-tokens 212) |
| **references/ 1-depth** | Anthropic best-practices | **위반 0** — references/ 보유 13스킬 전부 1-depth, 2-depth 중첩 없음 |
| **invocation type** | model / user | **28/28 model-invoked** — `disable-model-invocation: true` **0건** |
| **description "Use when…" 트리거** | model-invoked 요건 | **0/28** — 전부 한국어 blurb, 영문 "Use when" 트리거 부재 |
| **description 3인칭 영문** | soft 규범 | 전부 한국어 blurb(트리거 신뢰도 우선 — 02_standards §3상 soft) |

**해석**: 기계적 정량 규범(줄 수·depth)은 **완전 통과** — 라우터 SKILL.md는 이미 lean하고 progressive disclosure를 지킨다. 반면 **invocation frontmatter는 전 스킬 동일 패턴**(model-invoked + Korean blurb + no trigger)으로, 이것이 Invocation 축 systemic gap의 근원. references/ 없는 inline-only 스킬(15개) 중 장문(autopilot-design/draft-refine/autopilot-ship/design-tokens/autopilot-apply)만 sprawl 후보로 Step 3에서 판정.

---

## 2. 28행 × 4축 매트릭스

| # | 스킬 | 그룹 | 줄수 | Step0 | ①Inv | ②IH | ③Steer | ④Prune | flags |
|---|---|---|---|---|---|---|---|---|---|
| 1 | analyze-project | A entry | 88 | 🟢 | 🟡 | 🟢 | 🟡 | 🟡 | duplication |
| 2 | analyze-user | A entry | 98 | 🟢 | 🟡 | 🟢 | 🟡 | 🟡 | duplication, negation |
| 3 | audit | A entry | 115 | 🟢 | 🟡 | 🟢 | 🟢 | 🟡 | duplication |
| 4 | autopilot-code | A entry | 75 | 🟢 | 🟡 | 🟢 | 🟢 | 🟡 | duplication |
| 5 | autopilot-draft | A entry | 127 | 🟢 | 🟡 | 🟢 | 🟢 | 🟡 | duplication |
| 6 | autopilot-research | A entry | 127 | 🟢 | 🟡 | 🟢 | 🟢 | 🟡 | duplication |
| 7 | autopilot-spec | A entry | 103 | 🟢 | 🟡 | 🟢 | 🟢 | 🟡 | duplication |
| 8 | autopilot-apply | B pipe | 190 | 🟢 | 🟡 | 🟡 | 🟢 | 🟡 | duplication, sprawl |
| 9 | **autopilot-design** | B pipe | **315** | 🟢 | 🟡 | **🔴** | 🟢 | **🔴** | sprawl, duplication |
| 10 | autopilot-lab | B pipe | 204 | 🟢 | 🟡 | 🟢 | 🟢 | 🟡 | duplication |
| 11 | autopilot-note | B pipe | 85 | 🟢 | 🟡 | 🟢 | 🟢 | 🟡 | duplication |
| 12 | autopilot-refine | B pipe | 127 | 🟢 | 🟡 | 🟢 | 🟢 | 🟡 | duplication |
| 13 | autopilot-ship | B pipe | 241 | 🟢 | 🟡 | 🟡 | 🟢 | 🟡 | duplication, sprawl |
| 14 | code-execute | C sub | 142 | 🟢 | 🟡‡ | 🟡 | 🟡 | 🟡 | duplication, negation |
| 15 | code-plan | C sub | 89 | 🟢 | 🟡‡ | 🟢 | 🟡 | 🟢 | negation |
| 16 | code-refine | C sub | 61 | 🟢 | 🟡‡ | 🟢 | 🟡 | 🟡 | duplication, negation |
| 17 | code-report | C sub | 145 | 🟢 | 🟡‡ | 🟡 | 🟡 | 🟡 | duplication, negation |
| 18 | code-test | C sub | 93 | 🟢 | 🟡‡ | 🟢 | 🟡 | 🟡 | duplication, negation |
| 19 | design-components | D sub | 164 | 🟢 | 🟡 | 🟡 | 🟡 | 🟡 | duplication, sprawl, negation |
| 20 | design-handoff | D sub | 182 | 🟢 | 🟡 | 🟡 | 🟢 | 🟡 | duplication, sprawl |
| 21 | design-init | D sub | 132 | 🟢 | 🟡 | 🟢 | 🟢 | 🟢 | none |
| 22 | design-refs | D sub | 124 | 🟢 | 🟡 | 🟢 | 🟢 | 🟢 | none |
| 23 | design-review | D sub | 137 | 🟢 | 🟡 | 🟡 | 🟢 | 🟡 | duplication |
| 24 | design-tokens | D sub | 212 | 🟢 | 🟡 | 🟡 | 🟢 | 🟡 | sprawl, duplication |
| 25 | draft-refine | E | 278 | 🟢 | 🟡 | 🟡 | 🟡 | 🟡 | sprawl, negation, duplication |
| 26 | draft-strategy | E | 64 | 🟢 | 🟡 | 🟢 | 🟢 | 🟡 | duplication |
| 27 | post-it | E | 58 | 🟢 | 🟡 | 🟢 | 🟢 | 🟡 | duplication |
| 28 | sync-skills | E | 88 | 🟢 | 🟡 | 🟢 | 🟢 | 🟡 | duplication |

‡ code-* 5개: 연구팀 그룹 C는 Invocation 🔴(user-invoked 강권)로 판정 — 표에는 harmonized 🟡, dissent는 §0 각주 †와 동일 건이며 §4 P1에 승격 반영.

---

## 3. Failure-mode 요약 (Step 3-6)

canonical 6종 + variance-bug(IH 별도 7번째) 전수 flag 집계:

| failure-mode | 소속 축 | 건수 | 해당 스킬 | 성격 |
|---|---|---|---|---|
| **duplication** | Pruning | **25** | 거의 전 스킬 | **두 하위 패턴**으로 분리 — (a) within-skill Required Reads↔Reference Map 이중 서술(~13 라우터, cosmetic) (b) **cross-skill SoT 복제**(Plan Resolution 5× 물리 복제, 시각검증 loop 동형 3중, Language Rule, `<artifact-root>` 스니펫 — 실 SoT 위반) |
| **sprawl** | Info Hierarchy | 7 | autopilot-design, draft-refine, autopilot-ship, design-tokens, autopilot-apply, design-components, design-handoff | references/ 없는 장문 inline. autopilot-design(315·3중 phase)만 🔴, 나머지 🟡 |
| **negation** | Steering | 8 | analyze-user, code-execute/plan/refine/report/test, design-components, draft-refine | **대부분 load-bearing safety invariant**(read-only·canonical 불가침·날조 금지) — 정당, flip 여지는 소수 |
| **no-op** | Pruning | **0** | — | 무동작 문장 없음 |
| **sediment** | Pruning | **0** | — | 낡은·비활성 문장 없음 |
| **premature-completion** | Steering | **0** | — | completion criterion 전부 checkable, post-completion steps가 실제 context 경계(subagent/user hand-off) 뒤 |
| **variance-bug** | Info Hierarchy | **0** | — | must-have 자료가 약한 pointer 뒤에 놓인 사례 없음 — 포인터가 일관되게 파일명+시점+의무 명시 |

**핵심 읽기**:
- **duplication이 유일한 광범위 failure(25/28)** 지만, 위험한 건 (b) cross-skill SoT 복제뿐. 대표: `code-*` 5개의 **Plan Resolution 블록** — 헤더 자체가 `## Plan Resolution (canonical — keep in sync with code-execute, code-test, code-report, code-refine, autopilot-code)` 로, "canonical"을 표방하며 **5개 파일에 물리 복제**된 SoT 위반 자백. 시각검증 loop도 design-components/review/tokens 3중 verbatim.
- **within-skill Required Reads↔Reference Map 이중 서술**은 라우터 컨벤션 자체의 산물(~13개 동형) — cosmetic·family-level 단일 결정으로 일괄 해소 가능.
- **negation은 실질 non-issue** — 8건 중 대다수가 안전 guardrail. rubric상 flag되나 재작성 대상은 소수(예: "바퀴 재발명 금지" → positive).
- **0건 4종(no-op/sediment/premature/variance)은 하네스의 진짜 강점** — Pocock rubric이 겨냥하는 attention-budget 낭비의 주요 원천이 이미 부재.

---

## 4. Step 7 — impact × 수정비용 우선순위 (개선 spec 입력)

high-impact(auto-activation·SoT 위반)를 상위, 문구 다듬기를 하위로 정렬:

| # | 개선 항목 | impact | 수정비용 | 축 | 근거 |
|---|---|---|---|---|---|
| **P1** | **순수 sub-skill 13개 invocation 재분류** (code-* 5 + design-* 6 + draft-refine + draft-strategy → `disable-model-invocation`) | **높음**(×13 resident description ≈ context budget aggregate; "worst of both worlds" — 비용 지불+auto-activation 불가) | **낮음**(frontmatter 1줄) — 단 **파이프의 slash/explicit-invoke 경로 생존을 먼저 검증**(headless `claude -p "/code-execute"`·parent Skill 명시 호출이 disable flag 하에 동작하는지) | ① | 그룹 C dissent + 그룹 D/E 동일 근거. runtime-currentness gate상 flip 전 검증 의무. |
| **P2** | **cross-skill SoT 복제 통합** (Plan Resolution 5× → autopilot-code 또는 공유 reference 단일 authority + pointer; 시각검증 loop 3× → 공유 ref; Language Rule·`<artifact-root>` 스니펫) | **높음**(유지비 + 의미 서열 과대평가) | **중간**(1 authority 지정 + 나머지 pointer화) | ④ | Plan Resolution 헤더 "keep in sync" = 복제 자백. `code-*/SKILL.md:14` 등. |
| **P3** | **autopilot-design de-sprawl** (Phase 0-5 Execution 본문 + 하네스 표 + 시각검증 loop → references/ 추출; phase 목록은 stage-worker 표로 이미 완결) | **높음**(28개 중 최장 315줄·유일 double-🔴, attention 희석) | **중-높음**(references/ 신설 + 3중 서술 정리) | ②④ | 3중 phase 문서화 확인(:114/:127/:183-271). |
| **P4** | **entry-router "Use when…" 트리거 보강** (autopilot-*·analyze-*·audit description에 영문 트리거 첫 문장) | **중간**(soft 규범 — hook-routing 보완, auto-activation ~50% 상한) | **낮음**(description 1줄) | ① | 02_standards §3: wording 단독 불신, hook 보강 전제 soft. entry는 auto-routing 의존 최고. |
| **P5** | **Required Reads↔Reference Map 이중 서술 통합** (~13 라우터 family-level 컨벤션 결정 → 단일 reference index) | **중-낮음**(cosmetic, 高빈도) | **낮음**(두 절 병합, 컨벤션 1회 결정) | ④ | 라우터 동형 패턴. `analyze-project/SKILL.md:76-88` 등. |
| **P6** | **장문 inline → references/ 추출** (draft-refine 278·autopilot-ship 241·design-tokens 212·autopilot-apply 190의 worked example/delegate prompt/템플릿) | **중간**(sprawl 완화) | **중간**(스킬별 references/ 신설) | ② | design-tokens `:41-110` 70줄 exemplar, draft-refine `:60-207` delegate prompt 등. |
| **P7** | **post-it invocation wording 정합** (`:14` "호출할 때만 변경"을 실제 model-invoked+proactive-nudge와 일치 — 문구 완화 or disable flag) | 낮음 | 낮음 | ① | 확인된 계약 wording↔frontmatter 불일치. |
| **P8** | **negation → positive 선별 재작성** (safety invariant 제외, 순수 anti-pattern 프레임만) | 낮음 | 낮음 | ③ | 8건 중 소수만 대상. 대부분 skip(guardrail). |

**정렬 원리**: P1-P3이 high-impact 핵심(invocation type·SoT·최장 sprawl) — 개선 spec의 **1차 대상**. P4-P6은 systemic이나 impact 중간(soft 규범·cosmetic·중간 sprawl). P7-P8은 마무리 튜닝. **P1은 반드시 검증-게이트 통과 후 실행**(disable flag가 파이프 dispatch를 깨지 않음을 확인 전 flip 금지).

---

## 5. 하네스 강점 (진단이 확인한 것 — 개선 spec에서 보존)

1. **Predictability 전 스킬 🟢** — 불변식 블록·stage 계약·checkable completion criterion이 표준화돼 있어, Pocock의 root virtue를 이미 구현. 개선은 이 골격을 흔들지 않는다.
2. **variance-bug·premature-completion 0건** — context pointer가 일관되게 강함(파일명+시점+의무), post-completion steps가 실제 context 경계 뒤. → IH·Steering의 위험 failure는 부재.
3. **정량 규범 완전 통과** — <500줄·1-depth 위반 0. progressive disclosure(SKILL.md router + references/ disclosure)가 이미 3-rung Information Hierarchy를 구현(06_implementation §1과 일치).
4. **no-op·sediment 0건** — attention-budget 낭비의 주 원천이 이미 관리됨. Pruning gap은 "간결성 부족"이 아니라 "중복 배치"(SoT·이중 서술)에 국한.

---

## 6. Spec 인계 (다운스트림 autopilot-spec → autopilot-code refactor)

> 06_implementation §4 권장 순서: `/audit` → `/autopilot-spec` → `/autopilot-code --mode refactor`. 본 진단이 그 spec의 입력.

**개선 청사진 구성 제안** (autopilot-spec 입력):

- **Cluster 1 · Invocation 정합** (P1+P4+P7): sub-skill invocation type 재분류 + entry-router 트리거 보강 + post-it wording. **선행 검증 필수** — disable-model-invocation 하에서 파이프 slash/explicit dispatch 생존 확인(runtime-currentness gate). 검증 실패 시 P1 범위 축소.
- **Cluster 2 · SoT 통합** (P2+P5): cross-skill 물리 복제(Plan Resolution·시각검증 loop·Language Rule)를 단일 authority+pointer로 + Required Reads/Reference Map family 컨벤션 결정. **CONVENTIONS §5 산출물 컨벤션과 정합** 필요(공유 reference 위치).
- **Cluster 3 · Sprawl 추출** (P3+P6): autopilot-design 우선(유일 double-🔴) + 장문 inline 4스킬 references/ 신설. **버전 트래킹**(autopilot-code refactor가 `plans/<date>_<slug>/`에 누적).
- **불변 보존**: §5 강점 4종(Predictability 골격·강한 pointer·정량 규범·no-op 청결)을 회귀시키지 않는다 — refactor 후 본 audit rubric 재적용(drill 회귀 후보).

**우선 실행 권장**: Cluster 2(SoT, 검증 불요·즉시 실익) → Cluster 3(sprawl) → Cluster 1(검증 게이트 통과 후). Cluster 1의 P1은 impact 최고이나 검증 의존이라 병렬 검증 트랙으로 분리.

---

## 부록 · 산출물·재현

- **T1 종합**: `.agent_reports/analysis_project/code/skill_design_audit.md` (본 파일)
- **T2 per-skill 근거**: `.agent_reports/analysis_project/code/skill_design_audit_per_skill.md` (28스킬 × 4축 file:line)
- **T3 결정론 스캔**: `_internal/skill_design_audit/scan.sh` · `scan_raw.tsv` · `RUBRIC_BRIEF.md`(판정 rubric 압축)
- **재현**: `bash .agent_reports/analysis_project/code/_internal/skill_design_audit/scan.sh skills` (Step 1-2 전수). Step 0·3-6은 RUBRIC_BRIEF.md 기준 스킬별 판정.
- **skip 근거**: mode-code의 CLAUDE.md 갱신·lab 사전 자료 4종 단계는 본 read-only audit run 범위 밖(수정은 다운스트림 소관).
