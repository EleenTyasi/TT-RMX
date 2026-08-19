from .BattleBase import *
from toontown.toonbase.ToontownBattleGlobals import *
import random
from toontown.suit import DistributedSuitBaseAI
from . import SuitBattleGlobals, BattleExperienceAI
from toontown.toon import NPCToons
from toontown.pets import PetTricks, DistributedPetProxyAI
from direct.showbase.PythonUtil import lerp
from .StatusEffectManager import StatusEffectManager
from .StatusEffectsConfig import GAG_TRACK_STATUS_EFFECTS, SUIT_ATTACK_STATUS_EFFECTS, TOON_BUFFS
from toontown.battle.GagsConfig import TOONUP_CAN_TARGET_SELF

class BattleCalculatorAI:
    AccuracyBonuses = [
     0, 20, 40, 60]
    DamageBonuses = [
     0, 20, 20, 20]
    AttackExpPerTrack = [
     0, 10, 20, 30, 40, 50, 60]
    NumRoundsLured = [
     2, 2, 3, 3, 4, 4, 15]
    TRAP_CONFLICT = -2
    APPLY_HEALTH_ADJUSTMENTS = 1
    TOONS_TAKE_NO_DAMAGE = 0
    CAP_HEALS = 1
    CLEAR_SUIT_ATTACKERS = 1
    SUITS_UNLURED_IMMEDIATELY = 1
    CLEAR_MULTIPLE_TRAPS = 0
    KBBONUS_LURED_FLAG = 0
    KBBONUS_TGT_LURED = 1
    notify = DirectNotifyGlobal.directNotify.newCategory('BattleCalculatorAI')
    toonsAlwaysHit = simbase.config.GetBool('toons-always-hit', 0)
    toonsAlwaysMiss = simbase.config.GetBool('toons-always-miss', 0)
    toonsAlways5050 = simbase.config.GetBool('toons-always-5050', 0)
    suitsAlwaysHit = simbase.config.GetBool('suits-always-hit', 0)
    suitsAlwaysMiss = simbase.config.GetBool('suits-always-miss', 0)
    immortalSuits = simbase.config.GetBool('immortal-suits', 0)
    propAndOrganicBonusStack = simbase.config.GetBool('prop-and-organic-bonus-stack', 0)

    def __init__(self, battle, tutorialFlag=0):
        self.battle = battle
        self.statusEffectMgr = StatusEffectManager()
        self.SuitAttackers = {}
        self.currentlyLuredSuits = {}
        self.successfulLures = {}
        self.toonAtkOrder = []
        self.toonHPAdjusts = {}
        self.toonSkillPtsGained = {}
        self.traps = {}
        self.npcTraps = {}
        self.blockingToons = set()
        self.secondWindUsed = set()
        self.suitAtkStats = {}
        self.__clearBonuses(hp=1)
        self.__clearBonuses(hp=0)
        self.delayedUnlures = []
        self.__skillCreditMultiplier = 1
        self.tutorialFlag = tutorialFlag
        self.trainTrapTriggered = False

    def setSkillCreditMultiplier(self, mult):
        self.__skillCreditMultiplier = mult

    def getSkillCreditMultiplier(self):
        return self.__skillCreditMultiplier

    def cleanup(self):
        self.battle = None
        return

    def __calcToonAtkHit(self, attackIndex, atkTargets):
        toon = self.battle.getToon(attackIndex)
        if len(atkTargets) == 0:
            return (0, 0)
        if toon.getInstaKill() or toon.getAlwaysHitSuits():
            return (1, 95)
        if self.tutorialFlag:
            return (1, 95)
        if self.toonsAlways5050:
            roll = random.randint(0, 99)
            if roll < 50:
                return (1, 95)
            else:
                return (0, 0)
        if self.toonsAlwaysHit:
            return (1, 95)
        elif self.toonsAlwaysMiss:
            return (0, 0)
        debug = self.notify.getDebug()
        attack = self.battle.toonAttacks[attackIndex]
        atkTrack, atkLevel = self.__getActualTrackLevel(attack)
        if atkTrack == NPCSOS:
            return (1, 95)
        if atkTrack == HEAL:
            return (1, 100)
        if atkTrack == FIRE:
            return (1, 95)
        if atkTrack == TRAP:
            if debug:
                self.notify.debug('Attack is a trap, so it hits regardless')
            attack[TOON_ACCBONUS_COL] = 0
            return (1, 100)
        elif atkTrack == DROP and attack[TOON_TRACK_COL] == NPCSOS:
            unluredSuits = 0
            for tgt in atkTargets:
                if not self.__suitIsLured(tgt.getDoId()):
                    unluredSuits = 1

            if unluredSuits == 0:
                attack[TOON_ACCBONUS_COL] = 1
                return (0, 0)
        elif atkTrack == DROP:
            from toontown.toon.TrinketsConfig import TRINKET_LURED_DROP
            has_lured_drop = toon and hasattr(toon, 'hasTrinketEquipped') and toon.hasTrinketEquipped(TRINKET_LURED_DROP)
            if not has_lured_drop:
                allLured = True
                for i in range(len(atkTargets)):
                    if self.__suitIsLured(atkTargets[i].getDoId()):
                        pass
                    else:
                        allLured = False

                if allLured:
                    attack[TOON_ACCBONUS_COL] = 1
                    return (0, 0)
        elif atkTrack == PETSOS:
            return self.__calculatePetTrickSuccess(attack)
        tgtDef = 0
        numLured = 0
        if atkTrack != HEAL:
            targetDefs = []
            for currTarget in atkTargets:
                thisSuitDef = self.__targetDefense(currTarget, atkTrack, atkLevel)
                targetDefs.append(thisSuitDef)
                if debug:
                    self.notify.debug('Examining suit def for toon attack: ' + str(thisSuitDef))
                tgtId = currTarget.getDoId()
                if self.__suitIsLured(tgtId) or (tgtId in self.successfulLures):
                    numLured += 1
            if targetDefs:
                tgtDef = min(targetDefs)

        trackExp = self.__toonTrackExp(attack[TOON_ID_COL], atkTrack)
        for currOtherAtk in self.toonAtkOrder:
            if currOtherAtk != attack[TOON_ID_COL]:
                nextAttack = self.battle.toonAttacks[currOtherAtk]
                nextAtkTrack = self.__getActualTrack(nextAttack)
                if atkTrack == nextAtkTrack and attack[TOON_TGT_COL] == nextAttack[TOON_TGT_COL]:
                    currTrackExp = self.__toonTrackExp(nextAttack[TOON_ID_COL], atkTrack)
                    if debug:
                        self.notify.debug('Examining toon track exp bonus: ' + str(currTrackExp))
                    trackExp = max(currTrackExp, trackExp)

        if debug:
            if atkTrack == HEAL:
                self.notify.debug('Toon attack is a heal, no target def used')
            else:
                self.notify.debug('Suit defense used for toon attack: ' + str(tgtDef))
            self.notify.debug('Toon track exp bonus used for toon attack: ' + str(trackExp))
        if attack[TOON_TRACK_COL] == NPCSOS:
            randChoice = 0
        else:
            randChoice = random.randint(0, 99)
        propAcc = AvPropAccuracy[atkTrack][atkLevel]
        if atkTrack == LURE:
            treebonus = self.__toonCheckGagBonus(attack[TOON_ID_COL], atkTrack, atkLevel)
            propBonus = self.__checkPropBonus(atkTrack)
            if self.propAndOrganicBonusStack:
                propAcc = 0
                if treebonus:
                    self.notify.debug('using organic bonus lure accuracy')
                    propAcc += AvLureBonusAccuracy[atkLevel]
                if propBonus:
                    self.notify.debug('using prop bonus lure accuracy')
                    propAcc += AvLureBonusAccuracy[atkLevel]
            elif treebonus or propBonus:
                self.notify.debug('using oragnic OR prop bonus lure accuracy')
        attackAcc = propAcc + trackExp + tgtDef + 40
        currAtk = self.toonAtkOrder.index(attackIndex)
        if currAtk > 0 and atkTrack != HEAL:
            prevAtkId = self.toonAtkOrder[currAtk - 1]
            prevAttack = self.battle.toonAttacks[prevAtkId]
            prevAtkTrack = self.__getActualTrack(prevAttack)
            lure = atkTrack == LURE and (not attackAffectsGroup(atkTrack, atkLevel, 
             attack[TOON_TRACK_COL]) and attack[TOON_TGT_COL] in self.successfulLures or attackAffectsGroup(atkTrack, atkLevel, attack[TOON_TRACK_COL]))
            if atkTrack == prevAtkTrack and (attack[TOON_TGT_COL] == prevAttack[TOON_TGT_COL] or lure):
                if prevAttack[TOON_ACCBONUS_COL] == 1:
                    if debug:
                        self.notify.debug('DODGE: Toon attack track dodged')
                elif prevAttack[TOON_ACCBONUS_COL] == 0:
                    if debug:
                        self.notify.debug('HIT: Toon attack track hit')
                attack[TOON_ACCBONUS_COL] = prevAttack[TOON_ACCBONUS_COL]
                return (not attack[TOON_ACCBONUS_COL], attackAcc)
        atkAccResult = attackAcc
        if debug:
            self.notify.debug('setting atkAccResult to %d' % atkAccResult)
        acc = attackAcc + self.__calcToonAccBonus(attackIndex)
        if atkTrack != LURE and atkTrack != HEAL:
            if atkTrack != DROP:
                if numLured > 0:
                    if debug:
                        self.notify.debug('target is lured, attack hits with 100% accuracy')
                    attack[TOON_ACCBONUS_COL] = 0
                    return (1, 100)
            elif numLured > 0:
                if debug:
                    self.notify.debug('target is lured, drop attack misses')
                attack[TOON_ACCBONUS_COL] = 1
                return (0, 0)
        minAccFloor = [5, 8, 10, 13, 15, 18, 20][min(max(0, atkLevel), 6)]
        if acc < minAccFloor:
            acc = minAccFloor
        if acc > MaxToonAcc:
            acc = MaxToonAcc
        hit = randChoice < acc
        toonName = toon.getName() if toon else "Toon"
        trackName = Tracks[atkTrack] if atkTrack < len(Tracks) else f"Track{atkTrack}"
        print(f"[COMBAT LOG] TOON ATTACK -> Toon: {toonName} | Track: {trackName} Lvl {atkLevel+1} | BaseAcc: {propAcc}% | AccDelta: {tgtDef:+d}% | FinalAcc: {acc}% | Roll: {randChoice} | Result: {'HIT' if hit else 'MISS'}")
        if hit:
            if debug:
                self.notify.debug('HIT: Toon attack rolled' + str(randChoice) + 'to hit with an accuracy of' + str(acc))
            attack[TOON_ACCBONUS_COL] = 0
        else:
            if debug:
                self.notify.debug('MISS: Toon attack rolled' + str(randChoice) + 'to hit with an accuracy of' + str(acc))
            attack[TOON_ACCBONUS_COL] = 1
        return (not attack[TOON_ACCBONUS_COL], atkAccResult)

    def __toonTrackExp(self, toonId, track):
        toon = self.battle.getToon(toonId)
        if toon != None:
            toonExpLvl = toon.experience.getExpLevel(track)
            exp = self.AttackExpPerTrack[toonExpLvl]
            if track == HEAL:
                exp = exp * 0.5
            self.notify.debug('Toon track exp: ' + str(toonExpLvl) + ' and resulting acc bonus: ' + str(exp))
            return exp
        else:
            return 0
        return

    def __toonCheckGagBonus(self, toonId, track, level):
        toon = self.battle.getToon(toonId)
        if toon != None:
            return toon.checkGagBonus(track, level)
        else:
            return False
        return

    def __checkPropBonus(self, track):
        result = False
        if self.battle.getInteractivePropTrackBonus() == track:
            result = True
        return result

    def __targetDefense(self, suit, atkTrack, atkLevel=0):
        if atkTrack == HEAL:
            return 0
        
        gagLevel = atkLevel + 1
        cogLevel = suit.getActualLevel() if hasattr(suit, 'getActualLevel') else (suit.getLevel() + 1)
        levelDiff = gagLevel - cogLevel

        if levelDiff > 0:
            mismatchMod = levelDiff * 5
        elif levelDiff <= -2:
            mismatchMod = (levelDiff + 1) * 10
        else:
            mismatchMod = 0

        statusDefMod = -self.statusEffectMgr.get_defense_mod(suit.doId)
        return mismatchMod + statusDefMod

    def __createToonTargetList(self, attackIndex):
        attack = self.battle.toonAttacks[attackIndex]
        atkTrack, atkLevel = self.__getActualTrackLevel(attack)
        targetList = []
        if atkTrack == NPCSOS:
            return targetList
        if not attackAffectsGroup(atkTrack, atkLevel, attack[TOON_TRACK_COL]):
            if atkTrack == HEAL:
                target = attack[TOON_TGT_COL]
            else:
                target = self.battle.findSuit(attack[TOON_TGT_COL])
            if target != None:
                targetList.append(target)
        else:
            if atkTrack == HEAL or atkTrack == PETSOS:
                for currToon in self.battle.activeToons:
                    targetList.append(currToon)

            else:
                targetList = self.battle.activeSuits
        return targetList

    def __prevAtkTrack(self, attackerId, toon=1):
        if toon:
            prevAtkIdx = self.toonAtkOrder.index(attackerId) - 1
            if prevAtkIdx >= 0:
                prevAttackerId = self.toonAtkOrder[prevAtkIdx]
                attack = self.battle.toonAttacks[prevAttackerId]
                return self.__getActualTrack(attack)
            else:
                return NO_ATTACK

    def getSuitTrapType(self, suitId):
        if suitId in self.traps:
            if self.traps[suitId][0] == self.TRAP_CONFLICT:
                return NO_TRAP
            else:
                return self.traps[suitId][0]
        else:
            return NO_TRAP

    def __suitTrapDamage(self, suitId):
        if suitId in self.traps:
            return self.traps[suitId][2]
        else:
            return 0

    def addTrainTrapForJoiningSuit(self, suitId):
        self.notify.debug('addTrainTrapForJoiningSuit suit=%d self.traps=%s' % (suitId, self.traps))
        trapInfoToUse = None
        for trapInfo in list(self.traps.values()):
            if trapInfo[0] == UBER_GAG_LEVEL_INDEX:
                trapInfoToUse = trapInfo
                break

        if trapInfoToUse:
            self.traps[suitId] = trapInfoToUse
        else:
            self.notify.warning('huh we did not find a train trap?')
        return

    def __addSuitGroupTrap(self, suitId, trapLvl, attackerId, allSuits, npcDamage=0):
        if npcDamage == 0:
            if suitId in self.traps:
                if self.traps[suitId][0] == self.TRAP_CONFLICT:
                    pass
                else:
                    self.traps[suitId][0] = self.TRAP_CONFLICT
                for suit in allSuits:
                    id = suit.doId
                    if id in self.traps:
                        self.traps[id][0] = self.TRAP_CONFLICT
                    else:
                        self.traps[id] = [
                         self.TRAP_CONFLICT, 0, 0]

            else:
                toon = self.battle.getToon(attackerId)
                organicBonus = toon.checkGagBonus(TRAP, trapLvl)
                propBonus = self.__checkPropBonus(TRAP)
                damage = getAvPropDamage(TRAP, trapLvl, toon.experience.getExp(TRAP), organicBonus, propBonus, self.propAndOrganicBonusStack)
                if self.itemIsCredit(TRAP, trapLvl):
                    self.traps[suitId] = [
                     trapLvl, attackerId, damage]
                else:
                    self.traps[suitId] = [trapLvl, 0, damage]
                self.notify.debug('calling __addLuredSuitsDelayed')
                self.__addLuredSuitsDelayed(attackerId, targetId=-1, ignoreDamageCheck=True)
        else:
            if suitId in self.traps:
                if self.traps[suitId][0] == self.TRAP_CONFLICT:
                    self.traps[suitId] = [
                     trapLvl, 0, npcDamage]
            else:
                if not self.__suitIsLured(suitId):
                    self.traps[suitId] = [
                     trapLvl, 0, npcDamage]

    def __addSuitTrap(self, suitId, trapLvl, attackerId, npcDamage=0):
        if npcDamage == 0:
            if suitId in self.traps:
                if self.traps[suitId][0] == self.TRAP_CONFLICT:
                    pass
                else:
                    self.traps[suitId][0] = self.TRAP_CONFLICT
            else:
                toon = self.battle.getToon(attackerId)
                organicBonus = toon.checkGagBonus(TRAP, trapLvl)
                propBonus = self.__checkPropBonus(TRAP)
                damage = getAvPropDamage(TRAP, trapLvl, toon.experience.getExp(TRAP), organicBonus, propBonus, self.propAndOrganicBonusStack)
                if self.itemIsCredit(TRAP, trapLvl):
                    self.traps[suitId] = [
                     trapLvl, attackerId, damage]
                else:
                    self.traps[suitId] = [trapLvl, 0, damage]
        else:
            if suitId in self.traps:
                if self.traps[suitId][0] == self.TRAP_CONFLICT:
                    self.traps[suitId] = [
                     trapLvl, 0, npcDamage]
            else:
                if not self.__suitIsLured(suitId):
                    self.traps[suitId] = [
                     trapLvl, 0, npcDamage]

    def __removeSuitTrap(self, suitId):
        if suitId in self.traps:
            del self.traps[suitId]

    def __clearTrapCreator(self, creatorId, suitId=None):
        if suitId == None:
            for currTrap in list(self.traps.keys()):
                if creatorId == self.traps[currTrap][1]:
                    self.traps[currTrap][1] = 0

        elif suitId in self.traps:
            self.traps[suitId][1] = 0
        return

    def __trapCreator(self, suitId):
        if suitId in self.traps:
            return self.traps[suitId][1]
        else:
            return 0

    def __initTraps(self):
        self.trainTrapTriggered = False
        keysList = list(self.traps.keys())
        for currTrap in keysList:
            if self.traps[currTrap][0] == self.TRAP_CONFLICT:
                del self.traps[currTrap]

    def __calcToonAtkHp(self, toonId):
        attack = self.battle.toonAttacks[toonId]
        targetList = self.__createToonTargetList(toonId)
        atkHit, atkAcc = self.__calcToonAtkHit(toonId, targetList)
        atkTrack, atkLevel, atkHp = self.__getActualTrackLevelHp(attack)
        if not atkHit and atkTrack != HEAL:
            return
        validTargetAvail = 0
        lureDidDamage = 0
        currLureId = -1
        for currTarget in range(len(targetList)):
            attackLevel = -1
            attackTrack = None
            attackDamage = 0
            toonTarget = 0
            targetLured = 0
            if atkTrack == HEAL or atkTrack == PETSOS:
                targetId = targetList[currTarget]
                toonTarget = 1
            else:
                targetId = targetList[currTarget].getDoId()
            if atkTrack == LURE:
                if self.getSuitTrapType(targetId) == NO_TRAP:
                    if self.notify.getDebug():
                        self.notify.debug('Suit lured, but no trap exists')
                    if self.SUITS_UNLURED_IMMEDIATELY:
                        if not self.__suitIsLured(targetId, prevRound=1):
                            if not self.__combatantDead(targetId, toon=toonTarget):
                                validTargetAvail = 1
                            rounds = self.NumRoundsLured[atkLevel]
                            wakeupChance = 100 - atkAcc * 2
                            npcLurer = attack[TOON_TRACK_COL] == NPCSOS
                            currLureId = self.__addLuredSuitInfo(targetId, -1, rounds, wakeupChance, toonId, atkLevel, lureId=currLureId, npc=npcLurer)
                            if self.notify.getDebug():
                                self.notify.debug('Suit lured for ' + str(rounds) + ' rounds max with ' + str(wakeupChance) + '% chance to wake up each round')
                            targetLured = 1
                else:
                    attackTrack = TRAP
                    if targetId in self.traps:
                        trapInfo = self.traps[targetId]
                        attackLevel = trapInfo[0]
                        trap_damage = trapInfo[2]
                        if trap_damage > 0:
                            poison_cfg = {
                                'effect': 'POISON',
                                'rounds': 3,
                                'damage_per_round': trap_damage
                            }
                            self.statusEffectMgr.apply_effect(targetId, 'POISON', 3, poison_cfg)
                    else:
                        attackLevel = NO_TRAP
                    attackDamage = self.__suitTrapDamage(targetId)
                    trapCreatorId = self.__trapCreator(targetId)
                    if trapCreatorId > 0:
                        self.notify.debug('Giving trap EXP to toon ' + str(trapCreatorId))
                        self.__addAttackExp(attack, track=TRAP, level=attackLevel, attackerId=trapCreatorId)
                    self.__clearTrapCreator(trapCreatorId, targetId)
                    lureDidDamage = 1
                    if self.notify.getDebug():
                        self.notify.debug('Suit lured right onto a trap! (' + str(AvProps[attackTrack][attackLevel]) + ',' + str(attackLevel) + ')')
                    if not self.__combatantDead(targetId, toon=toonTarget):
                        validTargetAvail = 1
                    targetLured = 1
                if not self.SUITS_UNLURED_IMMEDIATELY:
                    if not self.__suitIsLured(targetId, prevRound=1):
                        if not self.__combatantDead(targetId, toon=toonTarget):
                            validTargetAvail = 1
                        rounds = self.NumRoundsLured[atkLevel]
                        wakeupChance = 100 - atkAcc * 2
                        npcLurer = attack[TOON_TRACK_COL] == NPCSOS
                        currLureId = self.__addLuredSuitInfo(targetId, -1, rounds, wakeupChance, toonId, atkLevel, lureId=currLureId, npc=npcLurer)
                        if self.notify.getDebug():
                            self.notify.debug('Suit lured for ' + str(rounds) + ' rounds max with ' + str(wakeupChance) + '% chance to wake up each round')
                        targetLured = 1
                    if attackLevel != -1:
                        self.__addLuredSuitsDelayed(toonId, targetId)
                if targetLured and (targetId not in self.successfulLures or targetId in self.successfulLures and self.successfulLures[targetId][1] < atkLevel):
                    self.notify.debug('Adding target ' + str(targetId) + ' to successfulLures list')
                    self.successfulLures[targetId] = [
                     toonId, atkLevel, atkAcc, -1]
            else:
                if atkTrack == TRAP:
                    npcDamage = 0
                    if attack[TOON_TRACK_COL] == NPCSOS:
                        npcDamage = atkHp
                    if self.CLEAR_MULTIPLE_TRAPS:
                        if self.getSuitTrapType(targetId) != NO_TRAP:
                            self.__clearAttack(toonId)
                            return
                    if atkLevel == UBER_GAG_LEVEL_INDEX:
                        self.__addSuitGroupTrap(targetId, atkLevel, toonId, targetList, npcDamage)
                        if self.__suitIsLured(targetId):
                            self.notify.debug('Train Trap on lured suit %d, \n indicating with KBBONUS_COL flag' % targetId)
                            tgtPos = self.battle.activeSuits.index(targetList[currTarget])
                            attack[TOON_KBBONUS_COL][tgtPos] = self.KBBONUS_LURED_FLAG
                    else:
                        self.__addSuitTrap(targetId, atkLevel, toonId, npcDamage)
                elif self.__suitIsLured(targetId) and atkTrack == SOUND:
                    self.notify.debug('Sound on lured suit, ' + 'indicating with KBBONUS_COL flag')
                    tgtPos = self.battle.activeSuits.index(targetList[currTarget])
                    attack[TOON_KBBONUS_COL][tgtPos] = self.KBBONUS_LURED_FLAG
                attackLevel = atkLevel
                attackTrack = atkTrack
                toon = self.battle.getToon(toonId)
                if attack[TOON_TRACK_COL] == NPCSOS and lureDidDamage != 1 or attack[TOON_TRACK_COL] == PETSOS:
                    attackDamage = atkHp
                elif atkTrack == FIRE:
                    suit = self.battle.findSuit(targetId)
                    if suit:
                        costToFire = 1
                        abilityToFire = toon.getPinkSlips()
                        toon.removePinkSlips(costToFire)
                        if costToFire > abilityToFire:
                            commentStr = 'Toon attempting to fire a %s cost cog with %s pinkslips' % (costToFire, abilityToFire)
                            simbase.air.writeServerEvent('suspicious', toonId, commentStr)
                            dislId = toon.DISLid
                            simbase.air.banManager.ban(toonId, dislId, commentStr)
                            print('Not enough PinkSlips to fire cog - print a warning here')
                        else:
                            suit.skeleRevives = 0
                            attackDamage = suit.getHP()
                    else:
                        attackDamage = 0
                else:
                    bonus = 0
                    from toontown.toon.TrinketsConfig import (
                        TRINKET_ORGANIC_TOONUP, TRINKET_ORGANIC_TRAP, TRINKET_ORGANIC_SOUND,
                        TRINKET_ORGANIC_LURE, TRINKET_ORGANIC_THROW, TRINKET_ORGANIC_SQUIRT,
                        TRINKET_ORGANIC_DROP
                    )
                    organicBonus = toon.checkGagBonus(attackTrack, attackLevel)
                    trinket_organic_map = {
                        0: TRINKET_ORGANIC_TOONUP,
                        1: TRINKET_ORGANIC_TRAP,
                        2: TRINKET_ORGANIC_SOUND,
                        3: TRINKET_ORGANIC_LURE,
                        4: TRINKET_ORGANIC_THROW,
                        5: TRINKET_ORGANIC_SQUIRT,
                        6: TRINKET_ORGANIC_DROP,
                    }
                    if attackTrack in trinket_organic_map and toon.hasTrinketEquipped(trinket_organic_map[attackTrack]):
                        organicBonus = 1
                    propBonus = self.__checkPropBonus(attackTrack)
                    attackDamage = getAvPropDamage(attackTrack, attackLevel, toon.experience.getExp(attackTrack), organicBonus, propBonus, self.propAndOrganicBonusStack)
                if not self.__combatantDead(targetId, toon=toonTarget):
                    if self.__suitIsLured(targetId) and atkTrack == DROP:
                        from toontown.toon.TrinketsConfig import TRINKET_LURED_DROP
                        if toon and hasattr(toon, 'hasTrinketEquipped') and toon.hasTrinketEquipped(TRINKET_LURED_DROP):
                            validTargetAvail = 1
                        else:
                            self.notify.debug('not setting validTargetAvail, since drop on a lured suit')
                    else:
                        validTargetAvail = 1
            if attackLevel == -1 and not atkTrack == FIRE:
                result = LURE_SUCCEEDED
            elif atkTrack != TRAP:
                toon = self.battle.getToon(toonId)
                if toon and toon.getInstaKill() and atkTrack != HEAL:
                    targetSuit = self.battle.findSuit(targetId)
                    for target in targetList:
                        if target.getHP() > targetSuit.getHP():
                            targetSuit = target
                    attackDamage = targetSuit.getHP()
                result = attackDamage
                if atkTrack == HEAL:
                    if not self.__attackHasHit(attack, suit=0):
                        result = result * 0.2
                    if self.notify.getDebug():
                        self.notify.debug('toon does ' + str(result) + ' healing to toon(s)')
                else:
                    if self.__suitIsLured(targetId) and atkTrack == DROP:
                        from toontown.toon.TrinketsConfig import TRINKET_LURED_DROP
                        if toon and hasattr(toon, 'hasTrinketEquipped') and toon.hasTrinketEquipped(TRINKET_LURED_DROP):
                            self.notify.debug('dealing drop damage on lured suit due to Lured Drop trinket')
                        else:
                            result = 0
                            self.notify.debug('setting damage to 0, since drop on a lured suit')
                    elif self.__suitIsLured(targetId) and atkTrack == SOUND:
                        from toontown.toon.TrinketsConfig import TRINKET_LOUDER_SOUND
                        if toon and hasattr(toon, 'hasTrinketEquipped') and toon.hasTrinketEquipped(TRINKET_LOUDER_SOUND):
                            result = int(round(result * 0.5))
                            self.notify.debug('Louder Sound dealing half damage on lured suit')
                    if self.notify.getDebug():
                        self.notify.debug('toon does ' + str(result) + ' damage to suit')
            else:
                result = 0
            if result != 0 or atkTrack == PETSOS:
                targets = self.__getToonTargets(attack)
                if targetList[currTarget] not in targets:
                    if self.notify.getDebug():
                        self.notify.debug('Target of toon is not accessible!')
                    continue
                targetIndex = targets.index(targetList[currTarget])
                if atkTrack == HEAL:
                    result = result / len(targetList)
                    if self.notify.getDebug():
                        self.notify.debug('Splitting heal among ' + str(len(targetList)) + ' targets')
                if result > 0:
                    import math
                    from toontown.battle.CritGlobals import roll_hit_type, HIT_TYPE_NAMES, HIT_NORMAL, HIT_CRITICAL, HIT_DIRECT, HIT_CRIT_DIRECT
                    hit_type, crit_mult = roll_hit_type(is_toon=True)
                    if toon and hasattr(toon, 'addStat'):
                        if hit_type == HIT_DIRECT:
                            toon.addStat(0, 1)
                        elif hit_type == HIT_CRITICAL:
                            toon.addStat(1, 1)
                        elif hit_type == HIT_CRIT_DIRECT:
                            toon.addStat(2, 1)

                        if atkTrack == THROW:
                            throwCalories = [150, 350, 500, 750, 1000, 2500, 6000]
                            if 0 <= attackLevel < len(throwCalories):
                                toon.addStat(3, throwCalories[attackLevel])

                        if atkTrack == HEAL:
                            toon.addStat(9, int(result))
                        else:
                            toon.addStat(7, int(result))

                    if hit_type != HIT_NORMAL:
                        result = max(result + 1, int(math.ceil(result * crit_mult)))

                    from toontown.toon.TrinketsConfig import (
                        TRINKET_DEF_UP_ATK_DOWN, TRINKET_GLASS_CANNON, TRINKET_DARING_DANGER,
                        TRINKET_RALLYING_TU, TRINKET_CLEANSING_TU, TRINKET_SHATTERING_FREEZING,
                        TRINKET_VAMPIRIC_GAGS, TRINKET_STATUS_CATALYST
                    )
                    if toon:
                        if toon.hasTrinketEquipped(TRINKET_DEF_UP_ATK_DOWN):
                            result = int(result * 0.85)
                        if toon.hasTrinketEquipped(TRINKET_GLASS_CANNON):
                            result = int(result * 1.25)
                        if toon.hasTrinketEquipped(TRINKET_DARING_DANGER) and (toon.hp / float(max(1, toon.maxHp)) <= 0.3):
                            result = int(result * 1.30)

                    if atkTrack != HEAL:
                        result = int(result * self.statusEffectMgr.get_damage_multiplier(targetId))
                    else:
                        if toon and toon.hasTrinketEquipped(TRINKET_RALLYING_TU):
                            self.statusEffectMgr.apply_effect(targetId, 'RALLIED', 2)
                        if toon and toon.hasTrinketEquipped(TRINKET_CLEANSING_TU):
                            for neg_eff in ['POISON', 'BURN', 'WEAKEN', 'SLOW', 'WET']:
                                self.statusEffectMgr.remove_effect(targetId, neg_eff)

                    if toon and toon.hasTrinketEquipped(TRINKET_VAMPIRIC_GAGS) and result > 0 and atkTrack != HEAL:
                        vamp_heal = max(1, int(result * 0.1))
                        toon.hp = min(toon.maxHp, toon.hp + vamp_heal)
                        self.notify.info('Vampiric Gags healed toon %d for %d HP' % (toonId, vamp_heal))

                    if atkTrack in GAG_TRACK_STATUS_EFFECTS:
                        eff_cfg = GAG_TRACK_STATUS_EFFECTS[atkTrack]
                        proc_chance = self.statusEffectMgr.calc_proc_chance(eff_cfg.get('chance', 100), atkLevel, HIT_TYPE_NAMES[hit_type])
                        # Wet + Freeze Synergy: Drenched Cogs freeze much more easily (+40% proc chance)
                        if eff_cfg.get('effect') == 'FREEZE' and self.statusEffectMgr.is_wet(targetId):
                            proc_chance = min(100, proc_chance + 40)
                            self.notify.info(f"Target suit {targetId} is WET! Freeze proc chance boosted to {proc_chance}%")
                        if random.randint(1, 100) <= proc_chance:
                            rounds = eff_cfg.get('rounds', 2)
                            if toon and toon.hasTrinketEquipped(TRINKET_STATUS_CATALYST):
                                rounds += 1
                            self.statusEffectMgr.apply_effect(targetId, eff_cfg['effect'], rounds, eff_cfg)
                            if atkTrack == HEAL:
                                self.statusEffectMgr.apply_effect(toonId, eff_cfg['effect'], rounds, eff_cfg)

                    # Pack hit_type (0-3) into bits 12-13 of TOON_HPBONUS_COL.
                    # Lower 12 bits remain available for the real hp bonus value later.
                    # Client unpacks: real_bonus = hpbonus & 0xFFF, crit_type = (hpbonus >> 12) & 0x3
                    existing_bonus = attack[TOON_HPBONUS_COL] & 0xFFF
                    attack[TOON_HPBONUS_COL] = existing_bonus | (hit_type << 12)
                if targetId in self.successfulLures and atkTrack == LURE:
                    self.notify.debug('Updating lure damage to ' + str(result))
                    self.successfulLures[targetId][3] = result
                else:
                    while len(attack[TOON_HP_COL]) <= targetIndex:
                        attack[TOON_HP_COL].append(0)
                    attack[TOON_HP_COL][targetIndex] = result
                if result > 0 and atkTrack != HEAL and atkTrack != DROP and atkTrack != PETSOS:
                    attackTrack = LURE
                    lureInfos = self.__getLuredExpInfo(targetId)
                    for currInfo in lureInfos:
                        if currInfo[3]:
                            self.notify.debug('Giving lure EXP to toon ' + str(currInfo[0]))
                            self.__addAttackExp(attack, track=attackTrack, level=currInfo[1], attackerId=currInfo[0])
                        self.__clearLurer(currInfo[0], lureId=currInfo[2])

        if lureDidDamage:
            if self.itemIsCredit(atkTrack, atkLevel):
                self.notify.debug('Giving lure EXP to toon ' + str(toonId))
                self.__addAttackExp(attack)
        if not validTargetAvail and self.__prevAtkTrack(toonId) != atkTrack:
            self.__clearAttack(toonId)
        return

    def __getToonTargets(self, attack):
        track = self.__getActualTrack(attack)
        if track == HEAL or track == PETSOS:
            return self.battle.activeToons
        else:
            return self.battle.activeSuits

    def __attackHasHit(self, attack, suit=0):
        if suit == 1:
            for dmg in attack[SUIT_HP_COL]:
                if dmg > 0:
                    return 1

            return 0
        else:
            track = self.__getActualTrack(attack)
            return not attack[TOON_ACCBONUS_COL] and track != NO_ATTACK

    def __attackDamage(self, attack, suit=0):
        if suit:
            for dmg in attack[SUIT_HP_COL]:
                if dmg > 0:
                    return dmg

            return 0
        else:
            for dmg in attack[TOON_HP_COL]:
                if dmg > 0:
                    return dmg

            return 0

    def __attackDamageForTgt(self, attack, tgtPos, suit=0):
        if suit:
            return attack[SUIT_HP_COL][tgtPos]
        else:
            return attack[TOON_HP_COL][tgtPos]

    def __calcToonAccBonus(self, attackKey):
        numPrevHits = 0
        attackIdx = self.toonAtkOrder.index(attackKey)
        for currPrevAtk in range(attackIdx - 1, -1, -1):
            attack = self.battle.toonAttacks[attackKey]
            atkTrack, atkLevel = self.__getActualTrackLevel(attack)
            prevAttackKey = self.toonAtkOrder[currPrevAtk]
            prevAttack = self.battle.toonAttacks[prevAttackKey]
            prvAtkTrack, prvAtkLevel = self.__getActualTrackLevel(prevAttack)
            if self.__attackHasHit(prevAttack) and (attackAffectsGroup(prvAtkTrack, prvAtkLevel, prevAttack[TOON_TRACK_COL]) or attackAffectsGroup(atkTrack, atkLevel, attack[TOON_TRACK_COL]) or attack[TOON_TGT_COL] == prevAttack[TOON_TGT_COL]) and atkTrack != prvAtkTrack:
                numPrevHits += 1

        if numPrevHits > 0 and self.notify.getDebug():
            self.notify.debug('ACC BONUS: toon attack received accuracy ' + 'bonus of ' + str(self.AccuracyBonuses[numPrevHits]) + ' from previous attack by (' + str(attack[TOON_ID_COL]) + ') which hit')
        return self.AccuracyBonuses[numPrevHits]

    def __applyToonAttackDamages(self, toonId, hpbonus = 0, kbbonus = 0):
        totalDamages = 0
        if not self.APPLY_HEALTH_ADJUSTMENTS:
            return totalDamages
        attack = self.battle.toonAttacks[toonId]
        track = self.__getActualTrack(attack)
        if track != NO_ATTACK and track != SOS and track != TRAP and track != NPCSOS:
            targets = self.__getToonTargets(attack)
            for position in range(len(targets)):
                if hpbonus:
                    if targets[position] in self.__createToonTargetList(toonId):
                        damageDone = attack[TOON_HPBONUS_COL] & 0xFFF
                    else:
                        damageDone = 0
                elif kbbonus:
                    if targets[position] in self.__createToonTargetList(toonId):
                        damageDone = attack[TOON_KBBONUS_COL][position]
                    else:
                        damageDone = 0
                else:
                    damageDone = attack[TOON_HP_COL][position]
                if damageDone <= 0 or self.immortalSuits:
                    continue
                if track == HEAL or track == PETSOS:
                    currTarget = targets[position]
                    if self.CAP_HEALS:
                        toonHp = self.__getToonHp(currTarget)
                        toonMaxHp = self.__getToonMaxHp(currTarget)
                        if toonHp + damageDone > toonMaxHp:
                            damageDone = toonMaxHp - toonHp
                            attack[TOON_HP_COL][position] = damageDone
                    self.toonHPAdjusts[currTarget] += damageDone
                    totalDamages = totalDamages + damageDone
                    continue
                currTarget = targets[position]
                prev_hp = currTarget.getHP()
                currTarget.setHP(prev_hp - damageDone)
                targetId = currTarget.getDoId()
                self.notify.info(f"Toon attack applied {damageDone} damage to suit {targetId} (HP: {prev_hp} -> {currTarget.getHP()})")
                totalDamages = totalDamages + damageDone

                if currTarget.getHP() <= 0:
                    # Ice Shatter: When a frozen cog dies and attacker has TRINKET_SHATTERING_FREEZING, deal 50% damage to adjacent Cogs
                    if self.statusEffectMgr.is_frozen(targetId):
                        toonObj = self.battle.getToon(toonId)
                        from toontown.toon.TrinketsConfig import TRINKET_SHATTERING_FREEZING
                        if toonObj and hasattr(toonObj, 'hasTrinketEquipped') and toonObj.hasTrinketEquipped(TRINKET_SHATTERING_FREEZING):
                            shatter_dmg = max(1, int(damageDone * 0.5))
                            self.notify.info(f"Shattering Freezing triggered on defeated suit {targetId}! Dealing {shatter_dmg} damage to adjacent suits.")
                            for adj_pos in [position - 1, position + 1]:
                                if 0 <= adj_pos < len(targets):
                                    adj_suit = targets[adj_pos]
                                    if adj_suit.getHP() > 0:
                                        adj_prev = adj_suit.getHP()
                                        adj_suit.setHP(adj_prev - shatter_dmg)
                                        self.notify.info(f"Shatter hit adjacent suit {adj_suit.doId} (HP: {adj_prev} -> {adj_suit.getHP()})")
                                        while len(attack[TOON_HP_COL]) <= adj_pos:
                                            attack[TOON_HP_COL].append(0)
                                        attack[TOON_HP_COL][adj_pos] += shatter_dmg
                                        totalDamages += shatter_dmg
                                        if adj_suit.getHP() <= 0:
                                            if adj_suit.getSkeleRevives() >= 1:
                                                adj_suit.useSkeleRevive()
                                                attack[SUIT_REVIVE_COL] |= (1 << adj_pos)
                                            else:
                                                self.suitLeftBattle(adj_suit.getDoId())
                                                attack[SUIT_DIED_COL] |= (1 << adj_pos)
                                                self.notify.debug('Adjacent Suit %d died to Ice Shatter!' % adj_suit.doId)

                    if currTarget.getSkeleRevives() >= 1:
                        currTarget.useSkeleRevive()
                        attack[SUIT_REVIVE_COL] = attack[SUIT_REVIVE_COL] | 1 << position
                    else:
                        self.suitLeftBattle(targetId)
                        attack[SUIT_DIED_COL] = attack[SUIT_DIED_COL] | 1 << position
                        if self.notify.getDebug():
                            self.notify.debug('Suit' + str(targetId) + 'bravely expired in combat')

        return totalDamages

    def __combatantDead(self, avId, toon):
        if toon:
            if self.__getToonHp(avId) <= 0:
                return 1
        else:
            suit = self.battle.findSuit(avId)
            if suit.getHP() <= 0:
                return 1
        return 0

    def __combatantJustRevived(self, avId):
        suit = self.battle.findSuit(avId)
        if suit.reviveCheckAndClear():
            return 1
        else:
            return 0

    def __addAttackExp(self, attack, track = -1, level = -1, attackerId = -1):
        trk = -1
        lvl = -1
        id = -1
        if attack:
            tgt = attack[TOON_TGT_COL]
            if tgt != -1 and tgt != None:
                if isinstance(tgt, list):
                    if any(getattr(s, 'isVirtual', False) for s in tgt if hasattr(s, 'isVirtual')):
                        return
                elif hasattr(tgt, 'isVirtual') and getattr(tgt, 'isVirtual', False):
                    return
        if track != -1 and level != -1 and attackerId != -1:
            trk = track
            lvl = level
            id = attackerId
        elif attack and self.__attackHasHit(attack):
            if self.notify.getDebug():
                self.notify.debug('Attack ' + repr(attack) + ' has hit')
            trk = attack[TOON_TRACK_COL]
            lvl = attack[TOON_LVL_COL]
            id = attack[TOON_ID_COL]
        if trk != -1 and trk != NPCSOS and trk != PETSOS and lvl != -1 and id != -1:
            expList = self.toonSkillPtsGained.get(id, None)
            if expList == None:
                expList = [0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0]
                self.toonSkillPtsGained[id] = expList
            expList[trk] = min(ExperienceCap, expList[trk] + (lvl + 1) * self.__skillCreditMultiplier)
        return

    def __clearTgtDied(self, tgt, lastAtk, currAtk):
        position = self.battle.activeSuits.index(tgt)
        currAtkTrack = self.__getActualTrack(currAtk)
        lastAtkTrack = self.__getActualTrack(lastAtk)
        if currAtkTrack == lastAtkTrack and lastAtk[SUIT_DIED_COL] & 1 << position and self.__attackHasHit(currAtk, suit=0):
            if self.notify.getDebug():
                self.notify.debug('Clearing suit died for ' + str(tgt.getDoId()) + ' at position ' + str(position) + ' from toon attack ' + str(lastAtk[TOON_ID_COL]) + ' and setting it for ' + str(currAtk[TOON_ID_COL]))
            lastAtk[SUIT_DIED_COL] = lastAtk[SUIT_DIED_COL] ^ 1 << position
            self.suitLeftBattle(tgt.getDoId())
            currAtk[SUIT_DIED_COL] = currAtk[SUIT_DIED_COL] | 1 << position

    def __addDmgToBonuses(self, dmg, attackIndex, hp=1):
        toonId = self.toonAtkOrder[attackIndex]
        attack = self.battle.toonAttacks[toonId]
        atkTrack = self.__getActualTrack(attack)
        if atkTrack == HEAL or atkTrack == PETSOS:
            return
        tgts = self.__createToonTargetList(toonId)
        for currTgt in tgts:
            tgtPos = self.battle.activeSuits.index(currTgt) # self.battle.suits.index(currTgt)
            attackerId = self.toonAtkOrder[attackIndex]
            attack = self.battle.toonAttacks[attackerId]
            track = self.__getActualTrack(attack)
            if hp:
                if track in self.hpBonuses[tgtPos]:
                    self.hpBonuses[tgtPos][track].append([attackIndex, dmg])
                else:
                    self.hpBonuses[tgtPos][track] = [
                     [
                      attackIndex, dmg]]
            elif self.__suitIsLured(currTgt.getDoId()):
                if track in self.kbBonuses[tgtPos]:
                    self.kbBonuses[tgtPos][track].append([attackIndex, dmg])
                else:
                    self.kbBonuses[tgtPos][track] = [
                     [
                      attackIndex, dmg]]

    def __clearBonuses(self, hp=1):
        if hp:
            self.hpBonuses = [{}, {}, {}, {}]
        else:
            self.kbBonuses = [{}, {}, {}, {}]

    def __bonusExists(self, tgtSuit, hp=1):
        tgtPos = self.activeSuits.index(tgtSuit)
        if hp:
            bonusLen = len(self.hpBonuses[tgtPos])
        else:
            bonusLen = len(self.kbBonuses[tgtPos])
        if bonusLen > 0:
            return 1
        return 0

    def __processBonuses(self, hp=1):
        if hp:
            bonusList = self.hpBonuses
            self.notify.debug('Processing hpBonuses: ' + repr(self.hpBonuses))
        else:
            bonusList = self.kbBonuses
            self.notify.debug('Processing kbBonuses: ' + repr(self.kbBonuses))
        tgtPos = 0
        for currTgt in bonusList:
            for currAtkType in list(currTgt.keys()):
                if len(currTgt[currAtkType]) > 1 or not hp and len(currTgt[currAtkType]) > 0:
                    totalDmgs = 0
                    for currDmg in currTgt[currAtkType]:
                        totalDmgs += currDmg[1]

                    numDmgs = len(currTgt[currAtkType])
                    attackIdx = currTgt[currAtkType][numDmgs - 1][0]
                    attackerId = self.toonAtkOrder[attackIdx]
                    attack = self.battle.toonAttacks[attackerId]
                    if hp:
                        raw_bonus = math.ceil(totalDmgs * (self.DamageBonuses[numDmgs - 1] * 0.01))
                        # Preserve upper bits (crit type packed in bits 12-13)
                        crit_bits = attack[TOON_HPBONUS_COL] & ~0xFFF
                        attack[TOON_HPBONUS_COL] = crit_bits | (int(raw_bonus) & 0xFFF)
                        if self.notify.getDebug():
                            self.notify.debug('Applying hp bonus to track ' + str(attack[TOON_TRACK_COL]) + ' of ' + str(raw_bonus))
                    elif len(attack[TOON_KBBONUS_COL]) > tgtPos:
                        attack[TOON_KBBONUS_COL][tgtPos] = totalDmgs * 0.5
                        if self.notify.getDebug():
                            self.notify.debug('Applying kb bonus to track ' + str(attack[TOON_TRACK_COL]) + ' of ' + str(attack[TOON_KBBONUS_COL][tgtPos]) + ' to target ' + str(tgtPos))
                    else:
                        self.notify.warning('invalid tgtPos for knock back bonus: %d' % tgtPos)

            tgtPos += 1

        if hp:
            self.__clearBonuses()
        else:
            self.__clearBonuses(hp=0)

    def __handleBonus(self, attackIdx, hp=1):
        attackerId = self.toonAtkOrder[attackIdx]
        attack = self.battle.toonAttacks[attackerId]
        atkDmg = self.__attackDamage(attack, suit=0)
        atkTrack = self.__getActualTrack(attack)
        if atkDmg > 0:
            if hp:
                if atkTrack != LURE:
                    self.notify.debug('Adding dmg of ' + str(atkDmg) + ' to hpBonuses list')
                    self.__addDmgToBonuses(atkDmg, attackIdx)
            elif self.__knockBackAtk(attackerId, toon=1):
                self.notify.debug('Adding dmg of ' + str(atkDmg) + ' to kbBonuses list')
                self.__addDmgToBonuses(atkDmg, attackIdx, hp=0)

    def __clearAttack(self, attackIdx, toon=1):
        if toon:
            if self.notify.getDebug():
                self.notify.debug('clearing out toon attack for toon ' + str(attackIdx) + '...')
            attack = self.battle.toonAttacks[attackIdx]
            self.battle.toonAttacks[attackIdx] = getToonAttack(attackIdx)
            longest = max(len(self.battle.activeToons), len(self.battle.activeSuits))
            taList = self.battle.toonAttacks
            for j in range(longest):
                taList[attackIdx][TOON_HP_COL].append(-1)
                taList[attackIdx][TOON_KBBONUS_COL].append(-1)

            if self.notify.getDebug():
                self.notify.debug('toon attack is now ' + repr(self.battle.toonAttacks[attackIdx]))
        else:
            self.notify.warning('__clearAttack not implemented for suits!')

    def __rememberToonAttack(self, suitId, toonId, damage):
        if suitId not in self.SuitAttackers:
            self.SuitAttackers[suitId] = {toonId: damage}
        else:
            if toonId not in self.SuitAttackers[suitId]:
                self.SuitAttackers[suitId][toonId] = damage
            else:
                if self.SuitAttackers[suitId][toonId] <= damage:
                    self.SuitAttackers[suitId] = [
                     toonId, damage]

    def __postProcessToonAttacks(self):
        self.notify.debug('__postProcessToonAttacks()')
        lastTrack = -1
        lastAttacks = []
        self.__clearBonuses()
        for currToonAttack in self.toonAtkOrder:
            if currToonAttack != -1:
                attack = self.battle.toonAttacks[currToonAttack]
                atkTrack, atkLevel = self.__getActualTrackLevel(attack)
                if atkTrack != HEAL and atkTrack != SOS and atkTrack != NO_ATTACK and atkTrack != NPCSOS and atkTrack != PETSOS:
                    targets = self.__createToonTargetList(currToonAttack)
                    allTargetsDead = 1
                    for currTgt in targets:
                        damageDone = self.__attackDamage(attack, suit=0)
                        if damageDone > 0:
                            self.__rememberToonAttack(currTgt.getDoId(), attack[TOON_ID_COL], damageDone)
                        if atkTrack == TRAP:
                            if currTgt.doId in self.traps:
                                trapInfo = self.traps[currTgt.doId]
                                currTgt.battleTrap = trapInfo[0]
                        targetDead = 0
                        if currTgt.getHP() > 0:
                            allTargetsDead = 0
                        else:
                            targetDead = 1
                            if atkTrack != LURE:
                                for currLastAtk in lastAttacks:
                                    self.__clearTgtDied(currTgt, currLastAtk, attack)

                        tgtId = currTgt.getDoId()
                        if tgtId in self.successfulLures and atkTrack == LURE:
                            lureInfo = self.successfulLures[tgtId]
                            self.notify.debug('applying lure data: ' + repr(lureInfo))
                            toonId = lureInfo[0]
                            lureAtk = self.battle.toonAttacks[toonId]
                            tgtPos = self.battle.activeSuits.index(currTgt)
                            if currTgt.doId in self.traps:
                                trapInfo = self.traps[currTgt.doId]
                                if trapInfo[0] == UBER_GAG_LEVEL_INDEX:
                                    self.notify.debug('train trap triggered for %d' % currTgt.doId)
                                    self.trainTrapTriggered = True
                            self.__removeSuitTrap(tgtId)
                            lureAtk[TOON_KBBONUS_COL][tgtPos] = self.KBBONUS_TGT_LURED
                            lureAtk[TOON_HP_COL][tgtPos] = lureInfo[3]
                        elif self.__suitIsLured(tgtId) and atkTrack == DROP:
                            self.notify.debug('Drop on lured suit, ' + 'indicating with KBBONUS_COL ' + 'flag')
                            tgtPos = self.battle.activeSuits.index(currTgt)
                            attack[TOON_KBBONUS_COL][tgtPos] = self.KBBONUS_LURED_FLAG
                        if targetDead and atkTrack != lastTrack:
                            tgtPos = self.battle.activeSuits.index(currTgt)
                            attack[TOON_HP_COL][tgtPos] = 0
                            attack[TOON_KBBONUS_COL][tgtPos] = -1

                    if allTargetsDead and atkTrack != lastTrack:
                        if self.notify.getDebug():
                            self.notify.debug('all targets of toon attack ' + str(currToonAttack) + ' are dead')
                        self.__clearAttack(currToonAttack, toon=1)
                        attack = self.battle.toonAttacks[currToonAttack]
                        atkTrack, atkLevel = self.__getActualTrackLevel(attack)
                damagesDone = self.__applyToonAttackDamages(currToonAttack)
                self.__applyToonAttackDamages(currToonAttack, hpbonus=1)
                if atkTrack != LURE and atkTrack != DROP and atkTrack != SOUND:
                    self.__applyToonAttackDamages(currToonAttack, kbbonus=1)
                if lastTrack != atkTrack:
                    lastAttacks = []
                    lastTrack = atkTrack
                lastAttacks.append(attack)
                if self.itemIsCredit(atkTrack, atkLevel):
                    if atkTrack == TRAP or atkTrack == LURE:
                        pass
                    elif atkTrack == HEAL:
                        if damagesDone != 0:
                            self.__addAttackExp(attack)
                    else:
                        self.__addAttackExp(attack)

        if self.trainTrapTriggered:
            for suit in self.battle.activeSuits:
                suitId = suit.doId
                self.__removeSuitTrap(suitId)
                suit.battleTrap = NO_TRAP
                self.notify.debug('train trap triggered, removing trap from %d' % suitId)

        if self.notify.getDebug():
            for currToonAttack in self.toonAtkOrder:
                attack = self.battle.toonAttacks[currToonAttack]
                self.notify.debug('Final Toon attack: ' + str(attack))

    def __allTargetsDead(self, attackIdx, toon=1):
        allTargetsDead = 1
        if toon:
            targets = self.__createToonTargetList(attackIdx)
            for currTgt in targets:
                if currTgt.getHp() > 0:
                    allTargetsDead = 0
                    break

        else:
            self.notify.warning('__allTargetsDead: suit ver. not implemented!')
        return allTargetsDead

    def __clearLuredSuitsByAttack(self, toonId, kbBonusReq = 0, targetId = -1):
        if self.notify.getDebug():
            self.notify.debug('__clearLuredSuitsByAttack')
        if targetId != -1 and self.__suitIsLured(t.getDoId()):
            self.__removeLured(t.getDoId())
        else:
            tgtList = self.__createToonTargetList(toonId)
            for t in tgtList:
                if self.__suitIsLured(t.getDoId()) and (not kbBonusReq or self.__bonusExists(t, hp=0)):
                    self.__removeLured(t.getDoId())
                    if self.notify.getDebug():
                        self.notify.debug('Suit %d stepping from lured spot' % t.getDoId())
                else:
                    self.notify.debug('Suit ' + str(t.getDoId()) + ' not found in currently lured suits')

    def __clearLuredSuitsDelayed(self):
        if self.notify.getDebug():
            self.notify.debug('__clearLuredSuitsDelayed')
        for t in self.delayedUnlures:
            if self.__suitIsLured(t):
                self.__removeLured(t)
                if self.notify.getDebug():
                    self.notify.debug('Suit %d stepping back from lured spot' % t)
            else:
                self.notify.debug('Suit ' + str(t) + ' not found in currently lured suits')

        self.delayedUnlures = []

    def __addLuredSuitsDelayed(self, toonId, targetId = -1, ignoreDamageCheck = False):
        if self.notify.getDebug():
            self.notify.debug('__addLuredSuitsDelayed')
        if targetId != -1:
            self.delayedUnlures.append(targetId)
        else:
            tgtList = self.__createToonTargetList(toonId)
            for t in tgtList:
                if self.__suitIsLured(t.getDoId()) and t.getDoId() not in self.delayedUnlures and (self.__attackDamageForTgt(self.battle.toonAttacks[toonId], self.battle.activeSuits.index(t), suit=0) > 0 or ignoreDamageCheck):
                    self.delayedUnlures.append(t.getDoId())

    def __calculateToonAttacks(self):
        self.notify.debug('__calculateToonAttacks()')
        self.__clearBonuses(hp=0)
        currTrack = None
        self.notify.debug('Traps: ' + str(self.traps))
        maxSuitLevel = 0
        for cog in self.battle.activeSuits:
            maxSuitLevel = max(maxSuitLevel, cog.getActualLevel())

        self.creditLevel = maxSuitLevel
        for toonId in self.toonAtkOrder:
            if self.__combatantDead(toonId, toon=1):
                if self.notify.getDebug():
                    self.notify.debug("Toon %d is dead and can't attack" % toonId)
                continue
            if hasattr(self, 'statusEffectMgr') and self.statusEffectMgr.is_frozen(toonId):
                self.notify.info("Toon %d is FROZEN — skipping gag turn!" % toonId)
                self.__clearAttack(toonId)
                continue
            attack = self.battle.toonAttacks[toonId]
            atkTrack = self.__getActualTrack(attack)
            if atkTrack != NO_ATTACK and atkTrack != SOS and atkTrack != NPCSOS:
                if self.notify.getDebug():
                    self.notify.debug('Calculating attack for toon: %d' % toonId)
                if self.SUITS_UNLURED_IMMEDIATELY:
                    if currTrack and atkTrack != currTrack:
                        self.__clearLuredSuitsDelayed()
                currTrack = atkTrack
                self.__calcToonAtkHp(toonId)
                attackIdx = self.toonAtkOrder.index(toonId)
                self.__handleBonus(attackIdx, hp=0)
                self.__handleBonus(attackIdx, hp=1)
                lastAttack = self.toonAtkOrder.index(toonId) >= len(self.toonAtkOrder) - 1
                unlureAttack = self.__attackHasHit(attack, suit=0) and self.__unlureAtk(toonId, toon=1)
                if unlureAttack:
                    if lastAttack:
                        self.__clearLuredSuitsByAttack(toonId)
                    else:
                        self.__addLuredSuitsDelayed(toonId)
                if lastAttack:
                    self.__clearLuredSuitsDelayed()

        self.__processBonuses(hp=0)
        self.__processBonuses(hp=1)
        self.__postProcessToonAttacks()
        return

    def __knockBackAtk(self, attackIndex, toon=1):
        if toon:
            track = self.battle.toonAttacks[attackIndex][TOON_TRACK_COL]
            if track == THROW or track == SQUIRT:
                if self.notify.getDebug():
                    self.notify.debug('attack is a knockback')
                return 1
            elif track == SOUND:
                toonObj = self.battle.getToon(attackIndex)
                from toontown.toon.TrinketsConfig import TRINKET_LOUDER_SOUND
                if toonObj and hasattr(toonObj, 'hasTrinketEquipped') and toonObj.hasTrinketEquipped(TRINKET_LOUDER_SOUND):
                    if self.notify.getDebug():
                        self.notify.debug('Louder Sound knockback proc!')
                    return 1
        return 0

    def __unlureAtk(self, attackIndex, toon=1):
        attack = self.battle.toonAttacks[attackIndex]
        track = self.__getActualTrack(attack)
        if toon:
            toonObj = self.battle.getToon(attackIndex)
            from toontown.toon.TrinketsConfig import TRINKET_GENTLE_WATER, TRINKET_LURED_DROP
            if track == SQUIRT:
                if toonObj and hasattr(toonObj, 'hasTrinketEquipped') and toonObj.hasTrinketEquipped(TRINKET_GENTLE_WATER):
                    if random.random() < 0.30:
                        if self.notify.getDebug():
                            self.notify.debug('Gentle Water proc! Squirt does not unlure')
                        return 0
                return 1
            elif track == THROW or track == SOUND:
                return 1
            elif track == DROP:
                if toonObj and hasattr(toonObj, 'hasTrinketEquipped') and toonObj.hasTrinketEquipped(TRINKET_LURED_DROP):
                    return 1
        return 0

    def __calcSuitAtkType(self, attackIndex):
        theSuit = self.battle.activeSuits[attackIndex]
        attacks = SuitBattleGlobals.SuitAttributes[theSuit.dna.name]['attacks']
        atk = SuitBattleGlobals.pickSuitAttack(attacks, theSuit.getLevel())
        return atk

    def __calcSuitTarget(self, attackIndex):
        attack = self.battle.suitAttacks[attackIndex]
        suitId = attack[SUIT_ID_COL]
        if suitId in self.SuitAttackers and random.randint(0, 99) < 75:
            totalDamage = 0
            for currToon in list(self.SuitAttackers[suitId].keys()):
                totalDamage += self.SuitAttackers[suitId][currToon]

            dmgs = []
            for currToon in list(self.SuitAttackers[suitId].keys()):
                dmgs.append(self.SuitAttackers[suitId][currToon] / totalDamage * 100)

            dmgIdx = SuitBattleGlobals.pickFromFreqList(dmgs)
            if dmgIdx == None:
                toonId = self.__pickRandomToon(suitId)
            else:
                toonId = list(self.SuitAttackers[suitId].keys())[dmgIdx]
            if toonId == -1 or toonId not in self.battle.activeToons:
                return -1
            self.notify.debug('Suit attacking back at toon ' + str(toonId))
            return self.battle.activeToons.index(toonId)
        else:
            return self.__pickRandomToon(suitId)
        return

    def __pickRandomToon(self, suitId):
        liveToons = []
        for currToon in self.battle.activeToons:
            if not self.__combatantDead(currToon, toon=1):
                liveToons.append(self.battle.activeToons.index(currToon))

        if len(liveToons) == 0:
            self.notify.debug('No tgts avail. for suit ' + str(suitId))
            return -1
        chosen = random.choice(liveToons)
        self.notify.debug('Suit randomly attacking toon ' + str(self.battle.activeToons[chosen]))
        return chosen

    def __suitAtkHit(self, attackIndex):
        if self.suitsAlwaysHit:
            return 1
        else:
            if self.suitsAlwaysMiss:
                return 0
        theSuit = self.battle.activeSuits[attackIndex]
        if self.statusEffectMgr.is_frozen(theSuit.doId):
            self.notify.info('Suit %d is FROZEN — skipping attack turn!' % theSuit.doId)
            return 0
        atkType = self.battle.suitAttacks[attackIndex][SUIT_ATK_COL]
        atkInfo = SuitBattleGlobals.getSuitAttack(theSuit.dna.name, theSuit.getLevel(), atkType)
        atkAcc = atkInfo['acc']
        accList = SuitBattleGlobals.SuitAttributes[theSuit.dna.name]['acc']
        suitAcc = accList[min(max(0, theSuit.getLevel()), len(accList) - 1)]
        targetIdx = self.battle.suitAttacks[attackIndex][SUIT_TGT_COL]
        targetId = self.battle.activeToons[targetIdx] if (targetIdx >= 0 and targetIdx < len(self.battle.activeToons)) else None
        targetDefMod = self.statusEffectMgr.get_defense_mod(targetId) if targetId else 0
        acc = atkAcc + self.statusEffectMgr.get_accuracy_mod(theSuit.doId) - targetDefMod
        randChoice = random.randint(0, 99)
        hit = randChoice < acc
        accDelta = self.statusEffectMgr.get_accuracy_mod(theSuit.doId) - targetDefMod
        suitName = theSuit.getName() if hasattr(theSuit, 'getName') else f"Suit #{theSuit.doId}"
        suitLvl = (theSuit.getActualLevel() if hasattr(theSuit, 'getActualLevel') else theSuit.getLevel() + 1)
        print(f"[COMBAT LOG] ENEMY ATTACK -> Suit: {suitName} Lvl {suitLvl} | Attack: {atkInfo['name']} | BaseAcc: {atkAcc}% | AccDelta: {accDelta:+d}% | FinalAcc: {acc}% | Roll: {randChoice} | Result: {'HIT' if hit else 'MISS'}")
        if hit:
            return 1
        return 0

    def __suitAtkAffectsGroup(self, attack):
        atkType = attack[SUIT_ATK_COL]
        theSuit = self.battle.findSuit(attack[SUIT_ID_COL])
        atkInfo = SuitBattleGlobals.getSuitAttack(theSuit.dna.name, theSuit.getLevel(), atkType)
        return atkInfo['group'] != SuitBattleGlobals.ATK_TGT_SINGLE

    def __createSuitTargetList(self, attackIndex):
        attack = self.battle.suitAttacks[attackIndex]
        targetList = []
        if attack[SUIT_ATK_COL] == NO_ATTACK:
            self.notify.debug('No attack, no targets')
            return targetList
        debug = self.notify.getDebug()
        if not self.__suitAtkAffectsGroup(attack):
            targetList.append(self.battle.activeToons[attack[SUIT_TGT_COL]])
            if debug:
                self.notify.debug('Suit attack is single target')
        else:
            if debug:
                self.notify.debug('Suit attack is group target')
            for currToon in self.battle.activeToons:
                if debug:
                    self.notify.debug('Suit attack will target toon' + str(currToon))
                targetList.append(currToon)

        return targetList

    def __calcSuitAtkHp(self, attackIndex):
        targetList = self.__createSuitTargetList(attackIndex)
        attack = self.battle.suitAttacks[attackIndex]
        for currTarget in range(len(targetList)):
            toonId = targetList[currTarget]
            toon = self.battle.getToon(toonId)
            result = 0
            if toon and toon.immortalMode:
                result = 1
            elif self.TOONS_TAKE_NO_DAMAGE:
                result = 0
            elif self.__suitAtkHit(attackIndex):
                atkType = attack[SUIT_ATK_COL]
                theSuit = self.battle.findSuit(attack[SUIT_ID_COL])
                atkInfo = SuitBattleGlobals.getSuitAttack(theSuit.dna.name, theSuit.getLevel(), atkType)
                raw_hp = atkInfo['hp']
                from toontown.battle.CritGlobals import roll_hit_type, HIT_TYPE_NAMES, HIT_NORMAL
                is_skelecog = getattr(theSuit, 'isSkelecogVariant', False) or getattr(theSuit, 'isSkelecog', False)
                hit_type, crit_mult = roll_hit_type(is_toon=False, is_skelecog=is_skelecog)
                dmg_mult = self.statusEffectMgr.get_damage_multiplier(toonId)
                if getattr(theSuit, 'isAlphatype', False) or getattr(theSuit, 'isSupertype', False):
                    dmg_mult *= 1.3
                from toontown.toon.TrinketsConfig import TRINKET_ORGANIC_ALL, TRINKET_GLASS_CANNON
                if toon and hasattr(toon, 'hasTrinketEquipped'):
                    if toon.hasTrinketEquipped(TRINKET_ORGANIC_ALL):
                        dmg_mult *= 1.5
                    if toon.hasTrinketEquipped(TRINKET_GLASS_CANNON):
                        dmg_mult *= 1.25
                result = int(raw_hp * crit_mult * dmg_mult)
                if hit_type != HIT_NORMAL:
                    result = max(result + 1, int(math.ceil(raw_hp * crit_mult * dmg_mult)))
                
                # Check if target Toon is BLOCKING (PASS action)
                if toonId in self.blockingToons:
                    result = int(result * 0.5)
                    hit_type = 4 if result > 0 else 5

                if not isinstance(attack[SUIT_BEFORE_TOONS_COL], int):
                    attack[SUIT_BEFORE_TOONS_COL] = 0
                targetIndex = self.battle.activeToons.index(toonId)
                attack[SUIT_BEFORE_TOONS_COL] |= ((hit_type & 0x7) << (targetIndex * 3))
                atkName = atkInfo['name']
                if atkName in SUIT_ATTACK_STATUS_EFFECTS:
                    eff_cfg = SUIT_ATTACK_STATUS_EFFECTS[atkName]
                    hit_name = HIT_TYPE_NAMES.get(hit_type, 'NORMAL')
                    proc_chance = self.statusEffectMgr.calc_proc_chance(eff_cfg.get('chance', 100), 0, hit_name)
                    if random.randint(1, 100) <= proc_chance:
                        self.statusEffectMgr.apply_effect(toonId, eff_cfg['effect'], eff_cfg['rounds'], eff_cfg)
            targetIndex = self.battle.activeToons.index(toonId)
            while len(attack[SUIT_HP_COL]) <= targetIndex:
                attack[SUIT_HP_COL].append(0)
            attack[SUIT_HP_COL][targetIndex] = result

    def __getToonHp(self, toonDoId):
        handle = self.battle.getToon(toonDoId)
        if handle != None and toonDoId in self.toonHPAdjusts:
            return handle.hp + self.toonHPAdjusts[toonDoId]
        else:
            return 0
        return

    def __getToonMaxHp(self, toonDoId):
        handle = self.battle.getToon(toonDoId)
        if handle != None:
            return handle.maxHp
        else:
            return 0
        return

    def __applySuitAttackDamages(self, attackIndex):
        attack = self.battle.suitAttacks[attackIndex]
        if self.APPLY_HEALTH_ADJUSTMENTS:
            for t in self.battle.activeToons:
                position = self.battle.activeToons.index(t)
                if attack[SUIT_HP_COL][position] <= 0:
                    continue
                toonHp = self.__getToonHp(t)
                toonMaxHp = self.__getToonMaxHp(t)
                incomingDmg = attack[SUIT_HP_COL][position]

                # One Shot Protection (OSP):
                # Only applies to Uber Toons (laffCap > 0), and specifically excluded for 1-Laff Ubers (maxHp > 1)
                # Normal toons do NOT have OSP.
                toonObj = self.battle.getToon(t)
                isUberToon = toonObj and getattr(toonObj, 'isUber', lambda: getattr(toonObj, 'laffCap', 0) > 0)()
                if isUberToon and toonMaxHp > 1 and (toonHp - incomingDmg) <= 0:
                    halfHpThreshold = int(math.ceil(toonMaxHp * 0.50))
                    quarterHpThreshold = int(math.ceil(toonMaxHp * 0.25))

                    if toonHp > halfHpThreshold:
                        # Dropped from above 50% HP -> survived with 50% HP
                        incomingDmg = max(0, toonHp - halfHpThreshold)
                        attack[SUIT_HP_COL][position] = incomingDmg
                        self.notify.info('Uber Toon %d triggered OSP (Tier 1: 50%%)! Survived with %d HP' % (t, halfHpThreshold))
                    elif toonHp > quarterHpThreshold:
                        # Dropped from above 25% HP -> survived with 25% HP
                        incomingDmg = max(0, toonHp - quarterHpThreshold)
                        attack[SUIT_HP_COL][position] = incomingDmg
                        self.notify.info('Uber Toon %d triggered OSP (Tier 2: 25%%)! Survived with %d HP' % (t, quarterHpThreshold))

                # Second Wind Trinket (Works on all Toons, including 1-Laff Ubers):
                # Once per battle, surviving fatal damage leaves you at 1 Laff with a SHIELD barrier.
                from toontown.toon.TrinketsConfig import TRINKET_SECOND_WIND
                has_second_wind = toonObj and hasattr(toonObj, 'hasTrinketEquipped') and toonObj.hasTrinketEquipped(TRINKET_SECOND_WIND)
                if has_second_wind and t not in self.secondWindUsed and (toonHp - incomingDmg) <= 0:
                    self.secondWindUsed.add(t)
                    incomingDmg = max(0, toonHp - 1)
                    attack[SUIT_HP_COL][position] = incomingDmg
                    if hasattr(self, 'statusEffectMgr'):
                        self.statusEffectMgr.apply_effect(t, 'SHIELD', 2, {'defense_reduction': -20})
                    self.notify.info(f"Toon {t} triggered SECOND WIND! Survived fatal blow with 1 HP and gained SHIELD!")

                if toonHp - attack[SUIT_HP_COL][position] <= 0:
                    if self.notify.getDebug():
                        self.notify.debug('Toon %d has died, removing' % t)
                    self.toonLeftBattle(t)
                    attack[TOON_DIED_COL] = attack[TOON_DIED_COL] | 1 << position
                dmg = attack[SUIT_HP_COL][position]
                if self.notify.getDebug():
                    self.notify.debug('Toon ' + str(t) + ' takes ' + str(dmg) + ' damage')
                self.toonHPAdjusts[t] -= dmg
                toon = self.battle.getToon(t)
                if toon and hasattr(toon, 'addStat'):
                    toon.addStat(8, dmg)
                self.notify.debug('Toon ' + str(t) + ' now has ' + str(self.__getToonHp(t)) + ' health')

    def __suitCanAttack(self, suitId):
        if self.__combatantDead(suitId, toon=0) or self.__suitIsLured(suitId) or self.__combatantJustRevived(suitId):
            return 0
        if hasattr(self, 'statusEffectMgr') and self.statusEffectMgr.is_frozen(suitId):
            self.notify.debug(f"Suit {suitId} is frozen and cannot attack!")
            return 0
        return 1

    def __updateSuitAtkStat(self, toonId):
        if toonId in self.suitAtkStats:
            self.suitAtkStats[toonId] += 1
        else:
            self.suitAtkStats[toonId] = 1

    def __printSuitAtkStats(self):
        self.notify.debug('Suit Atk Stats:')
        for currTgt in list(self.suitAtkStats.keys()):
            if currTgt not in self.battle.activeToons:
                continue
            tgtPos = self.battle.activeToons.index(currTgt)
            self.notify.debug(' toon ' + str(currTgt) + ' at position ' + str(tgtPos) + ' was attacked ' + str(self.suitAtkStats[currTgt]) + ' times')

    def calculateSuitAttacks(self):
        self.__calculateSuitAttacks()

    def __calculateSuitAttacks(self):
        for i in range(len(self.battle.suitAttacks)):
            if i < len(self.battle.activeSuits):
                suitId = self.battle.activeSuits[i].doId
                self.battle.suitAttacks[i][SUIT_ID_COL] = suitId
                if not self.__suitCanAttack(suitId):
                    self.battle.suitAttacks[i] = getDefaultSuitAttack()
                    if self.notify.getDebug():
                        self.notify.debug("Suit %d can't attack" % suitId)
                    continue
                if self.battle.pendingSuits.count(self.battle.activeSuits[i]) > 0 or self.battle.joiningSuits.count(self.battle.activeSuits[i]) > 0:
                    continue
                attack = self.battle.suitAttacks[i]
                attack[SUIT_ID_COL] = self.battle.activeSuits[i].doId
                attack[SUIT_ATK_COL] = self.__calcSuitAtkType(i)
                attack[SUIT_TGT_COL] = self.__calcSuitTarget(i)
                if attack[SUIT_TGT_COL] == -1:
                    self.battle.suitAttacks[i] = getDefaultSuitAttack()
                    attack = self.battle.suitAttacks[i]
                    self.notify.debug('clearing suit attack, no avail targets')
                self.__calcSuitAtkHp(i)
                if attack[SUIT_ATK_COL] != NO_ATTACK:
                    if self.__suitAtkAffectsGroup(attack):
                        for currTgt in self.battle.activeToons:
                            self.__updateSuitAtkStat(currTgt)

                    else:
                        tgtId = self.battle.activeToons[attack[SUIT_TGT_COL]]
                        self.__updateSuitAtkStat(tgtId)
                targets = self.__createSuitTargetList(i)
                allTargetsDead = 1
                for currTgt in targets:
                    if self.__getToonHp(currTgt) > 0:
                        allTargetsDead = 0
                        break

                if allTargetsDead:
                    self.battle.suitAttacks[i] = getDefaultSuitAttack()
                    if self.notify.getDebug():
                        self.notify.debug('clearing suit attack, targets dead')
                        self.notify.debug('suit attack is now ' + repr(self.battle.suitAttacks[i]))
                        self.notify.debug('all attacks: ' + repr(self.battle.suitAttacks))
                    attack = self.battle.suitAttacks[i]
                if self.__attackHasHit(attack, suit=1):
                    self.__applySuitAttackDamages(i)
                if self.notify.getDebug():
                    self.notify.debug('Suit attack: ' + str(self.battle.suitAttacks[i]))
                attack[SUIT_BEFORE_TOONS_COL] = 0

    def __updateLureTimeouts(self):
        if self.notify.getDebug():
            self.notify.debug('__updateLureTimeouts()')
            self.notify.debug('Lured suits: ' + str(self.currentlyLuredSuits))
        noLongerLured = []
        for currLuredSuit in list(self.currentlyLuredSuits.keys()):
            self.__incLuredCurrRound(currLuredSuit)
            if self.__luredMaxRoundsReached(currLuredSuit) or self.__luredWakeupTime(currLuredSuit):
                noLongerLured.append(currLuredSuit)

        for currLuredSuit in noLongerLured:
            self.__removeLured(currLuredSuit)

        if self.notify.getDebug():
            self.notify.debug('Lured suits: ' + str(self.currentlyLuredSuits))

    def __initRound(self):
        if self.CLEAR_SUIT_ATTACKERS:
            self.SuitAttackers = {}
        self.blockingToons = set()
        for toonId, attack in list(self.battle.toonAttacks.items()):
            if attack[TOON_TRACK_COL] == PASS:
                self.blockingToons.add(toonId)
        self.toonAtkOrder = []
        attacks = findToonAttack(self.battle.activeToons, self.battle.toonAttacks, PETSOS)
        for atk in attacks:
            self.toonAtkOrder.append(atk[TOON_ID_COL])

        attacks = findToonAttack(self.battle.activeToons, self.battle.toonAttacks, FIRE)
        for atk in attacks:
            self.toonAtkOrder.append(atk[TOON_ID_COL])

        for track in range(HEAL, DROP + 1):
            attacks = findToonAttack(self.battle.activeToons, self.battle.toonAttacks, track)
            if track == TRAP:
                sortedTraps = []
                for atk in attacks:
                    if atk[TOON_TRACK_COL] == TRAP:
                        sortedTraps.append(atk)

                for atk in attacks:
                    if atk[TOON_TRACK_COL] == NPCSOS:
                        sortedTraps.append(atk)

                attacks = sortedTraps
            for atk in attacks:
                self.toonAtkOrder.append(atk[TOON_ID_COL])

        specials = findToonAttack(self.battle.activeToons, self.battle.toonAttacks, NPCSOS)
        toonsHit = 0
        cogsMiss = 0
        for special in specials:
            npc_track = NPCToons.getNPCTrack(special[TOON_TGT_COL])
            if npc_track == NPC_TOONS_HIT:
                BattleCalculatorAI.toonsAlwaysHit = 1
                toonsHit = 1
            elif npc_track == NPC_COGS_MISS:
                BattleCalculatorAI.suitsAlwaysMiss = 1
                cogsMiss = 1

        if self.notify.getDebug():
            self.notify.debug('Toon attack order: ' + str(self.toonAtkOrder))
            self.notify.debug('Active toons: ' + str(self.battle.activeToons))
            self.notify.debug('Toon attacks: ' + str(self.battle.toonAttacks))
            self.notify.debug('Active suits: ' + str(self.battle.activeSuits))
            self.notify.debug('Suit attacks: ' + str(self.battle.suitAttacks))
        self.toonHPAdjusts = {}
        for t in self.battle.activeToons:
            self.toonHPAdjusts[t] = 0

        self.__clearBonuses()
        self.__updateActiveToons()
        self.delayedUnlures = []
        self.__initTraps()
        self.successfulLures = {}
        return (
toonsHit, cogsMiss)

    def calculateRound(self):
        self.poisonTicks = {}
        poison_ticks = self.statusEffectMgr.tick_round()
        self.poisonTicks = poison_ticks
        for avatar_id, tick_data in list(poison_ticks.items()):
            poison_dmg, hit_type = tick_data
            suit = self.battle.findSuit(avatar_id)
            if suit:
                if suit.getHP() > 0:
                    suit.setHP(max(0, suit.getHP() - poison_dmg))
                    if suit.getHP() <= 0:
                        self.suitLeftBattle(avatar_id)
                    self.notify.info('Poison tick: dealt %d damage (crit_type=%d) to suit %d' % (poison_dmg, hit_type, avatar_id))
            else:
                toon = self.battle.getToon(avatar_id)
                if toon:
                    if avatar_id in self.toonHPAdjusts:
                        self.toonHPAdjusts[avatar_id] -= poison_dmg
                    self.notify.info('Poison tick: dealt %d damage (crit_type=%d) to toon %d' % (poison_dmg, hit_type, avatar_id))
                else:
                    self.statusEffectMgr.clear_avatar(avatar_id)

        longest = max(len(self.battle.activeToons), len(self.battle.activeSuits))
        for t in self.battle.activeToons:
            for j in range(longest):
                self.battle.toonAttacks[t][TOON_HP_COL].append(-1)
                self.battle.toonAttacks[t][TOON_KBBONUS_COL].append(-1)

        for i in range(4):
            for j in range(len(self.battle.activeToons)):
                self.battle.suitAttacks[i][SUIT_HP_COL].append(-1)

        toonsHit, cogsMiss = self.__initRound()
        for suit in self.battle.activeSuits:
            if suit.isGenerated():
                suit.b_setHP(suit.getHP())

        for suit in self.battle.activeSuits:
            if not hasattr(suit, 'dna'):
                self.notify.warning('a removed suit is in this battle!')
                return None

        self.__calculateToonAttacks()
        self.__updateLureTimeouts()
        self.__calculateSuitAttacks()
        self.battle.broadcastStatusEffects()
        if toonsHit == 1:
            BattleCalculatorAI.toonsAlwaysHit = 0
        if cogsMiss == 1:
            BattleCalculatorAI.suitsAlwaysMiss = 0
        if self.notify.getDebug():
            self.notify.debug('Toon skills gained after this round: ' + repr(self.toonSkillPtsGained))
            self.__printSuitAtkStats()
        return None

    def __calculateFiredCogs():
        import pdb
        pdb.set_trace()

    def toonLeftBattle(self, toonId):
        if self.notify.getDebug():
            self.notify.debug('toonLeftBattle()' + str(toonId))
        if toonId in self.toonSkillPtsGained:
            del self.toonSkillPtsGained[toonId]
        if toonId in self.suitAtkStats:
            del self.suitAtkStats[toonId]
        if not self.CLEAR_SUIT_ATTACKERS:
            oldSuitIds = []
            for s in list(self.SuitAttackers.keys()):
                if toonId in self.SuitAttackers[s]:
                    del self.SuitAttackers[s][toonId]
                    if len(self.SuitAttackers[s]) == 0:
                        oldSuitIds.append(s)

            for oldSuitId in oldSuitIds:
                del self.SuitAttackers[oldSuitId]

        self.__clearTrapCreator(toonId)
        self.__clearLurer(toonId)

    def suitLeftBattle(self, suitId):
        if self.notify.getDebug():
            self.notify.debug('suitLeftBattle(): ' + str(suitId))
        self.statusEffectMgr.clear_avatar(suitId)
        self.__removeLured(suitId)
        if suitId in self.SuitAttackers:
            del self.SuitAttackers[suitId]
        self.__removeSuitTrap(suitId)

        suit = self.battle.findSuit(suitId)
        if suit and not getattr(suit, 'isVirtual', False):
            # 5 Cog Defeat Progression -> Trinket Unlock or 100 Jellybeans
            from toontown.toon.TrinketsConfig import ALL_TRINKET_IDS, get_trinket_info, TRINKET_LUCKY_CHARM
            for toonId in self.battle.activeToons:
                toon = self.battle.getToon(toonId)
                if toon:
                    count = toon.getCogKillsCount() + 1
                    if count >= 5:
                        count = 0
                        unlocked = toon.getUnlockedTrinkets()
                        unowned = [t_id for t_id in ALL_TRINKET_IDS if t_id not in unlocked]
                        if unowned:
                            new_trinket = random.choice(unowned)
                            toon.unlockTrinket(new_trinket)
                            info = get_trinket_info(new_trinket)
                            trinket_name = info['name'] if info else f"Trinket #{new_trinket}"
                            toon.d_setSystemMessage(0, f"+NEW TRINKET UNLOCKED: {trinket_name}!")
                        else:
                            jellybeans = 100
                            if toon.hasTrinketEquipped(TRINKET_LUCKY_CHARM):
                                jellybeans = 150
                            toon.addMoney(jellybeans)
                            toon.d_setSystemMessage(0, f"+{jellybeans} JELLYBEANS!")
                    toon.b_setCogKillsCount(count)

    def __updateActiveToons(self):
        if self.notify.getDebug():
            self.notify.debug('updateActiveToons()')
        if not self.CLEAR_SUIT_ATTACKERS:
            oldSuitIds = []
            for s in list(self.SuitAttackers.keys()):
                for t in list(self.SuitAttackers[s].keys()):
                    if t not in self.battle.activeToons:
                        del self.SuitAttackers[s][t]
                        if len(self.SuitAttackers[s]) == 0:
                            oldSuitIds.append(s)

            for oldSuitId in oldSuitIds:
                del self.SuitAttackers[oldSuitId]

        for trap in list(self.traps.keys()):
            if self.traps[trap][1] not in self.battle.activeToons:
                self.notify.debug('Trap for toon ' + str(self.traps[trap][1]) + ' will no longer give exp')
                self.traps[trap][1] = 0

    def getSkillGained(self, toonId, track):
        return BattleExperienceAI.getSkillGained(self.toonSkillPtsGained, toonId, track)

    def getLuredSuits(self):
        luredSuits = list(self.currentlyLuredSuits.keys())
        self.notify.debug('Lured suits reported to battle: ' + repr(luredSuits))
        return luredSuits

    def __suitIsLured(self, suitId, prevRound=0):
        inList = suitId in self.currentlyLuredSuits
        if prevRound:
            return inList and self.currentlyLuredSuits[suitId][0] != -1
        return inList

    def __findAvailLureId(self, lurerId):
        luredSuits = list(self.currentlyLuredSuits.keys())
        lureIds = []
        for currLured in luredSuits:
            lurerInfo = self.currentlyLuredSuits[currLured][3]
            lurers = list(lurerInfo.keys())
            for currLurer in lurers:
                currId = lurerInfo[currLurer][1]
                if currLurer == lurerId and currId not in lureIds:
                    lureIds.append(currId)

        lureIds.sort()
        currId = 1
        for currLureId in lureIds:
            if currLureId != currId:
                return currId
            currId += 1

        return currId

    def __addLuredSuitInfo(self, suitId, currRounds, maxRounds, wakeChance, lurer, lureLvl, lureId=-1, npc=0):
        if lureId == -1:
            availLureId = self.__findAvailLureId(lurer)
        else:
            availLureId = lureId
        if npc == 1:
            credit = 0
        else:
            credit = self.itemIsCredit(LURE, lureLvl)
        if suitId in self.currentlyLuredSuits:
            lureInfo = self.currentlyLuredSuits[suitId]
            if lurer not in lureInfo[3]:
                lureInfo[1] += maxRounds
                if wakeChance < lureInfo[2]:
                    lureInfo[2] = wakeChance
                lureInfo[3][lurer] = [
                 lureLvl, availLureId, credit]
        else:
            lurerInfo = {lurer: [lureLvl, availLureId, credit]}
            self.currentlyLuredSuits[suitId] = [
             currRounds, maxRounds, wakeChance, lurerInfo]
        self.notify.debug('__addLuredSuitInfo: currLuredSuits -> %s' % repr(self.currentlyLuredSuits))
        return availLureId

    def __getLurers(self, suitId):
        if self.__suitIsLured(suitId):
            return list(self.currentlyLuredSuits[suitId][3].keys())
        return []

    def __getLuredExpInfo(self, suitId):
        returnInfo = []
        lurers = self.__getLurers(suitId)
        if len(lurers) == 0:
            return returnInfo
        lurerInfo = self.currentlyLuredSuits[suitId][3]
        for currLurer in lurers:
            returnInfo.append([currLurer, lurerInfo[currLurer][0], lurerInfo[currLurer][1], lurerInfo[currLurer][2]])

        return returnInfo

    def __clearLurer(self, lurerId, lureId=-1):
        luredSuits = list(self.currentlyLuredSuits.keys())
        for currLured in luredSuits:
            lurerInfo = self.currentlyLuredSuits[currLured][3]
            lurers = list(lurerInfo.keys())
            for currLurer in lurers:
                if currLurer == lurerId and (lureId == -1 or lureId == lurerInfo[currLurer][1]):
                    del lurerInfo[currLurer]

    def __setLuredMaxRounds(self, suitId, rounds):
        if self.__suitIsLured(suitId):
            self.currentlyLuredSuits[suitId][1] = rounds

    def __setLuredWakeChance(self, suitId, chance):
        if self.__suitIsLured(suitId):
            self.currentlyLuredSuits[suitId][2] = chance

    def __incLuredCurrRound(self, suitId):
        if self.__suitIsLured(suitId):
            self.currentlyLuredSuits[suitId][0] += 1

    def __removeLured(self, suitId):
        if self.__suitIsLured(suitId):
            del self.currentlyLuredSuits[suitId]

    def __luredMaxRoundsReached(self, suitId):
        return self.__suitIsLured(suitId) and self.currentlyLuredSuits[suitId][0] >= self.currentlyLuredSuits[suitId][1]

    def __luredWakeupTime(self, suitId):
        return self.__suitIsLured(suitId) and self.currentlyLuredSuits[suitId][0] > 0 and random.randint(0, 99) < self.currentlyLuredSuits[suitId][2]

    def itemIsCredit(self, track, level):
        if track == PETSOS:
            return 0
        return level < self.creditLevel

    def __getActualTrack(self, toonAttack):
        if toonAttack[TOON_TRACK_COL] == NPCSOS:
            track = NPCToons.getNPCTrack(toonAttack[TOON_TGT_COL])
            if track != None:
                return track
            else:
                self.notify.warning('No NPC with id: %d' % toonAttack[TOON_TGT_COL])
        return toonAttack[TOON_TRACK_COL]

    def __getActualTrackLevel(self, toonAttack):
        if toonAttack[TOON_TRACK_COL] == NPCSOS:
            track, level, hp = NPCToons.getNPCTrackLevelHp(toonAttack[TOON_TGT_COL])
            if track != None:
                return (track, level)
            else:
                self.notify.warning('No NPC with id: %d' % toonAttack[TOON_TGT_COL])
        return (
         toonAttack[TOON_TRACK_COL], toonAttack[TOON_LVL_COL])

    def __getActualTrackLevelHp(self, toonAttack):
        if toonAttack[TOON_TRACK_COL] == NPCSOS:
            track, level, hp = NPCToons.getNPCTrackLevelHp(toonAttack[TOON_TGT_COL])
            if track != None:
                return (track, level, hp)
            else:
                self.notify.warning('No NPC with id: %d' % toonAttack[TOON_TGT_COL])
        else:
            if toonAttack[TOON_TRACK_COL] == PETSOS:
                trick = toonAttack[TOON_LVL_COL]
                petProxyId = toonAttack[TOON_TGT_COL]
                trickId = toonAttack[TOON_LVL_COL]
                healRange = PetTricks.TrickHeals[trickId]
                hp = 0
                if petProxyId in simbase.air.doId2do:
                    petProxy = simbase.air.doId2do[petProxyId]
                    if trickId < len(petProxy.trickAptitudes):
                        aptitude = petProxy.trickAptitudes[trickId]
                        hp = int(lerp(healRange[0], healRange[1], aptitude))
                else:
                    self.notify.warning('pet proxy: %d not in doId2do!' % petProxyId)
                return (toonAttack[TOON_TRACK_COL], toonAttack[TOON_LVL_COL], hp)
        return (
         toonAttack[TOON_TRACK_COL], toonAttack[TOON_LVL_COL], 0)

    def __calculatePetTrickSuccess(self, toonAttack):
        petProxyId = toonAttack[TOON_TGT_COL]
        if petProxyId not in simbase.air.doId2do:
            self.notify.warning('pet proxy %d not in doId2do!' % petProxyId)
            toonAttack[TOON_ACCBONUS_COL] = 1
            return (0, 0)
        petProxy = simbase.air.doId2do[petProxyId]
        trickId = toonAttack[TOON_LVL_COL]
        toonAttack[TOON_ACCBONUS_COL] = petProxy.attemptBattleTrick(trickId)
        if toonAttack[TOON_ACCBONUS_COL] == 1:
            return (0, 0)
        else:
            return (1, 100)
