from panda3d.core import *
from libotp import CFSpeech, CFTimeout
from direct.task.Task import Task
from direct.distributed import ClockDelta
from toontown.toonbase import TTLocalizer, ToontownGlobals
from toontown.toon import NPCToons
from .DistributedNPCToonBase import DistributedNPCToonBase
from . import CombatChrisGUI

class DistributedNPCCombatChris(DistributedNPCToonBase):

    def __init__(self, cr):
        DistributedNPCToonBase.__init__(self, cr)
        self.isLocalToon = 0
        self.gui = None
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
        if self.gui:
            self.gui.destroy()
            self.gui = None
        if self.isLocalToon:
            base.localAvatar.posCamera(0, 0)
        DistributedNPCToonBase.disable(self)

    def delete(self):
        if self.gui:
            self.gui.destroy()
            self.gui = None
        DistributedNPCToonBase.delete(self)

    def getCollSphereRadius(self):
        return 3.25

    def handleCollisionSphereEnter(self, collEntry):
        place = base.cr.playGame.getPlace()
        if place and hasattr(place, 'fsm'):
            place.fsm.request('purchase')
        self.sendUpdate('avatarEnter', [])

    def __handleGuiDone(self):
        if self.gui:
            self.gui.destroy()
            self.gui = None
        self.sendUpdate('setMovieDone', [])

    def setMovie(self, mode, avId, timestamp):
        isLocalToon = avId == base.localAvatar.doId
        if mode == NPCToons.COMBATCHRIS_MOVIE_CLEAR:
            return
        if mode == NPCToons.COMBATCHRIS_MOVIE_TIMEOUT:
            if isLocalToon:
                if self.gui:
                    self.gui.destroy()
                    self.gui = None
                place = base.cr.playGame.getPlace()
                if place and hasattr(place, 'fsm'):
                    place.fsm.request('walk')
                self.setChatAbsolute(TTLocalizer.STOREOWNER_TOOKTOOLONG, CFSpeech | CFTimeout)
            self.freeAvatar()
            return
        if mode == NPCToons.COMBATCHRIS_MOVIE_START:
            self.isLocalToon = isLocalToon
            if isLocalToon:
                self.gui = CombatChrisGUI.CombatChrisGUI(self.__handleGuiDone)
            self.setChatAbsolute("Ready to master battle tactics? Ask me anything!", CFSpeech | CFTimeout)
            return
        if mode == NPCToons.COMBATCHRIS_MOVIE_COMPLETE:
            if isLocalToon:
                if self.gui:
                    self.gui.destroy()
                    self.gui = None
                place = base.cr.playGame.getPlace()
                if place and hasattr(place, 'fsm'):
                    place.fsm.request('walk')
            self.setChatAbsolute("Stay safe out there, Toon! Give those Cogs a good pie in the face!", CFSpeech | CFTimeout)
            self.freeAvatar()
            return
