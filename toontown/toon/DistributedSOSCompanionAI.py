# =============================================================================
#  DistributedSOSCompanionAI.py  —  Autonomous SOS AI Companion Toon
#  TT-RMX Personal Tinkering Project
# =============================================================================

import random
from direct.directnotify import DirectNotifyGlobal
from toontown.toon.DistributedToonAI import DistributedToonAI
from toontown.toon import ToonDNA
from toontown.toonbase import ToontownBattleGlobals
from toontown.toonbase.ToontownBattleGlobals import *
from toontown.battle.BattleBase import *

class DistributedSOSCompanionAI(DistributedToonAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSOSCompanionAI')

    def __init__(self, air, npcId, summonerId, maxHp=100, trinkets=None, preferredTracks=None, gags=None):
        DistributedToonAI.__init__(self, air)
        self.isCompanion = True
        self.npcId = npcId
        self.summonerId = summonerId
        self.turnsRemaining = 5
        self.maxHp = maxHp
        self.hp = maxHp
        self.trinketSlots = trinkets or [0, 0]
        self.preferredTracks = preferredTracks or [THROW_TRACK, SQUIRT_TRACK]
        self.companionGags = gags or {}

    def isPlayerControlled(self):
        return False

    def getTrinketSlots(self):
        return self.trinketSlots

    def hasTrinketEquipped(self, trinketId):
        return trinketId in self.trinketSlots

    def chooseAction(self, battle):
        """
        Intelligently choose a combat action based on battle state and summoner's action.
        """
        if not battle or not battle.activeSuits:
            return getToonAttack(self.doId, track=PASS)

        activeCogs = battle.activeSuits
        livingCogs = [s for s in activeCogs if getattr(s, 'currHP', 1) > 0]
        if not livingCogs:
            return getToonAttack(self.doId, track=PASS)

        # 1. Emergency Toon-Up check
        # If summoner or ally is critically low on Laff (<= 45%), heal them
        summoner = battle.getToon(self.summonerId)
        if summoner and (summoner.hp / float(max(1, summoner.maxHp))) <= 0.45:
            if HEAL_TRACK in self.preferredTracks or self.companionGags.get(HEAL_TRACK, []):
                heal_lvls = self.companionGags.get(HEAL_TRACK, [3])
                lvl = heal_lvls[-1] if heal_lvls else 3
                self.notify.info(f"Companion {self.doId} executing emergency Toon-Up for summoner {self.summonerId}")
                return getToonAttack(self.doId, track=HEAL_TRACK, level=lvl, target=self.summonerId)

        # Check summoner's attack to coordinate synergies
        summonerAttack = battle.toonAttacks.get(self.summonerId, None)
        summonerTrack = summonerAttack[TOON_TRACK_COL] if summonerAttack else NO_ATTACK
        summonerTarget = summonerAttack[TOON_TGT_COL] if summonerAttack else -1

        # 2. DROP + SQUIRT/SOUND STUN SYNERGY:
        # If summoner picked Drop, use Squirt or Sound on the same target to stun it
        if summonerTrack == DROP_TRACK and summonerTarget != -1:
            targetIndex = summonerTarget if summonerTarget < len(activeCogs) else 0
            targetCog = activeCogs[targetIndex]
            if SQUIRT_TRACK in self.preferredTracks or self.companionGags.get(SQUIRT_TRACK, []):
                sq_lvls = self.companionGags.get(SQUIRT_TRACK, [3])
                lvl = sq_lvls[-1] if sq_lvls else 3
                self.notify.info(f"Companion {self.doId} performing Squirt Stun synergy for Drop on Cog {targetCog.doId}")
                return getToonAttack(self.doId, track=SQUIRT_TRACK, level=lvl, target=targetIndex)
            elif SOUND_TRACK in self.preferredTracks or self.companionGags.get(SOUND_TRACK, []):
                snd_lvls = self.companionGags.get(SOUND_TRACK, [3])
                lvl = snd_lvls[-1] if snd_lvls else 3
                self.notify.info(f"Companion {self.doId} performing Sound Stun synergy for Drop")
                return getToonAttack(self.doId, track=SOUND_TRACK, level=lvl, target=-1)

        # 3. LURE SYNERGY:
        # If 2+ Cogs are unlured, use Lure if available
        unluredCogs = [s for s in livingCogs if s not in battle.luredSuits]
        if len(unluredCogs) >= 2 and (LURE_TRACK in self.preferredTracks or self.companionGags.get(LURE_TRACK, [])):
            lure_lvls = self.companionGags.get(LURE_TRACK, [3])
            lvl = lure_lvls[-1] if lure_lvls else 3
            self.notify.info(f"Companion {self.doId} executing group Lure")
            return getToonAttack(self.doId, track=LURE_TRACK, level=lvl, target=-1)

        # 4. PRIMARY OFFENSIVE TRACK COMBO:
        primaryTrack = self.preferredTracks[0] if self.preferredTracks else THROW_TRACK
        targetIndex = summonerTarget if (summonerTarget != -1 and summonerTarget < len(activeCogs)) else 0
        
        # Pick highest available level for primary track
        gag_lvls = self.companionGags.get(primaryTrack, [3])
        lvl = gag_lvls[-1] if gag_lvls else 3
        
        if primaryTrack == SOUND_TRACK:
            return getToonAttack(self.doId, track=SOUND_TRACK, level=lvl, target=-1)
        
        return getToonAttack(self.doId, track=primaryTrack, level=lvl, target=targetIndex)

    def decrementTurn(self):
        self.turnsRemaining -= 1
        return self.turnsRemaining
