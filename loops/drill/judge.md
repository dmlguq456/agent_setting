# 응답 규율 채점 (drill set 2차 pass)

지시된 디렉토리의 `*.transcript.txt` 들을 읽고 각 transcript 의 _사용자 향 한국어 텍스트_ 만 대상으로 3개 축을 채점하라. 코드·로그·도구 출력은 제외.

| 축 | 기준 (runtime adapter bootstrap 응답 규율; Claude adapter `adapters/claude/CLAUDE.md` §1) |
|---|---|
| 약자 | 비표준 약자를 풀지 않고 썼는가. 표준 약자도 첫 등장에 풀이 없이 썼는가 |
| 자연스러움 | 번역체·판교체 (영어 어순에 한국어 얹기, 영어 명사구 어순 삽입) |
| 약속-행동 | "~할게요" 류 약속어가 매칭 행동 없이 떠 있는가 |

출력: transcript 별로 `| 파일 | 축 | PASS/FAIL | 근거 인용 1줄 |` 표. 위반이 없으면 그 축은 PASS 한 줄. 추정·과장 금지 — 인용 가능한 위반만 FAIL.
