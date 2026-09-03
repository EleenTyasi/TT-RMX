"""
TT-RMX Fusion Engine - Diagnostics Module
Provides failure analysis, Python traceback parsing, Panda3D exit code mapping,
and comprehensive bug report packaging for Toontown Remix.
"""

import os
import sys
import re
import glob
import json
import shutil
import zipfile
import platform
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# ----------------------------------------------------------------------
# Panda3D / Toontown Error Code Mappings
# ----------------------------------------------------------------------

PANDA_ERROR_CODES = {
    0: {
        "title": "Normal exit",
        "description": "Process terminated cleanly with normal exit status.",
        "fix": "No action needed. The application exited as expected.",
    },
    1: {
        "title": "Generic runtime error",
        "description": "General runtime error occurred during engine execution.",
        "fix": "Check the application logs (fusion_client.log, ttoff-*.log) for recent warning or traceback entries.",
    },
    2: {
        "title": "Download write error",
        "description": "Failed to write downloaded files or multifiles to the local disk.",
        "fix": "Ensure sufficient free disk space, verify folder write permissions, and confirm anti-virus software is not blocking file creation.",
    },
    3: {
        "title": "Proxy authentication failure",
        "description": "HTTP proxy authentication failed (status 407 or SOCKS authentication rejection).",
        "fix": "Verify proxy credentials and network configuration, or disable proxy servers in your operating system settings.",
    },
    4: {
        "title": "Network connection error",
        "description": "Failed to connect to the download server or network timeout occurred (HTTP status < 100).",
        "fix": "Check your internet connection, router, and firewall rules to ensure traffic to the game server is permitted.",
    },
    5: {
        "title": "Resource not found (404)",
        "description": "Requested game resource or multifile was not found on the download server (HTTP 404).",
        "fix": "Verify server update URLs and ensure client and server asset versions are synchronized.",
    },
    6: {
        "title": "Multifile download/decompression failure",
        "description": "Failed to download, patch, or decompress multifile game resources after multiple retry attempts.",
        "fix": "Remove corrupted .mf files in the game folder and retry downloading, or verify internet stability.",
    },
    7: {
        "title": "Failed to open default graphics window",
        "description": "Failed to open default graphics window or initialize graphics pipe / display device.",
        "fix": "Update your graphics card drivers, verify display settings and resolution in settings.json, and ensure your system supports OpenGL or DirectX.",
    },
    8: {
        "title": "Unauthorized program detected",
        "description": "Third-party unauthorized software or process hook was detected by the launcher.",
        "fix": "Close any third-party modification tools, debugging utilities, or memory editors before launching.",
    },
    9: {
        "title": "Gateway / proxy server error",
        "description": "Network gateway error occurred during resource download (HTTP status > 1000).",
        "fix": "Check local network proxy and firewall configuration or bypass gateway filtering.",
    },
    10: {
        "title": "Config/Initialization failure",
        "description": "Game configuration failed to initialize (Configrc did not run or no version set).",
        "fix": "Ensure Config.prc and client configuration files exist, are readable, and contain valid settings.",
    },
    11: {
        "title": "Display initialized",
        "description": "Display graphics window was successfully initialized.",
        "fix": "Display initialized normally. If a subsequent crash occurred, inspect runtime tracebacks in the log.",
    },
    12: {
        "title": "Graphics pipe / display initialization failure or window destroyed",
        "description": "Graphics pipe / display initialization failure or window destroyed, or an unhandled Python exception in main task loop.",
        "fix": "Check graphics drivers and settings.json display options. If an unhandled Python exception occurred, inspect the traceback in the logs.",
    },
    13: {
        "title": "Server connection rejected",
        "description": "Game connection was rejected by the server or login session was refused.",
        "fix": "Verify Astron server (astron/astrond.exe) and state server are running and reachable on 127.0.0.1:7199.",
    },
    14: {
        "title": "Graphics rendering error",
        "description": "Panda3D graphics engine encountered an unrecoverable rendering error frame.",
        "fix": "Update GPU drivers and check resolution or graphics settings in settings.json.",
    },
    15: {
        "title": "File hash mismatch",
        "description": "Client file database hash does not match expected server version.",
        "fix": "Repair or redownload game assets, or rebuild phase files to match expected versions.",
    },
}

