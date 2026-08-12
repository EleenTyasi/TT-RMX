# =============================================================================
#  EventsPage.py — Repurposed into TrinketPage (Stickerbook Equipment UI)
#  TT-RMX Personal Tinkering Project
# =============================================================================

from panda3d.core import Vec4, TextNode
from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton, DirectScrolledList, DGG
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import TTLocalizer, ToontownGlobals
from toontown.toon.TrinketsConfig import TRINKET_CATALOG, ALL_TRINKET_IDS, get_trinket_info
from . import ShtikerPage

class EventsPage(ShtikerPage.ShtikerPage):
    notify = DirectNotifyGlobal.directNotify.newCategory('EventsPage')

    def __init__(self):
        ShtikerPage.ShtikerPage.__init__(self)
        self.titleLabel = None
        self.leftFrame = None
        self.rightFrame = None
        self.guiModels = None
        self.inventoryList = None

    def load(self):
        ShtikerPage.ShtikerPage.load(self)
        
        # Main Title Header
        self.titleLabel = DirectLabel(
            parent=self, relief=None, text='TRINKET EQUIPMENT',
            text_scale=0.095, text_font=ToontownGlobals.getSignFont(),
            text_fg=(0.1, 0.3, 0.7, 1), text_shadow=(1, 1, 1, 0.8),
            pos=(0, 0, 0.6)
        )

        # --- Left Panel: Equipped Slots Frame ---
        self.leftFrame = DirectFrame(
            parent=self, relief=DGG.GROOVE, pos=(-0.44, 0, -0.02),
            frameSize=(-0.41, 0.41, -0.54, 0.52), frameColor=(0.92, 0.95, 1.0, 0.85),
            borderWidth=(0.015, 0.015)
        )

        # --- Slot 1 Card ---
        self.slot1Card = DirectFrame(
            parent=self.leftFrame, relief=DGG.RIDGE, pos=(0, 0, 0.25),
            frameSize=(-0.37, 0.37, -0.21, 0.21), frameColor=(1.0, 1.0, 1.0, 0.95),
            borderWidth=(0.01, 0.01)
        )
        self.slot1Header = DirectFrame(
            parent=self.slot1Card, relief=DGG.FLAT, pos=(0, 0, 0.15),
            frameSize=(-0.37, 0.37, -0.05, 0.05), frameColor=(0.2, 0.45, 0.85, 1.0)
        )
        self.slot1Title = DirectLabel(
            parent=self.slot1Header, relief=None, text='SLOT 1',
            text_scale=0.055, text_font=ToontownGlobals.getMinnieFont(),
            text_fg=(1, 1, 1, 1), pos=(0, 0, -0.015)
        )
        self.slot1Text = DirectLabel(
            parent=self.slot1Card, relief=None, text='Empty Slot',
            text_scale=0.038, text_wordwrap=18, text_align=TextNode.ACenter,
            text_fg=(0.2, 0.2, 0.2, 1), pos=(0, 0, 0.04)
        )
        self.slot1Btn = DirectButton(
            parent=self.slot1Card, relief=DGG.RAISED, text='Unequip',
            text_scale=0.035, text_font=ToontownGlobals.getInterfaceFont(),
            text_fg=(0.8, 0.1, 0.1, 1), frameSize=(-0.14, 0.14, -0.035, 0.045),
            pos=(0, 0, -0.14), frameColor=(0.95, 0.9, 0.9, 1),
            command=self.__unequipSlot, extraArgs=[0]
        )

        # --- Slot 2 Card ---
        self.slot2Card = DirectFrame(
            parent=self.leftFrame, relief=DGG.RIDGE, pos=(0, 0, -0.20),
            frameSize=(-0.37, 0.37, -0.21, 0.21), frameColor=(1.0, 1.0, 1.0, 0.95),
            borderWidth=(0.01, 0.01)
        )
        self.slot2Header = DirectFrame(
            parent=self.slot2Card, relief=DGG.FLAT, pos=(0, 0, 0.15),
            frameSize=(-0.37, 0.37, -0.05, 0.05), frameColor=(0.2, 0.45, 0.85, 1.0)
        )
        self.slot2Title = DirectLabel(
            parent=self.slot2Header, relief=None, text='SLOT 2',
            text_scale=0.055, text_font=ToontownGlobals.getMinnieFont(),
            text_fg=(1, 1, 1, 1), pos=(0, 0, -0.015)
        )
        self.slot2Text = DirectLabel(
            parent=self.slot2Card, relief=None, text='Empty Slot',
            text_scale=0.038, text_wordwrap=18, text_align=TextNode.ACenter,
            text_fg=(0.2, 0.2, 0.2, 1), pos=(0, 0, 0.04)
        )
        self.slot2Btn = DirectButton(
            parent=self.slot2Card, relief=DGG.RAISED, text='Unequip',
            text_scale=0.035, text_font=ToontownGlobals.getInterfaceFont(),
            text_fg=(0.8, 0.1, 0.1, 1), frameSize=(-0.14, 0.14, -0.035, 0.045),
            pos=(0, 0, -0.14), frameColor=(0.95, 0.9, 0.9, 1),
            command=self.__unequipSlot, extraArgs=[1]
        )

        # --- Bottom Progress Banner ---
        self.progressFrame = DirectFrame(
            parent=self.leftFrame, relief=DGG.GROOVE, pos=(0, 0, -0.47),
            frameSize=(-0.37, 0.37, -0.045, 0.045), frameColor=(0.9, 0.98, 0.9, 1)
        )
        self.progressLabel = DirectLabel(
            parent=self.progressFrame, relief=None, text='Cogs Defeated: 0/5',
            text_scale=0.038, text_font=ToontownGlobals.getMinnieFont(),
            text_fg=(0.1, 0.5, 0.1, 1), pos=(0, 0, -0.012)
        )

        # --- Right Panel: Collection Catalog ---
        self.rightFrame = DirectFrame(
            parent=self, relief=DGG.GROOVE, pos=(0.44, 0, -0.02),
            frameSize=(-0.41, 0.41, -0.54, 0.52), frameColor=(0.96, 0.96, 0.96, 0.85),
            borderWidth=(0.015, 0.015)
        )

        self.inventoryTitle = DirectLabel(
            parent=self.rightFrame, relief=None, text='TRINKET COLLECTION',
            text_scale=0.055, text_font=ToontownGlobals.getMinnieFont(),
            text_fg=(0.2, 0.3, 0.4, 1), pos=(0, 0, 0.45)
        )

        # Scrolled List with Explicit ForceHeight for Clean Spacing
        self.inventoryList = DirectScrolledList(
            parent=self.rightFrame, relief=None, pos=(0, 0, 0.02),
            frameSize=(-0.39, 0.39, -0.48, 0.38),
            decButton_relief=DGG.RAISED, decButton_text='SCROLL UP',
            decButton_text_scale=0.032, decButton_text_font=ToontownGlobals.getInterfaceFont(),
            decButton_pos=(0, 0, 0.37), decButton_scale=(1.2, 1, 0.9),
            decButton_frameSize=(-0.26, 0.26, -0.025, 0.035),
            incButton_relief=DGG.RAISED, incButton_text='SCROLL DOWN',
            incButton_text_scale=0.032, incButton_text_font=ToontownGlobals.getInterfaceFont(),
            incButton_pos=(0, 0, -0.46), incButton_scale=(1.2, 1, 0.9),
            incButton_frameSize=(-0.26, 0.26, -0.025, 0.035),
            itemFrame_pos=(0, 0, 0.24), itemFrame_relief=None,
            numItemsVisible=5, forceHeight=0.135
        )

    def unload(self):
        ShtikerPage.ShtikerPage.unload(self)

    def enter(self):
        ShtikerPage.ShtikerPage.enter(self)
        self.updatePage()

    def updatePage(self):
        toon = base.localAvatar
        if not toon:
            return

        slots = toon.getTrinketSlots()
        unlocked = toon.getUnlockedTrinkets()
        cog_kills = toon.getCogKillsCount()

        # Slot 1 Update
        t1_info = get_trinket_info(slots[0])
        if t1_info:
            self.slot1Text['text'] = f"{t1_info['name']}\n{t1_info['desc']}"
            self.slot1Text['text_fg'] = (0.1, 0.3, 0.6, 1)
            self.slot1Btn.show()
        else:
            self.slot1Text['text'] = "Empty Slot"
            self.slot1Text['text_fg'] = (0.5, 0.5, 0.5, 1)
            self.slot1Btn.hide()

        # Slot 2 Update
        t2_info = get_trinket_info(slots[1])
        if t2_info:
            self.slot2Text['text'] = f"{t2_info['name']}\n{t2_info['desc']}"
            self.slot2Text['text_fg'] = (0.1, 0.3, 0.6, 1)
            self.slot2Btn.show()
        else:
            self.slot2Text['text'] = "Empty Slot"
            self.slot2Text['text_fg'] = (0.5, 0.5, 0.5, 1)
            self.slot2Btn.hide()

        # Progress Update
        self.progressLabel['text'] = f"Cogs Defeated: {cog_kills}/5"

        # Catalog List Update
        self.inventoryList.removeAndDestroyAllItems()
        for t_id in ALL_TRINKET_IDS:
            info = get_trinket_info(t_id)
            if not info:
                continue

            is_unlocked = t_id in unlocked
            is_eq1 = (slots[0] == t_id)
            is_eq2 = (slots[1] == t_id)

            if is_eq1 or is_eq2:
                bgColor = (0.88, 0.98, 0.88, 1.0)
            elif is_unlocked:
                bgColor = (0.95, 0.97, 1.0, 1.0)
            else:
                bgColor = (0.9, 0.9, 0.9, 0.7)

            itemFrame = DirectFrame(
                relief=DGG.RIDGE, frameSize=(-0.36, 0.36, -0.06, 0.06),
                frameColor=bgColor, borderWidth=(0.008, 0.008)
            )

            if is_unlocked:
                nameLbl = DirectLabel(
                    parent=itemFrame, relief=None, text=info['name'],
                    text_scale=0.036, text_font=ToontownGlobals.getMinnieFont(),
                    text_align=TextNode.ALeft, text_fg=(0.1, 0.25, 0.6, 1),
                    pos=(-0.34, 0, 0.015)
                )
                descLbl = DirectLabel(
                    parent=itemFrame, relief=None, text=info['desc'],
                    text_scale=0.026, text_wordwrap=18, text_align=TextNode.ALeft,
                    text_fg=(0.25, 0.25, 0.25, 1), pos=(-0.34, 0, -0.025)
                )

                if is_eq1:
                    eqLbl = DirectLabel(
                        parent=itemFrame, relief=DGG.FLAT, text='EQUIPPED S1',
                        text_scale=0.028, text_fg=(0.1, 0.5, 0.1, 1),
                        frameColor=(0.8, 0.95, 0.8, 1), pos=(0.24, 0, -0.005)
                    )
                elif is_eq2:
                    eqLbl = DirectLabel(
                        parent=itemFrame, relief=DGG.FLAT, text='EQUIPPED S2',
                        text_scale=0.028, text_fg=(0.1, 0.5, 0.1, 1),
                        frameColor=(0.8, 0.95, 0.8, 1), pos=(0.24, 0, -0.005)
                    )
                else:
                    btn1 = DirectButton(
                        parent=itemFrame, relief=DGG.RAISED, text='Eq 1',
                        text_scale=0.03, pos=(0.18, 0, -0.005),
                        frameSize=(-0.06, 0.06, -0.03, 0.045),
                        command=self.__equipSlot, extraArgs=[0, t_id]
                    )
                    btn2 = DirectButton(
                        parent=itemFrame, relief=DGG.RAISED, text='Eq 2',
                        text_scale=0.03, pos=(0.30, 0, -0.005),
                        frameSize=(-0.06, 0.06, -0.03, 0.045),
                        command=self.__equipSlot, extraArgs=[1, t_id]
                    )
            else:
                nameLbl = DirectLabel(
                    parent=itemFrame, relief=None, text='??? (Locked)',
                    text_scale=0.036, text_font=ToontownGlobals.getMinnieFont(),
                    text_fg=(0.45, 0.45, 0.45, 1), text_align=TextNode.ALeft,
                    pos=(-0.34, 0, 0.015)
                )
                descLbl = DirectLabel(
                    parent=itemFrame, relief=None, text='Defeat 5 Cogs to unlock this Trinket!',
                    text_scale=0.026, text_fg=(0.55, 0.55, 0.55, 1),
                    text_align=TextNode.ALeft, pos=(-0.34, 0, -0.025)
                )

            self.inventoryList.addItem(itemFrame)

    def __equipSlot(self, slot_idx, trinket_id):
        base.localAvatar.sendUpdate('requestEquipTrinket', [slot_idx, trinket_id])
        taskMgr.doMethodLater(0.15, lambda task: self.updatePage(), 'updateTrinketPage')

    def __unequipSlot(self, slot_idx):
        base.localAvatar.sendUpdate('requestEquipTrinket', [slot_idx, 0])
        taskMgr.doMethodLater(0.15, lambda task: self.updatePage(), 'updateTrinketPage')
