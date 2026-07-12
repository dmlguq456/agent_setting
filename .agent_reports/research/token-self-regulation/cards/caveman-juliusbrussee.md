# JuliusBrussee/caveman — Claude Code skill, 65% output token 절감

**Type**: repo
**URL**: https://github.com/JuliusBrussee/caveman
**분류축1 (메커니즘)**: output-compression (주) + budget-directive-self-monitoring (Auto-Clarity 내장)
**절감 claim**: output 65% avg (range 22-87%, n=10). compressed CLAUDE.md 에 대해 input ~46%.
**실측/검증**: **저자 자기비판 있음** (`docs/HONEST-NUMBERS.md`) — output-only 수치이고 session-level
14-21%(output-heavy), terse workload 은 net-negative. skill 이 매 turn ~1-1.5k input tok 추가.
codepointer 독립 replay 는 3.7%(rtk+headroom+caveman 합산) 만 실절감. → claim vs 실측 gap 큼.
**신호->레버 매핑**: (Auto-Clarity) 위험/모호/multi-step 신호 → 출력 압축 강도 off(레버). intensity
lite/full/ultra/wenyan → 사용자·문맥이 신호, 압축 단계가 레버.
**하네스 시사점**: 출력 표면 압축은 token-budget 축의 한 레버일 뿐이고 세션 전체 효과는 작다. 오히려
이 repo 의 Auto-Clarity(위험→압축해제) 패턴이 self-regulation 축의 직접 참고 모델.

## Summary
Claude Code / Codex / Gemini 등 다중 런타임용 system-prompt skill. 알고리즘 압축이 아니라 "smart
caveman 처럼 짧게 써라"를 규율로 강제해 **출력 토큰만** 줄인다. commands: `/caveman [lite|full|ultra|
wenyan]`, `/caveman-commit`, `/caveman-review`, `/caveman-stats`, `/caveman-compress <file>`.

메커니즘 상세(실제 SKILL.md 열람): 관사·filler·pleasantry·hedging 제거, fragment 허용, 짧은 동의어.
주목할 정확성 — "invented abbreviation(cfg/impl/req/res/fn)은 tokenizer 가 full word 와 동일하게
쪼개 절감 0, 오히려 decode 비용" 이라며 **금지**. causal arrow(→)도 자체 토큰이라 금지. wenyan 모드는
문언문으로 80-90% char 감축.

가장 중요한 건 저자의 `HONEST-NUMBERS.md` — 마케팅 문서가 아니라 반증 문서다: input 압축 0%, skill
자체가 input 을 늘리며, terse Q&A·per-request 과금(Copilot)·일부 tool counter 에서 net-negative.
"Wanting the rock to work does not make the rock work." 이 자기비판이 본 연구 axis 2 의 1차 근거.

**Figures**: (none extracted)
