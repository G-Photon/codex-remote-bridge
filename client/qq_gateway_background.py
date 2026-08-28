#!/usr/bin/env python3
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "data"
LOG_FILE = LOG_DIR / "qq-gateway-autostart.log"
OLD_LOG_FILE = LOG_DIR / "qq-gateway-autostart.log.1"
MAX_LOG_BYTES = 5 * 1024 * 1024
RESTART_DELAY_SECONDS = 10


def merged_windows_path() -> str:
    if os.name != "nt":
        return os.environ.get("PATH", "")
    try:
        import winreg

        parts = []
        for root, subkey in (
            (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
            (winreg.HKEY_CURRENT_USER, r"Environment"),
        ):
            try:
                with winreg.OpenKey(root, subkey) as key:
                    value, _ = winreg.QueryValueEx(key, "Path")
                    expanded = os.path.expandvars(str(value))
                    if expanded:
                        parts.extend(expanded.split(os.pathsep))
            except OSError:
                pass
        parts.extend(os.environ.get("PATH", "").split(os.pathsep))
        seen = set()
        merged = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            key = part.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(part)
        return os.pathsep.join(merged)
    except Exception:
        return os.environ.get("PATH", "")


def now_text() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def rotate_log() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_LOG_BYTES:
        if OLD_LOG_FILE.exists():
            OLD_LOG_FILE.unlink()
        LOG_FILE.replace(OLD_LOG_FILE)


def python_exe() -> str:
    current = Path(sys.executable)
    if current.name.lower() == "pythonw.exe":
        sibling = current.with_name("python.exe")
        if sibling.exists():
            return str(sibling)
    return str(current)


def write_line(text: str) -> None:
    rotate_log()
    with LOG_FILE.open("a", encoding="utf-8", errors="replace") as log:
        log.write(text.rstrip() + "\n")
        log.flush()


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PATH"] = merged_windows_path()

    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    while True:
        rotate_log()
        try:
            with LOG_FILE.open("a", encoding="utf-8", errors="replace") as log:
                log.write(f"[{now_text()}] supervisor starting QQ Gateway bridge\n")
                log.flush()
                proc = subprocess.Popen(
                    [python_exe(), str(BASE_DIR / "qq_gateway_client.py")],
                    cwd=str(BASE_DIR),
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    env=env,
                    creationflags=creationflags,
                )
                return_code = proc.wait()
                log.write(
                    f"[{now_text()}] QQ Gateway exited code={return_code}; "
                    f"restart in {RESTART_DELAY_SECONDS}s\n"
                )
                log.flush()
        except Exception:
            write_line(f"[{now_text()}] supervisor error:\n{traceback.format_exc().rstrip()}")

        time.sleep(RESTART_DELAY_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
