# TT-RMX (Toontown Remix)

**TT-RMX** is an experimental single-player **Action-RPG (ARPG) & Solo-Raid overhaul** of Toontown built on a modernized Python 3 codebase powered by [Astron](https://github.com/Astron/Astron) and [Panda3D](https://github.com/panda3d/panda3d). 

TT-RMX re-envisions the classic turn-based MMORPG into a deep, solo-focused experience featuring **overworld World Boss raids**, **dynamic character leveling**, **status effects & tiered critical hits**, **an equippable Trinket system**, and **fluid third-person orbit camera controls with sprint mechanics**.

---

## 🌟 Key Features & Overhauls

### ⚔️ 1. Playground World Bosses (Solo-Raid System)
* **Roaming Overworld Bosses**: Six unique World Bosses roam the playground streets, acting as multi-phase solo-raid encounters.
  * **Toontown Central**: *The Fixer* (Level 12 • 500 HP)
  * **Donald's Dock**: *Loan Shark Tycoon* (Level 14 • 800 HP)
  * **Daisy Gardens**: *Lead Botanist* (Level 16 • 1,100 HP)
  * **Minnie's Melodyland**: *Maestro Manipulator* (Level 18 • 1,400 HP)
  * **The Brrrgh**: *Chief Cryomancer* (Level 20 • 1,700 HP)
  * **Donald's Dreamland**: *Nightmare Auditor* (Level 22 • 2,000 HP)
* **Pity Spawning Engine**: Streets start with a base 2.0% spawn chance. Defeating regular roaming Cogs builds pity up to 20% (or 100% via `~forceboss`), guaranteeing boss encounters over time.
* **7-Turn Flee Clock**: Players face an intense 7-round DPS sprint to deal as much damage as possible before the boss escapes.
* **Persistent Health Pool**: Damage dealt to a World Boss is saved globally on the server across encounters.
* **Permanent Laff Rewards**: Slaying a playground World Boss for the first time awards a permanent **+2 Max Laff Boost**.
* **World Boss HUD**: Top-screen boss health bar, escape turn counter countdown, and first-encounter tutorial modal.

---

### 📈 2. RPG Leveling, EXP & Character Stats
* **Levels 1–25 Progression**: Replaces rigid hood-task gates with an EXP and character level progression curve.
* **Dynamic EXP Sources**: Earn EXP directly by defeating street Cogs, clearing building floors, and completing revamped quests.
* **Player-Choice Track Unlocks**: Earn track unlock points on level milestones and choose which Gag tracks to unlock via a custom interface.
* **Character Stats Page**: The Shtiker Book track page has been transformed into a full RPG character stat sheet showing current Level, EXP progress, and combat attributes.
* **Uber / Challenge Mode**: Choose custom Laff caps during Make-a-Toon for specialized low-Laff challenge runs.

---

### 💥 3. Combat Overhaul: Status Effects, Crits & Guard
* **Multi-Round Status Engine**:
  * **Poison**: End-of-round damage-over-time (DoT) ticks.
  * **Freeze**: Skips enemy Cog turns and makes them vulnerable to Ice Shatter combos.
  * **Wet Status**: Squirt attacks apply the Wet debuff for follow-up accuracy and damage synergies.
  * **Burn, Slow & Weaken**: Applied via special gags and high-level Cog abilities.
* **4-Tier Critical Hit System**: Attacks and heals roll across *Normal*, *Direct Hit*, *Critical Hit*, and *Critical Direct Hit* for massive damage and healing multipliers.
* **Active Guard (Pass = 50% Damage Reduction)**: Choosing "Pass" functions as an active defensive Guard, halving all incoming damage for the round.
* **Live Combat Log Panel**: Real-time on-screen HUD feed displaying all damage, heals, crits, and status procs.
* **Enemy HP & Status Inspector**: Real-time Cog HP meters, variant markers (`.WB`, `.S`, `v2.0`), and hover tooltips explaining active status effects.
* **Self-Targeting Toon-Up**: Solo Toons can heal themselves in combat without requiring SOS cards or Doodles.

---

### 💍 4. Equippable Trinket System (25 Accessories)
* **2 Equipment Slots**: Equip passive Trinkets via the redesigned Shtiker Book Trinket Page (`EventsPage.py`).
* **Milestone Unlocks**: Defeating every 5 Cogs in combat rolls and unlocks a random unowned Trinket (or awards bonus Jellybeans once maxed).
* **Diverse Build Archetypes**:
  * **Organic-izers**: Permanent organic bonuses for each individual Gag track, or *Organic-ize* (all 7 tracks organic, +50% damage taken).
  * **Synergy Enablers**: *Vampiric Gags* (10% damage lifesteal), *Shattering Frost* (50% splash on frozen Cog defeat), *Lured Drop* (Drop hits lured Cogs), *Gentle Water* (Squirt won't unlure), *Status Catalyst* (+1 status duration).
  * **Survival & High-Risk**: *Second Wind* (fatal damage shield once per battle), *Daring Danger* (+30% damage at low Laff), *Glass Cannon* (+25% damage dealt & taken), *Guardian Bulwark* (+15% dodge).
  * **Speeding Toon**: 2x sprint speed, 4x collision ramming damage against Cogs.

---

### 🏃 5. FFXIV-Style Orbit Camera & Mobility
* **Modern Third-Person Camera**: Fluid mouse-look orbit camera with cursor locking during right-click hold, distance zooming (3.0 to 35.0 units), vertical pitch limits, floor penetration prevention, and automatic street visibility raycasting.
* **Shift-to-Sprint & Stamina Bar**: 1.5x movement speed boost with a bottom-centered stamina gauge. Stamina is unlimited in safe zones and scales with Toon level on streets.
* **Sprint-Ramming**: Charging directly into roaming Cogs on streets initiates battle with an explosive 10% Cog HP collision strike and automated Toon combat taunts.

---

### 🏰 6. Solo-Tuned Mini-Dungeons & Cog Variants
* **50% Reduced Reserve Cogs**: Interior building encounters are rebalanced for tight, engaging solo dungeon crawls.
* **Elite Cog Variants**: Rare overworld and building spawns with distinct visual markers and bitwise combat flags:
  * **Supertype**: 2x HP, +30% Attack Damage, v2.0 Skelecog Revive, and district-wide system alerts.
  * **Prototype**: 2x Base Max HP.
  * **Alphatype**: +30% Base Attack Damage.
  * **v2.0 / Skelecogs**: Full skeletal revive phase or increased critical chance.

---

### 🏥 7. Quality of Life & World NPCs
* **Healer Hank NPC**: Positioned across all safe zones for instant full Laff recovery and status cleansing.
* **Banker NPC**: Convenient high-capacity jellybean pouch banking and deposits.
* **Instant Name Approval**: Custom Toon wish names are auto-approved immediately upon login in single-player mode.

---

## 🛠️ Setup & Requirements

### 1. Panda3D Custom SDK
This source code requires a customized version of Panda3D with Astron support:
* [Panda3D SDK for Windows (64-bit)](https://drive.google.com/file/d/1i-7C_uAfzZSaArzFh80NMD3Dg5FD2Tdt/view?usp=sharing)

---

## 🪄 Useful Developer Magic Words

| Command | Description |
| :--- | :--- |
| `~callboss` | Forces the Playground World Boss to spawn on the current street on the next spawn cycle (sets pity to 100%). |
| `~pity` | Displays current street pity rate, defeated Cogs, and persistent World Boss HP. |
| `~unlocktrinkets` | Instantly unlocks all 25 Trinkets in your Shtiker Book. |
| `~maxtoon` | Maxes out your stats, level, Gags, unlocks all Trinkets, and maxes stamina. |
| `~tireless` | Toggles infinite sprinting stamina anywhere on the map. |


---

## 📜 Credits & Acknowledgments
* **The Toontown Offline Team** — [ttoffline.com](https://ttoffline.com)
* **Toontown School House**
* **Astron** — [github.com/Astron/Astron](https://github.com/Astron/Astron)
* **Panda3D** — [github.com/panda3d/panda3d](https://github.com/panda3d/panda3d)
* **libpandadna, libotp-movement, libotp-nametags**

---
*Disclaimer: TT-RMX is a personal non-commercial tinkering and single-player modding project. Toontown Online is property of The Walt Disney Company.* 
