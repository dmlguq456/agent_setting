# Autopilot-* 흐름 청사진

> 사용자 향 보고서 — autopilot-* skill 들의 _3 흐름_ (연구개발 / 문서 / 앱) 의 사용자 호출 자리·산출물·서브에이전트 분기 한눈에. _대칭 강제 X — 작업 본질에 맞는 분리_ 원칙.
>
> Source of truth: [`CONVENTIONS.md §6`](CONVENTIONS.md) (정의), [`README.md`](README.md) (entry list).
> 마지막 정돈: 2026-05-25.

---

## 1. 한 화면 청사진

### 1.1. 사용자 호출 단위 흐름 — 3 family

```
[연구·라이브러리 코드]
  autopilot-research / analyze-project  →  autopilot-code  (반복)

[문서 (paper / presentation / proposal / rebuttal)]
  autopilot-research / analyze-project  →  autopilot-draft  →  autopilot-refine  (반복)

[앱 (사용자 대상 소비자 앱)]
  autopilot-research / autopilot-app    →  autopilot-design (옵션)
                                        →  autopilot-code  (앱 mode 자동, 반복)
                                        →  autopilot-app   (가끔 — ship 첫 setup·env·domain·migration)
```

### 1.2. 작업 본질 매핑

|  | 사전 | 신규 의도·셋업 | 자산 작업 (신규·기존) |
|---|---|---|---|
| **연구·라이브러리 코드** | research(academic/tech) + analyze-project(code) | _없음_ — 텅 빈 폴더 autopilot-code 가 신규도 처리 | **autopilot-code** (일반 mode) |
| **문서** | research(academic/market) + analyze-project(paper/doc) | autopilot-draft | autopilot-refine |
| **앱** | research(tech/market) + analyze-project(code) | **autopilot-app** (PRD + 스택 + skeleton — analyze-project 대칭) | **autopilot-code** (앱 mode 자동) + autopilot-app `--mode setup` (보강) |
| **공통 시각** | — | autopilot-design (신규 사이클) | autopilot-design 재호출 |
| **공통 사용자 프로필** | — | analyze-user (init) | analyze-user (update) |

---

## 2. 사용자 호출 자리

### 2.1. 연구·라이브러리 코드

```bash
# 1. 사전 조사 (선택 — 새 분야·외부 baseline 참고할 때만)
/autopilot-research "X 분야 동향" --mode academic   # 논문 survey
/autopilot-research "Y 라이브러리 비교"  --mode technology  # 기술·코드 baseline 비교

# 2. 기존 코드 청사진 (선택 — 이미 있는 코드 위 작업 시)
/analyze-project --mode code

# 3. 작업 entry (반복 호출)
/autopilot-code "X 기능 추가"                    # 새 기능 (dev mode)
/autopilot-code --mode debug "Y 버그·이상 동작"   # 디버그
/autopilot-code "Z 리팩터링"                     # 리팩터링 (dev mode)
```

산출물: `.claude_reports/plans/<date>_<slug>/` 안 누적 (각 작업이 독립 폴더).

### 2.2. 문서 작업

```bash
# 1. 사전
/autopilot-research "X 분야 최근 동향" --mode academic   # paper 사전
/analyze-project --mode paper                            # 참고 paper PDF 영속화
/analyze-project --mode doc                              # reviewer comment·format template 등

# 2. 신규 entry
/autopilot-draft --mode paper "X paper 본문"
/autopilot-draft --mode presentation "Y 발표 자료"
/autopilot-draft --mode doc "Z 보고서·rebuttal·proposal"

# 3. 정정 entry (반복)
/autopilot-refine "X v2 — 검토 의견 반영"
/autopilot-refine "Y figure 교체" --memo memo.md
```

산출물: `.claude_reports/documents/<date>_<name>/` 안 누적. refine 은 _대상 artifact 안 v{N+1}_ 갱신.

### 2.3. 앱 개발

