"""
BattleConfigLoader.py

Modular battle tuning configuration loader and auto-generator for TT-RMX.
Organizes combat stats into separate JSON files:
  - config/cogs/bossbot.json, lawbot.json, cashbot.json, sellbot.json
  - config/cogs/cog_attacks.json
  - config/gags/heal.json, trap.json, lure.json, sound.json, throw.json, squirt.json, drop.json
  - config/status_effects.json

If any JSON file is missing, it is automatically generated with defaults.
Any edits made to these files will live-override combat stats on startup.
"""
import os
import json
import re

CONFIG_DIR = os.path.join(os.getcwd(), 'config')
COGS_DIR = os.path.join(CONFIG_DIR, 'cogs')
GAGS_DIR = os.path.join(CONFIG_DIR, 'gags')
STATUS_FILE = os.path.join(CONFIG_DIR, 'status_effects.json')
ATTACKS_FILE = os.path.join(COGS_DIR, 'cog_attacks.json')

# Department mappings
DEPARTMENTS = {
    'Bossbot': ('f', 'p', 'ym', 'mm', 'ds', 'hh', 'cr', 'tbc'),
    'Lawbot':  ('bf', 'b', 'dt', 'ac', 'bs', 'sd', 'le', 'bw'),
    'Cashbot': ('sc', 'pp', 'tw', 'bc', 'nc', 'mb', 'ls', 'rb'),
    'Sellbot': ('cc', 'tm', 'nd', 'gh', 'ms', 'tf', 'm', 'mh'),
}

COG_NAMES = {
    'f': 'Flunky', 'p': 'Pencil Pusher', 'ym': 'Yesman', 'mm': 'Micromanager',
    'ds': 'Downsizer', 'hh': 'Head Hunter', 'cr': 'Corporate Raider', 'tbc': 'The Big Cheese',
    'bf': 'Bottom Feeder', 'b': 'Bloodsucker', 'dt': 'Double Talker', 'ac': 'Ambulance Chaser',
    'bs': 'Back Stabber', 'sd': 'Spin Doctor', 'le': 'Legal Eagle', 'bw': 'Big Wig',
    'sc': 'Short Change', 'pp': 'Penny Pincher', 'tw': 'Tightwad', 'bc': 'Bean Counter',
    'nc': 'Number Cruncher', 'mb': 'Money Bags', 'ls': 'Loan Shark', 'rb': 'Robber Baron',
    'cc': 'Cold Caller', 'tm': 'Telemarketer', 'nd': 'Name Dropper', 'gh': 'Glad Hander',
    'ms': 'Mover & Shaker', 'tf': 'Two-Face', 'm': 'The Mingler', 'mh': 'Mr. Hollywood',
}

GAG_NAMES = [
    # Heal
    ['Feather', 'Megaphone', 'Lipstick', 'Bamboo Cane', 'Pixie Dust', 'Juggling Balls', 'High Dive'],
    # Trap
    ['Banana Peel', 'Rake', 'Marbles', 'Quicksand', 'Trapdoor', 'TNT', 'Railroad'],
    # Lure
    ['$1 Bill', 'Small Magnet', '$5 Bill', 'Big Magnet', '$10 Bill', 'Hypno-Goggles', 'Presentation'],
    # Sound
    ['Bike Horn', 'Whistle', 'Bugle', 'Aoogah', 'Elephant Trunk', 'Foghorn', 'Opera Singer'],
    # Throw
    ['Cupcake', 'Fruit Pie Slice', 'Cream Pie Slice', 'Whole Fruit Pie', 'Whole Cream Pie', 'Birthday Cake', 'Wedding Cake'],
    # Squirt
    ['Squirting Flower', 'Glass of Water', 'Squirt Gun', 'Seltzer Bottle', 'Fire Hose', 'Storm Cloud', 'Geyser'],
    # Drop
    ['Flower Pot', 'Sandbag', 'Anvil', 'Big Weight', 'Safe', 'Grand Piano', 'Toontanic'],
]

TRACK_KEYS = ('heal', 'trap', 'lure', 'sound', 'throw', 'squirt', 'drop')
TRACK_DISPLAY_NAMES = {
    'heal': 'Heal (Toon-Up)', 'trap': 'Trap', 'lure': 'Lure',
    'sound': 'Sound', 'throw': 'Throw', 'squirt': 'Squirt', 'drop': 'Drop'
}

DEFAULT_STATUS_EFFECTS = {
    'FREEZE': {'description': 'Target skips attack turn', 'default_rounds': 1},
    'SLOW':   {'description': 'Reduces target defense and dodge chance', 'defense_reduction': 30, 'default_rounds': 3},
    'WEAKEN': {'description': 'Reduces target attack power and defense', 'defense_reduction': 10, 'default_rounds': 2},
    'BURN':   {'description': 'Amplifies incoming damage', 'damage_multiplier': 1.5, 'default_rounds': 2},
    'POISON': {'description': 'Deals damage over time at turn start', 'damage_per_round': 15, 'default_rounds': 3},
}

