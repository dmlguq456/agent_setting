# Examples

### 예시 1 — 첫 Vercel 셋업

```
/autopilot-ship "가사관리앱 배포 셋업"
→ spec/가사관리/ 발견, ship.md 부재 → 첫 ship setup
→ stack: Next.js + Prisma + Turso 인지 → Vercel 권장
→ .env.example 키 list (DATABASE_URL / NEXT_PUBLIC_X / ...)
→ vercel.json (선택) + GitHub Actions deploy.yml
→ 배포 명령 안내: vercel login / link / deploy --prod
→ spec/가사관리/ship.md 작성
```

### 예시 2 — 환경 변수 변경 (재호출)

```
/autopilot-ship "STRIPE_KEY 환경 변수 추가"
→ ship.md 존재 → 재호출 자리
→ .env.example 에 STRIPE_KEY 키 추가
→ ship.md env vars 자리 갱신
→ 사용자 안내: Vercel dashboard 에서 실제 값 입력
```

### 예시 3 — 도메인 연결 (재호출)

```
/autopilot-ship "homemanager.app 도메인 연결"
→ DNS A 레코드 / CNAME 안내
→ Vercel dashboard 에서 domain 추가 안내
→ ship.md Domain 자리 갱신
```
