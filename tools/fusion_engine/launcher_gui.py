"""
Toontown Remix - Fusion Launcher GUI
Modern Tkinter / ttk graphical launcher for TT-RMX Fusion Engine.

Features:
- Play & Profiles: Launch mode selection, account token combobox with presets, auto-backup, launch button.
- Game Settings: Toggles & sliders hooked to settings.json (FFXIV camera, camera sensitivity, antialiasing, stretched screen, music, magic word activator).
- Save States: Database backup management, listing, creating slots, restoring, and district resetting.
- Dev & Diagnostics: Cache cleaner, bug report exporter, logs directory opener, process cleanup.
"""

import json
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Any, Dict, List, Optional

from tools.fusion_engine.config import (
    get_root_dir,
    load_game_settings,
    save_game_settings,
    update_game_settings,
    load_launcher_settings,
    save_launcher_settings,
    add_recent_token,
    set_launcher_setting,
    clean_cache,
)
from tools.fusion_engine.save_manager import (
    create_backup,
    list_backups,
    restore_backup,
    reset_district_state,
)
from tools.fusion_engine.diagnostics import package_bug_report


def _format_size(bytes_size: int) -> str:
    """Formats file size in bytes to human-readable string."""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    else:
        return f"{bytes_size / (1024 * 1024):.2f} MB"


def _open_folder_in_explorer(folder_path: str) -> None:
    """Safely opens a folder in Windows Explorer."""
    os.makedirs(folder_path, exist_ok=True)
    try:
        os.startfile(folder_path)
    except Exception:
        subprocess.Popen(["explorer.exe", os.path.normpath(folder_path)])


def _kill_lingering_ttoff_processes(exclude_pid: Optional[int] = None) -> Dict[str, Any]:
    """
    Terminates lingering Astron and TT-RMX background server processes.
    Carefully excludes the current launcher process and other unrelated processes.
    """
    killed = []
    errors = []

    # 1. Kill astrond.exe
    try:
        res = subprocess.run(
            ["taskkill", "/F", "/IM", "astrond.exe"],
            capture_output=True,
            text=True
        )
        if "SUCCESS" in res.stdout:
            killed.append("astrond.exe")
    except Exception as e:
        errors.append(f"astrond.exe: {e}")

    # 2. Query running python processes matching TT-RMX markers via PowerShell
    script = (
        'Get-CimInstance Win32_Process | '
        'Where-Object { ($_.Name -like "*python*" -or $_.Name -like "*ppython*") } | '
        'Select-Object ProcessId, CommandLine | '
        'ConvertTo-Json -Compress'
    )
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True
        )
        out = res.stdout.strip()
        if out:
            import json as _json
            data = _json.loads(out)
            if isinstance(data, dict):
                data = [data]
            
            markers = ["toontown.uberdog.UDStart", "toontown.ai.AIStart", "toontown.launcher.TTOffQuickStartLauncher"]
            for proc in data:
                pid = proc.get("ProcessId")
                cmdline = proc.get("CommandLine") or ""
                if pid and pid != exclude_pid and pid != os.getpid():
                    if any(m in cmdline for m in markers):
                        try:
                            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
                            killed.append(f"PID {pid} ({cmdline[:40]}...)")
                        except Exception as e:
                            errors.append(f"PID {pid}: {e}")
    except Exception as e:
        errors.append(f"Process query error: {e}")

    return {"killed": killed, "errors": errors}


