from panda3d.core import *
from libotp import *
from direct.interval.IntervalGlobal import *
from .BattleBase import *
from direct.actor import Actor
from toontown.suit import SuitDNA
from direct.directnotify import DirectNotifyGlobal
from . import DistributedBattleBase
from toontown.toon import TTEmote
from otp.avatar import Emote
from toontown.toonbase import TTLocalizer
from . import MovieUtil
from direct.fsm import State
from toontown.suit import Suit
from . import SuitBattleGlobals
import random
from direct.gui.DirectGui import DirectFrame, DirectLabel, DGG
from toontown.toonbase import ToontownGlobals

class DistributedBattleBldg(DistributedBattleBase.DistributedBattleBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleBldg')
    camFOFov = 30.0
    camFOPos = Point3(0, -10, 4)

    def __init__(self, cr):
        townBattle = cr.playGame.getPlace().townBattle
        DistributedBattleBase.DistributedBattleBase.__init__(self, cr, townBattle)
        self.streetBattle = 0
        self.waveIndicator = None
        self.fsm.addState(State.State('BuildingReward', self.enterBuildingReward, self.exitBuildingReward, ['Resume']))
        offState = self.fsm.getStateNamed('Off')
        offState.addTransition('BuildingReward')
        playMovieState = self.fsm.getStateNamed('PlayMovie')
        playMovieState.addTransition('BuildingReward')

    def updateWaveIndicator(self):
        self.cleanupWaveIndicator()
        place = base.cr.playGame.getPlace()
        interior = getattr(place, 'interior', None) or getattr(base.cr, 'suitInterior', None)
        if not interior:
            from toontown.building.DistributedSuitInterior import DistributedSuitInterior
            for obj in list(base.cr.doId2do.values()):
                if isinstance(obj, DistributedSuitInterior):
                    interior = obj
                    break

        if not interior:
            return

        currentFloor = getattr(interior, 'currentFloor', 0) + 1
        numFloors = getattr(interior, 'numFloors', 1)
        activeCogs = len(self.activeSuits)
        reserveCogs = len(getattr(interior, 'reserveSuits', []))
        totalFloorCogs = activeCogs + reserveCogs

        # Check if boss floor
        isBoss = (currentFloor == numFloors)
        floorTitle = f"BOSS FLOOR ({currentFloor}/{numFloors})" if isBoss else f"FLOOR {currentFloor}/{numFloors}"

        # Modifier info
        modKey = getattr(interior, 'modifierKey', 'STANDARD')
        modLabel = getattr(interior, 'modifierLabel', 'Standard Operation')
        modColorMap = {
            'AMBUSH': (1.0, 0.4, 0.4, 1),        # Red
            'LOCKDOWN': (1.0, 0.65, 0.2, 1),     # Orange
            'VETERAN': (0.85, 0.5, 1.0, 1),      # Purple
            'OVERCLOCKED': (1.0, 0.9, 0.3, 1),   # Yellow
            'REINFORCED': (0.4, 0.8, 1.0, 1),    # Blue
            'FRENZIED': (1.0, 0.5, 0.8, 1),      # Pink
            'STANDARD': (0.7, 0.7, 0.7, 1)       # Gray
        }
        modFg = modColorMap.get(modKey, (0.8, 0.8, 0.8, 1))

        self.modTooltip = None
        self.waveIndicator = DirectFrame(
            parent=base.a2dTopLeft,
            relief=DGG.RAISED,
            borderWidth=(0.008, 0.008),
            frameColor=(0.15, 0.15, 0.2, 0.85),
            frameSize=(-0.02, 0.46, -0.21, 0.02),
            pos=(0.05, 0, -0.22),
            state=DGG.NORMAL
        )

        modDesc = getattr(interior, 'modifierDesc', 'No special conditions in effect.')

        def __onEnter(event):
            if self.modTooltip:
                self.modTooltip.destroy()
            self.modTooltip = DirectFrame(
                parent=base.a2dTopLeft,
                relief=DGG.RAISED,
                borderWidth=(0.008, 0.008),
                frameColor=(0.1, 0.1, 0.15, 0.95),
                frameSize=(-0.02, 0.65, -0.16, 0.02),
                pos=(0.05, 0, -0.44)
            )
            DirectLabel(
                parent=self.modTooltip,
                relief=None,
                text=f"{modLabel.upper()}",
                text_scale=0.040,
                text_fg=modFg,
                text_shadow=(0, 0, 0, 1),
                text_font=ToontownGlobals.getSignFont(),
                text_align=TextNode.ALeft,
                pos=(0.02, 0, -0.04)
            )
            DirectLabel(
                parent=self.modTooltip,
                relief=None,
                text=modDesc,
                text_scale=0.033,
                text_fg=(1, 1, 1, 1),
                text_shadow=(0, 0, 0, 1),
                text_wordwrap=20,
                text_align=TextNode.ALeft,
                pos=(0.02, 0, -0.08)
            )

        def __onExit(event):
            if self.modTooltip:
                self.modTooltip.destroy()
                self.modTooltip = None

        self.waveIndicator.bind(DGG.ENTER, __onEnter)
        self.waveIndicator.bind(DGG.EXIT, __onExit)

        DirectLabel(
            parent=self.waveIndicator,
            relief=None,
            text=floorTitle,
            text_scale=0.046,
            text_fg=(1, 0.85, 0.2, 1) if not isBoss else (1, 0.3, 0.3, 1),
            text_shadow=(0, 0, 0, 1),
            text_font=ToontownGlobals.getSignFont(),
            text_align=TextNode.ALeft,
            pos=(0.02, 0, -0.04)
        )

        cogsText = f"Active Cogs: {activeCogs}"
        if reserveCogs > 0:
            cogsText += f" | Reserves: {reserveCogs}"
        else:
            cogsText += " (Final Wave)"

        DirectLabel(
            parent=self.waveIndicator,
            relief=None,
            text=cogsText,
            text_scale=0.036,
            text_fg=(1, 1, 1, 1),
            text_shadow=(0, 0, 0, 1),
            text_align=TextNode.ALeft,
            pos=(0.02, 0, -0.095)
        )

        DirectLabel(
            parent=self.waveIndicator,
            relief=None,
            text=f"Mod: {modLabel}",
            text_scale=0.033,
            text_fg=modFg,
            text_shadow=(0, 0, 0, 1),
            text_align=TextNode.ALeft,
            pos=(0.02, 0, -0.15)
        )

    def cleanupWaveIndicator(self):
        if hasattr(self, 'modTooltip') and self.modTooltip:
            self.modTooltip.destroy()
            self.modTooltip = None
        if self.waveIndicator:
            self.waveIndicator.destroy()
            self.waveIndicator = None

    def generate(self):
        DistributedBattleBase.DistributedBattleBase.generate(self)

    def setBossBattle(self, value):
        self.bossBattle = value
        if self.bossBattle:
            self.battleMusic = base.loader.loadMusic('phase_7/audio/bgm/encntr_suit_winning_indoor.ogg')
        else:
            self.battleMusic = base.loader.loadMusic('phase_7/audio/bgm/encntr_general_bg_indoor.ogg')
        base.playMusic(self.battleMusic, looping=1, volume=0.9)

    def getBossBattleTaunt(self):
        return TTLocalizer.BattleBldgBossTaunt

    def setMembers(self, suits, suitsJoining, suitsPending, suitsActive, suitsLured, suitTraps, toons, toonsJoining, toonsPending, toonsActive, toonsRunning, timestamp):
        res = DistributedBattleBase.DistributedBattleBase.setMembers(self, suits, suitsJoining, suitsPending, suitsActive, suitsLured, suitTraps, toons, toonsJoining, toonsPending, toonsActive, toonsRunning, timestamp)
        self.updateWaveIndicator()
        return res

    def disable(self):
        self.cleanupWaveIndicator()
        DistributedBattleBase.DistributedBattleBase.disable(self)
        self.battleMusic.stop()

    def delete(self):
        self.cleanupWaveIndicator()
        DistributedBattleBase.DistributedBattleBase.delete(self)
        del self.battleMusic

    def buildJoinPointList(self, avPos, destPos, toon = 0):
        return []

    def __faceOff(self, ts, name, callback):
        if len(self.suits) == 0:
            self.notify.warning('__faceOff(): no suits.')
            return
        if len(self.toons) == 0:
            self.notify.warning('__faceOff(): no toons.')
            return
        elevatorPos = self.toons[0].getPos()
        if len(self.suits) == 1:
            leaderIndex = 0
        elif self.bossBattle == 1:
            leaderIndex = 1
        else:
            maxTypeNum = -1
            for suit in self.suits:
                suitTypeNum = SuitDNA.getSuitType(suit.dna.name)
                if maxTypeNum < suitTypeNum:
                    maxTypeNum = suitTypeNum
                    leaderIndex = self.suits.index(suit)

        delay = FACEOFF_TAUNT_T
        suitTrack = Parallel()
        suitLeader = None
        for suit in self.suits:
            suit.setState('Battle')
            suitIsLeader = 0
            oneSuitTrack = Sequence()
            oneSuitTrack.append(Func(suit.loop, 'neutral'))
            oneSuitTrack.append(Func(suit.headsUp, elevatorPos))
            if self.suits.index(suit) == leaderIndex:
                suitLeader = suit
                suitIsLeader = 1
                from toontown.suit import SuitDialog
                if getattr(suit, 'sprintRammed', False):
                    taunt = getattr(suit, 'sprintRamLine', None) or SuitDialog.getSprintRamText(suit.getStyleName())
                    suit.sprintRammed = False
                elif self.bossBattle == 1:
                    taunt = self.getBossBattleTaunt()
                else:
                    taunt = SuitBattleGlobals.getFaceoffTaunt(suit.getStyleName(), suit.doId)
                oneSuitTrack.append(Func(suit.setChatAbsolute, taunt, CFSpeech | CFTimeout))
            destPos, destHpr = self.getActorPosHpr(suit, self.suits)
            oneSuitTrack.append(Wait(delay))
            if suitIsLeader == 1:
                oneSuitTrack.append(Func(suit.clearChat))
            oneSuitTrack.append(self.createAdjustInterval(suit, destPos, destHpr))
            suitTrack.append(oneSuitTrack)

        if suitLeader is None and len(self.suits) > 0:
            suitLeader = self.suits[0]

        toonTrack = Parallel()
        for toon in self.toons:
            oneToonTrack = Sequence()
            destPos, destHpr = self.getActorPosHpr(toon, self.toons)
            oneToonTrack.append(Wait(delay))
            oneToonTrack.append(self.createAdjustInterval(toon, destPos, destHpr, toon=1, run=1))
            toonTrack.append(oneToonTrack)

        camTrack = Sequence()

        def setCamFov(fov):
            base.camLens.setMinFov(fov / (4. / 3.))

        if suitLeader:
            camTrack.append(Func(camera.wrtReparentTo, suitLeader))
            camTrack.append(Func(setCamFov, self.camFOFov))
            suitHeight = suitLeader.getHeight()
            suitOffsetPnt = Point3(0, 0, suitHeight)
            MidTauntCamHeight = suitHeight * 0.66
            MidTauntCamHeightLim = suitHeight - 1.8
            if MidTauntCamHeight < MidTauntCamHeightLim:
                MidTauntCamHeight = MidTauntCamHeightLim
            TauntCamY = 18
            TauntCamX = 0
            TauntCamHeight = random.choice((MidTauntCamHeight, 1, 11))
            camTrack.append(Func(camera.setPos, TauntCamX, TauntCamY, TauntCamHeight))
            camTrack.append(Func(camera.lookAt, suitLeader, suitOffsetPnt))
            camTrack.append(Wait(delay))
            camPos = Point3(0, -6, 4)
            camHpr = Vec3(0, 0, 0)
            camTrack.append(Func(camera.reparentTo, base.localAvatar))
            camTrack.append(Func(setCamFov, ToontownGlobals.DefaultCameraFov))
        camTrack.append(Func(camera.setPosHpr, camPos, camHpr))
        mtrack = Parallel(suitTrack, toonTrack, camTrack)
        done = Func(callback)
        track = Sequence(mtrack, done, name=name)
        track.start(ts)
        self.storeInterval(track, name)
        return

    def enterFaceOff(self, ts):
        if len(self.toons) > 0 and base.localAvatar == self.toons[0]:
            Emote.globalEmote.disableAll(self.toons[0], 'dbattlebldg, enterFaceOff')
        self.delayDeleteMembers()
        self.__faceOff(ts, self.faceOffName, self.__handleFaceOffDone)
        return None

    def __handleFaceOffDone(self):
        self.notify.debug('FaceOff done')
        self.d_faceOffDone(base.localAvatar.doId)

    def exitFaceOff(self):
        self.notify.debug('exitFaceOff()')
        if len(self.toons) > 0 and base.localAvatar == self.toons[0]:
            Emote.globalEmote.releaseAll(self.toons[0], 'dbattlebldg exitFaceOff')
        self.clearInterval(self.faceOffName)
        self._removeMembersKeep()
        camera.wrtReparentTo(self)
        base.camLens.setMinFov(self.camFov / (4. / 3.))
        return None

    def __playReward(self, ts, callback):
        toonTracks = Parallel()
        for toon in self.toons:
            toonTracks.append(Sequence(Func(toon.loop, 'victory'), Wait(FLOOR_REWARD_TIMEOUT), Func(toon.loop, 'neutral')))

        name = self.uniqueName('floorReward')
        track = Sequence(toonTracks, Func(callback), name=name)
        camera.setPos(0, 0, 1)
        camera.setHpr(180, 10, 0)
        self.storeInterval(track, name)
        track.start(ts)

    def enterReward(self, ts):
        self.notify.debug('enterReward()')
        self.delayDeleteMembers()
        self.__playReward(ts, self.__handleFloorRewardDone)
        return None

    def __handleFloorRewardDone(self):
        return None

    def exitReward(self):
        self.notify.debug('exitReward()')
        self.clearInterval(self.uniqueName('floorReward'))
        self._removeMembersKeep()
        NametagGlobals.setMasterArrowsOn(1)
        for toon in self.toons:
            toon.startSmooth()

        return None

    def enterBuildingReward(self, ts):
        self.delayDeleteMembers()
        if self.hasLocalToon():
            NametagGlobals.setMasterArrowsOn(0)
        self.movie.playReward(ts, self.uniqueName('building-reward'), self.__handleBuildingRewardDone, noSkip=True)
        return None

    def __handleBuildingRewardDone(self):
        if self.hasLocalToon():
            self.d_rewardDone(base.localAvatar.doId)
        self.movie.resetReward()
        self.fsm.request('Resume')

    def exitBuildingReward(self):
        self.movie.resetReward(finish=1)
        self._removeMembersKeep()
        NametagGlobals.setMasterArrowsOn(1)
        return None

    def enterResume(self, ts = 0):
        if self.hasLocalToon():
            self.removeLocalToon()
        return None

    def exitResume(self):
        return None
