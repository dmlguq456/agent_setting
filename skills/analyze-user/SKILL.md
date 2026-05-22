---
name: analyze-user
description: "사용자 (Ui-Hyeop Shin) 의 cross-project 산출물 (paper / presentation / report / code / memory) 을 다단계로 스캔·분석해 `~/.claude/user_profile/*.md` 의 _범용 작업 성향_ 을 누적·갱신. autopilot-* 와 동급 ceremony — 사용자 프로필은 _한 번 만들어지면 모든 sub-agent 가 default 로 따르는 자료_ 라 작은 오류도 propagating. 따라서 source discovery → aspect 별 분석 → cross-aspect 일관성 검증 → 다중 QA gate (adversarial 고정) → 산출 → pipeline summary 6 phase. QA level 은 _항상 adversarial_ — 사용자 협상 불가."
argument-hint: "<aspect> [--source <path>] [--mode init|update] [--from discover|analyze|verify|qa|output|summary] [--user-refine]"
---

> **산출물 위치**: `~/.claude/user_profile/`. 단일 source `01_paper_figure_style.md` ~ `06_collaboration_style.md` + `_internal/` (source index / qa reviews / pipeline state). `.claude_reports/` 가 아니므로 [CONVENTIONS.md §5](../../CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) 의 _3-tier_ 가 _직접 적용_ 되진 않음 — 다만 main outputs / internal logs 의 _2-tier 분리_ 정신은 따른다.

> **Workspace assumption**: 본 skill 은 _cross-project_ 작업 — 현 cwd 와 무관하게 사용자의 _과거 모든 산출물_ 을 스캔. 입력 source 는 기본 위치 (`~/nas/user/Uihyeop/doc/` / `~/nas/user/Uihyeop/NN_Zoo/` / `~/.claude/projects/*/memory/`) + `--source <path>` 추가. 산출은 항상 `~/.claude/user_profile/` 영속.

## Default Invocation Rule (메인 Claude 자동 라우팅)

본 skill 은 글로벌 [`CLAUDE.md`](../../CLAUDE.md) §6 "autopilot-* 호출 패턴" 의 _컨펌 의무_ 적용 대상. 메인 Claude 가 사용자 발화에서 아래 trigger 신호를 인지하면, 옵션 자동 구성 + 자연어 요약 컨펌 거쳐 invoke.

### Trigger 신호 (자연어 발화 예시)

- "사용자 프로필 갱신해줘" / "내 figure 스타일 분석해줘"
- "내가 만든 발표 자료들 분석해" / "내 paper 작성 톤 추출해줘"
- "user_profile 업데이트" / "내 작업 성향 정리"
- 새 paper / 발표 / 보고서 완성 직후 "이번 자료도 프로필에 반영해줘"

### Default 옵션 권장값 (컨펌 시 메인 Claude 가 제안)

- `<aspect>`: 발화로 추론 — "figure" / "스타일" → `figure`, "발표" → `presentation`, "작성 톤" → `writing`, 명확히 안 보이면 `all`.
- `--mode`: 기본 `update`. 사용자가 "다시 처음부터" / "init" 신호 주면 `init`.
- `--from`: 자동 추론 (`pipeline_state.yaml` 발견 시 마지막 성공 phase 다음부터).
- `--user-refine`: **off** (글로벌 §4 — 명시 신호 있을 때만 켬).

### Override 1순위 — autopilot 우회

- `--scope user` 짧은 메모 한 줄만 — `/notes --scope user add ...` 직접 호출.
- 한 aspect 의 한 자리만 수정 — `~/.claude/user_profile/0X_*.md` 직접 Edit.
- `/analyze-user <args>` slash 직접 입력 — 컨펌 skip 즉시 invoke.

> 본 섹션은 `/sync-skills` 가 `~/.claude/README.md` 운영 룰 안내로 자동 반영.

## Language Rule