class FusionLauncherApp:
    """Main Application Controller for the Fusion Launcher GUI."""

    def __init__(self, root: tk.Tk, root_dir: Optional[str] = None):
        self.root = root
        self.root_dir = root_dir or get_root_dir()
        self.result: Dict[str, Any] = {"action": "exit"}

        # Window configuration
        self.root.title("Toontown Remix - Fusion Launcher")
        self.root.geometry("680x600")
        self.root.minsize(640, 560)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Try to set window icon
        icon_path = os.path.join(self.root_dir, "resources", "phase_3", "models", "gui", "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        # Load configuration settings
        self.launcher_settings = load_launcher_settings(self.root_dir)
        self.game_settings = load_game_settings(self.root_dir)

        # Configure styles
        self._setup_styles()

        # Build UI layout
        self._build_header()
        self._build_tabs()
        self._build_footer()

    def _setup_styles(self) -> None:
        """Configures ttk styles for a clean, modern aesthetic matching Toontown Remix."""
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.root.configure(bg="#F3F4F6")

        # Tab notebook styling
        self.style.configure(
            "TNotebook",
            background="#F3F4F6",
            borderwidth=0
        )
        self.style.configure(
            "TNotebook.Tab",
            font=("Segoe UI", 10, "bold"),
            padding=[16, 8],
            background="#E5E7EB",
            foreground="#374151"
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", "#FFFFFF"), ("active", "#D1D5DB")],
            foreground=[("selected", "#1D4ED8"), ("active", "#1F2937")]
        )

        # Standard card frames
        self.style.configure(
            "Card.TFrame",
            background="#FFFFFF",
            relief="solid",
            borderwidth=1
        )

        # Labels
        self.style.configure(
            "TLabel",
            background="#FFFFFF",
            foreground="#1F2937",
            font=("Segoe UI", 9)
        )
        self.style.configure(
            "Header.TLabel",
            background="#1E3A8A",
            foreground="#FFFFFF",
            font=("Segoe UI", 15, "bold")
        )
        self.style.configure(
            "SubHeader.TLabel",
            background="#1E3A8A",
            foreground="#93C5FD",
            font=("Segoe UI", 9)
        )
        self.style.configure(
            "SectionTitle.TLabel",
            background="#FFFFFF",
            foreground="#1E3A8A",
            font=("Segoe UI", 11, "bold")
        )
        self.style.configure(
            "Status.TLabel",
            background="#F3F4F6",
            foreground="#2563EB",
            font=("Segoe UI", 9, "bold")
        )

        # Checkbuttons & Radiobuttons
        self.style.configure(
            "TCheckbutton",
            background="#FFFFFF",
            foreground="#1F2937",
            font=("Segoe UI", 9)
        )
        self.style.configure(
            "TRadiobutton",
            background="#FFFFFF",
            foreground="#1F2937",
            font=("Segoe UI", 9)
        )

        # Treeview
        self.style.configure(
            "Treeview",
            font=("Segoe UI", 9),
            rowheight=24,
            background="#FFFFFF",
            fieldbackground="#FFFFFF"
        )
        self.style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#F1F5F9",
            foreground="#1E293B"
        )

        # Buttons
        self.style.configure(
            "Action.TButton",
            font=("Segoe UI", 9, "bold"),
            padding=[10, 5]
        )
        self.style.configure(
            "Primary.TButton",
            font=("Segoe UI", 9, "bold"),
            padding=[12, 6]
        )

    def _build_header(self) -> None:
        """Builds the top header banner."""
        header_frame = tk.Frame(self.root, bg="#1E3A8A", padx=20, pady=12)
        header_frame.pack(fill="x", side="top")

        title_lbl = tk.Label(
            header_frame,
            text="Toontown Remix",
            font=("Segoe UI", 16, "bold"),
            fg="#FFFFFF",
            bg="#1E3A8A"
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = tk.Label(
            header_frame,
            text="Fusion Engine - Next Generation 64-Bit Launcher",
            font=("Segoe UI", 9),
            fg="#93C5FD",
            bg="#1E3A8A"
        )
        subtitle_lbl.pack(anchor="w")

    def _build_tabs(self) -> None:
        """Builds the tabbed interface using ttk.Notebook."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=10)

        # Tab 1: Play & Profiles
        self.tab_play = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_play, text="  Play & Profiles  ")
        self._build_tab_play()

        # Tab 2: Game Settings
        self.tab_settings = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_settings, text="  Game Settings  ")
        self._build_tab_settings()

        # Tab 3: Save States
        self.tab_saves = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_saves, text="  Save States  ")
        self._build_tab_saves()

        # Tab 4: Dev & Diagnostics
        self.tab_dev = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dev, text="  Dev & Diagnostics  ")
        self._build_tab_dev()

    # -------------------------------------------------------------------------
    # TAB 1: Play & Profiles
    # -------------------------------------------------------------------------
    def _build_tab_play(self) -> None:
        pad_frame = tk.Frame(self.tab_play, bg="#F3F4F6", padx=8, pady=8)
        pad_frame.pack(fill="both", expand=True)

        card = tk.Frame(pad_frame, bg="#FFFFFF", bd=1, relief="solid", padx=20, pady=18)
        card.pack(fill="both", expand=True)

        # Section 1: Launch Mode
        mode_title = tk.Label(
            card,
            text="Launch Mode",
            font=("Segoe UI", 11, "bold"),
            fg="#1E3A8A",
            bg="#FFFFFF"
        )
        mode_title.pack(anchor="w", pady=(0, 6))

        self.mode_var = tk.StringVar(value=self.launcher_settings.get("launch_mode", "normal"))
        mode_box = tk.Frame(card, bg="#FFFFFF")
        mode_box.pack(fill="x", pady=(0, 16))

        modes = [
            ("Full Stack / Solo", "normal", "Launches Astron, UberDOG, AI Server, and Game Client."),
            ("Client Only", "client_only", "Launches only the Game Client (connects to existing local server)."),
            ("Dual Client", "dual_client", "Launches Full Stack with two client instances for multi-toon testing."),
        ]

        for text, val, desc in modes:
            r_frame = tk.Frame(mode_box, bg="#FFFFFF")
            r_frame.pack(fill="x", pady=2)
            rb = ttk.Radiobutton(r_frame, text=text, value=val, variable=self.mode_var)
            rb.pack(side="left", anchor="w")
            lbl_desc = tk.Label(r_frame, text=f"-  {desc}", font=("Segoe UI", 8), fg="#6B7280", bg="#FFFFFF")
            lbl_desc.pack(side="left", padx=(8, 0), anchor="w")

        sep1 = ttk.Separator(card, orient="horizontal")
        sep1.pack(fill="x", pady=(0, 14))

        # Section 2: Account / Login Token
        token_title = tk.Label(
            card,
            text="Account / Login Token",
            font=("Segoe UI", 11, "bold"),
            fg="#1E3A8A",
            bg="#FFFFFF"
        )
        token_title.pack(anchor="w", pady=(0, 4))

        token_hint = tk.Label(
            card,
            text="Select a preset profile or type any custom username/token for your local save:",
            font=("Segoe UI", 8),
            fg="#4B5563",
            bg="#FFFFFF"
        )
        token_hint.pack(anchor="w", pady=(0, 8))

        token_row = tk.Frame(card, bg="#FFFFFF")
        token_row.pack(fill="x", pady=(0, 16))

        # Build preset token list
        presets = ["dev", "uber"]
        recent = self.launcher_settings.get("recent_tokens", [])
        combined_tokens = list(dict.fromkeys(presets + recent))

        self.token_combobox = ttk.Combobox(token_row, values=combined_tokens, font=("Segoe UI", 10), width=32)
        self.token_combobox.set(self.launcher_settings.get("last_token", "dev"))
        self.token_combobox.pack(side="left", padx=(0, 10))

        preset_hint = tk.Label(
            token_row,
            text="('dev' = Maxed Toon, 'uber' = Uber Toon)",
            font=("Segoe UI", 8, "italic"),
            fg="#6B7280",
            bg="#FFFFFF"
        )
        preset_hint.pack(side="left")

        sep2 = ttk.Separator(card, orient="horizontal")
        sep2.pack(fill="x", pady=(0, 14))

        # Section 3: Pre-launch Options
        opts_title = tk.Label(
            card,
            text="Launch Options",
            font=("Segoe UI", 11, "bold"),
            fg="#1E3A8A",
            bg="#FFFFFF"
        )
        opts_title.pack(anchor="w", pady=(0, 6))

        self.auto_backup_var = tk.BooleanVar(value=self.launcher_settings.get("auto_backup", True))
        chk_backup = ttk.Checkbutton(
            card,
            text="Auto-backup database before launch (preserves last 5 snapshots)",
            variable=self.auto_backup_var
        )
        chk_backup.pack(anchor="w", pady=(0, 18))

        # Section 4: Prominent Launch Button
        btn_frame = tk.Frame(card, bg="#FFFFFF")
        btn_frame.pack(fill="x", pady=(8, 4))

        self.launch_btn = tk.Button(
            btn_frame,
            text="▶  LAUNCH GAME",
            font=("Segoe UI", 13, "bold"),
            bg="#16A34A",
            fg="#FFFFFF",
            activebackground="#15803D",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=24,
            pady=12,
            cursor="hand2",
            command=self._on_launch_clicked
        )
        self.launch_btn.pack(fill="x")

        # Status label
        self.play_status_lbl = tk.Label(
            card,
            text="Ready to launch",
            font=("Segoe UI", 9, "bold"),
            fg="#2563EB",
            bg="#FFFFFF"
        )
        self.play_status_lbl.pack(anchor="center", pady=(8, 0))

    # -------------------------------------------------------------------------
    # TAB 2: Game Settings
    # -------------------------------------------------------------------------
    def _build_tab_settings(self) -> None:
        pad_frame = tk.Frame(self.tab_settings, bg="#F3F4F6", padx=8, pady=8)
        pad_frame.pack(fill="both", expand=True)

        card = tk.Frame(pad_frame, bg="#FFFFFF", bd=1, relief="solid", padx=20, pady=16)
        card.pack(fill="both", expand=True)

        title = tk.Label(
            card,
            text="Game Configuration (settings.json)",
            font=("Segoe UI", 11, "bold"),
            fg="#1E3A8A",
            bg="#FFFFFF"
        )
        title.pack(anchor="w", pady=(0, 12))

        game_data = self.game_settings.get("game", {})

        # Controls grid
        grid = tk.Frame(card, bg="#FFFFFF")
        grid.pack(fill="both", expand=True, pady=(0, 12))

        # Row 0: FFXIV Camera
        self.ffxiv_var = tk.BooleanVar(value=bool(game_data.get("ffxiv-camera", True)))
        chk_ffxiv = ttk.Checkbutton(
            grid,
            text="FFXIV Camera (Modern 360° mouse-look camera)",
            variable=self.ffxiv_var
        )
        chk_ffxiv.grid(row=0, column=0, columnspan=2, sticky="w", pady=4)

        # Row 1: Camera Sensitivity
        lbl_sens = tk.Label(grid, text="Camera Sensitivity:", font=("Segoe UI", 9), bg="#FFFFFF")
        lbl_sens.grid(row=1, column=0, sticky="w", pady=6)

        sens_val = float(game_data.get("camera-sensitivity", 1.4))
        self.sens_var = tk.DoubleVar(value=sens_val)

        sens_subframe = tk.Frame(grid, bg="#FFFFFF")
        sens_subframe.grid(row=1, column=1, sticky="w", pady=6)

        self.sens_slider = ttk.Scale(
            sens_subframe,
            from_=0.2,
            to=4.0,
            variable=self.sens_var,
            orient="horizontal",
            length=220,
            command=self._on_sens_changed
        )
        self.sens_slider.pack(side="left", padx=(0, 8))

        self.sens_display = tk.Label(
            sens_subframe,
            text=f"{sens_val:.1f}",
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF",
            width=5
        )
        self.sens_display.pack(side="left")

        # Row 2: Antialiasing
        lbl_aa = tk.Label(grid, text="Antialiasing (MSAA):", font=("Segoe UI", 9), bg="#FFFFFF")
        lbl_aa.grid(row=2, column=0, sticky="w", pady=6)

        self.aa_options = {
            "Off (0)": 0,
            "2x MSAA (2)": 2,
            "4x MSAA (4)": 4,
            "8x MSAA (8)": 8,
            "16x MSAA (16)": 16,
        }
        curr_aa = int(game_data.get("antialiasing", 0))
        # Find key corresponding to current val
        default_aa_text = "Off (0)"
        for k, v in self.aa_options.items():
            if v == curr_aa:
                default_aa_text = k
                break

        self.aa_combobox = ttk.Combobox(
            grid,
            values=list(self.aa_options.keys()),
            state="readonly",
            width=20,
            font=("Segoe UI", 9)
        )
        self.aa_combobox.set(default_aa_text)
        self.aa_combobox.grid(row=2, column=1, sticky="w", pady=6)

        # Row 3: Stretched Screen
        self.stretched_var = tk.BooleanVar(value=bool(game_data.get("stretched-screen", False)))
        chk_stretched = ttk.Checkbutton(
            grid,
            text="Stretched Screen (Wide display stretch)",
            variable=self.stretched_var
        )
        chk_stretched.grid(row=3, column=0, columnspan=2, sticky="w", pady=4)

        # Row 4: Music
        self.music_var = tk.BooleanVar(value=bool(game_data.get("music", False)))
        chk_music = ttk.Checkbutton(
            grid,
            text="In-Game Music (Default music playback)",
            variable=self.music_var
        )
        chk_music.grid(row=4, column=0, columnspan=2, sticky="w", pady=4)

        # Row 5: Magic Word Activator
        lbl_mw = tk.Label(grid, text="Magic Word Activator:", font=("Segoe UI", 9), bg="#FFFFFF")
        lbl_mw.grid(row=5, column=0, sticky="w", pady=6)

        self.mw_options = {
            "0: ~ (Tilde, Default)": 0,
            "1: ? (Question Mark)": 1,
            "2: ` (Backtick)": 2,
        }
        curr_mw = int(game_data.get("magic-word-activator", 0))
        default_mw_text = "0: ~ (Tilde, Default)"
        for k, v in self.mw_options.items():
            if v == curr_mw:
                default_mw_text = k
                break

        self.mw_combobox = ttk.Combobox(
            grid,
            values=list(self.mw_options.keys()),
            state="readonly",
            width=24,
            font=("Segoe UI", 9)
        )
        self.mw_combobox.set(default_mw_text)
        self.mw_combobox.grid(row=5, column=1, sticky="w", pady=6)

        # Bottom Button Bar
        btn_bar = tk.Frame(card, bg="#FFFFFF")
        btn_bar.pack(fill="x", pady=(10, 0))

        save_btn = tk.Button(
            btn_bar,
            text="💾  Save Settings",
            font=("Segoe UI", 9, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=16,
            pady=6,
            cursor="hand2",
            command=self._on_save_settings
        )
        save_btn.pack(side="left")

        self.settings_status = tk.Label(
            btn_bar,
            text="",
            font=("Segoe UI", 9, "italic"),
            fg="#16A34A",
            bg="#FFFFFF"
        )
        self.settings_status.pack(side="left", padx=12)

    def _on_sens_changed(self, val: str) -> None:
        """Updates numeric display when sensitivity slider moves."""
        try:
            v = float(val)
            self.sens_display.config(text=f"{v:.1f}")
        except ValueError:
            pass

    def _on_save_settings(self) -> None:
        """Saves values from Game Settings tab into settings.json."""
        aa_val = self.aa_options.get(self.aa_combobox.get(), 0)
        mw_val = self.mw_options.get(self.mw_combobox.get(), 0)
        sens_val = round(float(self.sens_var.get()), 1)

        updates = {
            "ffxiv-camera": self.ffxiv_var.get(),
            "camera-sensitivity": sens_val,
            "antialiasing": aa_val,
            "stretched-screen": self.stretched_var.get(),
            "music": self.music_var.get(),
            "magic-word-activator": mw_val,
        }

        try:
            update_game_settings(updates, self.root_dir)
            self.game_settings = load_game_settings(self.root_dir)
            self.settings_status.config(text="✓ Settings saved to settings.json!", fg="#16A34A")
            self.root.after(3000, lambda: self.settings_status.config(text=""))
        except Exception as e:
            self.settings_status.config(text=f"Error saving settings: {e}", fg="#DC2626")

    # -------------------------------------------------------------------------
    # TAB 3: Save States
    # -------------------------------------------------------------------------
    def _build_tab_saves(self) -> None:
        pad_frame = tk.Frame(self.tab_saves, bg="#F3F4F6", padx=8, pady=8)
        pad_frame.pack(fill="both", expand=True)

        card = tk.Frame(pad_frame, bg="#FFFFFF", bd=1, relief="solid", padx=16, pady=14)
        card.pack(fill="both", expand=True)

        header_row = tk.Frame(card, bg="#FFFFFF")
        header_row.pack(fill="x", pady=(0, 8))

        title = tk.Label(
            header_row,
            text="Astron Database Backups",
            font=("Segoe UI", 11, "bold"),
            fg="#1E3A8A",
            bg="#FFFFFF"
        )
        title.pack(side="left")

        refresh_btn = ttk.Button(header_row, text="🔄 Refresh", command=self._refresh_backups_list)
        refresh_btn.pack(side="right")

        # Treeview frame with scrollbar
        tree_frame = tk.Frame(card, bg="#FFFFFF")
        tree_frame.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("slot_name", "date", "size", "type")
        self.tree_saves = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=9
        )

        self.tree_saves.heading("slot_name", text="Slot Name")
        self.tree_saves.heading("date", text="Date & Time")
        self.tree_saves.heading("size", text="Size")
        self.tree_saves.heading("type", text="Type")

        self.tree_saves.column("slot_name", width=220, anchor="w")
        self.tree_saves.column("date", width=160, anchor="center")
        self.tree_saves.column("size", width=90, anchor="e")
        self.tree_saves.column("type", width=80, anchor="center")

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_saves.yview)
        self.tree_saves.configure(yscrollcommand=scroll.set)

        self.tree_saves.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Action button bar
        btn_bar = tk.Frame(card, bg="#FFFFFF")
        btn_bar.pack(fill="x", pady=(4, 0))

        btn_new = tk.Button(
            btn_bar,
            text="＋ New Save Slot",
            font=("Segoe UI", 9, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=12,
            pady=5,
            cursor="hand2",
            command=self._on_new_save_slot
        )
        btn_new.pack(side="left", padx=(0, 6))

        btn_restore = tk.Button(
            btn_bar,
            text="⟲ Restore Selected",
            font=("Segoe UI", 9),
            bg="#F1F5F9",
            fg="#1E293B",
            activebackground="#E2E8F0",
            relief="solid",
            bd=1,
            padx=12,
            pady=5,
            cursor="hand2",
            command=self._on_restore_selected
        )
        btn_restore.pack(side="left", padx=(0, 6))

        btn_reset = tk.Button(
            btn_bar,
            text="⚠ Reset District (Fresh Start)",
            font=("Segoe UI", 9),
            bg="#FEF2F2",
            fg="#DC2626",
            activebackground="#FEE2E2",
            relief="solid",
            bd=1,
            padx=12,
            pady=5,
            cursor="hand2",
            command=self._on_reset_district
        )
        btn_reset.pack(side="left", padx=(0, 6))

        btn_folder = tk.Button(
            btn_bar,
            text="📁 Open Backups Folder",
            font=("Segoe UI", 9),
            bg="#F1F5F9",
            fg="#4B5563",
            activebackground="#E2E8F0",
            relief="solid",
            bd=1,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._on_open_backups_folder
        )
        btn_folder.pack(side="right")

        # Initial populate
        self._refresh_backups_list()

    def _refresh_backups_list(self) -> None:
        """Reloads backup slots into the Treeview."""
        for item in self.tree_saves.get_children():
            self.tree_saves.delete(item)

        backups = list_backups(self.root_dir)
        for b in backups:
            slot_name = b.get("slot_name", "")
            date_str = b.get("formatted_date", "")
            size_str = _format_size(b.get("size", 0))
            type_str = "Auto" if b.get("is_auto") else "Manual"
            self.tree_saves.insert("", "end", iid=slot_name, values=(slot_name, date_str, size_str, type_str))

    def _on_new_save_slot(self) -> None:
        """Prompts for a slot name and creates a new manual backup."""
        name = simpledialog.askstring("New Save Slot", "Enter a name for this backup slot:", parent=self.root)
        if not name:
            return
        clean_name = "".join(c for c in name.strip() if c.isalnum() or c in ("-", "_")).strip()
        if not clean_name:
            messagebox.showwarning("Invalid Name", "Please enter a valid slot name.", parent=self.root)
            return

        try:
            info = create_backup(self.root_dir, slot_name=clean_name, is_auto=False)
            self._refresh_backups_list()
            messagebox.showinfo(
                "Backup Created",
                f"Successfully created backup '{info['slot_name']}' ({_format_size(info['size'])}).",
                parent=self.root
            )
        except Exception as e:
            messagebox.showerror("Backup Error", f"Failed to create backup: {e}", parent=self.root)

    def _on_restore_selected(self) -> None:
        """Restores the currently selected backup slot."""
        selected = self.tree_saves.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a backup slot to restore.", parent=self.root)
            return

        slot_name = selected[0]
        confirm = messagebox.askyesno(
            "Restore Backup",
            f"Are you sure you want to restore '{slot_name}'?\n\n"
            "This will overwrite the current astron database state with the contents of this snapshot.",
            parent=self.root
        )
        if not confirm:
            return

        try:
            res = restore_backup(self.root_dir, slot_name=slot_name)
            messagebox.showinfo(
                "Backup Restored",
                f"Successfully restored slot '{slot_name}'.",
                parent=self.root
            )
            self._refresh_backups_list()
        except Exception as e:
            messagebox.showerror("Restore Error", f"Failed to restore backup: {e}", parent=self.root)

    def _on_reset_district(self) -> None:
        """Resets the district state for a fresh start after auto-backup."""
        confirm = messagebox.askyesno(
            "Reset District",
            "Are you sure you want to reset the district?\n\n"
            "• An automatic backup of the current state will be created.\n"
            "• All database objects and accounts will be wiped for a clean playthrough.\n\n"
            "Do you wish to proceed?",
            icon="warning",
            parent=self.root
        )
        if not confirm:
            return

        try:
            res = reset_district_state(self.root_dir)
            self._refresh_backups_list()
            messagebox.showinfo(
                "District Reset",
                f"District successfully reset to fresh state!\n"
                f"Pre-reset snapshot saved as: '{res['auto_backup']['slot_name']}'.",
                parent=self.root
            )
        except Exception as e:
            messagebox.showerror("Reset Error", f"Failed to reset district: {e}", parent=self.root)

    def _on_open_backups_folder(self) -> None:
        """Opens backups/saves folder in explorer."""
        backups_dir = os.path.join(self.root_dir, "backups", "saves")
        _open_folder_in_explorer(backups_dir)

    # -------------------------------------------------------------------------
    # TAB 4: Dev & Diagnostics
    # -------------------------------------------------------------------------
    def _build_tab_dev(self) -> None:
        pad_frame = tk.Frame(self.tab_dev, bg="#F3F4F6", padx=8, pady=8)
        pad_frame.pack(fill="both", expand=True)

        card = tk.Frame(pad_frame, bg="#FFFFFF", bd=1, relief="solid", padx=20, pady=18)
        card.pack(fill="both", expand=True)

        title = tk.Label(
            card,
            text="Developer & Diagnostic Utilities",
            font=("Segoe UI", 11, "bold"),
            fg="#1E3A8A",
            bg="#FFFFFF"
        )
        title.pack(anchor="w", pady=(0, 6))

        desc = tk.Label(
            card,
            text="Tools for cache maintenance, bug reporting, logs analysis, and orphan process termination:",
            font=("Segoe UI", 8),
            fg="#4B5563",
            bg="#FFFFFF"
        )
        desc.pack(anchor="w", pady=(0, 16))

        # Utilities list
        items = [
            (
                "🧹  Clean Cache",
                "Purges compiled Python bytecode (*.pyc, *.pyo, __pycache__, parsetab.py).",
                self._on_clean_cache,
                "#2563EB"
            ),
            (
                "📦  Export Bug Report (.zip)",
                "Packages logs, settings, system diagnostics, and failure traces into a zip archive.",
                self._on_export_bug_report,
                "#2563EB"
            ),
            (
                "📁  Open Logs Directory",
                "Opens the TT-RMX logs/ folder in Windows Explorer.",
                self._on_open_logs_dir,
                "#4B5563"
            ),
            (
                "⛔  Kill Lingering Processes",
                "Terminates any orphaned Astron (astrond.exe) or TT-RMX server background processes.",
                self._on_kill_processes,
                "#DC2626"
            ),
        ]

        for btn_text, item_desc, cmd, color in items:
            row = tk.Frame(card, bg="#FFFFFF")
            row.pack(fill="x", pady=8)

            btn = tk.Button(
                row,
                text=btn_text,
                font=("Segoe UI", 9, "bold"),
                bg=color,
                fg="#FFFFFF",
                activebackground="#1D4ED8" if color != "#DC2626" else "#B91C1C",
                activeforeground="#FFFFFF",
                relief="flat",
                bd=0,
                width=24,
                padx=10,
                pady=6,
                cursor="hand2",
                command=cmd
            )
            btn.pack(side="left", padx=(0, 14))

            lbl = tk.Label(
                row,
                text=item_desc,
                font=("Segoe UI", 9),
                fg="#374151",
                bg="#FFFFFF",
                wraplength=380,
                justify="left"
            )
            lbl.pack(side="left", fill="x", expand=True)

    def _on_clean_cache(self) -> None:
        """Cleans bytecode and cache."""
        try:
            res = clean_cache(self.root_dir)
            files_c = res.get("files_deleted", 0)
            dirs_c = res.get("dirs_deleted", 0)
            errors = res.get("errors", [])

            msg = f"Cache cleaned successfully!\n\n• {files_c} file(s) removed\n• {dirs_c} __pycache__ directory(ies) removed"
            if errors:
                msg += f"\n\nEncountered {len(errors)} error(s) during removal."
            messagebox.showinfo("Clean Cache", msg, parent=self.root)
        except Exception as e:
            messagebox.showerror("Clean Cache Error", f"Failed to clean cache: {e}", parent=self.root)

    def _on_export_bug_report(self) -> None:
        """Packages bug report and offers to open folder."""
        try:
            zip_path = package_bug_report(self.root_dir, component_id="launcher")
            open_folder = messagebox.askyesno(
                "Bug Report Exported",
                f"Bug report successfully created:\n{zip_path}\n\nDo you want to open the logs directory?",
                parent=self.root
            )
            if open_folder:
                logs_dir = os.path.dirname(zip_path)
                _open_folder_in_explorer(logs_dir)
        except Exception as e:
            messagebox.showerror("Bug Report Error", f"Failed to package bug report: {e}", parent=self.root)

    def _on_open_logs_dir(self) -> None:
        """Opens logs/ directory."""
        logs_dir = os.path.join(self.root_dir, "logs")
        _open_folder_in_explorer(logs_dir)

    def _on_kill_processes(self) -> None:
        """Terminates lingering background processes."""
        confirm = messagebox.askyesno(
            "Kill Lingering Processes",
            "Are you sure you want to terminate all background Astron and TT-RMX server processes?",
            icon="warning",
            parent=self.root
        )
        if not confirm:
            return

        res = _kill_lingering_ttoff_processes(exclude_pid=os.getpid())
        killed = res.get("killed", [])
        if killed:
            killed_list = "\n• " + "\n• ".join(killed)
            messagebox.showinfo(
                "Processes Terminated",
                f"Successfully terminated {len(killed)} process(es):{killed_list}",
                parent=self.root
            )
        else:
            messagebox.showinfo("Processes Clean", "No lingering TT-RMX processes were detected.", parent=self.root)

    # -------------------------------------------------------------------------
    # Footer & Launch Actions
    # -------------------------------------------------------------------------
    def _build_footer(self) -> None:
        """Builds bottom bar with status and exit button."""
        footer_frame = tk.Frame(self.root, bg="#E5E7EB", padx=16, pady=8)
        footer_frame.pack(fill="x", side="bottom")

        self.global_status = tk.Label(
            footer_frame,
            text="Toontown Remix Fusion Engine v2.0 - Ready",
            font=("Segoe UI", 8),
            fg="#4B5563",
            bg="#E5E7EB"
        )
        self.global_status.pack(side="left")

        exit_btn = ttk.Button(footer_frame, text="Exit", command=self._on_close)
        exit_btn.pack(side="right")

    def _on_launch_clicked(self) -> None:
        """Handles Launch Game button click."""
        token = self.token_combobox.get().strip() or "dev"
        mode = self.mode_var.get() or "normal"
        auto_backup = self.auto_backup_var.get()

        # Update launcher settings
        try:
            add_recent_token(token, self.root_dir)
            set_launcher_setting("launch_mode", mode, self.root_dir)
            set_launcher_setting("auto_backup", auto_backup, self.root_dir)
        except Exception as e:
            print(f"[Fusion Launcher] Notice: Could not save launcher settings: {e}")

        # Update UI feedback
        self.play_status_lbl.config(text="Launching Toontown Remix...", fg="#16A34A")
        self.global_status.config(text="Launching game...")
        self.root.update_idletasks()

        # Store launch configuration
        self.result = {
            "action": "launch",
            "token": token,
            "mode": mode,
            "auto_backup": auto_backup,
        }

        # Perform auto-backup if selected
        if auto_backup:
            try:
                self.play_status_lbl.config(text="Creating pre-launch database backup...", fg="#2563EB")
                self.root.update_idletasks()
                create_backup(self.root_dir, is_auto=True)
            except Exception as e:
                print(f"[Fusion Launcher] Warning: Pre-launch auto-backup failed: {e}")

        # Close launcher GUI to proceed to launch
        self.root.after(200, self.root.destroy)

    def _on_close(self) -> None:
        """Window close protocol handler."""
        self.result = {"action": "exit"}
        self.root.destroy()


def show_launcher_gui(root_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Displays the Toontown Remix Fusion Launcher Tkinter GUI.

    Args:
        root_dir: Path to the TT-RMX workspace root directory. If None, resolved automatically.

    Returns:
        Dict containing launch configuration or exit action:
        e.g. {"action": "launch", "token": "dev", "mode": "normal", "auto_backup": True}
        or {"action": "exit"}
    """
    root = tk.Tk()
    app = FusionLauncherApp(root, root_dir=root_dir)

    # Center window on screen
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    x = max(0, (root.winfo_screenwidth() // 2) - (w // 2))
    y = max(0, (root.winfo_screenheight() // 2) - (h // 2))
    root.geometry(f"{w}x{h}+{x}+{y}")

    root.lift()
    root.focus_force()
    root.mainloop()

    return app.result


if __name__ == "__main__":
    result = show_launcher_gui()
    print("[Fusion Launcher GUI Result]:", result)
