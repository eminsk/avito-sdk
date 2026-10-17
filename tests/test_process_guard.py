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
