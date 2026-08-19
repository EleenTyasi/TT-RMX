# ToonLevelGlobals.py — Toon Level EXP thresholds and track unlock milestones

MAX_TOON_LEVEL = 25

# Accumulated EXP required to reach each level (1-indexed, index 0 unused)
LEVEL_EXP_THRESHOLDS = [
    0,      # Index 0
    0,      # Level 1
    50,     # Level 2
    120,    # Level 3
    200,    # Level 4
    300,    # Level 5 (Track Choice 3)
    450,    # Level 6
    650,    # Level 7
    900,    # Level 8
    1200,   # Level 9
    1600,   # Level 10 (Track Choice 4)
    2100,   # Level 11
    2700,   # Level 12
    3400,   # Level 13
    4200,   # Level 14
    5100,   # Level 15 (Track Choice 5)
    6200,   # Level 16
    7400,   # Level 17
    8800,   # Level 18
    10400,  # Level 19
    12200,  # Level 20 (Track Choice 6)
    14300,  # Level 21
    16700,  # Level 22
    19400,  # Level 23
    22500,  # Level 24
    26000,  # Level 25 (Track Choice 7 / All 7 Unlocked)
]

TRACK_MILESTONE_LEVELS = [5, 10, 15, 20, 25]

def getLevelForExp(exp):
    level = 1
    for lvl in range(1, MAX_TOON_LEVEL + 1):
        if exp >= LEVEL_EXP_THRESHOLDS[lvl]:
            level = lvl
        else:
            break
    return level

def getExpForLevel(level):
    level = max(1, min(MAX_TOON_LEVEL, level))
    return LEVEL_EXP_THRESHOLDS[level]

def getExpForNextLevel(level):
    if level >= MAX_TOON_LEVEL:
        return LEVEL_EXP_THRESHOLDS[MAX_TOON_LEVEL]
    return LEVEL_EXP_THRESHOLDS[level + 1]

def getTrackCountForLevel(level):
    if level < 5:
        return 2
    elif level < 10:
        return 3
    elif level < 15:
        return 4
    elif level < 20:
        return 5
    elif level < 25:
        return 6
    else:
        return 7


def getMaxStaminaForLevel(level):
    return 100 + max(0, level - 1) * 10


TOON_LEVEL_LAFF_MILESTONES = [6, 12, 18, 24]

def getLaffBoostForLevel(level):
    """Returns +2 Max Laff for every 6 levels reached (Levels 6, 12, 18, 24 = max +8 Laff)."""
    return (min(25, max(1, level)) // 6) * 2
