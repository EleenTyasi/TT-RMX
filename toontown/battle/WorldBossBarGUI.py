from direct.gui.DirectGui import *
from panda3d.core import *
from direct.interval.IntervalGlobal import *
from toontown.toontowngui import TTDialog

class WorldBossBarGUI:
    def __init__(self, bossName, maxHp, currHp):
        self.maxHp = maxHp
        self.currHp = currHp
        self.bossName = bossName
        self.tutorialDialog = None
        self.frame = DirectFrame(parent=aspect2d, relief=None, pos=(0, 0, 0.82), scale=1.0)
        self.nameLabel = DirectLabel(parent=self.frame, relief=None, text=str(self.bossName).upper(), text_scale=0.065, text_fg=(1, 0.85, 0.2, 1), text_shadow=(0, 0, 0, 1), pos=(0, 0, 0.05))
        self.bgBar = DirectFrame(parent=self.frame, relief=DGG.FLAT, frameColor=(0.1, 0.1, 0.1, 0.85), frameSize=(-0.62, 0.62, -0.025, 0.025), pos=(0, 0, 0))
        self.hpBar = DirectWaitBar(parent=self.frame, relief=DGG.FLAT, frameColor=(0.2, 0.2, 0.2, 0.7), barColor=(0.9, 0.15, 0.15, 1.0), frameSize=(-0.6, 0.6, -0.02, 0.02), pos=(0, 0, 0), range=self.maxHp, value=self.currHp)
        self.hpLabel = DirectLabel(parent=self.frame, relief=None, text='%s / %s' % (self.currHp, self.maxHp), text_scale=0.04, text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), pos=(0, 0, -0.012))

        # Check if localAvatar has seen a World Boss before
        if hasattr(base, 'localAvatar') and base.localAvatar:
            seen = getattr(base.localAvatar, 'seenWorldBossTutorial', False)
            if not seen:
                base.localAvatar.seenWorldBossTutorial = True
                self.showTutorial()

    def showTutorial(self):
        msg = (
            "\\aPLAYGROUND WORLD BOSS ENCOUNTER!\\a\n\n"
            "You have engaged a rare Playground World Boss!\n\n"
            "* World Bosses possess huge Health Pools displayed on the Boss Bar above.\n"
            "* You have 7 TURNS in battle before the Boss flees.\n"
            "* Any damage you inflict is PERSISTENT! If the Boss flees, its missing Health is saved for the next time you encounter it.\n"
            "* Defeating a Playground's World Boss for the first time rewards you with a permanent +2 MAX LAFF BOOST!"
        )
        self.tutorialDialog = TTDialog.TTDialog(
            text=msg,
            command=self.__closeTutorial,
            style=TTDialog.Acknowledge,
            fadeScreen=0.5,
            text_wordwrap=18,
            text_scale=0.05
        )

    def __closeTutorial(self, value):
        if self.tutorialDialog:
            self.tutorialDialog.cleanup()
            self.tutorialDialog = None

    def updateHp(self, newHp):
        self.currHp = max(0, min(self.maxHp, newHp))
        self.hpBar['value'] = self.currHp
        self.hpLabel['text'] = '%s / %s' % (self.currHp, self.maxHp)

    def destroy(self):
        if self.tutorialDialog:
            self.tutorialDialog.cleanup()
            self.tutorialDialog = None
        if hasattr(self, 'frame') and self.frame:
            self.frame.destroy()
            self.frame = None
