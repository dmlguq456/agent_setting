# 01 — Technology Landscape: 4계층 메커니즘 분류

> 관련: [00_briefing.md](00_briefing.md) · [03_vendor_comparison.md](03_vendor_comparison.md) · [04_technical_deep_dive.md](04_technical_deep_dive.md)

이 생태계의 핵심 통찰은 **"token 절감"이 단일 현상이 아니라 서로 다른 표면·부호를 가진 4개 레버**라는 점이다. 이 4계층 분류 체계가 나머지 모든 보고서의 분류 기준이다.

---

## 1. Category Taxonomy — 4계층 메커니즘

| 계층 | 정의 | 대표 발견물 | 조절 대상 |
|---|---|---|---|
| **A. output-compression** | 모델이 짧게 답하게(문체) | caveman(JuliusBrussee), Hackenberger stack 의 Caveman Mode | 생성 출력 표면 |
| **B. behavior-suppression** | 얼마나 일할지/코드를 쓸지 억제 | ponytail | 작업 범위·산출물량 |
| **C. input-context-reduction** | 입력·컨텍스트·도구출력을 LLM 도달 전 압축 | wilpel/caveman-compression, headroom/RTK, tokensave, claw-compactor | 입력 페이로드 |
| **D. budget-directive-self-monitoring** | 예산·위험 신호로 스스로 조절/감사 | caveman Auto-Clarity, token-optimizer, ContextBudget, Active Context Compression | 정책·자기감사 |

**계층 간 부호 비대칭 (가장 중요)**: CAVEWOMAN(arXiv 2606.24083)이 A와 C의 부호가 반대임을 실측했다. A(output)는 1.4-2.4x 비용 절감, **C(input)는 strict lose-lose 로 순비용 ~1.15x 상승**(최악 1.8x). 즉 caveman 브랜드를 공유하는 두 프로젝트(JuliusBrussee=A, wilpel=C)가 정반대 효과를 낸다. 대부분 발견물은 복수 계층을 가진다 — caveman 은 A(주)+D(Auto-Clarity), token-optimizer 는 D(주)+C.

**Takeaway**: 4계층은 표면(출력/작업량/입력/정책)이 다르고, 특히 A와 C는 비용 부호가 반대다. "token 절감"을 하나로 묶는 순간 과대평가가 시작된다.

---

## 2. 발견물 × 계층 Matrix

각 발견물을 주 계층(●)과 보조 계층(○)으로 태깅.

| 발견물 | A output | B behavior | C input | D self-monitor | Type |
|---|:---:|:---:|:---:|:---:|---|
| **caveman** (JuliusBrussee) | ● | | | ○ | repo (skill) |
| **ponytail** (DietrichGebert) | | ● | | ○ | repo (skill) |
| **wilpel/caveman-compression** | | | ● | | repo (algo) |
| **headroom / RTK** | | | ● | | repo (proxy/MCP) |
| **TokenSave** (aovestdipaperino) | | | ● | | repo (MCP) |
| **claw-compactor** | | | ● | | repo (algo) |
| **token-optimizer** (alexgreensh) | | | ○ | ● | catalog (skill) |
| **Hackenberger Ultimate Stack** | ● | | ● | | blog (recipe) |
| **ContextBudget** (2604.01664) | | | ○ | ● | paper |
| **Active Context Compression** (2601.07190) | | | ○ | ● | paper |
| **CAVEWOMAN** (2606.24083) | ◆ | | ◆ | | paper (검증·반증) |
| **SkillReducer** (2603.29919) | | | ● | | paper (skill 정의 압축) |

◆ = 검증/반증 대상으로 A·C 를 대조. SkillReducer 는 skill 정의 자체를 압축하는 특수한 C(정적 컨텍스트) — 재주입 오버헤드 해법.

**Takeaway**: C(input) 계층에 도구가 가장 많이 몰려 있으나, 정작 CAVEWOMAN 이 반증한 계층이 바로 C다. D(self-monitoring) 계층은 학술(ContextBudget·Active Context Compression)이 주도하고 skill 생태계에는 caveman Auto-Clarity·token-optimizer 정도만 있다 — 하네스가 채울 공백.

---

## 3. Lineage — "caveman" 브랜드 분기

이 생태계에서 가장 혼동되는 지점은 **"caveman" 이름을 공유하는 두 프로젝트가 계열도 계층도 완전히 다르다**는 것이다.

