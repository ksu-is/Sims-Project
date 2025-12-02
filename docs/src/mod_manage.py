"""
Sims 4 Mod Manager & Organizer

Features:
1. Lets you select your Sims 4 Mods folder (CLI or GUI).
2. Backs up the Mods folder into _Backup/Mods_Backup_<timestamp>.
3. Organizes mods:
   - .ts4script  -> _Organized/Script_Mods
   - .package    -> _Organized/Package_CC
   - everything else -> _Organized/Other
   - zero-byte / unreadable files -> _Quarantine
4. Saves a simple text report in _Reports with counts.
5. Uses threads to organize files faster.
6. Has a --fast mode to SKIP backup (use only when you’re sure).
"""

import sys
import os
import shutil
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

# Special folders our tool creates and should ignore while scanning
IGNORE_DIRS = {"_Backup", "_Organized", "_Quarantine", "_Duplicates", "_Reports"}


# --------------- Folder Selection ---------------

def pick_mods_folder():
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

def get_timestamp():
    """Returns a timestamp string like 2025-11-30_16-22-05."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def backup_mods_folder(mods_path):
    """
    Makes a backup copy of the Mods folder inside Mods/_Backup.
    Returns the path to the new backup folder.
    """
    backup_root = mods_path / "_Backup"
    backup_root.mkdir(exist_ok=True)

    backup_folder = backup_root / f"Mods_Backup_{get_timestamp()}"

    # Ignore our own tool folders so backups don't explode in size
    ignore = shutil.ignore_patterns(
        "_Backup", "_Organized", "_Quarantine", "_Duplicates", "_Reports"
    )

    print("📦 Creating backup... this may take a moment...")
    shutil.copytree(mods_path, backup_folder, ignore=ignore)
    print("✅ Backup complete! Saved to:", backup_folder)

    return backup_folder


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


# --------------- File Listing (for threading + countdown) ---------------

def list_mod_files(mods_path: Path):
    """
    Walk the Mods folder and return a list of all files
    we actually want to process (ignores our special folders).
    """
    files = []
    for root, dirs, filenames in os.walk(mods_path):
        root_path = Path(root)

        # Skip our special folders early
        if any(ignored in root_path.parts for ignored in IGNORE_DIRS):
            continue

        for name in filenames:
            file_path = root_path / name

            # Extra safety: skip if already inside special folders
            if any(ignored in file_path.parts for ignored in IGNORE_DIRS):
                continue

            files.append(file_path)

    return files


# --------------- Per-file Worker (used by threads) ---------------

def process_single_file(file_path: Path,
                        script_folder: Path,
                        package_folder: Path,
                        other_folder: Path,
                        quarantine_folder: Path) -> str:
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


# --------------- Organizing Logic (Threaded + Countdown) ---------------

def organize_mods(mods_path: Path):
    """
    Use threads to speed up organizing:
    - First, build a list of all files to touch.
    - Then process them in a thread pool.
    - Show a progress counter: "Processing X/Y files..."

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

    # Number of threads (you can tweak this; 4 is safe for most)
    max_workers = 4

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                process_single_file,
                file_path,
                script_folder,
                package_folder,
                other_folder,
                quarantine_folder
            )
            for file_path in files
        ]

        # as_completed gives us futures as they finish
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

            # Progress line
            print(f"Processing {i}/{total_files} files...", end="\r")

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

def save_report(mods_path: Path, stats: dict):
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

def main():
    """
    Main function:
    1. Parse args and check for --fast.
    2. Get Mods folder (CLI or GUI).
    3. Back up Mods folder (unless --fast).
    4. Organize mods using threads.
    5. Save a summary report.
    """

    # -------- Parse command-line arguments --------
    fast_mode = False
    args = sys.argv[1:]  # everything after script name

    if "--fast" in args:
        fast_mode = True
        args.remove("--fast")

    if args:
        # If the user gave a path, use that as Mods folder
        mods_path = Path(args[0])
    else:
        # Otherwise, use the GUI picker
        mods_path = pick_mods_folder()

    # Validate path
    if not mods_path or not mods_path.exists():
        print("\n⚠ ERROR: Mods folder not found or not selected.")
        print("Examples:")
        print('  python mod_manager.py "C:\\Users\\YourName\\Documents\\Electronic Arts\\The Sims 4\\Mods"')
        print('  python mod_manager.py --fast "C:\\Users\\YourName\\Documents\\Electronic Arts\\The Sims 4\\Mods"')
        sys.exit(1)

    print("\n🎉 Selected Mods folder:")
    print(mods_path)

    # -------- Backup (unless fast mode) --------
    if fast_mode:
        print("\n[FAST MODE] Skipping backup to speed things up.")
        print("⚠ Use this only if you already have a safe backup!")
    else:
        print("\n[1/3] Backing up your Mods folder...")
        backup_mods_folder(mods_path)

    # -------- Organize (threaded) --------
    print("\n[2/3] Organizing your mods by type and quarantining broken files...")
    stats = organize_mods(mods_path)

    # -------- Report --------
    print("\n[3/3] Saving report...")
    save_report(mods_path, stats)

    print("\n✅ All done!")
    print("- Check _Backup for your backups (unless you used --fast)")
    print("- Check _Organized for sorted mods")
    print("- Check _Quarantine for broken mods")
    print("- Check _Reports for the summary file")


if __name__ == "__main__":
    main()
