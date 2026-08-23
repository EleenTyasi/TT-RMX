# =============================================================================
#  DistributedSOSCompanion.py  —  Client-side representation of SOS Companion
#  TT-RMX Personal Tinkering Project
# =============================================================================

from toontown.toon.DistributedNPCToonBase import DistributedNPCToonBase

class DistributedSOSCompanion(DistributedNPCToonBase):
    def __init__(self, cr):
        DistributedNPCToonBase.__init__(self, cr)
