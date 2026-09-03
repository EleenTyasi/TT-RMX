import sys
import os
import time
import traceback
from datetime import datetime
from panda3d.core import *
from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject
from toontown.toonbase import ToontownGlobals

class CrashShield(DirectObject):
    """
    Crash Shield & Soft-Recovery System for TT-RMX Fusion Engine.
    Intercepts unhandled runtime exceptions, logs them to logs/crash_shield.log,
    recovers avatar gameplay state, and displays a non-intrusive recovery notice.
    """

    def __init__(self):
        DirectObject.__init__(self)
        self.log_file = os.path.join(os.getcwd(), "logs", "crash_shield.log")
        self.last_traceback = ""
        self.notice = None
        self.noticeTask = None

        os.makedirs(os.path.join(os.getcwd(), "logs"), exist_ok=True)
        self.installHooks()

    def installHooks(self):
        self.orig_excepthook = sys.excepthook
        sys.excepthook = self.handleException

    def handleException(self, exc_type, exc_value, exc_traceback):
        # Ignore normal program exit
        if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
            if self.orig_excepthook:
                self.orig_excepthook(exc_type, exc_value, exc_traceback)
            return

        formatted = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        self.last_traceback = formatted

        # Write to log file
        self.recordCrash(formatted)

        # Print to console if available
        if hasattr(base, 'console') and base.console:
            base.console.log(f"CrashShield caught exception: {exc_value}", color='error')

        # Soft-recover the avatar state
        self.softRecover()

        # Display notice to user
        self.showNotice(str(exc_value))

    def recordCrash(self, tb_str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        toon_info = "Not logged in"
        zone_info = "Unknown"

        if hasattr(base, 'localAvatar') and base.localAvatar:
            try:
                av = base.localAvatar
                toon_info = f"{av.getName()} (HP: {av.getHp()}/{av.getMaxHp()})"
                zone_info = str(getattr(av, 'zoneId', 'Unknown'))
            except Exception:
                pass

        entry = (
            f"\n{'='*70}\n"
            f"[CRASH SHIELD INTERCEPT] - {now}\n"
            f"Toon: {toon_info} | Zone: {zone_info}\n"
            f"{'-'*70}\n"
            f"{tb_str}\n"
            f"{'='*70}\n"
        )

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass

    def softRecover(self):
        """Attempt to restore the player to a safe interactive state."""
        try:
            # Reset any stuck input keys
            if hasattr(base, 'localAvatar') and base.localAvatar:
                if hasattr(base.localAvatar, 'fsm'):
                    current_state = base.localAvatar.fsm.getCurrentState()
                    if current_state and current_state.getName() not in ('walk', 'neutral', 'run'):
                        try:
                            base.localAvatar.fsm.request('walk')
                        except Exception:
                            pass
        except Exception:
            pass

    def showNotice(self, err_msg):
        """Show non-intrusive on-screen notice."""
        try:
            if self.notice:
                self.notice.destroy()

            short_err = (err_msg[:45] + '...') if len(err_msg) > 45 else err_msg

            self.notice = DirectLabel(
                parent=base.a2dBottomRight,
                relief=DGG.FLAT,
                frameColor=(0.15, 0.05, 0.05, 0.88),
                frameSize=(-0.75, 0.02, -0.05, 0.05),
                pos=(-0.05, 0, 0.12),
                text=f"[!] Shield Recovered: {short_err}\n(Logged to logs/crash_shield.log)",
                text_scale=0.032,
                text_align=TextNode.ALeft,
                text_fg=(1.0, 0.4, 0.4, 1.0),
                text_pos=(-0.72, 0.01),
                text_font=ToontownGlobals.getToonFont()
            )

            # Auto hide after 7 seconds
            taskMgr.remove('hideCrashNotice')
            taskMgr.doMethodLater(7.0, self.hideNotice, 'hideCrashNotice')
        except Exception:
            pass

    def hideNotice(self, task=None):
        if self.notice:
            self.notice.destroy()
            self.notice = None
        return task.done if task else None
