# harness-installer — Spec (PRD)

> mode: **cli** (하네스 배포 표면 — managed release + linked maintainer installer) · 작성 2026-07-12 · v1 · v2 (2026-07-13) · v3 (2026-07-13) · v4 (2026-07-14) · **v5 (2026-07-14)**: bootstrap 코드와 archive를 동일 release tag에 결속. 구 버전 = `_internal/versions/v4/prd.md`
> 컴포넌트: `agent_setting` repo 의 **배포·설치 표면** — 일반 사용자는 검증된 managed release, 유지보수자는 linked checkout으로 Claude Code·Codex·OpenCode를 설치·검증·갱신한다. plugin/marketplace는 선택적 compatibility surface이며 공개 기본 경로가 아니다. `spec/harness-layer-sync/`(내부 canonical 바인딩)와 **형제·interlock** 관계의 독립 청사진 — 이 폴더(`spec/harness-installer/`)가 자체 SoT.
> 입력(1순위 근거):
> - research `.agent_reports/research/cross-platform-agent-frameworks/` — `05_deployment.md`(3단 배포 골격·cost model), `06_implementation.md`(채택 후보 1 = GSD hash-manifest), `cards/{gsd,claude-code-official-plugins,multi-harness-projection,claude-flow}.md`
> - 현행 실측(2026-07-12): `INSTALL_LAYOUT.md`(수동 symlink 레시피 + Migration Order 수동 검증 절차), `adapters/codex/plugin-marketplace/`(Codex plugin 채널 기존재), `adapters/claude/bin/install-windows.sh`(Windows 일회성 installer 선례), `tools/fleet/`(runtime-neutral zero-dep CLI 선례), `tools/build-manifest.py`(`--check` drift 생성기)
> - interlock spec: `.agent_reports/spec/harness-layer-sync/prd.md` v2 — §3(canonical 바인딩)·§3.2(GSD 실코드 정독 게이트)·§3.3(생성기 재사용)
> - **runtime-currentness 검증(2026-07-12, 본 spec 작성 중 공식 문서 재확인)**: Claude Code `code.claude.com/docs/en/{plugins,plugins-reference,plugin-marketplaces}` · Codex `developers.openai.com/codex/{plugins,build-plugins,hooks}` + `openai/codex` 소스(`codex-rs/plugin/src/manifest.rs`·`cli/src/main.rs`) · OpenCode `opencode.ai/docs/{config,plugins,skills}` — 주요 사실은 본문 해당 절에 인용, research 카드(7/9)와의 차이는 ⚠️drift 로 명시
> 본 문서는 청사진(PRD). 구현은 autopilot-code (산출물 `plans/`). 사용자 확정(2026-07-12): 새 spec 독립 생성(HLS v3 확장 아님) + **2-채널 하이브리드** 구조.

## 0. 한 줄

**하네스를 한 명령으로 설치·검증·갱신한다.** 소비·새 머신은 각 런타임의 native **plugin 채널**(Claude Code marketplace 신설 · Codex `agent-harness-codex` 승격 · OpenCode config+plugin)로, dev 머신은 **bootstrap installer CLI** 가 symlink projection 을 자동화하고, plugin 이 못 담는 runtime-owned 표면(settings 복사·memory DB 복원·PATH launcher·env 주입·검증)을 처리한다. installer 가 쓴 파일은 **hash-manifest** 로 추적해 사용자 로컬 수정을 감지·보존(`--reapply`)한다. `INSTALL_LAYOUT.md` 의 수동 레시피·수동 검증 절차가 이 CLI 의 `install`/`verify` 로 대체된다.

## 0.5 설계 원칙 ★ cross-cutting

