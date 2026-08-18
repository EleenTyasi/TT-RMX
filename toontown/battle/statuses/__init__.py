from .StatusBase import StatusBase
from .SlowStatus import SlowStatus
from .WetStatus import WetStatus
from .FreezeStatus import FreezeStatus
from .WeakenStatus import WeakenStatus
from .PoisonStatus import PoisonStatus
from .BurnStatus import BurnStatus
from .ShieldStatus import ShieldStatus
from .LuckyStatus import LuckyStatus
from .RalliedStatus import RalliedStatus

STATUS_CLASSES = {
    'SLOW': SlowStatus,
    'WET': WetStatus,
    'FREEZE': FreezeStatus,
    'WEAKEN': WeakenStatus,
    'POISON': PoisonStatus,
    'BURN': BurnStatus,
    'SHIELD': ShieldStatus,
    'LUCKY': LuckyStatus,
    'RALLIED': RalliedStatus,
}

def create_status_instance(effect_name, avatar_id, rounds, data=None):
    cls = STATUS_CLASSES.get(effect_name, StatusBase)
    inst = cls(avatar_id, rounds, data)
    inst.name = effect_name
    return inst
