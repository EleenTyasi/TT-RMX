from panda3d.core import *
from libotp import CFSpeech, CFTimeout
from direct.task.Task import Task
from direct.distributed import ClockDelta
from toontown.toonbase import TTLocalizer, ToontownGlobals
from toontown.toon import NPCToons
from toontown.estate import BankGUI
from .DistributedNPCToonBase import DistributedNPCToonBase

class DistributedNPCBanker(DistributedNPCToonBase):

    def __init__(self, cr):
        DistributedNPCToonBase.__init__(self, cr)
        self.isLocalToon = 0
        self.bankGui = None
        self.bankGuiDoneEvent = 'bankGuiDone'
        self.spawnX = 0.0
        self.spawnY = 0.0
        self.spawnZ = 0.0
        self.spawnH = 0.0

    def setSpawnPos(self, x, y, z, h):
        self.spawnX = x
        self.spawnY = y
        self.spawnZ = z
        self.spawnH = h
        if self.isGenerated():
            self.reparentTo(render)
            self.setPos(x, y, z)
            self.setH(h)

    def initToonState(self):
        self.setAnimState('neutral', 0.9, None, None)
        self.reparentTo(render)
        self.setPos(self.spawnX, self.spawnY, self.spawnZ)
        self.setH(self.spawnH)

    def disable(self):
        self.ignoreAll()
        if self.bankGui:
            self.bankGui.destroy()
            self.bankGui = None
        if self.isLocalToon:
            base.localAvatar.posCamera(0, 0)
        DistributedNPCToonBase.disable(self)

    def delete(self):
        if self.bankGui:
            self.bankGui.destroy()
            self.bankGui = None
        DistributedNPCToonBase.delete(self)

    def getCollSphereRadius(self):
        return 3.25

    def handleCollisionSphereEnter(self, collEntry):
        place = base.cr.playGame.getPlace()
        if place and hasattr(place, 'fsm'):
            place.fsm.request('purchase')
        self.sendUpdate('avatarEnter', [])

    def __handleBankDone(self, transactionAmount):
        self.sendUpdate('transferMoney', [transactionAmount])
        self.ignore(self.bankGuiDoneEvent)
        if self.bankGui is not None:
            self.bankGui.destroy()
            self.bankGui = None

    def resetBanker(self):
        self.ignoreAll()
        if self.bankGui:
            self.bankGui.destroy()
            self.bankGui = None
        self.startLookAround()
        self.detectAvatars()
        if self.isLocalToon:
            self.freeAvatar()
        return Task.done

    def setMovie(self, mode, npcId, avId, timestamp):
        timeStamp = ClockDelta.globalClockDelta.localElapsedTime(timestamp)
        self.isLocalToon = (avId == base.localAvatar.doId)
        av = base.cr.doId2do.get(avId)

        if mode == NPCToons.BANKER_MOVIE_CLEAR:
            return
        elif mode == NPCToons.BANKER_MOVIE_GUI:
            if self.isLocalToon:
                if self.bankGui:
                    self.bankGui.destroy()
                self.bankGui = BankGUI.BankGui(self.bankGuiDoneEvent)
                self.accept(self.bankGuiDoneEvent, self.__handleBankDone)
            self.setChatAbsolute(TTLocalizer.BankerGreeting, CFSpeech | CFTimeout)
        elif mode == NPCToons.BANKER_MOVIE_TRANSDONE:
            self.setChatAbsolute(TTLocalizer.BankerTransDone, CFSpeech | CFTimeout)
            if self.isLocalToon:
                base.playSfx(base.loader.loadSfx('phase_4/audio/sfx/SZ_DD_treasure.ogg'))
            self.resetBanker()
        elif mode == NPCToons.BANKER_MOVIE_CANCEL:
            self.setChatAbsolute(TTLocalizer.BankerCancel, CFSpeech | CFTimeout)
            self.resetBanker()
        elif mode == NPCToons.BANKER_MOVIE_TIMEOUT:
            self.resetBanker()
