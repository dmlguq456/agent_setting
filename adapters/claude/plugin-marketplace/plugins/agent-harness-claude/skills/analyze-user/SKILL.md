---
name: analyze-user
description: "Use when building or updating a cross-project user-preference profile from coding, writing, and analysis patterns."
argument-hint: "<aspect> [--source <path>] [--mode init|update] [--from discover|analyze|verify|qa|output|summary] [--user-refine]"
metadata:
  group: pre
  fam: pre
  modes: [init, update]
  blurb: "Build or update a cross-project user-preference profile."
---

# analyze-user

cross-project 사용자 성향 프로필 entry. 사용자의 과거 산출물(figure·writing·presentation·analysis·domain·coding)에서 범용 패턴을 추출해 DB `type=profile` 레코드로 영속·갱신한다. `discover → analyze → verify → qa → output → summary` 6-phase 파이프이며, 검증 rigor 는 항상 adversarial-tier 고정 (intensity=adversarial). 이 파일은 라우터·호출 계약만 담고, 세부 절차·프롬프트·템플릿은 필요할 때 아래 reference 를 Read 한다.

> **산출물 위치**: DB `type=profile` 레코드 (읽기: `python3 <agent-home>/tools/memory/mem.py profile <stem>` / `mem profile <stem>`). stem 목록: `01_paper_figure_style` ~ `07_coding_convention` (7 개). `_internal/` 은 source index / qa reviews / pipeline state 용 _일시 스크래치_ 디렉터리 — SoT 아님 (SoT 는 DB). `<artifact-root>/` 가 아니므로 [CONVENTIONS.md §5](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) 의 _3-tier_ 가 _직접 적용_ 되진 않음 — 다만 main outputs / internal logs 의 _2-tier 분리_ 정신은 따른다.

> **Workspace assumption**: 본 skill 은 _cross-project_ 작업 — 현 cwd 와 무관하게 사용자의 _과거 모든 산출물_ 을 스캔. 입력 source 는 기본 위치 (`~/nas/user/Uihyeop/doc/` / `~/nas/user/Uihyeop/NN_Zoo/` / `<agent-home>/projects/*/memory/`) + `--source <path>` 추가. 산출은 항상 DB `type=profile` 레코드로 영속 (파일 Write X).

## Default Invocation Rule (메인 에이전트 자동 라우팅)

본 skill 은 runtime adapter bootstrap 의 "autopilot-* 호출 패턴" 컨펌 의무 적용 대상(Claude Code: [`CLAUDE.md`](../../adapters/claude/CLAUDE.md) §0). 메인 에이전트가 사용자 발화에서 아래 trigger 신호를 인지하면, 옵션 자동 구성 + 자연어 요약 컨펌 거쳐 invoke.

### Trigger 신호 (자연어 발화 예시)

- "사용자 프로필 갱신해줘" / "내 figure 스타일 분석해줘"
- "내가 만든 발표 자료들 분석해" / "내 paper 작성 톤 추출해줘"
- "user_profile 업데이트" / "내 작업 성향 정리"
- "내 코딩 컨벤션 정리" / "model 폴더 패턴 추출" / "preferred layer 추출"
- 새 paper / 발표 / 보고서 / 모델 완성 직후 "이번 자료도 프로필에 반영해줘"

### Default 옵션 권장값 (컨펌 시 메인 에이전트가 제안)

- `<aspect>`: 발화로 추론 — "figure" / "스타일" → `figure`, "발표" → `presentation`, "작성 톤" → `writing`, "코딩 컨벤션" / "model 폴더" / "layer" → `coding_convention`, 명확히 안 보이면 `all`.
- `--mode`: 기본 `update`. 사용자가 "다시 처음부터" / "init" 신호 주면 `init`.
- `--from`: 자동 추론 (`pipeline_state.yaml` 발견 시 마지막 성공 phase 다음부터).
- `--user-refine`: **off** (글로벌 §2 — 명시 신호 있을 때만 켬).

### Override 1순위 — autopilot 우회

- 짧은 메모 한 줄만 — `/post-it --scope user <aspect> add <text>` 직접 호출. 해당 aspect 의 profile 레코드 body 안 `## 사용자 수동 메모` 절에 splice (DB write).
- 한 aspect 의 한 자리만 수정 — `/post-it --scope user <aspect>` 를 통해 DB 레코드 body 갱신. 파일 직접 Edit 아님 (SoT 는 DB). `## 사용자 수동 메모` 절은 사용자 영역이므로 `/post-it --scope user <aspect>` 경유.
- `/analyze-user <args>` slash 직접 입력 — 컨펌 skip 즉시 invoke.

## Language Rule

- User-facing output and artifact prose (including the DB profile-record body) follow the user's communication language unless an explicit audience or artifact-language requirement overrides it.
- Preserve code, file paths, identifiers, and domain expressions when translation would reduce precision.
- Match chat tone to the conversation; keep the user-profile body concise, declarative, and report-like in the selected language.

