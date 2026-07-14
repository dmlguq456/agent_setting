#!/bin/bash
# a_draft_image — analysis_project 에 figure asset(figure_index)이 있을 때, autopilot-draft 가
# cheatsheet 산출물에 그 figure 를 *활용*(Figure 참조·caption)하는지 (SKILL §4.0a). artifact 축.
set -eu
WORK="$1"; REPO="$WORK/repo"
mkdir -p "$REPO/.claude_reports/analysis_project/paper/figures" "$WORK/.pre"
cd "$REPO"; git init -q && git config user.email t@t && git config user.name t

# 분석 자료 (draft 입력)
cat > .claude_reports/analysis_project/paper/summary.md <<'EOF'
# Paper 분석 요약
- 주제: speech enhancement (TF-domain attention)
- 핵심 결과: PESQ 3.2 (baseline 2.8)
EOF

# figure asset + index (draft §4.0a 가 발견할 source 2)
cat > .claude_reports/analysis_project/paper/figures/figure_index.md <<'EOF'
# Figure Index
| id | path | caption |
|---|---|---|
| fig1 | figures/fig1_arch.png | 모델 아키텍처 — TF attention block |
| fig2 | figures/fig2_pesq.png | PESQ 비교 (제안 vs baseline) |
EOF
printf 'PNG-DUMMY' > .claude_reports/analysis_project/paper/figures/fig1_arch.png
printf 'PNG-DUMMY' > .claude_reports/analysis_project/paper/figures/fig2_pesq.png

git add -A && git commit -qm init
echo "figures: fig1_arch, fig2_pesq" > "$WORK/.pre/figures.txt"
