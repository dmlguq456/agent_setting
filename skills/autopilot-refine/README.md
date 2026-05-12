# autopilot-refine

> ⚠️ **Notion 페이지 없음**. 다음 `/sync-skills` 실행 시 자동으로 노션 자식 페이지 생성됩니다 (sync-skills SKILL.md §5c-5 절차). `/sync-skills`로 양방향 동기화. 권위 있는 동작 명세는 `SKILL.md`.

## 개요
Autopilot family — **post-creation iteration pipeline for research and doc artifacts** (NOT code). 갈래 E (사후 정정). 

- **Prompt-driven**: target artifact는 prompt 키워드 fuzzy match against `.claude_reports/{research,documents}/*`로 자동 식별
- artifact의 file structure 자동 발견 → plans edits → diff preview → 사용자 confirm → 적용 + 버전 스냅샷 + integrated history 누적 (`pipeline_summary.md` — 단일 source of truth, 별도 CHANGELOG 없음)
- 기본 `--qa quick` (1-pass review, fastest path). escalate to light/standard/thorough/adversarial for multi-round review, fact-check, or external Codex adversarial pass
- Optional `--memo <file>` falls back to file-memo style for deferred reviews

> code 산출물은 본 skill 대상 아님 — `/refine-plan` 또는 `/autopilot-code` 사용.

## 호출 형식
```
/autopilot-refine "<prompt>" [--qa quick|light|standard|thorough|adversarial] [--review-only | --memo <file>] [--confirm] [--no-fact-check] [--no-style-audit]
```

## Default Invocation Rule (자동 호출 트리거)
**메인 Claude가 slash command 명시 없이 자동 invoke** — `.claude_reports/{documents,research}/*` 하위 artifact에 대한 자연어 수정·정정·보강·스타일 변경 prompt를 받으면 `autopilot-refine "<prompt>" --qa quick`을 자동 호출.

**Override 1순위**:
- (a) 다른 qa level 명시 (`standard`/`thorough`/`adversarial`)
- (b) "refine 없이 직접 edit" · "Edit으로 처리" · "versioning 없이"
- (c) `--review-only` 검수만 요청

## 모드
| 플래그 | 동작 |
|---|---|
| `"<prompt>"` (default) | 자연어 prompt + 자동 fuzzy match artifact → diff preview → 자동 apply |
| `--memo <file>` | 별도 메모 파일에서 일괄 반영 (deferred review용) |
| `--confirm` | 수정 전 chat-pause (검토 원할 때) |
| `--review-only` | 점검만, 적용 X |

## QA Scaling
| Level | 처리 |
|---|---|
| quick (default) | 1-pass quality review, refine 자동 적용. fact-checker / style-audit skip |
| light | quality reviewer 1× (sonnet) |
| standard | quality reviewer (opus) + fact-checker (sonnet, parallel) |
| thorough | quality reviewer 2× parallel + fact-checker |
| adversarial | standard + Codex 외부 리뷰 (camera-ready·grant 등) |

## 버전 + 이력
- 적용 시 `_internal/versions/v{N}/` 스냅샷
- `pipeline_summary.md`에 통합 history 누적 (별도 CHANGELOG 없음)

---
*원본: `~/.claude/skills/autopilot-refine/SKILL.md`*
