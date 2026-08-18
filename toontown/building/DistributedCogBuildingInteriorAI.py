"""
DistributedCogBuildingInteriorAI.py

Server-side interior manager for the Cog Building mini-dungeon system.
Replaces the old DistributedSuitInteriorAI floor-elevator system for basic street
Cog Buildings ('suit' state). Field Offices (DistributedCogdoInteriorAI) are untouched.

Room geometry is loaded on the client side via the existing HQ LevelSpec files.
This class manages state, Cog generation, modifier application, and rewards.
"""
import copy
import random
import base64

from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI
from direct.fsm import ClassicFSM, State
from direct.task import Timer
from otp.ai.AIBaseGlobal import *
from toontown.battle import DistributedBattleBldgAI, BattleBase
from toontown.toonbase.ToontownBattleGlobals import getCreditMultiplier, getInvasionMultiplier
from toontown.building.ElevatorConstants import ElevatorData, ELEVATOR_NORMAL
from toontown.building import SuitBuildingGlobals, CogBuildingModifier
from toontown.building import SuitPlannerInteriorAI
from toontown.suit import DistributedSuitAI, SuitDNA
from toontown.coghq import MintRoomSpecs, CountryClubRoomSpecs
from toontown.coghq import LawbotOfficeRoomSpecs
from toontown.toon import NPCToons

# ---------------------------------------------------------------------------
# Room pools per department track.
# Each entry is a list of room IDs from the matching HQ spec registry.
# 's' Sellbot  -> uses Cashbot Mint middle rooms (Sellbot Factory is monolithic).
# 'c' Cashbot  -> Cashbot Mint middle rooms.
# 'l' Lawbot   -> Lawbot DA Office puzzle + battle rooms.
# 'b' Bossbot  -> Bossbot Country Club middle rooms.
# ---------------------------------------------------------------------------
_ROOM_POOLS = {
    's': list(MintRoomSpecs.CashbotMintMiddleRoomIDs),
    'c': list(MintRoomSpecs.CashbotMintMiddleRoomIDs),
    'l': list(LawbotOfficeRoomSpecs.LawbotOfficeMiddleRoomIDs),
    'b': list(CountryClubRoomSpecs.BossbotCountryClubMiddleRoomIDs),
}


class DistributedCogBuildingInteriorAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCogBuildingInteriorAI')

    def __init__(self, air, elevator):
        targetDClass = air.dclassesByName.get('DistributedSuitInteriorAI') or air.dclassesByName.get('DistributedSuitInterior')
        if targetDClass:
            air.dclassesByName['DistributedCogBuildingInteriorAI'] = targetDClass
            air.dclassesByName['DistributedCogBuildingInterior'] = targetDClass
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        if targetDClass:
            self.dclass = targetDClass
        self.extZoneId, self.zoneId = elevator.bldg.getExteriorAndInteriorZoneId()
        self.bldg = elevator.bldg
        self.elevator = elevator
        self.track = getattr(elevator.bldg, 'track', 'c')
        self.numRooms = max(1, elevator.bldg.numFloors)  # height = difficulty = room count
        self.modifier = getattr(elevator.bldg, 'buildingModifier', None) or             CogBuildingModifier.pick(self.track, elevator.bldg.difficulty)

        self.toonIds = copy.copy(elevator.seats)
        self.toons = [t for t in self.toonIds if t is not None]
        self.savedByMap = {}
        self.avatarExitEvents = []
        self.responses = {}

        # Room / battle state
        self.currentRoom = 0          # 0 .. numRooms-1 are traversal rooms; numRooms = boss
        self.roomSequence = []         # list of room IDs from the pool
        self.activeSuits = []
        self.reserveSuits = []
        self.suits = []
        self.joinedReserves = []
        self.suitsKilled = []
        self.suitsKilledPerFloor = []
        self.toonSkillPtsGained = {}
        self.toonExp = {}
        self.toonOrigQuests = {}
        self.toonItems = {}
        self.toonOrigMerits = {}
        self.toonMerits = {}
        self.toonParts = {}
        self.helpfulToons = []
        self.battle = None
        self.timer = Timer.Timer()
        self.ignoreResponses = 0
        self.ignoreElevatorDone = 0
        self.ignoreReserveJoinDone = 0

        # Build the room sequence
        self._buildRoomSequence()

        # Add toons
        for toonId in self.toonIds:
            if toonId is not None:
                self.__addToon(toonId)

        self.fsm = ClassicFSM.ClassicFSM(
            'DistributedCogBuildingInteriorAI',
            [
                State.State('WaitForAllToonsInside',
                    self.enterWaitForAllToonsInside, self.exitWaitForAllToonsInside,
                    ['Elevator']),
                State.State('Elevator',
                    self.enterElevator, self.exitElevator,
                    ['Battle']),
                State.State('Battle',
                    self.enterBattle, self.exitBattle,
                    ['ReservesJoining', 'BattleDone']),
                State.State('ReservesJoining',
                    self.enterReservesJoining, self.exitReservesJoining,
                    ['Battle']),
                State.State('BattleDone',
                    self.enterBattleDone, self.exitBattleDone,
                    ['Resting', 'Reward']),
                State.State('Resting',
                    self.enterResting, self.exitResting,
                    ['Elevator']),
                State.State('Reward',
                    self.enterReward, self.exitReward,
                    ['Off']),
                State.State('Off',
                    self.enterOff, self.exitOff,
                    ['WaitForAllToonsInside']),
            ],
            'Off', 'Off',
            onUndefTransition=ClassicFSM.ClassicFSM.ALLOW,
        )
        self.fsm.enterInitialState()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _buildRoomSequence(self):
        """Pick a random sequence of room IDs for this run, based on track."""
        pool = list(_ROOM_POOLS.get(self.track, _ROOM_POOLS['c']))
        random.shuffle(pool)
        self.roomSequence = pool[:self.numRooms]
        self.notify.debug('Room sequence for track %s: %s' % (self.track, self.roomSequence))

    def _getPlanner(self):
        """Return the SuitPlannerInteriorAI from the building."""
        return self.bldg.planner

    def _genRoomSuits(self, isBossRoom=False):
        """Generate suits for the current room via the building planner."""
        planner = self._getPlanner()
        floorIdx = min(self.currentRoom, planner.numFloors - 1)
        handles = planner.genFloorSuits(floorIdx)
        active = handles['activeSuits']
        reserve = handles['reserveSuits']

        # Apply whole-dungeon modifier
        CogBuildingModifier.apply([s for s in active], self.modifier, is_boss=isBossRoom)
        CogBuildingModifier.apply([info[0] for info in reserve], self.modifier, is_boss=False)

        # Boss room extras
        if isBossRoom:
            self._makeSupertypeBoss(active)
            if self.modifier.get('lockdown'):
                self._addLockdownGuard(active)

        # AMBUSH modifier: move reserves into active up to max capacity (4), rest stay as fast reserves
        if self.modifier.get('ambush') and not isBossRoom:
            while len(active) < 4 and len(reserve) > 0:
                active.append(reserve.pop(0)[0])

        # FRENZIED modifier: double join chance
        if self.modifier.get('frenzied') and not isBossRoom:
            reserve = [(suit, min(info[1] * 2, 100)) for suit, info in
                       ((i[0], i) for i in reserve)]

        return active, reserve

    def _makeSupertypeBoss(self, suits):
        """Mutate the highest-level suit in the list into a Supertype Building Manager."""
        if not suits:
            return
        boss = max(suits, key=lambda s: getattr(s, 'level', 0))
        boss.isSupertype = True
        boss.isV20 = True
        boss.isPrototype = True
        boss.isAlphatype = True
        boss.setSkeleRevives(1)
        boss.maxHP = max(1, boss.maxHP * 2)
        boss.currHP = boss.maxHP
        if hasattr(boss, 'setVariantFlags'):
            boss.setVariantFlags(1, 1, 1)

    def _addLockdownGuard(self, suits):
        """Spawn one extra elite guard Cog for the LOCKDOWN modifier."""
        try:
            dna = SuitDNA.SuitDNA()
            dna.newSuitRandom(track=self.track)
            guard = DistributedSuitAI.DistributedSuitAI(simbase.air, None)
            guard.dna = dna
            guard.setLevel(min(12, self.bldg.difficulty + 6))
            guard.generateWithRequired(self.zoneId)
            suits.append(guard)
        except Exception as e:
            self.notify.warning('_addLockdownGuard failed: %s' % e)

    def __addToon(self, toonId):
        if toonId not in self.air.doId2do:
            return
        event = self.air.getAvatarExitEvent(toonId)
        self.avatarExitEvents.append(event)
        self.accept(event, self.__handleUnexpectedExit, extraArgs=[toonId])
        if toonId not in self.toons:
            self.toons.append(toonId)
        self.responses[toonId] = 0

    def __removeToon(self, toonId):
        if toonId in self.toons:
            self.toons.remove(toonId)
        if toonId in self.toonIds:
            idx = self.toonIds.index(toonId)
            self.toonIds[idx] = None
        self.responses.pop(toonId, None)
        event = self.air.getAvatarExitEvent(toonId)
        if event in self.avatarExitEvents:
            self.avatarExitEvents.remove(event)
        self.ignore(event)

    def __resetResponses(self):
        self.responses = {toon: 0 for toon in self.toons}
        self.ignoreResponses = 0

    def __allToonsResponded(self):
        if all(self.responses.get(t, 0) > 0 for t in self.toons):
            self.ignoreResponses = 1
            return True
        return False

    def __handleUnexpectedExit(self, toonId):
        self.notify.warning('toon %d exited unexpectedly' % toonId)
        self.__removeToon(toonId)
        if not self.toons:
            self.timer.stop()
            if self.battle is None:
                self.bldg.deleteSuitInterior()

    # ------------------------------------------------------------------
    # DistributedObject
    # ------------------------------------------------------------------

    def delete(self):
        self.ignoreAll()
        self.toons = []
        self.toonIds = []
        self.fsm.requestFinalState()
        del self.fsm
        del self.bldg
        del self.elevator
        self.timer.stop()
        del self.timer
        self.__cleanupBattle()
        taskMgr.remove(self.taskName('deleteInterior'))
        DistributedObjectAI.DistributedObjectAI.delete(self)

    # ------------------------------------------------------------------
    # Network getters
    # ------------------------------------------------------------------

    def getZoneId(self):
        return self.zoneId

    def getExtZoneId(self):
        return self.extZoneId

    def getDistBldgDoId(self):
        return self.bldg.getDoId()

    def getNumFloors(self):
        return self.numRooms

    def getNumRooms(self):
        return self.numRooms

    def getCurrentRoom(self):
        return self.currentRoom

    def getRoomSequence(self):
        return self.roomSequence

    def getModifierKey(self):
        return self.modifier.get('key', 'STANDARD')

    def getTrack(self):
        return self.track

    def getToons(self):
        return [[t if t is not None else 0 for t in self.toonIds], 0]

    def d_setToons(self):
        self.sendUpdate('setToons', self.getToons())

    def getSuits(self):
        activeIds = [s.doId for s in self.activeSuits]
        reserveIds = [i[0].doId for i in self.reserveSuits]
        values = [i[1] for i in self.reserveSuits]
        return [activeIds, reserveIds, values]

    def d_setSuits(self):
        self.sendUpdate('setSuits', self.getSuits())

    def b_setState(self, state):
        from direct.distributed.ClockDelta import globalClockDelta
        stime = globalClock.getRealTime() + BattleBase.SERVER_BUFFER_TIME
        self.sendUpdate('setState', [state, globalClockDelta.localToNetworkTime(stime)])
        self.fsm.request(state)

    def getState(self):
        from direct.distributed.ClockDelta import globalClockDelta
        return [self.fsm.getCurrentState().getName(), globalClockDelta.getRealNetworkTime()]

    def getBuildingModifier(self):
        key = self.modifier.get('key', 'STANDARD') if self.modifier else 'STANDARD'
        label = self.modifier.get('label', 'Standard Operation') if self.modifier else 'Standard Operation'
        desc = self.modifier.get('desc', 'No special conditions in effect.') if self.modifier else 'No special conditions in effect.'
        return [key, label, desc]

    def d_setBuildingModifier(self):
        self.sendUpdate('setBuildingModifier', self.getBuildingModifier())

    def setAvatarJoined(self):
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.toons:
            return
        self.d_setBuildingModifier()
        avatar = self.air.doId2do.get(avId)
        if avatar:
            self.savedByMap[avId] = (
                avatar.getName(),
                base64.b64encode(avatar.dna.makeNetString()).decode(),
                avatar.isGM(),
            )
        self.responses[avId] = self.responses.get(avId, 0) + 1
        if self.__allToonsResponded():
            self.fsm.request('Elevator')

    def elevatorDone(self):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreResponses or toonId not in self.toons:
            return
        if self.fsm.getCurrentState().getName() != 'Elevator':
            return
        self.responses[toonId] = self.responses.get(toonId, 0) + 1
        if self.__allToonsResponded() and not self.ignoreElevatorDone:
            self.b_setState('Battle')

    def reserveJoinDone(self):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreResponses or toonId not in self.toons:
            return
        if self.fsm.getCurrentState().getName() != 'ReservesJoining':
            return
        self.responses[toonId] = self.responses.get(toonId, 0) + 1
        if self.__allToonsResponded() and not self.ignoreReserveJoinDone:
            self.b_setState('Battle')

    # ------------------------------------------------------------------
    # Battle management
    # ------------------------------------------------------------------

    def __createFloorBattle(self):
        isBossRoom = (self.currentRoom == self.numRooms)
        bossBattle = 1 if isBossRoom else 0
        self.battle = DistributedBattleBldgAI.DistributedBattleBldgAI(
            self.air, self.zoneId,
            self.__handleRoundDone, self.__handleBattleDone,
            bossBattle=bossBattle,
        )
        self.battle.suitsKilled = self.suitsKilled
        self.battle.suitsKilledPerFloor = self.suitsKilledPerFloor
        self.battle.battleCalc.toonSkillPtsGained = self.toonSkillPtsGained
        self.battle.toonExp = self.toonExp
        self.battle.toonOrigQuests = self.toonOrigQuests
        self.battle.toonItems = self.toonItems
        self.battle.toonOrigMerits = self.toonOrigMerits
        self.battle.toonMerits = self.toonMerits
        self.battle.toonParts = self.toonParts
        self.battle.helpfulToons = self.helpfulToons
        self.battle.setInitialMembers(self.toons, self.suits)
        self.battle.generateWithRequired(self.zoneId)
        mult = getCreditMultiplier(self.currentRoom)
        if self.air.suitInvasionManager.getInvading():
            mult *= getInvasionMultiplier()
        self.battle.battleCalc.setSkillCreditMultiplier(mult)

    def __cleanupBattle(self):
        for suit in self.suits:
            if not suit.isDeleted():
                suit.requestDelete()
        self.suits = []
        self.reserveSuits = []
        self.activeSuits = []
        if self.battle is not None:
            self.battle.requestDelete()
        self.battle = None

    def __handleRoundDone(self, toonIds, totalHp, deadSuits):
        totalMaxHp = sum(s.maxHP for s in self.suits)
        for suit in deadSuits:
            if suit in self.activeSuits:
                self.activeSuits.remove(suit)

        if self.reserveSuits and len(self.activeSuits) < 4:
            self.joinedReserves = []
            hpPercent = 100 - (totalHp / totalMaxHp * 100.0) if totalMaxHp else 100
            for info in list(self.reserveSuits):
                if info[1] <= hpPercent and len(self.activeSuits) < 4:
                    self.suits.append(info[0])
                    self.activeSuits.append(info[0])
                    self.joinedReserves.append(info)
            for info in self.joinedReserves:
                self.reserveSuits.remove(info)
            if self.joinedReserves:
                self.fsm.request('ReservesJoining')
                self.d_setSuits()
                return

        if not self.activeSuits:
            self.fsm.request('BattleDone', [toonIds])
        else:
            self.battle.resume()

    def __handleBattleDone(self, zoneId, toonIds):
        if not toonIds:
            taskMgr.doMethodLater(10, self.__doDeleteInterior,
                                  self.taskName('deleteInterior'))
        elif self.currentRoom == self.numRooms:
            self.fsm.request('Reward')
        else:
            self.b_setState('Resting')

    def __doDeleteInterior(self, task):
        self.bldg.deleteSuitInterior()
        return task.done

    # ------------------------------------------------------------------
    # FSM states
    # ------------------------------------------------------------------

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterWaitForAllToonsInside(self):
        self.__resetResponses()
        announcement = CogBuildingModifier.get_announcement(self.modifier)
        if announcement:
            for toonId in self.toons:
                toon = self.air.doId2do.get(toonId)
                if toon and hasattr(toon, 'd_setSystemMessage'):
                    toon.d_setSystemMessage(0, announcement)

    def exitWaitForAllToonsInside(self):
        self.__resetResponses()

    def enterElevator(self):
        isBossRoom = (self.currentRoom == self.numRooms)
        active, reserve = self._genRoomSuits(isBossRoom=isBossRoom)
        self.suits = active
        self.activeSuits = list(active)
        self.reserveSuits = reserve
        self.d_setToons()
        self.d_setSuits()
        self.__resetResponses()
        from direct.distributed.ClockDelta import globalClockDelta
        stime = globalClock.getRealTime() + BattleBase.SERVER_BUFFER_TIME
        self.sendUpdate('setState', ['Elevator', globalClockDelta.localToNetworkTime(stime)])
        self.timer.startCallback(
            BattleBase.ELEVATOR_T + ElevatorData[ELEVATOR_NORMAL]['openTime'] +
            BattleBase.SERVER_BUFFER_TIME,
            self.__serverElevatorDone,
        )

    def __serverElevatorDone(self):
        self.ignoreElevatorDone = 1
        self.b_setState('Battle')

    def exitElevator(self):
        self.timer.stop()
        self.__resetResponses()

    def enterBattle(self):
        if self.battle is None:
            self.__createFloorBattle()
            self.elevator.d_setFloor(self.currentRoom)

    def exitBattle(self):
        pass

    def enterReservesJoining(self):
        self.__resetResponses()
        self.timer.startCallback(
            ElevatorData[ELEVATOR_NORMAL]['openTime'] +
            SuitBuildingGlobals.SUIT_HOLD_ELEVATOR_TIME +
            BattleBase.SERVER_BUFFER_TIME,
            self.__serverReserveJoinDone,
        )

    def __serverReserveJoinDone(self):
        self.ignoreReserveJoinDone = 1
        self.b_setState('Battle')

    def exitReservesJoining(self):
        self.timer.stop()
        self.__resetResponses()
        for info in self.joinedReserves:
            self.battle.suitRequestJoin(info[0])
        self.battle.resume()
        self.joinedReserves = []

    def enterBattleDone(self, toonIds):
        deadToons = [t for t in self.toons if t not in toonIds]
        for t in deadToons:
            self.__removeToon(t)
        self.d_setToons()
        if not self.toons:
            self.bldg.deleteSuitInterior()
            return
        isBossRoom = (self.currentRoom == self.numRooms)
        self.battle.resume(self.currentRoom, topFloor=1 if isBossRoom else 0)

    def exitBattleDone(self):
        self.__cleanupBattle()

    def enterResting(self):
        from toontown.building import DistributedElevatorIntAI
        self.intElevator = DistributedElevatorIntAI.DistributedElevatorIntAI(
            self.air, self, self.toons)
        self.intElevator.generateWithRequired(self.zoneId)

    def handleAllAboard(self, seats):
        if not hasattr(self, 'fsm'):
            return
        emptySeats = seats.count(None)
        if emptySeats == 4:
            self.bldg.deleteSuitInterior()
            return
        for toon in list(self.toons):
            if toon not in seats:
                self.__removeToon(toon)
        self.toonIds = copy.copy(seats)
        self.toons = [t for t in self.toonIds if t is not None]
        self.d_setToons()
        self.currentRoom += 1
        self.fsm.request('Elevator')

    def exitResting(self):
        if hasattr(self, 'intElevator'):
            self.intElevator.requestDelete()
            del self.intElevator

    def enterReward(self):
        victors = self.toonIds[:]
        savedBy = []
        height = self.numRooms
        difficulty = getattr(self.bldg, 'difficulty', 1)

        expReward = 150 * height
        beanReward = 100 * height

        if difficulty <= 2:
            sosCard = NPCToons.npcFriendsMinMaxStars(0, 1)
        elif difficulty <= 4:
            sosCard = NPCToons.npcFriendsMinMaxStars(1, 1)
        else:
            sosCard = NPCToons.npcFriendsMinMaxStars(2, 2)
        sosCard = random.choice(sosCard) if sosCard else None
        sosChance = CogBuildingModifier.get_sos_chance(height, self.modifier)
        grantSos = (sosCard is not None) and (random.random() < sosChance)

        for v in victors:
            if v:
                toon = self.air.doId2do.get(v)
                if toon:
                    toon.addMoney(beanReward)
                    if hasattr(toon, 'addToonExp'):
                        toon.addToonExp(expReward)
                    msg = 'Building cleared! +%d Jellybeans, +%d Toon EXP!' % (
                        beanReward, expReward)
                    if grantSos:
                        if not toon.attemptAddNPCFriend(sosCard, numCalls=1):
                            self.notify.info('Could not add SOS card %s to toon %d' % (sosCard, v))
                        else:
                            msg += ' You found an SOS card!'
                    toon.d_setSystemMessage(0, msg)
            entry = self.savedByMap.get(v)
            if entry:
                savedBy.append([v, entry[0], entry[1], entry[2]])

        self.bldg.fsm.request('waitForVictors', [victors, savedBy])
        from direct.distributed.ClockDelta import globalClockDelta
        stime = globalClock.getRealTime() + BattleBase.SERVER_BUFFER_TIME
        self.sendUpdate('setState', ['Reward', globalClockDelta.localToNetworkTime(stime)])

    def exitReward(self):
        pass
