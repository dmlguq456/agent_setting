# sync-skills

> 본 README 는 GitHub mirror. 권위 있는 동작 명세는 `SKILL.md`.

## 개요
Skills + Agents 정의 변경을 감지해 `<agent-home>/README.md` (GitHub) 의 대시보드 (워크플로우 map + cheat-sheet + 통합 가이드라인) 를 동기화하는 skill. drift 체크 전용 모드도 지원.


## 호출 형식
```
/sync-skills [--check] [--force] [--auto-fix [--dry-run]]
```

## Source of Truth
- **Skills**: `<agent-home>/skills/*/SKILL.md` (frontmatter)
- **Roles**: `<agent-home>/roles/README.md`
- **Claude Agents**: `<agent-home>/adapters/claude/agents/*.md` (frontmatter)
- **CONVENTIONS.md**: `<agent-home>/core/CONVENTIONS.md` (QA / model / cross-doc invariants — Step 5b canonical)

## 출력
1. **GitHub**: `<agent-home>/README.md` (자동 생성, 직접 편집 금지 — `§3.(1) 자연어 발화 예시 표 + 그 직전 prose` 만 사람 유지 영역)
2. **상태 파일**: `<agent-home>/skills/.sync_state.json` (v4 schema)

## 인자
- `--check`: drift 만 보고하고 종료. 쓰기 작업 X
- `--force`: SHA 가 같아도 재생성
- `--auto-fix`: Step 5b 에서 발견한 cross-doc invariant drift 를 `CONVENTIONS.md` canonical wording 으로 자동 교체 (default 는 report-only). `--dry-run` 과 조합 시 미리보기.

기본 (인자 없음): drift 감지 → 변경 있으면 README 갱신.

## 파이프라인 (개요)
1. Discover + hash (SKILL.md / agent.md)
2. Read sync state (`.sync_state.json` v4)
3. Drift report (변경/신규/삭제/동일 4 분류)
4. Generate dashboard sections (워크플로우 map + Skills/Agents 표)
5. Write README.md (canonical layout)
   - 5a. 편집팀 검수 (LLM 스러운 어조 회피)
   - 5b. Cross-doc invariant scan (QA / model 정의 drift)
6. Update sync state
7. Final report

## Hook integration (옵션)
Claude Code adapter 의 `settings.json` 에 다음 추가하면 세션 종료 시 drift 알림:

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "find <agent-home>/skills <agent-home>/adapters/claude/agents -name '*.md' -newer <agent-home>/skills/.sync_state.json 2>/dev/null | head -1 | grep -q . && echo '[sync-skills] drift detected — run /sync-skills' || true"
      }]
    }]
  }
}
```

자동 sync 는 권하지 않음 — 명시적 호출 + drift 알림만 권장.

---
*원본: `<agent-home>/skills/sync-skills/SKILL.md`*
