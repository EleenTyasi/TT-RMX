from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from direct.gui.DirectGui import *
from panda3d.core import *
CatalogNotifyBaseXPos = -0.933333

class CatalogNotifyDialog:
    notify = DirectNotifyGlobal.directNotify.newCategory('CatalogNotifyDialog')

    def __init__(self, message):
        # Old yeller treatment: Completely neutralized
        self.message = message
        self.messageIndex = 0
        self.frame = None
        self.nextButton = None
        self.doneButton = None
        return

    def handleButton(self):
        self.messageIndex += 1
        if self.messageIndex >= len(self.message):
            self.cleanup()
            return
        self.frame['text'] = self.message[self.messageIndex]
        if self.messageIndex + 1 == len(self.message):
            self.nextButton.hide()
            self.doneButton.show()

    def cleanup(self):
        if self.frame:
            self.frame.destroy()
        self.frame = None
        if self.nextButton:
            self.nextButton.destroy()
        self.nextButton = None
        if self.doneButton:
            self.doneButton.destroy()
        self.doneButton = None
        return

    def __handleButton(self, value):
        self.cleanup()
