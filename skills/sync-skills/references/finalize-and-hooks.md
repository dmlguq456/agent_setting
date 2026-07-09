### Step 6: Update sync state
`<agent-home>/skills/.sync_state.json` 을 새 SHA + 시각으로 저장. v4 스키마 필드 모두 갱신:

- SKILL.md / agent.md: `sha256`, `synced_at`
- 전역: `last_readme_sync`

### Step 6b: Emit manifest.json

정의(skills/roles/Claude agents/loops/settings)를 긁어 단일 계약 `<agent-home>/manifest.json` (repo 루트, README 와 동일 계층) 을 재방출한다. **manifest 는 정의에서 deterministic 파생** — 손으로 편집하지 않고 빌드 스크립트가 유일한 전사 경로다 (정의=SoT, manifest=방출물).

```bash
python3 tools/build-manifest.py          # manifest.json 재생성 (멱등 — 정의 안 바뀌면 byte-identical)
# --check 모드:
python3 tools/build-manifest.py --check  # 빌드 결과를 기존 manifest.json 과 비교, 어긋나면 exit 1
```

- 빌드 스크립트가 긁는 것: Claude adapter skill frontmatter(`adapters/claude/skills/*/SKILL.md`, `metadata:{group,fam,modes,blurb}` + `argument-hint`) + agents `metadata:{modes,blurb}`·`model` + `loops/README.md` 현역 표 + Claude adapter settings hooks (read-only) + 문서화된 4-track 상수.
- `--check` 모드 (위 Argument Parsing) 에서는 `build-manifest.py --check` 로 manifest drift 도 감지해 Step 3 drift report / Step 7 final report 에 노출 (비-0 exit = 정의 변경 후 manifest 재방출 누락).
- 소비자(worklog-board)는 이 manifest **한 계약만** 소비한다 — 내부 정의를 직접 뒤지지 않는다 (경계 분리).

### Step 7: Final report
```
✅ Sync 완료
─────────────────────────────────────
SKILL.md/agent.md 변경: 3 (autopilot-code, autopilot-draft, code-plan)
README.md 갱신: <agent-home>/README.md
manifest.json 재방출: <agent-home>/manifest.json (Step 6b)

다음에 PR/푸시:
  cd <agent-home> && git add README.md manifest.json tools/build-manifest.py adapters/claude/skills/ skills/ roles/ adapters/claude/agents/
  git commit -m "skills+agents: <변경 요약>"
  git push
```

## Hook integration (옵션)
Claude Code adapter 의 `settings.json` 에 다음 추가하면 세션 종료 시 drift 알림:

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "AGENT_HOME=\"${AGENT_HOME:-${CLAUDE_HOME:-$HOME/.claude}}\"; find \"$AGENT_HOME/adapters/claude/skills\" \"$AGENT_HOME/adapters/claude/agents\" -name '*.md' -newer \"$AGENT_HOME/skills/.sync_state.json\" 2>/dev/null | head -1 | grep -q . && echo '[sync-skills] drift detected — run /sync-skills' || true"
      }]
    }]
  }
}
```

자동 sync 는 권하지 않음 — 명시적 호출 + drift 알림만이 권장 패턴.
