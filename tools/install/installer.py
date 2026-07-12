#!/usr/bin/env python3
"""installer.py — harness-installer CLI skeleton (`harness` 진입 명령, INST-OPEN-2 확정).

runtime-neutral core (tools/install/, fleet 과 같은 자리 컨벤션). 서브명령 트리:
  install [claude|codex|opencode|all]
  verify  [runtime]
  update  [--reapply]
  status
  uninstall [runtime]

SoT = .agent_reports/spec/harness-installer/prd.md ([cli] 섹션). 본 파일은 Step 4 scaffold —
서브명령 파싱·exit code·--json shape 만 확정하고, 실 동작(symlink 실행·hash 기록·drift 판정·
채널 driver 호출)은 각 모듈 stub 에 TODO 로 위임한다. 구현은 이후 autopilot-code 사이클(plans/).

의존성: python3 stdlib only (zero-pip, fleet 선례). git·각 런타임 CLI 는 verify 단계 한정.
"""
import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

import projector
import manifest
import verifier
from drivers import get_driver, RUNTIMES

# exit code 상수 — PRD [cli] "### Exit code" 표와 1:1
EXIT_OK = 0
EXIT_FAIL = 1
EXIT_VERIFY_FAIL = 2
EXIT_BLOCKED = 3
EXIT_DRIFT = 4
EXIT_USAGE = 64


class _UsageExitParser(argparse.ArgumentParser):
    """argparse 기본 usage-error exit(2) 대신 PRD exit code 표의 64(usage)로 통일."""

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"{self.prog}: error: {message}\n")


def build_parser():
    p = _UsageExitParser(
        prog="harness",
        description="agent-harness installer — install/verify/update/status/uninstall (2-채널 하이브리드).",
    )
    # 공통 옵션 (PRD [cli] "공통 옵션") — 모든 서브명령에 상속
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--runtime", action="append", choices=RUNTIMES, dest="runtimes",
        help="대상 런타임 (반복 가능). 생략 시 서브명령 positional 또는 전체.",
    )
    common.add_argument("--scope", choices=["global", "project"], default="global")
    common.add_argument("--dry-run", action="store_true", help="실행 없이 계획만 출력")
    common.add_argument("--json", action="store_true", help="기계 출력 (--json shape, fleet 스타일)")
    common.add_argument("--yes", action="store_true", help="비대화 확인 생략")
    common.add_argument("--plugin", action="store_true", help="plugin 채널 경로 (marketplace/plugin add wrapping)")

    sub = p.add_subparsers(dest="command", required=True, parser_class=_UsageExitParser)

    p_install = sub.add_parser("install", parents=[common], help="dev 머신 projection + runtime-owned 표면 + manifest 기록")
    p_install.add_argument("target", nargs="?", choices=[*RUNTIMES, "all"], default="all")

    p_verify = sub.add_parser("verify", parents=[common], help="Migration Order 기계화 — check 목록 실행")
    p_verify.add_argument("target", nargs="?", choices=RUNTIMES, default=None)

    p_update = sub.add_parser("update", parents=[common], help="repo pull 후 재-projection (+ plugin update wrapping)")
    p_update.add_argument("--reapply", action="store_true", help="local-patches 를 새 파일에 재적용")

    sub.add_parser("status", parents=[common], help="설치 상태 요약 — 채널·버전·drift")

    p_uninstall = sub.add_parser("uninstall", parents=[common], help="manifest 등재분만 제거 (소유 경계)")
    p_uninstall.add_argument("target", nargs="?", choices=RUNTIMES, default=None)

    return p


def resolve_runtimes(args):
    """positional target 과 --runtime 반복 옵션을 하나의 대상 목록으로 합친다."""
    if args.runtimes:
        return list(args.runtimes)
    target = getattr(args, "target", None)
    if target in (None, "all"):
        return list(RUNTIMES)
    return [target]


def emit(result, as_json):
    if as_json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        for line in result.get("lines", []):
            print(line)
    return result["exit"]


def cmd_install(args):
    runtimes = resolve_runtimes(args)
    plan = projector.plan(runtimes, scope=args.scope)
    lines = [f"install: runtime={r} scope={args.scope} plugin={args.plugin} dry_run={args.dry_run}" for r in runtimes]
    checks = []
    for rt in runtimes:
        driver = get_driver(rt)
        # TODO(autopilot-code): driver.install() 실행 — projector.plan() 결과를 실 symlink/
        # plugin-add 로 적용하고 manifest.record() 로 hash 등재. 지금은 계획만 노출한다.
        checks.append({"id": f"{rt}.plan", "ok": True, "detail": f"{len(plan.get(rt, []))}개 projection 항목 계획됨"})
    return {"runtime": runtimes, "channel": "plugin" if args.plugin else "dev", "checks": checks,
            "drift": [], "exit": EXIT_OK, "lines": lines}


def cmd_verify(args):
    runtimes = resolve_runtimes(args)
    all_checks = []
    ok = True
    for rt in runtimes:
        driver = get_driver(rt)
        rt_checks = verifier.run(rt, driver)
        all_checks.extend(rt_checks)
        if any(not c["ok"] for c in rt_checks):
            ok = False
    lines = [("✓" if c["ok"] else "✗") + f" {c['id']} {c['detail']}" for c in all_checks]
    return {"runtime": runtimes, "channel": "plugin" if args.plugin else "dev", "checks": all_checks,
            "drift": [], "exit": EXIT_OK if ok else EXIT_VERIFY_FAIL, "lines": lines}


def cmd_update(args):
    runtimes = resolve_runtimes(args)
    drift = manifest.check_drift(runtimes) if args.reapply else []
    lines = [f"update: runtime={r} reapply={args.reapply}" for r in runtimes]
    exit_code = EXIT_DRIFT if drift and not args.reapply else EXIT_OK
    return {"runtime": runtimes, "channel": "plugin" if args.plugin else "dev", "checks": [],
            "drift": drift, "exit": exit_code, "lines": lines}


def cmd_status(args):
    runtimes = resolve_runtimes(args)
    lines = []
    checks = []
    for rt in runtimes:
        driver = get_driver(rt)
        # TODO(autopilot-code): 실제 채널·commit·drift 조회 — driver.status() + manifest 대조.
        checks.append({"id": f"{rt}.status", "ok": True, "detail": "channel=미확인 (scaffold stub)"})
        lines.append(f"{rt}: channel=미확인 (scaffold stub)")
    return {"runtime": runtimes, "channel": "dev", "checks": checks, "drift": [], "exit": EXIT_OK, "lines": lines}


def cmd_uninstall(args):
    runtimes = resolve_runtimes(args)
    lines = [f"uninstall: runtime={r} (manifest 등재분만 제거 — 소유 경계)" for r in runtimes]
    return {"runtime": runtimes, "channel": "dev", "checks": [], "drift": [], "exit": EXIT_OK, "lines": lines}


COMMANDS = {
    "install": cmd_install,
    "verify": cmd_verify,
    "update": cmd_update,
    "status": cmd_status,
    "uninstall": cmd_uninstall,
}


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = COMMANDS.get(args.command)
    if handler is None:
        parser.print_usage(sys.stderr)
        return EXIT_USAGE
    result = handler(args)
    return emit(result, args.json)


if __name__ == "__main__":
    sys.exit(main())
