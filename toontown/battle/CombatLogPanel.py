# =============================================================================
#  CombatLogPanel.py  —  In-Game Purple-Hued Combat Log UI (TT-RMX)
#  Tracks all Toon & Cog battle actions, crits, status effects & damage
# =============================================================================

from panda3d.core import *
from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject
from toontown.toonbase import ToontownGlobals, TTLocalizer

# Color palette for log message types
COLOR_SYSTEM = Vec4(0.85, 0.65, 1.0, 1.0)       # Purple / Header
COLOR_TOON = Vec4(0.3, 0.95, 0.3, 1.0)          # Green / Toon attacks
COLOR_HEAL = Vec4(0.2, 0.85, 1.0, 1.0)          # Cyan / Toon-Up
COLOR_COG = Vec4(1.0, 0.4, 0.4, 1.0)            # Red / Cog attacks
COLOR_STATUS = Vec4(1.0, 0.85, 0.2, 1.0)        # Gold / Status effect procs & DoTs
COLOR_DEFENSE = Vec4(0.4, 0.7, 1.0, 1.0)        # Blue / Block & Shield
COLOR_MISS = Vec4(0.75, 0.75, 0.75, 1.0)        # Gray / Misses & Dodges

_GLOBAL_COMBAT_LOG_PANEL = None

def getCombatLog():
    global _GLOBAL_COMBAT_LOG_PANEL
    return _GLOBAL_COMBAT_LOG_PANEL

def logCombatEvent(text, color=None):
    global _GLOBAL_COMBAT_LOG_PANEL
    if _GLOBAL_COMBAT_LOG_PANEL:
        _GLOBAL_COMBAT_LOG_PANEL.addEntry(text, color)
    else:
        messenger.send('combat-log-entry', [text, color])


