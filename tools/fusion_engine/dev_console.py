"""
Toontown Remix - Fusion Engine Dev Console & Process Supervisor
Background interactive console and process metrics supervisor for TT-RMX.

Features:
- Non-blocking background listener thread for interactive developer commands.
- Native Windows memory & uptime tracking without psutil (using ctypes & Win32 API).
- Monitored components: astron, uberdog, ai, client.
- Commands: help, status, backup, clean, relaunch, export, kill / exit.
- LiveSupervisor class with process management and callback hooks.
"""

import ctypes
import os
import sys
import threading
import time
from ctypes import wintypes
from typing import Any, Callable, Dict, List, Optional, Tuple

from tools.fusion_engine.config import get_root_dir, clean_cache
from tools.fusion_engine.save_manager import create_backup
from tools.fusion_engine.diagnostics import package_bug_report


# -----------------------------------------------------------------------------
# Win32 ctypes Structures & Process Metrics (No external dependencies)
# -----------------------------------------------------------------------------

class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


class FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", wintypes.DWORD),
        ("dwHighDateTime", wintypes.DWORD),
    ]


# Process access flags
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_VM_READ = 0x0010


def _get_process_memory_mb(pid: int) -> Optional[float]:
    """
    Retrieves the process Working Set memory in Megabytes using native Win32 API.
    Returns None if process cannot be queried.
    """
    if os.name != "nt":
        return None

    handle = None
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(
            PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
            False,
            pid
        )
        if not handle:
            # Try limited information fallback
            handle = kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ,
                False,
                pid
            )
        if not handle:
            return None

        # Resolve GetProcessMemoryInfo from psapi or kernel32
        pm_func = None
        if hasattr(ctypes.windll, "psapi") and hasattr(ctypes.windll.psapi, "GetProcessMemoryInfo"):
            pm_func = ctypes.windll.psapi.GetProcessMemoryInfo
        elif hasattr(kernel32, "K32GetProcessMemoryInfo"):
            pm_func = kernel32.K32GetProcessMemoryInfo

        if not pm_func:
            return None

        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        if pm_func(handle, ctypes.byref(counters), counters.cb):
            return counters.WorkingSetSize / (1024.0 * 1024.0)
    except Exception:
        return None
    finally:
        if handle:
            try:
                ctypes.windll.kernel32.CloseHandle(handle)
            except Exception:
                pass

    return None


def _get_process_uptime_seconds(pid: int) -> Optional[float]:
    """
    Retrieves the uptime of a process in seconds using native Win32 GetProcessTimes.
    Returns None if process cannot be queried.
    """
    if os.name != "nt":
        return None

    handle = None
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(
            PROCESS_QUERY_INFORMATION,
            False,
            pid
        )
        if not handle:
            handle = kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION,
                False,
                pid
            )
        if not handle:
            return None

        creation_time = FILETIME()
        exit_time = FILETIME()
        kernel_time = FILETIME()
        user_time = FILETIME()

        if kernel32.GetProcessTimes(
            handle,
            ctypes.byref(creation_time),
            ctypes.byref(exit_time),
            ctypes.byref(kernel_time),
            ctypes.byref(user_time)
        ):
            # FileTime represents 100-nanosecond intervals since January 1, 1601 (UTC).
            c_time = (creation_time.dwHighDateTime << 32) + creation_time.dwLowDateTime
            # Difference between Windows epoch (1601) and Unix epoch (1970) in 100-ns intervals
            epoch_diff = 116444736000000000
            unix_c_time = (c_time - epoch_diff) / 10000000.0
            uptime = time.time() - unix_c_time
            return max(0.0, uptime)
    except Exception:
        return None
    finally:
        if handle:
            try:
                ctypes.windll.kernel32.CloseHandle(handle)
            except Exception:
                pass

    return None


def _format_uptime(seconds: Optional[float]) -> str:
    """Formats uptime seconds into HH:MM:SS format."""
    if seconds is None:
        return "N/A"
    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


# -----------------------------------------------------------------------------
# LiveSupervisor Class
# -----------------------------------------------------------------------------

