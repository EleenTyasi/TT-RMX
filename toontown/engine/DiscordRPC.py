import os
import sys
import json
import time
import struct
import threading
from direct.showbase.DirectObject import DirectObject

# Default Discord Application ID for TT-RMX (can be customized)
DEFAULT_CLIENT_ID = "1200000000000000000"

class DiscordRPC(DirectObject):
    """
    Zero-dependency native Discord Rich Presence IPC client.
    Connects to Discord via local named pipe on Windows (\\.\pipe\discord-ipc-0).
    """

    OP_HANDSHAKE = 0
    OP_FRAME = 1
    OP_CLOSE = 2
    OP_PING = 3
    OP_PONG = 4

    def __init__(self, client_id=DEFAULT_CLIENT_ID):
        DirectObject.__init__(self)
        self.client_id = client_id
        self.pipe = None
        self.connected = False
        self.start_time = int(time.time())
        self.last_update = 0

        if sys.platform == "win32":
            self.startBackgroundThread()

    def startBackgroundThread(self):
        t = threading.Thread(target=self._workerLoop, daemon=True)
        t.start()

    def _connect(self):
        for i in range(10):
            pipe_name = rf"\\.\pipe\discord-ipc-{i}"
            try:
                self.pipe = open(pipe_name, "w+b")
                # Send Handshake
                payload = json.dumps({"v": 1, "client_id": self.client_id}).encode("utf-8")
                header = struct.pack("<II", self.OP_HANDSHAKE, len(payload))
                self.pipe.write(header + payload)
                self.pipe.flush()

                # Read handshake response
                resp_header = self.pipe.read(8)
                if resp_header and len(resp_header) == 8:
                    op, length = struct.unpack("<II", resp_header)
                    resp_data = self.pipe.read(length)
                    self.connected = True
                    return True
            except Exception:
                self.pipe = None
        return False

    def _workerLoop(self):
        while True:
            try:
                if not self.connected:
                    if not self._connect():
                        time.sleep(15)
                        continue

                # When connected, update activity if in game
                self.updatePresence()
            except Exception:
                self.connected = False
                if self.pipe:
                    try:
                        self.pipe.close()
                    except Exception:
                        pass
                self.pipe = None

            time.sleep(5)

    def updatePresence(self):
        if not self.connected or not self.pipe:
            return

        now = time.time()
        if now - self.last_update < 4:
            return
        self.last_update = now

        details = "Exploring Toontown"
        state = "In Main Menu"

        if hasattr(base, 'localAvatar') and base.localAvatar:
            try:
                av = base.localAvatar
                name = av.getName()
                hp = av.getHp()
                max_hp = av.getMaxHp()

                level = getattr(av, 'getToonLevel', lambda: 1)()
                details = f"Lv. {level} {name} ({hp}/{max_hp} Laff)"

                # Check location
                zone_name = "Toontown"
                if hasattr(base.cr, 'playGame') and base.cr.playGame and base.cr.playGame.hood:
                    zone_name = base.cr.playGame.hood.id.capitalize()
                state = f"Exploring {zone_name}"
            except Exception:
                pass

        activity = {
            "details": details,
            "state": state,
            "timestamps": {"start": self.start_time},
            "assets": {
                "large_image": "icon",
                "large_text": "Toontown Remix (TT-RMX)",
            }
        }

        payload = json.dumps({
            "cmd": "SET_ACTIVITY",
            "args": {
                "pid": os.getpid(),
                "activity": activity
            },
            "nonce": str(time.time())
        }).encode("utf-8")

        header = struct.pack("<II", self.OP_FRAME, len(payload))
        self.pipe.write(header + payload)
        self.pipe.flush()

        # Discard response header and payload
        resp_header = self.pipe.read(8)
        if resp_header and len(resp_header) == 8:
            op, length = struct.unpack("<II", resp_header)
            self.pipe.read(length)
