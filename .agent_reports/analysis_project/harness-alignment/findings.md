# 하네스 3층 정합성 전수 감사 — findings

> 범위: `core/*.md` · `adapters/{claude,codex,opencode}/` · 최상위 공유층(`hooks/`·`tools/`·`utilities/`·`loops/`·`skills/`·`roles/`·`capabilities/`·`manifest.json`) · 런타임 projection(`~/.claude`·`~/.codex`·`~/.config/opencode`).
> 방법: read-only. depth-2 read-only inspector 4기(축 1+6 / 2+3 / 4+5 / 7+runtime)를 병렬 분사 + 오케스트레이터 직접 검증(구조 축). 모든 발견은 실제 파일 Read 로 `file:line` 근거. 미확인 의심은 말미 분리.
> severity: **P0** 즉시 수정(기능·안전 파손) / **P1** 구조적(갱신 시 필연 drift·계약 stale) / **P2** 사소·표기.
> 감사일 2026-07-09 · 브랜치 `principle-audit`.

**한 줄 결론**: 안전 hook·하드순서 게이트·런타임 wiring 은 대체로 정합(P0 0건)이나, 사용자가 느낀 "층 간 어긋남"의 **구조적 진원지는 최상위 공유층(`hooks/`·`tools/`·`utilities/`)이 `adapters/claude/`로 _물리 복제_ 돼 있고 두 복사본을 묶는 symlink/생성 바인딩이 없다**는 데 있다(§S). 이미 fix 하나가 한쪽에만 반영돼 Claude 런타임이 stale 하다. 나머지는 Claude bootstrap 의 intensity/qa 축 stale, 참조 앵커 이동 미반영, ADAPTATION ledger 의 codex hook 과소열거가 무게중심.

---

## §S. 구조 축 — 공유층 물리 복제·divergence (headline, 오케스트레이터 직접 검증)

최상위 `hooks/`·`tools/`·`utilities/` 는 심링크가 아니라 **실디렉토리이며, 그 안 다수 파일이 `adapters/claude/{hooks,tools,utilities}/` 와 inode 가 다른 물리 복사본**이다. 소비 경로가 갈린다:
- **Claude 런타임**: `settings.json` 이 `$HOME/.claude/hooks/*.sh`(= `adapters/claude/hooks/*.sh`, 복사본)를 실행.
- **Codex/OpenCode 런타임**: `adapters/codex/bin/preflight.sh` 가 **공유 최상위 `hooks/*.sh` 를 직접 실행**(`preflight.sh:234` spec-read-marker, `:369` mem-recall-inject, `:373` mem-briefing-inject), utilities 는 `adapters/{codex,opencode}/utilities/*` 가 공유 `../../../utilities/*` 로 symlink.
- **Claude core-* wrapper**: `adapters/claude/hooks/core-first-guard.sh:10`·`core-read-marker.sh:4` 는 `$AGENT_HOME/hooks/*`(공유)로 `exec` 위임 — 이 둘은 의도된 wrapper 라 **drift 아님**(S6 2026-07-09 회귀정합).
- **parity 가드**: `tools/check-adaptation-boundary.sh` 는 공유 `hooks/*.sh`(예 `:784` spec-read-marker, `:746` portable-guards.test)만 assert. adapter 복사본이 공유와 동일한지는 **비교하지 않음**.

즉 "공유(portable) = canonical" 과 "adapter 복사본 = Claude 런타임 실행본" 두 진실이 공존하는데 **동기화 강제가 없다**. 결과로 이미 벌어진 divergence:

