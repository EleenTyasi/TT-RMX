import random

MODIFIERS = [
    {'key': 'STANDARD',    'label': 'Standard Operations',   'desc': 'Business as usual. No special corporate directives in effect.',                               'weight': 30, 'hp_mult': 1.00, 'boss_hp_mult': 1.0, 'veteran_chance': 0,  'ambush': False, 'frenzied': False, 'lockdown': False},
    {'key': 'OVERCLOCKED', 'label': 'Mandatory Overtime',    'desc': 'All Cogs are clocking extra hours. They have 25% increased health.',                          'weight': 20, 'hp_mult': 1.25, 'boss_hp_mult': 1.0, 'veteran_chance': 0,  'ambush': False, 'frenzied': False, 'lockdown': False},
    {'key': 'REINFORCED',  'label': 'Executive Protection',  'desc': 'The Building Manager has secured additional capital, gaining 50% more health.',               'weight': 15, 'hp_mult': 1.00, 'boss_hp_mult': 1.5, 'veteran_chance': 0,  'ambush': False, 'frenzied': False, 'lockdown': False},
    {'key': 'AMBUSH',      'label': 'Ambush Marketing',      'desc': 'Unsolicited promotions! All reserve Cogs have been deployed to the floor immediately.',       'weight': 12, 'hp_mult': 1.00, 'boss_hp_mult': 1.0, 'veteran_chance': 0,  'ambush': True,  'frenzied': False, 'lockdown': False},
    {'key': 'FRENZIED',    'label': 'Aggressive Expansion',  'desc': 'Cogs are aggressively meeting quotas. Reserve join rate is doubled each room.',               'weight': 10, 'hp_mult': 1.00, 'boss_hp_mult': 1.0, 'veteran_chance': 0,  'ambush': False, 'frenzied': True,  'lockdown': False},
    {'key': 'VETERAN',     'label': 'Senior Management',     'desc': 'Staffed by seasoned operatives. Non-boss Cogs have a 50% chance to be Version 2.0.',          'weight': 8,  'hp_mult': 1.00, 'boss_hp_mult': 1.0, 'veteran_chance': 50, 'ambush': False, 'frenzied': False, 'lockdown': False},
    {'key': 'LOCKDOWN',    'label': 'Boardroom Quarantine',  'desc': 'Corporate security engaged. The Building Manager has summoned an additional elite guard.',    'weight': 5,  'hp_mult': 1.00, 'boss_hp_mult': 1.0, 'veteran_chance': 0,  'ambush': False, 'frenzied': False, 'lockdown': True},
]

_TOTAL_WEIGHT = sum(m['weight'] for m in MODIFIERS)


def pick(track, difficulty):
    roll = random.uniform(0, _TOTAL_WEIGHT)
    cumulative = 0.0
    for modifier in MODIFIERS:
        cumulative += modifier['weight']
        if roll < cumulative:
            return dict(modifier)
    return dict(MODIFIERS[0])


def apply(suits, modifier, is_boss=False):
    mult = modifier.get('boss_hp_mult', 1.0) if is_boss else modifier.get('hp_mult', 1.0)
    veteran_chance = modifier.get('veteran_chance', 0)
    for suit in suits:
        if mult != 1.0:
            suit.maxHP = max(1, int(suit.maxHP * mult))
            suit.currHP = suit.maxHP
        if not is_boss and veteran_chance > 0:
            if random.randint(1, 100) <= veteran_chance:
                suit.isV20 = True
                suit.setSkeleRevives(1)


def get_sos_chance(height, modifier):
    base = 0.02 + (max(1, height) - 1) * 0.01
    bonus = 0.02 if modifier.get('key') in ('VETERAN', 'LOCKDOWN') else 0.0
    return min(base + bonus, 0.08)


def get_barrel_type():
    roll = random.randint(1, 100)
    if roll <= 80:
        return 'gag'
    elif roll <= 90:
        return 'toonup'
    else:
        return 'jellybean'


def get_announcement(modifier):
    if modifier['key'] == 'STANDARD':
        return ''
    return '[%s] %s' % (modifier['label'].upper(), modifier['desc'])
