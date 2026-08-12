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
    # 5 (Squirt) → Slows Cogs (reduces Cog accuracy)
    5: {
        'effect': 'SLOW',
        'chance': 100,        # Proc chance % (0 to 100)
        'rounds': 3,          # Duration in turns
        'accuracy_reduction': 15, # Cog loses 15% accuracy
    },

    # 6 (Drop) → Freezes Cogs (Cog skips turn)
    6: {
        'effect': 'FREEZE',
        'chance': 50,
        'rounds': 1,
    },

    # 3 (Sound) → Weakens Cogs (reduces Cog defense)
    3: {
        'effect': 'WEAKEN',
        'chance': 75,
        'rounds': 2,
        'defense_reduction': 10, # Cog defense reduced by 10%
    },



    # 4 (Throw) → Burns Cogs (amplifies incoming damage)
    4: {
        'effect': 'BURN',
        'chance': 60,
        'rounds': 2,
        'damage_multiplier': 1.25, # Takes 25% extra damage
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
        'effect': 'SLOW',
        'rounds': 2,
        'accuracy_reduction': 10,
        'chance': 80,
    },
    'Demotion': {
        'effect': 'WEAKEN',
        'rounds': 2,
        'defense_reduction': 10,
        'chance': 75,
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
