# Lets the user pick their Sims 4 Mods folder so we know what to organize!

import sys
from pathlib import Path

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
    messagebox.showinfo("Sims 4 Mod Manager", 
                        "Please select your Sims 4 'Mods' folder.")

    # Ask the user to pick a folder
    selected = filedialog.askdirectory(title="Select your Sims 4 'Mods' folder")
    root.destroy()

    if selected:
        return Path(selected)
    else:
        return None

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

if __name__ == "__main__":
    main()