class CombatLogPanel(DirectObject):
    def __init__(self):
        DirectObject.__init__(self)
        global _GLOBAL_COMBAT_LOG_PANEL
        _GLOBAL_COMBAT_LOG_PANEL = self

        self.entries = []
        self.isOpen = False

        # Load GUI assets for buttons
        gui = loader.loadModel('phase_3.5/models/gui/chat_input_gui')
        btn_up = gui.find('**/ChtBx_ChtBtn_UP')
        btn_dn = gui.find('**/ChtBx_ChtBtn_DN')
        btn_rlvr = gui.find('**/ChtBx_ChtBtn_RLVR')

        # Purple SpeedChat-style button in top-left
        self.logButton = DirectButton(
            image=(btn_up, btn_dn, btn_rlvr),
            pos=(0.34, 0, -0.072),
            parent=base.a2dTopLeft,
            scale=1.179,
            relief=None,
            image_color=Vec4(0.78, 0.35, 0.95, 1.0),
            text=('', 'Log', 'Log'),
            text_scale=0.06,
            text_fg=Vec4(1, 1, 1, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_pos=(0, -0.09),
            textMayChange=0,
            sortOrder=DGG.FOREGROUND_SORT_INDEX,
            command=self.toggleLog,
        )

        # Popup Log Frame
        self.frame = DirectFrame(
            parent=base.a2dTopLeft,
            relief=None,
            image=DGG.getDefaultDialogGeom(),
            image_scale=(1.45, 1.0, 1.05),
            image_pos=(0.74, 0, -0.62),
            image_color=Vec4(0.10, 0.08, 0.14, 0.92),
            sortOrder=DGG.FOREGROUND_SORT_INDEX + 1,
        )

        # Title Label
        self.titleLabel = DirectLabel(
            parent=self.frame,
            relief=None,
            pos=(0.74, 0, -0.15),
            text='Combat Log',
            text_scale=0.055,
            text_fg=Vec4(0.9, 0.7, 1.0, 1.0),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getSignFont(),
        )

        # Close / Minimize Button
        closeBtnGui = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        close_up = closeBtnGui.find('**/CloseBtn_UP')
        close_dn = closeBtnGui.find('**/CloseBtn_DN')
        close_rlvr = closeBtnGui.find('**/CloseBtn_Rllvr')

        self.closeButton = DirectButton(
            parent=self.frame,
            image=(close_up, close_dn, close_rlvr),
            pos=(1.40, 0, -0.15),
            scale=0.75,
            relief=None,
            command=self.hideLog,
        )

        # Clear Button
        self.clearButton = DirectButton(
            parent=self.frame,
            relief=DGG.RAISED,
            borderWidth=(0.005, 0.005),
            frameColor=(0.3, 0.2, 0.4, 0.8),
            pos=(0.12, 0, -0.15),
            scale=0.7,
            text='Clear',
            text_scale=0.045,
            text_fg=(1, 1, 1, 1),
            text_pos=(0, -0.012),
            command=self.clearLog,
        )

        # Scrolled list of combat messages
        self.scrolledList = DirectScrolledList(
            parent=self.frame,
            relief=None,
            pos=(0.08, 0, -0.22),
            items=[],
            numItemsVisible=14,
            forceHeight=0.052,
            itemMakeFunction=None,
            itemMakeExtraArgs=[],
            decButton_pos=(0.66, 0, 0.02),
            decButton_image=(btn_up, btn_dn, btn_rlvr),
            decButton_image_scale=(0.5, 0.5, 0.5),
            decButton_image_color=Vec4(0.8, 0.4, 0.9, 1.0),
            decButton_relief=None,
            incButton_pos=(0.66, 0, -0.76),
            incButton_image=(btn_up, btn_dn, btn_rlvr),
            incButton_image_scale=(0.5, 0.5, 0.5),
            incButton_image_color=Vec4(0.8, 0.4, 0.9, 1.0),
            incButton_relief=None,
        )

        gui.removeNode()
        closeBtnGui.removeNode()

        self.frame.hide()

        # Listen for battle and combat log messenger events
        self.accept('combat-log-entry', self.addEntry)
        self.accept('f9', self.toggleLog)

    def showButton(self):
        if hasattr(self, 'logButton') and self.logButton:
            self.logButton.show()

    def hideButton(self):
        if hasattr(self, 'logButton') and self.logButton:
            self.logButton.hide()

    def toggleLog(self):
        if self.isOpen:
            self.hideLog()
        else:
            self.showLog()

    def showLog(self):
        self.frame.show()
        self.isOpen = True
        self.scrollToBottom()

    def hideLog(self):
        self.frame.hide()
        self.isOpen = False

    def clearLog(self):
        for item in self.scrolledList['items']:
            item.destroy()
        self.scrolledList['items'] = []
        self.scrolledList.refresh()
        self.entries = []
        self.addEntry('--- Combat Log Cleared ---', COLOR_SYSTEM)

    def addEntry(self, text, color=None):
        if color is None:
            color = COLOR_SYSTEM

        lbl = DirectLabel(
            relief=None,
            text=text,
            text_scale=0.038,
            text_align=TextNode.ALeft,
            text_fg=color,
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getToonFont(),
            text_wordwrap=33,
        )

        self.entries.append((text, color))
        if len(self.entries) > 150:
            old = self.scrolledList['items'].pop(0)
            old.destroy()
            self.entries.pop(0)

        self.scrolledList.addItem(lbl)
        self.scrollToBottom()

    def scrollToBottom(self):
        num_items = len(self.scrolledList['items'])
        visible = self.scrolledList['numItemsVisible']
        if num_items > visible:
            self.scrolledList.scrollTo(num_items - visible)

    def destroy(self):
        self.ignoreAll()
        global _GLOBAL_COMBAT_LOG_PANEL
        if _GLOBAL_COMBAT_LOG_PANEL == self:
            _GLOBAL_COMBAT_LOG_PANEL = None
        if hasattr(self, 'frame') and self.frame:
            self.frame.destroy()
            self.frame = None
        if hasattr(self, 'logButton') and self.logButton:
            self.logButton.destroy()
            self.logButton = None