EXCEPTION_SUGGESTIONS = {
    "KeyError": "A dictionary key was accessed that does not exist. Ensure the key exists or use dict.get() with a fallback default value.",
    "AttributeError": "An attribute or method was accessed on an object that does not exist. Check if the object is None or not yet initialized.",
    "TypeError": "A function was called with inappropriate argument types or invalid number of arguments. Inspect function signature and passed values.",
    "NameError": "A variable or symbol was referenced that has not been defined or imported in the current scope. Check for typos or missing imports.",
    "ImportError": "A Python module or object could not be imported. Check sys.path and verify the module exists.",
    "ModuleNotFoundError": "The specified Python module was not found. Verify package installation, spelling, and PYTHONPATH.",
    "FileNotFoundError": "A required file could not be found. Ensure asset paths and phase files exist.",
    "IndexError": "A sequence subscript is out of range. Check list or tuple length before indexing.",
    "ValueError": "A function received an argument that has the right type but an inappropriate value.",
    "ZeroDivisionError": "Division or modulo by zero occurred. Add a check to prevent zero divisors.",
    "AssertionError": "An internal code assertion condition failed. Inspect the failing condition logic.",
    "PermissionError": "File system permission denied. Run with appropriate privileges or ensure file is not locked.",
    "ConnectionRefusedError": "Connection to the host/port was actively refused. Verify background servers (Astron, AI, UberDOG) are running.",
    "TimeoutError": "A network or socket operation timed out. Verify network latency and server responsiveness.",
}


def get_panda_error_info(code: Union[int, str]) -> Dict[str, Any]:
    """
    Maps a Panda3D error code (int or str) to a dictionary containing:
    - code (int)
    - title (str)
    - description (str)
    - fix (str)
    """
    try:
        code_int = int(code)
    except (ValueError, TypeError):
        code_int = -1

    if code_int in PANDA_ERROR_CODES:
        entry = PANDA_ERROR_CODES[code_int]
        return {
            "code": code_int,
            "title": entry["title"],
            "description": entry["description"],
            "fix": entry["fix"],
        }
    else:
        return {
            "code": code_int,
            "title": f"Unknown Panda3D error ({code_int})",
            "description": f"Panda3D exited with unmapped error code {code_int}.",
            "fix": "Inspect the application log files for error messages and stack traces.",
        }


# ----------------------------------------------------------------------
# Traceback Parsing & Log Analysis
# ----------------------------------------------------------------------

FRAME_REGEX = re.compile(
    r'^\s*File\s+"(?P<file>[^"]+)",\s+line\s+(?P<line>\d+)(?:,\s+in\s+(?P<func>.+))?',
    re.MULTILINE
)

# Matches Python standard exception header, e.g. "KeyError: 'Bailout'" or "ValueError"
EXC_REGEX = re.compile(
    r'^(?P<type>[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception|Exit|Interrupt|Warning|Fault|LookupError|ArithmeticError|OSError|IOError|EOFError)?)(?::\s*(?P<msg>.*))?$'
)

# Matches Toontown TimeManager one-liner exception logs:
# e.g.: TimeManager: Client exception: toontown.battle.MovieCamera:484, ..., KeyError: 'Bailout'
TIMEMANAGER_EXC_REGEX = re.compile(
    r'TimeManager:\s+Client exception:\s+(?P<content>.+)$',
    re.MULTILINE
)

TASK_ERROR_REGEX = re.compile(
    r':task\(error\):\s+Exception occurred in PythonTask\s+(?P<task>[^\s\n]+)',
    re.IGNORECASE
)

LOADER_ERROR_REGEX = re.compile(
    r':loader\(error\):\s+(?P<msg>.+)',
    re.IGNORECASE
)


