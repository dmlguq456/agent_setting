## Step 0: Auto-Load Context (매번 자동 read — 사용자 재설명 부담 차단)

본 skill 의 핵심 — _사용자가 매번 상황 재설명 안 함_. 호출 자리에서 다음 자료 자동 read:

| Layer | 자료 | 누적 단위 | 자리 |
|---|---|---|---|
| **실험 컨벤션 (per-project)** | `<artifact-root>/analysis_project/code/experiment_conventions.md` | 프로젝트 단위 | **1순위** — 본 프로젝트의 실제 컨벤션이 source of truth. 개별 프로젝트의 특수 사정(외부 ref 기반 / 다른 framework / legacy 자리) 그대로 우선 |
| 사용자 일관 패턴 (cross-project) | `mem profile 07_coding_convention` (`python3 <agent-home>/tools/memory/mem.py profile 07_coding_convention`) | cross-project | **2순위 (default·fallback)** — per-project 부재 또는 _빈 자리_ 만 보강. 부재 시 `/analyze-user coding_convention` 권장 안내 |
| 프로젝트 timeline | `<artifact-root>/experiments/_RUNLOG.md` 의 최근 5 줄 | 한 실험 = 한 줄 | 직전 실험 컨텍스트 + ⏳ 대기/✅ 완료 상태 |
| 직전 실험 상세 | 직전 실험 폴더의 `summary.md` + `STORY.md` | 한 실험 narrative | 결과·다음 후보 인용 |
| **부모 실험** (`--parent` 자리) | 부모 폴더의 `summary.md` / `STORY.md` / `config` / ckpt path | 한 실험 | fine-tune base 또는 재평가 대상 |
| 외부 조사 | `<artifact-root>/research/` 최근 산출 (있으면) | topic 별 | motivation 기반 |
| 코드 청사진 | `<artifact-root>/analysis_project/code/` (있으면) | 프로젝트 단위 | baseline 파악 |
| **유사 모델** | `<artifact-root>/analysis_project/code/similar_models.md` | 프로젝트 단위 | `--ref` 자동 추천 |
| Cleanup 후보 | `<artifact-root>/analysis_project/code/cleanup_candidates.md` (있으면) | 프로젝트 단위 | dead code 자리 회피 |
| 실험 ready 점검 | `<artifact-root>/analysis_project/code/experiment_readiness.md` (있으면) | 프로젝트 단위 | 미흡 시 _autopilot-code 권장_ 한 줄 |

### 컨벤션·ready 부재 자리 (`experiment_conventions.md` 없음)

`analyze-project --mode code` 한 번도 안 돌렸으면:
1. **Lightweight scan** 자동 — `model/*/` 폴더 ls + `config.*` sample read + 한 모델 sample read
2. 추출 draft (모델 폴더 구조 / config 메커니즘 / prefix 패턴 / preferred layer 후보) 사용자 _한 화면 컨펌_
3. yes → `analysis_project/code/experiment_conventions.md` 저장 → 본 호출 진행
4. 수정 → 사용자 직접 편집 후 진행

이후 호출은 본 파일 read-only — 매번 재추출 X.

### 실험 ready 미흡 자리 (setup 모드)

`experiment_readiness.md` 의 항목 중 ❌ 가 있으면 setup 진행 _보류_:
```
=== 실험 ready 미흡 ===
- ❌ model 단위 폴더 분리 — model/ 폴더 없음
- ❌ train.py / eval.py 분리 — main.py 한 파일에 다 박힘
- ⚠️ config 메커니즘 일관성 — argparse / yaml 혼재

권장: /autopilot-code "model/ 폴더 분리 + train/eval 분리 + config 통일" 먼저
(진행 — 미흡 무시하고 setup 시작 / autopilot-code 호출 / 중단)
```
