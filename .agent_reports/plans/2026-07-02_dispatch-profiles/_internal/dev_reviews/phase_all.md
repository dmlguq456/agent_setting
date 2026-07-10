# 📋 코드 리뷰 결과 — dispatch-profiles v1 (전체 phase, deep reviewer)

**검토 대상**
- `tools/profile/build-home.py` (+ mirror `adapters/claude/tools/profile/build-home.py`)
- `adapters/claude/bin/dispatch-headless.py` (신규)
- `adapters/codex/bin/dispatch-headless.py`, `adapters/codex/bin/dispatch-harvest.py` (순수 확장)
- `utilities/dispatch-liveness.sh` (+ mirror)
- `tools/fleet/{model.py, collectors/dispatch.py, render.py}` (+ mirrors)
- `profiles/*` (선언·템플릿·fragment — 로직 없는 자료라 correctness 관점 대상 아님)

**변경 요약**
profiles/<name>.yaml 선언으로부터 symlink partial-projection 마스킹 홈을 만드는 build-home 생성기, 이를 `CLAUDE_CONFIG_DIR`/`CODEX_HOME`로 attach 하는 두 wrapper, jobs.log pipe의 `profile=` 를 인지하는 liveness/fleet/harvest 확장. `--profile` 생략 시 무파괴 유지.

**검증 방법**: 5개 소스 + 5개 mirror 전부 Read, mirror 5쌍 `diff -q` byte-identical 확인, `agent-home.sh` fallback 체인 확인. 게이트 통과분(boundary/portable-guards/manifest/smoke)은 재확인하지 않고 로직 correctness 만 대조.

---

## 🔴 꼭 수정해야 하는 문제

발견된 blocking 문제 없음 ✅

계획서의 round-1/round-2 QA 수정 6+6건이 코드에 정확히 반영돼 있고(아래 🟢 참조), 요청된 중점 항목은 대부분 계획대로 구현됐습니다.

---

## 🟡 수정하면 좋은 문제

### 1. `adapters/codex/bin/dispatch-headless.py:261-264` — `--instance` 빌드 return code 미확인 (claude wrapper와 비대칭)

codex 쪽 profile 빌드는 `--check` 결과는 확인(255-260)하지만, 뒤이은 실제 `--instance` 생성은 반환값을 버립니다.

```python
subprocess.run(
    ["python3", str(build_home), args.profile, "--instance", args.slug, "--home-root", str(home_root)],
    check=False,   # rc 캡처 안 함
)
profile_home = home_root / f"{args.slug}.{args.profile}"
```

- **왜 문제인지**: claude wrapper는 동일 자리를 `build_home_gate(...)` 로 감싸 `if rc != 0: return rc` 로 방어합니다(2.1 스텝 그대로). codex는 그렇지 않아, `--check` 통과 후 `--instance` 가 FS 오류(권한·디스크·중간 symlink 실패)로 깨져도 그대로 `append_job` + `Popen(... CODEX_HOME=profile_home)` 로 진행합니다. 즉 존재하지 않거나 부분 생성된 CODEX_HOME 을 향해 codex 를 띄웁니다. `--check`/`--instance` 가 같은 검증을 공유하므로 확률은 낮지만, 두 wrapper가 같은 anti-leak 계약을 표방하는데 한쪽만 구멍이 있는 비대칭입니다.
- **수정 방향**: claude 와 동형으로 `--instance` 도 rc 확인.
  ```python
  build_result = subprocess.run([...--instance...], stdout=PIPE, stderr=PIPE, text=True, check=False)
  if build_result.returncode != 0:
      if build_result.stdout: print(build_result.stdout, end="")
      if build_result.stderr: print(build_result.stderr, end="", file=sys.stderr)
      return fail("profile-build-failed", 3, profile=args.profile)
  ```

### 2. cross-file: AGENT_HOME **fallback** 체인이 3곳에서 서로 다름 (profile 기능이 이 divergence를 증폭)

home 경로 규약 `<home-root>/<slug>.<name>` 의 _문자열 조립_ 은 6곳 전부 동일합니다(아래 🟢에서 검증). 문제는 그 앞의 `<home-root>` = `<agent_home>/.dispatch/homes` 에서 **agent_home 을 못 구했을 때의 fallback** 이 갈린다는 점입니다.

| reader/writer | AGENT_HOME 미설정 시 fallback |
|---|---|
| claude/codex wrapper, harvest | `ROOT` = repo/worktree 루트 (`parents[3]`); build-home 은 marker-walk → 동일 repo 루트 |
| `tools/fleet/collectors/dispatch.py` `_proj_home()` | `CLAUDE_HOME` → `~/.claude` (`$HOME/agent_setting` 건너뜀) |
| `utilities/dispatch-liveness.sh` (`agent-home.sh`) | `CLAUDE_HOME` → `$HOME/agent_setting` → `$HOME/.claude` |

