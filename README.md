# Agent Harness

> **Portable workflows. Native runtimes. One local source of truth.**

Claude Code, Codex, OpenCode에서 조사·기획·구현·검증을 같은 방식으로 끝까지 닫는 로컬 agent harness입니다. 공통 계약은 한 번 정의하고, 각 런타임에는 그 런타임이 실제로 발견하는 skill·agent·hook 표면만 생성해 활성화합니다.

```text
"로그인 API를 구현하고 테스트한 뒤 변경 보고서까지 남겨줘."
                                  ↓
       plan → execute → test → report + durable evidence
```

## Quick start

Python 3.10+, Git, 사용할 런타임 CLI가 필요합니다.

```bash
git clone https://github.com/dmlguq456/agent_setting.git ~/agent_setting
cd ~/agent_setting

./tools/install/harness.sh runtime activate \
  --runtime all \
  --mode linked \
  --profile builder

./tools/install/harness.sh runtime doctor --runtime all --strict
```

이후에는 PATH에 설치된 `harness`로 관리합니다.

```bash
harness runtime status --runtime all
harness runtime refresh --runtime all
harness runtime doctor --runtime all --strict
```

`builder`가 기본 프로필이라 `--profile`을 생략해도 같은 구성이 활성화됩니다. 다른 머신에 고정 revision을 전달하려면 `--mode packaged`를 사용하세요. 이 경로도 marketplace나 원격 package를 호출하지 않습니다.

## Choose your profile

프로필은 런타임에 노출할 capability와 role의 크기를 정합니다. dependency closure는 자동으로 포함되고, guard·bootstrap·memory-scout 같은 kernel 표면은 모든 프로필에서 유지됩니다.

| 프로필 | 적합한 용도 | Capability | Role | Mode |
|---|---|---:|---:|---:|
| `starter` | 핵심 코드 파이프만 가볍게 시작 | 6 | 4 | 13 |
| `builder` **default** | 소프트웨어 개발 + 분석·운영·기억 | 14 | 7 | 26 |
| `full` | 연구·문서·디자인까지 전체 harness | 27 | 8 | 26 |

```bash
harness runtime activate --runtime codex --mode linked --profile starter
harness runtime refresh --runtime all --profile full
```

활성화 결과에는 선택된 profile, capability/role/mode 목록, manifest digest가 기록됩니다. 따라서 “무엇이 설치됐는지”를 README가 아니라 런타임 상태로 검증할 수 있습니다.

## What makes it different

- **작업을 끝까지 닫습니다.** 조사나 코드 생성에서 멈추지 않고 spec, plan, 실행, 테스트, 보고를 연결하고 evidence를 남깁니다.
- **런타임보다 계약이 먼저입니다.** workflow, role, artifact, memory, intensity, QA 의미는 portable core가 소유하고 adapter는 native surface로만 번역합니다.
- **필요한 만큼만 노출합니다.** `starter`/`builder`/`full`이 skill metadata와 agent discovery 크기를 실제로 줄입니다.
- **판단 가능한 설치 상태를 제공합니다.** source 절대경로, revision, digest, profile, duplicate, freshness, session action을 `status`와 `doctor`에서 확인합니다.
- **세션을 넘어 결정이 이어집니다.** project working memory, durable memory, 사용자 profile을 공통 recall 경로로 연결합니다.
- **안전 규칙을 코드로 검사합니다.** spec grounding, artifact 순서, git 상태, projection drift를 결정론적 guard와 테스트로 검증합니다.

## Use it like this

명령 이름을 외울 필요는 없습니다. 원하는 결과와 제약을 자연어로 말하면 runtime-native skill이 관련 pipeline을 선택합니다.

> “이 저장소를 분석하고 다음 기능을 위한 PRD를 만들어줘.”

> “로그인 API를 구현하고 테스트한 다음 변경 보고서까지 남겨줘.”

> “이 논문들과 실험 코드를 조사해서 재현 계획을 세워줘.”

