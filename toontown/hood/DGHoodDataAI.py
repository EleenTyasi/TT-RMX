from direct.directnotify import DirectNotifyGlobal
from . import HoodDataAI
from toontown.toonbase import ToontownGlobals
from toontown.safezone import DistributedTrolleyAI
from toontown.safezone import DGTreasurePlannerAI
from toontown.classicchars import DistributedGoofyAI
from toontown.classicchars import DistributedDaisyAI
from toontown.safezone import DistributedDGFlowerAI
from toontown.safezone import ButterflyGlobals

class DGHoodDataAI(HoodDataAI.HoodDataAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DGHoodDataAI')

    def __init__(self, air, zoneId=None):
        hoodId = ToontownGlobals.DaisyGardens
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
        self.treasurePlanner = DGTreasurePlannerAI.DGTreasurePlannerAI(self.zoneId)
        self.treasurePlanner.start()
        # self.classicChar = DistributedDaisyAI.DistributedDaisyAI(self.air)
        # self.classicChar.generateWithRequired(self.zoneId)
        # self.classicChar.start()
        # self.addDistObj(self.classicChar)
        flower = DistributedDGFlowerAI.DistributedDGFlowerAI(self.air)
        flower.generateWithRequired(self.zoneId)
        flower.start()
        self.addDistObj(flower)
        from toontown.toon import NPCToons
        self.healerHank = NPCToons.createHealerHank(self.air, self.zoneId, (-25.1167, 213.575, 10.026), 0.0)
        self.addDistObj(self.healerHank)
        self.createButterflies(ButterflyGlobals.DG)
