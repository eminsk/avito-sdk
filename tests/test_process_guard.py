import os
import subprocess
import sys
from pathlib import Path
from avito_sdk.process_guard import ensure_single_instance, release_instance_lock, terminate_competing_processes


def test_process_guard_lock_acquisition(tmp_path):
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()

    # First acquisition succeeds
    ensure_single_instance(
        storage_dir=storage_dir,
        lock_name="test_bot.lock",
        pid_name="test_bot.pid",
        auto_kill_others=False,
    )

    pid_file = storage_dir / "test_bot.pid"
    assert pid_file.exists()
    assert int(pid_file.read_text(encoding="utf-8").strip()) == os.getpid()

    # Clean release
    release_instance_lock()
    assert not pid_file.exists()


def test_dual_progress_rendering():
    from avito_sdk.telegram import render_telegram_progress_bar

    bar = render_telegram_progress_bar(50, 100, width=10)
    assert "🟩" in bar
    assert "⬜" in bar
    assert "50%" in bar


def test_single_instance_guard_collision(tmp_path):
    import pytest
    from avito_sdk.process_guard import SingleInstanceGuard, release_instance_lock

    g1 = SingleInstanceGuard(name="unit_test_collision", storage_dir=tmp_path, raise_on_collision=True)
    assert g1.acquire() is True

    # Second instance with same name must raise collision
    g2 = SingleInstanceGuard(name="unit_test_collision", storage_dir=tmp_path, raise_on_collision=True)
    with pytest.raises(RuntimeError, match="is already running"):
        g2.acquire()

    # Release g1
    g1.release()

    # Now g2 can acquire
    assert g2.acquire() is True
    g2.release()


def test_single_instance_guard_context_manager(tmp_path):
    import pytest
    from avito_sdk.process_guard import SingleInstanceGuard

    with SingleInstanceGuard(name="cm_test_app", storage_dir=tmp_path, raise_on_collision=True):
        # Nested/duplicate attempt fails
        with pytest.raises(RuntimeError):
            SingleInstanceGuard(name="cm_test_app", storage_dir=tmp_path, raise_on_collision=True).acquire()

    # After exiting block, can acquire again
    with SingleInstanceGuard(name="cm_test_app", storage_dir=tmp_path, raise_on_collision=True):
        pass


def test_single_instance_decorator():
    import pytest
    from avito_sdk.process_guard import single_instance

    @single_instance(name="dec_test_app", raise_on_collision=True)
    def my_function(depth=0):
        if depth == 0:
            # Recursive call fails because lock is already held
            my_function(depth=1)
        return "ok"

    with pytest.raises(RuntimeError):
        my_function()
