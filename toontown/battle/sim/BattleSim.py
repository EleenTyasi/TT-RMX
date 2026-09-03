# =============================================================================
#  BattleSim.py  —  Pure-Python Combat Calculation & Simulation Engine
#  TT-RMX Personal Tinkering Project
# =============================================================================
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import random
import math

from toontown.toonbase.ToontownBattleGlobals import (
    HEAL_TRACK, TRAP_TRACK, LURE_TRACK, SOUND_TRACK, THROW_TRACK, SQUIRT_TRACK, DROP_TRACK,
    AvPropDamage, AvPropAccuracy, AvPropStrings,
    Tracks, Levels
)
from toontown.battle import CritGlobals
from toontown.battle.StatusEffectsConfig import GAG_TRACK_STATUS_EFFECTS, SUIT_BUFF_ATTACKS, TOON_BUFFS

# Track names for easy reference
TRACK_NAMES = {
    HEAL_TRACK: 'Heal',
    TRAP_TRACK: 'Trap',
    LURE_TRACK: 'Lure',
    SOUND_TRACK: 'Sound',
    THROW_TRACK: 'Throw',
    SQUIRT_TRACK: 'Squirt',
    DROP_TRACK: 'Drop',
}

@dataclass
class ToonSnapshot:
    id: int
    name: str = "Toon"
    hp: int = 100
    max_hp: int = 100
    track_levels: List[int] = field(default_factory=lambda: [7, 7, 7, 7, 7, 7, 7])
    guard_active: bool = False
    active_buffs: Dict[str, int] = field(default_factory=dict)
    equipped_trinkets: List[str] = field(default_factory=list)

    def hasTrinketEquipped(self, trinket_id: str) -> bool:
        return trinket_id in self.equipped_trinkets


@dataclass
class SuitSnapshot:
    id: int
    name: str = "Cog"
    code: str = "f"
    level: int = 1
    hp: int = 6
    max_hp: int = 6
    defense: int = 0
    is_lured: bool = False
    status_effects: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    active_buffs: Dict[str, int] = field(default_factory=dict)

    def has_status(self, effect_name: str) -> bool:
        return effect_name.upper() in [k.upper() for k in self.status_effects.keys()]


@dataclass
class ForecastData:
    track: int
    level: int
    gag_name: str
    target_id: int
    target_name: str
    target_hp: int
    target_max_hp: int
    base_damage: int
    knockback_bonus: int = 0
    combo_bonus: int = 0
    total_expected_damage: int = 0
    min_damage: int = 0
    max_damage: int = 0
    hit_chance_pct: float = 95.0
    crit_chance_pct: float = 15.0
    direct_chance_pct: float = 10.0
    crit_direct_chance_pct: float = 5.0
    status_effect_name: Optional[str] = None
    status_effect_chance: float = 0.0
    is_lethal: bool = False
    is_pure_heal: bool = False

    def summary(self) -> str:
        dmg_str = f"{self.total_expected_damage}"
        if self.knockback_bonus:
            dmg_str += f" (+{self.knockback_bonus} KB)"
        if self.combo_bonus:
            dmg_str += f" (+{self.combo_bonus} Combo)"
        lethal_tag = " [LETHAL]" if self.is_lethal else ""
        return (f"{self.gag_name} -> {self.target_name} (HP: {self.target_hp}/{self.target_max_hp}): "
                f"DMG {dmg_str} | HIT {self.hit_chance_pct:.1f}% | CRIT {self.crit_chance_pct:.1f}%{lethal_tag}")


