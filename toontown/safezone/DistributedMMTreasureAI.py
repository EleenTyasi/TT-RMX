from . import DistributedSZTreasureAI

class DistributedMMTreasureAI(DistributedSZTreasureAI.DistributedSZTreasureAI):

    def __init__(self, air, treasurePlanner = None, x = 0, y = 0, z = 0):
        DistributedSZTreasureAI.DistributedSZTreasureAI.__init__(self, air, treasurePlanner, x, y, z)
