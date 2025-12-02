"""
Sims 4 Mod Manager & Organizer

What this script does:
1. Lets you select your Sims 4 Mods folder (CLI or GUI).
2. Backs up the Mods folder into _Backup/Mods_Backup_<timestamp>.
3. Organizes mods:
   - .ts4script  -> _Organized/Script_Mods
   - .package    -> _Organized/Package_CC
   - everything else -> _Organized/Other
   - zero-byte / unreadable files -> _Quarantine
4. Saves a simple text report in _Reports with counts.
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

# Try to import Tkinter for a folder picker GUI.
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except Exception:
    tk = None

# File type constants
SCRIPT_EXT = ".ts4script"
PACKAGE_EXT = ".package"

# Folders our tool uses and should ignore when scanning
IGNORE_DIRS = {"_Backup", "_Organized", "_Quarantine", "_Duplicates", "_Reports"}


# --------------- Folder Selection ---------------

def pick_mods_folder():
    """
    Opens a small window so the user can choose their Mods folder.
    Returns a Path object or None if the user cancels.
    """
    if tk is None:
        # GUI not available (e.g., no display)
        return None

    root = tk.Tk()
    root.withdraw()  # Hide main Tk window

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

def is_broken_mod(file_path):
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


# --------------- Organizing Logic ---------------

def organize_mods(mods_path):
    """
    Walk all files under the Mods folder and:
    - Move .ts4script files into _Organized/Script_Mods
    - Move .package files into _Organized/Package_CC
    - Move all other files into _Organized/Other
    - Broken files into _Quarantine

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

    script_count = 0
    package_count = 0
    other_count = 0
    broken_count = 0

    print("🔎 Scanning and organizing files...")

    for root, dirs, files in os.walk(mods_path):
        root_path = Path(root)

        # Skip our own management folders (_Backup, _Organized, etc.)
        if any(ignored in root_path.parts for ignored in IGNORE_DIRS):
            continue

        for filename in files:
            file_path = root_path / filename

            # Skip if somehow already in our special folders
            if any(ignored in file_path.parts for ignored in IGNORE_DIRS):
                continue

            # Check if the file seems broken
            if is_broken_mod(file_path):
                dest = quarantine_folder / filename
                shutil.move(str(file_path), str(dest))
                broken_count += 1
                print("🛑 Broken mod moved to _Quarantine:", filename)
                continue

            ext = file_path.suffix.lower()

            if ext == SCRIPT_EXT:
                dest = script_folder / filename
                shutil.move(str(file_path), str(dest))
                script_count += 1
            elif ext == PACKAGE_EXT:
                dest = package_folder / filename
                shutil.move(str(file_path), str(dest))
                package_count += 1
            else:
                dest = other_folder / filename
                shutil.move(str(file_path), str(dest))
                other_count += 1

    print("✨ Organizing complete!")
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

def save_report(mods_path, stats):
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
    1. Get Mods folder (CLI or GUI).
    2. Back up Mods folder.
    3. Organize mods and quarantine broken ones.
    4. Save a small report.
    """

    # 1. Find Mods folder
    if len(sys.argv) > 1:
        # Example: python mod_manager.py "C:\path\to\Mods"
        mods_path = Path(sys.argv[1])
    else:
        mods_path = pick_mods_folder()

    # Validate path
    if not mods_path or not mods_path.exists():
        print("\n⚠ ERROR: Mods folder not found or not selected.")
        print("Example usage in a terminal:")
        print('python mod_manager.py "C:\\Users\\YourName\\Documents\\Electronic Arts\\The Sims 4\\Mods"')
        sys.exit(1)

    print("\n🎉 Selected Mods folder:")
    print(mods_path)

    # 2. Backup
    print("\n[1/3] Backing up your Mods folder...")
    backup_mods_folder(mods_path)

    # 3. Organize + quarantine
    print("\n[2/3] Organizing your mods by type and quarantining broken files...")
    stats = organize_mods(mods_path)

    # 4. Report
    print("\n[3/3] Saving report...")
    save_report(mods_path, stats)

    print("\n✅ All done!")
    print("- Check _Backup for your backups")
    print("- Check _Organized for sorted mods")
    print("- Check _Quarantine for broken mods")
    print("- Check _Reports for the summary file")


if __name__ == "__main__":
    main()
