# =============================================================================
#  EnemyHPPanel.py  —  Enemy HP & Status Effects UI Panel
#  TT-RMX Personal Tinkering Project
# =============================================================================

from panda3d.core import *
from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject
from toontown.toonbase import ToontownGlobals, TTLocalizer

class EnemyHPPanel(DirectObject):
    def __init__(self, parent=None):
        self.frame = DirectFrame(
            parent=parent or aspect2d,
            relief=None,
            pos=(0, 0, 0.62),
            scale=0.14,
            image=DGG.getDefaultDialogGeom(),
            image_scale=(4.8, 1.0, 1.8),
            image_pos=(0, 0, 0),
            image_color=Vec4(0.15, 0.15, 0.18, 0.90),
            text='',
        )
        
        self.nameLabel = DirectLabel(
            parent=self.frame,
            relief=None,
            pos=(0, 0, 0.45),
            text='Target Cog',
            text_scale=0.35,
            text_fg=Vec4(1, 1, 1, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getSignFont(),
        )

        self.hpLabel = DirectLabel(
            parent=self.frame,
            relief=None,
            pos=(0, 0, 0.08),
            text='HP: -- / --',
            text_scale=0.32,
            text_fg=Vec4(0.2, 1.0, 0.3, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getSuitFont(),
        )

        self.statusLabel = DirectLabel(
            parent=self.frame,
            relief=None,
            pos=(0, 0, -0.35),
            text='',
            text_scale=0.25,
            text_fg=Vec4(1, 0.85, 0.2, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getInterfaceFont(),
        )

        self.frame.hide()

    def updateSuit(self, suit, status_effects=None):
        if not suit:
            self.frame.hide()
            return

        name = suit.getName()
        actualLevel = suit.getActualLevel()
        currHP = getattr(suit, 'currHP', 0)
        maxHP = getattr(suit, 'maxHP', 1)

        self.nameLabel['text'] = f"{name} (Lvl {actualLevel})"
        self.hpLabel['text'] = f"HP: {currHP} / {maxHP}"
        
        # Color hp text based on health percentage
        pct = float(currHP) / float(maxHP) if maxHP > 0 else 0
        if pct > 0.6:
            self.hpLabel['text_fg'] = Vec4(0.2, 1.0, 0.3, 1) # Green
        elif pct > 0.3:
            self.hpLabel['text_fg'] = Vec4(1.0, 0.8, 0.2, 1) # Yellow
        else:
            self.hpLabel['text_fg'] = Vec4(1.0, 0.25, 0.25, 1) # Red

        if status_effects:
            badge_str = " ".join([f"[{eff}]" for eff in status_effects])
            self.statusLabel['text'] = badge_str
        else:
            self.statusLabel['text'] = ''

        self.frame.show()

    def hide(self):
        self.frame.hide()

    def show(self):
        self.frame.show()

    def destroy(self):
        self.frame.destroy()
