---
# GENERATED METADATA — edit harness-manifest.json, then run tools/generate.py.
name: post-it
description: "Use when invoking the portable post-it capability. Store project/cross-project notes and handoffs in working memory."
argument-hint: "[show] | add <category> <text> | resolve <hint> | decide <text> | handoff [--no-confirm] | sweep [--no-confirm] | promote [<hint>] [--scope project|user [<aspect>]]"
metadata:
  group: ops
  fam: ops
  modes: []
  blurb: "Store project/cross-project notes and handoffs in working memory."
---

## 목적

사용자가 **직접 통제하는** 포스트잇 메모리. `<agent-home>/projects/*/memory/` 의 자동 메모리 시스템과는 별개로, 주 변경 경로는 사용자의 명시적 `/post-it` 호출이나, [references/nudge-and-boundaries.md](references/nudge-and-boundaries.md) 의 proactive-nudge 계약에 따라 model-invoked auto-record 도 함께 일어난다. 세션 종료 시 conversation 이 사라지는 휘발성을 메우는 목적 (compact 는 일시적 보존이라 불충분).

**핵심 비유 — 임시 포스트잇.** post-it 은 _영구 기록이 아니다_. 영구 진실은 산출물(`plans/`·`documents/`·`spec/`·code·git) 과 구조화 프로필(DB `type=profile` 레코드) 에 있다. post-it 은 그 사이를 잇는 _휘발성 작업면_ — 지금 떠올려야 할 것만 짧게 붙여두고, 산출물로 졸업하면 떼어낸다.

> **불변식 — 사용자는 post-it 을 들여다보지 않는다 (fire-and-forget).** post-it 은 _에이전트의 세션-간 연속성 작업면_ 이지 사용자 읽기용 문서가 아니다. 따라서 (1) lean 유지·졸업 prune 는 **에이전트 책임** — 사용자에게 레코드를 줄 단위로 검토시키지 않는다. (2) 자동 nudge 자리의 sweep 은 _확실한_ 졸업·stale 만 **자동 제거 + 한 줄 보고** (애매하면 keep). (3) 사용자에겐 _짧은 요약_ 만 주고, 액션 _저장 여부_ 만 confirm 받는다. 줄 단위 preview 는 사용자가 `/post-it sweep` 를 직접 칠 때만.

> **통합 기억 store 연동 (2026-06-15, v5).** post-it 은 _프로젝트 단위 working tier_ 로서 통합 store([tools/memory](../../tools/memory/README.md)) DB(`memory.db`, SQLite WAL) 에 저장된다 — `mem note`/`mem add` 로 working 레코드 write, `mem recall` 로 검색, working lifecycle(만료·졸업)은 `mem lifecycle` 이 관할. 세션 주입은 `python3 <agent-home>/tools/memory/mem.py inject --hook` 가 DB working tier 에서 수행. sweep 의 시간 lifecycle 은 `mem lifecycle` 과 동류(시간 기반 working lifecycle)이되 임계값·동작이 다름 — post-it 은 ≥30d stale·≥90d archive 를 _플래깅_(사람-점검), store 는 `WORKING_TTL_DAYS`(현재 21d)로 _자동 만료_.

## Quick Contract (라우터 개요)

본 SKILL.md 는 라우터 — 위 목적·불변식과 sub-action 분기만 담고, lifecycle·scope 정의와 sub-action 상세 절차는 실행 시 아래 reference 를 Read 한다 (내용은 reference 로 이동만 — 전부 그대로 유효).

- **Scope 2개**: `project` (default — DB working tier, cwd-scoped) / `user <aspect>` (profile 레코드 `## 사용자 수동 메모` 블록). scope 표·aspect 선택·analyze-user 계약 → `references/lifecycle-and-scope.md`.
- **Lifecycle 불변**: 모든 엔트리는 졸업(graduated)하거나 만료(stale)한다 — 영구 누적 금지. 분류 표·5 카테고리 type taxonomy·aging → `references/lifecycle-and-scope.md`.
- **Sub-action 7종**: show(무인자) / add / resolve / decide / sweep / promote / handoff — 절차 전문과 Confirm 정책 표 → `references/sub-actions.md`.
- **레코드 write 자리**: Writing Style(1 bullet = 1줄, dense) 준수 → `references/nudge-and-boundaries.md`.

## Reference Index

| 파일 | 언제 로드 (의무) | 내용 |
|---|---|---|
| `references/lifecycle-and-scope.md` | 모든 호출 (필수) | Lifecycle(graduated/stale/live), Scope — project vs user(scope 표·aspect 표·analyze-user 책임 분리·두 writer 계약·artifact-guard 주의), DB working tier & 자동 로드(mem 명령 형태), 5 카테고리 type taxonomy(aging stamp·시간 tier) |
| `references/sub-actions.md` | sub-action 실행 시 (add/resolve/decide/sweep/promote/handoff) | Sub-Actions 전문(show/add/resolve/decide/sweep — project·user scope 절차 / promote — read-modify-write·두 writer 계약 / handoff — sweep 자동 포함), Confirm 정책 요약 표 |
| `references/nudge-and-boundaries.md` | 자동 기록 자리·auto-memory 경계·write 전 Writing Style 판단 시 | Proactive nudge(자동 기록 트리거·자동 기록 모델), What this skill is NOT, Auto-memory와의 경계, Writing Style(간결성 원칙) |

## Language Rule
- User conversation follows the user's communication language.
- Working-record bodies preserve the language used by the user; mixed-language content is valid.

## Task

Argument `$ARG` 파싱:
- 비어 있으면 `show` (DB working 레코드 preview — 없으면 `/post-it add` 안내).
- `add <category> <text>` → working 레코드 `mem note` write.
- `resolve <hint>` → thread 레코드 fuzzy advisory 처리.
- `decide <text>` → decision 레코드 write.
- `sweep [--no-confirm] [--scope ...]` → 산출물·레코드 대조 후 graduated·stale flag/만료.
- `promote [<hint>] [--scope user [<aspect>]]` → user 메모를 profile 레코드 구조화 절로 졸업 (read-modify-write).
- `handoff [--no-confirm]` → sweep 제안 → 세션 요약 → hint 레코드 write.
- `--scope user [<aspect>]` 동반 시 `mem profile <stem>` / `mem add ... --source user-profile:<stem>` 대상 (profile 레코드 직접 write, ceremony 불필요).
- 그 외 → 사용법 안내.
