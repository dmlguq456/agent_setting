# Harness Productization — PRD

> 유형: component spec · library + CLI
> 상태: phase 4 implementation complete · automatic SemVer release policy implemented
> 버전: v8 (2026-07-14)

## 0. 한 줄 정의

Codex·Claude Code·OpenCode가 어느 harness release 또는 checkout revision을 실제로 사용 중인지 명확히 하고, clone 없는 배포와 local-first 활성화 경로 위에서 generated projection, 점진적 profile, 선택적 외부 확장을 제공한다.

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

1. **Local-first after delivery** — 일반 사용자는 검증된 managed release, 유지보수자는 로컬 checkout을 source로 사용하며 runtime activation 이후에는 원격 서비스가 필요 없다.
2. **Plugin-outside-core** — plugin은 별도 export/배포 실험일 뿐 Phase 1 활성화 형식이 아니다.
3. **No hybrid discovery** — 같은 capability를 native와 plugin에서 동시에 활성화하지 않는다.
4. **Explicit refresh boundary** — 파일이 바뀐 것과 현재 session이 새 내용을 읽은 것을 구분한다.
5. **Offline activation core** — activate/status/doctor와 built-in capability는 marketplace, Git fetch, npm registry, connector, MCP에 의존하지 않는다. 최초 release 다운로드와 managed update만 명시적 network boundary다.
6. **Runtime truthfulness** — 공통 의미만 통일하고 각 runtime의 hot reload·cache·restart 차이는 숨기지 않는다.

## 3. 목표와 비목표

### 목표

- `runtime status` 한 번으로 runtime별 active source, revision, mode, freshness, 필요한 action을 확인한다.
- `linked` 모드에서 repo 변경이 cache 재설치 없이 runtime discovery 경로에 도달한다.
- `packaged` 모드는 명시적 update 전까지 immutable revision을 유지한다.
- portable 의미 변경의 canonical 입력을 한 곳으로 좁히고 runtime projection을 생성·검증한다.
- 새 사용자가 3개 이하의 user-facing 명령으로 설치·검증·첫 golden task를 완료한다.
- 새 사용자는 Git clone 없이 한 줄 bootstrap으로 checksum 검증된 packaged release와 `harness` launcher를 설치한다.
- managed packaged 설치는 OS user scheduler를 통해 새 release를 자동 확인하고, staging 검증·원자 전환·rollback을 수행한다.
- 외부 skill은 core와 분리되고 provenance와 parity loss가 명시된 상태로 추가·제거된다.

### 비목표

- 모든 runtime에 존재하지 않는 live reload 기능을 가짜 공통 API로 약속하지 않는다.
- 초기 구현에서 범용 marketplace나 자체 package registry를 운영하지 않는다. GitHub Releases를 release artifact transport로만 사용한다.
- 외부 skill, hook, MCP, connector를 기본 설치에 포함하지 않는다.
- plugin cache나 release updater를 linked 개발 모드의 source of truth로 사용하지 않으며 updater가 `git pull`을 수행하지 않는다.
- 자체 benchmark를 대중적 검증의 대체물로 제시하지 않는다.

## 4. Runtime evidence baseline — 2026-07-14

