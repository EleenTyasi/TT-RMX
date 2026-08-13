# ToonExpGui.py — Bottom-centered Toon Level EXP HUD widget near the Laff Meter

from direct.gui.DirectGui import *
from panda3d.core import *
from direct.showbase.DirectObject import DirectObject
from toontown.toonbase import ToontownGlobals
from . import ToonLevelGlobals

class ToonExpGui(DirectObject):
    def __init__(self):
        DirectObject.__init__(self)
        self.container = DirectFrame(
            parent=base.a2dBottomLeft,
            relief=DGG.SUNKEN,
            frameColor=(0.1, 0.1, 0.15, 0.75),
            frameSize=(0.0, 0.48, 0.0, 0.11),
            pos=(0.32, 0.0, 0.07)
        )

        self.levelLabel = DirectLabel(
            parent=self.container,
            relief=None,
            pos=(0.07, 0, 0.055),
            text="LVL 1",
            text_scale=0.045,
            text_fg=(1, 0.9, 0.2, 1),
            text_shadow=(0, 0, 0, 1),
            text_font=ToontownGlobals.getSignFont(),
            text_align=TextNode.ACenter
        )

        self.expBar = DirectWaitBar(
            parent=self.container,
            relief=DGG.SUNKEN,
            pos=(0.30, 0, 0.055),
            frameSize=(-0.16, 0.16, -0.022, 0.022),
            borderWidth=(0.01, 0.01),
            scale=1.0,
            frameColor=(0.2, 0.2, 0.3, 1),
            barColor=(0.2, 0.8, 1.0, 1),
            range=100,
            value=0
        )

        self.expText = DirectLabel(
            parent=self.container,
            relief=None,
            pos=(0.30, 0, 0.015),
            text="0 / 50 EXP",
            text_scale=0.028,
            text_fg=(1, 1, 1, 1),
            text_shadow=(0, 0, 0, 1),
            text_font=ToontownGlobals.getToonFont(),
            text_align=TextNode.ACenter
        )

        self.accept('toonLevelChanged', self.updateDisplay)
        self.accept('toonExpChanged', self.updateDisplay)

        self.updateDisplay()

    def updateDisplay(self, *args):
        if not hasattr(base, 'localAvatar') or not base.localAvatar:
            return

        level = base.localAvatar.getToonLevel()
        exp = base.localAvatar.getToonExp()

        self.levelLabel['text'] = f"LVL {level}"

        if level >= ToonLevelGlobals.MAX_TOON_LEVEL:
            self.expBar['range'] = 100
            self.expBar['value'] = 100
            self.expText['text'] = "MAX LEVEL"
        else:
            currentLvlExp = ToonLevelGlobals.getExpForLevel(level)
            nextLvlExp = ToonLevelGlobals.getExpForNextLevel(level)
            neededExp = nextLvlExp - currentLvlExp
            progressExp = exp - currentLvlExp
            percent = max(0, min(100, int((progressExp / float(neededExp)) * 100)))

            self.expBar['range'] = 100
            self.expBar['value'] = percent
            self.expText['text'] = f"{progressExp} / {neededExp} EXP"

    def show(self):
        if self.container:
            self.container.show()

    def hide(self):
        if self.container:
            self.container.hide()

    def destroy(self):
        self.ignoreAll()
        if self.container:
            self.container.destroy()
            self.container = None