## Core Invariants

- **QA adversarial 고정** — 별도 rigor flag 없음 — intensity=adversarial 로 고정. Phase 4 는 항상 4-reviewer 병렬(source coverage / pattern accuracy / factcheck / external adversary). 사용자 프로필은 모든 sub-agent 가 default 로 따르는 propagating 자료라 협상 불가.
- **산출 = DB `type=profile` 레코드** (파일 Write X). write 는 `mem add durable profile <body> --scope global --source user-profile:<stem>` (source-keyed UPSERT — id 보존), read 는 `mem profile <stem>` (rowid-DESC newest-wins tie-break).
- **`## 사용자 수동 메모` two-writer contract** — analyze-user(update) 와 `/post-it --scope user` 두 곳이 같은 `user-profile:<stem>` 레코드에 write. 반드시 `mem profile <stem>` tie-broken read 후 splice (raw query 금지 — stale dup splice 시 promoted memo orphan).
- **per-stem 사후 read-back** — 각 stem write 직후 `mem profile <stem>` 로 read-back 해 dedup 병합 여부 검증 (불일치 → 큰 소리로 fail).
- **하드코딩 path 금지** — 모든 aspect 의 기본 source 자체가 사용자 `--source` 명시 자리. 명시 없으면 자료 0 + 한 줄 안내.

## Argument & Mode Overview

`<aspect> [--source <path>] [--mode init|update] [--from discover|analyze|verify|qa|output|summary] [--user-refine]`

- **`<aspect>`** (REQUIRED) — `figure` / `writing` / `presentation` / `analysis` / `domain` / `coding_convention` / `all`. 각 aspect ↔ profile stem(`01_paper_figure_style` ~ `07_coding_convention`) 매핑·source type 표 → `references/arguments-and-decisions.md`.
- **`--mode`** — 기본 `update` (incremental 누적), `init` 은 통째 재셋업(기존 body snapshot 후 교체).
- **`--from`** — `discover`/`analyze`/`verify`/`qa`/`output`/`repro`/`summary` 재개.
- **`--user-refine`** — Phase 5 직전 pause (명시 신호 있을 때만).
- **QA** — adversarial 고정 (flag 없음).

전체 aspect 표·source 매핑·`--mode`·QA·`--from`·`--user-refine` 상세, Decision Defaults, Resume `pipeline_state.yaml` 스키마 → `references/arguments-and-decisions.md`.

## Pipeline Overview (6 phase)

| Phase | 내용 |
|---|---|
| 1 Source Discovery | source 발견·분류·인덱싱 + docx/pptx/hwpx 자동 변환 (PDF + PNG 하이브리드) |
| 2 Aspect Analysis | 2.1 연구팀 3-instance parallel 추출 → 2.2 consensus 합산 (confidence 1.0/0.6/0.3) |
| 3 Cross-reference | aspect 간 일관성 점검 (색·폰트·용어·metric·layer) |
| 3.5 Prior-version 변증법 | `--mode update` 한정 — thesis/antithesis → synthesis (confirm/refine/contradict/new) |
| 4 Multi-agent QA | adversarial 4-reviewer 병렬 (coverage / accuracy / factcheck / external) |
| 5 Output | verified draft → DB profile 레코드 write (7-10K tokens 목표) |
| 5b pptx 개체 추출 | figure aspect 전용 — SVG 벡터 개체 라이브러리 산출 |
| 6 Pipeline Summary | `_internal/pipeline_summary.md` append |

각 phase 의 절차·Agent 프롬프트·자동 변환 명령·QA reviewer·출력 템플릿 전문 → `references/pipeline-phases.md`.

## Reference Index

| 파일 | 언제 로드 (의무) | 내용 |
|---|---|---|
| `references/arguments-and-decisions.md` | 인자 해석·Decision·Resume 자리 | Argument Parsing (`<aspect>` 표 / `--source` / `--mode init\|update` / QA adversarial 고정 / `--from` / `--user-refine`), Decision Defaults (no autonomy gating), Resume(`--from`) + `pipeline_state.yaml` 스키마 |
| `references/pipeline-phases.md` | 6-phase 파이프 실행 시 (필수) | Phase 1 Source Discovery+자동변환, Phase 2 Aspect Analysis(2.1 3-instance extraction / 2.2 consensus aggregation), Phase 3 Cross-reference Validation, Phase 3.5 Prior-version 변증법, Phase 4 Multi-agent QA, Phase 5 Output Generation, Phase 5b pptx 개체 추출, Phase 6 Pipeline Summary |
| `references/integration-and-usage.md` | sub-agent 참조·메모리 관계·호출 예시 판단 자리 | sub-agent 참조 패턴 매트릭스, 메모리와의 관계 표, 호출 예시, 갱신 빈도 권장 |
