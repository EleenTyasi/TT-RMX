# =============================================================================
#  ShieldStatus.py  —  Shield Buff (Absorbs 30% incoming damage)
# =============================================================================

from .StatusBase import StatusBase

class ShieldStatus(StatusBase):
    name = "SHIELD"

    def get_damage_multiplier(self):
        reduction = self.data.get('damage_reduction', 0.30)
        return max(0.0, 1.0 - reduction)
