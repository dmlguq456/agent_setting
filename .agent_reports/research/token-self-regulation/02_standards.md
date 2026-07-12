# 02 — 측정·검증 방법론 (절감을 어떻게 주장·검증했나)

> 관련: [01_landscape.md](01_landscape.md) · [03_vendor_comparison.md](03_vendor_comparison.md)
>
> 표준 technology 템플릿의 "Standards & Specs" 자리를, 이 주제에 맞춰 **"절감 수치를 어떻게 측정·검증했는가"의 방법론 인벤토리**로 대체한다. 이 생태계에는 공식 표준이 없고, 대신 각 발견물이 절감을 주장·측정한 방식의 신뢰도 계층이 핵심 축이다.

---

## 1. 검증 유형 4단계

절감 수치는 출처에 따라 신뢰도가 다르다. 낮은 쪽부터:

1. **광고 (마케팅 landing)** — 헤드라인 %만 노출, 세션 gap 무비판. 예: caveman 랜딩 "65%", Hackenberger stack "RTK/Headroom up to 90%" 등 per-tool 나열(합산 수치는 저자가 명시하지 않으나 stacking 이 합쳐진다는 인상), claw-compactor "up to 97%".
2. **저자 자기검증 (self-critique)** — 저자가 자기 도구의 한계를 문서로 반증. 예: caveman `docs/HONEST-NUMBERS.md`, ponytail `benchmarks/results/2026-06-17-cost-verification.md`.
3. **독립 replay** — 제3자가 실사용 세션을 재현. 예: codepointer 500 세션 replay.
4. **학술 반증 (peer-style)** — 통제된 benchmark 로 방향 자체를 검증. 예: CAVEWOMAN, SkillReducer, ContextBudget.

**핵심**: 신뢰도가 다른 이 네 유형이 **모두 같은 방향**(세션 효과는 광고보다 훨씬 작고, 입력 압축은 순손실 가능)으로 수렴한다 → 결론이 강건하다.

---

## 2. 검증 방법론 상세

### (a) codepointer 독립 replay — 가장 강한 실증 반증

- **데이터**: 500 sampled 실 Claude Code 세션 (모집단 2,182 세션·13 project·614M tok·$926.31 baseline).
- **방법**: turn-by-turn counterfactual replay — 각 turn 에 rtk+headroom+caveman 을 적용했을 때의 절감을 재계산.
- **결과**: 합산 실절감 **3.7%** (광고 60-90% 대비).
- **3중 gap 규명**:
  1. **denominator mismatch** — 광고 %는 per-payload(압축 대상 페이로드 한정), 실제 청구는 세션 전체이며 다른 비용이 지배.
  2. **workload mismatch** — 도구는 synthetic/repetitive 데이터에서 가장 잘 압축되는데, 실 트래픽에서 그 비중은 작음.
  3. **pricing structure** — 압축된 토큰은 싼 cache_read($0.50/M)로 떨어지는데, 청구는 cache_create(42%)·output(29%)이 지배하고 이들은 압축 도구가 못 건드림.

### (b) CAVEWOMAN (arXiv 2606.24083) — 학술 방향 검증

- **방법**: 5-benchmark, output 압축 vs input 압축을 통제 비교(length-control 포함).
- **결과**: output 압축 **1.4-2.4x**(최대 3x) 비용 절감 / input 압축 **순손실 ~1.15x**(최악 데이터셋 1.8x).
- **품질**: 비추론 모델에서 input-압축 생성물의 ~절반만 기술적으로 정확하고, 나머지는 baseline 과의 의미 괴리가 length-control 후에도 잔존.
- **의의**: "caveman style" 압축을 학명으로 직접 명명해 A/C 부호 비대칭을 실측. wilpel 계열의 "without losing meaning" 명제에 대한 결정적 반례.

### (c) SkillReducer (arXiv 2603.29919) — skill 정의 압축 검증

- **데이터**: 600 skills + SkillsBench.
- **결과**: skill description **48%** mean 압축, body **39%** 압축. 압축 후 기능 품질 **+2.8%**("less is more"), transferability 0.965 retention(5 model, 4 family).
- **의의**: caveman HONEST-NUMBERS 가 지적한 "skill 이 매 turn ~1-1.5k input 추가" 문제의 정면 해법. 압축이 비용뿐 아니라 품질도 개선(비필수 내용이 컨텍스트를 산만하게 만들기 때문).

### (d) 저자 자기검증

- **caveman HONEST-NUMBERS**: output 65% avg(22-87%, n=10)는 output-only, session-level 14-21%(output-heavy)·terse net-negative, skill 이 ~1-1.5k input tok/turn 추가. "Wanting the rock to work does not make the rock work."
- **ponytail cost-verification**: Claude 42-75% cheaper(Haiku 63/Sonnet 74.5/Opus 42.3, 30 reps), correctness 100%. **OpenAI reasoning model 에서 역전** — gpt-5.4-mini +26%, gpt-5.5 +39% more expensive.

---

## 3. 발견물별 검증 인벤토리

| 발견물 | 검증 유형 | 방법 | 결과 | 신뢰도 |
|---|---|---|---|---|
| caveman (JuliusBrussee) | 자기검증 + 독립replay | HONEST-NUMBERS + codepointer | output 65% → session 14-21%, terse net-neg | **높음** (자기비판) |
| ponytail (DietrichGebert) | 자기검증 | cost-verification 벤치(30 reps) | Claude 42-75% cheaper, OpenAI 역전, correctness 100% | **높음** |
| wilpel/caveman-compression | 자기 benchmark만 | 저자 측정 40-58% LLM | factual 13/13 주장 → **CAVEWOMAN 반증** | 낮음 (반증됨) |
| headroom / RTK | 자기 benchmark + 독립replay | GSM8K delta~0 → codepointer 3.7% | 벤치 정확성 ≠ 세션 절감 | 낮음 (반증됨) |
| Hackenberger stack | 광고 | recipe 나열 | 세션 합산 무비판 → codepointer 반증 | **최저** (광고) |
| TokenSave / claw-compactor | 미검증 | self-reported 60-80% / up-to 97% | 독립 검증 없음 | 미검증 |
| token-optimizer | 카탈로그(security scan) | audit 접근, 절감 수치 미기재 | SkillsLLM scan 통과 | 부분 |
| CAVEWOMAN | 학술 | 5-benchmark, length-control | output +, input − (순손실) | **높음** |
| SkillReducer | 학술 | 600 skills + SkillsBench | desc 48%·body 39%, 품질 +2.8% | **높음** |
| ContextBudget | 학술 | BACM-RL curriculum | >1.6x gain (high-complexity) | **높음** |
| Active Context Compression | 학술 | Focus 시스템 실험 | 22.7% overall, 정확도 유지 | 중간 (신호 임계 불명확) |

**Takeaway**: 검증 신뢰도 계층은 **저자 자기비판 > 독립 replay > 학술 반증** 순이지만, 결정적인 건 이 셋이 **같은 방향으로 수렴**한다는 점이다 — 세션 효과는 광고보다 훨씬 작고, input 압축은 순손실 가능. 반대로 광고·미검증 수치(star 수, up-to % 상한)는 방향을 뒤집는 증거가 되지 못한다. 하네스는 절감 목표를 반드시 세션 denominator·실제 pricing 구조로 환산해 평가해야 한다.