- Think and reason in English internally.
- All user-facing output and 산출물 (`user_profile/*.md`) 본문 in **한국어**.
- 코드·파일 경로·식별자·도메인 표현은 영어 그대로.
- 어미 톤 — chat 응답은 대화체, user_profile 본문은 _평어 단정형_ (보고서 톤 — `~다 / ~이다`).

## Argument Parsing

### `<aspect>` (REQUIRED)

| aspect | 갱신 파일 | 기본 source |
|---|---|---|
| `figure` | `01_paper_figure_style.md` | `~/nas/user/Uihyeop/doc/*/latex*/figures/`, `~/nas/user/Uihyeop/doc/*/figure*/` |
| `writing` | `02_paper_writing_style.md` | `~/nas/user/Uihyeop/doc/*/latex*/main.tex`, arXiv abstract |
| `presentation` | `03_presentation_strategy.md` | `~/nas/user/Uihyeop/doc/presentation/`, `~/nas/user/Uihyeop/doc/*ppt*/` |
| `analysis` | `04_analysis_methodology.md` | `~/nas/user/Uihyeop/NN_Zoo/*/analysis/*.py`, paper Method / Experiment 절 |
| `domain` | `05_domain_expertise.md` | paper 일람 (scholar.google), 사용자 GitHub |
| `collab` | `06_collaboration_style.md` | `~/.claude/projects/*/memory/*.md` |
| `all` | 6 개 모두 | 위 source 모두 |

### `--source <path>` (옵션)

추가 source 디렉토리 명시. 기본 source 외 더 살펴봐야 할 자리. 복수 지정 가능 (콤마 분리).

### `--mode init|update` (옵션, default `update`)

- `init` — 처음 셋업. 기존 파일 통째 교체 (`_internal/versions/` 안에 옛 버전 스냅샷 보존).
- `update` (default) — incremental. 새 자료 발견 시 기존 내용에 누적·갱신. 변경 항목은 _누적 vs 교체 vs 제거_ 셋 중 명시.

### QA 강도 — _adversarial 고정_ (사용자 협상 불가)

본 skill 의 QA level 은 _항상 adversarial_. `--qa` flag 자체 없음. 이유:

- 사용자 프로필은 _한 번 만들어지면 모든 sub-agent 가 default 로 따르는 자료_ — 작은 오류도 모든 작업에 propagating.
- 가벼운 incremental 갱신이라도 _기존 자료와의 모순_ 또는 _과잉 일반화_ 위험이 있어 multi-reviewer 검증이 필수.
- 비용 부담은 _프로필 자료 하나만의 비용_ — paper / cycle 마다 반복되는 것 아님.

Phase 4 의 reviewer 구성은 항상 4 개 parallel (Phase 4 절 참조).

### `--from <stage>` (옵션)

기존 `_internal/pipeline_state.yaml` 을 읽어 마지막 성공 phase 다음부터 재개. stage:

- `discover` — Phase 1 부터
- `analyze` — Phase 2 부터
- `verify` — Phase 3 부터
- `qa` — Phase 4 부터
- `output` — Phase 5 부터
- `summary` — Phase 6 부터

### `--user-refine` (boolean, opt-in)

분석 산출 _직전 (Phase 5 직전)_ pause. 사용자가 추출된 패턴에 _직접 memo 추가_ 하고 싶을 때. 명시 신호 ("사용자 검토 끼워" / "memo 추가" / `--user-refine`) 있을 때만 켬. 메인 Claude 가 임의 추가 X.

## Pipeline (6 phase)

### Phase 1 — Source Discovery

목적: aspect 별 _모든 expected source_ 를 발견·분류·인덱싱. 한 source 라도 누락되면 _패턴 추출이 편향됨_.

절차:

