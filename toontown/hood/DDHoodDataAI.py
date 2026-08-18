from direct.directnotify import DirectNotifyGlobal
from . import HoodDataAI
from toontown.toonbase import ToontownGlobals
from toontown.safezone import DistributedTrolleyAI
from toontown.safezone import DDTreasurePlannerAI
from toontown.safezone import DistributedBoatAI
from toontown.classicchars import DistributedDonaldDockAI

class DDHoodDataAI(HoodDataAI.HoodDataAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DDHoodDataAI')

    def __init__(self, air, zoneId=None):
        hoodId = ToontownGlobals.DonaldsDock
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
        self.treasurePlanner = DDTreasurePlannerAI.DDTreasurePlannerAI(self.zoneId)
        self.treasurePlanner.start()
        boat = DistributedBoatAI.DistributedBoatAI(self.air)
        boat.generateWithRequired(self.zoneId)
        boat.start()
        self.addDistObj(boat)
        self.classicChar = DistributedDonaldDockAI.DistributedDonaldDockAI(self.air)
        self.classicChar.generateWithRequired(self.zoneId)
        self.classicChar.start()
        self.addDistObj(self.classicChar)
        from toontown.toon import NPCToons
        from toontown.toonbase import TTLocalizer
        self.healerHank = NPCToons.createHealerHank(self.air, self.zoneId, (-115.952, -39.2264, 5.69199), -98.0)
        self.addDistObj(self.healerHank)
        self.banker = NPCToons.createBanker(self.air, self.zoneId, (-62.0, 134.0, 3.0), -210.0, name=TTLocalizer.BankerBarnabyName, npcId=20061)
        self.addDistObj(self.banker)
