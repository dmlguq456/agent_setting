#!/bin/bash
# g_eval_stage_dispatch_or_reason — standard+ eval 실행 그래프 (Case E).
# run/media/report/verify 가 분리 가능할 때 main 세션이 전부 직접 수행하면 안 되고,
# worker dispatch 또는 명시적 inline-exception 기록이 있어야 한다
# (capabilities/autopilot-lab.md eval topology + OPERATIONS §5.10 inline exceptions).
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
printf 'RIFF....WAVEfmt ' > "$REPO/data/test_unscaled/item_01.wav"
printf 'RIFF....WAVEfmt ' > "$REPO/data/test_unscaled/item_02.wav"

git add -A && git commit -qm init
cp .agent_reports/experiments/_RUNLOG.md "$WORK/.pre/runlog.baseline"
