### Step 4: Generate dashboard sections

> **README 의 독자 = GitHub 사용자뿐** (2026-05-27 재설계). README 는 더 이상 세션 시작 강제 Read 대상이 아니다 (adapter bootstrap 에서 제거 — skill 카탈로그는 자동 주입, 운영 라우팅은 runtime adapter, 흐름 청사진은 WORKFLOW.md on-demand). 따라서 README 는 _의미 지도_ 로만 짠다 — 옵션 spec·trigger 룰·QA 정의·상세 그래프는 _넣지 않고 canonical 에 링크_. 분량은 _순 감소_ 가 목표 (디테일을 다른 파일로 복사 X — 이미 canonical 에 있으면 drop + link).

#### 4a. 워크플로우 흐름 — 트랙별 텍스트 체인 (mermaid 안 씀)

README 는 _4 트랙_ (문서 / 연구·실험 / 앱 / 라이브러리·CLI) 을 _트랙마다 `### 헤딩 → 텍스트 화살표 체인 (```text 코드 블록) → 설명 한 문단`_ 순서로 짝지어 배치한다. **mermaid 안 씀** — GitHub 기본 mermaid 테마가 투박하고, 텍스트 화살표 체인이 어디서나 동일하게 렌더되며 WORKFLOW.md §1.1 ASCII 방식과 일관. 반복 자리는 `↻`, 단계 구분은 `  →  `.

예 (문서 트랙):
```text
analyze-project / autopilot-research  →  autopilot-draft  →  autopilot-refine ↻  →  autopilot-apply
```

> 트랙 4 개 (📄 문서 / 🔬 연구·실험 / 💻 앱 / 📦 라이브러리·CLI) 를 각각 _체인 → 설명_ 순서로. 4 트랙 뒤 본문은 점검·정정·사용자 프로필 한 줄 quote + 체이닝 청사진 reference (WORKFLOW.md) + 이름 읽는 법 한 줄.
>
> **_넣지 않음_ (의도적 drop + link)** — (1) mermaid 다이어그램 일체 (GitHub 렌더 투박 — 텍스트 체인으로 대체), (2) 전체 Skill 호출 그래프 (6 카테고리 의존) → WORKFLOW §1.1·§3.2, (3) 산출물 I/O 그래프 → WORKFLOW §4 + CONVENTIONS §5, (4) Agent 호출 구조. canonical 에 이미 있으므로 _복사하지 말고 drop_.

#### 4b. README 본문 구조 (canonical layout — meaning-first 의미 지도)

`<agent-home>/README.md` 가 본 sync 의 단일 진실 출처 (reference layout). sync 시 다음 순서로 9 섹션을 채운다:

1. **Header** — center div: title + 한 줄 설명 + 섹션 anchor 링크 (첫 anchor = §2 모드). sync 시각·이력은 git commit log 가 단일 출처. **존재의의 blockquote(🧬 model-agnostic skeleton + DESIGN_PRINCIPLES §0 링크) 는 사람 유지 영역 — 현행 보존, 덮어쓰지 않음.**
2. **🚦 작동 방식 — 📌tracked ↔ ⚡untracked** (_최상단 토대 섹션_) — hook 이 _신규 산출물 생성 순서_ 만 강제(신규 spec←research, plan←spec, 문서←research); 기존 편집·소스 코드는 convention. 두 모드 표 (**📌tracked** = 생성 순서 차단 + adapter status/reminder surface 가 WORKFLOW 따름 표시 / **⚡untracked** = 전부 우회·면제 신호·adapter toggle surface) + toggle 예시(Claude `/track`, Codex/OpenCode `preflight.sh track`) + 한 줄 quote(편집은 소유 스킬 권장·convention). 단일 출처 = `hooks/artifact-guard.sh`·`utilities/workflow-guard-hook.sh`·`utilities/workflow-toggle.sh`·runtime adapter docs·`core/WORKFLOW.md` §0(tracked 계약). **[§2 의도]** §2 도입 1문장에 "결정론적으로 가능한 건 코드(hook/script/gate/DB)가 강제 — 에이전트 판단은 진짜 비결정 자리에만"을 노출. 단일 출처 링크 = [`core/DESIGN_PRINCIPLES.md §0.5`](core/DESIGN_PRINCIPLES.md). callout 1문장 보강 수준, 큰 블록 신설 X.
3. **🧭 Mental model** — 핵심 한 단락 (자연어로 부르면 메인 에이전트가 컨텍스트 읽어 옵션 조립·컨펌·실행 / 각 runtime adapter 가 capability 를 자기 native surface 로 노출 / 사용자는 운전자) + bullet 3 (autopilot-\* = 추적형 파이프라인 / 직접 처리 = 가벼운 일·단 산출물 직접 Edit 은 📌tracked hook 차단 / 입력은 `<artifact-root>/` 자동 발견·cross-project 별 세션) + _의미 지도_ quote (옵션 spec·trigger·QA 는 capability spec·CONVENTIONS·runtime adapter·adapter-native surface 가 단일 출처, 링크만). **[§3 의도]** bullet 에 "코드 본작업은 작업 브랜치(worktree 격리) · 기억 추가=외부 자동 / 정리·삭제=세션끝 deep curator" 한 줄 추가. 디테일은 복사하지 말고 [`core/MEMORY.md §7`](core/MEMORY.md)·[`core/DESIGN_PRINCIPLES.md §7`](core/DESIGN_PRINCIPLES.md) 링크만.
4. **🌳 큰 갈래 4 트랙** — 트랙마다 `### 헤딩 → 텍스트 화살표 체인 (위 4a, mermaid 아님) → 설명 한 문단` 을 순서대로 짝지어 배치 (문서 / 연구·실험 / 앱 / 라이브러리·CLI — 왜 이 순서 / 무엇을 남기나) + 점검·정정·사용자 프로필 한 줄 quote + 체이닝 청사진 reference ([`core/WORKFLOW.md`](core/WORKFLOW.md)) + 이름 읽는 법 한 줄.
5. **📋 Skill 카탈로그 — 의의·핵심** — name (portable capability 링크) / _의의_ (왜 있나 + 핵심) 2 컬럼 표. _역할 dump·옵션 컬럼 X — 왜 존재하는지 중심_. 표 직후 sub-skill 한 줄 (autopilot 내부 자동 호출) + 세부 옵션은 adapter-native surface(Claude Skill `argument-hint`, Codex/OpenCode capability/mode map wrapper) / QA 정의는 CONVENTIONS §1 reference. **[§5 의도]** 표 도입 1~2문장 = "무엇을 부르면 무엇이 되나(자연어 발화→동작) = 사용자 API 표면" framing. 큰 재편 X, §7 부르는 법과 중복 금지 — 표 도입부 문장 수준.
6. **📦 산출물의 구조적 의미** — per-project (`<artifact-root>/`) vs cross-project (`user_profile/`) 두 축. per-project 는 _폴더 / 무엇이 쌓이나_ 작은 표 (analysis_project·research·documents·spec·plans·experiments), cross-project 는 한 단락 + 3-tier T1/T2/T3 _왜 그렇게 나뉘나_ 한 단락 (사용자는 T1 만 / spec/ 한 폴더 누적) + 상세 매핑 reference (CONVENTIONS §5·§6.5, WORKFLOW §4, runtime adapter bootstrap). **+ 통합 기억 store 단락** (`<agent-home>/memory/` — DB SQLite `memory.db` 단일 SoT, `dump.jsonl` 텍스트 mirror, SessionStart `mem inject` 주입 / SessionEnd `mem sync` 회수). **[§6 통합 기억 의도 — Cluster B/C/D 반영]** 단락에 아래를 1~2문장으로 추가(디테일은 [`core/MEMORY.md §7`](core/MEMORY.md) 링크, 복사 X): (C) 세션 자동 distillation — 외부 detached distiller 가 세션 delta를 distill→`mem add`. 트리거=turn-counter hook(N턴) + SessionEnd 공유 marker. distiller=도구0(`--disallowedTools`)이라 판단만, dispatch 스크립트가 JSON-lines 검증 후 `mem add` 실행(판단↔실행 분리, §0.5). **distiller 분사는 `MEM_DISTILL_ENABLE=1` 일 때만(off=완전 no-op); 현재 enable 됨** — 상시 동작 기정사실로 단정하지 않도록 캐비엣 동반. (D) 결정론-first lifecycle — recall 자동주입 hook(신호어 regex→`additionalContext`), 정리후보 `mem inject` 노출, 정리·삭제는 세션끝 deep curator 가 처리. **추가(가역)=외부 offload / 삭제(비가역)=deep curator** 원칙.
7. **🗣️ 부르는 법** — 두 갈래 한 줄 (자연어 / slash 동일 동작):
   - `### (1) 자연어 발화` — prose (옵션 자동 구성 + 자연어 요약 컨펌 + yes/수정/cancel/자율 진행 + ceremony 큰 (autopilot-\* 전체 + analyze-user) vs 작은 3 컨펌 의무) + [`adapters/claude/CLAUDE.md`](adapters/claude/CLAUDE.md) §0 reference + **자연어 발화 예시 표** (_사람 유지 영역_)
   - `### (2) adapter-native 직접 입력` — prose (의도 명시 = 즉시 invoke) + Claude slash 예시 code block (_축약 5 줄_: autopilot-code / autopilot-draft / autopilot-refine / audit / **track**(📌↔⚡ 토글), Codex/OpenCode 는 wrapper 표면으로 설명 — 전체 syntax dump X) + 전체 옵션은 adapter-native surface reference.
