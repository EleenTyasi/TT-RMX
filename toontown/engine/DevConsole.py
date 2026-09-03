import sys
import os
import io
import traceback
from panda3d.core import *
from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer

class ConsoleStream(io.StringIO):
    """Tee stdout to both original stream and console buffer."""
    def __init__(self, original, console_callback):
        super().__init__()
        self.original = original
        self.console_callback = console_callback

    def write(self, s):
        if self.original:
            try:
                self.original.write(s)
            except Exception:
                pass
        if self.console_callback and s and s.strip():
            try:
                self.console_callback(s.strip())
            except Exception:
                pass

    def flush(self):
        if self.original:
            try:
                self.original.flush()
            except Exception:
                pass

class DevConsole(DirectObject):
    """
    Source Engine Developer Console for TT-RMX Fusion Engine.
    Toggled with '~' (Tilde / Grave).
    Features sv_cheats 0/1, tab completion, command history, and live output feed.
    """
    MAX_LINES = 200
    DISPLAY_LINES = 15

    CHEAT_COMMANDS = {
        'god', 'noclip', 'maxtoon', 'callboss', 'forceboss', 'tireless',
        'unlocktrinkets', 'unlock_trinkets', 'heal', 'sethp', 'immortal',
        'give_gags', 'setlevel', 'skip', 'teleport', 'ghost', 'kill',
        'rich', 'maxgags', 'levelup', 'stun', 'boost'
    }

    def __init__(self):
        DirectObject.__init__(self)
        self.isOpen = False
        self.sv_cheats = False
        self.history = []
        self.historyIndex = 0
        self.lines = []
        self.tabMatches = []
        self.tabIndex = 0
        self.lastTabPrefix = None

        self.commands = {
            'sv_cheats': self.cmd_sv_cheats,
            'clear': self.cmd_clear,
            'help': self.cmd_help,
            'find': self.cmd_find,
            'status': self.cmd_status,
            'pity': self.cmd_pity,
            'echo': self.cmd_echo,
            'fps': self.cmd_fps,
            'net_graph': self.cmd_net_graph,
            'py': self.cmd_py,
            'version': self.cmd_version,
            'exit': self.cmd_exit,
            'quit': self.cmd_exit,
            'ai_log': self.cmd_ai_log,
        }

        self.aiLogFile = os.path.join(os.getcwd(), "logs", "fusion_ai.log")
        self.aiLogOffset = 0
        self.showAiLogs = True

        self.initTextProperties()
        self.buildGui()
        self.bindKeys()
        self.hookStreams()

        # Start background polling of AI server logs
        taskMgr.doMethodLater(0.2, self.pollAiLog, 'devConsolePollAiLog')

        self.log(f"] TT-RMX Fusion Engine Developer Console initialized (64-bit).", color='header')
        self.log(f"] Type 'help' for commands. sv_cheats is currently 0 (cheats disabled).", color='dim')
        self.log(f"] AI server live log streaming is active. Toggle with 'ai_log 0/1'.", color='dim')

    def initTextProperties(self):
        tpm = TextPropertiesManager.getGlobalPtr()

        tp_ai = TextProperties()
        tp_ai.setTextColor(0.75, 0.55, 1.0, 1.0)
        tpm.setProperties('console_ai', tp_ai)

        tp_err = TextProperties()
        tp_err.setTextColor(1.0, 0.35, 0.35, 1.0)
        tpm.setProperties('console_err', tp_err)

        tp_warn = TextProperties()
        tp_warn.setTextColor(1.0, 0.85, 0.2, 1.0)
        tpm.setProperties('console_warn', tp_warn)

        tp_echo = TextProperties()
        tp_echo.setTextColor(0.3, 0.9, 1.0, 1.0)
        tpm.setProperties('console_echo', tp_echo)

    def hookStreams(self):
        try:
            sys.stdout = ConsoleStream(sys.stdout, lambda s: self.log(s, color='normal'))
        except Exception:
            pass

    def buildGui(self):
        # Create full-width top drop-down frame
        self.frame = DirectFrame(
            parent=base.a2dTopCenter,
            relief=DGG.FLAT,
            frameColor=(0.06, 0.08, 0.11, 0.94),
            frameSize=(-base.a2dRight, base.a2dRight, -0.92, 0.0),
            pos=(0, 0, 0)
        )
        self.frame.hide()

        # Top banner bar
        self.titleLabel = DirectLabel(
            parent=self.frame,
            relief=None,
            text="] TT-RMX Fusion Engine Console (64-bit)  |  sv_cheats: 0  |  Press [~] to close",
            text_scale=0.038,
            text_align=TextNode.ALeft,
            text_fg=(0.3, 0.85, 1.0, 1.0),
            text_font=ToontownGlobals.getToonFont(),
            pos=(-base.a2dRight + 0.04, 0, -0.045)
        )

        # Output text display
        self.outputNode = TextNode('consoleOutput')
        self.outputNode.setTextColor(0.85, 0.88, 0.9, 1.0)
        self.outputNode.setAlign(TextNode.ALeft)
        self.outputNode.setFont(ToontownGlobals.getToonFont())
        self.outputNode.setWordwrap(65)
        self.outputNp = self.frame.attachNewNode(self.outputNode)
        self.outputNp.setScale(0.035)
        self.outputNp.setPos(-base.a2dRight + 0.04, 0, -0.10)

        # Bottom command line prompt bar
        self.promptLabel = DirectLabel(
            parent=self.frame,
            relief=None,
            text="]",
            text_scale=0.045,
            text_align=TextNode.ALeft,
            text_fg=(0.3, 1.0, 0.5, 1.0),
            text_font=ToontownGlobals.getToonFont(),
            pos=(-base.a2dRight + 0.04, 0, -0.875)
        )

        self.entry = DirectEntry(
            parent=self.frame,
            relief=DGG.FLAT,
            frameColor=(0.03, 0.04, 0.06, 0.8),
            frameSize=(0, (base.a2dRight * 2) - 0.14, -0.015, 0.045),
            scale=0.04,
            pos=(-base.a2dRight + 0.09, 0, -0.875),
            entryFont=ToontownGlobals.getToonFont(),
            text_fg=(1.0, 1.0, 1.0, 1.0),
            cursorKeys=1,
            numLines=1,
            width=50,
            command=self.executeCommand,
            focus=0
        )

    def bindKeys(self):
        # Toggle keys
        self.accept('`', self.toggle)
        self.accept('~', self.toggle)
        self.accept('shift-`', self.toggle)
        self.accept('f10', self.toggle)

        # Navigation keys while console is open
        self.accept('arrow_up', self.historyUp)
        self.accept('arrow_down', self.historyDown)
        self.accept('tab', self.handleTab)

    def toggle(self):
        if self.isOpen:
            self.close()
        else:
            self.open()

    def open(self):
        self.isOpen = True
        self.frame.show()
        self.entry['focus'] = 1
        self.updateDisplay()

        # Stop local avatar movement while typing
        if hasattr(base, 'localAvatar') and base.localAvatar:
            try:
                base.localAvatar.stopUpdateSmartCamera()
                if hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.stopChat()
            except Exception:
                pass

    def close(self):
        self.isOpen = False
        self.frame.hide()
        self.entry['focus'] = 0

        # Restore local avatar movement
        if hasattr(base, 'localAvatar') and base.localAvatar:
            try:
                base.localAvatar.startUpdateSmartCamera()
            except Exception:
                pass

    def pollAiLog(self, task=None):
        if not self.showAiLogs:
            return task.again if task else None

        if not os.path.exists(self.aiLogFile):
            return task.again if task else None

        try:
            current_size = os.path.getsize(self.aiLogFile)
            if current_size < self.aiLogOffset:
                self.aiLogOffset = 0

            if current_size > self.aiLogOffset:
                with open(self.aiLogFile, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(self.aiLogOffset)
                    chunk = f.read()
                    self.aiLogOffset = f.tell()

                for raw_line in chunk.splitlines():
                    line = raw_line.strip()
                    if line:
                        self.log(line, color='ai')
        except Exception:
            pass

        return task.again if task else None

    def log(self, text, color='normal'):
        for line in str(text).splitlines():
            prefix = ""
            if color == 'error':
                prefix = "[ERROR] "
            elif color == 'warning':
                prefix = "[WARN] "
            elif color == 'ai' and not line.startswith("[AI]"):
                prefix = "[AI] "
            self.lines.append((prefix + line, color))

        if len(self.lines) > self.MAX_LINES:
            self.lines = self.lines[-self.MAX_LINES:]

        if self.isOpen:
            self.updateDisplay()

    def updateDisplay(self):
        display = self.lines[-self.DISPLAY_LINES:]
        formatted_lines = []
        for line_text, color in display:
            if color == 'ai':
                formatted_lines.append(f"\1console_ai\1{line_text}\2")
            elif color == 'error':
                formatted_lines.append(f"\1console_err\1{line_text}\2")
            elif color == 'warning':
                formatted_lines.append(f"\1console_warn\1{line_text}\2")
            elif color == 'echo':
                formatted_lines.append(f"\1console_echo\1{line_text}\2")
            else:
                formatted_lines.append(line_text)

        self.outputNode.setText("\n".join(formatted_lines))
        cheats_str = "1 (ENABLED)" if self.sv_cheats else "0 (DISABLED)"
        self.titleLabel['text'] = f"] TT-RMX Fusion Engine Console  |  sv_cheats: {cheats_str}  |  Press [~] to close"

    def historyUp(self):
        if not self.isOpen or not self.history:
            return
        self.historyIndex = max(0, self.historyIndex - 1)
        self.entry.enterText(self.history[self.historyIndex])

    def historyDown(self):
        if not self.isOpen:
            return
        if self.historyIndex < len(self.history) - 1:
            self.historyIndex += 1
            self.entry.enterText(self.history[self.historyIndex])
        else:
            self.historyIndex = len(self.history)
            self.entry.enterText("")

    def handleTab(self):
        if not self.isOpen:
            return
        current = self.entry.get().strip()
        if not current:
            return

        all_commands = list(self.commands.keys()) + list(self.CHEAT_COMMANDS)
        if self.lastTabPrefix != current:
            self.lastTabPrefix = current
            self.tabMatches = [c for c in all_commands if c.startswith(current.lower())]
            self.tabIndex = 0

        if self.tabMatches:
            match = self.tabMatches[self.tabIndex % len(self.tabMatches)]
            self.tabIndex += 1
            self.entry.enterText(match + " ")

    def executeCommand(self, text):
        line = text.strip()
        self.entry.enterText("")
        if not line:
            return

        self.history.append(line)
        self.historyIndex = len(self.history)
        self.log(f"] {line}", color='echo')

        parts = line.split()
        cmd = parts[0].lower()
        args = parts[1:]

        # Built-in console commands
        if cmd in self.commands:
            try:
                self.commands[cmd](args)
            except Exception as e:
                self.log(f"Command error: {e}", color='error')
            return

        # Check cheat protection
        if cmd in self.CHEAT_COMMANDS and not self.sv_cheats:
            self.log("Cheats not enabled! Turn them on by using sv_cheats 1.", color='error')
            return

        # Forward to TT-RMX Magic Word Manager
        self.forwardMagicWord(cmd, args)

    def forwardMagicWord(self, cmd, args):
        if not hasattr(base, 'cr') or not hasattr(base.cr, 'magicWordManager') or not base.cr.magicWordManager:
            self.log("Server magic word manager not available (are you logged in?)", color='warning')
            return

        full_word = "~" + cmd
        if args:
            full_word += " " + " ".join(args)

        try:
            base.cr.magicWordManager.handleMagicWord(full_word)
            self.log(f"Dispatched magic word: {full_word}", color='dim')
        except Exception as e:
            self.log(f"Failed to execute magic word: {e}", color='error')

    # ==================== Command Implementations ====================

    def cmd_sv_cheats(self, args):
        if not args:
            val = "1" if self.sv_cheats else "0"
            self.log(f"\"sv_cheats\" is \"{val}\"", color='normal')
            return

        target = args[0].strip()
        if target in ('1', 'true', 'on'):
            self.sv_cheats = True
            self.log("Server cvar 'sv_cheats' changed to 1. Cheats enabled!", color='warning')
        elif target in ('0', 'false', 'off'):
            self.sv_cheats = False
            self.log("Server cvar 'sv_cheats' changed to 0. Cheats disabled.", color='normal')
        else:
            self.log("Usage: sv_cheats <0|1>", color='warning')
        self.updateDisplay()

    def cmd_clear(self, args):
        self.lines = []
        self.updateDisplay()

    def cmd_help(self, args):
        self.log("Available Console Commands:", color='header')
        for c in sorted(self.commands.keys()):
            self.log(f"  {c}", color='normal')
        self.log("Common Cheats (requires sv_cheats 1):", color='header')
        for c in sorted(self.CHEAT_COMMANDS):
            self.log(f"  {c}", color='dim')

    def cmd_find(self, args):
        if not args:
            self.log("Usage: find <keyword>", color='warning')
            return
        query = args[0].lower()
        matches = [c for c in list(self.commands.keys()) + list(self.CHEAT_COMMANDS) if query in c]
        self.log(f"Matches for '{query}': {', '.join(matches) if matches else 'None'}", color='normal')

    def cmd_status(self, args):
        self.log("=== Toon Status ===", color='header')
        if hasattr(base, 'localAvatar') and base.localAvatar:
            av = base.localAvatar
            self.log(f" Name:     {av.getName()}", color='normal')
            self.log(f" HP:       {av.getHp()} / {av.getMaxHp()}", color='normal')
            if hasattr(av, 'getToonLevel'):
                self.log(f" Level:    {av.getToonLevel()}", color='normal')
            if hasattr(av, 'zoneId'):
                self.log(f" Zone ID:  {av.zoneId}", color='normal')
        else:
            self.log(" LocalAvatar not loaded.", color='warning')

    def cmd_pity(self, args):
        self.forwardMagicWord("pity", args)

    def cmd_echo(self, args):
        self.log(" ".join(args), color='normal')

    def cmd_fps(self, args):
        base.setFrameRateMeter(not base.frameRateMeter)
        status = "enabled" if base.frameRateMeter else "disabled"
        self.log(f"FPS display {status}.", color='normal')

    def cmd_net_graph(self, args):
        self.cmd_fps(args)

    def cmd_py(self, args):
        if not args:
            self.log("Usage: py <expression>", color='warning')
            return
        code = " ".join(args)
        try:
            result = eval(code, globals(), {'base': base, 'localAvatar': getattr(base, 'localAvatar', None)})
            self.log(f"=> {result}", color='warning')
        except Exception:
            try:
                exec(code, globals(), {'base': base, 'localAvatar': getattr(base, 'localAvatar', None)})
                self.log("=> Executed.", color='dim')
            except Exception as e:
                self.log(f"Python Error: {e}", color='error')

    def cmd_version(self, args):
        self.log("TT-RMX Fusion Engine (64-bit Python 3.9 / Panda3D 1.11.0)", color='normal')

    def cmd_ai_log(self, args):
        if not args:
            status = "enabled" if self.showAiLogs else "disabled"
            self.log(f"\"ai_log\" is \"{1 if self.showAiLogs else 0}\" ({status})", color='normal')
            return

        val = args[0].strip().lower()
        if val in ('1', 'on', 'true'):
            self.showAiLogs = True
            self.log("AI server log streaming enabled.", color='normal')
        elif val in ('0', 'off', 'false'):
            self.showAiLogs = False
            self.log("AI server log streaming disabled.", color='normal')
    def cmd_sim_turn(self, args):
        if len(args) < 4:
            self.log("Usage: sim_turn <cog_code> <cog_lvl> <gag_track> <gag_lvl>", color='warning')
            self.log("Example: sim_turn rb 12 throw 6", color='dim')
            return

        from toontown.battle.sim.BattleSim import BattleSim, SuitSnapshot, ToonSnapshot
        from toontown.battle.SuitsConfig import SUIT_ATTRIBUTES
        from toontown.toonbase.ToontownBattleGlobals import (
            HEAL_TRACK, TRAP_TRACK, LURE_TRACK, SOUND_TRACK, THROW_TRACK, SQUIRT_TRACK, DROP_TRACK
        )

        cog_code = args[0].strip().lower()
        try:
            cog_lvl = int(args[1])
        except ValueError:
            self.log("Error: cog_lvl must be an integer.", color='error')
            return

        track_str = args[2].strip().lower()
        track_map = {
            'heal': HEAL_TRACK, 'trap': TRAP_TRACK, 'lure': LURE_TRACK,
            'sound': SOUND_TRACK, 'throw': THROW_TRACK, 'squirt': SQUIRT_TRACK, 'drop': DROP_TRACK
        }
        if track_str in track_map:
            track = track_map[track_str]
        else:
            try:
                track = int(track_str)
            except ValueError:
                self.log(f"Error: unknown gag track '{track_str}'. Use heal, trap, lure, sound, throw, squirt, drop.", color='error')
                return

        try:
            gag_lvl = int(args[3]) - 1 # Convert 1-indexed to 0-indexed
            gag_lvl = max(0, min(6, gag_lvl))
        except ValueError:
            self.log("Error: gag_lvl must be an integer (1-7).", color='error')
            return

        cog_data = SUIT_ATTRIBUTES.get(cog_code)
        cog_name = cog_data['name'] if cog_data else f"Cog ({cog_code})"
        hp_val = 200
        if cog_data and 'hp' in cog_data:
            idx = min(len(cog_data['hp']) - 1, max(0, cog_lvl - cog_data.get('level', 1)))
            hp_val = cog_data['hp'][idx]

        suit_snapshot = SuitSnapshot(
            id=1,
            name=cog_name,
            code=cog_code,
            level=cog_lvl,
            hp=hp_val,
            max_hp=hp_val,
            defense=cog_lvl * 5
        )

        toon_snapshot = None
        if hasattr(base, 'localAvatar') and base.localAvatar:
            av = base.localAvatar
            toon_snapshot = ToonSnapshot(id=av.doId, name=av.getName(), hp=av.getHp(), max_hp=av.getMaxHp())

        fc = BattleSim.forecast(track, gag_lvl, suit_snapshot, toon=toon_snapshot)
        self.log("=== BattleSim Forecast ===", color='header')
        self.log(f"Target:  {fc.target_name} (Lv. {cog_lvl})  [HP: {fc.target_hp}/{fc.target_max_hp}]", color='normal')
        self.log(f"Gag:     {fc.gag_name}  (Track: {track_str.capitalize()})", color='normal')
        self.log(f"Damage:  {fc.total_expected_damage} (Min: {fc.min_damage} | Max/Crit: {fc.max_damage})", color='warning')
        self.log(f"Chance:  Hit: {fc.hit_chance_pct:.0f}%  |  Crit: {fc.crit_chance_pct:.0f}%  |  Direct: {fc.direct_chance_pct:.0f}%", color='normal')
        if fc.status_effect_name:
            self.log(f"Status:  {fc.status_effect_name} ({fc.status_effect_chance:.0f}% proc)", color='echo')
        rem_hp = max(0, fc.target_hp - fc.total_expected_damage)
        outcome = "LETHAL KILL" if fc.is_lethal else f"Survives with {rem_hp} HP"
        self.log(f"Outcome: {outcome}", color='error' if fc.is_lethal else 'normal')

    def cmd_exit(self, args):
        self.close()
