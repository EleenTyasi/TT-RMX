# =============================================================================
#  LuckyStatus.py  —  Lucky Buff (+15% Gag accuracy boost)
# =============================================================================

from .StatusBase import StatusBase

class LuckyStatus(StatusBase):
    name = "LUCKY"

    def get_accuracy_mod(self):
        return self.data.get('accuracy_boost', 15)
