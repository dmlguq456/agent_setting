# 03 — Vendor / Solution Comparison

> 조사한 9개 프레임워크를 layer 구조·packaging·drift 방지 메커니즘·강약점으로 대조한다. 셀 값은 전부 `cards/*.md` 및 [analysis_summary](analysis_summary.md) §3 에 소급.

## 1. 종합 비교 매트릭스

| Framework | Layer 구조 | Packaging | Drift-prevention 메커니즘 | 강점 | 약점 |
|---|---|---|---|---|---|
| **GSD** | core(`gsd-core/`·agents·commands·skills) + 16 runtime capability manifest + installer converter | npm `@opengsd/gsd-core` **또는** Claude plugin; `/gsd-update` | **hash-manifest** drift 감지 → `gsd-local-patches/` → `--reapply` 재적용 + 소유 경계 규칙 + converter 흡수 | 유일하게 양방향 divergence(3-way merge) 실구현; 표현력 높은 manifest | 버전 넘버링/문서 drift 자증; installer file-ops line 단위 미검증 |
| **spec-kit** | core `templates/`+`scripts/`(agent-agnostic) + `integrations/` registry | Python `uv tool install specify-cli`; per-agent×per-shell zip(→embed 이동) | `INTEGRATION_REGISTRY` SoT + **계층적 template resolution**(overrides>presets>extensions>core) | registry 단일 SoT 로 30+ agent; 커스터마이즈 물리 분리 | 순서 gate 느슨(plan.md 존재만 hard); 구/신 registry 혼재 |
| **BMAD-METHOD** | authoring `src/*-skills/` → installer projection → runtime | npm `npx bmad-method install`; `@next` prerelease | **`_bmad/custom/*.toml` 3-layer override**(default/team/user) + cross-tool `.agents/skills` + CI validate | override 3계층(team vs user 구분까지); 20+ tool | 재설치 시 override 보존 file-ops 미검증; fork 는 최후수단 |
| **Superpowers** | harness별 adapter 폴더(`.claude-plugin/`·`.codex-plugin/`…) + core `skills/` | runtime별 개별 설치; update agent-dependent | **session lifecycle 재주입**(SessionStart+compaction) + core/lab/community repo 분리 | context 유실 drift 방지 독창적; skill 품질 관리 | update 시 로컬 보존 문서 미검증; 중앙 store 불명 |
| **Agent OS** | two-tier(base `~/agent-os/` + project `.agent-os/`) + tool adapter | install script(email-gated, 미확인); `project-update.sh` | **profile inheritance**(동일 파일명 override) + `.agent-os/` committable + index regeneration | 표준-코드 committable 로 drift 억제 | install verbatim 미확인; gate 없음(명시적) |
| **claude-flow (ruflo)** | monorepo `@claude-flow/*` core vs adapter(`@claude-flow/codex`) | npm `ruflo`/`npx ruflo init`; MCP; plugin(35개) | **MetaHarness snapshot 감사**(사후 drift 탐지) + `ruflo verify` witness manifest | machine gate 강력(hook dispatcher+12 worker+consensus) | **파일복제 스캐폴딩 → 자체 367개 중복 SKILL.md drift(#1834)** |
| **SuperClaude** | single-runtime(Claude Code); core(always) vs on-demand loading 축 | pipx/pip/npm `SuperClaude install`; `~/.claude/` 직접 배치 | **약함** — `~/.claude/` 덮어쓰기, 로컬 보존 전략 부재(자인 gap) | RULES priority+conflict hierarchy 문서화 | 문서 자체 버전 drift; 버전 격리 convention 부재 |
| **Claude Code official** | single-runtime plugin **host 규격**(투영 target) | `/plugin install`; source github/url/git-subdir/npm | **fork 안 함** — marketplace source 참조 + version/SHA pin + auto-update + `renames` | 소비 시나리오 최적; pin 정밀 | 양방향 divergence 용 3-way merge 부재(자인) |
| **AGENTS.md** | projection 없음 — 단일 prose Markdown(LCD) | tool 이 파일 직접 read | 정의상 최소공통분모(표현할 게 없어 drift 여지 최소) | 채택 장벽 0; drift 최소 | 실행 기능 0(hook/MCP/skill 불가) |
| **ruler / rulesync** | `.ruler/`·`.rulesync/` single source → N runtime | npm CLI | ruler: `.bak`+source 주석 / rulesync: per-tool override+hook 정규화 | 순수 배포 도구로 경량 | framework 아님; capability loss(silent drop/skip) |

## 2. Capability Checklist

| Framework | multi-runtime | machine-enforced gate | hash-manifest 또는 등가 | progressive disclosure |
|---|---|---|---|---|
| GSD | **Y** (16 runtime) | Partial (capability `gates[]`, 일부 blocking) | **Y** (hash-manifest+reapply) | **Y** (2-stage routing) |
| spec-kit | **Y** (30+ agent) | Partial (plan.md required, 순서는 convention) | N (registry SoT, hash 아님) | Partial (per-agent memory always) |
| BMAD-METHOD | **Y** (20+ tool) | Partial (state machine, `bmad-loop`만 hook) | N (override layer, hash 아님) | **Y** (per-skill on-demand) |
| Superpowers | **Y** (6+ harness) | Partial (bootstrap 재주입=mechanism, 순서=instruction) | N | **Y** (3-level) |
| Agent OS | **Y** | **N** (명시적 convention-only) | N (profile inheritance) | Partial (index.yml query) |
| claude-flow | **Y** (Claude/Codex, parity 미검증) | **Y** (hook dispatcher+consensus) | **Y** (`ruflo verify` witness) | N (파일복제) |
| SuperClaude | **N** (Claude 전용) | **N** (convention-only) | N | Partial (trigger-based) |
| Claude Code official | **N** (host 규격) | **Y** (`PreToolUse` block) | Partial (version/SHA pin) | **Y** (3-level, 1536자) |
| ruler / rulesync | **Y** (30~40+) | N/A (배포 도구) | Partial (ruler `.bak`) | N/A |

## 3. 활용 상황별 요점

- **양방향 divergence(로컬 수정 + upstream 추종) 관리 → GSD**. 유일하게 hash-manifest + `--reapply` 로 3-way merge 를 실구현. Claude 공식조차 이 도구는 "없다" 고 인정 (`gsd.md` §2, `claude-code-official-plugins.md` §6). **요점: 우리 harness 의 핵심 난점에 직접 대응하는 유일 후보.**
- **소비-only(제3자 컴포넌트 당겨오기) → Claude 공식 version/SHA pin**. fork 자체를 회피, `renames` 로 마이그레이션까지. **요점: 우리가 외부 skill 을 소비할 때의 모델.**
- **커스터마이즈 물리 분리 → spec-kit / BMAD / Agent OS**. override-layer 를 core 와 다른 계층에 두는 공통 패턴. **요점: 우리 `_internal/versions/` convention 을 물리 계층으로 승격하는 근거.**
- **파일-복제식 배포는 피하라 → claude-flow 반면교사**. 스스로 367개 중복 drift(#1834). **요점: core 를 프로젝트로 복사·생성하지 말고 참조+converter 로.**

---
관련: [04_technical_deep_dive](04_technical_deep_dive.md)(메커니즘 상세) · [06_implementation](06_implementation.md)(채택 결정)
