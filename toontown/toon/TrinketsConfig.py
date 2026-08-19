# =============================================================================
#  TrinketsConfig.py — Single-Player Trinket System Catalog
#  TT-RMX Personal Tinkering Project
# =============================================================================

TRINKET_NONE = 0

# Organic-izers (1-7)
TRINKET_ORGANIC_THROW = 1
TRINKET_ORGANIC_SQUIRT = 2
TRINKET_ORGANIC_SOUND = 3
TRINKET_ORGANIC_TOONUP = 4
TRINKET_ORGANIC_LURE = 5
TRINKET_ORGANIC_TRAP = 6
TRINKET_ORGANIC_DROP = 7

# Core Stat & Ability Modifiers (8-13)
TRINKET_CRIT_UP_LAFF_DOWN = 8
TRINKET_DEF_UP_ATK_DOWN = 9
TRINKET_DARING_DANGER = 10
TRINKET_RALLYING_TU = 11
TRINKET_CLEANSING_TU = 12
TRINKET_SHATTERING_FREEZING = 13

# Niche & Build-Enabling Trinkets (14-20)
TRINKET_VAMPIRIC_GAGS = 14
TRINKET_THORNS = 15
TRINKET_GLASS_CANNON = 16
TRINKET_STATUS_CATALYST = 17
TRINKET_SECOND_WIND = 18
TRINKET_LUCKY_CHARM = 19
TRINKET_PATIENT_LURING = 20
TRINKET_ORGANIC_ALL = 21
TRINKET_LURED_DROP = 22
TRINKET_LOUDER_SOUND = 23
TRINKET_GENTLE_WATER = 24
TRINKET_SPEEDING_TOON = 25

