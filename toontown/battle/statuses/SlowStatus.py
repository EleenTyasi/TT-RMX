# =============================================================================
#  SlowStatus.py  —  Slow Status Effect (-15% accuracy reduction)
# =============================================================================

from .StatusBase import StatusBase

class SlowStatus(StatusBase):
    name = "SLOW"

    def get_accuracy_mod(self):
        return -self.data.get('accuracy_reduction', 15)
