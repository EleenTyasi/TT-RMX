from direct.gui.DirectGui import *
from direct.directnotify import DirectNotifyGlobal
from panda3d.core import *
from . import NPCToons
from . import ToonHead
from . import ToonDNA
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownBattleGlobals

class NPCFriendPanel(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('NPCFriendPanel')

    def __init__(self, parent = aspect2d, **kw):
        optiondefs = (('relief', None, None), ('doneEvent', None, None))
        self.defineoptions(kw, optiondefs)
        DirectFrame.__init__(self, parent=parent)
        self.cardList = []
        self.updateLayout()
        self.initialiseoptions(NPCFriendPanel)
        self.accept(localAvatar.uniqueName('maxNPCFriendsChange'), self.updateLayout)
        return None

    def update(self, friendDict, fCallable = 0):
        friendList = list(friendDict.keys())
        for i in range(self.maxNPCFriends):
            card = self.cardList[i]
            try:
                NPCID = friendList[i]
                count = friendDict[NPCID]
            except IndexError:
                NPCID = None
                count = 0

            card.update(NPCID, count, fCallable)

        return

    def updateLayout(self):
        for card in self.cardList:
            card.destroy()

        self.cardList = []
        self.maxNPCFriends = localAvatar.getMaxNPCFriends()
        rotateCard = False
        if self.maxNPCFriends == 8:
            rotateCard = True
            xOffset = -5.25
            yOffset = 2.3
            yOffset2 = -4.7
        elif self.maxNPCFriends == 16:
            xOffset = -5.2
            yOffset = 3.5
            yOffset2 = -2.45
        else:
            self.notify.error('got wrong max SOS cards %s' % self.maxNPCFriends)
        count = 0
        for i in range(self.maxNPCFriends):
            card = NPCFriendCard(parent=self, rotateCard=rotateCard, doneEvent=self['doneEvent'])
            self.cardList.append(card)
            card.setPos(xOffset, 1, yOffset)
            card.setScale(0.75)
            xOffset += 3.5
            count += 1
            if count % 4 == 0:
                xOffset = -5.25
                yOffset += yOffset2


class NPCFriendCard(DirectFrame):
    normalTextColor = (0.3, 0.25, 0.2, 1)
    maxRarity = 5
    sosTracks = ToontownBattleGlobals.Tracks + ToontownBattleGlobals.NPCTracks

    def __init__(self, parent = aspect2dp, rotateCard = False, **kw):
        optiondefs = (('NPCID', 'Uninitialized', None), ('relief', None, None), ('doneEvent', None, None))
        self.defineoptions(kw, optiondefs)
        DirectFrame.__init__(self, parent=parent)
        self.initialiseoptions(NPCFriendCard)
        cardModel = loader.loadModel('phase_3.5/models/gui/playingCard')
        self.front = DirectFrame(parent=self, relief=None, image=cardModel.find('**/card_front'))
        self.front.hide()
        self.back = DirectFrame(parent=self, relief=None, image=cardModel.find('**/card_back'), geom=cardModel.find('**/logo'))
        callButtonPosZ = -0.9
        textWordWrap = 16.0
        textScale = 0.35
        textPosZ = 1.15
        nameScale = 0.4
        namePosZ = -0.45
        rarityScale = 0.2
        rarityPosZ = -1.2
        self.NPCHeadDim = 1.2
        self.NPCHeadPosZ = 0.45
        self.sosCountInfoPosZ = -0.9
        self.sosCountInfoScale = 0.4
        self.sosCountInfo2PosZ = -0.9
        self.sosCountInfo2Scale = 0.5
        if rotateCard:
            self.front.component('image0').configure(pos=(0, 0, 0.22), hpr=(0, 0, -90), scale=1.35)
            self.back.component('image0').configure(hpr=(0, 0, -90), scale=(-1.35, 1.35, 1.35))
            callButtonPosZ = -2.1
            textWordWrap = 7.0
            textScale = 0.5
            textPosZ = 2.0
            nameScale = 0.5
            namePosZ = -0.89
            rarityScale = 0.25
            rarityPosZ = -2.4
            self.NPCHeadDim = 1.8
            self.NPCHeadPosZ = 0.4
            self.sosCountInfoPosZ = -2.1
            self.sosCountInfoScale = 0.4
            self.sosCountInfo2PosZ = -2.0
            self.sosCountInfo2Scale = 0.55
        self.sosTypeInfo = DirectLabel(parent=self.front, relief=None, text='', text_font=ToontownGlobals.getMinnieFont(), text_fg=self.normalTextColor, text_scale=textScale, text_align=TextNode.ACenter, text_wordwrap=textWordWrap, pos=(0, 0, textPosZ))
        self.NPCHead = None
        self.NPCName = DirectLabel(parent=self.front, relief=None, text='', text_fg=self.normalTextColor, text_scale=nameScale, text_align=TextNode.ACenter, text_wordwrap=8.0, pos=(0, 0, namePosZ))
        buttonModels = loader.loadModel('phase_3.5/models/gui/inventory_gui')
        upButton = buttonModels.find('**/InventoryButtonUp')
        downButton = buttonModels.find('**/InventoryButtonDown')
        rolloverButton = buttonModels.find('**/InventoryButtonRollover')
        self.sosCallButton = DirectButton(parent=self.front, relief=None, text=TTLocalizer.NPCCallButtonLabel, text_fg=self.normalTextColor, text_scale=0.28, text_align=TextNode.ACenter, image=(upButton,
         downButton,
         rolloverButton,
         upButton), image_color=(1.0, 0.2, 0.2, 1), image0_color=Vec4(1.0, 0.4, 0.4, 1), image3_color=Vec4(1.0, 0.4, 0.4, 0.4), image_scale=(4.4, 1, 3.6), image_pos=Vec3(0, 0, 0.08), pos=(-1.15, 0, callButtonPosZ), scale=1.25, command=self.__chooseNPCFriend)
        self.sosCallButton.hide()

        # Info Button on each card to inspect Trinkets & stats
        self.infoButton = DirectButton(
            parent=self.front,
            relief=DGG.RAISED,
            frameColor=(0.2, 0.5, 0.8, 0.9),
            borderWidth=(0.04, 0.04),
            text="?",
            text_scale=0.35,
            text_fg=(1, 1, 1, 1),
            text_shadow=(0, 0, 0, 1),
            text_font=ToontownGlobals.getSignFont(),
            pos=(1.25, 0, 1.15),
            scale=0.8,
            command=self.showTrinketDetails
        )

        self.sosCountInfo = DirectLabel(parent=self.front, relief=None, text='', text_fg=self.normalTextColor, text_scale=0.75, text_align=TextNode.ALeft, textMayChange=1, pos=(0.0, 0, -1.0))
        star = loader.loadModel('phase_3.5/models/gui/name_star')
        self.rarityStars = []
        for i in range(self.maxRarity):
            label = DirectLabel(parent=self.front, relief=None, image=star, image_scale=rarityScale, image_color=Vec4(0.502, 0.251, 0.251, 1.0), pos=(1.1 - i * 0.24, 0, rarityPosZ))
            label.hide()
            self.rarityStars.append(label)

        self.detailsDialog = None
        return

    def showTrinketDetails(self):
        npcId = self['NPCID']
        if not npcId:
            return
        
        if self.detailsDialog:
            self.detailsDialog.destroy()
            self.detailsDialog = None

        from toontown.toon.TrinketsConfig import get_trinket_info
        name = NPCToons.getNPCName(npcId) or f"Merc #{npcId}"
        track, level, hp, stars = NPCToons.getNPCTrackLevelHpRarity(npcId)
        profile = NPCToons.get_companion_profile(npcId)
        maxHp = profile['maxHp']
        trinketIds = profile['trinkets']

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
        mainTrack = trackNames.get(track, "Offensive")
        secTracks = [trackNames.get(t, "") for t in profile['preferredTracks'] if t != track]
        secStr = f" / {secTracks[0]}" if secTracks and secTracks[0] else ""

        # Modal Dialog Frame
        self.detailsDialog = DirectFrame(
            parent=aspect2d,
            relief=DGG.SUNKEN,
            frameColor=(0.10, 0.12, 0.20, 0.96),
            frameSize=(-0.55, 0.55, -0.45, 0.45),
            borderWidth=(0.015, 0.015),
            pos=(0, 0, 0)
        )

        title = DirectLabel(
            parent=self.detailsDialog,
            relief=None,
            text=f"{name} ({stars}-Star)",
            text_scale=0.055,
            text_fg=Vec4(0.3, 0.9, 1.0, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getSignFont(),
            pos=(0, 0, 0.35)
        )

        stats = DirectLabel(
            parent=self.detailsDialog,
            relief=None,
            text=f"Tier: {stars}-Star {tierTitle}  |  Max Laff: {maxHp} Laff\nSpecialty: {mainTrack}{secStr}  |  Duration: 5 Turns",
            text_scale=0.035,
            text_fg=Vec4(1, 1, 1, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getToonFont(),
            pos=(0, 0, 0.22)
        )

        trinketTitle = DirectLabel(
            parent=self.detailsDialog,
            relief=None,
            text="Equipped Predefined Trinkets:",
            text_scale=0.04,
            text_fg=Vec4(1, 0.85, 0.3, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getSignFont(),
            text_align=TextNode.ALeft,
            pos=(-0.48, 0, 0.10)
        )

        trinketTexts = []
        for t_id in trinketIds:
            if t_id != 0:
                t_info = get_trinket_info(t_id)
                if t_info:
                    trinketTexts.append(f"• {t_info['name']}:\n  {t_info['desc']}")

        descStr = "\n\n".join(trinketTexts) if trinketTexts else "Standard high-tier Gag distribution."

        trinketDesc = DirectLabel(
            parent=self.detailsDialog,
            relief=None,
            text=descStr,
            text_scale=0.032,
            text_fg=Vec4(0.9, 0.92, 0.95, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getToonFont(),
            text_align=TextNode.ALeft,
            text_wordwrap=28,
            pos=(-0.48, 0, 0.02)
        )

        closeBtn = DirectButton(
            parent=self.detailsDialog,
            relief=DGG.RAISED,
            frameColor=(0.8, 0.2, 0.2, 0.9),
            borderWidth=(0.01, 0.01),
            text="Close",
            text_scale=0.045,
            text_fg=(1, 1, 1, 1),
            text_shadow=(0, 0, 0, 1),
            text_font=ToontownGlobals.getToonFont(),
            pos=(0, 0, -0.36),
            command=self.__closeDetailsDialog,
            pad=(0.04, 0.015)
        )

    def __closeDetailsDialog(self):
        if self.detailsDialog:
            self.detailsDialog.destroy()
            self.detailsDialog = None

    def __chooseNPCFriend(self):
        if self.detailsDialog:
            self.detailsDialog.destroy()
            self.detailsDialog = None
        if self['NPCID'] and self['doneEvent']:
            doneStatus = {}
            doneStatus['mode'] = 'NPCFriend'
            doneStatus['friend'] = self['NPCID']
            messenger.send(self['doneEvent'], [doneStatus])

    def destroy(self):
        if self.detailsDialog:
            self.detailsDialog.destroy()
            self.detailsDialog = None
        if self.NPCHead:
            self.NPCHead.detachNode()
            self.NPCHead.delete()
        DirectFrame.destroy(self)

    def update(self, NPCID, count = 0, fCallable = 0):
        oldNPCID = self['NPCID']
        self['NPCID'] = NPCID
        if NPCID != oldNPCID:
            if self.NPCHead:
                self.NPCHead.detachNode()
                self.NPCHead.delete()
            if NPCID is None:
                self.showBack()
                return
            self.front.show()
            self.back.hide()
            self.NPCName['text'] = TTLocalizer.NPCToonNames[NPCID]
            self.NPCHead = self.createNPCToonHead(NPCID, dimension=self.NPCHeadDim)
            self.NPCHead.reparentTo(self.front)
            self.NPCHead.setZ(self.NPCHeadPosZ)
            track, level, hp, rarity = NPCToons.getNPCTrackLevelHpRarity(NPCID)
            sosText = self.sosTracks[track]
            if track == ToontownBattleGlobals.NPC_RESTOCK_GAGS:
                if level == -1:
                    sosText += ' All'
                else:
                    sosText += ' ' + self.sosTracks[level]
            sosText = TextEncoder.upper(sosText)
            self.sosTypeInfo['text'] = sosText
            for i in range(self.maxRarity):
                if i < rarity:
                    self.rarityStars[i].show()
                else:
                    self.rarityStars[i].hide()

        if fCallable:
            self.sosCallButton.show()
            self.sosCountInfo.setPos(-0.4, 0, self.sosCountInfoPosZ)
            self.sosCountInfo['text_scale'] = self.sosCountInfoScale
            self.sosCountInfo['text_align'] = TextNode.ALeft
        else:
            self.sosCallButton.hide()
            self.sosCountInfo.setPos(0, 0, self.sosCountInfo2PosZ)
            self.sosCountInfo['text_scale'] = self.sosCountInfo2Scale
            self.sosCountInfo['text_align'] = TextNode.ACenter
        if count > 0:
            countText = TTLocalizer.NPCFriendPanelRemaining % count
            self.sosCallButton['state'] = DGG.NORMAL
        else:
            countText = 'Unavailable'
            self.sosCallButton['state'] = DGG.DISABLED
        self.sosCountInfo['text'] = countText
        return

    def showFront(self):
        self.front.show()
        self.back.hide()

    def showBack(self):
        self.front.hide()
        self.back.show()

    def createNPCToonHead(self, NPCID, dimension = 0.5):
        NPCInfo = NPCToons.NPCToonDict[NPCID]
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
        s = dimension / biggest
        mid = (p1 + d / 2.0) * s
        geomXform = hidden.attachNewNode('geomXform')
        for child in geom.getChildren():
            child.reparentTo(geomXform)

        geomXform.setPosHprScale(-mid[0], -mid[1] + 1, -mid[2], 180, 0, 0, s, s, s)
        geomXform.reparentTo(geom)
