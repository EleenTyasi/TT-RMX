from panda3d.core import *
from libotp import CFSpeech, CFTimeout
from direct.task.Task import Task
from direct.distributed import ClockDelta
from toontown.toonbase import TTLocalizer, ToontownGlobals
from toontown.toon import NPCToons
from toontown.toontowngui import TTDialog
from .DistributedNPCToonBase import DistributedNPCToonBase

class DistributedNPCHealer(DistributedNPCToonBase):

    def __init__(self, cr):
        DistributedNPCToonBase.__init__(self, cr)
        self.isLocalToon = 0
        self.dialog = None

    def initToonState(self):
        self.setAnimState('neutral', 0.9, None, None)

    def disable(self):
        self.ignoreAll()
        if self.dialog:
            self.dialog.cleanup()
            self.dialog = None
        if self.isLocalToon:
            base.localAvatar.posCamera(0, 0)
        DistributedNPCToonBase.disable(self)

    def delete(self):
        if self.dialog:
            self.dialog.cleanup()
            self.dialog = None
        DistributedNPCToonBase.delete(self)

    def getCollSphereRadius(self):
        return 3.25

    def handleCollisionSphereEnter(self, collEntry):
        place = base.cr.playGame.getPlace()
        if place and hasattr(place, 'fsm'):
            place.fsm.request('purchase')
        self.sendUpdate('avatarEnter', [])

    def __handleChoice(self, value):
        if self.dialog:
            self.dialog.cleanup()
            self.dialog = None
        if value > 0:
            self.sendUpdate('chooseHeal', [1])
        else:
            self.sendUpdate('chooseHeal', [0])

    def resetHealer(self):
        self.ignoreAll()
        if self.dialog:
            self.dialog.cleanup()
            self.dialog = None
        self.startLookAround()
        self.detectAvatars()
        if self.isLocalToon:
            self.freeAvatar()
        return Task.done

    def setMovie(self, mode, npcId, avId, timestamp):
        timeStamp = ClockDelta.globalClockDelta.localElapsedTime(timestamp)
        self.isLocalToon = (avId == base.localAvatar.doId)
        av = base.cr.doId2do.get(avId)
        toonName = av.getName() if av else 'Toon'

        if mode == NPCToons.HEALER_MOVIE_CLEAR:
            return
        elif mode == NPCToons.HEALER_MOVIE_PROMPT:
            if self.isLocalToon:
                if self.dialog:
                    self.dialog.cleanup()
                self.dialog = TTDialog.TTDialog(
                    style=TTDialog.TwoChoice,
                    text=TTLocalizer.HealerHankPrompt,
                    text_wordwrap=15,
                    command=self.__handleChoice,
                )
                self.dialog.show()
            self.setChatAbsolute(TTLocalizer.HealerHankPrompt, CFSpeech | CFTimeout)
        elif mode == NPCToons.HEALER_MOVIE_SAD:
            self.setChatAbsolute(TTLocalizer.HealerHankSad % toonName, CFSpeech | CFTimeout)
            self.resetHealer()
        elif mode == NPCToons.HEALER_MOVIE_FULL_HP:
            self.setChatAbsolute(TTLocalizer.HealerHankFullHp, CFSpeech | CFTimeout)
            self.resetHealer()
        elif mode == NPCToons.HEALER_MOVIE_NO_MONEY:
            self.setChatAbsolute(TTLocalizer.HealerHankNoMoney, CFSpeech | CFTimeout)
            self.resetHealer()
        elif mode == NPCToons.HEALER_MOVIE_HEALED:
            self.setChatAbsolute(TTLocalizer.HealerHankHealed, CFSpeech | CFTimeout)
            if self.isLocalToon:
                base.playSfx(base.loader.loadSfx('phase_4/audio/sfx/SZ_DD_treasure.ogg'))
            self.resetHealer()
        elif mode == NPCToons.HEALER_MOVIE_CANCEL:
            self.setChatAbsolute(TTLocalizer.HealerHankCancel, CFSpeech | CFTimeout)
            self.resetHealer()
        elif mode == NPCToons.HEALER_MOVIE_TIMEOUT:
            self.resetHealer()
