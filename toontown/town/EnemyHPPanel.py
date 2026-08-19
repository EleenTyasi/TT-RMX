# =============================================================================
#  EnemyHPPanel.py  —  2D Multi-Cog HP, Status Effects & Intention UI Panels
#                     with Mouse Hover Status Tooltips
#  TT-RMX Personal Tinkering Project
# =============================================================================

from panda3d.core import *
from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject
from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.battle import SuitBattleGlobals

STATUS_DESCRIPTIONS = {
    'SLOW': ("Slow Debuff", "-15% Accuracy penalty on all attacks."),
    'WET': ("Wet Status", "Drenched! -30% Cog defense & highly susceptible to Freeze."),
    'FREEZE': ("Freeze Stun", "Frozen solid! Skips attack turn."),
    'WEAKEN': ("Weaken Debuff", "-10% Defense penalty, takes extra damage."),
    'POISON': ("Poison DoT", "Takes Damage Over Time at round start."),
    'BURN': ("Burn Vulnerability", "Vulnerable! Takes 1.25x (25% extra) damage."),
    'SHIELD': ("Shield Buff", "Shielded! Takes 30% reduced damage."),
    'LUCKY': ("Lucky Buff", "Lucky momentum! +15% Gag accuracy boost."),
    'RALLIED': ("Rallied Buff", "Rallied spirit! +20% Gag damage boost."),
}