```bash
# 1. 사전 조사 (선택 — 복잡 도메인만)
/autopilot-research "가사관리 reference 앱" --mode market
/autopilot-research "Next.js + Prisma 스택" --mode technology

# 2. 초기 기반 (신규 앱)
/autopilot-app "할 일 관리 웹 앱"
# → PRD (피처·시나리오·API Contract·데이터 모델·화면 흐름)
# → 스택 결정 (Next.js / Expo / SvelteKit / Astro 후보)
# → scaffolding (npx create-next-app 등)
# → skeleton 코드 (빈 layout·routing·DB schema 초안)

# 3. 시각 사이클 (옵션 — UI 있는 자리만)
/autopilot-design --app 가사관리

# 4. 본격 개발 (반복)
/autopilot-code "task 추가·완료·삭제 기능"
# → apps/가사관리/ 발견 → 앱 mode 자동 활성화
# → 디자인팀 critic (UI 변경 자리)
# → DB migration destructive 자리 안내·자동 실행 X
# → push → CI/CD 자동 deploy
# → 산출 apps/가사관리/dev_log/<date>_<slug>/

/autopilot-code "카테고리 색 구분 추가"
/autopilot-code --mode debug "마감일 칸 모바일 터치 어려움"

# 5. 보강 setup (가끔 — 첫 배포·env·domain·migration deploy)
/autopilot-app
# → setup mode 자동 (apps/가사관리/ 발견)
# → 호스팅 선정 (Vercel/Fly/Railway) + CI/CD 파일 + env 가이드 + (옵션) domain
# → 실제 명령은 사용자 직접 실행 (vercel deploy 등 자동 X)
```

산출물: `.claude_reports/apps/<name>/` 한 폴더 안 _전체 흐름 누적_:
```
apps/가사관리/
├── pipeline_state.yaml               ← 현재 상태
├── 00_init/environment_check.md      ← 환경 점검
├── 00_init/stack_decision.md         ← 스택 결정 사유
├── 01_spec/PRD.md                    ← 피처·시나리오·API Contract·데이터 모델
├── 02_design/                        ← (옵션) 디자인 자산
├── dev_log/<date>_<slug>/            ← autopilot-code 가 누적
│   ├── 2026-06-15_add_category/
│   ├── 2026-06-18_debug_mobile/
│   └── ...
├── 05_ship/deploy_record.md          ← ship 첫 setup
└── _internal/                        ← 백업·버전·reviewer 로그
```

---

## 3. 사용자 주도성·서브에이전트 분기

### 3.1. 사용자 주도성 — 명시 호출 단위

각 _entry skill_ 이 _자연어 한 줄 발화_ 로 호출되고, 메인 Claude 가 _옵션 자동 구성 + 자연어 요약 컨펌_ 거쳐 invoke. _CONFIRM Gate 4 갈래 응답_ (진행 / 수정 — refine v2 / back-jump — 이전 phase / 중단). 발화 모호 시 옵션 다시 물음 (임의 추측 X).

사용자는 _운전자_ — 발화로 다음 의도 결정. Claude 는 _orchestrator + 보조_.

### 3.2. 서브에이전트 분기 (autopilot-* 내부 라우팅)

각 entry skill 이 _내부에서_ sub-skill / agent 분기 호출. 사용자는 _이름 명시 X_ — entry skill 한 줄만.

| entry | 내부 분기 |
|---|---|
| **autopilot-research** | 연구팀 mode=research-survey (자료 수집·요약) + 자료팀 mode=browser-fetch / pdf-extract / web-image-search (외부 자료) + 연구팀 mode=fact-check (verbatim cards) |
| **analyze-project** | 단일 skill 안 logic — code/paper/doc mode 별 자체 분석 |
| **autopilot-app** | (init mode) 기획팀 (PRD 위임 자리만) + 자료팀 (research 결과 import) | (setup mode) 호스팅 선정 logic + CI/CD 파일 생성 |
| **autopilot-design** | 디자인팀 mode=maker (컴포넌트·시각 자산) + 디자인팀 mode=critic (비평) + 자료팀 mode=web-image-search (외부 reference) |
| **autopilot-code** (일반) | 기획팀 (code-plan) + 개발팀 (code-execute) + 품질관리팀 mode=code-review·test (code-test) + 연구팀 mode=plan-review |
| **autopilot-code** (앱 mode) | 위 + **디자인팀 mode=critic** (UI 변경 자리 자동 호출) + DB migration 안전 logic + push 자동 deploy 인지 |
| **autopilot-draft** | 자료팀 (figure 자산·data 분석·외부 reference) + 개발팀 (draft writing) + 편집팀 mode=polish (한국어 다듬기) + 연구팀 mode=fact-check (citation·venue·metric) |
| **autopilot-refine** | 위 autopilot-draft 와 동일 (재활용) + 편집팀 mode=review (read-only 점검) |
| **analyze-user** | 자료팀 (사용자 산출물 cross-project 수집) + 편집팀 mode=review (메모리 누적 검증) |

