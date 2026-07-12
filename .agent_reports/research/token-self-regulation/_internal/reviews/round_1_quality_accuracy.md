# Round 1 Review — QA Accuracy / No-Fabrication / Internal Consistency

**Reviewer**: 연구팀 QA (deep, ACCURACY 초점) · round 1
**대상**: `00_briefing.md` ~ `07_resources.md` (8개)
**입력 대조**: `analysis_summary.md`, `code_resources/EXCERPTS.md`, `cards/*` (22 cards), 인용된 하네스 내부 doc `../token-ceremony-audit/2026-07-07_{context-footprint,reduction-plan}.md`
**Verdict**: 🔴 0건 · 🟡 1건 — fabrication 없음. 핵심 수치 전부 카드/EXCERPTS 와 정확 일치, 파일 간 모순 없음, 미검증 수치 전부 라벨링됨.

---

## 결론 요약

Fabrication risk 사실상 zero. 지정된 핵심 수치(codepointer 3.7% / 세션 14-21% / caveman output 65%(22-87%, n=10) / ponytail 42-75%·OpenAI +26~39% 역전 / CAVEWOMAN A 1.4-2.4x vs C ~1.15x / SkillReducer desc48%·body39%·+2.8% / ContextBudget >1.6x)를 전수 대조한 결과 모두 카드·EXCERPTS·analysis_summary 와 일치하고, 반올림도 규정 범위 내이며 파일 간 표기가 통일돼 있다. 논리 비대칭(A 절감 ↔ C 순손실), 3중 gap 원인(denominator/workload/pricing), caveman 브랜드 분기(JuliusBrussee=A ↔ wilpel=C)도 8개 파일에서 모순 없이 서술된다. 유일한 지적은 02 의 Hackenberger claim 을 "합산 90%+"로 프레이밍한 경미한 왜곡(🟡).

---

## 🟡 (경미) — 1건

### 🟡-1. `02_standards.md` L13 — Hackenberger "합산 90%+" 프레이밍이 카드 사실과 어긋남
- 보고서: 광고 유형 예시로 `Hackenberger stack "합산 90%+"` 를 나열.
- 카드(`hackenberger-ultimate-stack.md`): 저자는 **per-tool 수치만** 나열 — RTK/Headroom `up to 90%(CLI output)`, TokenSave `60-80%`, Caveman `40-70%` — 그리고 카드는 명시적으로 "세 도구의 per-payload 수치를 나열하나 **세션 합산 효과는 언급 안 함**"이라고 적는다.
- 문제: 단일 도구(RTK/Headroom)의 per-payload 상한 `90%` 를 stack **"합산"**(sum) 수치로 재라벨링. 숫자 `90%` 자체는 출처에 실재하므로 fabrication 은 아니나, "합산" 프레이밍은 카드가 명시적으로 부정한 주장을 저자에게 귀속시킨다. 게다가 보고서 자신이 여러 곳(00, 02 L62, 05)에서 "stacking 은 단순 합산되지 않는다"를 반복 강조하는 것과 미묘하게 어긋난다.
- 조치 제안: `Hackenberger stack "RTK/Headroom up to 90%" 등 per-payload 나열` 로 완화하거나, "저자는 합산 수치를 명시하지 않으나 stacking 이 합쳐진다는 인상을 준다"로 정확화.
- 위치: `02_standards.md` §1 (검증 유형 4단계) 광고 예시 줄.

---

## 검증 통과 항목 (수치·논리 정합 — 이상 없음)

