from toontown.battle import DistributedBattle
from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import DirectLabel, DGG
from panda3d.core import TextNode
from toontown.toonbase import ToontownGlobals
from toontown.battle import CombatLogPanel


class DistributedBattleTutorial(DistributedBattle.DistributedBattle):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleTutorial')

    def __init__(self, cr):
        DistributedBattle.DistributedBattle.__init__(self, cr)
        self.tutorialRound = 0
        self.hintBanner = None

    def startTimer(self, ts = 0):
        self.townBattle.timer.hide()

    def enterWaitForInput(self, ts = 0):
        self.tutorialRound += 1
        DistributedBattle.DistributedBattle.enterWaitForInput(self, ts)
        self.showTutorialHint()

    def showTutorialHint(self):
        if self.hintBanner:
            self.hintBanner.destroy()
            self.hintBanner = None

        msg = ""
        if self.tutorialRound == 1:
            msg = "Tutorial Tom: Click your Cupcake or Squirting Flower to attack the Cog!"
            CombatLogPanel.logCombatEvent("Tutorial Tom: Click your Cupcake or Squirting Flower to attack!", CombatLogPanel.COLOR_SYSTEM)
        elif self.tutorialRound == 2:
            is_uber = (base.localAvatar.hp <= 1 or getattr(base.localAvatar, 'isUber', lambda: False)())
            if is_uber:
                msg = "Tutorial Tom: Hold on! You only have 1 Laff! Let me handle this with a Pink Slip!"
                CombatLogPanel.logCombatEvent("Tutorial Tom: Stand back! Firing the Cog for the Uber Toon!", CombatLogPanel.COLOR_SYSTEM)
            else:
                msg = "Tutorial Tom: Watch out! He's charging a heavy attack!\nClick PASS to raise your Guard Bubble Shield and block it!"
                CombatLogPanel.logCombatEvent("Tutorial Tom: Watch out! Click PASS to raise your Guard Bubble Shield and block it!", CombatLogPanel.COLOR_SYSTEM)
        elif self.tutorialRound >= 3:
            msg = "Tutorial Tom: Great job! Now finish him off with your last Gag!"
            CombatLogPanel.logCombatEvent("Tutorial Tom: Finish off the Supervisor Flunky!", CombatLogPanel.COLOR_SYSTEM)

        if msg:
            self.hintBanner = DirectLabel(
                parent=base.a2dTopCenter,
                relief=DGG.RAISED,
                frameColor=(0.1, 0.15, 0.35, 0.85),
                borderWidth=(0.01, 0.01),
                text=msg,
                text_scale=0.045,
                text_fg=(1, 1, 0.2, 1),
                text_shadow=(0, 0, 0, 1),
                text_font=ToontownGlobals.getSignFont(),
                text_align=TextNode.ACenter,
                pos=(0, 0, -0.15),
                pad=(0.04, 0.02)
            )

    def exitWaitForInput(self):
        if self.hintBanner:
            self.hintBanner.destroy()
            self.hintBanner = None
        DistributedBattle.DistributedBattle.exitWaitForInput(self)

    def playReward(self, ts):
        if self.hintBanner:
            self.hintBanner.destroy()
            self.hintBanner = None
        self.movie.playTutorialReward(ts, self.uniqueName('reward'), self.handleRewardDone)

    def cleanup(self):
        if self.hintBanner:
            self.hintBanner.destroy()
            self.hintBanner = None
        DistributedBattle.DistributedBattle.cleanup(self)
