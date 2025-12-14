"""
Sims 4 Mod Manager & Organizer

Features:
1. Lets you select your Sims 4 Mods folder (CLI or GUI).
2. Optionally backs up the Mods folder into _Backup/Mods_Backup_<timestamp>.
   - Asks if you want to back up (GUI popup or terminal prompt).
   - Can remember your choice using a simple settings file.
   - You can still force skip backup with --fast.
3. Organizes mods:
   - .ts4script  -> _Organized/Script_Mods
   - .package    -> _Organized/Package_CC
   - everything else -> _Organized/Other
   - zero-byte / unreadable files -> _Quarantine
4. Uses threads to speed up organizing.
5. Shows a progress bar and ETA while processing.
6. Saves a simple text report in _Reports with counts.
"""

import sys
import os
import shutil
import time
import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try to import Tkinter for a folder picker GUI.
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except Exception:
    tk = None

# File type constants
SCRIPT_EXT = ".ts4script"
PACKAGE_EXT = ".package"

# Name of the settings file stored in the Mods folder
SETTINGS_FILENAME = "_ModManagerSettings.json"

# Special folders our tool creates and should ignore while scanning
IGNORE_DIRS = {"_Backup", "_Organized", "_Quarantine", "_Duplicates", "_Reports"}


# --------------- Folder Selection ---------------

def pick_mods_folder() -> Path | None:
    """
    Opens a small window so the user can choose their Mods folder.
    Returns a Path object or None if the user cancels.
    """
    if tk is None:
        return None  # GUI not available

    root = tk.Tk()
    root.withdraw()  # Hide main window

    messagebox.showinfo(
        "Sims 4 Mod Manager",
        "Please select your Sims 4 'Mods' folder."
    )

    selected = filedialog.askdirectory(
        title="Select your Sims 4 'Mods' folder"
    )

    root.destroy()

    if selected:
        return Path(selected)
    else:
        return None


# --------------- Backup Helpers ---------------

