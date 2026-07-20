# Round 1 Fact Check

## Verdict: PASS with scoped caveats

- ✅ Herdr parallel agent/persistent PTY/read-send-wait/attach claims match stable official docs.
- ✅ v0.7.4 is latest release as of 2026-07-20; local 0.6.6 is explicitly separated.
- ✅ Claude/Codex state authority and integration minimum versions match official docs.
- ✅ current harness claims map to cited local contracts and live checks.
- ✅ `agent.send` is described as transport, not a semantic debate bus; this is a source-based inference and is labeled as such.
- ✅ no claim that Herdr replaces or subsumes current routing/QA/worktree/attempt logic.

## Caveats retained

- Adapter claim-verification provider는 현재 unavailable(exit 69)이어서, 외부 주장은 Herdr/Codex 공식 문서·tagged source와 두 조사자의 교차 검토로 대체 검증했다.
- Herdr docs were updated after v0.7.4 release; installed schema probing is mandatory before implementation.
- screen-based blocked detection can classify unknown prompts as idle.
- server restart, detach, and live handoff have different persistence semantics.
- plugin and pane input are privileged actions.
