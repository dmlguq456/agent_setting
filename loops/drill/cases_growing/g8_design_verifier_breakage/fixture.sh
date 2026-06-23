#!/bin/bash
# g8_design_verifier_breakage: 의도적으로 깨진 디자인 HTML 두 개를 빌드한다.
#   (1) preview.html — <script> 가 undefined function 호출 → console error (MCP-free det 신호)
#   (2) broken_layout.html — overflow + overlap + 0px-height container (레이아웃 깨짐)
# verifier 가 이 둘을 잡는지 assert.sh 가 검수한다.
set -eu
WORK=$1
mkdir -p "$WORK/.pre" "$WORK/repo"
cd "$WORK/repo"

git init -q && git checkout -q -b main
git config user.email drill@test && git config user.name drill

# --- (1) console-error HTML ---
# DESIGN_RE = /(designs?\/|\/design\/|spec\/design|preview\.html$|slides?\.html$|.../
# "preview.html" 으로 naming 해야 console-check.mjs 의 DESIGN_RE 가 직접 경로 일치.
cat > preview.html <<'HTML_EOF'
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>Broken Console Test</title>
  <style>
    body { font-family: sans-serif; margin: 2rem; }
    .card { border: 1px solid #ccc; padding: 1rem; border-radius: 4px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>디자인 산출물 (고장)</h1>
    <p>이 파일은 의도적으로 콘솔 에러를 발생시킵니다.</p>
  </div>
  <script>
    // 의도적 에러: undefined function 호출
    // console-check.mjs 가 pageerror 로 잡고 exit 2 반환
    undefinedFunction();
  </script>
</body>
</html>
HTML_EOF

# --- (2) broken-layout HTML ---
# 정적 검출 가능한 레이아웃 깨짐:
#   - .overflow-child 가 .overflow-parent 를 벗어남 (width: 200%)
#   - .overlap-a / .overlap-b 가 정확히 같은 position 에 겹침
#   - .zero-box 가 height:0px (0px-height container)
cat > broken_layout.html <<'HTML_EOF'
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>Broken Layout Test</title>
  <style>
    body { font-family: sans-serif; margin: 2rem; }

    /* --- overflow breakage --- */
    .overflow-parent {
      width: 300px;
      overflow: hidden;
      border: 2px solid red;
      height: 80px;
    }
    .overflow-child {
      width: 200%;   /* 의도적 overflow */
      background: #f99;
      padding: 1rem;
    }

    /* --- overlap breakage: 동일 좌표에 겹침 --- */
    .overlap-container {
      position: relative;
      width: 300px;
      height: 100px;
      border: 2px solid blue;
      margin-top: 1rem;
    }
    .overlap-a {
      position: absolute;
      top: 10px;
      left: 10px;
      width: 80px;
      height: 80px;
      background: rgba(255,0,0,0.5);
    }
    .overlap-b {
      position: absolute;
      top: 10px;   /* 의도적 overlap: overlap-a 와 정확히 동일 좌표 */
      left: 10px;
      width: 80px;
      height: 80px;
      background: rgba(0,0,255,0.5);
    }

    /* --- zero-height breakage --- */
    .zero-box {
      width: 300px;
      height: 0px;   /* 의도적 0px height */
      background: #ff0;
      border: 2px solid orange;
      margin-top: 1rem;
    }
  </style>
</head>
<body>
  <h1>레이아웃 깨짐 테스트</h1>

  <div class="overflow-parent">
    <div class="overflow-child">overflow 발생 (width: 200%)</div>
  </div>

  <div class="overlap-container">
    <div class="overlap-a">A (overlap)</div>
    <div class="overlap-b">B (overlap)</div>
  </div>

  <div class="zero-box">
    <!-- 0px height — 이 텍스트는 보이지 않음 -->
    zero-height container
  </div>
</body>
</html>
HTML_EOF

# --- design_state.yaml: repo 를 design-review-resolvable 로 설정 ---
mkdir -p .claude_reports/spec
cat > .claude_reports/spec/design_state.yaml <<'YAML_EOF'
phase: review
artifact: preview.html
design_files:
  - preview.html
  - broken_layout.html
phases:
  design_init: done
  scaffolding: done
  iteration: done
  review: in_progress
YAML_EOF

# pipeline_state.yaml (spec-backed 설정)
cat > .claude_reports/spec/pipeline_state.yaml <<'YAML_EOF'
mode: [app]
phases:
  spec: done
  dev: done
  design: in_progress
YAML_EOF

# --- _design_rules.md 최소 stub ---
cat > _design_rules.md <<'MD_EOF'
# Design Rules

## 원칙
1. 콘솔 에러 0 건 — pageerror · console.error · request failed 모두 차단
2. 레이아웃 overflow 없음
3. 요소 겹침(overlap) 없음
4. 0px-height container 없음
MD_EOF

git add -A && git commit -q -m "fixture: broken design HTMLs (console error + layout breakage)"

# --- pre-state: 깨짐 마커 동적 캡처 (hardcode 금지) ---
# preview.html 의 undefined function 호출 줄
uf_line=$(grep -n "undefinedFunction" preview.html | head -1 | cut -d: -f1)
# broken_layout.html 의 height:0px 줄
zero_line=$(grep -n "height: 0px" broken_layout.html | head -1 | cut -d: -f1)
# overflow width:200% 줄
overflow_line=$(grep -n "width: 200%" broken_layout.html | head -1 | cut -d: -f1)
# overlap 줄 (overlap-b 의 top:10px — overlap-a 와 동일)
overlap_line=$(grep -n "overlap-b" broken_layout.html | head -1 | cut -d: -f1)

echo "preview_undefined_fn_line=$uf_line"           > "$WORK/.pre/refs"
echo "broken_layout_zero_height_line=$zero_line"   >> "$WORK/.pre/refs"
echo "broken_layout_overflow_line=$overflow_line"  >> "$WORK/.pre/refs"
echo "broken_layout_overlap_line=$overlap_line"    >> "$WORK/.pre/refs"

# enc_cwd: run.sh cleanup 보조 (g7 패턴)
enc=$(printf '%s' "$PWD" | sed 's#[/._]#-#g')
echo "$enc" > "$WORK/.pre/enc_cwd"
