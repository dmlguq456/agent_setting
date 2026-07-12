# token-optimizer (alexgreensh) — skill/memory/config audit skill

**Type**: catalog
**URL**: https://skillsllm.com/skill/token-optimizer
**분류축1 (메커니즘)**: budget-directive-self-monitoring (audit 기반) + input-context-reduction
**절감 claim**: "measured savings", cache-safe (구체 수치는 카탈로그에 미기재)
**실측/검증**: SkillsLLM security scan 통과. 절감 수치 독립 검증 없음. 1,610 star/128 fork.
**신호->레버 매핑**: **명시적** — 신호=bloated config·unused skill·stale memory·compaction loss·
model misrouting·behavioral waste, 레버=audit 후 정리 + real-time quality scoring + trend 분석
(`/token-optimizer` audit, `/token-coach` trend). SQLite session DB.
**하네스 시사점**: 압축이 아니라 **낭비 진단·자기 감사(self-monitoring)** 접근 — 하네스가 자기 skill
catalog·memory·라우팅의 token 낭비를 주기적으로 audit 하는 축에 직접 대응(우리 audit skill 과 유사).
axis 4 에서 "token-budget 축 = 압축 레버 + 자기감사 레버" 임을 보여주는 사례.

## Summary
caveman/ponytail(생성 시 압축)과 다른 계층: **세션의 token 낭비를 사후 진단**하는 audit skill. bloated
config, unused skill, stale memory, compaction loss, model misrouting, behavioral waste 를 스캔.
Claude Code/OpenCode/OpenClaw/Codex/Hermes/Copilot(beta) 지원. `/token-optimizer`(audit),
`/token-coach`(trend). SQLite session DB + audit trail + real-time quality scoring.

이 접근은 self-regulation 을 "생성 억제"가 아니라 "**낭비 감사 후 구조 정리**"로 본다 — 우리 하네스의
audit skill·mem consolidation·model routing 규율과 개념적으로 겹침. axis 4 에서 token-budget 축이
런타임 압축뿐 아니라 설정·기억·라우팅의 정적 최적화도 포함해야 함을 시사.

**Figures**: (none extracted)
