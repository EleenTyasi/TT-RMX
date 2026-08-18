# =============================================================================
#  WetStatus.py  —  Wet Status Effect (Squirt track)
# =============================================================================

from .StatusBase import StatusBase

class WetStatus(StatusBase):
    name = "WET"

    def get_defense_mod(self):
        return -self.data.get('defense_reduction', 30)

    def is_wet(self):
        return True
