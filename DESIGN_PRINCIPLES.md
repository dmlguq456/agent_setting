# Autopilot Design Principles

> `~/.claude/` 의 _아키텍처 헌법_ — autopilot family 가 어떻게 분리되고 어떻게 협력하는지의 single source.
>
> 자매 문서 (각자 단일 출처, 본 문서는 포인터만):
> - `CONVENTIONS.md` — QA 5단계 / agent model 표기 / 산출물 폴더 컨벤션 (§5) / hard invariants
> - `CLAUDE.md` §0~§3 — 작업 라우팅 (spec-first 파이프 + autopilot-* 호출 Pre-check) + 메인 Claude 행동 메타 원칙 (응답 규율·pause/자율·후속 단계)
>
> 본 문서는 _구조와 행동의 골격_ 만 담고, 정의·정책·운영 wording 은 위 자매 문서로 위임.

---

## 1. 3-Tier Role Separation

| Tier | Role | 예 | Anti-pattern |
|------|------|-----|--------------|
| **Orchestrator** | Deterministic state machine. 라우팅·gate·verdict 만, content 안 봄. | `autopilot-code` / `autopilot-draft` / `autopilot-research` / `autopilot-refine` 의 SKILL.md 본체 | Orchestrator 가 file content 읽기·요약·판단 |
| **Skill** | Expert capability module. WHAT + verification loop 정의. | `init-plan` · `execute-plan` · `run-test` · `init-doc-strategy` · `refine-doc` 등 | Skill 안에 orchestration 로직 (다른 skill 호출 chain, QA budget) |
| **Agent** | Persona with tools. Skill 안에서 실제 작업 수행. | `기획팀` · `품질관리팀` · `연구팀` · `편집팀` · `테스트팀` · `개발팀` · `탐색팀` · `codex-review-team` | Agent 가 verbose 결과를 orchestrator 로 반환 |

> **이름 충돌 주의**: 본 절의 _3-Tier_ 는 _역할 분리_. §4 의 _3-tier T1/T2/T3_ 는 _산출물 가시성 분리_. 같은 숫자지만 다른 layer.

### Interface Contract

```
Orchestrator → Agent:  file paths + 1-line task directive
Agent → Orchestrator:  file path + verdict token (한 줄)
Agent ↔ Agent:         file system 통해 (B 가 A 가 쓴 파일을 read)
```

Orchestrator 는 _내용을 매개하지 않는다_ — 오로지 path 만 전달.

### "No Read" 의 범위

이 규칙은 **orchestrator 에만** 적용. Skill 본문과 그 안 agent 는 file 을 자유롭게 read — orchestrator 는 delegate, skill·agent 는 execute.

### Stage 통합 orchestrator 의 예외

orchestrator 가 _단일 expert flow_ 만 다루는 경우 (예: `autopilot-refine` Stage A~E — investigate · plan · diff preview · apply · report 가 한 흐름) sub-skill 분리 비용이 커, orchestrator 가 직접 file read·Edit 해도 헌법 위반 X. _sub-skill 분리_ 는 _두 개 이상의 expert capability_ 가 모일 때만 의미 있고, 단일 expert flow 는 orchestrator-also-execute 가 정당.

같은 원칙이 `final-report` 의 _다른 artifact dir (`analysis_project/code/`) 보강 write_ 같이 _자기 책임의 자연 확장_ 자리에도 적용 — sub-skill 책임 범위가 자기 폴더에 한정된다는 _엄격 해석_ 은 헌법 의도 아님. 신규 sub-skill 도입 시 _분리해야 할 expert capability 가 둘 이상인가_ 만 점검하면 충분.

---

## 2. Default Behavior — Autopilot 정신

family 의 모든 멤버는 confirm 없이 pipeline 을 끝까지 돌린다. 사용자가 명시할 때만 멈춘다.

- `--user-refine` / `--confirm` 같은 pause flag 는 **사용자가 직접 typed 했을 때만** 켠다. 메인 Claude 가 _신중을 위해_ 임의 추가 금지.
- `--qa thorough` / `--qa adversarial` 같은 비싼 옵션도 명시했을 때만. default 는 skill 별 권장값 — CONVENTIONS.md §1.4 매트릭스.
- 실패 시 fail loudly + `pipeline_summary.md` 미해결 기록. 다음 호출에서 `--from <stage>` 재개.

