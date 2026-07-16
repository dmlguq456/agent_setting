# 최종 보고 — fleet gate-통과 표시

**2026-07-16 · autopilot-code / dev / quick / depth-1 · 브랜치 `fleet-gate-passed` · 커밋 `e41109ed`**

## 요약

PRD §4.9가 2026-07-16에 확정한 gate 통과 증거 소스를 fleet이 소비하도록 구현했다. v10이
"통과 증거가 디스크에 없다"는 이유로 정직 결손(`—`)으로 남겼던 자리를, stage-dispatch v13(SD-56)이
착륙시킨 canonical completion marker로 채웠다. 테스트 519 → 555, 회귀 0.

핵심 판정은 spec 그대로다: **marker 존재 + record의 route_id/route_hash 일치 = 통과**. 그 외
전부(부재·id 불일치·hash 불일치·garbage json)는 `None` = **무주장**이며 `False`가 아니다 —
record에 묶을 수 없는 marker는 반증이 아니라 침묵이므로 미통과·실패로 그리지 않는다.

## 변경 파일

| 파일 | 내용 |
|---|---|
| `tools/fleet/route.py` | `gate_mark()` / `resolve_gate_marks()` 신설, node dict + `summary()`에 `gate_passed` |
| `tools/fleet/render.py` | 과정 뷰 노드 `⊸` 표식, `a` 상세 `gates:` 줄에 통과 표시 |
| `tools/fleet/tests/test_f30_gate_passed.py` | 신규 36건 |
| `tools/fleet/tests/fixtures/completion/rt-5fd84b9bcf8a799c/` | 실물 marker 4건 (verbatim) |
| `tools/fleet/tests/fixtures/route/real_sd13_staged.json` | 그 marker가 실제로 쓰여진 record |
| `adapters/claude/tools/fleet/` | mirror 바이트 동기 (동일 6건) |

## 설계 판단 3가지

**1. 순수성 경계를 지켰다.** marker 읽기는 I/O인데 `build_views()`는 문서화된 PURE 계약(테스트가
`now`를 인자로 주입해 hermetic)이다. 그래서 `resolve_records()`의 형제로 impure 진입점
`resolve_gate_marks()`를 만들고, `build_views`는 `gate_marks` **optional 5번째 인자**만 받게 했다 —
기존 4-positional 호출부·테스트 전부 무영향, `os.stat`/`open`을 예외로 패치한 채 `build_views`를
호출하는 테스트로 pin.

**2. 실물이 writer와 다르다는 걸 발견해 스키마 요구를 좁혔다.** `capability-route.py:241`의 writer는
`sequence`/`completed_at`을 marker에 쓴다. 그런데 실제 착륙한 marker 4건에는 **둘 다 없고**
`schema_version`도 없다(다른 경로로 쓰인 것으로 보인다). writer 코드만 보고 필수 필드로 요구했다면
이 기능이 읽으려던 증거 자체를 거부했을 것이다. 요구 필드는 `route_id`/`route_hash`뿐으로 두고,
이 사실을 테스트로 못박았다(`test_optional_writer_fields_are_not_required`).

**3. 표식 색을 `dim`이 아니라 `gate_t`로 했다.** 과제는 "dim `⊸`"를 예로 들었지만, 통과 노드는
대부분 `done`(= 텍스트 전체가 dim)이라 dim 표식은 노드 자신의 dim 구절에 녹아든다 —
`render.py:101`이 명시적으로 경고하는 병합이다. 기존 디자인 어휘에 이미 있는 `gate_t`
(green-dim, spec-gate 단어가 쓰는 키)를 재사용해 상태 글리프와 진짜로 독립된 차원이 되게 했다.
표식은 별도 세그먼트이지 텍스트에 접합되지 않는다.

## 검증 결과

| 항목 | 결과 |
|---|---|
| 신규 테스트 36건 | **OK** — 통과/route_id 불일치/hash 불일치/부재/garbage/이력 최신 우선 전부 커버 |
| 전체 회귀 `unittest discover -s tools/fleet/tests -t .` | **555 OK** (기준선 519 + 36), 회귀 0 |
| `--json` additive | HEAD 대비 키 경로 diff = 추가 `route[]/nodes[]/gate_passed` 1건, **제거 0건** |
| `--json` live 실측 | route 7건 중 marker 보유한 `rt-5fd84b9bcf8a799c`만 4노드 `true`, 나머지 6건 전부 `null` |
| mirror parity | `rsync` 후 `diff -r` **무출력** |
| live 쓰기 | `.dispatch/completion/` mtime 4건 전부 불변, route record 불변, route.py 정적 read-only 게이트 통과 |

**폭 검사는 정직하게 보고한다.** 120·168열 넘침 0. **60열은 2줄 넘침이 있으나 `git archive HEAD`
기준선에서 동일하게 재현**되는 기존 pulse/mem 헤더 행(route 카드 아님)으로, 이번 변경 기여분은 0이다.
"넘침 0"이 아니라 "신규 넘침 0"이 맞다. 이번 스코프(gate 표식) 밖의 기존 결함이라 손대지 않았다.

표식 자체의 폭 회계는 별도로 pin했다: 같은 flow가 표식 없이 33열/포함 37열이라 36열에서 갈린다 —
표식을 폭 계산에서 뺐다면 folder가 `plan`을 유지한 뒤 36열 카드에 37열을 그렸을 것(표식당 1열
조용한 넘침). 그 경계를 실제로 assert한다.

## 실렌더 (live)

```
▾ [code·dev·standard] rt-5fd84b9b — 4/4 nodes
  plan ✓ ⊸ › execute ✓ ⊸ › test ✓ ⊸ › report ✓ ⊸
  gates: code-plan ⊸, code-execute ⊸, code-test ⊸, code-report ⊸    # a 토글에서만
```

이 route는 4/4 done이라 §5.4 기본 접힘(`▸`) 대상이라 `--once` 기본 출력에는 1행으로만 나온다.
표식은 펼쳤을 때 보인다 — 설계대로다.

## 남은 것 / 후속

- **carryover §1 해소됨.** `plans/2026-07-15_fleet-v10-process-view/_internal/carryover.md` §1의
  재개 조건("worker-route-guard 등이 실제 completion marker를 쓰면 F-28/F-30이 집어간다")이
  충족되어 구현됐다. 예견대로 additive였고 재작업은 없었다 — node dict의 `gate` 자리는 그대로 두고
  `gate_passed`를 옆에 더했다.
- **carryover §2 (detached resource-runner registry)는 여전히 미해소** — canonical 경로가 정의되지
  않아 이번 스코프 밖.
- merge/push는 main 오케스트레이터 몫(브랜치에 커밋만 완료).
- marker writer(`capability-route.py`)와 실물 marker의 필드 불일치(`sequence`/`completed_at` 부재)는
  fleet 쪽에서 tolerant하게 흡수했지만, **stage-dispatch 쪽에서 한 번 확인해 볼 가치가 있다** —
  writer가 아닌 다른 경로가 marker를 쓰고 있다는 신호일 수 있다.

## 산출물

- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_fleet-gate-passed/micro-plan.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_fleet-gate-passed/verification.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_fleet-gate-passed/final_report.md`
