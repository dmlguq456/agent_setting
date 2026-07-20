# Release 파이프라인 연쇄 실패 근본원인 조사

- 조사 대상 저장소: `/home/Uihyeop/agent_setting`
- 사고 유발 커밋: `d04ee778f67475bab596cad47d83585a3b60db7e`
- 조사일: 2026-07-20 KST
- 조사 범위: 세션·사이클 귀속, 계획 대비 실제 검증, projection 규범과 적용 여부, 생성 구조와 과거 이력, 동류 재발 표면
- 변경 범위: 이 보고서만 생성. 소스·설정·Git 상태는 수정하지 않음

## 1. 요약 판정

### 1.1 근본원인 분류

| 분류 | 판정 | 핵심 증거 |
|---|---|---|
| 직접 원인 | `d04ee778`이 portable `loops/drill/cases_growing/g11_*`, `g12_*`만 스테이징하고 Claude concrete loop projection을 빠뜨렸다. | Claude transcript `6957...jsonl:980-1010,1079-1080`; 커밋 `d04ee778`의 10개 변경 경로 |
| 기여 원인 1 | 이 변경은 등록된 headless worker나 durable `autopilot-code` 사이클이 아니라 herdr pane 3의 대화형 Claude main 세션에서 `caller.type=direct`로 inline 실행됐다. 그 결과 plan→code-test→report 검증 소유권과 작업트리 격리가 생략됐다. | `herdr-server.log:45559-45568`; `session.json:5-52`; Claude transcript `:860,862,890,928,968,1079-1080`; `core/OPERATIONS.md@d04ee778:79-104` |
| 기여 원인 2 | 세션은 drill case를 “portable fixture”로만 판정해 기존 g9/g10 형식과 `loops/drill/run.sh` 자동 발견만 확인했다. `adapters/claude/loops`, Claude adaptation 문서, boundary checker를 변경 표면으로 확장하지 않았다. | Claude transcript `:972-980`; `tools/check-adaptation-boundary.sh:2901-2926`; `adapters/claude/ADAPTATION.md:136-144,178-188` |
| 기여 원인 3 | 검증은 wrapper 동작과 새 assert의 수동 재현에 집중됐고, 실제 drill runner·conformance pre-stage·`tools/check-adaptation-boundary.sh`·`tools/generate.py --check`는 실행되지 않았다. | Claude transcript `:928-969,1013,1062-1075,1078-1079`; `loops/drill/run.sh@d04ee778:54-84`; 같은 transcript `:1160` |
| 구조 원인 | `loops/`의 Claude realization을 concrete 파일로 두는 설계는 의도적이지만, 생성기는 이를 만들거나 동기화하지 않는다. completeness guard는 누락을 탐지할 뿐이며, 평상시 로컬 commit/push 강제 지점도 없다. 즉 “수동 쌍 생성 + 사후 탐지” 구조다. | 커밋 `b0f462ab`; `adapters/claude/ADAPTATION.md:143-144,178-188`; `tools/generate.py@d04ee778:18-31`; `tools/build-manifest.py@d04ee778:298-335,637-648`; `tools/check-adaptation-boundary.sh:2901-2926` |

최종 분류는 **규범 부재가 아니라, 기존 규범 미준수와 변경 표면 판정 누락이 결합하고, 수동 concrete projection 구조가 이를 release 시점까지 허용한 사고**다.

### 1.2 확정 사실의 취급

요청에 제시된 다음 사실은 재검증하지 않고 조사 출발점으로 사용했다.

- `d04ee778`의 g11/g12 Claude mirror 누락과 Release CI의 6개 push 연속 실패
- `a7dcafb1`의 복구와 v1.27.0 발행 성공
- Claude 로컬 hook에 commit/push 시 boundary checker를 실행하는 강제 지점이 없다는 점

이 보고서는 그 사실의 앞단인 “누가, 어떤 사이클에서, 어떤 검증을 거쳐 누락을 만들었는가”와 구조적 재발 조건을 판정한다.

## 2. 작업 주체와 사이클 귀속

### 2.1 판정: herdr pane의 대화형 Claude main 세션이 inline으로 생성

`d04ee778`의 작업 주체는 등록된 headless worker가 아니라 다음 대화형 세션이다.

