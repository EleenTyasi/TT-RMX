# Tools / Fusion Engine Orchestrator
import os
import sys

# Ensure repository root is in sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
import time
import shutil
import argparse
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional

from tools.fusion_engine.config import (
    get_root_dir,
    load_launcher_settings,
    save_launcher_settings,
    add_recent_token,
    clean_cache,
)
from tools.fusion_engine.save_manager import (
    create_backup,
    list_backups,
    restore_backup,
    reset_district_state,
)
from tools.fusion_engine.diagnostics import (
    analyze_failure,
    package_bug_report,
    get_panda_error_info,
)
from tools.fusion_engine.launcher_gui import show_launcher_gui
from tools.fusion_engine.dev_console import LiveSupervisor


def show_warning_dialog(root_dir, dest_log_dir, failed_component, failure_info=None):
    choice = {"action": "abort"}

    summary_text = "It looks like Toontown Remix has ran into a problem... Check your logs!"
    root_cause_text = ""
    suggestion_text = ""

    if failure_info and isinstance(failure_info, dict):
        if failure_info.get("summary"):
            summary_text = failure_info["summary"]
        if failure_info.get("root_cause"):
            root_cause_text = "Cause: " + failure_info["root_cause"]
        if failure_info.get("suggestions"):
            suggestion_text = "Suggestion: " + failure_info["suggestions"][0]

    try:
        import tkinter as tk

        root = tk.Tk()
        root.title("Toontown Remix - Crash Diagnostics")
        root.resizable(False, False)
        root.attributes("-topmost", True)

        def on_relaunch():
            choice["action"] = "relaunch"
            root.destroy()

        def on_export_zip():
            try:
                zip_p = package_bug_report(root_dir, failed_component, extra_info=failure_info)
                print(f"[Fusion] Bug report generated: {zip_p}")
                try:
                    subprocess.Popen(["explorer.exe", "/select,", os.path.normpath(zip_p)])
                except Exception:
                    subprocess.Popen(["explorer.exe", os.path.dirname(os.path.normpath(zip_p))])
            except Exception as ex:
                print(f"[Fusion ERROR] Failed to create bug report: {ex}")

        def on_open_log():
            choice["action"] = "open_log"
            root.destroy()

        def on_abort():
            choice["action"] = "abort"
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_abort)

        frame = tk.Frame(root, padx=20, pady=18, bg="#ffffff")
        frame.pack(fill="both", expand=True)

        top_box = tk.Frame(frame, bg="#ffffff")
        top_box.pack(fill="x", pady=(0, 12))

        icon_lbl = tk.Label(top_box, text="[ ! ]", font=("Segoe UI", 20, "bold"), fg="#dc2626", bg="#ffffff")
        icon_lbl.pack(side="left", padx=(0, 12))

        msg_box = tk.Frame(top_box, bg="#ffffff")
        msg_box.pack(side="left", fill="x", expand=True)

        msg_lbl = tk.Label(
            msg_box,
            text=summary_text,
            font=("Segoe UI", 10, "bold"),
            fg="#1f2937",
            bg="#ffffff",
            wraplength=420,
            justify="left"
        )
        msg_lbl.pack(anchor="w")

        if root_cause_text:
            cause_lbl = tk.Label(
                msg_box,
                text=root_cause_text,
                font=("Consolas", 9),
                fg="#b91c1c",
                bg="#ffffff",
                wraplength=420,
                justify="left"
            )
            cause_lbl.pack(anchor="w", pady=(3, 0))

        if suggestion_text:
            sug_lbl = tk.Label(
                msg_box,
                text=suggestion_text,
                font=("Segoe UI", 8, "italic"),
                fg="#4b5563",
                bg="#ffffff",
                wraplength=420,
                justify="left"
            )
            sug_lbl.pack(anchor="w", pady=(3, 0))

        btn_bar = tk.Frame(frame, bg="#ffffff")
        btn_bar.pack(fill="x", pady=(10, 0))

        b1 = tk.Button(btn_bar, text="Attempt Relaunch", command=on_relaunch, width=15, font=("Segoe UI", 9))
        b1.pack(side="left", padx=3)

        b_zip = tk.Button(btn_bar, text="Export Bug Report (.zip)", command=on_export_zip, width=22, font=("Segoe UI", 9), bg="#f3f4f6")
        b_zip.pack(side="left", padx=3)

        b2 = tk.Button(btn_bar, text="Open Log Dir", command=on_open_log, width=13, font=("Segoe UI", 9))
        b2.pack(side="left", padx=3)

        b3 = tk.Button(btn_bar, text="Abort", command=on_abort, width=8, font=("Segoe UI", 9))
        b3.pack(side="left", padx=3)

        root.update_idletasks()
        w = root.winfo_width()
        h = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        root.geometry(f"{w}x{h}+{x}+{y}")
        root.lift()
        root.focus_force()

        root.mainloop()
    except Exception as e:
        print(f"[Fusion] Dialog display notice ({e}). Console fallback:")
        print(" [1] Attempt Relaunch")
        print(" [2] Export Bug Report (.zip)")
        print(" [3] Abort and open log directory.")
        print(" [4] Abort.")
        inp = input("Select an option (1-4) [4]: ").strip()
        if inp == "1":
            choice["action"] = "relaunch"
        elif inp == "2":
            try:
                zip_p = package_bug_report(root_dir, failed_component, extra_info=failure_info)
                print(f"[Fusion] Bug report generated: {zip_p}")
            except Exception as ex:
                print(f"[Fusion ERROR] Failed: {ex}")
            choice["action"] = "abort"
        elif inp == "3":
            choice["action"] = "open_log"
        else:
            choice["action"] = "abort"

    return choice["action"]


