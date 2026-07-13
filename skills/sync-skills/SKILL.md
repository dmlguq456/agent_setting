---
name: sync-skills
description: "skills·agents 정의 변경 감지 후 README 대시보드·manifest 동기화"
argument-hint: "[--check] [--force] [--auto-fix [--dry-run]]"
metadata:
  group: ops
  fam: ops
  modes: []
  blurb: "skills·agents 정의 변경 감지 후 README 대시보드·manifest 동기화"
---

## Language Rule
- 사용자 응답은 한국어로.

## Purpose
스킬·에이전트를 수정한 후 매번 GitHub README 에 일관된 정보가 반영되어 있는지 확인하는 도구.

**Source of Truth**:
- `<agent-home>/capabilities/README.md` + `<agent-home>/capabilities/*.md` + `<agent-home>/adapters/claude/skills/*/SKILL.md` + `<agent-home>/roles/README.md` + `<agent-home>/roles/MODES.md` + `<agent-home>/adapters/claude/agents/*.md` — 각 capability·Claude skill realization·role/mode·Claude agent 의 frontmatter/본문
- `<agent-home>/skills/*/SKILL.md` 는 historical compatibility reference 로 보존하며, Claude runtime source 로 취급하지 않는다.
- **`<agent-home>/core/CONVENTIONS.md`** — family-wide 운영 규칙의 단일 source (QA 5단계 정의 / model role 표기 / cross-doc invariants). 본 skill 의 Step 5b 가 본 문서를 canonical 로 cross-doc grep 해 drift 보고·자동 fix.

**파생 산출물**: GitHub `<agent-home>/README.md`

본 skill 은 Source of Truth 로부터 README 를 재생성한다. 사용자가 파생물을 직접 편집해서는 안 된다 (자동 생성 표지 있음).


## Targets

### 입력
- **Claude Skills**: `<agent-home>/adapters/claude/skills/*/SKILL.md`
- **Skill compatibility refs**: `<agent-home>/skills/*/SKILL.md` (parity/drift check only)
- **Capabilities**: `<agent-home>/capabilities/README.md`
- **Roles**: `<agent-home>/roles/README.md`
- **Role modes**: `<agent-home>/roles/MODES.md`
- **Runtime adapters**: `<agent-home>/adapters/{claude,codex,opencode}/`
- **Claude Agents**: `<agent-home>/adapters/claude/agents/*.md`

자동 발견: `ls <agent-home>/adapters/claude/skills/*/SKILL.md <agent-home>/adapters/claude/agents/*.md`. 실제 sync 시점에 발견된 파일 list 가 진실. Portable capability 의미는 `capabilities/README.md`와 `capabilities/*.md`, portable role 의미는 `roles/README.md`, role mode portability 는 `roles/MODES.md`, Claude native frontmatter 는 `adapters/claude/skills/*/SKILL.md` 와 `adapters/claude/agents/*.md` 가 source. 본 SKILL.md 본문에는 카운트·명단 hardcode 안 함 — drift 의 자기참조 source 가 됨.

각 파일에서 추출:
- frontmatter `name`, `description`, `argument-hint` (skills only), `tools`, `model`
- argument-hint 파싱 → 옵션 값 (예: `--mode dev|debug`, `--from analyze|strategy|...`)

### 출력
1. **GitHub**: `<agent-home>/README.md` (repo: `git@github.com:dmlguq456/agent_setting.git`, root: `<agent-home>`)
2. **상태 파일**: `<agent-home>/skills/.sync_state.json` — 각 입력 파일의 SHA-256, README sync 시각

## Argument Parsing
- `--check`: drift 만 보고하고 종료. 쓰기 작업 X. (manifest drift 도 함께 검사 — `python3 tools/build-manifest.py --check`; 비-0 exit = `manifest.json` 이 현행 정의와 어긋남. Step 3 drift report / Step 7 final report 에 노출.)
- `--force`: SHA 가 같아도 재생성 (포맷 일괄 적용·서식 수정에 사용).
- `--auto-fix`: Step 5b 에서 발견한 cross-doc invariant drift 를 `CONVENTIONS.md` canonical wording 으로 자동 교체 (default 는 report-only). `--dry-run` 과 조합 시 미리보기.

기본 (인자 없음): drift 감지 → 변경 있으면 README 갱신.

## Pipeline

`discover/hash → sync state 로드 → drift report → dashboard 재생성 → cross-doc invariant scan → state/manifest/report` 흐름. 각 Step 의 명령·표·템플릿 전문은 아래 reference 에 verbatim 보존한다. 이 파일은 라우터와 계약만 담고, 세부 절차는 필요할 때 해당 reference 를 Read 한다.

| Step | 내용 | Reference |
|---|---|---|
| Step 1–3 | Discover + hash → sync state 로드(v4 스키마) → Drift report (신규/변경/삭제/동일 · `--check` 종료) | `references/detect-and-report.md` |
| Step 4·5·5a | Dashboard 섹션 생성(4a 트랙 텍스트 체인 · 4b 9섹션 canonical layout) → README.md 작성(섹션별 자동 갱신 정책) → 편집팀 검수 | `references/readme-dashboard.md` |
| Step 5b·5c·5d | Cross-doc invariant scan(QA 정의/model role) → skill name rename drift scan → 에이전트 엔지니어링 매뉴얼 동기 검토 | `references/cross-doc-invariants.md` |
| Step 6·6b·6c·7 + Hook | Sync state 갱신 → manifest.json 재방출 → scan.sh 정량 규범 lint(§CONVENTIONS 5.6a) → Final report + Hook integration(옵션) | `references/finalize-and-hooks.md` |

## Reference Index

| 파일 | 언제 로드 (의무) | 내용 |
|---|---|---|
| `references/detect-and-report.md` | drift 감지 실행 시 (Step 1~3) | Step 1(Discover + hash), Step 2(Read sync state — v4 스키마), Step 3(Drift report — 4 분류·한국어 출력·`--check` 종료) |
| `references/readme-dashboard.md` | README 재생성 시 (Step 4·5·5a) | Step 4(dashboard — 4a 트랙 텍스트 체인, 4b README 9섹션 canonical layout·원칙·_넣지 않음_ drop+link), Step 5(Write README.md — 섹션별 자동 갱신 정책 표), Step 5a(편집팀 검수) |
| `references/cross-doc-invariants.md` | Cross-doc drift 스캔 시 (Step 5b·5c·5d) | Step 5b(QA/model role invariant scan 5b-1~5b-4), Step 5c(skill name rename drift 5c-1~5c-5), Step 5d(에이전트 엔지니어링 매뉴얼 동기 검토) |
| `references/finalize-and-hooks.md` | 종료 시 (Step 6·6b·6c·7 + Hook) | Step 6(Update sync state), Step 6b(Emit manifest.json), Step 6c(scan.sh 정량 규범 lint §CONVENTIONS 5.6a), Step 7(Final report), Hook integration(옵션 Stop hook) |

## Safety Rules
- README.md 는 자동 생성 표지가 있는 경우에만 덮어쓴다. 사용자 수동 편집 흔적이 감지되면 abort + 경고.
- `--force` 없이는 SHA 동일 항목은 처리 스킵.
- sync state JSON parse 실패 시 backup 으로 옮기고 빈 dict 로 재시작 (모든 항목을 변경으로 처리).
- 자기 자신 (`sync-skills/SKILL.md`) 갱신도 동일하게 처리 (메타 — `sync-skills` 가 자기 hash 를 state 에 기록).

## Task
$ARGUMENTS
