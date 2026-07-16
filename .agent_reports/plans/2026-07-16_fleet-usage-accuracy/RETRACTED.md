# ⛔ 이 사이클은 철회됨 (2026-07-16, merge 전)

이 디렉터리의 산출물(micro-plan / verification / final_report)은 구현·검증 품질과 무관하게
**전제가 된 진단이 틀려서** 전량 철회됐다. branch `fleet-usage-accuracy`(85716394)는 merge
직후 push 전에 reset으로 되돌려졌고 main에 반영되지 않았다.

## 무엇이 틀렸나

- 진단: "OAuth usage 엔드포인트가 200 성공에 전-버킷 0%를 실어 보내 진짜 값(tap 7d 43%)을 가린다."
- 진실 (사용자 지적 + 재실측): **주간 카운터가 실제로 초기화**됐고 API의 0%가 정확했다.
  재실측에서 API(5h 4%/7d 1%)와 활성 세션 tap들(3%/1%)이 일치했고, 43%를 보인 tap 하나만
  outlier — 그 파일은 mtime이 58초로 신선했지만 **내용물(rate_limits)은 초기화 이전 마지막
  응답의 낡은 값**이었다.
- 따라서 이 사이클의 규칙 ①(성공-제로 suspect)·②(신선 tap 창구별 max)는 오히려 낡은 tap
  값을 진실 위에 올리는 **역효과**를 낸다. 원래 코드("API authoritative, 실패 시에만 tap")가
  옳았다.

## 보존할 교훈

1. **tap payload 신선도 ≠ 파일 mtime.** statusline 파일은 tick마다 재기록되지만 안의
   rate_limits는 그 세션의 마지막 inference 응답 헤더다. idle 세션의 tap은 "신선한 파일에
   담긴 낡은 값"이 될 수 있다 — tap 기반 로직은 이 함정을 전제해야 한다.
2. 검증(mutation test 포함)이 완벽해도 **전제(진단)가 틀리면 무의미**하다. 이번엔 사용자의
   한 줄("실제로 토큰이 초기화가 됐었나 본데")이 독립 검증자 역할을 했다.

final_report.md가 "판단 요청"으로 남긴 부분-양수 응답 관측은 정상 동작으로 재해석되어
후속 작업이 필요 없다.
