### Step 5b: Cross-doc invariant scan (QA 정의 & family-wide 규칙)

> 각 SKILL.md `## Default Invocation Rule` 은 _그 SKILL.md 안에서만_ 의미를 가지고 README 에 모으지 않음 (README §6 운영 룰은 _runtime adapter bootstrap 을 가리킴 한 단락_). autopilot-* SKILL.md 의 trigger 신호·default 옵션·override 는 adapter 의 일반 패턴 + 각 SKILL.md 의 skill-specific 정보로 분리.

QA level / model role 표기 / family-wide invariant 은 **`<agent-home>/core/CONVENTIONS.md`** 가 단일 source of truth. 각 SKILL.md / README / `roles/README.md` / `adapters/claude/agents/*.md` 의 QA 표 wording 은 본 문서와 의미상 일치해야 함. Concrete model name 은 adapter 문서에서만 canonical 이며, 공통 문서에서는 role 의미와 분리한다.

#### 5b-1. Canonical 정의 로드

```bash
# Read core/CONVENTIONS.md fully; then parse:
#   §1.1 5단계 공통 정의 표 → QA wording (canonical)
#   §2 Model Role 표기 → portable model role 정의 + adapter mapping requirement
#   §3 Hard Cross-Doc Invariants → invariant rule list
```

이로부터 5단계 정의 (quick/light/standard/thorough/adversarial) 의 _구성_ 을 추출 (Quality reviewer / Fact-checker / External adversary 컬럼 wording).

#### 5b-2. 모든 .md 파일에서 QA wording 추출

대상 파일:
- `<agent-home>/adapters/claude/skills/*/SKILL.md`
- `<agent-home>/adapters/claude/skills/*/README.md`
- `<agent-home>/skills/*/SKILL.md` and `<agent-home>/skills/*/README.md` (compatibility refs, parity/drift check)
- `<agent-home>/capabilities/README.md`
- `<agent-home>/roles/README.md`
- `<agent-home>/roles/MODES.md`
- `<agent-home>/adapters/claude/agents/*.md`
- `<agent-home>/README.md`

각 파일에서 다음 패턴 grep:
- `adversarial` 정의 문장 (예: `adversarial = ...`, `Adversarial | ...`, `adversarial.*(external|Codex)`)
- `quick`/`light`/`standard`/`thorough` 정의 표 행
- "fact-checker" 적용 여부
- model role 표기 (`fast reviewer`, `deep reviewer`, `external adversary`, 가변 표기). `opus` / `sonnet` 같은 concrete name 은 Claude adapter mapping 또는 agent frontmatter 설명일 때만 허용

#### 5b-3. Invariance 검사 (drift 보고)

각 추출된 wording 을 canonical 정의와 비교. 다음 drift 패턴을 _하드 검사_:

| Invariant | 검사 패턴 | drift 시 보고 |
|---|---|---|
| **adversarial = thorough + external adversary** (+ research/doc 트랙은 claim-verify) | `adversarial.*standard.*(Codex|external)` 또는 `adversarial.*=.*standard` | 🔴 `잘못된 정의: adversarial base 는 thorough + external adversary (standard 아님). research/doc 트랙은 + 연구팀 claim-verify` |
| **autopilot-code 는 fact-checker 없음** | autopilot-code/SKILL.md or autopilot-code/README.md 에서 `fact-checker` 언급 (단, "doc/research 에만" 이라는 negative 안내는 OK) | 🔴 `code 파이프라인은 fact-checker 미적용` |
| **autopilot-* + analyze-user adversarial 지원** | autopilot-code / autopilot-draft / autopilot-research / autopilot-refine / analyze-user 의 `--intensity` argument-hint 에 `adversarial` 누락 또는 verification rigor 를 intensity 와 별개 축(`--qa`)처럼 설명 | 🔴 `adversarial 지원은 유지하되, autopilot-* default thorough 강제 금지. intensity가 graph/depth를 고르고 verification rigor는 intensity에서 파생 (별도 --qa 축 없음)` |
| **quick 은 refine skip + 1라운드 강제 종료** | quick 정의에서 위 둘 중 하나 누락 | 🟡 `quick 정의 incomplete` |
| **`--no-fact-check` / `--no-style-audit` 는 autopilot-refine·audit 전용** | 다른 skill 의 argument-hint 에 노출 | 🔴 `해당 flag 는 refine·audit 외 노출 금지` |

