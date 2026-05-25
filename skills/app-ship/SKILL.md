---
name: app-ship
description: "[DEPRECATED — autopilot-app 의 _setup mode_ 가 본 역할 흡수. 신규 호출 X]. 과거: App deployment setup — hosting (Vercel/Fly/Railway), CI/CD (GitHub Actions), env vars, domain. 현재: `/autopilot-app` 호출 시 setup mode 자동 (apps/<name>/ + pipeline_state.yaml 존재 + 사용자 발화 'ship 셋업'·'배포 셋업' 신호)."
argument-hint: "<app name or path>  # DEPRECATED — /autopilot-app setup mode 사용"
---

> **DEPRECATED (2026-05-25)** — autopilot-app 의 setup mode 가 본 역할 흡수. 본 파일은 _레거시 참조_ 용. 실제 ship setup logic 은 `~/.claude/skills/autopilot-app/SKILL.md` 의 `## Procedure → Mode B — setup` 안.

## Language Rule
- Korean output.

## App Resolution

1. `$ARG` 가 폴더 경로면 그것 사용
2. fuzzy search `.claude_reports/apps/*$ARG*`

## Pre-Check

- `phases.qa: done` 검증 → `failed` 면 ship 진행 거부
- git working tree clean 검증 → 더러우면 commit 권고 후 중단

## Forbidden Zones (명시적 요청 없이 X)

본 skill 은 _안내·셋업_ 만. 다음은 _사용자 명령 후_ 만 실행:

- 실제 배포 명령 (`vercel deploy`, `fly deploy` 등) — 안내만, 사용자가 명령 실행
- 결제 정보 입력·credit card 등록
- DNS 직접 변경
- 도메인 구매
- 환경변수 _실제 값_ 입력 (사용자가 dashboard 에서 직접)

## Procedure

### Step 1: 현재 상태 확인

```bash
git remote -v        # GitHub 연결 여부
ls vercel.json fly.toml railway.json 2>/dev/null  # 기존 deploy config
ls .github/workflows/ 2>/dev/null                  # CI 설정
ls .env.example 2>/dev/null                        # env 템플릿
```

### Step 2: 호스팅 선정

사용자 confirm. 스택 기반 권장:

| 스택 | 권장 호스팅 | 이유 |
|---|---|---|
| Next.js | **Vercel** | 공식, edge runtime, zero-config |
| Next.js + heavy backend | Fly.io | full Node.js, region pinning |
| 정적 (Astro, SvelteKit static) | Cloudflare Pages | 빠름, free tier 후함 |
| 컨테이너 (Docker) | Railway | 간편, DB 함께 |
| Mobile (Expo) | EAS Build | RN 공식 |

"Vercel 로 가시겠어요?" 한 줄 확인.

### Step 3: 환경변수 정리

`.env.example` 작성 (실제 값 없음, 키만):

```
# DB
DATABASE_URL=
TURSO_AUTH_TOKEN=

# Auth
AUTH_SECRET=
```

호스팅 dashboard 에서 _실제 값_ 입력 안내 — "이 키들을 Vercel dashboard 의 Environment Variables 에 입력하세요".

### Step 4: CI/CD 셋업

`.github/workflows/deploy.yml` 생성 (사용자 confirm 후):

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v3
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
      - run: pnpm install
      - run: pnpm build
      # Deploy step — provider-specific
```

provider 별 deploy step 추가 (Vercel/Fly/Railway 공식 GitHub Action 사용).

### Step 5: 도메인 (옵션)

사용자가 명시 요청 시:
- DNS 설정 _안내_ (어떤 record 를 어디에 추가하는지)
- 자동 변경 X

### Step 6: 배포 명령 안내

```
ship setup 완료. 첫 배포를 하려면:

1. <provider CLI> 로그인:
   $ vercel login

2. 프로젝트 연결:
   $ vercel link

3. 환경변수 dashboard 에 입력:
   <url>

4. 첫 deploy:
   $ vercel deploy --prod

이 명령들을 실행하면 됩니다. 진행할까요?
```

사용자가 "진행" 명시 시에만 Bash 로 실행. 그 외엔 안내만.

### Step 7: deploy_record.md 작성

`05_ship/deploy_record.md`:

```markdown
# Deployment Record

**Provider**: Vercel
**Setup date**: <date>
**Domain**: <prod url>

## CI/CD
- `.github/workflows/deploy.yml` 생성됨

## 환경변수
- (dashboard 에 입력된 키 목록 — 값 X)

## 첫 배포
- <date>: 첫 deploy 성공

## 다음 사용자 액션
- 도메인 연결 (선택)
- 모니터링 dashboard 확인
```

## Pipeline state 업데이트

`pipeline_state.yaml` 의 `phases.ship` 을 `done` 으로.

## Output

- `.claude_reports/apps/<name>/05_ship/deploy_record.md`
- 프로젝트 루트의 `.github/workflows/deploy.yml` (사용자 confirm 후)
- 프로젝트 루트의 `.env.example`

## Return Format

```
.claude_reports/apps/<name>/05_ship/ -- ✅ ship setup ready (provider: <name>)
```

배포까지 실행 완료 시:
```
.claude_reports/apps/<name>/05_ship/ -- ✅ deployed to <url>
```

## Update agent memory

- 사용자가 자주 쓰는 provider
- 환경변수 패턴 (어떤 키들이 매번 필요한지)
- 도메인·DNS 셋업 patterns
- 자주 만난 배포 함정