class EnemyHPPanel(DirectObject):
    def __init__(self, index=0, total=1):
        DirectObject.__init__(self)
        self.activeSuit = None
        self.badgeButtons = []
        
        self.frame = DirectFrame(
            parent=aspect2d,
            relief=None,
            scale=0.13,
            image=DGG.getDefaultDialogGeom(),
            image_scale=(5.5, 1.0, 2.2),
            image_pos=(0, 0, 0),
            image_color=Vec4(0.12, 0.12, 0.15, 0.90),
            text='',
        )
        
        self.nameLabel = DirectLabel(
            parent=self.frame,
            relief=None,
            pos=(0, 0, 0.55),
            text='Target Cog',
            text_scale=0.30,
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

        self.statusContainer = DirectFrame(
            parent=self.frame,
            relief=None,
            pos=(0, 0, -0.48),
        )

        # Tooltip Hover Frame
        self.tooltipFrame = DirectFrame(
            parent=self.frame,
            relief=None,
            pos=(0, 0, -1.35),
            scale=0.85,
            image=DGG.getDefaultDialogGeom(),
            image_scale=(4.2, 1.0, 1.3),
            image_pos=(0, 0, 0),
            image_color=Vec4(0.08, 0.08, 0.12, 0.96),
            sortOrder=100,
        )
        self.tooltipTitle = DirectLabel(
            parent=self.tooltipFrame,
            relief=None,
            pos=(0, 0, 0.30),
            text='',
            text_scale=0.26,
            text_fg=Vec4(1, 0.85, 0.2, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getSignFont(),
        )
        self.tooltipDesc = DirectLabel(
            parent=self.tooltipFrame,
            relief=None,
            pos=(0, 0, -0.08),
            text='',
            text_scale=0.22,
            text_fg=Vec4(1, 1, 1, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_wordwrap=17,
            text_font=ToontownGlobals.getInterfaceFont(),
        )
        self.tooltipFrame.hide()

        self.setPosition(index, total)
        self.frame.hide()
        self.accept('suit-hp-change', self.__handleSuitHPChange)

    def setPosition(self, index, total):
        # Position on the left side of the screen so it doesn't block the Cogs or Boss Bar
        if total <= 1:
            yPositions = [0.28]
        elif total == 2:
            yPositions = [0.42, 0.14]
        elif total == 3:
            yPositions = [0.55, 0.28, 0.01]
        else:
            yPositions = [0.65, 0.40, 0.15, -0.10]

        posY = yPositions[index] if index < len(yPositions) else 0.28
        self.frame.setPos(-0.95, 0, posY)
        self.frame.reparentTo(aspect2d)

    def __handleSuitHPChange(self, suit):
        if self.activeSuit and (self.activeSuit == suit or getattr(self.activeSuit, 'doId', None) == getattr(suit, 'doId', None)):
            self.updateSuit(suit)

    def __clearBadges(self):
        for btn in self.badgeButtons:
            btn.destroy()
        self.badgeButtons.clear()
        self.tooltipFrame.hide()

    def __showTooltip(self, key, full_str, extra=None):
        title, desc = STATUS_DESCRIPTIONS.get(key, (key, "Active Status Effect"))
        self.tooltipTitle['text'] = f"{title} [{full_str}]"
        self.tooltipDesc['text'] = desc
        self.tooltipFrame.show()

    def __hideTooltip(self, extra=None):
        self.tooltipFrame.hide()

    def updateSuit(self, suit=None, status_effects=None):
        if suit:
            self.activeSuit = suit
        suit = self.activeSuit
        if not suit or (hasattr(suit, 'isEmpty') and suit.isEmpty()):
            self.hide()
            return

        name = suit.getName() if hasattr(suit, 'getName') else 'Cog'
        actualLevel = suit.getActualLevel() if hasattr(suit, 'getActualLevel') else 1

        baseMaxHP = getattr(suit, 'maxHP', 1)
        if hasattr(suit, 'dna') and suit.dna and hasattr(suit, 'level'):
            attributes = SuitBattleGlobals.SuitAttributes.get(suit.dna.name)
            if attributes and 'hp' in attributes:
                try:
                    baseMaxHP = attributes['hp'][suit.level]
                except:
                    baseMaxHP = attributes['hp'][-1]

        isWorldBoss = getattr(suit, 'isWorldBoss', False) or bool(getattr(suit, 'worldBossName', None))
        isSuper = getattr(suit, 'isSupertype', False)
        isProto = getattr(suit, 'isPrototype', False)
        isAlpha = getattr(suit, 'isAlphatype', False)
        isSkele = bool(getattr(suit, 'isSkelecog', False) or getattr(suit, 'isSkelecogVariant', False) or (hasattr(suit, 'getSkelecog') and suit.getSkelecog()))
        revives = getattr(suit, 'skeleRevives', 0) if not hasattr(suit, 'getSkeleRevives') else suit.getSkeleRevives()
        isV2 = revives > 0 or getattr(suit, 'isV20', False)

        if isWorldBoss:
            name = getattr(suit, 'worldBossName', name)
            maxHP = getattr(suit, 'maxHP', baseMaxHP)
            currHP = getattr(suit, 'currHP', maxHP)
        elif isSuper or isProto:
            maxHP = baseMaxHP * 2
            currHP = getattr(suit, 'currHP', maxHP)
        elif isSkele:
            maxHP = max(1, int(baseMaxHP * 0.75))
            currHP = getattr(suit, 'currHP', maxHP)
        else:
            maxHP = baseMaxHP
            currHP = getattr(suit, 'currHP', maxHP)

        suit.maxHP = maxHP
        if currHP > maxHP:
            currHP = maxHP
        suit.currHP = currHP

        levelStr = str(actualLevel)
        if isWorldBoss:
            levelStr += '.WB'
        elif isSuper:
            levelStr += '.S'
        elif isAlpha and isProto:
            levelStr += '.A.P'
        elif isAlpha:
            levelStr += '.A'
        elif isProto:
            levelStr += '.P'

        if isV2:
            levelStr += ' v2.0'
        elif isSkele and not isSuper and not isWorldBoss:
            levelStr += ' (Skele)'

        nameStr = f"{name} (Lvl {levelStr})"
        self.nameLabel['text'] = nameStr
        if len(nameStr) > 22:
            self.nameLabel['text_scale'] = max(0.20, 0.30 * (22.0 / len(nameStr)))
        else:
            self.nameLabel['text_scale'] = 0.30
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

        # Rebuild interactive status badges with mouse hover events
        self.__clearBadges()
        eff_list = status_effects if status_effects is not None else getattr(suit, 'statusEffects', [])
        if eff_list:
            startX = -0.45 * (len(eff_list) - 1) / 2.0
            for i, eff_str in enumerate(eff_list):
                key = eff_str.split()[0].replace('[', '').replace(']', '')
                btn = DirectButton(
                    parent=self.statusContainer,
                    relief=DGG.RAISED,
                    frameSize=(-0.5, 0.5, -0.15, 0.2),
                    frameColor=(0.2, 0.2, 0.3, 0.9),
                    pos=(startX + i * 0.55, 0, 0),
                    scale=0.7,
                    text=f"[{eff_str}]",
                    text_scale=0.25,
                    text_fg=Vec4(1, 0.85, 0.2, 1),
                    text_shadow=Vec4(0, 0, 0, 1),
                    text_font=ToontownGlobals.getInterfaceFont(),
                    pressEffect=0,
                )
                btn.bind(DGG.ENTER, self.__showTooltip, extraArgs=[key, eff_str])
                btn.bind(DGG.EXIT, self.__hideTooltip)
                self.badgeButtons.append(btn)

        self.frame.show()

    def updateIntention(self, atkName, dmg):
        if atkName and atkName != 'Wait':
            self.intentionLabel['text'] = f"Intention: {atkName} ({dmg} Dmg)"
        else:
            self.intentionLabel['text'] = "Intention: Preparing..."

    def hide(self):
        self.__clearBadges()
        self.frame.reparentTo(hidden)
        self.frame.hide()

    def show(self):
        self.frame.reparentTo(aspect2d)
        self.frame.show()

    def destroy(self):
        self.__clearBadges()
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
