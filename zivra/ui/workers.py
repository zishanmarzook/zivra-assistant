from PySide6.QtCore import QObject, QRunnable, Signal


class Signals(QObject):
    finished = Signal(object, object)


class Job(QRunnable):
    def __init__(self, function):
        super().__init__()
        self.function = function
        self.signals = Signals()

    def run(self):
        try:
            value, error = self.function(), None
        except Exception as exc:
            value, error = None, str(exc)
        self.signals.finished.emit(value, error)
