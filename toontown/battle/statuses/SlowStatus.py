# =============================================================================
#  SlowStatus.py  —  Slow Status Effect (-15% accuracy reduction)
# =============================================================================

from .StatusBase import StatusBase

class SlowStatus(StatusBase):
    name = "SLOW"

    def get_defense_mod(self):
        return -self.data.get('defense_reduction', 30)
