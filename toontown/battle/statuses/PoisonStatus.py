# =============================================================================
#  PoisonStatus.py  —  Poison Status Effect (Damage Over Time)
# =============================================================================

from .StatusBase import StatusBase

class PoisonStatus(StatusBase):
    name = "POISON"

    def on_turn_end(self, manager):
        return self.data.get('damage_per_round', 8)
