"""paths.py — installer 전용 경로 해석 중앙화.

`AGENT_HOME`/`HOME` 환경변수 override 를 존중해 테스트가 임시 home 을 가리킬 수 있게 한다.
"""

import os
from pathlib import Path


def _absolute_env_path(name, default):
    raw = os.environ.get(name)
    path = Path(raw).expanduser() if raw else Path(default).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{name} must be an absolute path: {path}")
    return path


def agent_home():
    """repo 루트(AGENT_HOME)를 돌려준다.

    env `AGENT_HOME` 이 설정돼 있으면 그대로 사용, 아니면 이 파일에서 위로 올라가며
    `.git` 을 가진 조상 디렉터리를 찾는다.
    """
    env_home = os.environ.get("AGENT_HOME")
    if env_home:
        return Path(env_home)

    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / ".git").exists():
            return parent

    raise RuntimeError(
        "agent_home 해석 실패: AGENT_HOME env 도 없고, "
        f"{here} 상위에서 .git 을 찾지 못했다."
    )


def runtime_home(runtime, scope="global"):
    """runtime(+scope) 별 설치 대상 홈 디렉터리."""
    if runtime == "claude":
        return _absolute_env_path("CLAUDE_CONFIG_DIR", Path.home() / ".claude")
    if runtime == "codex":
        return _absolute_env_path("CODEX_HOME", Path.home() / ".codex")
    if runtime == "opencode":
        if scope == "project":
            return Path.cwd() / ".opencode"
        return xdg_config_home() / "opencode"
    raise ValueError(f"알 수 없는 runtime: {runtime!r}")


def opencode_data_home():
    """OpenCode 런타임 소유 데이터 디렉터리 (installer 는 절대 쓰지 않음, 참조용)."""
    return xdg_data_home() / "opencode"


def xdg_config_home():
    """Freedesktop config root; relative overrides are rejected."""
    return _absolute_env_path("XDG_CONFIG_HOME", Path.home() / ".config")


def xdg_state_home():
    """Freedesktop state root, honoring an explicit test/runtime override."""
    return _absolute_env_path("XDG_STATE_HOME", Path.home() / ".local" / "state")


def xdg_data_home():
    """Freedesktop data root, honoring an explicit test/runtime override."""
    return _absolute_env_path("XDG_DATA_HOME", Path.home() / ".local" / "share")


def extension_state_dir():
    """Harness-owned state for optional external extensions."""
    return xdg_state_home() / "agent-harness" / "extensions"


def extension_data_dir():
    """Harness-owned immutable snapshots for optional external extensions."""
    return xdg_data_home() / "agent-harness" / "extensions"


def harness_state_dir(runtime, scope="global"):
    """installer 소유 상태 디렉터리 (`<runtime_home>/.harness`)."""
    return runtime_home(runtime, scope) / ".harness"


def resolve_source(relpath):
    """repo 루트 기준 상대경로를 절대경로로 변환."""
    return agent_home() / relpath


def source_exists(relpath):
    """source 존재 여부 (symlink 디렉터리도 대상을 따라가 존재로 판정)."""
    return resolve_source(relpath).exists()