TRINKET_CATALOG = {
    TRINKET_ORGANIC_THROW: {
        'id': TRINKET_ORGANIC_THROW,
        'name': 'Organic Thrower',
        'desc': 'Grants Organic damage bonus (+10%) to the Throw Gag track.',
        'track': 4,
    },
    TRINKET_ORGANIC_SQUIRT: {
        'id': TRINKET_ORGANIC_SQUIRT,
        'name': 'Organic Squirter',
        'desc': 'Grants Organic damage bonus (+10%) to the Squirt Gag track.',
        'track': 5,
    },
    TRINKET_ORGANIC_SOUND: {
        'id': TRINKET_ORGANIC_SOUND,
        'name': 'Organic Sounder',
        'desc': 'Grants Organic damage bonus (+10%) to the Sound Gag track.',
        'track': 2,
    },
    TRINKET_ORGANIC_TOONUP: {
        'id': TRINKET_ORGANIC_TOONUP,
        'name': 'Organic Healer',
        'desc': 'Grants Organic healing bonus (+10%) to the Toon-Up Gag track.',
        'track': 0,
    },
    TRINKET_ORGANIC_LURE: {
        'id': TRINKET_ORGANIC_LURE,
        'name': 'Organic Lurer',
        'desc': 'Grants Organic accuracy bonus (+10%) to the Lure Gag track.',
        'track': 3,
    },
    TRINKET_ORGANIC_TRAP: {
        'id': TRINKET_ORGANIC_TRAP,
        'name': 'Organic Trapper',
        'desc': 'Grants Organic damage bonus (+10%) to the Trap Gag track.',
        'track': 1,
    },
    TRINKET_ORGANIC_DROP: {
        'id': TRINKET_ORGANIC_DROP,
        'name': 'Organic Dropper',
        'desc': 'Grants Organic damage bonus (+10%) to the Drop Gag track.',
        'track': 6,
    },
    TRINKET_CRIT_UP_LAFF_DOWN: {
        'id': TRINKET_CRIT_UP_LAFF_DOWN,
        'name': 'Critical Focus',
        'desc': 'Reduces Max Laff by 10%, but increases Critical and Direct Hit chance by +2.5%.',
    },
    TRINKET_DEF_UP_ATK_DOWN: {
        'id': TRINKET_DEF_UP_ATK_DOWN,
        'name': 'Guardian Bulwark',
        'desc': 'Lowers Gag damage by 15%, but increases dodge chance against Cog attacks by +15%.',
    },
    TRINKET_DARING_DANGER: {
        'id': TRINKET_DARING_DANGER,
        'name': 'Daring Danger',
        'desc': 'When your Laff is at 30% or less, your Gags deal +30% additional damage.',
    },
    TRINKET_RALLYING_TU: {
        'id': TRINKET_RALLYING_TU,
        'name': 'Rallying Compassion',
        'desc': 'Using Toon-Up grants the RALLIED status (bonus accuracy & defense) to targets.',
    },
    TRINKET_CLEANSING_TU: {
        'id': TRINKET_CLEANSING_TU,
        'name': 'Purifying Grace',
        'desc': 'Using Toon-Up cleanses all negative status effects (Poison, Burn, Weaken, Slow) from targets.',
    },
    TRINKET_SHATTERING_FREEZING: {
        'id': TRINKET_SHATTERING_FREEZING,
        'name': 'Shattering Frost',
        'desc': 'When a Frozen Cog is defeated, it shatters in an ice explosion, dealing 50% damage to adjacent Cogs.',
    },
    TRINKET_VAMPIRIC_GAGS: {
        'id': TRINKET_VAMPIRIC_GAGS,
        'name': 'Vampiric Gags',
        'desc': 'Heals your Toon for 10% of all Gag damage dealt in combat.',
    },
    TRINKET_THORNS: {
        'id': TRINKET_THORNS,
        'name': 'Retaliation Spike',
        'desc': 'When hit by a Cog attack, reflects 20% of the damage taken back to the attacking Cog.',
    },
    TRINKET_GLASS_CANNON: {
        'id': TRINKET_GLASS_CANNON,
        'name': 'Glass Cannon',
        'desc': 'Increases Gag damage dealt by +25%, but increases damage taken from Cogs by +25%.',
    },
    TRINKET_STATUS_CATALYST: {
        'id': TRINKET_STATUS_CATALYST,
        'name': 'Status Catalyst',
        'desc': 'All status effects applied by your Gags last +1 additional round.',
    },
    TRINKET_SECOND_WIND: {
        'id': TRINKET_SECOND_WIND,
        'name': 'Second Wind',
        'desc': 'Once per battle, surviving fatal damage leaves you at 1 Laff with a SHIELD barrier.',
    },
    TRINKET_LUCKY_CHARM: {
        'id': TRINKET_LUCKY_CHARM,
        'name': 'Lucky Charm',
        'desc': 'Grants LUCKY status (+5% Crit) at battle start & increases Jellybean rewards by +50%.',
    },
    TRINKET_PATIENT_LURING: {
        'id': TRINKET_PATIENT_LURING,
        'name': 'Patient Luring',
        'desc': 'Lured Cogs stay mesmerized for +1 additional turn.',
    },
    TRINKET_ORGANIC_ALL: {
        'id': TRINKET_ORGANIC_ALL,
        'name': 'Organic-ize',
        'desc': 'All Gag tracks are permanently Organic (+10% power / accuracy), but you take +50% more damage.',
    },
    TRINKET_LURED_DROP: {
        'id': TRINKET_LURED_DROP,
        'name': 'Lured Drop',
        'desc': 'Drop can target Lured Cogs. Drop can still miss, but missing will not unlure the Cog.',
    },
    TRINKET_LOUDER_SOUND: {
        'id': TRINKET_LOUDER_SOUND,
        'name': 'Louder Sound',
        'desc': 'Sound deals Lure Knockback bonus damage, but deals half damage to Lured Cogs.',
    },
    TRINKET_GENTLE_WATER: {
        'id': TRINKET_GENTLE_WATER,
        'name': 'Gentle Water',
        'desc': 'Squirt has a 30% chance to not unlure Cogs on hit.',
    },
    TRINKET_SPEEDING_TOON: {
        'id': TRINKET_SPEEDING_TOON,
        'name': 'Speeding Toon',
        'desc': 'Double sprint speed, but half Max Stamina. Deals & takes 4x Ram Damage when sprinting into Cogs.',
    },
}

ALL_TRINKET_IDS = list(TRINKET_CATALOG.keys())

def get_trinket_info(trinket_id):
    return TRINKET_CATALOG.get(trinket_id, None)
