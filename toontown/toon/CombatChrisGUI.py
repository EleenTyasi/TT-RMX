# =============================================================================
#  CombatChrisGUI.py  —  Combat Guide Menu for Combat Chris (TTC)
#  TT-RMX Personal Tinkering Project
# =============================================================================

from panda3d.core import *
from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject
from toontown.toonbase import ToontownGlobals, TTLocalizer

class CombatChrisGUI(DirectObject):
    def __init__(self, doneCallback=None):
        DirectObject.__init__(self)
        self.doneCallback = doneCallback

        self.mainFrame = DirectFrame(
            parent=aspect2d,
            relief=None,
            geom=DGG.getDefaultDialogGeom(),
            geom_color=Vec4(0.12, 0.14, 0.22, 0.95),
            geom_scale=(1.75, 1.0, 1.25),
            pos=(0, 0, 0.05),
        )

        self.title = DirectLabel(
            parent=self.mainFrame,
            relief=None,
            text="Combat Guide with Combat Chris",
            text_scale=0.07,
            text_fg=Vec4(1, 0.85, 0.2, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getSignFont(),
            pos=(0, 0, 0.48),
        )

        self.buttonFrame = DirectFrame(
            parent=self.mainFrame,
            relief=None,
            pos=(-0.58, 0, 0.32),
        )

        btn_font = ToontownGlobals.getToonFont()
        btn_style = {
            'relief': DGG.RAISED,
            'frameColor': (0.2, 0.45, 0.75, 0.9),
            'borderWidth': (0.01, 0.01),
            'text_scale': 0.038,
            'text_fg': (1, 1, 1, 1),
            'text_shadow': (0, 0, 0, 1),
            'text_font': btn_font,
            'pad': (0.02, 0.010),
        }

        self.btnCrit = DirectButton(
            parent=self.buttonFrame,
            text="Critical Hits",
            pos=(0, 0, 0.08),
            command=self.showSection,
            extraArgs=['crit'],
            **btn_style
        )

        self.btnBlock = DirectButton(
            parent=self.buttonFrame,
            text="Blocking & Guard",
            pos=(0, 0, 0.00),
            command=self.showSection,
            extraArgs=['block'],
            **btn_style
        )

        self.btnStatus = DirectButton(
            parent=self.buttonFrame,
            text="Status Effects",
            pos=(0, 0, -0.08),
            command=self.showSection,
            extraArgs=['status'],
            **btn_style
        )

        self.btnSpecialCogs = DirectButton(
            parent=self.buttonFrame,
            text="Special Cogs",
            pos=(0, 0, -0.16),
            command=self.showSection,
            extraArgs=['special_cogs'],
            **btn_style
        )

        self.btnSOS = DirectButton(
            parent=self.buttonFrame,
            text="SOS Summons",
            pos=(0, 0, -0.24),
            command=self.showSection,
            extraArgs=['sos_summons'],
            **btn_style
        )

        self.btnTrinket = DirectButton(
            parent=self.buttonFrame,
            text="Trinkets Guide",
            pos=(0, 0, -0.32),
            command=self.showSection,
            extraArgs=['trinket'],
            **btn_style
        )

        self.btnUber = DirectButton(
            parent=self.buttonFrame,
            text="Uber Guide",
            pos=(0, 0, -0.40),
            command=self.showSection,
            extraArgs=['uber'],
            **btn_style
        )

        # Content display frame
        self.contentFrame = DirectFrame(
            parent=self.mainFrame,
            relief=DGG.SUNKEN,
            frameColor=(0.06, 0.07, 0.12, 0.85),
            frameSize=(-0.55, 0.55, -0.36, 0.36),
            borderWidth=(0.01, 0.01),
            pos=(0.24, 0, -0.02),
        )

        self.contentTitle = DirectLabel(
            parent=self.contentFrame,
            relief=None,
            text="Welcome Toon!",
            text_scale=0.048,
            text_fg=Vec4(0.3, 0.9, 1.0, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getSignFont(),
            pos=(0, 0, 0.28),
        )

        self.contentText = DirectLabel(
            parent=self.contentFrame,
            relief=None,
            text="Howdy partner! The name is Combat Chris, your friendly neighborhood Gag tactician!\n\nPick a topic on the left to learn battle mechanics, or see how Ubers work!",
            text_scale=0.034,
            text_fg=Vec4(1, 1, 1, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_font=ToontownGlobals.getToonFont(),
            text_wordwrap=28,
            text_align=TextNode.ALeft,
            pos=(-0.50, 0, 0.18),
        )

        self.btnClose = DirectButton(
            parent=self.mainFrame,
            relief=DGG.RAISED,
            frameColor=(0.7, 0.2, 0.2, 0.9),
            borderWidth=(0.01, 0.01),
            text="Close",
            text_scale=0.045,
            text_fg=(1, 1, 1, 1),
            text_shadow=(0, 0, 0, 1),
            text_font=btn_font,
            pos=(0, 0, -0.50),
            command=self.close,
            pad=(0.04, 0.015),
        )

    def showSection(self, section):
        if section == 'crit':
            self.contentTitle['text'] = "Critical and Direct Hits"
            self.contentText['text'] = (
                "Landing a clean hit really puts a dent in those suits!\n\n"
                "- Critical Hit: Adds +5% extra damage! Toons have a 15% base chance to land one.\n\n"
                "- Direct Hit: A bullseye! Adds +15% extra damage with a 10% base chance.\n\n"
                "- Crit-Direct Combo: When both roll together, you unleash +25% bonus damage!\n\n"
                "Tip: Equip trinkets like Lucky Charm or Peril Band to multiply your crit odds!"
            )
        elif section == 'block':
            self.contentTitle['text'] = "Guard Stance and Blocking"
            self.contentText['text'] = (
                "In Toontown Remix, Passing has been completely replaced with the Guard mechanic!\n\n"
                "- Guarding: Choosing GUARD in battle raises your Giggle Barrier for the round.\n\n"
                "- Halved Damage: Taking a hit while guarding cuts incoming damage by 50% (or 80% with Toughened Toon)!\n\n"
                "- Status Defense: Guarding reduces the chance of suffering status afflictions by 10%.\n\n"
                "- Natural Reflexes: Every Toon also has an instinctive 5% natural block chance!"
            )
        elif section == 'status':
            self.contentTitle['text'] = "Status Effects"
            self.contentText['text'] = (
                "Watch out! Both Toons and Cogs can get afflicted with wild battle conditions!\n\n"
                "- SLOW: Drops attack accuracy by 15%.\n"
                "- WET: Drenches defense by 30%, making targets weak to Freeze!\n"
                "- FREEZE: Frozen solid! Turn is skipped.\n"
                "- WEAKEN: Lowers target defense by 10%.\n"
                "- POISON: Drains health at turn start.\n"
                "- BURN: Vulnerable! Takes +25% extra damage.\n"
                "- SHIELD: Absorbs 30% of incoming damage."
            )
        elif section == 'special_cogs':
            self.contentTitle['text'] = "Special Cog Variants"
            self.contentText['text'] = (
                "The Cogs have rolled out dangerous specialized modifications!\n\n"
                "- Alphatype (.A): Deals +30% extra attack damage with every strike.\n\n"
                "- Prototype (.P): Heavily reinforced chassis with double Max HP (2x HP).\n\n"
                "- Skelecog: Stripped of their suit with lower HP (0.75x), but possesses an elevated Critical Hit rate!\n\n"
                "- Version 2.0 (v2.0): Armed with a second internal skeleton. Defeating the suit revives them as a Skelecog!\n\n"
                "- Supertype (.S): A menacing red-glowing apex Cog combining Prototype (2x HP), Alphatype (+30% DMG), and v2.0 Revives!\n\n"
                "- World Boss (.WB): Giant roaming playground bosses with massive shared health bars and unique attacks!"
            )
        elif section == 'sos_summons':
            self.contentTitle['text'] = "SOS Companion Summons"
            self.contentText['text'] = (
                "Call in backup! SOS cards now summon autonomous AI Toon companions into battle!\n\n"
                "- Companion Limit: You can summon up to 3 active SOS companions into empty battle slots.\n\n"
                "- 5-Turn Limit: Companions fight alongside you for 5 combat rounds before bailing safely.\n\n"
                "- Power & Laff Scaling: Mercs range from 15 to 160 Max Laff with 1-Star to 5-Star Gag loadouts!\n\n"
                "- Predefined Trinkets: Every NPC companion comes equipped with their own signature Trinkets.\n\n"
                "- Smart Synergy AI: Companions coordinate attacks (e.g. using Squirt to stun before your Drop)!\n\n"
                "- Rewards: Field Offices reward 1-3 Star cards; the Sellbot VP rewards 3-5 Star cards!"
            )
        elif section == 'trinket':
            self.contentTitle['text'] = "Trinkets and Synergies"
            num_unlocked = 0
            if hasattr(base, 'localAvatar') and hasattr(base.localAvatar, 'getUnlockedTrinkets'):
                num_unlocked = len(base.localAvatar.getUnlockedTrinkets())

            self.contentText['text'] = (
                f"Trinkets Unlocked: {num_unlocked} / 33\n\n"
                "Trinkets augment and improve your toon in odd and interesting ways!\n\n"
                "- How to Attain: Every five cogs you defeat, you'll unlock one trinket!\n\n"
                "- Jellybean Pay: If you have all the trinkets you can get for now, you recieve 100 Jellybeans as a reward!\n\n"
                "- Shticker Book: Open your Shticker Book to equip up to 2 active Trinkets anytime outside of battle!"
            )
        elif section == 'uber':
            self.contentTitle['text'] = "The Uber Guide"
            is_uber = False
            laff_cap = 0
            if hasattr(base, 'localAvatar'):
                is_uber = getattr(base.localAvatar, 'isUber', lambda: False)() or getattr(base.localAvatar, 'laffCap', 0) > 0
                laff_cap = getattr(base.localAvatar, 'laffCap', 0)

            if is_uber:
                current_cap = laff_cap if laff_cap > 0 else getattr(base.localAvatar, 'maxHp', 15)
                header = f"Look at you! An official Uber Toon with a Laff cap of {current_cap}!\n\n"
            else:
                header = "Uber Toons restrict ONLY their Laff Points for true battle mastery!\n\n"

            self.contentText['text'] = (
                header +
                "1 Laff - Potentially Impossible! (Grade 5/5): One laff toons have minimal options when they are in combat...\n"
                "5 Laff - EXTREME (Grade 5/5): A much less punishing time than a 1 Laff, but later on, the Cogs might be overwhelming.\n"
                "15 Laff - VERY HARD (Grade 4/5): 15 laff points seems like it'll be plenty, but mind that bosses might give you some trouble.\n"
                "25 Laff - HARD (Grade 3/5): Solid intermediate challenge. Gives you some breathing room before they give you too much problems...\n"
                "34 Laff - MODERATE (Grade 2/5): Bit less challenging than the other Uber statuses, however, being a 34 Laff uber does mean some trinkets work better.\n"
                "40 Laff - ACCESSIBLE (Grade 1/5): Calmer, more relaxed experience."
            )

    def close(self):
        if self.doneCallback:
            self.doneCallback()
        self.destroy()

    def destroy(self):
        self.ignoreAll()
        if self.mainFrame:
            self.mainFrame.destroy()
            self.mainFrame = None
