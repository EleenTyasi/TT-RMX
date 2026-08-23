# =============================================================================
#  DistributedSOSCompanion.py  —  Client-side representation of SOS Companion
#  TT-RMX Personal Tinkering Project
# =============================================================================

from toontown.toon.DistributedToon import DistributedToon

class DistributedSOSCompanion(DistributedToon):
    def __init__(self, cr):
        DistributedToon.__init__(self, cr)
