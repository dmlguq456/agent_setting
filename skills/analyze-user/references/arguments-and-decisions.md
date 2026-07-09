## Argument Parsing

### `<aspect>` (REQUIRED)

| aspect | 갱신 대상 (profile 레코드) | source (사용자 `--source <path>` 명시 — 하드코딩 X) |
|---|---|---|
| `figure` | `mem profile 01_paper_figure_style` | 사용자 폴더 명시 — paper PDF 자료 / figure 모음 폴더 / pptx 안 figure 자료 (자동 변환 PNG) |
| `writing` | `mem profile 02_paper_writing_style` | 사용자 폴더 명시 — paper PDF·docx 자료·LaTeX main.tex·reports (`.docx` / `.hwpx` / `.hwp` 자동 변환) |
| `presentation` | `mem profile 03_presentation_strategy` | 사용자 폴더 명시 — pptx 자료 (자동 PDF + PNG 변환, 시각 layout fidelity) |
| `analysis` | `mem profile 04_analysis_methodology` | 사용자 폴더 명시 — 코드 자리 analysis script + paper Method/Experiment 절 |
| `domain` | `mem profile 05_domain_expertise` | 사용자 폴더 명시 — paper 자료 + 사용자 GitHub URL (옵션) |
| `coding_convention` | `mem profile 07_coding_convention` | 사용자 폴더 명시 — 코드 repo 자리 (`model/`·`train*.py`·`config*.yaml`·`*.ipynb` 패턴) |
| `all` | 6 aspect (01·02·03·04·05·07, 각 stem 별 DB 레코드) | 사용자 `--source <path>` 한 자리 (또는 복수 콤마 분리) — 안 자료 type 별 aspect 자동 분류 (재귀 자동 발견) |

> **하드코딩 path X — 사용자 자료 명시 default**: 모든 aspect 자리 _기본 source 위치 자체_ 가 _사용자 명시_ 자리. `--source` 명시 없으면 _자료 0 자리_, 사용자 안내 한 줄 — 사용자가 _참고 자료 폴더 path_ 던져주는 자리 ([analyze-project](../analyze-project/SKILL.md) doc mode 와 같은 패턴).

### `--source <path>` (옵션)

추가 source 디렉토리 명시. 기본 source 외 더 살펴봐야 할 자리. 복수 지정 가능 (콤마 분리).

### `--mode init|update` (옵션, default `update`)

- `init` — 처음 셋업. 기존 레코드 body 를 `_internal/versions/` 에 스냅샷 후 새 body 로 DB write (파일 통째 교체 X — DB record 교체).
- `update` (default) — incremental. 새 자료 발견 시 기존 레코드 body(`mem profile <stem>` 읽기) 에 누적·갱신. 변경 항목은 _누적 vs 교체 vs 제거_ 셋 중 명시.

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
- `verify` — Phase 3 부터 (Phase 3.5 prior-version 변증법 대조 포함, update mode)
- `qa` — Phase 4 부터
- `output` — Phase 5 부터
- `repro` — Phase 5b 부터 (figure aspect repro gate)
- `summary` — Phase 6 부터

### `--user-refine` (boolean, opt-in)

분석 산출 _직전 (Phase 5 직전)_ pause. 사용자가 추출된 패턴에 _직접 memo 추가_ 하고 싶을 때. 명시 신호 ("사용자 검토 끼워" / "memo 추가" / `--user-refine`) 있을 때만 켬. 메인 에이전트가 임의 추가 X.

## Decision Defaults (no autonomy gating)

| Decision Point | Default Behavior |
|---|---|
| Source 발견 0 건 (aspect 별) | Auto-stop 해당 aspect, 다른 aspect 만 계속. _all_ 호출 시 1 개 aspect 만 실패해도 나머지 진행. |
| Cross-aspect 모순 발견 | 자동 해소 (source 인용 빈도 / 최신 자료 우선). 해소 불가 자리는 _open question_ 으로 남기고 진행. |
| QA Phase 🔴 finding | Phase 2-3 자동 retry (max 2 회). |
| Retry 2 회 실패 | pipeline failed, summary 작성 후 중단. |
| **Figure repro gate (Phase 5b)** | figure aspect 에서만 실행. render→대조→spec 보정 max 2 loop. spec-fixable 격차 수렴 시 통과, 잔차가 _원본 복제 영역_ 뿐이면 통과, 남으면 open question. cairosvg/rsvg/inkscape 모두 부재 시 게이트 skip + 한 줄 경고. |
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
consensus:
  high: 18    # 3/3
  medium: 7   # 2/3
  low: 4      # 1/3 (quarantine)
qa_findings:
  red: 0
  yellow: 3
  green: 12
quarantine_outcome:
  promoted: 2
  dropped: 1
  open_question: 1
timestamp: "2026-05-22T15:30:00Z"
```

재개 시 CLI flag override 우선. `--from <stage>` 명시되면 그 phase 부터.