- Claude session UUID: `6957f9f2-a2ca-4a0a-9b92-bb34a5c8e96c`
- transcript: `/home/Uihyeop/.claude/projects/-home-Uihyeop-agent-setting/6957f9f2-a2ca-4a0a-9b92-bb34a5c8e96c.jsonl`
- cwd: `/home/Uihyeop/agent_setting`
- runtime entry: interactive CLI
- herdr surface: workspace `w65331bbe36f8b1`, pane 3

근거 사슬은 다음과 같다.

1. herdr 저장 상태는 workspace `w65331bbe36f8b1`의 identity cwd와 pane 1~4의 cwd를 모두 `/home/Uihyeop/agent_setting`으로 기록한다.
   증거: `/home/Uihyeop/.config/herdr/sessions/notes/session.json:5-52`.
2. 커밋 직전 10:24~10:25 KST에 pane 3에서 Claude 프로세스가 다시 활성화된다.
   증거: `/home/Uihyeop/.config/herdr/sessions/notes/herdr-server.log:45559-45568`.
3. 같은 시각·cwd의 Claude transcript에서 사용자가 직접 입력한 `작업 시작해.`가 기록되고, 이후 모든 Bash/Edit/Write 호출의 caller가 `direct`다.
   증거: transcript `:860,862,890,928,949,968,980,1079`.
4. 커밋·push 명령 자체가 transcript line 1079의 direct Bash 호출이다. 결과 line 1080은 `[main d04ee778]`, 10개 파일, `eaaa8922..d04ee778 main -> main`을 기록한다.
   증거: transcript `:1079-1080`.

herdr 로그 자체는 pane 번호와 Claude session UUID를 한 행에 결합하지 않는다. 따라서 pane 3↔UUID 매핑은 cwd·시각·interactive prompt·commit 결과를 교차한 **높은 확신의 귀속**이다. 반면 “대화형 main 세션이며 headless worker가 아니다”는 typed human prompt, `entrypoint=cli`, direct caller, main checkout commit으로 직접 확인된다.

### 2.2 두 plan 디렉터리와의 관계

#### `2026-07-20_memory-oncall-promotion-merge`

이 사이클은 d04의 **발단이 된 depth-2 침묵사**를 제공했지만 d04를 만든 구현 사이클은 아니다.

- 원래 route는 `autopilot-code · dev/refactor · strong`, 별도 worktree, depth-1 owner와 `code-plan → code-execute → code-test → code-report`였다.
  증거: `.agent_reports/plans/2026-07-20_memory-oncall-promotion-merge/owner_blocked.md:3-17`.
- 등록된 세 차례 code-plan worker는 각각 3·4·2 JSONL 행만 남기고 typed handoff나 plan artifact 없이 종료했다. source review, projection generation, test, report stage는 실행되지 않았다.
  증거: 같은 파일 `:21-47`.
- root acting owner가 이후 inline fallback을 기록했고, 보상 검증 항목에는 durable plan, repository contract regressions와 final verification이 있었다.
  증거: `.agent_reports/plans/2026-07-20_memory-oncall-promotion-merge/_internal/metrics.md:3-16`.
- 이 사이클의 plan은 memory/oncall 변경에 대해 core/adaptation boundary와 manifest/generated projection 검사를 명시했다.
  증거: `.agent_reports/plans/2026-07-20_memory-oncall-promotion-merge/plan/plan.md:81-110`.
- 실제 boundary PASS는 clean worktree의 병합 커밋 `eaaa8922`에 대한 것이며, 보고서는 concurrent `dispatch-headless.py`와 drill 2건을 병합 인덱스에서 제외했고 이후 별도 `d04ee778`로 완료됐다고 명시한다.
  증거: `.agent_reports/plans/2026-07-20_memory-oncall-promotion-merge/test_logs/test_report.md:3-9,22-40,56-65`; `final_report.md:9-12,48-63`.

따라서 memory cycle의 boundary PASS를 d04의 검증으로 간주할 수 없다. 검증 대상 commit과 worktree가 다르다.

#### `2026-07-20_namespace-safe-stage-dispatch`

이 사이클은 d04 이후의 후속 remediation이므로 d04의 생성 주체가 아니다.

- plan은 d04가 silent death를 exit 77 typed failure로 바꿨지만 stage 완료를 가능하게 하지는 못했다고 과거형으로 기록한다.
  증거: `.agent_reports/plans/2026-07-20_namespace-safe-stage-dispatch/plan.md:25-32`.