def trigger_failure_log(root_dir, component_id, component_name, source_log_path, extra_text=""):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = os.path.join(root_dir, "fusion", component_id, "log")
    os.makedirs(dest_dir, exist_ok=True)

    dest_file = os.path.join(dest_dir, f"{component_id}_{timestamp}.log")
    latest_file = os.path.join(dest_dir, "latest.log")
    file_alt = os.path.join(root_dir, "fusion", component_id, "log.txt")

    log_content = []
    log_content.append("=" * 70)
    log_content.append(f" TT-RMX FUSION ENGINE FAILURE REPORT - {component_name.upper()}")
    log_content.append(f" Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if extra_text:
        log_content.append(f" Details: {extra_text}")
    log_content.append("=" * 70)
    log_content.append("\n--- LOG OUTPUT ---\n")

    if source_log_path and os.path.exists(source_log_path):
        try:
            with open(source_log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content.append(f.read())
        except Exception as e:
            log_content.append(f"[Could not read source log: {e}]")
    else:
        log_content.append("[No additional source log content available]")

    full_text = "\n".join(log_content)

    try:
        with open(dest_file, "w", encoding="utf-8") as f:
            f.write(full_text)
        with open(latest_file, "w", encoding="utf-8") as f:
            f.write(full_text)
        with open(file_alt, "w", encoding="utf-8") as f:
            f.write(full_text)
    except Exception as e:
        print(f"[Fusion ERROR] Failed writing failure log: {e}")

    rel_path = os.path.relpath(dest_file, root_dir)
    print("\n" + "*" * 70)
    print(" [FUSION WARNING] A FAILURE HAS OCCURRED!")
    print(f" [FUSION WARNING] Component: {component_name}")
    print(" [FUSION WARNING] Failure report saved to:")
    print(f"                  --> {rel_path}")
    print(f"                  --> fusion/{component_id}/log/latest.log")
    if extra_text:
        print(f" [FUSION WARNING] Info: {extra_text}")
    print("*" * 70 + "\n")

    return dest_file


def attempt_recovery_relaunch(root_dir, failed_component, servers_healthy=False):
    win32_dir = os.path.join(root_dir, "win32")
    start_all_bat = os.path.join(win32_dir, "start_all.bat")
    start_game_bat = os.path.join(win32_dir, "start_game.bat")

    recovery_count = int(os.environ.get("FUSION_RECOVERY_ATTEMPT", "0"))
    max_attempts = 2

    print("=" * 70)
    print(" [FUSION AUTO-RECOVERY] Relaunch initiated!")
    print(f" [FUSION AUTO-RECOVERY] Attempt #{recovery_count + 1} of {max_attempts}")

    if recovery_count >= max_attempts:
        print(" [FUSION AUTO-RECOVERY] Maximum recovery attempts reached.")
        print(" [FUSION AUTO-RECOVERY] Auto-relaunch aborted to prevent loop. Please inspect logs.")
        print("=" * 70 + "\n")
        return False

    os.environ["FUSION_RECOVERY_ATTEMPT"] = str(recovery_count + 1)

    if failed_component == "client" and servers_healthy:
        target_bat = start_game_bat
        target_name = "win32\\start_game.bat"
        print(f" [FUSION AUTO-RECOVERY] Background servers are healthy.")
        print(f" [FUSION AUTO-RECOVERY] Relaunching '{target_name}' to regenerate client...")
    else:
        target_bat = start_all_bat
        target_name = "win32\\start_all.bat"
        print(f" [FUSION AUTO-RECOVERY] Server failure detected ({failed_component}).")
        print(f" [FUSION AUTO-RECOVERY] Relaunching full stack via '{target_name}'...")

    print(f" [FUSION AUTO-RECOVERY] Executing {target_name} in 2 seconds...")
    print("=" * 70 + "\n")
    time.sleep(2)

    try:
        subprocess.Popen(
            ["cmd.exe", "/c", "start", "", target_bat],
            cwd=win32_dir,
            shell=True
        )
        print(f"[FUSION AUTO-RECOVERY] Successfully dispatched {target_name}!")
        return True
    except Exception as e:
        print(f"[FUSION AUTO-RECOVERY ERROR] Failed to dispatch {target_name}: {e}")
        return False


def main():
    root_dir = get_root_dir()
    os.chdir(root_dir)

    parser = argparse.ArgumentParser(description="TT-RMX Fusion Engine (64-bit)")
    parser.add_argument("--quick", action="store_true", help="Skip launcher GUI and launch immediately")
    parser.add_argument("--nogui", action="store_true", help="Run headless without graphical launcher")
    parser.add_argument("--token", type=str, default=None, help="Login token to use")
    parser.add_argument("--mode", type=str, choices=["normal", "client_only", "dual_client"], default=None, help="Launch mode")
    parser.add_argument("--clean", action="store_true", help="Purge compiled bytecode and exit")
    parser.add_argument("--backup", nargs="?", const="", default=None, help="Take database backup snapshot and exit")
    parser.add_argument("--export", action="store_true", help="Export bug report archive and exit")

    args, unknown = parser.parse_known_args()

    if args.clean:
        print("[Fusion] Cleaning Python bytecode cache...")
        res = clean_cache(root_dir)
        print(f"[Fusion] [OK] Removed {res.get('files_deleted', 0)} files and {res.get('dirs_deleted', 0)} __pycache__ folders.")
        return

    if args.backup is not None:
        slot = args.backup.strip() or None
        print("[Fusion] Taking database snapshot...")
        binfo = create_backup(root_dir, slot_name=slot, is_auto=False)
        print(f"[Fusion] [OK] Backup saved to slot: {binfo.get('slot_name')}")
        return

    if args.export:
        print("[Fusion] Exporting diagnostic bug report...")
        zpath = package_bug_report(root_dir, component_id="client")
        print(f"[Fusion] [OK] Created: {zpath}")
        return

    launcher_settings = load_launcher_settings(root_dir)
    is_recovery = int(os.environ.get("FUSION_RECOVERY_ATTEMPT", "0")) > 0
    skip_gui = args.quick or args.nogui or is_recovery or launcher_settings.get("skip_launcher", False)

    launch_token = args.token or launcher_settings.get("last_token", "dev")
    launch_mode = args.mode or launcher_settings.get("launch_mode", "normal")
    auto_backup_enabled = launcher_settings.get("auto_backup", True)

    if not skip_gui:
        gui_result = show_launcher_gui(root_dir)
        if gui_result.get("action") != "launch":
            print("[Fusion] Launcher closed. Exiting cleanly.")
            return
        launch_token = gui_result.get("token", launch_token)
        launch_mode = gui_result.get("mode", launch_mode)
        auto_backup_enabled = gui_result.get("auto_backup", auto_backup_enabled)

    print("=" * 65)
    print("       Toontown Remix - Fusion Engine 2.0 (64-bit)")
    print("=" * 65)
    print("[Fusion] Working directory:", root_dir)
    print("[Fusion] Launch mode     :", launch_mode)
    print("[Fusion] Active token    :", launch_token)

    python_exe = sys.executable
    print("[Fusion] Python runtime  :", python_exe)

    if auto_backup_enabled and launch_mode != "client_only":
        try:
            print("[Fusion] Performing pre-launch database backup...")
            b_res = create_backup(root_dir, is_auto=True)
            print(f"[Fusion] [OK] Auto-backup created: {b_res.get('slot_name')}")
        except Exception as e:
            print(f"[Fusion Warning] Auto-backup skipped due to: {e}")

    astron_dir = os.path.join(root_dir, "astron")
    astron_exe = os.path.join(astron_dir, "astrond.exe")
    astron_config = "config/astrond.yml"

    if launch_mode != "client_only" and not os.path.exists(astron_exe):
        print(f"[Fusion ERROR] Astron executable not found at: {astron_exe}")
        print("[Fusion] If Start Fusion fails, please use win32\\start_all.bat")
        input("Press Enter to exit...")
        sys.exit(1)

    os.makedirs(os.path.join(root_dir, "logs"), exist_ok=True)
    astron_log_path = os.path.join(root_dir, "logs", "fusion_astron.log")
    uberdog_log_path = os.path.join(root_dir, "logs", "fusion_uberdog.log")
    ai_log_path = os.path.join(root_dir, "logs", "fusion_ai.log")
    client_log_path = os.path.join(root_dir, "logs", "fusion_client.log")

    astron_log = open(astron_log_path, "w", encoding="utf-8")
    uberdog_log = open(uberdog_log_path, "w", encoding="utf-8")
    ai_log = open(ai_log_path, "w", encoding="utf-8")
    client_log = open(client_log_path, "w", encoding="utf-8")

    subprocesses = []
    subproc_map = {}
    shutting_down = False
    warning_triggered = False
    failed_component = None
    keep_servers_alive = False

    def cleanup():
        nonlocal shutting_down
        if keep_servers_alive:
            print("[Fusion] Keeping healthy servers alive for client regeneration...")
            return
        shutting_down = True
        print("\n[Fusion] Shutting down processes cleanly...")
        for p in reversed(subprocesses):
            try:
                if p.poll() is None:
                    p.terminate()
                    p.wait(timeout=2)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        for log_f in (astron_log, uberdog_log, ai_log, client_log):
            try:
                log_f.close()
            except Exception:
                pass
        print("[Fusion] All processes stopped cleanly. Goodbye!")

    try:
        error_code_file = os.path.join(root_dir, "errorCode")
        try:
            with open(error_code_file, "w") as f:
                f.write("0")
        except Exception:
            pass

        if launch_mode != "client_only":
            print("[Fusion] [1/4] Starting Astron Server...")
            astron_proc = subprocess.Popen(
                [astron_exe, "--loglevel", "info", astron_config],
                cwd=astron_dir,
                stdout=astron_log,
                stderr=subprocess.STDOUT
            )
            subprocesses.append(astron_proc)
            subproc_map["astron"] = astron_proc
            time.sleep(1.5)

            if astron_proc.poll() is not None:
                astron_log.flush()
                warning_triggered = True
                failed_component = "ast"
                trigger_failure_log(
                    root_dir, "ast", "Astron Server",
                    astron_log_path,
                    f"Astron exited unexpectedly on startup with code {astron_proc.returncode}"
                )
                cleanup()
                f_info = analyze_failure(root_dir, "ast", return_code=astron_proc.returncode)
                dest_log_dir = os.path.join(root_dir, "fusion", "ast", "log")
                act = show_warning_dialog(root_dir, dest_log_dir, "ast", failure_info=f_info)
                if act == "relaunch":
                    attempt_recovery_relaunch(root_dir, "ast", servers_healthy=False)
                elif act == "open_log":
                    subprocess.Popen(["explorer.exe", os.path.normpath(dest_log_dir)])
                sys.exit(1)

            print("[Fusion] [2/4] Starting UberDOG Server...")
            uberdog_proc = subprocess.Popen(
                [
                    python_exe, "-m", "toontown.uberdog.UDStart",
                    "--base-channel", "1000000",
                    "--max-channels", "999999",
                    "--stateserver", "4002",
                    "--astron-ip", "127.0.0.1:7199",
                    "--eventlogger-ip", "127.0.0.1:7197"
                ],
                cwd=root_dir,
                stdout=uberdog_log,
                stderr=subprocess.STDOUT
            )
            subprocesses.append(uberdog_proc)
            subproc_map["uberdog"] = uberdog_proc
            time.sleep(1.5)

            if uberdog_proc.poll() is not None:
                uberdog_log.flush()
                warning_triggered = True
                failed_component = "uberdog"
                trigger_failure_log(
                    root_dir, "uberdog", "UberDOG Server",
                    uberdog_log_path,
                    f"UberDOG exited unexpectedly on startup with code {uberdog_proc.returncode}"
                )
                cleanup()
                f_info = analyze_failure(root_dir, "uberdog", return_code=uberdog_proc.returncode)
                dest_log_dir = os.path.join(root_dir, "fusion", "uberdog", "log")
                act = show_warning_dialog(root_dir, dest_log_dir, "uberdog", failure_info=f_info)
                if act == "relaunch":
                    attempt_recovery_relaunch(root_dir, "uberdog", servers_healthy=False)
                elif act == "open_log":
                    subprocess.Popen(["explorer.exe", os.path.normpath(dest_log_dir)])
                sys.exit(1)

            print("[Fusion] [3/4] Starting AI Server (Toon Valley)...")
            ai_env = os.environ.copy()
            ai_env["PYTHONUNBUFFERED"] = "1"
            ai_proc = subprocess.Popen(
                [
                    python_exe, "-m", "toontown.ai.AIStart",
                    "--base-channel", "401000000",
                    "--max-channels", "999999",
                    "--stateserver", "4002",
                    "--astron-ip", "127.0.0.1:7199",
                    "--eventlogger-ip", "127.0.0.1:7197",
                    "--district-name", "Toon Valley"
                ],
                cwd=root_dir,
                env=ai_env,
                stdout=ai_log,
                stderr=subprocess.STDOUT
            )
            subprocesses.append(ai_proc)
            subproc_map["ai"] = ai_proc
            time.sleep(2.5)

            if ai_proc.poll() is not None:
                ai_log.flush()
                warning_triggered = True
                failed_component = "ai"
                trigger_failure_log(
                    root_dir, "ai", "AI Server",
                    ai_log_path,
                    f"AI server exited unexpectedly on startup with code {ai_proc.returncode}"
                )
                cleanup()
                f_info = analyze_failure(root_dir, "ai", return_code=ai_proc.returncode)
                dest_log_dir = os.path.join(root_dir, "fusion", "ai", "log")
                act = show_warning_dialog(root_dir, dest_log_dir, "ai", failure_info=f_info)
                if act == "relaunch":
                    attempt_recovery_relaunch(root_dir, "ai", servers_healthy=False)
                elif act == "open_log":
                    subprocess.Popen(["explorer.exe", os.path.normpath(dest_log_dir)])
                sys.exit(1)
        else:
            print("[Fusion] Client-Only mode: Skipping local server stack.")

        print("[Fusion] [4/4] Launching Game Client...")
        print("=" * 65)
        print(" Game is running! Type 'help' or 'status' in this console.")
        print("=" * 65)

        client_env = os.environ.copy()
        client_env["TTOFF_LOGIN_TOKEN"] = launch_token

        client_proc = subprocess.Popen(
            [python_exe, "-m", "toontown.launcher.TTOffQuickStartLauncher"],
            cwd=root_dir,
            env=client_env,
            stdout=client_log,
            stderr=subprocess.STDOUT
        )
        subprocesses.append(client_proc)
        subproc_map["client"] = client_proc

        secondary_client_proc = None
        if launch_mode == "dual_client":
            print("[Fusion] Launching secondary test client...")
            c2_env = os.environ.copy()
            c2_env["TTOFF_LOGIN_TOKEN"] = launch_token + "_2"
            secondary_client_proc = subprocess.Popen(
                [python_exe, "-m", "toontown.launcher.TTOffQuickStartLauncher"],
                cwd=root_dir,
                env=c2_env
            )
            subprocesses.append(secondary_client_proc)
            subproc_map["client_2"] = secondary_client_proc

        relaunch_requested = False

        def on_relaunch():
            nonlocal relaunch_requested
            relaunch_requested = True
            try:
                client_proc.terminate()
            except Exception:
                pass

        def on_shutdown():
            try:
                client_proc.terminate()
            except Exception:
                pass

        supervisor = LiveSupervisor(
            processes=subproc_map,
            root_dir=root_dir,
            callbacks={"relaunch": on_relaunch, "shutdown": on_shutdown}
        )
        supervisor.start()

        while client_proc.poll() is None and not supervisor.is_shutdown_requested():
            if not shutting_down and launch_mode != "client_only":
                if astron_proc.poll() is not None:
                    astron_log.flush()
                    warning_triggered = True
                    failed_component = "ast"
                    trigger_failure_log(
                        root_dir, "ast", "Astron Server",
                        astron_log_path,
                        f"Astron crashed during runtime with exit code {astron_proc.returncode}"
                    )
                    break

                if ai_proc.poll() is not None:
                    ai_log.flush()
                    warning_triggered = True
                    failed_component = "ai"
                    trigger_failure_log(
                        root_dir, "ai", "AI Server",
                        ai_log_path,
                        f"AI Server crashed during runtime with exit code {ai_proc.returncode}"
                    )
                    break

            time.sleep(0.5)

        supervisor.stop()

        if failed_component in ("ast", "ai"):
            try:
                client_proc.terminate()
            except Exception:
                pass

        client_proc.wait()
        client_log.flush()

        client_code = client_proc.returncode
        error_code_val = "0"
        if os.path.exists(error_code_file):
            try:
                with open(error_code_file, "r") as f:
                    error_code_val = f.read().strip()
            except Exception:
                pass

        print(f"\n[Fusion] Game client closed (exit code: {client_code}, panda error: {error_code_val}).")

        client_failed = (client_code != 0) or (error_code_val not in ("0", ""))
        if client_failed and not shutting_down and not failed_component and not relaunch_requested:
            warning_triggered = True
            failed_component = "client"

            latest_ttoff = None
            try:
                logs_dir = os.path.join(root_dir, "logs")
                ttoff_files = [
                    os.path.join(logs_dir, f) for f in os.listdir(logs_dir)
                    if f.startswith("ttoff-") and f.endswith(".log")
                ]
                if ttoff_files:
                    ttoff_files.sort(key=os.path.getmtime)
                    latest_ttoff = ttoff_files[-1]
            except Exception:
                pass

            combined_log_path = os.path.join(root_dir, "logs", "temp_combined_client.log")
            try:
                with open(combined_log_path, "w", encoding="utf-8") as out_f:
                    if os.path.exists(client_log_path):
                        with open(client_log_path, "r", encoding="utf-8", errors="replace") as f:
                            out_f.write("=== CLIENT STDOUT/STDERR ===\n" + f.read() + "\n\n")
                    if latest_ttoff and os.path.exists(latest_ttoff):
                        with open(latest_ttoff, "r", encoding="utf-8", errors="replace") as f:
                            out_f.write("=== GAME ENGINE LOG ===\n" + f.read() + "\n")
            except Exception:
                combined_log_path = client_log_path

            trigger_failure_log(
                root_dir, "client", "Game Client",
                combined_log_path,
                f"Client process exited with code {client_code} (Panda error: {error_code_val})"
            )

            if launch_mode != "client_only":
                servers_healthy = (
                    astron_proc.poll() is None and
                    uberdog_proc.poll() is None and
                    ai_proc.poll() is None
                )
                if servers_healthy:
                    keep_servers_alive = True

    except KeyboardInterrupt:
        print("\n[Fusion] Interrupted by user.")
    except Exception as e:
        print(f"\n[Fusion ERROR] Unexpected exception: {e}")
        warning_triggered = True
    finally:
        cleanup()
        if warning_triggered and failed_component:
            dest_log_dir = os.path.join(root_dir, "fusion", failed_component, "log")
            failure_info = None
            try:
                failure_info = analyze_failure(root_dir, failed_component, return_code=client_code if failed_component == "client" else 0, panda_error=error_code_val if failed_component == "client" else 0)
            except Exception as e:
                print(f"[Fusion] Note: Diagnostics analysis error: {e}")

            action = show_warning_dialog(root_dir, dest_log_dir, failed_component, failure_info=failure_info)
            if action == "relaunch":
                servers_ok = keep_servers_alive
                attempt_recovery_relaunch(root_dir, failed_component, servers_healthy=servers_ok)
                if not servers_ok:
                    time.sleep(3)
            elif action == "open_log":
                print(f"[Fusion] Opening log directory: {dest_log_dir}")
                try:
                    subprocess.Popen(["explorer.exe", os.path.normpath(dest_log_dir)])
                except Exception as e:
                    print(f"[Fusion ERROR] Could not open Explorer: {e}")
            elif action == "abort":
                print("[Fusion] Session aborted.")
        elif warning_triggered:
            print("\n[Fusion] One or more warnings were logged above.")
            input("Press Enter to close Fusion Engine...")


if __name__ == "__main__":
    main()
