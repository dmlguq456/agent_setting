# 05 — 하네스 적용 시 고려사항

> 관련: [04_technical_deep_dive.md](04_technical_deep_dive.md) · [06_implementation.md](06_implementation.md)
>
> 표준 "Deployment" 자리를, 이 조사의 목적(우리 하네스에 token-budget 자기조절 축 설계)에 맞춰 **하네스 적용 고려사항**으로 대체한다. 내부 참조: `../token-ceremony-audit/2026-07-07_context-footprint.md`, `2026-07-07_reduction-plan.md`.

---

## 1. 두 축의 직교성 — intensity ⊥ token-budget

우리 하네스에는 이미 **intensity 축**(CONVENTIONS §1.1)이 있다. 여기에 얹을 **token-budget 축**은 이와 직교해야 한다.

| 축 | 신호 | 방향 | 조절 대상 |
|---|---|---|---|
| **intensity 축** | 작업 난이도·stakes | **올림** (up) | 검증 rigor·모델 tier·분사 깊이 |
| **token-budget 축** | 잔여 예산·컨텍스트 압박·세션 누적 비용 | **줄임** (down) | 출력·범위·도구·압축 |

두 축은 **원칙적으로 직교**하다. 어렵고 중요한 작업(high intensity)을 예산이 빠듯한 상황(tight budget)에서 수행할 수 있다. **intensity 를 낮춰 예산을 아끼는 것은 축의 혼동**이며 품질 희생이다 — 예산이 부족하다고 검증·분사를 줄이면 안 된다.

**Takeaway**: token-budget 이 tight 하다고 intensity(검증 rigor·모델 tier)를 낮추지 않는다. 두 축은 분리된 신호·분리된 레버를 갖는다.

---

## 2. 간섭 지점 — 직교가 깨지는 자리 (ponytail 이 코드로 예시)

ponytail 은 두 축이 한 skill 에 섞여 있는 실증 사례다([04](04_technical_deep_dive.md) 테마 2):

1. **ladder rung1(necessity)은 사실 intensity 판단**: "이 작업이 필요한가/존재해야 하나"는 중요도 축에 가깝다. 이를 token-budget 레버로 오해하면 **중요한 작업을 예산 이유로 skip** 하는 오류가 난다.
2. **"shortest diff"는 token-budget 판단**: 같은 작업을 더 적은 토큰으로. 이건 순수 예산 축이다.
3. **safety rail 은 어느 축에서도 불가침**: caveman(security warning→압축 off)·ponytail(validation/security/a11y 축소 금지) 모두 명시. token-budget 이 아무리 tight 해도 **검증·안전·에러 처리는 레버 대상이 아니다**.

**하네스 조치**: rung1(필요성) 판단은 intensity/scope 판단으로, "shortest diff" 는 token-budget 레버로 **명시 분리**한다. safety 관련 항목은 두 축 모두에서 레버화 금지 불변식으로 배선한다.

**Takeaway**: 하나의 skill 이 "필요성 판단(intensity)"과 "간결화(budget)"를 섞으면 예산 이유로 중요 작업을 건너뛰는 버그가 생긴다. 하네스는 이 둘을 분리하고 safety 를 불가침으로 못박는다.

---

## 3. 레버 우선순위 (발견물에서 도출)

| 우선순위 | 레버 | 상태 | 근거 (불변식) |
|---|---|---|---|
| 1 | **A output-compression** | **우선 채택** | 안전, 세션 효과 작지만 부호 +. CAVEWOMAN 1.4-2.4x |
| 2 | **D self-monitoring/audit** | 채택 (구조적) | token-optimizer 식 정적 낭비 감사, 위험 없음 |
| 3 | **B behavior-suppression** | 조건부 (intensity 와 분리 시) | ponytail, correctness 100%지만 reasoning 비용 역전 주의 |
| — | **C input-context-reduction** | **default off** | **CAVEWOMAN 순손실 ~1.15x — 불변식** |

**신호는 세션 denominator 기준** (codepointer 교훈): per-payload % 가 아니라 세션 청구액·잔여 예산을 신호로. 압축 레버의 목표를 세션 denominator 로 환산해 평가한다.

**재주입 오버헤드 회계**: skill/규율을 추가하면 그 자체가 input 비용이다(caveman ~1.5k/turn). token-budget 축은 자기 자신의 비용도 계상해야 한다. 우리 하네스는 이미 SkillReducer 방향으로 다이어트를 수행했다 — `context-footprint.md` 기준 **always-on context -8.9%**(53,932→49,131 in-tok), **선택-로드 skill body -77%**(481k→108k chars, P3), CLAUDE.md 단일-출처 dedup(P5). 이 회계 기반 위에 런타임 레버를 얹는다.

**Takeaway**: 레버 우선순위는 A > D > B, C 는 default off(불변식). 신호는 세션 denominator, 그리고 레버 자체의 재주입 비용을 회계에 포함한다.

---

## 4. Failure Modes + Mitigation

| failure mode | 증상 | mitigation |
|---|---|---|
| **input 압축 켜서 순손실** | 저장 토큰↓지만 세션 비용↑ | C 레버 default off, 명확성 손상 없는 좁은 범위만 |
| **per-payload % 를 세션으로 오인** | "90% 절감" 기대 vs 실제 3.7% | 신호·목표를 세션 청구액 denominator 로 정의 |
| **safety 를 레버화** | 예산 tight 라고 검증·에러처리 축소 | safety rail 불가침 불변식 배선 (두 축 공통) |
| **재주입 오버헤드 무시** | skill 추가가 절감보다 큼 (terse workload net-neg) | skill 정의 다이어트(SkillReducer), 재주입 비용 계상 |
| **intensity/budget 혼동** | 예산 이유로 중요 작업 skip·검증 생략 | 두 축 분리, rung1(필요성)은 intensity 쪽 |
| **레버 stacking 단순 합산 오인** | "여러 도구 쌓으면 절감 합쳐진다" | 공통 denominator 인식, Hackenberger stack→codepointer 3.7% 반례 |
| **reasoning model 비용 역전** | always-on ruleset 이 짧은 출력보다 큼 | 모델별 회계, ponytail OpenAI +26~39% 사례 |

**Takeaway**: 7개 failure mode 는 모두 "레버를 세션 denominator·재주입 회계·safety 불변식에 못 박지 않을 때" 발생한다. 개별 mitigation 을 Phase 배정으로 넘기면 [06_implementation.md](06_implementation.md) §3 Risk Register 가 된다.

---

## 5. Cost Model

- **재주입 input 비용을 반드시 계상**: token-budget 레버(skill 규율)를 추가할 때 그 skill 의 매-turn input 비용(예: caveman ~1-1.5k tok)을 절감 목표에서 차감. normal reply <1.5-2k output tok 이면 net-negative(caveman rule of thumb).
- **pricing 구조 반영**: 압축분이 싼 cache_read 로 떨어지고 청구는 cache_create·output 이 지배(codepointer). 압축 레버가 못 건드리는 청구 항목을 목표에서 제외.
- **세션 denominator**: 목표 = 세션 청구액 감소분 / 세션 전체 청구액. per-payload % 아님.

**Takeaway**: 하네스 배포 시 핵심 고려사항은 세 가지 — (1) 두 축(intensity/budget)을 직교 분리, (2) 레버 우선순위 A>D>B·C off, (3) 세션 denominator + 재주입 회계로 목표를 정의. 이미 수행한 P0~P6 다이어트가 재주입 회계의 기반이며, 그 위에 런타임 self-regulation 을 얹는다.