class LiveSupervisor:
    """
    Background supervisor and console command dispatcher for TT-RMX.
    Monitors process health (PID, uptime, memory) and handles live developer commands.
    """

    def __init__(
        self,
        processes: Optional[Dict[str, Any]] = None,
        root_dir: Optional[str] = None,
        callbacks: Optional[Dict[str, Callable[[], Any]]] = None
    ):
        """
        Initializes the supervisor.

        Args:
            processes: Dict mapping component names to subprocess.Popen objects or dicts with pid/poll.
                       Typical keys: 'astron', 'uberdog', 'ai', 'client'.
            root_dir: Workspace root directory.
            callbacks: Dict mapping command names to callback functions:
                       e.g. {'relaunch': on_relaunch, 'shutdown': on_shutdown}
        """
        self.processes: Dict[str, Any] = dict(processes or {})
        self.root_dir: str = root_dir or get_root_dir()
        self.callbacks: Dict[str, Callable[[], Any]] = dict(callbacks or {})

        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock: threading.Lock = threading.Lock()

        self._shutdown_requested: bool = False
        self._relaunch_requested: bool = False

    def set_process(self, name: str, proc: Any) -> None:
        """Registers or updates a monitored process reference."""
        with self._lock:
            self.processes[name] = proc

    def remove_process(self, name: str) -> None:
        """Removes a process from monitoring."""
        with self._lock:
            self.processes.pop(name, None)

    def get_process(self, name: str) -> Optional[Any]:
        """Gets a monitored process reference."""
        with self._lock:
            return self.processes.get(name)

    def start(self) -> None:
        """Starts the background non-blocking stdin listener thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._listener_loop,
            name="FusionLiveDevConsole",
            daemon=True
        )
        self._thread.start()

        # Banner output
        print("\n" + "=" * 72)
        print(" [Fusion Dev Console] Interactive live supervisor active.")
        print(" Type 'help' for command manual, 'status' for process metrics.")
        print("=" * 72 + "\n", flush=True)

    def stop(self) -> None:
        """Stops the background listener."""
        self._running = False

    def is_running(self) -> bool:
        """Returns True if the console listener is active."""
        return self._running

    def is_shutdown_requested(self) -> bool:
        """Returns True if user initiated shutdown via console."""
        return self._shutdown_requested

    def is_relaunch_requested(self) -> bool:
        """Returns True if user initiated relaunch and resets the flag."""
        with self._lock:
            if self._relaunch_requested:
                self._relaunch_requested = False
                return True
            return False

    def _listener_loop(self) -> None:
        """Background thread reading commands from sys.stdin."""
        while self._running:
            try:
                # Read line from standard input
                line = sys.stdin.readline()
                if not line:
                    # End-of-file encountered (e.g. detached pipe or redirected stream)
                    time.sleep(0.5)
                    continue

                cmd_line = line.strip()
                if not cmd_line:
                    continue

                self.execute_command(cmd_line)
            except Exception as e:
                if self._running:
                    print(f"\n[Fusion Dev Console] Error processing input: {e}", flush=True)
                time.sleep(0.2)

    def execute_command(self, cmd_line: str) -> None:
        """Parses and executes a developer command string."""
        parts = cmd_line.strip().split()
        if not parts:
            return

        command = parts[0].lower()
        args = parts[1:]

        if command in ("help", "?"):
            self._cmd_help()
        elif command == "status":
            self._cmd_status()
        elif command == "backup":
            self._cmd_backup(args)
        elif command == "clean":
            self._cmd_clean()
        elif command == "relaunch":
            self._cmd_relaunch()
        elif command == "export":
            self._cmd_export()
        elif command in ("kill", "exit", "quit", "shutdown"):
            self._cmd_kill()
        else:
            print(f"[Fusion Dev Console] Unknown command: '{command}'. Type 'help' for options.", flush=True)

    # -------------------------------------------------------------------------
    # Command Implementations
    # -------------------------------------------------------------------------

    def _cmd_help(self) -> None:
        """Prints available interactive commands."""
        print("\n" + "=" * 72)
        print(" TT-RMX FUSION ENGINE - LIVE DEV CONSOLE COMMANDS")
        print("=" * 72)
        commands = [
            ("help", "Display this list of interactive commands"),
            ("status", "Show PID, uptime, and memory usage for all running processes"),
            ("backup [name]", "Take an immediate database snapshot (optional custom name)"),
            ("clean", "Purge Python compiled bytecode (*.pyc) and __pycache__ directories"),
            ("relaunch", "Signal client relaunch to reload assets and code"),
            ("export", "Generate comprehensive diagnostic bug report archive (.zip)"),
            ("kill / exit", "Signal clean shutdown of all running servers and client"),
        ]
        for cmd, desc in commands:
            print(f"  {cmd:<16} - {desc}")
        print("=" * 72 + "\n", flush=True)

    def _cmd_status(self) -> None:
        """Inspects all monitored processes and prints PID, uptime, and memory usage."""
        with self._lock:
            process_items = list(self.processes.items())

        print("\n" + "-" * 75)
        print(f" {'Component':<12} {'PID':<8} {'Status':<16} {'Uptime':<12} {'Memory (Working Set)':<20}")
        print("-" * 75)

        if not process_items:
            print("  No processes currently registered for monitoring.")
        else:
            for name, proc in process_items:
                pid_str = "N/A"
                status_str = "UNKNOWN"
                uptime_str = "-"
                memory_str = "-"

                # Extract PID and check if alive
                if hasattr(proc, "pid"):
                    pid = proc.pid
                    pid_str = str(pid)

                    # Check running status
                    poll_res = proc.poll() if hasattr(proc, "poll") else None
                    if poll_res is None:
                        status_str = "RUNNING"
                        # Query metrics
                        mem_mb = _get_process_memory_mb(pid)
                        if mem_mb is not None:
                            memory_str = f"{mem_mb:.1f} MB"
                        else:
                            memory_str = "Active"

                        uptime_s = _get_process_uptime_seconds(pid)
                        uptime_str = _format_uptime(uptime_s)
                    else:
                        status_str = f"STOPPED ({poll_res})"
                elif isinstance(proc, dict):
                    pid = proc.get("pid")
                    pid_str = str(pid) if pid else "N/A"
                    status_str = proc.get("status", "UNKNOWN")
                    if pid and status_str.upper() == "RUNNING":
                        mem_mb = _get_process_memory_mb(pid)
                        if mem_mb is not None:
                            memory_str = f"{mem_mb:.1f} MB"
                        uptime_s = _get_process_uptime_seconds(pid)
                        uptime_str = _format_uptime(uptime_s)

                print(f" {name:<12} {pid_str:<8} {status_str:<16} {uptime_str:<12} {memory_str:<20}")

        print("-" * 75 + "\n", flush=True)

    def _cmd_backup(self, args: List[str]) -> None:
        """Takes an immediate database backup snapshot."""
        slot_name = args[0] if args else None
        print(f"[Fusion Dev Console] Taking database snapshot" + (f" ('{slot_name}')..." if slot_name else "..."), flush=True)

        try:
            # Custom callback if provided
            if "backup" in self.callbacks and callable(self.callbacks["backup"]):
                self.callbacks["backup"]()
            else:
                info = create_backup(root_dir=self.root_dir, slot_name=slot_name, is_auto=False)
                size_kb = info.get("size", 0) / 1024.0
                print(f"[Fusion Dev Console] [OK] Backup created successfully:")
                print(f"                     Slot: {info.get('slot_name')}")
                print(f"                     Size: {size_kb:.1f} KB")
                print(f"                     Path: {info.get('path')}\n", flush=True)
        except Exception as e:
            print(f"[Fusion Dev Console] [ERROR] Backup failed: {e}\n", flush=True)

    def _cmd_clean(self) -> None:
        """Purges compiled bytecode and cache directories."""
        print("[Fusion Dev Console] Purging Python bytecode cache...", flush=True)
        try:
            res = clean_cache(root_dir=self.root_dir)
            files_c = res.get("files_deleted", 0)
            dirs_c = res.get("dirs_deleted", 0)
            err_c = len(res.get("errors", []))
            print(f"[Fusion Dev Console] [OK] Cache cleaned: {files_c} files, {dirs_c} __pycache__ folders removed.", flush=True)
            if err_c > 0:
                print(f"[Fusion Dev Console] Notice: {err_c} error(s) during removal.", flush=True)
            print()
        except Exception as e:
            print(f"[Fusion Dev Console] [ERROR] Cache clean error: {e}\n", flush=True)

    def _cmd_relaunch(self) -> None:
        """Signals client relaunch."""
        print("[Fusion Dev Console] Signalling client relaunch...", flush=True)
        with self._lock:
            self._relaunch_requested = True

        cb = self.callbacks.get("relaunch")
        if cb and callable(cb):
            try:
                cb()
            except Exception as e:
                print(f"[Fusion Dev Console] Error in relaunch callback: {e}\n", flush=True)
        else:
            print("[Fusion Dev Console] Client relaunch request queued.\n", flush=True)

    def _cmd_export(self) -> None:
        """Exports diagnostic bug report zip archive."""
        print("[Fusion Dev Console] Packaging bug report zip...", flush=True)
        try:
            zip_path = package_bug_report(root_dir=self.root_dir, component_id="console")
            print(f"[Fusion Dev Console] [OK] Bug report exported successfully:")
            print(f"                     --> {zip_path}\n", flush=True)
        except Exception as e:
            print(f"[Fusion Dev Console] [ERROR] Bug report export failed: {e}\n", flush=True)

    def _cmd_kill(self) -> None:
        """Signals clean shutdown."""
        print("[Fusion Dev Console] Initiating clean shutdown sequence...", flush=True)
        self._shutdown_requested = True

        cb = (
            self.callbacks.get("shutdown")
            or self.callbacks.get("kill")
            or self.callbacks.get("exit")
        )
        if cb and callable(cb):
            try:
                cb()
            except Exception as e:
                print(f"[Fusion Dev Console] Error in shutdown callback: {e}\n", flush=True)

        self.stop()
        print("[Fusion Dev Console] Supervisor stopped.\n", flush=True)


if __name__ == "__main__":
    # Standalone demo for testing interactive dev console
    print("Starting TT-RMX Dev Console standalone demonstration...")
    supervisor = LiveSupervisor(processes={"self": sys.modules["__main__"]})
    supervisor.start()

    try:
        while supervisor.is_running() and not supervisor.is_shutdown_requested():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nShutdown via KeyboardInterrupt.")
    finally:
        supervisor.stop()
