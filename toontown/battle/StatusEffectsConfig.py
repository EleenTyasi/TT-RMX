# =============================================================================
#  StatusEffectsConfig.py  —  Status Effects & Buffs Configuration
#  TT-RMX Personal Tinkering Project
# =============================================================================
#
#  This file configures status effects applied by Toon Gags and Suit Attacks.
#
#  INFUSING STATUS EFFECTS INTO GAG TRACKS
#  ───────────────────────────────────────
#  You can attach a status effect to an existing Gag track below.
#  When a Gag in that track hits, it has a 'chance' % of applying the effect!
#
#  Track Numbers:
#    0 = Heal (Toon-Up)
#    1 = Trap
#    2 = Lure
#    3 = Sound
#    4 = Throw
#    5 = Squirt
#    6 = Drop
#
# =============================================================================

# Track status mappings for Toon Gags:
GAG_TRACK_STATUS_EFFECTS = {
    # 5 (Squirt) → Drenches Cogs with WET (reduces Cog defense by 30% and increases Freeze proc chance)
    5: {
        'effect': 'WET',
        'chance': 100,        # Proc chance % (0 to 100)
        'rounds': 3,          # Duration in turns
        'defense_reduction': 30, # Cog loses 30% dodge defense
    },

    # 6 (Drop) → Freezes Cogs (Cog skips turn)
    6: {
        'effect': 'FREEZE',
        'chance': 50,
        'rounds': 1,
    },

    # 3 (Sound) → Weakens Cogs (reduces Cog attack power)
    3: {
        'effect': 'WEAKEN',
        'chance': 75,
        'rounds': 2,
        'defense_reduction': 10,
    },

    # 4 (Throw) → Burns Cogs (amplifies incoming damage by 1.5x)
    4: {
        'effect': 'BURN',
        'chance': 60,
        'rounds': 2,
        'damage_multiplier': 1.5,
    },
}

# Suit Attacks can also inflict statuses on Toons!
SUIT_ATTACK_STATUS_EFFECTS = {
    'FreezeAssets': {
        'effect': 'FREEZE',
        'rounds': 1,
        'chance': 100,
    },
    'RedTape': {
        'effect': 'WET',
        'rounds': 2,
        'defense_reduction': 10,
        'chance': 80,
    },
    'Demotion': {
        'effect': 'WEAKEN',
        'rounds': 2,
        'defense_reduction': 10,
        'chance': 75,
    },
}

# Cog Buff and Self-Heal Attacks!
# When a Cog uses one of these attacks, they trigger a heal or defensive/offensive buff on themselves (or group).
# If 'is_pure_heal' is True, it deals 0 damage to Toons and purely restores Cog HP!
SUIT_BUFF_ATTACKS = {
    'Watercooler': {
        'heal_percent': 0.25,     # Restores 25% Max HP (group or self)
        'is_pure_heal': True,     # Deals NO damage to Toons — strictly a repair/heal skill
        'chance': 100,
    },
    'ReOrg': {
        'heal_percent': 0.30,     # Restores 30% Max HP
        'is_pure_heal': True,     # Deals NO damage to Toons — pure restructuring heal
        'chance': 100,
    },
    'Synergy': {
        'heal_percent': 0.15,     # Restores 15% Max HP to self
        'effect': 'RALLIED',      # +20% damage boost
        'rounds': 2,
        'chance': 100,
    },
    'Schmooze': {
        'effect': 'SHIELD',       # +30% damage reduction
        'rounds': 2,
        'damage_reduction': 0.30,
        'chance': 100,
    },
    'ParadigmShift': {
        'heal_percent': 0.20,     # Restores 20% Max HP
        'effect': 'SHIELD',
        'rounds': 2,
        'damage_reduction': 0.25,
        'chance': 100,
    },
    'Rolodex': {
        'heal_percent': 0.20,     # Restores 20% Max HP
        'is_pure_heal': True,
        'chance': 100,
    },
    'Bailout': {
        'heal_percent': 0.25,     # Restores 25% Max HP
        'is_pure_heal': True,     # Pure heal/recovery skill
        'chance': 100,
    },
    'DividendPayout': {
        'heal_percent': 0.20,     # Restores 20% Max HP
        'is_pure_heal': False,
        'chance': 100,
    },
    'CapitalInjection': {
        'heal_percent': 0.30,     # Restores 30% Max HP
        'is_pure_heal': True,
        'chance': 100,
    },
}

# Toon Buff definitions (applied via Toon-Up or items)
TOON_BUFFS = {
    'SHIELD': {
        'rounds': 3,
        'damage_reduction': 0.30, # Absorbs 30% of incoming damage
    },
    'LUCKY': {
        'rounds': 3,
        'accuracy_boost': 15,    # +15% Gag accuracy boost
    },
    'RALLIED': {
        'rounds': 1,
        'damage_boost': 1.20,      # Next Gag does +20% damage
    },
}
