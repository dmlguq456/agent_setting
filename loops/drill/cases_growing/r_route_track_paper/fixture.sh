#!/bin/bash
# r_route_track_paper — "camera-ready" 발화 → 문서 트랙(autopilot-draft paper) 라우팅 +
# high-stakes qa 상향(adversarial). routing 축. (라우팅 정합성 — README 부르는 법 표.)
set -eu
WORK="$1"; REPO="$WORK/repo"
mkdir -p "$REPO/.claude_reports/analysis_project/paper" "$WORK/.pre"
cd "$REPO"; git init -q && git config user.email t@t && git config user.name t
cat > .claude_reports/analysis_project/paper/summary.md <<'EOF'
# Paper 분석
- ICML 제출 논문, speech enhancement
- 본문 완성, camera-ready 다듬기 단계
EOF
printf '\\documentclass{article}\n\\begin{document}\ndraft body\n\\end{document}\n' > main.tex
git add -A && git commit -qm init
