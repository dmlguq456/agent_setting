#!/bin/bash
# a_postedit_spec_sync — spec-backed 프로젝트에서 *자잘한 직접 코드 수정*(epoch 값 1줄)이
# spec 서술을 stale 하게 만들 때, 코드 수정 + 대응 spec 사후 동기화를 하는지 (CLAUDE §3).
set -eu
WORK="$1"
REPO="$WORK/repo"
mkdir -p "$REPO/.claude_reports/spec" "$WORK/.pre"
cd "$REPO"
git init -q && git config user.email t@t && git config user.name t

# 코드 — train.py 의 EPOCHS=30 (자잘 수정 대상)
cat > train.py <<'EOF'
EPOCHS = 30  # 학습 epoch 수
def train():
    for e in range(EPOCHS):
        pass
EOF

# spec — prd.md 가 epoch 30 을 서술 (코드 바뀌면 이게 stale → 동기화 대상)
cat > .claude_reports/spec/prd.md <<'EOF'
# Demo Spec
## [research] 설정
- 학습 epoch: **30** (기본값)
- optimizer: Adam
EOF
cat > .claude_reports/spec/pipeline_state.yaml <<'EOF'
project_name: demo
mode: [research]
phases:
  spec: done
  dev: in_progress
last_updated: 2026-01-01
EOF

git add -A && git commit -qm init

# pre-state 기록
grep EPOCHS train.py > "$WORK/.pre/epochs_before.txt"
cp .claude_reports/spec/prd.md "$WORK/.pre/prd_before.md"
