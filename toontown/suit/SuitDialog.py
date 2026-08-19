import random
from direct.directnotify import DirectNotifyGlobal
from otp.otpbase import OTPLocalizer
from toontown.toonbase import TTLocalizer
notify = DirectNotifyGlobal.directNotify.newCategory('SuitDialog')

def getBrushOffIndex(suitName):
    if suitName in SuitBrushOffs:
        brushoffs = SuitBrushOffs[suitName]
    else:
        brushoffs = SuitBrushOffs[None]
    num = len(brushoffs)
    chunk = 100 / num
    randNum = random.randint(0, 99)
    count = chunk
    for i in range(num):
        if randNum < count:
            return i
        count += chunk

    notify.error('getBrushOffs() - no brush off found!')
    return


def getBrushOffText(suitName, index):
    if suitName in SuitBrushOffs:
        brushoffs = SuitBrushOffs[suitName]
    else:
        brushoffs = SuitBrushOffs[None]
    return brushoffs[index]


SuitBrushOffs = OTPLocalizer.SuitBrushOffs
SuitSprintRamDialog = getattr(TTLocalizer, 'SuitSprintRamTaunts', [
    "Watch where you're going, Toon!",
    "I'm suing you for reckless endangerment!",
    "That is a direct violation of OSHA regulations!",
    "Halt! You don't have clearance to move at that speed!",
    "A collision? I demand to see your insurance!",
    "Direct impact detected! Initiating emergency audit!",
    "Oof! That's coming out of your quarterly budget!",
    "Reckless driving in a corporate pedestrian zone?!",
    "My chassis wasn't built for vehicular combat!",
    "I'll see you in small claims court for that!",
    "Disorderly conduct! Prepare for immediate downsizing!",
    "Hey! That violates our personal boundary agreement!",
])


def getSprintRamText(suitName=None):
    ramDict = getattr(TTLocalizer, 'SuitSprintRamTaunts', {})
    if isinstance(ramDict, dict):
        if suitName in ramDict:
            lines = ramDict[suitName]
        else:
            lines = ramDict.get(None, SuitSprintRamDialog)
    elif isinstance(ramDict, (list, tuple)):
        lines = ramDict
    else:
        lines = SuitSprintRamDialog
    return random.choice(lines)


def getHealThanksText():
    thanksList = getattr(TTLocalizer, 'SuitHealThanks', [
        "Thank you for the capital injection!",
        "Quarterly restructuring approved!",
        "Synergy at maximum efficiency!",
        "Appreciate the corporate bailout!",
        "Thanks for the operational budget increase!",
        "My stock value just skyrocketed!",
        "A well-timed asset recovery!",
        "Excellent team synergy!",
        "Thanks! Reallocating resources now!",
        "Our partnership is paying dividends!",
        "Depreciation reversed! Back to business!",
        "Thanks for the emergency liquidity!",
    ])
    return random.choice(thanksList)


