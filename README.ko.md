<h1 align="center">Agent Harness</h1>

<p align="center"><strong>이식 가능한 워크플로. 런타임 네이티브 통합. 하나의 로컬 기준점.</strong></p>

<p align="center">Claude Code, Codex, OpenCode를 위한 로컬 우선 워크플로 계층입니다.</p>

<p align="center">
  <img alt="Claude Code: 네이티브" src="https://img.shields.io/badge/Claude_Code-native-D97757?style=flat-square">
  <img alt="Codex: 네이티브" src="https://img.shields.io/badge/Codex-native-111827?style=flat-square">
  <img alt="OpenCode: 네이티브" src="https://img.shields.io/badge/OpenCode-native-2563EB?style=flat-square">
  <img alt="설치: 로컬 우선" src="https://img.shields.io/badge/installation-local--first-059669?style=flat-square">
</p>

<p align="center"><a href="README.md">English</a> · <strong>한국어</strong></p>

> 이 문서는 유지보수 기준인 [README.md](README.md)의 한국어 번역입니다.
> 명령, 경로, 식별자와 기계 판독 계약은 영문 원문을 기준으로 합니다.

Agent Harness는 지원되는 코딩 에이전트 런타임에서 조사, 계획, 구현, 검증
작업을 일관되게 마무리합니다. 이는 **특정 단일 런타임을 위한 설정이
아닙니다**. 공유 계약은 한 번만 정의하고, 각 런타임이 실제로 발견하는
네이티브 Skill, Agent, hook, mode, command 표면에만 투영합니다.

```text
"로그인 API를 구현하고 테스트한 뒤 변경 보고서까지 남겨줘."
                                  ↓
       계획 → 실행 → 테스트 → 보고 + 지속 가능한 근거
```

## 한눈에 보기

| 완결된 워크플로 | 런타임 네이티브 제공 | 검증 가능한 상태 |
|---|---|---|
| 조사, 명세, 계획, 구현, 테스트, 보고서를 하나의 흐름으로 연결합니다. | 특정 벤더를 흉내 내지 않고 각 런타임의 네이티브 표면에 공유 동작을 투영합니다. | 소스, 리비전, 프로필, digest, 중복, 최신성과 필요한 세션 조치를 확인합니다. |

## 빠른 시작

### 요구 사항

- Python 3.10 이상
- Git
- 활성화하려는 각 런타임의 CLI

### 설치

```bash
git clone https://github.com/dmlguq456/agent_setting.git ~/agent_setting
cd ~/agent_setting

./tools/install/harness.sh runtime activate \
  --runtime all \
  --mode linked \
  --profile builder

./tools/install/harness.sh runtime doctor --runtime all --strict
```

활성화 후에는 `PATH`에 등록된 `harness` 명령으로 설치를 관리합니다.

```bash
harness runtime status --runtime all
harness runtime refresh --runtime all
harness runtime doctor --runtime all --strict
```

`builder`가 기본 프로필이므로 `--profile`을 생략해도 같은 구성이
활성화됩니다. 다른 장비에 불변 리비전을 전달하려면 `--mode packaged`를
사용합니다. 두 모드 모두 marketplace나 원격 package에 의존하지 않습니다.

## 프로필 선택

프로필은 각 런타임이 발견할 capability와 role의 범위를 조절합니다. 의존성
폐쇄는 자동으로 포함되며 guard, bootstrap 지침, `memory-scout` 같은 kernel
표면은 모든 프로필에서 유지됩니다.

| 프로필 | 적합한 용도 | Capability | Role | Mode |
|---|---|---:|---:|---:|
| `starter` | 가벼운 핵심 코드 파이프라인 | 6 | 4 | 13 |
| `builder` **기본값** | 소프트웨어 개발, 분석, 운영, 메모리 | 14 | 7 | 26 |
| `full` | 조사, 문서, 디자인을 포함한 전체 harness | 27 | 8 | 26 |

```bash
harness runtime activate --runtime codex --mode linked --profile starter
harness runtime refresh --runtime all --profile full
```

활성화 과정은 선택한 프로필, capability, role, mode 목록과 manifest digest를
기록합니다. 따라서 README의 설명을 그대로 믿는 대신 런타임 상태에서 실제
설치 내용을 검증할 수 있습니다.

## Agent Harness를 쓰는 이유

- **작업 사이클 전체를 닫습니다.** 조사와 코드 생성이 명세, 계획, 실행,
  테스트, 보고서와 지속 가능한 근거로 이어집니다.
- **런타임보다 계약을 우선합니다.** portable core가 workflow, role,
  artifact, memory, intensity, assurance 의미를 소유하고 adapter는 이를
  네이티브 런타임 표면으로만 번역합니다.
- **필요한 것만 노출합니다.** `starter`, `builder`, `full`은 문서상 구분에
  그치지 않고 실제 Skill metadata와 Agent discovery 범위를 줄입니다.
- **설치 상태를 검사할 수 있습니다.** `status`와 `doctor`가 절대 source
  path, revision, digest, profile, duplicate, freshness와 필요한 session
  action을 보고합니다.
- **세션 사이에 결정을 이어갑니다.** 프로젝트 working memory, durable
  memory, user profile이 하나의 보호된 retrieval 경로를 공유합니다.
- **안전 규칙을 실행 가능하게 만듭니다.** 결정적 guard와 test가 spec
  grounding, artifact order, git state, projection drift를 검증합니다.

## 자연어로 사용하기

