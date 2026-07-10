# 변경 보고서: dispatch-profiles v1

- **일시**: 2026-07-02 | **플랜**: `.agent_reports/plans/2026-07-02_dispatch-profiles/plan/plan.md` | **상태**: ✅ 완료 (checklist 전항목 성공, 실패/스킵 없음)

## 1. 변경 개요

`spec/dispatch-profiles/prd.md`(DP-1~12)를 근거로 dispatch-profiles v1(claude+codex)을 출하했다. 단일 repo 소스에서 심링크 partial-projection으로 만드는 "마스킹된 config home"을 `profiles/<name>.yaml`로 선언하고, 이를 두 dispatch wrapper(`claude`/`codex`)에 `--profile` 옵션으로 연결하며, liveness/fleet/harvest 관제 도구가 그 masked home을 인지하도록 확장했다. `--profile`를 생략하면 기존 동작과 완전히 동일해 무파괴(DP-7)를 지킨다. Phase 0~6, 6개 게이트(boundary 가드 2종·portable-guards 2종·build-manifest·build-home smoke)가 전부 통과했고, functional/integration 테스트(test_logs/test_report.md) 5개 레벨 전부 PASS했다.

## 2. 핵심 변경 사항

### 2.1 `profiles/` 선언 카탈로그 + 템플릿 (Phase 0)

- **파일**: `profiles/README.md`, `profiles/templates/bootstrap-{claude,codex}.md`, `profiles/lab-runner.yaml`, `profiles/fragments/lab-runner.md` — 전부 신설.
- **변경 내용**: 프로필 카탈로그 인덱스(README), harness별 L0 부트스트랩 스텁 템플릿, 참조 선언 예시(`lab-runner`, spec §3 그대로), L2 특화 fragment.
- **이유**: build-home.py가 조립할 입력 자료 — 선언(YAML) + 템플릿(L0) + fragment(L2)의 3단 구조가 있어야 마스킹된 home의 bootstrap 파일(`CLAUDE.md`/`AGENTS.md`)을 만들 수 있다.
- **핵심 원리**: L0(공통 규율) + L2(역할 특화)만 있고 **L1(오케스트레이션 절)은 의도적으로 없음**(DP-10) — masked home은 재분사하지 않는 leaf worker용이라는 것을 문서 구조 자체로 강제한다.
- **영향 범위**: repo-context-only 입력 — 어떤 projection surface에도 등록되지 않는다(정상 dispatch 흐름이 항상 source-tree 컨텍스트에서 도는 것에 의존, Scope Notes에 명시).

### 2.2 `build-home.py` 마스킹된 home 생성기 (Phase 1)

- **파일**: `tools/profile/build-home.py`(신설) + byte-identical mirror `adapters/claude/tools/profile/build-home.py`.
- **변경 내용**: 선언 파싱·검증(`name`/`description`/`harness` 필수, `model_role` XOR `model`), bootstrap 조립(템플릿+fragment 순수 concat), `install-runtime-projection.sh`의 `link()` 원시 로직을 Python으로 이식한 심링크 farm 생성(`--instance`), 재조립 대조 검증(`--check`), exit code 0/1/2 계약.
- **이유**: codex 진영에는 shell 기반 projection 도구만 있고, 임의 프로필 이름으로 매번 새 masked home을 만드는 범용 생성기가 없었다.
- **핵심 원리**: `resolve_agent_home()`이 env AGENT_HOME 우선, 없으면 `Path(__file__).resolve().parents`를 `core/CORE.md`가 나올 때까지 marker-walk — root(`tools/profile/`, depth 2)와 mirror(`adapters/claude/tools/profile/`, depth 4)가 depth가 달라도 **동일 바이트**로 양쪽에서 동작해야 하므로 고정 `parents[N]` 대신 marker-walk이 필수였다.
- **영향 범위**: `--instance` 호출 전까지는 파일시스템에 아무것도 쓰지 않고(fail-fast), L0 하드 포함(`core/`·`hooks/`·harness별 hook-registration 파일)은 선언에 노출되지 않아 사용자가 실수로 마스킹할 수 없다(DP-2).

### 2.3 dispatch wrapper 확장 — claude 신설 + codex `--profile` (Phase 2/3)

