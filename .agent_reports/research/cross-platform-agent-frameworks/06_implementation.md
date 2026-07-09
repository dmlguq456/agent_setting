# 06 — Goal-Adaptive Action Roadmap

> **Inferred goal: adopt** — 이 조사는 새 소프트웨어를 처음부터 만드는 것이 아니라, 다른 프레임워크의 drift-prevention 패턴 중 *어느 것을 이 repo 자신의 `core/`→`adapters/*`→`.agent_reports` 구조에 차용할지* 를 정하는 **기술 채택/선정 결정**이다. 아래는 "adopt" 템플릿을 따른다.

## 1. Selection Criteria Matrix (이 repo 실제 제약에 가중)

우리 harness 의 명시된 핵심 난점("core > adapter > project 3-layer 가 계속 sync 를 벗어난다")에 맞춰 4개 기준을 가중.

| 기준 | 가중치 | 근거 |
|---|---|---|
| **drift-prevention robustness** | ★★★ (0.40) | 명시된 핵심 난점 — 양방향 divergence 처리력 |
| **기존 `core/`→`adapters/*`→`.agent_reports` 형상 적합** | ★★★ (0.30) | 새 아키텍처 도입 아닌 증분이어야 함 ([05_deployment](05_deployment.md) §2) |
| **구현 비용** | ★★ (0.20) | installer/converter 층 개조 규모 |
| **유지 부담** | ★ (0.10) | N-runtime 확장 시 한계비용 |

## 2. 후보 목록 (장점/단점)

### 후보 1 — GSD-style hash-manifest + patch-reapply (adapter 파일 대상) ★ 최우선
- **무엇**: `core/`→`adapters/*` 재생성 시 파일 hash 를 manifest 에 기록 → 사용자가 adapter 파일 직접 수정하면 불일치 감지 → local-patch 로 분리 → 새 버전에 reapply (`gsd.md` §2, [04_technical_deep_dive](04_technical_deep_dive.md) §a).
- **장점**: 조사 대상 중 **유일하게 양방향 divergence(3-way merge) 실구현**; 우리 핵심 난점 정면 대응; 기존 converter 층에 증분.
- **단점**: installer file-ops 복잡도↑; GSD 카드도 line 단위는 일부만 검증 — 이식 전 GSD `bin/install.js` 실코드 재확인 필요.
- **적합도**: 최고 (robustness 0.40 만점, 형상 적합 高).

### 후보 2 — spec-kit-style registry + placeholder projection (adapter 생성)
- **무엇**: `INTEGRATION_REGISTRY` 처럼 adapter 메타데이터를 단일 registry SoT 로 두고 placeholder 치환으로 표면 생성 (`spec-kit.md` §1).
- **장점**: 새 runtime 추가가 registry 등록 4단계로 단순; core 수정이 전 adapter 전파.
- **단점**: 로컬 수정 자체는 감지 못 함(계층 resolution 으로 우회) → 후보 1 을 대체하지 못하고 보완 관계.
- **적합도**: 중 — 우리가 이미 유사 converter 를 가졌다면 한계효용 낮음.

### 후보 3 — Claude 공식 version/SHA-pin (skill/agent 파일 소비 시)
- **무엇**: 외부 skill/agent 를 소비할 때 fork 대신 marketplace source + `ref`+`sha` pin + `renames` 마이그레이션 (`claude-code-official-plugins.md` §6).
- **장점**: 소비-only 시나리오 최적, 저비용; rename 흡수.
- **단점**: **우리가 만든** core→adapter 내부 sync 엔 부적용(양방향 divergence 3-way merge 부재, 공식도 자인). 외부 컴포넌트 소비 경로에만 국한.
- **적합도**: 중 (범위 한정 — 내부 drift 문제엔 답 안 됨).

