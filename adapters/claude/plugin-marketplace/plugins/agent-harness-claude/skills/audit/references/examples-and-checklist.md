## Examples

    # Full audit of the SE seminar document artifact
    /audit 2026-05-06_se-seminar-tfrestormer

    # Facts-only check of the same artifact (after a 20-cycle refine session)
    /audit 2026-05-06_se-seminar-tfrestormer --scope facts

    # Audit a research artifact's cards consistency
    /audit speech-enhancement-trends --scope facts

    # Read-only static audit of a code plan (skip test execution)
    /audit 2026-05-11_audit-skill-infra --scope all --read-only

    # Inspection only (no auto-fix)
    /audit 2026-05-06_se-seminar-tfrestormer --report-only

## Post-Audit Checklist

After audit, the auto-fix chain (Stage E) dispatches automatically. If you used `--report-only`:
1. 🔴 이슈 존재 → `/autopilot-refine "<fix prompt suggested by audit log>"` 또는 `/autopilot-code --mode dev "<fix>"` 직접 호출
2. 🟡 only → 사용자 판단으로 deferred or batch-fix
3. clean → 추가 조치 불필요
