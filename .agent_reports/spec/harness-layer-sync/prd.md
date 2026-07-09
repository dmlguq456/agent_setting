# harness-layer-sync — Spec (PRD)

> mode: **library + cli** (하네스 인프라 — canonical 바인딩 계약 + 가드/생성기·매니페스트 CLI) · 작성 2026-07-09 · v1
> 컴포넌트: `agent_setting` repo 의 **하네스 내부 구조 개선** — 기존 `.agent_reports/spec/prd.md`(Unified Memory System)·`spec/agent-fleet-dashboard/`·`spec/dispatch-profiles/` 와 무관한 독립 청사진. 이 폴더(`spec/harness-layer-sync/`)가 자체 SoT.
> 입력(1순위 근거):
> - 감사 `.agent_reports/analysis_project/harness-alignment/` — `summary.md`(b) 구조후보 b1~b4, `findings.md` §S(S-1~S-4)·Axis 1~7, `cards/00_structural_shared-copy-drift.md`
> - research `.agent_reports/research/cross-platform-agent-frameworks/` — `analysis_summary.md` §4~§5, `06_implementation.md`, `cards/gsd.md`, `cards/multi-harness-projection.md`, `cards/claude-flow.md`(반면교사)
> - 현행 계약 실측(2026-07-09, 본 워크트리): `core/ADAPTATION.md`, `core/ADAPTATION_INVENTORY.md`, `tools/check-adaptation-boundary.sh`, `adapters/claude/settings.json`, `~/.claude`→`claude_setting`→`adapters/claude` projection 체인, `hooks`·`tools`·`utilities` 전수 diff census
> 본 문서는 청사진(PRD). 구현은 autopilot-code (산출물 `plans/`). 지침 파일(core/adapters) 자체는 본 spec 이 수정하지 않는다 — 방향만 확정.

## 0. 한 줄

**최상위 공유층(`hooks/`·`tools/`·`utilities/`)을 유일 canonical 로 삼고, Claude 런타임도 Codex/OpenCode 처럼 그 canonical 을 실행하게 만든다.** `adapters/claude/`의 물리 복사본을 제거(canonical 로 symlink 접기)하고, 런타임 제약으로 복제가 불가피하거나 의도적으로 다른 파일만 **명시 예외 목록 + hash-manifest 바인딩**으로 남긴다. parity 가드는 "공유본"이 아니라 **런타임이 실제 실행하는 파일**을 검증하고, surface 집합은 파일시스템에서 파생한다.

## 0.5 설계 원칙 — 단일 canonical, 예외는 선언된 결정 ★ cross-cutting

**공유층 파일의 진실은 한 곳(최상위 canonical)에만 있다. 어떤 런타임도 그 canonical 을 실행하거나(symlink), 그로부터 파생된 것을 실행한다. 물리 복제는 오직 _선언된 예외_ 로만 존재하고, 예외는 hash-manifest 로 canonical 에 묶여 drift 하면 가드가 red 낸다.**

- **왜**: 현행은 canonical(공유본)과 Claude 런타임 실행본(`adapters/claude/` 복사본)이라는 **두 진실이 바인딩 없이 공존**한다(§3 census). fix 가 한쪽에만 반영돼 이미 divergence 가 발생했다 — S-1(spec-read-marker relative-path fix 누락, Claude 런타임 stale, 가드는 통과)·S-2(harness-status 65줄 divergence)가 실사고 자증. research 는 이 배포 모델의 구조적 취약성을 **claude-flow #1834**(367개 중복 SKILL.md drift — 프레임워크 스스로 겪음, `cards/claude-flow.md` §3·§6)로 반면교사 삼고, 결론을 "파일 복사 금지 · reference + converter 유지"로 명시(`06_implementation.md` §4).
- **적용**: 새 공유 파일이 필요하면 "이미 canonical 이 어디 있나 → 런타임이 그걸 어떻게 실행하나"를 먼저 묻는다. Claude 에 새 복사본을 만들지 않는다. 정말 달라야 하는 파일은 예외 목록에 사유와 함께 등재한다 — silent 복제 금지(§0.5 결정론-우선 = `core/DESIGN_PRINCIPLES.md`, 감사 b4 근거).
- **결정론-first 연결**: b4(§6)에서 surface 집합(hook/agent/tool/utility 파일목록)을 사람이 서술하는 대신 파일시스템에서 파생 — ledger 는 사유(rationale)만 남긴다.

