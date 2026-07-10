# Step 2 — skills 개정 (surfaces 7-9)

| Surface | 파일 | 변경 |
|---|---|---|
| 7 | `skills/autopilot-code/references/context-and-guards.md` | 기존 "실행 메커니즘" bullet 의 금지 문구를 **main(depth 0)↔headless 쪼개기 금지**로 좁힘(그 우려는 유효). 새 "스테이지 분사" bullet 신설 — conductor 세션 _안_ 에서 스테이지 depth-2 분사가 `standard+` 기본, 과거 "상태 재발굴·연속성 상실" 우려는 산출물 기반 소통으로 해소(파일 로드 비용/파일 매체) 근거 병기, 계약 완결성 의무 + 마이크로-스테이지 inline 경계(SD-OPEN-1). autopilot-code SKILL.md 자체엔 금지 문구 없음(확인). |
| 8 | `skills/autopilot-code/references/dev-pipeline.md` | 상단에 "Stage-dispatch orchestration" 블록 — standard+ 는 conductor 가 `dispatch-headless.py --depth 2 --parent --worker-role code-<stage> --owner --model-role` 로 스테이지 분사, 프롬프트=산출물 경로만, verdict/status 만 읽음, jobs.log·liveness·상한. direct/quick·downgrade·비-headless 런타임은 inline Skill 경로(같은 계약). |
| 9 | `skills/{code-plan,code-execute,code-test,code-report}/SKILL.md` | 각 상단에 "Stage-session entry" 계약 — 입력=산출물 경로(대화 컨텍스트 X), 스테이지-워커 write 클래스 명시, 팀 위임은 세션 _안_ 유지. code-report 는 추가로 step 2 "orchestration memory" 전제를 dispatched 세션에선 산출물 파일 대조로 분기(+Rationale 문장 동기화). |

Decision: sub-skill 은 이미 `Plan Resolution` 으로 입력=경로였음 — "독립 세션 진입점" 은 명문화. code-report 의 in-session memory 가정이 유일한 실질 충돌이라 dispatched 분기 명시.

주의: SKILL.md `description:`/`blurb:` frontmatter 는 미변경 → context-footprint skill-metadata budget 불변.
