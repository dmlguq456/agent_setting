# Harness Productization — PRD

> 유형: component spec · library + CLI
> 상태: specified
> 버전: v1 (2026-07-14)

## 0. 한 줄 정의

현재 하네스의 강점인 portable semantics, deterministic guard, durable continuity는 kernel로 보존하면서, 변경 표면은 줄이고 사용자는 더 작게 시작하며 외부 스킬을 안전하게 조합할 수 있게 만든다.

## 1. 개선할 약점 3가지

| 순서 | 약점 | 현재 증상 | 우리가 바꿀 수 있는 것 |
|---|---|---|---|
| 1 | 변경 비용과 projection drift | canonical 문서·capability·runtime adapter·README/manifest가 넓게 연결되어 작은 의미 변경도 sync 작업과 다수 검사를 요구한다. `sync`가 독립 사용자 기능처럼 보이지만 실질적으로는 유지보수 절차다. | 단일 machine-readable manifest와 생성 projection으로 변경 경로를 좁히고, sync를 내부 검증으로 흡수한다. |
| 2 | 복잡도와 온보딩 비용 | 처음부터 core·capability·role·adapter·artifact 계약이 함께 노출되어 첫 성공 전에 알아야 할 개념이 많다. | kernel 안전장치는 유지한 채 starter/builder/full profile과 golden path로 점진 공개한다. |
| 3 | 외부 스킬 생태계와의 조합성 부족 | 내부 capability는 응집도가 높지만 공개 생태계의 폭을 자체 구현으로 따라갈 수 없고, 외부 skill을 받아들이는 ownership·provenance·parity 계약이 없다. | built-in pack과 외부 skill을 같은 extension boundary 아래 안전하게 조합한다. |

외부 프로젝트 비교 근거는 [cross-platform 분석](../../research/cross-platform-agent-frameworks/analysis_summary.md)과 [구현 시사점](../../research/cross-platform-agent-frameworks/06_implementation.md)을 따른다.

### 공개 검증에 대한 경계

대규모 사용자 채택과 battle-tested 평판은 내부 구현으로 만들 수 없으므로 이 spec의 개선 과제로 주장하지 않는다. 각 Phase의 자동 검증은 **회귀 방지와 재현 가능성**만 보장하며, 공개 신뢰는 향후 실제 사용자·issue·사례가 축적될 때 별도로 평가한다.

## 2. 목표와 비목표

### 목표

- portable 의미 변경의 canonical 입력을 한 곳으로 좁히고 runtime projection을 생성·검증한다.
- 새 사용자가 내부 구조를 먼저 학습하지 않아도 격리 환경에서 3개 이하의 user-facing 명령으로 설치·검증·첫 golden task를 완료한다.
- profile은 capability 정의를 복제하지 않고 pack dependency를 조합한다.
- 외부 skill은 provenance와 parity loss가 명시된 상태로 추가·제거·재현된다.
- 기존 full 설치와 kernel guard의 의미를 깨지 않는다.

### 비목표

- v1에서 범용 marketplace나 자체 package registry를 운영하지 않는다.
- 모든 공개 skill 또는 모든 agent runtime 지원을 약속하지 않는다.
- 외부 skill을 자동으로 canonical capability로 승격하지 않는다.
- profile에 따라 safety·permission·artifact guard를 끄지 않는다.
- 자체 benchmark를 대중적 검증의 대체물로 제시하지 않는다.

## 3. 목표 구조와 기존 spec 경계

```text
Plugin surface       built-in packs · external skill bridge · provenance lock
Product surface      starter · builder · full profiles · golden paths
Projection layer     generated runtime adapters · conformance checks
Portable kernel      routing · guards · artifact/state · memory contracts
```

- [harness-layer-sync](../harness-layer-sync/prd.md)는 현재 canonical→projection 동기화의 구현 근거다. Phase 1은 그 기능을 내부 build/check 경로로 재정의한다.
- [harness-installer](../harness-installer/prd.md)는 repo 설치와 runtime-home wiring을 소유한다. 이 spec은 profile 및 extension 선택만 추가한다.
- [skill-design-refactor](../skill-design-refactor/prd.md)는 개별 capability의 설계 계약을 소유한다. 이 spec은 capability 내용을 fork하지 않는다.

