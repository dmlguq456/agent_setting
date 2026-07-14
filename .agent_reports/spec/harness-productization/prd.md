# Harness Productization — PRD

> 유형: component spec · library + CLI
> 상태: specified
> 버전: v2 (2026-07-14)

## 0. 한 줄 정의

Codex·Claude Code·OpenCode가 어느 저장소 revision을 실제로 사용 중인지 명확히 하고, local-first 활성화 경로 위에서 generated projection, 점진적 profile, 선택적 외부 확장을 제공한다.

## 1. 개선할 약점 3가지

| 순서 | 약점 | 현재 증상 | 우리가 바꿀 수 있는 것 |
|---|---|---|---|
| 1 | source와 active runtime의 불일치 | repo 수정, feature worktree, symlink projection, plugin cache, session context가 서로 다른 revision을 가리킬 수 있다. Codex는 native+plugin 중복, Claude는 direct symlink, OpenCode는 adapter만 있고 runtime projection이 미설치인 상태다. | 세 runtime에 공통 `linked`/`packaged` 활성화 계약, revision 상태, refresh 동작, 중복 금지를 구현한다. |
| 2 | 변경 비용·복잡도·projection drift | portable 의미 변경이 canonical 문서·capability·runtime adapter·README/manifest로 넓게 번지고, 새 사용자는 이 구조를 처음부터 마주한다. | 단일 manifest와 generated projection으로 변경 경로를 좁히고 starter/builder/full profile로 점진 공개한다. |
| 3 | 외부 스킬 생태계와의 조합성 부족 | 외부 skill을 받아들이는 ownership·provenance·parity 계약이 없지만, plugin/marketplace를 core 경로에 넣으면 네트워크·cache·package manager라는 새 외부 변수가 생긴다. | built-in pack은 local-only로 유지하고 외부 extension은 격리된 선택 기능으로만 제공한다. |

외부 프로젝트 비교 근거는 [cross-platform 분석](../../research/cross-platform-agent-frameworks/analysis_summary.md)과 [구현 시사점](../../research/cross-platform-agent-frameworks/06_implementation.md)을 따른다.

### 공개 검증에 대한 경계

대규모 사용자 채택과 battle-tested 평판은 내부 구현으로 만들 수 없으므로 이 spec의 개선 과제로 주장하지 않는다. 각 Phase의 자동 검증은 회귀 방지와 재현 가능성만 보장한다.

## 2. 핵심 원칙

1. **Local-first** — 저장소 소유자의 기본 경로는 로컬 repo와 runtime-home 사이의 직접 projection이다.
2. **Plugin-optional** — plugin은 제3자 배포 형식이지 core 실행의 전제조건이 아니다.
3. **No hybrid discovery** — 같은 capability를 native와 plugin에서 동시에 활성화하지 않는다.
4. **Explicit refresh boundary** — 파일이 바뀐 것과 현재 session이 새 내용을 읽은 것을 구분한다.
5. **Offline core** — install/activate/status/doctor와 built-in capability는 marketplace, Git fetch, npm registry, connector, MCP에 의존하지 않는다.
6. **Runtime truthfulness** — 공통 의미만 통일하고 각 runtime의 hot reload·cache·restart 차이는 숨기지 않는다.

## 3. 목표와 비목표

### 목표

- `runtime status` 한 번으로 runtime별 active source, revision, mode, freshness, 필요한 action을 확인한다.
- `linked` 모드에서 repo 변경이 cache 재설치 없이 runtime discovery 경로에 도달한다.
- `packaged` 모드는 명시적 update 전까지 immutable revision을 유지한다.
- portable 의미 변경의 canonical 입력을 한 곳으로 좁히고 runtime projection을 생성·검증한다.
- 새 사용자가 3개 이하의 user-facing 명령으로 설치·검증·첫 golden task를 완료한다.
- 외부 skill은 core와 분리되고 provenance와 parity loss가 명시된 상태로 추가·제거된다.

### 비목표

- 모든 runtime에 존재하지 않는 live reload 기능을 가짜 공통 API로 약속하지 않는다.
- 초기 구현에서 범용 marketplace나 자체 package registry를 운영하지 않는다.
- 외부 skill, hook, MCP, connector를 기본 설치에 포함하지 않는다.
- plugin cache를 linked 개발 모드의 source of truth로 사용하지 않는다.
- 자체 benchmark를 대중적 검증의 대체물로 제시하지 않는다.

## 4. Runtime evidence baseline — 2026-07-14

