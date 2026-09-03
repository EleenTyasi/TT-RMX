"""
Configuration and Cache Management for Toontown Remix Fusion Engine.

Provides safe reading/writing of game settings (settings.json) and launcher
settings (fusion/launcher_settings.json), path resolution, and Python 3 cache cleaning.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

DEFAULT_GAME_SETTINGS: Dict[str, Any] = {
    "game": {
        "antialiasing": 0,
        "stretched-screen": False,
        "magic-word-activator": 0,
        "music": False,
        "ffxiv-camera": True,
        "camera-sensitivity": 1.4,
    },
    "controls": {
        "forward": "w",
        "reverse": "s",
        "turnLeft": "a",
        "turnRight": "d",
        "jump": "space",
    },
}

DEFAULT_LAUNCHER_SETTINGS: Dict[str, Any] = {
    "last_token": "dev",
    "recent_tokens": ["dev"],
    "auto_backup": True,
    "launch_mode": "normal",
    "skip_launcher": False,
}


def get_root_dir(start_path: Optional[Union[str, Path]] = None) -> str:
    """
    Returns the absolute path to the TT-RMX project root directory.
    Walks up from start_path (or __file__) to locate project root markers.
    """
    if start_path is None:
        current = Path(__file__).resolve().parent
    else:
        current = Path(start_path).resolve()

    # If start_path was a file, start from its parent directory
    if current.is_file():
        current = current.parent

    for candidate in [current] + list(current.parents):
        # Recognizable project root markers
        if (candidate / "astron").is_dir() and (candidate / "toontown").is_dir():
            return str(candidate)
        if (candidate / "settings.json").is_file() and (candidate / "win32").is_dir():
            return str(candidate)

    # Fallback: tools/fusion_engine is 2 levels below root
    fallback = Path(__file__).resolve().parent.parent.parent
    return str(fallback)


def _safe_write_json(file_path: Union[str, Path], data: Any, indent: int = 4) -> None:
    """
    Safely writes JSON data to file_path using an atomic temp-file replace.
    Ensures that interrupted writes never corrupt settings files.
    """
    target = Path(file_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    # Use a temp file in the same directory for atomic os.replace across filesystems
    temp_file = target.with_suffix(f"{target.suffix}.tmp_{os.getpid()}_{id(data)}")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, target)
    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass


# -----------------------------------------------------------------------------
# settings.json (Game Settings)
# -----------------------------------------------------------------------------

def get_game_settings_path(root_dir: Optional[str] = None) -> str:
    """Returns the absolute path to settings.json."""
    root = root_dir or get_root_dir()
    return os.path.join(root, "settings.json")


def load_game_settings(root_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Safely loads settings.json. If missing or invalid, falls back to default settings.
    Guarantees 'game' and 'controls' sub-dictionaries exist.
    """
    path = get_game_settings_path(root_dir)
    settings: Dict[str, Any] = {
        "game": dict(DEFAULT_GAME_SETTINGS["game"]),
        "controls": dict(DEFAULT_GAME_SETTINGS["controls"]),
    }

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                if "game" in loaded and isinstance(loaded["game"], dict):
                    settings["game"].update(loaded["game"])
                if "controls" in loaded and isinstance(loaded["controls"], dict):
                    settings["controls"].update(loaded["controls"])
                # Also capture any other top-level keys if present
                for k, v in loaded.items():
                    if k not in ("game", "controls"):
                        settings[k] = v
        except Exception as e:
            print(f"[Fusion Config] Warning: Failed to read {path} ({e}), using defaults.")

    return settings


