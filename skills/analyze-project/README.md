# analyze-project

> 본 README 는 `SKILL.md` 의 GitHub 표시용 mirror. 권위 있는 동작 명세는 `SKILL.md`.

## 개요
코드베이스를 분석해 `.claude_reports/analysis_project/{code,paper,doc}/`에 구조화된 문서를 생성하는 skill. autopilot 파이프라인의 **사전 준비 skill**. mode별:
- `--mode code` — 코드베이스 모듈 매핑·interface
- `--mode paper` — 논문 PDFs cards + overview
- `--mode doc` — reviewer comments / format templates / past samples 분류

## 호출 형식
```
/analyze-project [--mode code|paper|doc] [<scope/target/input-folder>] [--skip-qa]
```

- `--mode`: 생략 시 code/doc 자동 감지 (paper만 명시 필요)
- `--skip-qa` — Phase 5 QA Verification 생략
- 플래그 제거 후 남은 텍스트는 target directory / scope

## 언어 규칙
- 내부 추론은 영어
- `.claude_reports/analysis_project/` 산출 문서는 **영어**
- 사용자 설명은 한국어

## Phase 1: Codebase Analysis (code mode)
범위 결정:
- `$ARGUMENTS`가 디렉토리 → recursive 읽기
- keyword → CLAUDE.md 구조 섹션으로 관련 모듈 매핑 후 읽기
- 비어있음/없음 → CLAUDE.md Project Structure 참조, 없으면 repo root entry point + `src/`·`lib/`

식별:
- 각 파일/모듈 역할과 인터페이스
- 데이터 플로우 (input → processing → output)
- 모듈 간 의존성
- 설계 의도 및 핵심 알고리즘

## Phase 2: Documentation
`.claude_reports/analysis_project/code/` 아래 topic별 md 파일로 분리:
- role 기준 분할 (monolithic 금지)
- code-level 상세 집중
- 영어
- 각 문서 끝에 `## Interface Reference` 섹션:
  ```
  | Class/Function | File | Signature | Called by |
  |---|---|---|---|
  | `ClassName` | file.py:L | `(arg1, ...) → return` | `caller.func` |
  ```
- 모든 public class, 핵심 함수, cross-module caller 있는 함수 포함

## Phase 3: CLAUDE.md
코드 내용 최소화, 아래만 포함:
- 산출 문서 리스트 + coverage table
- 행동 규칙 (코딩 rules, 제한, commit rules)
- 프로젝트 구조 overview (tree)
- 실행 예시
- 기존 CLAUDE.md 존재 시 기존 규칙 보존 + 새 발견 merge

## Phase 4: Documentation Coverage 검증
주요 모듈 디렉토리의 모든 코드 파일이 최소 1개 산출 문서에 cover되는지 확인.

## Phase 5: QA Verification (선택, `--skip-qa`로 생략)
품질관리팀을 code review 모드로 호출하여 Interface Reference 엔트리를 실제 소스와 대조.
- **범위**: 현재 run에서 업데이트된 문서 파일만
- **최소 검증**: 파일당 최소 2개 엔트리 — 시그니처, 파일 경로, 라인 번호 대조
- **QA 모델**: Light QA (sonnet)

## paper mode
보유 논문 PDFs를 읽어 `.claude_reports/analysis_project/paper/`에 논문별 cards + `00_overview_and_constraints.md` 생성. 연구팀에 위임. autopilot-draft·autopilot-code·autopilot-research가 implicit input source로 활용.

## doc mode
reviewer comments / format templates / past samples / mixed doc 자료를 `.claude_reports/analysis_project/doc/{name}/` 하위에 분류 (reviewers/, formats/, samples/, misc/). autopilot-draft의 format spec auto-discovery source.

---
*원본: `~/.claude/skills/analyze-project/SKILL.md`*
