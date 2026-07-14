# Harness Productization — Pipeline Summary

> updated: 2026-07-14 · status: phase 2 complete · spec v4

## 결정된 개선 순서

1. **Cross-Runtime Source Activation — complete**: Codex·Claude Code·OpenCode의 active source/revision을 노출하고 linked와 packaged를 배타적으로 운영한다.
2. **Manifest + Generated Projections + Profiles — complete**: machine metadata를 하나의 manifest로 모으고 starter/builder/full로 runtime discovery 크기를 조절한다.
3. **Local-First Packs + Optional Extensions — next**: built-in은 외부 의존 없이 유지하고 외부 skill은 격리된 선택 기능으로만 조합한다.

공개 채택은 내부 작업으로 만들어낼 수 없으므로 이 spec의 자동 검증은 회귀 방지와 재현 가능성만 주장한다.

## v4 변경

- canonical machine source를 `harness-manifest.json`으로 고정했다.
- root `manifest.json`, capability/role catalog, runtime metadata를 generated output으로 전환했다.
- core projection build/check entrypoint를 `tools/generate.py` 하나로 통합했다.
- `starter` 6 capability/4 role, `builder` 14/7, `full` 27/8의 실제 runtime discovery profile을 구현했다.
- usability smoke 결과 새 activation 기본값을 `builder`로 확정했다.
- marketplace bundle을 core generator, activation, doctor, verify에서 분리했다.
- README를 profile quickstart와 native-first architecture 중심의 제품 페이지로 다시 작성했다.

## Phase 2 완료 근거

- canonical manifest는 27 capabilities, 8 portable roles, 26 modes, 5 built-in packs, 3 profiles와 generated/manual ownership map을 검증한다.
- 대표 canonical metadata 변경이 Claude Code·Codex·OpenCode native projection과 Claude compatibility reference에 전파된다.
- 연속 생성 hash가 같고 generated file 수동 편집은 `--check`에서 실패한다.
- isolated HOME에서 세 runtime의 starter/builder/full activation과 kernel guard 상시 노출을 검증했다.
- Phase 1의 linked/packaged immutability, duplicate detection, rollback, runtime-owned state 보존 회귀가 유지된다.
- portable guard 343건, skill conformance, adaptation boundary, Codex doctor가 통과했다.
- profile 없는 Phase 1 fixture는 legacy `full` 의미를 유지해 기존 설치 호환성을 보존한다.

## 제품 경계

- core 경로는 local repo, runtime home, Python, Git만 사용하며 marketplace·npm·MCP·connector를 요구하지 않는다.
- OpenCode guard plugin은 local runtime hook bridge이고 외부 package가 아니다.
- Codex/Claude marketplace bundle은 명시적 legacy 배포 산출물이며 core 성공 조건이 아니다.
- linked repo 변경이 discovery path에 보이는 것과 현재 session이 instruction을 다시 읽는 것은 별개이며 `session_action`이 그 차이를 보고한다.

## 다음 작업

[PRD](./prd.md)의 Phase 3 `Local-First Packs and Optional Extension Bridge`만 별도 `autopilot-code` cycle로 연다. 기존 built-in pack/profile resolver를 재사용하고, local path extension의 inspect-first·provenance·rollback·parity-loss 계약을 추가한다.
