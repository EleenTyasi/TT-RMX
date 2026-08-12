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
        
        # Title
        self.titleLabel = DirectLabel(
            parent=self, relief=None, text='TRINKET EQUIPMENT',
            text_scale=0.1, text_font=ToontownGlobals.getSignFont(),
            text_fg=(0, 0.4, 0.8, 1), pos=(0, 0, 0.6)
        )

        # --- Left Panel: Equipped Slots ---
        self.leftFrame = DirectFrame(
            parent=self, relief=DGG.RIDGE, pos=(-0.45, 0, 0),
            frameSize=(-0.42, 0.42, -0.55, 0.5), frameColor=(0.85, 0.9, 1, 0.6)
        )

        # Slot 1
        self.slot1Title = DirectLabel(
            parent=self.leftFrame, relief=None, text='SLOT 1',
            text_scale=0.06, text_font=ToontownGlobals.getMinnieFont(),
            text_fg=(0.2, 0.2, 0.6, 1), pos=(0, 0, 0.4)
        )
        self.slot1Text = DirectLabel(
            parent=self.leftFrame, relief=None, text='Empty',
            text_scale=0.045, text_wordwrap=15, text_align=TextNode.ACenter,
            pos=(0, 0, 0.28)
        )
        self.slot1Btn = DirectButton(
            parent=self.leftFrame, relief=DGG.RAISED, text='Unequip 1',
            text_scale=0.04, pos=(0, 0, 0.12), scale=(1.1, 1, 1),
            command=self.__unequipSlot, extraArgs=[0]
        )

        # Slot 2
        self.slot2Title = DirectLabel(
            parent=self.leftFrame, relief=None, text='SLOT 2',
            text_scale=0.06, text_font=ToontownGlobals.getMinnieFont(),
            text_fg=(0.2, 0.2, 0.6, 1), pos=(0, 0, -0.05)
        )
        self.slot2Text = DirectLabel(
            parent=self.leftFrame, relief=None, text='Empty',
            text_scale=0.045, text_wordwrap=15, text_align=TextNode.ACenter,
            pos=(0, 0, -0.17)
        )
        self.slot2Btn = DirectButton(
            parent=self.leftFrame, relief=DGG.RAISED, text='Unequip 2',
            text_scale=0.04, pos=(0, 0, -0.33), scale=(1.1, 1, 1),
            command=self.__unequipSlot, extraArgs=[1]
        )

        # --- Bottom Progress Label ---
        self.progressLabel = DirectLabel(
            parent=self.leftFrame, relief=None, text='Cogs Defeated: 0/5',
            text_scale=0.045, text_fg=(0, 0.5, 0, 1), pos=(0, 0, -0.48)
        )

        # --- Right Panel: Inventory List ---
        self.rightFrame = DirectFrame(
            parent=self, relief=DGG.RIDGE, pos=(0.45, 0, 0),
            frameSize=(-0.42, 0.42, -0.55, 0.5), frameColor=(0.95, 0.95, 0.95, 0.6)
        )

        self.inventoryTitle = DirectLabel(
            parent=self.rightFrame, relief=None, text='COLLECTION',
            text_scale=0.06, text_font=ToontownGlobals.getMinnieFont(),
            text_fg=(0.3, 0.3, 0.3, 1), pos=(0, 0, 0.4)
        )

        self.guiModels = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        scrollUp = self.guiModels.find('**/FndsLst_ScrollUp')
        scrollDown = self.guiModels.find('**/FndsLst_ScrollDN')
        scrollRollover = self.guiModels.find('**/FndsLst_ScrollUp_Rllvr')

        self.inventoryList = DirectScrolledList(
            parent=self.rightFrame, relief=None, pos=(0, 0, -0.05),
            incButton_image=(scrollUp, scrollDown, scrollRollover, scrollUp),
            incButton_relief=None, incButton_pos=(0, 0, -0.42), incButton_scale=(1.0, 1.0, -1.0),
            decButton_image=(scrollUp, scrollDown, scrollRollover, scrollUp),
            decButton_relief=None, decButton_pos=(0, 0, 0.38),
            itemFrame_pos=(0, 0, 0), itemFrame_relief=None, numItemsVisible=4
        )

    def unload(self):
        if self.guiModels:
            self.guiModels.removeNode()
            self.guiModels = None
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

        # Update Slot 1
        t1_info = get_trinket_info(slots[0])
        if t1_info:
            self.slot1Text['text'] = f"{t1_info['name']}\n\n{t1_info['desc']}"
            self.slot1Btn.show()
        else:
            self.slot1Text['text'] = "Empty Slot"
            self.slot1Btn.hide()

        # Update Slot 2
        t2_info = get_trinket_info(slots[1])
        if t2_info:
            self.slot2Text['text'] = f"{t2_info['name']}\n\n{t2_info['desc']}"
            self.slot2Btn.show()
        else:
            self.slot2Text['text'] = "Empty Slot"
            self.slot2Btn.hide()

        # Progress
        self.progressLabel['text'] = f"Cogs Defeated: {cog_kills}/5"

        # Update Inventory List
        self.inventoryList.removeAndDestroyAllItems()
        for t_id in ALL_TRINKET_IDS:
            info = get_trinket_info(t_id)
            if not info:
                continue

            itemFrame = DirectFrame(relief=DGG.GROOVE, frameSize=(-0.38, 0.38, -0.07, 0.07), frameColor=(0.9, 0.9, 0.95, 1))

            if t_id in unlocked:
                nameLbl = DirectLabel(
                    parent=itemFrame, relief=None, text=info['name'],
                    text_scale=0.04, text_font=ToontownGlobals.getMinnieFont(),
                    text_align=TextNode.ALeft, pos=(-0.36, 0, 0.02)
                )
                descLbl = DirectLabel(
                    parent=itemFrame, relief=None, text=info['desc'],
                    text_scale=0.03, text_wordwrap=18, text_align=TextNode.ALeft,
                    pos=(-0.36, 0, -0.02)
                )
                btn1 = DirectButton(
                    parent=itemFrame, relief=DGG.RAISED, text='Eq 1',
                    text_scale=0.035, pos=(0.24, 0, 0.02),
                    command=self.__equipSlot, extraArgs=[0, t_id]
                )
                btn2 = DirectButton(
                    parent=itemFrame, relief=DGG.RAISED, text='Eq 2',
                    text_scale=0.035, pos=(0.32, 0, 0.02),
                    command=self.__equipSlot, extraArgs=[1, t_id]
                )
            else:
                nameLbl = DirectLabel(
                    parent=itemFrame, relief=None, text='??? (Locked)',
                    text_scale=0.04, text_fg=(0.5, 0.5, 0.5, 1),
                    text_align=TextNode.ALeft, pos=(-0.36, 0, 0.01)
                )
                descLbl = DirectLabel(
                    parent=itemFrame, relief=None, text='Defeat Cogs to unlock this Trinket!',
                    text_scale=0.03, text_fg=(0.6, 0.6, 0.6, 1), text_align=TextNode.ALeft,
                    pos=(-0.36, 0, -0.03)
                )

            self.inventoryList.addItem(itemFrame)

    def __equipSlot(self, slot_idx, trinket_id):
        base.localAvatar.sendUpdate('requestEquipTrinket', [slot_idx, trinket_id])
        taskMgr.doMethodLater(0.2, lambda task: self.updatePage(), 'updateTrinketPage')

    def __unequipSlot(self, slot_idx):
        base.localAvatar.sendUpdate('requestEquipTrinket', [slot_idx, 0])
        taskMgr.doMethodLater(0.2, lambda task: self.updatePage(), 'updateTrinketPage')
