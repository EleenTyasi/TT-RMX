import os
import json
from direct.directnotify import DirectNotifyGlobal

notify = DirectNotifyGlobal.directNotify.newCategory('WorldBossGlobals')
CONFIG_PATH = os.path.join(os.getcwd(), 'config', 'cogs', 'world_bosses.json')

WORLD_BOSSES = {}
_boss_hp_storage = {}
_street_cogs_defeated = {}  # {zone_id: count}

def increment_street_cogs_defeated(zone_id):
    """Increments the defeated cogs counter on this street to increase pity spawn rate."""
    _street_cogs_defeated[zone_id] = _street_cogs_defeated.get(zone_id, 0) + 1

def get_world_boss_spawn_chance(zone_id):
    """
    Base chance is 2%.
    For each cog defeated on this street, pity adds +0.5% (or +1% per 2 cogs)
    scaling up to a maximum of 20% spawn rate.
    """
    defeated = _street_cogs_defeated.get(zone_id, 0)
    # Starts at 2.0%, reaches 20.0% after defeating ~36 cogs on the street
    pity_chance = min(20.0, 2.0 + (defeated * 0.5))
    return pity_chance

def reset_street_pity(zone_id):
    """Resets the pity counter for this street when a World Boss spawns."""
    _street_cogs_defeated[zone_id] = 0

def load_world_bosses(force=False):
    global WORLD_BOSSES
    if WORLD_BOSSES and not force:
        return
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                WORLD_BOSSES = json.load(f)
            notify.info('Loaded %d Playground World Bosses from %s' % (len(WORLD_BOSSES), CONFIG_PATH))
        except Exception as e:
            notify.warning('Failed to load world_bosses.json: %s' % e)

def get_world_boss_for_zone(zone_id):
    if not WORLD_BOSSES:
        load_world_bosses()
    # Zone ID matching (e.g. 2100 -> 2000)
    hood_id = (zone_id // 1000) * 1000
    return WORLD_BOSSES.get(str(hood_id)) or WORLD_BOSSES.get(str(zone_id))

def get_boss_current_hp(zone_id):
    boss_info = get_world_boss_for_zone(zone_id)
    if not boss_info:
        return 0
    hood_id = (zone_id // 1000) * 1000
    key = str(hood_id)
    if key not in _boss_hp_storage:
        _boss_hp_storage[key] = boss_info.get('max_hp', 1000)
    return _boss_hp_storage[key]

def set_boss_current_hp(zone_id, hp):
    hood_id = (zone_id // 1000) * 1000
    key = str(hood_id)
    _boss_hp_storage[key] = max(0, hp)

def reset_boss_hp(zone_id):
    boss_info = get_world_boss_for_zone(zone_id)
    if boss_info:
        hood_id = (zone_id // 1000) * 1000
        _boss_hp_storage[str(hood_id)] = boss_info.get('max_hp', 1000)

load_world_bosses()