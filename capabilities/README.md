# Portable Capability Catalog

This directory is the runtime-neutral capability layer. It describes what each
capability means, what artifacts it owns, and which portable roles it may use.
It is not a Claude Skill registry.

Claude Code currently realizes these capabilities through `skills/*/SKILL.md`
projected as `~/.claude/skills/*/SKILL.md`. Codex and future adapters should
start from this catalog, then consult adapter-native instructions only for
runtime mechanics.

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
- concrete model names such as `sonnet` or `opus`;
- CLI-specific external reviewer commands.

## Catalog

| Capability | Group | Modes | Portable meaning | Current Claude realization |
|---|---|---|---|---|
| `analyze-project` | pre | code, paper, doc | 사전 분석. 코드·논문·문서 primary 자료를 구조화해 다운스트림 입력으로 만든다. | `skills/analyze-project/SKILL.md` |
| `analyze-user` | pre | init, update | cross-project 사용자 성향 프로필 작성·갱신. 코드·작성·분석 패턴을 추출한다. | `skills/analyze-user/SKILL.md` |
| `audit` | ops | - | 산출물·파이프 사후 점검. drift·일관성·누락을 읽기 중심으로 진단한다. | `skills/audit/SKILL.md` |
| `autopilot-apply` | entry | - | cheatsheet 초안을 실제 source artifact에 적용하고 검증한다. | `skills/autopilot-apply/SKILL.md` |
| `autopilot-code` | entry | dev, debug, audit | 코드 작업 entry. spec 컨텍스트를 감지하고 plan→execute→test→report 흐름을 닫는다. | `skills/autopilot-code/SKILL.md` |
| `autopilot-design` | entry | - | 시각 산출물 디자인 파이프. refs→tokens→components→review→handoff를 조율한다. | `skills/autopilot-design/SKILL.md` |
| `autopilot-draft` | entry | paper, presentation, doc | 문서 초안 파이프. 전략·초안·검증·편집을 거쳐 적용용 문서 artifact를 만든다. | `skills/autopilot-draft/SKILL.md` |
| `autopilot-lab` | entry | setup, eval | 빠른 실험 prototype. 학습 세팅과 ckpt 평가·분석 앞뒤를 돕는다. | `skills/autopilot-lab/SKILL.md` |
| `autopilot-note` | entry | - | 산출물 라우팅/노트화. digest와 triage 제안을 만든다. | `skills/autopilot-note/SKILL.md` |
| `autopilot-refine` | entry | - | 기존 문서·연구 산출물의 정정·갱신. 버전 snapshot과 변경 이력을 보존한다. | `skills/autopilot-refine/SKILL.md` |
| `autopilot-research` | entry | academic, technology, market | 공통 사전조사. 논문·기술·시장 survey 후 downstream capability로 분기한다. | `skills/autopilot-research/SKILL.md` |
| `autopilot-ship` | entry | - | 앱 배포·출시 준비. build/deploy setup과 ship checklist를 만든다. | `skills/autopilot-ship/SKILL.md` |
| `autopilot-spec` | entry | app, library, api, cli, research, update | 요구사항·청사진 작성·갱신. `prd.md`를 spec 변경의 단일 경로로 유지한다. | `skills/autopilot-spec/SKILL.md` |
| `code-execute` | sub | - | plan 단계별 구현 실행. 개발 role에 작업을 위임하고 execution log를 남긴다. | `skills/code-execute/SKILL.md` |
| `code-plan` | sub | - | 코드 분석 후 상세 구현 plan 작성. planning role과 QA loop를 사용한다. | `skills/code-plan/SKILL.md` |
| `code-refine` | sub | - | 사용자 메모·QA 피드백을 반영해 기존 plan을 정정한다. | `skills/code-refine/SKILL.md` |
| `code-report` | sub | - | 코드 작업 사이클 결과를 사용자-facing 보고서로 조립한다. | `skills/code-report/SKILL.md` |
| `code-test` | sub | - | 구현 결과를 단계별로 검증하고 evidence를 기록한다. | `skills/code-test/SKILL.md` |
| `design-components` | sub | - | UI component/mockup 구현과 preview artifact를 만든다. | `skills/design-components/SKILL.md` |
| `design-handoff` | sub | - | 디자인 결과를 개발 handoff용 자산·스펙으로 정리한다. | `skills/design-handoff/SKILL.md` |
| `design-init` | sub | - | 디자인 환경과 state를 bootstrap한다. | `skills/design-init/SKILL.md` |
| `design-refs` | sub | - | 외부·사용자 reference 시각 자료를 수집하고 brief를 만든다. | `skills/design-refs/SKILL.md` |
| `design-review` | sub | - | 디자인 결과물을 품질·토큰 계약·breakage 관점으로 점검한다. | `skills/design-review/SKILL.md` |
| `design-tokens` | sub | - | 색·타이포·간격 등 디자인 토큰을 정의한다. | `skills/design-tokens/SKILL.md` |
| `draft-refine` | sub | - | 초안 정련·다듬기. memo/review feedback을 문서 전략이나 draft에 반영한다. | `skills/draft-refine/SKILL.md` |
| `draft-strategy` | sub | rebuttal, paper, review, report, proposal, presentation | 문서 전략 초안 작성. 자료 기반으로 writing plan을 만든다. | `skills/draft-strategy/SKILL.md` |
| `post-it` | ops | - | 프로젝트·cross-project 기록과 handoff를 working memory로 남긴다. | `skills/post-it/SKILL.md` |
| `sync-skills` | ops | - | 정의 변경을 읽어 README/manifest/cross-doc invariant drift를 점검·동기화한다. | `skills/sync-skills/SKILL.md` |

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
