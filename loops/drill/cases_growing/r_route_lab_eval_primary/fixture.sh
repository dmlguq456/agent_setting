#!/bin/bash
# r_route_lab_eval_primary — 2026-07-14 사고 재현 fixture (WORKFLOW §0.2 Case A).
# "기존 보고서 업데이트"라는 표면 산출물만 보고 autopilot-refine 을 primary 로 고르는 회귀를 감시한다.
# 완료된 학습 실험(m4) + 기존 REPORT.md + unscaled test set 을 준다. 기대 primary = autopilot-lab eval.
set -eu
WORK="$1"; REPO="$WORK/repo"
EXP="$REPO/.agent_reports/experiments/2026-01-01_m4"
mkdir -p "$EXP/runs/run-001/ckpt" "$REPO/data/test_unscaled" "$WORK/.pre"
cd "$REPO"; git init -q && git config user.email t@t && git config user.name t

cat > .agent_reports/experiments/_RUNLOG.md <<'EOF'
# Experiments RUNLOG
| date | slug | status |
|---|---|---|
| 2026-01-01 | m4 | ✅ train+eval 완료 (scaled test set, REPORT.md 참조) |
EOF
cat > "$EXP/STORY.md" <<'EOF'
# m4 — speech enhancement
- 학습 완료, scaled mixing test set 으로 1차 평가 완료.
EOF
cat > "$EXP/REPORT.md" <<'EOF'
# M4 Evaluation Report (scaled test set)
## Executive Summary
- SI-SDR 12.3 dB on the scaled test set.
EOF
cat > "$EXP/summary.md" <<'EOF'
m4: done — SI-SDR 12.3 (scaled). See REPORT.md.
EOF
printf 'CKPT-STUB' > "$EXP/runs/run-001/ckpt/best.pt"
cat > "$EXP/config.yaml" <<'EOF'
model: m4
sample_rate: 48000
EOF
# 빠르게 끝나는 결정적 eval 스텁 — 드릴이 실제 실행 가능하도록.
cat > "$EXP/eval.py" <<'EOF'
import json, sys, pathlib
out = pathlib.Path("metrics.jsonl")
out.write_text(json.dumps({"metric": "si_sdr", "value": 11.7, "testset": "unscaled"}) + "\n")
print("eval done: si_sdr=11.7 (unscaled)")
EOF
printf 'RIFF....WAVEfmt ' > "$REPO/data/test_unscaled/item_01.wav"
printf 'RIFF....WAVEfmt ' > "$REPO/data/test_unscaled/item_02.wav"

git add -A && git commit -qm init
# baseline 스냅샷: RUNLOG 원문과 실험 dir 목록 (append-only·lineage 검증용)
cp .agent_reports/experiments/_RUNLOG.md "$WORK/.pre/runlog.baseline"
ls -1 .agent_reports/experiments > "$WORK/.pre/expdirs.baseline"
md5sum "$EXP/REPORT.md" > "$WORK/.pre/report.md5"