> “현재 화면을 실제로 렌더해서 디자인을 다듬고 개발 handoff를 만들어줘.”

> “지난 작업 결정을 찾아서 이 프로젝트의 기존 명명 규칙대로 고쳐줘.”

전체 진입점은 [capabilities/README.md](capabilities/README.md), 역할은 [roles/README.md](roles/README.md)에서 확인할 수 있습니다.

## How it works

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

- `core/` — workflow, artifact, QA, memory, git/worktree 계약
- `harness-manifest.json` — capability, role, mode, pack, profile의 canonical machine contract
- `capabilities/`, `roles/` — 사람이 읽는 portable behavior source
- `adapters/` — 런타임별 native projection과 bridge
- `tools/install/` — runtime-owned state를 건드리지 않는 activation lifecycle
- `.agent_reports/` — spec, plan, test evidence, handoff가 쌓이는 project artifact root

`linked`는 maintainer 기본값으로 repo 변경이 discovery path에 즉시 보입니다. `packaged`는 immutable local bundle을 만들며 `runtime refresh` 전까지 active revision을 유지합니다. 파일 변경이 이미 보이는 것과 현재 대화가 새 instruction을 다시 읽는 것은 별개이므로, `runtime status`가 런타임별 재호출·새 세션·restart 필요 여부를 `session_action`으로 표시합니다.

## Native first, plugins optional

기본 제품 경로는 local native projection입니다. Codex/Claude marketplace bundle은 배포 실험을 위한 선택적 산출물이며 생성, 활성화, doctor의 성공 조건이 아닙니다. OpenCode의 local guard plugin은 외부 package가 아니라 native hook bridge입니다.

이 경계 덕분에 기본 설치는 다음을 요구하지 않습니다.

- marketplace 등록
- plugin cache 또는 registry
- npm package fetch
- 외부 MCP·connector·API
- Codex/Claude credentials, sessions, logs, local DB 변경

동일 harness의 native+plugin 중복 discovery는 허용하지 않으며 strict doctor가 실패로 처리합니다.

## Runtime support

| 런타임 | `linked` projection | `packaged` projection |
|---|---|---|
| Claude Code | skills, agents, commands, hooks | 같은 native surface의 immutable bundle |
| Codex | skills, custom agents, modes, hooks | 같은 native surface의 immutable bundle |
| OpenCode | skills, agents, commands, local guard plugin | 같은 native surface의 immutable bundle |

런타임별 지원 차이는 숨기지 않습니다. installer는 미지원 표면을 `SKIP`과 이유로 보고하며, credentials, sessions, DB, logs, foreign cache는 관리 범위 밖에 둡니다. 세부 매핑은 [INSTALL_LAYOUT.md](INSTALL_LAYOUT.md)에서 확인하세요.

## Develop the harness

공통 정의를 바꾼 뒤에는 단일 generator로 모든 core projection을 갱신하고 drift를 확인합니다.

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

Marketplace bundle generator는 이 경로에 포함되지 않습니다. root README의 가치 제안과 설명은 사람이 소유하고, machine contract와 runtime projection만 생성합니다.

## Documentation

| 목적 | 문서 |
|---|---|
| 전체 사용법 | [MANUAL.md](MANUAL.md) |
| capability와 role | [capabilities/README.md](capabilities/README.md), [roles/README.md](roles/README.md), [roles/MODES.md](roles/MODES.md) |
| routing과 artifact | [core/WORKFLOW.md](core/WORKFLOW.md), [core/CONVENTIONS.md](core/CONVENTIONS.md) |
| git, worktree, dispatch | [core/OPERATIONS.md](core/OPERATIONS.md) |
| memory와 recall | [core/MEMORY.md](core/MEMORY.md) |
| hook과 설계 원칙 | [core/HOOKS.md](core/HOOKS.md), [core/DESIGN_PRINCIPLES.md](core/DESIGN_PRINCIPLES.md) |
| 설치와 runtime projection | [INSTALL_LAYOUT.md](INSTALL_LAYOUT.md) |
