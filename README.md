# Agent Harness

**자연어 한 줄을 조사·기획·구현·검증까지 이어지는 재현 가능한 작업 흐름으로 바꿉니다.**

Agent Harness는 Claude Code, Codex, OpenCode에서 같은 작업 원칙을 쓰기 위한 portable agent harness입니다. 공통 계약은 한곳에서 관리하고, 각 런타임에는 그 런타임이 이해하는 native projection으로 활성화합니다. 제품 전체가 하나의 plugin인 것은 아니며, plugin이나 marketplace는 기본 실행 경로에 필요하지 않습니다.

## 빠른 설치

Python 3.10+, Git, 사용할 런타임 CLI가 필요합니다.

```bash
git clone https://github.com/dmlguq456/agent_setting.git ~/agent_setting
cd ~/agent_setting
./tools/install/harness.sh runtime activate --runtime all --mode linked
./tools/install/harness.sh runtime doctor --runtime all --strict
```

설치가 끝나면 PATH의 `harness` 명령으로 상태와 업데이트를 관리할 수 있습니다.

```bash
harness runtime status --runtime all
harness runtime refresh --runtime all
harness runtime doctor --runtime all --strict
```

다른 머신에 고정 revision을 전달하려면 local packaged mode를 사용합니다. 이 경로도 marketplace나 네트워크를 호출하지 않습니다.

```bash
harness runtime activate --runtime all --mode packaged --source ~/agent_setting
```

`linked`는 maintainer 기본값으로 repo 수정이 discovery path에 즉시 보이고, `packaged`는 `runtime refresh` 전까지 active revision을 바꾸지 않습니다. `native+plugin` 동시 discovery는 금지되며 `runtime doctor --strict`가 중복을 실패로 보고합니다. 자동화에서 구조화 결과가 필요하면 `--json`을 붙이세요. 수동 설치와 소유 경계는 [INSTALL_LAYOUT.md](INSTALL_LAYOUT.md)에 정리되어 있습니다.

## 바로 쓰기

설치 뒤에는 명령 이름을 외우기보다 원하는 결과를 자연어로 말하면 됩니다.

> “이 저장소를 분석하고 다음 기능을 위한 PRD를 만들어줘.”

> “로그인 API를 구현하고 테스트한 다음 변경 보고서까지 남겨줘.”

> “이 논문들과 실험 코드를 조사해서 재현 계획을 세워줘.”

> “현재 화면을 실제로 렌더해서 디자인을 다듬고 개발 handoff를 만들어줘.”

> “지난 작업 결정을 찾아서 이 프로젝트의 기존 명명 규칙대로 고쳐줘.”

하네스는 현재 저장소와 `.agent_reports/`를 읽어 필요한 capability, role, guard, 검증 단계를 고릅니다. 전체 capability 목록은 [capabilities/README.md](capabilities/README.md)에서 볼 수 있습니다.

## 핵심 효익

- **끝까지 닫히는 작업 흐름** — 조사와 분석에서 spec, plan, 실행, 테스트, 보고까지 산출물이 한 방향으로 이어집니다.
- **런타임이 바뀌어도 유지되는 계약** — workflow, role, artifact, memory, intensity와 검증 의미는 portable core가 소유하고 runtime adapter는 native surface로 번역합니다.
- **판단보다 코드로 지키는 안전장치** — artifact 순서, git 상태, spec grounding, projection drift를 hook과 결정론적 검사로 확인합니다.
- **세션을 넘어가는 작업 기억** — project working memory, durable memory, 사용자 profile을 공통 store와 recall 경로로 연결합니다.
- **보이는 검증** — active source의 절대경로·revision·digest·중복·session action을 `harness runtime status`와 `doctor`의 exit status로 확인할 수 있습니다.

## 런타임별 배포 차이

세 런타임은 지원하는 확장 표면이 다릅니다. installer가 차이를 숨기지 않고 설치·검증 결과에 `SKIP` 또는 제한 사유를 표시합니다.

