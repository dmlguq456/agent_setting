# 06 — Goal-Adaptive Action Roadmap

> 관련: [05_deployment.md](05_deployment.md) · [07_resources.md](07_resources.md)
>
> **Boundary disclaimer**: 이 06_implementation.md 는 분야 분석에서 도출된 **high-level 계획**입니다. 본격 청사진·구현은 autopilot-spec / autopilot-code 로 인계됩니다 (§ Next Pipeline).

> **Inferred goal**: 우리 하네스에 **token-budget 자기조절 축을 설계·도입**한다 → goal = **adopt(설계 채택 결정) + build(1단계 구현)** 혼합.

이 조사의 목적은 학술 서베이가 아니라 하네스 개선이다. 따라서 이 roadmap 은 "무엇을 알았나"가 아니라 "무엇을 도입할 것인가"에 초점을 둔다. 결정 지점마다 Option 과 Recommendation 을 제시한다.

---

## 1. Selection / Decision Matrix

### 결정 D1 — 신호를 어떻게 측정할 것인가

| Option | 내용 | 장단 |
|---|---|---|
| A | 잔여 context % 만 | 측정 쉬움, 하지만 세션 청구액과 괴리 (codepointer denominator gap) |
| B | 세션 누적 비용만 | 청구 정확, 하지만 실시간 노출 어려움 |
| **C (권장)** | **둘 다 — 잔여 context % + 세션 누적 in/out tok** | codepointer 교훈(세션 denominator) 반영, `context-footprint.py` 확장으로 계측 가능 |

**Recommendation: C.** 이미 `tools/context-footprint.py`(P4 guard)가 bootstrap·metadata·hook footprint 를 계측한다. 이를 런타임 세션 누적으로 확장하면 두 신호를 모두 노출할 수 있다. 근거: codepointer 의 denominator mismatch 는 단일 신호(per-payload)를 세션으로 오인해서 생긴 문제 — 두 신호를 함께 봐야 한다.

### 결정 D2 — 레버 우선순위

| Option | 내용 | 장단 |
|---|---|---|
| A | 모든 레버 동등 | Hackenberger stack 식 순진한 stacking → codepointer 3.7% 반례 |
| **B (권장)** | **A output 우선 · D audit 병행 · B 조건부 · C default off** | CAVEWOMAN 부호 비대칭 불변식 준수 |

**Recommendation: B.** output-compression(A)은 안전·부호+, input(C)은 순손실이므로 default off. 근거: CAVEWOMAN 1.4-2.4x(A) vs ~1.15x 순손실(C).

### 결정 D3 — 정적 if-then vs 예산-적응 정책

| Option | 내용 | 장단 |
|---|---|---|
| **A (권장 1단계)** | **caveman Auto-Clarity 식 if-then 을 예산축으로 확장** | 현실적, 구현 즉시, 검증 쉬움 |
| B | ContextBudget 식 RL 정책 | 정식화 최고, 하지만 학습·인프라 비용 큼 |
| C | Active Context Compression 식 prompt-driven 자율 | 중간, 하지만 임계 불명확 |

**Recommendation: A 먼저, B 는 실험(Phase 3).** RL 까지 안 가도 "예산 tight → 출력 간결·심볼 질의·분사 억제" if-then 이면 1단계로 충분. 근거: caveman Auto-Clarity 는 이미 검증된 "위험→레버 off" 패턴이며, 이를 "예산→레버 down" 으로 확장하는 게 최소 위험.

### 결정 D4 — safety 불변식 배선

| Option | 내용 | 장단 |
|---|---|---|
| A | 문서 convention 만 | 위반 감지 못 함 |
| **B (권장)** | **safety 항목을 두 축 모두에서 레버화 금지로 명시 배선** | ponytail/caveman 선례, 불변식 |

**Recommendation: B.** 검증·안전·에러 처리·security 는 token-budget·intensity 어느 축에서도 레버 대상이 아니다. 근거: ponytail "When NOT to be lazy", caveman Auto-Clarity(security→압축 off).

**Takeaway**: 4개 결정 모두 "안전·세션 denominator·직교" 쪽 Option 을 권장. 1단계는 if-then(D3-A)로 최소 위험 진입, 정식 정책(RL)은 나중 실험.

---

## 2. Phased Plan

### Phase 0 — 신호 계측·노출

- `tools/context-footprint.py`(P4)를 **런타임 세션 누적**으로 확장: 잔여 context %, 세션 in/out tok, cache_read vs cache_create 비율 노출.
- 목표를 세션 denominator 로 정의(per-payload % 금지).
- 산출: token-budget 신호가 statusline 또는 hook 으로 노출.

