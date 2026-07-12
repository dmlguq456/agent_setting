# harness-installer 구현 사이클 — 선행 게이트 입력 (2026-07-13)

> code-plan 스테이지는 본 파일의 핵심을 `plans/<slug>/_internal/` 로 옮겨 durable 하게 남길 것.
> (durable 복사본 — 원본 tmp: `/tmp/claude-1003/-home-Uihyeop-agent-setting/dc8f97ee-d5eb-48a0-91b1-92991d221e70/scratchpad/impl-inputs.md`. plan 은 §A/§B/§C 참조 시 이 경로를 인용한다.)

## A. GSD bin/install.js 실코드 정독 (HLS §3.2 게이트 통과 — 2026-07-13, open-gsd/gsd-core@next)

### 핵심 메커니즘 (line-grounded)
1. **Manifest**: `<configDir>/gsd-file-manifest.json` — `{version, timestamp, mode, files: {relPath: sha256hex}}`. per-file SHA-256, **설치 후 디스크 실바이트** 기준(transform 후). 매 install 끝에 재작성(늦은 표면 생성 후 재작성 포함), uninstall 시 삭제. 사용자 소유 파일(`USER_OWNED_ARTIFACTS`)은 manifest 에서 제외(#2771 — 안 빼면 매 재설치가 가짜 patch 를 flag).
2. **Drift 감지 타이밍**: 상시 감시가 아니라 **다음 installer 실행 시작 시** — wipe _전_ `saveLocalPatches` 가 구 manifest vs 디스크 diff. 상태는 이진(unmodified/user-modified); upstream-changed 분류는 reapply 의 3-way 로 미룸.
3. **백업 채널 2개 (연구 카드가 하나로 뭉뚱그렸던 것)**: manifest-hash 불일치 파일 → `gsd-local-patches/` (installer, **full-file copy** — .patch 형식 아님) / 관리 디렉토리 안 manifest 미등재 사용자-추가 파일 → `gsd-user-files-backup/` (update workflow 의 detect-custom-files).
4. **3-way 의 진짜 enabler = `gsd-pristine/`** + `backup-meta.json.pristine_hashes` — 수정된 파일의 구-릴리스 원본만 보관. GSD 는 설치 시점에 pristine 을 안 떠서 hash-검증 재생성 기계(#3407/#934)가 필요해졌음.
5. **Reapply 는 LLM prose workflow** (merge 알고리즘 아님) + **결정론 verifier 가 게이트** (`verify-reapply-patches.cjs` — 백업본의 유의미 라인이 병합본에 substring 존재하는지; LLM 의 거짓 "verified: yes" 방지 #2969). 충돌 = 대화형, conflict marker 파일 기록 없음.
6. **소유 경계 3중**: 전체 소유 디렉토리(재귀 wipe: `gsd-core/`·`commands/gsd/`) + prefix 스코프 공유 디렉토리(`agents/`·`hooks/`·`skills/` 의 `gsd-*` 만) + **enumerate 된 파일 리스트**(regex 아님 — regex 는 #941 버그). 공유 디렉토리는 비었을 때만 rmdir.
7. **경로 안전**: manifest 유래 relPath 전수 검증 — 절대경로·`..`·NUL·symlink 탈출 거부 (manifest 는 공격자-영향 가능 상태).
8. **버전**: installer 자체는 무조건 wipe+재설치(멱등성=클린 wipe+manifest 재작성). already-latest·채널(latest/next 태그만, 임의 X.Y.Z pin 없음)은 update workflow 측. 신뢰 버전 판정은 마커 2개(VERSION+구조 파일) 동시 요구. installed > latest = dev-install 로 다운그레이드 거부.

### 우리 installer 채택 노트 (정독 에이전트 결론)
- **복사**: per-file SHA-256 manifest 구조 / saveLocalPatches-before-wipe 순서 불변식 / backup-meta.json(from_version+pristine_hashes) / 소유 3중 모델(리스트, regex 금지) / 경로 안전 가드 / (LLM 병합 시) 결정론 post-merge verifier.
- **단순화 (우리 이점)**: **설치 시점에 pristine snapshot 을 뜬다** → GSD 의 재생성 기계 전부 불필요 + 3-way 베이스라인 항상 보장 → reapply 를 prose workflow 대신 **진짜 `git merge-file`/diff3 (conflict marker)** 로 가능. 백업 디렉토리도 1개로 통합 가능(감지 시 manifest 미등재 조건을 같은 pre-wipe pass 에 흡수).
- **함정**: pristine 은 반드시 **구-릴리스 바이트** (새 릴리스로 갱신하면 delta 반전 #3407) / "전부 기계적 diff 로 보임" 을 skip 경로로 만들지 말 것(hash 불일치 = 사용자 콘텐츠 존재 불변식) / 사용자 소유 파일 manifest 제외 / uninstall 위생(manifest 삭제·enumerate 만 제거·빈 디렉토리만 rmdir).

## B. OpenCode 실측 (INST-OPEN-4 데이터, 2026-07-13)

- 로컬 opencode **1.17.13**. 현행 배선 = **단수형** `~/.config/opencode/agent/`·`command/` (실존 확인) — 과거 Migration Order 검증 통과 이력 있음.
- 복수형 디렉토리(`skills/`·`agents/`·`commands/`) 로컬 **부재**. 현행 공식 문서는 복수형 + `skills.paths` config key 부재(대신 `permission.skill` 규칙) — 문서 vs 로컬 배선 drift.
- **plan 권고 방향**: 이번 사이클은 로컬 1.17.13 기준 현행 배선 유지 + verify check 는 실측 기반으로 작성. 복수형 migration 은 별도 사이클(INST-OPEN-4 는 PRD OPEN 유지). 단, verifier 의 opencode check 에 "문서-배선 drift 감시" 항목 하나를 넣어 향후 버전업 시 표면화되게.

## C. 채택 확정 사항 재확인 (PRD 준수)

- hash-manifest 대상 = installer 가 **복사**한 파일만 (symlink 제외, plugin cache 제외) — GSD 와 달리 우리 dev 채널은 symlink 위주라 manifest 표면이 작음.
- 소유 경계: manifest 등재분만 관리. runtime credentials/sessions/projects 불가침.
- 테스트는 실제 runtime home 을 건드리지 말 것 — temp HOME (mktemp) 방식 (INSTALL_LAYOUT Migration Order 검증 선례).