| 런타임 | `linked` 기본 | `packaged` 경계 | 권장 진입 |
|---|---|---|---|
| **Claude Code** | native skills·agents·commands·hooks를 local repo에 연결 | immutable local bundle을 같은 native 경로에 연결 | `harness runtime activate --runtime claude --mode linked` |
| **Codex** | native skills·custom agents·modes·hooks를 local repo에 연결 | immutable local bundle을 같은 native 경로에 연결 | `harness runtime activate --runtime codex --mode linked` |
| **OpenCode** | 복수형 `skills/agents/commands/plugins`를 local repo에 연결 | immutable local bundle을 같은 native 경로에 연결 | `harness runtime activate --runtime opencode --mode linked` |

Plugin은 Phase 1 활성화 형식이 아닙니다. 두 mode 모두 runtime-native discovery만 사용하며, 기존 Codex/Claude harness plugin registry와 cache 및 OpenCode의 명시적 harness npm 항목은 네트워크 호출 없이 비활성화합니다. Claude hook은 기존 `settings.json`의 사용자 키를 보존해 병합합니다. credentials, sessions, DB, logs, foreign cache는 쓰지 않습니다. 세부 지원 범위는 [Claude adapter](adapters/claude/README.md), [Codex adapter](adapters/codex/README.md), [OpenCode adapter](adapters/opencode/README.md)를 참고하세요.

파일 변경이 보이는 것과 현재 대화가 새 instruction을 읽는 것은 별개입니다. `runtime status`의 `freshness`와 runtime별 `session_action`이 재호출·새 세션·restart 필요 여부를 따로 표시합니다.

## 작동 구조

```text
자연어 요청
   ↓
portable contract
core/ + capabilities/ + roles/
   ↓  deterministic generators
runtime-native projections
Claude native · Codex native · OpenCode conventions
   ↓  harness runtime activate / status / doctor
runtime home + project .agent_reports/
```

- `core/`는 workflow, artifact, QA, memory, git/worktree 같은 portable 규칙을 소유합니다.
- `capabilities/`와 `roles/`는 “무슨 일을 어떤 역할이 맡는가”를 정의합니다.
- `adapters/`는 각 런타임의 plugin, skill, agent, mode, hook, config 경계로 투영합니다.
- `tools/install/`은 설치한 표면만 관리하고 사용자 credentials, sessions, local DB와 기존 config를 보존합니다.
- root README의 가치 제안·정보 순서·예시는 사람이 소유합니다. 생성 가능한 manifest와 runtime projection만 코드가 생성·검증합니다.

## 더 깊이 읽기

| 목적 | 문서 |
|---|---|
| 전체 흐름을 한 번에 이해 | [MANUAL.md](MANUAL.md) |
| capability와 role 찾기 | [capabilities/README.md](capabilities/README.md), [roles/README.md](roles/README.md), [roles/MODES.md](roles/MODES.md) |
| 라우팅과 산출물 규칙 | [core/WORKFLOW.md](core/WORKFLOW.md), [core/CONVENTIONS.md](core/CONVENTIONS.md) |
| git, worktree, dispatch | [core/OPERATIONS.md](core/OPERATIONS.md) |
| memory와 recall | [core/MEMORY.md](core/MEMORY.md) |
| hook·설계 원칙 | [core/HOOKS.md](core/HOOKS.md), [core/DESIGN_PRINCIPLES.md](core/DESIGN_PRINCIPLES.md) |
| 설치·runtime projection | [INSTALL_LAYOUT.md](INSTALL_LAYOUT.md) |

## 개발과 검증

정의나 adapter projection을 바꿨다면 해당 생성기를 먼저 실행한 뒤 아래 결정론적 검사를 통과시킵니다.

```bash
python3 tools/build-manifest.py --check

adapters/claude/bin/sync-native-plugin.py --check
adapters/codex/bin/sync-native-skills.py --check
adapters/codex/bin/sync-native-plugin.py --check
adapters/codex/bin/sync-native-agents.py --check
adapters/codex/bin/sync-native-modes.py --check
adapters/opencode/bin/sync-native-skills.py --check
adapters/opencode/bin/sync-native-commands.py --check
adapters/opencode/bin/sync-native-agents.py --check

tools/check-adaptation-boundary.sh
tools/skill-conformance/check.sh
adapters/codex/bin/preflight.sh doctor
./tools/install/runtime-activation.test.sh
./tools/install/harness.sh verify
```

`sync-native-skills.py` 같은 이름은 native projection generator를 뜻합니다. 사람이 쓴 README prose를 자동 재생성하는 기능이 아닙니다.
