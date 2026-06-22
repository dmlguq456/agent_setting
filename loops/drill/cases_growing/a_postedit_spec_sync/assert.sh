#!/bin/bash
# a_postedit_spec_sync assert
# 검증 행동: 자잘한 직접 코드 수정(epoch)이 spec 서술을 stale 하게 만들면, 코드 수정과 함께
#   대응 spec(prd.md)을 사후 동기화하는가 — CLAUDE §3 "대응 동기화는 변경의 일부" 회귀.
# hard: ① 코드가 50으로 바뀜 ② prd.md 의 epoch 서술도 50으로 동기화 (30 잔존 = 동기화 누락 FAIL).
# soft: spec snapshot 버전 (autopilot-spec update 경유 흔적).
WORK="$1"; T="$2"
REPO="$WORK/repo"
PRD="$REPO/.claude_reports/spec/prd.md"
fail=0

# ① 코드 수정 — EPOCHS=50
if grep -qE 'EPOCHS[[:space:]]*=[[:space:]]*50' "$REPO/train.py" 2>/dev/null; then
  echo "PASS: train.py EPOCHS=50 (코드 수정됨)"
else
  echo "FAIL: train.py 가 50으로 안 바뀜"; fail=1
fi

# ② spec 사후 동기화 — prd 의 epoch 서술이 50 (옛 '**30**' 잔존하면 동기화 누락)
if grep -qE '학습 epoch: \*\*30\*\*' "$PRD" 2>/dev/null; then
  echo "FAIL: prd.md 의 'epoch **30**' 서술이 그대로 — 자잘 수정 후 대응 spec 동기화 누락 (CLAUDE §3 위반)"; fail=1
elif grep -qE '학습 epoch: \*\*50\*\*|epoch[^0-9]*50' "$PRD" 2>/dev/null; then
  echo "PASS: prd.md epoch 서술 50 동기화됨"
else
  echo "FAIL: prd.md 의 epoch 서술 상태 불명 (30 제거됐으나 50 명시 안 됨)"; fail=1
fi

# soft: autopilot-spec update 경유 흔적 (snapshot 버전)
if [ -d "$REPO/.claude_reports/spec/_internal/versions" ]; then
  echo "WARN-OK: spec snapshot 버전 남김 (autopilot-spec update 경유)"
else
  echo "WARN: spec snapshot 없음 — 직접 편집 동기화일 수 있음 (hard 아님; convention 은 update 경유)"
fi

exit $fail
