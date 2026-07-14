# Harness Productization — Pipeline Summary

> updated: 2026-07-14 · status: specified

## 결정된 개선 순서

1. **Canonical Manifest + Generated Projections** — 독립 `sync` 기능을 내부 build/check로 흡수하고 변경 경로와 drift를 줄인다.
2. **Progressive Product Profiles** — starter/builder/full로 점진 공개하되 kernel guard는 항상 유지한다.
3. **Capability Packs + External Skill Bridge** — 공개 생태계의 폭을 재구현하지 않고 provenance·parity·rollback 계약 아래 조합한다.

공개 검증은 내부 작업으로 만들어낼 수 없으므로 top-level 개선 과제에서 제외했다. 이 spec의 test는 회귀 방지와 재현 가능성만 주장한다.

## Spec QA

- 우리가 직접 바꿀 수 있는 약점 3개와 해결 Phase가 1:1 대응한다.
- 기반 정리→제품 표면→외부 확장의 의존 순서를 명시했다.
- 기존 installer, sync, skill-design spec과 ownership 경계를 분리했다.
- 각 Phase에 제품 계약, 범위, 수용 기준, 종료 게이트가 있다.

다음 작업은 [PRD](./prd.md)의 Phase 1만 범위로 잡아 `autopilot-code` cycle을 여는 것이다.
