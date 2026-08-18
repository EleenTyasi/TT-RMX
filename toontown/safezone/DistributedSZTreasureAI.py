from . import DistributedTreasureAI
from toontown.toonbase import ToontownGlobals

class DistributedSZTreasureAI(DistributedTreasureAI.DistributedTreasureAI):

    def __init__(self, air, treasurePlanner = None, x = 0, y = 0, z = 0):
        DistributedTreasureAI.DistributedTreasureAI.__init__(self, air, treasurePlanner, x, y, z)
        self.healAmount = getattr(treasurePlanner, 'healAmount', 10) if treasurePlanner is not None else 10

    def validAvatar(self, av):
        return av.hp > 0 and av.hp < av.maxHp

    def d_setGrab(self, avId):
        DistributedTreasureAI.DistributedTreasureAI.d_setGrab(self, avId)
        if avId in self.air.doId2do:
            av = self.air.doId2do[avId]
            if av.hp > 0 and av.hp < av.maxHp:
                if ToontownGlobals.VALENTINES_DAY in simbase.air.holidayManager.currentHolidays:
                    av.toonUp(self.healAmount * 2)
                else:
                    av.toonUp(self.healAmount)
