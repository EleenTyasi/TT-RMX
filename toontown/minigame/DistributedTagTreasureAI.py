from toontown.safezone import DistributedTreasureAI
from direct.distributed.ClockDelta import *

class DistributedTagTreasureAI(DistributedTreasureAI.DistributedTreasureAI):

    def __init__(self, air, treasurePlanner = None, x = 0, y = 0, z = 0):
        DistributedTreasureAI.DistributedTreasureAI.__init__(self, air, treasurePlanner, x, y, z)
