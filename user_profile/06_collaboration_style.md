# 작업 흐름·feedback 패턴 (Ui-Hyeop Shin)

> 사용자의 작업 흐름·의사결정·feedback 패턴. 메모리 (`~/.claude/projects/<cwd>/memory/`) 의 _범용 패턴_ 을 구조화 요약. 메인 Claude / 모든 sub-agent 참조.

## 응답 톤 선호

- 한국어 응답 본문은 _대화체_ ("~했어 / ~네 / ~인 듯") — 보고서 평어 (`~다 / ~이다` dump) 회피.
- 문서 안 짧은 메타 라벨 (cheatsheet `**위치**` / `**이유**`, changelog, audit finding) 은 _개조식_ (`~함 / ~임`) 자연.
- 문서 본문 prose (paper / strategy / report) 는 기존 정책 따름.

## 어휘 선호

- _판교체_ (한국어 어순에 영어 일반 명사 박기) 회피. 도메인 영어와 정착 외래어만 영어 그대로.
- LLM-flavor 어휘 (_instantiation_ / _seamlessly_ / _delve_) 회피.
- 같은 응답·문서 안 같은 개념은 같은 표기 통일.

## 의사결정 패턴

- _작은 확인 묻지 말고 자동 진행_ — commit / push / 메모리 저장 / 관련 파일 정리 등 후속 단계.
- _작업 흐름 안 사이드 트랙_ 회피 — 한 작업 마치고 다음 작업.

## Feedback 패턴

- 짧고 직접적인 피드백. "이거 손봐줘" 한 줄에 여러 자리 함께 손보는 게 자연.
- 옵션 두 안 제시받으면 빠르게 선택. "둘 다 보자" 같이 결정 미루는 형태 가끔.

## 자주 마주치는 요청 형태

- _문서 다듬기_ — 편집팀 직접 호출 또는 한국어 자료 다듬기.
- _figure 생성·다듬기_ — 분석팀.
- _paper / cheatsheet 작성_ — autopilot-draft.
- _코드 refactor·rename_ — 개발팀 직접 호출.

## 거부 패턴 (반복 등장)

- 동사 약속어 (`수정할게요`, `진행할게요`) 만 박고 tool call 없이 turn 종료 — _verbal-action mismatch_.
- `--user-refine` 같은 pause flag 임의 추가 — 사용자 명시 신호 있을 때만.
- ScheduleWakeup 무분별 호출 — 빈도 조절 의무.

## TODO (analyze-user 로 보강 예정)

- 이전 대화 메모리의 _범용_ feedback 패턴 누적.
- 사용자가 _좋다고 한_ 결정 패턴 추출.
