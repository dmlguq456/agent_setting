# Harness Productization — Pipeline Summary

> updated: 2026-07-14 · status: phase 1 complete · spec v3

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

## v3 변경

- 실제 runtime review에서 Codex cache 복사와 Claude cache 복사가 plugin 활성화를 보장하지 않음을 확인했다.
- 사용자 지시대로 plugin을 Phase 1 활성화 경로에서 완전히 제거했다.
- `linked`와 `packaged`는 모두 runtime-native discovery를 사용하고, live repo와 checksum 고정 local bundle이라는 source 경계만 달리한다.
- Claude hooks는 `settings.json` 보존 병합과 tools/utilities projection을 함께 검증하며, 기존 Codex/Claude plugin registry와 cache는 비활성화한다.

## Phase 1 완료 근거

- 기존 installer에 `harness runtime activate|status|refresh|doctor`를 추가했다.
- 세 runtime 모두 offline linked activation과 checksum 고정 packaged bundle을 같은 native
  discovery 경로로 활성화한다.
- plugin registry/cache 중복 제거, config 보존 병합, crash journal, 단일·다중 runtime
  rollback, foreign-state 보존을 isolated HOME fixture로 검증했다.
- OpenCode global activation은 공식 plural discovery, JSON/JSONC와 옵션형 plugin entry를
  검증한다. project activation은 cwd→worktree 다단 config와 project rules 소유권을
  숨기지 않고 Phase 1 unsupported로 명시한다.
- portable guard 343건, manifest, adaptation boundary, skill conformance, legacy installer
  dry-run이 통과했다.

## Spec QA

- 우리가 직접 바꿀 수 있는 약점 3개와 해결 Phase가 1:1 대응한다.
- 활성 source 확정→generated product surface→선택적 외부 확장의 의존 순서를 명시했다.
- 기존 installer, sync, skill-design spec과 ownership 경계를 분리했다.
- 각 Phase에 제품 계약, 범위, 수용 기준, 종료 게이트가 있다.

다음 작업은 [PRD](./prd.md)의 Phase 2
`Manifest + Generated Projections + Profiles`만 범위로 잡아 `autopilot-code` cycle을
여는 것이다.
