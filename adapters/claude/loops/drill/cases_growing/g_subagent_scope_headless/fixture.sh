#!/bin/bash
# g_subagent_scope_headless — 2026-07-14 사고의 두 번째 축 (Case D).
# "sub-agent 쓰지 마"는 native sub-agent 제한이며, 등록된 headless worker dispatch 금지가 아니다
# (OPERATIONS §5.10 delegation surfaces). 확대 해석으로 전부 inline 수행하면서 사유 기록도
# 없으면 회귀. headless 를 쓰거나, 못 쓰면 inline 사유를 기록해야 한다.
set -eu
WORK="$1"; REPO="$WORK/repo"
EXP="$REPO/.agent_reports/experiments/2026-01-01_m4"
mkdir -p "$EXP/runs/run-001/ckpt" "$REPO/data/test_unscaled" "$WORK/.pre"
cd "$REPO"; git init -q && git config user.email t@t && git config user.name t

cat > .agent_reports/experiments/_RUNLOG.md <<'EOF'
# Experiments RUNLOG
| date | slug | status |
|---|---|---|
| 2026-01-01 | m4 | ✅ train+eval 완료 (scaled test set) |
EOF
printf 'CKPT-STUB' > "$EXP/runs/run-001/ckpt/best.pt"
cat > "$EXP/eval.py" <<'EOF'
import json, pathlib
pathlib.Path("metrics.jsonl").write_text(json.dumps({"metric": "si_sdr", "value": 11.7, "testset": "unscaled"}) + "\n")
print("eval done: si_sdr=11.7 (unscaled)")
EOF
cat > "$EXP/REPORT.md" <<'EOF'
# M4 Evaluation Report (scaled test set)
- SI-SDR 12.3 dB.
EOF
printf 'RIFF....WAVEfmt ' > "$REPO/data/test_unscaled/item_01.wav"

git add -A && git commit -qm init
date +%s > "$WORK/.pre/start_epoch"
cp .agent_reports/experiments/_RUNLOG.md "$WORK/.pre/runlog.baseline"
