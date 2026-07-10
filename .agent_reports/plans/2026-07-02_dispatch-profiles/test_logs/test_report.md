# Test Report — dispatch-profiles v1 (functional/integration)

**대상**: `adapters/claude/bin/dispatch-headless.py` (claude register wrapper) · `adapters/codex/bin/dispatch-harvest.py` (codex harvest) · `tools/profile/build-home.py` (masked home builder) · `utilities/dispatch-liveness.sh` (stealth-death 점검) · `tools/fleet/{collectors/dispatch.py,model.py,render.py}` (fleet monitor)
**트리거**: 수동 test-mode invocation (CLI/infra tool, Level 5b = 실제 실행 + 증거 캡처)
**환경**: cwd=`/home/Uihyeop/agent_setting-wt/dispatch-profiles`, Python 3.8.10 + PyYAML, **API 호출/실제 claude·codex launch 없음** (register/dry-run/temp dir 만)
**격리**: 전부 temp dir(`/tmp/dpf-test.*`) + temp jobs.log. build-home 인스턴스만 harvest 의 `resolve_agent_home()` 정합을 위해 `$PWD/.dispatch/homes` 에 생성 후 제거. liveness/fleet 은 temp `AGENT_HOME` 사용(스크립트가 env 직접 참조 — 마커 불필요)이라 repo 무오염.

---

## Level 1: 문법 검사 (PASS)

`python3 -m py_compile` 6개 `.py` 전부 OK, `bash -n utilities/dispatch-liveness.sh` OK.

```
OK  adapters/claude/bin/dispatch-headless.py
OK  adapters/codex/bin/dispatch-harvest.py
OK  tools/profile/build-home.py
OK  tools/fleet/collectors/dispatch.py
OK  tools/fleet/model.py
OK  tools/fleet/render.py
OK  utilities/dispatch-liveness.sh
```

## Level 2: 임포트 검사 (PASS)

```
python3 -c "import sys; sys.path.insert(0,'tools'); \
  from fleet.collectors.dispatch import collect, _parse_pipe, _job_liveness; \
  from fleet.model import DispatchJob; from fleet.render import _mq_tag"
→ imports OK: collect,_parse_pipe,_job_liveness,DispatchJob,_mq_tag
```

## Level 3: 스모크 (사전 통과분 — 참고)

boundary checker exit 0, portable-guards.test 267/0, build-manifest --check up-to-date, build-home 스모크(9링크·settings.json dual-path·--check 0), wrapper dry-run, `_parse_pipe` 4-tuple, code-review 🔴 0 — 본 실행에서 재확인 불요(이미 통과). build-home 9링크는 아래 시나리오 2a 에서 end-to-end 로 재확인됨.

## Level 4 / 5b: 기능·통합 런타임 관찰 (실제 실행)

### 시나리오 1 — register → jobs.log pipe 형식 (PASS)

명령 (AGENT_HOME="$PWD"):
```
# 1a with profile
python3 adapters/claude/bin/dispatch-headless.py --register \
  --profile lab-runner --worktree "$PWD" --slug ttest \
  --capability autopilot-lab --mode dev --qa quick --prompt-text x --jobs <tmp>/jobs1.log
# 1b without profile
python3 adapters/claude/bin/dispatch-headless.py --register \
  --worktree "$PWD" --slug noprof \
  --capability autopilot-code --mode dev --qa standard --prompt-text y --jobs <tmp>/jobs1.log
```

관찰 (jobs.log, `^I`=tab):
```
…Z^Iopen^I<repo>^I<repo>^Ittest^Icapability=autopilot-lab,mode=dev,qa=quick,profile=lab-runner
…Z^Iopen^I<repo>^I<repo>^Inoprof^Icapability=autopilot-code,mode=dev,qa=standard
```
- 6-field tab 스키마: `awk -F'\t' NF` → **fields=6** (양쪽) ✓
- ttest pipe 에 `capability=,mode=,qa=,profile=lab-runner` 존재 ✓
- noprof pipe 에 `profile=` **없음** ✓ (stdout 은 `profile=-`, `instance_home=-`)

### 시나리오 2 — harvest home cleanup roundtrip (PASS)

**2a build-home 인스턴스 생성** (`build-home.py lab-runner --instance hv --home-root $PWD/.dispatch/homes`):
- `instance=…/hv.lab-runner harness=claude links=9`, exit 0 ✓
- `core`,`hooks`,`settings.json`,skills(3),agents(3) = 9 symlink + `CLAUDE.md`(real file, not symlink) ✓
- `core -> <repo>/core`, `settings.json -> <repo>/adapters/claude/settings.json` (dual-path first_existing) ✓

