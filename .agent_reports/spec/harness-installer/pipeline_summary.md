# harness-installer — pipeline summary

## v5 (2026-07-14) — release-bound bootstrap

- snapshot: `_internal/versions/v4/prd.md`. v1.0.0 공개 뒤 발견된 raw-main bootstrap과 release archive의 버전 분리 가능성을 계약 위반으로 분류했다.
- public one-line install은 `releases/latest/download/install.sh` asset만 실행하고, 이 asset은 같은 tag의 `distribution.py`와 exact release version을 내장한다.
- version pin은 versioned installer asset URL로 선택하며 latest installer에서 다른 `--version`을 주입하는 경로를 닫는다.
- root `install.sh`는 legacy raw URL을 release asset으로 넘기는 compatibility redirect만 유지한다.
- release workflow는 archive/checksum과 self-contained installer/checksum을 한 tag에서 함께 게시한다.

## v4 (2026-07-14) — clone-free release + automatic packaged update

- snapshot: `_internal/versions/v3/prd.md`. 일반 사용자는 Git clone 대신 GitHub Release archive+SHA-256을 한 줄 bootstrap으로 설치한다.
- XDG data의 immutable `releases/<version>`과 atomic `current` pointer를 사용하고, runtime은 packaged bundle로 활성화한다.
- `harness update`는 managed distribution에서 release updater로 분기하되 linked/foreign runtime과 Git checkout을 건드리지 않는다. checkout에서는 기존 drift/reapply 의미를 유지한다.
- Linux systemd user timer/macOS LaunchAgent 자동 확인, opt-out/pin, safe extraction, activation/state rollback을 구현 계약으로 고정했다.
- README는 “native first, plugins optional”을 독립 홍보 포인트에서 내리고 clone 없는 설치와 다섯 가지 제품 강점을 앞세운다.
- 구현 완료: 실제 archive의 세 runtime packaged activation, safe extraction 공격군, pin/scheduler/pointer/profile rollback, 기존 runtime/profile/extension 및 adaptation 회귀가 통과했다. 독립 보안 리뷰 최종 HIGH/MEDIUM은 0건이다.
- deployment: `v1.0.1` 공개 완료. 네 asset 게시와 public latest isolated install 검증을 통과했다.

## v3 (2026-07-13) — 공개 README 표면 + sync-skills 퇴역

- snapshot: `_internal/versions/v2/prd.md`. 사용자 결정: root README를 plugin/product landing page로 전면 개편하고, false-green prose hash 동기화인 `sync-skills` capability를 퇴역한다.
- 공개 문서 계약: 가치 제안 → 설치 → 바로 쓰기 → 핵심 기능 → 런타임별 배포 차이 → 구조 → deep docs/검증. 제품 전체는 portable harness이며, Claude/Codex native plugin과 OpenCode installer projection의 차이를 숨기지 않는다.
- 검증 소유권: manifest·native projection·adaptation boundary·skill conformance·installer verify는 결정론 도구가 유지한다. README prose는 human-owned review 대상이다. 근거는 `_internal/readme-reference-brief.md`.

## v2 (2026-07-13) — spec update (구현 사이클 1·2 반영)

- snapshot: `_internal/versions/v1/prd.md`. 변경: INST-OPEN-1 확정(hook 채택 2·이월 3·제외 기록), INST-OPEN-3 완료(INSTALL_LAYOUT 514→250줄), INST-OPEN-4 만 잔존(drift-watch 상시 감시로 강등), [cli] verify 절에 채널-인지 계약 추가(실측 오탐 → quick fix 사이클 `harness-installer-fix-verify-gate` 와 동기).
- 구현 현황: 사이클 1(0e6b3fe — CLI 본체·3-런타임 driver·hash-manifest 3-way·Codex plugin wrap, 51/51 PASS) + 사이클 2(8311dcf — Claude plugin content generator·install --plugin·문서 축소, 53/53 PASS). 실환경 verify 로 opencode projection drift 1건 발견·복구 실적.

## v1 (2026-07-12) — 신규 spec 생성

- 계기: 사용자 발화 "claude code와 codex, opencode 등을 바로 플러그인 형태로 쓸 수 있는 installer" (2026-07-12). 라우팅 컨펌 — 새 spec 독립 생성(HLS v3 확장 아님).
- 하드 게이트 근거: `research/cross-platform-agent-frameworks/`(7/9) — GSD hash-manifest 채택 후보 1, Claude plugin 규격 카드, claude-flow 반면교사.
- runtime-currentness 검증(작성 중, 백그라운드 에이전트): Claude Code plugin 은 hooks·bin 까지 탑재 가능(cache self-contained·ephemeral), Codex plugin 은 skills/hooks/MCP/app 4종만(agents .toml 불가 → symlink 병행), OpenCode 는 번들 포맷 부재 + 기존 배선 drift 발견(복수형 디렉토리·`skills.paths` 문서 부재 → INST-OPEN-4).
- 사용자 결정 2건: 2-채널 하이브리드 구조(INST-D-1), CLI 명령 `harness`(INST-D-2).
- 의미↔규칙 경계 체크: 충돌 0 (config merge 충돌 판정도 규칙 처리).
- Step 4 scaffold: worktree `agent_setting-wt/harness-installer-scaffold` 에 headless 분사 (sonnet·fast implementer, ~25분 완주) — 브랜치 커밋 `9792fd3`(skeleton 13 files, 432 insertions) + `20c4f7e`(handoff 보고). 산출: `tools/install/{harness.sh,installer.py,projector,manifest,verifier,drivers/*}` + `adapters/claude/plugin-marketplace/` 대칭 skeleton + `.gitignore` 예외 2줄(Codex 선례 동형). 구문·JSON·CLI 스모크 전부 통과. hash-manifest 는 의도적 `NotImplementedError`(GSD 정독 게이트 준수). 상세 = `_internal/scaffold_v1.md`(브랜치).
- 다음: 사용자 merge 신호 → 브랜치 수확 / 구현 = `autopilot-code` (선행 게이트: GSD `bin/install.js` 정독 + INST-OPEN-4 OpenCode 실측).

- minor(2026-07-13, 사이클 3 반영): INST-D-6 이월 3종 해소 — spec 파이프 hook PLUGIN_DATA env-prefix 탑재(채택 set 2→5, canonical 무수정, 29/29 PASS). PRD OPEN-1 문구 동기. 부수: dispatch-liveness pid 신호(별건 머지)·codex modes projection 재동기.
