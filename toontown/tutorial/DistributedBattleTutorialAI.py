from direct.directnotify import DirectNotifyGlobal
from toontown.battle.DistributedBattleAI import DistributedBattleAI


class DistributedBattleTutorialAI(DistributedBattleAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleTutorialAI')

    def __init__(self, air, battleMgr, pos, suit, toonId, zoneId, finishCallback = None, maxSuits = 1, tutorialFlag = 1):
        DistributedBattleAI.__init__(self, air, battleMgr, pos, suit, toonId, zoneId, finishCallback, maxSuits=maxSuits, tutorialFlag=tutorialFlag)
        self.tutorialRound = 0
        self.bossFlunkyHp = 20
        if suit:
            suit.maxHP = self.bossFlunkyHp
            suit.currHP = self.bossFlunkyHp

    def enterWaitForInput(self):
        self.tutorialRound += 1
        self.notify.info(f"DistributedBattleTutorialAI enterWaitForInput: Round {self.tutorialRound}")
        
        # Check if the player is a 1-Laff / Uber Toon who would die from a hit
        toon = self.getToon(self.toons[0]) if self.toons else None
        if toon:
            self.notify.info(f"Tutorial Toon {toon.doId}: hp={toon.hp}, maxHp={toon.maxHp}, isUber={getattr(toon, 'isUber', lambda: False)()}")
        is_1_laff_uber = (toon and (toon.maxHp <= 1 or (hasattr(toon, 'isUber') and toon.isUber() and toon.maxHp <= 1)))

        # If it's a 1-Laff Uber on Round 2, Tutorial Tom steps in and Fires the Cog!
        if is_1_laff_uber and self.tutorialRound >= 2 and len(self.activeSuits) > 0:
            suit = self.activeSuits[0]
            self.handleTomFireSuit(suit)
            return

        DistributedBattleAI.enterWaitForInput(self)

        # Set Cog speech based on tutorial phase
        if len(self.activeSuits) > 0:
            suit = self.activeSuits[0]
            if self.tutorialRound == 1:
                if hasattr(suit, 'd_setChat'):
                    suit.d_setChat("Welcome to your orientation... to DEFEAT!")
            elif self.tutorialRound == 2:
                if hasattr(suit, 'd_setChat'):
                    suit.d_setChat("Prepare for MAXIMUM OVERTIME!")
            elif self.tutorialRound >= 3:
                if hasattr(suit, 'd_setChat'):
                    suit.d_setChat("My corporate ladder... is broken!")

    def handleTomFireSuit(self, suit):
        self.notify.info("Uber Toon detected in tutorial! Tutorial Tom Fires the Cog!")
        if hasattr(suit, 'd_setChat'):
            suit.d_setChat("Wait! What is Tutorial Tom holding?!")
        encounter = {
            'type': 'f',
            'level': 1,
            'track': 'c',
            'isSkelecog': 0,
            'isForeman': 0,
            'isVP': 0,
            'isCFO': 0,
            'isSupervisor': 0,
            'isVirtual': 0,
            'hasRevives': 0,
            'isWorldBoss': False,
            'worldBossZoneId': self.zoneId,
            'activeToons': self.activeToons[:]
        }
        self.suitsKilled.append(encounter)
        self.suitsKilledThisBattle.append(encounter)
        self.suits = []
        self.activeSuits = []
        self.d_setMembers()
        for toonId in self.activeToons:
            toon = self.getToon(toonId)
            if toon:
                self.toonItems[toonId] = self.air.questManager.recoverItems(toon, self.suitsKilled, self.zoneId)
        self.d_setBattleExperience()
        self.b_setState('Reward')
