# Round 1 — Fact-Check Review (verbatim card 대조)

> fast fact-checker mode. 표만. narrative/coverage/roadmap 품질은 대상 아님 (quality reviewer 소관).
> Single source of truth: `cards/*.md` + `analysis_summary.md`. GSD 우선, 그다음 spec-kit/BMAD/claude-code-official.

| Report | Section | Claim | Source card (file:line) | Match | Severity |
|---|---|---|---|---|---|
| 00_briefing | Key Findings | GSD 원본 `gsd-build/get-shit-done` archived → `open-gsd/gsd-core` (npm `@opengsd/gsd-core`) 이전 | gsd.md:4 | ✅ | 🟢 |
| 00_briefing | Key Findings | GSD hash-manifest+`--reapply` 로 3-way merge 양방향 divergence 유일 실구현 | gsd.md:37-38,101 | ✅ | 🟢 |
| 00_briefing | Key Findings | Claude 공식 규격 "3-way merge 도구는 문서에 없다" 자인 | claude-code-official-plugins.md:132 | ✅ | 🟢 |
| 00_briefing | Key Findings | claude-flow 자체 repo 367개 중복 SKILL.md drift (#1834) | claude-flow.md:28 | 🟡 | 🟡 |
| 00_briefing | Top-3 Insights | GSD byte-budget `workflow-size-budget.test.cjs` | gsd.md:57 | ✅ | 🟢 |
| 01_landscape | §4 Adoption | GSD 버전 넘버링 불일치 1.7.0-rc.4 vs changelog v1.4x | gsd.md:107 | ✅ | 🟢 |
| 01_landscape | §4 Adoption | BMAD 43K+ stars, v6.10.0 (2026-07-03), 20+ tool | bmad-method.md:3-4,15 | ✅ | 🟢 |
| 01_landscape | §4 Adoption | spec-kit `github/spec-kit`, 30+ agent | spec-kit.md:1,9 | ✅ | 🟢 |
| 01_landscape | §4 Adoption | Superpowers obra/Jesse Vincent, core/lab/community 3-repo 분리 | superpowers.md:1,3,20 | 🟡 | 🟡 |
| 01_landscape | §4 Adoption | SuperClaude v4.3.0 stable, v5.0 plugin 완성형 개발 중(ETA 미정) | superclaude.md:4,27,82 | ✅ | 🟢 |
| 01_landscape | §4 Adoption | Agent OS v3.0, install email-gated (verbatim 미확인) | agent-os.md:3,18 | ✅ | 🟢 |
| 01_landscape | §2 매트릭스 | GSD 16 runtime capability manifest | gsd.md:20,86 | ✅ | 🟢 |
| 01_landscape | §3 Lineage | claude-flow v2(swarm+SQLite) → ruflo v3(monorepo @claude-flow/*) | claude-flow.md:3,8 | ✅ | 🟢 |
| 01_landscape | §3 Lineage | BMAD v4 .bmad-core → v6 skills 아키텍처 | bmad-method.md:67 | ✅ | 🟢 |
| 02_standards | §1 schema | `.claude-plugin/` 안엔 `plugin.json` 만, 나머지는 plugin root | claude-code-official-plugins.md:9 | ✅ | 🟢 |
| 02_standards | §1 schema | skills desc+when_to_use 1,536자 truncate | claude-code-official-plugins.md:91 | ✅ | 🟢 |
| 02_standards | §1 schema | marketplace `renames`(v2.1.193+), source github/url/git-subdir/npm | claude-code-official-plugins.md:45-46,48 | ✅ | 🟢 |
| 02_standards | §1 schema | hooks 31 event(PreToolUse block, SessionStart, PreCompact) | claude-code-official-plugins.md:78 | ✅ | 🟢 |
| 02_standards | §2 AGENTS.md | 2025-08 OpenAI 주도 spec, 2025-12 LF 기부, 60,000+ repo | multi-harness-projection.md:36 | ✅ | 🟢 |
| 03_vendor | §1 매트릭스 | GSD npm `@opengsd/gsd-core` 또는 Claude plugin; `/gsd-update` | gsd.md:32-34 | ✅ | 🟢 |
| 03_vendor | §1 매트릭스 | spec-kit overrides>presets>extensions>core 계층 resolution | spec-kit.md:22,63 | ✅ | 🟢 |
| 03_vendor | §1 매트릭스 | BMAD `_bmad/custom/*.toml` 3-layer override(default/team/user) | bmad-method.md:29,55,77 | ✅ | 🟢 |
| 03_vendor | §1 매트릭스 | claude-flow 367개 중복 SKILL.md drift(#1834) | claude-flow.md:28 | 🟡 | 🟡 |
| 03_vendor | §2 Checklist | BMAD `bmad-loop`만 hook | bmad-method.md:46 | ✅ | 🟢 |
| 04_deep_dive | §a | GSD gsd-local-patches/ 백업 → --reapply 재적용 | gsd.md:37-38 | ✅ | 🟢 |
| 04_deep_dive | §b | GSD byte-budget XL 90KB, Codex 32,768 truncation 정렬 | gsd.md:57 | ✅ | 🟢 |
| 04_deep_dive | §b | GSD 2-stage routing 67→6 entries; router desc ≤60자 | gsd.md:47,59 | ✅ | 🟢 |
| 04_deep_dive | §b | Superpowers description ≤1024자, getting-started ≤150 words | superpowers.md:25-26 | ✅ | 🟢 |
| 04_deep_dive | §c | GSD `capabilities/<feature>/capability.json` gates[] plan:pre/execute:wave:post, verify.schema-drift | gsd.md:69 | ✅ | 🟢 |
| 04_deep_dive | §d | rulesync OpenCode/Kilo JS plugin emit `.opencode/plugins/rulesync-hooks.js` | multi-harness-projection.md:30 | ✅ | 🟢 |
| 04_deep_dive | §d | ruler Copilot tool 어휘 silent drop; subagent 없으면 skip+warning | multi-harness-projection.md:16-17 | ✅ | 🟢 |
| 04_deep_dive | §d | dispatch maxDepth claude=5, codex=1 | gsd.md:91 | ✅ | 🟢 |
| 05_deployment | §1 | GSD 2경로 병존 npm `@opengsd/gsd-core` 또는 Claude plugin | gsd.md:32-33 | ✅ | 🟢 |
| 05_deployment | §1 | claude-flow 3경로 npm/CLI + MCP + plugin(35개) | claude-flow.md:24-27 | ✅ | 🟢 |
| 06_impl | 후보1 | GSD hash-manifest 후보 근거 `gsd.md §2`, bin/install.js line 단위 미검증 | gsd.md:37,105-107 | ✅ | 🟢 |
| 07_resources | Tier1 | GSD `gsd-core/bin/lib/state-transition.cjs` FIELD_CLASSIFICATION, ADR-1769 | gsd.md:80 | ✅ | 🟢 |
| 07_resources | Tier1 | spec-kit `INTEGRATION_REGISTRY`/`_register_builtins()`, check-prerequisites.sh | spec-kit.md:11,33 | ✅ | 🟢 |
| 07_resources | 설치명령 | BMAD `npx bmad-method install` | bmad-method.md:26 | ✅ | 🟢 |
| 07_resources | 설치명령 | ruflo `npx ruflo@latest init` / `claude mcp add ruflo` | claude-flow.md:25-26 | ✅ | 🟢 |

## 🟡 노트 (verbatim nuance, 조작 아님)

- **367 SKILL.md** (00·03·05 반복): 카드 verbatim = "repo has 367 SKILL.md files (5x duplicates of common skills)". 즉 367은 SKILL.md **총 개수**(그중 흔한 skill 이 5배 중복)이지 "367개가 전부 중복본"은 아니다. 리포트의 "367개 중복 SKILL.md"는 경미한 과장 — "367개 SKILL.md(5x 중복 포함)"가 정확. 세 리포트 동일 표현이라 일괄 조정 권장. (conflict 아님, no-match 아님 — 카드 값 존재, 해석만 미세.)
- **Superpowers "core/lab/community 3-repo"** (01): 카드 repo 는 `superpowers`/`superpowers-skills`(Community-editable)/`superpowers-lab`/`superpowers-marketplace` 4개. "core/lab/community 3-repo"는 재명명 요약 — skills=community, lab=experimental 매핑은 성립하나 marketplace 누락·명칭 불일치. 경미.

## 종합

- 검사한 30+ material claim 전부 매칭 카드 존재 (**no-match/fabrication 0건, conflict 0건**).
- GSD·spec-kit·BMAD·claude-code-official 핵심 수치·메커니즘·파일명·패키지명 전부 카드 verbatim 소급 확인.
- 🟡 2건은 값 자체는 카드에 있으나 리포트의 해석 표현이 미세하게 느슨 — 재현/드리프트 누적 방지용 wording 조정 권장, 채택 근거로는 무해.
- 카드가 unverified 로 표시한 항목(GSD installer file-ops line 단위, Codex parity, Agent OS install verbatim, spec-kit on-demand 렌더)은 리포트가 모두 "미검증" caveat 을 그대로 전파 — 조작 위험 없음.