**핵심 수치 (전수 대조, 카드와 정확 일치·파일 간 통일)**:
- codepointer **3.7%** (rtk+headroom+caveman 합산) — 00·02·03·05 전부 동일 표기. 모집단 데이터 `500 sampled / 2,182 세션 / 13 project / 614M tok / $926.31 baseline` (02 정확, 00 은 analysis_summary 와 동일하게 $926 로 반올림 — 허용). pricing 세부 `cache_read $0.50/M · cache_create 42% · output 29%` (02) 카드 일치.
- caveman **output 65% avg (22-87%, n=10)**, 세션 **14-21%**, 재주입 **~1-1.5k input tok/turn** — 모든 파일 일치 (04·05·06 의 "~1.5k" 는 상한 shorthand, 범위 내이며 모순 아님).
- ponytail **Claude 42-75% cheaper (Haiku 63 / Sonnet 74.5 / Opus 42.3, 30 reps)**, **correctness 100% (baseline Sonnet 76%)**, OpenAI 역전 **gpt-5.4-mini +26.2%→+26%, gpt-5.5 +38.7%→+39%** — 반올림 규정 내, 00·02·03·04·05·07 표기 통일. 광고 claim `up to 94% less code / ~54% mean` 과 실측 `42-75% 비용` 을 카드처럼 지표 구분해 서술.
- CAVEWOMAN **A output 1.4-2.4x (max 3x) ↔ C input ~1.15x (worst 1.8x)**, **~절반만 correct** — 00·01·02·03·04·07 일치. 부호 비대칭이 전 파일 모순 없이 유지.
- SkillReducer **desc 48% · body 39% · +2.8% · transferability 0.965 (5 model/4 family)** — 02·03·07 일치.
- ContextBudget **>1.6x (high-complexity), BACM-RL** — 03·04·07 일치.
- Active Context Compression **22.7% (14.9M→11.5M) · max 57% · 6.0회/task** — 03·04·07 일치.
- 보조: wilpel `LLM 40-58% / NLP 15-30% / MLM 20-30% · factual 13/13`, headroom `60-95%`, tokensave `60-80%`, claw `up to 97% / 14-stage`, token-optimizer `1,610 star/128 fork` — 전부 카드 일치.

**논리 정합 (모순 없음)**:
- CAVEWOMAN 부호 비대칭(A 절감 vs C 순손실) — 00·01·04·07 에서 일관.
- 광고 vs 세션 gap 3중 원인(denominator/workload/pricing) — 00 L26·02 L30-32 카드와 일치.
- caveman 브랜드 분기(JuliusBrussee=A output ↔ wilpel=C input) — 01 lineage 섹션이 00·04 와 정합, 브랜드 공유≠메커니즘 동일 서술 일관.

**미검증 수치 라벨링 (지정 항목 전부 "미검증/self-reported" 표기됨 — 단정 없음)**:
- headroom **58.7k star** → 01·07 "미검증" ✓
- ponytail **74k star** → 01·07 "미검증(secondary)" ✓
- claw **97%** → 01·03·07 "미검증 상한" ✓
- tokensave **60-80%** → 03·07 "미검증" ✓
- ponytail **up to 94%** → 07 "상한/미검증" ✓
검증된 것처럼 단정한 사례 없음.

**하네스 내부 수치 (fabrication 아님 — 인용 doc 로 역추적 확인)**:
- 05·06 의 `always-on -8.9% (53,932→49,131 in-tok)`, `선택-로드 skill body -77% (481k→108k chars, P3)`, `P5 CLAUDE.md dedup`, `P0~P6` — analysis_summary/cards 에는 없으나 05 가 인용한 내부 doc `2026-07-07_reduction-plan.md` L79·L81·L87 에 실재(481k→108k -77%, 53,932→49,131 -8.9% post P0/P2/P5, P5 dedup, P6 deferred). 수치·P3 귀속 정확. (참고: context-footprint.md 에는 이 수치가 없고 reduction-plan.md 에 있음 — 둘 다 05 상단에 인용돼 있어 문제 없음.)

---

## 파일 간 수치 충돌 점검 결과
동일 수치가 파일마다 다르게 적힌 사례 **없음**. 반올림($926.31↔$926, +38.7↔+39, +26.2↔+26)은 전 파일이 같은 방향으로 통일 적용.
