# code-review — Phase 3+4 drivers (claude / codex / opencode) + verifier

- 검토 대상: `tools/install/drivers/{claude,codex,opencode}.py`, `tools/install/verifier.py`
- 방식: 정적 검토 + `tempfile.mkdtemp()` HOME 하 실측(실제 `~/.claude`/`~/.codex`/`~/.config/opencode` 미접촉)
- verdict: **CHANGES REQUESTED** — 데이터 유실급 안전 불변식 위반 1건(HIGH, claude·opencode 공통) + Phase 5 배선을 깨는 cross-module `blocked` 불일치 1건(MEDIUM).

---

## HIGH — claude·opencode 가 symlink 자리의 기존 **real 파일**을 삭제(데이터 유실)

안전 불변식 (a) 위반. 세 드라이버 모두 "real 디렉터리는 밀지 말고 blocked" 를 의도했으나, claude·opencode 의 가드가 **디렉터리만** 막고 **일반 파일은 못 막는다**.

- claude.py:103 / opencode.py:180 — `if dest.exists() and not dest.is_symlink() and dest.is_dir():` → blocked.
- 그 아래 claude.py:115 / opencode.py:192 — `if dest.is_symlink() or dest.exists(): dest.unlink()` 로 **떨어져서 real 파일을 unlink 후 symlink 로 대체**.

symlink dest 중 실제로 **파일**인 것:
- claude: `CLAUDE.md`, `README.md`, `manifest.json`, `statusline.sh`, `track-toggle.sh`
- opencode: `agent-agents.md`, `agent-harness-readme.md`, `plugins/agent-harness-guards.js`, 그리고 agent/command glob 의 **모든 `.md`**

즉 vanilla Claude 사용자가 이미 갖고 있는 `~/.claude/CLAUDE.md` 가 설치 시 **말없이 삭제**된다. temp HOME 실측:

```
CLAUDE: ~/.claude/CLAUDE.md (사용자 내용) → became a symlink (DATA LOSS): True ; blocked: False
OPENCODE: ~/.config/opencode/agent-agents.md (사용자 내용) → DATA LOSS: True ; blocked: False
CODEX (control): ~/.codex/AGENTS.md → still real file: True ; blocked: True   ← 올바름
```

codex.py:91 은 `if dest.exists() and not dest.is_symlink():` 로 파일·디렉터리 **둘 다** 커버해 정답이다. claude·opencode 의 가드를 codex 와 동일하게 `... and not dest.is_symlink():` 로 좁혀 `.is_dir()` 조건을 제거해야 한다. (step log 의 "real directory 방어" 결정이 파일 케이스를 빠뜨린 것 — codex step log 는 정확히 이 차이를 짚고 파일까지 커버했다.)

## MEDIUM — top-level `blocked` 산출이 드라이버마다 달라 Phase 5 배선이 uniform 소비 불가

install() 반환의 `blocked` 키 계산 규칙이 3사 제각각:

- codex.py:140 — `any(a.get("status") == "blocked" for a in actions)` (정답)
- claude.py:200 — **하드코딩 `"blocked": False`** — 어떤 action 이 blocked 여도 top-level 은 항상 False.
- opencode.py — `blocked` 변수는 **merge conflict 에서만** True. symlink-blocked 는 반영 안 됨.

실측(real 디렉터리를 자리에 둔 뒤 설치):

```
CLAUDE   dir-in-way: action-level blocked=1건, top-level blocked=False
OPENCODE dir-in-way: action-level blocked=1건, top-level blocked=False
         → 게다가 blocked 가 False 라 manifest.record() 까지 호출됨(부분 blocked 설치인데 매니페스트 기록)
```

Phase 5 `cmd_install` 은 세 드라이버의 `blocked` 를 균일하게 읽어 `EXIT_BLOCKED` 를 결정해야 하는데(plan §5.1), claude·opencode 는 symlink 가 막혀도 `EXIT_OK` 로 흘러간다. opencode 는 부분 실패 상태에서 매니페스트를 남겨 이후 drift/uninstall 회계가 어긋난다.

수정: 세 드라이버 모두 `blocked = any(a.get("status") == "blocked" for a in actions)` 로 통일(opencode 는 merge conflict OR 로), 그리고 `manifest.record()` 를 `not dry_run and not blocked` 로 가드(opencode 는 이미 `not blocked` 가드가 있으니 blocked 계산만 고치면 자동 해결).

