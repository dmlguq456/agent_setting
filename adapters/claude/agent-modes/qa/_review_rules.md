# QA Shared Review Rules

> 품질관리팀 라우터가 `code-review`·`plan-review`·`test` 모드 선택 직후 이 파일을 함께 Read 한다. 심각도 출력 골격과 1줄 반환 계약의 단일 원천. 헤더 문구·항목 식별자·항목별 필드·verdict 토큰·표시 언어는 각 모드 파일이 정의한다.

## 적대적 stance (모든 intensity 공통, 단일 원천)

세 모드 모두 dispatch된 intensity와 무관하게 refute-by-default로 검토한다 (`CONVENTIONS §1.1`, `roles/MODES.md` Universal Review Stance). 변경·계획·표면이 틀렸다고 가정하고 이를 깨뜨릴 입력·상태·순서·동시성·환경을 능동적으로 찾으며, 한 부분을 "solid"라 결론 내리기 전 최소 1개의 구체적 실패모드를 명시한다. "문제를 못 찾음"과 "문제가 없음이 입증됨"은 다른 verdict다 — 가용 증거(테스트·런타임 동작·도달 가능한 caller)로 정합성을 확인할 수 없으면 PASS가 아닌 '미입증'으로 보고한다. `test`에서 실패 신호의 부재는 정합성의 증거가 아니며, 증거가 부족하면 PASS 대신 BLOCKED/FAIL을 반환한다. 친절·교육적 톤은 발견을 설명하는 방식에만 적용되고 이 기준을 낮추지 않는다. 이 stance는 각 검토 안에 들어가는 태도이며, 상위 intensity가 추가하는 별도 cross-harness adversary *pass*와는 구별된다.

## Severity Output Skeleton (🔴🟡🟢) — code-review·plan-review

리뷰 산출물은 아래 골격과 섹션 순서를 따른다.

```
## 📋 {mode-defined header}

**검토 대상**: (mode-defined)
**요약**: (1-2 sentences)

---

### 🔴 (must-fix issues)

Per item: **{mode-defined item id}** — problem description + mode-defined fields

(If none: "발견된 문제 없음 ✅" / "No issues found ✅")

---

### 🟡 (suggested improvements)

같은 항목 형태. (If none: 동일한 ✅ 문구)

---

### 🟢 (what is already solid)

- 잘된 부분·좋은 패턴 사용을 구체적으로 언급한다.
```

## Return Format (CRITICAL) — 세 모드 공통

프롬프트에 출력 파일 경로가 지정되면 정확히 한 줄만 반환한다:

```
{output_file_path} -- {verdict}
```

전체 결과는 출력 파일에 쓴다. 반환에 요약·설명·코드 스니펫을 넣지 않는다.
예외: 사용자가 출력 경로 없이 직접 호출하면 전체 결과를 인라인으로 반환한다.
verdict 토큰은 각 모드가 정의한다.
