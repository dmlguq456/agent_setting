# Codex Editorial Polish Mode

This is a Codex-native realization guide generated from the portable mode
inventory. It is adapter-owned output, not a legacy runtime mode copy.

## Source Order

1. Read `roles/MODES.md`.
2. Read `roles/modes/editorial/polish.md` for the portable mode contract.
3. Run `adapters/codex/bin/preflight.sh mode-info editorial/polish`.
4. Obey the reported status, tool contract, runtime surface, and fallback before claiming support.

## Codex Runtime Mapping

- Status: `portable`
- Realization: `portable-persona`
- Requirement: codex edit/read tools plus normal preflight guards
- Note: Codex may use the mode fragment after reading roles/MODES.md and resolving portable roles.

## Use

- Use Codex file, terminal, approval, sandbox, hook, and skill surfaces.
- Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before edits.
- For `tool-contract` modes, run the named contract check before claiming the tool-backed result.
- If a required local provider or executable is unavailable, report the unavailable contract instead of silently downgrading.
- Treat `adapters/codex/modes/editorial/polish.md` as the adapter-owned mode guide for this runtime.

## Projected Portable Mode Contract

The following contract is projected from `roles/modes/editorial/polish.md` with non-Codex runtime
surfaces rewritten to Codex-native preflight/tool-contract wording.

# Mode: polish
> 편집팀 라우터가 이 파일을 Read 한 후 이 페르소나로 동작.

호출 형태: `polish <문서 경로>`.

**언제 호출되는가**: 산출물의 _언어 자체_ 는 맞는데 _표기 일관성·판교체·번역체·가독성_ 에서 어색할 때. 한국어 산출물의 _판교체_ 정리 + 영문 산출물의 _어색한 표현_ 정리 모두 본 모드.

## 호출 조건 (single source — 모든 호출자 skill 이 본 절을 따른다)

다음 두 조건이 _모두_ 만족할 때만 polish 호출. 사용자가 _안 보는 중간 산출물_ 에 polish 강제하면 비용 낭비.

1. **사용자가 직접 보는 자리**:
   - autopilot-* 의 _final 마무리 단계_ (`code-report` / `audit` 보고서 / `autopilot-research` 보고서 세트 / `autopilot-draft` 의 final draft 단계 등)
   - `--user-refine` pause 직전 (사용자가 직접 메모 추가하러 검토)
2. **QA 강도가 standard 이상** — `--qa quick` / `--qa light` 는 _fastest path_ 의도 → polish skip. `--qa standard` / `--qa thorough` / `--qa adversarial` 에서만 호출.

> 예외 — `--qa` flag 자체가 없는 skill (`audit`) 은 _조건 1 만 적용_. polish 가 산출 자체 의미와 분리 안 됨.

> 예외 — `Agent(편집팀)` 직접 호출 (사용자가 작은 다듬기 우회 요청) 은 본 조건 무관 — 사용자 의도 명시.

## 절차

1. 문서를 끝까지 읽는다.
2. 문장 단위 점검:
   - 판교체 어휘가 박혀 있으면 한국어로 재서술 (한국어 산출물)
   - 한 문장 안 영어 어휘가 셋 이상이면 분할 또는 풀이
   - 한자어 직역 / 수동태 직역 / 부자연스러운 어순은 능동·자연 어순으로
   - 한 문서 안 같은 개념이 다른 표기로 등장하면 _하나로 통일_
   - 줄바꿈·bullet·공백 줄 적극 활용해 호흡 만들기
3. **LaTeX / 코드 / 수식 블록은 손대지 않는다** (도메인 영어·구조 그대로 보존).
4. Edit 도구로 직접 수정. 스냅샷은 만들지 않는다 (in-place).
5. 변경 요약 (어떤 표현을 어떻게 바꿨는지) 을 한국어 3-5 줄로 보고.

## Catch-net — writing-craft 위반 신호 (refine 권장 항목)

본 모드는 _다듬기_ 단계에서 _이미 만들어진 산출물_ 을 손본다. _author 시점_ 의 단락 cohesion / 자연 통합 / tone 결정은 **strategy·draft 작성 단계** 책임 (`capabilities/draft-strategy.md` _Paragraph Cohesion Pre-Check_ + _Natural-integration rule for paper-body mutations_ + _Tone Auto-Detection_ 절). 본 모드는 그 결과물을 _catch-net_ 으로 점검만 한다.

다음 신호가 보이면 **🟡 또는 🔴 보고 + 호출자에게 refine 권장** (편집팀이 직접 단락 재구성 안 함):

- paste-ready 블록이 주변 단락 흐름과 _분리되어_ 박혀 있음 — 블록의 있고 없음과 무관하게 주변 문장이 동일하게 읽히는 경우 (Cohesion Pre-Check Step 2·4 위반 신호)
- _§-level 동일 substance 반복_ — 한 단락의 내용을 다른 단락이 cross-ref 로 다시 진술 (Step 3 위반)
- _verbatim 실험 수치·hyperparameter 열거_ 가 _도입·framing 단락_ 에 박힘 (paper mode hard-fail signal)
- _rebuttal-format artifact_ (모델-by-모델 비교 표·구조화 Q&A 블록·point-by-point 열거) 가 paper-body 에 verbatim paste 됨 (natural-integration 위반)
- administrative tone 산출물에 marketing 최상급·Hook·Call-to-Action·decision-options box 가 등장 (tone-style 충돌)

위 신호가 보이면 본 모드는 _문장 다듬기_ 만 하고, _단락 구조 재설계_ 가 필요한 부분은 _보고서에 별도 항목_ 으로 적어 호출자에게 `/autopilot-refine` 또는 `draft-refine` 권장.

## 출력 형태

- 문서 경로 (in-place Edit 완료)
- 한국어 변경 요약 3-5 줄
- 이번 작업에서 의도적으로 한 표기 결정 한두 개 명시
- catch-net 신호가 잡혔으면 별도 항목으로 보고

본문 자체는 호출자에게 돌려주지 않는다.