### [S-1] Claude `spec-read-marker.sh` 가 relative-path fix 를 누락 — 런타임 stale (parity 가드는 통과) ⚠️P0 후보
- **severity: P1** (P0 후보 — spec 게이트 오작동 가능성)
- 근거:
  - 공유 `hooks/spec-read-marker.sh` 는 상대경로 정규화 블록 보유: `*) fp="$PWD/$fp" ;;` (git `1d97534` 2026-07-01 "fix: accept relative spec read markers").
  - Claude `adapters/claude/hooks/spec-read-marker.sh` 는 그 5줄 부재(git `e83ff5e` 2026-06-29, 이전). `diff adapters/claude/hooks/spec-read-marker.sh hooks/spec-read-marker.sh` → 공유 측에만 `case`/`*) fp="$PWD/$fp" ;;` 5줄 존재.
  - `adapters/claude/settings.json:119` — `sh "$HOME/.claude/hooks/spec-read-marker.sh"` = **fix 없는 복사본 실행**.
  - `tools/check-adaptation-boundary.sh:784` — `grep -Fq '*) fp="$PWD/$fp" ;;' hooks/spec-read-marker.sh` 로 **공유 복사본에만** fix 존재를 강제 → 가드는 green, Claude 는 stale.
  - Codex 는 공유본 직접 실행(`preflight.sh:234`)이라 fix 정상 적용.
- 영향: Claude 런타임에서 prd.md 를 상대경로로 Read 하면 read-marker 경로가 정규화되지 않아 후속 `spec-skill-gate` 의 grounding 판정이 어긋날 수 있음(오차단/오허용). Codex/OpenCode 와 Claude 가 같은 hook 이름으로 다르게 동작.
- 제안: adapter 복사본을 공유본으로 재동기(또는 spec-read-marker 를 core-* 처럼 wrapper 화). 근본은 §S-핵심 참조.

### [S-2] `harness-status.sh` 공유(221줄) vs Claude 복사본(158줄) divergence — Claude 가 git-signal 확장 누락
- **severity: P1**
- 근거:
  - 공유 `utilities/harness-status.sh` (221줄, git `f5a98db` 2026-07-01 "expand harness git status signals"), Claude `adapters/claude/utilities/harness-status.sh` (158줄, git `d7b1612` 2026-06-30, 확장 이전). diff 65줄.
  - `adapters/{codex,opencode}/utilities/harness-status.sh` → `../../../utilities/harness-status.sh`(공유 221줄) symlink. Codex/OpenCode 는 확장본, Claude 복사본은 구본.
  - ADAPTATION_INVENTORY `core/ADAPTATION_INVENTORY.md:61` 은 이를 "portable helper + adapter wrapper" 단일 항목으로 서술하나, 실제로는 독립 divergd 복사본.
- 제안: adapter 복사본 재동기 또는 wrapper 화. 최소한 어느 쪽이 canonical 인지 명시.

### [S-3] canonical 모호성이 acceptance test 자체와 충돌
- **severity: P1**
- 근거: `core/ADAPTATION_INVENTORY.md:113` acceptance test — "`claude_setting/`, `codex_setting/`, `opencode_setting/` remain **projections, not independent semantic sources**." 그러나 최상위 `hooks/`·`tools/`·`utilities/` 는 projection 이 아닌 독립 복사본이고(§S), 그 안 divergd 파일(§S-1/2)이 "independent semantic source" 로 이미 갈라짐. §55/§65 ledger 는 이 둘을 "adapter-native projection, mixed content" 로만 서술해 물리 복제·비동기화 사실을 숨김.
- 제안: (a) 공유↔adapter 복사본 content-parity 를 `check-adaptation-boundary.sh` 에 추가하거나 (b) 복사본을 wrapper/symlink 로 전환해 물리 이중화를 제거. GSD 종합 대상(§summary-b).

### [S-4] 그 밖의 divergd 복사본(감시 목록)
- **severity: P2**
- 근거(diff 라인수, `<shared>` vs `<adapters/claude/>` 동커밋 내 divergence): `hooks/mem-distill-dispatch.sh`(30) · `tools/build-manifest.py`(15) · `hooks/mem-turn-nudge.sh`(6) · `hooks/mem-recall-inject.sh`(4) · `utilities/workflow-guard-hook.sh`(2) · `utilities/agent-worklog-state.sh`(neutral 기본값 vs claude 하드코딩 경로) · `tools/{design-mcp,memory}`.
- 대부분 동일 커밋 내 adapter-specific 조정(경로 fallback 등)으로 보이나, 바인딩 부재로 언제든 §S-1 형 stale 재발 가능. 개별 판정은 후속.
- 제안: 최소한 각 파일 상단에 "공유본 파생/차이 사유" 주석 + parity 체크 대상 등록.