- **파일**: `adapters/claude/bin/dispatch-headless.py`(신설, 258줄) / `adapters/codex/bin/dispatch-headless.py`(EDIT, 순수 확장) / `adapters/codex/bin/dispatch-harvest.py`(EDIT, `--keep-home` + home cleanup).
- **변경 내용**: `--profile <name>` 플래그, jobs.log pipe에 `,profile={name}` 추가, `--start`+`--profile` 시 `build-home.py --check`(게이트) → `--instance`(생성) → `append_job`(등록) → `Popen(env={**os.environ, "CLAUDE_CONFIG_DIR"/"CODEX_HOME": <instance>})` 순서로 attach. codex harvest는 `open→done` 전이 행에서 `profile=`이 있으면 instance home을 `shutil.rmtree`.
- **이유**: claude에는 codex와 대칭되는 헤드리스 dispatch wrapper 자체가 없었고, `--profile` 부착·정리 훅이 양쪽 harness에 필요했다.
- **핵심 원리**: 게이트를 **생성보다 먼저** 돌려야 실패해도 instance leak이 없고(anti-leak 순서), jobs.log 등록을 **launch보다 먼저** 해야 harvest가 항상 회수 가능하다. codex harvest는 harness와 무관하게 `profile=` 필드만 보고 청소하므로 claude·codex가 공유 `~/.claude/.dispatch/{jobs.log,homes/}`를 쓰는 한 claude 프로필 home도 codex harvest가 회수한다(DP-4).
- **영향 범위**: `--profile` 생략 시 게이트·인스턴스 생성·env 주입이 전부 스킵되어 기존 수동 `claude -p`/`codex exec` 분사와 완전히 동일(DP-7). codex 쪽은 `~30`개 `grep -Fq` 경계 리터럴을 훼손 없이 보존.

### 2.4 liveness·fleet·harvest 관제 확장 (Phase 4/5/6)

- **파일**: `utilities/dispatch-liveness.sh`(+mirror), `tools/fleet/{model.py,collectors/dispatch.py,render.py}`(+mirror).
- **변경 내용**: liveness와 fleet 모두 pipe의 `profile=`을 파싱해 transcript 조회 경로를 `<AGENT_HOME>/.dispatch/homes/<slug>.<name>/projects/<enc>`로 전환(profile 없으면 기존 경로 유지). `DispatchJob.profile` 필드 신설, `_parse_pipe()` 4-tuple 확장(3개 return 지점 전부), proc job의 `mode`/`profile` 자동 backfill, `_mq_tag()`에 `·<profile>` 세그먼트 추가.
- **이유**: profile job은 transcript가 main home이 아니라 masked home 아래에 격리되므로, 이 경로 전환이 없으면 liveness/fleet이 **모든 profile job을 항상 DEAD로 오판**한다(spec §7 요구사항).
- **핵심 원리**: `dispatch-liveness.sh`(bash)와 `_job_liveness()`(fleet collector)는 **동일 로직의 두 개 독립 리더**다 — 하나가 다른 하나를 대체하지 않고 둘 다 필요(스크립트 단독 실행 vs fleet 대시보드).
- **영향 범위**: `profile=`이 없는 기존 job은 파싱·경로·렌더 전부 이전과 byte-for-byte 동일 — 회귀 없음. mirror 5쌍(`diff -q`) byte-identical 확인됨.

## 3. 설계 인사이트

- **심링크 partial-projection**: masked home은 `core/`·`hooks/`(전체 디렉터리), harness별 hook-registration 파일, `expose:`로 선언한 skills/agents 서브셋만 심링크하고, `.credentials.json`은 공유(심링크), `projects/`·`sessions/`·`.statusline/` 같은 세션 상태는 아예 링크하지 않아 인스턴스별로 격리된다. `shutil.rmtree`가 심링크를 unlink만 하고 target을 따라가지 않으므로 harvest cleanup이 원본 소스를 절대 건드리지 않는다는 것도 실측 확인됨(test 시나리오 2c).
- **L0 하드 포함은 선언에 노출되지 않는다(DP-2)**: `settings.json`/`hooks.json` 같은 guard hook 등록 요소는 `profiles/<name>.yaml`의 `expose:` 목록에 없어도 무조건 링크된다 — 사용자가 프로필 선언으로 guard hook을 마스킹해서 끌 수 있는 경로 자체가 존재하지 않는다.
- **marker-walk이 byte-identical 미러를 가능케 한다**: repo root와 `adapters/claude/` 미러는 소스 트리 depth가 다르므로, 고정된 `parents[N]` 상수 대신 `core/CORE.md` 존재를 기준으로 위로 walk하는 방식이어야 두 위치에서 완전히 같은 바이트의 파일이 동작한다.
- **pipe k=v는 순수 확장이라 후방호환이 저절로 따라온다**: `capability=,mode=,qa=`에 `,profile=`을 덧붙이는 방식이라, 기존 `_parse_pipe()`가 몰랐던 필드는 무시하고 지나간다 — 다만 실패 경로(빈/malformed pipe)의 return 개수까지 tuple 크기를 맞춰야 한다는 게 round 1 QA가 잡아낸 함정이었다.
- **게이트 exit code는 레이어별로 소유가 나뉜다**: `build-home.py`는 0/1/2만 쓰고(`3`은 절대 안 씀), dispatch wrapper가 자신의 preflight 실패를 `3`으로 접는다 — 생성기와 wrapper가 같은 코드 공간을 침범하지 않는 계약.