#### 5b-4. 보고 형식

drift 발견 시 Step 7 final report 에 별도 섹션:
```
[QA invariant drift]
🔴 skills/autopilot-refine/SKILL.md:46 — `--qa thorough`를 default graph처럼 설명함 (canonical: `intensity`가 graph/depth를 선택하고 verification rigor는 intensity에서 파생 — 별도 --qa 축 없음)
🟡 skills/autopilot-research/SKILL.md:632 — quick 정의에 'refine skip' 명시 누락
```

자동 fix 정책 (CONVENTIONS.md §4):
- **default (report-only)**: drift 보고만, 수정 안 함
- **`--auto-fix`** flag 시: CONVENTIONS.md §3 hard invariants 위반은 canonical wording 으로 강제 교체. 단 _wording 자체_ 가 다를 경우 (의미 동일·표현 차이): skip (사람 결정). _의미가 다른_ 명백한 drift 만 propagate.
- **`--auto-fix --dry-run`**: 미리보기 (실제 write 안 함)
- `--check` 모드에서는 invariant drift 만 보고하고 종료 (auto-fix 자동 적용 안 함).

> **새 invariant 추가**: CONVENTIONS.md §3 에 한 행 추가하면 sync 시 자동 검사 list 에 포함.

### Step 5c: Cross-doc skill name reference scan (rename drift 차단)

**왜 신설** (2026-05-25): autopilot-app → autopilot-spec rename 자리에서 본 step 부재로 SKILL.md SHA 만 갱신되고 _README mermaid 다이어그램·다른 SKILL.md 의 cross-reference_ 가 그대로 통과. sync 가 _자동 잡았어야_ 자리. 본 step 이 _skill 이름 rename_ + _산출물 폴더 명 변경_ 자리의 drift 자동 검출.

#### 5c-1. Skill / agent name 인벤토리 추출

```bash
# 현재 진실 (entry point list)
AGENT_HOME="${AGENT_HOME:-${CLAUDE_HOME:-$HOME/.claude}}"
SKILLS=$(ls -d "$AGENT_HOME"/adapters/claude/skills/*/  | xargs -n1 basename | sort)
AGENTS=$(ls "$AGENT_HOME"/adapters/claude/agents/*.md   | xargs -n1 basename .md | sort)
```

#### 5c-2. Cross-doc reference grep

전체 `<agent-home>/` 안 `*.md` / `*.json` / `*.yaml` 에서 다음 패턴 grep:

| 패턴 | 검출 |
|---|---|
| `autopilot-X` (X = 알파벳·하이픈) | autopilot-* skill name reference |
| `/autopilot-X` | slash 명령 reference |
| `\bX-Y\b` (X = app / code / design / draft, Y = init / spec / build / refine / 등) | sub-skill name reference |
| `Agent\(X팀` 또는 `Agent\(X-team` | agent reference |

각 reference 의 _name 부분_ 추출 후 인벤토리 (5c-1) 와 대조:

| drift 종류 | 보고 |
|---|---|
| **폴더 부재 skill name reference** | 🔴 `<file>:<line> — '<missing-name>' reference 발견, skill 폴더 없음. rename 후 정정 누락?` |
| **slash 명령 (`/autopilot-X`) 의 X 가 폴더 부재** | 🔴 `<file>:<line> — /autopilot-<missing> 호출 reference` |

#### 5c-3. README 트랙 체인 ↔ skill list 일관성

