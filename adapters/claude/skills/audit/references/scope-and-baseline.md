### Stage A — Detect artifact type

1. Resolve `<artifact_path>` to an absolute directory path.
2. Inspect path prefix:
   - `<artifact-root>/plans/*` → **plans** type (autopilot-code dev/debug plan)
   - `<artifact-root>/research/*` → **research** type (field survey)
   - `<artifact-root>/documents/*` → **documents** type (doc strategy + draft)
   - Other → error: "audit은 <artifact-root>/{plans,research,documents}/* 산출물 전용. resolved path: {path}"
3. Print one-line to user (Korean): `Type 인식: {type} — {artifact short name}`.

### Stage B — Determine effective scope

**우선순위**:
1. **사용자가 `--scope <value>`를 명시한 경우 (1순위, override)** — 그 값을 그대로 사용. type-specific aspect group으로 매핑하여 적용 (아래 표 참조). 매핑이 N/A인 경우(예: `--scope coverage` on plans) 한 줄 warn 후 빈 aspect set 반환.
2. **명시 없음 (default = `auto`)** — Stage B.1 자동 판단 로직 실행.

#### Stage B.1 — Auto-scope detection (artifact 특성 기반)

artifact의 다음 단서를 _순차적으로_ 읽어 적절한 aspect set 결정:

**documents type:**
| 단서 | 우선 aspect | 이유 |
|---|---|---|
| `pipeline_summary.md` frontmatter `mode: presentation` | facts + cross-ref + coverage + **structure (§presentation-0 슬라이드 분량 자가 검사 — bullet 5~6 줄 / 키워드 ≤ 10 단어 / 그림·표 ≥ 60% / 표 6×5)** | slide claim 정확성 + cards 인용 완전성 + 16:9 분량 검증 (PPT 옮긴 시점 깨짐 사전 차단) |
| `mode: paper` | facts + style + cross-ref | 논문 citation 양식 + claim 검증 + paste-ready 의도면 §paper natural-integration rule 준수 |
| `mode: doc` (task description 안 _peer review_ / _rebuttal-response_ 의도) | structure + cross-ref | review form 양식 / reviewer point 대응 |
| `mode: doc` (그 외 — 보고서 / 제안서 / blog / memo) | style + structure | 양식 일관성 + 산출물 구조 |
| `pipeline_summary.md` 버전 히스토리 행 수 ≥ 10 (누적 drift 의심) | **all** | refine 다회 누적 → 종합 점검 |
| 위 단서 미발견 / 정보 부족 | **all** | 안전 default |

**research type:**
| 단서 | 우선 aspect | 이유 |
|---|---|---|
| chapters (`01_*.md ~ NN_*.md`) 존재 + `cards/` 존재 | **all** | 종합 (Tier + coverage + cards 정합성 + cross-card) |
| `cards/` only (chapters 없음) | cards 정합성 + cross-card | 카드 자체 점검 |
| chapters only (cards 없음) | Tier consistency + coverage | 인용 정합성 |

**plans type:**
| 단서 | 우선 aspect | 이유 |
|---|---|---|
| `status: done` + `test_logs/test_report.md` 존재 | test results + code review + semantic-deterministic consistency | 완료된 plan의 실행 정합성 — semantic-deterministic consistency 는 Step 3d 통과 후 코드 수정으로 spec 의미요구 ↔ 구현이 어긋났는지 _drift 재검출_ (중복비용 아님, 다른 시점) |
| `status: done` + test_logs 부재 | code review + TODO·미구현 + semantic-deterministic consistency | dev review 잔존 issue + 미완료 항목 |
| `status: partial` or `status: failed` | TODO·미구현 + code review + semantic-deterministic consistency | 실패 항목 + reviewer 의견 우선 |
| `status: active` | TODO·미구현 | 진행 중 — 다른 aspect는 미완료 상태 |

**Output to chat** (자동 판단 시):
```
Auto-scope: {aspect 1} + {aspect 2} + ... ({이유 한 줄})
```
사용자 명시 시:
```
Scope: {value} (사용자 지정, override)
```

#### Stage B.2 — Type-specific aspect mapping (when `--scope <value>` is given)

| `--scope` | documents | research | plans |
|---|---|---|---|
| `facts` | facts | cards 정합성 | test results + TODO·미구현 |
| `style` | style | Tier consistency | lint |
| `structure` | structure | coverage | code review |
| `cross-ref` | cross-ref | cross-card | N/A (warn) |
| `coverage` | coverage | coverage | N/A (warn) |
| `all` | facts + style + structure + cross-ref + coverage | cards 정합성 + Tier + coverage + cross-card | test results + lint + code review + TODO·미구현 + semantic-deterministic consistency |

**Why `coverage` is new for documents**: the Stage B.5 regex detector can only flag _present_ claims in `new_text` — it cannot, by construction, flag _absent_ claims (e.g., UniSE missing from a timeline). Omission requires a separate _set-diff_ mechanism. The `coverage` aspect fills this: reports the difference between the full cards source vs cards actually cited in the draft. Without it, UniSE-class omissions recur.

### Stage B.5 — Minor log baseline ingestion (doc / research 전용)

plans type은 본 단계 skip (minor log 컨벤션 없음).

**입력**:
- `pipeline_summary.md`의 `## 마이너 변경 로그 (v{N} → next major 누적)` 섹션 (있으면)
- `_internal/versions/v{N}/` 가장 최근 major snapshot 디렉토리 (있으면)

**동작**:

1. `## 마이너 변경 로그` 섹션 파싱 — 각 entry의 다음 정보 수집:
   - 버전 (`v{N}_M`)
   - 일시
   - Files touched (경로 list)
   - Audit-flag (`facts`/`style`/`structure`/`cross-ref`/`coverage` 중 표시된 것)
   - Trigger / Rationale (요약 인용)

2. 마지막 major snapshot vs 현재 artifact 디렉토리 diff:
   ```bash
   diff -ruN _internal/versions/v{N}/ {artifact_root} \
     --exclude=_internal --exclude=pipeline_summary.md \
     > /tmp/audit_p1_diff.txt
   ```
   (`_internal/`과 `pipeline_summary.md`는 audit log/version 메타라 diff에서 제외.)

3. 두 정보를 cross-correlate — 각 minor entry의 audit-flag를 현재 stage C aspect set에 _bias_로 전달:
   - audit-flag에 `facts`가 있는 minor가 N개 → Stage C `facts` lint에서 해당 file의 diff 영역을 우선 검사.
   - audit-flag가 `none`인 minor — Stage C는 default behavior로 점검 (특별 bias 없음).

4. 산출: `p1_findings` dict (minor entry별 변경 요지 + cross-correlate 결과)를 Stage D 보고용으로 보관.

**chat 출력 (1줄)**:
```
P1 baseline: v{N} snapshot 발견, 누적 minor {count}건 ingest (audit-flag 집계: facts={A} / style={B} / structure={C} / cross-ref={D} / coverage={E})
```

snapshot 또는 minor log 부재 시:
```
P1 baseline: skipped — last major snapshot 또는 minor log 부재. P2 only.
```
