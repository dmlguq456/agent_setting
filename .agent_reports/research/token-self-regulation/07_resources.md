# 07 — Open-source Code / Tools (Tier)

> 관련: [06_implementation.md](06_implementation.md) · [04_technical_deep_dive.md](04_technical_deep_dive.md)
>
> Tier 1 = 직접 참조 가능(clone·소스 열람 완료) / Tier 2 = 참조용 / Tier 3 = 실험·학술. self-reported star·미검증 수치는 명시.

---

## Tier 1 — 직접 참조 가능 (primary, clone·열람 완료)

| repo | 계층 | language | 자기검증 문서 위치 |
|---|---|---|---|
| **JuliusBrussee/caveman** | A (output) | system-prompt skill (Markdown) | `docs/HONEST-NUMBERS.md` |
| **DietrichGebert/ponytail** | B (behavior) | system-prompt skill (Markdown) | `benchmarks/results/2026-06-17-cost-verification.md` |
| **wilpel/caveman-compression** | C (input) | Python (spaCy/RoBERTa/LLM) | `SPEC.md`, `prompts/compression.txt` |

**Quick verify (1-line each)**:

```bash
# caveman — SKILL.md 규율 + HONEST-NUMBERS 자기비판
git clone https://github.com/JuliusBrussee/caveman && sed -n '1,80p' caveman/skills/caveman/SKILL.md && sed -n '1,60p' caveman/docs/HONEST-NUMBERS.md

# ponytail — 7-rung ladder + cost-verification 벤치
git clone https://github.com/DietrichGebert/ponytail && sed -n '1,80p' ponytail/skills/ponytail/SKILL.md && sed -n '1,80p' ponytail/benchmarks/results/2026-06-17-cost-verification.md

# wilpel — SPEC 원리 + compression prompt (입력 압축, CAVEWOMAN 반증 대상)
git clone https://github.com/wilpel/caveman-compression && sed -n '1,80p' caveman-compression/SPEC.md && cat caveman-compression/prompts/compression.txt
```

**핵심 열람 포인트**:
- caveman: SKILL.md 의 drop 규칙 + invented-abbreviation 금지(tokenizer 정확성) + Auto-Clarity if-then. HONEST-NUMBERS 는 마케팅이 아닌 반증 문서.
- ponytail: SKILL.md decision ladder + "When NOT to be lazy"(safety rail). cost-verification 은 OpenAI reasoning 역전(+26~39%) 포함.
- wilpel: SPEC.md "복원 가능한 것만 제거" 원리 — 단 CAVEWOMAN 반증 대상임을 함께 읽을 것.

**Takeaway**: Tier 1 세 repo 는 소스가 직접 확인됐고, 각각 자기검증 문서를 보유한다. 특히 caveman HONEST-NUMBERS·ponytail cost-verification 은 저자 자기비판으로 신뢰도가 높다.

---

## Tier 2 — 참조용 (미검증, clone 미완)

| repo | 계층 | language | 비고 |
|---|---|---|---|
| **headroomlabs-ai/headroom** (RTK) | C | library/proxy/MCP | MCP tools: `headroom_compress/retrieve/stats`. "58.7k star" **미검증**. codepointer 반증 대상(합산 3.7%) |
| **aovestdipaperino/tokensave** | C | Rust (CodeGraph port) | 40+ tools, 80+ symbol-level MCP tool, 100% local. "60-80%" **미검증**. TokenSave 브랜드 충돌 |
| **alexgreensh/token-optimizer** | D (+C) | skill (SQLite session DB) | `/token-optimizer`(audit)·`/token-coach`(trend). 1,610 star. SkillsLLM scan 통과 |
| **open-compress/claw-compactor** | C | Python (결정론 14-stage) | `pip install claw-compactor`. AST-aware, reversible. "up to 97%" **미검증 상한** |

**Takeaway**: Tier 2 는 메커니즘 지도로 유용하나 수치가 self-reported 또는 상한값이다. headroom 은 codepointer 가 직접 반증했고, token-optimizer(D, audit)만 위험 없는 구조적 접근이라 하네스 Phase 2 참조 가치가 있다.

---

## Tier 3 — 실험·학술 (arXiv)

| paper | arXiv | 계층 | 제공하는 것 |
|---|---|---|---|
| **CAVEWOMAN** | 2606.24083 | A vs C 검증 | A/C 부호 비대칭 실측 (output 1.4-2.4x / input 순손실 ~1.15x). 입력 압축 반증의 결정적 근거 |
| **ContextBudget** | 2604.01664 | D | budget-constrained sequential decision, BACM-RL 정책. 신호=잔여 budget, 레버=압축 강도 |
| **Active Context Compression** ("Focus") | 2601.07190 | D (+C) | 자율 self-regulation, Knowledge block + prune, task당 6.0회, 22.7% overall |
| **SkillReducer** | 2603.29919 | C (skill 정의) | desc 48%·body 39% 압축, 품질 +2.8%("less is more"), progressive disclosure |

**Takeaway**: Tier 3 학술이 이 조사의 결론을 지탱한다 — CAVEWOMAN(부호 비대칭 불변식), ContextBudget(정식화 방향), SkillReducer(재주입 다이어트). 하네스 Phase 1(불변식)·Phase 3(정책)의 직접 근거.

---

## Reproducibility 매트릭스

| 발견물 | 코드 공개 | 자기검증 문서 | 독립 검증 | 종합 |
|---|:---:|:---:|:---:|---|
| caveman (JuliusBrussee) | ✓ | ✓ HONEST-NUMBERS | ✓ codepointer | **재현 가능·검증됨** |
| ponytail (DietrichGebert) | ✓ | ✓ cost-verification | 자체 벤치만 | **재현 가능** |
| wilpel/caveman-compression | ✓ | 자체 벤치만 | ✗ (CAVEWOMAN 반증) | 코드 있음, 주장 반증됨 |
| headroom / RTK | ✓ | 자체 벤치 | ✓ codepointer (부정적) | 코드 있음, 세션 효과 반증 |
| TokenSave | ✓ | ✗ | ✗ | 코드 있음, **미검증** |
| claw-compactor | ✓ | ✗ | ✗ | 코드 있음, **97% 미검증** |
| token-optimizer | ✓ (catalog) | ✗ (수치 미기재) | 부분 (security scan) | 코드 있음, 수치 미검증 |
| CAVEWOMAN | 논문 | — | 학술 | **검증 근거 자체** |
| ContextBudget | 논문 | — | 학술 | **정식화 근거** |
| Active Context Compression | 논문 | — | 학술 (신호 임계 불명확) | 학술 |
| SkillReducer | 논문 | — | 학술 | **다이어트 근거** |

**미검증 명시**: "74k star"(ponytail secondary), "58.7k star"(headroom), "up to 97%"(claw), "60-80%"(tokensave), "up to 94%"(ponytail 상한)는 모두 self-reported/secondary 이며 라이브 repo 대조가 안 됐다.

**Takeaway**: 재현성은 Tier 1(caveman·ponytail 코드+자기검증+독립검증) > Tier 3(학술) > Tier 2(코드는 있으나 수치 미검증) 순. 하네스 설계는 재현·검증된 발견물(caveman Auto-Clarity, CAVEWOMAN 부호, SkillReducer 다이어트, codepointer denominator)만 불변식 근거로 채택하고, 미검증 인기·상한 수치는 배제한다.
