"""
StaminaBar.py

Sleek on-screen Stamina Bar HUD widget for TT-RMX.
Displays the Toon's current stamina, maximum stamina, and unlimited playground mode.
"""
from panda3d.core import Vec4, TextNode
from direct.gui import DirectGuiGlobals
from direct.gui.DirectGui import DirectFrame, DirectWaitBar, DirectLabel
from toontown.toonbase import ToontownGlobals


class StaminaBar(DirectFrame):
    def __init__(self, stamina=100, maxStamina=100):
        DirectFrame.__init__(self, relief=None, sortOrder=50)
        self.initialiseoptions(StaminaBar)
        self.stamina = stamina
        self.maxStamina = maxStamina
        self.load()

    def load(self):
        self.bar = DirectWaitBar(
            parent=self,
            relief=DirectGuiGlobals.SUNKEN,
            borderWidth=(0.004, 0.004),
            range=self.maxStamina,
            value=self.stamina,
            frameSize=(-0.24, 0.24, -0.024, 0.024),
            frameColor=(0.1, 0.1, 0.1, 0.75),
            barColor=(0.2, 0.85, 0.35, 0.9),
        )
        self.label = DirectLabel(
            parent=self.bar,
            relief=None,
            text="STAMINA",
            text_scale=0.033,
            text_pos=(0, -0.010),
            text_fg=(1, 1, 1, 0.95),
            text_shadow=(0, 0, 0, 1),
            text_font=ToontownGlobals.getSignFont(),
        )

    def update(self, current, max_val, is_unlimited=False):
        self.stamina = max(0, min(current, max_val))
        self.maxStamina = max(1, max_val)
        self.bar['range'] = self.maxStamina
        self.bar['value'] = self.stamina

        if is_unlimited:
            self.bar['barColor'] = (0.2, 0.75, 1.0, 0.9)  # Energized cyan for safe zones
            self.label['text'] = "SPRINT (INFINITE)"
        else:
            ratio = float(self.stamina) / float(self.maxStamina)
            if ratio > 0.5:
                # Green to Yellow
                g_ratio = (ratio - 0.5) * 2.0
                self.bar['barColor'] = (1.0 - 0.7 * g_ratio, 0.85, 0.25, 0.9)
            else:
                # Yellow to Red
                r_ratio = ratio * 2.0
                self.bar['barColor'] = (0.95, 0.85 * r_ratio, 0.2, 0.9)
            self.label['text'] = "%d / %d" % (int(self.stamina), int(self.maxStamina))

    def setBarVisible(self, visible):
        if visible:
            self.show()
        else:
            self.hide()

    def destroy(self):
        if hasattr(self, 'bar') and self.bar:
            self.bar.destroy()
            self.bar = None
        DirectFrame.destroy(self)
