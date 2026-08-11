# =============================================================================
#  WeakenStatus.py  —  Weaken Status Effect (-10% defense reduction)
# =============================================================================

from .StatusBase import StatusBase

class WeakenStatus(StatusBase):
    name = "WEAKEN"

    def get_defense_mod(self):
        return -self.data.get('defense_reduction', 10)
