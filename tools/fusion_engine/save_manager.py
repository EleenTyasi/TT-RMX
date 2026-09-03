"""
Save and Database Management for Toontown Remix Fusion Engine.

Handles database backup creation, rotation, listing, restoring, and district state resetting
for Astron database files in astron/databases/ (astrondb/ directory with YAML files and accounts.db.*).
"""

import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.fusion_engine.config import get_root_dir

MAX_AUTO_BACKUPS = 5


def _get_database_dir(root_dir: Optional[str] = None) -> str:
    """Returns the absolute path to astron/databases/."""
    root = root_dir or get_root_dir()
    return os.path.join(root, "astron", "databases")


def _get_backups_dir(root_dir: Optional[str] = None) -> str:
    """Returns the absolute path to backups/saves/."""
    root = root_dir or get_root_dir()
    return os.path.join(root, "backups", "saves")


def _calc_dir_size(dir_path: str, exclude_meta: bool = True) -> int:
    """Calculates total file size of a directory in bytes."""
    total = 0
    if not os.path.isdir(dir_path):
        return 0
    for root, _, files in os.walk(dir_path):
        for f in files:
            if exclude_meta and f == "backup_meta.json":
                continue
            p = os.path.join(root, f)
            try:
                total += os.path.getsize(p)
            except OSError:
                pass
    return total


def _rotate_auto_backups(root_dir: Optional[str] = None, max_keep: int = MAX_AUTO_BACKUPS) -> List[str]:
    """
    Deletes older auto-backups when the total count exceeds max_keep.
    Returns list of deleted slot names.
    """
    backups_dir = _get_backups_dir(root_dir)
    all_backups = list_backups(root_dir)
    auto_backups = [b for b in all_backups if b.get("is_auto") is True]

    # Sort auto-backups by timestamp ascending (oldest first)
    auto_backups.sort(key=lambda b: b.get("timestamp", 0.0))

    deleted_slots: List[str] = []
    if len(auto_backups) > max_keep:
        excess_count = len(auto_backups) - max_keep
        to_delete = auto_backups[:excess_count]
        for b in to_delete:
            slot_name = b["slot_name"]
            slot_path = os.path.join(backups_dir, slot_name)
            try:
                if os.path.isdir(slot_path):
                    shutil.rmtree(slot_path)
                    deleted_slots.append(slot_name)
            except Exception as e:
                print(f"[Fusion SaveManager] Warning: Could not delete old auto backup {slot_path}: {e}")

    return deleted_slots


def create_backup(
    root_dir: Optional[str] = None,
    slot_name: Optional[str] = None,
    is_auto: bool = False
) -> Dict[str, Any]:
    """
    Copies astron/databases/ into backups/saves/<slot_name_or_timestamp>/.
    If is_auto=True, rotates and keeps the latest 5 auto backups.

    Args:
        root_dir: Root project directory (optional, resolved automatically if None).
        slot_name: Custom name for the backup slot (optional).
        is_auto: Boolean indicating if this is an automated backup.

    Returns:
        Dict containing backup info (slot_name, timestamp, formatted date, size, is_auto, path).
    """
    root = root_dir or get_root_dir()
    db_dir = _get_database_dir(root)
    backups_dir = _get_backups_dir(root)

    os.makedirs(db_dir, exist_ok=True)
    os.makedirs(backups_dir, exist_ok=True)

    now = datetime.now()
    timestamp = now.timestamp()
    formatted_date = now.strftime("%Y-%m-%d %H:%M:%S")

    if not slot_name:
        time_str = now.strftime("%Y%m%d_%H%M%S")
        slot_name = f"auto_{time_str}" if is_auto else f"backup_{time_str}"

    dest_dir = os.path.join(backups_dir, slot_name)

    # Clean existing destination directory if it exists
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir, ignore_errors=True)
    os.makedirs(dest_dir, exist_ok=True)

    # Copy files and subdirectories from astron/databases/
    total_size = 0
    if os.path.exists(db_dir):
        for item in os.listdir(db_dir):
            s = os.path.join(db_dir, item)
            d = os.path.join(dest_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

    total_size = _calc_dir_size(dest_dir, exclude_meta=True)

    # Write backup metadata
    meta = {
        "slot_name": slot_name,
        "timestamp": timestamp,
        "formatted_date": formatted_date,
        "formatted date": formatted_date,
        "size": total_size,
        "is_auto": is_auto,
    }
    meta_path = os.path.join(dest_dir, "backup_meta.json")
    try:
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4)
    except Exception as e:
        print(f"[Fusion SaveManager] Warning: Could not write {meta_path}: {e}")

    # Rotate auto backups if requested
    if is_auto:
        _rotate_auto_backups(root, max_keep=MAX_AUTO_BACKUPS)

    return {
        "slot_name": slot_name,
        "timestamp": timestamp,
        "formatted_date": formatted_date,
        "formatted date": formatted_date,
        "size": total_size,
        "is_auto": is_auto,
        "path": dest_dir,
    }


