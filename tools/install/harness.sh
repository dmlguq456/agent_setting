#!/usr/bin/env sh
# harness.sh — thin POSIX sh launcher: 심링크(AGENT_HOME) 해석 후 installer.py 서브명령 트리로
# 위임한다 (fleet.sh 동형 패턴, PRD §공통 "언어·런타임"). 옵션은 그대로 installer.py 로 전달.
# 설치: PATH 상 `harness` 심링크 → 이 스크립트 (INST-OPEN-2 확정: 진입 명령 = `harness`).
set -eu

# 심링크 경유해도 실제 스크립트 위치 해석 (POSIX sh — bash 배열/BASH_SOURCE 없이 $0 만 사용)
SOURCE=$0
while [ -h "$SOURCE" ]; do
  DIR=$(CDPATH= cd -P "$(dirname "$SOURCE")" && pwd)
  SOURCE=$(readlink "$SOURCE")
  case $SOURCE in
    /*) ;;
    *) SOURCE="$DIR/$SOURCE" ;;
  esac
done
SCRIPT_DIR=$(CDPATH= cd -P "$(dirname "$SOURCE")" && pwd)
INSTALLER_PY="$SCRIPT_DIR/installer.py"

PY=$(command -v python3 || command -v python || true)
if [ -z "$PY" ]; then echo "harness: python3 가 필요합니다." >&2; exit 1; fi
if [ ! -f "$INSTALLER_PY" ]; then echo "harness: installer.py 를 찾을 수 없습니다 ($INSTALLER_PY)." >&2; exit 1; fi

exec "$PY" "$INSTALLER_PY" "$@"