- 이 후속 plan은 focused suite 뒤 dispatch·route·liveness·Fleet·projection·boundary 검증을 명시한다.
  증거: 같은 파일 `:13-19`.
- task brief도 completion evidence로 기존 projection과 boundary check의 green 상태를 요구한다.
  증거: `.agent_reports/plans/2026-07-20_namespace-safe-stage-dispatch/_internal/task_brief.md:91-102`.

즉 적절한 후속 durable cycle에는 boundary가 들어갔지만, d04를 만든 즉석 inline continuation에는 들어가지 않았다.

## 3. d04 작업의 경위와 실제 검증

### 3.1 경위

1. 사용자는 memory-oncall code-plan worker 세 건의 침묵사를 전달하고 원인과 drill이 이를 놓친 이유까지 검수해 달라고 했다.
   증거: Claude transcript `:812`.
2. Claude는 PID namespace lifetime 결함, wrapper 감시 사각, liveness 오귀속을 진단했다. 동시에 fail-fast와 drill 신설은 stage-dispatch spec 개정이 걸리므로 “route card 승인 후 별도 사이클”로 올리는 것이 맞다고 결론 냈다.
   증거: transcript `:856`.
3. 사용자가 `작업 시작해.`라고 승인했다. 이는 직전 설명대로라면 별도 spec/route 사이클의 시작 승인이었다.
   증거: transcript `:860`.
4. 그러나 다음 응답부터 별도 spec/plan cycle을 열지 않고 현재 main checkout에서 직접 adapter 구현을 시작했다.
   증거: transcript `:862-925`.
5. adapter edit가 core-first hook에 두 번 거부된 뒤, 세션은 `core/OPERATIONS.md §5.10`만 읽고 구현을 계속했다.
   증거: transcript `:883,890-899`.
6. wrapper 변경 뒤 portable g11/g12 디렉터리만 만들고 파일을 썼다.
   증거: transcript `:972-1010`.
7. g11 수동 재현이 인자 분리와 process-leak assertion 문제로 두 차례 실패한 뒤 수정돼 PASS했고, g12 수동 재현도 PASS했다.
   증거: transcript `:1013-1075`.
8. 곧바로 portable case 두 디렉터리와 adapter wrapper 두 파일만 `git add`해 commit/push했다.
   증거: transcript `:1078-1080`.

사용자의 `작업 시작해.`가 material-work 승인으로 기능할 수는 있다. 그러나 승인 직전 세션이 예고한 것은 별도 spec/route cycle이었고 실제 실행은 main inline 구현이었다. `core/WORKFLOW.md@d04ee778:147-188`은 같은 route와 scope의 직전 승인만 재사용하고 material change에는 재확인을 요구한다. 따라서 핵심 위반은 “카드 문구를 생략했다”보다 **승인받은 실행 형태와 실제 실행 형태가 달라졌는데도 durable route를 열지 않은 것**이다.

### 3.2 계획·주장·실행 비교

| 검증 항목 | 계획 또는 주장 | 실제 관찰 | 판정 |
|---|---|---|---|
| syntax | wrapper 문법 검사 | 두 wrapper에 `python3 -m py_compile` 실행 | 실행됨 — transcript `:928-929` |
| namespace detector | 밖 False, 안 True | `pid_namespace_scoped()`를 host/unshare 양방향 실행 | 실행됨 — `:949-950` |
| 양 wrapper 실거부 | unshare에서 Claude/Codex typed reject | 반복 probe 후 양쪽 `nested-sandbox-lifetime` 확인 | 실행됨 — `:930-959` |
| override spawn | override에서 spawn 진행 | `AGENT_DISPATCH_ALLOW_NAMESPACED_SPAWN=1`, `started=1` 확인 | 실행됨 — `:951-952` |
| 기존 sd15/sd45 | Claude/Codex 각 2 suite | shell 2개, Python 2개 실행, 모두 PASS/OK | 실행됨 — `:968-969` |
| g11 assert | 새 회귀 assert | fixture를 직접 구성해 assert script만 실행; 실패 두 건 수정 후 PASS | 수동 재현 — `:1013,1062-1073` |
| g12 assert | 새 회귀 assert | fixture를 직접 구성해 assert script만 실행, PASS | 수동 재현 — `:1074-1075` |
| 실제 drill runner | commit 메시지의 “drill assert 수동 재현 PASS” | `loops/drill/run.sh`는 실행하지 않음. 세션도 나중에 “drill 회차 자체는 안 돌렸다”고 명시 | 미실행 — `:1160` |
| conformance pre-stage | full drill이면 boundary 실행 | 실제 runner가 호출되지 않아 발화하지 않음 | 미실행 — `loops/drill/run.sh@d04ee778:54-84` |
| adaptation boundary | canonical↔adapter completeness | commit 전 실행 기록 없음 | 미실행 — 실행이 끝난 `:1074-1079` 사이에 해당 command 없음 |
| generated projection check | generator-owned drift | 실행 기록 없음 | 미실행 |
| durable code-test | standard+ final verify | plan/checklist·test report·code-test stage 없음 | 미실행 |
| isolated worktree | multi-file feature 변경 | main checkout에서 direct edit/commit | 미준수 |

