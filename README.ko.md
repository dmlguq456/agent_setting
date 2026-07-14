<h1 align="center">Agent Harness</h1>

<p align="center"><strong>Claude Code, Codex, OpenCode에서 이어지는 하나의 완결된 에이전트 워크플로.</strong></p>

<p align="center">Claude Code, Codex, OpenCode를 위한 로컬 우선 워크플로 계층입니다.</p>

<p align="center">
  <img alt="Claude Code: 네이티브" src="https://img.shields.io/badge/Claude_Code-native-D97757?style=flat-square">
  <img alt="Codex: 네이티브" src="https://img.shields.io/badge/Codex-native-111827?style=flat-square">
  <img alt="OpenCode: 네이티브" src="https://img.shields.io/badge/OpenCode-native-2563EB?style=flat-square">
  <img alt="설치: 관리형 릴리스" src="https://img.shields.io/badge/installation-one--line_release-059669?style=flat-square">
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

## Agent Harness를 쓰는 이유

- **작업 사이클 전체를 닫습니다.** 조사, 명세, 계획, 구현, 테스트, 보고서와
  지속 가능한 근거가 한 흐름으로 이어집니다.
- **세 런타임에서 하나의 계약을 유지합니다.** 공유 동작을 Claude Code,
  Codex, OpenCode가 실제로 발견하는 표면에 투영합니다.
- **무엇이 실행 중인지 확인합니다.** 활성 release 또는 checkout, profile,
  revision, freshness, duplicate와 필요한 session action을 검사합니다.
- **작게 시작해서 확장합니다.** Capability를 fork하거나 별도 setup을 관리하지
  않고 `starter`, `builder`, `full`을 선택합니다.
- **결정을 안전하게 이어갑니다.** Durable memory와 실행 가능한 guard가 기존
  convention을 보존하고 spec, artifact, git, projection 경계를 확인합니다.

## 빠른 시작

### 요구 사항

- Python 3.10 이상
- `curl` 또는 `wget`
- 활성화하려는 각 런타임의 CLI

### 설치

```bash
curl -fsSL https://github.com/dmlguq456/agent_setting/releases/latest/download/install.sh | sh
~/.local/bin/harness runtime doctor --runtime all --strict
```

installer와 distribution logic은 동일한 immutable Release tag에서 오며, 그 exact
tag의 archive를 SHA-256으로 확인한 뒤 설치합니다. 세 런타임에 `builder`
profile의 불변 packaged bundle을 활성화하고, OS가 지원하면
user-level 일일 update 확인도 등록합니다. Runtime credential, session, log,
database는 건드리지 않습니다.

`~/.local/bin`을 `PATH`에 넣은 뒤에는 다음처럼 관리합니다.

```bash
harness runtime status --runtime all
harness update
harness auto-update status
harness runtime doctor --runtime all --strict
```

`harness update`는 새 release를 staging에서 검증한 뒤 active pointer를
전환하고 실패하면 이전 release로 rollback합니다. 이미 열린 agent session이
자동으로 지침을 다시 읽는 것은 아니므로 update 뒤 `runtime status`에서
재호출, 새 session 또는 restart 필요 여부를 확인하세요.

Checksum sidecar는 전송 또는 asset 손상을 탐지합니다. Publisher 진위의 신뢰
경계는 이 저장소의 GitHub Release와 HTTPS account이며 독립 서명은 아닙니다.

Version 고정 또는 자동 확인 제외:

```bash
curl -fsSL https://github.com/dmlguq456/agent_setting/releases/download/v1.0.1/install.sh | sh -s -- --no-auto-update
```

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

Managed release가 일반 사용자 기본값입니다. `linked`는 maintainer mode로
남습니다. Checkout 변경은 discovery path에 즉시 나타나며 release updater는
그 checkout을 fetch, pull, repoint하지 않습니다. 파일 노출과 지침 재로딩은
서로 다른 문제이므로 `runtime status`는 각 런타임에 재호출, 새 session 또는
restart 중 무엇이 필요한지 `session_action`으로 알려줍니다.

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

## Harness 개발

Maintainer는 managed release 대신 live checkout을 사용할 수 있습니다.

```bash
git clone https://github.com/dmlguq456/agent_setting.git ~/agent_setting
cd ~/agent_setting
./tools/install/harness.sh runtime activate --runtime all --mode linked --profile builder
```

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