def parse_tracebacks(log_text: str) -> List[Dict[str, Any]]:
    """
    Scans log text for Python tracebacks and returns a list of parsed traceback dictionaries.
    Each dictionary contains:
    - exception_type (str)
    - message (str)
    - file (str)
    - line (int)
    - function (str)
    - code (str)
    - frames (list of frame dicts)
    - raw_text (str)
    """
    if not log_text:
        return []

    tracebacks: List[Dict[str, Any]] = []
    lines = log_text.splitlines()
    i = 0
    num_lines = len(lines)

    while i < num_lines:
        line = lines[i]
        if "Traceback (most recent call last):" in line:
            tb_start = i
            raw_lines = [line]
            frames: List[Dict[str, Any]] = []
            i += 1

            while i < num_lines:
                curr_line = lines[i]

                # End of traceback or start of another section
                if (curr_line.startswith("During handling of the above exception") or
                        curr_line.startswith("The above exception was the direct cause") or
                        "Traceback (most recent call last):" in curr_line):
                    # Handled on next iteration
                    break

                # Frame line: File "...", line 123, in func
                frame_match = FRAME_REGEX.match(curr_line)
                if frame_match:
                    raw_lines.append(curr_line)
                    file_path = frame_match.group("file")
                    line_no = int(frame_match.group("line"))
                    func_name = frame_match.group("func") or "<unknown>"
                    code_line = ""

                    # Peek next line for code snippet
                    if i + 1 < num_lines:
                        next_line = lines[i + 1]
                        if (next_line.startswith("    ") or next_line.startswith("\t")) and not FRAME_REGEX.match(next_line):
                            code_line = next_line.strip()
                            raw_lines.append(next_line)
                            i += 1

                    frames.append({
                        "file": file_path,
                        "line": line_no,
                        "function": func_name,
                        "code": code_line,
                    })
                    i += 1
                    continue

                # Check if this line is the exception line
                stripped = curr_line.strip()
                exc_match = EXC_REGEX.match(stripped)
                if exc_match and frames:
                    raw_lines.append(curr_line)
                    exc_type = exc_match.group("type")
                    exc_msg = (exc_match.group("msg") or "").strip()

                    # Check for multi-line exception messages
                    i += 1
                    while i < num_lines:
                        peek = lines[i]
                        # If indented or continuation without new log tag
                        if (peek.startswith("  ") or peek.startswith("\t")) and not FRAME_REGEX.match(peek):
                            exc_msg += " " + peek.strip()
                            raw_lines.append(peek)
                            i += 1
                        else:
                            break

                    last_frame = frames[-1] if frames else {
                        "file": "<unknown>",
                        "line": 0,
                        "function": "<unknown>",
                        "code": "",
                    }

                    tracebacks.append({
                        "exception_type": exc_type,
                        "message": exc_msg,
                        "file": last_frame["file"],
                        "line": last_frame["line"],
                        "function": last_frame["function"],
                        "code": last_frame.get("code", ""),
                        "frames": frames,
                        "raw_text": "\n".join(raw_lines),
                    })
                    break
                else:
                    # Non-frame, non-exception line inside traceback block
                    if curr_line.strip() == "" and frames:
                        # Blank line after frames might mean exception on next line
                        raw_lines.append(curr_line)
                        i += 1
                        continue
                    elif not frames:
                        # Before first frame
                        raw_lines.append(curr_line)
                        i += 1
                        continue
                    else:
                        break
        else:
            i += 1

    # Fallback: Check for TimeManager one-liner exception logs if no full traceback was found
    if not tracebacks:
        for match in TIMEMANAGER_EXC_REGEX.finditer(log_text):
            content = match.group("content").strip()
            parts = [p.strip() for p in content.split(",")]
            exc_part = parts[-1] if parts else ""
            exc_type = "Exception"
            exc_msg = ""
            exc_m = EXC_REGEX.match(exc_part)
            if exc_m:
                exc_type = exc_m.group("type")
                exc_msg = exc_m.group("msg") or ""

            frames = []
            for p in parts[:-1]:
                if ":" in p:
                    f_parts = p.split(":")
                    f_file = f_parts[0].strip()
                    try:
                        f_line = int(f_parts[1].strip())
                    except ValueError:
                        f_line = 0
                    frames.append({
                        "file": f_file,
                        "line": f_line,
                        "function": "<unknown>",
                        "code": "",
                    })

            last_frame = frames[0] if frames else {
                "file": "<unknown>",
                "line": 0,
                "function": "<unknown>",
                "code": "",
            }

            tracebacks.append({
                "exception_type": exc_type,
                "message": exc_msg,
                "file": last_frame["file"],
                "line": last_frame["line"],
                "function": last_frame["function"],
                "code": "",
                "frames": frames,
                "raw_text": match.group(0),
            })

    return tracebacks