def list_backups(root_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns list of dicts with backup info:
    (slot_name, timestamp, formatted date, size, is_auto).
    Sorted by timestamp descending (newest first).
    """
    root = root_dir or get_root_dir()
    backups_dir = _get_backups_dir(root)

    if not os.path.exists(backups_dir):
        return []

    backups: List[Dict[str, Any]] = []

    for entry in os.listdir(backups_dir):
        entry_path = os.path.join(backups_dir, entry)
        if not os.path.isdir(entry_path):
            continue

        meta_path = os.path.join(entry_path, "backup_meta.json")
        loaded_meta: Optional[Dict[str, Any]] = None

        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    loaded_meta = json.load(f)
            except Exception:
                loaded_meta = None

        if loaded_meta and isinstance(loaded_meta, dict):
            slot_name = loaded_meta.get("slot_name", entry)
            timestamp = loaded_meta.get("timestamp")
            if timestamp is None:
                timestamp = os.path.getmtime(entry_path)
            formatted_date = loaded_meta.get("formatted_date") or loaded_meta.get("formatted date")
            if not formatted_date:
                formatted_date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            size = loaded_meta.get("size", _calc_dir_size(entry_path))
            is_auto = loaded_meta.get("is_auto", entry.lower().startswith("auto"))
        else:
            # Fallback when metadata file is missing
            slot_name = entry
            timestamp = os.path.getmtime(entry_path)
            formatted_date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            size = _calc_dir_size(entry_path)
            is_auto = entry.lower().startswith("auto")

        backups.append({
            "slot_name": slot_name,
            "timestamp": timestamp,
            "formatted_date": formatted_date,
            "formatted date": formatted_date,
            "size": size,
            "is_auto": bool(is_auto),
            "path": entry_path,
        })

    # Sort descending by timestamp (newest first)
    backups.sort(key=lambda b: b.get("timestamp", 0.0), reverse=True)
    return backups


def restore_backup(root_dir: Optional[str] = None, slot_name: str = "") -> Dict[str, Any]:
    """
    Safely restores the specified backup into astron/databases/.

    Args:
        root_dir: Root project directory.
        slot_name: The slot identifier/folder in backups/saves/ to restore from.

    Returns:
        Dict with restore status and path information.

    Raises:
        FileNotFoundError: If the specified backup slot does not exist.
    """
    if not slot_name:
        raise ValueError("slot_name must be specified to restore a backup.")

    root = root_dir or get_root_dir()
    backups_dir = _get_backups_dir(root)
    backup_dir = os.path.join(backups_dir, slot_name)

    if not os.path.exists(backup_dir) or not os.path.isdir(backup_dir):
        raise FileNotFoundError(f"Backup slot '{slot_name}' not found at {backup_dir}")

    db_dir = _get_database_dir(root)
    astrondb_dir = os.path.join(db_dir, "astrondb")

    os.makedirs(db_dir, exist_ok=True)

    # 1. Clean current database files in astron/databases/ (preserving .gitignore)
    for root_scan, dirs, files in os.walk(db_dir, topdown=False):
        for f in files:
            if f.lower() == ".gitignore":
                continue
            try:
                os.unlink(os.path.join(root_scan, f))
            except OSError as e:
                print(f"[Fusion SaveManager] Warning: Could not remove old file {f}: {e}")
        for d in dirs:
            dir_to_clean = os.path.join(root_scan, d)
            # Remove directory if empty (except if it has .gitignore)
            try:
                os.rmdir(dir_to_clean)
            except OSError:
                pass

    # 2. Copy files from backup slot into astron/databases/ (skipping backup_meta.json)
    restored_items: List[str] = []
    for item in os.listdir(backup_dir):
        if item == "backup_meta.json":
            continue
        src = os.path.join(backup_dir, item)
        dst = os.path.join(db_dir, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        restored_items.append(item)

    # 3. Ensure astrondb directory exists for astron server
    os.makedirs(astrondb_dir, exist_ok=True)

    # 4. Ensure .gitignore files exist to prevent uncommitted db files in git
    db_gitignore = os.path.join(db_dir, ".gitignore")
    if not os.path.exists(db_gitignore):
        try:
            with open(db_gitignore, "w", encoding="utf-8") as f:
                f.write("*.db*\n*.bak\n*.dat\n*.dir\n*.yaml\nastrondb/*.yaml\n!astrondb/.gitignore\n")
        except OSError:
            pass

    astrondb_gitignore = os.path.join(astrondb_dir, ".gitignore")
    if not os.path.exists(astrondb_gitignore):
        try:
            with open(astrondb_gitignore, "w", encoding="utf-8") as f:
                f.write("*.yaml\n")
        except OSError:
            pass

    return {
        "success": True,
        "slot_name": slot_name,
        "restored_from": backup_dir,
        "target_dir": db_dir,
        "restored_items": restored_items,
    }


def reset_district_state(root_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Wipes the database for a fresh playthrough while creating an auto-backup first.

    1. Automatically creates an auto-backup of current state.
    2. Deletes accounts.db.* and astrondb/*.yaml files.
    3. Preserves .gitignore files and ensures astrondb/ directory exists.

    Returns:
        Dict with status, auto_backup info, and deleted files count.
    """
    root = root_dir or get_root_dir()
    db_dir = _get_database_dir(root)
    astrondb_dir = os.path.join(db_dir, "astrondb")

    # Step 1: Create auto-backup prior to reset
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    auto_backup = create_backup(
        root_dir=root,
        slot_name=f"auto_pre_reset_{now_str}",
        is_auto=True
    )

    # Step 2: Wipe database files
    deleted_files: List[str] = []

    if os.path.exists(db_dir):
        # Remove accounts.db files and any dbm files in astron/databases/
        for filename in os.listdir(db_dir):
            filepath = os.path.join(db_dir, filename)
            if os.path.isfile(filepath):
                name_lower = filename.lower()
                if name_lower == ".gitignore":
                    continue
                if name_lower.startswith("accounts.db") or name_lower.endswith((".db", ".bak", ".dat", ".dir")):
                    try:
                        os.unlink(filepath)
                        deleted_files.append(filepath)
                    except OSError as e:
                        print(f"[Fusion SaveManager] Warning: Could not delete {filepath}: {e}")

    # Remove all YAML files from astrondb
    if os.path.exists(astrondb_dir):
        for filename in os.listdir(astrondb_dir):
            filepath = os.path.join(astrondb_dir, filename)
            if os.path.isfile(filepath):
                name_lower = filename.lower()
                if name_lower == ".gitignore":
                    continue
                if name_lower.endswith(".yaml") or name_lower.endswith(".yml"):
                    try:
                        os.unlink(filepath)
                        deleted_files.append(filepath)
                    except OSError as e:
                        print(f"[Fusion SaveManager] Warning: Could not delete {filepath}: {e}")
    else:
        os.makedirs(astrondb_dir, exist_ok=True)

    # Ensure .gitignore in astrondb exists
    astrondb_gitignore = os.path.join(astrondb_dir, ".gitignore")
    if not os.path.exists(astrondb_gitignore):
        try:
            with open(astrondb_gitignore, "w", encoding="utf-8") as f:
                f.write("*.yaml\n")
        except OSError:
            pass

    return {
        "success": True,
        "auto_backup": auto_backup,
        "deleted_files_count": len(deleted_files),
        "deleted_files": deleted_files,
    }