**Why**: 사용자가 _명시 요청_ 을 했는데 메인 Claude 가 _신중을 위해_ 라며 confirm 단계를 추가하면 작업이 한 turn 지연되고 "이미 했어?" 같은 follow-up 으로 갈등이 누적. high-stakes 일수록 사용자가 _직접_ pause 를 거는 게 자연스럽다.

**강제 위치**: CLAUDE.md 응답 원칙 §4 (args 구성 단계 차단) + 각 SKILL.md `--user-refine` 절 default false.

---

## 3. Implicit Input Discovery

입력 자료는 _프로젝트 컨텍스트 내부의 영속 산출물_ 에서 자동 발견한다.

- `.claude_reports/analysis_project/{code,paper,doc}/*` — analyze-project 산출물
- `.claude_reports/research/{topic}/*` — autopilot-research 산출물
- 외부 raw 자료는 `analyze-project --mode {code|paper|doc}` 으로 먼저 영속화 → 이후 skill 이 fuzzy match 로 implicit 인지

**Why**: 한 세션 한 프로젝트의 단순한 가정 (cwd = working dir) 이 cognitive cost 를 낮추고, 영속 산출물 재활용성을 높인다. cross-project 작업은 `cd <other>` 후 별도 세션.

---

## 4. Artifact Convention — 3-tier T1/T2/T3

Artifact 폴더 안의 _가시성 분리_. 상세는 CONVENTIONS.md §5 single source.

| Tier | 위치 | 예 |
|---|---|---|
| **T1** Primary | root | `pipeline_summary.md`, `draft/`, `plan/` |
| **T2** Secondary | named subdir | `strategy/`, `analysis/`, `dev_logs/`, `test_logs/`, `cards/` |
| **T3** Tertiary | `_internal/` 하위 | review logs, version 스냅샷, raw scan metadata |

### Minor vs Major 변경

같은 artifact 의 후속 변경도 두 layer 분리:

| Tier | 처리 | 추적 |
|---|---|---|
| **Minor** (default) | 직접 Edit | `pipeline_summary.md` 안 minor log entry |
| **Major** (3-criteria — 사용자 명시 / 구조적 ≥200 줄 / 외부 검토 직전) | `/autopilot-refine` ceremony | snapshot + 통합 history + QA |

누적 minor 5건 도달 시 `/audit` chat alert → audit 이 dual-perspective (vs last major + vs universal principles) batch 점검.

상세 — `autopilot-refine/SKILL.md` Default Invocation Rule + CLAUDE.md 도메인 트리거 표 row 2.

---

## 5. Quality Gates

QA loop 는 _skill 안에서 닫힌 loop_ 으로 돌고, orchestrator 는 verdict token 만 본다.

- **QA 5단계** (quick / light / standard / thorough / adversarial) — CONVENTIONS.md §1 single source. wording / Skill 별 매트릭스 / opt-out flag 그곳.
- **Fact-checker** — doc / research / refine 한정 (code 는 ground-truth 가 코드 자신이라 fact-check 무의미). `--no-fact-check` 단독 skip 가능 — autopilot-refine · audit 전용, 다른 skill 노출 시 drift.
- **Natural-integration rule** (paper mode 한정) — reviewer 의견 → 본문 mutation 옮길 때 표·enumeration 통째 paste 금지. 1~2 문장 in-line rewrite 가 안 되면 drop 또는 Appendix. 4-step Paragraph Cohesion Pre-Check (substance 중복 / paragraph axis / cross-section redundancy / EDIT·REPLACE·INSERT·DROP 분류) 가 mechanical INSERT 사전 차단. 상세 — `init-doc-strategy/SKILL.md` paper mode + `autopilot-draft/SKILL.md` Step 4.1.

**Why**: QA 가 orchestrator 에 박혀 있으면 skill 마다 budget 정책이 어긋남. Skill 안 닫혀 있어야 _expert + verification_ 한 단위가 reuse 가능. fact-checker 의 _verbatim 대조_ 와 quality reviewer 의 _구조 판단_ 은 다른 layer 라 parallel.

---

## 6. Output Surface — 사용자 향 산출물의 일관성

사용자가 직접 보는 markdown 산출물은 _내용 정확성_ 만 아니라 _읽기 호흡_ 까지 책임진다. 전담 부서 — **편집팀** (editorial-team, opus).

