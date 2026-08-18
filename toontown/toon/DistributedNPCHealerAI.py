from direct.task import Task
from direct.distributed import ClockDelta
from toontown.toonbase import TTLocalizer, ToontownGlobals
from toontown.toon import NPCToons
from .DistributedNPCToonBaseAI import DistributedNPCToonBaseAI

class DistributedNPCHealerAI(DistributedNPCToonBaseAI):

    def __init__(self, air, npcId):
        DistributedNPCToonBaseAI.__init__(self, air, npcId)
        self.givesQuests = 0
        self.busy = 0

    def delete(self):
        taskMgr.remove(self.uniqueName('clearMovie'))
        self.ignoreAll()
        DistributedNPCToonBaseAI.delete(self)

    def avatarEnter(self):
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.air.doId2do:
            self.notify.warning('Avatar: %s not found' % avId)
            return
        if self.isBusy():
            self.freeAvatar(avId)
            return
        av = self.air.doId2do[avId]
        self.busy = avId
        self.acceptOnce(self.air.getAvatarExitEvent(avId), self.__handleUnexpectedExit, extraArgs=[avId])

        if av.hp <= 0:
            self.d_setMovie(avId, NPCToons.HEALER_MOVIE_SAD)
            self.sendClearMovie(None)
        elif av.hp >= av.maxHp:
            self.d_setMovie(avId, NPCToons.HEALER_MOVIE_FULL_HP)
            self.sendClearMovie(None)
        elif av.getMoney() < 20:
            self.d_setMovie(avId, NPCToons.HEALER_MOVIE_NO_MONEY)
            self.sendClearMovie(None)
        else:
            self.d_setMovie(avId, NPCToons.HEALER_MOVIE_PROMPT)
            taskMgr.doMethodLater(30.0, self.sendTimeoutMovie, self.uniqueName('clearMovie'))
        DistributedNPCToonBaseAI.avatarEnter(self)

    def d_setMovie(self, avId, flag):
        self.sendUpdate('setMovie', [flag,
         self.npcId,
         avId,
         ClockDelta.globalClockDelta.getRealNetworkTime()])

    def sendTimeoutMovie(self, task):
        self.d_setMovie(self.busy, NPCToons.HEALER_MOVIE_TIMEOUT)
        self.sendClearMovie(None)
        return Task.done

    def sendClearMovie(self, task):
        self.ignore(self.air.getAvatarExitEvent(self.busy))
        taskMgr.remove(self.uniqueName('clearMovie'))
        self.busy = 0
        self.d_setMovie(0, NPCToons.HEALER_MOVIE_CLEAR)
        return Task.done

    def chooseHeal(self, wantsHeal):
        avId = self.air.getAvatarIdFromSender()
        if self.busy != avId:
            self.air.writeServerEvent('suspicious', avId, 'DistributedNPCHealerAI.chooseHeal busy with %s' % self.busy)
            self.notify.warning('somebody called chooseHeal that I was not busy with! avId: %s' % avId)
            return
        av = simbase.air.doId2do.get(avId)
        if av:
            if wantsHeal:
                if av.hp > 0 and av.hp < av.maxHp and av.getMoney() >= 20:
                    av.takeMoney(20)
                    av.b_setHp(av.maxHp)
                    self.d_setMovie(avId, NPCToons.HEALER_MOVIE_HEALED)
                elif av.hp >= av.maxHp:
                    self.d_setMovie(avId, NPCToons.HEALER_MOVIE_FULL_HP)
                elif av.getMoney() < 20:
                    self.d_setMovie(avId, NPCToons.HEALER_MOVIE_NO_MONEY)
                else:
                    self.d_setMovie(avId, NPCToons.HEALER_MOVIE_SAD)
            else:
                self.d_setMovie(avId, NPCToons.HEALER_MOVIE_CANCEL)
        self.sendClearMovie(None)

    def __handleUnexpectedExit(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' has exited unexpectedly')
        self.sendClearMovie(None)
