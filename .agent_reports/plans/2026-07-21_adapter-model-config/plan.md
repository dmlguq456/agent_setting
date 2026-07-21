---
slug: adapter-model-config
date: 2026-07-21
mode: dev (library/cli — harness infra)
intensity: standard
status: planning
spec_significance: within-spec (SD-22 delegates concrete model to adapter; no PRD amendment)
worktree: /home/Uihyeop/agent_setting-wt/adapter-model-config
canonical_artifact_root: /home/Uihyeop/agent_setting/.agent_reports
base_head: eda11cd4
---

# adapter-model-config — 어댑터 concrete 모델/effort를 단일 config SoT로 통합

## 0. 목표 (한 줄)

세 어댑터(codex/claude/opencode)의 concrete 모델 ID·effort 기술을 **어댑터별 단일 config SoT**에
국한하고, 나머지 전 표면(model-map·생성기·tomls·문서·라이프사이클)은 그 config에서 **결정론적으로
파생**하게 리팩터한다. config 밖에 concrete 모델 ID가 새면 **fail-closed 가드**로 차단한다.

## 1. 확정 값 스킴 (사용자 결정 2026-07-21)

| 티어 | 역할 | codex | claude | opencode |
|---|---|---|---|---|
| **deep** | deep maker·reviewer·editor, external adversary, fast implementer | `gpt-5.6-sol`/high (소진→light) | `fable`/high (소진→캐스케이드→opus) | `GLM 5.2` |
| **light** | balanced orchestrator, fast reviewer·writer·tool | `gpt-5.6-luna`/medium | `sonnet`/medium | `DeepSeek Pro` |
| **mini** | 단순 요약·반복(turn-nudge 등) | `gpt-5.4-mini`/low | `haiku`/low | `Flash` |

- **codex: `gpt-5.6-terra` 완전 제거.** fast implementer(구) terra → **deep(SOL)**, balanced orchestrator(구) terra → **light(LUNA)**.
- **claude: Opus는 상시 티어 아님** — deep(Fable) capacity-failover 전용. deep 캐스케이드 =
  `fable/max → fable/xhigh → fable/med → opus/max → opus/xhigh → opus/med → sonnet/high → sonnet/med`
  (effort 우선: 모델 교체 전 effort부터 강등).
- **라이프사이클**: turn-nudge=**mini**, 세션종료 curate=**light** (사용자 조정 2026-07-21).
- 원칙: 모델 티어 교체보다 effort 티어 조정 우선(memory: effort-tier-over-model-tier).

## 2. 설계 — config SoT + 결정론적 파생 + 가드

### 2.1 config 포맷 결정 = **POSIX-sh-sourceable flat conf** (`adapters/<adapter>/config/models.conf`)

근거: 세 어댑터의 model-map/role-map/distill-worker가 전부 POSIX `sh`이고 **매 dispatch마다 호출되는
hot path**다. toml을 쓰면 매 호출에 파서(파이썬 subprocess)가 붙어 비용·복잡도 증가. flat
`KEY=value`는 sh가 `.` 로 source하고 python이 그대로 파싱 → **포맷 불일치 0, 단일 SoT 진짜 성립**.
(toml 검토했으나 hot-path sh-parseability 때문에 기각.)

스키마 (예 — codex):
```
# adapters/codex/config/models.conf — 이 어댑터 concrete 모델의 유일한 선언처
TIER_DEEP_MODEL=gpt-5.6-sol
TIER_DEEP_EFFORT=high
TIER_DEEP_FAILOVER=light          # SOL 소진 시 강등 대상
TIER_LIGHT_MODEL=gpt-5.6-luna
TIER_LIGHT_EFFORT=medium
TIER_MINI_MODEL=gpt-5.4-mini
TIER_MINI_EFFORT=low
# 역할 → 티어
ROLE_DEEP="deep maker|deep reviewer|deep editor|deep orchestrator|external adversary|fast implementer"
ROLE_LIGHT="orchestrator|external adversary orchestrator|fast reviewer|fast fact checker|fast writer|fast tool worker"
# 라이프사이클 → 티어
LIFECYCLE_CURATE=light
LIFECYCLE_NUDGE=mini
```
claude conf는 추가로 `TIER_DEEP_FAILOVER_CASCADE="fable/max fable/xhigh fable/med opus/max opus/xhigh opus/med sonnet/high sonnet/med"`.
opencode conf는 native-owned 성격 반영 — 기본값 placeholder(`opencode-default` 대체어) + `NATIVE_OWNED=1` 선언.

### 2.2 파생 (손으로 쓰는 곳 0)

| 표면 | 지금 | 후 |
|---|---|---|
| `model-map.sh`/`role-map.sh` | 인라인 case 리터럴 | `. config/models.conf` 후 `${ENV:-$TIER_x_MODEL}` |
| codex `sync-native-agents.py` PROFILE_CONFIG | 별도 dict | config 파싱 (dict 제거) |
| codex `agents/*.toml` | 생성됨 | config 파생 생성 (경로 유지) |
| `distill-worker.sh` / `mem-distill-worker.sh` | 인라인 default | `${ENV:-$LIFECYCLE_x}`→티어→모델 |
| README/ADAPTATION 모델표 | prose 중복 | `<!-- GENERATED: models.conf -->` 생성영역 |