1. **기본 source 위치 일람** — `<aspect>` 별 기본 source 표 (위) 의 모든 경로 glob.
2. **`--source` 추가 디렉토리 일람** — 사용자 명시 source 도 같이.
3. **메모리 자료 일람** (collab / domain aspect 시) — `~/.claude/projects/*/memory/*.md` 전수.
4. **scholar / arXiv 자료 일람** (writing / domain aspect 시) — 사용자 paper 목록 + abstract.
5. **분류 표기** — 각 source 별 type (figure / latex / slide / py-script / memory / paper-abs) + 마지막 수정 시각 + 사이즈.
6. **`_internal/source_index.md` 작성** — 위 일람 통째.

산출:
- `~/.claude/user_profile/_internal/source_index.md` (또는 갱신)
- Phase 1 verdict 한 줄 (총 source N 건 발견, 어느 aspect 에 몇 건씩).

### Phase 2 — Aspect-specific Analysis (연구팀 위임)

목적: aspect 별 source 에서 _범용 패턴_ 추출. 도메인 지식 필요한 작업이라 연구팀 위임.

각 aspect 별 위임 procedure (예시 `figure` aspect):

```
Agent(연구팀, prompt="""
사용자 산출물 분석 — aspect: figure
Source index: ~/.claude/user_profile/_internal/source_index.md
기존 user_profile/01_paper_figure_style.md 내용 (update 모드 시): {기존 내용}

추출 대상 패턴:
1. Architecture diagram 양식 — 색·aspect·layout·label·panel 수
2. Curve plot 양식 — palette·폰트·legend·grid·annotation 위치
3. Scatter / 표 layout — column 순서·row 순서·강조·footnote
4. Spectrogram 관례 — window·resample·color axis
5. 도메인별 metric set
6. ours 강조 패턴

각 패턴은 _source 인용_ 명시 (어느 paper / 어느 figure / 어느 script 에서 나왔는지).
mode=init 면 통째 교체, mode=update 면 누적 (새 source 발견 분만 추가, 기존은 보존).

산출 형태: 임시 파일 ~/.claude/user_profile/_internal/aspect_{aspect}_draft.md.
다음 phase 의 verification 이 ground truth 와 대조한 뒤 최종 적용.
""")
```

`writing` / `presentation` / `analysis` / `domain` / `collab` aspect 도 동일 패턴 — _추출 대상 패턴 목록만 aspect 별_ 다름. `all` 은 6 aspect 모두 병렬.

산출:
- `_internal/aspect_{aspect}_draft.md` (per aspect)
- Phase 2 verdict — 각 aspect 별 추출된 패턴 수.

### Phase 3 — Cross-reference Validation

목적: aspect 사이 _일관성_ 점검. 예 `01_figure_style.md` 의 _ours 색_ 이 `03_presentation_strategy.md` 의 _슬라이드 강조 색_ 과 어긋나면 어느 쪽이 맞는지 결정.

절차:

1. 6 aspect draft 를 모두 Read.
2. 다음 _cross-aspect 일관성 axis_ 점검:
   - 색 팔레트 — figure / presentation / scatter / spectrogram 의 색 결정이 같은가?
   - 폰트 — figure / presentation / paper 의 폰트 일관성.
   - 도메인 용어 — writing / domain / collab 의 약자·용어 사용이 일치하는가?
   - metric set — figure 의 metric column 과 analysis 의 검증 방법이 매칭되는가?
3. 모순 발견 시 _source 인용 빈도가 더 많은 쪽_ 우선 (또는 _더 최근 자료_ 우선).
4. 모순 자체를 _open question_ 으로 남길지, _즉시 해소_ 할지 결정 — 사용자 명시 패턴 (`/notes --scope user`) 이 있으면 그게 ground truth.

산출:
- `_internal/cross_aspect_consistency.md` — 점검 결과 + 모순 해소 결정.
- Phase 3 verdict — N 자리 모순 발견, M 자리 해소, K 자리 open question 남김.

### Phase 4 — Multi-agent QA Verification (adversarial 고정, 4 parallel reviewer)

목적: 추출된 패턴이 _실제 source 와 일치_ 하는지, _사실 오류·과잉 일반화·bias·missing aspect_ 없는지 검증. 사용자 프로필은 propagating 자료라 _4 개 reviewer 모두 항상_ 병렬.

