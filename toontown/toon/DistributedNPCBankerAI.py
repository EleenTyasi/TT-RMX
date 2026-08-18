from direct.task import Task
from direct.distributed import ClockDelta
from toontown.toonbase import TTLocalizer, ToontownGlobals
from toontown.toon import NPCToons
from .DistributedNPCToonBaseAI import DistributedNPCToonBaseAI

class DistributedNPCBankerAI(DistributedNPCToonBaseAI):

    def __init__(self, air, npcId):
        DistributedNPCToonBaseAI.__init__(self, air, npcId)
        self.givesQuests = 0
        self.busy = 0
        self.spawnX = 0.0
        self.spawnY = 0.0
        self.spawnZ = 0.0
        self.spawnH = 0.0

    def setSpawnPos(self, x, y, z, h):
        self.spawnX = x
        self.spawnY = y
        self.spawnZ = z
        self.spawnH = h

    def getSpawnPos(self):
        return (self.spawnX, self.spawnY, self.spawnZ, self.spawnH)

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
        self.busy = avId
        self.acceptOnce(self.air.getAvatarExitEvent(avId), self.__handleUnexpectedExit, extraArgs=[avId])
        self.d_setMovie(avId, NPCToons.BANKER_MOVIE_GUI)
        taskMgr.doMethodLater(60.0, self.sendTimeoutMovie, self.uniqueName('clearMovie'))
        DistributedNPCToonBaseAI.avatarEnter(self)

    def d_setMovie(self, avId, flag):
        self.sendUpdate('setMovie', [flag,
         self.npcId,
         avId,
         ClockDelta.globalClockDelta.getRealNetworkTime()])

    def sendTimeoutMovie(self, task):
        self.d_setMovie(self.busy, NPCToons.BANKER_MOVIE_TIMEOUT)
        self.sendClearMovie(None)
        return Task.done

    def sendClearMovie(self, task):
        self.ignore(self.air.getAvatarExitEvent(self.busy))
        taskMgr.remove(self.uniqueName('clearMovie'))
        self.busy = 0
        self.d_setMovie(0, NPCToons.BANKER_MOVIE_CLEAR)
        return Task.done

    def transferMoney(self, amount):
        avId = self.air.getAvatarIdFromSender()
        if self.busy != avId:
            self.air.writeServerEvent('suspicious', avId, 'DistributedNPCBankerAI.transferMoney busy with %s' % self.busy)
            self.notify.warning('somebody called transferMoney that I was not busy with! avId: %s' % avId)
            return
        av = simbase.air.doId2do.get(avId)
        if av:
            bankMoney = av.getBankMoney()
            money = av.getMoney()
            maxMoney = av.getMaxMoney()
            maxBankMoney = av.getMaxBankMoney()

            if amount < 0:
                # Withdraw from bank into pocket
                withdrawAmount = -amount
                if withdrawAmount <= bankMoney and (money + withdrawAmount) <= maxMoney:
                    av.b_setMoney(money + withdrawAmount)
                    av.b_setBankMoney(bankMoney - withdrawAmount)
                    self.d_setMovie(avId, NPCToons.BANKER_MOVIE_TRANSDONE)
                else:
                    self.d_setMovie(avId, NPCToons.BANKER_MOVIE_CANCEL)
            elif amount > 0:
                # Deposit from pocket into bank
                depositAmount = amount
                if depositAmount <= money and (bankMoney + depositAmount) <= maxBankMoney:
                    av.b_setMoney(money - depositAmount)
                    av.b_setBankMoney(bankMoney + depositAmount)
                    self.d_setMovie(avId, NPCToons.BANKER_MOVIE_TRANSDONE)
                else:
                    self.d_setMovie(avId, NPCToons.BANKER_MOVIE_CANCEL)
            else:
                self.d_setMovie(avId, NPCToons.BANKER_MOVIE_CANCEL)
        self.sendClearMovie(None)

    def __handleUnexpectedExit(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' has exited unexpectedly')
        self.sendClearMovie(None)