## 4. QA 리뷰 요약

| 리뷰 | 발견 | 해결 |
|---|---|---|
| plan-review round 1 (deep) | 🔴1(L0 `settings.json` 소스 경로가 repo 레이아웃과 불일치) · 🟡5(`_parse_pipe` 실패경로 3-tuple 잔존/harvest가 running job home 삭제 위험/liveness `name` 변수 leak/claude 프로필 cleanup 소유권 불명/gate 순서+Popen env 상속 누락) | 6/6 전부 반영 (plan Change History round 1) |
| plan-review round 2 (focused re-verify) | round 1 6건 전부 반영 확인(🔴0) · 신규 🟡1(N1 — round 1 수정 과정에서 codex `hooks.json` 소스가 존재하지 않는 `codex-hooks/` 디렉터리를 가리키게 됨, 동일 결함 계열의 codex 브랜치 재발) | v1(lab-runner=claude만) 비차단이나 정정 완료 — 현재 `build-home.py`는 `adapters/codex/hooks/hooks.json` 실경로를 fallback으로 사용함을 코드로 확인 |
| plan-review research_review (user-proxy) | 🔴1(Memo 1 — spec §7 fleet의 `.dispatch/homes/*/` 추가 스캔 루트를 Phase 5가 누락, profile job이 fleet에서 항상 DEAD로 오판) · 🟡3(profiles/ non-projection 미명시·sync-skills/README 연동 미언급·"profile" 용어가 기존 mem-profile과 충돌) · 🟢2(ADAPTATION.md 앵커링·guard 목록에 spec-gate 누락) | 🔴 → 신규 Step 5.3(`_job_liveness()` profile-aware) 추가로 해소. 🟡3 → Scope Notes/README에 명시적 서술 추가로 해소 |
| dev-review phase_all (post-code, deep) | blocking 없음(🔴0) · 🟡3(codex `--instance` 결과 rc 미확인 — claude wrapper와 비대칭 / AGENT_HOME fallback이 wrapper·fleet·liveness 3곳에서 서로 다른 순서 — 정상 운용 무해하나 확인 권장 / build-home.py PyYAML ImportError가 자체 문서화한 exit code 계약(2=`--check` drift)을 위반) | 3건 전부 적용 완료(§4.5) |
| test_report (functional/integration) | Level 1~5b(문법/import/smoke/기능/통합) 5개 레벨 전부 실측 PASS — register pipe 스키마, harvest 홈 정리(원본 보존·running job 보호·`--keep-home`), liveness profile 경로(엄격 격리, main으로 fallback 안 함 negative control), fleet collect(profile 필드·liveness·render 세그먼트) | 권장 조치 없음 |

미해결 항목은 없다. dev-review의 관찰(observation) 2건 — `--check` 재조립 대조가 사실상 tautology(방어값은 exit 1 검증 쪽에 있음), `resolve_agent_home()` 중복 호출 — 은 무해하다고 판단되어 코드 변경 없이 기록만 남겼다.

## 4.5 자율 판단 기록

plan-review 2라운드 + user-proxy 1라운드에 걸쳐 발견된 🔴급 이슈 3건을 사용자 개입 없이 자율 수정했다.