def save_game_settings(settings: Dict[str, Any], root_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Safely saves game settings to settings.json atomically.
    """
    path = get_game_settings_path(root_dir)
    _safe_write_json(path, settings)
    return settings


def get_game_setting(key: str, default: Any = None, root_dir: Optional[str] = None) -> Any:
    """
    Fetches a setting value from settings.json.
    Searches 'game' section, 'controls' section, and top-level keys.
    """
    settings = load_game_settings(root_dir)
    if key in settings.get("game", {}):
        return settings["game"][key]
    if key in settings.get("controls", {}):
        return settings["controls"][key]
    if key in settings:
        return settings[key]
    return default


def set_game_setting(key: str, value: Any, root_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Updates a single game setting and saves settings.json safely.
    Properly places setting in 'game' or 'controls' section.
    """
    settings = load_game_settings(root_dir)

    game_keys = {
        "antialiasing",
        "stretched-screen",
        "magic-word-activator",
        "music",
        "ffxiv-camera",
        "camera-sensitivity",
    }
    control_keys = {"forward", "reverse", "turnLeft", "turnRight", "jump"}

    if key == "controls" and isinstance(value, dict):
        settings.setdefault("controls", {}).update(value)
    elif key == "game" and isinstance(value, dict):
        settings.setdefault("game", {}).update(value)
    elif key in game_keys or key in settings.get("game", {}):
        settings.setdefault("game", {})[key] = value
    elif key in control_keys or key in settings.get("controls", {}):
        settings.setdefault("controls", {})[key] = value
    else:
        # Default to placing unknown keys in 'game'
        settings.setdefault("game", {})[key] = value

    save_game_settings(settings, root_dir)
    return settings


def update_game_settings(updates: Dict[str, Any], root_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Applies multiple updates to settings.json and saves in one atomic operation.
    """
    settings = load_game_settings(root_dir)
    game_keys = {
        "antialiasing",
        "stretched-screen",
        "magic-word-activator",
        "music",
        "ffxiv-camera",
        "camera-sensitivity",
    }
    control_keys = {"forward", "reverse", "turnLeft", "turnRight", "jump"}

    for key, value in updates.items():
        if key == "controls" and isinstance(value, dict):
            settings.setdefault("controls", {}).update(value)
        elif key == "game" and isinstance(value, dict):
            settings.setdefault("game", {}).update(value)
        elif key in game_keys or key in settings.get("game", {}):
            settings.setdefault("game", {})[key] = value
        elif key in control_keys or key in settings.get("controls", {}):
            settings.setdefault("controls", {})[key] = value
        else:
            settings.setdefault("game", {})[key] = value

    save_game_settings(settings, root_dir)
    return settings


# -----------------------------------------------------------------------------
# fusion/launcher_settings.json (Launcher Settings)
# -----------------------------------------------------------------------------

def get_launcher_settings_path(root_dir: Optional[str] = None) -> str:
    """Returns the absolute path to fusion/launcher_settings.json."""
    root = root_dir or get_root_dir()
    return os.path.join(root, "fusion", "launcher_settings.json")


def load_launcher_settings(root_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Safely loads fusion/launcher_settings.json. If missing, writes default settings
    and returns them. Always ensures all default keys are present.
    """
    path = get_launcher_settings_path(root_dir)
    settings = dict(DEFAULT_LAUNCHER_SETTINGS)

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                settings.update(loaded)
        except Exception as e:
            print(f"[Fusion Config] Warning: Failed to read {path} ({e}), using defaults.")
    else:
        # Create initial default file
        try:
            _safe_write_json(path, settings)
        except Exception as e:
            print(f"[Fusion Config] Warning: Could not create initial {path} ({e})")

    return settings


def save_launcher_settings(settings: Dict[str, Any], root_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Safely saves launcher settings to fusion/launcher_settings.json atomically.
    """
    path = get_launcher_settings_path(root_dir)
    _safe_write_json(path, settings)
    return settings


def get_launcher_setting(key: str, default: Any = None, root_dir: Optional[str] = None) -> Any:
    """Fetches a specific setting from fusion/launcher_settings.json."""
    settings = load_launcher_settings(root_dir)
    return settings.get(key, default)


def set_launcher_setting(key: str, value: Any, root_dir: Optional[str] = None) -> Dict[str, Any]:
    """Updates a single launcher setting and saves atomically."""
    settings = load_launcher_settings(root_dir)
    settings[key] = value
    save_launcher_settings(settings, root_dir)
    return settings


def update_launcher_settings(updates: Dict[str, Any], root_dir: Optional[str] = None) -> Dict[str, Any]:
    """Applies multiple updates to launcher settings and saves atomically."""
    settings = load_launcher_settings(root_dir)
    settings.update(updates)
    save_launcher_settings(settings, root_dir)
    return settings


def add_recent_token(token: str, root_dir: Optional[str] = None, max_recent: int = 10) -> Dict[str, Any]:
    """
    Adds a login token to recent_tokens, sets it as last_token, and saves.
    Maintains uniqueness and orders most-recent first, capping at max_recent items.
    """
    settings = load_launcher_settings(root_dir)
    recent = settings.get("recent_tokens", [])
    if not isinstance(recent, list):
        recent = []

    # Filter out existing occurrences and place at front
    recent = [t for t in recent if t != token]
    recent.insert(0, token)
    recent = recent[:max_recent]

    settings["recent_tokens"] = recent
    settings["last_token"] = token
    save_launcher_settings(settings, root_dir)
    return settings


# -----------------------------------------------------------------------------
# Cache Cleaner
# -----------------------------------------------------------------------------

def clean_cache(root_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Modern Python 3 cache cleaner that scans the project root and deletes:
      - *.pyc files
      - *.pyo files
      - __pycache__ directories (recursively)
      - parsetab.py files (generated by ply)

    Preserves .git directory to avoid modifying version control metadata.

    Returns:
        Dict containing counts and lists of removed items, plus any errors encountered:
        {
            "files_deleted": int,
            "dirs_deleted": int,
            "deleted_files": List[str],
            "deleted_dirs": List[str],
            "errors": List[Dict[str, str]]
        }
    """
    root = root_dir or get_root_dir()
    deleted_files: List[str] = []
    deleted_dirs: List[str] = []
    errors: List[Dict[str, str]] = []

    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # Exclude .git directory from traversal
        if ".git" in dirnames:
            dirnames.remove(".git")

        # Delete __pycache__ directories
        for dirname in list(dirnames):
            if dirname == "__pycache__":
                target_dir = os.path.join(dirpath, dirname)
                try:
                    shutil.rmtree(target_dir)
                    deleted_dirs.append(target_dir)
                except Exception as e:
                    errors.append({"path": target_dir, "error": str(e)})
                dirnames.remove(dirname)

        # Delete cache and trash files
        for filename in filenames:
            name_lower = filename.lower()
            ext = os.path.splitext(name_lower)[1]
            if ext in (".pyc", ".pyo") or name_lower == "parsetab.py":
                target_file = os.path.join(dirpath, filename)
                try:
                    os.unlink(target_file)
                    deleted_files.append(target_file)
                except Exception as e:
                    errors.append({"path": target_file, "error": str(e)})

    return {
        "files_deleted": len(deleted_files),
        "dirs_deleted": len(deleted_dirs),
        "deleted_files": deleted_files,
        "deleted_dirs": deleted_dirs,
        "errors": errors,
    }