---

## Axis 1 — core↔adapter 내용 drift

### [1-1] Claude bootstrap 이 파이프 경량화를 `--qa quick` 로 표기 — intensity-first 계약 위반
- **severity: P1**
- 근거: `adapters/claude/CLAUDE.md:46` "spec-drift 체크 → `autopilot-code --qa quick`" ↔ `core/CONVENTIONS.md:48`·§3#1(`:131`) "`--qa` … must not choose the stage graph by itself" + `core/WORKFLOW.md:165` "stage graph 는 `--intensity` 가 선택… `--qa` 는 assurance override". Codex(`adapters/codex/AGENTS.md:71`)·OpenCode(`adapters/opencode/AGENTS.md:48` `stage_graph_selector=intensity-not-qa`)는 정정 완료 → Claude 만 stale.
- 제안: `CLAUDE.md:46` → `autopilot-code --intensity quick`(또는 qa 표기 제거).

### [1-2] "함정" 항목이 qa 레벨을 파이프 경중 다이얼로 서술
- **severity: P2**
- 근거: `adapters/claude/CLAUDE.md:120` "처음부터 `--qa thorough`/`adversarial` — 작은 요청은 quick, 본작업은 standard 부터 상향" ↔ `core/CONVENTIONS.md:13`·§3#1 (파이프=intensity, `--qa`=assurance budget).
- 제안: "작은 요청은 `--intensity quick`, 본작업은 standard 부터" 로 축 명확화.

### [1-3] ScheduleWakeup 대기 수치 불일치 (10–30분 vs 15–20분)
- **severity: P2**
- 근거: `adapters/claude/CLAUDE.md:67` "`ScheduleWakeup` 10–30 분" ↔ `core/CONVENTIONS.md:604` "runtime adapter bootstrap 의 pause/autonomy rule **동일**(…CLAUDE.md §2) — ScheduleWakeup **15-20분**". core 가 "동일" 이라 선언하며 다른 수치.
- 제안: 한쪽으로 통일(어댑터가 SoT 이므로 CONVENTIONS:604 을 10–30분으로).

---

## Axis 2 — 어댑터 parity 신고 정확성

### [2-1] ADAPTATION_INVENTORY 의 Codex hook surface 가 실제 7-스크립트를 과소열거(UNDERCLAIM)
- **severity: P1**
- 근거: `core/ADAPTATION_INVENTORY.md:33` location 열은 `hooks.json` + 2개 py(`pretooluse-write-guard.py`, `posttooluse-design-check.py`)만 명시. 실제 `adapters/codex/hooks/hooks.json` 에는 **7개** lifecycle py 가 wired(`sessionstart/sessionend/userprompt/permissionrequest/posttooluse-read-marker/pretooluse-write-guard/posttooluse-design-check`), 가드 `tools/check-adaptation-boundary.sh:788` 도 이 7개를 필수 강제. ledger 파일 목록이 실제·가드와 불일치.
- 제안: `:33` location 을 7-스크립트 + `run-hook.sh` 로 갱신하거나 가드 열거를 단일 출처로 참조.

### [2-2] Codex ADAPTATION.md 요약표/매핑행/prose 가 서로 다른 hook 파일집합 제시(self-inconsistent)
- **severity: P2**
- 근거: `adapters/codex/ADAPTATION.md:50` 요약표 Hook bridge = 3파일, prose(236-315)는 6브리지 서술, "Required Codex Mappings" `:397` 은 5파일(sessionstart/userprompt 누락). 3자 불일치.
- 제안: 요약표·397행을 실제 7-스크립트로 통일.