커밋 메시지의 좁은 검증 주장은 transcript와 대체로 일치한다. 문제는 그 검증이 **변경된 wrapper의 동작 정확성**에는 집중했지만 **새 portable path의 adapter projection completeness**에는 닿지 않았다는 점이다. “수동 assert PASS”는 case의 assert logic을 검증했을 뿐, 저장소 전체 drill/conformance 또는 release boundary를 검증했다는 뜻이 아니다.

## 4. projection 검증 규범은 있었는가

### 4.1 규범 존재: 예

사고 커밋 시점의 저장소 규범은 boundary/projection 검증 소유권을 이미 명시했다.

- `core/CONVENTIONS.md@d04ee778:7`은 `tools/check-adaptation-boundary.sh`가 adapter boundary를 검증한다고 명시한다.
- 같은 파일 `:15-35`는 `verify`를 concrete checker·consistency·drift check로 정의하고 standard/strong에 plan과 verify를 요구한다.
- 같은 파일 `:62`는 `code-test`가 rigor에 맞춰 concrete verification을 수행한다고 정한다.
- 같은 파일 `:147-155`는 mechanically expressible invariant를 deterministic tooling/test에 넣고 canonical-to-adapter boundary의 소유 command를 `tools/check-adaptation-boundary.sh`로 지정한다.
- `core/OPERATIONS.md@d04ee778:79-86`은 adapter/projection 변경도 core-first이고 실제 edit·test·QA는 isolated worktree에서 수행한다고 정한다.
- 같은 파일 `:90-104`는 main이 기본 executor가 아니며 multi-file/feature standard+ work는 worktree와 dispatch를 사용한다고 정한다.
- 같은 파일 `:96`은 standard+ inline 예외 사유를 plan metrics에 기록하지 않으면 contract violation이라고 명시한다.
- `adapters/claude/ADAPTATION.md:143-144,178-188`은 loops와 scaffolds를 adapter-owned concrete realization으로 분류한다.
- `core/ADAPTATION_INVENTORY.md:69-71`도 scaffolds·loops·tools를 shared source와 concrete Claude projection의 mixed surface로 기록한다.
- 사고 시점의 `check_claude_loop_projection`은 `loops/` 아래 non-ignored 모든 path를 순회해 `adapters/claude/loops/<rel>` concrete counterpart가 없으면 실패한다.
  증거: `tools/check-adaptation-boundary.sh@d04ee778:2901-2927`.

특히 같은 실패 클래스가 이미 알려져 있었다.

- skill-design-refactor PRD는 tools/frozen case 변경 시 Claude concrete mirror를 byte-identical하게 동기화하지 않으면 `check_claude_loop_projection` 또는 tool projection check가 실패한다고 적는다.
  증거: `.agent_reports/spec/skill-design-refactor/_internal/versions/v2/prd.md@d04ee778:119-126`.
- 2026-07-13 test log에는 `adapters/claude/loops/drill/cases_growing/g_stage_dispatch`와 네 파일이 없어서 boundary가 실패한 정확한 선례가 남아 있다.
  증거: `.agent_reports/plans/2026-07-13_dispatch-routing-policy-v7/test_logs/06_adaptation-boundary.log@d04ee778:1-10`.

따라서 “loops를 건드리면 projection 검증을 해야 한다는 규범이 없었다”는 판정은 증거와 맞지 않는다.

### 4.2 왜 적용되지 않았는가

판정은 다음 두 원인이 결합한 것이다.

#### A. 규범 미준수

