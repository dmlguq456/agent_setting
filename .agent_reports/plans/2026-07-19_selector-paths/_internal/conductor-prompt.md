# Assignment — autopilot-code dev/standard conductor: 어댑터 투영 셀렉터 경로 해석 수리

You are the depth-1 capability owner (thin conductor) for one approved autopilot-code cycle.
Load `capabilities/autopilot-code.md` and the owner-execution reference, then run the
`plan → execute → test → report` stage graph. Do not re-select capability, intensity,
or topology (SD-45): they are fixed by the immutable route record below.

## ⚠️ Liveness contract — read this before anything else

**You are a `claude -p` one-shot process. There is no next turn. The moment you end your
turn "to wait", you are dead and the pipeline is orphaned (measured twice on 2026-07-19).**
Never use Monitor, never schedule wakeups, never end a message saying "대기한다". To wait
for a stage: run `sh /home/Uihyeop/agent_setting/utilities/dispatch-wait.sh --parent selector-paths`
**synchronously in the same turn, repeatedly** until exit 0 (exit 2 → run again immediately;
exit 3 → diagnose from artifacts, then redispatch). Keep calling tools until
`pipeline_summary.md` is written and your three final lines are printed.

## ⚠️ Registry hygiene — measured violation on the previous cycle

After harvesting each stage: **flip the harvested row to done first** (the dispatch tooling
notes how), **then** write the completion marker, **then** dispatch the next stage. Do not
leave harvested rows open — the previous conductor did, and depth-0 had to clean up.

## Immutable route binding

- route file: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_selector-paths/_internal/route.json`
- route_id: `rt-0970ceb6cde95614`
- route_hash: `sha256:0970ceb6cde95614697a0391fa83f0e65bc8df245c6d8124f67b026cae0dbb52`
- dispatch_contract_version: 3 (launch_authority=conductor)
- nodes: `plan → execute → test → report` (all depth 2)
- worktree (cwd, source writes): `/home/Uihyeop/agent_setting-wt/selector-paths` (branch `selector-paths`, base `main` @ `321792e5`)
- canonical plan root (artifact writes): `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_selector-paths/`
- spec-significance: within-spec — governing: `spec/stage-dispatch/prd.md` §13.8.1 SD-66
  1단계 소비자 배선(SD-23 read-only selector 유지) — 투영 표면에서 셀렉터가 동작해야
  한다는 기존 계약의 수리이며 신규 결정 불요. Read that section before planning.

## Task — what to fix (baseline bug, 재현 완료)

`utilities/dispatch-route.sh`는 `adapters/{claude,codex,opencode}/utilities/dispatch-route.sh`
심링크로 투영되는데, 내부 헬퍼 경로를 `$(dirname -- "$0")` 기준으로 해석해 심링크를
따라가지 않는다. depth-0 재현(2026-07-19, 최신 main):

- codex/opencode 투영: 39행 `usage-check.sh: not found`
  (`adapters/<h>/utilities/usage-check.sh`로 오해석 — usage-check는 투영되어 있지 않음)
- claude 투영: 106행 `model-map.sh: not found`
  (`$(dirname $0)/..` = `adapters/claude` → `adapters/claude/adapters/claude/bin/model-map.sh`)

### (1) `utilities/dispatch-route.sh` — 자기 실체 경로 해석

`$0`의 심링크를 해석해 **실제 utilities/ 디렉터리와 repo 루트**를 기준으로
`dispatch-defaults.py`(28행)·`usage-check.sh`(38행)·`model-map.sh`(103-104행)를 찾도록
수정한다. 제약:

- POSIX sh 유지 — `sh -n`과 `dash -n` 모두 clean해야 한다(기존 검증 기준).
  Linux coreutils `readlink -f` 사용은 허용되나, 사용 시 비존재 환경 fallback을
  한 줄이라도 고려하라(예: readlink 실패 시 기존 dirname 경로 유지).
- 셀렉터는 read-only 유지(SD-23) — 로직·캐스케이드·출력 형식 변경 금지.
  경로 해석만 고친다.
- `utilities/dispatch-defaults.py`는 이미 자체 realpath 해석을 한다 — 건드리지 마라.

### (2) 회귀 테스트

`utilities/dispatch-route.test.sh`에 **투영 표면 테스트**를 추가한다: 세 어댑터의
`adapters/<h>/utilities/dispatch-route.sh`를 직접 호출해 `adapter=` 출력까지 도달함을
단정(최소 1개 스테이지, 픽스처 config 격리 유지 — 기존 테스트의
`DISPATCH_DEFAULTS_CONFIG` 패턴을 따르라). 기존 단정 전부 유지.

### (3) 검증

- `sh utilities/dispatch-route.test.sh` PASS + `sh -n`/`dash -n` clean.
- 세 어댑터 투영 수동 실측: `--stage test --capability autopilot-code --maker-family gpt`
  → `status=eligible`/`adapter=` 출력 확인, `--stage plan`도 1회.
- `bash tools/check-adaptation-boundary.sh` exit 0 (worktree 안에서만).
- 기존 스위트 회귀 0: `dispatch_contract.test.py`, `dispatch_node.test.py`,
  sd45 3종(`adapters/*/bin/dispatch-headless.sd45.test.py`),
  sd15 3종(**bash로 실행** — sh는 pipefail 미지원).

## Explicitly OUT of scope

SD-68(route compile 봉인 — 다음 사이클), usage-check.sh/model-map.sh 내부 로직,
셀렉터 캐스케이드 의미 변경, 권한 분류기, `spec/**` 편집, worker-route-guard.

## Hard operational constraints

- guard/테스트는 **task worktree 안에서만**. primary checkout에서 guard 금지.
- 소스 편집은 worktree만; 산출물은 canonical plan root에만. main 머지/push 금지.
- 테스트가 만든 `adapters/**/__pycache__`는 커밋 전 삭제(boundary guard가 잡는다).
- execute FAIL 후 재시도가 필요하면: **SD-67이 main에 머지되어 이제 in-place 재분사가
  가능하다** — 같은 route에서 새 attempt로 execute를 재분사하라. `git reset --hard` 금지.

## Stage dispatch mechanics

For each node, in order:

```bash
AGENT_DISPATCH_JOBS=/home/Uihyeop/agent_setting/.dispatch/jobs.log \
python3 /home/Uihyeop/agent_setting/utilities/dispatch-node.py \
  --route /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_selector-paths/_internal/route.json \
  --node <plan|execute|test|report> --adapter <claude|codex> --action start \
  --slug selector-paths-<stage> --parent selector-paths --qa standard \
  --prompt-text "<stage contract: sub-skill name + absolute input paths + output contract + intensity standard + slug>" \
  -- --model-role "<node role>"
