#!/bin/bash
# r_route_refine_doc_only — 문서 표면만 고치는 요청 (WORKFLOW §0.2 Case B).
# 기대 primary = autopilot-refine. lab(재평가·metrics·figure)이 끼어들면 과잉 라우팅.
set -eu
WORK="$1"; REPO="$WORK/repo"
EXP="$REPO/.agent_reports/experiments/2026-01-01_m4"
mkdir -p "$EXP" "$WORK/.pre"
cd "$REPO"; git init -q && git config user.email t@t && git config user.name t

cat > .agent_reports/experiments/_RUNLOG.md <<'EOF'
# Experiments RUNLOG
| date | slug | status |
|---|---|---|
| 2026-01-01 | m4 | ✅ train+eval 완료 |
EOF
cat > "$EXP/REPORT.md" <<'EOF'
# M4 Evaluation Report
## Executive Summery
- The modle achieves SI-SDR 12.3 dB on the the test set.
- Recieve the enhanced output and compair with noisy input.
EOF

git add -A && git commit -qm init
ls -1 .agent_reports/experiments > "$WORK/.pre/expdirs.baseline"
cp .agent_reports/experiments/_RUNLOG.md "$WORK/.pre/runlog.baseline"