### 보조 후보 — override-layer 승격 + byte-budget CI + parity-loss warning
- override-layer 물리 분리(spec-kit/BMAD/Agent OS 공통)를 `_internal/versions/` convention 에서 물리 계층으로 명문화; GSD byte-budget 테스트로 core 문서 비대화 방지; adapter 투영 시 capability loss 를 silent drop 아닌 explicit warning 으로 노출 (ruler 반면 [04_technical_deep_dive](04_technical_deep_dive.md) §d). 저비용·고적합 — 후보 1 과 함께 묶어 채택 권장.

## 3. Pilot Evaluation Plan

1. **범위 축소 pilot**: `adapters/claude/` 의 파일 1~2개(예: settings.json projection)에만 hash-manifest 를 시범 적용. core 수정 → 재생성 → 사용자가 adapter 직접 수정 → 재생성 시 감지·reapply 되는지 확인.
2. **성공 기준**: (a) 로컬 수정이 core 재생성에 덮이지 않고 보존 (b) 3-way 충돌 시 명시적 report (c) `gsd-`처럼 소유 경계 밖 파일 불가침.
3. **비교 기준선**: 현재의 "산출물은 소유 스킬로만 수정" convention(hook 이 편집은 차단 안 함) 대비, hash-manifest 가 실제 수정을 *감지* 하는지의 delta.
4. **선행 검증**: pilot 전 GSD `bin/install.js`·`state-transition.cjs` 실코드를 참고 자료로 정독([07_resources](07_resources.md) Tier 1).

## 4. Integration Considerations

- **증분 원칙**: 새 아키텍처가 아니라 기존 converter 층 개조 ([05_deployment](05_deployment.md) §2). `core/`→`adapters/*` 생성 순서 hard-gate(`artifact-guard.sh`)는 이미 조사 대상 중 가장 강한 순서 불변식이므로 유지.
- **파일-복제 회피**: claude-flow #1834(367개 중복 drift)를 반면교사 삼아 core 를 프로젝트로 복사·생성하지 말 것 — reference + converter 유지.
- **parity 정직성**: hook 같은 실행 격리는 어떤 도구도 lesser runtime 에서 재현 못 함 — core→adapter parity 문서에 skip+warning/prompt-simulation 처리 정책 명시.

## 5. Risk Assessment

| 리스크 | 심각도 | 완화 |
|---|---|---|
| GSD installer 실코드가 카드 서술과 다를 수 있음(line 단위 미검증) | 중 | pilot 전 실코드 정독(§3-4) |
| hash-manifest 도입이 installer 복잡도·유지비 증가 | 중 | 범위 축소 pilot 로 ROI 먼저 검증 |
| 우리 harness 가 이미 override convention 을 가져 후보 2 한계효용 낮음 | 저 | 후보 1+보조에 집중, 후보 2 는 skip 고려 |
| Codex/opencode adapter 의 parity loss 가 silent 할 위험 | 중 | explicit warning 계측(보조 후보) |

## Next Pipeline

이 조사 결과를 기술 채택 보고서로 정리하는 다음 단계:

```
/autopilot-draft "cross-platform agent framework drift-prevention 패턴 tech adoption report" --mode doc
```

이 보고서는 후보 1(GSD hash-manifest)+보조(override 승격·byte-budget·parity warning)를 채택 권고안으로 문서화하고, 후보 2·3 은 범위 한정 보완으로 배치한다.

> **경계 disclaimer**: 본 로드맵은 조사·의사결정 지원 산출물이며 실제 코드 변경·채택 결정을 대신하지 않는다. 채택 확정 전 GSD 실코드 재검증([07_resources](07_resources.md))과 pilot(§3)을 선행하고, 모든 수치·주장은 `cards/*.md` 에 소급 — 카드가 unverified 로 표시한 항목(installer file-ops, Codex parity 등)은 채택 근거로 삼기 전 재확인.

---
관련: [03_vendor_comparison](03_vendor_comparison.md) · [04_technical_deep_dive](04_technical_deep_dive.md) · [07_resources](07_resources.md)
