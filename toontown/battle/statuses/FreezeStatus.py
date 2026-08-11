# =============================================================================
#  FreezeStatus.py  —  Freeze Status Effect (Turn Skip / Immobilized)
# =============================================================================

from .StatusBase import StatusBase

class FreezeStatus(StatusBase):
    name = "FREEZE"

    def is_frozen(self):
        return True
