## Sub-Actions

### `/post-it` (인자 없음) = `show`
`python3 <agent-home>/tools/memory/mem.py recall "" --tier working --scope project` 로 현 cwd 의 working 레코드를 preview 표시. 레코드 없으면 `/post-it add` 안내.

### `/post-it add <category> <text>`
- `<category>` ∈ {`convention`, `resource`, `thread`, `decision`}. Alias: `conv`, `res`, `th`, `dec`.
- `python3 <agent-home>/tools/memory/mem.py note "<text>" --type <type>` 실행 (type 매핑: convention→`convention`, resource→`reference`, thread→`thread`, decision→`decision`).
- `thread` → body 에 `[in-progress YYYY-MM-DD]` prefix 자동.
- `decision` → body 에 `YYYY-MM-DD:` prefix 자동.
- **사용자 텍스트 원문 그대로** → **즉시 적용** (검토 X). `--confirm` 시 diff preview.

### `/post-it resolve <hint>`
- working 레코드 중 `type=thread` 인 것에서 `<hint>` fuzzy 매칭 레코드를 찾는다.
- **default: preview → confirm** (1개 매칭 → 확인 / 여러 매칭 → 번호 선택 / 0개 → 중단).
- `mem delete <id>` 로 결정론적 삭제 — `resolve` 는 매칭 thread 레코드를 `mem delete` 로 즉시 제거 (`--no-confirm` 시 가장 유사한 1개 즉시 삭제). default 는 preview → confirm.

### `/post-it decide <text>`
- `python3 <agent-home>/tools/memory/mem.py note "<YYYY-MM-DD: text>" --type decision` 실행. 원문 → **즉시 적용**. `--confirm` 으로 검토.

### `/post-it sweep [--no-confirm] [--scope project|user [<aspect>]]`
**산출물·DB 레코드 대조 → 졸업·stale 항목 플래그/만료 (post-it lean 유지의 핵심).**

- **자동 자리** (nudge·handoff 내부): _확실한_ graduated/stale 만 **자동 flag + 한 줄 보고**, 애매하면 keep.
- **수동 자리** (`/post-it sweep` 직접 호출): **preview → confirm**. `--no-confirm` 시 확실분 즉시 처리.

**project scope (default)**:
1. `python3 <agent-home>/tools/memory/mem.py recall "" --tier working --scope project` 로 현 cwd working 레코드 전체 조회.
2. 현 산출물과 대조: `<artifact-root>/plans/*/`·`documents/*/`·`spec/`·`experiments/*/` + `git log --oneline -30` + 관련 코드·문서.
3. 각 레코드 분류:
   - **graduated** — 내용이 산출물에 영구 반영됨 → 만료 후보 (+ 어디로 갔는지 한 줄 pointer).
   - **stale** — 시간 기반 lifecycle tier. 대상 = `type=thread/decision/hint` (time-sensitive):
     - **active** (< 30d 또는 최근 git 활동과 연결) → 유지.
     - **stale 후보** (≥ ~30d 미갱신, git 활동과 단절) → 만료 후보로 분류.
     - **archive 대상** (≥ ~90d 미갱신, 또는 완료 정황 확실) → 자동 자리는 flag(한 줄 보고). `mem lifecycle` 이 `WORKING_TTL_DAYS` 기준으로 처리. graduated 내용은 이미 산출물에 있으므로 archive 불요(drop).
   - **live** — working 레코드에만 있고 유효(시간 무관 — convention/reference 는 _졸업_ 으로만 제거) → 유지.
4. 분류 결과를 **graduated / stale / keep 3 묶음으로 preview** → 사용자가 제거할 항목 confirm.
5. `mem lifecycle` 트리거 또는 advisory 처리.
- **sweep 은 working 레코드만 처리** — 산출물에 _추가_ 하지 않는다 (졸업 반영은 소유 스킬 몫).

**user scope (`--scope user <aspect>`)**:
- `python3 <agent-home>/tools/memory/mem.py profile <stem>` 으로 profile 레코드 조회.
- `## 사용자 수동 메모` 의 각 항목을 _같은 aspect 의 구조화 절_ 과 대조 → 이미 반영된 항목을 제거 후보로 preview → confirm.

### `/post-it promote [<hint>] [--scope user [<aspect>]]`
**user 메모를 구조화 aspect 절로 _졸업_ 시키는 sub-action** (user scope 전용).

