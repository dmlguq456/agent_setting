# sync-skills

> 본 README는 Notion 페이지 [🔄 sync-skills](https://www.notion.so/35e87c2bb75381a0b0c9ca3fa3159919)의 미러. `/sync-skills`로 양방향 동기화. 권위 있는 동작 명세는 `SKILL.md`.

## 개요
Skills + Agents 정의 변경을 감지해 다음을 동기화하는 skill:
- `~/.claude/README.md` (GitHub mirror)
- Notion 대문 페이지 (Agents/Skills) 상단 대시보드 (워크플로우 map + cheat-sheet + 통합 가이드라인)
- 각 skill/agent의 개별 README ↔ Notion 자식 페이지 (양방향)

drift 체크 전용 모드도 지원.

## 호출 형식
```
/sync-skills [--check] [--readme-only] [--notion-only] [--force] [--prefer-local] [--prefer-notion]
```

## Source of Truth
- **Skills**: `~/.claude/skills/*/SKILL.md` (frontmatter)
- **Agents**: `~/.claude/agents/*.md` (frontmatter)
- **개별 README**: `~/.claude/skills/{name}/README.md`, `~/.claude/agents/{name}.README.md`

## 출력
1. **GitHub**: `~/.claude/README.md` (자동 생성, 직접 편집 금지)
2. **Notion 대문 상단 대시보드**: `Agents/Skills` 페이지 (id: `34987c2b-b753-80d6-8df4-d6ce4d469bff`) — 상단 대시보드 영역 자동 갱신, 하단 `<columns>` 자식 페이지 보존
3. **개별 README ↔ Notion 자식 페이지**: 양방향 동기화 (last_edited_time 비교, newer가 source, 충돌 시 사용자 확인)
4. **상태 파일**: `~/.claude/skills/.sync_state.json` (v3 schema)

## 인자
- `--check`: drift만 보고하고 종료. 쓰기 작업 X
- `--readme-only`: README.md + 개별 README만 갱신, Notion은 건드리지 않음
- `--notion-only`: Notion 대문 + 자식 페이지만 갱신, 로컬 README는 건드리지 않음
- `--force`: SHA가 같아도 재생성
- `--prefer-local`: 충돌 시 자동으로 local README가 source (Notion 덮어쓰기)
- `--prefer-notion`: 충돌 시 자동으로 Notion이 source (local README 덮어쓰기)

기본 (인자 없음): drift 감지 → 변경 있으면 README + Notion 모두 갱신. 충돌은 사용자 확인.

## 파이프라인 (개요)
1. Discover + hash (SKILL.md / agent.md + 개별 README)
2. Read sync state (`.sync_state.json` v3)
3. Drift report (변경/신규/삭제/동일 4 분류)
4. Generate dashboard sections (워크플로우 map + Skills/Agents 표)
5. Write README.md (canonical layout)
5c. **개별 README ↔ Notion 자식 페이지 양방향 sync** (변경 감지 3-way, 충돌 처리, 신규 마이그레이션)
6. Update Notion 대문 상단 (update_content)
7. Update sync state (v3 fields 모두 갱신)
8. Final report

## Hook integration (옵션)
`~/.claude/settings.json`에 다음 추가하면 세션 종료 시 drift 알림:

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "find ~/.claude/skills ~/.claude/agents -name '*.md' -newer ~/.claude/skills/.sync_state.json 2>/dev/null | head -1 | grep -q . && echo '[sync-skills] drift detected — run /sync-skills' || true"
      }]
    }]
  }
}
```

자동 sync는 권하지 않음 (편집 중간마다 노션이 푸시되면 노이즈) — 명시적 호출 + drift 알림만 권장.

---
*원본: `~/.claude/skills/sync-skills/SKILL.md`*
