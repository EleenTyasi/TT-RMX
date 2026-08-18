from direct.directnotify import DirectNotifyGlobal
from . import HoodDataAI
from toontown.toonbase import ToontownGlobals
from toontown.safezone import DistributedTrolleyAI
from toontown.safezone import BRTreasurePlannerAI
from toontown.classicchars import DistributedPlutoAI
from toontown.toon import DistributedNPCFishermanAI

class BRHoodDataAI(HoodDataAI.HoodDataAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('BRHoodDataAI')

    def __init__(self, air, zoneId=None):
        hoodId = ToontownGlobals.TheBrrrgh
        if zoneId == None:
            zoneId = hoodId
        HoodDataAI.HoodDataAI.__init__(self, air, zoneId, hoodId)
        return

    def startup(self):
        HoodDataAI.HoodDataAI.startup(self)
        trolley = DistributedTrolleyAI.DistributedTrolleyAI(self.air)
        trolley.generateWithRequired(self.zoneId)
        trolley.start()
        self.addDistObj(trolley)
        self.treasurePlanner = BRTreasurePlannerAI.BRTreasurePlannerAI(self.zoneId)
        self.treasurePlanner.start()
        # self.classicChar = DistributedPlutoAI.DistributedPlutoAI(self.air)
        # self.classicChar.generateWithRequired(self.zoneId)
        # self.classicChar.start()
        # self.addDistObj(self.classicChar)
        from toontown.toon import NPCToons
        self.healerHank = NPCToons.createHealerHank(self.air, self.zoneId, (36.0, -83.0, 6.17), -120.0)
        self.addDistObj(self.healerHank)
