# =============================================================================
#  StatusEffectManager.py  —  Runtime Status Effects Engine
#  TT-RMX Personal Tinkering Project
# =============================================================================

from direct.directnotify import DirectNotifyGlobal
from toontown.battle.statuses import create_status_instance
from toontown.battle.StatusEffectsConfig import (
    GAG_TRACK_STATUS_EFFECTS,
    SUIT_ATTACK_STATUS_EFFECTS,
    TOON_BUFFS,
)

class StatusEffectManager:
    notify = DirectNotifyGlobal.directNotify.newCategory('StatusEffectManager')

    def __init__(self):
        # Maps avatar_id -> dict of {effect_name: StatusBase instance}
        self.effects = {}

    @staticmethod
    def calc_proc_chance(base_chance, gag_level=0, hit_type='NORMAL'):
        """
        Calculates dynamic status application chance:
        - +5% per Gag level
        - +25% on Critical or Direct Hit
        - 100% (Guaranteed) on Critical Direct Hit
        """
        if hit_type == 'CRIT_DIRECT_HIT':
            return 100
        
        chance = base_chance + (gag_level * 5)
        if hit_type in ('CRITICAL', 'DIRECT_HIT'):
            chance += 25
            
        return min(100, chance)

    def apply_effect(self, avatar_id, effect_name, rounds, data=None):
        if avatar_id not in self.effects:
            self.effects[avatar_id] = {}
        
        inst = create_status_instance(effect_name, avatar_id, rounds, data)
        inst.on_apply(self)
        self.effects[avatar_id][effect_name] = {'rounds': rounds, 'data': data or {}, 'inst': inst}
        self.notify.info(f"Applied status effect '{effect_name}' to avatar {avatar_id} for {rounds} rounds.")

    def remove_effect(self, avatar_id, effect_name):
        if avatar_id in self.effects and effect_name in self.effects[avatar_id]:
            entry = self.effects[avatar_id][effect_name]
            if 'inst' in entry:
                entry['inst'].on_remove(self)
            del self.effects[avatar_id][effect_name]
            self.notify.info(f"Removed status effect '{effect_name}' from avatar {avatar_id}.")

    def clear_avatar(self, avatar_id):
        if avatar_id in self.effects:
            for eff_name in list(self.effects[avatar_id].keys()):
                self.remove_effect(avatar_id, eff_name)
            del self.effects[avatar_id]

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
        if avatar_id in self.effects:
            for entry in self.effects[avatar_id].values():
                if 'inst' in entry:
                    mod += entry['inst'].get_accuracy_mod()
        return mod

    def get_defense_mod(self, avatar_id):
        mod = 0
        if avatar_id in self.effects:
            for entry in self.effects[avatar_id].values():
                if 'inst' in entry:
                    mod += entry['inst'].get_defense_mod()
        return mod

    def get_damage_multiplier(self, avatar_id):
        mult = 1.0
        if avatar_id in self.effects:
            for entry in self.effects[avatar_id].values():
                if 'inst' in entry:
                    mult *= entry['inst'].get_damage_multiplier()
        return mult

    def is_frozen(self, avatar_id):
        if avatar_id in self.effects:
            for effect_name, entry in self.effects[avatar_id].items():
                if effect_name == 'FREEZE':
                    return True
                if 'inst' in entry and hasattr(entry['inst'], 'is_frozen') and entry['inst'].is_frozen():
                    return True
        return False

    def is_wet(self, avatar_id):
        if avatar_id in self.effects:
            for effect_name, entry in self.effects[avatar_id].items():
                if effect_name == 'WET':
                    return True
                if 'inst' in entry and hasattr(entry['inst'], 'is_wet') and entry['inst'].is_wet():
                    return True
        return False

    def is_burned(self, avatar_id):
        return self.has_effect(avatar_id, 'BURN')

    def is_poisoned(self, avatar_id):
        return self.has_effect(avatar_id, 'POISON')

    def is_weakened(self, avatar_id):
        return self.has_effect(avatar_id, 'WEAKEN')

    def is_slowed(self, avatar_id):
        return self.has_effect(avatar_id, 'SLOW')

    def is_shielded(self, avatar_id):
        return self.has_effect(avatar_id, 'SHIELD')

    def tick_round(self):
        """
        Ticks down all active status durations by 1 round.
        Returns a dictionary of {avatar_id: (poison_damage, hit_type)} for any active POISON ticks.
        """
        poison_ticks = {}
        expired = []

        for avatar_id, avatar_effects in list(self.effects.items()):
            for effect_name, info in list(avatar_effects.items()):
                if 'inst' in info:
                    dmg = info['inst'].on_turn_end(self)
                    if dmg:
                        from toontown.battle.CritGlobals import roll_hit_type
                        is_toon_target = (avatar_id >= 100000000)
                        hit_type, crit_mult = roll_hit_type(is_toon=not is_toon_target)
                        final_dmg = int(dmg * crit_mult)
                        poison_ticks[avatar_id] = (final_dmg, hit_type)

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
