"""
Single-instance enforcement guard for avito-sdk processes on Windows/Linux/macOS.
Ensures that no two bot or scraper instances can ever run simultaneously,
preventing Telegram 409 Conflict errors, mobile proxy modem conflicts, and database corruption.
"""

from __future__ import annotations

import atexit
import functools
import hashlib
import json
import logging
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable, Optional, Union

logger = logging.getLogger("avito_sdk")

_ACTIVE_GUARDS: list[SingleInstanceGuard] = []
_GLOBAL_LOCK_FILE_OBJ = None
_GLOBAL_LOCK_PATH: Optional[Path] = None
_GLOBAL_PID_PATH: Optional[Path] = None


def is_pid_alive(pid: int) -> bool:
    """Check if a process with given PID is actively running in the OS."""
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        kernel32 = ctypes.windll.kernel32
        h_process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not h_process:
            return False
        exit_code = ctypes.c_ulong()
        success = kernel32.GetExitCodeProcess(h_process, ctypes.byref(exit_code))
        kernel32.CloseHandle(h_process)
        return bool(success and exit_code.value == STILL_ACTIVE)
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def terminate_competing_processes(script_keyword: Optional[str] = None) -> int:
    """
    Search and forcibly terminate any other running Python processes
    that contain `script_keyword` in their command line (excluding current PID).
    Returns the count of terminated processes.
    """
    curr_pid = os.getpid()
    parent_pid = os.getppid() if hasattr(os, "getppid") else -1
    terminated_count = 0

    target_kw = script_keyword
    if not target_kw:
        target_kw = Path(sys.argv[0]).name if sys.argv and sys.argv[0] else "main.py"

    if sys.platform == "win32":
        try:
            ps_script = (
                f"$curr = {curr_pid}; $parent = {parent_pid}; "
                f"Get-CimInstance Win32_Process | "
                f"Where-Object {{ ($_.Name -like 'python*' -or $_.Name -like 'pypy*') -and $_.ProcessId -ne $curr -and $_.ProcessId -ne $parent -and $_.CommandLine -like '*{target_kw}*' }} | "
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
                logger.info(f"[ProcessGuard] Terminated conflicting process PID {p}")
                terminated_count += 1
        except Exception as e:
            logger.debug(f"[ProcessGuard] Process scan error: {e}")
    else:
        try:
            res = subprocess.run(["pgrep", "-f", str(target_kw)], capture_output=True, text=True, timeout=5)
            for line in res.stdout.strip().splitlines():
                if line.isdigit():
                    p = int(line)
                    if p != curr_pid:
                        try:
                            os.kill(p, signal.SIGKILL)
                            logger.info(f"[ProcessGuard] Killed conflicting process PID {p}")
                            terminated_count += 1
                        except OSError:
                            pass
        except Exception as e:
            logger.debug(f"[ProcessGuard] Linux process scan error: {e}")

    return terminated_count


class SingleInstanceGuard:
    """
    Cross-platform, OS-level single instance enforcer.
    On Windows: Uses kernel Named Mutex (100% crash-proof and zero-file-lock residue).
    On Unix/Linux: Uses fcntl.flock on a shared system-temp lockfile.
    """

    def __init__(
        self,
        name: str = "bot",
        token: Optional[str] = None,
        storage_dir: Union[str, Path] = "storage",
        lock_name: Optional[str] = None,
        pid_name: Optional[str] = None,
        script_keyword: Optional[str] = None,
        auto_kill_others: bool = False,
        raise_on_collision: bool = False,
    ):
        clean_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in name)
        if token:
            token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]
            clean_name = f"{clean_name}_{token_hash}"

        self.name = clean_name
        self.token = token
        self.auto_kill_others = auto_kill_others
        self.raise_on_collision = raise_on_collision
        self.script_keyword = script_keyword
        self.storage_dir = Path(storage_dir)

        self._win_mutex_handle = None
        self._lock_file_obj = None
        self._is_locked = False

        temp_dir = Path(tempfile.gettempdir())
        self.global_pid_file = temp_dir / f".avito_sdk_{self.name}.pid"
        self.global_lock_file = temp_dir / f".avito_sdk_{self.name}.lock"

        l_name = lock_name or f"{self.name}.lock"
        p_name = pid_name or f"{self.name}.pid"
        self.local_lock_file = self.storage_dir / l_name
        self.local_pid_file = self.storage_dir / p_name

    def _get_existing_pid_info(self) -> tuple[Optional[int], str]:
        for pfile in (self.global_pid_file, self.local_pid_file):
            if pfile.exists():
                try:
                    text = pfile.read_text(encoding="utf-8").strip()
                    if text.isdigit():
                        return int(text), ""
                    try:
                        data = json.loads(text)
                        if isinstance(data, dict):
                            return int(data.get("pid", 0)) or None, str(data.get("started_at", ""))
                    except Exception:
                        pass
                except Exception:
                    pass
        return None, ""

    def _write_pid_info(self, pid: int) -> None:
        try:
            self.global_pid_file.write_text(str(pid), encoding="utf-8")
        except Exception:
            pass

        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            self.local_pid_file.write_text(str(pid), encoding="utf-8")
        except Exception:
            pass

    def _show_collision_banner(self, existing_pid: Optional[int], started_at: str) -> None:
        pid_str = f"PID {existing_pid}" if existing_pid else "PID неизвестен"
        time_str = f" (запущен: {started_at})" if started_at else ""
        banner = (
            "\n"
            "======================================================================\n"
            "🛑 [ЗАЩИТА ОТ ДУБЛИКАТОВ / SINGLE INSTANCE GUARD]\n"
            "⚠️ Внимание: Другая копия бота или программы уже запущена и активна!\n"
            f"   • Модуль/Задача: {self.name}\n"
            f"   • Активный процесс: {pid_str}{time_str}\n"
            f"   • Запускаемый файл: {sys.argv[0] if sys.argv else 'Python script'}\n\n"
            "❌ Запуск второй копии заблокирован во избежание:\n"
            "   1. Конфликтов Telegram API (409 Conflict: terminated by getUpdates)\n"
            "   2. Сбоев мобильного 4G LTE прокси (одновременная смена IP обрывает поток)\n"
            "   3. Повреждения баз данных и отчётов Excel\n\n"
            f"💡 Чтобы запустить бота, остановите запущенную копию ({pid_str})\n"
            "   или закройте предыдущее окно терминала.\n"
            "======================================================================\n"
        )
        print(banner, file=sys.stderr)
        logger.warning(
            f"[ProcessGuard] Duplicate instance prevented: '{self.name}' is already running ({pid_str})."
        )

    def acquire(self) -> bool:
        """Acquire exclusive single instance lock. Returns True on success, exits or raises on collision."""
        curr_pid = os.getpid()

        # Check existing PID
        existing_pid, started_at = self._get_existing_pid_info()
        if existing_pid and existing_pid != curr_pid:
            if is_pid_alive(existing_pid):
                if self.auto_kill_others:
                    logger.info(f"[ProcessGuard] Found existing PID {existing_pid}. Terminating...")
                    if sys.platform == "win32":
                        subprocess.run(["taskkill", "/F", "/PID", str(existing_pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        try:
                            os.kill(existing_pid, signal.SIGKILL)
                        except OSError:
                            pass
                    time.sleep(1.0)
                else:
                    self._show_collision_banner(existing_pid, started_at)
                    if self.raise_on_collision:
                        raise RuntimeError(f"Another instance of '{self.name}' is already running ({existing_pid})")
                    sys.exit(0)
            else:
                # Stale PID file from an old crash
                try:
                    self.global_pid_file.unlink(missing_ok=True)
                    self.local_pid_file.unlink(missing_ok=True)
                except Exception:
                    pass

        # 1. Windows Named Mutex
        if sys.platform == "win32":
            import ctypes
            ERROR_ALREADY_EXISTS = 183
            kernel32 = ctypes.windll.kernel32
            mutex_name = f"Local\\AvitoSDK_{self.name}"

            handle = kernel32.CreateMutexW(None, False, mutex_name)
            last_err = kernel32.GetLastError()
            if last_err == ERROR_ALREADY_EXISTS:
                if self.auto_kill_others:
                    terminate_competing_processes(self.script_keyword)
                    time.sleep(1.0)
                    handle = kernel32.CreateMutexW(None, False, mutex_name)
                    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
                        self._show_collision_banner(existing_pid, started_at)
                        if self.raise_on_collision:
                            raise RuntimeError(f"Another instance of '{self.name}' is already running")
                        sys.exit(0)
                else:
                    if handle:
                        kernel32.CloseHandle(handle)
                    self._show_collision_banner(existing_pid, started_at)
                    if self.raise_on_collision:
                        raise RuntimeError(f"Another instance of '{self.name}' is already running")
                    sys.exit(0)

            self._win_mutex_handle = handle

        # 2. File lock (Unix or supplementary on Windows)
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            self._lock_file_obj = open(self.local_lock_file, "w")
            if sys.platform == "win32":
                import msvcrt
                try:
                    msvcrt.locking(self._lock_file_obj.fileno(), msvcrt.LK_NBLCK, 1)
                except Exception:
                    pass
            else:
                import fcntl
                try:
                    fcntl.flock(self._lock_file_obj.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except (IOError, OSError) as flock_err:
                    self._show_collision_banner(existing_pid, started_at)
                    if self.raise_on_collision:
                        raise RuntimeError(f"Another instance of '{self.name}' is running: {flock_err}")
                    sys.exit(0)
        except (IOError, OSError) as lock_err:
            if sys.platform != "win32" or not self._win_mutex_handle:
                self._show_collision_banner(existing_pid, started_at)
                if self.raise_on_collision:
                    raise RuntimeError(f"Another instance is running: {lock_err}")
                sys.exit(0)

        # 3. Write PID & register cleanup
        self._write_pid_info(curr_pid)
        self._is_locked = True
        _ACTIVE_GUARDS.append(self)

        atexit.register(self.release)
        try:
            signal.signal(signal.SIGINT, lambda sig, frame: (self.release(), sys.exit(0)))
            signal.signal(signal.SIGTERM, lambda sig, frame: (self.release(), sys.exit(0)))
        except Exception:
            pass

        logger.info(f"[ProcessGuard] Exclusive single-instance lock acquired for '{self.name}' (PID: {curr_pid}).")
        return True

    def release(self) -> None:
        """Release OS mutex and lock handles, cleaning up PID files."""
        if not self._is_locked:
            return

        # Close Windows mutex
        if self._win_mutex_handle and sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.kernel32.CloseHandle(self._win_mutex_handle)
            except Exception:
                pass
            self._win_mutex_handle = None

        # Close and unlock file
        if self._lock_file_obj is not None:
            try:
                if sys.platform == "win32":
                    import msvcrt
                    try:
                        msvcrt.locking(self._lock_file_obj.fileno(), msvcrt.LK_UNLCK, 1)
                    except Exception:
                        pass
                else:
                    import fcntl
                    try:
                        fcntl.flock(self._lock_file_obj.fileno(), fcntl.LOCK_UN)
                    except Exception:
                        pass
                self._lock_file_obj.close()
            except Exception:
                pass
            self._lock_file_obj = None

        # Clean PID and lock files
        for f in (self.global_pid_file, self.local_pid_file, self.local_lock_file, self.global_lock_file):
            try:
                if f.exists():
                    f.unlink()
            except Exception:
                pass

        self._is_locked = False
        if self in _ACTIVE_GUARDS:
            _ACTIVE_GUARDS.remove(self)

    def __enter__(self) -> SingleInstanceGuard:
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()


def release_instance_lock() -> None:
    """Release all active single-instance locks and remove PID files."""
    for guard in list(_ACTIVE_GUARDS):
        try:
            guard.release()
        except Exception:
            pass
    _ACTIVE_GUARDS.clear()


def ensure_single_instance(
    storage_dir: Union[str, Path] = "storage",
    lock_name: str = "bot.lock",
    pid_name: str = "bot.pid",
    script_keyword: Optional[str] = None,
    auto_kill_others: bool = False,
    token: Optional[str] = None,
    name: Optional[str] = None,
    raise_on_collision: bool = False,
) -> SingleInstanceGuard:
    """
    Acquire an exclusive OS-level kernel mutex and PID record to guarantee that
    ONLY ONE instance of the bot or program runs on this machine at any time.

    If another copy is already active:
    - Displays a clear alert banner and prevents the duplicate from starting.
    - If auto_kill_others=True, terminates the conflicting process before claiming the lock.
    """
    guard_name = name or (Path(lock_name).stem if lock_name else "app")
    guard = SingleInstanceGuard(
        name=guard_name,
        token=token,
        storage_dir=storage_dir,
        lock_name=lock_name,
        pid_name=pid_name,
        script_keyword=script_keyword,
        auto_kill_others=auto_kill_others,
        raise_on_collision=raise_on_collision,
    )
    guard.acquire()
    return guard


def single_instance(
    name: str = "app",
    token: Optional[str] = None,
    auto_kill_others: bool = False,
    raise_on_collision: bool = False,
) -> Callable:
    """Decorator to enforce single instance execution on any entrypoint function."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with SingleInstanceGuard(
                name=name,
                token=token,
                auto_kill_others=auto_kill_others,
                raise_on_collision=raise_on_collision,
            ):
                return func(*args, **kwargs)
        return wrapper
    return decorator