| Runtime | 공식 동작 | 현재 로컬 realization | 설계 결론 |
|---|---|---|---|
| Codex | [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md.md)는 session 시작 때 instruction chain을 만들고, [Skills](https://learn.chatgpt.com/docs/build-skills.md)는 변경을 자동 감지할 수 있으며, [Plugins](https://learn.chatgpt.com/docs/build-plugins.md)는 설치 cache를 사용한다. | repo symlink native skill 27개와 `agent-harness-codex@0.1.0` cache가 동시에 활성화되어 duplicate warning이 난다. | linked=native only, packaged=plugin only. session-bound instruction은 restart/new session으로 표시한다. |
| Claude Code | [Skills](https://code.claude.com/docs/en/slash-commands)는 watched native directory를 hot reload하지만 이미 호출한 skill 본문은 재호출 전 대화에 남는다. [Plugins](https://code.claude.com/docs/en/plugins)는 cache와 `/reload-plugins`를 사용한다. | `~/.claude` 주요 경로가 repo adapter로 직접 symlink되고 harness plugin은 설치되지 않았다. | linked=direct native symlink, packaged=plugin cache. invoked-skill/session stale을 별도 표시한다. |
| OpenCode | [Rules](https://opencode.ai/docs/rules)는 시작 시 rule을 찾고, [Plugins](https://opencode.ai/docs/plugins)는 local plugin을 직접 읽되 npm plugin은 cache한다. [Skills](https://opencode.ai/docs/skills)는 repo/user 경로를 discovery한다. | adapter 파일은 있으나 `~/.config/opencode` harness projection이 설치되지 않았다. | linked projection installer를 먼저 제공한다. 공식 hot-reload 보장이 없는 surface는 restart-required fallback으로 표시한다. |

## 5. 목표 구조와 기존 spec 경계

```text
Optional extension   external skills · explicit provenance · isolated approval
Product surface      starter · builder · full profiles · built-in packs
Activation layer     linked | packaged · active revision · refresh/status
Projection layer     generated runtime adapters · conformance checks
Portable kernel      routing · guards · artifact/state · memory contracts
```

- [harness-layer-sync](../harness-layer-sync/prd.md)는 현재 canonical→projection 동기화의 구현 근거다. Phase 2는 그 기능을 내부 build/check 경로로 재정의한다.
- [harness-installer](../harness-installer/prd.md)는 repo 설치와 runtime-home wiring을 소유한다. Phase 1은 runtime 활성화 mode와 freshness contract를 추가한다.
- [skill-design-refactor](../skill-design-refactor/prd.md)는 개별 capability의 설계 계약을 소유한다. 이 spec은 capability 내용을 fork하지 않는다.

## 6. Phase 1 — Cross-Runtime Source Activation

### 해결하는 약점

repo source, runtime projection, plugin cache, current session이 서로 다른 내용을 사용하는 문제.

### 공통 활성화 모델

| Mode | 목적 | Source of truth | 외부 의존 | 갱신 방식 |
|---|---|---|---|---|
| `linked` | 소유자 개발·일상 사용 | local canonical repo | 없음 | repo 변경→projection digest 확인→runtime별 reload/new session |
| `packaged` | 제3자 배포·재현 설치 | immutable local bundle revision | 설치 artifact만; marketplace는 선택 | 새 bundle을 명시적으로 install/update |

- `both` mode는 존재하지 않는다.
- feature worktree는 명시적으로 activate하지 않는 한 active source가 아니다.
- dirty repo는 revision을 `<HEAD>+dirty:<digest>`로 표시하고 packaged artifact 생성은 기본 거부한다.
- 활성화는 transactional하며 실패 시 이전 runtime-home projection과 mode를 복구한다.

### CLI 계약

```text
harness runtime status [--runtime codex|claude|opencode|all] [--json]
harness runtime activate --runtime <...> --mode linked|packaged [--source <path>]
harness runtime refresh --runtime <...>
harness runtime doctor --runtime <...> [--strict]
```

`status --json` 최소 필드:

```text
runtime, mode, source_root, source_revision, active_revision,
projection_digest, discovery_paths, duplicate_sources,
freshness, session_action, external_dependencies
```

`freshness`는 `fresh`, `source-ahead`, `cache-stale`, `session-reload-needed`, `duplicate`, `missing`, `unsupported` 중 하나다. 명령은 사람이 읽는 다음 action과 machine-readable exit status를 함께 제공한다.

### Runtime realization

- **Codex linked**: `$CODEX_HOME` native skill/agent/mode/hook projection만 repo에 연결하고 harness plugin을 disable/uninstall한다.
- **Codex packaged**: versioned harness plugin만 활성화하고 native harness discovery link를 제거한다.
- **Claude linked**: `~/.claude` native skill/agent/hook projection만 repo에 연결한다. 변경 surface에 따라 hot reload, skill 재호출, new session을 안내한다.
- **Claude packaged**: versioned plugin cache만 사용하고 `/reload-plugins` 또는 restart requirement를 상태에 표시한다.
- **OpenCode linked**: `~/.config/opencode`의 rules/skills/commands/agents/local-plugin projection을 repo에 연결하는 installer를 제공한다.
- **OpenCode packaged**: local immutable bundle을 projection한다. npm registry는 기본 경로로 사용하지 않는다.
- runtime이 지원하지 않는 surface는 다른 runtime 형식을 복사하지 않고 `unsupported + fallback`으로 기록한다.

### 외부 요인 제거 계약

- Phase 1 명령은 `HOME`, runtime binary, local repo 외 네트워크 자원을 사용하지 않는다.
- core 활성화에 marketplace refresh, plugin download, npm/bun install, Git fetch, MCP/connector 인증을 요구하지 않는다.
- packaged bundle은 repo에서 local build하고 checksum과 source revision을 포함한다.
- runtime-owned credentials, config DB, session log는 수정하지 않는다.
- config 변경이 필요하면 harness-owned fragment를 병합하되 기존 사용자 값을 보존하고 rollback metadata를 남긴다.

### 수용 기준

- 격리된 HOME에서 세 runtime의 `linked activate→status→doctor`가 네트워크 없이 실행된다.
- repo fixture 수정 후 linked projection digest는 즉시 변하고, packaged active revision은 명시적 refresh 전까지 변하지 않는다.
- Codex native+plugin, Claude native+plugin, OpenCode local+npm duplicate fixture를 모두 탐지하고 strict doctor가 실패한다.
- active source가 main repo인지 feature worktree인지 absolute path와 revision으로 구분한다.
- rules/instructions, skill, agent, hook/config 각각에 필요한 session action을 runtime별로 정확히 출력한다.
- 실패 주입 후 이전 projection이 복구되고 credentials/session/cache의 비소유 파일 hash가 유지된다.
- OpenCode linked projection이 실제 runtime-home에 설치되고 doctor가 missing이 아닌 fresh를 보고한다.

### 종료 게이트

세 runtime의 offline linked smoke, packaged immutability, duplicate detection, rollback, session-boundary matrix가 통과해야 Phase 2를 시작한다.

## 7. Phase 2 — Canonical Manifest, Generated Projections, Profiles

### 해결하는 약점

변경 비용, projection drift, 복잡도와 온보딩 비용.

### 제품 계약

- capability/role/mode의 portable metadata와 dependency는 versioned canonical manifest가 소유한다.
- runtime adapter metadata와 README capability table은 manifest에서 생성한다.
- runtime 고유 구현과 fallback만 adapter-owned block으로 남긴다.
- `sync-skills` 사용자 entrypoint는 `build/check generated projections` 내부 절차로 흡수한다.
- profile은 `starter`, `builder`, `full` 세 개이며 manifest의 pack dependency를 조합한다.
- `starter`는 golden code task와 필수 guard, `builder`는 analyze/spec/code/memory, `full`은 현재 전체 capability를 노출한다.
- kernel guard와 source-of-truth 규칙은 profile에 관계없이 항상 활성이다.

### 구현 범위

1. metadata census, canonical manifest schema, generated/manual ownership map.
2. deterministic projection generator와 `--check`.
3. README/manifest/adapter parity 검사 전환과 `sync-skills` migration.
4. pack/profile resolver와 installer `--profile`.
5. 설치→doctor→golden task README quickstart.

### 수용 기준

- 대표 portable 변경 1건이 canonical 입력만으로 세 runtime projection에 반영된다.
- generated 파일 수동 수정과 stale projection이 CI에서 실패하고 연속 생성 diff가 0이다.
- adapter 고유 fallback과 unsupported 표시는 보존된다.
- `starter` 발견 metadata가 `full`의 50% 이하이고 첫 성공까지 user-facing 명령은 3개 이하이다.
- 기존 full 설치와 direct/quick/standard guard 의미가 유지된다.

### 종료 게이트

generator determinism, sync 소비자 migration, 세 profile isolated install과 golden path가 통과해야 Phase 3를 시작한다.

## 8. Phase 3 — Local-First Packs and Optional Extension Bridge

### 해결하는 약점

core에 외부 변수를 끌어들이지 않으면서 공개 스킬 생태계와 조합해야 하는 문제.

### 제품 계약

- built-in capability는 `core`, `software`, `research-writing`, `design`, `operations` pack으로 조합하며 모두 repo-local이다.
- 외부 extension 기능은 기본 비활성이고 core install/doctor 성공 조건에 포함되지 않는다.
- 외부 source v1은 local path와 이미 존재하는 local Git checkout만 지원한다. 원격 fetch/marketplace client는 별도 optional adapter다.
- 추가 전 `inspect`가 manifest, script/hook/MCP 요구, secret pattern, symlink escape, license/provenance를 보고한다.
- 외부 skill은 `external/<publisher>/<skill>` namespace와 source/ref/SHA/checksum lock을 사용한다.
- script, hook, MCP, connector, package install은 각각 별도 승인 없이는 활성화하지 않는다.

### 구현 범위

1. built-in pack manifest와 profile resolver 통합.
2. offline `extension inspect/add/remove/update` 최소 CLI와 provenance lock.
3. runtime별 projection/parity-loss report.
4. ownership-aware uninstall/rollback과 supply-chain 검사.
5. instruction-only portable fixture 1개와 runtime-specific fixture 1개.

### 수용 기준

- 빈 network namespace에서도 built-in pack과 local extension lifecycle이 동작한다.
- 외부 파일은 canonical source를 수정하지 않고 제거 후 소유 projection만 사라진다.
- 외부 extension 실패가 kernel 시작, doctor, built-in capability 실행을 깨지 않는다.
- dependency download가 필요하면 자동 실행하지 않고 `external-dependency-required`로 중단한다.
- unsupported/parity loss를 성공으로 위장하지 않는다.

### 종료 게이트

두 fixture의 offline lifecycle, security boundary, rollback, 세 runtime parity report가 통과하면 v1 productization을 완료한다.

## 9. 순서와 의존성

```text
Phase 1: source → runtime activation truth
        ↓ one active source and explicit refresh boundary
Phase 2: canonical manifest → generated projection → profiles
        ↓ stable local product surface
Phase 3: optional external extension bridge
```

- 무엇이 실제로 실행되는지 모르는 상태에서 generator나 plugin을 추가하면 drift를 확대하므로 activation contract가 최우선이다.
- Phase 2가 stable local product surface를 고정해야 외부 extension이 core를 오염시키지 않는다.
- 각 Phase는 별도 `autopilot-code` cycle과 commit/rollback 경계를 가진다.

## 10. 고정 결정과 열린 결정

### 고정 결정

1. Phase 1은 Codex 전용이 아닌 Codex·Claude Code·OpenCode 공통 계약이다.
2. maintainer 기본은 `linked`, 제3자 배포만 `packaged`다.
3. plugin은 core runtime dependency가 아니며 native+plugin 동시 활성화를 금지한다.
4. network, marketplace, package manager는 core activation 경로에서 제외한다.
5. runtime별 reload 차이를 숨기지 않고 status에 표시한다.
6. 구현 순서는 Phase 1→2→3이며 종료 게이트를 건너뛰지 않는다.

### 구현 착수 시 확정할 결정

- 공통 CLI의 물리적 진입점을 기존 installer에 둘지 새 `utilities/runtime-activation` 모듈로 둘지 Phase 1 plan에서 정한다.
- packaged bundle 포맷은 세 runtime 공통 tar artifact와 runtime-native plugin 중 어떤 조합이 가장 단순한지 구현 census 후 정한다.
- 신규 설치의 실제 기본 profile을 `builder`로 할지 Phase 2 usability smoke에서 확정한다.

## 11. 주요 위험과 완화

| 위험 | 완화 |
|---|---|
| 즉시 파일 반영과 session 반영을 혼동 | projection freshness와 session action을 별도 필드로 둔다. |
| linked mode가 다른 worktree를 가리킴 | absolute source root, git common-dir, revision을 status와 activation record에 고정한다. |
| plugin 제거가 배포 기능까지 약화 | linked와 packaged를 분리하고 plugin은 packaged adapter로만 유지한다. |
| OpenCode parity를 추정으로 과장 | 공식 surface가 없는 항목은 unsupported/restart fallback으로 기록한다. |
| manifest가 또 하나의 중복 source가 됨 | metadata ownership map과 generated-field boundary를 schema에 포함한다. |
| 외부 skill supply-chain 위험 | offline/local source 우선, inspect-first, provenance pin, 실행 surface 별도 승인을 강제한다. |

## 12. 다음 구현 단위

- Cycle 1: 세 runtime activation census, 상태 schema, linked activate/status/doctor, duplicate cleanup, rollback.
- Cycle 2: canonical manifest/generator, sync migration, profile resolver와 quickstart.
- Cycle 3: built-in packs, offline extension lifecycle, provenance/security/parity.

Cycle 1 착수 전 `autopilot-code`가 Codex·Claude Code·OpenCode의 실제 runtime-home과 공식 reload/cache 경계를 다시 확인하고 이 PRD를 source of truth로 읽어야 한다.