DEFAULT_SUIT_ATTACK_STATUS = {
    'FreezeAssets': {'effect': 'FREEZE', 'rounds': 1, 'chance': 100},
    'RedTape': {'effect': 'SLOW', 'rounds': 2, 'accuracy_reduction': 10, 'chance': 80},
    'Demotion': {'effect': 'WEAKEN', 'rounds': 2, 'defense_reduction': 10, 'chance': 75},
}


def _clean_str(s):
    return re.sub(r'[\s\-_\.\&]', '', str(s).lower())


def _calc_hp_list(base_hp, hp_growth, count=5):
    """Calculates an HP list using base_hp and growth (or default polynomial)."""
    return [int(base_hp + i * hp_growth) for i in range(count)]


def _calc_stat_list(base_val, growth, count=5):
    return [int(base_val + i * growth) for i in range(count)]


def ensure_directories():
    os.makedirs(COGS_DIR, exist_ok=True)
    os.makedirs(GAGS_DIR, exist_ok=True)


def export_status_effects():
    if not os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_STATUS_EFFECTS, f, indent=2)
            print('[BATTLE-CONFIG] Generated %s' % STATUS_FILE)
        except Exception as e:
            print('[BATTLE-CONFIG] Warning: Could not write %s: %s' % (STATUS_FILE, e))


