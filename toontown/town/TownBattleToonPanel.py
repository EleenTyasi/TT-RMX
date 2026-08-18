from panda3d.core import *
from toontown.toonbase import ToontownGlobals
from toontown.toonbase.ToontownBattleGlobals import *
from direct.directnotify import DirectNotifyGlobal
import string
from toontown.toon import LaffMeter
from toontown.battle import BattleBase
from direct.gui.DirectGui import *
from toontown.toonbase import TTLocalizer

from toontown.town.EnemyHPPanel import STATUS_DESCRIPTIONS

class TownBattleToonPanel(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('TownBattleToonPanel')

    def __init__(self, id):
        gui = loader.loadModel('phase_3.5/models/gui/battle_gui')
        DirectFrame.__init__(self, relief=None, image=gui.find('**/ToonBtl_Status_BG'), image_color=Vec4(0.5, 0.9, 0.5, 0.7))
        self.setScale(0.8)
        self.initialiseoptions(TownBattleToonPanel)
        self.avatar = None
        self.badgeButtons = []
        self.sosText = DirectLabel(parent=self, relief=None, pos=(0.1, 0, 0.015), text=TTLocalizer.TownBattleToonSOS, text_scale=0.06)
        self.sosText.hide()
        self.fireText = DirectLabel(parent=self, relief=None, pos=(0.1, 0, 0.015), text=TTLocalizer.TownBattleToonFire, text_scale=0.06)
        self.fireText.hide()
        self.undecidedText = DirectLabel(parent=self, relief=None, pos=(0.1, 0, 0.015), text=TTLocalizer.TownBattleUndecided, text_scale=0.1)
        self.healthText = DirectLabel(parent=self, text='', pos=(-0.06, 0, -0.075), text_scale=0.055)
        self.hpChangeEvent = None
        self.gagNode = self.attachNewNode('gag')
        self.gagNode.setPos(0.1, 0, 0.03)
        self.hasGag = 0
        passGui = gui.find('**/tt_t_gui_bat_pass')
        passGui.detachNode()
        self.passNode = self.attachNewNode('pass')
        self.passNode.setPos(0.1, 0, 0.05)
        passGui.setScale(0.2)
        passGui.reparentTo(self.passNode)
        self.passNode.hide()
        self.laffMeter = None
        self.whichText = DirectLabel(parent=self, text='', pos=(0.1, 0, -0.08), text_scale=0.05)
        
        self.statusContainer = DirectFrame(
            parent=self,
            relief=None,
            pos=(-0.06, 0, -0.13),
        )
        self.statusText = DirectLabel(
            parent=self.statusContainer,
            relief=None,
            text='=OK=',
            pos=(0, 0, 0),
            text_scale=0.06,
            text_fg=Vec4(0.2, 1.0, 0.3, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getSignFont()
        )

        # Tooltip Hover Frame (displays above the Toon battle panel)
        self.tooltipFrame = DirectFrame(
            parent=self,
            relief=None,
            pos=(0.0, 0, 0.35),
            scale=0.14,
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

        self.hide()
        gui.removeNode()
        return

    def __clearBadges(self):
        for btn in self.badgeButtons:
            btn.destroy()
        self.badgeButtons.clear()
        if hasattr(self, 'tooltipFrame') and self.tooltipFrame:
            self.tooltipFrame.hide()

    def __showTooltip(self, key, full_str, extra=None):
        title, desc = STATUS_DESCRIPTIONS.get(key, (key, "Active Status Effect"))
        self.tooltipTitle['text'] = f"{title} [{full_str}]"
        self.tooltipDesc['text'] = desc
        self.tooltipFrame.show()

    def __hideTooltip(self, extra=None):
        if hasattr(self, 'tooltipFrame') and self.tooltipFrame:
            self.tooltipFrame.hide()

    def setStatusEffects(self, effects):
        self.__clearBadges()
        if effects:
            self.statusText.hide()
            startX = -0.12 * (len(effects) - 1) / 2.0
            for i, eff_str in enumerate(effects):
                key = eff_str.split()[0].replace('[', '').replace(']', '').upper()
                btn = DirectButton(
                    parent=self.statusContainer,
                    relief=DGG.RAISED,
                    frameSize=(-0.5, 0.5, -0.15, 0.2),
                    frameColor=(0.2, 0.2, 0.3, 0.9),
                    pos=(startX + i * 0.12, 0, 0),
                    scale=0.11,
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
        else:
            self.statusText['text'] = '=OK='
            self.statusText['text_scale'] = 0.06
            self.statusText['text_fg'] = Vec4(0.2, 1.0, 0.3, 1.0)
            self.statusText.show()

    def setLaffMeter(self, avatar):
        self.notify.debug('setLaffMeter: new avatar %s' % avatar.doId)
        if self.avatar == avatar:
            messenger.send(self.avatar.uniqueName('hpChange'), [avatar.hp, avatar.maxHp, 1])
            return None
        else:
            if self.avatar:
                self.cleanupLaffMeter()
            self.avatar = avatar
            self.laffMeter = LaffMeter.LaffMeter(avatar.style, avatar.hp, avatar.maxHp)
            self.laffMeter.setAvatar(self.avatar)
            self.laffMeter.reparentTo(self)
            self.laffMeter.setPos(-0.06, 0, 0.05)
            self.laffMeter.setScale(0.045)
            self.laffMeter.start()
            self.setHealthText(avatar.hp, avatar.maxHp)
            self.hpChangeEvent = self.avatar.uniqueName('hpChange')
            self.accept(self.hpChangeEvent, self.setHealthText)
        return None

    def setHealthText(self, hp, maxHp, quietly = 0):
        self.healthText['text'] = TTLocalizer.TownBattleHealthText % {'hitPoints': hp,
         'maxHit': maxHp}

    def show(self):
        DirectFrame.show(self)
        if self.laffMeter:
            self.laffMeter.start()

    def hide(self):
        DirectFrame.hide(self)
        self.__hideTooltip()
        if self.laffMeter:
            self.laffMeter.stop()

    def updateLaffMeter(self, hp):
        if self.laffMeter:
            self.laffMeter.adjustFace(hp, self.avatar.maxHp)
        self.setHealthText(hp, maxHp)

    def setValues(self, index, track, level = None, numTargets = None, targetIndex = None, localNum = None):
        self.notify.debug('Toon Panel setValues: index=%s track=%s level=%s numTargets=%s targetIndex=%s localNum=%s' % (index,
         track,
         level,
         numTargets,
         targetIndex,
         localNum))
        self.undecidedText.hide()
        self.sosText.hide()
        self.fireText.hide()
        self.gagNode.hide()
        self.whichText.hide()
        self.passNode.hide()
        if self.hasGag:
            self.gag.removeNode()
            self.hasGag = 0
        if track == BattleBase.NO_ATTACK or track == BattleBase.UN_ATTACK:
            self.undecidedText.show()
        elif track == BattleBase.PASS_ATTACK:
            self.passNode.show()
        elif track == BattleBase.FIRE:
            self.fireText.show()
            self.whichText.show()
            self.whichText['text'] = self.determineWhichText(numTargets, targetIndex, localNum, index)
        elif track == BattleBase.SOS or track == BattleBase.NPCSOS or track == BattleBase.PETSOS:
            self.sosText.show()
        elif track >= MIN_TRACK_INDEX and track <= MAX_TRACK_INDEX:
            self.undecidedText.hide()
            self.passNode.hide()
            self.gagNode.show()
            invButton = base.localAvatar.inventory.buttonLookup(track, level)
            self.gag = invButton.instanceUnderNode(self.gagNode, 'gag')
            self.gag.setScale(0.8)
            self.gag.setPos(0, 0, 0.02)
            self.hasGag = 1
            if numTargets is not None and targetIndex is not None and localNum is not None:
                self.whichText.show()
                self.whichText['text'] = self.determineWhichText(numTargets, targetIndex, localNum, index)
        else:
            self.notify.error('Bad track value: %s' % track)
        return

    def determineWhichText(self, numTargets, targetIndex, localNum, index):
        returnStr = ''
        targetList = list(range(numTargets))
        targetList.reverse()
        for i in targetList:
            if targetIndex == -1:
                returnStr += 'X'
            elif targetIndex == -2:
                if i == index:
                    returnStr += '-'
                else:
                    returnStr += 'X'
            elif targetIndex >= 0 and targetIndex <= 3:
                if i == targetIndex:
                    returnStr += 'X'
                else:
                    returnStr += '-'
            else:
                self.notify.error('Bad target index: %s' % targetIndex)

        return returnStr

    def cleanup(self):
        self.ignoreAll()
        self.__clearBadges()
        self.cleanupLaffMeter()
        if hasattr(self, 'tooltipFrame') and self.tooltipFrame:
            self.tooltipFrame.destroy()
            self.tooltipFrame = None
        if hasattr(self, 'statusContainer') and self.statusContainer:
            self.statusContainer.destroy()
            self.statusContainer = None
        if self.hasGag:
            self.gag.removeNode()
            del self.gag
        self.gagNode.removeNode()
        del self.gagNode
        DirectFrame.destroy(self)

    def cleanupLaffMeter(self):
        self.notify.debug('Cleaning up laffmeter!')
        self.ignore(self.hpChangeEvent)
        if self.laffMeter:
            self.laffMeter.destroy()
            self.laffMeter = None
        return
