# browser-acceptance

실행 중인 앱을 브라우저로 검수하는 QA/verification worker용 공통 primitive.
계약은 `spec/browser-acceptance/prd.md`(BA-1~6)가 소유한다. 즉석 스크립트로
반복된 4계열 실수(top-level await, 미개방 disclosure, whole-page selector,
mount 미대기)를 이 라이브러리 경유로 차단한다.

- **CJS-safe**: `require()` 즉시 사용, top-level await 없음.
- **주입식·0-dependency**: Playwright `page`와 axe-core 소스는 호출자가 주입.
  `resolvePlaywright()`/`resolveAxeSource()`는 호출 cwd → `tools/design-mcp`
  순으로 기존 설치만 찾고, 없으면 명시 오류로 닫는다.
- **판정은 호출자 소유**: 라이브러리는 증거 수집과 결정론 verdict 집계만.

## 사용 예 (CJS)

```js
const ba = require("<agent-home>/tools/browser-acceptance");

async function acceptReader(baseUrl, evidenceDir) {
  const { chromium } = ba.resolvePlaywright();
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const consoleCapture = ba.captureConsole(page);          // ④ 콘솔/페이지 오류 수집
  const result = ba.createResult({ url: `${baseUrl}/reader`, scope: "#reader-root" });

  await ba.gotoAndWaitMount(page, result.url, "#reader-root"); // ① mount 대기
  await ba.openDisclosure(page, '[data-testid="hubs-toggle"]'); // ③ 접힌 그룹 열기

  const reader = ba.scoped(page, "#reader-root");           // ② scope 강제
  result.checks.push({
    id: "readonly-controls",
    verdict: (await reader.count("input:not([readonly])")) === 0 ? "PASS" : "FAIL",
  });

  const axe = await ba.runScopedAxe(page, {                 // ⑤ scoped Axe
    scope: "#reader-root",
    axeSourcePath: ba.resolveAxeSource(),
  });
  result.axe = axe;
  result.screenshots.push(await ba.takeScreenshot(page, evidenceDir, "reader"));
  result.console_errors = consoleCapture.stop();

  const evidence = ba.writeEvidence(evidenceDir, result);   // ⑥ result.json + verdict
  await browser.close();
  return evidence; // { path, verdict: "PASS" | "FAIL" }
}
```

## 검증

- 단위 게이트(브라우저 불요): `node --test tools/browser-acceptance/test/`
- 실브라우저 통합 acceptance는 첫 소비 앱 사이클에서 회수한다(BA-OPEN-1).