- 세션은 스스로 별도 spec/route cycle이 필요하다고 결론 내렸으나 승인 직후 current main에서 direct implementation으로 전환했다.
  증거: transcript `:856,860,862`.
- multi-file feature임에도 durable plan, code-test stage, isolated worktree, inline exception metrics가 없다.
  규범 증거: `core/CONVENTIONS.md@d04ee778:26-37`; `core/OPERATIONS.md@d04ee778:81-104`.
- adapter guard가 막은 뒤에도 governing documents 전체가 아니라 `OPERATIONS §5.10`의 dispatch 조항만 읽었다. projection ownership이 있는 `CONVENTIONS §4`, Claude adaptation, boundary script는 읽지 않았다.
  증거: transcript `:883-899`.

#### B. 변경 표면 판정 누락

- 세션은 새 drill의 자동 발견 여부를 확인하기 위해 root `loops/drill/run.sh`와 g9/g10 case 형식만 열었다.
  증거: transcript `:972-977`.
- directory 생성도 root `loops/drill/cases_growing/...`에만 했다.
  증거: transcript `:980`.
- commit staging list도 root case 두 개와 wrapper 두 개만 명시했다.
  증거: transcript `:1079`.

즉 세션의 mental model은 “runner가 root case를 자동 발견하므로 새 case 설치 완료”에서 멈췄고, Claude runtime projection이 별도 concrete tree라는 두 번째 표면을 인식하지 못했다.

### 4.3 관련 Skill의 역할

`code-test` Skill 자체는 plan의 verification section과 checklist를 읽고, syntax→import→smoke→functional→integration의 적용 가능한 level을 실행하며 exact command와 결과를 기록하도록 요구한다.
증거: `adapters/claude/skills/code-test/SKILL.md@d04ee778:18-63,73-96`; `roles/modes/qa/test.md@d04ee778:3-29`.

다만 이 Skill에는 “`loops/` 변경이면 `check-adaptation-boundary.sh`”라는 path-specific 매핑이 직접 적혀 있지 않다. 정상 경로에서는 durable plan이 changed surface에 맞는 command를 넣고 code-test가 이를 실행한다. 이번에는 그 plan/stage 자체가 생략됐다. 따라서:

- 1차 원인: Skill 규범 부재가 아니라 Skill을 포함한 pipeline bypass
- 2차 취약점: generic test stage가 plan 없이 호출될 때 changed-path→boundary command를 자동 선택하지 못하는 discovery gap

새 core 규범을 만들 필요는 없다. 기존 규범을 실행 경로와 변경 표면 선택기에 결속하는 것이 맞다.

## 5. 왜 `loops/`는 자동 생성되지 않는가

### 5.1 concrete realization은 의도된 설계

Git 이력은 Claude loop tree가 우연히 복제된 것이 아님을 보여준다.

1. `37624632` (`refactor: route claude shared helpers through adapter`)에서 Claude shared helper가 adapter 경로로 이동하기 시작했다.
2. `b0f462ab` (`refactor: materialize claude loop projections`)은 기존 loop passthrough를 제거하고 `adapters/claude/loops/` 아래 78개 concrete 파일을 물리화했다.
3. 문서는 Claude loops를 “adapter-owned concrete loop files”로 규정하고, runtime-coupled invocation을 장래에 분리하도록 한다.
   증거: `adapters/claude/ADAPTATION.md:136-144,184-188`; `core/ADAPTATION_INVENTORY.md:69-71`.
4. `5bf1e53f`는 source-domain-derived loop completeness guard와 full drill conformance pre-stage를 추가하고 당시 누락된 frozen cases를 mirror해 guard를 green으로 만들었다.

따라서 concrete adapter ownership 자체는 설계 의도다. Claude와 portable loop가 영원히 byte-identical해야 하는 단일 생성물이라는 설계가 아니다.

### 5.2 generator는 loop case tree를 소유하지 않음

사고 시점 `tools/generate.py`의 12개 group은 Skill layer, invocation policy, manifest/catalog, Claude metadata/plugin, Codex Skills/agents/modes/plugin, OpenCode Skills/commands/agents다. loops나 scaffolds copy group은 없다.
증거: `tools/generate.py@d04ee778:18-31`.

