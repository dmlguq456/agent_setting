#!/bin/bash
# g7 static-assert: 사용자 turn 없음 (AXIS=static). fixture 는 자리만 만든다 —
# assert.sh 는 WORK 이 아니라 live harness repo 의 skills/ 를 scan 한다.
set -eu
WORK=$1
mkdir -p "$WORK/repo"