- **왜 문제인지**: `AGENT_HOME` 이 export 된 정상 운용(계획서가 "typically ~/.claude" 로 명시한 상태)에서는 셋 다 같은 루트로 수렴해 문제없습니다. 하지만 `AGENT_HOME` 이 없으면 wrapper 는 worktree 루트의 `.dispatch/homes/` 에 홈을 쓰고, fleet 은 `~/.claude/.dispatch/homes/` 를, liveness 는 `$HOME/agent_setting/.dispatch/homes/` 를 뒤집니다 → 모든 profile job 이 fleet/liveness 에서 false-DEAD. 이 divergence 자체는 이번 변경 이전부터 있던 것이지만, profile 기능은 "쓴 쪽과 읽는 쪽이 같은 home root 를 본다"는 것을 _새로_ 전제로 삼기 때문에 기존 불일치의 영향이 커졌습니다.
- **수정 방향**: 코드 수정보다는 **운용 계약을 명시**하는 쪽 권장 — profile dispatch 는 `AGENT_HOME` 설정을 전제(계획서 shared-registry 주석과 동일)로 한다는 점을 wrapper 주석/README 에 못박거나, 최소한 fleet `_proj_home()` 와 `agent-home.sh` 의 fallback 순서를 일치시키기. (이 부분은 의도된 전제일 수 있으니 확인해보세요.)

### 3. `tools/profile/build-home.py:28` — PyYAML ImportError 가 exit 2 사용 (자체 문서화한 exit-code 계약 위반)

```python
except ImportError:
    sys.stderr.write("PyYAML required: pip install pyyaml\n")
    sys.exit(2)
```

- **왜 문제인지**: 파일 docstring(16-17행)이 `2 = --check drift` 로 명시했는데 의존성 부재라는 전혀 다른 조건에 2 를 씁니다. `--check` 아닌 일반 호출에서 PyYAML 이 없으면 "drift" 코드가 나가 오해를 부릅니다. 두 wrapper 는 non-zero 를 전부 3 으로 접어버려 _기능상_ 무해하지만, 파일이 스스로 선언한 계약과 모순됩니다.
- **수정 방향**: `sys.exit(1)` (declaration/환경 오류 부류)로 변경. exit 2 는 drift 전용으로 남기기.

---

## 🟢 지금은 괜찮은 점 (관찰 포함)

**정확히 landing 한 것들 (요청 중점 항목 검증 결과):**

