# analyze-papers (legacy — 통합됨)

> ⚠️ **DEPRECATED**: 본 skill은 `analyze-project --mode paper`로 통합되어 별도 skill로는 존재하지 않습니다. 본 README는 historical reference로만 보관 (Notion 페이지 [📚 analyze-papers](https://www.notion.so/34987c2bb75381739e00db18de46c62b) 미러).
>
> **현재 사용법**: `/analyze-project --mode paper [specific paper or 'all']`

## 개요 (historical)
`.claude_reports/refs/`의 참고 논문 PDF를 읽어 `.claude_reports/docs_paper/`에 논문 문서를 생성/갱신하던 skill. `00_overview_and_constraints.md`를 포함. 연구팀에 위임.

> 현재는 `analyze-project --mode paper`로 통합되어 `.claude_reports/analysis_project/paper/`에 산출.

## 통합 후 호출 형식
```
/analyze-project --mode paper [specific paper or 'all']
```

## 언어 규칙
- 내부 추론 영어, 사용자 출력 한국어

## 위임 — 연구팀
```
Analyze reference papers and generate paper documentation.

Scope: {$ARGUMENTS or "all"}
Date: {YYYY-MM-DD}

## Inputs
- Reference PDFs: (current convention: user-supplied folder or `.claude_reports/analysis_project/paper/` raw section)
- Existing paper docs: .claude_reports/analysis_project/paper/*.md
- Existing code docs: .claude_reports/analysis_project/code/*.md (for paper-code mapping)
- Source code: 프로젝트 modules/ (for verifying paper-code alignment)
```

## 절차 (요약)
1. 모든 reference PDF 읽기 — core contributions, architecture, equations, experimental findings, ablation
2. 기존 paper docs 읽기 — 무엇이 있고 무엇을 갱신할지
3. Code docs와 source code 읽어 paper-code alignment 검증
4. 논문별 summary 파일 생성/갱신 (연구팀이 파일명 결정)
   - title/venue/year, core contribution, architecture, key design decisions, equations, ablation, paper-to-code mapping
5. `00_overview_and_constraints.md` 생성/갱신 — **가장 중요**:
   - Paper Evolution
   - Paper → Code Variant Mapping
   - Core Design Principles
   - Architecture Constraints (Hard / Soft)
   - Terminology Mapping
   - Cross-Paper Relationships
6. paper-code alignment 검증 + discrepancy 문서화

Write in English. Code identifiers stay as-is.

## Post-Analysis
연구팀 반환 후:
1. 파일 경로와 요약을 사용자에게 relay
2. `00_overview_and_constraints.md` 먼저 검토 권장

---
*원본 (legacy): `~/.claude/skills/analyze-papers/SKILL.md` (제거됨, analyze-project --mode paper로 통합)*
