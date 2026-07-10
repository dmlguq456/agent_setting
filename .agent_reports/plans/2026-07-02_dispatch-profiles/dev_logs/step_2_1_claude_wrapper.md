# Step 2.1 — Claude dispatch wrapper (`adapters/claude/bin/dispatch-headless.py`)

new-lib mode. Phase 2 (depends on Phase 1) — 이번 step 은 orchestrator 의 병렬 분사로 Phase 1(`tools/profile/build-home.py`)과 동시에 실행됨. `--profile` 경로의 게이트(`build-home.py --check`)는 여기서 호출만 하고 **실행 검증은 하지 않음**(orchestrator 소유, plan Verification §6).

## 신규 파일

`adapters/claude/bin/dispatch-headless.py` (chmod +x) — `adapters/codex/bin/dispatch-headless.py` (279L) 이식 + `--profile` 신설.

## Decision 로그

- **parser()**: codex 동형 (`--dry-run|--register|--start` 배타 그룹 + `--worktree/--slug/--capability/--mode/--qa/--prompt-file|--prompt-text/--jobs/--log-dir`) + `--profile`. codex 전용 `--sandbox/--approval/--require-hook-trust` 는 claude 에 대응 개념이 없어 제외 (plan 명시 지시).
- **resolve_agent_home()**: codex 와 완전히 동일한 marker-walk 패턴 — `env AGENT_HOME` + `(Path(env_home)/"core"/"CORE.md").is_file()` 검사, 실패 시 `ROOT = Path(__file__).resolve().parents[3]`. `adapters/claude/bin/`(depth 3) 이므로 `parents[3]` = repo root, codex 와 동일 깊이라 리터럴 그대로 이식 가능. `check_claude_bin_wrappers` 는 이 파일을 아직 enumerate 하지 않지만(plan Current State 확인됨), `def resolve_agent_home()` / `core" / "CORE.md"` 리터럴 보존 + 금지 anti-pattern(`Path(os.environ.get("AGENT_HOME", os.getcwd()))`) 미포함을 grep 으로 직접 확인함(아래 검증 참조) — codex 패턴 정합을 hook 부재와 무관하게 지킴.
- **jobs.log default + 공유 registry 주석**: `jobs = args.jobs or agent_home/.dispatch/jobs.log`. claude 는 codex 와 동일 `AGENT_HOME`(보통 `~/.claude`)을 공유하므로 같은 `.dispatch/jobs.log`·`.dispatch/homes/` 를 쓴다는 것을 코드 주석으로 명시 — "두 개의 독립 registry" 가 아니라 "하나의 공유 registry" 로 서술(codex `dispatch-harvest.py` 가 claude profile home 도 회수할 수 있는 이유, plan #5 수정사항 반영).
- **append_job()**: 6필드 스키마 그대로, `pipe = f"capability={cap},mode={mode},qa={qa}"` + `args.profile` 있으면 `,profile={profile}` append. `repo = git -C worktree rev-parse --show-toplevel`.
- **dispatch_prompt()**: codex 의 preflight.sh 체인(`Required bootstrap: Read AGENTS.md / preflight.sh status / route / mode-info / qa-policy ...`)을 이식하지 않음 — CLAUDE_CONFIG_DIR 로 붙는 masked home 자체가 이미 L0 bootstrap(core 4문서 + guard 준수 + depth-1 규칙)을 로드하기 때문(spec §4.2/§6). 대신 프롬프트를 `task + dispatch metadata + depth-1 재분사 금지 리마인더 + 한국어 보고 요청` 으로 최소화. `--profile` 유무로 헤더 한 문단만 분기(프로필 있으면 masked home 언급 + "오케스트레이션 절 없음" 안내). `task_prompt()` 는 codex 와 동일 3경로(`--prompt-file` / `--prompt-text` / generated fallback, 파일+텍스트 동시 지정은 `ValueError`).
- **shell_command()**: `claude -p` 를 stdin(prompt 파일)에서 읽어 실행, `cd {worktree} && claude -p < {prompt_path} >> {log_path} 2>&1` — codex 의 `codex exec --cd ... < prompt_path >> log_path 2>&1` 와 대응 구조(claude CLI 는 `--cd` 플래그가 없어 `cd &&` 로 대체).
- **게이트 순서 (`--start` + `--profile`)**: `build_home_gate()` 헬퍼로 ① `build-home.py <name> --check` (실패 시 `fail(...)` + `return 3`, 인스턴스 생성 전이라 leak 없음) → ② `build-home.py <name> --instance <slug> --home-root <home-root>` (인스턴스 생성) → 이후 공통 경로에서 ③ `append_job()` (launch 전 등록 — harvest 가 항상 회수 가능) → ④ `subprocess.Popen(["sh","-c",command], env={**os.environ, "CLAUDE_CONFIG_DIR": str(instance_dir)}, start_new_session=True)`. `env` 는 `os.environ` 을 spread 로 상속(순수 dict 대체 시 PATH 유실 우려 — plan 명시 요구사항).
- **`--profile` 생략**: 인스턴스 생성·게이트 완전히 스킵, `env` 는 `{**os.environ}` 그대로(CLAUDE_CONFIG_DIR 미설정) — 기존 수동 `claude -p` 분사와 동일한 non-destructive 경로(DP-7).
- **QA_LEVELS 체크**: codex 와 동일하게 `{quick,light,standard,thorough,adversarial}` 검증을 남김 — CONVENTIONS §1 QA 레벨 불변식과의 정합, plan 이 명시 배제하지 않았고 다른 harness 와 계약을 맞추는 저비용 안전장치라 유지.
- **출력 k=v**: `adapter=claude`·`runtime_surface=claude-print-headless`·`status`·`worktree`·`slug`·`capability`·`mode`·`qa`·`profile={profile or '-'}`·`instance_home`·`job_registry`·`registry_lock`·`registered`·`started`·`prompt_source`·`prompt_file`·`log_file`·`command`.
- **미러 없음**: adapter 고유 파일이라 plan 대로 mirror step 없음.

## 검증

```
python3 -c "import ast; ast.parse(open('adapters/claude/bin/dispatch-headless.py').read())"   # 문법 OK
grep -Fq 'def resolve_agent_home()' adapters/claude/bin/dispatch-headless.py                  # OK
grep -Fq 'core" / "CORE.md"' adapters/claude/bin/dispatch-headless.py                          # OK
grep -Fq 'Path(os.environ.get("AGENT_HOME", os.getcwd()))' adapters/claude/bin/dispatch-headless.py  # 없음 (OK)
AGENT_HOME="$PWD" python3 adapters/claude/bin/dispatch-headless.py --dry-run --worktree "$PWD" \
  --slug t --capability autopilot-lab --mode dev --qa quick --prompt-text x   # exit=0, .dispatch/ 미생성 확인(non-destructive)
```

`--profile` 경로(build-home.py 호출)는 Phase 1 산출물이 이 worktree 에 병렬 생성 중이라 이 step 에서는 **실행하지 않음** — plan 지시대로 게이트 실행은 orchestrator 몫(Verification §6 build-home smoke, `tools/check-adaptation-boundary.sh` 등 completion gates 에서 통합 검증).

## 변경 파일

- NEW `adapters/claude/bin/dispatch-headless.py` (chmod +x, 258줄)
