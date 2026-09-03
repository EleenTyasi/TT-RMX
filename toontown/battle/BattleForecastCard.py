# =============================================================================
#  BattleForecastCard.py  —  Target Damage & Kill Forecast UI Card
#  TT-RMX Personal Tinkering Project
# =============================================================================

from direct.gui.DirectGui import DirectFrame, DirectLabel, DGG
from panda3d.core import Vec4, Point3, TextNode
from toontown.toonbase import ToontownGlobals
from toontown.battle.sim.BattleSim import ForecastData

class BattleForecastCard:
    """
    Floating UI card displaying live predictive battle calculations:
    Damage, accuracy %, critical odds, status effect procs, and lethal kill badges.
    """

    def __init__(self):
        self.frame = None
        self.titleLabel = None
        self.damageLabel = None
        self.statsLabel = None
        self.statusLabel = None
        self.lethalBadge = None
        self.hpRemainingLabel = None
        self.isLoaded = False
        self.buildGui()

    def buildGui(self):
        if self.isLoaded:
            return

        # Main background card - sleek dark slate with blue border
        self.frame = DirectFrame(
            parent=aspect2d,
            relief=DGG.RAISED,
            frameSize=(-0.38, 0.38, -0.22, 0.22),
            frameColor=Vec4(0.07, 0.09, 0.13, 0.92),
            borderWidth=(0.012, 0.012),
            pos=(0, 0, 0.48),
            sortOrder=100
        )
        self.frame.hide()

        # Title Label: Gag Name on Target Cog Name
        self.titleLabel = DirectLabel(
            parent=self.frame,
            relief=None,
            pos=(0, 0, 0.14),
            text="Gag on Cog",
            text_scale=0.048,
            text_font=ToontownGlobals.getToonFont(),
            text_fg=Vec4(0.95, 0.85, 0.40, 1.0),
            text_align=TextNode.ACenter,
            text_shadow=(0, 0, 0, 0.8)
        )

        # Big Damage Label
        self.damageLabel = DirectLabel(
            parent=self.frame,
            relief=None,
            pos=(0, 0, 0.06),
            text="DMG: 0",
            text_scale=0.062,
            text_font=ToontownGlobals.getToonFont(),
            text_fg=Vec4(1.0, 0.60, 0.20, 1.0),
            text_align=TextNode.ACenter,
            text_shadow=(0, 0, 0, 0.8)
        )

        # Accuracy & Crit stats
        self.statsLabel = DirectLabel(
            parent=self.frame,
            relief=None,
            pos=(0, 0, -0.01),
            text="HIT: 95%  |  CRIT: 15%",
            text_scale=0.040,
            text_font=ToontownGlobals.getToonFont(),
            text_fg=Vec4(0.40, 0.85, 1.0, 1.0),
            text_align=TextNode.ACenter
        )

        # Status effect prediction
        self.statusLabel = DirectLabel(
            parent=self.frame,
            relief=None,
            pos=(0, 0, -0.07),
            text="",
            text_scale=0.038,
            text_font=ToontownGlobals.getToonFont(),
            text_fg=Vec4(0.75, 0.55, 1.0, 1.0),
            text_align=TextNode.ACenter
        )

        # HP remaining readout
        self.hpRemainingLabel = DirectLabel(
            parent=self.frame,
            relief=None,
            pos=(0, 0, -0.14),
            text="HP: 100 / 100",
            text_scale=0.038,
            text_font=ToontownGlobals.getToonFont(),
            text_fg=Vec4(0.85, 0.85, 0.85, 1.0),
            text_align=TextNode.ACenter
        )

        # Lethal Kill Badge (prominent gold/red badge)
        self.lethalBadge = DirectLabel(
            parent=self.frame,
            relief=DGG.RIDGE,
            frameSize=(-0.24, 0.24, -0.035, 0.035),
            frameColor=Vec4(0.70, 0.10, 0.10, 0.90),
            borderWidth=(0.008, 0.008),
            pos=(0, 0, -0.15),
            text="[ LETHAL KILL ]",
            text_scale=0.044,
            text_font=ToontownGlobals.getToonFont(),
            text_fg=Vec4(1.0, 0.90, 0.20, 1.0),
            text_align=TextNode.ACenter,
            text_pos=(0, -0.012),
            text_shadow=(0, 0, 0, 0.9)
        )
        self.lethalBadge.hide()

        self.isLoaded = True

    def show_forecast(self, forecast: ForecastData, pos_override: tuple = None):
        if not self.isLoaded:
            self.buildGui()

        if pos_override:
            self.frame.setPos(pos_override[0], 0, pos_override[1])
        else:
            self.frame.setPos(0, 0, 0.48)

        # Title
        self.titleLabel['text'] = f"{forecast.gag_name} on {forecast.target_name}"

        # Damage breakdown
        dmg_str = f"DMG: {forecast.total_expected_damage}"
        sub_tags = []
        if forecast.knockback_bonus:
            sub_tags.append(f"+{forecast.knockback_bonus} KB")
        if forecast.combo_bonus:
            sub_tags.append(f"+{forecast.combo_bonus} Combo")
        if sub_tags:
            dmg_str += f" ({', '.join(sub_tags)})"
        self.damageLabel['text'] = dmg_str

        # Hit & Crit stats
        hit_str = f"HIT: {forecast.hit_chance_pct:.0f}%"
        crit_str = f"CRIT: {forecast.crit_chance_pct:.0f}%"
        self.statsLabel['text'] = f"{hit_str}   |   {crit_str}"

        # Status effect
        if forecast.status_effect_name:
            self.statusLabel['text'] = f"Status: {forecast.status_effect_name} ({forecast.status_effect_chance:.0f}%)"
            self.statusLabel.show()
        else:
            self.statusLabel['text'] = ""
            self.statusLabel.hide()

        # HP Remaining & Lethal Badge
        rem_hp = max(0, forecast.target_hp - forecast.total_expected_damage)
        self.hpRemainingLabel['text'] = f"Cog HP: {rem_hp} / {forecast.target_max_hp}"

        if forecast.is_lethal:
            self.lethalBadge.show()
            self.hpRemainingLabel.setPos(0, 0, -0.09)
        else:
            self.lethalBadge.hide()
            self.hpRemainingLabel.setPos(0, 0, -0.14)

        self.frame.show()

    def hide(self):
        if self.frame:
            self.frame.hide()

    def destroy(self):
        if self.frame:
            self.frame.destroy()
            self.frame = None
        self.isLoaded = False
