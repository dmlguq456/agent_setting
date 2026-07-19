# Plan self-review — round 1 (code-plan, SD-68)

## 실측 근거 (설계를 확정한 소스 확인)
- `capability-route.py`: `route_hash(payload)`는 route_hash/route_id 외 전 필드 해시 →
  nodes에 스탬프·payload에 digest만 넣으면 자동 봉인(별도 hash 로직 불요). compile line
  221, verify line 225. main `except (ValueError, TOPO.TopologyError)` → exit 64.
- `dispatch-defaults.py`: `DefaultsConfigError`는 **ValueError 비상속**(실측) → compile에서
  ValueError 승격 필수. `query_affinity`는 미지정 칸 `"neutral"` 반환(selector 어휘) →
  스탬프엔 `unspecified` 필요 → 별도 `query_stage_affinity` 헬퍼. `default_config_path()`가
  `DISPATCH_DEFAULTS_CONFIG` env 존중 → 픽스처 오버라이드 재구현 금지.
- route.json(현 사이클): `dispatch_defaults_digest` 부재, 4 노드 전부 depth=2·
  harness_affinity 부재 → 구 route 하위호환 경로 실재(conductor-prompt 경고와 일치).
- wrapper 3종: 동형 pipe 키 루프 확인 — claude:420, codex:517, opencode:483. row 6-탭 필드
  불변, pipe kv 추가는 dict 파서에 무해.
- dispatch-node.py line 178 `subprocess.run(argv)` 후 즉시 종료, attempt_id 미소유 →
  annotate_attempt_row 경로 부적합 → wrapper 인자 passthrough 선택 정당.

## 판단이 갈렸던 지점과 결론
1. **canonicalization: 정규화 파싱 vs 원시 바이트** → 정규화 채택. 사유: 봉인 대상은 효과적
   config지 포맷이 아님(주석 편집 false churn 방지), 검증된 dict만 digest, 결정론.
   plan.md §2에 근거 명시. execute가 반대 선택 시 acceptance ②의 "주석변경→hash불변" 테스트가
   깨지므로 정규화가 계약으로 고정됨.
2. **digest를 direct/quick route에도 기록? uniform** → 채택. selector의 무조건 validate
   선례와 일관, 스키마 균일. 미소 비용. (스탬프는 depth-2 노드만.)
3. **verify 어휘 검사 범위** → 필드 존재 시에만(구 route 하위호환) + 위조 route 결정론 가드.
   §14 v17 "어휘 검증 결정론 대상" 충족.
4. **wrapper 편집이 OUT-of-scope("신규 검증 게이트")에 저촉?** → 아니오. passthrough는
   메타데이터 전달이지 게이트/차단이 아님. SD-68 "차단 장치 신설 금지"와 오히려 정합
   (비교·거부 없음).

## 잔여 리스크 / execute 주의
- wrapper pipe exact-string 단언 스위트 존재 시(회귀에서 발견되면) kv 추가에 맞춰 갱신 —
  형식 계약(6-탭·kv) 불변 범위 내. plan.md §5.3에 명시.
- `_seal_dispatch_defaults`가 nodes를 in-place 변이 → compile은 `nodes`를 이미
  `json.loads(json.dumps(...))`로 deep-copy해 recipe 원본 오염 없음(line 191). 확인됨.
- 픽스처 config의 stage 키는 실제 topologies.json에 validate됨 — autopilot-code는
  plan/execute/test/report만 유효(exec/review 리터럴 키 금지). 테스트 픽스처 작성 시 준수.

## 완결성(§0.5) 자기점검
execute는 plan.md만으로 6개 파일 편집 + 테스트 8케이스 작성 가능. 대화 컨텍스트 불요.
파일별 정확 삽입 지점(라인)·헬퍼 시그니처·예외 승격·env 재사용·커밋 순서 모두 기재.
verdict: PASS 준비 완료.