| Runtime | 공식 동작 | 현재 로컬 realization | 설계 결론 |
|---|---|---|---|
| Codex | [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md.md)는 session 시작 때 instruction chain을 만들고, [Skills](https://learn.chatgpt.com/docs/build-skills.md)는 변경을 자동 감지할 수 있다. [Plugins](https://learn.chatgpt.com/docs/build-plugins.md)는 cache 복사만으로 활성화되지 않고 marketplace 설치와 enable 상태를 별도로 가진다. | repo symlink native skill 27개와 `agent-harness-codex@0.1.0` plugin이 동시에 활성화되어 duplicate warning이 난다. | linked와 packaged 모두 native discovery를 사용하고 source만 live repo/immutable bundle로 구분한다. 기존 harness plugin은 비활성화한다. |
| Claude Code | [Skills](https://code.claude.com/docs/en/slash-commands)는 watched native directory를 hot reload하지만 이미 호출한 skill 본문은 재호출 전 대화에 남는다. [Plugins](https://code.claude.com/docs/en/plugins)는 별도 설치 registry와 cache, `/reload-plugins`를 사용한다. | `~/.claude` 주요 경로가 repo adapter로 직접 symlink되고 harness plugin은 설치되지 않았다. | linked와 packaged 모두 native discovery를 사용한다. hooks는 `settings.json`에 보존적으로 병합하고 필요한 tools/utilities를 함께 projection한다. |
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
| `packaged` | 재현 가능한 고정 revision | immutable local bundle revision | 없음 | 새 bundle을 명시적으로 refresh |

- `both` mode는 존재하지 않는다.
- feature worktree는 명시적으로 activate하지 않는 한 active source가 아니다.
- dirty repo는 revision을 `<HEAD>+dirty:<digest>`로 표시하고 packaged artifact 생성은 기본 거부한다.
- 활성화는 transactional하며 실패 시 이전 runtime-home projection과 mode를 복구한다.
- Phase 1 activation scope는 세 runtime 모두 `global`이다. `project`는 runtime별
  다단 config/rules 소유권을 별도 설계할 때까지 명시적으로 실패하며 legacy installer와
  혼동하지 않는다.

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

- **Codex linked**: `$CODEX_HOME` native skill/agent/mode/hook projection을 repo에 연결하고 harness plugin enable state와 cache discovery를 제거한다.
- **Codex packaged**: local immutable bundle의 동일 native surface를 projection한다. plugin marketplace/config/cache는 활성화 경로에 쓰지 않는다.
- **Claude linked**: `~/.claude` native skill/agent/hook projection을 repo에 연결하고 harness hook만 `settings.json`에 병합한다. hooks가 참조하는 tools/utilities를 함께 연결한다.
- **Claude packaged**: local immutable bundle의 동일 native surface와 hook 설정을 projection한다. plugin install registry/cache는 활성화 경로에 쓰지 않는다.
- **OpenCode linked**: `~/.config/opencode`의 rules/skills/commands/agents/local-plugin projection을 repo에 연결하는 installer를 제공한다.
- **OpenCode packaged**: local immutable bundle을 projection한다. npm registry는 기본 경로로 사용하지 않는다.
- runtime이 지원하지 않는 surface는 다른 runtime 형식을 복사하지 않고 `unsupported + fallback`으로 기록한다.

### 외부 요인 제거 계약

- Phase 1 명령은 `HOME`, runtime binary, local repo 외 네트워크 자원을 사용하지 않는다.
- core 활성화에 marketplace refresh, plugin download, npm/bun install, Git fetch, MCP/connector 인증을 요구하지 않는다.
- packaged bundle은 repo에서 local build하고 checksum과 source revision을 포함한다.
- packaged bundle checksum이 달라지면 strict doctor는 `cache-stale`로 실패한다.
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

### 구현 결과 — 2026-07-14

- `harness-manifest.json`이 27 capabilities, 8 portable roles, 26 modes, 5 built-in packs, 3 profiles의 canonical machine contract가 됐다.
- root `manifest.json`은 generated compatibility view로 남고, core projection은 `python3 tools/generate.py [--check]` 한 경로로 생성·검증한다.
- 대표 metadata 변경이 Claude Code·Codex·OpenCode native projection과 Claude compatibility reference에 전파되며, 수동 drift와 비결정적 재생성을 acceptance test가 거부한다.
- `starter`/`builder`/`full`은 각각 6/14/27 capabilities와 4/7/8 roles를 실제 runtime discovery에 노출하며 kernel guard와 `memory-scout`는 항상 유지한다.
- 새 activation의 기본 profile은 usability smoke 결과 `builder`로 확정했다. profile field가 없는 Phase 1 legacy state는 기존 동작 보존을 위해 `full`로 해석한다.
- marketplace bundle 생성·등록·cache는 core generator, activation, doctor, verify의 성공 조건에서 제거했다. 명시적 legacy `install --plugin`만 선택 배포 경로로 남는다.
- isolated HOME의 세 runtime × 세 profile activation, generated drift/determinism, runtime activation 회귀, portable guards, skill conformance, adaptation boundary가 통과했다.

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

### v1 source와 manifest 계약

- source는 URL이 아닌 존재하는 local directory만 받는다. directory가 Git worktree 안이면 현재 local checkout의 repo root, ref, HEAD SHA, dirty 여부를 기록하지만 fetch·pull·clone은 실행하지 않는다.
- source root에는 `extension.json`과 하나의 instruction skill이 있어야 한다. manifest 최소 필드는 `schema_version=1`, `publisher`, `name`, `version`, `license`, `skill_path`, `requirements`다.
- `publisher`와 `name`은 lowercase alphanumeric + single-hyphen 형식이다. canonical id는 `external/<publisher>/<name>`이다. 세 runtime의 flat discovery id는 `external-<readable>-<sha256(canonical-id)[:12]>`이며 전체 64자 이하가 되도록 readable 부분만 경계에서 truncate한다. 이 physical id는 서로 다른 canonical id가 같은 flat name이 되는 충돌을 막는다.
- v1 extension은 한 manifest당 skill 하나다. 여러 skill bundle, remote source, archive, marketplace catalog, registry client는 범위 밖이다.
- canonical source는 수정하지 않는다. add/update는 검사된 Markdown instruction 파일만 harness-owned immutable snapshot으로 materialize한다.

`requirements`는 다음 다섯 배열을 가진다.

```json
{
  "scripts": [],
  "hooks": [],
  "mcp": [],
  "connectors": [],
  "packages": []
}
```

선언과 실제 file census가 다르면 둘 다 보고한다. `scripts`, `hooks`, `mcp`, `connectors`는 v1에서 항상 inactive이며 projection에 포함하지 않는다. `packages`가 하나라도 있으면 add/update는 mutation 전에 `external-dependency-required`로 중단한다.

### CLI 계약

```text
harness extension inspect <local-source> [--json]
harness extension add <local-source> [--runtime codex|claude|opencode|all] [--json]
harness extension update <external/publisher/skill> [--source <local-source>] [--json]
harness extension remove <external/publisher/skill> [--json]
```

- `inspect`는 read-only이며 manifest validity, provenance, license, source checksum, secret finding, symlink finding, declared/detected surface, external dependency, runtime parity를 반환한다.
- `add`는 inspect를 내부에서 다시 실행하고 모든 blocking finding을 mutation 전에 거부한다. source root를 directory fd로 고정한 `lstat`/`O_NOFOLLOW` census의 `extension.json` bytes를 manifest 입력으로 사용하고, staging materialize → staging bytes 재검사 → canonical identity·manifest digest·source checksum 재확인까지 통과한 뒤에만 선택 runtime 전체를 한 transaction으로 projection한다.
- `update`는 lock의 기존 source를 기본 사용하며 `--source`로 다른 local checkout을 명시할 수 있다. checksum이 같으면 no-op이다.
- `remove`는 registry가 소유하고 현재 lock과 일치하는 projection만 제거한다. 사용자가 교체한 path나 다른 target은 ownership conflict로 남기고 임의 삭제하지 않는다.
- extension command는 core `verify`, runtime `doctor`, built-in profile의 성공 조건에 들어가지 않는다. extension failure는 별도 nonzero exit와 report로만 격리한다.

### Provenance lock과 저장 위치

- registry: `${XDG_STATE_HOME:-~/.local/state}/agent-harness/extensions/registry.json`
- immutable snapshot: `${XDG_DATA_HOME:-~/.local/share}/agent-harness/extensions/<publisher>/<skill>/<checksum>/`
- XDG/runtime override는 절대 경로만 허용한다. Codex는 `$CODEX_HOME`, Claude Code는 `$CLAUDE_CONFIG_DIR`, OpenCode는 `$XDG_CONFIG_HOME/opencode`를 해석하며 add 시 확정된 runtime root를 lock에 기록한다. update/remove 시 root가 달라졌으면 기존 소유권을 추측하지 않고 중단한다.
- lock 최소 필드: canonical id, absolute source, source kind, Git root/ref/SHA/dirty, source checksum, projection checksum, manifest version/license, snapshot root, selected runtimes, runtime root, runtime별 destination/status/parity loss, created/updated timestamp.
- digest는 versioned canonical encoding(`source-digest-v1`, `projection-digest-v1`)으로 path/type/link-target/content를 묶는다. source checksum과 exact projected-tree checksum을 분리하고 snapshot key는 둘의 composite digest다. 기존 snapshot은 재계산 결과가 lock과 정확히 맞고 symlink가 없을 때만 재사용한다.
- registry, transaction journal, snapshot directory 자체가 symlink면 fail closed한다. source symlink는 root-anchored directory-fd census로 전수 검사해 source root 밖 escape, broken target, cycle을 blocking finding으로 처리하고 projection snapshot에는 symlink를 보존하지 않는다. Snapshot lookup, digest, cleanup도 XDG data root부터 각 component를 no-follow로 열고 root-anchored deletion을 사용한다. unreadable, file-count/size limit 초과도 skip하지 않고 blocking finding이다.
- secret 검사 결과에는 pattern id와 relative path만 남기며 matched value를 출력·lock 저장하지 않는다. private-key/token 형식의 high-confidence finding은 add/update를 막는다.
- registry는 삭제 권한의 진실원천이 아니다. canonical id와 runtime에서 destination/native id를 다시 계산하고, snapshot path도 검증된 XDG data root와 checksum에서 다시 계산한다. 저장된 arbitrary path는 mutation에 사용하지 않는다.

### Runtime projection과 parity 계약

| Runtime | v1 projection | session action | plugin/runtime-specific surface |
|---|---|---|---|
| Codex | `$CODEX_HOME/skills/<physical-id>` → immutable snapshot | skill 재호출 또는 새 session | plugin/hook/MCP는 inactive |
| Claude Code | `~/.claude/skills/<physical-id>` → immutable snapshot | watched dir이면 재호출, top-level dir 최초 생성 시 새 session | plugin namespace·agent·hook·MCP는 inactive |
| OpenCode | `~/.config/opencode/skills/<physical-id>` → immutable snapshot | restart-required fallback | JS/TS plugin·MCP·custom tool은 inactive |

- source `SKILL.md`의 instruction body는 보존하되 snapshot frontmatter의 `name`은 hashed physical id로 생성한다. source name은 manifest name과 일치해야 한다.
- instruction-only extension은 세 runtime에서 `parity=full`이다. runtime-specific/실행 surface가 있으면 skill projection과 별개로 `parity=degraded`, `inactive_surfaces`, runtime별 loss reason을 반환한다.
- physical name은 canonical namespace의 projection mapping이지 source identity 변경이 아니다. registry와 user-facing 출력은 항상 canonical id를 우선한다.

### Transaction과 ownership 계약

1. add/update/remove 전에 모든 destination과 current registry ownership을 preflight한다.
2. invocation 전체에 XDG state file lock을 잡고 registry schema/generation을 검증해 concurrent lost update를 막는다.
3. snapshot은 temp directory에서 staging 재검사와 projection checksum을 확인한 뒤 atomic rename으로 publish한다.
4. 첫 mutation 전에 registry 원본 bytes·hash·generation, 예상 after hash/generation, 모든 runtime link 상태를 XDG transaction journal에 기록한다. 다음 extension invocation은 incomplete journal을 먼저 복구하되 현재 registry가 기록된 before 또는 expected-after state일 때만 복구하고, 다른 generation/content면 `recovery-conflict`로 fail closed한다.
5. runtime link는 temp symlink + atomic replace로 전환한다. multi-runtime 중간 실패나 registry write 실패 시 journal에서 역순 복구한다.
6. registry와 link commit 뒤 journal을 committed로 전환한 후에만 이전/미사용 snapshot을 정리한다. source, runtime-owned config, credential, session, cache, built-in activation state는 건드리지 않는다.
7. built-in capability id에는 `external-` prefix를 예약한다. add/update는 built-in manifest, registry, 세 destination을 함께 preflight한다.

### 구현 범위

1. built-in pack manifest와 profile resolver 통합.
2. offline `extension inspect/add/remove/update` 최소 CLI와 provenance lock.
3. runtime별 projection/parity-loss report.
4. ownership-aware uninstall/rollback과 supply-chain 검사.
5. instruction-only portable fixture 1개와 runtime-specific fixture 1개.

기존 `harness-manifest.json`의 five-pack/profile resolver는 Phase 2 결과를 그대로 재사용하고 Phase 3 회귀 테스트에서 local-only invariant를 확인한다. extension registry를 canonical built-in manifest에 합치지 않는다.

### 수용 기준

- 빈 network namespace에서도 built-in pack과 local extension lifecycle이 동작한다.
- 외부 파일은 canonical source를 수정하지 않고 제거 후 소유 projection만 사라진다.
- 외부 extension 실패가 kernel 시작, doctor, built-in capability 실행을 깨지 않는다.
- dependency download가 필요하면 자동 실행하지 않고 `external-dependency-required`로 중단한다.
- unsupported/parity loss를 성공으로 위장하지 않는다.
- malicious symlink, secret token, invalid namespace/path, destination ownership conflict가 mutation 전에 거부된다.
- multi-runtime failure injection 후 registry, prior projection, built-in activation state가 byte-for-byte 복구된다.
- instruction-only fixture는 세 runtime 모두 full parity이고 runtime-specific fixture는 inactive surface와 degraded parity를 runtime별로 정확히 보고한다.
- source TOCTOU, tampered registry/snapshot, concurrent writer, incomplete transaction journal이 fail closed 또는 이전 상태 복구로 끝난다.
- dangling/corrupt external extension과 extension-only+legacy-plugin 조합이 native built-in duplicate로 오인되지 않고 core doctor 결과를 바꾸지 않는다.

### 종료 게이트

두 fixture의 offline lifecycle, security boundary, rollback, 세 runtime parity report가 통과하면 v1 productization을 완료한다.

### 구현 결과 — 2026-07-14

- `harness extension inspect|add|update|remove`를 기존 installer CLI에 추가하고 JSON/human exit 계약을 고정했다.
- instruction-only snapshot만 projection하며 script, hook, MCP, connector, plugin은 inactive/parity loss로 남고 package dependency는 mutation 전에 차단된다.
- source/manifest TOCTOU, secret, symlink escape, XDG parent escape, destination collision, registry/snapshot tamper, runtime-root drift, concurrent writer, injected rollback, crash-journal CAS recovery를 isolated HOME E2E로 검증했다.
- Codex·Claude Code·OpenCode runtime skill projection은 각 runtime override를 따르고, built-in profile/runtime activation state와 core doctor는 extension 실패 도메인에서 격리된다.
- 독립 구현 리뷰의 HIGH 3건과 MEDIUM 4건을 모두 폐쇄했으며 남은 HIGH/MEDIUM finding은 없다.

## 9. Phase 4 — Release Bootstrap and Automatic Packaged Updates

### 해결하는 약점

현재 일반 사용자도 repository clone, checkout 위치, linked/packaged 선택을 알아야 하며
`harness update`는 release를 받지 않고 기존 copy-once drift만 확인한다. 이 때문에
설치가 단순한 제품 표면과 runtime currentness 계약이 연결되지 않는다.

### 배포 계약

| 사용자 | 기본 source | 설치 | 갱신 |
|---|---|---|---|
| 일반 사용자 | checksum-verified managed release | `curl .../releases/latest/download/install.sh \| sh` | OS user scheduler가 stable release를 확인하고 packaged runtime만 원자 교체 |
| 유지보수자 | explicit local Git checkout | clone 후 `runtime activate --mode linked` | 사용자가 checkout을 직접 갱신; harness는 fetch/pull하지 않음 |

- GitHub Release asset은 고정 이름의 archive와 SHA-256 sidecar를 제공한다.
  Sidecar는 전송/asset corruption을 탐지하며 독립 서명이 아니다. Publisher
  authenticity의 trust anchor는 repository GitHub Release와 HTTPS account 경계다.
- public installer도 release asset이며, 동일 tag의 distribution module과 exact version을
  내장한다. `raw main`의 코드와 latest archive를 한 invocation에서 섞지 않는다.
- root `install.sh`는 과거 raw URL을 위한 latest-release redirect만 수행한다.
- bootstrap과 updater는 archive 절대 경로, `..` escape, archive 밖 symlink/hardlink,
  special file을 거부하고 private staging에서만 해제한다.
- managed root는 XDG data 아래 `releases/<version>`에 publish되고 `current` symlink와
  PATH launcher는 검증·activation 성공 뒤 atomic replace한다.
- update는 이전 managed release를 source로 쓰는 `packaged` runtime만 선택한다.
  linked 또는 foreign source runtime은 명시적으로 skip하며 Git 동작을 수행하지 않는다.
- multi-runtime activation은 invocation rollback을 사용한다. 이후 current/state commit이
  실패하면 이전 release를 재활성화하고 pointer/state를 복구한다.
- stable 자동 업데이트는 Linux systemd user timer 또는 macOS LaunchAgent를 사용한다.
  scheduler가 없는 환경은 설치를 실패시키지 않고 manual 상태와 명령을 보고한다.
- scheduler는 설치 시 선택된 HOME/XDG, harness data/state/bin, Codex/Claude runtime
  home override를 고정해 background update가 다른 설치를 보지 않게 한다. Version pin은
  state에 보존되며 `--auto` 확인이 latest로 승격하지 않는다.
- update가 파일을 교체해도 이미 시작한 Codex·Claude Code·OpenCode session이 지침을
  다시 읽었다고 주장하지 않는다. 결과는 runtime별 `session_action`을 그대로 반환한다.

### CLI 및 상태

- `harness update [--version <tag>]`는 managed release에서는 network updater, checkout에서는
  기존 local drift/reapply 동작을 수행한다.
- `harness auto-update status|enable|disable`은 scheduler 상태를 관리한다.
- distribution state는 version, repository, archive checksum, release root, profile,
  managed runtimes, scheduler 상태, last check를 XDG state에 기록한다.
- `HARNESS_VERSION`, `HARNESS_PROFILE`, `HARNESS_RUNTIME`, `HARNESS_NO_AUTO_UPDATE`와 CLI
  옵션으로 pin/profile/runtime/자동 갱신을 명시할 수 있다.

### 수용 기준

- fixture release에서 clone 없이 bootstrap→packaged activation→launcher 실행이 통과한다.
- public installer asset과 archive가 동일 tag임을 검증하고 다른 version override를 거부한다.
- 같은 version update는 no-op이고 새 version은 staging 검증 뒤 pointer/runtime을 전환한다.
- checksum mismatch, path traversal, outside symlink, activation failure, state commit failure가
  새 release를 활성 상태로 남기지 않는다.
- linked runtime과 foreign source는 자동 update 전후 source/working tree가 byte-for-byte 같다.
- scheduler enable/disable/status가 isolated HOME에서 실제 user unit/plist를 생성·제거하고,
  scheduler command 실패는 명시적 manual fallback으로 보고된다.
- 기존 runtime activation/profile/extension regression과 generated projection 검사가 유지된다.

## 10. 순서와 의존성

```text
Phase 1: source → runtime activation truth
        ↓ one active source and explicit refresh boundary
Phase 2: canonical manifest → generated projection → profiles
        ↓ stable local product surface
Phase 3: optional external extension bridge
        ↓ stable local product behavior
Phase 4: release bootstrap → managed packaged update
```

- 무엇이 실제로 실행되는지 모르는 상태에서 generator나 plugin을 추가하면 drift를 확대하므로 activation contract가 최우선이다.
- Phase 2가 stable local product surface를 고정해야 외부 extension이 core를 오염시키지 않는다.
- 각 Phase는 별도 `autopilot-code` cycle과 commit/rollback 경계를 가진다.

## 11. 고정 결정과 열린 결정

### 고정 결정

1. Phase 1은 Codex 전용이 아닌 Codex·Claude Code·OpenCode 공통 계약이다.
2. maintainer 기본은 `linked`, 제3자 배포만 `packaged`다.
3. plugin은 core runtime dependency가 아니며 native+plugin 동시 활성화를 금지한다.
4. network, marketplace, package manager는 core activation 경로에서 제외한다.
5. runtime별 reload 차이를 숨기지 않고 status에 표시한다.
6. 구현 순서는 Phase 1→2→3이며 종료 게이트를 건너뛰지 않는다.
7. 공통 CLI는 기존 `tools/install/harness.sh` → `installer.py`에
   `runtime activate|status|refresh|doctor`로 둔다.
8. packaged 형식은 archive/plugin이 아니라 runtime별 harness state 아래 checksum 고정
   local bundle이며 linked와 같은 native discovery surface를 사용한다.
9. Phase 1 runtime activation은 global-only이며 project scope는 silent fallback 없이
   unsupported로 보고한다.
10. 신규 activation 기본 profile은 `builder`다. `starter`와 `full`은 명시적으로 선택한다.
11. canonical machine source는 `harness-manifest.json`이며 root `manifest.json`과 runtime metadata는 generated output이다.
12. core projection의 단일 build/check entrypoint는 `tools/generate.py`다. marketplace bundle generator는 이 경로 밖에 둔다.
13. extension v1 source는 local directory 또는 그 directory를 포함하는 existing local Git checkout뿐이다.
14. extension canonical id는 `external/<publisher>/<skill>`, native discovery id는 readable prefix + canonical-id hash suffix의 64자 이하 physical id다.
15. extension state/snapshot은 XDG state/data 아래 harness-owned 영역에 있고 built-in manifest·source와 분리한다.
16. v1은 Markdown instruction skill만 projection하며 script/hook/MCP/connector/plugin/package를 활성화하지 않는다.
17. package dependency가 있으면 install을 시도하지 않고 `external-dependency-required`로 중단한다.
18. extension 실패와 drift는 core verify/runtime doctor의 성공 조건과 격리한다.
19. add/update/remove는 multi-runtime transaction과 ownership preflight를 적용한다.
20. remote fetch, marketplace, archive, dependency resolver, 실행 surface 승인 UI는 v1 범위 밖이다.
21. 일반 사용자 기본은 Git checkout이 아니라 checksum 검증된 managed packaged release다.
22. 유지보수자 기본은 계속 linked checkout이며 release updater는 linked source를 fetch/pull/repoint하지 않는다.
23. release transport는 GitHub Releases이고 activation core·built-in execution과 network failure domain을 분리한다.
24. 자동 update는 supported OS user scheduler를 사용하며 새 session/restart 필요성을 숨기지 않는다.
25. public bootstrap code와 archive는 동일 immutable GitHub repository와 release tag에서 오며 raw main은 public install trust path가 아니다.
26. release-relevant `main` 변경은 deterministic SemVer policy로 자동 배포한다. 명시적 breaking/feature signal은 major/minor, 나머지 동작 변경은 patch이고 docs/report/CI/test-only는 skip한다.

### 열린 결정

없음. Phase 3 v1 source, namespace, projection, state, security, parity, rollback 계약을 위에서 고정했다.

## 12. 주요 위험과 완화

| 위험 | 완화 |
|---|---|
| 즉시 파일 반영과 session 반영을 혼동 | projection freshness와 session action을 별도 필드로 둔다. |
| linked mode가 다른 worktree를 가리킴 | absolute source root, git common-dir, revision을 status와 activation record에 고정한다. |
| plugin 제거가 배포 기능까지 약화 | Phase 1은 native local bundle로 재현성을 제공하고 plugin export/배포는 core 밖의 명시적 선택 기능으로 남긴다. |
| OpenCode parity를 추정으로 과장 | 공식 surface가 없는 항목은 unsupported/restart fallback으로 기록한다. |
| manifest가 또 하나의 중복 source가 됨 | metadata ownership map과 generated-field boundary를 schema에 포함한다. |
| 외부 skill supply-chain 위험 | offline/local source 우선, inspect-first, provenance pin, 실행 surface 별도 승인을 강제한다. |
| release archive supply-chain/path escape | GitHub release asset의 SHA-256 sidecar 검증, safe extraction, immutable version root, staged publish를 강제한다. |
| raw-main bootstrap과 release archive의 버전 mismatch | public installer를 self-contained release asset으로 만들고 exact embedded tag만 설치한다. |
| `main`의 배포 동작과 latest release가 다시 분리 | stable tag 이후 release-relevant diff를 매 push 판정하고 검증한 exact commit을 tag+publish하는 단일 직렬 workflow를 사용한다. |
| 자동 update가 개발 checkout을 덮어씀 | managed state + packaged source match를 동시에 만족하는 runtime만 갱신하고 Git 명령을 금지한다. |
| update 뒤 현재 session도 갱신됐다고 오인 | activation 결과의 runtime별 `session_action`을 설치·update 출력과 README에 유지한다. |

## 13. 다음 구현 단위

- Cycle 1 — 완료: 세 runtime activation census, 상태 schema, linked activate/status/doctor, duplicate cleanup, rollback.
- Cycle 2 — 완료: canonical manifest/generator, generated consumer migration, profile resolver와 quickstart.
- Cycle 3 — 완료: built-in pack 계약을 사용하는 offline extension lifecycle, provenance/security/parity.
- Cycle 4 — 완료: clone 없는 release bootstrap, packaged automatic updater, release workflow, 공개 README 단순화, `v1.0.0` 공개.
- Cycle 4.1 — 완료: bootstrap code/archive 동일 repository/tag 결속과 `v1.0.1` patch release.
- Cycle 4.2 — 완료: release-relevant `main` 변경의 deterministic SemVer 판정, 검증 후 tag+release 자동화, 명시적 prerelease override.

Cycle 3 착수 전 `autopilot-code`가 세 runtime의 현재 extension surface와 local-path security boundary를 공식 문서와 로컬 realization에서 다시 확인하고 이 PRD를 source of truth로 읽어야 한다.