**저장 모델 (중요)**: user 메모는 profile 레코드 body 안 `## 사용자 수동 메모` 블록에 embed된다 — 별도 `user-postit:` source 레코드로 분리하지 않는다 (별도 source 는 `mem profile`/`_derive_aspect` 에 보이지 않아 모든 agent 가 읽지 못함).

**promote 동작 (read-modify-write)**:
1. `<aspect>` (또는 default `collab`) profile 레코드에서 `## 사용자 수동 메모` 항목 중 _안정·범용_ 한 것을 식별 (`<hint>` 주면 그 항목).
2. 적절한 구조화 절(해당 aspect 본문)에 통합할 문안을 제안 → **preview → confirm** (analyze-user 의 "읽기만" 계약을 confirm 으로 보존).
3. 확정 시:
   - (1) `python3 <agent-home>/tools/memory/mem.py profile <stem>` 으로 현재 body 읽기 (newest-wins, rowid-DESC tie-broken).
   - (2) 해당 note 를 구조화 절에 splice + `## 사용자 수동 메모` 블록에서 그 항목 제거.
   - (3) `python3 <agent-home>/tools/memory/mem.py add durable profile "<whole-new-body>" --scope global --source user-profile:<stem>` 으로 전체 body write (SAME source = analyze-user 와 같은 logical record; 이전 working 레코드는 만료).
4. _대량·정식 재구조화_ 가 필요하면 promote 대신 `/analyze-user` 를 권한다 (promote 는 가벼운 1-2 항목 졸업용).

> **두 writer 계약**: `/post-it promote --scope user` 와 `analyze-user update` 는 모두 `source user-profile:<stem>` 으로 write — ONE logical record. analyze-user 의 "read existing body" 는 반드시 `mem profile <stem>` (tie-broken) 으로 읽어야 한다 (raw `db_iter_records` 로 읽으면 stale dup 에서 splice 될 위험). `write_record` 는 `(tier, scope, source)` source-keyed UPSERT — 같은 `source=user-profile:<stem>` 면 body 변경 시 기존 레코드를 in-place UPDATE (id 보존), dup row 없음. 두 writer 가 ONE record 로 결정론화.

### `/post-it handoff [--no-confirm]`
**세션 인계 — sweep 먼저, 그 다음 hints 생성** (에이전트가 내용 생성).

1. **sweep 자동 포함** — `sweep` 로직을 돌려 _확실한_ graduated·stale 을 자동 prune (애매하면 keep). 한 줄 보고 ("졸업 N·stale M 정리").
2. **hints 생성** — 현 세션 conversation 을 review 해 다음 세션에 알아야 할 5-10 bullet 요약:
   - 지금 어디까지 진행했는지 / 다음 세션에서 먼저 할 일 / 미해결 질문·블로커 / 주의사항.
   - **제외**: 이미 산출물·git 에 영속화된 내용, 다른 working 레코드에 이미 있는 내용.
3. **Default: preview → confirm** — 요약 bullets 를 보여주고 확인. 사용자 직접 편집·추가 가능.
4. 확인 시 `python3 <agent-home>/tools/memory/mem.py note "<hint-text>" --type hint` 로 각 bullet 기록 (이전 hint 레코드는 `mem lifecycle` 에 의해 교체·만료).
5. `--no-confirm` 시 sweep·hints 검토 없이 즉시 적용.

## Confirm 정책 요약

| Sub-action | Default | Override |
|---|---|---|
| `show` | 즉시 | n/a |
| `add` / `decide` | 즉시 (사용자 텍스트 원문) | `--confirm` |
| `resolve` | preview → confirm (fuzzy 매칭 + advisory) | `--no-confirm` |
| `sweep` (수동 호출) | preview → confirm (Claude 분류) | `--no-confirm` |
| `sweep` (자동 — nudge/handoff 내부) | 확실분 자동 prune + 한 줄 보고 (애매 keep) | n/a |
| `promote` | preview → confirm (Claude 제안 + 구조화 절 편집) | (없음 — 항상 confirm) |
| `handoff` (자동 nudge) | sweep 자동 포함 → 짧은 요약 보여주고 _저장 여부_ confirm | `--no-confirm` |

원칙: **사용자가 직접 적은 텍스트는 즉시, 에이전트가 만들거나 매칭하는 경우는 검토.** 단 _사용자는 post-it 을 안 본다_ — 자동 자리의 prune 은 _확실한 것만_ 자동 적용 + 한 줄 보고 (애매하면 keep), 사용자에겐 액션 단위 confirm 만.