## 1. 배경 — 사용자 문제의식과 감사·research 종합

사용자 문제의식: **"에이전트 세팅이 core > adapter > proj 순으로 되는데 매번 서로 어긋나는 느낌."** 전수 감사(`harness-alignment`)는 이 "어긋남"의 메커니즘적 진원지를 찾았고(§S), cross-platform research 는 같은 문제를 푸는 8개 프레임워크의 실장을 조사했다. 본 spec 은 그 둘을 종합한 구조 개선 청사진이다.

감사 결론(재인용): 총 21건(P0 0 · P1 8 · P2 13). **안전 hook·하드순서 게이트·런타임 wiring 은 정합(파손 없음)**이나, 무게중심은 (1) 발견 절반이 Claude bootstrap(`adapters/claude/CLAUDE.md`) stale, (2) 진짜 구조적 원인은 **공유층 물리 복제(§S)**, (3) OVERCLAIM 0 — 전부 UNDERCLAIM/stale 계열이라 방향은 명확하고 fix 는 저위험.

research 결론(재인용): 거의 모든 multi-runtime 프레임워크가 "core 1벌 → runtime 표면 차이는 변환으로 흡수"라는 우리와 동형 철학을 공유(`analysis_summary.md` §4-(1)). 우리가 참고할 prior art 중 **양방향 divergence(3-way merge)를 실제 구현한 건 GSD 하나**(hash-manifest + `--reapply`, §4-(2)·§5). Claude 공식 규격조차 이 양방향 merge 를 "문서에 없다"고 인정. one-runtime-only 기능(hook 실행 격리)은 **어떤 도구도 없는 runtime 에서 진짜 재현 못 하며** 최선이 skip+warning / event 어휘 정규화 / prompt simulation 수준(§4-(6), `cards/multi-harness-projection.md`).

## 2. 현행 배선 실측 (2026-07-09, 본 워크트리)

### 2.1 projection 체인 — canonical 이 아니라 복사본이 런타임 진실

```
Claude 런타임:
  settings.json → $HOME/.claude/hooks/*.sh
  ~/.claude/hooks ─(symlink)→ agent_setting/claude_setting/hooks
  claude_setting/hooks ─(symlink)→ ../adapters/claude/hooks   ← 실디렉토리, 물리 복사본(inode 다름)
  ⇒ Claude 는 adapters/claude/hooks/*.sh (복사본) 를 실행

Codex/OpenCode 런타임:
  preflight.sh → $ROOT/hooks/*.sh (공유 최상위 직접 실행)
  adapters/{codex,opencode}/utilities/* ─(symlink)→ ../../../utilities/* (공유)
  ⇒ Codex/OpenCode 는 공유 canonical 을 실행

parity 가드:
  tools/check-adaptation-boundary.sh:784 → grep 공유 hooks/spec-read-marker.sh 만 assert
  :217 → check_link_target claude_setting/hooks ../adapters/claude/hooks (projection 링크만 확인, 내용 비교 X)
  ⇒ 가드는 공유본만 본다. Claude 가 실행하는 복사본은 검증 대상 밖
```

`claude_setting/` 계층은 **정상**(전부 symlink projection). 문제는 그 아래 `adapters/claude/{hooks,tools,utilities}/`가 최상위 공유층의 **물리 복제**라는 점, 그리고 둘을 묶는 바인딩이 없다는 점이다.

### 2.2 전수 diff census (adapters/claude/ 복사본 ↔ 공유 canonical)

| 층 | SAME(내용 동일) | DIFFER | 파일집합 |
|---|---|---|---|
| `hooks/` | 12 | 6 | 두 디렉터리의 **파일 _집합_ 은 동일**(CLAUDE-ONLY·SHARED-ONLY 0). 내용만 6개 갈라짐 |
| `tools/` | 2 | 1 | build-manifest.py(15) |
| `utilities/` | 6 | 3 | agent-worklog-state.sh(54)·harness-status.sh(65)·workflow-guard-hook.sh(2) |