### 3.3. _운전자가 누구인가_ — 흐름 자체 통제

사용자가 운전자 — 매 호출이 _명시 의도 단위_. 내부 sub-skill 들은 _사용자 호출 X_, autopilot-* 가 자동 orchestration. 사용자 호출 entry 9 개 (위 표) 외 다른 호출 자리 _거의 없음_.

---

## 4. 산출물 폴더 컨벤션

### 4.1. 한 프로젝트 = 한 폴더

| 프로젝트 종류 | 폴더 구조 |
|---|---|
| 연구·라이브러리 코드 | `<proj>/.claude_reports/plans/<date>_<slug>/` 별 누적 (각 task 독립) |
| 문서 | `<proj>/.claude_reports/documents/<date>_<name>/` |
| 앱 | `<proj>/.claude_reports/apps/<app>/` 안 _전체 흐름 누적_ (PRD + dev_log + 05_ship) |
| 사전 조사 | `<proj>/.claude_reports/research/<topic>/` |
| 사전 분석 | `<proj>/.claude_reports/analysis_project/<mode>/` |

### 4.2. 앱 자리의 _한 폴더 누적_ 가치

사용자가 _내 앱의 전체 흐름_ 보려면 `apps/<name>/` 한 폴더만 보면 됨. PRD·디자인·dev_log·ship 모두 그 안. 두 폴더 다니지 않음.

### 4.3. 산출물 도메인 분화 (앱 자리만)

```
apps/<name>/
├── 01_spec/
│   ├── PRD.md            ← 전체 청사진
│   ├── api_contract.md   ← 백·프론트 공유
│   ├── data_model.md     ← DB
│   └── ui_flow.md        ← 프론트
├── dev_log/<date>_<slug>/
│   ├── plan.md
│   ├── backend/          ← 백 변경
│   ├── frontend/         ← 프론트 변경
│   ├── db/               ← migration 기록
│   └── external/         ← 외부 service·SDK 통합
└── 05_ship/
    ├── hosting.md
    ├── ci_cd.md
    ├── env_vars.md
    └── domain.md
```

사용자가 _백만·프론트만·DB migration 만·외부 service 통합만_ 원하면 sub-folder 하나만 봄.

---

## 5. 비개발자용 — 앱 개발 표준 흐름 (참고)

### 5.1. 앱 = 3 부품 + 사이클

```
[사용자 화면 (프론트엔드)] ←─ API ─→ [서버 로직 (백엔드)] ←─→ [데이터 저장소 (DB)]
       ↑                                   ↑                            ↑
   사용자가 보는 것                요청 받아 처리·인증·권한            영구 보관
   버튼·폼·페이지                     비즈니스 규칙                  user / task / log
```

| 용어 | 의미 |
|---|---|
| **프론트엔드** | 사용자가 _직접 보는_ 화면 |
| **백엔드** | _서버_ 요청 처리 logic. 사용자는 직접 안 봄 |
| **DB** | 영구 보관소. 앱 꺼져도 남음 |
| **API** | 프론트 ↔ 백 _공유 약속_ |
| **배포** | 인터넷에 올려 사용자가 쓸 수 있게 |

### 5.2. 1 사이클 = MVP 하나

한 번에 _완벽한 앱_ 못 만듦. 작게 (P0 1-3 개) → 써보고 → 부족함 발견 → 다음 사이클. 첫 사이클은 _MVP (Minimal Viable Product)_.

### 5.3. 단계별 사용자 결정 무게

