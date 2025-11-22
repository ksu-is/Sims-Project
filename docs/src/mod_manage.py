# Step 3: Backup AND organize mods by type

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except:
    tk = None


SCRIPT_EXT = ".ts4script"
PACKAGE_EXT = ".package"


def pick_mods_folder():
    """Open window to choose Mods folder."""
    if tk is None:
        return None

    root = tk.Tk()
    root.withdraw()

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


def get_timestamp():
    """Returns a timestamp string."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def backup_mods_folder(mods_path):
    """Make backup into Mods/_Backup."""
    backup_root = mods_path / "_Backup"
    backup_root.mkdir(exist_ok=True)

    backup_folder = backup_root / f"Mods_Backup_{get_timestamp()}"

    ignore = shutil.ignore_patterns(
        "_Backup", "_Organized", "_Quarantine", "_Duplicates", "_Reports"
    )

    print("📦 Creating backup...")
    shutil.copytree(mods_path, backup_folder, ignore=ignore)
    print("✅ Backup complete! Saved to:", backup_folder)

    return backup_folder


def organize_mods(mods_path):
    """
    Move files into:
    - _Organized/Script_Mods
    - _Organized/Package_CC
    - _Organized/Other
    """
    organized_root = mods_path / "_Organized"
    script_folder = organized_root / "Script_Mods"
    package_folder = organized_root / "Package_CC"
    other_folder = organized_root / "Other"

    script_folder.mkdir(parents=True, exist_ok=True)
    package_folder.mkdir(parents=True, exist_ok=True)
    other_folder.mkdir(parents=True, exist_ok=True)

    script_count = 0
    package_count = 0
    other_count = 0

    ignore_dirs = {"_Backup", "_Organized", "_Quarantine", "_Duplicates", "_Reports"}

    print("🔎 Organizing files...")

    for root, dirs, files in os.walk(mods_path):
        root_path = Path(root)

        # skip our own folders
        if any(ignored in root_path.parts for ignored in ignore_dirs):
            continue

        for filename in files:
            file_path = root_path / filename

            # skip if somehow inside special folders already
            if any(ignored in file_path.parts for ignored in ignore_dirs):
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
    print("Script mods moved   :", script_count)
    print("Package files moved :", package_count)
    print("Other files moved   :", other_count)

    return script_count, package_count, other_count


def main():
    """Main: select Mods, backup, then organize."""
    if len(sys.argv) > 1:
        mods_path = Path(sys.argv[1])
    else:
        mods_path = pick_mods_folder()

    if not mods_path or not mods_path.exists():
        print("\n⚠ ERROR: Mods folder not found or not selected.")
        print("Example usage in a terminal:")
        print('python mod_manager.py "C:\\Users\\YourName\\Documents\\Electronic Arts\\The Sims 4\\Mods"')
        sys.exit(1)

    print("\n🎉 Selected Mods folder:")
    print(mods_path)

    print("\n[1/2] Backing up your Mods folder...")
    backup_mods_folder(mods_path)

    print("\n[2/2] Organizing your mods by type...")
    organize_mods(mods_path)


if __name__ == "__main__":
    main()