8. **🤝 Agents** — name (agent .md 링크) / model role / _의의_ 표 (_자동 호출자·역할 dump X_) + 직접 호출 안내 한 단락 + 사용자 프로필 참조 매트릭스는 [`core/MEMORY.md §7.6`](core/MEMORY.md) reference (대시보드 README 에 매트릭스 표 _넣지 않음_).
9. **📚 더 깊이 + 🔁 동기화** — canonical 문서 reference index 표 (**MANUAL**(앞층 사용자 지도) / **CORE+adapters** / **capabilities+roles** / **INSTALL_LAYOUT**(neutral repo + runtime home projection) / **adapters/claude/CLAUDE.md** / **adapters/codex/AGENTS.md** / **adapters/opencode/AGENTS.md** / **core/WORKFLOW.md** / **core/CONVENTIONS.md** / **core/OPERATIONS.md**(git·worktree·dispatch·push §5.8~5.11) / **core/MEMORY.md**(통합 기억 §7 + 프로필 매트릭스 §7.6) / **core/HOOKS.md**(portable hook invariant catalog) / **core/DESIGN_PRINCIPLES.md** + **harness 행**: `hooks/`(생성순서·git상태·spec게이트·디자인·**메모리 4종**: `builtin-memory-guard`·`mem-recall-inject`·`mem-turn-nudge`·`mem-distill-dispatch`)·`utilities/`·adapter status/toggle surfaces(Claude `statusline.sh`/`/track`, Codex/OpenCode preflight wrappers)·`tools/memory`(통합 기억 store + `mem inject`/`mem sync`, MEMORY §7)·`tools/build-manifest.py`(정의 → 루트 `manifest.json` 단일계약 기계 전사, Step 6b) · `tools/check-adaptation-boundary.sh`(adapter/projection 경계 검증) · `tools/skill-conformance/{scan,check}.sh`(정량 규범 + invocation registry gate, CONVENTIONS §5.6a) + **loops 행**: `loops/README.md` — **현역 루프·호칭은 `loops/README.md` 현역 표가 단일 출처** (cron runner 가 `loops/` 밖[worklog-board cron 등]으로 이동한 현역 루프도 포함 — "`loops/` 파일 부재 = 루프 부재" 아님); §10 파일 트리만 `loops/` 실제 파일을 나열) + `/sync-skills` 두 명령 + GitHub 링크. **[§9 harness 의도]** hooks 카운트 hardcode 금지 — 카테고리 묶음(생성순서·git상태·spec게이트·디자인·메모리 4종)으로 표기. memory hook 4종 병기 필수. **[§9 loops 의도]** 현역 루프 판정은 `loops/README.md` 현역 표 기준(runner 외부 이동 케이스 포함) — `ls loops/` 파일 유무로 현역 여부 판정 금지.
10. **🗺️ 전체 디렉토리 맵** (🔁 동기화 직전 배치) — `<agent-home>/` 트리 + 항목별 한 줄 의미 (```text 블록). tier1 공통 문서는 `core/` 아래를 canonical 로, adapter bootstrap 은 `adapters/<adapter>/` 아래를 canonical 로 표시한다. 루트에 tier1 compatibility symlink 를 나열하지 않는다. runtime home projection 은 `INSTALL_LAYOUT.md` / adapter README 에서만 설명한다. sync 시 실제 `ls` 와 대조해 신규·삭제 디렉토리 반영 — **hooks·loops·drill cases 에 명시 적용**: 부재 파일(예: `loops/note.sh` — runner 가 worklog-board 로 이동) 줄 제거, drill cases 범위는 실제 `ls cases/` 가 진실. **단 §10 파일 트리에서 runner 가 빠진 것이 곧 루프 사망은 아님 — 현역 루프 목록은 §9 가 `loops/README.md` 현역 표 기준으로 든다.** harness 런타임 자동 생성 폴더(backups·cache·sessions 등)는 마지막 한 묶음. 루프 호칭은 `loops/README.md` 가 단일 출처.

원칙:
- prose 최소화, 표·bullet 우선. 단 §7.(1) _자연어 발화 예시 표_ 는 핵심 anchor 라 단단히 유지.
- 같은 정보 반복 X — 옵션 spec 은 SKILL.md, autopilot 호출 룰은 runtime adapter bootstrap, QA 정의·폴더 컨벤션은 CONVENTIONS, 체이닝 청사진은 WORKFLOW 가 각각 source. README 는 _의미만_ 들고 나머지는 링크.
- _넣지 않음_ 항목 (의도적 drop + link, 복사 X):
  - 전체 Skill 호출 그래프 mermaid (6 카테고리) → WORKFLOW
  - 산출물 I/O 그래프 mermaid → WORKFLOW §4 + CONVENTIONS §5
  - Agent 호출 구조 mermaid
  - 운영 룰 trigger 표 (skill 별 4컬럼 dump) → runtime adapter bootstrap + 각 SKILL.md
  - 사용자 프로필 참조 매트릭스 → MEMORY.md §7.6
  - slash 전체 syntax block → 축약 4 줄 + SKILL.md
  - Skills 표의 옵션 컬럼

**§7.(1) 자연어 발화 예시 표는 _사람 유지 영역_** — 사람 손길 큐레이션 자료. sync-skills 는 _현행 README 의 §7.(1) 자연어 발화 표 + 그 직전 prose_ 를 그대로 보존하고 (SHA 비교 skip), 나머지만 자동 갱신. 사용자가 직접 편집해도 덮어쓰지 않음.

현행 README 가 본 layout 의 reference. 대규모 변경 시 README 를 먼저 손보고 본 SKILL.md 를 동기화.

### Step 5: Write README.md

`<agent-home>/README.md` 를 4b 의 layout 그대로 작성. 단 _섹션별 자동 갱신 정책_ 이 다름:

| 섹션 | 처리 |
|---|---|
| §1 Header | center div 표지 / anchor 링크(첫 anchor=§2 모드) 자동 갱신 |
| **§2 작동 방식 (harness)** | 두 모드 표 + adapter toggle/status surface(Claude `/track`/statusline, Codex/OpenCode preflight) + auto-scope(spec 유무) 한 줄 + 한 줄 quote 자동 갱신. 단일 출처 = `hooks/artifact-guard.sh`·`utilities/workflow-guard-hook.sh`·`utilities/workflow-toggle.sh`·runtime adapter bootstrap |
| §3 Mental model | 핵심 한 단락 + bullet 3 + _의미 지도_ quote 자동 갱신 (고정 메시지: 자연어 호출·운전자·canonical 링크) |
| §4 4 트랙 | Diagram (개념 1 개) + 트랙별 narrative + 점검·정정·프로필 quote + WORKFLOW reference 자동 갱신 |
| §5 Skill 카탈로그 | name / _의의_ 자동 추출. 옵션·역할 dump 컬럼 X. 새 skill 추가·삭제 자동 반영 |
| §6 산출물 구조 | 두 축 bullet + 3-tier _왜_ 한 단락 + CONVENTIONS·WORKFLOW reference 자동 갱신. 통합 기억 store 단락에 (C) distillation 캐비엣(`MEM_DISTILL_ENABLE=1` 조건부) + (D) 결정론-first lifecycle(추가=외부/삭제=세션끝 deep curator) 1~2문장 포함. 디테일은 MEMORY §7 링크, 복사 X |
| **§7 부르는 법** | **§7.(1) 자연어 발화 예시 표 + 그 직전 prose 는 사람 유지 영역 — 현행 wording 그대로 보존 (SHA 비교 skip).** 단 _섹션 헤딩 자체_ 누락 시 placeholder 헤딩 + 한 줄만 삽입. §7.(2) slash 예시 code block 은 argument-hint 에서 _축약 5 줄_(+`track`) 자동 생성 + ceremony 큰 (autopilot-\* 전체 + analyze-user) vs 작은 3 컨펌 의무·runtime adapter reference 자동 갱신 |
| §8 Agents 표 | name / model role / _의의_ 자동 추출. 자동 호출자 컬럼 X. 사용자 프로필 매트릭스는 표 대신 MEMORY §7.6 reference |
| §9 더 깊이 + 동기화 | canonical reference index 표(+harness 행 — hooks 카테고리 묶음·memory 4종 병기·카운트 hardcode 금지) + loops 행(실제 `ls loops/` 현존 루프만·루프 호칭은 loops/README.md 단일 출처) + 두 명령 + GitHub 링크 |

**sync 시각·이력은 README 본문에 쓰지 않음** (git commit log 가 단일 출처).

### Step 5a: 편집팀 검수 (사용자 영역 wording — LLM 스러운 어조 회피)

Step 5 에서 README 본문 wording 을 자동 생성·갱신한 자리 (§1 Header / §2 작동 방식 / §3 Mental model / §4 4 트랙 narrative / §5 Skill 카탈로그 wording / §6 산출물 구조 / §7.(2) slash 직접 입력 / §8 Agents 표 wording / §9 더 깊이) 는 메인 에이전트가 wording 을 직접 짜므로 _LLM 스러운 인공적 어조_ (풀어쓰기 과잉·모범생 화법·친절 안내체) risk. Step 5 자동 갱신 직후 _같은 turn 안에_ `Agent(편집팀)` _다듬기 모드_ 호출해 검수.

**검수 범위** — Step 5 가 _자동 갱신_ 한 섹션만. _§7.(1) 자연어 발화 예시 표 + 그 직전 prose_ 는 _사람 유지 영역_ (이미 사람 손길 큐레이션) 이므로 검수 제외.

**Prompt 초점** (Agent 호출 시 그대로 전달):
- 풀어쓰기 과잉 정리 (한 줄 표현 가능한 자리)
- 모범생·친절 안내체 ("~가 평등하게 있습니다" / "어느 쪽을 써도 ~합니다") 회피
- 간결·단정 한국어 (`~다` / `~이다` 어미)
- adapter response policy(Claude Code: [`adapters/claude/CLAUDE.md`](../../adapters/claude/CLAUDE.md) §1) + 도메인 트리거 표 _사용자 영역 메타 문서 작성·수정_ 행 준수
- 표·코드 블록·heading 구조·mermaid·링크는 그대로 유지 (의미·구조 변경 X, 어조만)

**Skip 조건** — `--check` 는 drift 보고만이라 Step 5 자체가 안 돌아 검수 무관. `--force` / default 는 검수 포함.

> 본 step 의 규칙: 자동 sync 가 LLM 스러운 어조를 재발시키지 않도록 README 생성물의 편집팀 검수를 의무화한다.