1. **2-채널 하이브리드 (사용자 확정)** — plugin 채널(consume: 새 머신·제3자)과 installer CLI(dev: 본인 머신·repo 개발 흐름)는 **대체가 아니라 병존**. 근거: Claude Code plugin 은 설치 시 `~/.claude/plugins/cache` 로 **복사**되는 모델이라(`cards/claude-code-official-plugins.md` §2) "repo 수정 즉시 반영" dev 흐름과 구조적으로 상충 — GSD 도 같은 이유로 npm installer + Claude plugin 2경로 병존(`cards/gsd.md` §2).
2. **결정론 우선 (DESIGN_PRINCIPLES §0.5)** — 설치·검증·drift 감지·config merge 는 전부 코드. 에이전트 판단 개입 0. `verify` 는 exit code 로 말한다.
3. **파일-복제 회피 (claude-flow #1834 반면교사)** — plugin 채널에 들어가는 내용물도 **생성된 projection**(`codex_setting/codex-skills` 동형)에서 나온다. 손복사·중복 SoT 금지. plugin 내용물의 SoT 는 언제나 `capabilities/`·`roles/`·core 이고, sync-native-* 생성기가 유일 경로.
4. **소유 경계 (GSD 모델)** — installer 는 **자신이 설치한 파일(manifest 등재분)만** 관리한다. 사용자 영역(runtime credentials·sessions·`projects/`·기존 사용자 config)은 불가침. 지우기 전 백업, 덮기 전 감지.
5. **idempotent** — 같은 명령 재실행이 안전 (`install-windows.sh` 선례 계승). 부분 실패 후 재실행이 복구 경로.
6. **공개 문서는 사람이 소유한다 (v3)** — root `README.md`는 설치 전 사용자가 제품을 이해하고 선택하는 공개 진입점이다. capability 정의를 기계적으로 늘어놓거나 prose를 hash로 동기화하지 않는다. 생성 가능한 manifest·runtime projection은 코드로 생성·검증하고, README의 가치 제안·정보 순서·예시는 review와 링크 검증으로 관리한다.

## 1. 배경 — 문제와 근거

- **현행 = 수동 레시피**: `INSTALL_LAYOUT.md` 는 런타임별 `ln -sfn` 나열(Claude ~17줄·Codex ~30줄·OpenCode ~25줄) + Migration Order 검증 ~260줄을 **사람이 셸에 붙여넣는** 구조. 신규 머신 셋업·타인 온보딩·Windows 가 각각 다른 절차로 흩어져 있다(`install-windows.sh` 는 Windows 만 자동화한 부분해).
- **Codex 채널 절반 존재**: `adapters/codex/plugin-marketplace/` + `codex plugin add agent-harness-codex@agent-harness` 가 이미 동작(Migration Order 검증 항목으로 실측). Claude Code·OpenCode 에는 대응물이 없다 — 비대칭.
- **research 결론**: 모든 조사 대상이 "SoT repo → distribution channel → target" 3단 골격(`05_deployment.md` §1). 채택 권고 = **GSD-style hash-manifest + reapply**(후보 1, 유일한 양방향 divergence 실구현) + 보조(parity-loss warning·byte-budget). 파일-복제식 스캐폴딩은 명시 회피.
- **HLS 와의 경계 (interlock)**: HLS = repo **내부** canonical↔adapter 바인딩(공유층 물리 이중화 해소). installer = repo→**runtime home** 배포. hash-manifest 메커니즘·생성기(`tools/build-manifest.py` 증분)·GSD 실코드 정독 게이트(HLS §3.2)는 **공유** — 한 번 정독이 양쪽 구현의 입력이고, manifest 스키마는 두 spec 이 같은 것을 쓴다(중복 구현 금지). HLS 구현이 canonical 구조를 바꾸면 installer 의 projection 소스 경로가 따라간다 — installer 는 경로를 하드코드하지 않고 HLS 예외 목록·manifest 를 읽는다.
- **공개 진입점 drift (v3)**: root README가 capability 전개표·내부 디렉터리 지도·런타임별 레거시 상태를 한 문서에서 자동 재생성하면서, 실제 installer/plugin 표면보다 뒤처져도 `.sync_state.json` hash만 갱신되면 정상처럼 보였다. 따라서 prose sync capability를 제거하고, 공개 설명과 기계 계약을 분리한다.

## 공통

- **Module 구조**: `tools/install/` (runtime-neutral core — `fleet` 과 같은 자리 컨벤션) + 런타임별 channel driver 는 core 안 모듈로 두되 adapter-specific 실현(기존 `adapters/*/bin/sync-native-*.py`·`preflight.sh`)을 **호출**한다(재구현 금지).
- **의존성**: python3 stdlib + git + (검증 단계 한정, 있으면 사용) 각 런타임 CLI (`claude`/`codex`/`opencode`). zero-pip (fleet 선례).
- **언어·런타임**: python3 ≥ 3.10 + thin sh launcher (`tools/install/install.sh`). Linux/macOS/WSL/Git Bash(Windows) — `install-windows.sh` 의 두 수리(HOME env 주입·symlink→copy 대체)를 Windows 분기로 **흡수**한다.
- **License**: repo 와 동일.

## [cli]

### 명령 (서브명령 트리)

| 명령 | 무엇 | 채널 |
|---|---|---|
| `install [claude\|codex\|opencode\|all]` | dev 머신 기본 경로 — symlink projection(INSTALL_LAYOUT 레시피 기계화) + runtime-owned 표면 처리(아래 표) + manifest 기록. `--plugin` 시 plugin 채널 경로(각 런타임 CLI 의 marketplace add/plugin add 를 wrapping·안내) | 양쪽 |
| `verify [runtime]` | Migration Order 수동 검증 ~260줄의 기계화 — projection 링크·생성기 `--check`·preflight 계약·bootstrap 로드 스모크를 check 목록으로 실행, 결과 pass/fail 표. **채널-인지**: plugin 채널 미채택 머신(dev projection 활성 + marketplace 미등록)에서 plugin check 는 명시 SKIP(ok) — parity-loss 원칙(silent drop 금지)과 동형. marketplace 등록됐는데 plugin 미설치·생성물 drift 는 실패 유지 | 공통 |
| `update [--reapply]` | repo pull 후 재-projection + plugin 채널이면 런타임 update 명령 wrapping. `--reapply` = local-patches 를 새 파일에 재적용 | 양쪽 |
| `status` | 설치 상태 요약 — 런타임별 채널·버전(commit)·drift(수정 감지) 유무 | 공통 |
| `uninstall [runtime]` | manifest 등재분만 제거(소유 경계) + 백업 안내 | 공통 |

- **공통 옵션**: `--runtime <r>`(반복 가능) · `--scope global|project` · `--dry-run`(실행 없이 계획 출력) · `--json`(기계 출력) · `--yes`(비대화)
- **채널 자동 판정**: cwd 또는 `AGENT_HOME` 에 git repo 가 있으면 dev 경로 기본, 없으면 plugin 채널 안내. `--plugin` 으로 명시 override.

### Input/Output 형식

- 사람: 단계별 진행 라인 + 최종 요약 표. `verify` 는 check 별 `✓/✗ <check-id> <한 줄>`.
- 기계(`--json`): `{runtime, channel, checks: [{id, ok, detail}], drift: [...], exit}` — fleet `--json` 스타일.

### Exit code

| code | 의미 |
|---|---|
| 0 | 성공 (verify: 전 check 통과) |
| 1 | 실행 실패 (I/O·전제 미충족) |
| 2 | verify 실패 — 1개 이상 check ✗ |
| 3 | BLOCKED — 대상 런타임 프로세스 활성 등 안전 정지 (INSTALL_LAYOUT Migration Order 2 계승) |
| 4 | drift 감지 — 사용자 수정 발견, `--reapply` 또는 백업 확인 필요 |
| 64 | usage 오류 |

### 표면 × 채널 결정 매트릭스

| 표면 | dev (installer symlink) | plugin 채널 | 비고 |
|---|---|---|---|
| capabilities(skills)·commands | ✓ symlink | ✓ (생성 projection 탑재) | SoT = `capabilities/`, 생성기 경유 |
| roles(agents)·modes | ✓ symlink | ✓ | 〃 (`roles/`) |
| hooks | ✓ symlink (settings.json 이 참조) | ✓ Claude·Codex `hooks/hooks.json` (currentness 확인 — Claude ~30 이벤트, Codex 는 `type:"command"` 만 실행) / OpenCode 는 JS plugin | 탑재 **범위**는 INST-OPEN-1 (소비자에 의미 있는 가드만, self-contained·fail-open) |
| MCP·bin(PATH) | ✓ | ✓ (`.mcp.json`·`bin/`) | fleet launcher 는 bin/ 후보 |
| settings.json·keybindings (runtime-owned 복사) | ✓ copy-once + manifest | ✗ (plugin 은 `agent`·`subagentStatusLine` 키만) | CLI 몫 |
| statusline·env 주입·PATH launcher | ✓ | ✗ | CLI 몫 |
| memory DB 복원 (`mem import`) | ✓ | ✗ | CLI 몫 (dump.jsonl → memory.db) |
| 검증 (Migration Order) | ✓ `verify` | ✓ 동일 `verify` 사용 | 공통 |

### plugin 채널 — 런타임별 스펙 (2026-07-12 currentness 검증 반영)

- **Claude Code (신설)**: `adapters/claude/plugin-marketplace/`(Codex 동형 대칭) 에 `.claude-plugin/marketplace.json` + plugin `agent-harness-claude`. source 는 relative-path(로컬)·github(원격) 2형. 내용물은 sync-native 생성기 산출(원칙 3).
  - **탑재 가능(공식 확인)**: skills·agents·`hooks/hooks.json`(~30 이벤트)·`.mcp.json`·`bin/`(Bash PATH). **불가**: settings.json 일반 키(`agent`·`subagentStatusLine` 만)·env·permissions·statusline·plugin 내 CLAUDE.md(컨텍스트 미로드).
  - **설치본은 self-contained**: cache 는 plugin root 밖 참조(`../`) 차단 + 버전-ephemeral(`~/.claude/plugins/cache`) — plugin 디렉토리에 생성물을 **빌드 시점에 물리 포함**해야 한다. 이는 claude-flow 식 손복제가 아니라 생성기 산출물이며(원칙 3), `build-manifest --check` 계열 가드로 SoT 와 바인딩. 영속 상태는 `${CLAUDE_PLUGIN_DATA}`(`~/.claude/plugins/data/<id>/`, 업데이트 생존).
  - **postinstall 부재** — 공식 대체 = `Setup`/`SessionStart` hook 이 `${CLAUDE_PLUGIN_DATA}` 에 초기화. runtime-owned 표면이 필요한 소비자는 plugin 이 CLI(`verify`/`install`) 실행을 안내.
  - version 정책 = git SHA 추종(`version` 생략) 기본 + 릴리스 채널 필요 시 marketplace 2개(`ref` 분리) 패턴.
  - CLI wrapping: 비대화 `claude plugin marketplace add` + `claude plugin install` 확인됨 — installer 의 `--plugin` 경로가 사용.
- **Codex (승격)**: 기존 `adapters/codex/plugin-marketplace/`(`.agents/plugins/marketplace.json` — 현행 공식 위치와 일치 확인) 재사용 — installer 는 `codex plugin marketplace add` + `codex plugin add <name>@<marketplace>` 를 wrapping 하고 verify 항목을 잇는다.
  - ⚠️ **plugin 이 못 싣는 것(공식 확인)**: custom agents(`.codex/agents/*.toml`)·prompts·config.toml fragment·AGENTS.md — plugin 은 skills·`.mcp.json`·`hooks/hooks.json`(`type:"command"` 만 실행)·`.app.json` 4종만. **따라서 Codex 는 plugin 채널만으로 완결 불가** — agents .toml 은 installer 의 symlink projection 이 계속 담당(현행 INSTALL_LAYOUT 배선 유지).
- **OpenCode**: marketplace·번들 포맷 **부재 확인** — plugin 채널 없음, installer 가 유일 경로. `opencode.json` 에 `instructions[]`·`plugin[]` 을 **non-destructive merge**(rulesync 선례: 기존 사용자 config 보존, 충돌 시 보고·중단 — 의미 판단 아닌 규칙) + convention 디렉토리 projection.
  - ⚠️ **drift(currentness 검증)**: 현행 공식 문서는 **복수형** 디렉토리(`.opencode/skills|commands|agents|plugins/`, global `~/.config/opencode/…`)이고 **`skills.paths` config key 는 문서에 없다**(skill 노출은 `permission.skill` 규칙 + convention 디렉토리) — 기존 `INSTALL_LAYOUT.md`·`opencode_setting` 배선(단수형 `agent/`·`command/`, `skills.paths`)은 legacy 일 가능성. **구현 Step 0 에서 로컬 opencode 버전 대상 실측 후 migration 포함**(구식 배선 침묵 유지 금지).

### 공개 진입점 — root README (v3)

- **목적**: 저장소 내부를 이미 아는 운영자용 dashboard가 아니라, 처음 방문한 사용자가 30초 안에 “무엇인지 / 어떻게 설치하는지 / 어떤 런타임을 지원하는지 / 어디서 더 읽는지” 판단하는 product landing page.
- **정보 순서**: 한 줄 가치 제안 → 빠른 설치(`harness install`) → 바로 쓰는 예시 → 핵심 기능 → 런타임별 배포 차이 → 작동 구조 → 깊은 문서/개발 검증. 세부 capability 전수 표와 전체 디렉터리 트리는 각각 `capabilities/README.md`, `MANUAL.md`, `core/`, `INSTALL_LAYOUT.md`로 보낸다.
- **포지셔닝**: 제품 전체는 단일 plugin이 아니라 **portable agent harness**다. Claude Code와 Codex에서는 native plugin + installer projection을 제공하고, marketplace bundle이 없는 OpenCode는 installer projection을 제공한다. 지원 수준을 같은 것으로 뭉개지 않는다.
- **소유권**: README prose는 human-owned. 자동 생성 블록을 기본으로 두지 않는다. 이름·경로·projection의 기계적 정합성은 `tools/build-manifest.py --check`, adapter `sync-native-* --check`, `tools/check-adaptation-boundary.sh`, `tools/skill-conformance/check.sh`, `harness verify`가 담당한다.
- **`sync-skills` 퇴역**: `capabilities/sync-skills.md`, Claude compatibility skill, Codex/OpenCode native projections, catalog/manifest entry, `.sync_state.json`, README regeneration/oncall reminder를 제거한다. 기존 cross-doc 불변식은 결정론적 guard의 명시적 명령으로 유지하고, 문서 편집 품질은 review 대상이다. 역사 산출물과 git 이력은 소급 수정하지 않는다.
- **근거**: `_internal/readme-reference-brief.md`의 GitHub 상위 프로젝트 패턴과 2026-07-13 공식 runtime 문서 재검증. 외부 프로젝트의 문구/레이아웃을 복제하지 않고 정보 구조만 참고한다.

### hash-manifest + reapply (fork-drift 대응)

- **대상**: installer 가 runtime home 에 **복사**한 파일만 (settings.json·keybindings·Windows copy 분기). symlink 는 자체가 canonical 이라 제외, plugin cache 는 런타임 소유라 제외.
- **동작**: install 시 hash 기록 → `verify`/`update` 시 불일치 = 사용자 수정 감지 → `local-patches/` 백업 → `update --reapply` 가 새 파일 위에 재적용, 3-way 충돌은 명시 report(자동 머지 강행 금지).
- **구현 선행 게이트 (HLS §3.2 공유)**: GSD `bin/install.js` 실코드 line 단위 정독 후 manifest 스키마 확정. research 카드 서술 그대로 이식 금지.

### parity-loss warning (보조 채택)

런타임이 못 싣는 표면(예: OpenCode 에 없는 hook 이벤트)은 **silent drop 금지** — install/verify 출력에 `SKIP(<runtime>): <surface> — <사유>` 명시(ruler 반면교사, `cards/multi-harness-projection.md` §2).

## Architecture Diagrams

### Component diagram (mermaid)

```mermaid
flowchart TD
    subgraph CLI["tools/install/ (runtime-neutral core)"]
      ENTRY[install.sh → installer.py] --> CMD{install / verify / update / status / uninstall}
      CMD --> PROJ[projector<br/>symlink plan = INSTALL_LAYOUT 기계화]
      CMD --> MAN[manifest<br/>hash 기록·drift 감지·reapply]
      CMD --> VER[verifier<br/>Migration Order check 목록]
    end
    subgraph DRV["channel drivers (기존 어댑터 실현 호출)"]
      D1[claude driver<br/>symlink + plugin-marketplace 신설]
      D2[codex driver<br/>preflight.sh · plugin add 승격]
      D3[opencode driver<br/>opencode.json merge + plugins]
    end
    PROJ --> D1 & D2 & D3
    VER --> D1 & D2 & D3
    D1 --> G1[sync-native 생성기<br/>SoT: capabilities/ · roles/]
    D2 --> G1
    D3 --> G1
    MAN -.공유 스키마.-> HLS[harness-layer-sync<br/>hash-manifest / build-manifest.py]
    README[root README<br/>human-owned landing page] --> ENTRY
    README --> DOCS[MANUAL · capabilities · core · INSTALL_LAYOUT]
```

## 의미↔규칙 경계 체크 (DESIGN_PRINCIPLES §0.7)

- 의미 판단 구간 스캔: installer 동작은 전부 결정론(파일 ops·hash 비교·config merge·check 실행). **충돌 0**.
- 유일 경계 후보 = OpenCode config merge 의 "충돌" 판정 — **규칙으로 처리**(같은 key 에 다른 값 = 충돌 → 보고·중단, 자동 해석 시도 없음). LLM fallback 불요.

## v5 — release-bound bootstrap과 automatic packaged update

### 기본 사용자 흐름

```bash
curl -fsSL https://github.com/dmlguq456/agent_setting/releases/latest/download/install.sh | sh
harness runtime doctor --runtime all --strict
```

공개 bootstrap은 `raw main`의 installer 코드를 실행하지 않는다. GitHub의 latest-release
redirect가 선택한 `install.sh` asset에는 그 release tag와 같은 commit의
`distribution.py`가 내장되고, bootstrap은 내장된 exact tag의 metadata만 요청한다.
Version pin은 latest installer의 `--version` override가 아니라
`releases/download/<tag>/install.sh` URL로 선택하며, script와 archive tag 불일치는
mutation 전에 거부한다. Root `install.sh`는 기존 raw URL 사용자를 위한 latest-release
redirect shim일 뿐 distribution 코드를 `main`에서 직접 읽지 않는다.

bootstrap은 GitHub Release metadata에서 고정 이름 asset `agent-harness.tar.gz`와
`agent-harness.tar.gz.sha256`을 찾아 checksum을 검증한다. archive는 private staging에서
안전하게 해제하고 `RELEASE_VERSION`, installer entrypoint, manifest/core surface를 확인한
뒤 `${XDG_DATA_HOME:-$HOME/.local/share}/agent-harness/releases/<version>`에 publish한다.
`current`와 `${HARNESS_BIN_DIR:-$HOME/.local/bin}/harness`는 activation 성공 뒤 원자 전환한다.
SHA-256 sidecar는 전송/asset corruption 검사이며 독립 signature가 아니다. Publisher
authenticity는 repository의 GitHub Release와 HTTPS account를 trust anchor로 둔다.

### update 분기

- managed distribution state가 있으면 `harness update`는 stable release를 확인한다.
- managed state가 없으면 기존 hash-manifest drift/reapply 동작을 유지한다.
- managed updater는 이전 release를 source로 쓰는 packaged runtime만 새 release로 활성화한다.
- linked/foreign source는 `skipped-linked`/`skipped-foreign`으로 보고하고 Git 명령을 실행하지 않는다.
- `--version <tag>` 또는 `HARNESS_VERSION`은 release pin이다. 같은 version+checksum은 no-op이다.
- 실패 시 runtime activation snapshot/이전 release 재활성화와 current/state bytes 복구를 수행한다.

### automatic update

- bootstrap은 기본적으로 Linux systemd user timer 또는 macOS LaunchAgent를 등록한다.
- `--no-auto-update`/`HARNESS_NO_AUTO_UPDATE=1`로 opt out할 수 있다.
- `harness auto-update status|enable|disable`은 launcher만 호출하는 user-owned scheduler를 관리한다.
- scheduler가 없거나 user bus 등록이 실패하면 install 자체는 성공하고 manual fallback과 원인을 출력한다.
- 자동 update가 runtime-owned credential/session/log/cache/database를 수정하지 않으며 현재 session의 instruction reload를 약속하지 않는다.
- scheduler unit/plist는 설치 시 HOME/XDG, harness data/state/bin, Codex/Claude runtime
  home override를 보존한다. Explicit version pin은 distribution state에 남고 `--auto`
  실행은 pinned status로 끝나며 latest를 받지 않는다.

### release workflow

- tag `v*` push가 deterministic `agent-harness.tar.gz`, archive SHA-256 sidecar,
  같은 ref의 distribution module을 내장한 `install.sh`, installer SHA-256 sidecar를 생성한다.
- workflow는 최소 `contents: write` permission으로 tag를 검증한 뒤 GitHub Release에 네 asset을 함께 게시한다.
- archive에는 tracked source와 `RELEASE_VERSION`만 포함하며 credential, local state, report cache, Git metadata를 포함하지 않는다.

### README 공개 계약 변경

- 첫 화면은 한 줄 가치 제안 → clone 없는 설치 → 자연어 예시 → 다섯 가지 강점 순서다.
- 강점은 complete work cycle, cross-runtime contract, inspectable runtime state, selectable profiles, durable memory/guards로 간단히 제시한다.
- “native first, plugins optional”은 독립 홍보 section에서 제거한다. 중복 discovery와 plugin compatibility 설명은 Runtime support/깊은 문서에 필요한 만큼만 남긴다.

### 보안·회귀 수용 기준

- checksum mismatch, missing asset, traversal, archive 밖 symlink/hardlink, special file을 publish 전에 거부한다.
- concurrent update는 distribution lock으로 직렬화한다.
- activation/state commit failure에서 current, distribution state, runtime projections가 이전 version으로 복구된다.
- updater/scheduler fixture는 isolated HOME/XDG와 local file release metadata만 사용한다.
- release installer가 exact embedded tag만 설치하고 `--version`/`HARNESS_VERSION`으로
  다른 archive를 선택할 수 없으며, public README와 root compatibility shim 어디에도
  `raw main` distribution module URL이 남지 않는다.
- 동일 ref에서 두 번 빌드한 archive, installer, 두 checksum은 byte-identical하다.
- 기존 runtime activation/profile/extension lifecycle, manifest/projection/adaptation/conformance 검사를 회귀한다.

## 열린 결정 (OPEN) — v5 현황

- ~~INST-OPEN-1~~ **확정(구현 사이클 2, 2026-07-13)**: plugin 탑재 hook 목록 — **채택 2**: `git-state-guard.sh`·`artifact-guard.sh`(self-contained·fail-open 충족) / ~~이월 3~~ **채택 완결(사이클 3, 2026-07-13)**: spec 파이프 3종(`spec-skill-gate`·`spec-read-marker`·`spec-sync-nudge`) — 생성기 `hooks.json` 의 `AGENT_HOME="${CLAUDE_PLUGIN_DATA}"` env-prefix 로 재기준, canonical 무수정 / **제외**: memory(mem-*)·statusline·dispatch·core-first 계열(CLI 설치 전제 상태 의존). 근거 = `plans/2026-07-13_harness-installer-impl2/final_report.md`.
- ~~INST-OPEN-2~~ **확정(사용자, 2026-07-12)**: CLI 진입 명령 = **`harness`** (fleet 동형 한 단어 + 서브명령, `tools/install/harness.sh` launcher → `~/.local/bin/harness` symlink). PATH 충돌은 install 시 기존 `harness` 명령 존재 검사로 방어.
- ~~INST-OPEN-3~~ **완료(구현 사이클 2, 2026-07-13)**: `INSTALL_LAYOUT.md` 514→250줄 — 셸 레시피 나열·수동 검증 블록을 `harness install`/`harness verify` 참조로 대체, 계약적 내용(Windows 절·런타임별 특기사항) 보존.
- **INST-OPEN-4** (유지): OpenCode 배선 drift(복수형 디렉토리·`skills.paths` 부재) — 로컬 1.17.13 은 단수형 배선으로 정상 동작(verify `opencode.drift-watch` check 가 상시 감시), 복수형 migration 은 opencode 버전업 시 별도 사이클.

## v3 확정 결정

- **INST-D-8 (사용자 확정, 2026-07-13)**: root README는 plugin/product landing page 구조의 human-owned 공개 문서다. 세부 내부 지도를 자동 재생성하지 않는다.
- **INST-D-9 (사용자 확정, 2026-07-13)**: `sync-skills` portable capability와 모든 현역 runtime projection을 퇴역한다. manifest/projection/adaptation/conformance 검사는 각각의 결정론 도구가 계속 소유한다.

## v4 확정 결정

- **INST-D-10 (사용자 확정, 2026-07-14)**: 공개 기본 설치는 clone 없는 managed packaged release다. linked checkout은 maintainer 경로로 유지한다.
- **INST-D-11 (사용자 확정, 2026-07-14)**: managed release는 supported OS에서 자동 확인·갱신하며 staging/checksum/rollback을 통과하기 전 active pointer를 바꾸지 않는다.
- **INST-D-12 (사용자 확정, 2026-07-14)**: updater는 linked source에 Git fetch/pull/repoint를 수행하지 않는다.
- **INST-D-13 (사용자 확정, 2026-07-14)**: README 상단은 plugin 구현 경계 대신 제품 강점을 간결하게 나열한다.

## v5 확정 결정

- **INST-D-14 (사용자 확정, 2026-07-14)**: 한 설치 invocation의 bootstrap 코드와
  archive는 반드시 같은 immutable GitHub repository와 Release tag에서 온다. `raw main`은 public
  install trust path가 아니며 root shim은 release asset으로만 redirect한다.