### [2-3] ADAPTATION_INVENTORY 의 Codex agent 생성경로가 EXTRA_AGENTS(memory-scout) 누락 — OpenCode 행과 비대칭
- **severity: P2**
- 근거: `core/ADAPTATION_INVENTORY.md:30` "Generated from `roles/README.md`" 만 서술. memory-scout 는 roles/README 카탈로그(8행)에 없고 `adapters/codex/bin/sync-native-agents.py:29` `EXTRA_AGENTS` 로 생성. OpenCode 행(`:41`)은 이 경로 명시, Codex 행만 누락 → codex `memory-scout.toml` 이 roles 로 역추적 불가.
- 제안: `:30` 에 OpenCode 와 동일한 EXTRA_AGENTS(§7.4 출처) 문구 추가.

---

## Axis 3 — single-source 위반

*(구조적 최상위 위반은 §S-3 참조.)*

### [3-1] Codex 기본 모델 튜플(gpt-5.4-mini/gpt-5.5)이 한 파일 3곳 + 생성기 중복 기재
- **severity: P2**
- 근거: `adapters/codex/ADAPTATION.md:184-185`·`:418-419`·`:428-432` 3회 재기술 + 생성기 `adapters/codex/bin/sync-native-agents.py:25` DEFAULTS. 변경 시 4곳 수동 동기.
- 제안: 1곳을 기준으로 나머지는 "see Model Mapping" 포인터.

### [3-2] DESIGN_PRINCIPLES 에이전트 로스터가 roles/README(단일출처)와 divergence
- **severity: P2**
- 근거: `core/DESIGN_PRINCIPLES.md:97` 로스터 재기술이 `memory-scout` 누락 + `external-adversary` 만 portable 명 표기(claude 실파일은 `codex-review-team.md`). 단일출처 `roles/README.md:15-22`.
- 제안: memory-scout 추가하거나 "로스터 = roles/README 참조" 포인터로 대체.

---

## Axis 4 — 죽은 참조

### [4-1] report-generation 의 죽은 앵커 `CONVENTIONS §1.4` + 이미 폐기된 QA-default 계약 인용
- **severity: P1**
- 근거: `adapters/claude/skills/autopilot-research/references/report-generation.md:290` "QA level: … default thorough (모든 autopilot-* 통일 — CONVENTIONS.md §1.4)". 실제 `core/CONVENTIONS.md` §1 하위엔 §1.1 하나뿐(§1.4·앵커 부재). "default thorough 통일" 은 `CONVENTIONS.md:71`("assurance normally follows intensity — direct→none/light, quick→quick…") 및 CLAUDE.md 함정과 정면 모순.
- 제안: 앵커를 실존 §1.1 로 교체 + "default thorough" 문구를 intensity-derived 로 수정.

### [4-2] CLAUDE.md 가 `CONVENTIONS.md §5.10` 로 오인용(실 내용은 OPERATIONS.md)
- **severity: P2** (A·C 공통 발견)
- 근거: `adapters/claude/CLAUDE.md:54` "(C) 작업 격리·병렬 디스패치 (`CONVENTIONS.md` §5.10)" + 이어지는 bare `§5.9`/`§5.10`. `core/CONVENTIONS.md:366` 은 "`## §5.8~§5.11 → OPERATIONS.md`" 리다이렉트 스텁(2026-06-23 이동)이고 본문은 `core/OPERATIONS.md:46,78`. 같은 CLAUDE.md `:62` 는 올바르게 "OPERATIONS §5.10" 인용 → 파일 내부 자기모순. (리다이렉트로 최종 도달은 되나 문서명이 틀림.)
- 제안: `OPERATIONS.md §5.10`/`§5.9` 로 정정.

### [4-3] study.md 의 `CONVENTIONS §3.6` — §3 은 하위번호 없는 평 리스트
- **severity: P2**
- 근거: `loops/study.md:14` "CONVENTIONS §3.6 위반". `core/CONVENTIONS.md:129` §3 은 항목 1–9 평 리스트, §3.6 서브섹션 없음. 의도 규칙(왜/날짜 주석)은 §3 항목 8(`:141` 부근).
- 제안: `CONVENTIONS §3(항목 8)` 로 표기.

---

## Axis 5 — 문서↔코드 불일치

