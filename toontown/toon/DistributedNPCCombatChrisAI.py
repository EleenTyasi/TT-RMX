from direct.task.Task import Task
from direct.distributed import ClockDelta
from toontown.toonbase import TTLocalizer
from toontown.toon import NPCToons
from .DistributedNPCToonBaseAI import DistributedNPCToonBaseAI

class DistributedNPCCombatChrisAI(DistributedNPCToonBaseAI):

    def __init__(self, air, npcId):
        DistributedNPCToonBaseAI.__init__(self, air, npcId)
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
        self.notify.debug('avatarEnter: %d' % avId)
        av = self.air.doId2do.get(avId)
        if av is None:
            self.notify.warning('avatar %d not found' % avId)
            return
        if not self.busy:
            self.sendUpdate('setMovie', [NPCToons.COMBATCHRIS_MOVIE_START, avId, ClockDelta.globalClockDelta.getRealNetworkTime()])
            self.busy = avId
            taskMgr.doMethodLater(NPCToons.CLERK_COUNTDOWN_TIME, self.sendTimeoutMovie, self.uniqueName('clearMovie'))
        else:
            self.sendUpdate('setMovie', [NPCToons.COMBATCHRIS_MOVIE_CLEAR, avId, ClockDelta.globalClockDelta.getRealNetworkTime()])

    def sendTimeoutMovie(self, task):
        self.notify.debug('sendTimeoutMovie')
        self.sendUpdate('setMovie', [NPCToons.COMBATCHRIS_MOVIE_TIMEOUT, self.busy, ClockDelta.globalClockDelta.getRealNetworkTime()])
        self.busy = 0
        return Task.done

    def setMovieDone(self):
        avId = self.air.getAvatarIdFromSender()
        if avId != self.busy:
            return
        taskMgr.remove(self.uniqueName('clearMovie'))
        self.sendUpdate('setMovie', [NPCToons.COMBATCHRIS_MOVIE_COMPLETE, avId, ClockDelta.globalClockDelta.getRealNetworkTime()])
        self.busy = 0