DIFFER 6 hooks 의 성격 분류(census + 감사 교차):

| 파일 | diff | 분류 | 근거 |
|---|---|---|---|
| `core-first-guard.sh` | 134 | **의도된 wrapper** (복사본이 아니라 `exec "$AGENT_HOME/hooks/..."` 위임) | 감사 §S "drift 아님"(S6 2026-07-09 회귀정합). 파일 상단 주석이 사유 명기 |
| `core-read-marker.sh` | 86 | **의도된 wrapper** (동형) | 〃 |
| `spec-read-marker.sh` | 5 | **STALE (버그)** — Claude 가 relative-path fix 누락 | **[S-1]** git `1d97534`(공유)만 fix, 복사본은 `e83ff5e` stale. settings.json:119 가 fix 없는 복사본 실행 |
| `harness-status.sh`(utilities) | 65 | **STALE (버그)** — Claude 가 git-signal 확장 누락 | **[S-2]** 공유 221줄(`f5a98db`) vs 복사본 158줄(`d7b1612`) |
| `mem-distill-dispatch.sh`(30)·`mem-recall-inject.sh`(4)·`mem-turn-nudge.sh`(6)·`build-manifest.py`(15)·`agent-worklog-state.sh`(54)·`workflow-guard-hook.sh`(2) | — | **미판정 (adapter-specific vs stale)** | **[S-4]** 동커밋 내 조정(경로 fallback 등)으로 보이나 바인딩 부재로 언제든 S-1 형 재발 가능. 파일별 후속 판정 필요 |

핵심: **두 wrapper(core-*)가 이미 "canonical 을 exec 하는 예외" 모델을 실증**한다(§4 선례). SAME 20개는 접어도 무행동변화. STALE 2개는 재동기 대상. S-4 6개는 phase 1 에서 파일별 판정.

## 3. b1 — 공유층 물리 이중화 해소 (채택: 감사 옵션 (iii)+(i) 조합)

**원칙: 최상위 `hooks/`·`tools/`·`utilities/` 가 유일 canonical. Claude 런타임도 그 canonical(또는 파생)을 실행한다.**

감사 b1 세 옵션 — (i) content-parity 가드 (ii) wrapper/symlink 전환 (iii) 단일 canonical 선언 — 중 **(iii)+(i) 조합** 을 채택한다. research(`06_implementation.md` 후보 1 = GSD hash-manifest, 후보 보조 = override 물리분리)와 종합한 근거:

- **(iii) 단일 canonical**: SAME/STALE 파일은 canonical 로 **symlink 접기**. Codex/OpenCode 가 이미 `adapters/*/utilities/* → ../../../utilities/*` 로 하는 그 방식(§2.1), 그리고 Claude core-* wrapper 가 이미 하는 exec-위임(§2.2)의 일반화. Claude 런타임이 symlink 를 따라감은 실측 확인(`~/.claude/hooks` 자체가 symlink 이며 정상 동작). ⇒ 물리 이중화 원천 소거.
- **(i) 예외 + hash-manifest**: 런타임 제약·의도로 **복제가 불가피한 파일만** 명시 예외 목록에 사유와 함께 등재하고, GSD-style **hash-manifest** 로 canonical 과 바인딩 — 복제본이 canonical 의 파생 계약에서 어긋나면 가드 red. research 관찰: GSD 만이 "upstream 갱신 + 로컬 delta" 양방향을 hash-manifest+patch 로 관리(`cards/gsd.md` §2, `analysis_summary.md` §4-(2)). S-1(fix 가 한쪽만) 이 정확히 이 바인딩 부재의 산물.

### 3.1 파일 3분류 (canonical 바인딩 계약)

