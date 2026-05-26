# notes

> 본 README 는 `SKILL.md` 의 GitHub 표시용 mirror. 권위 있는 동작 명세는 `SKILL.md`.

## 개요

사용자가 **직접 통제하는** per-project 메모리. `~/.claude/projects/*/memory/`의 자동 메모리 시스템과는 별개 layer로, 사용자가 명시적으로 `/notes` 명령을 호출할 때만 변경된다. 세션 종료 시 conversation이 사라지는 휘발성을 메우는 목적 (compact는 일시적이라 불충분).

## 파일 위치 & 자동 로드

- **위치**: 현재 working directory의 `.claude_reports/NOTES.md` (단일 파일)
- **자동 로드**: 글로벌 `~/.claude/CLAUDE.md`의 도메인 트리거 표에 의해 메인 Claude가 새 세션 시작 시 Read. 파일 없으면 무시.
- **갱신**: 항상 `/notes` 명령으로만. Claude가 자동으로 쓰지 않는다.

## 파일 형식 (5 카테고리)

```markdown
# Project Notes

- **Project**: {프로젝트 이름}
- **Last Updated**: YYYY-MM-DD

## Conventions
- (영속 규약 — 예: 노션 정리 위치, 커밋 메시지 언어)

## External Resources
- (외부 링크/경로 — 예: 데이터셋, Overleaf)

## Open Threads
- [in-progress] (현재 진행 중인 작업)
- [blocked] (사용자가 직접 수동 편집)

## Decisions
- YYYY-MM-DD: (그 시점의 의사결정과 사유)

## Next Session Hints
(가장 마지막 `/notes handoff` 결과로 **덮어쓰여짐** — 누적 X)
- (다음 세션에 알아야 할 현재 진행 상황·다음 할 일·주의사항)
```

## Sub-Actions

| 명령 | 동작 | Confirm |
|---|---|---|
| `/notes` (또는 `show`) | 파일 표시 (없으면 init 안내) | — |
| `/notes init` | `.claude_reports/NOTES.md` 없으면 템플릿 생성. Project = cwd basename, Last Updated = today | — |
| `/notes add <category> <text>` | 해당 섹션 bullet 추가. category ∈ {convention, resource, thread, decision} (alias: conv/res/th/dec). thread는 `[in-progress]` prefix 자동, decision은 `YYYY-MM-DD:` prefix 자동 | **즉시** (`--confirm` 가능) |
| `/notes resolve <hint>` | Open Threads에서 fuzzy 매칭으로 thread 찾아 제거 | **preview→confirm** (`--no-confirm` 가능) |
| `/notes decide <text>` | Decisions에 `- YYYY-MM-DD: <text>` 추가 | **즉시** (`--confirm` 가능) |
| `/notes handoff [--no-confirm]` | 현재 conversation review → 5-10 bullet 요약 → Next Session Hints **전체 교체** | **preview→confirm** (`--no-confirm` 가능) |

## Confirm 정책 원칙

사용자가 텍스트를 **직접 적은 경우**는 즉시 적용 (add / decide), Claude가 **내용을 생성하거나 fuzzy 매칭**하는 경우는 검토 후 적용 (resolve / handoff).

## 간결성 원칙 (NOTES.md 작성 시 강제)

NOTES.md는 세션 시작 시 항상 읽히는 컨텍스트 파일 — **짧고 dense하게** 유지.

- 한 bullet = 한 줄. 줄바꿈 금지 (최대 2줄).
- 명사구·사실 문장 위주. 형용사·부사·존댓말·이유 설명 최소화.
- 핵심 어휘만. 한·영 혼용 OK, 약어·기호 (`→`, `&`, `vs`) 적극 사용.
- 같은 정보는 한 카테고리에만 (중복 X).
- `handoff` 요약도 같은 원칙 — 5-10 bullet, 각 1줄.

## What this skill is NOT

- **자동 메모리 시스템 대체 X** — `~/.claude/projects/*/memory/`는 그대로 작동. 본 skill은 추가 layer.
- **코드 변경 기록 X** — `autopilot-code` plans/dev_logs.
- **문서 변경 기록 X** — `autopilot-draft` documents/.
- **세션 활동 로그 X** — pipeline_summary.md 등.

NOTES.md는 "매 세션 시작 시 자동으로 떠올리고 싶은 한정된 정보"만.

## Auto-memory와의 경계

| 위치 | 범위 | 갱신 |
|---|---|---|
| `~/.claude/projects/*/memory/` | account-wide cross-project | Claude 자동 학습·기록 |
| `.claude_reports/NOTES.md` | per-project (cwd 한정) | 사용자가 `/notes`로만 |

구분 기준:
- 이 레포에만 적용되는 사실 (노션 위치, 데이터셋 경로, 진행 작업) → NOTES.md
- 사용자 자신·일반 작업 선호 (Korean output, 코드 스타일) → auto memory

겹치는 경우 NOTES.md가 더 정확한 local context를 가지므로 우선.
