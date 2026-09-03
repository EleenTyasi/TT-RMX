import os
import sys
import time
import signal
import subprocess

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)

    print("=" * 60)
    print("       Toontown Remix - Start Fusion (64-bit Engine)")
    print("=" * 60)
    print("[Fusion] Working directory:", root_dir)

    # Determine Python executable
    python_exe = sys.executable
    print("[Fusion] Using Python runtime:", python_exe)

    # Astron paths
    astron_dir = os.path.join(root_dir, "astron")
    astron_exe = os.path.join(astron_dir, "astrond.exe")
    astron_config = "config/astrond.yml"

    if not os.path.exists(astron_exe):
        print(f"[Fusion ERROR] Astron executable not found at: {astron_exe}")
        print("[Fusion] If Start Fusion fails, please use win32\\start_all.bat")
        input("Press Enter to exit...")
        sys.exit(1)

    os.makedirs(os.path.join(root_dir, "logs"), exist_ok=True)
    astron_log = open(os.path.join(root_dir, "logs", "fusion_astron.log"), "w", encoding="utf-8")
    uberdog_log = open(os.path.join(root_dir, "logs", "fusion_uberdog.log"), "w", encoding="utf-8")
    ai_log = open(os.path.join(root_dir, "logs", "fusion_ai.log"), "w", encoding="utf-8")

    subprocesses = []

    def cleanup():
        print("\n[Fusion] Shutting down background servers...")
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
        for log_f in (astron_log, uberdog_log, ai_log):
            try:
                log_f.close()
            except Exception:
                pass
        print("[Fusion] All servers stopped cleanly. Goodbye!")

    try:
        # 1. Start Astron
        print("[Fusion] [1/4] Starting Astron Server...")
        astron_proc = subprocess.Popen(
            [astron_exe, "--loglevel", "info", astron_config],
            cwd=astron_dir,
            stdout=astron_log,
            stderr=subprocess.STDOUT
        )
        subprocesses.append(astron_proc)
        time.sleep(1.5)

        if astron_proc.poll() is not None:
            print("[Fusion ERROR] Astron failed to start. Check logs/fusion_astron.log")
            print("[Fusion] If Start Fusion fails, please use win32\\start_all.bat")
            cleanup()
            input("Press Enter to exit...")
            sys.exit(1)

        # 2. Start UberDOG
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
        time.sleep(1.5)

        if uberdog_proc.poll() is not None:
            print("[Fusion ERROR] UberDOG failed to start. Check logs/fusion_uberdog.log")
            print("[Fusion] If Start Fusion fails, please use win32\\start_all.bat")
            cleanup()
            input("Press Enter to exit...")
            sys.exit(1)

        # 3. Start AI
        print("[Fusion] [3/4] Starting AI Server (Toon Valley)...")
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
            stdout=ai_log,
            stderr=subprocess.STDOUT
        )
        subprocesses.append(ai_proc)
        time.sleep(2.5)

        if ai_proc.poll() is not None:
            print("[Fusion ERROR] AI Server failed to start. Check logs/fusion_ai.log")
            print("[Fusion] If Start Fusion fails, please use win32\\start_all.bat")
            cleanup()
            input("Press Enter to exit...")
            sys.exit(1)

        # 4. Start Game Client
        print("[Fusion] [4/4] Launching Game Client...")
        print("=" * 60)
        print(" Game is running! Keep this window open while playing.")
        print(" (Closing the game will automatically stop the servers)")
        print(" If Start Fusion fails, use 'win32\\start_all.bat'")
        print("=" * 60)

        client_env = os.environ.copy()
        client_env["TTOFF_LOGIN_TOKEN"] = "dev"

        client_proc = subprocess.Popen(
            [python_exe, "-m", "toontown.launcher.TTOffQuickStartLauncher"],
            cwd=root_dir,
            env=client_env
        )

        # Wait for the client to exit
        client_proc.wait()
        print(f"\n[Fusion] Game client closed (exit code: {client_proc.returncode}).")

    except KeyboardInterrupt:
        print("\n[Fusion] User interrupted.")
    except Exception as e:
        print(f"\n[Fusion ERROR] Unexpected error: {e}")
        print("[Fusion] If Start Fusion fails, please use win32\\start_all.bat")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
