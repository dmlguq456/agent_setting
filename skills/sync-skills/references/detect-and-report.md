### Step 1: Discover + hash
```bash
AGENT_HOME="${AGENT_HOME:-${CLAUDE_HOME:-$HOME/.claude}}"
ls "$AGENT_HOME"/adapters/claude/skills/*/SKILL.md "$AGENT_HOME"/adapters/claude/agents/*.md
```
각 파일:
- SHA-256 (`shasum -a 256 <file> | awk '{print $1}'`)
- frontmatter 파싱 (간단한 YAML 파서: 첫 `---` ~ 두 번째 `---`)

### Step 2: Read sync state
`<agent-home>/skills/.sync_state.json` 로드. 없으면 빈 dict.

스키마 (v4):
```json
{
  "version": 4,
  "last_readme_sync": "ISO8601",
  "items": {
    "adapters/claude/skills/autopilot-code": {
      "sha256": "...",
      "synced_at": "ISO8601"
    },
    "adapters/claude/agents/research-team": {
      "sha256": "...",
      "synced_at": "ISO8601"
    }
  }
}
```

- `sha256` / `synced_at` — SKILL.md / agent.md 자체 (frontmatter parsing source)


### Step 3: Drift report
**신규 / 변경 / 삭제 / 동일** 4 분류. 한국어 출력:
```
Sync 상태 (2026-05-25 12:34 KST)
─────────────────────────────────────
Skills:  변경 3 / 신규 0 / 삭제 0 / 동일 9
Agents:  변경 0 / 신규 0 / 삭제 0 / 동일 8

[변경된 항목]
  ✏️  adapters/claude/skills/autopilot-code   (마지막 sync: 2026-04-21)
  ✏️  adapters/claude/skills/autopilot-draft  (마지막 sync: 2026-04-21)
  ✏️  adapters/claude/skills/code-plan        (마지막 sync: 2026-04-21)

마지막 README sync: 2026-04-21 09:08
```

`--check` 이면 종료.

