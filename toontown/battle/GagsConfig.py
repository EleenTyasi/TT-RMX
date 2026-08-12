# =============================================================================
#  GagsConfig.py  —  Gag Stats & Track Configuration
#  TT-RMX Personal Tinkering Project
# =============================================================================
#
#  This is the ONE file you edit to change anything about Gags (Toon attacks),
#  such as damage, accuracy, carry limits, and level thresholds.
#
#  TRACK INDEXES
#  ──────────────
#  0 = Heal    (Toon-Up)
#  1 = Trap
#  2 = Lure
#  3 = Sound
#  4 = Throw
#  5 = Squirt
#  6 = Drop
#
#  HOW DAMAGE WORKS (AvPropDamage)
#  ───────────────────────────────
#  For each track (0-6) and level (0-6):
#      ((min_damage, max_damage), (min_xp, max_xp))
#  As your Toon gains XP in that track (from min_xp to max_xp), the gag's
#  damage scales smoothly from min_damage to max_damage!
#
# =============================================================================

# No external globals needed

# Skill Level Thresholds required to unlock each Gag (Level 1 through Level 7)
GAG_LEVEL_XP = [
    [0, 20, 200, 800, 2000, 6000, 10000],  # Heal
    [0, 20, 100, 800, 2000, 6000, 10000],  # Trap
    [0, 20, 100, 800, 2000, 6000, 10000],  # Lure
    [0, 40, 200, 1000, 2500, 7500, 10000], # Sound
    [0, 10, 50, 400, 2000, 6000, 10000],   # Throw
    [0, 10, 50, 400, 2000, 6000, 10000],   # Squirt
    [0, 20, 100, 500, 2000, 6000, 10000],  # Drop
]

# Base accuracy for each Gag level (0 to 100)
GAG_ACCURACY = (
    (70, 70, 70, 70, 70, 70, 100), # Heal
    (0,  0,  0,  0,  0,  0,  0),   # Trap (Traps always hit if Cog is lured into them)
    (50, 50, 60, 60, 70, 70, 90),  # Lure
    (95, 95, 95, 95, 95, 95, 95),  # Sound
    (75, 75, 75, 75, 75, 75, 75),  # Throw
    (95, 95, 95, 95, 95, 95, 95),  # Squirt
    (50, 50, 50, 50, 50, 50, 50),  # Drop
)

# Damage Ranges per Gag Level: ((min_dmg, max_dmg), (min_xp, max_xp))
MAX_SKILL = 10500

