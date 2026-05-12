# refine-doc

> 본 README는 Notion 페이지 [✏️ refine-doc](https://www.notion.so/34987c2bb75381bfadc3c4c26ba6cdb6)의 미러. `/sync-skills`로 양방향 동기화. 권위 있는 동작 명세는 `SKILL.md`.

## 개요
autopilot-doc의 refine 단계 서브스킬. 사용자 메모 또는 review 피드백을 strategy 또는 draft에 반영. **versioned output** + **mandatory ref-grounding** (메모마다 source re-read).

> 이전 이름 `refine-doc-strategy`에서 2026-05-06에 `refine-doc`로 리네임 — strategy + draft 양쪽 처리하므로 generic한 이름으로 변경.

## 호출 흐름
```mermaid
flowchart TD
    INPUT["입력: <strategy/draft 경로>"] --> DETECT{"경로에 /strategy/ or /draft/?"}
    DETECT -->|/strategy/| STR["strategy mode (strategy.md + strategy_ko.md)"]
    DETECT -->|/draft/| DR["draft mode (draft.md + draft_ko.md)"]
    STR --> VER["Pre-Refine: Versioning Setup"]
    DR --> VER
    VER --> RT["연구팀 위임 (메모 탐색 + ref-grounding + 적용)"]
    RT --> WRITE["latest 파일 + v{N} archive 저장 + CHANGELOG 갱신"]
    WRITE --> QA["Post-Refine Review Loop (quality + fact-check 병렬, max 2 rounds)"]
    QA -->|🔴 없음| DONE["사용자 보고"]
    QA -->|🔴 있음| RT
```

## 1. 메모 탐색
한국어 파일에서 다음 형식 탐색:
- `<!-- memo: ... -->` (표준 메모 태그)
- `<!-- ... -->` (HTML 주석 — CHANGELOG block 제외)
- `// ...` (인라인 주석)
- `[memo] ...` (대괄호 주석)
- `(**...**)` (괄호 주석)
- 기타 사용자 주석 표시

## 2. Mandatory Ref-Grounding (핵심)
각 메모마다 *적용 전에* 필수:
1. 메모가 가리키는 source 식별:
   - Paper analyses (`.claude_reports/analysis_project/paper/*.md`) — citation / venue / score / dataset 사실 (single source of truth)
   - Strategy document — narrative arc / outline 정합성
   - Analysis files — audience / key messages / visual strategy
   - Original PDFs — paper 본문 재독이 필요한 nuanced 주장 (paper analyses 부족 시만)
2. **Source 재독** (메모 주장만 믿지 말 것)
3. 메모 vs source 대조:
   - 메모 = source 일치 → 메모대로 적용
   - 메모 ≠ source 충돌 → **메모 override**, 원본 텍스트 유지, changelog에 충돌 기록
   - source 모호 → 적용하되 `[CAUTION: source ambiguous]` 표시
4. Changelog에 source 검증 기록: `[verified analysis_project/paper/2020_Hu_DCCRN.md]` 형식

> 사용자 메모가 *틀린 경우* silent하게 전파하지 않음 — source가 진실의 출처.

## 3. Versioned Output
- Modern convention: `{artifact_root}/_internal/versions/v{N}/{strategy,draft}/`
- Legacy: `{ko_path.parent}/{ko_path.stem}_v{N}.md` 형제 (artifact가 이미 그 패턴 사용 시만)
- `latest` 파일 (현재 vN) + `v{N-1}` archive 양쪽 저장
- 이전 버전은 **immutable** — 절대 수정 X
- 첫 refine 시 현재 상태를 v1으로 스냅샷 후 작업이 v2로 진행

## 4. CHANGELOG Block (자동 관리)
파일 최상단에 다음 형식의 block:
```
<!-- CHANGELOG (auto-managed by refine-doc — do NOT edit manually)
v{N} ({YYYY-MM-DDTHH:MM}, applied X memos / overrode Y memos):
  - [Slide N | Section X] [verified <source>]: <one-line description>
  - [Slide N | Section X] [OVERRIDDEN — memo conflicted with <source>]: <reason>
  ...
{previous CHANGELOG entries preserved verbatim}
-->
```

- 새 v{N+1} entry는 *기존 block 위에* prepend (newest first)
- 사용자가 직접 편집 금지 — autopilot이 관리

## 5. Post-Refine Review Loop
연구팀 작업 후 **품질관리팀이 quality + fact-checker 병렬 검수** (최대 2 rounds).

| Level | 조건 | Quality reviewer | Fact-checker (parallel) |
|---|---|---|---|
| Quick | `--qa quick` only | 1× (sonnet), spot-check만 | skip (`--qa quick`는 autopilot에서 refine entirely skip — manual invoke 시만) |
| Light | ≤3 sections 변경 | 1× (sonnet) | skip |
| Standard | 4+ sections 변경 | 1× (opus) | 1× fact-check (sonnet) |
| Thorough | major overhaul / new evidence | 2× parallel (opus) | 1× fact-check (sonnet) |

- **Quality reviewer**: narrative arc / cohesion / strategy 반영 / rebuttal 시 모든 reviewer point 응답
- **Fact-checker**: `analysis_project/paper/*.md` verbatim 대조

🔴 발견 시 연구팀 재호출 (max 2 rounds). 2 rounds 후에도 🔴 잔존 → `## 미해결 이슈` 섹션에 기록 + `[FACT-RESIDUAL]` 태그.

## 다른 skill과의 관계
```mermaid
flowchart LR
    INIT["init-doc-strategy"] -->|v1 (initial)| STR["strategy.md"]
    STR -->|메모 추가| RD["refine-doc (strategy mode)"]
    RD -->|v2, v3, ...| STR
    STR -->|draft 생성| DRAFT["draft.md"]
    DRAFT -->|메모 추가| RD2["refine-doc (draft mode)"]
    RD2 -->|v2, v3, ...| DRAFT
```

`init-doc-strategy`는 v1 (initial)만 만들고, 모든 후속 수정은 `refine-doc`이 담당.

---
*원본: `~/.claude/skills/refine-doc/SKILL.md`*