def find_latest_ttoff_log(root_dir: str) -> Optional[str]:
    """Finds the most recently modified ttoff-*.log in root_dir/logs/."""
    logs_dir = os.path.join(root_dir, "logs")
    if not os.path.exists(logs_dir):
        return None

    ttoff_files = [
        os.path.join(logs_dir, f)
        for f in os.listdir(logs_dir)
        if f.startswith("ttoff-") and f.endswith(".log")
    ]
    if not ttoff_files:
        return None

    ttoff_files.sort(key=os.path.getmtime)
    return ttoff_files[-1]


def read_file_safe(file_path: str, max_bytes: int = 1024 * 1024) -> str:
    """Reads file text safely up to max_bytes, handling encoding and errors gracefully."""
    if not file_path or not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(max_bytes)
    except Exception:
        try:
            with open(file_path, "r", encoding="latin-1", errors="replace") as f:
                return f.read(max_bytes)
        except Exception:
            return ""


def get_relevant_log_sources(root_dir: str, component_id: str) -> List[str]:
    """
    Returns an ordered list of relevant log file paths for a given component_id.
    """
    root_dir = os.path.abspath(root_dir)
    logs_dir = os.path.join(root_dir, "logs")
    component_lower = (component_id or "").lower()
    sources: List[str] = []

    # 1. Component failure log in fusion/<component_id>/log/latest.log
    if component_id:
        fusion_latest = os.path.join(root_dir, "fusion", component_id, "log", "latest.log")
        if os.path.exists(fusion_latest):
            sources.append(fusion_latest)

    # 2. Main component log in logs/
    if component_lower in ("client", "game", "ttr"):
        combined_client = os.path.join(logs_dir, "temp_combined_client.log")
        if os.path.exists(combined_client):
            sources.append(combined_client)
        fusion_client = os.path.join(logs_dir, "fusion_client.log")
        if os.path.exists(fusion_client):
            sources.append(fusion_client)
        latest_ttoff = find_latest_ttoff_log(root_dir)
        if latest_ttoff and latest_ttoff not in sources:
            sources.append(latest_ttoff)
    elif component_lower in ("ai", "district"):
        fusion_ai = os.path.join(logs_dir, "fusion_ai.log")
        if os.path.exists(fusion_ai):
            sources.append(fusion_ai)
    elif component_lower in ("ast", "astron"):
        fusion_astron = os.path.join(logs_dir, "fusion_astron.log")
        if os.path.exists(fusion_astron):
            sources.append(fusion_astron)
    elif component_lower in ("uberdog", "ud"):
        fusion_uberdog = os.path.join(logs_dir, "fusion_uberdog.log")
        if os.path.exists(fusion_uberdog):
            sources.append(fusion_uberdog)
    else:
        # Generic component fallback
        custom_log = os.path.join(logs_dir, f"fusion_{component_id}.log")
        if os.path.exists(custom_log):
            sources.append(custom_log)

    return sources


