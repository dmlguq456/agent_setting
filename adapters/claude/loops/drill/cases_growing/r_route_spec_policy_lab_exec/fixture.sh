#!/bin/bash
# r_route_spec_policy_lab_exec — 평가 정책 변경 + 재평가 (WORKFLOW §0.2 Case C).
# 기대: blueprint sync = autopilot-spec update (snapshot 포함), 실행 = autopilot-lab eval.
# 어느 한쪽이 다른 쪽을 대체하면 회귀 (spec 만 고치고 재평가 생략 / 재평가만 하고 정책 미기록).
set -eu
WORK="$1"; REPO="$WORK/repo"
EXP="$REPO/.agent_reports/experiments/2026-01-01_m4"
mkdir -p "$REPO/.agent_reports/spec" "$EXP/runs/run-001/ckpt" "$WORK/.pre"
cd "$REPO"; git init -q && git config user.email t@t && git config user.name t

cat > .agent_reports/spec/prd.md <<'EOF'
# PRD — M4 speech enhancement

## Evaluation policy
- Test mixing: target/noise gain scaling ENABLED (SNR-normalized).
- Metrics: SI-SDR, PESQ.
EOF
cat > .agent_reports/spec/pipeline_state.yaml <<'EOF'
mode: research
phase: eval
EOF
cat > .agent_reports/experiments/_RUNLOG.md <<'EOF'
# Experiments RUNLOG
| date | slug | status |
|---|---|---|
| 2026-01-01 | m4 | ✅ train+eval 완료 (scaled 정책) |
EOF
printf 'CKPT-STUB' > "$EXP/runs/run-001/ckpt/best.pt"
cat > "$EXP/eval.py" <<'EOF'
import json, pathlib
pathlib.Path("metrics.jsonl").write_text(json.dumps({"metric": "si_sdr", "value": 11.2, "policy": "unscaled"}) + "\n")
print("eval done: si_sdr=11.2 (unscaled)")
EOF
cat > "$EXP/REPORT.md" <<'EOF'
# M4 Evaluation Report (scaled policy)
- SI-SDR 12.3 dB.
EOF

git add -A && git commit -qm init
cp .agent_reports/spec/prd.md "$WORK/.pre/prd.baseline"
ls -1 .agent_reports/experiments > "$WORK/.pre/expdirs.baseline"
cp .agent_reports/experiments/_RUNLOG.md "$WORK/.pre/runlog.baseline"