*핵심 안전 hook 11종(artifact-guard·builtin-memory-guard·git-state-guard·spec-skill-gate·core-first-guard·workflow-guard-hook·mem-recall-inject·mem-briefing-inject·dispatch-liveness·build-manifest·harness-status)은 문서 서술과 실동작 일치 — P0 없음.* (근거 다수: `hooks/artifact-guard.sh:92-102` 신규생성만 차단·소스 비차단 / `hooks/builtin-memory-guard.sh:22,67` 내장메모리 hard-deny / `hooks/git-state-guard.sh:44-53` merge/rebase/detached deny + `CLAUDE_MERGE_EDIT_OK` 탈출구 / `hooks/mem-recall-inject.sh:98` PAT = `core/MEMORY.md:78` = 테스트 fixture 3자 일치 / `tools/build-manifest.py --check` = up-to-date.) 단, §S-1 은 "동작 일치" 가 **공유 복사본 기준**일 때만 참이라는 점에서 Axis 5 와 교차.

### [5-1] recall 신호어 목록이 CLAUDE.md 에서 6개로 축약(hook 은 8개)
- **severity: P2**
- 근거: `adapters/claude/CLAUDE.md:99` 는 6개(`지난번·예전에·전에·그때·저번에·아까`)로 예시("류"). 실제 `hooks/mem-recall-inject.sh:98` PAT 은 8개(`지난번에`·`이전에` 추가, canonical `core/MEMORY.md:78` 와 일치).
- 제안: CLAUDE.md 예시에 `지난번에·이전에` 보강 또는 "(전체 MEMORY §7.5)" 명시.

---

## Axis 6 — 계층 방향 위반

