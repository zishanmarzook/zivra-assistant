"""Per-user single instance; IPC can only restore a window, never run commands."""
import hashlib
from PySide6.QtCore import QLockFile, QIODevice
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class Instance:
    def __init__(self, directory):
        self.name = "zivra-" + hashlib.sha256(str(directory.resolve()).encode()).hexdigest()[:24]
        self.lock = QLockFile(str(directory / "instance.lock"))
        self.server = QLocalServer()
        self.server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)

    def acquire(self, restore):
        if not self.lock.tryLock(100):
            socket = QLocalSocket()
            socket.connectToServer(self.name, QIODevice.OpenModeFlag.WriteOnly)
            if socket.waitForConnected(1500):
                socket.write(b"RESTORE")
                socket.waitForBytesWritten(1000)
                socket.disconnectFromServer()
            return False
        QLocalServer.removeServer(self.name)
        if not self.server.listen(self.name):
            self.lock.unlock()
            raise RuntimeError("Could not establish ZIVRA's single-instance channel")

        def connected():
            while self.server.hasPendingConnections():
                socket = self.server.nextPendingConnection()
                # A same-user connection only restores the UI. Ignore all payloads.
                restore()
                socket.disconnectFromServer()
                socket.deleteLater()

        self.server.newConnection.connect(connected)
        return True

    def close(self):
        self.server.close()
        self.lock.unlock()
