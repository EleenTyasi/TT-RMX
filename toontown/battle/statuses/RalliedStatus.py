# =============================================================================
#  RalliedStatus.py  —  Rallied Buff (+20% damage boost on next Gag)
# =============================================================================

from .StatusBase import StatusBase

class RalliedStatus(StatusBase):
    name = "RALLIED"

    def get_damage_multiplier(self):
        return 1.20
