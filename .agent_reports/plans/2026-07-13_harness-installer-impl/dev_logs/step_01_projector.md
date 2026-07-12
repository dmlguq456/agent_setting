# Step 1 — projector.py: INSTALL_LAYOUT 심링크 레시피 포팅

## 대상
`tools/install/projector.py` — `_PROJECTION_STUB` + `plan()` (scaffold stub) 을 실제
INSTALL_LAYOUT.md 레시피 데이터 + 계산 로직으로 교체.

## Old → New 요약

- Old: `_PROJECTION_STUB = {"claude": [], "codex": [], "opencode": []}`, `plan()` 은 항상
  빈 리스트만 반환 (scaffold placeholder, TODO 주석만 있음).
- New:
  - runtime 별 `_CLAUDE_TABLE` / `_CODEX_TABLE` / `_OPENCODE_TABLE` — INSTALL_LAYOUT.md 의
    `ln -sfn`/`cp` 나열을 그대로 데이터로 옮김 (action: `symlink`/`copy_once`/`symlink_glob`/
    `delegate`/`merge`).
  - `paths.py` (Phase 0 산출물) 의 `agent_home()`/`resolve_source()`/`runtime_home()` 만 사용
    — 경로 계산 재구현 없음.
  - `_expand(table, runtime, scope)` — 추상 테이블 항목을 concrete plan 항목으로 펼침:
    - `symlink`/`copy_once`: source 존재 확인 후 `{"source", "dest", "source_present": True}`
      또는 부재 시 `{"action": "skip", "reason": ...}`.
    - `symlink_glob`: source_dir 존재 확인 → `Path.glob(pattern)` 으로 개별 파일마다
      concrete `symlink` 항목 생성. source_dir 자체가 없으면 그 glob 은 조용히 스킵(에러 아님).
    - `delegate`/`merge`: source 개념 없음 — `source_present: True` 로 trivial 표시.
  - `plan(runtimes, scope="global")` — `_TABLES.get(rt, [])` 를 `_expand` 로 펼쳐 반환.
    shape 은 기존과 동일 `{runtime: [entry, ...]}`, installer 의 `plan.get(rt, [])` 소비 방식
    변경 없음.

## 각 runtime 표 포팅 내역

- **claude**: `CLAUDE.md README.md core commands skills agents agent-modes hooks utilities
  tools scaffolds loops manifest.json statusline.sh track-toggle.sh` symlink (14개) +
  `settings.json keybindings.json` copy_once (2개) + Windows `install-windows.sh` delegate
  (1개) = 17 테이블 항목 → 18 concrete entries (glob 없음, 1:1 대응 + delegate).
- **codex**: 고정 심링크 17개 (`agent-harness` 포함) + `codex-skills/*` glob + `codex-agents/*.toml`
  glob (agents glob 은 project scope 특례) = 19 테이블 항목 → 54 concrete entries (glob 확장
  포함, scope=global 기준: skills 다수 디렉터리 + agents 8개 toml).
- **opencode**: 고정 심링크 13개 + `opencode-agents/*/*.md` glob + `opencode-commands/*.md`
  glob + opencode.json merge intent = 16 테이블 항목 → 51 concrete entries. 로컬 1.17.13
  singular 배선 (`agent/`, `command/`, `skills.paths`) 유지, plural 전환 안 함 (INST-OPEN-4
  OPEN 유지).

## Decision (판단 콜)

1. **bare-repo-root source 처리** (`agent-harness` 포인터 심링크, codex·opencode 공통):
   테이블에 `source: ""` 로 표시하고 `_resolve_source_path()` 에서 빈 문자열이면
   `paths.agent_home()` 자체를 반환하도록 특례 처리. `paths.resolve_source("")` 은
   `agent_home() / ""` 로도 사실상 같은 결과지만, 의도를 명시적으로 드러내기 위해
   별도 분기로 뺐다 (읽는 사람이 "왜 source 가 빈 문자열이지" 헷갈리지 않게).

2. **codex project-scope agents glob 특례**: `paths.runtime_home("codex", scope)` 는
   scope 값과 무관하게 항상 `~/.codex` 를 반환 (paths.py 자체는 이 특례를 모름 — Phase 0
   산출물 그대로 사용, 재구현 안 함). 그래서 `_dest_dir_for()` 헬퍼에서 `runtime=="codex"
   and dest_subdir=="agents" and scope=="project"` 조건만 별도로 `Path.cwd() / ".codex" /
   "agents"` 로 override. INSTALL_LAYOUT.md 141-142행 "project-scoped install 은 같은 생성
   TOML 을 프로젝트의 `.codex/agents/` 로" 요구사항을 최소 침습으로 만족.

3. **symlink_glob 확장 시점**: `plan()` 호출 시점(즉시, `plan.py` 정의 시점이 아니라)에
   `Path.glob()` 으로 펼친다 — 요청서 지시대로. 정적 테이블에 파일 목록을 미리 박아두지
   않음으로써 `codex-skills/`·`codex-agents/`·`opencode-agents/`·`opencode-commands/` 신규
   파일 추가 시 코드 변경 없이 자동 반영됨.

4. **skip 표현**: symlink_glob 안에서 개별 glob 매치 파일이 사라진 경우(이론상 TOCTOU 레이스
   외엔 발생 안 함)도 동일하게 `{"action": "skip", ...}` 로 낙제 처리 — 상위 symlink/copy_once
   와 같은 포맷으로 통일해 installer 쪽 소비 로직을 단순하게 유지.

## 검증 결과

```
claude total= 18 skips= 0
codex total= 54 skips= 0
opencode total= 51 skips= 0
```

전 runtime skip 0 확인 (plan.md Phase 1 "Done when" 요건 충족). 추가로 codex
`scope="project"` 로 별도 실행해 agents glob 이 `<cwd>/.codex/agents/*.toml` 로 정확히
뒤집히는 것도 확인 (`design-team.toml`, `dev-team.toml`, `editorial-team.toml` 등 dest 가
repo cwd 하위 `.codex/agents/` 로 나옴, `~/.codex/agents/` 아님).

전 과정 read-only — `HOME` 을 `tempfile.mkdtemp()` 임시 디렉터리로 export 해 실행,
실제 `~/.claude`/`~/.codex`/`~/.config/opencode` 는 손대지 않음. `plan()` 자체도 glob +
`.exists()` 조회만 수행하고 어떤 심링크도 생성하지 않음.