`tools/build-manifest.py`의 `build_loops()`도 case tree를 생성하거나 비교하지 않는다. `loops/README.md`의 active-loop 표를 읽어 manifest의 loop catalog row를 만들 뿐이다.
증거: `tools/build-manifest.py@d04ee778:294-335,637-648`.

반면 loop mirror의 보장은 별도 shell guard가 담당한다.

- source domain: `find loops -mindepth 1`
- 예외: gitignored runtime output
- adapter counterpart: `adapters/claude/loops/<rel>`
- 조건: concrete이며 path가 존재

증거: `tools/check-adaptation-boundary.sh:2901-2926`.

중요한 차이는 이 guard가 **detect-only**라는 점이다. 누락을 생성·복구하지 않는다.

### 5.3 의도와 공백의 경계

관찰 가능한 증거로 내릴 수 있는 가장 좁은 판정은 다음과 같다.

- 의도된 것: Claude loop runtime surface를 concrete, adapter-owned realization으로 유지
- 명시적으로 자동화된 것: source-domain을 순회해 missing concrete path를 탐지
- 명시적으로 자동화되지 않은 것: 신규 loop case의 counterpart 생성과 contents synchronization
- 증거 불충분: maintainers가 loop sync generator를 검토해 의도적으로 기각했는지 여부

`harness-layer-sync` spec은 물리 복제 문제를 인식했지만 적용 원칙을 최상위 `hooks/`·`tools/`·`utilities/`로 한정했다.
증거: `.agent_reports/spec/harness-layer-sync/prd.md:31-93,193-224`.

따라서 “concrete 설계 전체가 우연한 공백”은 아니지만, “concrete tree에 신규 항목을 넣는 안전한 동기화 메커니즘 부재”는 구조적 공백이다. 자동 copy를 무조건 도입하면 adapter delta를 덮을 수 있으므로, 생성 여부와 adapter-specific divergence를 구분하는 설계가 필요하다.

## 6. 과거 drill 추가 이력 비교

| 사례 | portable 추가 | Claude concrete 추가 | 이력 판정 |
|---|---|---|---|
| g9 `g9_cross_harness_depth2_dispatch` | `69243d1f` | 같은 `69243d1f` | 네 파일이 같은 commit에 추가됐고 두 디렉터리는 당시 byte-identical |
| g10 `g10_claude_opencode_depth2_start` | `d545e210` | 같은 `d545e210` | 네 파일이 같은 commit에 추가됐고 두 디렉터리는 당시 byte-identical |
| `g_stage_dispatch` | `a558f7f7` | `319f700a`, 이틀 뒤 | portable-only commit이 먼저 들어간 동일 실패 선례 |
| g11/g12 | `d04ee778` | 누락 | `g_stage_dispatch` 선례 반복 |

근거는 각 commit의 `git show --name-status`와 다음 path들이다.

- `69243d1f`: `loops/drill/cases_growing/g9_cross_harness_depth2_dispatch/**`와 `adapters/claude/loops/drill/cases_growing/g9_cross_harness_depth2_dispatch/**`
- `d545e210`: `loops/drill/cases_growing/g10_claude_opencode_depth2_start/**`와 `adapters/claude/loops/drill/cases_growing/g10_claude_opencode_depth2_start/**`
- `a558f7f7`: root `g_stage_dispatch/**`만 추가
- `319f700a`: Claude `g_stage_dispatch/**`만 추가
- `d04ee778`: root g11/g12만 추가

g9/g10 디렉터리의 byte identity는 두 commit tree 간 `git diff --exit-code <commit>:loops/... <commit>:adapters/claude/loops/...`가 clean인 것으로 확인했다. 다만 보존된 Git tree만으로는 작성자가 `cp`를 썼는지 양쪽을 별도 Write했는지까지 판정할 수 없다. 확실한 사실은 **정상 선례는 쌍을 한 commit에 넣었고, 실패 선례는 portable-only commit을 먼저 허용했다**는 것이다.

## 7. 동일 계열 재발 위험

### 7.1 공통 실패 조건

다음 조건이 동시에 존재하는 표면은 같은 계열의 위험을 가진다.

1. portable/source domain이 성장하면 adapter-side concrete 또는 classified counterpart가 필요함
2. generator가 그 counterpart를 완전히 소유하지 않음
3. boundary checker는 detect-only임
4. local commit/push hook가 boundary checker를 강제하지 않음
5. Release CI가 사실상 첫 강제 지점임