def analyze_failure(
    root_dir: str,
    component_id: str,
    return_code: Union[int, str] = 0,
    panda_error: Union[int, str] = 0,
    log_content: str = ""
) -> Dict[str, Any]:
    """
    Analyzes a component failure and returns a diagnostic dictionary containing:
    - summary (str)
    - root_cause (str)
    - details (dict)
    - suggestions (list of str)

    Parameters:
    - root_dir: Workspace root directory
    - component_id: Component identifier ('client', 'ai', 'ast', 'uberdog', etc.)
    - return_code: Process exit return code
    - panda_error: Panda3D exit error code (e.g. 12, 7, 0, 11)
    - log_content: Optional raw log content. If omitted or empty, reads from relevant log files.
    """
    root_dir = os.path.abspath(root_dir)

    try:
        ret_code_int = int(return_code)
    except (ValueError, TypeError):
        ret_code_int = 0

    try:
        panda_error_int = int(panda_error)
    except (ValueError, TypeError):
        panda_error_int = 0

    # If panda_error is 0, attempt to read from errorCode file in root_dir
    if panda_error_int == 0:
        error_code_file = os.path.join(root_dir, "errorCode")
        if os.path.exists(error_code_file):
            try:
                with open(error_code_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        panda_error_int = int(content)
            except Exception:
                pass

    # Gather log content if not provided
    log_sources_used: List[str] = []
    combined_log_text = log_content or ""

    if not combined_log_text.strip():
        sources = get_relevant_log_sources(root_dir, component_id)
        accumulated: List[str] = []
        for src in sources:
            text = read_file_safe(src)
            if text:
                accumulated.append(f"=== SOURCE: {os.path.basename(src)} ===\n" + text)
                log_sources_used.append(src)
        combined_log_text = "\n\n".join(accumulated)

    # Check if panda error was logged in text (e.g. "setting panda error code to 12")
    if panda_error_int == 0 and combined_log_text:
        m = re.search(r'setting panda error code to\s+(\d+)', combined_log_text)
        if m:
            try:
                panda_error_int = int(m.group(1))
            except ValueError:
                pass

    # Parse tracebacks
    tracebacks = parse_tracebacks(combined_log_text)

    # Detect additional log errors
    detected_task_errors = TASK_ERROR_REGEX.findall(combined_log_text)
    detected_loader_errors = LOADER_ERROR_REGEX.findall(combined_log_text)

    # Panda error info
    panda_info = get_panda_error_info(panda_error_int)

    # Identify primary traceback
    primary_tb = tracebacks[-1] if tracebacks else None

    # Determine root cause and summary
    comp_name = (component_id or "Component").capitalize()
    if component_id == "ast":
        comp_name = "Astron Server"
    elif component_id == "ai":
        comp_name = "AI Server"
    elif component_id == "uberdog":
        comp_name = "UberDOG Server"
    elif component_id == "client":
        comp_name = "Game Client"

    root_cause = ""
    suggestions: List[str] = []

    if primary_tb:
        exc_type = primary_tb["exception_type"]
        exc_msg = primary_tb["message"]
        file_name = os.path.basename(primary_tb["file"])
        line_no = primary_tb["line"]
        func_name = primary_tb["function"]

        root_cause = f"{exc_type}: {exc_msg} at {file_name}:{line_no} in {func_name}" if exc_msg else f"{exc_type} at {file_name}:{line_no} in {func_name}"
        summary = f"{comp_name} crashed due to unhandled {exc_type}"
        if exc_msg:
            summary += f" ({exc_msg})"
        summary += f" at {file_name}:{line_no}"

        # Suggestions based on exception type
        if exc_type in EXCEPTION_SUGGESTIONS:
            suggestions.append(EXCEPTION_SUGGESTIONS[exc_type])
        else:
            suggestions.append(f"Inspect exception {exc_type} at {primary_tb['file']} line {line_no}.")

        # Specific suggestion for KeyError
        if exc_type == "KeyError":
            suggestions.append(f"Check definition of key {exc_msg} in {file_name} and verify dictionary lookup logic.")
    elif panda_error_int not in (0, 11) and panda_error_int in PANDA_ERROR_CODES:
        root_cause = f"Panda3D error code {panda_error_int}: {panda_info['title']}"
        summary = f"{comp_name} terminated with Panda3D error {panda_error_int}: {panda_info['title']}"
        suggestions.append(panda_info["fix"])
    elif ret_code_int != 0:
        root_cause = f"Process exited unexpectedly with non-zero exit code {ret_code_int}"
        summary = f"{comp_name} failed with process exit code {ret_code_int}"
        suggestions.append("Check process startup arguments and verify background server availability.")
    else:
        root_cause = "Normal termination (no errors detected)"
        summary = f"{comp_name} exited normally with code 0."
        suggestions.append("No action needed.")

    # Additional suggestions from Panda3D error if available
    if panda_error_int != 0 and panda_info["fix"] not in suggestions:
        suggestions.append(f"Panda3D Error {panda_error_int} ({panda_info['title']}): {panda_info['fix']}")

    # Suggestions for loader errors
    if detected_loader_errors:
        suggestions.append(f"Asset loading errors detected ({len(detected_loader_errors)} file(s)). Verify model paths and mounted phase files.")

    # Suggest bug report creation
    suggestions.append(f"Generate a diagnostic bug report using package_bug_report(root_dir, '{component_id}').")

    details = {
        "component_id": component_id,
        "return_code": ret_code_int,
        "panda_error": panda_error_int,
        "panda_error_info": panda_info,
        "has_traceback": bool(primary_tb),
        "exception_type": primary_tb["exception_type"] if primary_tb else None,
        "exception_message": primary_tb["message"] if primary_tb else None,
        "file": primary_tb["file"] if primary_tb else None,
        "line": primary_tb["line"] if primary_tb else None,
        "function": primary_tb["function"] if primary_tb else None,
        "code": primary_tb.get("code") if primary_tb else None,
        "tracebacks": tracebacks,
        "relevant_logs": log_sources_used,
        "task_errors": detected_task_errors,
        "loader_errors": detected_loader_errors[:5],
    }

    return {
        "summary": summary,
        "root_cause": root_cause,
        "details": details,
        "suggestions": suggestions,
    }


# ----------------------------------------------------------------------
# Bug Report Packager
# ----------------------------------------------------------------------

def get_git_info(root_dir: str) -> Dict[str, str]:
    """Retrieves current git commit, branch, and status if git is available."""
    info = {
        "commit": "N/A",
        "branch": "N/A",
        "status": "N/A",
        "available": "false",
    }
    try:
        commit_res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if commit_res.returncode == 0:
            info["commit"] = commit_res.stdout.strip()
            info["available"] = "true"

        branch_res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if branch_res.returncode == 0:
            info["branch"] = branch_res.stdout.strip()

        status_res = subprocess.run(
            ["git", "status", "--short"],
            cwd=root_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if status_res.returncode == 0:
            info["status"] = status_res.stdout.strip() or "Clean (no uncommitted changes)"
    except Exception as e:
        info["commit"] = f"Git unavailable ({e})"

    return info


def build_environment_info(
    root_dir: str,
    component_id: Optional[str] = None,
    extra_info: Optional[Union[Dict[str, Any], str]] = None
) -> str:
    """
    Builds the environment_info.txt content including:
    - Timestamp
    - Component ID
    - Python Version & Executable
    - OS and Platform details
    - Git commit, branch, and status
    - Extra diagnostic information
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    git_info = get_git_info(root_dir)

    lines = [
        "=" * 70,
        " TT-RMX FUSION ENGINE ENVIRONMENT & DIAGNOSTIC REPORT",
        "=" * 70,
        f"Generated Timestamp:  {now_str}",
        f"Target Component:     {component_id or 'N/A'}",
        f"Workspace Root:       {root_dir}",
        "",
        "--- PYTHON ENVIRONMENT ---",
        f"Python Version:       {platform.python_version()}",
        f"Python Build:         {platform.python_build()}",
        f"Python Compiler:      {platform.python_compiler()}",
        f"Python Executable:    {sys.executable}",
        "",
        "--- SYSTEM & OS INFORMATION ---",
        f"Operating System:     {platform.system()} {platform.release()} ({platform.version()})",
        f"Platform:             {platform.platform()}",
        f"Architecture:         {platform.machine()} ({', '.join(platform.architecture())})",
        f"Processor:            {platform.processor()}",
        "",
        "--- GIT REPOSITORY STATUS ---",
        f"Git Available:        {git_info['available']}",
        f"Current Commit:       {git_info['commit']}",
        f"Current Branch:       {git_info['branch']}",
        f"Working Tree Status:\n{git_info['status']}",
        "",
    ]

    # Include extra_info if provided
    if extra_info:
        lines.append("--- ADDITIONAL DIAGNOSTIC INFO ---")
        if isinstance(extra_info, dict):
            try:
                lines.append(json.dumps(extra_info, indent=2, default=str))
            except Exception:
                for k, v in extra_info.items():
                    lines.append(f"{k}: {v}")
        else:
            lines.append(str(extra_info))
        lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


def package_bug_report(
    root_dir: str,
    component_id: str,
    extra_info: Optional[Union[Dict[str, Any], str]] = None
) -> str:
    """
    Collects diagnostics and packages a comprehensive bug report into a .zip file.
    Collected files:
    - All logs/fusion_*.log
    - Latest logs/ttoff-*.log
    - fusion/<component_id>/log/latest.log
    - settings.json
    - environment_info.txt (containing Python version, OS info, timestamp, git info, and failure analysis)

    Saves to logs/bugreport_<timestamp>.zip and returns its absolute path.
    """
    root_dir = os.path.abspath(root_dir)
    logs_dir = os.path.join(root_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"bugreport_{timestamp}.zip"
    zip_path = os.path.join(logs_dir, zip_filename)

    # If extra_info was not provided, automatically perform failure analysis
    if extra_info is None:
        try:
            extra_info = analyze_failure(root_dir, component_id)
        except Exception as e:
            extra_info = f"Automatic failure analysis failed: {e}"

    env_info_text = build_environment_info(root_dir, component_id, extra_info)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Add environment_info.txt
        zf.writestr("environment_info.txt", env_info_text)

        # 2. Add diagnostic_analysis.json if available
        if isinstance(extra_info, dict):
            try:
                zf.writestr("diagnostic_analysis.json", json.dumps(extra_info, indent=2, default=str))
            except Exception:
                pass

        # 3. Add settings.json if present
        settings_file = os.path.join(root_dir, "settings.json")
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "rb") as f:
                    zf.writestr("settings.json", f.read())
            except Exception as e:
                zf.writestr("settings.json.error.txt", f"Failed to read settings.json: {e}")

        # 4. Add all logs/fusion_*.log
        fusion_logs = glob.glob(os.path.join(logs_dir, "fusion_*.log"))
        for log_file in fusion_logs:
            arc_name = f"logs/{os.path.basename(log_file)}"
            try:
                with open(log_file, "rb") as f:
                    zf.writestr(arc_name, f.read())
            except Exception as e:
                zf.writestr(f"{arc_name}.error.txt", f"Failed reading log: {e}")

        # 5. Add latest logs/ttoff-*.log
        latest_ttoff = find_latest_ttoff_log(root_dir)
        if latest_ttoff and os.path.exists(latest_ttoff):
            arc_name = f"logs/{os.path.basename(latest_ttoff)}"
            try:
                with open(latest_ttoff, "rb") as f:
                    zf.writestr(arc_name, f.read())
            except Exception as e:
                zf.writestr(f"{arc_name}.error.txt", f"Failed reading latest ttoff log: {e}")

        # 6. Add fusion/<component_id>/log/latest.log
        if component_id:
            fusion_latest = os.path.join(root_dir, "fusion", component_id, "log", "latest.log")
            if os.path.exists(fusion_latest):
                arc_name = f"fusion/{component_id}/log/latest.log"
                try:
                    with open(fusion_latest, "rb") as f:
                        zf.writestr(arc_name, f.read())
                except Exception as e:
                    zf.writestr(f"{arc_name}.error.txt", f"Failed reading component latest log: {e}")

            # Also check fusion/<component_id>/log.txt if present
            alt_log = os.path.join(root_dir, "fusion", component_id, "log.txt")
            if os.path.exists(alt_log):
                arc_name = f"fusion/{component_id}/log.txt"
                try:
                    with open(alt_log, "rb") as f:
                        zf.writestr(arc_name, f.read())
                except Exception as e:
                    pass

    return os.path.abspath(zip_path)


# ----------------------------------------------------------------------
# Self-Test & Diagnostic CLI
# ----------------------------------------------------------------------

def run_self_test(root_dir: Optional[str] = None) -> bool:
    """Runs a self-test suite validating traceback parsing, error code mapping, and bug packaging."""
    if not root_dir:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    print("=" * 60)
    print(" Running TT-RMX Diagnostics Module Self-Tests")
    print("=" * 60)

    # Test 1: Panda3D Error Code Mapping
    print("[1/4] Testing Panda3D Error Code Mapping...")
    err0 = get_panda_error_info(0)
    assert err0["title"] == "Normal exit", f"Unexpected code 0: {err0}"

    err7 = get_panda_error_info(7)
    assert "default graphics window" in err7["title"].lower(), f"Unexpected code 7: {err7}"

    err11 = get_panda_error_info(11)
    assert "display initialized" in err11["title"].lower(), f"Unexpected code 11: {err11}"

    err12 = get_panda_error_info(12)
    assert "graphics pipe" in err12["title"].lower(), f"Unexpected code 12: {err12}"
    print("   -> Panda3D error codes mapped successfully.")

    # Test 2: Traceback Parsing
    print("[2/4] Testing Python Traceback Parsing...")
    sample_log = """
:09-03-2026 02:20:42 :task(error): Exception occurred in PythonTask readerPollTask-2519163509248
Traceback (most recent call last):
  File "C:\\Users\\Mario\\OneDrive\\Documents\\TT-RMX\\otp\\launcher\\LauncherBase.py", line 1081, in mainLoop
    self._runTaskManager()
  File "C:\\Users\\Mario\\OneDrive\\Documents\\TT-RMX\\toontown\\battle\\MovieCamera.py", line 484, in chooseSuitShot
    displayName = TTLocalizer.SuitAttackNames[attack['name']]
KeyError: 'Bailout'
"""
    tbs = parse_tracebacks(sample_log)
    assert len(tbs) == 1, f"Expected 1 traceback, found {len(tbs)}"
    tb = tbs[0]
    assert tb["exception_type"] == "KeyError", f"Expected KeyError, got {tb['exception_type']}"
    assert tb["message"] == "'Bailout'", f"Expected 'Bailout', got {tb['message']}"
    assert "MovieCamera.py" in tb["file"], f"Expected MovieCamera.py, got {tb['file']}"
    assert tb["line"] == 484, f"Expected line 484, got {tb['line']}"
    assert tb["function"] == "chooseSuitShot", f"Expected chooseSuitShot, got {tb['function']}"
    print("   -> Traceback parsing verified successfully.")

    # Test 3: Failure Analysis
    print("[3/4] Testing analyze_failure()...")
    res = analyze_failure(
        root_dir=root_dir,
        component_id="client",
        return_code=1,
        panda_error=12,
        log_content=sample_log
    )
    assert "KeyError" in res["summary"], f"Summary missing KeyError: {res['summary']}"
    assert "KeyError" in res["root_cause"], f"Root cause missing KeyError: {res['root_cause']}"
    assert len(res["suggestions"]) > 0, "Suggestions list is empty"
    assert res["details"]["line"] == 484, f"Details missing line: {res['details']}"
    print(f"   -> Summary: {res['summary']}")
    print(f"   -> Root Cause: {res['root_cause']}")

    # Test 4: Bug Report Packaging
    print("[4/4] Testing package_bug_report()...")
    zip_path = package_bug_report(root_dir, "client", extra_info=res)
    assert os.path.exists(zip_path), f"Bug report zip not found at {zip_path}"
    assert zipfile.is_zipfile(zip_path), f"Generated file is not a valid zip: {zip_path}"

    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        print(f"   -> Zip created with {len(namelist)} entries:")
        for name in namelist:
            print(f"      - {name}")
        assert "environment_info.txt" in namelist, "environment_info.txt missing from zip"

    print("=" * 60)
    print(" All Diagnostics Self-Tests Passed Cleanly!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TT-RMX Fusion Engine Diagnostics")
    parser.add_argument("--test", action="store_true", help="Run self-test suite")
    parser.add_argument("--analyze", action="store_true", help="Analyze failure for component")
    parser.add_argument("--package", action="store_true", help="Package bug report for component")
    parser.add_argument("--component", default="client", help="Component ID (client, ai, ast, uberdog)")
    parser.add_argument("--root", default="", help="Project root directory")
    parser.add_argument("--retcode", type=int, default=0, help="Return code")
    parser.add_argument("--panda-error", type=int, default=0, help="Panda3D error code")

    args = parser.parse_args()
    target_root = args.root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    if args.test:
        success = run_self_test(target_root)
        sys.exit(0 if success else 1)
    elif args.analyze:
        analysis = analyze_failure(target_root, args.component, args.retcode, args.panda_error)
        print(json.dumps(analysis, indent=2, default=str))
    elif args.package:
        zip_path = package_bug_report(target_root, args.component)
        print(f"Bug report packaged successfully: {zip_path}")
    else:
        # Default action when run directly: run self-test
        run_self_test(target_root)