| 클래스 | 처리 | hash-manifest | 예시(census) |
|---|---|---|---|
| **collapsed** | canonical 로 symlink. 물리 파일 제거 | 불요(파일이 곧 canonical) | SAME 20개 + 재동기 후 STALE 2개(spec-read-marker·harness-status) |
| **wrapper 예외** | canonical 을 `exec` 하는 얇은 어댑터 래퍼. 물리 유지 | wrapper 형식 assert(예: `exec "$AGENT_HOME/hooks/<name>"` 포함) | core-first-guard·core-read-marker |
| **delta 예외** | canonical + 선언된 adapter patch. 물리 유지 | canonical 파생분 hash 바인딩 — patch 외 divergence 시 red | S-4 중 "진짜 adapter-specific" 로 판정되는 것 (예: 런타임 경로 fallback) |

- **예외 목록의 위치**: 가드 옆 선언 파일(ADAPTATION.md §6 "intentional exclusion belongs in an explicit exemption list, never a silent omission" 계약 준수). 각 항목 = {파일, 클래스, 사유, (delta면) canonical baseline}.
- **collapse 가 기본, 예외가 증명 부담**을 진다 — "왜 이 파일만 복제되어야 하나"를 사유로 대야 예외에 들어간다.

### 3.2 GSD 실코드 정독 = 구현 선행 조건 (불변)

hash-manifest 세부(manifest 스키마, 3-way patch/reapply, 소유 경계)는 **GSD `bin/install.js`·`gsd-core/bin/lib/state-transition.cjs` 실코드를 line 단위로 정독한 뒤** 확정한다. research 카드는 installer file-ops 를 line 단위로 미검증이라 명시(`06_implementation.md` §2 단점·§5 리스크, `cards/gsd.md` "미검증/주의"). 카드 서술을 그대로 이식하지 말 것 — pilot 전 실코드 재확인이 research 가 건 명시 gate.

### 3.3 기존 생성기 재사용

`tools/build-manifest.py` 는 이미 `build_hooks()`·`build_skills()`·`build_agents()`·`build_loops()` 로 파일시스템에서 surface 를 파생하고 `--check` 로 drift 를 감지한다(실측). hash-manifest·예외 검증은 **신규 시스템이 아니라 이 생성기 + `check-adaptation-boundary.sh` 가드의 증분**으로 얹는다(research §4 "새 아키텍처 아닌 증분" 원칙, `06_implementation.md` §4).

## 4. b3 — parity 가드의 검증 대상을 런타임 실행본까지 확장 (채택)

`check-adaptation-boundary.sh` 가 **공유본만 assert 하는 틈**(S-1 이 통과한 구멍, §2.1)을 닫는다.

- **가드 계약 변경**: 가드는 "canonical 이 옳은가"만이 아니라 **"런타임이 실제 실행하는 파일이 canonical 과 정합인가"**를 검증한다. 구체적으로 (a) `settings.json` 이 가리키는 실행 경로를 따라가(`~/.claude`→`claude_setting`→`adapters/claude`), 그 실행본이 §3.1 클래스 계약(collapsed=symlink 동일성 / wrapper=형식 / delta=baseline)에 맞는지 assert. (b) `:784` 처럼 공유본 한 곳만 grep 하는 assertion 은 실행본까지 확장하거나 collapse 로 실행본=canonical 을 보장.
- **런타임 currentness 게이트 준수**: symlink 추종·hook 실행이 각 런타임에서 실제로 동작하는지는 `core/ADAPTATION.md` §2.2("existence vs parity 분리, 현행 문서 확인") 대로 구현 plan 에 현행-doc 인용 + 로컬 projection 체크 + fallback 을 넣는다.

### 4.1 동류 버그 동반 정리 — runtime-root 해석 계약 (dispatch-liveness)

같은 "런타임 실행본 ≠ 검증 대상" 계열의 실사고: `utilities/dispatch-liveness.sh:14` 가 `PROJ="$AGENT_HOME/projects"` 로 transcript 를 찾는다. `AGENT_HOME` 은 `agent-home.sh` 기본값이 `$HOME/agent_setting`(harness 소스 repo)이라, Claude 세션 transcript 가 실제 있는 `~/.claude/projects/` 를 못 보고 **살아있는 job 을 DEAD 오탐**(2026-07-09 실측).