full drill은 boundary를 실행할 수 있지만 항상 실행되는 로컬 게이트는 아니다. subset/list/skip 조건에서는 기본적으로 conformance를 건너뛰며, 이번 작업처럼 case assert만 직접 호출하면 전혀 발화하지 않는다.
증거: `loops/drill/run.sh@d04ee778:54-84`; transcript `:1013,1072,1074,1160`.

### 7.2 위험 표면 분류

| 표면 | boundary 계약 | generator 소유 | 재발 위험 |
|---|---|---|---|
| Claude `loops/` | 모든 non-ignored source path에 concrete counterpart 요구 | 없음 | **높음** — 이번 사고와 동일 |
| Claude `scaffolds/` | `find scaffolds`의 모든 path에 concrete counterpart 요구 | 없음 | **높음** — 신규 scaffold/path가 root에만 추가되면 동일 missing failure |
| Codex scaffolds | 모든 `scaffolds/*/`에 Codex asset 요구, 대부분 shared asset과 `cmp` | 없음 | **높음** — 신규 scaffold dir은 manual Codex realization 필요 |
| Claude agent modes | 모든 `roles/modes/<family>/*.md`에 concrete Claude mode file 요구 | Claude mode generator 없음 | **중간~높음** — 신규 mode file의 counterpart 누락 가능 |
| Claude hooks/tools/utilities | canonical entry마다 adapter path와 collapsed/wrapper/delta class 요구 | 일반 copy generator 없음; symlink 또는 exemption을 수동 결정 | **중간** — 단순 missing뿐 아니라 class/baseline 결정도 같은 commit에 필요 |
| Claude Skills | root `skills/`와 Claude tree 전체 byte-equivalence 요구 | entry-router와 metadata는 생성되지만 모든 invocation class의 body copy가 단일 generator에 완전히 귀속되지는 않음 | **중간** — 부분 자동화 표면 |
| Codex/OpenCode tools·utilities | 각 top-level source entry를 projected/deferred로 분류하도록 요구 | generator가 아니라 checker 내 분류 목록 | **중간** — mirror보다는 “projection 결정 미등재” 실패 형태 |

주요 코드 증거:

- Claude scaffolds: `tools/check-adaptation-boundary.sh:2875-2899`
- Claude loops: 같은 파일 `:2901-2927`
- Claude modes: 같은 파일 `:2759-2788`
- Claude hooks/utilities/tools: 같은 파일 `:2791-2834,2929-3021`; `tools/adaptation-exemptions.tsv:1-16`
- Codex scaffolds: 같은 파일 `:1417-1460`
- Codex tools/utilities classification: 같은 파일 `:1247-1268,1392-1414`
- OpenCode tools/utilities classification: 같은 파일 `:2290-2311,2427-2449`
- Claude Skill partial generation: `tools/sync-entry-skill-layer.py:93-145`; `adapters/claude/bin/sync-native-metadata.py:61-99`

scaffolds와 loops가 가장 직접적인 동류다. 둘 다 source-domain을 순회하는 completeness guard는 있지만 concrete tree 생성기는 없다. modes와 shared-layer paths도 같은 “source 성장 시 same-change projection 결정” 부담을 갖는다.

## 8. 재발 방지 옵션 후보

아래는 제안만이며 구현하지 않았다. 기존 core 규범이 이미 boundary ownership과 standard+ verification을 정하므로 **새 규범 신설은 권고하지 않는다**.

### 우선순위 1 — 기존 boundary checker를 평상시 필수 검증 경로에 결속

- `loops/`, `scaffolds/`, `roles/modes/`, `skills/`, `hooks/`, `tools/`, `utilities/`, `adapters/**` 변경을 감지하면 기존 `tools/check-adaptation-boundary.sh`를 code-test/final verification에 자동 선택한다.
- Release publish job만이 아니라 일반 push/PR CI에 독립 boundary job을 둬 release 계획 여부와 무관하게 빨리 실패시킨다.
- 선택적으로 local pre-push에 같은 checker를 연결하되, repository-owned opt-in과 실행시간을 검토한다.

이는 `core/CONVENTIONS.md §4`의 기존 command ownership을 기계화하는 것이지 새 정책을 추가하는 것이 아니다.

### 우선순위 2 — subset drill에도 conformance를 명시적으로 포함

