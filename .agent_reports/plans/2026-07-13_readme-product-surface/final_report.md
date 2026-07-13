# Final report — README product surface

## 결과

Root README를 PRD v3의 제품 landing page로 전면 재설계하고, active `sync-skills` capability 및 Claude/Codex/OpenCode projection을 퇴역했다. README prose는 human-owned로 두고 manifest·runtime projection·boundary·conformance를 결정론적 도구가 소유하도록 계약 문구를 정리했다.

## 변경 범위

- Public surface: `README.md`, `MANUAL.md`, capability catalog, core adaptation/convention 문구.
- Retirement: canonical capability, compatibility/Claude skill trees, Codex/OpenCode skill·command·plugin projection, `.sync_state.json`, manifest entry.
- Active consumers: oncall, editorial mode, agents, skill notes, tool comments, dispatch fixtures를 직접 검사 명령 또는 neutral fixture로 교체.
- Generated output: Claude plugin, Codex skills/plugin/agents/modes, OpenCode skills/commands/agents, `manifest.json` 재생성.

## 검증

- README 내부 링크 16개, heading 순서, help/dry-run/plugin 설치 명령 PASS.
- current source `sync-skills` active reference 0건; 퇴역 경로와 manifest entry 부재.
- manifest와 모든 native projection `--check`, adaptation boundary, skill conformance, Codex doctor PASS.
- portable guard 343개 PASS, root/Claude fleet dispatch unit 각 58개 PASS, `git diff --check` PASS.
- 격리 HOME에서 Claude/Codex/OpenCode install all → verify PASS.
- 실제 worktree Codex runtime projection 27 skills/9 agents 설치와 `doctor --runtime` PASS.

## 잔여 위험과 한계

- 실제 사용자 홈의 Claude/OpenCode projection은 기존 main checkout을 계속 가리킨다. worktree 변경의 통합 검증은 격리 HOME에서 수행했고, 임시 Codex projection은 main orchestrator가 원래 main checkout으로 복원한다.
- depth-2 Codex worker는 app-server read-only 초기화 실패로 시작하지 못했다. adapter의 inline fallback을 사용했으며 독립 QA를 주장하지 않는다.
- 첫 portable guard 병렬 실행의 runtime projection 두 항목은 동시 검사 간섭으로 실패했지만, 단독 재실행에서 343/343 PASS했다.