### 2.3 fail-closed 가드 (`tools/check-model-config.sh` 신규 또는 check-adaptation-boundary 확장)

- 규칙: 알려진 concrete 모델 토큰(`gpt-5.x`, `gpt-5.4-mini`, `\bfable\b`, `\bopus\b`, `\bsonnet\b`, `\bhaiku\b`,
  `GLM`, `deepseek`, `flash`)이 **`adapters/*/config/models.conf` + 생성영역(`<!-- GENERATED -->`) 밖**의
  어댑터 소스/문서에 나타나면 **비정상 종료**.
- 제외(오탐 방지): statusline/fleet 모델 **색상 팔레트**(display용), 테스트 fixture, portable role 이름
  (`deep maker` 등 티어명 아님), 본 plan/문서의 인용.
- 배선: write-guard/preflight 또는 CI 검사에 편입. 재생성 idempotent 검사도 포함.

### 2.4 포터블 계약 강화 (P0)

`roles/README.md`의 "Adapter Requirements"의 *"어떤 concrete model이 portable role에 매핑되는지 문서화"*
요구를 **"단일 config SoT + 결정론 가드"로 강화**(신설 아님). core/ADAPTATION.md 모델-role 문단과 정합.

## 3. 표면 인벤토리 (실측 완료)

### codex
- `adapters/codex/bin/model-map.sh` — case: SOL/TERRA/LUNA + env fallback
- `adapters/codex/bin/sync-native-agents.py` — `PROFILE_CONFIG` dict (line ~19) + `codex_config()` 기본값 line 192
- `adapters/codex/agents/*.toml` — 8개 생성물 (model= 라인)
- `adapters/codex/bin/distill-worker.sh` — line 48: increment=gpt-5.4-mini, curate=gpt-5.5 (env override 있음)
- `adapters/codex/README.md`(≈207), `ADAPTATION.md`(449-451, 644-649 라이프사이클)

### claude
- `adapters/claude/bin/model-map.sh` — case: deep→opus/high, balanced→sonnet/medium (env fallback). **haiku 티어 없음 → 추가 필요**
- `adapters/claude/bin/dispatch-headless.py` — `role_map()`가 model-map.sh 호출 (변경 불요, 소스만 바뀜)
- `adapters/claude/agents/*.md` — frontmatter `model:` (memory-scout=haiku, 개발팀=sonnet 등)
- `adapters/claude/bin/mem-distill-worker.sh` — increment=claude-sonnet-4-6, sessionend=claude-opus-4-8 (env override)
- `adapters/claude/README.md`(79-88 역할표), `ADAPTATION.md`(6-8, 92-93, 212-231)

### opencode
- `adapters/opencode/bin/role-map.sh` — AGENT_MODEL_FAST/BALANCED/DEEP/EXTERNAL, opencode-default fallback
- `adapters/opencode/AGENTS.md` — native-owned 명시
- `adapters/opencode/agents/*/*.md` — portable role note (concrete 없음)

## 4. 실행 순서 (checklist.md 참조)

1. **P0** 포터블 계약 강화 (roles/README, core/ADAPTATION 정합)
2. **codex** (참조 구현): models.conf 신설 → model-map.sh config-source → PROFILE_CONFIG 제거·config 파싱 → tomls 재생성 → distill-worker config화 → docs 생성영역
3. **claude**: models.conf(deep/light/mini, 캐스케이드) → model-map.sh(haiku 티어 추가) → agent frontmatter 생성 정합 → mem-distill-worker config화 → docs
4. **opencode**: models.conf(GLM5.2/DeepSeek Pro/Flash 또는 native-owned) → role-map.sh config-source → AGENTS.md
5. **가드**: check-model-config.sh 신규 + 배선 + 재생성 idempotent
6. **테스트 정합**: capacity test(terra 참조), check-adaptation-boundary(gpt-5.4-mini 참조) 갱신

## 5. 검증 계획 (code-test)

- L1: 세 model-map/role-map이 config 값을 정확히 반환 (역할별 spot-check, terra 부재 확인)
- L2: sync 재실행 idempotent (tomls diff 0), 생성영역 재생성 idempotent
- L3: 가드가 config-외 concrete ID를 fail-closed (positive: 일부러 문서에 opus 심으면 실패 / negative: 정상 트리 통과)
- L4: 기존 테스트 스위트 회귀 없음 (capacity test, check-adaptation-boundary, dispatch tests)

## 6. 범위 밖 / 리스크

- **범위 밖**: dispatch-defaults.yaml capability×stage effort/model 선언(SD-66/68 개정) = 이후 spec 트랙(P2).
- **리스크**: (a) claude agent frontmatter가 생성물이 아니라 수기면 config-파생 배선에 생성 단계 추가 필요 — 실측 후 결정.
  (b) opencode 실제 provider/model-id 문자열(GLM 5.2/DeepSeek Pro/Flash의 정확한 provider prefix)은 opencode
  native config 규약 확인 필요 — 불명이면 placeholder + native-owned로 정직 처리. (c) capacity-failover 캐스케이드의
  SD-59 배선 연결은 데이터 제공까지만 (본 사이클), 실제 소진 감지 로직 변경은 최소화.