## 4. Phase 1 — Canonical Manifest and Generated Projections

### 해결하는 약점

변경 비용, 중복된 projection 관리, 독립 `sync` 기능의 불명확한 가치.

### 제품 계약

- capability/role/mode의 portable metadata와 dependency는 versioned canonical manifest가 소유한다.
- runtime adapter의 skill/agent/mode metadata와 README capability table은 manifest에서 생성한다.
- runtime 고유 구현과 fallback만 adapter-owned 파일로 남기며 portable 의미를 복제하지 않는다.
- 기존 `sync-skills` 사용자 entrypoint는 새 기능 추가를 중단하고 `build/check generated projections` 내부 절차로 흡수한다. 제거 전 deprecation 및 호출처 migration을 완료한다.
- 생성 결과가 dirty하면 check가 실패하며, 생성기는 동일 입력에 동일 출력을 낸다.

### 구현 범위

1. 기존 core/capability/role metadata census와 canonical manifest schema.
2. generated file header, ownership, stable ordering, manual override boundary.
3. projection generator와 `--check` 모드.
4. README/manifest/adapter parity 검사를 generator 기반으로 전환.
5. `sync-skills` 호출처·문서·테스트 migration 및 deprecation 판단 기록.

### 수용 기준

- 대표 portable 변경 1건이 canonical manifest와 필요한 본문 수정만으로 세 runtime projection에 반영된다.
- generated 파일 수동 수정과 stale projection이 CI에서 실패한다.
- 두 번 연속 생성한 diff가 0이다.
- adapter 고유 fallback과 unsupported 표시는 생성 과정에서 보존된다.
- 기존 installer, doctor, adaptation-boundary 검사가 통과한다.

### 종료 게이트

canonical schema, generator, 모든 기존 sync 소비자 migration, 세 runtime projection smoke가 완료되어야 Phase 2를 시작한다.

## 5. Phase 2 — Progressive Product Profiles

### 해결하는 약점

복잡도와 온보딩 비용.

### 제품 계약

- profile은 `starter`, `builder`, `full` 세 가지만 제공한다.
- `starter`는 golden code task와 필수 guard를 충족하는 최소 pack 집합이다.
- `builder`는 starter에 analyze/spec/code pipeline과 memory continuity를 더하며 신규 사용자의 권장값이다.
- `full`은 현재 지원 capability 전체를 노출하고 기존 설치의 기본 동작을 보존한다.
- profile resolver는 Phase 1 manifest의 dependency를 자동 폐쇄한다.
- kernel guard, permission boundary, source-of-truth 규칙은 모든 profile에서 항상 활성이다.
- 기존 설치는 명시적 migration 없이는 축소되지 않는다.

### 구현 범위

1. manifest에 pack/profile schema와 dependency resolver 추가.
2. installer에 `--profile starter|builder|full` 및 선택 결과 explain 출력.
3. 격리된 HOME에서 설치→doctor→golden task로 이어지는 README quickstart.
4. profile별 발견 metadata 수, user decision 수, user-facing command 수 baseline.

### 수용 기준

- 세 profile이 각 runtime의 지원 범위에서 install/verify되며 미지원 항목은 명시적으로 보고된다.
- `starter`의 발견 capability metadata 수가 `full`의 50% 이하이고 첫 성공까지 user-facing 명령은 3개 이하이다.
- 같은 capability 원본은 profile별로 복제되지 않는다.
- direct/quick/standard guard 의미와 기존 full 설치가 regression test를 통과한다.
- profile manifest와 설치 결과가 어긋나면 deterministic check가 실패한다.

### 종료 게이트

세 profile의 isolated install smoke, dependency-closure test, README golden path가 모두 통과해야 Phase 3를 시작한다.

## 6. Phase 3 — Capability Packs and External Skill Bridge

### 해결하는 약점

외부 스킬 생태계와의 조합성 부족.

### 제품 계약

