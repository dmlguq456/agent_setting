# Portable Capability Catalog

This directory is the runtime-neutral capability layer. It describes what each
capability means, what artifacts it owns, and which portable roles it may use.
It is not a Claude Skill registry. Per-capability contracts live in
`capabilities/<capability>.md`; this README is the catalog index.

Claude Code realizes these capabilities through adapter-owned concrete Skill
files under `adapters/claude/skills/*/SKILL.md`. Historical
`skills/*/SKILL.md` files remain compatibility references while portable
contracts move into this directory.
Codex and future adapters should start from this catalog, then consult
adapter-native instructions only for runtime mechanics.

## Capability Contract

Each capability has:

- an identifier;
- a capability group;
- supported modes;
- invocation semantics in runtime-neutral terms;
- artifact ownership;
- required role families;
- adapter realization notes.

Runtime-specific details stay out of portable capability meaning:

- Claude Skill frontmatter and folder layout;
- slash command names;
- Claude hook names, `ScheduleWakeup`, statusline, or MCP registration details;
- concrete model names;
- CLI-specific external reviewer commands.

## Catalog

| Capability | Group | Modes | Portable spec | Portable meaning | Current Claude realization |
|---|---|---|---|---|---|
| `analyze-project` | pre | code, paper, doc | [`analyze-project.md`](analyze-project.md) | 사전 분석. 코드·논문·문서 primary 자료를 구조화해 다운스트림 입력으로 만든다. | `adapters/claude/skills/analyze-project/SKILL.md` |
| `analyze-user` | pre | init, update | [`analyze-user.md`](analyze-user.md) | cross-project 사용자 성향 프로필 작성·갱신. 코드·작성·분석 패턴을 추출한다. | `adapters/claude/skills/analyze-user/SKILL.md` |
| `audit` | ops | - | [`audit.md`](audit.md) | 산출물·파이프 사후 점검. drift·일관성·누락을 읽기 중심으로 진단한다. | `adapters/claude/skills/audit/SKILL.md` |
| `autopilot-apply` | entry | - | [`autopilot-apply.md`](autopilot-apply.md) | cheatsheet 초안을 실제 source artifact에 적용하고 검증한다. | `adapters/claude/skills/autopilot-apply/SKILL.md` |
| `autopilot-code` | entry | dev, debug, audit | [`autopilot-code.md`](autopilot-code.md) | 코드 작업 entry. spec 컨텍스트를 감지하고 plan→execute→test→report 흐름을 닫는다. | `adapters/claude/skills/autopilot-code/SKILL.md` |
| `autopilot-design` | entry | - | [`autopilot-design.md`](autopilot-design.md) | 시각 산출물 디자인 파이프. refs→tokens→components→review→handoff를 조율한다. | `adapters/claude/skills/autopilot-design/SKILL.md` |
| `autopilot-draft` | entry | paper, presentation, doc | [`autopilot-draft.md`](autopilot-draft.md) | 문서 초안 파이프. 전략·초안·검증·편집을 거쳐 적용용 문서 artifact를 만든다. | `adapters/claude/skills/autopilot-draft/SKILL.md` |
| `autopilot-lab` | entry | setup, eval | [`autopilot-lab.md`](autopilot-lab.md) | 빠른 실험 prototype. 학습 세팅과 ckpt 평가·분석 앞뒤를 돕는다. | `adapters/claude/skills/autopilot-lab/SKILL.md` |
| `autopilot-note` | entry | - | [`autopilot-note.md`](autopilot-note.md) | 산출물 라우팅/노트화. digest와 triage 제안을 만든다. | `adapters/claude/skills/autopilot-note/SKILL.md` |
| `autopilot-refine` | entry | - | [`autopilot-refine.md`](autopilot-refine.md) | 기존 문서·연구 산출물의 정정·갱신. 버전 snapshot과 변경 이력을 보존한다. | `adapters/claude/skills/autopilot-refine/SKILL.md` |
| `autopilot-research` | entry | academic, technology, market | [`autopilot-research.md`](autopilot-research.md) | 공통 사전조사. 논문·기술·시장 survey 후 downstream capability로 분기한다. | `adapters/claude/skills/autopilot-research/SKILL.md` |
| `autopilot-ship` | entry | - | [`autopilot-ship.md`](autopilot-ship.md) | 앱 배포·출시 준비. build/deploy setup과 ship checklist를 만든다. | `adapters/claude/skills/autopilot-ship/SKILL.md` |
| `autopilot-spec` | entry | app, library, api, cli, research, update | [`autopilot-spec.md`](autopilot-spec.md) | 요구사항·청사진 작성·갱신. `prd.md`를 spec 변경의 단일 경로로 유지한다. | `adapters/claude/skills/autopilot-spec/SKILL.md` |
| `code-execute` | sub | - | [`code-execute.md`](code-execute.md) | plan 단계별 구현 실행. 개발 role에 작업을 위임하고 execution log를 남긴다. | `adapters/claude/skills/code-execute/SKILL.md` |
| `code-plan` | sub | - | [`code-plan.md`](code-plan.md) | 코드 분석 후 상세 구현 plan 작성. planning role과 QA loop를 사용한다. | `adapters/claude/skills/code-plan/SKILL.md` |
| `code-refine` | sub | - | [`code-refine.md`](code-refine.md) | 사용자 메모·QA 피드백을 반영해 기존 plan을 정정한다. | `adapters/claude/skills/code-refine/SKILL.md` |
| `code-report` | sub | - | [`code-report.md`](code-report.md) | 코드 작업 사이클 결과를 사용자-facing 보고서로 조립한다. | `adapters/claude/skills/code-report/SKILL.md` |
| `code-test` | sub | - | [`code-test.md`](code-test.md) | 구현 결과를 단계별로 검증하고 evidence를 기록한다. | `adapters/claude/skills/code-test/SKILL.md` |
| `design-components` | sub | - | [`design-components.md`](design-components.md) | UI component/mockup 구현과 preview artifact를 만든다. | `adapters/claude/skills/design-components/SKILL.md` |
| `design-handoff` | sub | - | [`design-handoff.md`](design-handoff.md) | 디자인 결과를 개발 handoff용 자산·스펙으로 정리한다. | `adapters/claude/skills/design-handoff/SKILL.md` |
| `design-init` | sub | - | [`design-init.md`](design-init.md) | 디자인 환경과 state를 bootstrap한다. | `adapters/claude/skills/design-init/SKILL.md` |
| `design-refs` | sub | - | [`design-refs.md`](design-refs.md) | 외부·사용자 reference 시각 자료를 수집하고 brief를 만든다. | `adapters/claude/skills/design-refs/SKILL.md` |
| `design-review` | sub | - | [`design-review.md`](design-review.md) | 디자인 결과물을 품질·토큰 계약·breakage 관점으로 점검한다. | `adapters/claude/skills/design-review/SKILL.md` |
| `design-tokens` | sub | - | [`design-tokens.md`](design-tokens.md) | 색·타이포·간격 등 디자인 토큰을 정의한다. | `adapters/claude/skills/design-tokens/SKILL.md` |
| `draft-refine` | sub | - | [`draft-refine.md`](draft-refine.md) | 초안 정련·다듬기. memo/review feedback을 문서 전략이나 draft에 반영한다. | `adapters/claude/skills/draft-refine/SKILL.md` |
| `draft-strategy` | sub | rebuttal, paper, review, report, proposal, presentation | [`draft-strategy.md`](draft-strategy.md) | 문서 전략 초안 작성. 자료 기반으로 writing plan을 만든다. | `adapters/claude/skills/draft-strategy/SKILL.md` |
| `post-it` | ops | - | [`post-it.md`](post-it.md) | 프로젝트·cross-project 기록과 handoff를 working memory로 남긴다. | `adapters/claude/skills/post-it/SKILL.md` |
| `sync-skills` | ops | - | [`sync-skills.md`](sync-skills.md) | 정의 변경을 읽어 README/manifest/cross-doc invariant drift를 점검·동기화한다. | `adapters/claude/skills/sync-skills/SKILL.md` |

## Adapter Requirements

An adapter that supports capabilities must document:

- how a user invokes the capability;
- whether confirmation is automatic, required, or unsupported;
- how the adapter discovers artifact roots;
- how it loads the portable roles in `roles/`;
- which deterministic guards it can enforce;
- where durable output is written;
- how unsupported sub-capabilities are reported.

If an adapter cannot support a capability, it must say so explicitly and offer a
fallback path instead of silently treating a Claude Skill file as native.
