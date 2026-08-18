from direct.directnotify import DirectNotifyGlobal
from . import HoodDataAI
from toontown.toonbase import ToontownGlobals
from toontown.safezone import DistributedTrolleyAI
from toontown.safezone import MMTreasurePlannerAI
from toontown.classicchars import DistributedMinnieAI
from toontown.safezone import DistributedMMPianoAI

class MMHoodDataAI(HoodDataAI.HoodDataAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('MMHoodDataAI')

    def __init__(self, air, zoneId=None):
        hoodId = ToontownGlobals.MinniesMelodyland
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
        self.treasurePlanner = MMTreasurePlannerAI.MMTreasurePlannerAI(self.zoneId)
        self.treasurePlanner.start()
        # self.classicChar = DistributedMinnieAI.DistributedMinnieAI(self.air)
        # self.classicChar.generateWithRequired(self.zoneId)
        # self.classicChar.start()
        # self.addDistObj(self.classicChar)
        from toontown.toon import NPCToons
        from toontown.toonbase import TTLocalizer
        self.healerHank = NPCToons.createHealerHank(self.air, self.zoneId, (-73.1605, 25.7023, 6.525), -155.58)
        self.addDistObj(self.healerHank)
        self.banker = NPCToons.createBanker(self.air, self.zoneId, (63.0, -18.0, -13.0), -270.0, name=TTLocalizer.BankerBarryName, npcId=20063)
        self.addDistObj(self.banker)