README 는 mermaid 를 안 쓰고 _4 트랙 텍스트 화살표 체인_ (```text 코드 블록 4 개) 으로 흐름을 보인다 (4a). 체인에 등장하는 skill 만 검사 대상 — `audit` / `post-it` / `analyze-user` 는 _의도적으로 체인 밖_ (사후 점검·메모·cross-project 프로필이라 트랙 체인에 안 들어감, 본문 quote 가 대신 다룸).

`<agent-home>/README.md` §4 의 \`\`\`text 코드 블록 4 개 추출 후 `autopilot-X` / `analyze-project` 토큰 파싱:

- _트랙 체인 skill_ (analyze-project · autopilot-research · autopilot-draft · -refine · -apply · -spec · -code · -lab · -design · -ship) 이 체인에 등장하나
- 부재 시: 🟡 `README 4 트랙 체인에 '<missing-skill>' 누락 — 보강 권장`
- `audit` / `post-it` / `analyze-user` 는 _체인 밖이 정상_ — 누락 보고 X
- mermaid 블록 발견 시: 🟡 `README 에 mermaid 잔존 — 텍스트 체인으로 전환 (4a)` (재설계 후 mermaid 안 씀)

#### 5c-4. 산출물 폴더 컨벤션 일관성

`CONVENTIONS.md §6.5 산출물 폴더 컨벤션 정리` 표 파싱 → 각 skill 의 _산출물 폴더 명_ 추출 (예: `spec/`, `documents/<date>_<name>/`).

다른 SKILL.md 본문에서 _다른 skill 의 산출물 폴더 reference_ 추출 (예: autopilot-spec 의 본문이 autopilot-code 의 산출물 폴더 가리킴 자리).

| drift 종류 | 보고 |
|---|---|
| **CONVENTIONS 매핑 표와 SKILL.md 산출물 wording 불일치** | 🔴 `adapters/claude/skills/<x>/SKILL.md 의 산출물 '<wrong>' — CONVENTIONS §6.5 매핑은 '<correct>'` |
| **다른 SKILL.md 의 _A skill 산출물 폴더 reference_ 가 매핑 표와 불일치** | 🔴 `adapters/claude/skills/<other>/SKILL.md:<line> — '<x>' 산출물을 '<wrong>' 으로 reference (매핑: '<correct>')` |

#### 5c-5. 자동 fix 정책

- **default (report-only)**: drift 보고만, 수정 안 함
- **`--auto-fix`** flag 시:
  - 폴더 부재 skill name → 자동 정정 불가, 사용자 결정 (rename 매핑은 사람이 판단)
  - 산출물 폴더 명 — CONVENTIONS.md §6.5 canonical 로 자동 정정
- **`--check` 모드**: drift 만 보고하고 종료

### Step 5d: 에이전트 엔지니어링 매뉴얼 동기 검토 (autopilot-refine 경유)

**왜 신설** (2026-06-11): 이 설정 repo 의 artifact root(`<agent-home>/.agent_reports/`) 아래 `documents/{date}_agent-engineering-manual/draft/draft.md` 는 업계 원칙 ↔ 우리 세팅을 _라이브 파일 anchor_ 로 매핑한 참조서 (autopilot-draft 산출물). skills/agents/지침이 바뀌면 매뉴얼 2부(세팅 매핑)·anchor 가 조용히 stale 해지는데 이를 잡는 자리가 없었다. sync 가 drift 를 보는 자리에서 매뉴얼 검토를 **항상** 같이 본다.

- Step 3 의 변경(신규·변경·삭제) ≥ 1 이면 final report 에 매뉴얼 검토 항목을 항상 포함 — 변경된 skill/agent 명단을 들어 `/autopilot-refine` (대상: agent-engineering-manual draft) 검토 제안. 변경 0 이어도 매뉴얼이 last sync 이후 갱신 안 됐고 지침 파일(runtime adapter bootstrap / core/WORKFLOW / core/CONVENTIONS)이 바뀌었으면 동일 제안.
- 매뉴얼은 autopilot-draft 산출물 — **직접 Edit 금지**, 수정은 소유 스킬 `autopilot-refine` 경유 (버전 snapshot·changelog 보존).
- `--check` 모드 포함 모든 모드에서 _보고만_ — refine 실행 자체는 사용자 컨펌 후 (ceremony 분류상 자동 invoke 아님).

