"""Desktop entry point and a read-only diagnostic CLI for development."""
import argparse
import json
import sys
from zivra import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(description="ZIVRA local Windows assistant")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--diagnose", action="store_true", help="Print a read-only local system report without launching the UI")
    parser.add_argument("--smoke-test", action="store_true", help="Exercise the Qt UI, command worker and monitoring, then exit")
    args = parser.parse_args(argv)
    from zivra.config import Settings
    settings = Settings()
    if args.diagnose:
        from zivra.core.assistant import Assistant
        assistant = Assistant(settings)
        try:
            result = assistant.respond("system status")
            print(result)
            return 1 if result.startswith("Could not complete") else 0
        finally:
            assistant.shutdown()
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    from zivra.ui.instance import Instance
    from zivra.ui.main_window import MainWindow
    app = QApplication([sys.argv[0]])
    app.setApplicationName("ZIVRA")
    app.setOrganizationName("ZIVRA")
    instance = Instance(settings.directory)
    window = None
    if not instance.acquire(lambda: window.restore() if window else None):
        return 2 if args.smoke_test else 0
    try:
        window = MainWindow(settings)
        window.show()
        if args.smoke_test:
            # Check real worker results, not just whether a window was constructed.
            window.submit("system status")
            state = {"attempts": 0, "passed": False}

            def verify():
                state["attempts"] += 1
                if not window.foreground_busy and not window.monitor_busy:
                    state["passed"] = "RAM:" in window.chat.toPlainText() and "Disk free:" in window.monitor_text.text()
                    from psutil import Process
                    print(json.dumps({"ui_smoke_passed": state["passed"], "rss_mb": round(Process().memory_info().rss / 1024**2, 1)}), flush=True)
                    window.request_quit()
                elif state["attempts"] >= 100:
                    print("UI smoke test timed out", flush=True)
                    window.request_quit()
                else:
                    QTimer.singleShot(100, verify)

            QTimer.singleShot(300, verify)
        code = app.exec()
        return (0 if state["passed"] else 1) if args.smoke_test else code
    finally:
        instance.close()


if __name__ == "__main__":
    raise SystemExit(main())