- 새 case 개발 검증 시 직접 `assert.sh`만 실행하지 말고, 기존 `DRILL_CONFORMANCE_ONLY=1` 또는 `DRILL_CONFORMANCE=1` 경로를 검증 command set에 포함한다.
- test report에는 “manual assert”와 “runner/conformance”를 다른 행으로 기록해 둘을 혼동하지 않게 한다.

기존 `loops/drill/run.sh`의 P-20 conformance pre-stage를 재사용하는 옵션이다.

### 우선순위 3 — concrete projection용 안전한 sync/check helper

- loops/scaffolds처럼 concrete divergence가 허용되는 표면에는 무조건 overwrite하는 generator 대신 다음 중 하나를 검토한다.
  - missing counterpart만 scaffold하는 `--sync-missing`
  - source hash + adapter delta/exemption ledger
  - frozen drill case만 byte-identical 대상으로 선언하는 좁은 sync group
- 실행 결과는 `tools/generate.py --check` 또는 boundary checker에서 한 maintainer entrypoint로 노출한다.

adapter-specific loop 내용을 덮지 않도록 “복사 가능한 identical class”와 “의도된 delta class”를 분리해야 한다.

### 우선순위 4 — guard의 content 계약 강화

- 현재 `check_claude_loop_projection`은 대부분 path 존재만 검사하고, drill runner만 별도 `cmp`한다.
- frozen/growing drill case 중 양 tree가 동일해야 하는 class가 공식화돼 있다면 해당 class에 byte/hash equivalence를 추가한다.
- 반대로 divergence가 허용되는 case는 명시적 exemption과 이유를 둔다.

이는 `.agent_reports/spec/skill-design-refactor/.../prd.md:124`의 기존 byte-identical mirror 불변식을 구현과 맞추는 선택지다.

### 우선순위 5 — pipeline bypass를 검출

- multi-file adapter/portable 변경을 main inline으로 수행할 때 기존 inline exception metrics가 없으면 final commit 이전에 실패시키거나 최소한 명시 경고한다.
- commit 대상에 `loops/**`가 있는데 대응 `adapters/claude/loops/**` 변경이 없으면 changed-set preflight가 boundary command를 요구하도록 한다.

이 역시 `core/OPERATIONS.md §5.10`의 기존 worktree/inline-exception 계약을 집행하는 옵션이다.

## 9. 한계

- GitHub Actions run과 6회 실패·복구 release는 요청의 확정 사실로 받아들였고 다시 조회하지 않았다.
- herdr 로그는 pane 3과 Claude session UUID를 직접 결합하지 않는다. 세션 귀속은 시각·cwd·typed prompt·commit output 교차에 의한 높은 확신의 inference다.
- Claude JSONL은 runtime-owned 외부 로그다. 현재 조사에는 남아 있었지만 저장소의 영구 증적은 아니며 향후 소실될 수 있다.
- g9/g10은 Git tree로 same-commit·byte-identical 상태까지 확인했으나 실제 작성 명령이 copy였는지는 증거가 불충분하다.
- “loop sync generator 부재를 과거 설계자가 명시적으로 기각했다”는 기록은 찾지 못했다. concrete adapter ownership은 의도적이지만, 자동 sync 부재의 의도성은 단정하지 않았다.

## 10. 최종 결론

`d04ee778`의 실패는 단순한 파일 복사 실수 하나로 끝나지 않는다.

1. **직접 원인**은 g11/g12의 Claude concrete loop projection 누락이다.
2. **기여 원인**은 별도 spec/route cycle이 필요하다는 자체 판단 뒤에도 대화형 main 세션이 current checkout에서 inline 구현을 계속해 durable plan·code-test·boundary 검증을 우회한 것이다.
3. **표면 판정 원인**은 “새 drill case가 root runner에 자동 발견된다”는 확인을 “모든 runtime projection이 완결됐다”로 오인한 것이다.
4. **구조 원인**은 deliberate concrete realization을 유지하면서 신규 counterpart 생성은 수동으로 남겨 두고, detect-only boundary checker의 첫 강제 지점을 Release CI에 둔 것이다.

기존 규범은 이미 이 사고를 막을 command와 verification ownership을 제공했다. 필요한 것은 새 문구가 아니라 **기존 boundary checker를 changed-surface 선택, standard+ code-test, 일반 CI 또는 local push gate에 결속하고, concrete projection의 identical/delta class를 기계적으로 관리하는 것**이다.
