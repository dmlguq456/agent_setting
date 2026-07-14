# Change Report: Context Recovery and Spectrogram Report QA

## 결과

read-only 내용 파악은 이제 기존 상태를 회수한 뒤에만 capability를
선택하며, 기존 분석이 있는 상황에서 `analyze-project`를 자동 갱신
경로로 쓰지 않는다. 축약 memory hit는 record ID로 전문을 읽고,
spec/user 결정 → durable fact → 최신 experiment contract → legacy 문서
순으로 충돌을 해결하면서 drift를 보고한다.

보고서 spectrogram은 metric band와 display band를 분리했다. 48 kHz
profile은 0–24 kHz metadata, 공통 panel scale, colormap/dynamic range,
claim-evidence, 완전한 PNG와 hash-current 육안 검토가 모두 맞아야만
통과한다. 파일 존재·크기·링크만으로는 완료할 수 없다.

## QA

- semantic verifier 회귀 29개 통과
- Codex/OpenCode wrapper positive/negative integration 통과
- Claude/Codex/OpenCode 및 installable plugin projection 동기화 통과
- adapter boundary, Skill conformance, generator freshness 통과
- 대표 PNG 직접 검토 및 증거 기록 완료

self-edit/setting evolution loop는 사용자 지시에 따라 이 변경에 포함하지
않았다.
