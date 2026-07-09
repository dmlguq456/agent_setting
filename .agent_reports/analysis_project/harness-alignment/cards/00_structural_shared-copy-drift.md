# card 00 — 구조 축: 공유층 물리 복제·divergence (headline)

> 사용자 문제의식("core>adapter>proj 가 매번 어긋난다")의 **메커니즘적 진원지**. 오케스트레이터 직접 검증.

## 사실관계 (검증된 배선)

```
최상위 hooks/ tools/ utilities/   ← 실디렉토리(심링크 아님)
        │  물리 복사본(inode 다름), 바인딩 없음
        ▼
adapters/claude/{hooks,tools,utilities}/

소비 경로:
  Claude 런타임    : settings.json → $HOME/.claude/hooks/*.sh = adapters/claude/hooks/* (복사본)
  Codex/OpenCode   : preflight.sh → $ROOT/hooks/*.sh (공유 최상위 직접 실행)
                     adapters/{codex,opencode}/utilities/* → ../../../utilities/* (공유 symlink)
  Claude core-*    : adapters/claude/hooks/core-first-guard.sh·core-read-marker.sh
                     → exec $AGENT_HOME/hooks/* (공유 위임 = 의도된 wrapper, drift 아님)
  parity 가드      : check-adaptation-boundary.sh → 공유 hooks/*.sh 만 assert
```

핵심 결함: **공유본(portable canonical)과 adapter 복사본(Claude 런타임 실행본)을 동기화하는 강제가 없다.** 가드는 공유본만 검증하고, Claude 는 복사본을 실행한다.

## 검증 근거

| 대상 | 공유 | Claude 복사본 | 증거 |
|---|---|---|---|
| `spec-read-marker.sh` | relative-path fix 有 (`*) fp="$PWD/$fp" ;;`, git `1d97534` 07-01) | fix 無 (git `e83ff5e` 06-29) | `diff` 5줄 · `settings.json:119` 가 복사본 실행 · `check-adaptation-boundary.sh:784` 는 공유본만 assert |
| `harness-status.sh` | 221줄, "expand git status signals"(`f5a98db` 07-01) | 158줄(`d7b1612` 06-30, 확장 이전) | codex/opencode 는 공유 221줄 symlink |
| `mem-distill-dispatch.sh` | — | diff 30줄 | 동커밋 내 divergence |
| `build-manifest.py` | — | diff 15줄 | 동커밋 내 |
| `agent-worklog-state.sh` | neutral 기본값(unset) | 하드코딩 경로(`/home/nas/...`) | diff |
| `core-first-guard.sh`·`core-read-marker.sh` | full impl | 10줄·4줄 wrapper | **의도된 위임 — drift 아님** |

## 발견
- **[S-1] P1(P0후보)** — Claude spec-read-marker 가 relative-path fix 누락, 런타임 stale, 가드는 통과. spec 게이트 오작동 가능.
- **[S-2] P1** — harness-status 공유/Claude 65줄 divergence, Claude 가 git-signal 확장 누락.
- **[S-3] P1** — acceptance test `ADAPTATION_INVENTORY.md:113`("projections, not independent semantic sources")와 물리 복제 사실이 자기모순. `§55/§65` ledger 가 복제·비동기화를 "mixed content projection" 으로만 서술.
- **[S-4] P2** — 그 밖 divergd 복사본 감시 목록.

## 제안 방향 (GSD 종합 대상 — b1/b3)
1. content-parity 를 `check-adaptation-boundary.sh` 에 추가(공유 == adapter 복사본 강제), 또는
2. 복사본을 core-* 처럼 wrapper/symlink 로 전환해 물리 이중화 제거, 또는
3. 단일 canonical 을 선언하고 나머지는 생성물로.
> 즉시 응급패치로는 최소 spec-read-marker·harness-status 두 파일 재동기(S-1/S-2)가 저위험 fix.
