# TrackPage.py — Replaced legacy Gag Training page with comprehensive Toon Stats page

from panda3d.core import *
from . import ShtikerPage
from direct.gui.DirectGui import *
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer

class TrackPage(ShtikerPage.ShtikerPage):

    def __init__(self):
        ShtikerPage.ShtikerPage.__init__(self)
        self.statLabels = {}

    def load(self):
        ShtikerPage.ShtikerPage.load(self)
        self.title = DirectLabel(
            parent=self,
            relief=None,
            text="TOON STATS",
            text_scale=0.10,
            text_font=ToontownGlobals.getSignFont(),
            text_fg=(1, 0.9, 0.2, 1),
            text_shadow=(0, 0, 0, 1),
            pos=(0, 0, 0.62)
        )

        self.subtitle = DirectLabel(
            parent=self,
            relief=None,
            text="Lifetime Combat & Progression Records",
            text_scale=0.045,
            text_font=ToontownGlobals.getToonFont(),
            text_fg=(0.3, 0.3, 0.3, 1),
            pos=(0, 0, 0.53)
        )

        # Background Frame
        self.mainFrame = DirectFrame(
            parent=self,
            relief=DGG.SUNKEN,
            frameSize=(-0.75, 0.75, -0.55, 0.45),
            frameColor=(0.95, 0.95, 0.9, 0.85),
            borderWidth=(0.01, 0.01),
            pos=(0, 0, -0.05)
        )

        # Left Column — Combat Stats
        self.createStatRow("directHits", "Direct Hits:", (-0.68, 0.34))
        self.createStatRow("critHits", "Critical Hits:", (-0.68, 0.24))
        self.createStatRow("critDirectHits", "Critical Direct Hits:", (-0.68, 0.14))
        self.createStatRow("dmgDealt", "Damage Dealt:", (-0.68, 0.04))
        self.createStatRow("dmgTaken", "Damage Taken:", (-0.68, -0.06))
        self.createStatRow("dmgHealed", "Damage Healed:", (-0.68, -0.16))

        # Right Column — Cogs & Adventure
        self.createStatRow("cogsKilled", "Cogs Destroyed:", (0.05, 0.34))
        self.createStatRow("specCogsKilled", "Special Cogs Defeated:", (0.05, 0.24))
        self.createStatRow("caloriesThrown", "Calories Thrown:", (0.05, 0.14))
        self.createStatRow("timesSad", "Times Gone Sad:", (0.05, 0.04))
        self.createStatRow("playTime", "Playtime:", (0.05, -0.06))
        self.createStatRow("uberStatus", "Uber Status:", (0.05, -0.16))

    def createStatRow(self, key, labelText, pos):
        x, y = pos
        lbl = DirectLabel(
            parent=self.mainFrame,
            relief=None,
            text=labelText,
            text_scale=0.042,
            text_font=ToontownGlobals.getToonFont(),
            text_fg=(0.1, 0.2, 0.4, 1),
            text_align=TextNode.ALeft,
            pos=(x, 0, y)
        )
        val = DirectLabel(
            parent=self.mainFrame,
            relief=None,
            text="0",
            text_scale=0.042,
            text_font=ToontownGlobals.getSignFont(),
            text_fg=(0.8, 0.1, 0.1, 1),
            text_align=TextNode.ARight,
            pos=(x + 0.62, 0, y)
        )
        self.statLabels[key] = val

    def formatPlaytime(self, totalSeconds):
        hours = totalSeconds // 3600
        minutes = (totalSeconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes} mins"

    def updatePage(self):
        if not hasattr(base, 'localAvatar') or not base.localAvatar:
            return

        stats = base.localAvatar.getToonStats()

        directHits = stats[0] if len(stats) > 0 else 0
        critHits = stats[1] if len(stats) > 1 else 0
        critDirectHits = stats[2] if len(stats) > 2 else 0
        calories = stats[3] if len(stats) > 3 else 0
        cogsKilled = stats[4] if len(stats) > 4 else 0
        timesSad = stats[5] if len(stats) > 5 else 0
        playtime = stats[6] if len(stats) > 6 else 0
        dmgDealt = stats[7] if len(stats) > 7 else 0
        dmgTaken = stats[8] if len(stats) > 8 else 0
        dmgHealed = stats[9] if len(stats) > 9 else 0
        specCogs = stats[10] if len(stats) > 10 else 0

        self.statLabels["directHits"]['text'] = f"{directHits:,}"
        self.statLabels["critHits"]['text'] = f"{critHits:,}"
        self.statLabels["critDirectHits"]['text'] = f"{critDirectHits:,}"
        self.statLabels["dmgDealt"]['text'] = f"{dmgDealt:,}"
        self.statLabels["dmgTaken"]['text'] = f"{dmgTaken:,}"
        self.statLabels["dmgHealed"]['text'] = f"{dmgHealed:,}"

        self.statLabels["cogsKilled"]['text'] = f"{cogsKilled:,}"
        self.statLabels["specCogsKilled"]['text'] = f"{specCogs:,}"
        self.statLabels["caloriesThrown"]['text'] = f"{calories:,} kcal"
        self.statLabels["timesSad"]['text'] = f"{timesSad:,}"
        self.statLabels["playTime"]['text'] = self.formatPlaytime(playtime)

        laffCap = getattr(base.localAvatar, 'laffCap', 0)
        if laffCap > 0:
            self.statLabels["uberStatus"]['text'] = f"UBER [{laffCap} Laff]"
            self.statLabels["uberStatus"]['text_fg'] = (0.9, 0.1, 0.1, 1)
        else:
            self.statLabels["uberStatus"]['text'] = "Standard Toon"
            self.statLabels["uberStatus"]['text_fg'] = (0.2, 0.6, 0.2, 1)

    def enter(self):
        self.updatePage()
        self.accept('toonStatsChanged', self.updatePage)
        ShtikerPage.ShtikerPage.enter(self)

    def exit(self):
        self.ignore('toonStatsChanged')
        ShtikerPage.ShtikerPage.exit(self)

    def unload(self):
        self.statLabels = {}
        ShtikerPage.ShtikerPage.unload(self)
