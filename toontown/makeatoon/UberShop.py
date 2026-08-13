from panda3d.core import *
from direct.fsm import StateData
from direct.gui.DirectGui import *
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from toontown.toontowngui import TTDialog
from .MakeAToonGlobals import *
from direct.directnotify import DirectNotifyGlobal

class UberShop(StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('UberShop')

    def __init__(self, makeAToon, doneEvent):
        StateData.StateData.__init__(self, doneEvent)
        self.makeAToon = makeAToon
        self.laffCap = 0  # 0 = Unrestricted / Normal
        self.buttons = []
        self.warningDialog = None
        self.warningStep = 0

    def enter(self):
        base.disableMouse()
        self.accept('next', self.__handleForward)
        self.accept('last', self.__handleBackward)
        self.showButtons()

    def exit(self):
        self.ignore('next')
        self.ignore('last')
        self.hideButtons()
        self.cleanupWarningDialog()

    def __handleForward(self):
        self.doneStatus = 'next'
        messenger.send(self.doneEvent)

    def __handleBackward(self):
        self.doneStatus = 'last'
        messenger.send(self.doneEvent)

    def load(self):
        self.container = aspect2d.attachNewNode('uberShopContainer')
        
        self.subLabel = DirectLabel(
            parent=self.container,
            relief=None,
            text="Select an optional maximum Laff limit for your Toon.\nNormal Toons select Unrestricted.",
            text_font=ToontownGlobals.getInterfaceFont(),
            text_scale=0.045,
            text_fg=(1, 1, 1, 1),
            text_shadow=(0, 0, 0, 1),
            pos=(0, 0, 0.45)
        )

        # Options: (Laff Cap Value, Label Text, Color)
        capOptions = [
            (1, "1 Laff", (1, 0.3, 0.3, 1)),
            (5, "5 Laff", (1, 0.6, 0.3, 1)),
            (15, "15 Laff", (1, 0.8, 0.3, 1)),
            (25, "25 Laff", (0.8, 1, 0.3, 1)),
            (34, "34 Laff", (0.2, 1, 0.4, 1)),
            (40, "40 Laff", (0.2, 0.8, 1, 1)),
            (0, "Unrestricted", (0.9, 0.9, 0.9, 1))
        ]

        gui = loader.loadModel('phase_3/models/gui/quit_button')
        btnUp = gui.find('**/QuitBtn_UP')
        btnDn = gui.find('**/QuitBtn_DN')
        btnRl = gui.find('**/QuitBtn_RLVR')

        self.buttons = []
        
        for idx, (capVal, capText, color) in enumerate(capOptions):
            row = idx // 2
            col = idx % 2
            posX = -0.35 if col == 0 else 0.35
            posY = 0.3 - (row * 0.16)
            if idx == 6:  # Unrestricted centered at bottom
                posX = 0.0
                posY = 0.3 - (3 * 0.16)

            btn = DirectButton(
                parent=self.container,
                relief=None,
                image=(btnUp, btnDn, btnRl),
                image_scale=(1.4, 1.0, 1.0),
                text=capText,
                text_font=ToontownGlobals.getInterfaceFont(),
                text_scale=0.055,
                text_pos=(0, -0.015),
                text_fg=color,
                text_shadow=(0, 0, 0, 1),
                pos=(posX, 0, posY),
                command=self.selectCap,
                extraArgs=[capVal]
            )
            self.buttons.append((capVal, btn))

        gui.removeNode()
        self.container.hide()
        self.highlightSelected()

    def unload(self):
        self.cleanupWarningDialog()
        if hasattr(self, 'container') and self.container:
            self.container.removeNode()
            self.container = None
        self.buttons = []

    def showButtons(self):
        if hasattr(self, 'container') and self.container:
            self.container.show()
            self.highlightSelected()

    def hideButtons(self):
        if hasattr(self, 'container') and self.container:
            self.container.hide()

    def selectCap(self, capVal):
        if capVal == 1 and self.laffCap != 1:
            self.startOneLaffWarningSequence()
        else:
            self.laffCap = capVal
            self.makeAToon.laffCap = capVal
            self.highlightSelected()

    def highlightSelected(self):
        for capVal, btn in self.buttons:
            if capVal == self.laffCap:
                btn['text_scale'] = 0.065
                btn['text_shadow'] = (1, 1, 0, 1)
            else:
                btn['text_scale'] = 0.055
                btn['text_shadow'] = (0, 0, 0, 1)

    def cleanupWarningDialog(self):
        if self.warningDialog:
            self.warningDialog.cleanup()
            self.warningDialog = None

    def startOneLaffWarningSequence(self):
        self.warningStep = 1
        self.showWarningStage(1)

    def showWarningStage(self, step):
        self.cleanupWarningDialog()
        self.warningStep = step

        if step == 1:
            msg = "1st WARNING: 1 Laff Ubers can be defeated in a single hit by almost any Cog!\nAre you sure you want to attempt this extreme challenge?"
            btnText = "I Understand..."
        elif step == 2:
            msg = "2nd WARNING: You will have only 1 hit point for your ENTIRE Toontown career!\nOne miss or trap will defeat you immediately."
            btnText = "I Know What I'm Doing..."
        elif step == 3:
            msg = "3rd WARNING: This mode requires maximum skill, strategy, and teamwork!\nDo you still wish to proceed with 1 Laff?"
            btnText = "Give Me The 1 Laff!"
        elif step == 4:
            msg = "FINAL CONFIRMATION: Lock in 1 Laff Cap for this Toon?"
            btnText = "LOCK IN 1 LAFF!"
        else:
            self.laffCap = 1
            self.makeAToon.laffCap = 1
            self.highlightSelected()
            return

        self.warningDialog = TTDialog.TTGlobalDialog(
            doneEvent='uberWarningDone',
            message=msg,
            style=TTDialog.Acknowledge,
            okButtonText=btnText,
            command=self.__handleWarningResponse
        )
        self.warningDialog.show()

    def __handleWarningResponse(self, value):
        if self.warningStep < 4:
            self.showWarningStage(self.warningStep + 1)
        else:
            self.cleanupWarningDialog()
            self.laffCap = 1
            self.makeAToon.laffCap = 1
            self.highlightSelected()
