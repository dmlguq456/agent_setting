# 04 — Technical Deep Dive

> 4개 핵심 기술 테마: (a) drift-prevention 메커니즘 설계공간, (b) context loading / progressive disclosure, (c) workflow gate 강제 스펙트럼, (d) multi-runtime projection mechanics. 모든 구현 서술은 `cards/*.md` 에 소급하며 카드가 unverified 로 남긴 것은 그대로 표기.

## (a) Drift-Prevention 메커니즘 설계공간

5개 서로 다른 접근이 관측된다. 강도(양방향 divergence 처리력) 순.

| 접근 | 대표 | 동작 | 한계 |
|---|---|---|---|
| **hash-manifest + patch-reapply** | GSD | installer 가 설치 파일 hash 보관 → 사용자 직접 수정 시 hash 불일치 감지 → `gsd-local-patches/` 백업 → `--reapply` 로 새 버전에 로컬 patch 재적용 | installer file-ops line 단위 미검증 (`gsd.md` 미검증) |
| **registry + placeholder-substitution** | spec-kit | `INTEGRATION_REGISTRY`(`_register_builtins()`) SoT + `CommandRegistrar` 가 format별 placeholder 치환 (`$ARGUMENTS`↔`{{args}}`, `{SCRIPT}`) | 로컬 수정 자체 감지는 안 함(계층 resolution 으로 우회) |
| **override-layer 물리 분리** | spec-kit / BMAD / Agent OS | 사용자 수정을 core 와 다른 계층에 격리 — `overrides>presets>extensions>core`(spec-kit), `_bmad/custom/*.toml` 3-layer(BMAD), profile inheritance(Agent OS) | 재설치 시 실제 보존 file-ops 미검증(BMAD·Agent OS) |
| **version / SHA-pin + source 참조** | Claude 공식 | fork 안 하고 marketplace source 참조, `plugin.json` version→marketplace version→git SHA 우선순위, `ref`+`sha` pin, `renames` 마이그레이션 | 양방향 divergence 용 3-way merge **없음**(자인) |
| **snapshot 감사 (사후 탐지)** | claude-flow | MetaHarness 로 config 스냅샷 → 회귀/drift 사후 탐지, `ruflo verify` cryptographic witness | 사전 차단 아닌 사후; 자신도 drift 겪음(#1834) |
| **prose-only LCD** | AGENTS.md | 표현할 machine 기능이 없어 drift 여지 최소 | 실행 기능 0 |

**GSD reapply 의사 흐름** (`gsd.md` §2·특기사항 기반):

```
/gsd-update:
  1. 설치 버전·scope 감지
  2. npm latest 조회 → changelog diff 를 확인 요청 前 표시
  3. GSD-managed 디렉토리 안 사용자 추가 파일 → gsd-user-files-backup/
  4. 각 관리 파일 hash 비교:
       if hash(local) != hash(manifest):   # 사용자가 직접 수정함
           gsd-local-patches/ 에 로컬본 백업
  5. installer 재실행 (새 버전 설치)
  6. --reapply: gsd-local-patches/ 의 diff 를 새 파일에 머지
  # gsd- prefix 밖 파일(custom agent, CLAUDE.md)은 절대 불가침 (소유 경계)
```

**요점**: 우리 harness 의 `core/`→`adapters/*` sync 에 직접 이식 가능한 건 **hash-manifest 계층**뿐이고, 나머지 4개는 "감지 없이 물리 분리로 회피" 하는 열등 대안이다.

## (b) Context Loading / Progressive Disclosure 비교

| 프레임워크 | always-loaded 층 | on-demand 메커니즘 | token 절약 기법 |
|---|---|---|---|
| Claude 공식 | skill name+description(1536자 truncate, budget ~1%) | Level2 body(invoke 시) → Level3 번들파일(navigate 시) | "10,000줄 도메인 지식도 필요 전까지 비용 0" (`claude-code-official-plugins.md` §4) |
| GSD | `AGENTS.md`/`CONTEXT.md` + slash 호출 시 workflow verbatim | `gsd-tools.cjs init <workflow>`; namespace router routing table | **workflow byte-budget**(XL 90KB, Codex 32,768 truncation 정렬); 2-stage routing(67→6 entries); router desc=pipe keyword ≤60자 (`gsd.md` §4) |
| Superpowers | `using-superpowers` bootstrap 만 | description(≤1024자) → body(getting-started ≤150 words) → supporting files | file-per-concern, heavy reference 는 링크만 (`superpowers.md` §3) |
| BMAD | 없음(per-skill) | description frontmatter 로 필요 시; `bmad-help.csv` 경량 catalog | "fresh context window per skill"; CSV+config JSON 만 읽어 catalog dump 회피 (`bmad-method.md` §3) |
| SuperClaude | FLAGS/RULES/PRINCIPLES(MANDATORY) | trigger-based(command/agent/keyword/flag) | `@import` 미사용(descriptive path 참조, 비결정론적) (`superclaude.md` §3) |
| spec-kit | per-agent memory 파일(`CLAUDE.md`/`GEMINI.md`) | slash command 시 템플릿; `constitution.md` | agent-context 를 CLI 밖 script 로 관리 (`spec-kit.md` §3) |

공통 관용구: **"fresh context per agent + file 로 복원"** 이 context rot 방지의 지배 패턴 (`analysis_summary.md` §4-8). DB 예외는 claude-flow(SQLite+HNSW)·SuperClaude(Serena MCP)뿐.

**요점**: 우리 harness 의 always-on bootstrap 최소화 방향은 Superpowers(bootstrap 1개만)·GSD(2-stage routing) 와 정렬 — 특히 GSD 의 **byte-budget 테스트**(`workflow-size-budget.test.cjs`)는 우리가 CLAUDE.md 비대화를 막을 기계적 장치로 참고 가치.

## (c) Workflow Gate 강제 스펙트럼

이분법이 아닌 연속체. *무엇을* 강제하는지가 프레임워크 철학을 가른다 (`analysis_summary.md` §4-7).

```
convention-only ─────────── state-file state machine ─────────── machine-enforced blocking
SuperClaude                 BMAD (sprint-status.yaml)            GSD (capability gates[])
Agent OS (명시적)            spec-kit (check-prerequisites.sh)    claude-flow (hook dispatcher)
                                                                 우리 harness (artifact-guard.sh)
```

- **convention-only**: SuperClaude RULES.md workflow rule("no gating system", design→implement 점프 가능), Agent OS 명시적 "scaffolding without enforcing execution order" (`superclaude.md` §4, `agent-os.md` §4).
- **state-file state machine**: BMAD `sprint-status.yaml` 의 story status(`ready-for-dev`→`in-progress`) + soft `preceded-by` vs hard `required` 구분, `<check>`/`HALT`/`goto` 로직; spec-kit `check-prerequisites.sh` 가 `plan.md` 무조건 required + `--require-tasks` (`bmad-method.md` §4, `spec-kit.md` §4).
- **machine-enforced**: GSD `capabilities/<feature>/capability.json` 의 `gates[]` 가 workflow point(`plan:pre`, `execute:wave:post`)에 `check.query`(`verify.schema-drift`)를 걸고 `blocking:true|false`, CLI(`gsd_run query`)가 집행 — 단 hook 대부분은 soft("advises, not blocks"), blocking 은 schema-gate 등 일부 (`gsd.md` §5).

**gate 대상 차이 (핵심)**: 같은 "machine-enforced" 라도 GSD/우리 harness = 산출물 *생성 순서 불변식*(spec→plan→code), claude-flow = *agent 조율/합의 lifecycle*, BMAD = *story status 전이*. 우리 harness 의 생성-순서 hard-gate 와 가장 가까운 건 GSD capability gate 뿐이고 그마저 대부분 soft (`analysis_summary.md` §5).

**요점**: 우리 `artifact-guard.sh` 의 생성-순서 hard-block 은 조사 대상 중 **가장 강한 순서 불변식 강제** 에 속한다 — 오히려 우리가 차용할 것은 gate 강도가 아니라 GSD 의 `gates[]` 처럼 gate 를 *선언적 manifest 로 외부화* 하는 설계다.

## (d) Multi-Runtime Projection Mechanics

3개 구현 기법 + one-runtime-only 기능의 3층 처리.

**projection 기법 3갈래** (`analysis_summary.md` §4-1):
- **manifest/converter (GSD)**: `capability.json` 이 runtime 표면 계약 선언 — `commandStyle`(claude=slash-hyphen, codex=shell-var), `hooksSurface`, `artifactLayout.converter`(`convertClaudeCommandToCodexSkill`), `embeddingMode`(claude=imperative, codex=declarative), `dispatch.maxDepth`(claude=5, codex=1). installer 가 core Claude-command 를 각 표면으로 변환 (`gsd.md` §7).
- **registry/placeholder (spec-kit)**: base class(`MarkdownIntegration`/`TomlIntegration`/`YamlIntegration`/`SkillsIntegration`)별 `registrar_config` + placeholder 치환 (`spec-kit.md` §1).
- **config-driven 파일복제 (BMAD/claude-flow/ruler)**: target_dir 선언 → 복사. 단순하나 claude-flow(#1834)처럼 복제본 drift 취약.

**one-runtime-only 기능(hook 등)의 3층 처리** (`multi-harness-projection.md` §종합답 — 핵심):

| 전략 | 도구 | 동작 |
|---|---|---|
| (i) **skip + warning** | ruler | Copilot 에 없는 tool 어휘 silent drop; native subagent 없으면 skip+warning (보수적) |
| (ii) **event-vocabulary 정규화 + tool별 재작성/plugin 컴파일** | rulesync hooks | canonical camelCase 1회 작성 → Claude/Codex/Gemini=PascalCase, **OpenCode/Kilo=JS plugin emit**(`.opencode/plugins/rulesync-hooks.js`), Copilot=자체 rename |
| (iii) **prompt-level simulation** | rulesync `s/command` | native primitive 없는 곳에 텍스트 컨벤션(`s/your-command`, "Call your-subagent to…")으로 대체 |

**결정적 관찰**: **어느 도구도 hook 같은 실행 격리를 없는 runtime 에서 진짜 재현하지 못하며** 최선이 (ii)·(iii) 관례적 대체다 (`multi-harness-projection.md` §3). 우리 harness 의 core→adapter parity 도 이 한계를 공유하는지 자체 점검 필요 — Codex adapter 에 Claude hook 을 투영할 때 (ii)/(iii) 수준으로 떨어지는지.

**요점**: 우리 harness 는 GSD manifest/converter 급 표현력을 지향하되, parity 불가 지점은 **silent drop 이 아니라 명시적 warning(ruler 방식)** 으로 노출해 capability loss 를 감춰선 안 된다.

---
관련: [03_vendor_comparison](03_vendor_comparison.md) · [05_deployment](05_deployment.md) · [06_implementation](06_implementation.md)
