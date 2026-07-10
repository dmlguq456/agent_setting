#!/bin/bash
# g_stage_dispatch: standard+ 다파일 dev 작업을 spec-backed fixture 에서 준다.
# 목적(§8.5.5 doc-efficacy) — skill 문서(dev-pipeline Step 1~7)만 주고, conductor 가
#   각 스테이지를 depth-2 headless 로 분사하는지(스푼피딩 없이) 관찰.
# SD-13 전제: fixture 에 spec/ 가 이미 있어 spec precondition 통과.
set -eu
WORK=$1; mkdir -p "$WORK/.pre"
git init -q --bare "$WORK/origin.git"
git clone -q "$WORK/origin.git" "$WORK/repo"
cd "$WORK/repo"
git config user.email drill@test && git config user.name drill
git checkout -q -b main

# 소스 두 파일
printf 'def main():\n    print("app")\n\n\nif __name__ == "__main__":\n    main()\n' > app.py
printf 'VERSION = "0.1.0"\n' > version.py

# spec-backed: artifact root + spec/prd.md + pipeline_state.yaml (SD-13 전제 충족)
mkdir -p .agent_reports/spec
cat > .agent_reports/spec/prd.md <<'PRD'
# PRD — demo config app

## 목표
YAML 설정 로딩 모듈을 추가한다 — 기본값·환경변수 override·스키마 검증.

## 범위
- `config_loader.py` — 로더 진입점
- `settings/` — 기본 설정 파일 디렉토리
- `app.py` 가 로더를 사용하도록 배선
PRD
cat > .agent_reports/spec/pipeline_state.yaml <<'PS'
project: demo-config-app
spec_version: 1
stage: spec
PS

git add -A && git commit -q -m "init: app + spec" && git push -q -u origin main
git rev-parse main > "$WORK/.pre/main_sha"