| 단계 | 무게 | 비고 |
|---|---|---|
| 1. PRD (autopilot-app) | 🔴 큼 | 만들 _것 자체_ 결정 — 빗나가면 build 다 끝나도 _틀린 것_ |
| 2. 디자인 (autopilot-design) | 🟡 중 | 색·폰트 — 취향. default 무난 |
| 3. 본격 개발 (autopilot-code) | 🟢 작 | 결과만 확인 |
| 4. 보강 setup (autopilot-app `--mode setup`) | 🟡 중 | 호스팅 선택·DNS·env. 자동 X — 사용자 직접 |
| 5. iteration | 🔴 큼 | 써보고 _다음 의도_ 표현 |

---

## 6. DEPRECATED — 정리 자리 (2026-05-25)

다음 sub-skill 은 _레거시 참조_ 용으로 파일 보존, 신규 호출 X. 본 흐름 청사진의 _진짜 자리_ 가 어디인지 명확히:

| DEPRECATED | 흡수 자리 |
|---|---|
| `app-build` | `autopilot-code` 의 앱 mode |
| `app-qa` | `autopilot-code` 앱 mode 안 검증 단계 (code-test + 품질관리팀 code-review + 디자인팀 critic) |
| `app-ship` | `autopilot-app --mode setup` |
| `app-iterate` | `autopilot-code` 호출 자체가 iteration |

본 흡수는 _작업 본질에 맞는 분리_ 원칙 적용 결과:
- 앱 코드 변경 = 일반 코드 변경과 _본질 동일_ → autopilot-code 한 skill 통합
- _앱 특수성_ (디자인팀 critic / DB 안전 / push 자동 deploy) 는 _컨텍스트 자동 감지_ 로 처리

---

## 7. 자주 묻는 자리

### Q. 이미 chat 으로 만든 앱이 있다. autopilot-app 부터 시작?

A. **부분 가능**. autopilot-app 의 init mode 는 _신규 cold start_ 기준. 이미 있는 앱은:
1. `cd 가사관리앱 && /analyze-project --mode code` ← 현재 청사진 영속화
2. 새 기능 추가 → `/autopilot-code "X 기능"` ← 앱 mode 자동 (apps/ 부재여도 package.json + UI framework 감지)
3. PRD 부재면 → `/autopilot-app --mode init` 으로 _기존 코드 → PRD 역추출_ 시도 (사용자 검토 부담 있음)

### Q. 디자인 사이클은 _초기 한 번_ 만?

A. **아니다**. _토큰 (색·폰트·간격)_ 은 안정, _컴포넌트_ 는 cycle 마다 추가·수정 잦음. autopilot-design 재호출 시 _확장 mode_ — 기존 토큰 보존하며 새 컴포넌트만 추가.

### Q. ship 은 매번 호출?

A. **아니다**. _첫 setup_ 만 한 번 (`vercel link` / CI/CD 파일 / env). 이후는 _git push → CI/CD 자동 deploy_. autopilot-app `--mode setup` 은 _가끔 보강_ (env 변경·domain·migration deploy) 자리만.

### Q. autopilot-code 가 어떻게 앱 vs 라이브러리 mode 자동 감지?

A. cwd 검사 — `apps/<name>/pipeline_state.yaml` 또는 `package.json` 의 UI framework (Next.js / Expo / SvelteKit / Astro / Vite+React) 발견 시 _앱 mode_. 그 외 _일반 mode_. 활성화 시 사용자에 명시 보고.

### Q. 백/프론트/DB 가 어떻게 잘 나뉘어 짜였는지 확인?

A. `apps/<name>/01_spec/PRD.md` 의 _API Contract / 데이터 모델 / ui_flow_ 섹션이 _경계_ 명시. `dev_log/<date>_<slug>/{backend, frontend, db, external}/` 폴더 분화 (산출물 도메인 분화). 본 두 자리만 봐도 구조 잡힘.

---

## 8. 참고

- 정의 source: [`CONVENTIONS.md §6`](CONVENTIONS.md)
- skill entry list: [`README.md`](README.md)
- 자연어 발화 패턴: [`CLAUDE.md`](CLAUDE.md) §6 (autopilot-* 호출 패턴)
- 작업 본질 매트릭스: 본 문서 §1.2

이후 _사용 중 부딪치는 자리_ 발견되면 본 청사진에 반영 — 추측보다 부딪쳐 본 정정이 정확.
