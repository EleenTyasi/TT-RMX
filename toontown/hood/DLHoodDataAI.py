from direct.directnotify import DirectNotifyGlobal
from . import HoodDataAI
from toontown.toonbase import ToontownGlobals
from toontown.safezone import DistributedTrolleyAI
from toontown.safezone import DLTreasurePlannerAI
from toontown.classicchars import DistributedDonaldAI
from toontown.safezone import ButterflyGlobals

class DLHoodDataAI(HoodDataAI.HoodDataAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DLHoodDataAI')

    def __init__(self, air, zoneId=None):
        hoodId = ToontownGlobals.DonaldsDreamland
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
        self.treasurePlanner = DLTreasurePlannerAI.DLTreasurePlannerAI(self.zoneId)
        self.treasurePlanner.start()
        # self.classicChar = DistributedDonaldAI.DistributedDonaldAI(self.air)
        # self.classicChar.generateWithRequired(self.zoneId)
        # self.classicChar.start()
        # self.addDistObj(self.classicChar)
        from toontown.toon import NPCToons
        from toontown.toonbase import TTLocalizer
        self.healerHank = NPCToons.createHealerHank(self.air, self.zoneId, (-32.7906, -98.2514, 0.0250001), 0.0)
        self.addDistObj(self.healerHank)
        self.banker = NPCToons.createBanker(self.air, self.zoneId, (-28.0, -2.0, -14.0), -117.0, name=TTLocalizer.BankerBrunoName, npcId=20065)
        self.addDistObj(self.banker)