def get_timestamp() -> str:
    """Returns a timestamp string like 2025-11-30_16-22-05."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def backup_mods_folder(mods_path: Path) -> Path:
    """
    Makes a backup copy of the Mods folder inside Mods/_Backup.
    Returns the path to the new backup folder.
    """
    backup_root = mods_path / "_Backup"
    backup_root.mkdir(exist_ok=True)

    backup_folder = backup_root / f"Mods_Backup_{get_timestamp()}"

    # Ignore our own tool folders so backups don't explode in size
    ignore = shutil.ignore_patterns(
        "_Backup", "_Organized", "_Quarantine", "_Duplicates", "_Reports", SETTINGS_FILENAME
    )

    print("📦 Creating backup... this may take a moment...")
    shutil.copytree(mods_path, backup_folder, ignore=ignore)
    print("✅ Backup complete! Saved to:", backup_folder)

    return backup_folder


# --------------- Settings (remember backup choice) ---------------

def load_settings(mods_path: Path) -> dict:
    """Load settings from _ModManagerSettings.json if it exists."""
    settings_file = mods_path / SETTINGS_FILENAME
    if not settings_file.exists():
        return {}
    try:
        with settings_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # If the file is corrupt, ignore it
        return {}


def save_settings(mods_path: Path, settings: dict) -> None:
    """Save settings to _ModManagerSettings.json."""
    settings_file = mods_path / SETTINGS_FILENAME
    try:
        with settings_file.open("w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        # If saving fails, just keep going; not critical
        pass


def ask_backup_choice() -> tuple[bool, bool]:
    """
    Ask user if they want to back up the Mods folder.
    Returns (do_backup, remember_choice).
    """
    # GUI version
    if tk is not None:
        root = tk.Tk()
        root.withdraw()
        do_backup = messagebox.askyesno(
            "Backup Mods?",
            "Do you want to back up your Mods folder first?\n\n"
            "(Recommended to avoid losing mods if something goes wrong.)"
        )
        # Ask if they want to remember the choice
        remember = messagebox.askyesno(
            "Remember Choice?",
            "Do you want to remember this backup choice for future runs?"
        )
        root.destroy()
        return do_backup, remember

    # Terminal fallback version
    while True:
        answer = input("Do you want to back up your Mods folder? (Y/N): ").strip().lower()
        if answer in ("y", "yes"):
            do_backup = True
            break
        if answer in ("n", "no"):
            do_backup = False
            break
        print("Please type Y or N.")

    while True:
        remember_ans = input("Remember this choice for next time? (Y/N): ").strip().lower()
        if remember_ans in ("y", "yes"):
            return do_backup, True
        if remember_ans in ("n", "no"):
            return do_backup, False
        print("Please type Y or N.")


# --------------- Broken File Check ---------------

def is_broken_mod(file_path: Path) -> bool:
    """
    Very simple broken check:
    - If the file is 0 bytes, treat as broken.
    - If we can't read its size, also treat as broken.
    """
    try:
        size = file_path.stat().st_size
        if size == 0:
            return True
        return False
    except Exception:
        # If stat() fails, something is off.
        return True


# --------------- File Listing (for threading + progress) ---------------

def list_mod_files(mods_path: Path) -> list[Path]:
    """
    Walk the Mods folder and return a list of all files
    we actually want to process (ignores our special folders and settings file).
    """
    files: list[Path] = []
    for root, dirs, filenames in os.walk(mods_path):
        root_path = Path(root)

        # Skip our special folders early
        if any(ignored in root_path.parts for ignored in IGNORE_DIRS):
            continue

        for name in filenames:
            file_path = root_path / name

            # Skip settings file itself
            if file_path.name == SETTINGS_FILENAME:
                continue

            # Extra safety: skip if already inside special folders
            if any(ignored in file_path.parts for ignored in IGNORE_DIRS):
                continue

            files.append(file_path)

    return files


# --------------- Per-file Worker (used by threads) ---------------

def process_single_file(
    file_path: Path,
    script_folder: Path,
    package_folder: Path,
    other_folder: Path,
    quarantine_folder: Path,
) -> str:
    """
    Process one file:
    - If broken -> move to _Quarantine
    - Else sort by extension into Script_Mods, Package_CC, or Other

    Returns one of: "script", "package", "other", "broken"
    """
    try:
        # Check if broken
        if is_broken_mod(file_path):
            dest = quarantine_folder / file_path.name
            shutil.move(str(file_path), str(dest))
            return "broken"

        ext = file_path.suffix.lower()

        if ext == SCRIPT_EXT:
            dest = script_folder / file_path.name
            shutil.move(str(file_path), str(dest))
            return "script"
        elif ext == PACKAGE_EXT:
            dest = package_folder / file_path.name
            shutil.move(str(file_path), str(dest))
            return "package"
        else:
            dest = other_folder / file_path.name
            shutil.move(str(file_path), str(dest))
            return "other"

    except Exception:
        # If something goes wrong, best effort: quarantine it
        try:
            dest = quarantine_folder / file_path.name
            shutil.move(str(file_path), str(dest))
        except Exception:
            pass
        return "broken"


# --------------- Organizing Logic (Threaded + Progress Bar + ETA) ---------------

def organize_mods(mods_path: Path) -> dict:
    """
    Use threads to speed up organizing:
    - First, build a list of all files to touch.
    - Then process them in a thread pool.
    - Show a progress bar, percentage, and ETA.

    Returns a dict with stats.
    """
    organized_root = mods_path / "_Organized"
    script_folder = organized_root / "Script_Mods"
    package_folder = organized_root / "Package_CC"
    other_folder = organized_root / "Other"
    quarantine_folder = mods_path / "_Quarantine"

    script_folder.mkdir(parents=True, exist_ok=True)
    package_folder.mkdir(parents=True, exist_ok=True)
    other_folder.mkdir(parents=True, exist_ok=True)
    quarantine_folder.mkdir(parents=True, exist_ok=True)

    # List all files once (used for both total count + work list)
    files = list_mod_files(mods_path)
    total_files = len(files)

    if total_files == 0:
        print("No files found to organize.")
        return {
            "Script Mods Organized": 0,
            "Package Files Organized": 0,
            "Other Files Organized": 0,
            "Broken Mods Quarantined": 0,
        }

    print(f"🔎 Organizing files with threading... Total Mods Found: {total_files}\n")

    script_count = 0
    package_count = 0
    other_count = 0
    broken_count = 0

    max_workers = 4  # You can adjust if you want more/less parallelism
    bar_length = 30  # Characters for the visual progress bar

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                process_single_file,
                file_path,
                script_folder,
                package_folder,
                other_folder,
                quarantine_folder,
            )
            for file_path in files
        ]

        for i, future in enumerate(as_completed(futures), start=1):
            result = future.result()

            if result == "script":
                script_count += 1
            elif result == "package":
                package_count += 1
            elif result == "other":
                other_count += 1
            elif result == "broken":
                broken_count += 1

            # Progress stats
            progress = i / total_files
            filled = int(bar_length * progress)
            bar = "#" * filled + "-" * (bar_length - filled)
            percent = progress * 100

            elapsed = time.time() - start_time
            if i > 0:
                avg_per_file = elapsed / i
                remaining = total_files - i
                eta_seconds = avg_per_file * remaining
            else:
                eta_seconds = 0

            eta_min = int(eta_seconds // 60)
            eta_sec = int(eta_seconds % 60)

            print(
                f"\r[{bar}] {percent:5.1f}%  ({i}/{total_files})  "
                f"ETA ~ {eta_min:02d}:{eta_sec:02d}",
                end="",
                flush=True,
            )

    print("\n\n✨ Organizing complete!")
    print("Script mods moved      :", script_count)
    print("Package files moved    :", package_count)
    print("Other files moved      :", other_count)
    print("Broken mods quarantined:", broken_count)

    stats = {
        "Script Mods Organized": script_count,
        "Package Files Organized": package_count,
        "Other Files Organized": other_count,
        "Broken Mods Quarantined": broken_count,
    }

    return stats


# --------------- Reporting ---------------

def save_report(mods_path: Path, stats: dict) -> None:
    """
    Saves a simple text report in Mods/_Reports/report_<timestamp>.txt
    with counts of what the script did.
    """
    reports_folder = mods_path / "_Reports"
    reports_folder.mkdir(exist_ok=True)

    report_file = reports_folder / f"report_{get_timestamp()}.txt"

    with report_file.open("w", encoding="utf-8") as f:
        f.write("Sims 4 Mod Manager Report\n")
        f.write("-------------------------\n\n")
        f.write(f"Mods folder: {mods_path}\n\n")
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")

    print("📝 Report saved to:", report_file)


# --------------- Main Entry Point ---------------

def main() -> None:
    """
    Main function:
    1. Parse args for Mods path, and optional --fast.
    2. Get Mods folder (CLI or GUI).
    3. Ask if user wants backup (unless --fast or remembered).
    4. Optionally back up Mods folder.
    5. Organize mods using threads with progress bar and ETA.
    6. Save a summary report.
    """

    args = sys.argv[1:]
    fast_mode = False

    # Check for --fast flag (skip backup entirely)
    if "--fast" in args:
        fast_mode = True
        args.remove("--fast")

    # Determine Mods folder path
    if args:
        mods_path = Path(args[0])
    else:
        mods_path = pick_mods_folder()

    if not mods_path or not mods_path.exists():
        print("\n⚠ ERROR: Mods folder not found or not selected.")
        print("Examples:")
        print('  python mod_manager.py "C:\\Users\\YourName\\Documents\\Electronic Arts\\The Sims 4\\Mods"')
        print('  python mod_manager.py --fast "C:\\Users\\YourName\\Documents\\Electronic Arts\\The Sims 4\\Mods"')
        sys.exit(1)

    print("\n🎉 Selected Mods folder:")
    print(mods_path)

    # Load settings (backup preference)
    settings = load_settings(mods_path)
    do_backup = False

    if fast_mode:
        print("\n[FAST MODE] Skipping backup to speed things up.")
        print("⚠ Use this only if you already have a safe backup!")
    else:
        pref = settings.get("backup_preference")

        if pref == "always":
            print("\nSettings: Always back up before organizing.")
            do_backup = True
        elif pref == "never":
            print("\nSettings: Skip backup (user preference).")
            do_backup = False
        else:
            # Ask user what they want to do this time
            do_backup, remember = ask_backup_choice()
            if remember:
                settings["backup_preference"] = "always" if do_backup else "never"
                save_settings(mods_path, settings)

    # Backup if chosen
    if do_backup and not fast_mode:
        print("\n[1/3] Backing up your Mods folder...")
        backup_mods_folder(mods_path)
    else:
        print("\n[1/3] Skipping backup step.")

    # Organize (threaded)
    print("\n[2/3] Organizing your mods by type and quarantining broken files...")
    stats = organize_mods(mods_path)

    # Save report
    print("\n[3/3] Saving report...")
    save_report(mods_path, stats)

    print("\n✅ All done!")
    print("- Check _Backup for your backups (if enabled)")
    print("- Check _Organized for sorted mods")
    print("- Check _Quarantine for broken mods")
    print("- Check _Reports for the summary file")


if __name__ == "__main__":
    main()