1. **L0 `settings.json` 경로**(round 1 🔴) — repo root에는 `settings.json`이 없고 canonical은 `adapters/claude/settings.json`이라는 실측을 반영해, skills/agents와 동일한 runtime-first/repo-fallback 이중경로로 재작성. smoke test에 `test -e .../settings.json` false-green guard도 추가.
2. **codex `hooks.json` 경로**(round 2 N1, #1 수정 과정에서 유입된 재발) — harness=codex 분기를 harness=claude와 대칭으로 일반화하면서 존재하지 않는 `codex-hooks/` 디렉터리를 가리키게 된 것을 실경로(`adapters/codex/hooks/hooks.json`)로 정정.
3. **fleet 스캔 루트**(research_review Memo 1 🔴) — spec §7이 명시한 `.dispatch/homes/*/` 추가 스캔 루트 요구를 Phase 5가 누락했던 것을, `dispatch-liveness.sh`와 동형인 새 Step 5.3(`_job_liveness()` profile-aware 확장)으로 채워 넣음.

dev-review(post-code)의 🟡 3건도 자율 적용했다.

1. codex wrapper의 `--instance` 빌드 결과 rc를 claude wrapper와 동형으로 확인하도록 추가(`build_result.returncode != 0` 시 `fail("profile-build-failed", 3, ...)`).
2. `build-home.py`의 PyYAML `ImportError` exit code를 `2`(자체 문서화한 "`--check` drift" 전용 코드)에서 `1`(declaration/환경 오류 부류)로 정정.
3. AGENT_HOME fallback이 wrapper/harvest·fleet `_proj_home()`·liveness `agent-home.sh` 3곳에서 서로 다른 순서라는 지적은, 코드를 셋 다 맞추는 대신 "profile dispatch는 공유 `~/.claude` registry를 전제한다"는 기존 운용 계약 주석(round 1 fix #5, `dispatch-headless.py`)으로 갈음 — dev-review 자신도 "코드 수정보다는 운용 계약을 명시하는 쪽 권장"이라고 제안한 항목이라 기존 주석이 그 요건을 충족한다고 판단.

## 5. 실패/스킵된 단계

실패한 단계는 없다 — Phase 0~6 checklist 전 항목([x]) + 완료 게이트 6종 전부 통과.

`analysis_project/code/` 문서 업데이트는 **스킵**했다 — 이 repo에는 `.agent_reports/analysis_project/` 아래 `memory-audit/`만 있고 `code/` 서브디렉터리 자체가 없어(부트스트랩되지 않은 상태) 갱신할 대상 문서가 없다. 코드베이스 구조를 지속적으로 추적하려면 `/analyze-project --mode code`로 먼저 부트스트랩하는 것을 권장한다.

## 6. 향후 참고사항

- **opencode는 v1 범위 밖(P1)** — `harness: opencode`는 스키마는 통과하지만 `profiles/templates/bootstrap-opencode.md`가 없어 template-read에서 fail-loud(exit 1)한다. 실제 opencode wrapper/liveness/harvest 확장은 별도 사이클.
- **`CLAUDE_CONFIG_DIR` 마스킹 attach는 문서화되지 않은 경험적 동작(DP-9)** — 관찰로 검증됐을 뿐 공식 문서 근거가 없어 Claude 릴리스에 따라 회귀할 수 있다. build-home smoke는 파일/심링크 존재만 확인하고 실제 hook 발화까지는 검증하지 않으므로, 실사용 검증은 향후 drill/oncall 항목으로 남겨야 한다.
- **WORKFLOW/OPERATIONS §8 하이브리드 라우팅 문서 갱신은 이번 사이클 범위 밖** — spec §8에 따라 별도 사이클.
- **`profiles/README.md`의 sync-skills/README 대시보드 연동은 의도적으로 defer** — spec §9는 sync-skills 자동 갱신 후보로 지목하지만 v1은 카탈로그를 수동 유지, `build-manifest.py --check`는 영향받지 않음을 재확인함.
- **AGENT_HOME 공유가 전제 조건** — claude·codex가 동일 `AGENT_HOME`(보통 `~/.claude`)을 가리켜야 wrapper가 쓰는 home root, fleet `_proj_home()`, liveness `agent-home.sh`의 fallback이 전부 같은 곳으로 수렴한다. 이 전제가 깨지면(예: `AGENT_HOME` 미설정 상태에서 fleet/liveness만 다른 기본값으로 실행) profile job이 false-DEAD로 보이거나 harvest cleanup이 무발생할 수 있다(비파괴적이라 blocking은 아님) — dev-review가 지적한 항목으로, 향후 세 도구의 fallback 순서를 명시적으로 통일하는 것도 고려할 만하다.