**spec 이 명문화하는 계약 — 두 루트를 구분한다:**

| 루트 | 의미 | 해석 |
|---|---|---|
| **AGENT_HOME** | 하네스 _소스_ repo (canonical 스크립트·계약이 사는 곳) | `agent-home.sh` (`AGENT_HOME`→`CLAUDE_HOME`→`$HOME/agent_setting`→`$HOME/.claude`) |
| **runtime-root** | _런타임이 세션 상태(transcript/DB)를 쓰는_ 곳 | Claude=`${CLAUDE_CONFIG_DIR:-$HOME/.claude}` · Codex=`$CODEX_HOME` · OpenCode=`~/.config/opencode`(DB) |

- session transcript·projects·liveness 를 읽는 도구는 **runtime-root 로 해석**해야 한다 — AGENT_HOME 이나 jobs.log 위치와 무관. dispatch-liveness 의 non-profile 경로(`PROJ`)를 runtime-root 기준으로 고친다.
- profile 분사 경로(`homes/<slug>.<name>/projects/`, dispatch-profiles DP-4)는 이미 runtime-root 격리라 정상 — 이 계약은 그것과 정합.
- **경계**: dispatch-profiles spec(`spec/dispatch-profiles/`)이 profile home 을 소유하므로, 본 spec 은 **runtime-root 해석 계약의 명문화**만 하고 profile 별 home 생성 로직은 건드리지 않는다(중복 회피).

## 5. b4 — ADAPTATION_INVENTORY 를 서술에서 파일목록 파생으로 (채택)

hook/agent surface 집합을 사람이 서술(수동 ledger)하는 대신 **실제 파일시스템에서 생성기·가드가 파생**하고, 수동 ledger 는 사유(rationale)만 남긴다. (§0.5 결정론-first, 감사 b4·2-1·2-3.)

- **문제**: `core/ADAPTATION_INVENTORY.md:33` 은 Codex hook 을 3파일로 서술하나 실제 `hooks.json` 은 7개 wired 이고 가드 `:788` 도 7개 강제 → ledger·실제·가드 3자 불일치(반복적 UNDERCLAIM, S-2 계열). memory-scout 도 `EXTRA_AGENTS` 생성인데 ledger 누락(2-3).
- **이미 있는 계약**: `core/ADAPTATION.md` §6 은 projection-completeness 가드가 "**enumerate the source domain** (실제 현행 항목을 iterate) rather than a hardcoded list" 여야 하고, 의도적 제외는 "explicit exemption list"에 두라고 이미 명문화. b4 는 이 계약을 **실집행**으로 옮긴다.
- **메커니즘**: `build-manifest.py`(이미 hook/agent/skill/loop 를 파일에서 파생) 출력을 SoT 로, (a) `check-adaptation-boundary.sh` 의 하드코딩 열거(`:788` 등)를 파생 집합 iterate 로 교체, (b) ADAPTATION_INVENTORY 의 _파일목록_ 부분은 파생값과 대조해 drift 시 red, prose 는 사유만.
- **경계**: 감사 a1~a14 의 개별 문구 fix(지침 파일 직접 수정)는 본 spec 밖 — core-first 게이트 경유 별도 처리. b4 는 그 fix 들이 _재발 안 하게_ 하는 구조만 확정한다.

## 6. 보조 채택 (research 06 보조 후보)

### 6.1 parity-loss explicit warning — silent skip 금지 (채택)

adapter 투영에서 한 런타임에만 있는 기능(hook 실행 격리 등)이 다른 런타임에 없을 때, **silent drop 하지 말고 explicit warning/unsupported 로 노출**한다. ruler 반면교사(`cards/multi-harness-projection.md` — Copilot 없는 tool 어휘 "dropped silently", `analysis_summary.md` §4-(6) 관찰 (6)). `core/ADAPTATION.md` §2("fail closed for unknown features")·Acceptance Test("explicitly marks the behavior unsupported with fallback")와 정합 — 이미 문서 계약은 있으므로, 가드가 그 warning 의 _존재_ 를 검증하는 데까지 확장한다. 어느 도구도 hook 실행 격리를 없는 런타임에서 진짜 재현 못 함(research 결론)을 정직하게 반영.

