# 03 — 발견물 비교 매트릭스

> 관련: [01_landscape.md](01_landscape.md) · [02_standards.md](02_standards.md) · [04_technical_deep_dive.md](04_technical_deep_dive.md)
>
> 모든 수치는 카드/analysis_summary 출처만 사용. 미검증 수치는 명시.

---

## 1. 핵심 매트릭스

| 도구 | 계층 | 절감 claim (광고) | 실측치 | 재주입 오버헤드 | 품질 영향 | 검증 신뢰도 |
|---|---|---|---|---|---|---|
| **caveman** (JuliusBrussee) | A (+D) | output 65% avg (22-87%, n=10) | 세션 14-21% (output-heavy), terse **net-negative** | ~1-1.5k input tok/turn | 소비자-의존 (사람↔에이전트) | **높음** (HONEST-NUMBERS + codepointer) |
| **ponytail** (DietrichGebert) | B (+D) | up to 94% less code, ~54% mean | Claude 비용 42-75% cheaper, **OpenAI reasoning +26~39% 역전** | always-on ruleset (reasoning model 에서 큼) | correctness 100% (baseline Sonnet 76% over-eng) | **높음** (자체 벤치) |
| **wilpel/caveman-compression** | C | LLM 40-58%, NLP 15-30%, MLM 20-30% | **CAVEWOMAN 반증: 순손실 ~1.15x** | 압축 자체 비용(LLM 모드 ~2s/req) | factual 13/13 주장 vs **~절반만 정확** | 낮음 (반증됨) |
| **headroom / RTK** | C | 60-95% fewer tokens | **codepointer 합산 3.7%** (rtk+headroom+caveman) | proxy/MCP round-trip | GSM8K delta ~0 (벤치상) | 낮음 (workload mismatch) |
| **TokenSave** (aovestdipaperino) | C | 구조 discovery 60-80% | 미검증 | MCP tool 호출 | (심볼 질의, 파일 dump 회피) | 미검증 |
| **claw-compactor** | C | up to 97% | 미검증 (per-payload 상한 추정) | 결정론 파이프라인 (no-LLM) | reversible (복원 보장) | 미검증 |
| **token-optimizer** (alexgreensh) | D (+C) | "measured savings", cache-safe | 수치 미기재 | audit skill 자체 비용 | 정적 낭비 진단 | 부분 (security scan) |
| **ContextBudget** (2604.01664) | D | >1.6x gain (high-complexity) | 논문 실험 (budget↓일수록 우위↑) | RL 정책 (학습 필요) | 성능 유지·향상 | **높음** (학술) |
| **Active Context Compression** (2601.07190) | D (+C) | 22.7% overall, 최대 57% | 논문 실험 (task당 6.0회 자율) | prompt-driven (임계 불명확) | 정확도 유지 (3/5 동일) | 중간 (학술) |
| **CAVEWOMAN** (2606.24083) | A vs C | (검증) output 1.4-2.4x / input 순손실 | — | — | input 압축 ~절반만 정확 | **높음** (반증 근거) |
| **SkillReducer** (2603.29919) | C (skill 정의) | desc 48%·body 39% 압축 | 논문 실험 (600 skills) | **재주입 비용 자체를 줄임** | **품질 +2.8%** ("less is more") | **높음** (학술) |

**Takeaway**: 광고 claim(60-97%)과 실측치(3.7-21%, 또는 순손실) 사이 gap 이 계층별로 다르다. A(caveman)는 output-heavy 에서만 세션 14-21%, C(wilpel/headroom)는 순손실 또는 3.7%. 재주입 오버헤드는 어느 skill 이든 존재하며 reasoning model 에서 절감을 역전시킬 수 있다.

---

## 2. Self-Regulation 내장 여부 (Capability Checklist)

| 도구 | self-regulation 내장? | 신호 | 레버 | 정책화 수준 |
|---|:---:|---|---|---|
| caveman Auto-Clarity | ✓ | 위험·모호·multi-step | 출력 압축 강도 off | 정적 rule (if-then) |
| ponytail | ✓ | 작업 필요성·복잡도 | 작업 범위 축소·되묻기 | 정적 ladder (reflex) |
| token-optimizer | ✓ | 낭비 audit(bloated config·stale memory·misrouting) | config/memory/routing 정리 | audit rule |
| ContextBudget | ✓ | **잔여 context budget** | history 압축 시점·정도 | **RL 정책 (가장 정식화)** |
| Active Context Compression | ✓ (자율) | 컨텍스트 누적 (prompt-driven) | history prune + Knowledge block | prompt-driven 자율 |
| wilpel / headroom / TokenSave / claw-compactor | ✗ | — (정적, 사용자 선택) | 입력/도구출력 압축률 | 없음 (정적) |
| SkillReducer | ✗ | — (설계-시 정적) | skill 정의 압축 | 없음 (offline) |

**Takeaway**: self-regulation 은 caveman(A)·ponytail(B)·token-optimizer(D)의 얕은 정적 rule 부터 ContextBudget(D)의 RL 정책까지 스펙트럼을 이룬다. C 계층 순수 압축 도구(wilpel/headroom/claw)는 대부분 신호 없이 항상 on 이라 CAVEWOMAN 이 반증한 순손실 위험을 그대로 진다.

---

## 3. 상황별 레버 추천

| Workload / 상황 | 추천 레버 | 근거 |
|---|---|---|
| output-heavy **agent-to-agent** 통신 | **A (caveman)** 권장 | 세션 14-21% 절감, 소비자가 에이전트라 문체 손실 무해 |
| terse / **human-facing** 산출물 | A **비권장** (net-negative) | 짧은 응답은 skill 재주입(~1.5k)이 절감을 초과, 사람은 압축 문체 가독성↓ |
| 과도한 코드/scope 억제 필요 | **B (ponytail)** | correctness 100%, over-engineering 방지. 단 reasoning model 비용 역전 주의 |
| 큰 도구출력/로그 처리 | C (headroom) — **제한적** | code-search 류만 잘 압축, 세션 비중 작음(codepointer) |
| 입력/프롬프트 압축 | **C 비권장 (default off)** | CAVEWOMAN 순손실 ~1.15x, 의미 divergence |
| 구조적 낭비(config·memory·routing) | **D (token-optimizer 식 audit)** | 런타임 압축 아닌 정적 최적화, 위험 없음 |
| 예산-적응 동적 조절 | **D (ContextBudget 식 정책)** | 잔여 budget 신호로 레버 동적화, budget tight 일수록 우위↑ |

**Takeaway**: 상황별 최적 레버가 다르며 부호도 다르다. output-heavy agent-to-agent 에는 A, 과도 작업 억제엔 B, 구조적 낭비엔 D(audit) 가 안전하다. input 압축(C)은 순손실 위험으로 default off 가 원칙이다. 여러 레버 stacking 은 공통 세션 denominator 를 나눠 갖기에 단순 합산되지 않는다.
