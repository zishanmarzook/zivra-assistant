import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import time
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication
import pytest
from zivra.config import Settings
from zivra.ui.main_window import MainWindow, PAGES
from zivra.ui.instance import Instance


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def pump(app, condition, timeout=10):
    deadline = time.monotonic() + timeout
    while not condition() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert condition(), "Qt worker did not complete"


def finish(window, app):
    window.timer.stop()
    pump(app, lambda: not window.jobs)
    window.quitting = True
    window.close()


def test_desktop_command_metrics_and_privacy_controls(app, tmp_path):
    window = MainWindow(Settings(tmp_path))
    try:
        window.show()
        assert window.pages.count() == len(PAGES)
        for row in range(len(PAGES)):
            window.navigation.setCurrentRow(row)
            app.processEvents()
            assert window.pages.currentIndex() == row
        window.submit("system status")
        pump(app, lambda: not window.jobs)
        assert "RAM:" in window.chat.toPlainText()
        assert "Disk free:" in window.monitor_text.text()
        window.settings.set("remember_history", True)
        window.history_check.setChecked(True)
        window.submit("help")
        pump(app, lambda: not window.jobs)
        assert window.settings.history()
        window.history_check.setChecked(False)
        assert not window.settings.history()
        window.clear_chat()
        assert not window.chat.toPlainText()
    finally:
        finish(window, app)


def test_worker_callback_runs_on_ui_thread(app, tmp_path):
    window = MainWindow(Settings(tmp_path))
    threads = []
    try:
        window.start_job(lambda: QThread.currentThread(), lambda worker, error: threads.append((worker, QThread.currentThread())))
        pump(app, lambda: bool(threads))
        assert threads[0][0] != app.thread()
        assert threads[0][1] == app.thread()
    finally:
        finish(window, app)


def test_second_instance_only_restores_window(app, tmp_path):
    restored = []
    first = Instance(tmp_path)
    second = Instance(tmp_path)
    try:
        assert first.acquire(lambda: restored.append(True))
        assert not second.acquire(lambda: None)
        pump(app, lambda: bool(restored))
    finally:
        first.close()
