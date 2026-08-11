# =============================================================================
#  BurnStatus.py  —  Burn Status Effect (Amplifies incoming damage by 1.25x)
# =============================================================================

from .StatusBase import StatusBase

class BurnStatus(StatusBase):
    name = "BURN"

    def get_damage_multiplier(self):
        return self.data.get('damage_multiplier', 1.25)
