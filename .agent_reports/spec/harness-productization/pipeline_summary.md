# Harness Productization — Pipeline Summary

> updated: 2026-07-14 · status: specified · spec v2

## 결정된 개선 순서

1. **Cross-Runtime Source Activation** — Codex·Claude Code·OpenCode 모두에서 active source/revision을 노출하고 linked와 packaged를 배타적으로 운영한다.
2. **Manifest + Generated Projections + Profiles** — 독립 `sync`를 내부 build/check로 흡수하고 starter/builder/full로 점진 공개한다.
3. **Local-First Packs + Optional Extensions** — built-in은 외부 의존 없이 유지하고 외부 skill은 격리된 선택 기능으로만 조합한다.

공개 검증은 내부 작업으로 만들어낼 수 없으므로 top-level 개선 과제에서 제외했다. 이 spec의 test는 회귀 방지와 재현 가능성만 주장한다.

## v2 변경

- repo 수정이 runtime과 현재 session에 자동 반영된다는 전제를 폐기했다.
- Codex native+plugin 중복, Claude symlink, OpenCode projection 미설치 상태를 하나의 공통 activation 문제로 승격했다.
- maintainer 경로를 local `linked` mode로 고정하고 plugin/marketplace/network/package manager를 core 전제에서 제거했다.
- plugin은 immutable `packaged` 배포 adapter로만 남긴다.

## Spec QA

- 우리가 직접 바꿀 수 있는 약점 3개와 해결 Phase가 1:1 대응한다.
- 활성 source 확정→generated product surface→선택적 외부 확장의 의존 순서를 명시했다.
- 기존 installer, sync, skill-design spec과 ownership 경계를 분리했다.
- 각 Phase에 제품 계약, 범위, 수용 기준, 종료 게이트가 있다.

다음 작업은 [PRD](./prd.md)의 Phase 1만 범위로 잡아 `autopilot-code` cycle을 여는 것이다.
