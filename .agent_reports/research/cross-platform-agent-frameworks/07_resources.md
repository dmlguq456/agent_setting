# 07 — Open-Source Code / Tools Inventory

> 정독할 만한 reference implementation 목록. 이들은 npm/Python 패키지라 **코드를 그대로 복사하는 것이 아니라 설계 참고 자료로 정독** 하는 것이 목적. 모든 링크는 `cards/*.md` 의 `## Sources` 에 소급.

## Tier 1 — 직접 참고할 reference implementation (채택 결정 근거)

### GSD state-transition + installer (양방향 divergence 의 유일 선행 사례)
- **왜**: [06_implementation](06_implementation.md) 후보 1(hash-manifest+reapply)의 실코드 근거. 채택 전 정독 필수.
- **핵심 파일**:
  - `gsd-core/bin/lib/state-transition.cjs` — `STATE.md` 를 pure-core `transitionCore(content, intent, deps)` + injected I/O 로 변환, `FIELD_CLASSIFICATION` 테이블(preserve-when-unchanged/preserve-always/derive)로 frontmatter↔body 충돌 해소 (`gsd.md` §6, ADR-1769).
  - `bin/install.js` — hash-manifest drift 감지 + `gsd-local-patches/` + `--reapply` (line 단위는 카드도 일부만 검증 — **재확인 필요**).
  - `capabilities/<runtime>/capability.json` — runtime 표면 계약 선언(`commandStyle`/`hooksSurface`/`artifactLayout.converter`) 의 manifest 설계 reference (`gsd.md` §7).
  - `tests/workflow-size-budget.test.cjs` — byte-budget CI(XL 90KB) 참고 (`gsd.md` §4).
- **repo**: https://github.com/open-gsd/gsd-core (active), raw: `next` 브랜치.

### spec-kit INTEGRATION_REGISTRY (registry+placeholder projection reference)
- **왜**: [06_implementation](06_implementation.md) 후보 2 의 설계 reference — registry SoT + placeholder 치환.
- **핵심 파일**:
  - `src/specify_cli/__init__.py` — `AGENT_CONFIG` import, `_install_shared_infra`/`_refresh_shared_templates`, `core_pack`, `GITHUB_API_LATEST` (`spec-kit.md` §1-2).
  - `AGENTS.md`(repo 내) — integration base class·`config`/`registrar_config`·placeholder·새 agent 4단계 등록 절차 (`spec-kit.md` §1).
  - `scripts/bash/check-prerequisites.sh` — prerequisite gate(`plan.md` required, `--require-tasks`) 로직 (`spec-kit.md` §4).
- **repo**: https://github.com/github/spec-kit

## Tier 2 — 참고 전용 (설계 대조용, 직접 채택 대상 아님)

- **Claude 공식 plugin/marketplace 문서** — version/SHA-pin, `renames`, source types 규격. https://code.claude.com/docs/en/plugin-marketplaces , https://code.claude.com/docs/en/plugins (`claude-code-official-plugins.md` 전체).
- **BMAD `resolve_customization.py`** — 3-layer TOML override(skill default/team committed/user gitignored) merge 설계. `tools/installer/ide/_config-driven.js` + `platform-codes.yaml` = config-driven projection. https://github.com/bmad-code-org/BMAD-METHOD (`bmad-method.md` §1·6).
- **ruler / rulesync** — one-runtime-only 기능 3층 처리(skip+warning / event 정규화 / prompt-simulation) reference. rulesync `docs/guide/simulated-features.md`·`docs/reference/file-formats.md` 가 특히 parity-loss 처리의 실증. https://github.com/intellectronica/ruler , https://github.com/dyoshikawa/rulesync (`multi-harness-projection.md` §1-2).
- **claude-flow MetaHarness / `ruflo verify`** — snapshot 감사 + cryptographic witness manifest(`.harness/manifest.json`) reference (단 파일-복제 배포는 반면교사). https://github.com/ruvnet/ruflo (`claude-flow.md` §6).
- **Superpowers hooks bootstrap** — session lifecycle 재주입(SessionStart+compaction) reference. https://github.com/obra/superpowers (`superpowers.md` §4·6).
- **Agent OS `config.yml` profile inheritance** — 동일 파일명 override reference. https://github.com/buildermethods/agent-os (`agent-os.md` §2, config.yml verbatim).

## 설치 명령 (카드에 실재 인용된 것만)

카드에 명시된 실제 명령만 옮긴다 (fabricated verify 명령 없음).

| 도구 | 명령 | 근거 |
|---|---|---|
| GSD | `npx @opengsd/gsd-core@latest` (installer) / `/gsd-update --reapply` | `gsd.md` §2 |
| spec-kit | `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z` | `spec-kit.md` §2 |
| BMAD | `npx bmad-method install` (interactive) | `bmad-method.md` §2 |
| SuperClaude | `pipx install SuperClaude && SuperClaude install` | `superclaude.md` §2 |
| Superpowers | `/plugin install superpowers@claude-plugins-official` | `superpowers.md` §2 |
| claude-flow | `npx ruflo@latest init` / `claude mcp add ruflo -- npx ruflo@latest mcp start` | `claude-flow.md` §3 |
| ruler | npm `@intellectronica/ruler` | `multi-harness-projection.md` §1 |
| rulesync | `rulesync generate --targets <tools> --features <features>` | `multi-harness-projection.md` §2 |

> **caveat**: GSD 버전 넘버링(repo 1.7.0-rc.4 vs changelog v1.4x), Agent OS install(email-gated, verbatim 미확인), claude-flow 정체성(`claude-flow`↔`ruflo`) 은 카드가 unverified/주의로 표시 — 정확한 최신 버전·명령은 각 릴리스 페이지 재확인.

---
관련: [06_implementation](06_implementation.md)(채택 로드맵) · 전체 인용은 각 `cards/*.md` 의 `## Sources` 참조.
