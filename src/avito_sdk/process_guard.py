"""
Single-instance enforcement guard for avito-sdk processes on Windows/Linux.
Ensures that no two bot instances can ever run simultaneously.
"""

from __future__ import annotations

import atexit
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger("avito_sdk")

_LOCK_FILE_OBJ = None
_LOCK_PATH: Optional[Path] = None
_PID_PATH: Optional[Path] = None


def terminate_competing_processes(script_keyword: str = "run_telegram_bot") -> int:
    """
    Search and forcibly terminate any other running Python processes
    that contain `script_keyword` in their command line (excluding current PID).
    Returns the count of terminated processes.
    """
    curr_pid = os.getpid()
    parent_pid = os.getppid() if hasattr(os, "getppid") else -1
    terminated_count = 0

    if sys.platform == "win32":
        try:
            # Query Win32_Process for Python/PyPy processes matching script_keyword (excluding self and parent)
            ps_script = (
                f"$curr = {curr_pid}; $parent = {parent_pid}; "
                f"Get-CimInstance Win32_Process | "
                f"Where-Object {{ ($_.Name -like 'python*' -or $_.Name -like 'pypy*') -and $_.ProcessId -ne $curr -and $_.ProcessId -ne $parent -and $_.CommandLine -like '*{script_keyword}*' }} | "
                f"ForEach-Object {{ Write-Output $_.ProcessId; Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }}"
            )
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=10,
            )
            pids = [line.strip() for line in res.stdout.strip().splitlines() if line.strip().isdigit()]
            for p in pids:
                logger.info(f"[ProcessGuard] Terminated conflicting bot process PID {p}")
                terminated_count += 1
        except Exception as e:
            logger.debug(f"[ProcessGuard] Process scan error: {e}")
    else:
        try:
            res = subprocess.run(["pgrep", "-f", script_keyword], capture_output=True, text=True, timeout=5)
            for line in res.stdout.strip().splitlines():
                if line.isdigit():
                    p = int(line)
                    if p != curr_pid:
                        os.kill(p, signal.SIGKILL)
                        logger.info(f"[ProcessGuard] Killed conflicting process PID {p}")
                        terminated_count += 1
        except Exception as e:
            logger.debug(f"[ProcessGuard] Linux process scan error: {e}")

    return terminated_count


def release_instance_lock() -> None:
    """Release the single-instance lock file and remove bot.pid."""
    global _LOCK_FILE_OBJ, _LOCK_PATH, _PID_PATH

    if _PID_PATH and _PID_PATH.exists():
        try:
            _PID_PATH.unlink()
        except Exception:
            pass
        _PID_PATH = None

    if _LOCK_FILE_OBJ is not None:
        try:
            if sys.platform == "win32":
                import msvcrt
                try:
                    msvcrt.locking(_LOCK_FILE_OBJ.fileno(), msvcrt.LK_UNLCK, 1)
                except Exception:
                    pass
            else:
                import fcntl
                try:
                    fcntl.flock(_LOCK_FILE_OBJ.fileno(), fcntl.LOCK_UN)
                except Exception:
                    pass
            _LOCK_FILE_OBJ.close()
        except Exception:
            pass
        _LOCK_FILE_OBJ = None

    if _LOCK_PATH and _LOCK_PATH.exists():
        try:
            _LOCK_PATH.unlink()
        except Exception:
            pass
        _LOCK_PATH = None


def ensure_single_instance(
    storage_dir: Union[str, Path] = "storage",
    lock_name: str = "bot.lock",
    pid_name: str = "bot.pid",
    script_keyword: str = "run_telegram_bot",
    auto_kill_others: bool = True,
) -> None:
    """
    Acquire an exclusive OS-level file lock and PID record to guarantee that
    ONLY ONE instance of the bot is running on this machine at any time.

    If auto_kill_others=True (default), any stale or conflicting bot instances
    are killed automatically before claiming the lock.
    """
    global _LOCK_FILE_OBJ, _LOCK_PATH, _PID_PATH

    dir_path = Path(storage_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    _LOCK_PATH = dir_path / lock_name
    _PID_PATH = dir_path / pid_name
    curr_pid = os.getpid()

    # 1. Check existing PID file and terminate old process if alive
    if _PID_PATH.exists():
        try:
            old_pid_str = _PID_PATH.read_text(encoding="utf-8").strip()
            if old_pid_str.isdigit():
                old_pid = int(old_pid_str)
                if old_pid != curr_pid:
                    if auto_kill_others:
                        logger.info(f"[ProcessGuard] Found existing PID file with PID {old_pid}. Terminating...")
                        if sys.platform == "win32":
                            subprocess.run(
                                ["taskkill", "/F", "/PID", str(old_pid)],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                timeout=5,
                            )
                        else:
                            try:
                                os.kill(old_pid, signal.SIGKILL)
                            except OSError:
                                pass
        except Exception as e:
            logger.debug(f"[ProcessGuard] Error reading old PID file: {e}")

    # 2. Kill any other competing python processes
    if auto_kill_others:
        terminated = terminate_competing_processes(script_keyword)
        if terminated > 0:
            time.sleep(1.0)

    # 3. Acquire exclusive non-blocking lock
    try:
        _LOCK_FILE_OBJ = open(_LOCK_PATH, "w")
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(_LOCK_FILE_OBJ.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(_LOCK_FILE_OBJ.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, IOError) as lock_err:
        logger.warning(f"[ProcessGuard] Lock collision detected ({lock_err}). Retrying after force kill...")
        if auto_kill_others:
            terminate_competing_processes(script_keyword)
            time.sleep(1.5)
            try:
                _LOCK_FILE_OBJ = open(_LOCK_PATH, "w")
                if sys.platform == "win32":
                    import msvcrt
                    msvcrt.locking(_LOCK_FILE_OBJ.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(_LOCK_FILE_OBJ.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except Exception as final_err:
                logger.critical(f"[ProcessGuard] CRITICAL: Unable to acquire exclusive instance lock: {final_err}")
                print(f"[FATAL] Another bot instance is strictly locked. Exiting to prevent collisions: {final_err}")
                sys.exit(1)
        else:
            print("[FATAL] Another bot instance is already running. Exiting.")
            sys.exit(1)

    # 4. Save current PID to pid_path
    try:
        _PID_PATH.write_text(str(curr_pid), encoding="utf-8")
    except Exception as e:
        logger.warning(f"[ProcessGuard] Could not write PID file: {e}")

    # 5. Register cleanup handlers
    atexit.register(release_instance_lock)
    try:
        signal.signal(signal.SIGINT, lambda sig, frame: (release_instance_lock(), sys.exit(0)))
        signal.signal(signal.SIGTERM, lambda sig, frame: (release_instance_lock(), sys.exit(0)))
    except Exception:
        pass

    logger.info(f"[ProcessGuard] Single-instance lock acquired successfully (PID: {curr_pid}).")
