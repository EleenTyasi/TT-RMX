# =============================================================================
#  StatusBase.py  —  Base Class for Status Effects & Buffs
#  TT-RMX Personal Tinkering Project
# =============================================================================

class StatusBase:
    name = "STATUS"

    def __init__(self, avatar_id, rounds, data=None):
        self.avatar_id = avatar_id
        self.rounds = rounds
        self.data = data or {}

    def on_apply(self, manager):
        pass

    def on_turn_start(self, manager):
        pass

    def on_turn_end(self, manager):
        pass

    def get_accuracy_mod(self):
        return 0

    def get_defense_mod(self):
        return 0

    def get_damage_multiplier(self):
        return 1.0

    def is_frozen(self):
        return False

    def on_remove(self, manager):
        pass