명령 이름을 외울 필요가 없습니다. 원하는 결과와 제약을 평소 사용하는
소통 언어로 설명하세요. 런타임 네이티브 Skill이 관련 파이프라인을 선택하고,
사용자향 출력은 이 README의 언어를 물려받지 않고 대화, 대상 독자 또는
산출물 언어를 따릅니다.

> “이 저장소를 분석하고 다음 기능을 위한 PRD를 만들어줘.”

> “로그인 API를 구현하고 테스트한 뒤 변경 보고서까지 남겨줘.”

> “논문과 실험 코드를 검토하고 재현 계획을 만들어줘.”

> “현재 화면을 렌더링하고 디자인을 다듬은 뒤 개발 handoff를 만들어줘.”

> “이전 결정을 찾아서 이 프로젝트의 기존 naming convention을 적용해줘.”

전체 진입점은 [capabilities/README.md](capabilities/README.md), portable role
모델은 [roles/README.md](roles/README.md)를 참고하세요.

## 작동 방식

```text
                       harness-manifest.json
                    capability · role · profile
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
      Claude Code native   Codex native    OpenCode native
      skills / agents      skills / agents  skills / agents
      hooks / commands     hooks / modes    commands / plugins
             └─────────────────┼─────────────────┘
                               │
              activate · status · refresh · doctor
```

| 계층 | 책임 |
|---|---|
| `core/` | Workflow, artifact, assurance, memory, git/worktree 계약 |
| `harness-manifest.json` | Capability, role, mode, pack, profile의 canonical machine contract |
| `capabilities/`, `roles/` | 사람이 읽는 portable behavior source |
| `adapters/` | 각 런타임의 네이티브 projection과 bridge |
| `tools/install/` | 런타임 소유 상태를 건드리지 않는 activation lifecycle |
| `.agent_reports/` | Spec, plan, test evidence, handoff를 위한 project artifact |

`linked`는 maintainer 기본값입니다. 저장소 변경이 discovery path에 즉시
나타납니다. `packaged`는 불변 로컬 bundle을 만들고 `runtime refresh` 전까지
활성 리비전을 유지합니다. 파일 노출과 지침 재로딩은 서로 다른 문제이므로
`runtime status`는 각 런타임에 재호출, 새 세션 또는 재시작 중 무엇이 필요한지
`session_action`으로 알려줍니다.

## 런타임 지원

| 런타임 | `linked` projection | `packaged` projection |
|---|---|---|
| Claude Code | Skill, Agent, command, hook | 동일한 네이티브 표면의 불변 bundle |
| Codex | Skill, custom agent, mode, hook | 동일한 네이티브 표면의 불변 bundle |
| OpenCode | Skill, Agent, command, local guard plugin | 동일한 네이티브 표면의 불변 bundle |

런타임 차이는 숨기지 않고 보고합니다. installer는 지원하지 않는 표면을
이유와 함께 `SKIP`으로 표시하며 credential, session, database, log, 외부
cache는 소유하지 않습니다. 자세한 매핑은
[INSTALL_LAYOUT.md](INSTALL_LAYOUT.md)를 참고하세요.

## 네이티브 우선, 플러그인은 선택 사항

기본 제품 경로는 로컬 네이티브 projection입니다. Codex와 Claude marketplace
bundle은 선택 가능한 배포 채널이며 생성, 활성화 또는 doctor 성공의 선행
조건이 아닙니다. OpenCode의 local guard plugin은 외부 package가 아니라
네이티브 hook bridge입니다.

따라서 기본 설치에는 다음이 필요하지 않습니다.

- marketplace 등록
- plugin cache 또는 registry
- npm package fetch
- 외부 MCP server, connector 또는 API
- Codex나 Claude의 credential, session, log 또는 local database 변경

같은 harness를 native와 plugin 경로에서 중복 발견하는 구성은 금지되며 strict
doctor 검증이 실패합니다.

## Harness 개발

공유 정의를 변경한 후에는 모든 생성 projection을 갱신하고 drift를
검사합니다.

```bash
python3 tools/generate.py
python3 tools/generate.py --check

./tools/generated-projections.test.sh
./tools/install/profile-activation.test.sh
./tools/install/runtime-activation.test.sh
./tools/skill-conformance/check.sh
./tools/check-adaptation-boundary.sh
adapters/codex/bin/preflight.sh doctor
```

Marketplace bundle 생성은 이 경로에 포함되지 않습니다. 루트 README의 가치
제안과 설명은 사람이 관리하며, machine contract와 runtime projection만
자동으로 생성됩니다.

## 문서

| 목적 | 문서 |
|---|---|
| 전체 사용 안내 | [MANUAL.md](MANUAL.md) |
| 설치와 런타임 projection | [INSTALL_LAYOUT.md](INSTALL_LAYOUT.md) |
| Capability와 role | [capabilities/README.md](capabilities/README.md), [roles/README.md](roles/README.md), [roles/MODES.md](roles/MODES.md) |
| Routing과 artifact | [core/WORKFLOW.md](core/WORKFLOW.md), [core/CONVENTIONS.md](core/CONVENTIONS.md) |
| Git, worktree, dispatch | [core/OPERATIONS.md](core/OPERATIONS.md) |
| Memory와 recall | [core/MEMORY.md](core/MEMORY.md) |
| Hook과 design principle | [core/HOOKS.md](core/HOOKS.md), [core/DESIGN_PRINCIPLES.md](core/DESIGN_PRINCIPLES.md) |
