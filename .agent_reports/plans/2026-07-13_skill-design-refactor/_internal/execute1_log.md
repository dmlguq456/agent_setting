# execute1 log — CORE + Cluster 2 (SoT consolidation)

> stage: code-execute #1 (depth-2) · date: 2026-07-13 · scope: 플랜 §1(CORE-1~4) + §2(C2-1~5)
> behavior-preserving refactor — pointer 화·SoT 흡수·정량 lint 승격. 의미 변경 0.

## CORE

| 파일 | 변경 |
|---|---|
| `core/CONVENTIONS.md` | §5.6a "Skill-Design 정량 규범 (scan.sh lint SoT)" 표 신설(줄수/depth/frontmatter ↔ scan.sh 컬럼 1:1) + §5.6 에 "단일 Reference Index 표 1회" 컨벤션 1줄(C2-5) 추가 |
| `core/DESIGN_PRINCIPLES.md` | §10 "Skill-Design Tenets (Pocock 4축 + Predictability)" 신설(tenet만·정량 수치 X, CONVENTIONS §5.6a 상호 포인터) + 부록 이력 표에 §10 행 |
| `roles/modes/design/_design_rules.md` | §시각 자가검증 루프에 4-scope(ui/webapp·slide·icon·diagram) 렌더 표 흡수(design-components + design-review 합집합) + 렌더불가 fallback 문단. **core-first — roles/ 만 편집, adapter 사본은 sync-skills 재투영** |
| `tools/skill-conformance/scan.sh` | `git mv` (구 `.agent_reports/analysis_project/code/_internal/skill_design_audit/scan.sh` → 신규 stable 위치). executable 유지, TSV 10-컬럼 shape 불변 |
| `skills/sync-skills/references/finalize-and-hooks.md` | Step 6c "scan.sh 정량 규범 lint (§CONVENTIONS 5.6a)" 신설 — `--check` 에서 line_ok=N/ref_depth_ok=N drift 노출 |
| `skills/sync-skills/SKILL.md` | Step 표 6·6b·7 행 → 6·6b·**6c**·7 (scan.sh lint 편입) + Reference Index 병합(C2-5) |
| `loops/drill/run.sh` | `AXIS=static` 브랜치 신설 — static-assert 케이스는 adapter turn 없이 assert 만 실행(zero-cost) |
| `loops/drill/cases/g7_skill_conformance/{config,fixture.sh,assert.sh,prompt.md}` | 신규 static-assert 회귀 케이스. assert = live `skills/` 에 scan.sh 돌려 line_ok=N·ref_depth_ok=N 행 0 + disable_model 컬럼 파싱 검증(Cluster 1 flip 후 sub-skill=true 상향은 TODO — flip 전/후 모두 자연 PASS). run.sh 통해 PASS 검증 완료 |
| `loops/drill/README.md` | 케이스 목록에 static 축 설명 + g7_skill_conformance 행 등재 |

## Cluster 2 — SoT 통합

### C2-1 Plan Resolution 단일 authority
- authority = `skills/autopilot-code/references/arguments-and-decisions.md` — 헤더 "keep in sync…" → "canonical authority — single SoT".
- 블록 → 1줄 pointer: `code-execute`·`code-test`·`code-report`·`code-refine` SKILL.md + 4개 README.md 미러.
- **behavior-preserve**: 블록이 byte-identical 이 아니었음 — code-test 의 no-match "직접 파일/디렉터리 테스트" fallback, code-refine 의 `plan.md`+`plan_ko.md` 이중 해석을 pointer 옆에 고유 note 로 보존(SD-10 variance-bug 방지). code-report `:37` "resolved via Plan Resolution above" → "위 pointer 의 authority 절차".

### C2-2 Language Rule 통합
- SoT = `arguments-and-decisions.md:1` — richer wording 흡수("All user-facing output in natural Korean … don't translate from an English draft" + code track 전 스테이지 SoT 명시).
- `code-execute`·`code-refine`·`code-report`·`code-test`·`code-plan` SKILL.md `## Language Rule` 블록 5개 → 1줄 pointer.

### C2-3 시각검증 loop 단일 SoT
- SoT = `_design_rules.md §시각 자가검증 루프`(CORE-3 scope 표 흡수 완료).
- `design-components`·`design-review`·`design-tokens`·`autopilot-design` SKILL.md → 공통 렌더 흐름·scope 표 pointer 화. 각 스킬 고유 gate 유지: design-tokens=specimen-consume gate, design-review=critic 렌더 framing, design-components=산출-직후-렌더 invariant.

### C2-4 `<artifact-root>` 스니펫 → CONVENTIONS §5.1
- verbatim `REPORTS_DIR=…` 스니펫 6개(`analyze-project`·`audit`·`autopilot-research`·`autopilot-draft`·`autopilot-spec`·`autopilot-refine`) → `[CONVENTIONS §5.1]` 1줄 pointer.

### C2-5 Required Reads + Reference Map → 단일 Reference Index
- 13 라우터(analyze-project·analyze-user·audit·autopilot-code·autopilot-draft·autopilot-lab·autopilot-note·autopilot-refine·autopilot-research·autopilot-spec·draft-strategy·post-it·sync-skills) 각각 두 절 → **`## Reference Index` 3-컬럼 표**(파일 · 언제 로드(의무) · 내용). Reference Map 의 내용 detail + Required Reads 의 시점·의무 둘 다 보존(SD-10 포인터 약화 방지). autopilot-code/autopilot-lab 은 두 절이 멀리 떨어져 있어 상단 표로 병합 + 하단에 "위 Reference Index 참조" 1줄.

## 검증 결과 (stop 전)
- `bash tools/skill-conformance/scan.sh skills` → 10 컬럼 / 29 행(header+28), line_ok=N 0, ref_depth_ok=N 0.
- `grep -rln "keep in sync" skills/*/SKILL.md skills/*/README.md` = 0.
- `grep -rln "## Language Rule" skills/code-*/SKILL.md` = 0.
- `grep -rln "REPORTS_DIR=.agent_reports; [ -d .claude_reports ]" skills/*/SKILL.md` = 0.
- 13 라우터 각 old-header 0 / Reference Index 1.
- `python3 tools/build-manifest.py --check` → up-to-date (frontmatter 무변경).
- drill `g7_skill_conformance` run.sh 통해 PASS (0 tokens).

## 다음 스테이지 인계
- **sync-skills 미실행** (depth-2 Skill tool 없음). core/roles 편집 → adapter 미러(`adapters/claude/*`·`adapters/codex/*`·opencode) + `skills/*/README.md` 재투영 필요. `_design_rules.md` 3사본 parity 재동기 포함. → **다음 test 스테이지가 sync-skills 실행**(SD-6 게이트: README/manifest 재생성 + doctor 28/28/9 parity).
- Cluster 3·Cluster 1 은 본 스테이지 범위 밖(후속 스테이지).
