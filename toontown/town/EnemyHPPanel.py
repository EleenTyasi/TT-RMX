# =============================================================================
#  EnemyHPPanel.py  —  2D Multi-Cog HP, Status Effects & Intention UI Panels
#  TT-RMX Personal Tinkering Project
# =============================================================================

from panda3d.core import *
from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject
from toontown.toonbase import ToontownGlobals, TTLocalizer

class EnemyHPPanel(DirectObject):
    def __init__(self, index=0, total=1):
        DirectObject.__init__(self)
        self.activeSuit = None
        self.frame = DirectFrame(
            parent=aspect2d,
            relief=None,
            scale=0.13,
            image=DGG.getDefaultDialogGeom(),
            image_scale=(4.6, 1.0, 2.2),
            image_pos=(0, 0, 0),
            image_color=Vec4(0.12, 0.12, 0.15, 0.90),
            text='',
        )
        
        self.nameLabel = DirectLabel(
            parent=self.frame,
            relief=None,
            pos=(0, 0, 0.55),
            text='Target Cog',
            text_scale=0.35,
            text_fg=Vec4(1, 1, 1, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getSignFont(),
        )

        self.hpLabel = DirectLabel(
            parent=self.frame,
            relief=None,
            pos=(0, 0, 0.20),
            text='HP: -- / --',
            text_scale=0.32,
            text_fg=Vec4(0.2, 1.0, 0.3, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getSuitFont(),
        )

        self.intentionLabel = DirectLabel(
            parent=self.frame,
            relief=None,
            pos=(0, 0, -0.15),
            text='',
            text_scale=0.25,
            text_fg=Vec4(1, 0.45, 0.3, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getInterfaceFont(),
        )

        self.statusLabel = DirectLabel(
            parent=self.frame,
            relief=None,
            pos=(0, 0, -0.48),
            text='',
            text_scale=0.25,
            text_fg=Vec4(1, 0.85, 0.2, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getInterfaceFont(),
        )

        self.setPosition(index, total)
        self.frame.hide()
        self.accept('suit-hp-change', self.__handleSuitHPChange)

    def setPosition(self, index, total):
        if total <= 1:
            xPositions = [0.0]
        elif total == 2:
            xPositions = [-0.55, 0.55]
        elif total == 3:
            xPositions = [-0.72, 0.0, 0.72]
        else: # 4 Cogs
            xPositions = [-0.95, -0.32, 0.32, 0.95]

        posX = xPositions[index] if index < len(xPositions) else 0.0
        self.frame.setPos(posX, 0, 0.75)
        self.frame.reparentTo(aspect2d)

    def __handleSuitHPChange(self, suit):
        if self.activeSuit and (self.activeSuit == suit or getattr(self.activeSuit, 'doId', None) == getattr(suit, 'doId', None)):
            self.updateSuit(suit)

    def updateSuit(self, suit=None, status_effects=None):
        if suit:
            self.activeSuit = suit
        suit = self.activeSuit
        if not suit or (hasattr(suit, 'isEmpty') and suit.isEmpty()):
            self.hide()
            return

        name = suit.getName() if hasattr(suit, 'getName') else 'Cog'
        actualLevel = suit.getActualLevel() if hasattr(suit, 'getActualLevel') else 1
        currHP = getattr(suit, 'currHP', 0)
        maxHP = getattr(suit, 'maxHP', 1)

        self.nameLabel['text'] = f"{name} (Lvl {actualLevel})"
        self.hpLabel['text'] = f"HP: {currHP} / {maxHP}"
        
        pct = float(currHP) / float(maxHP) if maxHP > 0 else 0
        if pct > 0.6:
            self.hpLabel['text_fg'] = Vec4(0.2, 1.0, 0.3, 1)
        elif pct > 0.3:
            self.hpLabel['text_fg'] = Vec4(1.0, 0.8, 0.2, 1)
        else:
            self.hpLabel['text_fg'] = Vec4(1.0, 0.25, 0.25, 1)

        intent = getattr(suit, 'intendedAttack', None)
        if intent:
            self.updateIntention(intent[0], intent[1])
        else:
            self.intentionLabel['text'] = ''

        if status_effects is not None:
            badge_str = " ".join([f"[{eff}]" for eff in status_effects])
            self.statusLabel['text'] = badge_str
        else:
            effs = getattr(suit, 'statusEffects', None)
            if effs:
                self.statusLabel['text'] = " ".join([f"[{eff}]" for eff in effs])
            else:
                self.statusLabel['text'] = ''

        self.frame.show()

    def updateIntention(self, atkName, dmg):
        if atkName and atkName != 'Wait':
            self.intentionLabel['text'] = f"Intention: {atkName} ({dmg} Dmg)"
        else:
            self.intentionLabel['text'] = "Intention: Preparing..."

    def hide(self):
        self.frame.reparentTo(hidden)
        self.frame.hide()

    def show(self):
        self.frame.reparentTo(aspect2d)
        self.frame.show()

    def destroy(self):
        self.ignore('suit-hp-change')
        self.frame.reparentTo(hidden)
        self.frame.destroy()


class EnemyHPPanelManager(DirectObject):
    def __init__(self):
        DirectObject.__init__(self)
        self.panels = {}

    def updateCogs(self, cogs):
        if not cogs:
            self.hideAll()
            return

        valid_cogs = [s for s in cogs if s and (not hasattr(s, 'isEmpty') or not s.isEmpty())]
        total = len(valid_cogs)
        current_ids = set()

        for index, suit in enumerate(valid_cogs):
            doId = getattr(suit, 'doId', id(suit))
            current_ids.add(doId)
            if doId not in self.panels:
                panel = EnemyHPPanel(index, total)
                panel.updateSuit(suit)
                self.panels[doId] = panel
            else:
                self.panels[doId].setPosition(index, total)
                self.panels[doId].updateSuit(suit)

        for doId in list(self.panels.keys()):
            if doId not in current_ids:
                self.panels[doId].destroy()
                del self.panels[doId]

    def updateSuit(self, suit, status_effects=None):
        if not suit:
            return
        doId = getattr(suit, 'doId', id(suit))
        if doId in self.panels:
            self.panels[doId].updateSuit(suit, status_effects)

    def updateSuitHP(self, suit, status_effects=None):
        self.updateSuit(suit, status_effects)

    def updateSuitIntention(self, suit, atkName, dmg):
        doId = getattr(suit, 'doId', id(suit))
        if doId in self.panels:
            self.panels[doId].updateIntention(atkName, dmg)

    def hideAll(self):
        for panel in self.panels.values():
            panel.hide()
        self.panels.clear()

    def destroyAll(self):
        for panel in self.panels.values():
            panel.destroy()
        self.panels.clear()