## LOW-MEDIUM — opencode checks() 의 check id 가 basename 만 써서 shadowing 잠재

opencode.py:273 `f"opencode.symlink.{name}"` (`name = Path(dest).name`). codex 는 같은 glob fan-out 위험 때문에 의도적으로 `parent.name + name` 합성(codex.py:157, codex step log Decision 5)을 썼는데 opencode 는 basename 만 쓴다. opencode 도 `agent/*`·`command/*` 두 glob + agent 는 `*/*.md` 플랫화가 있어 구조적으로 같은 위험.

현재 실측으로는 충돌 없음(agent 9개·command 28개 basename 유니크, DUP ids 0). 즉 **잠재 위험**이지 활성 버그는 아니다. 다만 future 에 agent/command 가 같은 basename 을 갖거나 두 subdir 이 같은 파일명을 가지면 check id가 조용히 shadowing 되고(그 전에 dest symlink 자체도 충돌) 관측 불가. codex 컨벤션(`parent.name.name`)에 맞추길 권장.

## LOW — opencode drift-watch `plugins` 오탐(요청서 spot-check 확인)

step log 의 self-noted caveat 이 **실재함을 확인**했고, 더 깊은 설계 결함은 아니다.

```
설치 전: "plural dirs not detected — INST-OPEN-4 still open"   (정상)
설치 후: "plural dirs ... DETECTED ... may have migrated: [~/.config/opencode/plugins]"   (오탐)
```

원인: projector `_OPENCODE_FIXED_SYMLINKS` 가 `plugins/agent-harness-guards.js` 를 심어 **우리 스스로** `~/.config/opencode/plugins/` 를 항상 생성 → sentinel 4-후보 중 `plugins` 가 매 설치 후 참. INST-OPEN-4 의 마이그레이션 신호는 singular `agent/`·`command/` → plural `skills/`·`commands/`·`agents/` 전환이고 `plugins/` 는 그와 무관하게 우리가 늘 만드는 정당한 디렉터리다. informational(`ok=True` 고정)이라 verify 를 fail 시키진 않으나 detail 정확도가 항상 깨진다. 수정: 후보에서 `plugins` 제거(신호는 skills/commands/agents 로 한정). 저심각, 다음 사이클 처리 가능.

---

## 검증되어 양호한 항목(칭찬)

- **dry_run 디스크 미접촉**: 세 드라이버 모두 temp HOME 이 dry-run 후 완전히 빈 상태(claude 19·codex 55·opencode 51 actions, HOME empty=True). mkdir·record 전에 dry_run 분기가 선다 — 안전 불변식 (d) 통과.
- **INST-D-5**: codex 는 `plugin=True` 여도 symlink projection 루프를 먼저 다 돌고 plugin 배지만 뒤에 붙인다(codex.py:40~131 vs 121). 실측 `plugin=True actions include symlinks: True`. anti-pattern 회피 확인.
- **opencode 동종키-이종타입 conflict**: `_merge_config` 가 `existing` 를 그대로 반환 + `blocked=True` + 파일 미기록(opencode.py:231~236). 안전 불변식 (c) 통과 — 파일 untouched 확인.
- **CLI-gated 체크 graceful degrade**: 세 bootstrap-smoke + opencode drift-watch 모두 `shutil.which(...) is None` 이면 subprocess 없이 `ok=True`+SKIP 반환. 분기 로직 정확(이 샌드박스엔 CLI 3종이 다 있어 present 경로가 실행됨 — absent 경로는 정적으로 확인).
- **check id 유니크**: 현재 데이터로 claude 20·codex 61·opencode 57 전부 DUP 0.
- **codex real-file 가드**가 세 드라이버 중 유일하게 정답 — 이 패턴을 claude·opencode 에 그대로 이식하면 HIGH 해결.

## 참고(비차단)

- already_linked 판정이 드라이버마다 다름: claude/opencode `resolve()==resolve()`, codex `os.readlink` 문자열 비교. 동작상 문제는 없으나(codex step log Decision 2 에 근거 있음) 통일하면 유지보수 편함.
- opencode merge conflict 시 **이미 만든 symlink 는 롤백 안 함** — plan 의 "BLOCKED=stop+report, undo 아님" 지시대로라 의도된 동작(비차단).