def export_cog_attacks(suit_attributes, suit_attacks_dict):
    if not os.path.exists(ATTACKS_FILE):
        attacks_data = {}
        for code, data in suit_attributes.items():
            for atk in data.get('attacks', ()):
                atk_name = str(atk[0])
                if atk_name not in attacks_data:
                    anim, tgt = suit_attacks_dict.get(atk_name, ('magic1', 2))
                    tgt_str = 'group' if tgt == 3 else 'single'
                    status_proc = DEFAULT_SUIT_ATTACK_STATUS.get(atk_name)
                    attacks_data[atk_name] = {
                        'name': atk_name,
                        'anim': anim,
                        'target': tgt_str,
                        'damage': list(atk[1]),
                        'accuracy': list(atk[2]),
                        'frequency': list(atk[3]),
                        'status_effect': status_proc,
                    }
        try:
            with open(ATTACKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(attacks_data, f, indent=2)
            print('[BATTLE-CONFIG] Generated %s' % ATTACKS_FILE)
        except Exception as e:
            print('[BATTLE-CONFIG] Warning: Could not write %s: %s' % (ATTACKS_FILE, e))


def export_departments(suit_attributes):
    for dept_name, codes in DEPARTMENTS.items():
        dept_file = os.path.join(COGS_DIR, '%s.json' % dept_name.lower())
        if not os.path.exists(dept_file):
            dept_dict = {}
            for code in codes:
                info = suit_attributes.get(code, {})
                full_name = COG_NAMES.get(code, code)
                hp = list(info.get('hp', [6, 12, 20, 30, 42]))
                def_vals = list(info.get('def', [2, 5, 10, 12, 15]))
                acc_vals = list(info.get('acc', [35, 40, 45, 50, 55]))
                attacks_list = [str(a[0]) for a in info.get('attacks', ())]

                base_hp = hp[0] if hp else 6
                hp_growth = (hp[1] - hp[0]) if len(hp) > 1 else 6
                base_def = def_vals[0] if def_vals else 2
                def_growth = (def_vals[1] - def_vals[0]) if len(def_vals) > 1 else 3
                base_acc = acc_vals[0] if acc_vals else 35
                acc_growth = (acc_vals[1] - acc_vals[0]) if len(acc_vals) > 1 else 5

                dept_dict[full_name] = {
                    'code': code,
                    'base_level': int(info.get('level', 0)) + 1,
                    'base_hp': base_hp,
                    'hp_growth': hp_growth,
                    'base_defense': base_def,
                    'defense_growth': def_growth,
                    'base_accuracy': base_acc,
                    'accuracy_growth': acc_growth,
                    'attacks': attacks_list,
                }
            try:
                with open(dept_file, 'w', encoding='utf-8') as f:
                    json.dump(dept_dict, f, indent=2)
                print('[BATTLE-CONFIG] Generated %s' % dept_file)
            except Exception as e:
                print('[BATTLE-CONFIG] Warning: Could not write %s: %s' % (dept_file, e))


def export_gags(gag_damage, gag_accuracy, gag_xp):
    for track_idx, track_key in enumerate(TRACK_KEYS):
        track_file = os.path.join(GAGS_DIR, '%s.json' % track_key)
        if not os.path.exists(track_file):
            gags_list = []
            for lvl_idx in range(7):
                dmg_min, dmg_max = gag_damage[track_idx][lvl_idx][0] if track_idx < len(gag_damage) and lvl_idx < len(gag_damage[track_idx]) else (10, 10)
                acc = gag_accuracy[track_idx][lvl_idx] if track_idx < len(gag_accuracy) and lvl_idx < len(gag_accuracy[track_idx]) else 75
                xp = gag_xp[track_idx][lvl_idx] if track_idx < len(gag_xp) and lvl_idx < len(gag_xp[track_idx]) else 0
                name = GAG_NAMES[track_idx][lvl_idx] if track_idx < len(GAG_NAMES) and lvl_idx < len(GAG_NAMES[track_idx]) else 'Gag'
                
                # Determine default target (group vs single)
                is_group = False
                if track_key == 'sound':
                    is_group = True
                elif track_key == 'heal' and lvl_idx in (1, 3, 5, 6):
                    is_group = True
                elif track_key in ('throw', 'squirt', 'drop', 'trap', 'lure') and lvl_idx == 6:
                    is_group = True

                gags_list.append({
                    'level': lvl_idx + 1,
                    'name': name,
                    'damage_min': dmg_min,
                    'damage_max': dmg_max,
                    'accuracy': acc,
                    'target': 'group' if is_group else 'single',
                    'xp_unlock': xp,
                    'status_effect': None,
                })

            track_dict = {
                'track': track_key,
                'display_name': TRACK_DISPLAY_NAMES.get(track_key, track_key),
                'gags': gags_list,
            }
            try:
                with open(track_file, 'w', encoding='utf-8') as f:
                    json.dump(track_dict, f, indent=2)
                print('[BATTLE-CONFIG] Generated %s' % track_file)
            except Exception as e:
                print('[BATTLE-CONFIG] Warning: Could not write %s: %s' % (track_file, e))


def load_or_create_config(suit_attributes, gag_damage, gag_accuracy, gag_xp, max_skill=10500):
    """
    Ensures all modular JSON files exist (generating any missing ones), then
    loads and applies overrides in-place.
    """
    from toontown.battle.SuitsConfig import SUIT_ATTACKS
    ensure_directories()
    export_status_effects()
    export_cog_attacks(suit_attributes, SUIT_ATTACKS)
    export_departments(suit_attributes)
    export_gags(gag_damage, gag_accuracy, gag_xp)

    # 1. Load Cog Attacks
    cog_attacks_db = {}
    if os.path.exists(ATTACKS_FILE):
        try:
            with open(ATTACKS_FILE, 'r', encoding='utf-8') as f:
                cog_attacks_db = json.load(f)
            # Update SUIT_ATTACKS anim / target and status effects
            for atk_name, atk_data in cog_attacks_db.items():
                anim = atk_data.get('anim', 'magic1')
                tgt = 3 if atk_data.get('target') == 'group' else 2
                SUIT_ATTACKS[atk_name] = (anim, tgt)
                status = atk_data.get('status_effect')
                if status:
                    from toontown.battle import StatusEffectsConfig
                    StatusEffectsConfig.SUIT_ATTACK_STATUS_EFFECTS[atk_name] = status
        except Exception as e:
            print('[BATTLE-CONFIG] Warning: Could not read %s: %s' % (ATTACKS_FILE, e))

    # 2. Load Department Cogs
    for dept_name in DEPARTMENTS:
        dept_file = os.path.join(COGS_DIR, '%s.json' % dept_name.lower())
        if os.path.exists(dept_file):
            try:
                with open(dept_file, 'r', encoding='utf-8') as f:
                    cogs_dict = json.load(f)
                for cog_name, cog_data in cogs_dict.items():
                    # Resolve code
                    code = cog_data.get('code')
                    if not code:
                        for c, n in COG_NAMES.items():
                            if _clean_str(n) == _clean_str(cog_name):
                                code = c
                                break
                    if code and code in suit_attributes:
                        # HP calculation
                        if 'hp' in cog_data and isinstance(cog_data['hp'], list):
                            suit_attributes[code]['hp'] = tuple(cog_data['hp'])
                        else:
                            base_hp = cog_data.get('base_hp', suit_attributes[code]['hp'][0])
                            growth = cog_data.get('hp_growth', 6)
                            suit_attributes[code]['hp'] = tuple(_calc_hp_list(base_hp, growth))

                        # Defense calculation
                        if 'def' in cog_data and isinstance(cog_data['def'], list):
                            suit_attributes[code]['def'] = tuple(cog_data['def'])
                        else:
                            base_def = cog_data.get('base_defense', suit_attributes[code]['def'][0])
                            growth = cog_data.get('defense_growth', 3)
                            suit_attributes[code]['def'] = tuple(_calc_stat_list(base_def, growth))

                        # Accuracy calculation
                        if 'acc' in cog_data and isinstance(cog_data['acc'], list):
                            suit_attributes[code]['acc'] = tuple(cog_data['acc'])
                        else:
                            base_acc = cog_data.get('base_accuracy', suit_attributes[code]['acc'][0])
                            growth = cog_data.get('accuracy_growth', 5)
                            suit_attributes[code]['acc'] = tuple(_calc_stat_list(base_acc, growth))

                        # Attacks linking
                        raw_attacks = cog_data.get('attacks', [])
                        attacks_list = []
                        for atk_item in raw_attacks:
                            if isinstance(atk_item, str):
                                atk_name = atk_item
                                atk_info = cog_attacks_db.get(atk_name, {})
                                hp_arr = tuple(atk_info.get('damage', [2, 3, 4, 5, 6]))
                                acc_arr = tuple(atk_info.get('accuracy', [75, 75, 80, 85, 90]))
                                freq_arr = tuple(atk_info.get('frequency', [25, 25, 25, 25, 25]))
                                attacks_list.append((atk_name, hp_arr, acc_arr, freq_arr))
                            elif isinstance(atk_item, dict):
                                atk_name = atk_item.get('name', 'PoundKey')
                                hp_arr = tuple(atk_item.get('hp', [2, 3, 4, 5, 6]))
                                acc_arr = tuple(atk_item.get('acc', [75, 75, 80, 85, 90]))
                                freq_arr = tuple(atk_item.get('freq', [25, 25, 25, 25, 25]))
                                attacks_list.append((atk_name, hp_arr, acc_arr, freq_arr))
                        if attacks_list:
                            suit_attributes[code]['attacks'] = tuple(attacks_list)
            except Exception as e:
                print('[BATTLE-CONFIG] Warning: Could not read %s: %s' % (dept_file, e))

    # 3. Load Gags
    new_gag_xp = [list(xp) for xp in gag_xp]
    new_gag_acc = [list(acc) for acc in gag_accuracy]
    new_gag_damage = []

    for track_idx, track_key in enumerate(TRACK_KEYS):
        track_file = os.path.join(GAGS_DIR, '%s.json' % track_key)
        track_dmg_tuples = []
        if os.path.exists(track_file):
            try:
                with open(track_file, 'r', encoding='utf-8') as f:
                    track_data = json.load(f)
                gags_list = track_data.get('gags', [])
                for lvl_idx in range(7):
                    gag_entry = gags_list[lvl_idx] if lvl_idx < len(gags_list) else {}
                    dmg_min = gag_entry.get('damage_min', gag_damage[track_idx][lvl_idx][0][0])
                    dmg_max = gag_entry.get('damage_max', gag_damage[track_idx][lvl_idx][0][1])
                    acc = gag_entry.get('accuracy', gag_accuracy[track_idx][lvl_idx])
                    xp = gag_entry.get('xp_unlock', gag_xp[track_idx][lvl_idx])

                    new_gag_acc[track_idx][lvl_idx] = acc
                    new_gag_xp[track_idx][lvl_idx] = xp

                    # Optional per-gag status effect
                    status_proc = gag_entry.get('status_effect')
                    if status_proc:
                        from toontown.battle import StatusEffectsConfig
                        StatusEffectsConfig.GAG_TRACK_STATUS_EFFECTS[track_idx] = status_proc

            except Exception as e:
                print('[BATTLE-CONFIG] Warning: Could not read %s: %s' % (track_file, e))

        for lvl_idx in range(7):
            min_xp = new_gag_xp[track_idx][lvl_idx]
            max_xp = new_gag_xp[track_idx][lvl_idx + 1] if (lvl_idx + 1) < len(new_gag_xp[track_idx]) else max_skill
            dmg_range = (new_gag_acc[track_idx][lvl_idx], new_gag_acc[track_idx][lvl_idx])
            if track_idx < len(gag_damage) and lvl_idx < len(gag_damage[track_idx]):
                d_min = gag_damage[track_idx][lvl_idx][0][0]
                d_max = gag_damage[track_idx][lvl_idx][0][1]
                if os.path.exists(track_file):
                    try:
                        d_min = gags_list[lvl_idx].get('damage_min', d_min)
                        d_max = gags_list[lvl_idx].get('damage_max', d_max)
                    except Exception:
                        pass
                dmg_range = (d_min, d_max)
            track_dmg_tuples.append((dmg_range, (min_xp, max_xp)))
        new_gag_damage.append(tuple(track_dmg_tuples))

    print('[BATTLE-CONFIG] Successfully loaded modular battle configuration from %s' % CONFIG_DIR)
    return tuple(new_gag_damage), tuple(tuple(a) for a in new_gag_acc), new_gag_xp