### Phase 1 — if-then 레버 (caveman Auto-Clarity 식)

- "예산 tight → 출력 간결·심볼 질의·분사 억제" if-then 규칙.
- **safety 불변식 배선**: 검증·안전 항목 레버화 금지.
- 레버 우선순위 A(output) 우선, C(input) off.
- 산출: budget 신호에 반응하는 최소 self-regulation.

### Phase 2 — 재주입 회계·skill 다이어트 (SkillReducer 식)

- 신규 token-budget 규율의 재주입 비용을 회계에 포함(caveman ~1.5k/turn 교훈).
- 이미 수행한 P0~P6 다이어트(always-on -8.9%, skill body -77%) 위에서 규율 정의를 progressive disclosure(essential/supplement)로 분리.
- 산출: 레버 자체가 net-negative 되지 않도록 보장.

### Phase 3 — 예산-적응 정책 실험 (ContextBudget 식)

- if-then 을 넘어 잔여 budget 을 명시 신호로 삼는 동적 정책 실험(RL 여부는 별도 판단).
- Active Context Compression 식 자율 prune 도 후보.
- 산출: 실험적 정식화, 채택은 결과 보고 후.

**Takeaway**: Phase 0(계측) → 1(if-then + safety) → 2(회계·다이어트) → 3(정책 실험). 1단계까지가 core 도입, 3단계는 실험. 각 phase 는 앞 phase 산출물 위에 쌓인다.

---

## 3. Risk Register

| risk | 영향 | mitigation | phase |
|---|---|---|---|
| input 압축 켜서 순손실 | 세션 비용↑ | C default off 불변식 | 1 |
| 재주입이 절감 초과 | net-negative | 회계 포함, terse workload 감지 | 2 |
| intensity/budget 혼동 | 중요 작업 skip | 두 축 분리, rung1=intensity | 1 |
| safety 레버화 | 검증·안전 훼손 | 불변식 배선 | 1 |
| per-payload 오인 | 목표 과대설정 | 세션 denominator | 0 |
| RL 인프라 과투자 | 비용 초과 | if-then 우선, RL 은 실험만 | 3 |

**Takeaway**: [05_deployment.md](05_deployment.md) §4 의 failure mode 를 phase 로 배정한 것 — 위험의 절반은 Phase 0-1(계측·직교·safety)에서, 나머지는 Phase 2-3(회계·정책)에서 차단된다.

---

## 4. Paper-to-Mechanism Mapping

| 발견물 | 제공하는 것 | 하네스 phase |
|---|---|---|
| caveman Auto-Clarity | if-then "신호→레버 off" 패턴 | Phase 1 |
| CAVEWOMAN (2606.24083) | A/C 부호 비대칭 불변식 | Phase 1 (레버 우선순위) |
| codepointer | 세션 denominator 신호 규율 | Phase 0 |
| ponytail | safety rail 불가침 + 축 분리 | Phase 1 |
| SkillReducer (2603.29919) | 재주입 다이어트(progressive disclosure) | Phase 2 |
| ContextBudget (2604.01664) | 예산-적응 정책 정식화 | Phase 3 |
| Active Context Compression (2601.07190) | 자율 prune 대안 | Phase 3 |
| token-optimizer | 구조적 낭비 audit 레버 | Phase 2 (D 축) |

**Takeaway**: 각 발견물이 하나의 phase 조각을 제공한다 — 이 조사의 8개 핵심 소스가 로드맵의 근거로 1:1 대응되며, 새로 만들 규율이 아니라 검증된 패턴의 이식임을 보인다.

---

## Next Pipeline

이 06 은 high-level sketch 이며, 실제 청사진은 autopilot-spec 이 prd.md 로 만든다. research 산출물은 자동 인지된다. copy-paste-ready 커맨드:

```
/autopilot-spec "token-budget 자기조절 축 (intensity 직교, output-compression 우선·input default off, safety 불가침, 세션 denominator 신호, 재주입 오버헤드 회계)"
```

**hand-off rationale**: 위 4개 결정(D1~D4)과 Phased Plan 은 방향 결정이고, autopilot-spec 이 이를 prd.md·acceptance criteria·구체 배선으로 청사진화한다. 그 다음 autopilot-code 가 plans/ 로 구현한다.

**Takeaway**: 도입은 adopt(D1~D4 방향 결정 완료) + build(Phase 0-1 우선). 다음 단계는 autopilot-spec 인계 — 이 문서는 지도이지 청사진이 아니다.
