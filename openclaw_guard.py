import json
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path


REQUIRED_SKILL = "mundo-materno-inventory"
DEFAULT_GATEWAY_HOST = "127.0.0.1"
DEFAULT_GATEWAY_PORT = 30000
CACHE_SECONDS = 10

_last_full_check_at = 0.0
_last_full_check = (False, "OpenClaw has not been checked yet.")


def _openclaw_executable():
    for name in ("openclaw", "openclaw.cmd", "openclaw.CMD", "openclaw.ps1"):
        path = shutil.which(name)
        if path:
            return path
    return "openclaw"


def _run_openclaw(args, timeout=10):
    return subprocess.run(
        [_openclaw_executable(), *args],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        text=True,
        timeout=timeout,
        check=False,
    )


def _config_path():
    return Path(os.environ.get("OPENCLAW_CONFIG", Path.home() / ".openclaw" / "openclaw.json"))


def _gateway_port():
    path = _config_path()
    if not path.exists():
        return DEFAULT_GATEWAY_PORT

    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_GATEWAY_PORT

    try:
        return int(config.get("gateway", {}).get("port") or DEFAULT_GATEWAY_PORT)
    except (TypeError, ValueError):
        return DEFAULT_GATEWAY_PORT


def _is_gateway_listening(host=DEFAULT_GATEWAY_HOST, port=None):
    port = port or _gateway_port()
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


def _full_openclaw_check():
    try:
        version = _run_openclaw(["--version"], timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return False, f"OpenClaw CLI is not available: {exc}"

    if version.returncode != 0:
        return False, f"OpenClaw CLI failed: {version.stderr.strip() or version.stdout.strip()}"

    validate = _run_openclaw(["config", "validate"], timeout=15)
    if validate.returncode != 0:
        return False, f"OpenClaw config is invalid: {validate.stderr.strip() or validate.stdout.strip()}"

    skills = _run_openclaw(["skills", "list", "--eligible"], timeout=20)
    if skills.returncode != 0:
        return False, f"OpenClaw skills check failed: {skills.stderr.strip() or skills.stdout.strip()}"
    if REQUIRED_SKILL not in (skills.stdout or ""):
        return False, f"OpenClaw skill '{REQUIRED_SKILL}' is not available."

    return True, "OpenClaw CLI, config, and inventory skill are ready."


def check_openclaw_ready():
    global _last_full_check_at, _last_full_check

    now = time.monotonic()
    if now - _last_full_check_at > CACHE_SECONDS:
        _last_full_check = _full_openclaw_check()
        _last_full_check_at = now

    ok, message = _last_full_check
    if not ok:
        return ok, message

    port = _gateway_port()
    if not _is_gateway_listening(port=port):
        return (
            False,
            f"OpenClaw gateway is not listening on {DEFAULT_GATEWAY_HOST}:{port}. "
            "Start it with: openclaw gateway run",
        )

    return True, f"{message} Gateway is listening on {DEFAULT_GATEWAY_HOST}:{port}."


def require_openclaw_ready():
    ok, message = check_openclaw_ready()
    if not ok:
        raise RuntimeError(
            "OpenClaw is required for Mundo Materno, but it is not ready.\n"
            f"{message}"
        )
    return message