### 6.2 bootstrap byte-budget 회귀 (채택 — 경량)

GSD `tests/workflow-size-budget.test.cjs`(파일당 byte 상한, XL 90KB, Codex `project_doc_max_bytes` 32,768 truncation 과 정렬 — `cards/gsd.md` §4)를 차용해, adapter bootstrap(`CLAUDE.md`/`AGENTS.md`)·always-load 문서에 **byte 예산 회귀 테스트**를 건다. bootstrap 비대화가 런타임 truncation 을 조용히 유발하는 것을 조기 감지. 기존 bootstrap footprint 규율(CLAUDE.md "비확장" 운영 정책, token-ceremony 관심사)과 연결. 저비용·직교라 phase 2 보조로 묶는다.

## 7. b2 — 포터블 행동 규율의 core 승격 범위 (★ 사용자 논의 안건 — 전면 확정 금지)

감사 b2·6-1·6-2: 말투·간결·pause·자율·후속동기화·"무조건 브랜치" 같은 행동 규율이 **Claude bootstrap 에만 풍부**하고 Codex/OpenCode 는 4줄 → 런타임 전환 시 행동 계약이 조용히 빈약해진다. 단 `core/DESIGN_PRINCIPLES.md:196`·`:133` 은 "메인 에이전트 응답 메타 원칙은 runtime adapter bootstrap 이 single source"라고 **core 가 명시 위임**한 자리 — 감사도 "어디까지 core 로 올릴지가 설계 판단"이라 판정.

⇒ 본 spec 은 **전면 확정하지 않는다.** 옵션 스펙트럼과 트레이드오프만 정리하고 사용자 결정에 부친다:

| 옵션 | 무엇 | 장점 | 단점/리스크 |
|---|---|---|---|
| **A. 현행 유지** | 행동 규율을 Claude bootstrap single source 로 둠 | DESIGN_PRINCIPLES 위임과 정합, 변경 0 | Codex/OpenCode 전환 시 톤·자율·후속동기화 계약 빈약(6-2 잔존) |
| **B. roles/ 승격** | 최소 포터블 행동 계약을 `roles/`(또는 신설 `roles/response-policy.md`)에 두고 세 어댑터가 참조 | 런타임 무관 최소 계약 확보, 어댑터별 상세는 유지 | roles/ 의미 확장(현재는 에이전트 역할 카탈로그) — 경계 재정의 필요 |
| **C. core 승격** | 응답 메타 원칙 자체를 core(CONVENTIONS/DESIGN_PRINCIPLES)로 올림 | 최강 단일 계약, 3어댑터 동일 참조 | DESIGN_PRINCIPLES 의 "adapter single source" 위임을 뒤집음 — core 계약 변경(파급 큼) |

- **부분 채택 여지**: 6-1("무조건/애매하면 브랜치" 휴리스틱)은 _운영 안전 규칙_ 이라 core `OPERATIONS.md §5.10` 규모 분기표 승격이 상대적으로 자명(감사 제안). 반면 6-2(말투·자율·후속동기화)는 위임 경계라 논쟁적. **두 개를 분리 결정**할 수 있음을 옵션에 명시.
- research 대응: override/포터블 계층 물리 분리 패턴(spec-kit `overrides>presets>extensions>core`, BMAD 3-layer, Agent OS profile inheritance — `analysis_summary.md` §4-(3))이 B/C 의 참고 선례. 단 "어디까지"는 여전히 우리 설계 판단.
- **본 spec 의 입장**: b2 를 **미결(open) 결정**으로 등재(§11 HLS-OPEN-1). phase 확정 전 사용자 논의 필요.

## 8. 기각·비채택 (근거와 함께)

