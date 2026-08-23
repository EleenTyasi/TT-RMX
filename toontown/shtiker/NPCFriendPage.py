from . import ShtikerPage
from direct.gui.DirectGui import *
from direct.directnotify import DirectNotifyGlobal
from panda3d.core import *
from toontown.toon import NPCToons
from toontown.toon import ToonHead
from toontown.toon import ToonDNA
from toontown.toon.TrinketsConfig import get_trinket_info
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownBattleGlobals

class NPCFriendPage(ShtikerPage.ShtikerPage):
    notify = DirectNotifyGlobal.directNotify.newCategory('NPCFriendPage')

    def __init__(self):
        ShtikerPage.ShtikerPage.__init__(self)
        self.curPage = 0
        self.pageSize = 6
        self.selectedNpcId = None
        self.mercList = []
        self.cardButtons = []
        self.mercHeads = []
        self.inspectorHead = None

    def load(self):
        ShtikerPage.ShtikerPage.load(self)
        self.title = DirectLabel(
            parent=self,
            relief=None,
            text="SOS Mercenaries Roster",
            text_scale=0.08,
            text_fg=Vec4(0.15, 0.15, 0.25, 1),
            text_font=ToontownGlobals.getSignFont(),
            pos=(0, 0, 0.60)
        )

        # Left Column - Roster List Frame
        self.rosterFrame = DirectFrame(
            parent=self,
            relief=DGG.SUNKEN,
            frameColor=(0.88, 0.88, 0.92, 0.8),
            frameSize=(-0.78, -0.05, -0.55, 0.48),
            borderWidth=(0.01, 0.01),
            pos=(0, 0, 0)
        )

        self.rosterTitle = DirectLabel(
            parent=self.rosterFrame,
            relief=None,
            text="Unlocked Mercs",
            text_scale=0.048,
            text_fg=Vec4(0.2, 0.3, 0.5, 1),
            text_font=ToontownGlobals.getToonFont(),
            pos=(-0.415, 0, 0.42)
        )

        # Pagination controls
        btn_font = ToontownGlobals.getToonFont()
        btn_style = {
            'relief': DGG.RAISED,
            'frameColor': (0.3, 0.5, 0.8, 0.9),
            'borderWidth': (0.01, 0.01),
            'text_scale': 0.04,
            'text_fg': (1, 1, 1, 1),
            'text_shadow': (0, 0, 0, 1),
            'text_font': btn_font,
            'pad': (0.02, 0.01),
        }

        self.prevButton = DirectButton(
            parent=self.rosterFrame,
            text="< Prev",
            pos=(-0.65, 0, -0.50),
            command=self.prevPage,
            **btn_style
        )

        self.pageLabel = DirectLabel(
            parent=self.rosterFrame,
            relief=None,
            text="Page 1/1",
            text_scale=0.038,
            text_fg=Vec4(0.2, 0.2, 0.3, 1),
            text_font=btn_font,
            pos=(-0.415, 0, -0.50)
        )

        self.nextButton = DirectButton(
            parent=self.rosterFrame,
            text="Next >",
            pos=(-0.18, 0, -0.50),
            command=self.nextPage,
            **btn_style
        )

        # Right Column - Detailed Inspector Frame
        self.inspectorFrame = DirectFrame(
            parent=self,
            relief=DGG.SUNKEN,
            frameColor=(0.12, 0.14, 0.22, 0.95),
            frameSize=(0.02, 0.78, -0.55, 0.48),
            borderWidth=(0.01, 0.01),
            pos=(0, 0, 0)
        )

        self.inspectorTitle = DirectLabel(
            parent=self.inspectorFrame,
            relief=None,
            text="Merc Profile & Trinkets",
            text_scale=0.048,
            text_fg=Vec4(1, 0.85, 0.2, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getSignFont(),
            pos=(0.40, 0, 0.42)
        )

        self.inspectorName = DirectLabel(
            parent=self.inspectorFrame,
            relief=None,
            text="Select a Merc",
            text_scale=0.045,
            text_fg=Vec4(0.3, 0.9, 1.0, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getSignFont(),
            pos=(0.40, 0, 0.30)
        )

        self.inspectorStats = DirectLabel(
            parent=self.inspectorFrame,
            relief=None,
            text="",
            text_scale=0.032,
            text_fg=Vec4(1, 1, 1, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getToonFont(),
            text_align=TextNode.ALeft,
            text_wordwrap=22,
            pos=(0.06, 0, 0.22)
        )

        self.inspectorTrinketsTitle = DirectLabel(
            parent=self.inspectorFrame,
            relief=None,
            text="Equipped Trinkets:",
            text_scale=0.036,
            text_fg=Vec4(1, 0.85, 0.3, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getSignFont(),
            text_align=TextNode.ALeft,
            pos=(0.06, 0, 0.06)
        )

        self.inspectorTrinketsText = DirectLabel(
            parent=self.inspectorFrame,
            relief=None,
            text="Select an SOS Merc on the left to inspect their combat stats and predefined trinkets!",
            text_scale=0.028,
            text_fg=Vec4(0.9, 0.9, 0.95, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getToonFont(),
            text_align=TextNode.ALeft,
            text_wordwrap=24,
            pos=(0.06, 0, -0.02)
        )

    def unload(self):
        self.clearRosterItems()
        self.clearInspectorHead()
        ShtikerPage.ShtikerPage.unload(self)

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

    def updatePage(self):
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
            self.inspectorTrinketsText['text'] = "Defeat the Sellbot VP or clear Field Offices to earn SOS Companion cards!"
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
        
        yOffset = 0.32
        for i, npcId in enumerate(pageMercs):
            count = npcFriendsDict.get(npcId, 0)
            name = NPCToons.getNPCName(npcId) or f"Merc #{npcId}"
            track, level, hp, stars = NPCToons.getNPCTrackLevelHpRarity(npcId)
            rarityNames = {1: "Novice", 2: "Adept", 3: "Veteran", 4: "Elite", 5: "Legendary"}
            tierTitle = rarityNames.get(stars, "Mercenary")
            
            # Card selection button
            btn = DirectButton(
                parent=self.rosterFrame,
                relief=DGG.RAISED,
                frameColor=(0.25, 0.4, 0.65, 0.9) if npcId == self.selectedNpcId else (0.18, 0.25, 0.4, 0.8),
                borderWidth=(0.008, 0.008),
                text=f"{name}\n{stars}-Star {tierTitle}  (x{count})",
                text_scale=0.030,
                text_fg=(1, 1, 1, 1),
                text_shadow=(0, 0, 0, 1),
                text_font=ToontownGlobals.getToonFont(),
                text_align=TextNode.ALeft,
                frameSize=(-0.02, 0.62, -0.05, 0.06),
                pos=(-0.72, 0, yOffset),
                command=self.selectMerc,
                extraArgs=[npcId]
            )
            self.cardButtons.append(btn)
            
            # Mini head
            try:
                head = self.createNPCToonHead(npcId, dimension=0.09)
                head.reparentTo(btn)
                head.setPos(0.04, 0, 0.005)
                self.mercHeads.append(head)
            except Exception:
                pass
                
            yOffset -= 0.13

    def selectMerc(self, npcId):
        self.selectedNpcId = npcId
        self.renderRoster()
        self.renderInspector(npcId)

    def renderInspector(self, npcId):
        self.clearInspectorHead()
        if not npcId:
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
            self.inspectorTrinketsText['text'] = "Standard combat loadout with high-accuracy gag distribution."

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

    def enter(self):
        self.updatePage()
        ShtikerPage.ShtikerPage.enter(self)

    def exit(self):
        self.clearRosterItems()
        self.clearInspectorHead()
        ShtikerPage.ShtikerPage.exit(self)