- **Agent A — source coverage** (sonnet, `_internal/qa_coverage.md`):
  ```
  사용자 프로필 draft 와 source index 대조.
  각 추출된 패턴이 _하나 이상의 source 인용_ 을 갖는가?
  source 일람의 file 들이 _모두 추출 대상에 포함_ 됐는가?
  누락된 source 또는 인용 없는 패턴은 🔴 finding.
  ```

- **Agent B — pattern accuracy** (opus, `_internal/qa_accuracy.md`):
  ```
  draft 의 각 패턴을 source 자료와 직접 대조.
  색 hex code · 폰트 이름 · figsize · paper title / venue / 연도 등 verbatim 정확성.
  잘못된 fact · 과장된 일반화 · source 와 모순되는 표현은 🔴 finding.
  ```

- **Agent C — factcheck** (sonnet, `_internal/qa_factcheck.md`):
  ```
  paper 인용 verbatim 점검 — 제목 / 학회 / 연도 / 인용수 / DOI / arXiv ID.
  metric 수치 인용 점검 — paper / abstract 에서 직접 대조.
  ```

- **Agent D — Codex external review** (codex-review-team, `_internal/qa_codex.md`):
  ```
  외부 hostile reader 관점 review — 사용자 프로필이 _과잉 일반화_ · _bias_ · _missing aspect_ 가 있는가?
  ```

> Codex 가용 안 한 환경이면 Agent D 만 skip + 한 줄 경고. A·B·C 는 반드시 실행.

산출:
- `_internal/qa_{coverage,accuracy,factcheck,codex}.md` (4 개)
- Phase 4 verdict — 🔴 N · 🟡 M · 🟢 K finding 누적.
- 🔴 finding 1 개 이상 → Phase 2-3 으로 _자동 retry_ (max 2 회). 2 회 모두 실패 시 _pipeline failed_ 보고.

### Phase 5 — Output Generation

목적: verified draft 를 _최종 user_profile/0X_*.md_ 에 반영.

절차:

1. **--user-refine pause** (있으면) — draft + qa review path 안내 후 종료. 사용자가 `<!-- memo: ... -->` 추가 후 `/analyze-user --from output` 재개.
2. **mode 별 처리**:
   - `init` — 기존 파일 `_internal/versions/v{N}/` 스냅샷 후 통째 교체.
   - `update` — 기존 파일 Read + draft 비교 + _누적 / 교체 / 제거_ 자리 결정 + Edit. changelog 한 줄 frontmatter 의 `changelog:` 배열에 추가.
3. **source 인용 일람** — 각 user_profile/0X 파일 끝의 _분석 source 일람_ 절에 이번 사이클의 source 추가 (다음 update 시 _이미 본 자료 vs 새 자료_ 구분 용도).

산출:
- `~/.claude/user_profile/0X_*.md` (해당 aspect 갱신됨).
- Phase 5 verdict — 각 aspect 별 누적·교체·제거 항목 수.

### Phase 6 — Pipeline Summary

`~/.claude/user_profile/_internal/pipeline_summary.md` (단일 파일, append 누적):

```markdown
## {YYYY-MM-DD} — {aspect} {mode}

**Source**: {N source files scanned, breakdown by type}
**Extracted patterns**: {M new + K updated + L removed}
**QA findings**: 🔴 {n_red} 🟡 {n_yellow} 🟢 {n_green}  (resolved {res})
**Affected files**: {list of user_profile/0X_*.md 갱신된 자리}
**Retry count**: {0 / 1 / 2 if any}
**Total time**: ~{minutes}

**개선 사항**: {이번 사이클에서 발견된 새 패턴 또는 정정된 자리 요약 3-5 줄}
**남은 open question**: {Phase 3 의 미해소 모순 / 향후 보강 후보}
```

## Decision Defaults (no autonomy gating)

