# Main/worker bootstrap 분리 결과

자동 curator/hook lifecycle의 소유자를 interactive main 한 곳으로 고정했다.
분사·loop·title·distill·cron worker는 자동 memory injection, briefing,
turn counter, SessionEnd sync/curation, title 재요약, token context, main pane
publication을 실행하지 않는다. deterministic safety와 명시적 task bootstrap은
그대로 유지한다.

폭주 방지는 세 겹이다: launch marker, hook/preflight 조기 반환, 기존의 전역
동시성·rolling start budget·kill switch. 따라서 오래된 wrapper가 portable
marker를 빠뜨려도 compatibility marker가 있으면 fail closed한다.

외부 worklog 예약 호출 패치는 `agent-note` main의 `72e96dd`로 push했다.
이 저장소의 main/worker 경계 패치도 별도 커밋으로 분리했다.
distill/title kill switch는 운영자가 재개를 결정할 때까지 유지한다.
