# TrackSelectionFrame.py — Modal dialog for choosing a new Gag Track upon level up

from direct.gui.DirectGui import *
from panda3d.core import *
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownBattleGlobals
from toontown.toonbase import TTLocalizer

class TrackSelectionFrame(DirectFrame):
    def __init__(self, choicesLeft=1, doneCallback=None):
        DirectFrame.__init__(
            self,
            parent=aspect2d,
            relief=DGG.GROOVE,
            state=DGG.NORMAL,
            frameColor=(0.1, 0.1, 0.15, 0.92),
            frameSize=(-0.7, 0.7, -0.6, 0.6),
            pos=(0, 0, 0)
        )
        self.choicesLeft = choicesLeft
        self.doneCallback = doneCallback
        self.buttons = []

        # Title Label
        self.title = DirectLabel(
            parent=self,
            relief=None,
            pos=(0, 0, 0.45),
            text="LEVEL UP! CHOOSE A GAG TRACK",
            text_scale=0.07,
            text_fg=(1, 0.9, 0.2, 1),
            text_font=ToontownGlobals.getSignFont(),
            text_shadow=(0, 0, 0, 1)
        )

        self.subtitle = DirectLabel(
            parent=self,
            relief=None,
            pos=(0, 0, 0.35),
            text="Select a Gag Track to unlock for your Toon:",
            text_scale=0.045,
            text_fg=(1, 1, 1, 1),
            text_font=ToontownGlobals.getToonFont()
        )

        self.buildTrackButtons()

    def buildTrackButtons(self):
        trackAccess = base.localAvatar.getTrackAccess()
        lockedTracks = []
        for trackId in range(len(ToontownBattleGlobals.Tracks)):
            if not trackAccess[trackId]:
                lockedTracks.append(trackId)

        if not lockedTracks:
            self.destroy()
            return

        # Position buttons nicely across rows
        startY = 0.15
        yOffset = -0.12
        for index, trackId in enumerate(lockedTracks):
            trackName = ToontownBattleGlobals.Tracks[trackId].capitalize()
            btn = DirectButton(
                parent=self,
                relief=DGG.RAISED,
                frameColor=(0.2, 0.5, 0.8, 1),
                text=f"Unlock {trackName} Track",
                text_scale=0.05,
                text_fg=(1, 1, 1, 1),
                text_shadow=(0, 0, 0, 1),
                text_font=ToontownGlobals.getInterfaceFont(),
                pos=(0, 0, startY + (index * yOffset)),
                scale=(1.2, 1.0, 1.0),
                command=self.selectTrack,
                extraArgs=[trackId]
            )
            self.buttons.append(btn)

    def selectTrack(self, trackId):
        base.localAvatar.d_requestChooseTrack(trackId)
        if self.doneCallback:
            self.doneCallback()
        self.destroy()

    def destroy(self):
        for btn in self.buttons:
            btn.destroy()
        self.buttons = []
        DirectFrame.destroy(self)