class BattleSim:
    """
    Pure-Python deterministic battle calculation and prediction engine.
    """

    @classmethod
    def get_base_gag_damage(cls, track: int, level: int, exp: int = 0, organic_bonus: bool = False, prop_bonus: bool = False) -> int:
        try:
            from toontown.toonbase.ToontownBattleGlobals import getAvPropDamage
            return int(getAvPropDamage(track, level, exp, organic_bonus, prop_bonus))
        except Exception:
            try:
                val = AvPropDamage[track][level]
                if isinstance(val, (tuple, list)):
                    if isinstance(val[0], (tuple, list)):
                        return int(val[0][0])
                    return int(val[0])
                return int(val)
            except Exception:
                return 10

    @classmethod
    def get_base_gag_accuracy(cls, track: int, level: int) -> int:
        try:
            return int(AvPropAccuracy[track][level])
        except Exception:
            return 75

    @classmethod
    def get_gag_name(cls, track: int, level: int) -> str:
        try:
            return AvPropStrings[track][level]
        except Exception:
            return f"{TRACK_NAMES.get(track, 'Gag')} Lv.{level+1}"

    @classmethod
    def calc_hit_chance(cls, track: int, level: int, suit: SuitSnapshot,
                        prop_bonus: bool = False, organic_bonus: bool = False,
                        lured: bool = False) -> float:
        """
        Computes accurate Toontown / TT-RMX hit chance formula:
        Accuracy = TrackAcc + TrackLvlBonus + LureBonus - CogDefense + StatusBonus
        """
        if track in (HEAL_TRACK, LURE_TRACK):
            base_acc = cls.get_base_gag_accuracy(track, level)
            return min(100.0, max(5.0, float(base_acc)))

        if lured and track in (THROW_TRACK, SQUIRT_TRACK):
            # Attacks on lured cogs have 100% accuracy
            return 100.0

        base_acc = cls.get_base_gag_accuracy(track, level)
        track_bonus = level * 10
        cog_def = suit.defense

        # TT-RMX Status Effects on Cog Defense / Hit Chance:
        if suit.has_status('SLOW'):
            cog_def = max(0, cog_def - 30)
        if suit.has_status('WET'):
            cog_def = max(0, cog_def - 30)
        if suit.has_status('WEAKEN'):
            cog_def = max(0, cog_def - 10)

        acc = base_acc + track_bonus - cog_def
        if prop_bonus:
            acc += 10
        if organic_bonus:
            acc += 10

        return min(95.0, max(5.0, float(acc)))

    @classmethod
    def calc_status_proc_chance(cls, track: int, level: int, hit_type: str = 'NORMAL') -> Tuple[Optional[str], float]:
        """
        Determines the status effect name and proc chance for a given Gag.
        """
        cfg = GAG_TRACK_STATUS_EFFECTS.get(track)
        if not cfg:
            return None, 0.0

        effect_name = cfg.get('effect')
        base_chance = cfg.get('chance', 60)

        if hit_type == 'CRIT_DIRECT_HIT':
            return effect_name, 100.0

        chance = base_chance + (level * 5)
        if hit_type in ('CRITICAL', 'DIRECT_HIT'):
            chance += 25.0

        return effect_name, min(100.0, float(chance))

    @classmethod
    def forecast(cls,
                 gag_track: int,
                 gag_level: int,
                 target_suit: SuitSnapshot,
                 toon: Optional[ToonSnapshot] = None,
                 lured_override: Optional[bool] = None,
                 num_same_track_attacks: int = 1) -> ForecastData:
        """
        Generates an instant mathematical prediction for selecting a Gag against a Cog.
        """
        base_dmg = cls.get_base_gag_damage(gag_track, gag_level)
        gag_name = cls.get_gag_name(gag_track, gag_level)

        is_lured = target_suit.is_lured if lured_override is None else lured_override

        # Knockback bonus (+50% for Throw and Squirt on lured cogs)
        kb_bonus = 0
        if is_lured and gag_track in (THROW_TRACK, SQUIRT_TRACK):
            kb_bonus = int(math.ceil(base_dmg * 0.5))

        # Combo bonus (+20% if 2 or more Toons use the same track on this Cog)
        combo_bonus = 0
        if num_same_track_attacks >= 2 and gag_track in (SOUND_TRACK, THROW_TRACK, SQUIRT_TRACK, DROP_TRACK):
            combo_bonus = int(math.ceil(base_dmg * 0.2))

        # Burn Status effect bonus (+50% incoming damage)
        burn_multiplier = 1.5 if target_suit.has_status('BURN') else 1.0

        raw_dmg = (base_dmg + kb_bonus + combo_bonus) * burn_multiplier
        total_dmg = int(math.floor(raw_dmg))

        # Min and Max variance considering Crits
        min_dmg = total_dmg
        max_dmg = int(math.floor(total_dmg * CritGlobals.CRIT_DIRECT_MULT))

        # Hit chance
        hit_chance = cls.calc_hit_chance(gag_track, gag_level, target_suit, lured=is_lured)

        # Crit odds
        crit_chance = CritGlobals.TOON_CRIT_CHANCE
        direct_chance = CritGlobals.TOON_DIRECT_CHANCE
        crit_direct_chance = CritGlobals.TOON_CRIT_DIRECT_CHANCE

        if toon and hasattr(toon, 'hasTrinketEquipped'):
            if toon.hasTrinketEquipped('TRINKET_LUCKY_CHARM'):
                crit_chance += 5.0
            if toon.hasTrinketEquipped('TRINKET_CRIT_UP_LAFF_DOWN'):
                crit_chance += 2.5
                direct_chance += 2.5

        # Status effect prediction
        effect_name, status_chance = cls.calc_status_proc_chance(gag_track, gag_level, hit_type='NORMAL')

        # Lethal kill check
        is_lethal = total_dmg >= target_suit.hp and target_suit.hp > 0

        return ForecastData(
            track=gag_track,
            level=gag_level,
            gag_name=gag_name,
            target_id=target_suit.id,
            target_name=target_suit.name,
            target_hp=target_suit.hp,
            target_max_hp=target_suit.max_hp,
            base_damage=base_dmg,
            knockback_bonus=kb_bonus,
            combo_bonus=combo_bonus,
            total_expected_damage=total_dmg,
            min_damage=min_dmg,
            max_damage=max_dmg,
            hit_chance_pct=hit_chance,
            crit_chance_pct=crit_chance,
            direct_chance_pct=direct_chance,
            crit_direct_chance_pct=crit_direct_chance,
            status_effect_name=effect_name,
            status_effect_chance=status_chance,
            is_lethal=is_lethal,
            is_pure_heal=(gag_track == HEAL_TRACK)
        )

    @classmethod
    def calculate_cog_damage_against_toon(cls,
                                          raw_damage: int,
                                          toon: ToonSnapshot,
                                          cog_crit_type: int = CritGlobals.HIT_NORMAL) -> int:
        """
        Calculates incoming Cog damage against a Toon factoring in Active Guard and Shields.
        """
        dmg = float(raw_damage)

        # Crit multiplier for Cog
        if cog_crit_type == CritGlobals.HIT_CRITICAL:
            dmg *= CritGlobals.CRIT_MULT
        elif cog_crit_type == CritGlobals.HIT_DIRECT:
            dmg *= CritGlobals.DIRECT_MULT
        elif cog_crit_type == CritGlobals.HIT_CRIT_DIRECT:
            dmg *= CritGlobals.CRIT_DIRECT_MULT

        # Active Guard (Pass) cuts damage by 50%
        if toon.guard_active:
            dmg *= 0.50

        # Toon SHIELD buff cuts damage by 30%
        if 'SHIELD' in toon.active_buffs:
            dmg *= 0.70

        return max(1, int(math.ceil(dmg)))

    @classmethod
    def choose_companion_action(cls, companion, battle) -> List[int]:
        """
        Calculates and selects the mathematically optimal combat move for an SOS Companion.
        Uses BattleSim combat calculation formulas to evaluate kill securing, Drop stun synergy,
        Lure knockback bonus, and emergency healing.
        """
        from toontown.battle.BattleBase import getToonAttack, TOON_TRACK_COL, TOON_TGT_COL, PASS, NO_ATTACK

        if not battle or not getattr(battle, 'activeSuits', None):
            return getToonAttack(companion.doId, track=PASS)

        active_cogs = battle.activeSuits
        living_cogs = [s for s in active_cogs if getattr(s, 'currHP', 1) > 0]
        if not living_cogs:
            return getToonAttack(companion.doId, track=PASS)

        preferred_tracks = getattr(companion, 'preferredTracks', [THROW_TRACK, SQUIRT_TRACK])
        companion_gags = getattr(companion, 'companionGags', {})

        def get_best_gag_level(track: int) -> Optional[int]:
            if track in companion_gags and companion_gags[track]:
                return max(companion_gags[track])
            if track in preferred_tracks:
                return 4
            return None

        # 1. EMERGENCY HEALING CHECK (Allies <= 45% HP)
        heal_level = get_best_gag_level(HEAL_TRACK)
        if heal_level is not None:
            lowest_toon = None
            lowest_hp_ratio = 1.0
            for t_id in getattr(battle, 'activeToons', []):
                t_obj = battle.getToon(t_id)
                if t_obj and t_obj.hp > 0:
                    ratio = t_obj.hp / float(max(1, t_obj.maxHp))
                    if ratio <= 0.45 and ratio < lowest_hp_ratio:
                        lowest_hp_ratio = ratio
                        lowest_toon = t_id

            if lowest_toon is not None:
                return getToonAttack(companion.doId, track=HEAL_TRACK, level=heal_level, target=lowest_toon)

        # Inspect summoner attack
        summoner_id = getattr(companion, 'summonerId', 0)
        summoner_atk = battle.toonAttacks.get(summoner_id) if hasattr(battle, 'toonAttacks') else None
        summoner_track = summoner_atk[TOON_TRACK_COL] if summoner_atk else NO_ATTACK
        summoner_target = summoner_atk[TOON_TGT_COL] if summoner_atk else -1

        # 2. DROP STUN ACCURACY SYNERGY:
        # If summoner used Drop, stun that same Cog using Squirt or Sound (+20% accuracy stun)
        if summoner_track == DROP_TRACK and summoner_target != -1:
            target_idx = summoner_target if summoner_target < len(active_cogs) else 0
            squirt_lvl = get_best_gag_level(SQUIRT_TRACK)
            sound_lvl = get_best_gag_level(SOUND_TRACK)
            if squirt_lvl is not None:
                return getToonAttack(companion.doId, track=SQUIRT_TRACK, level=squirt_lvl, target=target_idx)
            elif sound_lvl is not None:
                return getToonAttack(companion.doId, track=SOUND_TRACK, level=sound_lvl, target=-1)

        # 3. LURE SYNERGY:
        # If 2+ Cogs are unlured, deploy Lure
        lured_suits = getattr(battle, 'luredSuits', [])
        unlured_cogs = [s for s in living_cogs if s not in lured_suits]
        lure_lvl = get_best_gag_level(LURE_TRACK)
        if len(unlured_cogs) >= 2 and lure_lvl is not None:
            return getToonAttack(companion.doId, track=LURE_TRACK, level=lure_lvl, target=-1)

        # 4. LETHAL KILL SECURING & KNOCKBACK COMBO:
        best_attack = None
        highest_score = -1

        for idx, cog in enumerate(active_cogs):
            if getattr(cog, 'currHP', 0) <= 0:
                continue

            is_lured = cog in lured_suits
            cog_snapshot = SuitSnapshot(
                id=cog.doId,
                name=getattr(cog, 'worldBossName', None) or getattr(cog, 'name', 'Cog'),
                hp=cog.currHP,
                max_hp=cog.maxHP,
                defense=getattr(cog, 'getActualLevel', lambda: 1)(),
                is_lured=is_lured
            )

            for trk in (THROW_TRACK, SQUIRT_TRACK, SOUND_TRACK, DROP_TRACK):
                lvl = get_best_gag_level(trk)
                if lvl is None:
                    continue

                tgt = -1 if trk == SOUND_TRACK else idx
                fc = cls.forecast(trk, lvl, cog_snapshot, lured_override=is_lured)

                score = fc.total_expected_damage
                if fc.is_lethal:
                    score += 500
                if is_lured and trk in (THROW_TRACK, SQUIRT_TRACK):
                    score += 150
                if summoner_track == trk and trk in (SOUND_TRACK, THROW_TRACK, SQUIRT_TRACK):
                    score += 100

                if score > highest_score:
                    highest_score = score
                    best_attack = (trk, lvl, tgt)

        if best_attack:
            return getToonAttack(companion.doId, track=best_attack[0], level=best_attack[1], target=best_attack[2])

        # 5. FALLBACK: Preferred track
        primary_track = preferred_tracks[0] if preferred_tracks else THROW_TRACK
        fallback_lvl = get_best_gag_level(primary_track) or 3
        fallback_target = summoner_target if (summoner_target != -1 and summoner_target < len(active_cogs)) else 0
        if primary_track == SOUND_TRACK:
            fallback_target = -1

        return getToonAttack(companion.doId, track=primary_track, level=fallback_lvl, target=fallback_target)