- 모드 3종: A 옮기기 (영문 ↔ 국문) / B 다듬기 (언어 무관, 판교체 + 영문 어색한 표현 모두) / C 점검만
- 판교체 회피 — 한국어 산출물에서 영어 어휘를 한국어 어순에 그냥 박지 않는다. 도메인 영어와 정착 외래어만 영어로, 나머지는 한국어로. 매핑 표 — `agents/editorial-team.md`
- 적용 범위 — 사용자가 직접 보는 _모든_ .md 산출물 (doc 한정 X). autopilot-code 의 final-report, audit 보고서, autopilot-refine 결과, pipeline_summary 등

**메인 Claude 응답 자체** 의 메타 원칙은 별개 layer — CLAUDE.md §0~§3 single source (§0 작업 라우팅: spec-first 파이프 + autopilot-* 호출 Pre-check·컨펌 · §1 응답 규율: 판교체 회피·출력 자제·동사 약속어 self-check · §2 pause flag 비자동·자율 진행 · §3 후속 단계 자동).

**Why**: 산출물 품질만 좋고 응답 / 가독성이 부자연스러우면 사용자 짜증이 누적. 편집팀이 _마지막 한 번_ 의 다듬기를 책임지고, CLAUDE.md 응답 원칙이 _매 turn_ 의 메타 self-check.

---

## 7. Memory Layers

per-project 메모는 두 layer 분리.

| Layer | 위치 | 갱신 주체 | 용도 |
|---|---|---|---|
| **사용자 통제** | `<cwd>/.claude_reports/NOTES.md` (1 파일 5 카테고리) | `/notes` 명령으로만 (Claude 자동 X) | conventions / external resources / open threads / decisions / next session hints |
| **Claude 자동** | `~/.claude/projects/*/memory/MEMORY.md` + `feedback_*.md` / `reference_*.md` | Claude 가 feedback 인지 시 자동 누적 | 사용자가 _명시 지적_ 한 패턴 자동 학습 |

세션 시작 시 CLAUDE.md 도메인 트리거 표 row 4 가 `cwd/.claude_reports/NOTES.md` 자동 Read.

**Why**: 자동 메모리가 모든 feedback 을 누적하면 사용자가 _명시적으로 박아두고 싶은_ 정보 (코딩 컨벤션 · 외부 자원 link · 미해결 thread) 가 noise 에 묻혀 보인다. layer 분리 후 우선순위 명확.

---

## 8. Performance Preservation

효율 ≠ corner cutting. 줄어드는 것은 _orchestrator 의 중복 reasoning_ 이지 _verification 의 깊이_ 가 아니다.

- 유지: QA round 수 / agent prompt 풍성함 / verification step
- 줄임: orchestrator 가 agent 작업을 다시 읽고 요약하는 중복 / context 에 결과 본문이 누적되는 노이즈
- 결과 흐름: file 통해 (verdict 만 token)

---

## 부록 — 도입 이력 (간략)

본 문서의 각 절이 어떤 incident 에서 결정됐는지 git log 기반 압축 reference. 상세 narrative 는 `git log --oneline` + 각 SKILL.md 의 `## Why` 절.

| 절 | 도입 incident · key commit |
|---|---|
| §1 3-Tier role | 초기 autopilot family 설계 — orchestrator 가 file 읽고 reasoning 하던 시기 → state machine 으로 분리 |
| §2 Autopilot 정신 | `782ccf6` autopilot-refine default 자동 apply / `2058325` user-refine opt-in only (2026-05-21 사용자 지적) |
| §3 Implicit discovery | `444616a` analyze-project cwd default / `d8f42cd` `--format-ref` 제거 / `215fc23` legacy cleanup |
| §4 T1/T2/T3 + Minor·Major | 초기 SKILL_OUTPUT_CONVENTION 도입 → 2026-05-21 CONVENTIONS.md §5 흡수 / `56708c4` minor vs major + dual-perspective audit |
| §5 Natural-integration | `bf8d565` rebuttal 표 본문 paste 거부 (2026-05-19 ICML camera-ready M11/M15 incident) + 2026-05-20 M8/M9 Paragraph Cohesion Pre-Check 4-step |
| §6 편집팀 + 응답 원칙 | `3f5a48c` translation-team 신설 → `cfb0e12` editorial-team rename + scope 확장 / `bf8d565` 응답 원칙 §3 / `2058325` §4 / `3f5a48c` §1 (판교체) |
| §7 Memory layers | `60f141a` `/notes` skill 신설 — 사용자 통제 layer 와 자동 메모리 분리 |
