#!/bin/bash
# a_draft_image assert
# 검증 행동: draft 가 분석된 figure(figure_index)를 cheatsheet 산출물에 활용하는가 (SKILL §4.0a
#   multi-source figure discovery → Figure caption·참조). 자주 빠지는 craft.
# hard: draft 산출물(documents/)에 figure 참조(fig*_*.png / Figure N / includegraphics) 존재.
WORK="$1"; T="$2"; REPO="$WORK/repo"
fail=0
DOCS="$REPO/.claude_reports/documents"
hit=$(grep -rliE 'fig1_arch|fig2_pesq|Figure[ _][0-9]|includegraphics|figure_index' "$DOCS" 2>/dev/null | head -1)
if [ -n "$hit" ]; then
  echo "PASS: draft cheatsheet 가 figure 참조 ($(basename "$hit"))"
else
  echo "FAIL: draft 산출물에 figure 참조 없음 — 첨부 figure 미활용 (SKILL §4.0a craft 누락)"; fail=1
fi
[ -d "$DOCS" ] && echo "WARN-OK: documents 산출물 생성됨" || echo "WARN: documents 산출물 자체 없음 (draft 미완·turn cap?)"
exit $fail
