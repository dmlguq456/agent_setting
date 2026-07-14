# Harness Productization — Pipeline Summary

> updated: 2026-07-14 · status: release-bound bootstrap patch in progress · spec v7

## v7 변경

- `v1.0.0` 공개 뒤 public bootstrap이 `raw main`의 distribution code를 읽고 release archive는 별도 latest tag에서 받는 mismatch window를 확인했다.
- public one-line은 self-contained `install.sh` release asset으로 이동하고, installer와 archive를 같은 immutable tag에 결속한다.
- root raw-main script는 distribution code를 읽지 않는 release redirect compatibility shim으로 축소한다.
- 완료 기준은 `v1.0.1` 자산 네 개 게시와 공개 URL 기반 exact-tag 설치 검증이다.

## 결정된 개선 순서

1. **Cross-Runtime Source Activation — complete**: Codex·Claude Code·OpenCode의 active source/revision을 노출하고 linked와 packaged를 배타적으로 운영한다.
2. **Manifest + Generated Projections + Profiles — complete**: machine metadata를 하나의 manifest로 모으고 starter/builder/full로 runtime discovery 크기를 조절한다.
3. **Local-First Packs + Optional Extensions — complete**: built-in은 외부 의존 없이 유지하고 외부 skill은 격리된 선택 기능으로만 조합한다.
4. **Release Bootstrap + Automatic Packaged Updates — complete**: 일반 사용자는 clone 없이 무결성 검사된 release를 설치하고, linked checkout을 건드리지 않는 staged updater로 갱신한다.

## v6 변경

- 일반 사용자 기본을 managed packaged release, 유지보수자 기본을 linked checkout으로 분리했다.
- GitHub Release archive+SHA-256을 유일한 network delivery boundary로 고정했다.
- update는 managed packaged source만 교체하고 linked/foreign source와 Git working tree를 건드리지 않는다.
- systemd user timer/LaunchAgent 자동 확인, staging 검증, multi-runtime rollback, atomic pointer/state commit을 수용 기준으로 추가했다.
- 공개 README는 plugin 경계 설명을 전면 가치 제안에서 내리고, 한 줄 설치와 다섯 가지 제품 강점을 앞세운다.

## Phase 4 완료 근거

- 실제 working-tree release archive를 격리 HOME에 clone 없이 설치하고 세 runtime packaged activation과 strict doctor를 통과했다.
- checksum mismatch, traversal, escaping symlink/hardlink, special file, state/lock symlink, invalid state, activation/state commit failure를 거부·rollback했다.
- linked/foreign source 보존, persistent pin, same-release repair, actual profile drift/rollback, scheduler path/ownership을 fixture로 고정했다.
- runtime/profile/extension, generated projection, conformance, adaptation boundary, Codex doctor가 모두 통과했다.
- 독립 보안 리뷰의 모든 HIGH/MEDIUM을 폐쇄했으며 최종 잔여 HIGH/MEDIUM은 0건이다.
- 첫 public release `v1.0.0`은 발행 완료했다. release-bound bootstrap 수정은 `v1.0.1`로 전달한다.

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

## v5 Phase 3 계약

- 외부 source는 local directory/existing local Git checkout만 받으며 fetch·clone·marketplace·archive를 지원하지 않는다.
- `extension.json` 한 개와 instruction skill 한 개를 `external/<publisher>/<skill>`로 lock하고 runtime에는 flat safe name으로 projection한다.
- XDG state registry와 immutable data snapshot이 source/ref/SHA/checksum, license, runtime destinations, parity loss를 소유한다.
- inspect가 secret, symlink escape, scripts/hooks/MCP/connectors/packages를 mutation 전에 전수 보고한다.
- v1은 Markdown instruction만 projection한다. 실행 surface는 항상 inactive이고 package requirement는 `external-dependency-required`로 add/update를 막는다.
- add/update/remove는 multi-runtime atomic rollback과 exact ownership check를 사용하며 core verify/runtime doctor와 실패 도메인을 분리한다.

## Phase 3 완료 근거

- local instruction-only/runtime-specific fixture의 inspect→add→no-op update→changed update→remove lifecycle이 세 runtime에서 통과했다.
- manifest/census 원자성, root-anchored no-follow snapshot I/O, secret/package/symlink 차단, destination ownership, snapshot/registry tamper, runtime-root drift를 회귀 테스트로 고정했다.
- registry 원본 bytes/hash/generation CAS와 transaction journal이 injected failure 및 hard-crash 뒤 이전 상태를 복구하고 foreign registry state는 덮어쓰지 않는다.
- Phase 1/2 profile/runtime activation, generated projections, adaptation boundary/negative guard, Codex doctor가 모두 통과했다.
- 독립 risk review가 이전 HIGH 3건·MEDIUM 4건의 폐쇄와 남은 HIGH/MEDIUM 0건을 확인했다.

## 다음 작업

공개 사용 근거는 내부 구현으로 대체하지 않는다. 이후에는 실제 외부 extension 사용 사례와 실패 데이터를 수집하되, remote marketplace/package execution은 별도 spec 없이는 core 경로에 넣지 않는다.