- **`link()` 포팅 충실도** (build-home.py:161-181): target 부재 skip / 실파일·실디렉토리 clobber 거부(`exists() and not is_symlink()`) / 심링크 unlink 후 재생성 — codex 원본 semantics 그대로. 특히 broken symlink(`exists()`=False, `is_symlink()`=True)도 `if linkpath.is_symlink(): unlink()` 로 올바르게 정리됩니다.
- **harvest cleanup 스코핑** (dispatch-harvest.py:111-120): `homes_to_clean` 는 오직 `fields[1] == "open"` 전이 분기 _안_ 에서만 append 되어 `matched_jobs` 스냅샷(‑‑status all 시 running 포함)이 아니라 실제 open→done 행만 rmtree. round-1 #3 fix 정확히 반영. `--keep-home` 존중(112행), 대상은 인스턴스 home 한정, `home.exists()` + `ignore_errors=True` 안전. rmtree 는 jobs.log rewrite 커밋 _후_ 실행되어 순서도 안전.
- **liveness `name` 리셋 위치** (dispatch-liveness.sh:22): while 본문 안(open 판정·enc 계산 뒤, case 매치 전)에서 매 iteration `name=""`. 이전 profile 행이 다음 profile-less 행으로 새지 않음(round-1 #4 fix). profile 없는 행은 `dir="$PROJ/$enc"` 현행 경로 유지 — 후방호환 OK. exit 3 유지.
- **`_parse_pipe` 4-tuple 전 return 경로** (collectors/dispatch.py:64/68/72): NEW form·**실패 경로(`None×4`)**·OLD form 세 곳 모두 4-tuple. 빈/malformed pipe 가 실제로 타는 66행 실패경로가 3-tuple 로 남았다면 caller 4-way unpack 이 `ValueError` 로 fleet 전체 렌더를 죽였을 텐데 정확히 막았습니다(round-1 #2). caller(363) 및 `_jobs_log_fields`(398) 모두 4-unpack.
- **home 경로 규약 6곳 일치**: `<slug>.<profile>` (slug 먼저, 구분자 `.`) 가 build-home(188)·claude wrapper(198)·codex wrapper(265)·liveness.sh(25)·harvest(120)·fleet(129) 전부 동일. pipe `profile=` key 도 두 append_job / liveness / fleet / harvest 5곳 동일. `enc` 변환도 liveness `sed 's#[/._]#-#g'` 와 fleet `_enc`(`/._`→`-`)가 동일 문자집합.
- **fleet `_job_liveness` isomorphism** (118-144): profile+slug 있으면 `.dispatch/homes/<slug>.<profile>/projects/<enc>`, 없으면 현행 `projects/<enc>` — Phase 4 와 동형, 후방호환. caller(425) 가 `profile=j.profile, slug=j.slug` 전달.
- **backfill tolerant + proc 한정** (403-422): `_jobs_log_fields` 는 파일부재→`{}`, malformed 행 skip. `collect()` 는 proc job 중 mode/profile None 만 slug 매칭 backfill, last-occurrence-wins.
- **Popen env 상속**: claude(231 `{**os.environ}` 뒤 CLAUDE_CONFIG_DIR)·codex(282 `{**os.environ, "CODEX_HOME":...}`) 둘 다 os.environ 상속 — PATH 유지, bare dict 아님. codex 는 CLAUDE_CONFIG_DIR 미설정(cross-harness leak 방지).
- **claude 게이트 순서** (main:210-234): `--check`(fail→return 3) → `--instance` → `append_job` → Popen. 인스턴스 생성 전 게이트라 실패 시 leak 없음. `--profile` 생략 시 게이트·인스턴스·CLAUDE_CONFIG_DIR 전부 skip → 무파괴(DP-7).
- **codex additive 삽입** (main:245-265): 기존 `check_runtime_projection` 게이트 뒤에 profile 분기 추가. 6-field schema·`matches()`·boundary 리터럴 불변.
- **opencode fail-loud 순서**: build_instance(186)가 `BOOTSTRAP_FILENAME[harness]`(258) 조회 _전_ 에 `assemble_bootstrap` 를 먼저 불러 opencode 템플릿 부재로 exit 1 → KeyError 도달 안 함. 계획서 Memo 6c 대로 latent-but-loud.
- **model_role XOR model** (validate:99-104): both / neither 둘 다 error 로 잡음.
- **mirror 5쌍 byte-identical** (`diff -q` 확인): build-home / liveness / fleet 3파일 전부 root=adapter 일치. build-home 은 marker-walk 라 양쪽 depth 에서 동일 바이트로 동작.

**관찰 (지금 바꿀 필요는 없음):**

- **`--check` drift 비교는 tautology** (do_check:270-280): 같은 입력을 `assemble_bootstrap` 로 두 번 읽어 비교 → 두 동기 read 사이에 외부 변경이 없는 한 _절대_ 달라지지 않아 exit 2(drift) 경로는 사실상 도달 불가. 즉 `--check` 의 실질 방어값은 declaration schema·template/fragment 존재·opencode fail-loud 같은 **exit 1 검증**이고, "결정론 재조립 대조" 는 장식에 가깝습니다. 계획서(273-275행)가 "v1 은 대조할 영속 instance 가 없다"고 이미 근거를 밝혔고, wrapper 가 non-zero 를 3 으로 접으므로 무해합니다. 다만 "deterministic 검증을 한다"는 인상과 달리 그 부분이 보호를 더하지는 않는다는 점은 알아두면 좋습니다.
- **codex `resolve_agent_home()` 3회 호출** (246·247·267) — 동일값 반복, 미세 중복. claude 게이트도 `--check`+`--instance` 로 2회 검증(do_instance 가 mkdir 전 validate 하므로 leak 방지값은 marginal). 둘 다 방어적이라 그대로 둬도 무방.
- **`--register` + `--profile`**: 두 wrapper 모두 인스턴스 빌드는 `--start` 에서만 하므로, `--register --profile` 은 `profile=` 행만 남기고 home 은 안 만듭니다. harvest(존재확인 후 skip)·liveness(DEAD)에 무해하나 계획서에 미명세인 조합.

---

## 요약

blocking 0건. 핵심 로직(link 포팅·게이트 순서·harvest 스코핑·liveness 리셋·_parse_pipe 실패경로·경로 규약 일치·profile-aware isomorphism)은 계획서 QA 수정분까지 정확히 반영됐습니다. 🟡 3건은 (1) codex `--instance` rc 미확인 비대칭, (2) AGENT_HOME fallback 3-way divergence(정상 운용 무해·전제 명시 권장), (3) ImportError exit-code 계약 위반 — 모두 정상 운용에서는 무해하나 방어·일관성 차원에서 다듬으면 좋습니다.
