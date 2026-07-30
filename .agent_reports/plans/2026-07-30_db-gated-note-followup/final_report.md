# DB 연결 조건부 note 후속 단계 구현 보고서

## 요약

결과를 만드는 주요 capability 뒤에 `autopilot-note`가 필요한 공백을
토폴로지로 명시했다. note는 항상 실행되는 새 stage가 아니라 capability
owner가 durable terminal 뒤에 평가하는 조건부 postcondition이다. 사용자의
원격 note DB가 실제 read-only probe에 응답할 때만 필수 실행되고, 그렇지
않으면 `skipped/db-unavailable`로 기록된다.

## 주요 변경

1. `autopilot-code`, `autopilot-draft`, `autopilot-lab` setup/eval,
   `autopilot-refine`, `autopilot-research`에 note follow-up을 선언했다.
2. topology schema v6 validator와 route compiler가 activation condition,
   terminal anchor, source output, unavailable skip을 fail-closed로 검증한다.
3. 동일 canonical source는 create가 아니라 upsert한다. 피드백 수정 시 note
   identity, 생성 시각, 사용자/DB 소유 routing/workflow 필드를 보존하고
   agent-derived 요약·결과·결정·지표·다음 단계와 revision evidence를 갱신한다.
4. lab setup/eval은 동일 `experiment-artifact`를 사용해 한 실험이 두 note로
   갈라지지 않으며, snapshot·diff preview·run ID·재처리 날짜는 새 source가
   아니다.
5. 공유 readiness utility는 설정 존재 여부가 아니라 실제 remote DB의
   `SELECT 1` 성공으로 연결을 판정한다. local file DB는 활성 조건이 아니며,
   dotenv의 임의 셸 코드를 실행하지 않고 비밀값을 출력하지 않는다.

## 적용하지 않은 범위

`autopilot-apply`, `autopilot-design`, `autopilot-ship`, `autopilot-spec`에는
현재 recipe가 concrete note-source output을 선언하지 않으므로 자동 follow-up을
추가하지 않았다. 사용자가 명시적으로 호출하는 standalone `autopilot-note`는
DB gate와 별개로 그대로 사용할 수 있다. hook은 추가하지 않았다.

## 검증 결과

토폴로지 25개 테스트와 route compiler 40개 테스트가 통과했다. readiness
fixture, 생성 projection 회귀, 전체 adaptation boundary, utility census,
manifest, shell syntax 및 diff whitespace 검사도 통과했다.

현재 runtime에는 `WORKLOG_BOARD_APP`가 없어 live readiness가 unavailable로
확인되었다. 따라서 본 산출물의 automatic note 후속 단계는
`skipped/db-unavailable`이며 DB나 credential 설정은 변경하지 않았다.
