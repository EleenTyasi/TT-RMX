# =============================================================================
#  StatusEffectManager.py  —  Runtime Status Effects Engine
#  TT-RMX Personal Tinkering Project
# =============================================================================

from direct.directnotify import DirectNotifyGlobal
from toontown.battle.StatusEffectsConfig import (
    GAG_TRACK_STATUS_EFFECTS,
    SUIT_ATTACK_STATUS_EFFECTS,
    TOON_BUFFS,
)

class StatusEffectManager:
    notify = DirectNotifyGlobal.directNotify.newCategory('StatusEffectManager')

    def __init__(self):
        # Maps avatar_id -> dict of {effect_name: {'rounds': N, 'data': dict}}
        self.effects = {}

    def apply_effect(self, avatar_id, effect_name, rounds, data=None):
        if avatar_id not in self.effects:
            self.effects[avatar_id] = {}
        
        entry = {'rounds': rounds, 'data': data or {}}
        self.effects[avatar_id][effect_name] = entry
        self.notify.info(f"Applied status effect '{effect_name}' to avatar {avatar_id} for {rounds} rounds.")

    def remove_effect(self, avatar_id, effect_name):
        if avatar_id in self.effects and effect_name in self.effects[avatar_id]:
            del self.effects[avatar_id][effect_name]
            self.notify.info(f"Removed status effect '{effect_name}' from avatar {avatar_id}.")

    def has_effect(self, avatar_id, effect_name):
        return avatar_id in self.effects and effect_name in self.effects[avatar_id]

    def get_effect(self, avatar_id, effect_name):
        if self.has_effect(avatar_id, effect_name):
            return self.effects[avatar_id][effect_name]
        return None

    def get_active_effects(self, avatar_id):
        if avatar_id in self.effects:
            return list(self.effects[avatar_id].keys())
        return []

    def get_accuracy_mod(self, avatar_id):
        mod = 0
        if self.has_effect(avatar_id, 'SLOW'):
            eff = self.get_effect(avatar_id, 'SLOW')
            mod -= eff['data'].get('accuracy_reduction', 15)
        if self.has_effect(avatar_id, 'LUCKY'):
            eff = self.get_effect(avatar_id, 'LUCKY')
            mod += eff['data'].get('accuracy_boost', 15)
        return mod

    def get_defense_mod(self, avatar_id):
        mod = 0
        if self.has_effect(avatar_id, 'WEAKEN'):
            eff = self.get_effect(avatar_id, 'WEAKEN')
            mod -= eff['data'].get('defense_reduction', 10)
        return mod

    def get_damage_multiplier(self, avatar_id):
        mult = 1.0
        if self.has_effect(avatar_id, 'BURN'):
            eff = self.get_effect(avatar_id, 'BURN')
            mult *= eff['data'].get('damage_multiplier', 1.25)
        if self.has_effect(avatar_id, 'SHIELD'):
            eff = self.get_effect(avatar_id, 'SHIELD')
            reduction = eff['data'].get('damage_reduction', 0.30)
            mult *= (1.0 - reduction)
        return mult

    def is_frozen(self, avatar_id):
        return self.has_effect(avatar_id, 'FREEZE')

    def tick_round(self):
        """
        Ticks down all active status durations by 1 round.
        Returns a dictionary of {avatar_id: poison_damage} for any active POISON ticks.
        """
        poison_ticks = {}
        expired = []

        for avatar_id, avatar_effects in list(self.effects.items()):
            for effect_name, info in list(avatar_effects.items()):
                # Handle periodic ticks (e.g. POISON)
                if effect_name == 'POISON':
                    dmg = info['data'].get('damage_per_round', 8)
                    poison_ticks[avatar_id] = poison_ticks.get(avatar_id, 0) + dmg

                # Decrement turn duration
                info['rounds'] -= 1
                if info['rounds'] <= 0:
                    expired.append((avatar_id, effect_name))

        for avatar_id, effect_name in expired:
            self.remove_effect(avatar_id, effect_name)

        return poison_ticks

    def clear_avatar(self, avatar_id):
        if avatar_id in self.effects:
            del self.effects[avatar_id]

    def clear_all(self):
        self.effects.clear()
