# harness-layer-sync — Spec Pipeline Summary

- **Date**: 2026-07-09
- **Mode**: library + cli (하네스 내부 구조 개선 인프라)
- **Status**: spec done (v1)
- **Placement**: 독립 컴포넌트 `spec/harness-layer-sync/` — 기존 `spec/prd.md`(Unified Memory System)·`spec/agent-fleet-dashboard/`·`spec/dispatch-profiles/` 무수정.

## 배경

사용자 문제의식 "core > adapter > proj 가 매번 어긋난다"의 구조 개선 청사진. 전수 감사(`harness-alignment`, 21건)와 cross-platform framework research(8개 프레임워크)를 종합. 감사가 찾은 메커니즘적 진원지 = **공유층 물리 복제(§S)**, research 가 찾은 유일한 양방향 divergence 실장 = **GSD hash-manifest**.

## Process Log
| Step | Action | Result | Notes |
|---|---|---|---|
| 입력 Read | 감사 3종(summary·findings·card00) + research 5종(summary·06·gsd·multi-harness·claude-flow) | — | 모든 설계 결정 근거를 감사 발견번호(S-1~S-4, b1~b4, 6-1/6-2)·research 카드로 인라인 소급 |
| 실측 교차검증 | projection 체인(`~/.claude`→`claude_setting`→`adapters/claude`) + hooks·tools·utilities 전수 diff census | — | canonical vs Claude 복사본: hooks 12 SAME/6 DIFFER, tools 2/1, utilities 6/3. 파일집합은 동일, 내용만 갈라짐 |
| 실측 교차검증 | dispatch-liveness `PROJ="$AGENT_HOME/projects"` + build-manifest.py 파생 machinery | — | b3 runtime-root 버그 라인 확인 · b4 생성기 기존재 확인 |
| spec | PRD 작성 (lean) | `prd.md` v1 | b1/b3/b4 채택 + 보조 2 + b2 open. 구현 2-phase 분할 |

## 채택 결정 (locked)
- **HLS-1~4 (b1)**: 최상위 공유층 = 유일 canonical. Claude 도 canonical 실행(물리 복사본 collapse). 복제 불가피 파일만 예외목록(wrapper/delta) + hash-manifest 바인딩. build-manifest·가드 증분(신규 아님).
- **HLS-5~6 (b3)**: parity 가드가 런타임 실행본 검증(공유본만 보던 S-1 구멍 차단). runtime-root ≠ AGENT_HOME 명문화 → dispatch-liveness DEAD 오탐 정정.
- **HLS-7 (b4)**: surface 집합 파일시스템 파생, ledger prose = 사유만.
- **HLS-8~9 (보조)**: parity-loss explicit warning(ruler 반면교사) + bootstrap byte-budget 회귀(GSD 차용).
- **HLS-10 (기각)**: 파일복사 스캐폴딩(claude-flow #1834 반면교사)·spec-kit registry·Claude SHA-pin 기각/범위한정.

## 미결 (open — 사용자 논의)
- **HLS-OPEN-1 (b2)**: 포터블 행동 규율(말투·자율·후속동기화·"무조건 브랜치")의 core 승격 범위. 옵션 A(현행)/B(roles)/C(core) + 6-1(무조건 브랜치, 승격 자명)·6-2(응답 메타, 위임 경계) 분리 결정 가능. **DESIGN_PRINCIPLES 가 "adapter single source"로 명시 위임한 자리라 설계 판단** → 전면 확정 보류.

## 구현 선행 조건 (research gate)
GSD `bin/install.js`·`state-transition.cjs` 실코드 line 단위 정독 후 hash-manifest 세부 확정 — 카드는 installer file-ops 미검증이라 명시.

## Next
`/autopilot-code --mode dev "harness-layer-sync 구현"` (worktree). Phase 1(복제제거+가드확장, 저위험) → Phase 2(manifest·INVENTORY 파생·보조). b2 는 사용자 논의 후 별도 사이클. 상세 = PRD §10.

## Version History
- v1 (2026-07-09): 초기 PRD. 감사 harness-alignment + research cross-platform-agent-frameworks 종합 근거.
