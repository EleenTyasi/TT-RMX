# =============================================================================
#  DistributedSOSCompanion.py  —  Client-side representation of SOS Companion
#  TT-RMX Personal Tinkering Project
# =============================================================================

from toontown.toon.DistributedNPCToonBase import DistributedNPCToonBase

class DistributedSOSCompanion(DistributedNPCToonBase):
    def __init__(self, cr):
        DistributedNPCToonBase.__init__(self, cr)
        self.maxHp = 100
        self.hp = 100
        self.trinketSlots = [0, 0]

    def setMaxHp(self, maxHp):
        self.maxHp = maxHp

    def setHp(self, hp):
        self.hp = hp

    def setTrinketSlots(self, t1, t2):
        self.trinketSlots = [t1, t2]
