# =============================================================================
#  CritGlobals.py  —  FFXIV Style Critical & Direct Hit Combat System
#  TT-RMX Personal Tinkering Project
# =============================================================================

import random

# Multipliers
CRIT_MULT = 1.05          # Critical Hit: +5% damage
DIRECT_MULT = 1.15        # Direct Hit: +15% damage
CRIT_DIRECT_MULT = 1.25   # Critical Direct Hit: +25% damage

# Toon Proc Rates (Player Favored)
TOON_CRIT_CHANCE = 15     # 15% Crit Chance
TOON_DIRECT_CHANCE = 10   # 10% Direct Hit Chance
TOON_CRIT_DIRECT_CHANCE = 5 # 5% Crit Direct Hit Chance

# Cog Proc Rates (Rigged Lower for Player Protection)
COG_CRIT_CHANCE = 5       # 5% Crit Chance
COG_DIRECT_CHANCE = 3     # 3% Direct Hit Chance
COG_CRIT_DIRECT_CHANCE = 1 # 1% Crit Direct Hit Chance

# Hit Types
HIT_NORMAL = 0
HIT_CRITICAL = 1
HIT_DIRECT = 2
HIT_CRIT_DIRECT = 3
HIT_BLOCKED = 4
HIT_BLOCKED_FULL = 5

HIT_TYPE_NAMES = {
    HIT_NORMAL: "NORMAL",
    HIT_CRITICAL: "CRITICAL",
    HIT_DIRECT: "DIRECT_HIT",
    HIT_CRIT_DIRECT: "CRIT_DIRECT_HIT",
    HIT_BLOCKED: "BLOCKED",
    HIT_BLOCKED_FULL: "BLOCKED_FULL",
}

def roll_hit_type(is_toon=True, is_skelecog=False, toon=None):
    """
    Rolls for hit type:
    Returns (hit_type_code, multiplier)
    """
    crit_d_chance = TOON_CRIT_DIRECT_CHANCE if is_toon else COG_CRIT_DIRECT_CHANCE
    direct_chance = TOON_DIRECT_CHANCE if is_toon else COG_DIRECT_CHANCE
    crit_chance = TOON_CRIT_CHANCE if is_toon else (15 if is_skelecog else COG_CRIT_CHANCE)

    if is_toon and toon and hasattr(toon, 'hasTrinketEquipped'):
        from toontown.toon.TrinketsConfig import (
            TRINKET_CRIT_UP_LAFF_DOWN, TRINKET_LUCKY_CHARM, TRINKET_PANIC_BAND,
            TRINKET_PERIL_BAND, TRINKET_SMALL_MIGHTY
        )
        # Critical Focus (+2.5% crit & direct)
        if toon.hasTrinketEquipped(TRINKET_CRIT_UP_LAFF_DOWN):
            crit_chance += 2.5
            direct_chance += 2.5
        # Lucky Charm (+5% crit)
        if toon.hasTrinketEquipped(TRINKET_LUCKY_CHARM):
            crit_chance += 5.0
        # Panic Band: Double crit rate when at or below 50% max laff
        if toon.hasTrinketEquipped(TRINKET_PANIC_BAND):
            if (toon.hp / float(max(1, toon.maxHp))) <= 0.5:
                crit_chance *= 2
        # Peril Band: Double crit rate when at 1% max laff or at 1 Laff exactly
        if toon.hasTrinketEquipped(TRINKET_PERIL_BAND):
            is_one_laff = (toon.hp <= 1) or ((toon.hp / float(max(1, toon.maxHp))) <= 0.01)
            if is_one_laff:
                crit_chance *= 2
                direct_chance *= 2
        # Small But Mighty: Below 34 laff or Uber -> Crit Direct Hits much more easily (e.g. +20% Crit Direct)
        if toon.hasTrinketEquipped(TRINKET_SMALL_MIGHTY):
            is_uber = getattr(toon, 'isUber', lambda: False)() or (getattr(toon, 'laffCap', 0) > 0)
            if (toon.maxHp < 34) or is_uber:
                crit_d_chance += 20.0
                crit_chance += 10.0

    roll = random.random() * 100.0

    if roll <= crit_d_chance:
        return HIT_CRIT_DIRECT, CRIT_DIRECT_MULT
    elif roll <= crit_d_chance + direct_chance:
        return HIT_DIRECT, DIRECT_MULT
    elif roll <= crit_d_chance + direct_chance + crit_chance:
        return HIT_CRITICAL, CRIT_MULT
    else:
        return HIT_NORMAL, 1.0
