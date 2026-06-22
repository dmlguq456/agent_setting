#!/bin/bash
# a_lab_audio_html — eval 결과가 오디오일 때, autopilot-lab 이 *재생 가능한 HTML*(<audio> 임베드)
# 보고서를 만드는지 (SKILL line 445/469: audio→HTML, md 는 <audio> 차단). artifact 축.
set -eu
WORK="$1"; REPO="$WORK/repo"
EXP="$REPO/.claude_reports/experiments/2026-01-01_demo"
mkdir -p "$EXP/outputs" "$WORK/.pre"
cd "$REPO"; git init -q && git config user.email t@t && git config user.name t

cat > .claude_reports/experiments/_RUNLOG.md <<'EOF'
# Experiments RUNLOG
| date | slug | status |
|---|---|---|
| 2026-01-01 | demo | ✅ eval 완료 (enhanced 오디오 출력) |
EOF
cat > "$EXP/STORY.md" <<'EOF'
# demo — speech enhancement eval
- ckpt 평가 완료. enhanced / noisy 오디오 쌍 출력 (청취 비교 대상).
EOF
# 더미 오디오 결과 (재생 대상 — 실제 wav 아니어도 존재·확장자만)
printf 'RIFF....WAVEfmt ' > "$EXP/outputs/enhanced_01.wav"
printf 'RIFF....WAVEfmt ' > "$EXP/outputs/noisy_01.wav"

git add -A && git commit -qm init
echo "audio: enhanced_01.wav, noisy_01.wav" > "$WORK/.pre/audio.txt"
