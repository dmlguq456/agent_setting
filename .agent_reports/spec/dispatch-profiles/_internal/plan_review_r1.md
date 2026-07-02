# plan-review r1 — dispatch-profiles PRD v1 (2026-07-02, 품질관리팀 plan-review, qa=standard)

대상: `spec/dispatch-profiles/prd.md` (반영 전 v1 초안). 전 발견 반영 완료 — 반영 방식은 각 항목 뒤 `→`.

## 🔴 Blocker

- **B1. bootstrap 조립 생성 규칙 미정의** — CLAUDE.md 는 층 구분 마커가 없어 생성기가 "어느 절이 L1인가"를 알 수 없음. 하네스별 source 템플릿·concat 대상 미명시. `--check` 의 대조 기준도 부재.
  → **DP-10 신설**: 층 경계 = 소스 파일 분리. `profiles/templates/bootstrap-<harness>.md`(L0 참조부, L1 처음부터 부재) + `fragments/` 단순 concat. 기존 CLAUDE.md/AGENTS.md 파싱 금지. `--check` = 재조립 대조.

## 🟠 Major

- **M1. `model: sonnet` 을 "portable role tier" 로 인용 — 실제 core/ADAPTATION.md §3 은 역할명만 정의, role→model 매핑 없음. portable 경계("concrete model names belong in adapter documents") 위반.**
  → §3 재정의: 프로필 = **harness-scoped 선언** (top-level 은 카탈로그 단일성 목적, 경계 예외를 profiles/README 에 명시). `model_role`(portable, 권장) XOR `model`(concrete, 결속 하네스 한정) 2단. DP-3 수정.
- **M2. opencode inline-config 조합 미정의** — expose subset 을 파일 투영 vs inline JSON 중 무엇으로 낼지 미정, opencode wrapper 는 home env 를 세팅하지 않아 신규 메커니즘 필요.
  → 채널 고정: XDG 파일 투영(agent-skills 디렉터리), inline 미사용. **v1 범위 = claude+codex, opencode 는 P1** (DP-12).
- **M3. home 세션 상태 수명주기 미정의** — persistent home 재사용 시 transcript 무한 누적 → liveness 오판, `--all` regen 이 live home clobber.
  → **DP-4 재설계**: per-dispatch ephemeral 인스턴스 `homes/<slug>.<name>/` (codex scratch-home idiom). harvest `--mark-done` 시 제거, `--keep-home` 진단 예외.
- **M4. index.tsv 동시성 보호 부재** — flock 없음, rewrite/append 정책 미정.
  → **index.tsv 삭제** (리뷰 권장안 채택): home 경로를 jobs.log 의 (slug, profile) 에서 결정론 유도 (DP-11). 동시성 표면 자체 제거.

## 🟡 Minor

- **m1. `locks:` 필드 = 생성기가 무시하는 장식 설정** → 선언 스키마에서 제거, 생성기 불변식으로만 (DP-2 문구 수정).
- **m2. §8 하이브리드 라우팅 = 스코프 확장** → "v1 구현 범위 외, 별도 사이클" 명시 (방향 기록만 유지).
- **m3. exit 3 소유 불일치** (build-home vs wrapper) → wrapper 단독 소유로 단일화. build-home 은 0/1/2 만.
- **m4. liveness 확장이 claude transcript 레이아웃을 전 하네스에 암묵 적용** → transcript 기반 확장은 claude 한정, codex/opencode 는 기존 로그 채널 유지 (§7 명시).

## 🟢 검증 통과 (리뷰가 확인)

- jobs.log `pipe+=profile=` 후방호환 — 3 reader (liveness 통필드 read / harvest join 보존 / fleet `_parse_pipe` 미지 키 무시) 실코드 대조로 **진짜 무파괴** 확인.
- 참조 정확성 — `link()` clobber 거부, opencode cross-harness 누출 가드, CODEX_HOME 격리 실증, 6필드 스키마 인용 모두 실재.
- CLAUDE_CONFIG_DIR 리스크 처리 (실측 + DP-9 회귀 항목화) 적절.
- depth-1 정합 (§5 L1 근거 ↔ OPERATIONS §5.10 ③).