```
                          "caveman" 브랜드
                                │
          ┌─────────────────────┴─────────────────────┐
          │                                            │
  JuliusBrussee/caveman                        wilpel/caveman-compression
  ─────────────────────                        ──────────────────────────
  계층 A (output-compression)                  계층 C (input-context-reduction)
  system-prompt skill (SKILL.md)               Python 알고리즘 파이프라인
  "짧게 써라"를 규율로 강제                    caveman_compress.py / _nlp.py / _mlm.py
  CAVEWOMAN: 1.4-2.4x 절감 (부호 +)            CAVEWOMAN: 순손실 ~1.15x (부호 −)
          │                                            │
          │ ponytail 저자 "pair with Caveman"         │ 저자: William Peltomäki
          │  (ponytail→caveman 직교 조합 권장)         │  (Medium writeup)
          ▼                                            ▼
  DietrichGebert/ponytail                      Peltomäki Medium
  계층 B (behavior-suppression)                "without losing meaning" ← CAVEWOMAN 반례


  ── 기타 브랜드 충돌 / mirror ──
  • "TokenSave" 브랜드 충돌:
      Hackenberger stack 의 "TokenSave" ↔ aovestdipaperino/tokensave (AST 심볼 MCP)
      — 동일 프로젝트 여부 미확정 (headroom issue #1194 에서 통합 논의)
  • token-optimizer mirror:
      alexgreensh (skillsllm 원본) ↔ majidraza1228 (skillsmp mirror)
      — 동일 skill 의 fork/mirror 추정, 카탈로그 handle 만 다름 → 병합 취급
  • caveman 랜딩 도메인:
      juliusbrussee.github.io ↔ getcaveman.dev
      — 동일/미러 여부 미확정 (마케팅 표면)
```

**핵심**: JuliusBrussee/caveman(A)과 wilpel/caveman-compression(C)은 **이름만 공유·계열 완전 다름**. 하나는 출력을 짧게 하는 프롬프트 규율, 다른 하나는 입력을 압축하는 Python 알고리즘이며, CAVEWOMAN 기준 비용 부호가 정반대다. 이 구분을 놓치면 "caveman 은 효과 있다/없다" 논쟁이 서로 다른 대상을 가리키게 된다.

**Takeaway**: caveman 논의에서는 반드시 어느 caveman(JuliusBrussee=출력 A / wilpel=입력 C)인지 명시해야 한다. 브랜드 공유가 메커니즘·부호의 동일성을 뜻하지 않는다.

---

## 4. Adoption Stage (발견물별)

| 발견물 | 단계 | 인기 지표(self-reported, **미검증**) | 비고 |
|---|---|---|---|
| caveman (JuliusBrussee) | mainstream | — | HONEST-NUMBERS 로 자기검증, 다중 런타임 이식 |
| ponytail (DietrichGebert) | mainstream | "74k star" (미검증, secondary blog 출처) | cost-verification 벤치 보유 |
| headroom / RTK | emerging | "58.7k star" (미검증) | codepointer 반증 대상 |
| wilpel/caveman-compression | emerging | — | CAVEWOMAN 반증 대상 |
| TokenSave (aovestdipaperino) | emerging | — | CodeGraph(TS)의 Rust port |
| claw-compactor | emerging | "up to 97%" (미검증 상한) | OpenClaw 전용, 결정론 |
| token-optimizer | emerging | 1,610 star / 128 fork | SkillsLLM security scan 통과 |
| ContextBudget / Active Context Compression / CAVEWOMAN / SkillReducer | 학술(research) | — | arXiv, 실험 근거 |

**미검증 표기 원칙**: star 수("74k", "58.7k"), 상한 수치("up to 97%", "up to 94%")는 self-reported 또는 secondary blog 출처이며 라이브 repo 대조가 안 됐다. 메커니즘 유효성과 인기·상한 지표는 무관하므로 하네스 설계 입력으로는 배제한다.

**Takeaway**: 생태계는 개별 skill → 통합 stack(headroom↔tokensave 임베딩, Hackenberger recipe)으로 수렴 중이나, 그 stacking 의 실효는 codepointer 가 3.7% 로 반증했다. 인기 지표는 확산 폭일 뿐 절감 효과의 증거가 아니다.
