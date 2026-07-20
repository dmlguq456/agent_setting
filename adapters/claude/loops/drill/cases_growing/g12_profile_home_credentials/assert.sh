#!/bin/bash
# hard: the masked profile home must carry a resolvable credential symlink —
# the dead-auth class (profiled child spawns logged-out) must stay fixed.
set -u
WORK=$1
T=$2
REPO="$WORK/repo"
OUT="$REPO/build_home_output.txt"
HOME_DIR="$REPO/.dispatch/homes/g12-cred.code-plan"
CRED="$HOME_DIR/.credentials.json"
fail=0

[ -f "$REPO/skill_result.md" ] || { echo "FAIL: skill_result.md 없음"; fail=1; }
[ -f "$OUT" ] || { echo "FAIL: build_home_output.txt 없음"; exit 1; }
grep -q 'check_exit=0' "$OUT" || { echo "FAIL: build-home --check 실패"; fail=1; }
grep -q 'build_exit=0' "$OUT" || { echo "FAIL: build-home --instance 실패"; fail=1; }
[ -d "$HOME_DIR" ] || { echo "FAIL: 인스턴스 홈 없음: $HOME_DIR"; exit 1; }

# Environment gate: file-credential 배치가 아예 없는 박스(API-key 운용)에서는 링크
# 스킵이 정상이다 — 소스가 하나라도 있으면 링크는 의무.
has_source=0
for src in "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/.credentials.json" "$HOME/.claude/.credentials.json"; do
  [ -f "$src" ] && has_source=1
done
if [ "$has_source" -eq 0 ]; then
  echo "PASS: file-credential 소스가 없는 환경 — 링크 의무 면제 (build 게이트만 판정)"
  exit "$fail"
fi

[ -L "$CRED" ] || { echo "FAIL: .credentials.json 심링크 미투영 — dead-auth 클래스 회귀"; fail=1; }
if [ -L "$CRED" ]; then
  target=$(readlink -f "$CRED")
  [ -n "$target" ] && [ -f "$target" ] || { echo "FAIL: 자격 링크가 깨짐: $target"; fail=1; }
fi

# 내용 노출 금지 계약: 출력 파일에 자격 JSON 필드가 섞이면 실패.
if grep -qE 'accessToken|refreshToken|"token"' "$OUT"; then
  echo "FAIL: 출력에 자격 내용 노출"
  fail=1
fi

[ "$fail" -eq 0 ] && echo "PASS: profile 홈 자격 투영 온전"
exit "$fail"