```

- Model roles: plan=`deep maker`, execute=`fast implementer`, test=`deep reviewer`, report=`fast writer`.
- Harness per node — config 소비 + 실측 이탈 사유:
  - plan=`codex`(deep-maker affinity), report=`claude`(config).
  - execute: config는 `codex`지만 **이탈하여 `claude`를 써라**. 기록할 사유: "2026-07-19
    retry-lineage 실측 — codex workspace-write 샌드박스는 linked worktree git metadata가
    read-only라 커밋 불가(BLOCKED)". 이 사유를 pipeline_summary에 남겨라.
  - test: diverse → execute(claude)와 다른 `codex`. 알려진 제약: codex 워커는 primary
    `.spec-grounding`에 못 써서 마커류 영속화가 실패할 수 있다 — 검증 자체는 유효하니
    worker가 verdict를 로그에 남기면 네가 salvage해 `test_logs/`에 영속화하라.
- 분사 직전 `bash /home/Uihyeop/agent_setting/utilities/usage-check.sh` 확인.
- 각 스테이지: dispatch-wait 동기 반복 → row flip → completion marker
  (`python3 /home/Uihyeop/agent_setting/utilities/capability-route.py complete --route <route.json> --node <id> --evidence <terminal artifact>`)
  → 다음 스테이지.
- Stage prompts carry absolute paths only. Sequential; conductor + one active stage.

## Completion

Write `pipeline_summary.md` (§5.8 lock) at the plan root before finishing.
Final output exactly three lines:

```
artifact: /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_selector-paths/final_report.md
verdict: PASS | FAIL | BLOCKED
blocker: none | <one line>
```