- built-in capability는 `core`, `software`, `research-writing`, `design`, `operations` pack으로 조합한다. profile은 pack 집합의 이름일 뿐 capability를 fork하지 않는다.
- 외부 source v1은 local path와 Git ref를 지원한다. 기존 공개 installer 연동은 adapter로 추가할 수 있지만 필수 구현은 아니다.
- 추가 전 `inspect`가 manifest, 파일 경계, script/hook/MCP 요구, secret pattern, symlink escape, license/provenance를 보고한다.
- 외부 skill은 `external/<publisher>/<skill>` namespace에 배치하고 source/ref/SHA/runtime realization을 lock에 기록한다.
- 각 extension은 `portable`, `runtime-specific`, `instruction-only`, `tool-contract`, `unsupported` 중 하나로 분류한다.
- script, hook, MCP 활성화는 별도 사용자 승인 없이는 금지한다.

### 구현 범위

1. pack manifest와 profile resolver 통합.
2. `extension inspect/add/remove/update` 최소 CLI와 provenance lock.
3. runtime별 projection 결과 및 parity-loss report.
4. ownership-aware uninstall/rollback과 supply-chain 검사.
5. portable 1개, runtime-specific 1개의 대표 외부 skill fixture.

### 수용 기준

- 동일 lock과 source로 격리 환경에서 동일 revision을 재설치할 수 있다.
- 외부 파일은 core/capabilities canonical source를 수정하지 않는다.
- 제거 후 extension이 소유한 projection만 사라지고 기존 사용자 파일은 보존된다.
- 외부 extension 실패가 kernel 시작, doctor, built-in capability 실행을 깨지 않는다.
- runtime별 unsupported/parity loss를 성공으로 위장하지 않는다.
- 두 fixture가 inspect→add→verify→remove→reinstall 및 rollback test를 통과한다.

### 종료 게이트

대표 fixture cycle, security boundary test, 세 runtime parity report가 통과하면 v1 productization을 완료한다.

## 7. 순서와 의존성

```text
Phase 1: canonical manifest · generated projection
        ↓ stable dependency/ownership contract
Phase 2: starter · builder · full product profiles
        ↓ stable user-facing composition model
Phase 3: built-in packs · external skill bridge
```

- profile과 plugin을 먼저 만들면 현재의 넓은 sync 표면을 그대로 확대하므로 Phase 1이 선행한다.
- Phase 2가 최소 사용자 표면을 고정해야 외부 extension이 어디에 노출되고 어떤 dependency를 요구하는지 설명할 수 있다.
- 각 Phase는 별도 `autopilot-code` cycle과 commit/rollback 경계를 가진다.

## 8. 고정 결정과 열린 결정

### 고정 결정

1. kernel guard는 profile 대상이 아니며 항상 켜진다.
2. generated projection은 수동 source of truth가 아니다.
3. profile은 pack 조합이고 capability 정의를 복제하지 않는다.
4. 외부 skill은 검토 없이 core로 승격되지 않는다.
5. 구현 순서는 Phase 1→2→3이며 종료 게이트를 건너뛰지 않는다.

### 구현 착수 시 확정할 결정

- canonical manifest의 물리적 포맷과 기존 본문 frontmatter 중 어느 쪽이 metadata를 소유할지 Phase 1 census 후 확정한다.
- 신규 설치의 실제 기본값을 `builder`로 할지 추천만 할지 Phase 2 usability smoke로 확정한다.
- 어느 공개 skill format/installer와 먼저 연동할지 Phase 3 조사로 정한다.

## 9. 주요 위험과 완화

| 위험 | 완화 |
|---|---|
| manifest가 또 하나의 중복 source가 됨 | metadata ownership map과 generated-field boundary를 schema에 포함한다. |
| generator가 runtime nuance를 덮어씀 | portable generated block과 adapter-owned block을 물리적으로 분리한다. |
| 단순화가 안전장치 약화로 이어짐 | guard는 kernel always-on이며 profile schema가 참조할 수 없게 한다. |
| profile별 문서·지원 분화 | v1 profile을 3개로 제한하고 단일 resolver와 생성 문서를 사용한다. |
| 외부 skill supply-chain 위험 | inspect-first, provenance pin, 실행 surface 별도 승인, ownership rollback을 강제한다. |

## 10. 다음 구현 단위

- Cycle 1: metadata census, canonical schema, projection generator, sync migration.
- Cycle 2: profile/pack resolver, installer CLI, golden path.
- Cycle 3: extension inspect/lifecycle, provenance/security/parity.

Cycle 1 착수 전 `autopilot-code`가 현재 sync 호출처와 generated/manual ownership을 다시 조사하고 이 PRD를 source of truth로 읽어야 한다.
