# Lets the user pick their Sims 4 Mods folder so we know what to organize!

import sys
import shutil
from pathlib import Path
from datetime import datetime

# We try to import Tkinter so we can use a folder picker window.
# If it fails (like no display on some computers), we will skip the GUI.
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except:
    tk = None  # GUI is not available


def pick_mods_folder():
    """
    Open a small window so the user can choose their Mods folder.
    Returns the selected path or None if cancelled.
    """
    if tk is None:
        return None  # GUI isn't available

    # Create and hide main window (we only want the folder picker)
    root = tk.Tk()
    root.withdraw()

    # Pop up a message to help the user
    messagebox.showinfo(
        "Sims 4 Mod Manager",
        "Please select your Sims 4 'Mods' folder."
    )

    # Ask the user to pick a folder
    selected = filedialog.askdirectory(
        title="Select your Sims 4 'Mods' folder"
    )
    root.destroy()

    if selected:
        return Path(selected)
    else:
        return None


def get_timestamp():
    """Returns a timestamp string for naming backup folders."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def backup_mods_folder(mods_path):
    """
    Makes a full backup of the Mods folder before any changes happen.
    This prevents the user from losing their mods if something goes wrong.
    """
    # Add a new folder inside Mods called _Backup
    backup_folder = mods_path / "_Backup"
    backup_folder.mkdir(exist_ok=True)  # Create folder if it does not exist yet

    # Create a new timestamped backup folder
    new_backup = backup_folder / f"Mods_Backup_{get_timestamp()}"

    # Copy everything except folders we will create later
    shutil.copytree(
        mods_path,
        new_backup,
        ignore=shutil.ignore_patterns(
            "_Backup", "_Organized", "_Quarantine", "_Duplicates", "_Reports"
        )
    )

    print("📦 Backup complete!")
    print("Backup saved to:", new_backup)
    return new_backup


def main():
    """
    Main function that tries to get the Mods folder.
    It checks the command-line first, then the GUI window if needed.
    """
    # If user typed a folder path in the terminal, use that first
    if len(sys.argv) > 1:
        mods_path = Path(sys.argv[1])
    else:
        mods_path = pick_mods_folder()  # Ask the user to choose a folder

    # If nothing was selected or the path is invalid, stop here
    if not mods_path or not mods_path.exists():
        print("\n⚠ ERROR: Mods folder not found!")
        print("Example usage in a terminal:")
        print('python mod_manager.py "C:\\Users\\YourName\\Documents\\Electronic Arts\\The Sims 4\\Mods"')
        sys.exit(1)

    print("\n🎉 Successfully selected Mods folder:")
    print(mods_path)

    print("\n[1/4] Backing up your Mods folder...")
    backup_mods_folder(mods_path)


if __name__ == "__main__":
    main()
