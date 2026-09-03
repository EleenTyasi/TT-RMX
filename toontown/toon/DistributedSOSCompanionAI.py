# =============================================================================
#  DistributedSOSCompanionAI.py  —  Autonomous SOS AI Companion Toon
#  TT-RMX Personal Tinkering Project
# =============================================================================

import random
from direct.directnotify import DirectNotifyGlobal
from direct.task import Task
from toontown.toon.DistributedNPCToonBaseAI import DistributedNPCToonBaseAI
from toontown.toon import ToonDNA
from toontown.toonbase import ToontownBattleGlobals
from toontown.toonbase.ToontownBattleGlobals import *
from toontown.battle.BattleBase import *

class CompanionExperience:
    def getExp(self, track):
        return 500

    def getExpLevel(self, track):
        return 6

    def getExpVal(self, track):
        return 500

    def getCurrentTotalExp(self):
        return 3500

    def getNextExpValue(self, track, curSkill):
        return 10000

class CompanionInventory:
    def zeroInv(self, *args, **kwargs):
        pass
    def getTrackAndLevel(self, *args, **kwargs):
        return (0, 0)
    def useItem(self, *args, **kwargs):
        return 0
    def addItem(self, *args, **kwargs):
        return 0
    def makeNetString(self, *args, **kwargs):
        return b''

class DistributedSOSCompanionAI(DistributedNPCToonBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSOSCompanionAI')

    def __init__(self, air, npcId, summonerId, maxHp=100, trinkets=None, preferredTracks=None, gags=None):
        DistributedNPCToonBaseAI.__init__(self, air, npcId)
        self.posIndex = 0
        self.isCompanion = True
        self.npcId = npcId
        self.summonerId = summonerId
        self.turnsRemaining = 5
        self.maxHp = maxHp
        self.hp = maxHp
        self.trinketSlots = trinkets or [0, 0]
        self.preferredTracks = preferredTracks or [THROW_TRACK, SQUIRT_TRACK]
        self.companionGags = gags or {}
        self.experience = CompanionExperience()
        self.inventory = CompanionInventory()
        self.quests = []
        self.cogMerits = [0, 0, 0, 0]
        self.immortalMode = False
        self.hpOwnedByBattle = 0
        self.battleId = 0
        self.trackBonusLevel = [-1] * 7
        self._isDeparting = False

    def d_setInventory(self, *args, **kwargs):
        pass

    def isPlayerControlled(self):
        return False

    def getTrinketSlots(self):
        return self.trinketSlots

    def hasTrinketEquipped(self, trinketId):
        return trinketId in self.trinketSlots

    def d_setEarnedExperience(self, roundList):
        pass

    def stopToonUp(self):
        pass

    def toonUp(self, hp, *args, **kwargs):
        self.hp = min(self.maxHp, self.hp + hp)
        self.d_setHp(self.hp)

    def takeDamage(self, hp, *args, **kwargs):
        self.hp = max(0, self.hp - hp)
        self.d_setHp(self.hp)

    def getHp(self):
        return self.hp

    def setHp(self, hp):
        self.hp = hp

    def d_setHp(self, hp):
        self.sendUpdate('setHp', [hp])

    def b_setHp(self, hp):
        self.setHp(hp)
        self.d_setHp(hp)

    def getMaxHp(self):
        return self.maxHp

    def setMaxHp(self, maxHp):
        self.maxHp = maxHp

    def d_setMaxHp(self, maxHp):
        self.sendUpdate('setMaxHp', [maxHp])

    def b_setMaxHp(self, maxHp):
        self.setMaxHp(maxHp)
        self.d_setMaxHp(maxHp)

    def d_setTrinketSlots(self, t1, t2):
        self.sendUpdate('setTrinketSlots', [t1, t2])

    def setTrinketSlots(self, t1, t2):
        self.trinketSlots = [t1, t2]

    def b_setBattleId(self, battleId):
        self.battleId = battleId

    def d_setBattleId(self, battleId):
        pass

    def getBattleId(self):
        return self.battleId

    def setBattleId(self, battleId):
        self.battleId = battleId

    def getTrackBonusLevel(self, track=None):
        if track is None:
            return self.trackBonusLevel
        if 0 <= track < len(self.trackBonusLevel):
            return self.trackBonusLevel[track]
        return -1

    def setTrackBonusLevel(self, trackBonusLevelArray):
        self.trackBonusLevel = trackBonusLevelArray

    def checkGagBonus(self, track, level):
        from toontown.toon.TrinketsConfig import (
            TRINKET_ORGANIC_ALL, TRINKET_ORGANIC_TOONUP, TRINKET_ORGANIC_TRAP,
            TRINKET_ORGANIC_SOUND, TRINKET_ORGANIC_LURE, TRINKET_ORGANIC_THROW,
            TRINKET_ORGANIC_SQUIRT, TRINKET_ORGANIC_DROP
        )
        if self.hasTrinketEquipped(TRINKET_ORGANIC_ALL):
            return True
        track_trinket_map = {
            0: TRINKET_ORGANIC_TOONUP,
            1: TRINKET_ORGANIC_TRAP,
            2: TRINKET_ORGANIC_SOUND,
            3: TRINKET_ORGANIC_LURE,
            4: TRINKET_ORGANIC_THROW,
            5: TRINKET_ORGANIC_SQUIRT,
            6: TRINKET_ORGANIC_DROP,
        }
        if track in track_trinket_map and self.hasTrinketEquipped(track_trinket_map[track]):
            return True
        bonus = self.getTrackBonusLevel(track)
        return bonus >= level

    def addStat(self, *args, **kwargs):
        pass

    def getInstaKill(self):
        return False

    def getAlwaysHitSuits(self):
        return False

    def getPinkSlips(self):
        return 0

    def removePinkSlips(self, num):
        pass

    def depart(self, delay=3.0):
        """
        Executes portable hole teleport out animation and cleanly deletes after completion.
        """
        if getattr(self, '_isDeparting', False):
            return
        self._isDeparting = True
        try:
            self.b_setAnimState('TeleportOut', 1.0)
        except Exception:
            try:
                self.d_setAnimState('TeleportOut', 1.0)
            except Exception:
                pass
        taskMgr.doMethodLater(delay, self._doDelayedDelete, f'companion-depart-{self.doId}')

    def _doDelayedDelete(self, task):
        try:
            self.requestDelete()
        except Exception:
            pass
        return Task.done

    def chooseAction(self, battle):
        """
        Intelligently choose a combat action using BattleSim.
        """
        from toontown.battle.sim.BattleSim import BattleSim
        return BattleSim.choose_companion_action(self, battle)

    def decrementTurn(self):
        self.turnsRemaining -= 1
        return self.turnsRemaining
