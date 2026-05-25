# autopilot-refine

> 본 README는 Notion 페이지 [🔁 autopilot-refine](https://www.notion.so/35e87c2bb75381fab020d6f7c2685aef)의 미러. `/sync-skills`로 양방향 동기화. 권위 있는 동작 명세는 `SKILL.md`.

## 개요
Autopilot family — **post-creation iteration pipeline for research and doc artifacts** (NOT code). 갈래 E (사후 정정). 

- **Prompt-driven**: target artifact는 prompt 키워드 fuzzy match against `.claude_reports/{research,documents}/*`로 자동 식별
- artifact의 file structure 자동 발견 → plans edits → diff preview → 사용자 confirm → 적용 + 버전 스냅샷 + integrated history 누적 (`pipeline_summary.md` — 단일 source of truth, 별도 CHANGELOG 없음)
- 기본 `--qa quick` (1-pass review, fastest path). escalate to light/standard/thorough/adversarial for multi-round review, fact-check, or external Codex adversarial pass
- Optional `--memo <file>` falls back to file-memo style for deferred reviews

> code 산출물은 본 skill 대상 아님 — `/code-refine` 또는 `/autopilot-code` 사용.

## 호출 형식
```
/autopilot-refine "<prompt>" [--qa quick|light|standard|thorough|adversarial] [--review-only | --memo <file>] [--confirm] [--no-fact-check] [--no-style-audit]
```

## Default Invocation Rule (자동 호출 트리거)
**메인 Claude가 slash command 명시 없이 자동 invoke되는 조건은 _major-level 변경_으로만 narrowing.** `.claude_reports/{documents,research}/*` 하위 artifact에 대한 prompt가 다음 3-criteria 중 하나에 해당할 때 `autopilot-refine "<prompt>" --qa quick`을 자동 호출:

1. **사용자 명시**: "major" / "v{N+1}" / "/autopilot-refine" / "전면 재작성" / "phase 재시작"
2. **구조적 대규모 변경**: ≥200 줄 영향 / 전체 section rewrite / mutation tier 재분류 batch
3. **외부 검토 직전 ceremony**: "camera-ready 마무리" / "submission 직전 finalize" / "PR open 직전"

**Minor-level (default — 위 미해당 시 모두)** = 직접 Edit + `pipeline_summary.md` 상세 minor log entry 추가 (snapshot X, last major snapshot이 audit baseline). 누적 minor 5건 도달 시 `/audit` 권장 alert → audit이 dual-perspective (vs last major + vs principles) batch 점검.

**Minor log entry 형식** (반드시 준수 — 추적성 핵심):

- `## 버전 히스토리` 표에 `| v{N}_M | YYYY-MM-DD | (minor) 한 줄 요지 |` row 추가
- `## 마이너 변경 로그 (v{N} → next major 누적)` 섹션에 상세 entry (Trigger / Scope / Rationale / Files touched / Cross-ref / Audit-flag / Reversibility)

**Override 1순위**:
- (a) 다른 qa level 명시 (`standard`/`thorough`/`adversarial`) → 강제 refine
- (b) "refine 없이 직접 edit" · "Edit으로 처리" · "versioning 없이" → 강제 minor 경로
- (c) `--review-only` 검수만 요청
- (d) `/autopilot-refine` slash 명시 invoke → 강제 refine flow

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
| adversarial | thorough (2× opus + fact-checker) + Codex 외부 리뷰 (camera-ready·grant 등) |

## 버전 + 이력
- **Major 적용 시**: `_internal/versions/v{N+1}/` 스냅샷 + `pipeline_summary.md` 통합 history 누적. Stage D는 활성 `## 마이너 변경 로그` 섹션을 _verbatim_ 으로 새 major의 `## v{N+1} 변경 사항` 안 `### 누적 마이너 변경 사항 (v{N}_1 → v{N}_M)` sub-block 으로 migrate + 활성 로그 섹션 clear. **추가로 각 affected file의 frontmatter `changelog:` array에 v{N+1} entry insert** (in-file git-tracked lineage 보존).
- **Minor 적용 시**: snapshot X — Claude가 직접 Edit + `pipeline_summary.md` `## 마이너 변경 로그` 섹션에 상세 entry. **추가로 각 affected file의 frontmatter `changelog:` array에 v{N}_M entry 1줄 insert**. last major snapshot이 audit baseline.

---
*원본: `~/.claude/skills/autopilot-refine/SKILL.md`*