| 항목 | 판정 | 근거 |
|---|---|---|
| **파일 복사식 스캐폴딩** (claude-flow init 모델) | **기각(반면교사)** | 프레임워크 스스로 367개 중복 SKILL.md drift(#1834)를 겪음 — 배포 모델의 구조적 취약성 자증(`cards/claude-flow.md` §3·§6). 우리의 §0.5 canonical+예외가 정반대 방향 |
| **spec-kit registry + placeholder projection** (research 후보 2) | **범위 한정 보완** | 우리는 이미 유사 converter(`sync-native-*.py`)·심링크 projection 보유 → 한계효용 낮음(`06_implementation.md` §2 후보2·§5 리스크). 후보 1(hash-manifest)을 대체 못 함 |
| **Claude 공식 version/SHA-pin** (research 후보 3) | **범위 한정** | _외부_ 컴포넌트 소비 경로 최적. **우리가 만든** core→adapter _내부_ sync 엔 부적용(양방향 3-way merge 부재, 공식도 자인 — `06_implementation.md` §2 후보3, `analysis_summary.md` §4-(4)) |
| **hook 실행 격리의 lesser-runtime 재현** | **불가(정직 인정)** | 어떤 도구도 없는 runtime 에서 hook 실행 격리를 진짜 재현 못 함 → skip+warning 수준이 최선(§6.1, research §4-(6)·§5) |

## 9. Module 구조 (확정 — 코드 생성은 autopilot-code)

```
tools/
  build-manifest.py            # (증분) surface 파생 + hash-manifest 산출 — b4·b1(i)
  check-adaptation-boundary.sh # (증분) 런타임 실행본 검증 + 파생집합 iterate + 예외목록 대조 — b3·b4
  <canonical-sync 도구>         # (신규 후보) collapse 실행 + 예외 baseline 검증 (GSD install.js 정독 후 확정)
hooks/ tools/ utilities/       # 최상위 = 유일 canonical (진실)
adapters/claude/{hooks,tools,utilities}/
                               # SAME/STALE → canonical 로 symlink 접기(collapsed)
                               # wrapper/delta 예외만 물리 유지 + 예외목록 등재
<가드 옆 예외 선언 파일>         # {파일, 클래스, 사유, delta baseline} — ADAPTATION.md §6 exemption 계약
core/ADAPTATION_INVENTORY.md   # 파일목록 부분 = 파생값 대조, prose = 사유만 (b4)
utilities/dispatch-liveness.sh # runtime-root 해석으로 정정 (b3 §4.1)
```

- 신규 코드 최소화 — 대부분 `build-manifest.py`·`check-adaptation-boundary.sh` 증분 + symlink 전환. hash-manifest 도구만 신규 후보(규모는 GSD 정독 후 결정).
- 지침 파일(core/adapters) 문구 변경은 소유 스킬(core-first) 경유 별도 — 본 spec 은 _구조_ 만 확정.

## 10. Next (구현 phase 분할 — autopilot-code, 본 v1 입력)

`/autopilot-code --mode dev "harness-layer-sync 구현"` (worktree 브랜치). **선행 조건: GSD `bin/install.js`·`state-transition.cjs` 실코드 정독**(§3.2, research gate).

### Phase 1 — 복제 제거 + 가드 확장 (저위험, 즉효)
1. **STALE 2건 재동기**(S-1 spec-read-marker·S-2 harness-status) → canonical 로 symlink 접기. 응급 저위험 fix(카드 00 "즉시 응급패치").
2. **SAME 20건 collapse** — canonical 로 symlink 전환, 무행동변화 확인(가드·drill 회귀).
3. **S-4 6건 파일별 판정** — wrapper/delta 예외 vs stale. 예외는 목록 등재, stale 은 collapse.
4. **가드 확장(b3)** — `check-adaptation-boundary.sh` 가 런타임 실행본을 검증하도록. `:784` 류 공유본-only assertion 을 실행본까지.
5. **dispatch-liveness runtime-root 정정(§4.1)** — `PROJ` 를 runtime-root 기준으로. non-profile 경로 DEAD 오탐 회귀 테스트.

### Phase 2 — manifest · INVENTORY 파생 · 보조
6. **hash-manifest(b1-i)** — 예외(delta) 파일의 canonical baseline 바인딩. GSD 정독 결과 반영. `build-manifest.py` 증분.
7. **INVENTORY 파생(b4)** — 하드코딩 열거(`:788` 등)를 파생집합 iterate 로. ledger 파일목록 부분 = 파생 대조, prose = 사유만.
8. **보조**: parity-loss warning 가드(§6.1) + bootstrap byte-budget 회귀(§6.2).

### Phase 외 (사용자 논의 후 별도 사이클)
- **b2 행동 규율 승격(§7)** — HLS-OPEN-1 해소 후. 6-1(무조건 브랜치)/6-2(응답 메타) 분리 결정 가능.

검증: 각 phase 후 `tools/check-adaptation-boundary.sh` + `loops/drill/run.sh`(지침 회귀) + collapse 전후 hook 동작 diff(무행동변화 증명). Phase 1 은 산출물·안전 hook 무회귀가 통과 기준.

## 11. 결정 목록

- **HLS-1**: 최상위 `hooks/`·`tools/`·`utilities/` = 유일 canonical. Claude 런타임도 canonical(또는 파생)을 실행 — 물리 복사본 제거(collapse). (§0.5·§3, 감사 b1 (iii))
- **HLS-2**: 복제 불가피/의도적 파일만 **명시 예외 목록** — wrapper / delta 2클래스, 사유 필수. collapse 가 기본, 예외가 증명 부담. (§3.1, ADAPTATION.md §6 exemption 계약)
- **HLS-3**: delta 예외는 **hash-manifest 로 canonical 바인딩** — patch 외 divergence 시 가드 red. GSD-style. 세부는 GSD 실코드 정독 후. (§3.2·§3.3, 감사 b1 (i))
- **HLS-4**: 신규 시스템 아님 — `build-manifest.py`·`check-adaptation-boundary.sh` 증분. (§3.3, research "증분 원칙")
- **HLS-5**: parity 가드 검증 대상 = 공유본이 아니라 **런타임 실행본**(settings.json 경로 추종). S-1 이 통과한 구멍을 닫음. (§4, 감사 b3)
- **HLS-6**: **runtime-root ≠ AGENT_HOME** 구분 명문화. transcript/liveness 는 runtime-root 해석. dispatch-liveness `PROJ` 정정. (§4.1, 2026-07-09 실측)
- **HLS-7**: surface 집합은 **파일시스템 파생**(build-manifest), 하드코딩 열거 폐기. ledger prose = 사유만. (§5, 감사 b4·ADAPTATION.md §6)
- **HLS-8**: parity-loss = **explicit warning**(silent skip 금지). hook 실행 격리 lesser-runtime 재현은 불가로 정직 인정. (§6.1, ruler 반면교사)
- **HLS-9**: bootstrap **byte-budget 회귀**(GSD size-budget 차용). phase 2 보조. (§6.2)
- **HLS-10**: 파일 복사식 스캐폴딩(claude-flow)·spec-kit registry·Claude SHA-pin 은 기각/범위한정. (§8)
- **HLS-OPEN-1**(미결): b2 포터블 행동 규율 core 승격 범위 = **사용자 논의 안건**. 옵션 A/B/C + 6-1/6-2 분리 결정. phase 확정 전 미정. (§7, 감사 b2·6-1·6-2)

## 12. 의미↔규칙 경계 체크 (DESIGN_PRINCIPLES §0.7)

- **규칙 구간(코드로 강제)**: canonical collapse·예외 baseline·런타임 실행본 검증·surface 파생·byte-budget — 전부 결정론 가드/생성기(§0.5). "어긋남"을 사람 vigilance 가 아니라 바인딩으로 잡는 것이 본 spec 의 전부.
- **의미 판단 구간(사람/LLM)**: (1) S-4 파일이 "진짜 adapter-specific(delta 예외)"인지 "stale(collapse)"인지의 _판정_ — phase 1 에서 파일별. (2) b2 승격 범위 — HLS-OPEN-1, 사용자 결정.
- **충돌**: 없음 — 의미 판단(예외 여부·승격 범위)을 규칙으로 떠넘기지 않고, 판정된 결과만 가드가 집행. b2 를 굳이 확정하지 않고 open 으로 둔 것이 이 경계 존중.