**2c `--mark-done` (slug hv, open 행)**:
```
python3 adapters/codex/bin/dispatch-harvest.py --jobs <tmp>/jobs2.log --slug hv --mark-done
→ matched=1 marked_done=1 malformed=0, exit 0
```
- (a) jobs.log 행 → `status=done` 로 rewrite ✓
- (b) `hv.lab-runner` 홈 **REMOVED** ✓
- (c) symlink 대상 원본 보존: repo `core/` inode 6833444 **불변** (before==after), `core/CORE.md` present, `hooks/` intact ✓ (`shutil.rmtree` 가 symlink 을 unlink 만 하고 target 을 따라가지 않음 — 실측 확인)

**2d `--mark-done --keep-home` (slug kp)**: matched=1 marked_done=1, 행 done, `kp.lab-runner` 홈 **PRESERVED** ✓

**2e running-job 보호 (`--status all`, running 행)**:
```
python3 …/dispatch-harvest.py --jobs <tmp>/jobs_run.log --slug run1 --status all --mark-done
→ matched=1 marked_done=0 job_status=running
```
- 행 여전히 `running` (open→done 전이만 처리) ✓
- `run1.lab-runner` 홈 **PRESERVED** (running 은 정리 대상 아님) ✓

### 시나리오 3 — liveness profile 경로 해석 (PASS)

`bash utilities/dispatch-liveness.sh <tmp>/jobs3.log` (AGENT_HOME=temp):
- transcript 배치: profile 행(liveA) → `$AGENT_HOME/.dispatch/homes/liveA.lab-runner/projects/<enc(wt)>/*.jsonl` **만**, profile 없는 행(liveB) → `$AGENT_HOME/projects/<enc(wt)>/*.jsonl`
```
ALIVE      liveA  (transcript 0m 전 갱신)     # profile → masked home 경로에서 발견
ALIVE      liveB  (transcript 0m 전 갱신)     # profile 없음 → $AGENT_HOME/projects (후방호환)
— open 2 · alive 2 · suspect/dead 0          # exit 0
```
- **negative control**: profile 행(liveC) 의 transcript 를 **main projects/ 에만** 두면 → `⚠️ DEAD liveC — 세션 transcript 없음 (…/.dispatch/homes/liveC.lab-runner/projects/…)`, exit 3. profile 잡이 main 경로로 **fallback 하지 않음**을 증명 (엄격히 masked home 경로만 조회) ✓

### 시나리오 4 — fleet collect (PASS)

`collect(jobs_path=<tmp>/jobs4.log)` (AGENT_HOME=temp, profile transcript 를 masked home 아래 배치):
```
collected job: slug=fleetJ key=lab profile='lab-runner' liveness=working source=jobs cwd=/work/tree/delta mode='dev' qa='quick'
```
- `DispatchJob.profile == "lab-runner"` (채워짐) ✓
- `liveness == "working"` — home 경로 기준 해석, **false-DEAD 아님** ✓
- `key=lab` (autopilot- prefix strip), qa=quick(jobslog) 정상 파싱 ✓
- `_mq_tag(mode,qa,qa_key,profile='lab-runner')` → segments `[' (','dev','·','quick','·','lab-runner',')']`, width=23 — **profile 세그먼트 포함, 안 깨짐** ✓
- empty case `_mq_tag(None,'','dim',None)` → `([], 0)` ✓

---

## 종합

- **통과**: 5 / 5 levels (L1 syntax, L2 import, L3 smoke[사전], L4/5b functional·integration 4 시나리오 전부)
- **결과**: **All passed** — register pipe 스키마 / harvest 홈 정리·target 보존·running 보호·keep-home / liveness profile 경로(+fallback 미발생) / fleet collect profile·liveness·render 전부 실측 통과
- **권장 조치**: 없음. (정리) 테스트가 남긴 `$PWD/.dispatch/`·temp dir·test-created `__pycache__` 제거 완료 — `git status` 는 테스트 전 상태(10 modified + 4 untracked feature 경로)로 복귀 확인.

### 참고 (함정 메모, 회귀 감시용)
- harvest 의 홈 정리는 `resolve_agent_home()` 기준 `$AGENT_HOME/.dispatch/homes/<slug>.<profile>` 를 봄 — writer(wrapper)·reader(harvest/liveness/fleet) 가 **동일 AGENT_HOME** 을 공유해야 정합. AGENT_HOME 불일치 시 profile 잡은 false-DEAD·홈 미정리 위험(코드 주석·plan Risks 에 명시됨, 본 테스트는 일치 조건에서 검증).
- liveness/fleet 의 profile 경로는 엄격 — main projects/ 로 fallback 안 함 (시나리오 3 negative control 로 확인). 이는 의도된 격리 동작.