### [6-1] "무조건 브랜치" 분기 휴리스틱이 Claude 어댑터에만 존재(core 미승격)
- **severity: P1**
- 근거: `adapters/claude/CLAUDE.md:54` "기능 추가·모듈 신설·다파일 변경은 규모 판단 없이 **무조건 브랜치, 애매해도 브랜치 쪽** (drill g3 재발 방지)". core `core/OPERATIONS.md:84-88` 규모 분기표는 "본작업(qa standard 이상·plan 추적)" 만 규정 — "무조건/애매하면 브랜치"·`drill g3` 근거 core 전무(grep 확인). Codex/OpenCode 어댑터에도 부재 → 런타임 전환 시 소실되는 포터블 행동 규칙.
- 제안: 휴리스틱을 `core/OPERATIONS.md §5.10` 규모 분기표에 승격(사유·날짜 인라인=CONVENTIONS §3#8), 어댑터는 참조만.

### [6-2] 응답 규율(§1 말투·간결·약속 / §2 pause·자율 / §3 후속단계 자동)이 Claude 어댑터에만 풍부
- **severity: P1** (core 가 어댑터로 명시 위임한 자리라 "설계상 의도" 여지 있음 — 판단 필요)
- 근거: `adapters/claude/CLAUDE.md:56-77` 상세 vs `core/DESIGN_PRINCIPLES.md:196`·`:133` "메인 에이전트 응답 메타 원칙은 … runtime adapter bootstrap 이 single source"(core 미소유). Codex `adapters/codex/AGENTS.md:82-86`·OpenCode `adapters/opencode/AGENTS.md:68-72` 의 Response Policy 는 4줄뿐 → Codex/OpenCode 사용 시 톤·자율·후속동기화 계약이 조용히 빈약.
- 제안: 포터블 행동 규율의 최소 계약을 core(또는 roles/)에 승격, 세 어댑터 동일 참조. 최소한 Codex/OpenCode Response Policy 에 pause·autonomy·auto-followthrough 보강. **GSD 종합 대상**(어디까지 core 로 올릴지가 설계 결정).

---

## Axis 7 — project 층 어긋남 + 런타임 projection

*하드순서 게이트(research/analyze→spec→plans)·artifact-guard 대상폴더(spec/·plans/·documents/)·`.agent_reports`↔`.claude_reports` 대칭처리는 3층(CLAUDE.md §0·WORKFLOW §0·artifact-guard.sh·artifact-root.sh) 일치 확인. 런타임 wiring(Claude settings.json↔adapter 동일, Codex hooks.json 7이벤트 일치, OpenCode 28/28/9)도 일치.*

### [7-1] drill 회귀 스위트가 신표준 `.agent_reports` 를 사실상 미검증
- **severity: P2**
- 근거: `loops/drill/cases*` 하위 fixture/assert 중 `.claude_reports` 사용 **21개** vs `.agent_reports` **1개**(예 `loops/drill/cases/g5_artifact_guard/fixture.sh`, `g4_spec_gate/fixture.sh`). 구현(`artifact-guard.sh`·`artifact-root.sh`)은 신표준 우선인데 회귀는 legacy 경로만 밟음 → 신표준 default 순서게이트 무방비.
- 제안: g5/g4 중 최소 1개를 `.agent_reports` fixture 로 복제.

### [7-2] `agent-worklog-state.sh` 보드 probe 가 legacy 루트만 인식
- **severity: P2**
- 근거: `utilities/agent-worklog-state.sh:41` `for path in "$board_app" … "$board_app/.claude_reports"` — `.agent_reports` 부재. artifact-root.sh 와 달리 신표준 루트를 `path.missing` 으로 보고(관측 사각). (adapter 복사본도 동일 — §S-4.)
- 제안: probe 목록에 `.agent_reports` 를 `.claude_reports` 앞에 추가.

### [7-3] (전제 정정) OpenCode projection 은 `~/.opencode` 가 아니라 `~/.config/opencode`
- **severity: P2** (문서 아닌 과제 전제 정정 — 실제 wiring 정상)
- 근거: `~/.opencode/` 에는 `bin/opencode` 바이너리만. 실제 projection 은 `~/.config/opencode/`(agent-* 심링크 + `opencode.jsonc` + native `command/`·`agent/` + `plugins/agent-harness-guards.js` 심링크). `adapters/opencode/ADAPTATION.md:36` 도 `~/.config/opencode` 로 명시 → 문서 drift 아님.
- 제안: 후속 감사·문서는 `~/.config/opencode` 를 projection 루트로.

---

## 미확인 / 판단 유보
- **자동 distillation "full parity" 주장**(`adapters/opencode/ADAPTATION.md:195`·`adapters/codex/ADAPTATION.md:598`): 런타임 실행 검증 필요, 정적 감사 범위 밖. 문서는 self-consistent.
- **OpenCode 플러그인 guard throw 실발동**·**Codex hooks.json 실 trust/fire**: 코드·심링크 존재만 확인, 런타임 실행 로그 미검증(ADAPTATION 은 `check-runtime-projection.sh` 로 별도 검증한다고 서술).
- **ADAPTATION_INVENTORY/INSTALL_LAYOUT 의 수십 개 preflight subcommand**: 스크립트 존재는 확인, 각 subcommand 동작 대조는 미수행(후속 감사 권장).
- **§S-4 개별 divergd 복사본**: adapter-specific 의도 vs stale 판정은 파일별 후속 필요.
- `adapters/claude/CLAUDE.md:70` opus/sonnet concrete 모델명: `adapters/claude/ADAPTATION.md:75-76` 매핑에 명시된 정당한 어댑터 모델매핑 → **drift 아님**.

## 집계표

| Axis | P0 | P1 | P2 |
|---|---|---|---|
| §S 구조(공유층 복제·single-source) | 0 | 3 | 1 |
| Axis 1 (core↔adapter drift) | 0 | 1 | 2 |
| Axis 2 (parity 신고 정확성) | 0 | 1 | 2 |
| Axis 3 (single-source) | 0 | 0 | 2 |
| Axis 4 (죽은 참조) | 0 | 1 | 2 |
| Axis 5 (문서↔코드) | 0 | 0 | 1 |
| Axis 6 (계층 방향) | 0 | 2 | 0 |
| Axis 7 (project·runtime) | 0 | 0 | 3 |
| **합계** | **0** | **8** | **13** |

> 이전 감사 잔존 여부: `memory-audit`·`token-ceremony-audit` 산출물과 중복 재발견 없음(그쪽은 메모리 lifecycle·context footprint 축, 본 감사는 3층 정합 축). 기존 발견 잔존 표기 대상 없음.
