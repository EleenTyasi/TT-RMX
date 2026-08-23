from panda3d.core import *
from toontown.toonbase.ToontownGlobals import *
from direct.gui.DirectGui import *
from direct.showbase import DirectObject
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import StateData
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toon import NPCToons
from toontown.toon import ToonHead
from toontown.toon import ToonDNA
from toontown.toon.TrinketsConfig import get_trinket_info
from toontown.toonbase import ToontownBattleGlobals

class TownBattleSOSPanel(DirectFrame, StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('TownBattleSOSPanel')

    def __init__(self, doneEvent):
        DirectFrame.__init__(self, relief=None)
        self.initialiseoptions(TownBattleSOSPanel)
        StateData.StateData.__init__(self, doneEvent)
        self.friends = {}
        self.NPCFriends = {}
        self.curPage = 0
        self.pageSize = 5
        self.selectedNpcId = None
        self.mercList = []
        self.cardButtons = []
        self.mercHeads = []
        self.inspectorHead = None
        self.showingOnlineFriends = False
        self.bldg = 0
        self.chosenNPCToons = []

    def load(self):
        if self.isLoaded == 1:
            return None
        self.isLoaded = 1
        
        btn_font = ToontownGlobals.getToonFont()
        sign_font = ToontownGlobals.getSignFont()

        # Main Outer Panel Frame
        self.mainFrame = DirectFrame(
            parent=self,
            relief=DGG.RAISED,
            frameColor=(0.10, 0.12, 0.18, 0.96),
            frameSize=(-0.82, 0.82, -0.58, 0.58),
            borderWidth=(0.015, 0.015),
            pos=(0, 0, 0)
        )

        self.title = DirectLabel(
            parent=self.mainFrame,
            relief=None,
            text="Call an SOS Mercenary",
            text_scale=0.065,
            text_fg=Vec4(0.3, 0.9, 1.0, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=sign_font,
            pos=(0.0, 0.0, 0.49)
        )

        # Left Column Frame: Merc Roster List
        self.rosterFrame = DirectFrame(
            parent=self.mainFrame,
            relief=DGG.SUNKEN,
            frameColor=(0.16, 0.18, 0.26, 0.85),
            frameSize=(-0.78, -0.05, -0.46, 0.42),
            borderWidth=(0.01, 0.01),
            pos=(0, 0, 0)
        )

        self.rosterTitle = DirectLabel(
            parent=self.rosterFrame,
            relief=None,
            text="Available Mercs",
            text_scale=0.042,
            text_fg=Vec4(1, 0.85, 0.3, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=sign_font,
            pos=(-0.415, 0, 0.36)
        )

        # Pagination controls
        btn_style = {
            'relief': DGG.RAISED,
            'frameColor': (0.25, 0.45, 0.75, 0.9),
            'borderWidth': (0.01, 0.01),
            'text_scale': 0.036,
            'text_fg': (1, 1, 1, 1),
            'text_shadow': (0, 0, 0, 1),
            'text_font': btn_font,
            'pad': (0.02, 0.01),
        }

        self.prevButton = DirectButton(
            parent=self.rosterFrame,
            text="< Prev",
            pos=(-0.65, 0, -0.41),
            command=self.prevPage,
            **btn_style
        )

        self.pageLabel = DirectLabel(
            parent=self.rosterFrame,
            relief=None,
            text="Page 1/1",
            text_scale=0.035,
            text_fg=Vec4(1, 1, 1, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=btn_font,
            pos=(-0.415, 0, -0.41)
        )

        self.nextButton = DirectButton(
            parent=self.rosterFrame,
            text="Next >",
            pos=(-0.18, 0, -0.41),
            command=self.nextPage,
            **btn_style
        )

        # Right Column Frame: Selected Merc Inspector & Use Button
        self.inspectorFrame = DirectFrame(
            parent=self.mainFrame,
            relief=DGG.SUNKEN,
            frameColor=(0.14, 0.16, 0.24, 0.92),
            frameSize=(0.02, 0.78, -0.46, 0.42),
            borderWidth=(0.01, 0.01),
            pos=(0, 0, 0)
        )

        self.inspectorTitle = DirectLabel(
            parent=self.inspectorFrame,
            relief=None,
            text="Merc Profile & Trinkets",
            text_scale=0.042,
            text_fg=Vec4(1, 0.85, 0.3, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=sign_font,
            pos=(0.40, 0, 0.36)
        )

        self.inspectorName = DirectLabel(
            parent=self.inspectorFrame,
            relief=None,
            text="Select a Merc",
            text_scale=0.045,
            text_fg=Vec4(0.3, 0.9, 1.0, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=sign_font,
            pos=(0.40, 0, 0.26)
        )

        self.inspectorStats = DirectLabel(
            parent=self.inspectorFrame,
            relief=None,
            text="",
            text_scale=0.030,
            text_fg=Vec4(1, 1, 1, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=btn_font,
            text_align=TextNode.ALeft,
            text_wordwrap=22,
            pos=(0.06, 0, 0.19)
        )

        self.inspectorTrinketsTitle = DirectLabel(
            parent=self.inspectorFrame,
            relief=None,
            text="Equipped Trinkets:",
            text_scale=0.034,
            text_fg=Vec4(1, 0.85, 0.3, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=sign_font,
            text_align=TextNode.ALeft,
            pos=(0.06, 0, 0.05)
        )

        self.inspectorTrinketsText = DirectLabel(
            parent=self.inspectorFrame,
            relief=None,
            text="Select a mercenary on the left to inspect their combat stats and trinkets.",
            text_scale=0.026,
            text_fg=Vec4(0.9, 0.92, 0.95, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=btn_font,
            text_align=TextNode.ALeft,
            text_wordwrap=25,
            pos=(0.06, 0, -0.02)
        )

        # "USE SOS" Action Button in the Inspector!
        self.useSosButton = DirectButton(
            parent=self.inspectorFrame,
            relief=DGG.RAISED,
            frameColor=(0.15, 0.65, 0.25, 0.95),
            borderWidth=(0.012, 0.012),
            text="Use SOS",
            text_scale=0.045,
            text_fg=(1, 1, 1, 1),
            text_shadow=(0, 0, 0, 1),
            text_font=sign_font,
            pos=(0.40, 0, -0.38),
            command=self.__useSelectedSOS,
            pad=(0.06, 0.015)
        )

        # Back Button at Bottom
        self.backButton = DirectButton(
            parent=self.mainFrame,
            relief=DGG.RAISED,
            frameColor=(0.75, 0.2, 0.2, 0.9),
            borderWidth=(0.01, 0.01),
            text=TTLocalizer.TownBattleSOSBack,
            text_scale=0.042,
            text_fg=(1, 1, 1, 1),
            text_shadow=(0, 0, 0, 1),
            text_font=btn_font,
            pos=(0.0, 0.0, -0.52),
            command=self.__close,
            pad=(0.04, 0.012)
        )

        self.hide()
        return

    def unload(self):
        if self.isLoaded == 0:
            return None
        self.isLoaded = 0
        self.exit()
        self.clearRosterItems()
        self.clearInspectorHead()
        del self.mainFrame
        DirectFrame.destroy(self)
        return None

    def clearInspectorHead(self):
        if self.inspectorHead:
            self.inspectorHead.detachNode()
            self.inspectorHead.delete()
            self.inspectorHead = None

    def clearRosterItems(self):
        for btn in self.cardButtons:
            btn.destroy()
        self.cardButtons = []
        for head in self.mercHeads:
            head.detachNode()
            head.delete()
        self.mercHeads = []

    def enter(self, canLure = 1, canTrap = 1):
        if self.isEntered == 1:
            return None
        self.isEntered = 1
        if self.isLoaded == 0:
            self.load()
        self.canLure = canLure
        self.canTrap = canTrap
        self.factoryToonIdList = None
        messenger.send('SOSPanelEnter', [self])
        self.updateMercRoster()
        self.show()
        return

    def exit(self):
        if self.isEntered == 0:
            return None
        self.isEntered = 0
        self.clearRosterItems()
        self.clearInspectorHead()
        self.hide()
        messenger.send(self.doneEvent)
        return None

    def updateMercRoster(self):
        npcFriendsDict = getattr(base.localAvatar, 'NPCFriendsDict', {})
        self.mercList = [npcId for npcId in list(npcFriendsDict.keys()) if npcFriendsDict[npcId] > 0]
        
        # Sort by star rating descending, then name
        def sortKey(npcId):
            stars = NPCToons.getNPCTrackLevelHpRarity(npcId)[3]
            name = NPCToons.getNPCName(npcId) or ""
            return (-stars, name)
        
        self.mercList.sort(key=sortKey)
        
        maxPages = max(1, (len(self.mercList) + self.pageSize - 1) // self.pageSize)
        self.curPage = max(0, min(self.curPage, maxPages - 1))
        
        self.renderRoster()
        
        if self.mercList and (self.selectedNpcId is None or self.selectedNpcId not in self.mercList):
            self.selectMerc(self.mercList[0])
        elif not self.mercList:
            self.selectedNpcId = None
            self.inspectorName['text'] = "No Mercs Owned"
            self.inspectorStats['text'] = ""
            self.inspectorTrinketsText['text'] = "No SOS Merc cards available! Clear Field Offices or defeat the Sellbot VP to earn SOS cards."
            self.useSosButton['state'] = DGG.DISABLED
            self.clearInspectorHead()

    def renderRoster(self):
        self.clearRosterItems()
        
        totalPages = max(1, (len(self.mercList) + self.pageSize - 1) // self.pageSize)
        self.pageLabel['text'] = f"Page {self.curPage + 1}/{totalPages}"
        self.prevButton['state'] = DGG.NORMAL if self.curPage > 0 else DGG.DISABLED
        self.nextButton['state'] = DGG.NORMAL if self.curPage < totalPages - 1 else DGG.DISABLED
        
        startIdx = self.curPage * self.pageSize
        pageMercs = self.mercList[startIdx:startIdx + self.pageSize]
        
        npcFriendsDict = getattr(base.localAvatar, 'NPCFriendsDict', {})
        
        yOffset = 0.26
        for i, npcId in enumerate(pageMercs):
            count = npcFriendsDict.get(npcId, 0)
            name = NPCToons.getNPCName(npcId) or f"Merc #{npcId}"
            track, level, hp, stars = NPCToons.getNPCTrackLevelHpRarity(npcId)
            rarityNames = {1: "Novice", 2: "Adept", 3: "Veteran", 4: "Elite", 5: "Legendary"}
            tierTitle = rarityNames.get(stars, "Mercenary")
            
            trackNames = {
                ToontownBattleGlobals.HEAL_TRACK: "Toon-Up",
                ToontownBattleGlobals.TRAP_TRACK: "Trap",
                ToontownBattleGlobals.LURE_TRACK: "Lure",
                ToontownBattleGlobals.SOUND_TRACK: "Sound",
                ToontownBattleGlobals.THROW_TRACK: "Throw",
                ToontownBattleGlobals.SQUIRT_TRACK: "Squirt",
                ToontownBattleGlobals.DROP_TRACK: "Drop",
            }
            trackStr = trackNames.get(track, "Combat")

            # Selection Card Button
            isSelected = (npcId == self.selectedNpcId)
            btn = DirectButton(
                parent=self.rosterFrame,
                relief=DGG.RAISED,
                frameColor=(0.20, 0.45, 0.70, 0.95) if isSelected else (0.16, 0.22, 0.35, 0.85),
                borderWidth=(0.008, 0.008),
                text=f"{name} ({trackStr})\n{stars}-Star {tierTitle}  (x{count})",
                text_scale=0.026,
                text_fg=(1, 1, 1, 1),
                text_shadow=(0, 0, 0, 1),
                text_font=ToontownGlobals.getToonFont(),
                text_align=TextNode.ALeft,
                frameSize=(-0.02, 0.62, -0.045, 0.055),
                pos=(-0.72, 0, yOffset),
                command=self.selectMerc,
                extraArgs=[npcId]
            )
            self.cardButtons.append(btn)
            
            # Mini Toon Head
            try:
                head = self.createNPCToonHead(npcId, dimension=0.08)
                if head:
                    head.reparentTo(btn)
                    head.setPos(0.04, 0, 0.005)
                    self.mercHeads.append(head)
            except Exception:
                pass
                
            yOffset -= 0.12

    def selectMerc(self, npcId):
        self.selectedNpcId = npcId
        self.renderRoster()
        self.renderInspector(npcId)

    def renderInspector(self, npcId):
        self.clearInspectorHead()
        if not npcId:
            self.useSosButton['state'] = DGG.DISABLED
            return

        name = NPCToons.getNPCName(npcId) or f"Merc #{npcId}"
        track, level, hp, stars = NPCToons.getNPCTrackLevelHpRarity(npcId)
        profile = NPCToons.get_companion_profile(npcId)
        maxHp = profile['maxHp']
        trinketIds = profile['trinkets']
        
        rarityNames = {1: "Novice", 2: "Adept", 3: "Veteran", 4: "Elite", 5: "Legendary"}
        tierTitle = rarityNames.get(stars, "Mercenary")

        self.inspectorName['text'] = f"{name} ({stars}-Star)"
        
        trackNames = {
            ToontownBattleGlobals.HEAL_TRACK: "Toon-Up",
            ToontownBattleGlobals.TRAP_TRACK: "Trap",
            ToontownBattleGlobals.LURE_TRACK: "Lure",
            ToontownBattleGlobals.SOUND_TRACK: "Sound",
            ToontownBattleGlobals.THROW_TRACK: "Throw",
            ToontownBattleGlobals.SQUIRT_TRACK: "Squirt",
            ToontownBattleGlobals.DROP_TRACK: "Drop",
        }
        mainTrack = trackNames.get(track, "Offensive")
        secTracks = [trackNames.get(t, "") for t in profile['preferredTracks'] if t != track]
        secStr = f" / {secTracks[0]}" if secTracks and secTracks[0] else ""

        npcFriendsDict = getattr(base.localAvatar, 'NPCFriendsDict', {})
        count = npcFriendsDict.get(npcId, 0)

        self.inspectorStats['text'] = (
            f"Tier: {stars}-Star {tierTitle}\n"
            f"Max Laff: {maxHp} Laff  |  Summons: x{count}\n"
            f"Specialty: {mainTrack}{secStr}\n"
            f"Duration: 5 Combat Rounds"
        )

        # Build Trinket breakdown
        trinketTexts = []
        for t_id in trinketIds:
            if t_id != 0:
                t_info = get_trinket_info(t_id)
                if t_info:
                    trinketTexts.append(f"• {t_info['name']}:\n  {t_info['desc']}")
        
        if trinketTexts:
            self.inspectorTrinketsText['text'] = "\n\n".join(trinketTexts)
        else:
            self.inspectorTrinketsText['text'] = "Standard combat loadout with high-tier Gag distribution."

        # Enable or disable Use SOS button
        if count > 0:
            self.useSosButton['state'] = DGG.NORMAL
        else:
            self.useSosButton['state'] = DGG.DISABLED

        # Large Toon Portrait Head in Inspector
        try:
            head = self.createNPCToonHead(npcId, dimension=0.18)
            if head:
                head.reparentTo(self.inspectorFrame)
                head.setPos(0.66, 0, 0.26)
                self.inspectorHead = head
        except Exception:
            pass

    def __useSelectedSOS(self):
        if self.selectedNpcId:
            self.__choseNPCFriend(self.selectedNpcId)

    def prevPage(self):
        if self.curPage > 0:
            self.curPage -= 1
            self.renderRoster()

    def nextPage(self):
        totalPages = max(1, (len(self.mercList) + self.pageSize - 1) // self.pageSize)
        if self.curPage < totalPages - 1:
            self.curPage += 1
            self.renderRoster()

    def createNPCToonHead(self, NPCID, dimension = 0.5):
        NPCInfo = NPCToons.NPCToonDict.get(NPCID)
        if not NPCInfo:
            return None
        dnaList = NPCInfo[2]
        gender = NPCInfo[3]
        if dnaList == 'r':
            dnaList = NPCToons.getRandomDNA(NPCID, gender)
        dna = ToonDNA.ToonDNA()
        dna.newToonFromProperties(*dnaList)
        head = ToonHead.ToonHead()
        head.setupHead(dna, forGui=1)
        self.fitGeometry(head, fFlip=1, dimension=dimension)
        return head

    def fitGeometry(self, geom, fFlip = 0, dimension = 0.5):
        p1 = Point3()
        p2 = Point3()
        geom.calcTightBounds(p1, p2)
        if fFlip:
            t = p1[0]
            p1.setX(-p2[0])
            p2.setX(-t)
        d = p2 - p1
        biggest = max(d[0], d[2])
        if biggest <= 0:
            biggest = 1.0
        s = dimension / biggest
        mid = (p1 + d / 2.0) * s
        geomXform = hidden.attachNewNode('geomXform')
        for child in geom.getChildren():
            child.reparentTo(geomXform)

        geomXform.setPosHprScale(-mid[0], -mid[1] + 1, -mid[2], 180, 0, 0, s, s, s)
        geomXform.reparentTo(geom)

    def __close(self):
        doneStatus = {}
        doneStatus['mode'] = 'Back'
        messenger.send(self.doneEvent, [doneStatus])

    def __choseNPCFriend(self, friendId):
        doneStatus = {}
        doneStatus['mode'] = 'NPCFriend'
        doneStatus['friend'] = friendId
        self.chosenNPCToons.append(friendId)
        messenger.send(self.doneEvent, [doneStatus])

    def setFactoryToonIdList(self, toonIdList):
        self.factoryToonIdList = toonIdList[:]