GAG_DAMAGE = (
    # Heal (Toon-Up) — Heals HP instead of dealing damage
    (((8, 10), (GAG_LEVEL_XP[0][0], GAG_LEVEL_XP[0][1])),
     ((15, 18), (GAG_LEVEL_XP[0][1], GAG_LEVEL_XP[0][2])),
     ((25, 30), (GAG_LEVEL_XP[0][2], GAG_LEVEL_XP[0][3])),
     ((40, 45), (GAG_LEVEL_XP[0][3], GAG_LEVEL_XP[0][4])),
     ((60, 70), (GAG_LEVEL_XP[0][4], GAG_LEVEL_XP[0][5])),
     ((90, 120), (GAG_LEVEL_XP[0][5], GAG_LEVEL_XP[0][6])),
     ((210, 210), (GAG_LEVEL_XP[0][6], MAX_SKILL))),

    # Trap (Base damage divided by 8, rounded up)
    (((2, 2), (GAG_LEVEL_XP[1][0], GAG_LEVEL_XP[1][1])),
     ((3, 3), (GAG_LEVEL_XP[1][1], GAG_LEVEL_XP[1][2])),
     ((4, 5), (GAG_LEVEL_XP[1][2], GAG_LEVEL_XP[1][3])),
     ((6, 7), (GAG_LEVEL_XP[1][3], GAG_LEVEL_XP[1][4])),
     ((8, 9), (GAG_LEVEL_XP[1][4], GAG_LEVEL_XP[1][5])),
     ((12, 23), (GAG_LEVEL_XP[1][5], GAG_LEVEL_XP[1][6])),
     ((25, 25), (GAG_LEVEL_XP[1][6], MAX_SKILL))),

    # Lure (Rounds of stun/lure)
    (((0, 0), (0, 0)),
     ((0, 0), (0, 0)),
     ((0, 0), (0, 0)),
     ((0, 0), (0, 0)),
     ((0, 0), (0, 0)),
     ((0, 0), (0, 0)),
     ((0, 0), (0, 0))),

    # Sound
    (((3, 4), (GAG_LEVEL_XP[3][0], GAG_LEVEL_XP[3][1])),
     ((5, 7), (GAG_LEVEL_XP[3][1], GAG_LEVEL_XP[3][2])),
     ((9, 11), (GAG_LEVEL_XP[3][2], GAG_LEVEL_XP[3][3])),
     ((14, 16), (GAG_LEVEL_XP[3][3], GAG_LEVEL_XP[3][4])),
     ((19, 21), (GAG_LEVEL_XP[3][4], GAG_LEVEL_XP[3][5])),
     ((25, 50), (GAG_LEVEL_XP[3][5], GAG_LEVEL_XP[3][6])),
     ((90, 90), (GAG_LEVEL_XP[3][6], MAX_SKILL))),

    # Throw
    (((4, 6), (GAG_LEVEL_XP[4][0], GAG_LEVEL_XP[4][1])),
     ((8, 10), (GAG_LEVEL_XP[4][1], GAG_LEVEL_XP[4][2])),
     ((14, 17), (GAG_LEVEL_XP[4][2], GAG_LEVEL_XP[4][3])),
     ((24, 27), (GAG_LEVEL_XP[4][3], GAG_LEVEL_XP[4][4])),
     ((36, 40), (GAG_LEVEL_XP[4][4], GAG_LEVEL_XP[4][5])),
     ((48, 100), (GAG_LEVEL_XP[4][5], GAG_LEVEL_XP[4][6])),
     ((120, 120), (GAG_LEVEL_XP[4][6], MAX_SKILL))),

    # Squirt
    (((3, 4), (GAG_LEVEL_XP[5][0], GAG_LEVEL_XP[5][1])),
     ((6, 8), (GAG_LEVEL_XP[5][1], GAG_LEVEL_XP[5][2])),
     ((10, 12), (GAG_LEVEL_XP[5][2], GAG_LEVEL_XP[5][3])),
     ((18, 21), (GAG_LEVEL_XP[5][3], GAG_LEVEL_XP[5][4])),
     ((27, 30), (GAG_LEVEL_XP[5][4], GAG_LEVEL_XP[5][5])),
     ((36, 80), (GAG_LEVEL_XP[5][5], GAG_LEVEL_XP[5][6])),
     ((105, 105), (GAG_LEVEL_XP[5][6], MAX_SKILL))),

    # Drop
    (((10, 10), (GAG_LEVEL_XP[6][0], GAG_LEVEL_XP[6][1])),
     ((18, 18), (GAG_LEVEL_XP[6][1], GAG_LEVEL_XP[6][2])),
     ((30, 30), (GAG_LEVEL_XP[6][2], GAG_LEVEL_XP[6][3])),
     ((45, 45), (GAG_LEVEL_XP[6][3], GAG_LEVEL_XP[6][4])),
     ((60, 60), (GAG_LEVEL_XP[6][4], GAG_LEVEL_XP[6][5])),
     ((85, 170), (GAG_LEVEL_XP[6][5], GAG_LEVEL_XP[6][6])),
     ((180, 180), (GAG_LEVEL_XP[6][6], MAX_SKILL))),
)

# Target Types for each Gag (0 = Single Target, 1 = Group Target)
# Arranged by Gag Level (0 through 6)
ATK_SINGLE_TARGET = 0
ATK_GROUP_TARGET  = 1

GAG_TARGET_CATEGORY = (
    # Heal, Trap, Lure, Sound, Throw, Squirt, Drop
    (ATK_SINGLE_TARGET, ATK_GROUP_TARGET,  ATK_SINGLE_TARGET, ATK_GROUP_TARGET,  ATK_SINGLE_TARGET, ATK_GROUP_TARGET,  ATK_GROUP_TARGET),
    (ATK_SINGLE_TARGET, ATK_SINGLE_TARGET, ATK_SINGLE_TARGET, ATK_SINGLE_TARGET, ATK_SINGLE_TARGET, ATK_SINGLE_TARGET, ATK_SINGLE_TARGET),
    (ATK_GROUP_TARGET,  ATK_GROUP_TARGET,  ATK_GROUP_TARGET,  ATK_GROUP_TARGET,  ATK_GROUP_TARGET,  ATK_GROUP_TARGET,  ATK_GROUP_TARGET),
    (ATK_SINGLE_TARGET, ATK_SINGLE_TARGET, ATK_SINGLE_TARGET, ATK_SINGLE_TARGET, ATK_SINGLE_TARGET, ATK_SINGLE_TARGET, ATK_GROUP_TARGET),
)

GAG_TARGET_MAP = (0, 3, 0, 2, 3, 3, 3)

# Toon Up Settings (Solo Friendly!)
TOONUP_CAN_TARGET_SELF = True