| Decision Point | Default Behavior |
|---|---|
| Source 발견 0 건 (aspect 별) | Auto-stop 해당 aspect, 다른 aspect 만 계속. _all_ 호출 시 1 개 aspect 만 실패해도 나머지 진행. |
| Cross-aspect 모순 발견 | 자동 해소 (source 인용 빈도 / 최신 자료 우선). 해소 불가 자리는 _open question_ 으로 남기고 진행. |
| QA Phase 🔴 finding | Phase 2-3 자동 retry (max 2 회). |
| Retry 2 회 실패 | pipeline failed, summary 작성 후 중단. |
| `--user-refine` pause | 한 번만 (Phase 5 직전). resume 은 `--from output`. |

## Resume (`--from`)

`_internal/pipeline_state.yaml` 형식:

```yaml
aspect: figure
mode: update
qa_level: adversarial  # 고정 — 본 skill 은 협상 불가
last_completed_phase: verify
sources_indexed: 47
drafts_complete: [figure]
qa_findings:
  red: 0
  yellow: 3
  green: 12
timestamp: "2026-05-22T15:30:00Z"
```

재개 시 CLI flag override 우선. `--from <stage>` 명시되면 그 phase 부터.

## sub-agent 참조 패턴 (작업 시작 자리에서 Read)

각 agent 가 user_profile 의 어떤 파일을 Read 해야 하는지:

| Agent | 작업 시작 시 Read |
|---|---|
| 분석팀 | `01_paper_figure_style.md`, `04_analysis_methodology.md` |
| 연구팀 | `02_paper_writing_style.md`, `05_domain_expertise.md` |
| 편집팀 | `02_paper_writing_style.md`, `06_collaboration_style.md` |
| 기획팀 | `04_analysis_methodology.md`, `06_collaboration_style.md` |
| 메인 Claude | `06_collaboration_style.md` |

본 참조 패턴은 _agent 정의 본문_ 에 명시되어 있어 agent 가 invoke 될 때 자동.

## 메모리와의 관계

| | 메모리 (`~/.claude/projects/<cwd>/memory/`) | user_profile (`~/.claude/user_profile/`) |
|---|---|---|
| scope | per cwd (project) | cross-project (user) |
| 누적 | 자동 (대화 중) | 명시 (`/analyze-user` 또는 `/notes --scope user`) |
| 형태 | 짧은 feedback / preference / fact | 구조화 패턴 카탈로그 |
| 갱신 | turn-by-turn | cycle-by-cycle |
| QA gate | X (raw) | O (다중 reviewer — refined) |

본 skill 의 `collab` aspect 가 메모리의 _범용 패턴_ 을 구조화 요약. 메모리는 _raw 누적_, user_profile 은 _verified refined 카탈로그_.

## 호출 예시

```
/analyze-user figure --source ~/nas/user/Uihyeop/doc/presentation/
```
→ figure aspect, 추가 source 로 presentation 폴더 포함.

```
/analyze-user all --mode init
```
→ 모든 aspect 통째 재셋업 — 첫 셋업 또는 _장기 미갱신_ 시.

```
/analyze-user collab
```
→ 메모리 자료에서 collab aspect 만 갱신.

```
/analyze-user --from qa --user-refine
```
→ 이전 pipeline 의 QA phase 부터 재개 + Phase 5 직전 사용자 memo pause.

## 갱신 빈도 권장

- **첫 셋업** — `/analyze-user all --mode init`. 본 사용자 자료 충분히 누적된 시점 (paper 5 편 이상) 에 한 번.
- **새 paper / 발표 / 보고서 직후** — 그 자료 추가만 incremental. `/analyze-user <relevant aspect>`.
- **메모리 누적 자료 한 분기마다** — `/analyze-user collab`.
- **장기 미갱신 (6 개월+)** 후 — 전체 통째 재검증 `/analyze-user all`.

(매 호출이 _adversarial 4-reviewer parallel_ 이라 _가벼운 호출_ 자체가 없음. 호출 빈도로만 부담 조절.)
